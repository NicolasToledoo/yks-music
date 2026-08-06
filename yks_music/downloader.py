"""
Módulo de download com yt-dlp.
"""

import subprocess
from pathlib import Path

from .config import DEFAULT_AUDIO_FORMAT, YTDLP_CMD, get_cookie_browser


# Otimizações de download para áudio
AUDIO_OPTS = [
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
    "--cookies-from-browser", get_cookie_browser(),
]


def download_video(url: str, output_dir: Path, audio_format: str = DEFAULT_AUDIO_FORMAT, no_convert: bool = False):
    """
    Baixa um vídeo ou faixa do YouTube.
    Se no_convert=True, pega o áudio sem conversão (usa bestaudio).
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    out_template = str(output_dir / "%(title)s.%(ext)s")

    cmd = [YTDLP_CMD, "-o", out_template] + AUDIO_OPTS

    if no_convert:
        cmd += ["--audio-format", audio_format]

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
    output_dir.mkdir(parents=True, exist_ok=True)
    out_template = str(output_dir / "%(title)s.%(ext)s")

    cmd = [YTDLP_CMD, "-o", out_template] + AUDIO_OPTS + ["--yes-playlist", url]

    try:
        subprocess.run(cmd, check=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Falha ao baixar playlist: {e}")
        return False
