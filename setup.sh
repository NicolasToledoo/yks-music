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
            print_status "[!] Não foi possível detectar o gerenciador de pacotes."
            print_status "    Instale ffmpeg manualmente: https://ffmpeg.org/download.html"
            exit 1
            ;;
    esac
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
            print_status "    Instale Python 3 manualmente."
            exit 1
            ;;
    esac
fi

PYTHON="${PYTHON:-python3}"
PYTHON_VERSION="$($PYTHON --version 2>&1)"
print_status "[*] Python encontrado: $PYTHON_VERSION"

# --- Check for previous installation ---
if [[ -e "$HOME/.local/bin/yks-music" ]]; then
    print_status "[*] yks-music já instalado globalmente"
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
run_cmd "[*] Instalando dependências..." pip install yt-dlp

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

print_status "Escolha o navegador que você utiliza:"
print_status ""

browsers=("brave" "chrome" "chromium" "edge" "firefox" "opera" "safari" "vivaldi" "whale")
select_option_2col "${browsers[@]}"
BROWSER="${browsers[$SELECTED_OPTION]}"

print_status "[*] Detectando caminho dos cookies..."

DETECTED_PATH=$(detect_cookie_path "$BROWSER")

if [ -n "$DETECTED_PATH" ] && [ "$DETECTED_PATH" != "null" ]; then
    BROWSER_PATH="$DETECTED_PATH"
    DETECTED_DIR="${DETECTED_PATH#*:}"
    print_status "[✓] Caminho detectado automaticamente: $DETECTED_DIR"
else
    BROWSER_PATH="$BROWSER"
    print_status "[!] Caminho não detectado automaticamente"
    read -rp "Digite caminho manualmente (ou ENTER para usar nome apenas): " MANUAL_PATH
    if [ -n "$MANUAL_PATH" ]; then
        if [[ "$MANUAL_PATH" == *":"* ]]; then
            BROWSER_PATH="$MANUAL_PATH"
        else
            BROWSER_PATH="$BROWSER:$MANUAL_PATH"
        fi
    fi
fi

CONFIG_DIR="$HOME/.config/yks-music"
CONFIG_FILE="$CONFIG_DIR/config.json"
mkdir -p "$CONFIG_DIR"
printf '{"cookie_browser": "%s"}\n' "$BROWSER_PATH" > "$CONFIG_FILE"

print_status "[✓] Navegador configurado: $BROWSER"

# --- Create global shortcut ---
# Garante que ~/.local/bin está no PATH para detectar yks-music depois
export PATH="$HOME/.local/bin:$PATH"

run_cmd "[*] Criando atalho global..." bash -c "mkdir -p $HOME/.local/bin && cat > $HOME/.local/bin/yks-music << 'EOshortcut'
#!/usr/bin/env bash
exec \"$VENV_DIR/bin/yks-music\" \"\$@\"
EOshortcut
chmod +x $HOME/.local/bin/yks-music"

# --- Verify installation ---
print_status ""
print_status "========================================="
print_status "  Instalação Concluída!"
print_status "========================================="
print_status ""
print_status "[✓] yks-music instalado com sucesso!"
print_status "[✓] Comando disponível: ~/.local/bin/yks-music"

if command -v yks-music &>/dev/null; then
    print_status "[✓] Verificação: OK"
else
    print_status "[!] ~/.local/bin não está no PATH"
    print_status "    Adicione a seu ~/.bashrc ou ~/.zshrc:"
    print_status '    export PATH="$HOME/.local/bin:$PATH"'
    print_status "    Ou execute: yks-music via $HOME/.local/bin/yks-music"
fi

print_status ""
print_status "Requisitos (instalados automaticamente):"
print_status "  - yt-dlp: instalado no .venv"
print_status "  - ffmpeg: detectado/instalado acima"