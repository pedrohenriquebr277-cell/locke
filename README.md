# Locke

Bloqueador de sites e aplicativos para Windows 10/11. Você escolhe o que proteger e por quanto tempo; depois de iniciar, **não dá para cancelar antes do fim do timer**. Feito para ajudar a manter o foco.

## Como funciona

```
┌────────────┐   TCP 127.0.0.1:47653   ┌──────────────────────────────┐
│ Locke.exe  │ ──────────────────────► │ LockeService (serviço SYSTEM)│
│ (interface)│   JSON por linha        │  • guarda o estado           │
└────────────┘                         │  • edita o arquivo hosts     │
                                       │  • encerra os apps da lista  │
                                       └──────────────────────────────┘
```

- **Interface** (`main.py`, `web/`): janela sem moldura feita com [pywebview](https://pywebview.flowrl.com/), HTML/CSS/JS puro, sem build step. Nunca calcula o fim do bloqueio: lê `ends_at` do serviço e mostra o tempo restante.
- **Serviço** (`locke_service.py`, `locke_core/`): roda em segundo plano, inicia com o Windows e mantém o bloqueio mesmo com o app fechado. Reaplica o bloco do `hosts` a cada segundo, encerra os processos da lista e, durante a sessão, trava a própria parada pelo gerenciador de serviços.
- **Contrato** (`backend_client.py`): a interface só conhece essa camada. `get_backend()` escolhe o serviço real (`backend_real.py`) ou o mock (`backend_mock.py`).

## Instalação (usuário)

1. Gere o instalador (veja [Build](#build)) ou baixe o `LockeSetup.exe`.
2. Dê dois cliques no `LockeSetup.exe` e siga o assistente. Ele pede permissão de administrador, instala o Locke e o serviço (início automático, reinício em caso de falha) e cria o atalho no menu Iniciar.
3. Abra o Locke pelo menu Iniciar.

Para remover: Configurações → Aplicativos → Locke → Desinstalar. Não funciona durante uma sessão ativa.

Sem o instalador, também dá para usar `scripts\instalar_servico.ps1` / `scripts\desinstalar_servico.ps1` (PowerShell como administrador, com os `.exe` na mesma pasta).

O parâmetro `--teste` abre o app com a duração de 1 minuto, para validar.

## Desenvolvimento

```powershell
pip install -r requirements-dev.txt

# Interface com o backend de mentira (não bloqueia nada de verdade)
$env:LOCKE_BACKEND = "mock"
python main.py --teste

# Simular erros na interface
$env:LOCKE_MOCK_ERROR = "service"   # ou "admin"
```

Para testar o serviço real sem instalá-lo (como administrador): `python locke_service.py console`.

### Testes

```powershell
python -m unittest discover -s tests -p "test_*.py"
node tests/test_validate.js
```

Os testes usam arquivos e processos falsos; nenhum toca no seu `hosts`.

## Build

```powershell
.\scripts\build.ps1
```

Gera `dist\Locke.exe` e `dist\LockeService.exe` com PyInstaller e o instalador `dist\LockeSetup.exe` com [Inno Setup](https://jrsoftware.org/isinfo.php) (`winget install JRSoftware.InnoSetup`). Feche o Locke antes, e pare o serviço se for substituir o `LockeService.exe`.

## Estrutura

```
main.py, api.py         interface (pywebview) e ponte JS → backend
backend_client.py       contrato + get_backend() (único ponto de troca)
backend_real.py         cliente do serviço
backend_mock.py         backend de mentira, só para desenvolver
locke_service.py        serviço do Windows
locke_core/             estado, regras, hosts, processos, servidor
web/                    HTML, CSS, JS, fontes e mascote
scripts/                build e instalação
tests/                  testes
```

## Limitações conhecidas

- **DNS seguro dos navegadores** (Chrome, Edge, Firefox) pode ignorar o `hosts`. Desative-o para sites bloqueados valerem.
- **Antivírus** pode proteger o `hosts` e barrar a escrita.
- **Administradores** conseguem encerrar o processo do serviço pelo Gerenciador de Tarefas (ele reinicia em 1 s). Para o uso diário, prefira uma conta de usuário comum.
- Mudar o **relógio do Windows** pode encerrar o bloqueio antes do fim.

## Créditos

- Fontes [Inter](https://rsms.me/inter/) e [Source Serif 4](https://github.com/adobe-fonts/source-serif), licença OFL.
- Mascote inspirado no personagem do Claude Code, da Anthropic.
