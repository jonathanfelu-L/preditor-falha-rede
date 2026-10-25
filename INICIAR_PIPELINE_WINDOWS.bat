@echo off
setlocal
cd /d "%~dp0"
echo ============================================================
echo PREDITOR DE REDE - SOMENTE DADOS PUBLICOS DO RIPE ATLAS
echo ============================================================
py -3.11 --version >nul 2>&1
if errorlevel 1 (
  echo ERRO: Python 3.11 nao foi encontrado.
  echo Instale Python 3.11 e marque a opcao para adicionar Python ao PATH.
  echo Depois execute este arquivo novamente.
  pause
  exit /b 1
)
if not exist ".venv\Scripts\python.exe" (
  echo Criando ambiente virtual...
  py -3.11 -m venv .venv
  if errorlevel 1 goto erro
)
echo Instalando/verificando bibliotecas...
".venv\Scripts\python.exe" -m pip install --upgrade pip
if errorlevel 1 goto erro
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 goto erro
echo.
echo O pipeline padrao SOMENTE LE dados publicos. Ele nao cria medicoes e nao gasta creditos.
echo Agora comecara a consulta a API, download e auditoria de publicidade.
echo.
".venv\Scripts\python.exe" executar_pipeline.py
if errorlevel 1 goto erro
echo.
echo PIPELINE FINALIZADO. Confira os arquivos de avaliacao e avisos no README.
pause
exit /b 0
:erro
echo.
echo O processo parou. Leia a mensagem acima; ele nao inventou dados para continuar.
pause
exit /b 1
