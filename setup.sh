#!/usr/bin/env bash
#
# setup.sh — Cross-platform installer for yks-music
# Installs locally in .venv, creates global shortcut in ~/.local/bin/
# Supports: Ubuntu/Debian, Arch Linux, macOS, and other Linux distros
#
# Não usamos 'set -e' para não abortar o script em falhas não-críticas
# (ex.: pip/venv/yt-dlp). Falhas são registradas em $SETUP_LOG.
set -o pipefail
umask 022

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# --- Log file ---
SETUP_LOG="/tmp/yks-setup.log"
: > "$SETUP_LOG"

# --- Parse arguments ---
FORCE_REINSTALL=0
for arg in "$@"; do
    case "$arg" in
        --force) FORCE_REINSTALL=1 ;;
    esac
done

# --- Color helpers ---
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
CYAN='\033[0;36m'
NC='\033[0m'

msg_info()    { printf "${CYAN}[INFO]${NC} %s\n" "$1"; }
msg_success() { printf "${GREEN}[SUCCESS]${NC} %s\n" "$1"; }
msg_warn()    { printf "${YELLOW}[WARN]${NC} %s\n" "$1"; }
msg_error()   { printf "${RED}[ERROR]${NC} %s\n" "$1"; }

# --- Banner fixo no topo (9 linhas) ---
BANNER_LINES=9
print_banner() {
    printf "\033[1;36m"
    echo " __  __     __  __     ______     __    __     __  __     ______     __     ______    "
    echo "/\ \_\ \   /\ \/ /    /\  ___\   /\ \"-./  \   /\ \/\ \   /\  ___\   /\ \   /\  ___\   "
    echo "\ \____ \  \ \  _\"-.  \ \___  \  \ \ \-./\ \  \ \ \_\ \  \ \___  \  \ \ \  \ \ \____  "
    echo " \/\_____\  \ \_\ \_\  \/\_____\  \ \_\ \ \_\  \ \_____\  \/\_____\  \ \_\  \ \_____\ "
    echo "  \/_____/   \/_/\/_/   \/_____/   \/_/  \/_/   \/_____/   \/_____/   \/_/   \/_____/ "
    echo "======================================================================"
    printf "\033[0m"
}

# --- Função para imprimir abaixo do banner ---
OUTPUT_LINE=0

print_status() {
    local msg="$1"
    local term_lines
    term_lines=$(tput lines 2>/dev/null || echo 24)
    local available=$((term_lines - BANNER_LINES - 1))

    if [[ $OUTPUT_LINE -ge $available ]]; then
        clear_output
        OUTPUT_LINE=0
    fi

    printf "\033[%d;1H\033[2K%s" "$((BANNER_LINES + 1 + OUTPUT_LINE))" "$msg"
    OUTPUT_LINE=$((OUTPUT_LINE + 1))
}

clear_output() {
    local term_lines
    term_lines=$(tput lines 2>/dev/null || echo 24)
    for ((i = BANNER_LINES + 1; i <= term_lines; i++)); do
        printf "\033[%d;1H\033[2K" "$i"
    done
    printf "\033[%d;1H" "$((BANNER_LINES + 1))"
}

# --- Executa comando redirecionando output para log (nunca aborta) ---
run_cmd() {
    local msg="$1"
    shift
    print_status "$msg"
    if ! "$@" >> "$SETUP_LOG" 2>&1; then
        print_status "[!] Falhou (não fatal). Verifique: $SETUP_LOG"
    fi
    return 0
}

# --- Detect OS ---
detect_os() {
    if [[ "$(uname)" == "Darwin" ]]; then
        echo "macos"
    elif command -v pacman &>/dev/null; then
        echo "arch"
    elif command -v apt-get &>/dev/null; then
        echo "debian"
    elif command -v dnf &>/dev/null; then
        echo "fedora"
    elif command -v yum &>/dev/null; then
        echo "rhel"
    elif command -v zypper &>/dev/null; then
        echo "opensuse"
    elif command -v apk &>/dev/null; then
        echo "alpine"
    elif command -v xbps-install &>/dev/null; then
        echo "void"
    elif command -v eopkg &>/dev/null; then
        echo "solus"
    else
        echo "unknown"
    fi
}

# --- Select option with arrow keys ---
SELECTED_OPTION=0
select_option() {
    local options=("$@")
    local selected=0
    local last=$((${#options[@]} - 1))

    printf "\033[?25l"

    while true; do
        for i in "${!options[@]}"; do
            if [[ $i -eq $selected ]]; then
                printf "\033[%d;1H\033[2K\033[1;32m ► %s\033[0m" "$((BANNER_LINES + 1 + OUTPUT_LINE + i))" "${options[$i]}"
            else
                printf "\033[%d;1H\033[2K   %s" "$((BANNER_LINES + 1 + OUTPUT_LINE + i))" "${options[$i]}"
            fi
        done

        read -rsn1 -t 60 key 2>/dev/null || true
        if [[ $key == "" ]]; then
            break
        elif [[ $key == $'\x1b' ]]; then
            read -rsn2 -t 10 key 2>/dev/null || true
            if [[ $key == "[A" ]]; then
                selected=$((selected - 1))
                [[ $selected -lt 0 ]] && selected=$last
            elif [[ $key == "[B" ]]; then
                selected=$((selected + 1))
                [[ $selected -gt $last ]] && selected=0
            fi
        fi
    done

    printf "\033[?25h"

    for i in "${!options[@]}"; do
        printf "\033[%d;1H\033[2K" "$((BANNER_LINES + 1 + OUTPUT_LINE + i))"
    done

    OUTPUT_LINE=$((OUTPUT_LINE + ${#options[@]}))
    SELECTED_OPTION=$selected
}

# --- Select option with arrow keys (2 columns) ---
select_option_2col() {
    local options=("$@")
    local total=${#options[@]}
    local cols=2
    local rows=$(( (total + cols - 1) / cols ))
    local selected=0
    local col row idx xoff

    printf "\033[?25l"

    while true; do
        for ((r = 0; r < rows; r++)); do
            printf "\033[%d;1H\033[2K" "$((BANNER_LINES + 1 + OUTPUT_LINE + r))"

            col=0
            idx=$((col * rows + r))
            xoff=1
            if [[ $idx -lt $total ]]; then
                if [[ $idx -eq $selected ]]; then
                    printf "\033[%d;%dH\033[1;32m► %-17s\033[0m" \
                        "$((BANNER_LINES + 1 + OUTPUT_LINE + r))" "$xoff" "${options[$idx]}"
                else
                    printf "\033[%d;%dH %-18s" \
                        "$((BANNER_LINES + 1 + OUTPUT_LINE + r))" "$xoff" "${options[$idx]}"
                fi
            fi

            col=1
            idx=$((col * rows + r))
            xoff=21
            if [[ $idx -lt $total ]]; then
                if [[ $idx -eq $selected ]]; then
                    printf "\033[%d;%dH\033[1;32m► %-17s\033[0m" \
                        "$((BANNER_LINES + 1 + OUTPUT_LINE + r))" "$xoff" "${options[$idx]}"
                else
                    printf "\033[%d;%dH %-18s" \
                        "$((BANNER_LINES + 1 + OUTPUT_LINE + r))" "$xoff" "${options[$idx]}"
                fi
            fi
        done

        read -rsn1 -t 60 key 2>/dev/null || true
        if [[ $key == "" ]]; then
            break
        elif [[ $key == $'\x1b' ]]; then
            read -rsn2 -t 10 key 2>/dev/null || true
            col=$((selected / rows))
            row=$((selected % rows))

            case "$key" in
                "[A") row=$((row - 1)); [[ $row -lt 0 ]] && row=$((rows - 1)) ;;
                "[B") row=$((row + 1)); [[ $row -ge $rows ]] && row=0 ;;
                "[D") col=$((col - 1)); [[ $col -lt 0 ]] && col=$((cols - 1)) ;;
                "[C") col=$((col + 1)); [[ $col -ge $cols ]] && col=0 ;;
            esac

            selected=$((col * rows + row))
            [[ $selected -ge $total ]] && selected=$((total - 1))
        fi
    done

    printf "\033[?25h"

    for ((r = 0; r < rows; r++)); do
        printf "\033[%d;1H\033[2K" "$((BANNER_LINES + 1 + OUTPUT_LINE + r))"
    done

    OUTPUT_LINE=$((OUTPUT_LINE + rows))
    SELECTED_OPTION=$selected
}

# --- Install ffmpeg if missing ---
install_ffmpeg() {
    case "$OS" in
        debian)
            run_cmd "[*] Atualizando pacotes..." sudo apt update
            run_cmd "[*] Instalando ffmpeg..." sudo apt install -y ffmpeg
            ;;
        arch)
            run_cmd "[*] Instalando ffmpeg..." sudo pacman -Sy --noconfirm ffmpeg
            ;;
        fedora)
            run_cmd "[*] Instalando ffmpeg..." sudo dnf install -y ffmpeg
            ;;
        rhel)
            run_cmd "[*] Instalando ffmpeg..." sudo yum install -y ffmpeg
            ;;
        opensuse)
            run_cmd "[*] Instalando ffmpeg..." sudo zypper install -y ffmpeg
            ;;
        alpine)
            run_cmd "[*] Instalando ffmpeg..." apk add --no-cache ffmpeg
            ;;
        void)
            run_cmd "[*] Instalando ffmpeg..." sudo xbps-install -S -y ffmpeg
            ;;
        solus)
            run_cmd "[*] Instalando ffmpeg..." sudo eopkg install -y ffmpeg
            ;;
        macos)
            if command -v brew &>/dev/null; then
                run_cmd "[*] Instalando ffmpeg..." brew install ffmpeg
            else
                print_status "[!] Homebrew não encontrado. Instale ffmpeg manualmente:"
                print_status "    https://ffmpeg.org/download.html"
                exit 1
            fi
            ;;
        *)
            if command -v ffmpeg &>/dev/null; then
                print_status "[*] ffmpeg já instalado: $(command -v ffmpeg)"
            else
                print_status "[!] Gerenciador de pacotes não detectado."
                print_status "    Instale ffmpeg manualmente: https://ffmpeg.org/download.html"
                print_status "    Exemplos para distros não listadas:"
                print_status "      Void Linux:    sudo xbps-install -S ffmpeg"
                print_status "      NixOS:         nix-env -iA nixpkgs.ffmpeg"
                print_status "      Gentoo:        sudo emerge media-video/ffmpeg"
                print_status "      Solus:         sudo eopkg install ffmpeg"
                print_status "      Amazon Linux:  sudo yum install ffmpeg"
                print_status ""
                read -rp "    Pressione ENTER após instalar ffmpeg, ou Ctrl+C para abortar: " -n 1 REPLY_MANUAL
                echo
                if ! command -v ffmpeg &>/dev/null; then
                    print_status "[!] ffmpeg ainda não encontrado. Abortando."
                    exit 1
                fi
            fi
            ;;
    esac
}

# --- Install yt-dlp with native + pip fallback ---
install_yt_dlp() {
    local venv_ytdlp="$VENV_DIR/bin/yt-dlp"

    # 1. Check if already installed (unless --force)
    if [ "$FORCE_REINSTALL" -eq 0 ]; then
        local existing_ytdlp
        existing_ytdlp=$(command -v yt-dlp 2>/dev/null)
        if [ -n "$existing_ytdlp" ]; then
            local ytdlp_version
            ytdlp_version=$("$existing_ytdlp" --version 2>/dev/null | head -1)
            msg_success "yt-dlp já instalado: $existing_ytdlp ($ytdlp_version)"
            return 0
        fi
        if [ -x "$venv_ytdlp" ]; then
            ytdlp_version=$("$venv_ytdlp" --version 2>/dev/null | head -1)
            msg_success "yt-dlp já instalado no .venv: $ytdlp_version"
            return 0
        fi
    fi

    msg_info "Instalando yt-dlp..."
    local install_ok=0

    # 2. Try native package manager
    case "$OS" in
        debian)
            if sudo apt update >> "$SETUP_LOG" 2>&1 && \
               sudo apt install -y yt-dlp >> "$SETUP_LOG" 2>&1; then
                install_ok=1
            fi
            ;;
        arch)
            if sudo pacman -Sy --noconfirm yt-dlp >> "$SETUP_LOG" 2>&1; then
                install_ok=1
            fi
            ;;
        fedora)
            if sudo dnf install -y yt-dlp >> "$SETUP_LOG" 2>&1; then
                install_ok=1
            fi
            ;;
        rhel)
            if sudo yum install -y yt-dlp >> "$SETUP_LOG" 2>&1; then
                install_ok=1
            fi
            ;;
        opensuse)
            if sudo zypper install -y yt-dlp >> "$SETUP_LOG" 2>&1; then
                install_ok=1
            fi
            ;;
        alpine)
            if apk add yt-dlp >> "$SETUP_LOG" 2>&1; then
                install_ok=1
            fi
            ;;
        void)
            if sudo xbps-install -S -y yt-dlp >> "$SETUP_LOG" 2>&1; then
                install_ok=1
            fi
            ;;
        solus)
            if sudo eopkg install -y yt-dlp >> "$SETUP_LOG" 2>&1; then
                install_ok=1
            fi
            ;;
        macos)
            if command -v brew &>/dev/null; then
                if brew install yt-dlp >> "$SETUP_LOG" 2>&1; then
                    install_ok=1
                fi
            else
                msg_warn "Homebrew não encontrado, tentando pip..."
            fi
            ;;
    esac

    # 3. Verify native binary works
    if [ "$install_ok" -eq 1 ]; then
        local nativo
        nativo=$(command -v yt-dlp 2>/dev/null)
        if [ -n "$nativo" ] && "$nativo" --version &>/dev/null; then
            local nativo_version
            nativo_version=$("$nativo" --version 2>/dev/null | head -1)
            msg_success "yt-dlp instalado via gerenciador de pacotes: $nativo ($nativo_version)"
            return 0
        fi
        msg_warn "Instalação nativa falhou, tentando fallback pip..."
    fi

    # 4. Fallback: pip in .venv
    msg_info "Tentando instalação via pip no .venv..."
    local pip_args="yt-dlp"
    if [ "$FORCE_REINSTALL" -eq 1 ]; then
        pip_args="--force-reinstall yt-dlp"
    fi

    # Try without --break-system-packages
    if pip install $pip_args >> "$SETUP_LOG" 2>&1; then
        if [ -x "$venv_ytdlp" ]; then
            local pip_version
            pip_version=$("$venv_ytdlp" --version 2>/dev/null | head -1)
            msg_success "yt-dlp instalado via pip no .venv ($pip_version)"
            return 0
        fi
    fi

    # Try with --break-system-packages
    if pip install --break-system-packages $pip_args >> "$SETUP_LOG" 2>&1; then
        if [ -x "$venv_ytdlp" ]; then
            pip_version=$("$venv_ytdlp" --version 2>/dev/null | head -1)
            msg_success "yt-dlp instalado via pip --break-system-packages ($pip_version)"
            return 0
        fi
    fi

    # Try --user as last resort
    if pip install --user $pip_args >> "$SETUP_LOG" 2>&1; then
        msg_success "yt-dlp instalado via pip --user"
        return 0
    fi

    # 5. Everything failed
    msg_error "Falha ao instalar yt-dlp."
    msg_error "Verifique o log: $SETUP_LOG"
    msg_error "Tente instalar manualmente:"
    msg_error "  Debian/Ubuntu: sudo apt install yt-dlp"
    msg_error "  Arch:          sudo pacman -S yt-dlp"
    msg_error "  Fedora:        sudo dnf install yt-dlp"
    msg_error "  macOS:         brew install yt-dlp"
    msg_error "  pip:           pip install yt-dlp"
    return 1
}

# ============================================
# Início
# ============================================
clear
print_banner
clear_output

OS="$(detect_os)"
print_status "[*] Sistema detectado: $OS"

# --- Check Python (prefer python3, fallback python) ---
if command -v python3 &>/dev/null; then
    PYTHON=python3
elif command -v python &>/dev/null; then
    PYTHON=python
else
    print_status "[!] Python 3 não encontrado. Instalando..."
    case "$OS" in
        debian)
            run_cmd "[*] Atualizando pacotes..." sudo apt update
            run_cmd "[*] Instalando Python 3..." sudo apt install -y python3 python3-pip python3-venv
            ;;
        arch)
            run_cmd "[*] Instalando Python 3..." sudo pacman -Sy --noconfirm python python-pip
            ;;
        fedora)
            run_cmd "[*] Instalando Python 3..." sudo dnf install -y python3 python3-pip
            ;;
        rhel)
            run_cmd "[*] Instalando Python 3..." sudo yum install -y python3 python3-pip
            ;;
        opensuse)
            run_cmd "[*] Instalando Python 3..." sudo zypper install -y python3 python3-pip
            ;;
        alpine)
            run_cmd "[*] Instalando Python 3..." apk add --no-cache python3 py3-pip
            ;;
        void)
            run_cmd "[*] Instalando Python 3..." sudo xbps-install -S -y python3 python3-pip
            ;;
        solus)
            run_cmd "[*] Instalando Python 3..." sudo eopkg install -y python3
            ;;
        macos)
            if ! command -v brew &>/dev/null; then
                print_status "[*] Homebrew não encontrado. Instalando..."
                /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)" >> "$SETUP_LOG" 2>&1
            fi
            run_cmd "[*] Instalando Python 3..." brew install python
            ;;
        *)
            print_status "[!] Gerenciador de pacotes não detectado."
            print_status "    Instale Python 3 manualmente: https://www.python.org/downloads/"
            print_status "    Exemplos para distros não listadas:"
            print_status "      Void Linux:    sudo xbps-install -S python3 python3-pip"
            print_status "      NixOS:         nix-env -iA nixpkgs.python3"
            print_status "      Gentoo:        sudo emerge dev-lang/python"
            print_status "      Solus:         sudo eopkg install python3"
            print_status ""
            read -rp "    Pressione ENTER após instalar Python 3, ou Ctrl+C para abortar: " -n 1 REPLY_MANUAL
            echo
            if ! command -v python3 &>/dev/null && ! command -v python &>/dev/null; then
                print_status "[!] Python 3 ainda não encontrado. Abortando."
                exit 1
            fi
            ;;
    esac
    if command -v python3 &>/dev/null; then
        PYTHON=python3
    else
        PYTHON=python
    fi
fi

PYTHON_VERSION="$($PYTHON --version 2>&1)"
print_status "[*] Python encontrado: $PYTHON ($PYTHON_VERSION)"

# --- Check for previous installation ---
if [[ -e "$HOME/.local/bin/yks-music" ]] || [[ -e "/usr/local/bin/yks-music" ]]; then
    print_status "[*] yks-music já instalado globalmente"
    read -rp "Deseja reinstalar? (s/N): " -n 1 REPLY
    echo
    if [[ ! $REPLY =~ ^[Ss]$ ]]; then
        print_status "Instalação cancelada."
        exit 0
    fi
    rm -f "$HOME/.local/bin/yks-music" "/usr/local/bin/yks-music"
fi

# --- Install ffmpeg only if missing ---
if ! command -v ffmpeg &>/dev/null; then
    install_ffmpeg
else
    print_status "[*] ffmpeg já instalado: $(command -v ffmpeg)"
fi

# --- Create virtual environment (with retry + ensure venv tooling) ---
VENV_DIR="$SCRIPT_DIR/.venv"

ensure_venv() {
    if "$PYTHON" -m venv "$VENV_DIR" >> "$SETUP_LOG" 2>&1; then
        return 0
    fi
    print_status "[!] Falha ao criar venv; tentando instalar dependências de venv..."
    case "$OS" in
        debian|unknown)
            sudo apt-get update >> "$SETUP_LOG" 2>&1
            sudo apt-get install -y python3-venv python3-pip >> "$SETUP_LOG" 2>&1 || true
            ;;
        arch)    sudo pacman -Sy --noconfirm python-pip >> "$SETUP_LOG" 2>&1 || true ;;
        fedora|rhel) sudo dnf install -y python3-pip >> "$SETUP_LOG" 2>&1 || true ;;
        opensuse) sudo zypper install -y python3-pip >> "$SETUP_LOG" 2>&1 || true ;;
        alpine)  sudo apk add --no-cache py3-pip >> "$SETUP_LOG" 2>&1 || true ;;
        void)    sudo xbps-install -S -y python3-pip >> "$SETUP_LOG" 2>&1 || true ;;
        solus)   sudo eopkg install -y python3-pip >> "$SETUP_LOG" 2>&1 || true ;;
        macos)   brew install python >> "$SETUP_LOG" 2>&1 || true ;;
    esac
    if "$PYTHON" -m venv "$VENV_DIR" >> "$SETUP_LOG" 2>&1; then
        return 0
    fi
    print_status "[!] Não foi possível criar o virtual environment."
    print_status "    Verifique o log: $SETUP_LOG"
    exit 1
}

if [[ ! -d "$VENV_DIR" ]]; then
    print_status "[*] Criando virtual environment..."
    ensure_venv
fi

# --- Activate venv and install Python deps ---
source "$VENV_DIR/bin/activate"

print_status "[*] Atualizando pip..."
pip install --upgrade pip >> "$SETUP_LOG" 2>&1 || print_status "[!] Falha ao atualizar pip (continuando)."

print_status "[*] Instalando yks-music..."
if pip install -e "$SCRIPT_DIR" >> "$SETUP_LOG" 2>&1; then
    print_status "[✓] yks-music instalado (editable)."
elif pip install --no-build-isolation -e "$SCRIPT_DIR" >> "$SETUP_LOG" 2>&1; then
    print_status "[✓] yks-music instalado (sem build isolation)."
elif pip install "$SCRIPT_DIR" >> "$SETUP_LOG" 2>&1; then
    print_status "[✓] yks-music instalado."
else
    print_status "[!] Falha ao instalar yks-music. Verifique: $SETUP_LOG"
fi

print_status "[*] Instalando dependências de download (yt-dlp, mutagen, pillow)..."
if pip install yt-dlp mutagen pillow >> "$SETUP_LOG" 2>&1; then
    print_status "[✓] yt-dlp + mutagen + pillow instalados no .venv"
elif pip install --break-system-packages yt-dlp mutagen pillow >> "$SETUP_LOG" 2>&1; then
    print_status "[✓] yt-dlp + mutagen + pillow instalados no .venv (--break-system-packages)"
else
    print_status "[!] Falha ao instalar deps de download. Verifique: $SETUP_LOG"
fi

install_yt_dlp || print_status "[!] yt-dlp não instalado; o app tentará usar o do venv se disponível."

# --- Configurar Cookie do Navegador ---
print_status ""
print_status "========================================="
print_status "  Configuração de Cookies"
print_status "========================================="
print_status ""
print_status "O yks-music precisa de cookies do navegador para:"
print_status "  • Baixar músicas com restrição de idade"
print_status "  • Evitar erro 'Sign in to confirm you're not a bot'"
print_status "  • Garantir estabilidade nos downloads"
print_status ""

detect_cookie_path() {
    local browser="$1"
    "$PYTHON" -c "
import sys
sys.path.insert(0, '$SCRIPT_DIR')
from yks_music.detector_cookie import detect_browser_path
import json
result = detect_browser_path('$browser')
print(json.dumps(result) if result else 'null')
" 2>/dev/null
}

detect_any_browser_path() {
    "$PYTHON" -c "
import sys
sys.path.insert(0, '$SCRIPT_DIR')
from yks_music.detector_cookie import detect_any_browser
result = detect_any_browser()
if result:
    print(result[1])
else:
    print('null')
" 2>/dev/null
}

print_status "[*] Detectando navegador e caminho dos cookies..."

DETECTED_PATH=$(detect_any_browser_path)

if [ -n "$DETECTED_PATH" ] && [ "$DETECTED_PATH" != "null" ]; then
    BROWSER_PATH="$DETECTED_PATH"
    DETECTED_DIR="${DETECTED_PATH#*:}"
    BROWSER="${DETECTED_PATH%%:*}"
    print_status "[✓] Navegador detectado: $BROWSER"
    print_status "[✓] Caminho encontrado: $DETECTED_DIR"
else
    print_status "[!] Nenhum navegador com cookies encontrado automaticamente"
    print_status "    Buscando por nome selecionado..."
    
    browsers=("brave" "chrome" "chromium" "edge" "firefox" "opera" "safari" "vivaldi" "whale")
    select_option_2col "${browsers[@]}"
    BROWSER="${browsers[$SELECTED_OPTION]}"
    
    DETECTED_PATH=$(detect_cookie_path "$BROWSER")
    
    if [ -n "$DETECTED_PATH" ] && [ "$DETECTED_PATH" != "null" ]; then
        BROWSER_PATH="$DETECTED_PATH"
        DETECTED_DIR="${DETECTED_PATH#*:}"
        print_status "[✓] Caminho detectado: $DETECTED_DIR"
    else
        BROWSER_PATH="$BROWSER"
        print_status "[!] Caminho não detectado para $BROWSER"
        print_status "    O yks-music tentará localizar automaticamente"
    fi
fi

CONFIG_DIR="$HOME/.config/yks-music"
CONFIG_FILE="$CONFIG_DIR/config.json"
mkdir -p "$CONFIG_DIR"

# Determinar método de instalação detectado
get_install_method() {
    local path="$1"
    if [[ "$path" == *"snap"* ]]; then
        echo "snap"
    elif [[ "$path" == *".var/app"* ]]; then
        echo "flatpak"
    else
        echo "native"
    fi
}

INSTALL_METHOD=$(get_install_method "$DETECTED_DIR")

# Mapear navegador para caminhos de origem
case "$BROWSER" in
    brave)
        NATIVE_PATH="$HOME/.config/BraveSoftware/Brave-Browser"
        SNAP_PATH="$HOME/snap/brave/current/.config/BraveSoftware/Brave-Browser"
        FLATPAK_PATH="$HOME/.var/app/com.brave.Browser/config/BraveSoftware/Brave-Browser"
        ;;
    chrome)
        NATIVE_PATH="$HOME/.config/google-chrome"
        FLATPAK_PATH="$HOME/.var/app/com.google.Chrome/config/google-chrome"
        SNAP_PATH=""
        ;;
    chromium)
        NATIVE_PATH="$HOME/.config/chromium"
        SNAP_PATH="$HOME/snap/chromium/common/chromium"
        FLATPAK_PATH="$HOME/.var/app/org.chromium.Chromium/config/chromium"
        ;;
    edge)
        NATIVE_PATH="$HOME/.config/microsoft-edge"
        FLATPAK_PATH="$HOME/.var/app/com.microsoft.Edge/config/microsoft-edge"
        SNAP_PATH=""
        ;;
    opera)
        NATIVE_PATH="$HOME/.config/opera"
        FLATPAK_PATH="$HOME/.var/app/com.opera.Opera/config/opera"
        SNAP_PATH=""
        ;;
    vivaldi)
        NATIVE_PATH="$HOME/.config/vivaldi"
        FLATPAK_PATH="$HOME/.var/app/com.vivaldi.Vivaldi/config/vivaldi"
        SNAP_PATH=""
        ;;
    firefox)
        NATIVE_PATH="$HOME/.mozilla/firefox"
        FLATPAK_PATH="$HOME/.var/app/org.mozilla.firefox/.mozilla/firefox"
        SNAP_PATH="$HOME/snap/firefox/common/.mozilla/firefox"
        ;;
    *)
        NATIVE_PATH=""
        FLATPAK_PATH=""
        SNAP_PATH=""
        ;;
esac

# Criar config.json com informações detalhadas
if [ -n "$DETECTED_PATH" ] && [ "$DETECTED_PATH" != "null" ]; then
    cat > "$CONFIG_FILE" << EOF
{
  "cookie_browser": "$BROWSER_PATH",
  "browser": "$BROWSER",
  "profile_path": "$DETECTED_DIR",
  "install_method": "$INSTALL_METHOD",
  "sources": {
    "native": "$NATIVE_PATH",
    "snap": "$SNAP_PATH",
    "flatpak": "$FLATPAK_PATH"
  },
  "detected_at": "$(date -Iseconds 2>/dev/null || date +%Y-%m-%dT%H:%M:%S%z)"
}
EOF
    print_status "[✓] Config criado - método: $INSTALL_METHOD"
    print_status "[✓] URL: $BROWSER_PATH"
else
    printf '{"cookie_browser": "%s", "browser": "%s", "install_method": "none"}\n' "$BROWSER_PATH" "$BROWSER" > "$CONFIG_FILE"
fi

print_status "[✓] Navegador configurado: $BROWSER"

# --- Create global launchers (PATH-independent) ---
print_status "[*] Criando atalhos globais..."
VENV_PATH="$SCRIPT_DIR/.venv"
VENV_PY="$VENV_PATH/bin/python3"

create_launcher() {
    # $1 = destination path
    local dest="$1"
    mkdir -p "$(dirname "$dest")"
    cat > "$dest" << EOF
#!/usr/bin/env bash
export PATH="$VENV_PATH/bin:\$PATH"
exec "$VENV_PY" -m yks_music.cli "\$@"
EOF
    chmod +x "$dest"
}

# 1) ~/.local/bin (fallback, sempre gravável pelo usuário)
create_launcher "$HOME/.local/bin/yks-music"
print_status "[✓] Atalho criado: ~/.local/bin/yks-music"

# 2) /usr/local/bin (PRIMARY: está no PATH por padrão em todas as distros e macOS,
#    em shells interativos, de login e em launchers do Hyprland)
if [ -w /usr/local/bin ] || (mkdir -p /usr/local/bin 2>/dev/null && [ -w /usr/local/bin ]); then
    create_launcher "/usr/local/bin/yks-music"
    print_status "[✓] Atalho criado: /usr/local/bin/yks-music"
elif command -v sudo &>/dev/null; then
    sudo tee "/usr/local/bin/yks-music" >/dev/null << EOF
#!/usr/bin/env bash
export PATH="$VENV_PATH/bin:\$PATH"
exec "$VENV_PY" -m yks_music.cli "\$@"
EOF
    sudo chmod +x "/usr/local/bin/yks-music"
    print_status "[✓] Atalho criado: /usr/local/bin/yks-music (sudo)"
else
    print_status "[!] Sem escrita em /usr/local/bin; o comando ficará em ~/.local/bin"
fi

# --- Detect default shell ---
get_default_shell() {
    if [[ "$(uname)" == "Darwin" ]]; then
        if command -v dscl &>/dev/null; then
            dscl . -read ~ UserShell 2>/dev/null | awk '{print $2}'
        fi
    else
        if command -v getent &>/dev/null; then
            getent passwd "$USER" 2>/dev/null | cut -d: -f7
        fi
    fi
    echo "${SHELL:-/bin/sh}"
}

DEFAULT_SHELL="$(get_default_shell)"
print_status "[*] Shell padrão detectado: $DEFAULT_SHELL"

# --- Configure PATH for installed shells ---
configure_shell_path() {
    local shell_name="$1"
    local shell_rc="$2"
    local path_line="$3"

    # Check if shell is installed
    if ! command -v "$shell_name" &>/dev/null; then
        return
    fi

    # Check if this is the default shell
    local is_default="false"
    if [[ "$DEFAULT_SHELL" == *"$shell_name"* ]]; then
        is_default="true"
    fi

    # For fish: create config.fish if it doesn't exist
    if [[ "$shell_name" == "fish" ]] && [[ ! -f "$shell_rc" ]]; then
        mkdir -p "$(dirname "$shell_rc")"
        echo "$path_line" > "$shell_rc"
        print_status "[✓] $shell_rc criado com PATH (shell padrão: fish)"
        return
    fi

    # Check if already configured
    if [[ -f "$shell_rc" ]] && grep -q '\.local/bin' "$shell_rc" 2>/dev/null; then
        if [[ "$is_default" == "true" ]]; then
            print_status "[*] $shell_name: PATH já configurado (shell padrão)"
        else
            print_status "[*] $shell_name: PATH já configurado"
        fi
        return
    fi

    # Add PATH entry
    if [[ -f "$shell_rc" ]]; then
        echo "$path_line" >> "$shell_rc"
        if [[ "$is_default" == "true" ]]; then
            print_status "[✓] PATH adicionado em $shell_rc (shell padrão: $shell_name)"
        else
            print_status "[✓] PATH adicionado em $shell_rc ($shell_name)"
        fi
    fi
}

# Configure PATH for each installed shell (reforço; o principal é /usr/local/bin)
configure_shell_path "bash" "$HOME/.bashrc" 'export PATH="$HOME/.local/bin:$PATH"'
configure_shell_path "bash" "$HOME/.bash_profile" 'export PATH="$HOME/.local/bin:$PATH"'
configure_shell_path "bash" "$HOME/.profile" 'export PATH="$HOME/.local/bin:$PATH"'
configure_shell_path "zsh" "$HOME/.zshrc" 'export PATH="$HOME/.local/bin:$PATH"'
configure_shell_path "zsh" "$HOME/.zprofile" 'export PATH="$HOME/.local/bin:$PATH"'
configure_shell_path "fish" "$HOME/.config/fish/config.fish" 'fish_add_path ~/.local/bin'

# Aplica ~/.local/bin ao fish IMEDIATAMENTE (variável universal fish_user_paths) e
# de forma persistente, sem exigir reinício da sessão de fish.
if command -v fish &>/dev/null; then
    fish -c "fish_add_path $HOME/.local/bin" 2>/dev/null || \
    fish -c "set -Ua fish_user_paths $HOME/.local/bin" 2>/dev/null || true
fi

# Garante que esta própria sessão de bash também enxergue o binário.
export PATH="$HOME/.local/bin:$PATH"

# --- Verify installation ---
print_status ""
print_status "========================================="
print_status "  Verificando Instalação..."
print_status "========================================="
print_status ""

# Verificar yt-dlp: PATH do sistema primeiro, depois .venv
VENV_PATH="$SCRIPT_DIR/.venv"
ytdlp_found=0

# Checar no PATH do sistema
system_ytdlp=$(command -v yt-dlp 2>/dev/null)
if [ -n "$system_ytdlp" ]; then
    ytdlp_version=$("$system_ytdlp" --version 2>/dev/null | head -1)
    print_status "[✓] yt-dlp (sistema): $system_ytdlp ($ytdlp_version)"
    ytdlp_found=1
fi

# Checar no .venv
if [ -x "$VENV_PATH/bin/yt-dlp" ]; then
    ytdlp_version=$("$VENV_PATH/bin/yt-dlp" --version 2>/dev/null | head -1)
    print_status "[✓] yt-dlp (.venv): $ytdlp_version"
    ytdlp_found=1
fi

# Se não encontrou nenhum, reinstalar
if [ "$ytdlp_found" -eq 0 ]; then
    print_status "[!] yt-dlp não encontrado, reinstalando..."
    FORCE_REINSTALL=1
    install_yt_dlp
fi

# Verificar ffmpeg
if command -v ffmpeg &>/dev/null; then
    print_status "[✓] ffmpeg encontrado: $(command -v ffmpeg)"
else
    print_status "[!] ffmpeg não encontrado"
fi

print_status ""
print_status "========================================="
print_status "  Instalação Concluída!"
print_status "========================================="
print_status ""
print_status "[✓] yks-music instalado com sucesso!"
print_status "[✓] Comando disponível em: /usr/local/bin/yks-music e ~/.local/bin/yks-music"

# Verificar atalho funcional
if command -v yks-music >/dev/null 2>&1; then
    print_status "[✓] yks-music disponível no PATH atual: $(command -v yks-music)"
elif [ -x "/usr/local/bin/yks-music" ]; then
    print_status "[✓] Atalho criado em /usr/local/bin/yks-music."
    print_status "    Abra um NOVO terminal e digite: yks-music"
elif [ -x "$HOME/.local/bin/yks-music" ]; then
    print_status "[✓] Atalho criado em ~/.local/bin/yks-music."
    print_status "    Reinicie o terminal ou rode: export PATH=\"\$HOME/.local/bin:\$PATH\""
    print_status "    e digite: yks-music"
else
    print_status "[!] Atalho não está funcional. Verifique: $SETUP_LOG"
fi

if command -v fish &>/dev/null && fish -c 'command -v yks-music' >/dev/null 2>&1; then
    print_status "[✓] yks-music disponível no fish (nova sessão)."
fi

# Launch yks-music
print_status ""
print_status "Iniciando yks-music..."
if [ -x "$VENV_PATH/bin/python3" ]; then
    "$VENV_PATH/bin/python3" -m yks_music.cli
elif [ -x "$HOME/.local/bin/yks-music" ]; then
    "$HOME/.local/bin/yks-music"
elif [ -x "/usr/local/bin/yks-music" ]; then
    "/usr/local/bin/yks-music"
else
    print_status "[!] Não foi possível iniciar o yks-music automaticamente."
    print_status "    Reinicie o terminal e digite: yks-music"
fi