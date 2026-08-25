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

    effective_format = audio_format if (audio_format and not no_convert) else (None if no_convert else DEFAULT_AUDIO_FORMAT)

    opts = [
        "-f", format_selector,
        "-x",
        "--audio-quality", "5",
        "--embed-metadata",
        "--no-mtime",
        "--sleep-interval", "0.5",
        "--max-sleep-interval", "1",
        "--concurrent-fragments", "32",
        "--throttled-rate", "100K",
        "--fragment-retries", "5",
        "--sleep-requests", "0.5",
    ]

    if effective_format:
        opts.extend(["--audio-format", effective_format])

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
        result = subprocess.run(full_cmd, check=True, capture_output=True, text=True)
        return True
    except subprocess.CalledProcessError as e:
        if e.stderr:
            print(f"   yt-dlp: {e.stderr.strip().splitlines()[-1] if e.stderr.strip() else ''}")
        return False


def download_video(url: str, output_dir: Path, audio_format: str = DEFAULT_AUDIO_FORMAT, no_convert: bool = False):
    """
    Baixa um vídeo ou faixa do YouTube.
    Se no_convert=True, pega o áudio sem conversão (usa bestaudio).
    Tenta o seletor principal e, se falhar por formato indisponível,
    tenta fallbacks progressivos.
    """
    is_shorts = "/shorts/" in url.lower()

    effective_format = None if no_convert else audio_format

    if is_shorts:
        attempts = [
            build_cmd(output_dir, effective_format, no_convert, "best"),
            build_cmd(output_dir, effective_format, no_convert, "bestaudio/best"),
            build_cmd(output_dir, effective_format, no_convert, "b"),
        ]
    else:
        attempts = [
            build_cmd(output_dir, effective_format, no_convert, "bestaudio/best"),
            build_cmd(output_dir, effective_format, no_convert, "best"),
            build_cmd(output_dir, effective_format, no_convert, "b"),
        ]

    for i, cmd in enumerate(attempts, start=1):
        if _run(cmd, url):
            return True
        if i < len(attempts):
            print(f"Formato indisponivel, tentando alternativa ({i}/{len(attempts)})...")

    print(f"Falha ao baixar: formato indisponivel mesmo apos tentativas alternativas.")
    print(f"   Dica: o video pode estar restrito (idade/regiao) ou indisponivel. Tente 'yt-dlp -U' para atualizar.")
    return False


def download_playlist(url: str, output_dir: Path, audio_format: str = DEFAULT_AUDIO_FORMAT):
    """
    Baixa uma playlist inteira do YouTube com fallback de formatos.
    """
    attempts = [
        build_cmd(output_dir, audio_format, format_selector="bestaudio/best") + ["--yes-playlist", url],
        build_cmd(output_dir, audio_format, format_selector="best") + ["--yes-playlist", url],
        build_cmd(output_dir, audio_format, format_selector="b") + ["--yes-playlist", url],
    ]

    for i, cmd in enumerate(attempts, start=1):
        try:
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)
            return True
        except subprocess.CalledProcessError as e:
            if e.stderr:
                last_line = e.stderr.strip().splitlines()[-1] if e.stderr.strip() else str(e)
                print(f"   yt-dlp: {last_line}")
            if i < len(attempts):
                print(f"Formato indisponivel, tentando alternativa ({i}/{len(attempts)})...")
            else:
                print(f"Falha ao baixar playlist apos {len(attempts)} tentativas.")
                print(f"   Dica: tente 'yt-dlp -U' para atualizar.")
    return False
