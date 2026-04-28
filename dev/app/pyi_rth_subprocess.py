import sys
import os

if sys.platform == 'win32':
    try:
        import ctypes
        import ctypes.wintypes
        ctypes.windll.kernel32.FreeConsole()
    except Exception:
        pass

    try:
        user32 = ctypes.windll.user32
        kernel32 = ctypes.windll.kernel32
        WINEVENT_OUTOFCONTEXT = 0x0000
        EVENT_OBJECT_CREATE = 0x8000
        EVENT_OBJECT_SHOW = 0x8002
        OBJID_WINDOW = 0x00000000

        _console_hwnds = set()

        def _get_all_console_hwnds():
            result = set()
            current_pid = kernel32.GetCurrentProcessId()
            def enum_cb(hwnd, _):
                pid = ctypes.wintypes.DWORD()
                user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
                cls_buf = ctypes.create_unicode_buffer(256)
                user32.GetClassNameW(hwnd, cls_buf, 256)
                if cls_buf.value == 'ConsoleWindowClass':
                    result.add(hwnd)
                return True
            cb_type = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.wintypes.HWND, ctypes.wintypes.LPARAM)
            user32.EnumWindows(cb_type(enum_cb), 0)
            return result

        _console_hwnds = _get_all_console_hwnds()

        @ctypes.WINFUNCTYPE(None, ctypes.wintypes.HWINEVENTHOOK, ctypes.wintypes.DWORD,
                            ctypes.wintypes.HWND, ctypes.wintypes.LONG, ctypes.wintypes.LONG,
                            ctypes.wintypes.DWORD, ctypes.wintypes.DWORD)
        def _win_event_proc(hook, event, hwnd, id_object, id_child, dw_event_thread, dwms_event_time):
            if id_object != OBJID_WINDOW:
                return
            try:
                cls_buf = ctypes.create_unicode_buffer(256)
                user32.GetClassNameW(hwnd, cls_buf, 256)
                if cls_buf.value == 'ConsoleWindowClass':
                    if event == EVENT_OBJECT_SHOW:
                        user32.ShowWindow(hwnd, 0)
                    elif event == EVENT_OBJECT_CREATE:
                        user32.ShowWindow(hwnd, 0)
            except Exception:
                pass

        _event_hook = user32.SetWinEventHook(
            EVENT_OBJECT_SHOW, EVENT_OBJECT_SHOW,
            0, _win_event_proc, 0, 0, WINEVENT_OUTOFCONTEXT
        )
        _create_hook = user32.SetWinEventHook(
            EVENT_OBJECT_CREATE, EVENT_OBJECT_CREATE,
            0, _win_event_proc, 0, 0, WINEVENT_OUTOFCONTEXT
        )
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

    _subprocess._pyi_hidden_patched = True
