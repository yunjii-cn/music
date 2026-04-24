# PyInstaller runtime hook: patch subprocess.Popen to hide all windows
# This hook runs BEFORE any user code in PyInstaller frozen apps
import sys

if sys.platform == 'win32':
    import subprocess as _subprocess
    
    # Store original __init__
    _orig_popen_init = _subprocess.Popen.__init__

    def _patched_popen_init(self, *args, **kwargs):
        # Ensure startupinfo is set with SW_HIDE
        si = kwargs.get('startupinfo', None)
        if si is None:
            si = _subprocess.STARTUPINFO()
        si.dwFlags |= _subprocess.STARTF_USESHOWWINDOW
        si.wShowWindow = 0  # SW_HIDE
        kwargs['startupinfo'] = si
        
        # Ensure CREATE_NO_WINDOW flag is set
        if 'creationflags' in kwargs:
            kwargs['creationflags'] = kwargs['creationflags'] | _subprocess.CREATE_NO_WINDOW
        else:
            kwargs['creationflags'] = _subprocess.CREATE_NO_WINDOW
        
        # Call original __init__
        _orig_popen_init(self, *args, **kwargs)

    # Apply patch
    _subprocess.Popen.__init__ = _patched_popen_init
    
    # Also patch subprocess.run to ensure it uses hidden windows
    _orig_run = _subprocess.run
    
    def _patched_run(*args, **kwargs):
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
