"""
Detector de cookies para navegadores suportados pelo yt-dlp.
Detecta automaticamente os caminhos dos bancos de dados de cookies.

Suporta:
- Linux nativo (deb/rpm), Snap, Flatpak
- macOS
- Navegadores: Brave, Chrome, Chromium, Edge, Opera, Vivaldi, Whale, Firefox, Safari
"""

import os
import platform
from pathlib import Path
from typing import Optional, Tuple, List, Dict


CHROMIUM_PATHS: Dict[str, List[str]] = {}

if platform.system() == "Darwin":  # macOS
    CHROMIUM_PATHS.update({
        "chrome": [
            "~/Library/Application Support/Google/Chrome",
        ],
        "brave": [
            "~/Library/Application Support/BraveSoftware/Brave-Browser",
        ],
        "edge": [
            "~/Library/Application Support/Microsoft Edge",
        ],
        "chromium": [
            "~/Library/Application Support/Chromium",
        ],
        "opera": [
            "~/Library/Application Support/com.operasoftware.Opera",
        ],
        "vivaldi": [
            "~/Library/Application Support/Vivaldi",
        ],
    })
else:  # Linux
    CHROMIUM_PATHS.update({
        "brave": [
            "~/.config/BraveSoftware/Brave-Browser",
            "~/snap/brave/current/.config/BraveSoftware/Brave-Browser",
            "~/.var/app/com.brave.Browser/config/BraveSoftware/Brave-Browser",
        ],
        "chrome": [
            "~/.config/google-chrome",
            "~/.config/google-chrome-stable",
            "~/snap/google-chrome/current/.config/google-chrome",
            "~/.var/app/com.google.Chrome/config/google-chrome",
        ],
        "chromium": [
            "~/.config/chromium",
            "~/snap/chromium/common/chromium",
            "~/.var/app/org.chromium.Chromium/config/chromium",
        ],
        "edge": [
            "~/.config/microsoft-edge",
            "~/.var/app/com.microsoft.Edge/config/microsoft-edge",
        ],
        "opera": [
            "~/.config/opera",
            "~/snap/opera/common/opera",
            "~/.var/app/com.opera.Opera/config/opera",
        ],
        "vivaldi": [
            "~/.config/vivaldi",
            "~/.var/app/com.vivaldi.Vivaldi/config/vivaldi",
        ],
        "whale": [
            "~/.config/naver-whale",
            "~/.var/app/com.naver.Whale/config/naver-whale",
        ],
    })

FIREFOX_PATHS_LINUX = [
    "~/.mozilla/firefox",
    "~/snap/firefox/common/.mozilla/firefox",
    "~/.var/app/org.mozilla.firefox/.mozilla/firefox",
]

FIREFOX_PATHS_MAC = [
    "~/Library/Application Support/Firefox/Profiles",
    "~/Library/Mozilla/Profiles",
]

FIREFOX_PATHS: List[str] = []
if platform.system() == "Darwin":
    FIREFOX_PATHS = FIREFOX_PATHS_MAC
else:
    FIREFOX_PATHS = FIREFOX_PATHS_LINUX

COOKIE_FILE_NAMES = ["Cookies", "cookies.sqlite", "cookies.sqlite-wal"]


def expand_path(path: str) -> str:
    """Expande ~ e variáveis de ambiente em um caminho."""
    path = os.path.expanduser(path)
    path = os.path.expandvars(path)
    return path


def verify_cookie_file(directory: str, required_size: int = 0) -> bool:
    """Verifica se um diretório de perfil contém um arquivo de cookies válido."""
    if not os.path.isdir(directory):
        return False
    
    cookie_path = Path(directory)
    
    # Para Chromium: procura o arquivo "Cookies" dentro de Default ou Profile X
    for item in os.listdir(directory):
        item_path = cookie_path / item
        if item_path.is_file():
            if item == "Cookies" or item.startswith("Cookies"):
                if item_path.stat().st_size >= required_size:
                    return True
    
    # Verifica subdiretórios de perfis
    for profile_subdir in ["Default", "Profile 1", "Profile 2", "Profile 3", "Profile 4", "Profile 5"]:
        profile_path = cookie_path / profile_subdir
        cookie_file = profile_path / "Cookies"
        if cookie_file.is_file():
            try:
                if cookie_file.stat().st_size >= required_size or required_size == 0:
                    return True
            except OSError:
                pass
    
    return False


def find_chrome_profile(browser: str) -> Optional[str]:
    """
    Encontr a caminho da pasta de perfil para navegadores Chromium.
    Verifica tanto o arquivo Cookies quanto se tem tamanho adequado.
    """
    if browser not in CHROMIUM_PATHS:
        return None
    
    for base_path in [expand_path(p) for p in CHROMIUM_PATHS[browser]]:
        if not os.path.isdir(base_path):
            continue
        
        # Verifica perfil Default
        default_path = os.path.join(base_path, "Default")
        cookie_file = Path(default_path) / "Cookies"
        if cookie_file.is_file():
            try:
                if cookie_file.stat().st_size > 0:
                    return base_path
            except OSError:
                pass
        
        # Verifica perfis numerados (Profile 1, Profile 2, etc.)
        try:
            for item in os.listdir(base_path):
                if item.startswith("Profile ") or item == "Default":
                    profile_path = os.path.join(base_path, item)
                    if os.path.isdir(profile_path):
                        cookie_file = Path(profile_path) / "Cookies"
                        if cookie_file.is_file():
                            try:
                                if cookie_file.stat().st_size > 0:
                                    return base_path
                            except OSError:
                                continue
        except PermissionError:
            continue
        
        # Verifica se o próprio diretório é um perfil
        cookie_file = Path(base_path) / "Cookies"
        if cookie_file.is_file():
            try:
                if cookie_file.stat().st_size > 0:
                    return base_path
            except OSError:
                pass
    
    return None


def parse_firefox_profilesIni(profile_dir: str) -> Optional[str]:
    """Parse profiles.ini e retorna o caminho do primeiro perfil com cookies."""
    profiles_ini = os.path.join(profile_dir, "profiles.ini")
    if not os.path.isfile(profiles_ini):
        return None
    
    try:
        with open(profiles_ini, "r", encoding="utf-8") as f:
            content = f.read()
    except (IOError, UnicodeDecodeError):
        return None
    
    lines = content.split("\n")
    current_profile_name: Optional[str] = None
    current_path: Optional[str] = None
    is_default = False
    
    for line in lines:
        line = line.strip()
        
        if line.startswith("[Profile"):
            if current_path and is_default:
                profile_full_path = os.path.join(profile_dir, current_path)
                cookies_path = Path(profile_full_path) / "cookies.sqlite"
                if cookies_path.is_file() and cookies_path.stat().st_size > 0:
                    return profile_full_path
            
            current_profile_name = None
            current_path = None
            is_default = False
        
        if line.startswith("Default="):
            is_default = line.split("=", 1)[1].strip() == "1"
        
        if line.startswith("Name="):
            current_profile_name = line.split("=", 1)[1].strip()
        
        if line.startswith("Path="):
            current_path = line.split("=", 1)[1].strip()
    
    # Check last profile
    if current_path:
        profile_full_path = os.path.join(profile_dir, current_path)
        cookies_path = Path(profile_full_path) / "cookies.sqlite"
        if cookies_path.is_file() and cookies_path.stat().st_size > 0:
            return profile_full_path
    
    return None


def find_firefox_profile() -> Optional[str]:
    """
    Encontra o perfil Firefox ativo.
    Retorna o caminho do perfil (não o arquivo cookies.sqlite).
    """
    # Ordem de verificação: profiles.ini > perfis por nome
    for base_path in [expand_path(p) for p in FIREFOX_PATHS]:
        if not os.path.isdir(base_path):
            continue
        
        # Primeiro tenta via profiles.ini
        result = parse_firefox_profilesIni(base_path)
        if result:
            return result
        
        # Depois tenta localizar perfis manualmente
        try:
            for item in os.listdir(base_path):
                item_lower = item.lower()
                # Perfis podem ter nomes como: xxxxx.default-release, profile.default, etc.
                if "default" in item_lower:
                    profile_path = os.path.join(base_path, item)
                    if os.path.isdir(profile_path):
                        cookies_path = Path(profile_path) / "cookies.sqlite"
                        if cookies_path.is_file():
                            try:
                                if cookies_path.stat().st_size > 0:
                                    return profile_path
                            except OSError:
                                continue
                        # Também verifica cookies.sqlite-wal
                        wal_path = Path(profile_path) / "cookies.sqlite-wal"
                        if wal_path.is_file() and wal_path.stat().st_size > 0:
                            return profile_path
        except PermissionError:
            continue
    
    return None


def detect_browser_path(browser: str) -> Optional[str]:
    """
    Detecta o caminho do navegador para cookies.
    Retorna o caminho formatado para yt-dlp (ex: "brave:/home/user/.config/BraveSoftware/Brave-Browser").
    """
    browser_lower = browser.lower()
    
    if browser_lower == "firefox" or browser_lower == "safari":
        if browser_lower == "firefox":
            profile_path = find_firefox_profile()
        else:
            # Safari não tem suporte direto - retorna None mas avisa
            return None
        
        if profile_path:
            return f"firefox:{profile_path}"
        return None
    
    if browser_lower in CHROMIUM_PATHS:
        path = find_chrome_profile(browser_lower)
        if path:
            return f"{browser_lower}:{path}"
        return None
    
    return None


def detect_any_browser() -> Optional[Tuple[str, str]]:
    """
    Detecta qualquer navegador com cookies disponíveis.
    Retorna (browser_name, formatted_path) ou None.
    Prioriza navegadores na ordem: brave, chrome, firefox, edge, chromium, opera, vivaldi, whale
    """
    priority_order = ["brave", "chrome", "firefox", "edge", "chromium", "opera", "vivaldi", "whale"]
    
    for browser in priority_order:
        path = detect_browser_path(browser)
        if path:
            return (browser.split(":")[0] if ":" in path else browser, path)
    
    return None


def get_detected_browsers() -> List[Tuple[str, str]]:
    """Retorna lista de todos os navegadores com cookies detectados."""
    results = []
    for browser in CHROMIUM_PATHS.keys():
        if browser == "whale":
            continue  # Tratado separadamente
        path = detect_browser_path(browser)
        if path:
            results.append((browser, path))
    
    ff_path = detect_browser_path("firefox")
    if ff_path:
        results.append(("firefox", ff_path))
    
    return results