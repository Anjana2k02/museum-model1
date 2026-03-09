"""
Root entry point for the HAR API server.

Usage:
    Local dev:    python main.py          (loads .env.local, hot-reload ON)
    Production:   python main.py          (reads ENV from --env-file or system env)
    Docker CMD:   python main.py          (ENV injected via --env-file at docker run)

The FastAPI application lives in api/main.py.
This file handles .env loading and uvicorn launch only.
"""
from __future__ import annotations

import os
from pathlib import Path


def _load_env() -> None:
    """Load environment variables from the appropriate .env file.

    - ENV=local  → loads .env.local  (override=True, hot dev values)
    - ENV=live   → skips file load (container/system env already set)
    """
    # dotenv import here so the rest of the module doesn't hard-depend on it
    from dotenv import load_dotenv

    env_mode = os.getenv("ENV", "local").strip().lower()

    if env_mode == "local":
        env_file = Path(__file__).resolve().parent / ".env.local"
        if env_file.exists():
            load_dotenv(env_file, override=True)
            print(f"[startup] Loaded {env_file}")
        else:
            print(
                "[startup] WARNING: .env.local not found. "
                "Copy .env.example to .env.local and edit as needed."
            )
    else:
        # Production: vars come from docker --env-file or host system.
        # Call load_dotenv with override=False so system env always wins.
        from dotenv import load_dotenv as _ld
        _ld(override=False)
        print(f"[startup] ENV={env_mode} — using container/system environment")


def main() -> None:
    _load_env()

    # Import uvicorn AFTER dotenv so HAR_MODEL_PATH etc. are already in
    # os.environ when api/main.py is imported by uvicorn at startup.
    import uvicorn

    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8888"))
    env_mode = os.getenv("ENV", "local").strip().lower()
    is_local = env_mode == "local"

    print(f"[startup] ENV={env_mode}  HOST={host}  PORT={port}  reload={is_local}")

    uvicorn.run(
        "api.main:app",
        host=host,
        port=port,
        reload=is_local,
        log_level="info",
    )


if __name__ == "__main__":
    main()
