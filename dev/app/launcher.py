import sys
import os

if sys.platform == 'win32':
    import subprocess as _subprocess
    import traceback as _traceback

    _log_path = os.path.join(os.path.dirname(os.path.abspath(sys.executable if hasattr(sys, 'frozen') else __file__)), 'subprocess_debug.log')

    _orig_popen_init = _subprocess.Popen.__init__

    def _patched_popen_init(self, *args, **kwargs):
        try:
            with open(_log_path, 'a', encoding='utf-8') as f:
                f.write(f"[Popen] args={args[:1]} creationflags={kwargs.get('creationflags', 'NONE')} startupinfo={kwargs.get('startupinfo', 'NONE')}\n")
                for line in _traceback.format_stack()[-5:-1]:
                    f.write(line)
                f.write("---\n")
        except Exception:
            pass

        si = kwargs.get('startupinfo', None)
        if si is None:
            si = _subprocess.STARTUPINFO()
        si.dwFlags |= _subprocess.STARTF_USESHOWWINDOW
        si.wShowWindow = 0
        kwargs['startupinfo'] = si
        if 'creationflags' in kwargs:
            kwargs['creationflags'] = kwargs['creationflags'] | _subprocess.CREATE_NO_WINDOW
        else:
            kwargs['creationflags'] = _subprocess.CREATE_NO_WINDOW
        _orig_popen_init(self, *args, **kwargs)

    _subprocess.Popen.__init__ = _patched_popen_init

    _orig_run = _subprocess.run

    def _patched_run(*args, **kwargs):
        try:
            with open(_log_path, 'a', encoding='utf-8') as f:
                f.write(f"[run] args={args[:1]} creationflags={kwargs.get('creationflags', 'NONE')}\n")
                for line in _traceback.format_stack()[-5:-1]:
                    f.write(line)
                f.write("---\n")
        except Exception:
            pass

        si = kwargs.get('startupinfo', None)
        if si is None:
            si = _subprocess.STARTUPINFO()
        si.dwFlags |= _subprocess.STARTF_USESHOWWINDOW
        si.wShowWindow = 0
        kwargs['startupinfo'] = si
        if 'creationflags' in kwargs:
            kwargs['creationflags'] = kwargs['creationflags'] | _subprocess.CREATE_NO_WINDOW
        else:
            kwargs['creationflags'] = _subprocess.CREATE_NO_WINDOW
        return _orig_run(*args, **kwargs)

    _subprocess.run = _patched_run

import main
main.main()
