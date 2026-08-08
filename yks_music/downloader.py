"""
Módulo de download com yt-dlp.
"""

import subprocess
from pathlib import Path
from typing import List, Optional

from .config import DEFAULT_AUDIO_FORMAT, YTDLP_CMD, get_cookie_browser_and_path, get_yt_dlp_path


def build_audio_opts() -> List[str]:
    """Constrói as opções de áudio para yt-dlp, incluindo cookies se disponíveis."""
    browser, cookies_path = get_cookie_browser_and_path()
    
    opts = [
        "-f", "bestaudio",
        "-x",
        "--audio-format", "mp3",
        "--audio-quality", "5",
        "--embed-thumbnail",
        "--embed-metadata",
        "--no-mtime",
        "--sleep-interval", "1",
        "--max-sleep-interval", "3",
        "--concurrent-fragments", "32",
        "--throttled-rate", "100K",
        "--fragment-retries", "5",
        "--sleep-requests", "1",
    ]
    
    if cookies_path:
        opts.extend(["--cookies-from-browser", cookies_path])
    
    return opts


def build_cmd(output_dir: Path, audio_format: Optional[str] = None, no_convert: bool = False) -> List[str]:
    """Constrói o comando yt-dlp completo."""
    output_dir.mkdir(parents=True, exist_ok=True)
    out_template = str(output_dir / "%(title)s.%(ext)s")
    
    opts = build_audio_opts()
    
    cmd = [get_yt_dlp_path(), "-o", out_template] + opts
    
    if audio_format and no_convert:
        cmd.extend(["--audio-format", audio_format])
    
    return cmd


def download_video(url: str, output_dir: Path, audio_format: str = DEFAULT_AUDIO_FORMAT, no_convert: bool = False):
    """
    Baixa um vídeo ou faixa do YouTube.
    Se no_convert=True, pega o áudio sem conversão (usa bestaudio).
    """
    cmd = build_cmd(output_dir, audio_format if no_convert else None, no_convert)
    cmd.append(url)

    try:
        subprocess.run(cmd, check=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Falha ao baixar: {e}")
        return False


def download_playlist(url: str, output_dir: Path, audio_format: str = DEFAULT_AUDIO_FORMAT):
    """
    Baixa uma playlist inteira do YouTube.
    """
    cmd = build_cmd(output_dir) + ["--yes-playlist", url]

    try:
        subprocess.run(cmd, check=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Falha ao baixar playlist: {e}")
        return False
