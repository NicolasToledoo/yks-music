# yks-music

CLI interativo para baixar músicas e playlists do YouTube.
Pesquise, baixe e organize sua biblioteca musical diretamente no terminal.

## ✨ Recursos

- Pesquisa no YouTube com paginação (10 resultados por página)
- Download por URL ou busca interativa
- Conversão automática para MP3 com thumbnail e metadata
- Organização em playlists (pastas separadas)
- Navegação com setas do teclado (prompt_toolkit)
- Suporte a cookies de navegador (bypass de restrições de idade e bot detection)
- Desinstalador completo (`yks-music uninstall`)
- Configurações integradas (formato de áudio, navegador, informações do sistema)
- Detecção automática da pasta de músicas (XDG, xdg-user-dir)
- Instalação multiplataforma (Ubuntu/Debian, Arch, macOS, Fedora)

## 📦 Requisitos

- Python 3.7+
- `ffmpeg`
- Navegador instalado (para cookies)

## 🔧 Instalação

```bash
git clone https://github.com/NicolasToledoo/yks-music.git
cd yks-music
./setup.sh
```

O instalador:
- Detecta seu sistema operacional (Ubuntu/Debian, Pop!_OS, Arch, Fedora, openSUSE, Alpine, macOS)
- Instala `ffmpeg` e Python 3 se necessário
- Cria `.venv` na pasta do projeto
- Instala `yt-dlp`, `rich`, `pyfiglet`, `prompt_toolkit`
- **Detecta automaticamente o navegador e caminho dos cookies** (sem necessidade de configuração manual)
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

### Opções de Download
- `--format mp3|m4a|opus` - Define formato de áudio
- `--no-convert` - Mantém formato original (mais rápido)
- `--sleep-interval 3` - Pausa entre requisições

### Comandos do Menu
```
   Pesquisar Músicas     - Busca e pagina resultados
   Download Direto       - Baixa por link
   Gerenciar Playlists   - Criar/listar/deletar playlists
   Listar Músicas        - Mostra arquivos baixados
   Configurações          - Informações do sistema
   Ajuda                  - Documentação
   Sair                   - Fechar programa
```

↑↓ navegar  Enter selecionar  Esc voltar

## 📁 Estrutura

```
~/Músicas/yks-musics/
├── minha_musica.mp3
├── playlist_rock/
│   ├── 01 - Musica 1.mp3
│   └── 02 - Musica 2.mp3
└── .venv/              # Instalação local

~/.config/yks-music/
└── config.json         # Configurações do navegador (ex: {"cookie_browser": "brave:/home/user/.config/BraveSoftware/Brave-Browser"})
```

## 💡 Dicas para Pop!_OS e Distros Linux

### Detecção Automática de Cookies

O YKS-music detecta automaticamente:
- **Navegadores instalados** (Brave, Chrome, Chromium, Edge, Opera, Vivaldi, Whale, Firefox)
- **Instalações Flatpak** (`~/.var/app/...`) 
- **Perfis múltiplos** (Default, Profile 1, 2, etc)
- **Perfis Firefox** via `profiles.ini`

### Navegadores Suportados

| Navegador | Caminho Nativo | Caminho Flatpak |
|-----------|----------------|-----------------|
| Brave | `~/.config/BraveSoftware/Brave-Browser` | `~/.var/app/com.brave.Browser/config` |
| Chrome | `~/.config/google-chrome` | `~/.var/app/com.google.Chrome/config` |
| Firefox | `~/.mozilla/firefox` | `~/.var/app/org.mozilla.firefox/.mozilla` |
| Vivaldi | `~/.config/vivaldi` | `~/.var/app/com.vivaldi.Vivaldi/config` |

### Se precisar de ajuda:
```bash
# Verificar config atual
cat ~/.config/yks-music/config.json

# Redetectar cookies no menu "Configurações > Cookies do Navegador > Redetectar"

# Verificar se pasta de músicas existe
ls -la ~/Músicas/yks-musics  # ou ~/Music/yks-musics
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

O YKS-music funciona automaticamente em todas essas distribuições, detectando cookies de navegadores instalados nativamente ou via Flatpak/Snap.


https://www.youtube.com/playlist?list=PLKdpAe6eh-UU