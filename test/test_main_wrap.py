import sys
import os
import traceback

os.chdir(r'E:\软件开发\云集智能音乐创意台\dev\app')
sys.path.insert(0, '.')

try:
    print("Importing main module...", flush=True)
    import main as main_mod
    print("Main module imported successfully", flush=True)

    print("Calling main()...", flush=True)
    main_mod.main()
except SystemExit as e:
    print(f"SystemExit: code={e.code}", flush=True)
except Exception as e:
    print(f"EXCEPTION: {type(e).__name__}: {e}", flush=True)
    traceback.print_exc()
