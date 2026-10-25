"""Hardware-free regression checks; no Tk window or BLE adapter is used."""
import asyncio
import contextlib
import importlib.util
import io
import json
from pathlib import Path
import sys
import tempfile
import threading
import types
import unittest
from unittest.mock import patch


def load_app_module():
    bleak = types.ModuleType("bleak")
    bleak.BleakScanner = object
    bleak.BleakClient = object
    tkinter = types.ModuleType("tkinter")
    tkinter.ttk = types.SimpleNamespace()
    tkinter.messagebox = types.SimpleNamespace()
    spec = importlib.util.spec_from_file_location("clock_app", Path(__file__).resolve().parents[1] / "main.py")
    module = importlib.util.module_from_spec(spec)
    with patch.dict(sys.modules, {"bleak": bleak, "tkinter": tkinter}):
        spec.loader.exec_module(module)
    return module


APP = load_app_module()
FIRST = "11111111-1111-1111-1111-111111111111"
SECOND = "22222222-2222-2222-2222-222222222222"


class TargetConfigurationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name) / "devices.local.json"

    def write_config(self, value):
        self.path.write_text(json.dumps(value))

    def test_missing_config_does_not_choose_a_device(self):
        self.assertIsNone(APP.load_target_identifier(self.path, "test-mac"))

    def test_only_current_mac_mapping_is_used(self):
        self.write_config({"targets": {"test-mac": FIRST, "other-mac": SECOND}})
        self.assertEqual(APP.load_target_identifier(self.path, "Test-Mac.example.net"), FIRST)

    def test_unknown_host_does_not_reuse_another_mac_mapping(self):
        self.write_config({"targets": {"other-mac": SECOND}})
        self.assertIsNone(APP.load_target_identifier(self.path, "test-mac"))

    def test_invalid_uuid_disables_the_marker(self):
        self.write_config({"targets": {"test-mac": "not-a-device-uuid"}})
        with contextlib.redirect_stderr(io.StringIO()):
            self.assertIsNone(APP.load_target_identifier(self.path, "test-mac"))

    def test_malformed_config_disables_the_marker(self):
        self.path.write_text("{broken json")
        with contextlib.redirect_stderr(io.StringIO()):
            self.assertIsNone(APP.load_target_identifier(self.path, "test-mac"))


class Listbox:
    def __init__(self, rows=(), selected=()):
        self.rows = rows
        self.selected = selected

    def curselection(self):
        return self.selected

    def get(self, index):
        return self.rows[index]


class DeviceSelectionTests(unittest.TestCase):
    def setUp(self):
        self.app = APP.LYWSD02SyncApp.__new__(APP.LYWSD02SyncApp)
        self.app.lywsd02_devices = {FIRST: {"address": FIRST}, SECOND: {"address": SECOND}}
        self.app.other_devices = {}
        self.app.lywsd02_listbox = Listbox()
        self.app.other_listbox = Listbox()

    def test_filtered_first_row_resolves_visible_device(self):
        self.app.lywsd02_listbox = Listbox([f"LYWSD02 [{SECOND}]"], (0,))
        self.assertEqual(self.app.get_selected_device()["address"], SECOND)

    def test_marker_does_not_change_identifier_resolution(self):
        self.app.lywsd02_listbox = Listbox([f"🎯 LYWSD02 [{SECOND}]"], (0,))
        self.assertEqual(self.app.get_selected_device()["address"], SECOND)

    def test_no_selection_does_not_choose_a_device(self):
        self.assertIsNone(self.app.get_selected_device())


class EventLoopTests(unittest.TestCase):
    def test_async_tasks_run_on_the_thread_pumping_tk(self):
        app = APP.LYWSD02SyncApp.__new__(APP.LYWSD02SyncApp)
        app.loop = asyncio.new_event_loop()
        self.addCleanup(app.loop.close)
        app._closing = False
        callbacks = []
        app.root = types.SimpleNamespace(after=lambda delay, callback: callbacks.append((delay, callback)))
        observed_threads = []

        async def task():
            observed_threads.append(threading.get_ident())
            await asyncio.sleep(0)
            observed_threads.append(threading.get_ident())

        app.loop.create_task(task())
        for _ in range(3):
            app.start_loop()
        self.assertEqual(observed_threads, [threading.get_ident()] * 2)
        self.assertEqual(len(callbacks), 3)
        self.assertTrue(all(delay == 10 for delay, _ in callbacks))


if __name__ == "__main__":
    unittest.main()
