"""
Handler para arquivos .txt com conteúdo ZPL — impressora Zebra.
"""
import shutil
from pathlib import Path

import printer
import updater
from logger import log


def processar(txt_path: Path, cfg: dict):
    processados = txt_path.parent / "ZPL_ArquivosProcessados"
    processados.mkdir(exist_ok=True)

    try:
        impressora = cfg.get("zebra_printer", "ELGIN L42PRO FULL")
        updater.registrar_impressao()
        ok = printer.imprimir_zpl(txt_path, impressora)
        if ok:
            shutil.move(str(txt_path), processados / txt_path.name)
    except Exception as e:
        log.error(f"Erro ao processar ZPL {txt_path.name}: {e}")
