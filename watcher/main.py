"""
Fervo Expedição — Watcher Unificado v1.0.0

Monitora a pasta Downloads e roteia automaticamente:
  .pdf  → handler PDF (genérico ou Shein conforme nome do arquivo)
  .txt  → handler ZPL (impressora Zebra)

Modos:
  --modo olist   Apenas PDFs genéricos (padrão)
  --modo shein   Apenas PDFs Shein (2 páginas lado a lado)
  --modo zpl     Apenas arquivos ZPL (.txt)
  --modo tudo    Todos os tipos simultâneos
"""
import argparse
import sys
import time
from pathlib import Path

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileCreatedEvent

import config
import updater
from logger import log, purgar_logs_antigos
from handlers import pdf_generic, pdf_shein, zpl as zpl_handler


MODO_DESCRICAO = {
    "olist": "PDFs genéricos (Mercado Livre, Shopee, etc.)",
    "shein": "PDFs Shein (etiqueta + DANFE lado a lado)",
    "zpl":   "Arquivos ZPL (.txt) para Zebra",
    "tudo":  "Todos os tipos",
}

# Arquivo precisa ter pelo menos este tamanho para ser processado (evita arquivos incompletos)
TAMANHO_MINIMO_BYTES = 1024

# Tempo de espera após detectar o arquivo (garantir que o download terminou)
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


class FervoHandler(FileSystemEventHandler):
    def __init__(self, modo: str, cfg: dict):
        self.modo = modo
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

        # Ignora arquivos já processados ou temporários
        if any(tag in nome for tag in ("_PRIMEIRA_PAGINA", "_10x15_FINAL", "_FINAL", "_tmp")):
            return

        if ext == ".pdf" and self.modo in ("olist", "tudo"):
            self._processados.add(nome)
            time.sleep(ESPERA_DOWNLOAD_SEGUNDOS)
            if not _aguardar_disponibilidade(path):
                log.warning(f"Arquivo indisponível após espera: {nome}")
                return
            log.info(f"PDF detectado (modo olist): {nome}")
            pdf_generic.processar(path, self.cfg)

        elif ext == ".pdf" and self.modo == "shein":
            self._processados.add(nome)
            time.sleep(ESPERA_DOWNLOAD_SEGUNDOS)
            if not _aguardar_disponibilidade(path):
                log.warning(f"Arquivo indisponível após espera: {nome}")
                return
            log.info(f"PDF detectado (modo shein): {nome}")
            pdf_shein.processar(path, self.cfg)

        elif ext == ".txt" and self.modo in ("zpl", "tudo"):
            self._processados.add(nome)
            time.sleep(1.0)
            if not _aguardar_disponibilidade(path):
                log.warning(f"Arquivo indisponível após espera: {nome}")
                return
            log.info(f"ZPL detectado: {nome}")
            zpl_handler.processar(path, self.cfg)


def main():
    parser = argparse.ArgumentParser(description="Fervo Expedição — Watcher de etiquetas")
    parser.add_argument(
        "--modo",
        choices=["olist", "shein", "zpl", "tudo"],
        default="olist",
        help="Tipo de arquivo a monitorar (padrão: olist)",
    )
    args = parser.parse_args()

    cfg = config.load()
    purgar_logs_antigos(cfg.get("log_days_to_keep", 30))

    downloads = Path.home() / "Downloads"
    log.info(f"=== Fervo Expedição v{config.VERSION} iniciado ===")
    log.info(f"Modo: {args.modo} — {MODO_DESCRICAO[args.modo]}")
    log.info(f"Monitorando: {downloads}")

    # Verifica atualização em background sem bloquear
    updater.verificar_atualizacao_em_background(
        idle_seconds=cfg.get("idle_seconds_before_update", 60)
    )

    event_handler = FervoHandler(modo=args.modo, cfg=cfg)
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
