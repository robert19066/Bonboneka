#!/usr/bin/env bash
# ─────────────────────────────────────────────
#  Bonboneka Installer  (Linux / macOS)
# ─────────────────────────────────────────────
set -euo pipefail

# ── Colours ───────────────────────────────────
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[0;33m'
CYAN='\033[0;36m'; BOLD='\033[1m'; DIM='\033[2m'; RESET='\033[0m'

print_header() {
    echo
    echo -e "${BOLD}${CYAN}┌──────────────────────────────────────┐${RESET}"
    echo -e "${BOLD}${CYAN}│        Bonboneka  Installer          │${RESET}"
    echo -e "${BOLD}${CYAN}│  Ver 2.0 \"Choco-Milk-Sugar Goodness\" │${RESET}"
    echo -e "${BOLD}${CYAN}└──────────────────────────────────────┘${RESET}"
    echo
}

ok()   { echo -e "${GREEN}  ✔  ${RESET}$*"; }
info() { echo -e "${CYAN}  •  ${RESET}$*"; }
warn() { echo -e "${YELLOW}  !  ${RESET}$*"; }
die()  { echo -e "${RED}  ✘  ${RESET}$*" >&2; exit 1; }
step() { echo; echo -e "${BOLD}  $*${RESET}"; }

# ── Preflight checks ──────────────────────────
check_python() {
    if command -v python3 &>/dev/null; then
        PYTHON=python3
    elif command -v python &>/dev/null; then
        PYTHON=python
    else
        die "Python not found. Install Python 3.8+ and try again."
    fi
    PY_VER=$($PYTHON -c 'import sys; print("%d.%d" % sys.version_info[:2])')
    ok "Python $PY_VER  ($PYTHON)"
}

check_pip() {
    if ! $PYTHON -m pip --version &>/dev/null; then
        die "pip not found. Run:  $PYTHON -m ensurepip --upgrade"
    fi
    ok "pip found"
}

check_node() {
    if ! command -v node &>/dev/null; then
        warn "Node.js not found — PWA support (--pwa) will not be available."
        warn "Install Node.js 14+ from https://nodejs.org/ to enable it."
        HAS_NODE=0
    else
        NODE_VER=$(node --version)
        ok "Node.js $NODE_VER"
        HAS_NODE=1
    fi
}

check_npm() {
    if [ "$HAS_NODE" -eq 1 ] && ! command -v npm &>/dev/null; then
        warn "npm not found — bubblewrap will not be installed."
        HAS_NODE=0
    fi
}

install_via_setup() {
    step "Installing Bonboneka via setup.py (editable)…"
    if [ ! -f setup.py ] && [ ! -f pyproject.toml ]; then
        die "setup.py / pyproject.toml not found. Run this installer from the project root."
    fi
    $PYTHON -m pip install -e . --quiet
    ok "Bonboneka installed (editable)"
}

install_via_pip() {
    step "Installing Bonboneka via pip…"
    $PYTHON -m pip install bonboneka --quiet
    ok "Bonboneka installed"
}

# ── Menu ──────────────────────────────────────
print_menu() {
    echo -e "  ${BOLD}How would you like to install Bonboneka?${RESET}"
    echo
    echo -e "  ${CYAN}1${RESET}  setup.py  ${DIM}(editable install — for contributors / local dev)${RESET}"
    echo -e "  ${CYAN}2${RESET}  pip       ${DIM}(standard install from PyPI)${RESET}"
    echo -e "  ${CYAN}q${RESET}  Quit"
    echo
}

# ── Main ──────────────────────────────────────
main() {
    print_header

    step "Checking prerequisites…"
    check_python
    check_pip
    check_node
    check_npm

    echo
    print_menu

    while true; do
        read -rp "  Enter choice [1/2/q]: " choice
        case "$choice" in
            1)
                
                install_via_setup
                break
                ;;
            2)
                
                install_via_pip
                break
                ;;
            q|Q)
                echo; info "Cancelled."; exit 0
                ;;
            *)
                warn "Invalid choice — enter 1, 2, or q."
                ;;
        esac
    done

    echo
    echo -e "${BOLD}${GREEN}  ┌─────────────────────────────────────┐${RESET}"
    echo -e "${BOLD}${GREEN}  │   Installation complete!  🎉        │${RESET}"
    echo -e "${BOLD}${GREEN}  └─────────────────────────────────────┘${RESET}"
    echo
    info "Run ${BOLD}bomk --help${RESET} to get started."
    echo
}

main