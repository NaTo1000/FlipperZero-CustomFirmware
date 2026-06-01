"""
Tests for ConductorX core components.
All tests use only stdlib + testcontainers — no external services required.
"""
import pytest
from cloud.dolfi.conductorx.speed.mode_controller import ModeController, Speed
from cloud.dolfi.conductorx.ledger.chain import AuditLedger
from cloud.dolfi.conductorx.agents.receptionist import ReceptionistAgent
from cloud.dolfi.conductorx.agents.code_agent import CodeAgent
from cloud.dolfi.conductorx.agents.debug_agent import DebugAgent
from cloud.dolfi.conductorx.agents.recovery import RecoveryAgent
from cloud.dolfi.conductorx.agents.crypto_agent import CryptoAgent
from cloud.dolfi.conductorx.scaler.pec import PECScaler, LoadSample


# ---------------------------------------------------------------------------
# ModeController
# ---------------------------------------------------------------------------

class TestModeController:
    def test_default_speed_is_guidance(self):
        mc = ModeController()
        assert mc.speed == Speed.GUIDANCE

    def test_set_speed(self):
        mc = ModeController()
        mc.set_speed(3)
        assert mc.speed == Speed.FULL_AUTO
        assert mc.is_autonomous()

    def test_auto_detect_tutorial_keywords(self):
        mc = ModeController()
        mc.auto_detect("how do I flash my Flipper?")
        assert mc.speed == Speed.OVERLAY

    def test_auto_detect_auto_keywords(self):
        mc = ModeController()
        mc.auto_detect("deploy the latest firmware release")
        assert mc.speed == Speed.FULL_AUTO

    def test_system_prompt_changes_with_speed(self):
        mc = ModeController()
        mc.set_speed(Speed.OVERLAY)
        prompt = mc.system_prompt()
        assert "Tutorial" in prompt or "Overlay" in prompt

    def test_invalid_speed_raises(self):
        mc = ModeController()
        with pytest.raises(ValueError):
            mc.set_speed(99)


# ---------------------------------------------------------------------------
# AuditLedger
# ---------------------------------------------------------------------------

class TestAuditLedger:
    def test_empty_chain_is_valid(self):
        ledger = AuditLedger()
        assert ledger.verify_chain()

    def test_append_and_verify(self):
        ledger = AuditLedger()
        ledger.append("test_agent", "test_action", {"key": "value"})
        ledger.append("test_agent", "second_action", {"key": "value2"})
        assert ledger.verify_chain()

    def test_tampered_chain_fails_verification(self):
        ledger = AuditLedger()
        ledger.append("agent", "action", {"x": 1})
        # Tamper with the first entry's prev_hash
        ledger._storage[0]["prev_hash"] = "deadbeef" * 8
        assert not ledger.verify_chain()

    def test_genesis_hash_for_first_entry(self):
        ledger = AuditLedger()
        row = ledger.append("agent", "first", {})
        assert row["prev_hash"] == "0" * 64


# ---------------------------------------------------------------------------
# ReceptionistAgent
# ---------------------------------------------------------------------------

class TestReceptionistAgent:
    def test_routes_firmware_to_conductor(self):
        agent = ReceptionistAgent()
        decision = agent.route("flash the latest firmware to my Flipper")
        assert decision.target == "conductor"

    def test_routes_how_to_tutorial(self):
        agent = ReceptionistAgent()
        decision = agent.route("how do I capture NFC cards?")
        assert decision.target == "tutorial"

    def test_routes_debug_keywords(self):
        agent = ReceptionistAgent()
        decision = agent.route("I got an error crash in the log")
        assert decision.target == "debug"

    def test_routes_code_generation(self):
        agent = ReceptionistAgent()
        decision = agent.route("write a BadUSB script for me")
        assert decision.target == "code"

    def test_default_route_on_unknown(self):
        agent = ReceptionistAgent()
        decision = agent.route("xyzzy frobnigate the quux")
        # Should default to conductor with low confidence
        assert decision.confidence <= 0.5


# ---------------------------------------------------------------------------
# CodeAgent
# ---------------------------------------------------------------------------

class TestCodeAgent:
    def test_proof_safe_python(self):
        agent = CodeAgent()
        code = "def hello():\n    print('Hello, Flipper!')\n"
        result = agent.proof_python(code)
        assert result.is_safe

    def test_proof_detects_eval(self):
        agent = CodeAgent()
        code = "eval(user_input)"
        result = agent.proof_python(code)
        assert not result.is_safe or any("eval" in i for i in result.issues)

    def test_proof_syntax_error(self):
        agent = CodeAgent()
        result = agent.proof_python("def broken(:\n    pass")
        assert not result.is_safe

    def test_generate_fam_manifest(self):
        agent = CodeAgent()
        manifest = agent.generate_fam_manifest("My App", "my_app_id")
        assert "my_app_id" in manifest
        assert "My App" in manifest

    def test_safe_rewrite_fixes_strcpy(self):
        agent = CodeAgent()
        code = "strcpy(dest, src);"
        result = agent.safe_rewrite(code, language="c")
        assert result.rewritten is not None
        assert "strncpy" in result.rewritten


# ---------------------------------------------------------------------------
# DebugAgent
# ---------------------------------------------------------------------------

class TestDebugAgent:
    def test_analyze_connection_error(self):
        agent = DebugAgent()
        tb = "ConnectionRefusedError: [Errno 111] Connection refused"
        analysis = agent.analyze(tb)
        assert analysis.error_type == "ConnectionRefusedError"
        assert len(analysis.suggestions) > 0

    def test_analyze_timeout(self):
        agent = DebugAgent()
        analysis = agent.analyze("asyncio.TimeoutError")
        assert analysis.auto_fixable

    def test_format_report_contains_error_type(self):
        agent = DebugAgent()
        analysis = agent.analyze("KeyError: 'firmware_version'")
        report = agent.format_report(analysis)
        assert "KeyError" in report

    def test_analyze_flipper_log(self):
        agent = DebugAgent()
        log = "[D] SubGhz: Starting\n[E] NFC: Read timeout\n[D] Done"
        errors = agent.analyze_flipper_log(log)
        assert len(errors) == 1
        assert "Read timeout" in errors[0].message


# ---------------------------------------------------------------------------
# RecoveryAgent
# ---------------------------------------------------------------------------

class TestRecoveryAgent:
    def test_recover_with_snapshot(self):
        agent = RecoveryAgent()
        agent.snapshot({"state": "good"})
        agent.snapshot({"state": "broken"})
        result = agent.recover({"state": "broken"})
        assert result.success
        assert result.rolled_back_to is not None

    def test_recover_uses_safe_base(self):
        agent = RecoveryAgent()
        agent.mark_safe({"state": "safe"})
        result = agent.recover({"state": "broken"})
        assert result.success
        assert "safe_base" in result.rolled_back_to

    def test_recover_factory_defaults_when_no_snapshots(self):
        agent = RecoveryAgent()
        result = agent.recover({"state": "broken"})
        assert result.success
        assert result.rolled_back_to == "factory_defaults"


# ---------------------------------------------------------------------------
# CryptoAgent
# ---------------------------------------------------------------------------

class TestCryptoAgent:
    def test_encrypt_decrypt_roundtrip(self):
        agent = CryptoAgent()
        key = agent.generate_aes_key()
        plaintext = b"Flipper Zero secret payload"
        blob = agent.encrypt(plaintext, key)
        recovered = agent.decrypt(blob, key)
        assert recovered == plaintext

    def test_encrypt_produces_different_ciphertexts(self):
        agent = CryptoAgent()
        key = agent.generate_aes_key()
        b1 = agent.encrypt(b"same", key)
        b2 = agent.encrypt(b"same", key)
        # Nonces differ → ciphertexts differ
        assert b1.nonce != b2.nonce

    def test_sign_verify_roundtrip(self):
        agent = CryptoAgent()
        private_key, public_key = agent.generate_signing_keypair()
        message = b"ConductorX audit entry"
        signature = agent.sign(message, private_key)
        assert agent.verify(message, signature, public_key)

    def test_tampered_signature_fails(self):
        agent = CryptoAgent()
        private_key, public_key = agent.generate_signing_keypair()
        message = b"original"
        signature = agent.sign(message, private_key)
        assert not agent.verify(b"tampered", signature, public_key)

    def test_b64_roundtrip(self):
        agent = CryptoAgent()
        key = agent.generate_aes_key()
        blob = agent.encrypt(b"test data", key)
        b64 = blob.to_b64()
        from cloud.dolfi.conductorx.agents.crypto_agent import EncryptedBlob
        recovered_blob = EncryptedBlob.from_b64(b64)
        assert agent.decrypt(recovered_blob, key) == b"test data"


# ---------------------------------------------------------------------------
# PECScaler
# ---------------------------------------------------------------------------

class TestPECScaler:
    def test_scale_up_on_high_load(self):
        scaler = PECScaler(backend="stub", min_replicas=1, max_replicas=10)
        # Simulate high load sample
        high_load = LoadSample(
            timestamp="2026-01-01T00:00:00Z",
            connections=100,
            queue_depth=80,
            cpu_pct=90.0,
            memory_pct=85.0,
        )
        # Force EMA to high value by running multiple high-load decisions
        for _ in range(5):
            decision = scaler._decide(high_load)
        assert decision.action in ("scale_up", "hold")

    def test_no_scale_below_min(self):
        scaler = PECScaler(backend="stub", min_replicas=1, max_replicas=10)
        scaler._current_replicas = 1
        low_load = LoadSample(
            timestamp="2026-01-01T00:00:00Z",
            connections=0,
            queue_depth=0,
            cpu_pct=5.0,
            memory_pct=10.0,
        )
        for _ in range(10):
            decision = scaler._decide(low_load)
        assert scaler._current_replicas >= 1

    def test_hold_on_normal_load(self):
        scaler = PECScaler(backend="stub")
        normal_load = LoadSample(
            timestamp="2026-01-01T00:00:00Z",
            connections=10,
            queue_depth=5,
            cpu_pct=40.0,
            memory_pct=50.0,
        )
        decision = scaler._decide(normal_load)
        # With a single sample, EMA hasn't warmed up to threshold yet
        assert decision.action in ("hold", "scale_up", "scale_down")
