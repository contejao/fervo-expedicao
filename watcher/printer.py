import os
import subprocess
from pathlib import Path

from logger import log


def _sumatra_disponivel(sumatra_path: str) -> bool:
    return Path(sumatra_path).exists()


def imprimir_pdf(pdf_path: Path, impressora: str = "", sumatra_path: str = "") -> bool:
    """
    Imprime PDF silenciosamente.
    Tenta SumatraPDF primeiro (sem janela), cai para ShellExecute como fallback.
    """
    try:
        if sumatra_path and _sumatra_disponivel(sumatra_path):
            args = [sumatra_path, "-silent", "-print-settings", "noprompt"]
            if impressora:
                args += ["-print-to", impressora]
            else:
                args += ["-print-to-default"]
            args.append(str(pdf_path))
            subprocess.run(args, creationflags=subprocess.CREATE_NO_WINDOW, timeout=30)
            log.info(f"PDF impresso (SumatraPDF): {pdf_path.name}")
            return True

        # Fallback: ShellExecute com "printto" para impressora específica
        if impressora:
            import win32api
            win32api.ShellExecute(0, "printto", str(pdf_path), f'"{impressora}"', ".", 0)
        else:
            os.startfile(str(pdf_path), "print")

        log.info(f"PDF impresso (ShellExecute): {pdf_path.name}")
        return True

    except Exception as e:
        log.error(f"Erro ao imprimir PDF {pdf_path.name}: {e}")
        return False


def imprimir_zpl(zpl_path: Path, impressora: str) -> bool:
    """Envia arquivo ZPL diretamente para impressora Zebra via RAW."""
    try:
        import win32print
        conteudo = zpl_path.read_text(encoding="utf-8")
        handle = win32print.OpenPrinter(impressora)
        try:
            win32print.StartDocPrinter(handle, 1, ("Etiqueta ZPL", None, "RAW"))
            win32print.StartPagePrinter(handle)
            win32print.WritePrinter(handle, conteudo.encode("utf-8"))
            win32print.EndPagePrinter(handle)
            win32print.EndDocPrinter(handle)
        finally:
            win32print.ClosePrinter(handle)
        log.info(f"ZPL enviado para {impressora}: {zpl_path.name}")
        return True
    except Exception as e:
        log.error(f"Erro ao imprimir ZPL {zpl_path.name}: {e}")
        return False
