"""
EvoP-Security Test Suite: EventTap + aintercept
"""
import sys, os, json, asyncio, tempfile
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')))

from PROVOCATEUR.AEGIS.core.event_tap import EventTap


async def _ok():
    return {"ok": True}


async def _fail():
    raise ValueError("test_error")


def test_ndjson_write():
    with tempfile.NamedTemporaryFile(mode='w', suffix='.ndjson', delete=False) as f:
        path = f.name

    tap = EventTap(ndjson_path=path)
    asyncio.run(tap.aintercept(_ok, origin="test", provider="test_prov", intent="unit_test"))

    with open(path, 'r') as f:
        lines = f.read().strip().splitlines()

    assert len(lines) >= 1
    obj = json.loads(lines[-1])
    assert obj["origin"] == "test"
    assert obj["status"] == "allowed"
    assert obj["provider"] == "test_prov"
    os.unlink(path)
    print("[PASS] test_ndjson_write")


def test_aintercept_error_capture():
    with tempfile.NamedTemporaryFile(mode='w', suffix='.ndjson', delete=False) as f:
        path = f.name

    tap = EventTap(ndjson_path=path)
    try:
        asyncio.run(tap.aintercept(_fail, origin="test", provider="err", intent="fail_test"))
    except ValueError:
        pass  # expected

    with open(path, 'r') as f:
        lines = f.read().strip().splitlines()

    obj = json.loads(lines[-1])
    assert obj["status"] == "error"
    assert "ValueError" in obj["meta"]["error"]
    os.unlink(path)
    print("[PASS] test_aintercept_error_capture")


def test_log_simple():
    with tempfile.NamedTemporaryFile(mode='w', suffix='.ndjson', delete=False) as f:
        path = f.name

    tap = EventTap(ndjson_path=path)
    tap.log_simple(origin="api", intent="access", status="allowed", details="GET /test")

    with open(path, 'r') as f:
        lines = f.read().strip().splitlines()

    obj = json.loads(lines[-1])
    assert obj["origin"] == "api"
    assert obj["meta"]["details"] == "GET /test"
    os.unlink(path)
    print("[PASS] test_log_simple")


if __name__ == "__main__":
    test_ndjson_write()
    test_aintercept_error_capture()
    test_log_simple()
    print("\n[SUCCESS] All EventTap tests passed!")
