@echo off
rem Lancador do runtime do sintetica, criado por npx sintetica install.
setlocal
set "ROOT=%~dp0..\.."
set "SINTETICA_CMD=.sintetica\bin\sintetica.cmd"
set "WHEEL=%ROOT%\.sintetica\runtime\sintetica-0.1.0-py3-none-any.whl"
if exist "%WHEEL%" (
  uvx --from "%WHEEL%" sintetica %*
) else (
  uv run sintetica %*
)
exit /b %ERRORLEVEL%
