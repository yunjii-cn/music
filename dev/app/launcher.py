import sys
import os

if sys.platform == 'win32':
    try:
        import ctypes
        ctypes.windll.kernel32.FreeConsole()
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
        kwargs = _ensure_hidden(kwargs)
        _orig_popen_init(self, *args, **kwargs)
    _subprocess.Popen.__init__ = _patched_popen_init

    _orig_run = _subprocess.run
    def _patched_run(*args, **kwargs):
        kwargs = _ensure_hidden(kwargs)
        return _orig_run(*args, **kwargs)
    _subprocess.run = _patched_run

    _orig_call = _subprocess.call
    def _patched_call(*args, **kwargs):
        kwargs = _ensure_hidden(kwargs)
        return _orig_call(*args, **kwargs)
    _subprocess.call = _patched_call

    _orig_check_call = _subprocess.check_call
    def _patched_check_call(*args, **kwargs):
        kwargs = _ensure_hidden(kwargs)
        return _orig_check_call(*args, **kwargs)
    _subprocess.check_call = _patched_check_call

    _orig_check_output = _subprocess.check_output
    def _patched_check_output(*args, **kwargs):
        kwargs = _ensure_hidden(kwargs)
        return _orig_check_output(*args, **kwargs)
    _subprocess.check_output = _patched_check_output

try:
    import pyi_splash
    pyi_splash.update_text("正在加载模块...")
except Exception:
    pass

import main
main.main()
