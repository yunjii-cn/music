import sys
import os
import traceback
from datetime import datetime

_RTH_LOG = None

def _rth_log(msg):
    global _RTH_LOG
    if _RTH_LOG is None:
        try:
            if hasattr(sys, 'frozen'):
                log_dir = os.path.dirname(sys.executable)
            else:
                log_dir = os.path.dirname(os.path.abspath(__file__))
            _RTH_LOG = open(os.path.join(log_dir, "rth_debug.log"), "a", encoding="utf-8")
        except Exception:
            return
    try:
        ts = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        _RTH_LOG.write(f"[{ts}] {msg}\n")
        _RTH_LOG.flush()
    except Exception:
        pass

if sys.platform == 'win32':
    try:
        import ctypes
        ctypes.windll.kernel32.FreeConsole()
        _rth_log("FreeConsole called in rth")
    except Exception as e:
        _rth_log(f"FreeConsole failed in rth: {e}")

    import subprocess as _subprocess

    def _ensure_hidden(kwargs):
        si = kwargs.get('startupinfo', None)
        if si is None:
            si = _subprocess.STARTUPINFO()
        si.dwFlags |= _subprocess.STARTF_USESHOWWINDOW
        si.wShowWindow = 0
        kwargs['startupinfo'] = si
        flags = _subprocess.CREATE_NO_WINDOW
        if hasattr(_subprocess, 'DETACHED_PROCESS'):
            flags |= _subprocess.DETACHED_PROCESS
        if hasattr(_subprocess, 'CREATE_NEW_PROCESS_GROUP'):
            flags |= _subprocess.CREATE_NEW_PROCESS_GROUP
        if 'creationflags' in kwargs:
            kwargs['creationflags'] = kwargs['creationflags'] | flags
        else:
            kwargs['creationflags'] = flags
        return kwargs

    _orig_popen_init = _subprocess.Popen.__init__
    def _patched_popen_init(self, *args, **kwargs):
        cmd = args[0] if args else kwargs.get('args', '?')
        caller = ''.join(traceback.format_stack()[-4:-1])
        _rth_log(f"RTH Popen: {cmd}\nCaller:\n{caller}")
        kwargs = _ensure_hidden(kwargs)
        _orig_popen_init(self, *args, **kwargs)
    _subprocess.Popen.__init__ = _patched_popen_init

    _orig_run = _subprocess.run
    def _patched_run(*args, **kwargs):
        cmd = args[0] if args else kwargs.get('args', '?')
        caller = ''.join(traceback.format_stack()[-4:-1])
        _rth_log(f"RTH run: {cmd}\nCaller:\n{caller}")
        kwargs = _ensure_hidden(kwargs)
        return _orig_run(*args, **kwargs)
    _subprocess.run = _patched_run

    _orig_call = _subprocess.call
    def _patched_call(*args, **kwargs):
        cmd = args[0] if args else kwargs.get('args', '?')
        _rth_log(f"RTH call: {cmd}")
        kwargs = _ensure_hidden(kwargs)
        return _orig_call(*args, **kwargs)
    _subprocess.call = _patched_call

    _orig_check_call = _subprocess.check_call
    def _patched_check_call(*args, **kwargs):
        cmd = args[0] if args else kwargs.get('args', '?')
        _rth_log(f"RTH check_call: {cmd}")
        kwargs = _ensure_hidden(kwargs)
        return _orig_check_call(*args, **kwargs)
    _subprocess.check_call = _patched_check_call

    _orig_check_output = _subprocess.check_output
    def _patched_check_output(*args, **kwargs):
        cmd = args[0] if args else kwargs.get('args', '?')
        _rth_log(f"RTH check_output: {cmd}")
        kwargs = _ensure_hidden(kwargs)
        return _orig_check_output(*args, **kwargs)
    _subprocess.check_output = _patched_check_output

_rth_log("pyi_rth_subprocess loaded, patches applied")
