# PyInstaller hook: ensure subprocess.Popen is patched to hide windows
# This hook runs when subprocess module is imported
import sys

if sys.platform == 'win32':
    import subprocess as _subprocess
    
    _orig_popen_init = _subprocess.Popen.__init__

    def _patched_popen_init(self, *args, **kwargs):
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
