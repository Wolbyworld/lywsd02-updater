# Regression check: real Tk mainloop and scan result processing, no Bluetooth I/O.
import asyncio
import runpy
import threading
from types import SimpleNamespace
from pathlib import Path
m = runpy.run_path(str(Path(__file__).with_name("main.py")))
main_thread = threading.get_ident()
root = m["tk"].Tk()
root.withdraw()
app = m["LYWSD02SyncApp"](root)
errors = []
calls = []
original_log = app.log
def log(message):
    assert threading.get_ident() == main_thread, "Tk log called outside main thread"
    original_log(message)
app.log = log
ids = ["11111111-1111-1111-1111-111111111111", "22222222-2222-2222-2222-222222222222"]
async def discover(*args, **kwargs):
    assert threading.get_ident() == main_thread, "Scan coroutine outside main thread"
    calls.append(True)
    await asyncio.sleep(0.05)
    return {identifier: (SimpleNamespace(address=identifier, name="LYWSD02 test " + str(i)),
                        SimpleNamespace(local_name="LYWSD02 test " + str(i), service_uuids=[], service_data={}))
            for i, identifier in enumerate(ids)}
m["BleakScanner"].discover = discover
def exception(exc_type, exc, tb):
    errors.append(repr(exc))
    app.close_app()
root.report_callback_exception = exception
def finish():
    try:
        assert len(calls) == 3, calls
        assert len(app.lywsd02_devices) == 2
        app.search_var.set("test 1")
        app.lywsd02_listbox.selection_set(0)
        assert app.get_selected_device()["address"] == ids[1], "Filtered selection selected another device"
        assert threading.get_ident() == main_thread
        print("PASS: three scan completions, Tk logs on main thread, filtered device identity, clean shutdown", flush=True)
    except Exception as exc:
        errors.append(repr(exc))
    finally:
        app.close_app()
for delay in [100, 500, 900]:
    root.after(delay, lambda: app.start_scan(duration=0.05))
root.after(1600, finish)
root.mainloop()
if errors:
    raise RuntimeError(errors)
print("NO BLUETOOTH ACCESS OR DEVICE WRITES WERE USED", flush=True)
