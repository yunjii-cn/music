import sys
import os
import traceback
from datetime import datetime

_SUBPROCESS_LOG = None

def _log_subprocess(msg):
    global _SUBPROCESS_LOG
    if _SUBPROCESS_LOG is None:
        try:
            if hasattr(sys, 'frozen'):
                log_dir = os.path.dirname(sys.executable)
            else:
                log_dir = os.path.dirname(os.path.abspath(__file__))
                parent = os.path.dirname(log_dir)
                log_dir = parent
            _SUBPROCESS_LOG = open(os.path.join(log_dir, "subprocess_debug.log"), "a", encoding="utf-8")
        except Exception:
            return
    try:
        ts = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        _SUBPROCESS_LOG.write(f"[{ts}] {msg}\n")
        _SUBPROCESS_LOG.flush()
    except Exception:
        pass

if sys.platform == 'win32':
    try:
        import ctypes
        ctypes.windll.kernel32.FreeConsole()
        _log_subprocess("FreeConsole called successfully")
    except Exception as e:
        _log_subprocess(f"FreeConsole failed: {e}")

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
        _log_subprocess(f"Popen called: {cmd}\nCaller:\n{caller}")
        kwargs = _ensure_hidden(kwargs)
        _orig_popen_init(self, *args, **kwargs)
    _subprocess.Popen.__init__ = _patched_popen_init

    _orig_run = _subprocess.run
    def _patched_run(*args, **kwargs):
        cmd = args[0] if args else kwargs.get('args', '?')
        caller = ''.join(traceback.format_stack()[-4:-1])
        _log_subprocess(f"run called: {cmd}\nCaller:\n{caller}")
        kwargs = _ensure_hidden(kwargs)
        return _orig_run(*args, **kwargs)
    _subprocess.run = _patched_run

    _orig_call = _subprocess.call
    def _patched_call(*args, **kwargs):
        cmd = args[0] if args else kwargs.get('args', '?')
        _log_subprocess(f"call called: {cmd}")
        kwargs = _ensure_hidden(kwargs)
        return _orig_call(*args, **kwargs)
    _subprocess.call = _patched_call

    _orig_check_call = _subprocess.check_call
    def _patched_check_call(*args, **kwargs):
        cmd = args[0] if args else kwargs.get('args', '?')
        _log_subprocess(f"check_call called: {cmd}")
        kwargs = _ensure_hidden(kwargs)
        return _orig_check_call(*args, **kwargs)
    _subprocess.check_call = _patched_check_call

    _orig_check_output = _subprocess.check_output
    def _patched_check_output(*args, **kwargs):
        cmd = args[0] if args else kwargs.get('args', '?')
        _log_subprocess(f"check_output called: {cmd}")
        kwargs = _ensure_hidden(kwargs)
        return _orig_check_output(*args, **kwargs)
    _subprocess.check_output = _patched_check_output

_log_subprocess("launcher.py loaded, subprocess patches applied")

import main
main.main()
