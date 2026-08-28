import os
import sys
import asyncio
from pathlib import Path

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

import uvicorn
from src.app.main import app

if __name__ == '__main__':
    print("Starting FinPilot AI on http://localhost:8000 (http://127.0.0.1:8000) ...")
    config = uvicorn.Config(
        app=app,
        host="0.0.0.0",
        port=8000,
        log_level="info",
        loop="asyncio"
    )
    server = uvicorn.Server(config)
    loop = asyncio.SelectorEventLoop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(server.serve())
    finally:
        loop.close()
