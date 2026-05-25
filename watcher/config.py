import json
import os
from pathlib import Path

VERSION = "1.0.0"

# URL do arquivo version.json hospedado no GitHub (atualizar após criar o repositório)
UPDATE_URL = "https://raw.githubusercontent.com/contejao/fervo-expedicao/main/version.json"
DOWNLOAD_URL = "https://github.com/contejao/fervo-expedicao/releases/latest/download/FervoExpedicao.zip"

_config_path = Path(os.getenv("APPDATA", "")) / "FervoExpedicao" / "config.json"

_defaults = {
    "zebra_printer": "ELGIN L42PRO FULL",
    "pdf_printer": "",           # vazio = impressora padrão do Windows
    "sumatra_path": r"C:\Program Files\SumatraPDF\SumatraPDF.exe",
    "log_days_to_keep": 30,
}

_config_path.parent.mkdir(parents=True, exist_ok=True)

def load() -> dict:
    if _config_path.exists():
        try:
            with open(_config_path, encoding="utf-8") as f:
                saved = json.load(f)
            return {**_defaults, **saved}
        except Exception:
            pass
    return dict(_defaults)

def save(cfg: dict):
    with open(_config_path, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2, ensure_ascii=False)
