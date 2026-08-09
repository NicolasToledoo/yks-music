"""
Configurações globais do yks-music.
"""

import json
import platform
import shutil
import os
from pathlib import Path
from typing import Optional, Tuple

# Comandos externos necessários
YTDLP_CMD = "yt-dlp"
FFMPEG_CMD = "ffmpeg"

# Formato de áudio padrão
DEFAULT_AUDIO_FORMAT = "mp3"

# Extensões de áudio suportadas
AUDIO_EXTENSIONS = {".mp3", ".m4a", ".opus", ".flac", ".wav"}

# Tamanho da página de resultados de busca
SEARCH_PAGE_SIZE = 10

# Browser para cookies (padrão)
DEFAULT_COOKIE_BROWSER = "vivaldi"

# Navegadores suportados pelo yt-dlp
SUPPORTED_BROWSERS = [
    "brave",
    "chrome",
    "chromium",
    "edge",
    "firefox",
    "opera",
    "safari",
    "vivaldi",
    "whale",
]

# Configurações do usuário
CONFIG_DIR = Path.home() / ".config" / "yks-music"
CONFIG_FILE = CONFIG_DIR / "config.json"


def get_yt_dlp_path() -> str:
    """Retorna o caminho absoluto para yt-dlp, resolvendo a instalação no sistema."""
    path = shutil.which(YTDLP_CMD)
    if path:
        return path
    # Fallback: tentar buscar no .venv do projeto (criado pelo setup.sh)
    venv_path = Path.home() / ".config" / "yks-music" / ".venv" / "bin" / "yt-dlp"
    if venv_path.exists():
        return str(venv_path)
    # Fallback: tentar no .venv da pasta do projeto
    project_venv = Path(__file__).parent.parent.parent / ".venv" / "bin" / "yt-dlp"
    if project_venv.exists():
        return str(project_venv)
    return YTDLP_CMD


def load_config() -> dict:
    """Carrega configurações do arquivo JSON."""
    try:
        if CONFIG_FILE.exists():
            with open(CONFIG_FILE, "r") as f:
                return json.load(f)
    except (json.JSONDecodeError, IOError):
        pass
    return {}


def save_config(config: dict):
    """Salva configurações no arquivo JSON."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=2)


def get_cookie_browser() -> str:
    """Retorna o navegador configurado para cookies."""
    config = load_config()
    value = config.get("cookie_browser", DEFAULT_COOKIE_BROWSER)
    if ":" in value:
        return value.split(":", 1)[0]
    return value


def get_cookie_browser_and_path() -> Tuple[str, Optional[str]]:
    """
    Retorna (browser_name, formatted_path_for_yt_dlp).
    
    Formato de caminho suportado:
    - "chrome:/home/user/.config/google-chrome"
    - "firefox:/home/user/.mozilla/firefox/abc123.default"
    - "brave" (sem caminho, usado como fallback)
    """
    config = load_config()
    value = config.get("cookie_browser", DEFAULT_COOKIE_BROWSER)
    
    if value and ":" in value:
        parts = value.split(":", 1)
        return (parts[0], value)
    
    try:
        from .detector_cookie import detect_browser_path
        path = detect_browser_path(value)
        if path:
            return (value, path)
    except ImportError:
        pass
    
    return (value, None)


def set_cookie_browser(browser: str):
    """Define o navegador para cookies."""
    config = load_config()
    config["cookie_browser"] = browser
    save_config(config)


def set_cookie_browser_with_path(path_value: str):
    """Define o navegador e caminho completo para cookies."""
    config = load_config()
    config["cookie_browser"] = path_value
    save_config(config)


def get_music_base() -> Path:
    """
    Detecta a pasta de músicas do usuário.

    Prioriza:
    1. Variável de ambiente XDG_MUSIC_DIR
    2. xdg-user-dir MUSIC (Linux)
    3. Candidatos por plataforma (macOS vs Linux)
    4. ~/Music como fallback padrão
    """
    home = Path.home()
    is_macos = platform.system() == "Darwin"

    # 1. Verifica XDG_MUSIC_DIR (variável de ambiente padrão Linux)
    xdg_music = os.environ.get("XDG_MUSIC_DIR")
    if xdg_music:
        music_dir = Path(xdg_music)
        if music_dir.exists():
            return music_dir / "yks-musics"

    # 2. Tenta usar xdg-user-dir (mais confiável no Linux)
    try:
        import subprocess
        result = subprocess.run(
            ["xdg-user-dir", "MUSIC"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            music_dir = Path(result.stdout.strip())
            if music_dir.exists():
                return music_dir / "yks-musics"
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass  # xdg-user-dir não disponível

    # 3. Candidatos por plataforma
    if is_macos:
        # No macOS, ~/Music é o padrão do sistema
        candidates = [
            home / "Music",
            home / "Músicas",
        ]
    else:
        # No Linux, ~/Músicas é o XDG padrão em português
        candidates = [
            home / "Músicas",       # Português (Brasil)
            home / "Music",         # Inglês
            home / "Música",        # Singular português
            home / "músicas",       # Minúsculo
            home / "music",         # Minúsculo inglês
        ]

    for candidate in candidates:
        if candidate.exists():
            return candidate / "yks-musics"

    # 4. Fallback padrão (usa ~/Music por ser universal)
    default_path = home / "Music" / "yks-musics"
    return default_path


# Caminho da pasta base do yks-music
MUSIC_BASE = get_music_base()
