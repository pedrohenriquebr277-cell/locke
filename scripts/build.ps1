# Gera dist\Locke.exe, dist\LockeService.exe e o instalador dist\LockeSetup.exe.
# Feche o Locke.exe e pare o serviço antes: o Windows trava os arquivos enquanto estão em uso.
Set-Location (Join-Path $PSScriptRoot "..")

python -m PyInstaller --noconfirm --onefile --noconsole --name Locke --icon icon.ico `
    --add-data "web;web" --add-data "icon.ico;." main.py
python -m PyInstaller --noconfirm --onefile --console --name LockeService --icon icon.ico `
    --hidden-import win32timezone locke_service.py

# Instalador (Inno Setup: winget install JRSoftware.InnoSetup)
$iscc = @("$env:ProgramFiles\Inno Setup 6\ISCC.exe", "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe",
          "$env:LOCALAPPDATA\Programs\Inno Setup 6\ISCC.exe") | Where-Object { Test-Path $_ } | Select-Object -First 1
if ($iscc) { & $iscc installer\locke.iss } else { Write-Warning "Inno Setup não encontrado: instalador não gerado." }
