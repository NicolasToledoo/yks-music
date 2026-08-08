"""
Detector de cookies para navegadores suportados pelo yt-dlp.
Detecta automaticamente os caminhos dos bancos de dados de cookies.
"""

import os
from pathlib import Path
from typing import Optional, Tuple, List


CHROMIUM_BASE_PATHS = {
    "brave": [
        "~/.config/BraveSoftware/Brave-Browser",
        "~/.var/app/com.brave.Browser/config/BraveSoftware/Brave-Browser",
    ],
    "chrome": [
        "~/.config/google-chrome",
        "~/.config/google-chrome-stable",
        "~/.var/app/com.google.Chrome/config/google-chrome",
    ],
    "chromium": [
        "~/.config/chromium",
        "~/.var/app/org.chromium.Chromium/config/chromium",
    ],
    "edge": [
        "~/.config/microsoft-edge",
        "~/.var/app/com.microsoft.Edge/config/microsoft-edge",
    ],
    "opera": [
        "~/.config/opera",
        "~/.var/app/com.opera.Opera/config/opera",
    ],
    "vivaldi": [
        "~/.config/vivaldi",
        "~/.var/app/com.vivaldi.Vivaldi/config/vivaldi",
    ],
    "whale": [
        "~/.config/naver-whale",
    ],
}

FIREFOX_BASE_PATHS = [
    "~/.mozilla/firefox",
    "~/.var/app/org.mozilla.firefox/.mozilla/firefox",
    "~/.snap/firefox/common/.mozilla/firefox",
]


def expand_path(path: str) -> str:
    """Expande ~ e variáveis de ambiente em um caminho."""
    path = os.path.expanduser(path)
    path = os.path.expandvars(path)
    return path


def find_chrome_cookie_path(browser: str) -> Optional[str]:
    """
    Encontra o caminho da pasta de perfil para navegadores Chromium.
    Retorna o caminho da pasta base (não do arquivo Cookies).
    """
    if browser not in CHROMIUM_BASE_PATHS:
        return None
    
    paths_to_check = [expand_path(p) for p in CHROMIUM_BASE_PATHS[browser]]
    
    for base_path in paths_to_check:
        if not os.path.isdir(base_path):
            continue
        
        profile_names = ["Default", "Profile 1", "Profile 2", "Profile 3", "Profile 4", "Profile 5"]
        
        for profile in profile_names:
            cookie_file = os.path.join(base_path, profile, "Cookies")
            if os.path.isfile(cookie_file):
                return base_path
        
        try:
            subdirs = [d for d in os.listdir(base_path) if os.path.isdir(os.path.join(base_path, d))]
            for subdir in subdirs:
                if subdir.startswith("Profile ") or subdir == "Default":
                    cookie_file = os.path.join(base_path, subdir, "Cookies")
                    if os.path.isfile(cookie_file):
                        return base_path
        except PermissionError:
            continue
    
    return None


def find_firefox_profile() -> Optional[Tuple[str, str, str]]:
    """
    Encontra o perfil Firefox ativo.
    Retorna (profile_path, profile_name, cookie_file_path).
    """
    for base_path in [expand_path(p) for p in FIREFOX_BASE_PATHS]:
        if not os.path.isdir(base_path):
            continue
        
        profiles_ini = os.path.join(base_path, "profiles.ini")
        if os.path.isfile(profiles_ini):
            try:
                with open(profiles_ini, "r") as f:
                    content = f.read()
                
                lines = content.split("\n")
                current_profile_id = None
                default_found = False
                
                for i, line in enumerate(lines):
                    line_stripped = line.strip()
                    
                    if line_stripped.startswith("[Profile"):
                        current_profile_id = i
                    
                    if line_stripped == "Default=1" and current_profile_id is not None:
                        default_found = True
                    
                    if line_stripped.startswith("Path=") and current_profile_id is not None:
                        profile_rel_path = line_stripped.split("=", 1)[1].strip()
                        
                        if "Relative=" in lines[current_profile_id] if current_profile_id < len(lines) else False:
                            pass
                        
                        profile_path = os.path.join(base_path, profile_rel_path)
                        if not os.path.isabs(profile_rel_path):
                            if os.path.isfile(os.path.join(profile_path, "cookies.sqlite")):
                                return (profile_path, profile_rel_path, os.path.join(profile_path, "cookies.sqlite"))
                        else:
                            if os.path.isdir(profile_path) and os.path.isfile(os.path.join(profile_path, "cookies.sqlite")):
                                return (profile_path, profile_rel_path, os.path.join(profile_path, "cookies.sqlite"))
            except (IOError, PermissionError):
                pass
        
        try:
            for item in os.listdir(base_path):
                lower_item = item.lower()
                if "default" in lower_item or lower_item == "default-release":
                    profile_path = os.path.join(base_path, item)
                    if os.path.isdir(profile_path):
                        for sqlite_file in ["cookies.sqlite", "cookies.sqlite-wal"]:
                            if os.path.isfile(os.path.join(profile_path, sqlite_file)) or \
                               os.path.isfile(os.path.join(profile_path, "cookies.sqlite")):
                                return (profile_path, item, os.path.join(profile_path, "cookies.sqlite"))
        except PermissionError:
            continue
    
    return None


def find_all_firefox_profiles() -> List[Tuple[str, str]]:
    """Encontra todos os perfis Firefox disponíveis."""
    profiles = []
    
    for base_path in [expand_path(p) for p in FIREFOX_BASE_PATHS]:
        if not os.path.isdir(base_path):
            continue
        
        if os.path.isfile(os.path.join(base_path, "cookies.sqlite")):
            for item in os.listdir(base_path):
                full_path = os.path.join(base_path, item)
                if os.path.isdir(full_path):
                    if os.path.isfile(os.path.join(full_path, "cookies.sqlite")):
                        profiles.append((full_path, item))
        
        profiles_ini = os.path.join(base_path, "profiles.ini")
        if os.path.isfile(profiles_ini):
            try:
                with open(profiles_ini, "r") as f:
                    content = f.read()
                
                paths = set()
                lines = content.split("\n")
                
                for line in lines:
                    if line.startswith("Path="):
                        path_val = line.split("=", 1)[1].strip()
                        paths.add(path_val)
                
                for path_val in paths:
                    profile_path = os.path.join(base_path, path_val)
                    if os.path.isdir(profile_path) and path_val not in [p[1] for p in profiles]:
                        if os.path.isfile(os.path.join(profile_path, "cookies.sqlite")):
                            profiles.append((profile_path, path_val))
            except (IOError, PermissionError):
                pass
    
    return profiles


def detect_browser_path(browser: str) -> Optional[str]:
    """
    Detecta o caminho do navegador para cookies.
    Retorna o caminho formatado para yt-dlp.
    
    Exemplos de saída:
    - "chrome:/home/user/.config/google-chrome"
    - "firefox:/home/user/.mozilla/firefox/abc123.default-release"
    """
    browser_lower = browser.lower()
    
    if browser_lower == "firefox":
        result = find_firefox_profile()
        if result:
            profile_path, profile_name, _ = result
            return f"firefox:{profile_path}"
        return None
    
    if browser_lower in CHROMIUM_BASE_PATHS:
        path = find_chrome_cookie_path(browser_lower)
        if path:
            return f"{browser_lower}:{path}"
        return None
    
    return None


def detect_any_browser() -> Optional[Tuple[str, str]]:
    """
    Detecta qualquer navegador com cookies disponíveis.
    Retorna (browser_name, formatted_path) ou None.
    """
    for browser in list(CHROMIUM_BASE_PATHS.keys()) + ["firefox"]:
        path = detect_browser_path(browser)
        if path:
            return (browser.split(":")[0] if ":" in path else browser, path)
    return None