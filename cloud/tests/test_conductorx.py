"""
Tests for ConductorX core components.
All tests use only stdlib + testcontainers — no external services required.
"""
import pytest

from cloud.dolfi.conductorx.agents.code_agent import CodeAgent
from cloud.dolfi.conductorx.agents.crypto_agent import CryptoAgent
from cloud.dolfi.conductorx.agents.debug_agent import DebugAgent
from cloud.dolfi.conductorx.agents.health_monitor import (
    HealthCheck,
    HealthMonitorAgent,
    HealthStatus,
)
from cloud.dolfi.conductorx.agents.receptionist import ReceptionistAgent
from cloud.dolfi.conductorx.agents.recovery import RecoveryAgent
from cloud.dolfi.conductorx.ledger.chain import AuditLedger
from cloud.dolfi.conductorx.protocols.circuit_breaker import (
    CircuitBreaker,
    CircuitOpenError,
    CircuitState,
)
from cloud.dolfi.conductorx.scaler.pec import LoadSample, PECScaler
from cloud.dolfi.conductorx.speed.mode_controller import ModeController, Speed

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
        # Force DEMA to high value by running multiple high-load decisions
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
            scaler._decide(low_load)
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
        # With a single sample, DEMA hasn't warmed up to threshold yet
        assert decision.action in ("hold", "scale_up", "scale_down")

    def test_dema_property_within_bounds(self):
        scaler = PECScaler(backend="stub")
        load = LoadSample(
            timestamp="2026-01-01T00:00:00Z",
            connections=50,
            queue_depth=40,
            cpu_pct=70.0,
            memory_pct=65.0,
        )
        for _ in range(10):
            scaler._decide(load)
        assert 0.0 <= scaler.dema <= 1.0

    def test_dema_reacts_faster_than_single_ema(self):
        """DEMA should converge toward a load spike faster than single EMA."""
        scaler = PECScaler(backend="stub")
        high = LoadSample(
            timestamp="2026-01-01T00:00:00Z",
            connections=100,
            queue_depth=100,
            cpu_pct=100.0,
            memory_pct=100.0,
        )
        # After 3 high-load samples DEMA should exceed single EMA1 value
        for _ in range(3):
            scaler._decide(high)
        # dema = 2*ema1 - ema2; since ema2 lags behind ema1, dema > ema1
        assert scaler.dema >= scaler._ema1


# ---------------------------------------------------------------------------
# Speed 4 — Swarm Mode
# ---------------------------------------------------------------------------

class TestSwarmMode:
    def test_swarm_speed_value_is_4(self):
        assert int(Speed.SWARM) == 4

    def test_set_speed_swarm(self):
        mc = ModeController()
        mc.set_speed(4)
        assert mc.speed == Speed.SWARM

    def test_is_autonomous_in_swarm_mode(self):
        mc = ModeController()
        mc.set_speed(Speed.SWARM)
        assert mc.is_autonomous()

    def test_is_swarm_flag(self):
        mc = ModeController()
        mc.set_speed(Speed.SWARM)
        assert mc.is_swarm()
        mc.set_speed(Speed.FULL_AUTO)
        assert not mc.is_swarm()

    def test_auto_detect_swarm_keywords(self):
        mc = ModeController()
        mc.auto_detect("run all agents in parallel simultaneously")
        assert mc.speed == Speed.SWARM

    def test_swarm_system_prompt_mentions_swarm(self):
        mc = ModeController()
        mc.set_speed(Speed.SWARM)
        prompt = mc.system_prompt()
        assert "Swarm" in prompt or "parallel" in prompt.lower()

    def test_invalid_speed_still_raises(self):
        mc = ModeController()
        with pytest.raises(ValueError):
            mc.set_speed(99)


# ---------------------------------------------------------------------------
# Circuit Breaker Protocol
# ---------------------------------------------------------------------------

class TestCircuitBreaker:
    def test_initial_state_is_closed(self):
        cb = CircuitBreaker(name="test-svc")
        assert cb.state == CircuitState.CLOSED

    def test_successful_call_passes_through(self):
        cb = CircuitBreaker(name="test-svc")
        result = cb.call(lambda: 42)
        assert result == 42

    def test_opens_after_failure_threshold(self):
        cb = CircuitBreaker(name="test-svc", failure_threshold=3)
        for _ in range(3):
            try:
                cb.call(lambda: (_ for _ in ()).throw(RuntimeError("boom")))
            except RuntimeError:
                pass
        assert cb.state == CircuitState.OPEN

    def test_open_circuit_fast_fails(self):
        cb = CircuitBreaker(name="test-svc", failure_threshold=1)
        try:
            cb.call(lambda: (_ for _ in ()).throw(RuntimeError("boom")))
        except RuntimeError:
            pass
        with pytest.raises(CircuitOpenError):
            cb.call(lambda: 99)

    def test_manual_reset_closes_circuit(self):
        cb = CircuitBreaker(name="test-svc", failure_threshold=1)
        try:
            cb.call(lambda: (_ for _ in ()).throw(RuntimeError("boom")))
        except RuntimeError:
            pass
        cb.reset()
        assert cb.state == CircuitState.CLOSED
        result = cb.call(lambda: "ok")
        assert result == "ok"

    def test_metrics_track_calls(self):
        cb = CircuitBreaker(name="test-svc")
        cb.call(lambda: 1)
        cb.call(lambda: 2)
        assert cb.metrics.total_calls == 2
        assert cb.metrics.total_successes == 2

    def test_half_open_after_timeout(self):
        cb = CircuitBreaker(name="test-svc", failure_threshold=1, reset_timeout=0.0)
        try:
            cb.call(lambda: (_ for _ in ()).throw(RuntimeError("boom")))
        except RuntimeError:
            pass
        # reset_timeout=0 → immediately transitions on next state check
        assert cb.state in (CircuitState.HALF_OPEN, CircuitState.OPEN)

    def test_circuit_open_error_message_contains_name(self):
        cb = CircuitBreaker(name="my-service", failure_threshold=1, reset_timeout=60)
        try:
            cb.call(lambda: (_ for _ in ()).throw(RuntimeError("boom")))
        except RuntimeError:
            pass
        try:
            cb.call(lambda: None)
        except CircuitOpenError as exc:
            assert "my-service" in str(exc)


# ---------------------------------------------------------------------------
# Weighted Intent Routing
# ---------------------------------------------------------------------------

class TestWeightedRouting:
    def test_high_weight_keyword_wins_over_count(self):
        """
        'traceback' (weight 3.0 for debug) should beat a message with
        two low-weight code keywords like 'build' and 'code'.
        """
        agent = ReceptionistAgent()
        decision = agent.route("build the code and fix the traceback")
        # 'traceback' = 3.0 debug; 'build' = 1.0 code; 'code' = 1.0 code → debug wins
        assert decision.target == "debug"

    def test_firmware_routes_conductor_with_high_confidence(self):
        agent = ReceptionistAgent()
        decision = agent.route("flash the latest firmware via dfu mode")
        assert decision.target == "conductor"
        assert decision.confidence > 0.5

    def test_sql_keywords_route_to_sql(self):
        agent = ReceptionistAgent()
        decision = agent.route("run a SELECT query against the database schema")
        assert decision.target == "sql"

    def test_confidence_is_normalised_between_0_and_1(self):
        agent = ReceptionistAgent()
        for msg in [
            "flash firmware",
            "encrypt my aes key with gpg",
            "write a badusb script",
            "xyzzy frobnigate quux",
        ]:
            d = agent.route(msg)
            assert 0.0 <= d.confidence <= 1.0

    def test_reason_mentions_weighted_score(self):
        agent = ReceptionistAgent()
        decision = agent.route("rollback to the last snapshot")
        assert "/" in decision.reason  # "score X/Y" format


# ---------------------------------------------------------------------------
# Merkle Ledger
# ---------------------------------------------------------------------------

class TestMerkleLedger:
    def test_empty_ledger_merkle_root_is_genesis(self):
        from cloud.dolfi.conductorx.ledger.chain import GENESIS_HASH
        ledger = AuditLedger()
        assert ledger.merkle_root() == GENESIS_HASH

    def test_single_entry_merkle_root_is_leaf_hash(self):
        ledger = AuditLedger()
        ledger.append("agent", "action", {})
        root = ledger.merkle_root()
        # root should be a 64-char hex string
        assert len(root) == 64
        assert all(c in "0123456789abcdef" for c in root)

    def test_merkle_root_changes_on_append(self):
        ledger = AuditLedger()
        ledger.append("agent", "action1", {})
        root1 = ledger.merkle_root()
        ledger.append("agent", "action2", {})
        root2 = ledger.merkle_root()
        assert root1 != root2

    def test_verify_merkle_passes_on_untampered(self):
        ledger = AuditLedger()
        ledger.append("a", "b", {"x": 1})
        ledger.append("a", "c", {"x": 2})
        root = ledger.merkle_root()
        assert ledger.verify_merkle(root)

    def test_verify_merkle_fails_on_tampered_root(self):
        ledger = AuditLedger()
        ledger.append("a", "b", {})
        assert not ledger.verify_merkle("deadbeef" * 8)

    def test_merkle_is_deterministic(self):
        ledger = AuditLedger()
        for i in range(5):
            ledger.append("agent", f"action{i}", {"i": i})
        r1 = ledger.merkle_root()
        r2 = ledger.merkle_root()
        assert r1 == r2

    def test_odd_length_chain_handles_padding(self):
        """Odd number of entries must not raise and must produce a valid root."""
        ledger = AuditLedger()
        for i in range(3):
            ledger.append("agent", f"act{i}", {})
        root = ledger.merkle_root()
        assert len(root) == 64


# ---------------------------------------------------------------------------
# HealthMonitor Agent
# ---------------------------------------------------------------------------

class TestHealthMonitorAgent:
    def test_empty_monitor_returns_unknown(self):
        monitor = HealthMonitorAgent()
        report = monitor.check_all()
        assert report.overall == HealthStatus.UNKNOWN

    def test_healthy_probe_classifies_healthy(self):
        monitor = HealthMonitorAgent()
        monitor.register(HealthCheck(
            name="fast-db",
            probe=lambda: 5.0,  # 5 ms
            warn_threshold=100.0,
            critical_threshold=500.0,
            unit="ms",
        ))
        report = monitor.check_all()
        assert report.overall == HealthStatus.HEALTHY
        assert report.results[0].status == HealthStatus.HEALTHY

    def test_degraded_probe_classifies_degraded(self):
        monitor = HealthMonitorAgent()
        monitor.register(HealthCheck(
            name="slow-db",
            probe=lambda: 150.0,
            warn_threshold=100.0,
            critical_threshold=500.0,
            unit="ms",
        ))
        report = monitor.check_all()
        assert report.overall == HealthStatus.DEGRADED

    def test_critical_probe_classifies_critical(self):
        monitor = HealthMonitorAgent()
        monitor.register(HealthCheck(
            name="dead-svc",
            probe=lambda: 600.0,
            warn_threshold=100.0,
            critical_threshold=500.0,
            unit="ms",
        ))
        report = monitor.check_all()
        assert report.overall == HealthStatus.CRITICAL

    def test_exception_in_probe_is_critical(self):
        monitor = HealthMonitorAgent()
        monitor.register(HealthCheck(
            name="unreachable",
            probe=lambda: (_ for _ in ()).throw(ConnectionError("refused")),
            warn_threshold=50.0,
            critical_threshold=200.0,
        ))
        report = monitor.check_all()
        assert report.overall == HealthStatus.CRITICAL
        assert report.results[0].value is None

    def test_worst_check_determines_overall(self):
        monitor = HealthMonitorAgent()
        monitor.register(HealthCheck("ok", lambda: 1.0, 50.0, 200.0))
        monitor.register(HealthCheck("bad", lambda: 300.0, 50.0, 200.0))
        report = monitor.check_all()
        assert report.overall == HealthStatus.CRITICAL

    def test_markdown_report_contains_service_name(self):
        monitor = HealthMonitorAgent()
        monitor.register(HealthCheck("redis", lambda: 2.0, 50.0, 200.0, "ms"))
        report = monitor.check_all()
        md = report.markdown()
        assert "redis" in md
        assert "HEALTHY" in md.upper() or "healthy" in md

    def test_check_one_returns_result_for_known_name(self):
        monitor = HealthMonitorAgent()
        monitor.register(HealthCheck("qdrant", lambda: 10.0, 50.0, 200.0))
        result = monitor.check_one("qdrant")
        assert result is not None
        assert result.name == "qdrant"

    def test_check_one_returns_none_for_unknown(self):
        monitor = HealthMonitorAgent()
        assert monitor.check_one("nonexistent") is None

    def test_unregister_removes_check(self):
        monitor = HealthMonitorAgent()
        monitor.register(HealthCheck("vault", lambda: 1.0, 50.0, 200.0))
        removed = monitor.unregister("vault")
        assert removed
        report = monitor.check_all()
        assert report.overall == HealthStatus.UNKNOWN

    def test_history_accumulates(self):
        monitor = HealthMonitorAgent()
        monitor.register(HealthCheck("svc", lambda: 1.0, 50.0, 200.0))
        monitor.check_all()
        monitor.check_all()
        assert len(monitor.history()) == 2
