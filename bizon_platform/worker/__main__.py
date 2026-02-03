"""Allow running the worker as a module: python -m bizon_platform.worker"""

from bizon_platform.worker.main import main

if __name__ == "__main__":
    main()
