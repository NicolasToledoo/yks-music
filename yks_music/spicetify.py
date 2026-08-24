"""
Instalação e desinstalação do Spotify + Spicetify em Python puro.

Port fiel dos scripts referencias/instalar_spicetify.sh e
referencias/desinstalar_spotify_spicetify.sh, integrado ao CLI do yks-music.
Suporta: Ubuntu/Debian, Fedora, Arch Linux e macOS.
"""

import os
import shutil
import subprocess
from datetime import datetime
from pathlib import Path

from rich.console import Console
from rich.prompt import Confirm, Prompt

console = Console()

HOME = Path.home()

# Locais de alvos do Spicetify (usados na desinstalação)
SPICETIFY_TARGETS = [
    HOME / ".spicetify",
    HOME / ".config" / "spicetify",
    HOME / ".cache" / "spicetify",
    HOME / ".local" / "share" / "spicetify",
    HOME / ".local" / "bin" / "spicetify",
    Path("/usr/local/bin/spicetify"),
    Path("/opt/homebrew/bin/spicetify"),
    HOME / "go" / "bin" / "spicetify",
]

SPOTIFY_PREFS_LOCATIONS = [
    HOME / ".config" / "spotify" / "prefs",
    HOME / ".var" / "app" / "com.spotify.Client" / "config" / "spotify" / "prefs",
    HOME / "snap" / "spotify" / "common" / ".config" / "spotify" / "prefs",
    HOME / "Library" / "Application Support" / "Spotify" / "prefs",
]


# ---------------------------------------------------------------------------
# Helpers de output (cores espelhando os .sh)
# ---------------------------------------------------------------------------

def print_header(title):
    console.print(f"[bold blue]══════════════════════════════════════════════════════════╗[/bold blue]")
    console.print(f"[bold blue]║[/bold blue]  [bold]{title}[/bold]")
    console.print(f"[bold blue]══════════════════════════════════════════════════════════╝[/bold blue]")
    console.print()


def print_success(msg):
    console.print(f"  [green]✔[/green] {msg}")


def print_info(msg):
    console.print(f"  [cyan]→[/cyan] {msg}")


def print_warn(msg):
    console.print(f"  [yellow]![yellow] {msg}")


def print_error(msg):
    console.print(f"  [red]✗[/red] {msg}")


def print_phase(msg):
    console.print(f"\n[bold blue]━━━ {msg} ━━━[/bold blue]\n")


def print_divider():
    console.print("[dim]────────────────────────────────────────────────────────────────[/dim]")


def run_cmd(cmd, check=False, capture=False, shell=False):
    """Executa um comando, retornando CompletedProcess."""
    try:
        return subprocess.run(cmd, check=check, capture_output=capture, text=True, shell=shell)
    except subprocess.CalledProcessError as e:
        if check:
            raise
        return e


def detect_os():
    """Detecta o sistema operacional (macos/debian/fedora/arch/unknown)."""
    if os.uname().sysname == "Darwin":
        os_name = "macos"
    elif Path("/etc/debian_version").exists():
        os_name = "debian"
    elif Path("/etc/fedora-release").exists():
        os_name = "fedora"
    elif Path("/etc/arch-release").exists():
        os_name = "arch"
    else:
        os_name = "unknown"

    console.print(f"[green][✔][/green] Sistema detectado: [yellow]{os_name}[/yellow]")
    return os_name


def _writable(path):
    """Retorna True se o caminho (ou seu pai) for gravável pelo usuário."""
    if path.exists():
        return os.access(path, os.W_OK)
    parent = path.parent
    return os.access(parent, os.W_OK)


def _remove_path(target):
    """Remove arquivo ou diretório, usando sudo quando necessário."""
    if not target.exists():
        return
    if _writable(target):
        shutil.rmtree(target, ignore_errors=True)
        print_success(f"Removido: {target}")
    else:
        run_cmd(["sudo", "rm", "-rf", str(target)])
        print_success(f"Removido (sudo): {target}")


# ---------------------------------------------------------------------------
# INSTALAÇÃO
# ---------------------------------------------------------------------------

def _install_spotify_macos():
    if not shutil.which("brew"):
        print_warn("Homebrew não encontrado. Instalando...")
        run_cmd(["/bin/bash", "-c",
                 "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"])
        if os.uname().machine == "arm64":
            os.system("eval \"$(/opt/homebrew/bin/brew shellenv)\"")
        else:
            os.system("eval \"$(/usr/local/bin/brew shellenv)\"")
    run_cmd(["brew", "install", "--cask", "spotify"])


def _install_spotify_debian():
    run_cmd(["sudo", "bash", "-c",
             "curl -sS https://download.spotify.com/debian/pubkey_5384CE82BA52C83A.asc | "
             "sudo gpg --dearmor --yes -o /etc/apt/trusted.gpg.d/spotify.gpg"])
    run_cmd(["sudo", "bash", "-c",
             "echo 'deb https://repository.spotify.com stable non-free' | "
             "sudo tee /etc/apt/sources.list.d/spotify.list > /dev/null"])
    run_cmd(["sudo", "apt-get", "update"])
    run_cmd(["sudo", "apt-get", "install", "-y", "spotify-client"])


def _install_spotify_fedora():
    if subprocess.run(["rpm", "-q", "rpmfusion-free-release"], capture_output=True).returncode != 0:
        print_warn("Instalando RPM Fusion...")
        run_cmd(["sudo", "dnf", "install", "-y",
                 "https://download1.rpmfusion.org/free/fedora/"
                 "rpmfusion-free-release-$(rpm -E %fedora).noarch.rpm"])
    run_cmd(["sudo", "dnf", "install", "-y", "spotify"])


def _install_spotify_arch():
    if shutil.which("yay"):
        run_cmd(["yay", "-S", "--noconfirm", "spotify"])
    elif shutil.which("paru"):
        run_cmd(["paru", "-S", "--noconfirm", "spotify"])
    elif shutil.which("snap"):
        run_cmd(["sudo", "snap", "install", "spotify"])
    else:
        print_error("Nenhum AUR helper encontrado. Instale 'yay', 'paru' ou 'snap' primeiro.")
        raise SystemExit(1)


def install_spotify(os_name):
    console.print("\n[blue]Instalando Spotify...[/blue]")

    if os_name == "macos":
        _install_spotify_macos()
    elif os_name == "debian":
        _install_spotify_debian()
    elif os_name == "fedora":
        _install_spotify_fedora()
    elif os_name == "arch":
        _install_spotify_arch()
    else:
        print_error("Sistema não suportado para instalação automática do Spotify")
        print_info("https://www.spotify.com/download")
        raise SystemExit(1)

    # Conceder permissões de escrita para o Spicetify
    console.print("\n[blue]Configurando permissões para Spicetify...[/blue]")
    if os_name == "arch" and (HOME / ".." / "opt" / "spotify").exists() or Path("/opt/spotify").exists():
        if Path("/opt/spotify").exists():
            run_cmd(["sudo", "chmod", "a+wr", "/opt/spotify"], check=False)
            run_cmd(["sudo", "chmod", "a+wr", "/opt/spotify/Apps", "-R"], check=False)
            print_success("Permissões concedidas em /opt/spotify")
    elif os_name == "debian" and Path("/usr/share/spotify").exists():
        run_cmd(["sudo", "chmod", "a+wr", "/usr/share/spotify"], check=False)
        run_cmd(["sudo", "chmod", "a+wr", "/usr/share/spotify/Apps", "-R"], check=False)
        print_success("Permissões concedidas em /usr/share/spotify")
    elif os_name == "fedora":
        if Path("/usr/lib64/spotify").exists():
            run_cmd(["sudo", "chmod", "a+wr", "/usr/lib64/spotify"], check=False)
            run_cmd(["sudo", "chmod", "a+wr", "/usr/lib64/spotify/Apps", "-R"], check=False)
        elif Path("/usr/share/spotify").exists():
            run_cmd(["sudo", "chmod", "a+wr", "/usr/share/spotify"], check=False)
            run_cmd(["sudo", "chmod", "a+wr", "/usr/share/spotify/Apps", "-R"], check=False)
        print_success("Permissões concedidas no diretório do Spotify")

    print_success("Spotify instalado com sucesso!")


def generate_spotify_prefs():
    console.print("\n[blue]Gerando arquivo de configuração do Spotify...[/blue]")

    for prefs_file in SPOTIFY_PREFS_LOCATIONS:
        if prefs_file.exists():
            print_success(f"Arquivo prefs encontrado em: {prefs_file}")
            return

    print_info("Abrindo Spotify brevemente para gerar arquivo de configuração...")
    if shutil.which("spotify"):
        proc = subprocess.Popen(
            ["spotify", "--no-zygote", "--uri=spotify://stop"],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.terminate()
        import time
        time.sleep(2)

    for prefs_file in SPOTIFY_PREFS_LOCATIONS:
        if prefs_file.exists():
            print_success(f"Arquivo prefs gerado em: {prefs_file}")
            return

    print_warn("Arquivo prefs não foi criado automaticamente. Criando manualmente...")
    prefs_dir = HOME / ".config" / "spotify"
    prefs_dir.mkdir(parents=True, exist_ok=True)
    (prefs_dir / "prefs").write_text("[Device]\ndevice_id=\n\n[Registry]\n")
    print_success(f"Arquivo prefs criado manualmente em: {prefs_dir / 'prefs'}")


def install_spicetify():
    console.print("\n[blue]Instalando Spicetify CLI...[/blue]")

    install = subprocess.Popen(
        ["curl", "-fsSL", "https://raw.githubusercontent.com/spicetify/cli/main/install.sh"],
        stdout=subprocess.PIPE,
    )
    subprocess.run(["sh"], stdin=install.stdout, check=False)
    install.stdout.close()

    os.environ["PATH"] = os.environ["PATH"] + f":{HOME}/.spicetify:{HOME}/.local/bin"

    if not shutil.which("spicetify"):
        print_error("Falha ao instalar spicetify. Verifique a conexão.")
        raise SystemExit(1)

    print_success("Spicetify CLI instalado com sucesso!")


def setup_spicetify():
    console.print("\n[blue]Configurando Spicetify...[/blue]")

    if shutil.which("spotify"):
        run_cmd(["pkill", "-x", "spotify"], check=False)
        run_cmd(["pkill", "-x", "Spotify"], check=False)
        import time
        time.sleep(2)

    console.print("\n[blue]Verificando backup dos arquivos originais...[/blue]")
    if subprocess.run(["spicetify", "backup"], capture_output=True).returncode != 0:
        print_warn("Backup já existe ou foi criado pelo instalador. Continuando...")
    else:
        print_success("Backup criado")

    console.print("\n[blue]Aplicando customizações finais...[/blue]")
    if subprocess.run(["spicetify", "apply"], capture_output=True).returncode != 0:
        print_warn("Apply encontrou avisos, mas deve estar funcionando.")
    else:
        print_success("Customizações aplicadas!")


def install_spotify_spicetify():
    """Fluxo completo de instalação do Spotify + Spicetify."""
    print_header("Spotify + Spicetify Auto Installer")
    os_name = detect_os()
    install_spotify(os_name)
    generate_spotify_prefs()
    install_spicetify()
    setup_spicetify()

    console.print()
    console.print("[green]══════════════════════════════════════════════════════════╗[/green]")
    console.print("[green]║[/green]  [bold green]🎉 INSTALAÇÃO CONCLUÍDA![/bold green]")
    console.print("[green]══════════════════════════════════════════════════════════╝[/green]")
    console.print()
    console.print("[yellow]Próximos passos:[/yellow]")
    console.print("  [bold]1.[/bold] Abra um NOVO terminal (para carregar o PATH configurado)")
    console.print("  [bold]2.[/bold] Abra o Spotify personalizado!")
    console.print()
    console.print("[blue]Comandos úteis do Spicetify:[/blue]")
    console.print("  • spicetify config current_theme <nome>   - Mudar tema")
    console.print("  • spicetify config color_scheme <cor>      - Mudar cor")
    console.print("  • spicetify marketplace                    - Loja de temas/apps")
    console.print("  • spicetify apply                          - Aplicar mudanças")
    console.print("  • spicetify restore                        - Restaurar original")
    console.print()


# ---------------------------------------------------------------------------
# DESINSTALAÇÃO
# ---------------------------------------------------------------------------

def _backup_login():
    spotify_users = HOME / ".config" / "spotify" / "Users"
    spotify_prefs = HOME / ".config" / "spotify" / "prefs"
    backup_dir = HOME / f".config/spotify_backup_{datetime.now():%Y%m%d_%H%M%S}"

    login_preserved = False
    if spotify_users.is_dir() and any(spotify_users.iterdir()):
        (backup_dir / "Users").mkdir(parents=True, exist_ok=True)
        for item in spotify_users.iterdir():
            if item.is_dir():
                shutil.copytree(item, backup_dir / "Users" / item.name)
            else:
                shutil.copy2(item, backup_dir / "Users" / item.name)
        print_success("Credenciais de usuário copiadas")
        login_preserved = True

    if spotify_prefs.exists():
        backup_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(spotify_prefs, backup_dir / "prefs")
        print_success("Arquivo prefs copiado")
        login_preserved = True

    if login_preserved:
        console.print()
        print_info(f"Backup salvo em: [bold]{backup_dir}[/bold]")
        print_warn("Seu login será restaurado automaticamente após reinstalar o Spotify")
    else:
        print_warn("Nenhuma credencial de login encontrada")

    return login_preserved, backup_dir


def _diagnose_spicetify():
    console.print("[bold]Procurando vestígios do Spicetify...[/bold]\n")

    spicetify_bin = shutil.which("spicetify")
    if spicetify_bin:
        print_warn(f"Binário ativo: [bold]{spicetify_bin}[/bold]")
    else:
        print_success("Comando 'spicetify' não está no PATH atual")

    found = 0
    for target in SPICETIFY_TARGETS:
        if target.exists():
            print_warn(f"Encontrado: {target}")
            found += 1

    fish_vars = HOME / ".config" / "fish" / "fish_variables"
    fish_config = HOME / ".config" / "fish" / "config.fish"
    shell_files = [HOME / f for f in (".bashrc", ".zshrc", ".profile", ".bash_profile")]

    if fish_vars.exists() and "spicetify" in fish_vars.read_text(errors="ignore"):
        print_warn(f"PATH no Fish: {fish_vars}")
        found += 1
    if fish_config.exists() and "spicetify" in fish_config.read_text(errors="ignore"):
        print_warn(f"Config Fish: {fish_config}")
        found += 1
    for shell_file in shell_files:
        if shell_file.exists() and "spicetify" in shell_file.read_text(errors="ignore"):
            print_warn(f"Shell config: {shell_file}")
            found += 1

    return found


def _clean_shell_configs():
    fish_vars = HOME / ".config" / "fish" / "fish_variables"
    fish_config = HOME / ".config" / "fish" / "config.fish"
    shell_files = [HOME / f for f in (".bashrc", ".zshrc", ".profile", ".bash_profile")]

    for cfg in [fish_vars, fish_config, *shell_files]:
        if cfg.exists() and "spicetify" in cfg.read_text(errors="ignore"):
            backup = cfg.with_suffix(cfg.suffix + f".bak.{int(datetime.now().timestamp())}")
            shutil.copy2(cfg, backup)
            lines = [ln for ln in cfg.read_text(errors="ignore").splitlines() if "spicetify" not in ln]
            cfg.write_text("\n".join(lines))
            print_success(f"Limpo {cfg.name} (backup criado)")


def _remove_spotify(os_name):
    console.print("\n[blue]Removendo aplicativo Spotify...[/blue]")
    if os_name == "macos":
        if shutil.which("brew"):
            run_cmd(["brew", "uninstall", "--cask", "spotify"], check=False)
        _remove_path(Path("/Applications/Spotify.app"))
        print_success("Spotify removido (macOS)")
    elif os_name == "debian":
        run_cmd(["sudo", "apt-get", "purge", "-y", "spotify-client"], check=False)
        run_cmd(["sudo", "apt-get", "autoremove", "-y"], check=False)
        _remove_path(Path("/etc/apt/sources.list.d/spotify.list"))
        _remove_path(Path("/etc/apt/trusted.gpg.d/spotify.gpg"))
        print_success("Spotify removido (Debian/Ubuntu)")
    elif os_name == "fedora":
        run_cmd(["sudo", "dnf", "remove", "-y", "spotify"], check=False)
        run_cmd(["sudo", "dnf", "autoremove", "-y"], check=False)
        print_success("Spotify removido (Fedora)")
    elif os_name == "arch":
        if shutil.which("yay"):
            run_cmd(["yay", "-Rns", "--noconfirm", "spotify"], check=False)
        elif shutil.which("paru"):
            run_cmd(["paru", "-Rns", "--noconfirm", "spotify"], check=False)
        elif shutil.which("pacman"):
            run_cmd(["sudo", "pacman", "-Rns", "--noconfirm", "spotify"], check=False)
        _remove_path(Path("/opt/spotify"))
        print_success("Spotify removido (Arch)")
    else:
        print_warn("Sistema não reconhecido, pulei a remoção do Spotify")


def _restore_login(login_preserved, backup_dir):
    console.print("[bold]Restaurando credenciais...[/bold]\n")

    spotify_config = HOME / ".config" / "spotify"
    spotify_users = spotify_config / "Users"
    spotify_prefs = spotify_config / "prefs"

    spotify_config.mkdir(parents=True, exist_ok=True)

    if (backup_dir / "Users").is_dir():
        spotify_users.mkdir(parents=True, exist_ok=True)
        for item in (backup_dir / "Users").iterdir():
            if item.is_dir():
                shutil.copytree(item, spotify_users / item.name, dirs_exist_ok=True)
            else:
                shutil.copy2(item, spotify_users / item.name)
        print_success("Credenciais de usuário restauradas")

    if (backup_dir / "prefs").exists():
        shutil.copy2(backup_dir / "prefs", spotify_prefs)
        print_success("Arquivo prefs restaurado")

    print_info("Login preservado com sucesso!")
    print_warn("Ao reinstalar o Spotify, você estará logado automaticamente")


def uninstall_spotify_spicetify():
    """Fluxo completo de desinstalação (preservando login do Spotify)."""
    print_header("LIMPEZA PROFUNDA: Spicetify + Spotify")

    print_phase("FASE 0: PRESERVANDO LOGIN DO SPOTIFY")
    console.print("[bold]Salvando credenciais de login...[/bold]\n")
    login_preserved, backup_dir = _backup_login()

    print_phase("FASE 1: DIAGNÓSTICO")
    found = _diagnose_spicetify()

    os_name = detect_os()

    if found == 0:
        console.print()
        print_success("Nenhum arquivo do Spicetify encontrado no sistema")
        console.print()
        print_warn("Se o comando ainda funciona, feche este terminal e abra um novo")
        print_info("O PATH pode estar em cache na sessão atual")
        console.print()
        return

    console.print()
    print_divider()
    console.print("[yellow][bold]ATENÇÃO:[/bold][/yellow] Os itens acima serão [red][bold]permanentemente removidos[/bold][/red]")
    console.print("[green][bold]✔[/bold][/green] [green]Seu login do Spotify será preservado[/green]")
    print_divider()
    console.print()

    confirm = Prompt.ask("[bold]Continuar com a remoção?[/bold] [dim](s/N)[/dim]", default="n")
    if confirm.lower() not in ("s", "sim", "y", "yes"):
        console.print()
        print_warn("Operação cancelada pelo usuário")
        console.print()
        return

    print_phase("FASE 2: REMOÇÃO")

    spicetify_bin = shutil.which("spicetify")
    if spicetify_bin:
        _remove_path(Path(spicetify_bin))

    for target in SPICETIFY_TARGETS:
        _remove_path(target)

    _clean_shell_configs()

    remove_spotify = Prompt.ask(
        "[bold]Deseja remover o aplicativo Spotify também?[/bold] [dim](s/N)[/dim]", default="n")
    if remove_spotify.lower() in ("s", "sim", "y", "yes"):
        _remove_spotify(os_name)

    if login_preserved:
        print_phase("FASE 3: RESTAURANDO LOGIN DO SPOTIFY")
        _restore_login(login_preserved, backup_dir)

    print_phase("FASE 4: VERIFICAÇÃO")
    still_found = 0
    for target in SPICETIFY_TARGETS:
        if target.exists():
            print_warn(f"Ainda existe: {target}")
            still_found += 1
    if still_found == 0:
        print_success("Todos os arquivos foram removidos com sucesso")

    console.print()
    console.print("[green]══════════════════════════════════════════════════════════════╗[/green]")
    console.print("[green]║[/green]  [bold green]🎉 LIMPEZA CONCLUÍDA![/bold green]")
    console.print("[green]══════════════════════════════════════════════════════════════╝[/green]")
    console.print()
    console.print("[yellow][bold]PRÓXIMOS PASSOS:[/bold][/yellow]")
    console.print()
    console.print("  [bold]1.[/bold] [bold]Feche este terminal completamente[/bold]")
    console.print("  [bold]2.[/bold] [bold]Abra um novo terminal[/bold]")
    console.print("  [bold]3.[/bold] Verifique se sumiu rodando:")
    console.print()
    console.print("     [cyan]$[/cyan] [green]command -v spicetify[/green]")
    console.print()
    console.print("     [dim](não deve retornar absolutamente nada)[/dim]")
    console.print()

    if login_preserved:
        console.print("[green][bold]✔ LOGIN PRESERVADO[/bold][/green]")
        console.print()
        console.print(f"  [dim]Quando você reinstalar o Spotify, estará logado automaticamente[/dim]")
        console.print(f"  [dim]Backup salvo em: [bold]{backup_dir}[/bold][/dim]")
        console.print()

    print_divider()
    console.print("[dim]Se ainda aparecer algo, execute o diagnóstico novamente[/dim]")
    console.print()


if __name__ == "__main__":
    install_spotify_spicetify()
