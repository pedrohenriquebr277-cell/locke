# Instala e inicia o serviço do Locke. Execute como administrador (clique direito > Executar com o PowerShell).
$ErrorActionPreference = "Stop"
$principal = [Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()
if (-not $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Write-Host "Abra o PowerShell como administrador e rode este script de novo." -ForegroundColor Red
    exit 1
}
$exe = Join-Path $PSScriptRoot "LockeService.exe"
if (-not (Test-Path $exe)) { Write-Host "LockeService.exe não encontrado ao lado deste script." -ForegroundColor Red; exit 1 }

if (Get-Service LockeService -ErrorAction SilentlyContinue) {
    Write-Host "O serviço já está instalado."
} else {
    sc.exe create LockeService binPath= "`"$exe`"" start= auto DisplayName= "Locke" | Out-Null
    sc.exe description LockeService "Bloqueia sites e aplicativos durante as sessões de foco do Locke." | Out-Null
}
# Se o processo for encerrado (ex.: Gerenciador de Tarefas), o Windows o reinicia em 1 segundo.
# A última ação se repete nas falhas seguintes.
sc.exe failure LockeService reset= 86400 actions= restart/1000/restart/1000/restart/1000/restart/1000 | Out-Null
sc.exe failureflag LockeService 1 | Out-Null
Start-Service LockeService -ErrorAction SilentlyContinue
Get-Service LockeService | Format-Table Name, Status, StartType
