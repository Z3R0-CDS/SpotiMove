#!/usr/bin/env bash

# ==============================
# Beginner-friendly setup script
# Works on macOS & Linux
# ==============================

set -e

# ---------- Colors ----------
GREEN="\033[0;32m"
YELLOW="\033[1;33m"
RED="\033[0;31m"
BLUE="\033[0;34m"
NC="\033[0m" # No Color

# ---------- Helpers ----------
info()    { echo -e "${BLUE}ℹ️  $1${NC}"; }
success() { echo -e "${GREEN}✅ $1${NC}"; }
warn()    { echo -e "${YELLOW}⚠️  $1${NC}"; }
error()   { echo -e "${RED}❌ $1${NC}"; exit 1; }

command_exists() {
  command -v "$1" >/dev/null 2>&1
}

# ---------- OS Detection ----------
OS="$(uname)"
info "Detected OS: $OS"

# ---------- Checks ----------
info "Checking required tools..."

command_exists python || error "Python is not installed. Please install Python 3 first."
command_exists pip || error "pip is not installed. Please install pip first."
command_exists mkcert || warn "mkcert is not installed. SSL cert generation will fail."

success "Basic tools check complete"

# ---------- Virtual Environment ----------
if [ ! -d ".venv" ]; then
  info "Creating virtual environment..."
  python -m venv .venv
  success "Virtual environment created"
else
  success "Virtual environment already exists"
fi

# ---------- Activate Venv ----------
info "Activating virtual environment..."
# shellcheck disable=SC1091
source .venv/bin/activate
success "Virtual environment activated"

# ---------- Python Dependencies ----------
if [ -f "requirements.txt" ]; then
  info "Installing Python dependencies..."
  pip install --upgrade pip
  pip install -r requirements.txt
  success "Dependencies installed"
else
  warn "requirements.txt not found, skipping dependency installation"
fi

# ---------- SSL Certificates ----------
if command_exists mkcert; then
  mkdir -p certs
  info "Generating local SSL certificates..."
  mkcert localhost \
    -cert-file ./certs/localhost.pem \
    -key-file ./certs/localhost-key.pem
  success "SSL certificates created"
else
  warn "mkcert not available. Skipping certificate generation."
  warn "Install mkcert to enable HTTPS locally."
fi

# ---------- Run Application ----------
info "Starting application..."
python app.py

