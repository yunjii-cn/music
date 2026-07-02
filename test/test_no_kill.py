import sys
import os
import traceback

os.chdir(r'E:\软件开发\云集智能音乐创意台\dev\app')
sys.path.insert(0, '.')

import main as main_mod

try:
    print("Step 1: _create_single_instance_event...", flush=True)
    evt = main_mod._create_single_instance_event()
    print(f"  Event handle: {evt}", flush=True)

    print("Step 2: SKIPPING _kill_old_instances_async", flush=True)

    print("Step 3: extract_scripts...", flush=True)
    main_mod.extract_scripts()

    print("Step 4: Creating QApplication...", flush=True)
    from PyQt6.QtWidgets import QApplication
    app = QApplication(sys.argv)
    print("  QApplication created", flush=True)

    print("Step 5: Creating SplashScreen...", flush=True)
    splash = main_mod.SplashScreen()
    print("  SplashScreen created", flush=True)

    print("Step 6: Creating MainWindow...", flush=True)
    window = main_mod.MainWindow(splash=splash)
    print("  MainWindow created", flush=True)

    print("SUCCESS!", flush=True)
    from PyQt6.QtCore import QTimer
    QTimer.singleShot(3000, app.quit)
    ret = app.exec()
    print(f"Event loop exited with code: {ret}", flush=True)
except SystemExit as e:
    print(f"SystemExit: code={e.code}", flush=True)
except Exception as e:
    print(f"EXCEPTION: {type(e).__name__}: {e}", flush=True)
    traceback.print_exc()
