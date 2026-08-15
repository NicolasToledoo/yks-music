#!/usr/bin/env bash
#
# setup.sh — Cross-platform installer for yks-music
# Installs locally in .venv, creates global shortcut in ~/.local/bin/
# Supports: Ubuntu/Debian, Arch Linux, macOS, and other Linux distros
#
set -euo pipefail
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

# --- Trap de erro para limpeza ---
cleanup_on_error() {
    print_status ""
    print_status "[!] Ocorreu um erro durante a instalação."
    print_status "    Verifique o log: $SETUP_LOG"
    print_status "[!] O .venv pode estar em estado inconsistente."
    print_status "    Remova a pasta .venv e tente novamente."
}
trap cleanup_on_error ERR

# --- Executa comando redirecionando output para log ---
run_cmd() {
    local msg="$1"
    shift
    print_status "$msg"
    if ! "$@" >> "$SETUP_LOG" 2>&1; then
        print_status "[!] Falhou. Verifique o log: $SETUP_LOG"
        return 1
    fi
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

# --- Check Python ---
if ! command -v python3 &>/dev/null; then
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
        macos)
            if ! command -v brew &>/dev/null; then
                print_status "[*] Homebrew não encontrado. Instalando..."
                /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)" >> "$SETUP_LOG" 2>&1
            fi
            run_cmd "[*] Instalando Python 3..." brew install python
            ;;
        *)
            if command -v python3 &>/dev/null; then
                print_status "[*] Python 3 já instalado: $(command -v python3)"
            else
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
                if ! command -v python3 &>/dev/null; then
                    print_status "[!] Python 3 ainda não encontrado. Abortando."
                    exit 1
                fi
            fi
            ;;
    esac
fi

PYTHON="${PYTHON:-python3}"
PYTHON_VERSION="$($PYTHON --version 2>&1)"
print_status "[*] Python encontrado: $PYTHON_VERSION"

# --- Check for previous installation ---
if [[ -e "$HOME/.local/bin/yks-music" ]]; then
    print_status "[*] yks-music já instalado globalmente "
    set +e
    read -rp "Deseja reinstalar? (s/N): " -n 1 REPLY
    set -e
    echo
    if [[ ! $REPLY =~ ^[Ss]$ ]]; then
        print_status "Instalação cancelada."
        exit 0
    fi
    rm -f "$HOME/.local/bin/yks-music"
fi

# --- Install ffmpeg only if missing ---
if ! command -v ffmpeg &>/dev/null; then
    install_ffmpeg
else
    print_status "[*] ffmpeg já instalado: $(command -v ffmpeg)"
fi

# --- Create virtual environment ---
VENV_DIR="$SCRIPT_DIR/.venv"
if [[ ! -d "$VENV_DIR" ]]; then
    run_cmd "[*] Criando virtual environment..." "$PYTHON" -m venv "$VENV_DIR"
fi

# --- Activate venv and install Python deps ---
source "$VENV_DIR/bin/activate"
run_cmd "[*] Atualizando pip..." pip install --upgrade pip
run_cmd "[*] Instalando yks-music..." pip install -e "$SCRIPT_DIR"
install_yt_dlp

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
    python3 -c "
import sys
sys.path.insert(0, '$SCRIPT_DIR')
from yks_music.detector_cookie import detect_browser_path
import json
result = detect_browser_path('$browser')
print(json.dumps(result) if result else 'null')
" 2>/dev/null
}

detect_any_browser_path() {
    python3 -c "
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

# --- Create global shortcut ---
print_status "[*] Atualizando atalho global..."
VENV_PATH="$SCRIPT_DIR/.venv"
if [ -d "$VENV_PATH" ]; then
    cat > "$HOME/.local/bin/yks-music" << EOF
#!/usr/bin/env bash
exec "$VENV_PATH/bin/yks-music" "\$@"
EOF
    chmod +x "$HOME/.local/bin/yks-music"
    print_status "[✓] Atalho atualizado: ~/.local/bin/yks-music"
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

# Configure PATH for each installed shell
configure_shell_path "bash" "$HOME/.bashrc" 'export PATH="$HOME/.local/bin:$PATH"'
configure_shell_path "zsh" "$HOME/.zshrc" 'export PATH="$HOME/.local/bin:$PATH"'
configure_shell_path "fish" "$HOME/.config/fish/config.fish" 'fish_add_path ~/.local/bin'

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
print_status "[✓] Comando disponível: ~/.local/bin/yks-music"

# Verificar atalho funcional
if [ -x "$HOME/.local/bin/yks-music" ]; then
    print_status "[✓] Verificação: OK"
else
    print_status "[!] ~/.local/bin/yks-music não está funcional"
    print_status "    Execute: export PATH=\"\$HOME/.local/bin:\$PATH\""
fi

# Launch yks-music
print_status ""
print_status "Iniciando yks-music..."
"$HOME/.local/bin/yks-music"