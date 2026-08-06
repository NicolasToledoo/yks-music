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
- Detecta seu sistema operacional (Ubuntu/Debian, Arch, macOS, Fedora)
- Instala `ffmpeg` e Python 3 se necessário
- Cria `.venv` na pasta do projeto
- Instala `yt-dlp`, `rich`, `pyfiglet`, `prompt_toolkit`
- Pede para selecionar navegador para cookies (interativamente com setas)
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
└── config.json         # Configurações do navegador
```

## 🌐 Navegadores Suportados

- Brave
- Chrome
- Chromium
- Edge
- Firefox
- Opera
- Safari
- Vivaldi
- Whale
