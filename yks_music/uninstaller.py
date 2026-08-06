"""
Modulo de desinstalacao do yks-music.
Remove o comando global, configuracoes, musicas e o pacote Python.
"""

import os
import sys
import shutil
from pathlib import Path
from rich.prompt import Confirm
from rich.console import Console

console = Console()


def get_install_info():
    """Retorna informacoes sobre a instalacao atual."""
    local_bin = Path.home() / ".local" / "bin" / "yks-music"
    cache_dir = Path.home() / ".cache" / "yks-music"
    config_dir = Path.home() / ".config" / "yks-music"
    music_dir = Path.home() / "Músicas" / "yks-musics"

    return {
        "command_path": local_bin,
        "cache_dir": cache_dir,
        "config_dir": config_dir,
        "music_dir": music_dir,
    }


def perform_uninstall():
    """Realiza a desinstalacao completa do yks-music."""
    info = get_install_info()

    console.print("[bold yellow]=== yks-music Uninstall ===[/bold yellow]\n")

    console.print("[bold]Serao removidos:[/bold]")
    console.print(f"  - Comando: {info['command_path']}")
    console.print(f"  - Cache:   {info['cache_dir']}")
    console.print(f"  - Config:  {info['config_dir']}")
    console.print(f"  - Musicas: {info['music_dir']}")
    console.print("  - Pacote Python (via pip)")

    console.print("\n[bold red]AVISO:[/bold red] Esta acao nao pode ser desfeita.")

    try:
        confirmed = Confirm.ask("\nDeseja continuar? [y/N]")
    except (EOFError, KeyboardInterrupt):
        console.print("[cyan]Desinstalacao cancelada (sem input).[/cyan]")
        return False

    if not confirmed:
        console.print("[cyan]Desinstalacao cancelada.[/cyan]")
        return False

    success = True

    # 1. Remover o comando ~/.local/bin/yks-music
    command_path = info["command_path"]
    if command_path.exists():
        try:
            command_path.unlink()
            console.print(f"[green]  [OK] Comando removido: {command_path}[/green]")
        except PermissionError:
            console.print(f"[red]  [ERRO] Permissao negada: {command_path}[/red]")
            console.print("[dim]    Tente: rm ~/.local/bin/yks-music[/dim]")
            success = False
        except Exception as e:
            console.print(f"[red]  [ERRO] Falha ao remover comando: {e}[/red]")
            success = False
    else:
        console.print(f"[dim]  [IGNORADO] Comando nao encontrado: {command_path}[/dim]")

    # 2. Remover cache
    cache_dir = info["cache_dir"]
    if cache_dir.exists():
        try:
            shutil.rmtree(cache_dir)
            console.print(f"[green]  [OK] Cache removido: {cache_dir}[/green]")
        except Exception as e:
            console.print(f"[red]  [ERRO] Falha ao remover cache: {e}[/red]")
            success = False
    else:
        console.print(f"[dim]  [IGNORADO] Cache nao encontrado: {cache_dir}[/dim]")

    # 3. Remover configuracoes
    config_dir = info["config_dir"]
    if config_dir.exists():
        try:
            shutil.rmtree(config_dir)
            console.print(f"[green]  [OK] Configuracao removida: {config_dir}[/green]")
        except Exception as e:
            console.print(f"[red]  [ERRO] Falha ao remover configuracao: {e}[/red]")
            success = False
    else:
        console.print(f"[dim]  [IGNORADO] Configuracao nao encontrada: {config_dir}[/dim]")

    # 4. Perguntar sobre remover musicas
    music_dir = info["music_dir"]
    if music_dir.exists():
        songs_count = sum(1 for f in music_dir.rglob('*') if f.is_file())
        console.print(f"\n[yellow]A pasta de musicas contem seus downloads:[/yellow]")
        console.print(f"  {music_dir}")
        console.print(f"  Arquivos: {songs_count}")

        try:
            remove_music = Confirm.ask("[red]Deseja remover todas as musicas baixadas?[/red]")
        except (EOFError, KeyboardInterrupt):
            remove_music = False

        if remove_music:
            try:
                shutil.rmtree(music_dir)
                console.print(f"[green]  [OK] Musicas removidas: {music_dir}[/green]")
            except Exception as e:
                console.print(f"[red]  [ERRO] Falha ao remover musicas: {e}[/red]")
                success = False
        else:
            console.print("[dim]  [MANTIDO] Pasta de musicas preservada.[/dim]")

    # 5. Desinstalar pacote Python
    try:
        import subprocess
        extra_args = []
        if sys.platform != "darwin":
            test_result = subprocess.run(
                [sys.executable, "-m", "pip", "uninstall", "yks-music", "-y"],
                check=False,
                capture_output=True,
                text=True
            )
            if test_result.returncode != 0 and "externally-managed-environment" in (test_result.stderr + test_result.stdout):
                extra_args = ["--break-system-packages"]

            result = subprocess.run(
                [sys.executable, "-m", "pip", "uninstall", "yks-music", "-y"] + extra_args,
                check=False,
                capture_output=True,
                text=True
            )

        if result.returncode == 0:
            console.print("[green]  [OK] Pacote Python desinstalado (yks-music)[/green]")
        elif "WARNING: Skipping yks-music" in result.stdout:
            console.print("[dim]  [IGNORADO] Pacote nao encontrado (yks-music)[/dim]")
        else:
            console.print(f"[red]  [ERRO] Falha ao desinstalar pacote:[/red]")
            console.print(f"[dim]    {result.stderr.strip()}[/dim]")
            success = False
    except Exception as e:
        console.print(f"[red]  [ERRO] Falha ao executar pip uninstall: {e}[/red]")
        console.print("[dim]    Tente manualmente: pip uninstall yks-music -y[/dim]")
        success = False

    # Resultado final
    console.print("\n" + "=" * 50)
    if success:
        console.print("[bold green]>>> Desinstalacao concluida com sucesso! <<<[/bold green]")
    else:
        console.print("[bold yellow]>>> Desinstalacao concluida com alguns erros. <<<[/bold yellow]")
        console.print("[dim]Verifique as mensagens acima e remova manualmente se necessario.[/dim]")

    return True
