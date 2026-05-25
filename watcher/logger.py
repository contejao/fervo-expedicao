import logging
import os
from datetime import datetime
from pathlib import Path

_log_dir = Path(os.getenv("APPDATA", "")) / "FervoExpedicao" / "logs"
_log_dir.mkdir(parents=True, exist_ok=True)

_log_file = _log_dir / f"expedicao_{datetime.now().strftime('%Y-%m-%d')}.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
    handlers=[
        logging.FileHandler(_log_file, encoding="utf-8"),
        logging.StreamHandler(),
    ],
)

log = logging.getLogger("fervo")


def purgar_logs_antigos(dias: int = 30):
    cutoff = datetime.now().timestamp() - dias * 86400
    for f in _log_dir.glob("expedicao_*.log"):
        if f.stat().st_mtime < cutoff:
            try:
                f.unlink()
            except Exception:
                pass
