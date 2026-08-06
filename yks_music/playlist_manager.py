"""
Gerenciador de playlists.
"""

from pathlib import Path

from .config import MUSIC_BASE
from .utils import get_audio_files, get_playlists


def create_playlist(name: str) -> bool:
    """Cria uma nova playlist (pasta)."""
    target = MUSIC_BASE / name
    if target.exists():
        print(f"❌ Playlist '{name}' já existe.")
        return False
    target.mkdir(parents=True)
    print(f"✅ Playlist '{name}' criada.")
    return True


def delete_playlist(name: str) -> bool:
    """Remove uma playlist vazia."""
    target = MUSIC_BASE / name
    if not target.exists() or not target.is_dir():
        print(f"❌ Playlist '{name}' não encontrada.")
        return False
    if any(target.iterdir()):
        print(f"❌ Playlist '{name}' não está vazia.")
        return False
    target.rmdir()
    print(f"✅ Playlist '{name}' removida.")
    return True


def list_playlists():
    """Lista todas as playlists com número de músicas."""
    playlists = get_playlists()
    if not playlists:
        print("Nenhuma playlist.")
        return
    for p in playlists:
        songs = get_audio_files(MUSIC_BASE / p)
        print(f"  - {p} ({len(songs)} músicas)")


def add_to_playlist(name: str, url: str, audio_format: str = "mp3"):
    """Adiciona uma música/playlist a uma playlist existente."""
    target = MUSIC_BASE / name
    if not target.is_dir():
        print(f"❌ Playlist '{name}' não existe. Crie primeiro.")
        return False
    from .downloader import download_playlist, download_video
    if "list=" in url or "playlist" in url.lower():
        return download_playlist(url, target, audio_format=audio_format)
    else:
        return download_video(url, target, audio_format=audio_format)
