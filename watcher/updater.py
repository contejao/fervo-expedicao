"""
Auto-updater: verifica na inicialização, aplica imediatamente se houver versão nova.
"""
import os
import sys
import time
import threading
import tempfile
import urllib.request
import json
from pathlib import Path

import config
from logger import log


def registrar_impressao():
    pass  # mantido por compatibilidade com handlers


def _comparar_versoes(atual: str, nova: str) -> bool:
    try:
        return tuple(int(x) for x in nova.split(".")) > tuple(int(x) for x in atual.split("."))
    except Exception:
        return False


def _baixar(url: str) -> Path | None:
    try:
        tmp = Path(tempfile.mktemp(suffix=".exe", prefix="FervoExpedicao_new_"))
        log.info(f"Baixando atualização...")
        urllib.request.urlretrieve(url, tmp)
        return tmp
    except Exception as e:
        log.error(f"Falha ao baixar atualização: {e}")
        return None


def _aplicar_e_reiniciar(novo_exe: Path):
    exe_atual = Path(sys.executable)
    bat = exe_atual.parent / "_atualizar.bat"
    bat.write_text(
        f'@echo off\n'
        f'timeout /t 2 /nobreak >nul\n'
        f'del /f /q "{exe_atual}"\n'
        f'move /y "{novo_exe}" "{exe_atual}"\n'
        f'start "" "{exe_atual}"\n'
        f'del /f /q "%~f0"\n',
        encoding="utf-8"
    )
    log.info("Aplicando atualização e reiniciando...")
    os.startfile(str(bat))
    time.sleep(1)
    sys.exit(0)


def verificar_atualizacao_em_background(**_):
    def _worker():
        try:
            with urllib.request.urlopen(config.UPDATE_URL, timeout=10) as resp:
                dados = json.loads(resp.read())
            nova_versao = dados.get("version", "")
            download_url = dados.get("download_url", config.DOWNLOAD_URL)

            if _comparar_versoes(config.VERSION, nova_versao):
                log.info(f"Atualização encontrada: {nova_versao} (atual: {config.VERSION})")
                novo_exe = _baixar(download_url)
                if novo_exe:
                    _aplicar_e_reiniciar(novo_exe)
            else:
                log.info(f"Versão {config.VERSION} já é a mais recente.")
        except Exception as e:
            log.warning(f"Verificação de atualização falhou (sem internet?): {e}")

    threading.Thread(target=_worker, daemon=True, name="updater").start()
