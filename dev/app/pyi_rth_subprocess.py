import sys
import os
import traceback

_LOG_FILE = None

def _get_log_path():
    global _LOG_FILE
    if _LOG_FILE is not None:
        return _LOG_FILE
    try:
        if hasattr(sys, '_MEIPASS'):
            base = os.path.dirname(sys.executable)
        else:
            base = os.path.dirname(os.path.abspath(__file__))
        _LOG_FILE = os.path.join(base, "subprocess_debug.log")
    except Exception:
        _LOG_FILE = os.path.join(os.environ.get('TEMP', '.'), "subprocess_debug.log")
    return _LOG_FILE

def _log_subprocess_call(method, args, kwargs):
    try:
        cmd = ""
        if args:
            cmd = str(args[0])[:200]
        elif 'args' in kwargs:
            cmd = str(kwargs['args'])[:200]
        stack = ''.join(traceback.format_stack()[-6:-1])
        with open(_get_log_path(), 'a', encoding='utf-8') as f:
            f.write(f"\n{'='*60}\n")
            f.write(f"[{method}] CMD: {cmd}\n")
            f.write(f"CALL STACK:\n{stack}\n")
    except Exception:
        pass

if sys.platform == 'win32':
    try:
        import ctypes
        ctypes.windll.kernel32.FreeConsole()
    except Exception:
        pass

    try:
        with open(_get_log_path(), 'w', encoding='utf-8') as f:
            f.write(f"=== subprocess debug log started ===\n")
    except Exception:
        pass

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
        _log_subprocess_call('Popen.__init__', args, kwargs)
        kwargs = _ensure_hidden(kwargs)
        _orig_popen_init(self, *args, **kwargs)
    _subprocess.Popen.__init__ = _patched_popen_init

    _orig_run = _subprocess.run
    def _patched_run(*args, **kwargs):
        _log_subprocess_call('subprocess.run', args, kwargs)
        kwargs = _ensure_hidden(kwargs)
        return _orig_run(*args, **kwargs)
    _subprocess.run = _patched_run

    _orig_call = _subprocess.call
    def _patched_call(*args, **kwargs):
        _log_subprocess_call('subprocess.call', args, kwargs)
        kwargs = _ensure_hidden(kwargs)
        return _orig_call(*args, **kwargs)
    _subprocess.call = _patched_call

    _orig_check_call = _subprocess.check_call
    def _patched_check_call(*args, **kwargs):
        _log_subprocess_call('subprocess.check_call', args, kwargs)
        kwargs = _ensure_hidden(kwargs)
        return _orig_check_call(*args, **kwargs)
    _subprocess.check_call = _patched_check_call

    _orig_check_output = _subprocess.check_output
    def _patched_check_output(*args, **kwargs):
        _log_subprocess_call('subprocess.check_output', args, kwargs)
        kwargs = _ensure_hidden(kwargs)
        return _orig_check_output(*args, **kwargs)
    _subprocess.check_output = _patched_check_output
