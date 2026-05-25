@echo off
chcp 65001 >nul
title Fervo Expedição — Instalador
color 0A

echo.
echo  =============================================
echo   FERVO EXPEDIÇÃO — Instalador Automático
echo  =============================================
echo.

:: ── 1. Verifica Python ────────────────────────────────────────────────
python --version >nul 2>&1
if errorlevel 1 (
    color 0C
    echo  [ERRO] Python não encontrado!
    echo.
    echo  Instale o Python antes de continuar:
    echo    1. Acesse: https://www.python.org/downloads/
    echo    2. Clique em "Download Python"
    echo    3. IMPORTANTE: marque "Add Python to PATH"
    echo    4. Conclua a instalação e rode este arquivo novamente.
    echo.
    pause
    exit /b 1
)

echo  [OK] Python encontrado.

:: ── 2. Instala dependências ────────────────────────────────────────────
echo.
echo  Instalando dependências (pode demorar alguns minutos)...
echo.
pip install watchdog PyMuPDF reportlab Pillow pywin32 requests --quiet --disable-pip-version-check
if errorlevel 1 (
    color 0C
    echo  [ERRO] Falha ao instalar dependências.
    echo  Verifique sua conexão com a internet e tente novamente.
    pause
    exit /b 1
)
echo  [OK] Dependências instaladas.

:: ── 3. Baixa o projeto do GitHub ──────────────────────────────────────
echo.
echo  Baixando arquivos do GitHub...
set DESTINO=%LOCALAPPDATA%\FervoExpedicao
set ZIP=%TEMP%\fervo-expedicao.zip

powershell -Command "Invoke-WebRequest -Uri 'https://github.com/contejao/fervo-expedicao/archive/refs/heads/main.zip' -OutFile '%ZIP%'" 2>nul
if errorlevel 1 (
    color 0C
    echo  [ERRO] Falha ao baixar arquivos.
    echo  Verifique sua conexão com a internet e tente novamente.
    pause
    exit /b 1
)

:: Extrai
if exist "%DESTINO%" rmdir /s /q "%DESTINO%"
mkdir "%DESTINO%"
powershell -Command "Expand-Archive -Path '%ZIP%' -DestinationPath '%DESTINO%' -Force" 2>nul
:: Move conteúdo da subpasta para o destino
for /d %%D in ("%DESTINO%\fervo-expedicao-*") do (
    xcopy /e /i /q "%%D\*" "%DESTINO%\" >nul
    rmdir /s /q "%%D"
)
del /q "%ZIP%"
echo  [OK] Arquivos instalados em %DESTINO%

:: ── 4. Cria atalho na Área de Trabalho ───────────────────────────────
echo.
echo  Criando atalho na Área de Trabalho...
powershell -Command ^
  "$s = (New-Object -COM WScript.Shell).CreateShortcut('%USERPROFILE%\Desktop\Fervo Expedicao.lnk'); ^
   $s.TargetPath = 'python'; ^
   $s.Arguments = '%DESTINO%\watcher\main.py'; ^
   $s.WorkingDirectory = '%DESTINO%\watcher'; ^
   $s.WindowStyle = 7; ^
   $s.Description = 'Fervo Expedicao — Monitor de etiquetas'; ^
   $s.Save()"

echo  [OK] Atalho criado na Área de Trabalho.

:: ── 5. Verifica nome da impressora Zebra ─────────────────────────────
echo.
echo  Impressoras instaladas neste computador:
echo  ─────────────────────────────────────────
powershell -Command "Get-Printer | Select-Object -ExpandProperty Name | Sort-Object" 2>nul || wmic printer get name 2>nul
echo  ─────────────────────────────────────────
echo.
echo  Se o nome da sua Zebra for diferente de "ELGIN L42PRO FULL",
echo  edite o arquivo: %DESTINO%\watcher\config.py
echo  e ajuste a linha: "zebra_printer": "NOME DA SUA IMPRESSORA"
echo.

:: ── Concluído ─────────────────────────────────────────────────────────
color 0A
echo  =============================================
echo   Instalação concluída com sucesso!
echo.
echo   Próximo passo: instalar o Tampermonkey
echo   (veja as instruções na tela)
echo  =============================================
echo.
pause
