"""
Handler para PDFs da Shein.
Combina página 1 (etiqueta) + página 2 (DANFE) lado a lado em A6 landscape.
"""
import io
import os
import shutil
from pathlib import Path

import fitz
from PIL import Image
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import landscape, A6
from reportlab.lib.units import cm

import printer
import updater
from logger import log


def processar(pdf_path: Path, cfg: dict):
    processados = pdf_path.parent / "Shein_ArquivosProcessados"
    processados.mkdir(exist_ok=True)

    try:
        doc = fitz.open(pdf_path)
        if len(doc) < 2:
            log.warning(f"PDF Shein com menos de 2 páginas, ignorando: {pdf_path.name}")
            doc.close()
            return

        saida = pdf_path.parent / f"{pdf_path.stem}_10x15_FINAL.pdf"
        tmp1 = pdf_path.parent / "_shein_tmp1.png"
        tmp2 = pdf_path.parent / "_shein_tmp2.png"

        pix1 = doc.load_page(0).get_pixmap(dpi=300)
        pix2 = doc.load_page(1).get_pixmap(dpi=300)
        doc.close()

        Image.open(io.BytesIO(pix1.tobytes("png"))).save(tmp1)
        Image.open(io.BytesIO(pix2.tobytes("png"))).save(tmp2)

        c = canvas.Canvas(str(saida), pagesize=landscape(A6))
        c.drawImage(str(tmp1), 0, 0, width=7.5 * cm, height=10 * cm)
        c.drawImage(str(tmp2), 7.5 * cm, 0, width=7.5 * cm, height=10 * cm)
        c.save()

        updater.registrar_impressao()
        printer.imprimir_pdf(
            saida,
            impressora=cfg.get("pdf_printer", ""),
            sumatra_path=cfg.get("sumatra_path", ""),
        )

        shutil.move(str(pdf_path), processados / pdf_path.name)

    except Exception as e:
        log.error(f"Erro ao processar PDF Shein {pdf_path.name}: {e}")
    finally:
        for tmp in [tmp1, tmp2, saida]:
            try:
                if Path(tmp).exists():
                    os.remove(tmp)
            except Exception:
                pass
