"""
Funções utilitárias para yks-music.
"""

import os
import re
import shutil
import sys
from pathlib import Path

from .config import AUDIO_EXTENSIONS, FFMPEG_CMD, MUSIC_BASE, YTDLP_CMD


def check_dependencies():
    """Verifica se yt-dlp e ffmpeg estão instalados."""
    missing = []
    if not shutil.which(YTDLP_CMD):
        missing.append("yt-dlp")
    if not shutil.which(FFMPEG_CMD):
        missing.append("ffmpeg")
    if missing:
        console = None
        try:
            from rich.console import Console
            console = Console()
        except:
            pass
            
        if console:
            console.print(f"[red]❌ Dependências faltando: {', '.join(missing)}[/red]")
        else:
            print(f"❌ Dependências faltando: {', '.join(missing)}")
        print("Instale com:")
        print("  pip install yt-dlp")
        print("  sudo apt install ffmpeg  # ou equivalente no seu SO")
        sys.exit(1)


def ensure_base_dir():
    """Cria a pasta base ~/Music/yks-musics se não existir."""
    MUSIC_BASE.mkdir(parents=True, exist_ok=True)


def sanitize_filename(name: str) -> str:
    """Remove caracteres proibidos em nomes de arquivos."""
    return re.sub(r'[<>:"/\\|?*\x00-\x1f]', "", name).strip() or "untitled"


def is_playlist_url(url: str) -> bool:
    """Detecta se a URL é de uma playlist do YouTube."""
    return "playlist" in url.lower() or "&list=" in url


def get_playlists() -> list[str]:
    """Lista todas as playlists (subpastas)."""
    if not MUSIC_BASE.exists():
        return []
    return sorted([p.name for p in MUSIC_BASE.iterdir() if p.is_dir()])


def get_audio_files(path: Path) -> list[str]:
    """Lista arquivos de áudio em um diretório."""
    if not path.exists():
        return []
    return sorted([f.name for f in path.iterdir() if f.suffix.lower() in AUDIO_EXTENSIONS])
