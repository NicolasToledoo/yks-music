"""
Módulo de busca no YouTube usando yt-dlp.
"""

import subprocess

from .config import SEARCH_PAGE_SIZE, YTDLP_CMD, get_yt_dlp_path


def search_youtube(query: str, page: int = 1, page_size: int = SEARCH_PAGE_SIZE) -> list[dict]:
    """
    Pesquisa no YouTube usando yt-dlp com paginação real.
    
    Args:
        query: Termo de pesquisa
        page: Número da página (começa em 1)
        page_size: Resultados por página
    
    Returns:
        Lista de dicionários com 'title' e 'duration'
    """
    start = (page - 1) * page_size + 1
    end = page * page_size
    
    cmd = [
        get_yt_dlp_path(),
        f"ytsearch{end}:{query}",
        f"--playlist-items={start}:{end}",
        "--print", "%(id)s|||%(title)s|||%(duration_string)s",
        "--no-playlist", "--flat-playlist",
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        lines = result.stdout.strip().splitlines()

        items = []
        for line in lines:
            if "|||" in line:
                parts = line.split("|||", 2)
                if len(parts) == 3:
                    vid_id, title, duration = parts
                    vid_id = vid_id.strip()
                    title = title.strip()
                    duration = duration.strip()
                    if title:
                        items.append({
                            "id": vid_id,
                            "title": title,
                            "duration": duration if duration else "??:??"
                        })
        return items
    except subprocess.CalledProcessError as e:
        print(f"❌ Erro na pesquisa: {e.stderr}")
        return []
