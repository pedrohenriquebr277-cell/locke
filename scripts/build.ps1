# Gera dist\Locke.exe (interface) e dist\LockeService.exe (serviço) + scripts de instalação.
# Feche o Locke.exe antes: o Windows trava o arquivo enquanto ele está aberto.
Set-Location (Join-Path $PSScriptRoot "..")

python -m PyInstaller --noconfirm --onefile --noconsole --name Locke --icon icon.ico `
    --add-data "web;web" --add-data "icon.ico;." main.py
python -m PyInstaller --noconfirm --onefile --console --name LockeService --icon icon.ico `
    --hidden-import win32timezone locke_service.py

Copy-Item scripts\instalar_servico.ps1, scripts\desinstalar_servico.ps1 dist\ -Force
