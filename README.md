# yks-music

CLI interativo para baixar músicas e playlists do YouTube.
Pesquise, baixe e organize sua biblioteca musical diretamente no terminal.

## ✨ Recursos

- Pesquisa no YouTube com paginação (10 resultados por página)
- Download por URL ou busca interativa
- Conversão automática para MP3 com thumbnail e metadata embutidos
- Organização em playlists (pastas separadas)
- Navegação com setas do teclado (`prompt_toolkit`)
- Suporte a cookies de navegador (bypass de restrições de idade e bot detection)
- Desinstalador completo (`yks-music uninstall`)
- Configurações integradas (formato de áudio, navegador, dependências, sistema)
- Detecção automática da pasta de músicas (XDG, `xdg-user-dir`)
- Instalação multiplataforma (Ubuntu/Debian, Arch, macOS, Fedora, openSUSE, Alpine)

## 📦 Requisitos

- Python 3.9+
- `ffmpeg`
- `yt-dlp`
- Navegador instalado (para cookies de download estável)

## 🔧 Instalação

```bash
git clone https://github.com/NicolasToledoo/yks-music.git
cd yks-music
./setup.sh
```

O instalador:

- Detecta seu sistema operacional (Ubuntu/Debian, Pop!_OS, Arch, Fedora, RHEL/CentOS, openSUSE, Alpine, macOS)
- Instala `ffmpeg` e Python 3 se necessário
- Cria `.venv` na pasta do projeto
- Instala dependências Python: `yt-dlp`, `rich`, `pyfiglet`, `prompt_toolkit`
- Detecta automaticamente o navegador e caminho dos cookies (sem necessidade de configuração manual)
- Configura `PATH` no shell do usuário (`bash`, `zsh`, `fish`)
- Cria comando global `~/.local/bin/yks-music`

## 🗑️ Desinstalação

```bash
yks-music uninstall
```

Remove completamente: comando global, cache, configurações, pacote pip e opcionalmente as músicas baixadas.

## 🚀 Uso

```bash
yks-music                    # Abre o menu interativo
yks-music uninstall          # Remove completamente do sistema
```

### Comandos do Menu Principal

- 🔍 **Pesquisar Músicas** — busca e pagina resultados do YouTube
- 📥 **Download Direto** — baixa por link (vídeo ou playlist)
- 📁 **Gerenciar Playlists** — criar, listar, adicionar músicas e deletar playlists
- 📀 **Listar Músicas** — mostra arquivos baixados (avulsas, playlists ou tudo)
- ⚙️ **Configurações** — pasta, formato, cookies, dependências e informações do sistema
- ❓ **Ajuda** — documentação
- 🚪 **Sair** — fecha o programa

↑↓ navegar | Enter selecionar | Esc voltar

### Submenus

**Gerenciar Playlists:**

- Criar Nova Playlist
- Importar Playlist pelo Link
- Listar Playlists
- Adicionar Música a Playlist
- Deletar Playlist

**Listar Músicas:**

- Músicas Avulsas
- Playlists
- Tudo

**Configurações:**

- Pasta de Músicas
- Formato Padrão (`mp3`, `m4a`, `opus`, `flac`, `wav`)
- Cookies do Navegador (selecionar browser ou redetectar automaticamente)
- Verificar Dependências
- Informações do Sistema

## 📁 Estrutura

```
~/Music/yks-musics/          # Pasta padrão de downloads
├── minha_musica.mp3
├── playlist_rock/
│   ├── 01 - Musica 1.mp3
│   └── 02 - Musica 2.mp3
└── ...

~/.config/yks-music/
└── config.json              # Configurações (browser, cookies, formato)

~/.local/bin/yks-music       # Atalho global criado pelo setup.sh

<project_root>/
├── yks_music/               # Pacote Python
│   ├── __init__.py
│   ├── cli.py               # Interface interativa (menus, banners, navegação)
│   ├── config.py            # Configurações globais, paths, formatos
│   ├── detector_cookie.py   # Detecção automática de cookies por browser
│   ├── downloader.py        # Download de vídeos e playlists via yt-dlp
│   ├── playlist_manager.py  # CRUD de playlists (pastas)
│   ├── search.py            # Pesquisa no YouTube com paginação
│   ├── uninstaller.py       # Desinstalação completa do sistema
│   └── utils.py             # Utilitários (sanitize, dependencies, audio files)
├── setup.sh                 # Instalador multiplataforma
└── pyproject.toml           # Dependências e metadados do pacote
```

## 💡 Cookies do Navegador

O yks-music usa cookies do navegador para:

- Baixar músicas com restrição de idade
- Evitar erro "Sign in to confirm you're not a bot"
- Garantir estabilidade nos downloads

### Detecção Automática

O instalador e o app detectam automaticamente:

- **Navegadores instalados** (Brave, Chrome, Chromium, Edge, Firefox, Opera, Safari, Vivaldi, Whale)
- **Instalações Flatpak** (`~/.var/app/...`)
- **Instalações Snap** (`~/snap/...`)
- **Perfis múltiplos** (Default, Profile 1, 2, etc.)
- **Perfis Firefox** via `profiles.ini`

### Navegadores Suportados

| Navegador | Caminho Nativo | Caminho Flatpak | Caminho Snap |
|-----------|----------------|-----------------|--------------|
| Brave | `~/.config/BraveSoftware/Brave-Browser` | `~/.var/app/com.brave.Browser/config` | `~/snap/brave/current/.config/BraveSoftware/Brave-Browser` |
| Chrome | `~/.config/google-chrome` | `~/.var/app/com.google.Chrome/config` | — |
| Chromium | `~/.config/chromium` | `~/.var/app/org.chromium.Chromium/config` | `~/snap/chromium/common/chromium` |
| Edge | `~/.config/microsoft-edge` | `~/.var/app/com.microsoft.Edge/config` | — |
| Firefox | `~/.mozilla/firefox` | `~/.var/app/org.mozilla.firefox/.mozilla/firefox` | `~/snap/firefox/common/.mozilla/firefox` |
| Opera | `~/.config/opera` | `~/.var/app/com.opera.Opera/config/opera` | `~/snap/opera/common/opera` |
| Vivaldi | `~/.config/vivaldi` | `~/.var/app/com.vivaldi.Vivaldi/config/vivaldi` | — |
| Whale | `~/.config/naver-whale` | `~/.var/app/com.naver.Whale/config/naver-whale` | — |

> **Nota:** Safari é listado como suportado no código mas não possui detecção automática de cookies no Linux.

### Redetectar Cookies

Se o browser for alterado ou os cookies pararem de funcionar:

```bash
# Via menu interativo
yks-music
# Configurações > Cookies do Navegador > [selecionar browser] ou 🔄 Redetectar

# Verificar config atual
cat ~/.config/yks-music/config.json
```

### Se precisar de ajuda:

```bash
# Verificar config atual
cat ~/.config/yks-music/config.json

# Redetectar cookies no menu "Configurações > Cookies do Navegador > Redetectar"

# Verificar se pasta de músicas existe
ls -la ~/Music/yks-musics  # ou ~/Músicas/yks-musics
```

## 📊 Distribuições Suportadas

| Distro | Gerenciador de Pacotes | Suporte |
|--------|----------------------|---------|
| Ubuntu/Debian | apt-get | ✅ |
| Pop!_OS | apt-get | ✅ |
| Linux Mint | apt-get | ✅ |
| Arch Linux | pacman | ✅ |
| Manjaro | pacman | ✅ |
| Fedora | dnf | ✅ |
| RHEL/CentOS | yum | ✅ |
| openSUSE | zypper | ✅ |
| Alpine | apk | ✅ |
| macOS | brew | ✅ |

O yks-music funciona automaticamente em todas essas distribuições, detectando cookies de navegadores instalados nativamente ou via Flatpak/Snap.

## 🛠️ Tecnologias

- **yt-dlp** — engine de download do YouTube
- **ffmpeg** — conversão e extração de áudio
- **prompt_toolkit** — interface TUI com navegação por setas
- **Rich** — saída estilizada no terminal (banners, tabelas, painéis)
- **pyfiglet** — arte ASCII do banner
