"""
Módulo de download com yt-dlp.
"""

import subprocess
from pathlib import Path
from typing import List, Optional

from .config import DEFAULT_AUDIO_FORMAT, YTDLP_CMD, get_cookie_browser_and_path, get_yt_dlp_path


def build_audio_opts(format_selector: str = "bestaudio/best", audio_format: Optional[str] = None, no_convert: bool = False) -> List[str]:
    """Constrói as opções de áudio para yt-dlp, incluindo cookies se disponíveis."""
    browser, cookies_path = get_cookie_browser_and_path()
    
    opts = [
        "-f", format_selector,
        "-x",
        "--audio-quality", "5",
        "--embed-thumbnail",
        "--embed-metadata",
        "--no-mtime",
        "--sleep-interval", "0.5",
        "--max-sleep-interval", "1",
        "--concurrent-fragments", "32",
        "--throttled-rate", "100K",
        "--fragment-retries", "5",
        "--sleep-requests", "0.5",
    ]
    
    if audio_format and not no_convert:
        opts.extend(["--audio-format", audio_format])
    
    if cookies_path:
        opts.extend(["--cookies-from-browser", cookies_path])
    
    return opts


def build_cmd(output_dir: Path, audio_format: Optional[str] = None, no_convert: bool = False,
              format_selector: str = "bestaudio/best") -> List[str]:
    """Constrói o comando yt-dlp completo."""
    output_dir.mkdir(parents=True, exist_ok=True)
    out_template = str(output_dir / "%(title)s.%(ext)s")
    
    opts = build_audio_opts(format_selector, audio_format, no_convert)
    
    cmd = [get_yt_dlp_path(), "-o", out_template] + opts
    
    return cmd


def _run(cmd: List[str], url: str) -> bool:
    """Executa o comando yt-dlp e retorna True em caso de sucesso."""
    full_cmd = cmd + [url]
    try:
        subprocess.run(full_cmd, check=True)
        return True
    except subprocess.CalledProcessError as e:
        return False


def download_video(url: str, output_dir: Path, audio_format: str = DEFAULT_AUDIO_FORMAT, no_convert: bool = False):
    """
    Baixa um vídeo ou faixa do YouTube.
    Se no_convert=True, pega o áudio sem conversão (usa bestaudio).
    Tenta o seletor principal e, se falhar por formato indisponível,
    tenta fallbacks progressivos.
    """
    is_shorts = "/shorts/" in url.lower()
    
    if is_shorts:
        attempts = [
            build_cmd(output_dir, audio_format if no_convert else None, no_convert, "best"),
            build_cmd(output_dir, audio_format if no_convert else None, no_convert, "bestaudio/best"),
            build_cmd(output_dir, audio_format if no_convert else None, no_convert, "b"),
        ]
    else:
        attempts = [
            build_cmd(output_dir, audio_format if no_convert else None, no_convert, "bestaudio/best"),
            build_cmd(output_dir, audio_format if no_convert else None, no_convert, "best"),
            build_cmd(output_dir, audio_format if no_convert else None, no_convert, "b"),
        ]

    for i, cmd in enumerate(attempts, start=1):
        if _run(cmd, url):
            return True
        if i < len(attempts):
            print(f"⚠️  Formato indisponível, tentando alternativa ({i}/{len(attempts)})...")

    print(f"❌ Falha ao baixar: formato indisponível mesmo após tentativas alternativas.")
    print(f"   Dica: o vídeo pode estar restrito (idade/região) ou indisponível. Tente 'yt-dlp -U' para atualizar.")
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
