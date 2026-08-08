"""
Interface CLI interativa para yks-music.
Design limpo, moderno e responsivo.
"""

import os
import sys
import shlex
import subprocess
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.table import Table
from rich.prompt import Confirm, Prompt
from rich.columns import Columns
from rich.align import Align

from prompt_toolkit import Application
from prompt_toolkit.layout import Layout, HSplit, Window
from prompt_toolkit.buffer import Buffer
from prompt_toolkit.layout.controls import BufferControl, FormattedTextControl
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.formatted_text import FormattedText
from prompt_toolkit.styles import Style

from .config import (
    DEFAULT_AUDIO_FORMAT, MUSIC_BASE, SEARCH_PAGE_SIZE, get_music_base,
    SUPPORTED_BROWSERS, get_cookie_browser, get_cookie_browser_and_path, set_cookie_browser
)
from .downloader import download_playlist, download_video
from .playlist_manager import add_to_playlist, create_playlist, delete_playlist, list_playlists
from .search import search_youtube
from .utils import ensure_base_dir, get_audio_files, get_playlists, is_playlist_url
from .uninstaller import perform_uninstall

console = Console()


def clear_screen():
    """Limpa a tela do terminal."""
    os.system('clear' if os.name == 'posix' else 'cls')


# ASCII art clássico do yks-music
YKS_BANNER = """
 __  __     __  __     ______     __    __     __  __     ______     __     ______    
/\ \_\ \   /\ \/ /    /\  ___\   /\ "-./  \   /\ \/\ \   /\  ___\   /\ \   /\  ___\   
\ \____ \  \ \  _"-.  \ \___  \  \ \ \-./\ \  \ \ \_\ \  \ \___  \  \ \ \  \ \ \____  
 \/\_____\  \ \_\ \_\  \/\_____\  \ \_\ \ \_\  \ \_____\  \/\_____\  \ \_\  \ \_____\ 
  \/_____/   \/_/\/_/   \/_____/   \/_/  \/_/   \/_____/   \/_____/   \/_/   \/_____/ 
"""

def draw_banner():
    """Desenha o banner ASCII clássico do yks-music no topo da tela."""
    console.print(f"[bold cyan]{YKS_BANNER}[/bold cyan]")
    console.print("=" * 70)


def draw_header(title="yks-music", subtitle=""):
    """Desenha um cabeçalho com banner ASCII."""
    clear_screen()
    console.print(f"[bold cyan]{YKS_BANNER}[/bold cyan]")
    console.print("=" * 70)
    if subtitle:
        console.print(f"[dim]{subtitle}[/dim]")


def draw_footer(message="Pressione ENTER para continuar..."):
    """Desenha um rodapé com mensagem."""
    console.print("[dim]" + "─" * 45 + "[/dim]")
    input(f"\n{message}")


def arrow_menu(options, selected=0, page_info=None, allow_pagination=False):
    """Exibe menu navegável com setas do teclado.
    
    Args:
        options (list): Lista de tuplas (ícone, texto).
        selected (int): Índice inicial selecionado.
        page_info (tuple): (página atual, total de páginas) ou None.
        allow_pagination (bool): Se True, permite←→ para mudar página.
    
    Returns:
        int ou None ou especial:
            >= 0: índice da opção selecionada
            None: Esc/voltar
            -1:← (página anterior)
            -2: → (próxima página)
    """
    if not options:
        return None
    
    bindings = KeyBindings()
    
    @bindings.add('up')
    def _(event):
        nonlocal selected
        selected = (selected - 1) % len(options)
        render_menu()
    
    @bindings.add('down')
    def _(event):
        nonlocal selected
        selected = (selected + 1) % len(options)
        render_menu()
    
    @bindings.add('enter')
    def _(event):
        event.app.exit(result=selected)
    
    if allow_pagination:
        @bindings.add('left')
        def _(event):
            event.app.exit(result=-1)
        
        @bindings.add('right')
        def _(event):
            event.app.exit(result=-2)
    
    @bindings.add('c-c')
    @bindings.add('c-q')
    @bindings.add('escape')
    def _(event):
        event.app.exit(result=None)
    
    def render_menu():
        """Renderiza o menu na tela."""
        clear_screen()
        draw_banner()
        console.print()
        
        for i, (icon, text) in enumerate(options):
            if i == selected:
                console.print(f"[bold green]►[/bold green] [bold cyan]{icon}  {text}[/bold cyan]")
            else:
                console.print(f"    {icon}  {text}")
        
        console.print()
        console.print("=" * 70)
        
        # Instruções
        if allow_pagination and page_info:
            current, total = page_info
            pagination_text = f"← Página {current}/{total} →"
            console.print(f"[dim]{pagination_text}    Enter selecionar    Esc voltar[/dim]")
        else:
            console.print("[dim]↑↓ navegar  Enter selecionar  Esc voltar[/dim]")
        
        console.print("=" * 70)
    
    render_menu()
    
    try:
        buf = Buffer()
        layout = Layout(HSplit([
            Window(BufferControl(buffer=buf)),
        ]))
        
        style = Style.from_dict({})
        app = Application(layout=layout, key_bindings=bindings, style=style, full_screen=False)
        result = app.run()
        
        return result
    except (EOFError, KeyboardInterrupt):
        return None


def draw_menu(title, options, back_option=True, subtitle=""):
    """Desenha um menu navegável com setas do teclado.
    
    Args:
        title (str): Título do menu.
        options (list): Lista de tuplas (ícone, texto).
        back_option (bool): Se True, adiciona opção de voltar.
        subtitle (str): Subtítulo opcional.
    """
    # Adiciona opção de voltar se necessário
    menu_options = list(options)
    if back_option:
        menu_options.append(("", "Voltar"))
    
    # Se não há opções, retorna None
    if not menu_options:
        return None
    
    # Usa arrow_menu para navegação com setas
    result = arrow_menu(menu_options)
    
    if result is None:
        return None
    
    # Se selecionou a última opção (Voltar), retorna None
    if back_option and result == len(menu_options) - 1:
        return None
    
    return result

def show_info_panel(title, content, border_color="cyan"):
    """Mostra um painel informativo estilizado."""
    panel = Panel(
        Text(content, justify="left"),
        title=f" {title} ",
        border_style=border_color,
        padding=(1, 2)
    )
    console.print(panel)


def _show_video_details(video):
    """Mostra detalhes de um vídeo de forma limpa."""
    console.print(f"[bold cyan]▶ {video['title']}[/bold cyan]")
    console.print(f"  [dim]ID:[/dim] [yellow]{video['id']}[/yellow]")
    console.print(f"  [dim]Duração:[/dim] [green]{video.get('duration', 'Desconhecida')}[/green]")
    console.print(f"  [dim]Link:[/dim] [blue]https://youtu.be/{video['id'][:10]}...[/blue]")
def _handle_video_selection(video):
    """Lida com a seleção de um vídeo para download."""
    draw_header("yks-music", "Detalhes da Música")
    _show_video_details(video)
    console.print("[dim]" + "─" * 45 + "[/dim]")
    
    playlists = get_playlists()
    save_options = [("󰏓 ", "Raíz (Músicas Avulsas)")]
    for p in playlists:
        save_options.append(("", f"Playlist: {p}"))
    save_options.append(("", "Criar Nova Playlist"))
    
    save_idx = draw_menu("Salvar em:", save_options, back_option=True)
    
    if save_idx is None:
        return
    
    if save_idx == 0:
        target_dir = MUSIC_BASE
    else:
        playlist_name = playlists[save_idx - 1] if save_idx - 1 < len(playlists) else None
        if playlist_name:
            target_dir = MUSIC_BASE / playlist_name
        else:
            new_name = Prompt.ask("Nome da nova playlist")
            if new_name:
                target_dir = MUSIC_BASE / new_name
                target_dir.mkdir(parents=True, exist_ok=True)
                console.print(f"[green]✓ Playlist '{new_name}' criada.[/green]")
            else:
                return
    
    console.print(f"[yellow]Baixando: {video['title']}[/yellow]")
    success = download_video(f"https://youtu.be/{video['id']}", output_dir=target_dir)
    console.print("[bold green]✅ Concluído![/bold green]" if success else "[bold red]❌ Falha no download.[/bold red]")
    input("\nPressione ENTER para continuar...")


def search_menu():
    """Menu para pesquisar e baixar músicas com paginação."""
    query = ""
    current_page = 1
    results = []
    total_pages = 1
    
    while True:
        if not results:
            if query:
                new_query = Prompt.ask("Pesquisar", default=query)
            else:
                new_query = Prompt.ask("Pesquisar")
            
            if not new_query.strip():
                return
            
            query = new_query
            current_page = 1
            results = search_youtube(query, current_page)
            if len(results) >= SEARCH_PAGE_SIZE:
                total_pages = current_page + 1
            else:
                total_pages = current_page
        
        options = []
        for item in results:
            title = item['title']
            duration = item.get('duration', '??:??')
            options.append(("", f"{title} [{duration}]"))
        
        result = arrow_menu(
            options,
            page_info=(current_page, total_pages),
            allow_pagination=True
        )
        
        if result is None:
            return
        
        if result == -1:
            if current_page > 1:
                current_page -= 1
                results = search_youtube(query, current_page)
            continue
        
        if result == -2:
            current_page += 1
            new_results = search_youtube(query, current_page)
            if new_results:
                results = new_results
                total_pages = max(total_pages, current_page)
            else:
                current_page -= 1
            continue
        
        if 0 <= result < len(results):
            video = results[result]
            _handle_video_selection(video)
        
        results = search_youtube(query, current_page)
def download_from_search_in_playlist(results, playlist_name):
    """Permite escolher e baixar um resultado da pesquisa para uma playlist específica."""
    if not results:
        return
    
    # Cria opções a partir dos resultados
    options = []
    for item in results:
        title = item['title']
        title_short = title[:50] + ("…" if len(title) > 50 else "")
        duration = item.get('duration', '??:??')
        options.append(("", f"{title_short} [{duration}]"))
    
    # Usa arrow_menu para selecionar
    selected = arrow_menu(options)
    
    if selected is None:
        return
    
    video = results[selected]
    url = f"https://youtu.be/{video['id']}"
    target_dir = MUSIC_BASE / playlist_name
    
    console.print(f"[yellow]Baixando: {video['title']}[/yellow]")
    success = download_video(url, output_dir=target_dir)
    console.print("[bold green]✅ Concluído![/bold green]" if success else "[bold red]❌ Falha no download.[/bold red]")
    input("\nPressione ENTER para continuar...")


def direct_download_menu():
    """Menu para download direto por link."""
    while True:
        url = Prompt.ask("Cole o link do YouTube (ou 0 para voltar)")
        
        if url.strip() == "0":
            return
        
        if not url.strip():
            continue
        
        if not (url.startswith("http://") or url.startswith("https://")):
            console.print("[red]  URL inválida. Deve começar com http:// ou https://[/red]")
            continue
        
        # Pergunta onde salvar
        save_options = [("󰏓 ", "Raíz (Músicas Avulsas)")]
        playlists = get_playlists()
        for p in playlists:
            save_options.append((" ", f"Playlist: {p}"))
        save_options.append((" ", "Criar Nova Playlist"))
        
        save_idx = draw_menu("Salvar em:", save_options, back_option=True)
        
        if save_idx is None:
            continue
        
        if save_idx == 0:
            target_dir = MUSIC_BASE
        else:
            playlist_name = playlists[save_idx - 1] if save_idx - 1 < len(playlists) else None
            if playlist_name:
                target_dir = MUSIC_BASE / playlist_name
            else:
                new_name = Prompt.ask("Nome da nova playlist")
                if new_name:
                    target_dir = MUSIC_BASE / new_name
                    target_dir.mkdir(parents=True, exist_ok=True)
                    console.print(f"[green]✓ Playlist '{new_name}' criada.[/green]")
                else:
                    continue
        
        # Fazer download
        if is_playlist_url(url):
            console.print(f"[yellow]Baixando playlist para: {target_dir}[/yellow]")
            success = download_playlist(url, target_dir)
        else:
            console.print(f"[yellow]Baixando música para: {target_dir}[/yellow]")
            success = download_video(url, output_dir=target_dir)
        
        console.print("[bold green]✅ Concluído![/bold green]" if success else "[bold red]❌ Falha no download.[/bold red]")
        input("\nPressione ENTER para continuar...")
        return


def playlist_management_menu():
    """Menu para gerenciar playlists."""
    while True:
        options = [
            (" ", "Criar Nova Playlist"),
            (" ", "Criar Playlist de Link"),
            (" ", "Listar Playlists"),
            (" ", "Adicionar Música a Playlist"),
            (" ", "Deletar Playlist"),
        ]
        
        idx = draw_menu("Gerenciar Playlists", options, back_option=True)
        
        if idx is None:
            return
        
        if idx == 0:
            name = Prompt.ask("Nome da nova playlist")
            if name:
                success = create_playlist(name)
                if success:
                    console.print("[green]✓ Playlist criada com sucesso![/green]")
                else:
                    console.print("[red]  Falha ao criar playlist.[/red]")
                input("\nPressione ENTER para continuar...")

        elif idx == 1:
            url = Prompt.ask("Cole o link da playlist do YouTube")
            if url:
                name = Prompt.ask("Nome da nova playlist")
                if name:
                    target = MUSIC_BASE / name
                    if target.exists():
                        console.print(f"[red]Playlist '{name}' já existe.[/red]")
                    else:
                        success = create_playlist(name)
                        if success:
                            console.print(f"[yellow]Baixando playlist para: {target}[/yellow]")
                            download_playlist(url, target)
                            console.print("[green]✓ Playlist criada e baixada com sucesso![/green]")
                input("\nPressione ENTER para continuar...")

        elif idx == 2:
            show_playlist_list()
            
        elif idx == 3:
            add_music_to_playlist()
            
        elif idx == 4:
            delete_playlist_menu()


def show_playlist_list():
    """Mostra lista de playlists com suas músicas."""
    playlists = get_playlists()
    
    draw_header("yks-music", "Minhas Playlists")
    
    if not playlists:
        console.print("[yellow]Nenhuma playlist criada.[/yellow]")
        draw_footer("Crie uma playlist usando 'playlist create <nome>'")
        input("\nPressione ENTER para continuar...")
        return
    
    console.print("[bold yellow] Playlists[/bold yellow]")
    console.print("[dim]" + "─" * 45 + "[/dim]")
    
    for i, p in enumerate(playlists, 1):
        playlist_path = MUSIC_BASE / p
        songs = get_audio_files(playlist_path)
        status = "[green]●[/green] " if songs else "[dim]○[/dim] "
        console.print(f" {status}[cyan]{p}[/cyan]  [dim]({len(songs)} músicas)[/dim]")
    
    console.print("[dim]" + "─" * 45 + "[/dim]")
    
    # Mostrar detalhes das playlists
    for p in playlists:
        songs = get_audio_files(MUSIC_BASE / p)
        if songs:
            console.print(f"\n[bold]{p}[/bold]")
            for song in songs[:3]:  # Limita a 3 para preview
                console.print(f"  [dim]- {song}[/dim]")
            if len(songs) > 3:
                console.print(f"  [dim]… e mais {len(songs) - 3} música(s)[/dim]")
        else:
            console.print(f"\n[bold]{p}[/bold] [dim](vazia)[/dim]")
    
    draw_footer()
    input("\nPressione ENTER para continuar...")


def add_music_to_playlist():
    """Adiciona música a uma playlist existente."""
    playlists = get_playlists()
    
    if not playlists:
        console.print("[yellow]Nenhuma playlist disponível. Crie uma primeiro.[/yellow]")
        input("\nPressione ENTER para continuar...")
        return
    
    playlist_options = [(f" ", p) for p in playlists]
    idx = draw_menu("Selecione a playlist", playlist_options, back_option=True)
    
    if idx is None:
        return
    
    selected_playlist = playlists[idx]
    console.print(f"[cyan]Adicionando música à playlist: {selected_playlist}[/cyan]")
    
    # Pergunta pelo link ou pesquisa
    add_options = [
        (" ", "Pesquisar e adicionar"),
        (" ", "Adicionar por link"),
    ]
    
    add_idx = draw_menu("Como deseja adicionar?", add_options, back_option=True)
    
    if add_idx is None:
        return
    
    if add_idx == 0:  # Pesquisar
        query = Prompt.ask("Digite o termo de pesquisa")
        if query:
            results = search_youtube(query, SEARCH_PAGE_SIZE)
            if results:
                download_from_search_in_playlist(results, selected_playlist)
            else:
                console.print("[yellow]Nenhum resultado encontrado.[/yellow]")
                input("\nPressione ENTER para continuar...")
                
    elif add_idx == 1:  # Link
        url = Prompt.ask("Cole o link do YouTube")
        if url and (url.startswith("http://") or url.startswith("https://")):
            target_dir = MUSIC_BASE / selected_playlist
            if is_playlist_url(url):
                console.print(f"[yellow]Baixando playlist para: {target_dir}[/yellow]")
                success = download_playlist(url, target_dir)
            else:
                console.print(f"[yellow]Baixando música para: {target_dir}[/yellow]")
                success = download_video(url, output_dir=target_dir)
            console.print("[bold green]✅ Concluído![/bold green]" if success else "[bold red]❌ Falha no download.[/bold red]")
            input("\nPressione ENTER para continuar...")
        else:
            console.print("[red]URL inválida.[/red]")
            input("\nPressione ENTER para continuar...")


def delete_playlist_menu():
    """Menu para deletar uma playlist."""
    playlists = get_playlists()
    
    if not playlists:
        console.print("[yellow]Nenhuma playlist para deletar.[/yellow]")
        input("\nPressione ENTER para continuar...")
        return
    
    playlist_options = [(f" ", p) for p in playlists]
    idx = draw_menu("Selecione a playlist para deletar", playlist_options, back_option=True)
    
    if idx is None:
        return
    
    selected_playlist = playlists[idx]
    playlist_path = MUSIC_BASE / selected_playlist
    songs = get_audio_files(playlist_path)
    
    console.print(f"[yellow]Playlist: {selected_playlist}[/yellow]")
    console.print(f" Músicas: {len(songs)}")
    
    if songs:
        console.print(f"[red]⚠ A playlist '{selected_playlist}' contém {len(songs)} música(s).[/red]")
        console.print("[red]Todas as músicas serão perdidas![/red]")
    else:
        console.print(f"[yellow]Playlist '{selected_playlist}' está vazia.[/yellow]")
    
    if Confirm.ask(f"[red]Tem certeza que deseja deletar '{selected_playlist}'?[/red]"):
        success = delete_playlist(selected_playlist)
        if success:
            console.print("[green]✓ Playlist deletada com sucesso![/green]")
        else:
            console.print("[red]  Falha ao deletar playlist.[/red]")
        input("\nPressione ENTER para continuar...")


def list_music_menu():
    """Menu para listar músicas baixadas."""
    while True:
        options = [
            ("󰏓 ", "Músicas Avulsas"),
            (" ", "Playlists"),
            (" ", "Tudo"),
        ]
        
        idx = draw_menu("Listar Músicas", options, back_option=True)
        
        if idx is None:
            return
        
        draw_header("yks-music", "Listar Músicas")
        
        if idx == 0:  # Músicas avulsas
            console.print("[bold yellow] Músicas Avulsas[/bold yellow]")
            console.print("[dim]" + "─" * 45 + "[/dim]")
            songs = get_audio_files(MUSIC_BASE)
            if songs:
                for i, song in enumerate(songs, 1):
                    console.print(f" [dim]{i}.[/dim] {song}")
            else:
                console.print("[yellow]Nenhuma música avulsa.[/yellow]")
            console.print("[dim]" + "─" * 45 + "[/dim]")
            
        elif idx == 1:  # Playlists
            show_playlist_list()
            continue
            
        elif idx == 2:  # Tudo
            console.print("[bold yellow] Todas as Músicas[/bold yellow]")
            console.print("[dim]" + "─" * 45 + "[/dim]")
            
            # Músicas avulsas
            songs = get_audio_files(MUSIC_BASE)
            if songs:
                console.print("[bold cyan]Músicas Avulsas:[/bold cyan]")
                for song in songs:
                    console.print(f"  [dim]- {song}[/dim]")
            
            # Playlists
            playlists = get_playlists()
            if playlists:
                console.print("\n[bold cyan]Playlists:[/bold cyan]")
                for p in playlists:
                    console.print(f"  [cyan]{p}/[/cyan]")
                    pl_songs = get_audio_files(MUSIC_BASE / p)
                    if pl_songs:
                        for s in pl_songs:
                            console.print(f"    [dim]- {s}[/dim]")
                    else:
                        console.print("    [dim](vazia)[/dim]")
            
            console.print("[dim]" + "─" * 45 + "[/dim]")
        
        draw_footer()
        input("\nPressione ENTER para continuar...")


def settings_menu():
    """Menu de configurações."""
    while True:
        options = [
            ("󰈀 ", "Pasta de Músicas"),
            (" ", "Formato Padrão"),
            (" ", "Cookies do Navegador"),
            (" ", "Verificar Dependências"),
            (" ", "Informações do Sistema"),
        ]
        
        idx = draw_menu("Configurações", options, back_option=True)
        
        if idx is None:
            return
        
        if idx == 0:  # Pasta de músicas
            show_music_folder_info()
            
        elif idx == 1:  # Formato padrão
            current_fmt = DEFAULT_AUDIO_FORMAT
            new_fmt = Prompt.ask("Formato de áudio padrão (mp3|m4a|opus)", default=current_fmt)
            if new_fmt.lower() in ("mp3", "m4a", "opus", "flac", "wav"):
                console.print(f"[green]✓ Formato atualizado para: {new_fmt}[/green]")
            else:
                console.print("[red]  Formato não suportado.[/red]")
            input("\nPressione ENTER para continuar...")
        
        elif idx == 2:  # Cookies do navegador
            cookie_settings_menu()
            
        elif idx == 3:  # Verificar dependências
            check_dependencies()
            
        elif idx == 4:  # Informações
            show_system_info()


def cookie_settings_menu():
    """Menu para configurar o navegador de cookies."""
    current_browser, cookies_path = get_cookie_browser_and_path()
    current_browser_display = current_browser
    if cookies_path and ":" in cookies_path:
        current_browser_display = f"{current_browser} @ {cookies_path.split(':', 1)[1]}"
    
    def get_install_method(path: str) -> str:
        if "snap" in path:
            return "snap"
        elif ".var/app" in path:
            return "flatpak"
        else:
            return "native"
    
    def get_browser_sources(browser: str) -> dict:
        native = snap = flatpak = ""
        if browser == "firefox":
            native = "~/.mozilla/firefox"
            snap = "~/snap/firefox/common/.mozilla/firefox"
            flatpak = "~/.var/app/org.mozilla.firefox/.mozilla/firefox"
        else:
            native = os.path.expanduser(f"~/.config/{browser.capitalize()[:-1]}")
            flatpak = os.path.expanduser(f"~/.var/app/com.{browser}.Browser/config/{browser.capitalize()}")
        return {"native": native, "snap": snap, "flatpak": flatpak}
    
    while True:
        options = []
        for browser in SUPPORTED_BROWSERS:
            if browser == current_browser:
                options.append(("", f"{browser}  (atual)"))
            else:
                options.append(("", browser))
        options.append(("", "🔄 Redetectar automaticamente"))
        
        idx = arrow_menu(options)
        
        if idx is None:
            return
        
        if 0 <= idx < len(SUPPORTED_BROWSERS):
            selected_browser = SUPPORTED_BROWSERS[idx]
            
            # Detectar caminho automaticamente
            from .detector_cookie import detect_browser_path
            new_path = detect_browser_path(selected_browser)
            
            if new_path:
                install_method = get_install_method(new_path)
                sources = get_browser_sources(selected_browser)
                
                # Atualizar config.json com todos os campos
                from .config import save_config
                import json
                from datetime import datetime
                
                config_data = {
                    "cookie_browser": new_path,
                    "browser": selected_browser,
                    "profile_path": new_path.split(":", 1)[1],
                    "install_method": install_method,
                    "sources": sources,
                    "detected_at": datetime.now().isoformat()
                }
                save_config(config_data)
                
                current_browser = selected_browser
                current_browser_display = f"{selected_browser} @ {new_path.split(':', 1)[1]}"
                console.print(f"[green]✓ Navegador alterado: {selected_browser}[/green]")
                console.print(f"[green]✓ Caminho: {new_path.split(':', 1)[1]}[/green]")
                console.print(f"[green]✓ Método: {install_method}[/green]")
            else:
                console.print(f"[yellow]! Navegador {selected_browser} não encontrado[/yellow]")
                # Salvar apenas o nome caso não encontre caminho
                from .config import set_cookie_browser
                set_cookie_browser(selected_browser)
                current_browser = selected_browser
            input("\nPressione ENTER para continuar...")
            return
        
        if idx == len(options) - 1:
            from .detector_cookie import detect_browser_path
            new_path = detect_browser_path(current_browser)
            if new_path:
                install_method = get_install_method(new_path)
                sources = get_browser_sources(current_browser)
                
                from .config import save_config
                import json
                from datetime import datetime
                
                config_data = {
                    "cookie_browser": new_path,
                    "browser": current_browser,
                    "profile_path": new_path.split(":", 1)[1],
                    "install_method": install_method,
                    "sources": sources,
                    "detected_at": datetime.now().isoformat()
                }
                save_config(config_data)
                
                current_browser_display = f"{current_browser} @ {new_path.split(':', 1)[1]}"
                console.print(f"[green]✓ Caminho detectado: {new_path.split(':', 1)[1]}[/green]")
                console.print(f"[green]✓ Método: {install_method}[/green]")
            else:
                console.print(f"[yellow]! Navegador {current_browser} não encontrado[/yellow]")
            input("\nPressione ENTER para continuar...")
            return


def show_music_folder_info():
    """Mostra informações sobre a pasta de músicas."""
    draw_header("yks-music", "Pasta de Músicas")
    
    console.print("[bold yellow] Informações da Pasta[/bold yellow]")
    console.print("[dim]" + "─" * 45 + "[/dim]")
    console.print(f"  Caminho: [cyan]{MUSIC_BASE}[/cyan]")
    console.print(f"  Existe: {'[green]✓ Sim[/green]' if MUSIC_BASE.exists() else '[red]✗ Não[/red]'}")
    
    if MUSIC_BASE.exists():
        total_files = sum(1 for f in MUSIC_BASE.rglob('*') if f.is_file())
        total_size = sum(f.stat().st_size for f in MUSIC_BASE.rglob('*') if f.is_file())
        size_mb = total_size / (1024 * 1024)
        
        console.print(f"  Total de arquivos: {total_files}")
        console.print(f"  Tamanho total: {size_mb:.2f} MB")
        
        playlists = get_playlists()
        console.print(f"  Playlists: {len(playlists)}")
        if playlists:
            for p in playlists:
                songs = get_audio_files(MUSIC_BASE / p)
                console.print(f"    [cyan]- {p}[/cyan] ({len(songs)} músicas)")
    
    console.print("[dim]" + "─" * 45 + "[/dim]")
    draw_footer()
    input("\nPressione ENTER para continuar...")


def check_dependencies():
    """Verifica se as dependências estão instaladas."""
    draw_header("yks-music", "Verificar Dependências")
    
    console.print("[bold yellow] Dependências do Sistema[/bold yellow]")
    console.print("[dim]" + "─" * 45 + "[/dim]")
    
    import shutil
    deps = {
        "yt-dlp": "yt-dlp",
        "ffmpeg": "ffmpeg",
    }
    
    for name, cmd in deps.items():
        path = shutil.which(cmd)
        if path:
            console.print(f"  [green]✓[/green] {name}: {path}")
        else:
            console.print(f"  [red]✗[/red] {name}: Não encontrado")
    
    console.print("[dim]" + "─" * 45 + "[/dim]")
    
    console.print("\n[bold yellow] Dependências Python (instaladas no .venv)[/bold yellow]")
    console.print("[dim]" + "─" * 45 + "[/dim]")
    
    python_deps = ["rich", "pyfiglet"]
    for dep in python_deps:
        try:
            mod = __import__(dep)
            version = getattr(mod, '__version__', 'instalada')
            console.print(f"  [green]✓[/green] {dep}: {version}")
        except ImportError:
            console.print(f"  [red]✗[/red] {dep}: Não instalada")
    
    console.print("[dim]" + "─" * 45 + "[/dim]")
    draw_footer()
    input("\nPressione ENTER para continuar...")


def show_system_info():
    """Mostra informações do sistema."""
    import platform
    
    draw_header("yks-music", "Informações do Sistema")
    
    console.print("[bold yellow] Sobre[/bold yellow]")
    console.print("[dim]" + "─" * 45 + "[/dim]")
    console.print(f"  Versão: [cyan]1.0.0[/cyan]")
    console.print(f"  Python: {platform.python_version()}")
    console.print(f"  Sistema: {platform.system()} {platform.release()}")
    console.print(f"  Plataforma: {platform.platform()}")
    console.print(f"  Diretório base: {MUSIC_BASE}")
    console.print("[dim]" + "─" * 45 + "[/dim]")
    
    console.print("\n[bold yellow] Diretórios[/bold yellow]")
    console.print("[dim]" + "─" * 45 + "[/dim]")
    console.print(f"  Executável: ~/.local/bin/yks-music")
    console.print(f"  Virtual env: {MUSIC_BASE.parent.parent if 'yks-musics' in str(MUSIC_BASE) else 'N/A'}")
    console.print(f"  Pasta de músicas: {MUSIC_BASE}")
    console.print("[dim]" + "─" * 45 + "[/dim]")
    
    draw_footer()
    input("\nPressione ENTER para continuar...")


def show_help():
    """Exibe tela de ajuda detalhada com exemplos."""
    draw_header("yks-music", "Ajuda")
    
    help_text = """
[bold cyan]yks-music[/bold cyan] - CLI para baixar músicas do YouTube
[dim]Uma ferramenta simples e interativa para baixar músicas e playlists.[/dim]

[bold yellow]   Pesquisar Músicas[/bold yellow]
Digite o nome da música ou artista quando solicitado.
Os resultados serão exibidos numerados. Use o número para baixar.

[bold yellow] 󰇚  Download Direto[/bold yellow]
Cole qualquer link do YouTube (vídeo ou playlist) para baixar.

[bold yellow]   Playlists[/bold yellow]
Criar, deletar e adicionar músicas a playlists organizadas.

[bold yellow] 󰎘  Comandos Úteis[/bold yellow]
  1] - Selecionar opção pelo número
  0] - Voltar/cancelar
  [ENTER] - Confirmar

[bold green]   Exemplos de uso:[/bold green]
  search "Imagine Dragons"
  download https://youtu.be/dQw4w9WgXcQ
  playlist create "Minhas Favoritas"
  playlist add "Minhas Favoritas" https://youtu.be/abc123
"""
    console.print(help_text)
    
    draw_footer("Pressione ENTER para voltar ao menu principal")
    input()


def main_menu():
    """Menu principal do yks-music."""
    while True:
        options = [
            (" ", "Pesquisar Músicas"),
            ("󰇚 ", "Download Direto"),
            (" ", "Gerenciar Playlists"),
            (" ", "Listar Músicas"),
            (" ", "Configurações"),
            (" ", "Ajuda"),
            ("󰈆 ", "Sair"),
        ]
        
        idx = draw_menu("Menu Principal", options, back_option=False)
        
        if idx is None:
            return
        
        if idx == 0:
            search_menu()
            
        elif idx == 1:
            direct_download_menu()
            
        elif idx == 2:
            playlist_management_menu()
            
        elif idx == 3:
            list_music_menu()
            
        elif idx == 4:
            settings_menu()
            
        elif idx == 5:
            show_help()
            
        elif idx == 6:
            # Sair
            console.print("\n[green]Até logo![/green]")
            return


def main():
    """Ponto de entrada CLI."""
    ensure_base_dir()
    
    # Tratar comando 'uninstall' antes de iniciar o menu
    if len(sys.argv) > 1 and sys.argv[1] == "uninstall":
        perform_uninstall()
        return
    
    # Captura Ctrl+C para sair limparsmente
    try:
        main_menu()
    except KeyboardInterrupt:
        console.print("\n[green]Até logo![/green]")
        return


if __name__ == "__main__":
    main()
