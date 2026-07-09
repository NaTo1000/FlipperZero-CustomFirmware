"""Tests for build_configs/fbt_options.py and fbt_options_local.py.

Run with:
    python -m pytest tests/test_fbt_options.py -v
"""

import importlib.util
import os
import sys
import tempfile
from pathlib import Path
from types import ModuleType
from unittest import mock

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_BASE_CONFIG = Path(__file__).parents[1] / "build_configs" / "fbt_options.py"
_LOCAL_CONFIG = Path(__file__).parents[1] / "fbt_options_local.py"


def _load_fbt_options(tmpdir: Path, local_content: str = "") -> ModuleType:
    """
    Copy fbt_options.py into *tmpdir*, optionally write a local override file
    alongside it, then import and return the module.
    """
    config_path = tmpdir / "fbt_options.py"
    config_path.write_text(_BASE_CONFIG.read_text(encoding="utf-8"), encoding="utf-8")

    if local_content:
        local_path = tmpdir / "fbt_options_local.py"
        local_path.write_text(local_content, encoding="utf-8")

    # Remove any cached version so each test gets a fresh module.
    sys.modules.pop("fbt_options", None)

    spec = importlib.util.spec_from_file_location("fbt_options", config_path)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["fbt_options"] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)  # type: ignore[union-attr]
    return module


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_defaults(tmp_path: Path) -> None:
    """fbt_options.py loads with correct default values and passes validation."""
    mod = _load_fbt_options(tmp_path)

    assert mod.FIRMWARE_ORIGIN == "NaTo1000-Custom"
    assert mod.TARGET_HW == 7
    assert mod.COMPACT == 0
    assert mod.DEBUG == 1
    assert mod.LOADER_AUTOSTART == "Autostart Test"
    assert mod.COPRO_STACK_BIN == "stm32wb5x_BLE_Stack_light_fw.bin"
    assert mod.COPRO_STACK_TYPE == "ble_light"
    assert mod.FIRMWARE_APP_SET in mod.FIRMWARE_APPS
    assert mod.FIRMWARE_APP_SET == "default"


def test_local_override_applied(tmp_path: Path) -> None:
    """Local fbt_options_local.py overrides are picked up correctly."""
    local = (
        'LOADER_AUTOSTART = "Local App"\n'
        'FIRMWARE_APP_SET = "minimal"\n'
        'FIRMWARE_ORIGIN = "LocalDev"\n'
    )
    mod = _load_fbt_options(tmp_path, local_content=local)

    assert mod.LOADER_AUTOSTART == "Local App"
    assert mod.FIRMWARE_APP_SET == "minimal"
    assert mod.FIRMWARE_ORIGIN == "LocalDev"


def test_local_override_unknown_key_ignored(tmp_path: Path) -> None:
    """Variables not on the whitelist must not leak into fbt_options."""
    local = 'SNEAKY_VAR = "should not appear"\n'
    mod = _load_fbt_options(tmp_path, local_content=local)

    assert not hasattr(mod, "SNEAKY_VAR")


def test_invalid_app_set_raises(tmp_path: Path) -> None:
    """An invalid FIRMWARE_APP_SET in the local file raises a clear ValueError."""
    local = 'FIRMWARE_APP_SET = "does_not_exist"\n'

    try:
        _load_fbt_options(tmp_path, local_content=local)
    except ValueError as exc:
        assert "does_not_exist" in str(exc)
    else:
        raise AssertionError("Expected ValueError for invalid FIRMWARE_APP_SET")


def test_invalid_app_set_in_base_raises(tmp_path: Path) -> None:
    """Patching FIRMWARE_APP_SET directly to an invalid value raises ValueError."""
    # Write a base config with a bad app set to simulate misconfiguration.
    bad_config = _BASE_CONFIG.read_text(encoding="utf-8").replace(
        "FIRMWARE_APP_SET: str = APP_SET_DEFAULT",
        'FIRMWARE_APP_SET: str = "bad_set"',
    )
    config_path = tmp_path / "fbt_options.py"
    config_path.write_text(bad_config, encoding="utf-8")

    sys.modules.pop("fbt_options", None)
    spec = importlib.util.spec_from_file_location("fbt_options", config_path)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)

    try:
        assert spec.loader is not None
        spec.loader.exec_module(module)  # type: ignore[union-attr]
    except ValueError as exc:
        assert "bad_set" in str(exc)
    else:
        raise AssertionError("Expected ValueError for invalid FIRMWARE_APP_SET in base")


def test_selftest_runs(tmp_path: Path, capsys) -> None:
    """Self-test mode prints expected diagnostic output."""
    # Copy the real local config into the temp dir so fbt_options.py finds it.
    local_content = _LOCAL_CONFIG.read_text(encoding="utf-8")
    (tmp_path / "fbt_options_local.py").write_text(local_content, encoding="utf-8")

    with mock.patch.dict(os.environ, {"FW_OPTIONS_SELFTEST": "1"}):
        _load_fbt_options(tmp_path, local_content=local_content)

    captured = capsys.readouterr()
    assert "[fbt_options_local] Self-test started" in captured.out
    assert "[fbt_options_local] Self-test finished" in captured.out


def test_selftest_quiet_by_default(tmp_path: Path, capsys) -> None:
    """Self-test must NOT run when FW_OPTIONS_SELFTEST is absent."""
    local_content = _LOCAL_CONFIG.read_text(encoding="utf-8")

    env = {k: v for k, v in os.environ.items() if k != "FW_OPTIONS_SELFTEST"}
    with mock.patch.dict(os.environ, env, clear=True):
        _load_fbt_options(tmp_path, local_content=local_content)

    captured = capsys.readouterr()
    assert "[fbt_options_local] Self-test started" not in captured.out


if __name__ == "__main__":
    # Minimal runner for environments without pytest.
    import tempfile

    tests = [
        test_defaults,
        test_local_override_applied,
        test_local_override_unknown_key_ignored,
        test_invalid_app_set_raises,
        test_invalid_app_set_in_base_raises,
    ]

    passed = 0
    failed = 0
    for fn in tests:
        with tempfile.TemporaryDirectory() as td:
            try:
                fn(Path(td))
                print(f"PASS: {fn.__name__}")
                passed += 1
            except Exception as exc:
                print(f"FAIL: {fn.__name__} – {exc}")
                failed += 1

    print(f"\n{passed} passed, {failed} failed.")
    if failed:
        sys.exit(1)
