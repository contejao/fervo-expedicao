"""
Handler para PDFs genéricos (pedidos Olist/marketplaces).
Extrai apenas a primeira página e imprime.
"""
import shutil
from pathlib import Path

import fitz

import printer
import updater
from logger import log

_SUFIXO = "_PRIMEIRA_PAGINA"


def processar(pdf_path: Path, cfg: dict):
    if _SUFIXO in pdf_path.stem:
        return  # arquivo já processado, ignora

    processados = pdf_path.parent / "Olist_ArquivosProcessados"
    processados.mkdir(exist_ok=True)

    try:
        doc = fitz.open(pdf_path)
        novo_pdf = pdf_path.parent / f"{pdf_path.stem}{_SUFIXO}.pdf"

        novo_doc = fitz.open()
        novo_doc.insert_pdf(doc, from_page=0, to_page=0)
        novo_doc.save(novo_pdf)
        novo_doc.close()
        doc.close()

        updater.registrar_impressao()
        printer.imprimir_pdf(
            novo_pdf,
            impressora=cfg.get("pdf_printer", ""),
            sumatra_path=cfg.get("sumatra_path", ""),
        )

        shutil.move(str(pdf_path), processados / pdf_path.name)
        shutil.move(str(novo_pdf), processados / novo_pdf.name)

    except Exception as e:
        log.error(f"Erro ao processar PDF genérico {pdf_path.name}: {e}")
