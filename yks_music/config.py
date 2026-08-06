"""
Configurações globais do yks-music.
"""

import json
import os
from pathlib import Path

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
    return config.get("cookie_browser", DEFAULT_COOKIE_BROWSER)


def set_cookie_browser(browser: str):
    """Define o navegador para cookies."""
    config = load_config()
    config["cookie_browser"] = browser
    save_config(config)


def get_music_base() -> Path:
    """
    Detecta a pasta de músicas do usuário.
    
    Prioriza:
    1. Variável de ambiente XDG_MUSIC_DIR
    2. xdg-user-dir MUSIC (Linux)
    3. ~/Músicas (português)
    4. ~/Music (inglês)
    5. ~/Music como fallback padrão
    """
    home = Path.home()
    
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
    
    # 3. Tentativas comuns de pastas de música
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
    
    # 4. Fallback padrão (cria ~/Músicas se não existir)
    default_path = home / "Músicas" / "yks-musics"
    return default_path


# Caminho da pasta base do yks-music
MUSIC_BASE = get_music_base()
