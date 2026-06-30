#!/usr/bin/env bash
set -euo pipefail

# PythonAnywhere defaults. Adjust these if your project/virtualenv names differ.
PROJECT_DIR="${PROJECT_DIR:-/home/myapp01/mysite}"
VENV_DIR="${VENV_DIR:-/home/myapp01/.virtualenvs/myvirtualenv}"
PYTHON_BIN="${PYTHON_BIN:-$VENV_DIR/bin/python}"
PIP_BIN="${PIP_BIN:-$VENV_DIR/bin/pip}"
WSGI_FILE="${WSGI_FILE:-/var/www/myapp01_pythonanywhere_com_wsgi.py}"
BRANCH="${BRANCH:-main}"

cd "$PROJECT_DIR"

echo "==> Project: $PROJECT_DIR"
echo "==> Branch: $BRANCH"

if [ -d "$VENV_DIR" ]; then
  # shellcheck disable=SC1091
  source "$VENV_DIR/bin/activate"
else
  echo "Virtualenv not found: $VENV_DIR" >&2
  exit 1
fi

echo "==> Pulling latest code"
git fetch origin "$BRANCH"
git checkout "$BRANCH"
git pull --ff-only origin "$BRANCH"

echo "==> Installing requirements"
"$PIP_BIN" install -r requirements.txt

echo "==> Running Django checks"
"$PYTHON_BIN" manage.py check

echo "==> Applying migrations"
"$PYTHON_BIN" manage.py migrate --noinput

echo "==> Collecting static files"
"$PYTHON_BIN" manage.py collectstatic --noinput

if [ -f "$WSGI_FILE" ]; then
  echo "==> Reloading PythonAnywhere web app"
  touch "$WSGI_FILE"
else
  echo "==> WSGI file not found, skip reload: $WSGI_FILE"
  echo "    Reload manually from PythonAnywhere Web tab."
fi

echo "==> Deploy complete"
