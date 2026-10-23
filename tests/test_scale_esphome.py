"""Regression tests for scan-only ESPHome Bluetooth Proxy integration."""

import asyncio
import sys
from types import ModuleType, SimpleNamespace

import pytest

from app.scale import BODY_COMPOSITION, ScaleListener, parse

ADDRESS = "0C:95:41:BA:FC:C1"
PACKET = bytes([0, 0x22, 0xEA, 0x07, 10, 23, 12, 34, 56, 0xBC, 0x01, 0xE8, 0x67])


def setup_mocks(monkeypatch, *, connection_fails=False):
    recorder = SimpleNamespace(mgr=None, subscription=None, events=[], conn=None)

    class BluetoothManager:
        def __init__(self):
            recorder.mgr = self
            self.unsubscribed = False
            self.stopped = False

        async def async_setup(self):
            recorder.events.append("bluetooth_setup")

        def async_register_advertisement_callback(self, callback, address):
            assert address == ADDRESS
            self.callback = callback
            recorder.subscription = address
            recorder.events.append("subscribed")

            def unsubscribe():
                self.unsubscribed = True
                recorder.events.append("unsubscribed")

            return unsubscribe

        def async_stop(self):
            self.stopped = True
            recorder.events.append("bluetooth_stop")

    class APIConnectionManager:
        def __init__(self, config):
            recorder.conn = self
            self.config = config
            self.stopped = False

        async def start(self):
            recorder.events.append("proxy_start")
            if connection_fails:
                raise ConnectionRefusedError("proxy unreachable")
            assert recorder.subscription == ADDRESS
            info = SimpleNamespace(
                address=ADDRESS, name="MIBFS", rssi=-52,
                service_data={BODY_COMPOSITION: PACKET}, manufacturer_data={},
                service_uuids=[BODY_COMPOSITION],
            )
            recorder.mgr.callback(info)
            recorder.mgr.callback(info)

        async def stop(self):
            self.stopped = True
            recorder.events.append("proxy_stop")

    hab = ModuleType("habluetooth")
    hab.BluetoothManager = BluetoothManager
    hab.get_manager = lambda: recorder.mgr
    esphome = ModuleType("bleak_esphome")
    esphome.APIConnectionManager = APIConnectionManager
    monkeypatch.setitem(sys.modules, "habluetooth", hab)
    monkeypatch.setitem(sys.modules, "bleak_esphome", esphome)
    return recorder


def test_packet_decoding():
    p = parse(PACKET)
    assert p.weight_kg == 133.0
    assert p.impedance == 444
    assert p.stabilized is True


def test_passive_proxy_and_cleanup(monkeypatch):
    recorder = setup_mocks(monkeypatch)
    monkeypatch.setenv("MISCALE_ESPHOME_HOST", "192.168.88.52")
    monkeypatch.setenv("MISCALE_ESPHOME_API_KEY", "testing-key")
    readings = []
    listener = ScaleListener(readings.append, ADDRESS.lower())

    async def run():
        task = asyncio.create_task(listener.run())
        for _ in range(100):
            if readings:
                break
            await asyncio.sleep(0.005)
        assert len(readings) == 1
        assert readings[0].weight_kg == 133.0
        assert readings[0].impedance == 444
        assert readings[0].rssi == -52
        assert recorder.conn.config == {"address": "192.168.88.52", "noise_psk": "testing-key"}
        assert listener.error is None
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task

    asyncio.run(run())
    assert recorder.conn.stopped
    assert recorder.mgr.unsubscribed
    assert recorder.mgr.stopped
    assert "proxy_start" in recorder.events


def test_missing_scale_mac(monkeypatch):
    recorder = setup_mocks(monkeypatch)
    listener = ScaleListener(lambda _: None)
    asyncio.run(listener.run_esphome())
    assert "MISCALE_SCALE_MAC" in listener.error
    assert recorder.mgr is None


def test_connection_failure_sets_error_and_stops(monkeypatch):
    recorder = setup_mocks(monkeypatch, connection_fails=True)
    monkeypatch.setenv("MISCALE_ESPHOME_HOST", "192.168.88.52")
    listener = ScaleListener(lambda _: None, ADDRESS)

    async def run():
        task = asyncio.create_task(listener.run_esphome())
        for _ in range(100):
            if listener.error:
                break
            await asyncio.sleep(0.005)
        assert "proxy unreachable" in listener.error
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task

    asyncio.run(run())
    assert recorder.mgr.unsubscribed
    assert recorder.mgr.stopped


def test_local_ble_path_unchanged(monkeypatch):
    monkeypatch.delenv("MISCALE_ESPHOME_HOST", raising=False)
    import inspect

    assert 'scanning_mode="active"' in inspect.getsource(ScaleListener.run)
