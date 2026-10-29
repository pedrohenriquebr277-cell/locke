# Remove o serviço do Locke. Execute como administrador.
# Atenção: se houver uma sessão ativa, remover o serviço a interrompe (o bloco do hosts é limpo).
$principal = [Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()
if (-not $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Write-Host "Abra o PowerShell como administrador e rode este script de novo." -ForegroundColor Red
    exit 1
}
Stop-Service LockeService -ErrorAction SilentlyContinue
sc.exe delete LockeService | Out-Null

$hosts = Join-Path $env:SystemRoot "System32\drivers\etc\hosts"
$text = Get-Content $hosts -Raw
$clean = [regex]::Replace($text, "(?s)\r?\n*# >>> LOCKE BEGIN.*?# <<< LOCKE END[ \t]*\r?\n?", "")
if ($clean -ne $text) { Set-Content $hosts $clean.TrimEnd() -Encoding ASCII; ipconfig /flushdns | Out-Null }
Write-Host "Serviço removido."
