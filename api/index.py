"""
Vercel Python serverless entrypoint.
Copies the bundled SQLite DB to /tmp (writable) then imports the FastAPI app.
"""
import os
import shutil
from pathlib import Path

_src = Path(__file__).parent.parent / "db" / "arrecon.db"
_dst = Path("/tmp/arrecon.db")

if not _dst.exists() and _src.exists():
    shutil.copy(_src, _dst)

os.environ.setdefault("AR_DB_PATH", str(_dst if _dst.exists() else _src))

from backend.main import app  # noqa: F401, E402 — re-exported as the ASGI handler
