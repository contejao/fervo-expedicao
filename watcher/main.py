"""
Fervo Expedição — Watcher Unificado v1.1.0

Monitora Downloads e roteia automaticamente sem precisar escolher modo:
  .txt            → ZPL (Zebra)
  .pdf  1 página  → imprime direto (etiquetas Olist: ML, Shopee, etc.)
  .pdf  2 páginas → handler Shein (etiqueta + DANFE lado a lado)
  .pdf  3+ páginas→ extrai só a primeira página
"""
import sys
import time
from pathlib import Path

import fitz
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileCreatedEvent

import config
import updater
from logger import log, purgar_logs_antigos
from handlers import pdf_generic, pdf_shein, zpl as zpl_handler

TAMANHO_MINIMO_BYTES = 1024
ESPERA_DOWNLOAD_SEGUNDOS = 2.0


def _aguardar_disponibilidade(path: Path, tentativas: int = 10, intervalo: float = 1.5) -> bool:
    for _ in range(tentativas):
        try:
            with open(path, "rb+"):
                if path.stat().st_size >= TAMANHO_MINIMO_BYTES:
                    return True
        except (PermissionError, OSError):
            pass
        time.sleep(intervalo)
    return False


def _contar_paginas(pdf_path: Path) -> int:
    try:
        doc = fitz.open(pdf_path)
        n = len(doc)
        doc.close()
        return n
    except Exception:
        return 1


def _rotear_pdf(pdf_path: Path, cfg: dict):
    paginas = _contar_paginas(pdf_path)
    log.info(f"PDF detectado ({paginas} pág.): {pdf_path.name}")

    if paginas == 2:
        log.info("→ Handler Shein (etiqueta + DANFE)")
        pdf_shein.processar(pdf_path, cfg)
    elif paginas == 1:
        log.info("→ Impressão direta (etiqueta única)")
        pdf_generic.processar_direto(pdf_path, cfg)
    else:
        log.info(f"→ Extrai primeira página ({paginas} páginas detectadas)")
        pdf_generic.processar(pdf_path, cfg)


class FervoHandler(FileSystemEventHandler):
    def __init__(self, cfg: dict):
        self.cfg = cfg
        self._processados: set[str] = set()

    def on_created(self, event: FileCreatedEvent):
        if event.is_directory:
            return

        path = Path(event.src_path)
        ext = path.suffix.lower()
        nome = path.name

        if nome in self._processados:
            return

        if any(tag in nome for tag in ("_PRIMEIRA_PAGINA", "_10x15_FINAL", "_tmp")):
            return

        if ext not in (".pdf", ".txt"):
            return

        self._processados.add(nome)
        time.sleep(ESPERA_DOWNLOAD_SEGUNDOS)

        if not _aguardar_disponibilidade(path):
            log.warning(f"Arquivo indisponível após espera: {nome}")
            return

        if ext == ".txt":
            log.info(f"ZPL detectado: {nome}")
            zpl_handler.processar(path, self.cfg)
        elif ext == ".pdf":
            _rotear_pdf(path, self.cfg)


def main():
    cfg = config.load()
    purgar_logs_antigos(cfg.get("log_days_to_keep", 30))

    downloads = Path.home() / "Downloads"
    log.info(f"=== Fervo Expedição v{config.VERSION} iniciado ===")
    log.info(f"Monitorando: {downloads}")
    log.info("Modo: automático (PDF 1pág=direto · 2pág=Shein · ZPL=Zebra)")

    updater.verificar_atualizacao_em_background()

    event_handler = FervoHandler(cfg=cfg)
    observer = Observer()
    observer.schedule(event_handler, str(downloads), recursive=False)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        log.info("Encerrando...")
        observer.stop()
    observer.join()


if __name__ == "__main__":
    main()
