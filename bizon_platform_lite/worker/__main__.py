"""Allow running the worker as a module: python -m bizon_platform_lite.worker"""

from bizon_platform_lite.worker.main import main

if __name__ == "__main__":
    main()
