#!/bin/bash
# IICE-CRM Superuser Creation Runner Script
# This script activates the virtual environment (if available) and runs the superuser creation script

set -euo pipefail

echo "🚀 IICE-CRM Superuser Creation Runner"
echo "======================================"

# Set the correct paths
CRM_DIR="/home/iqraacad/domains/iqraacademy.com.pk/public_html/crm"
VENV_PATH="/home/iqraacad/virtualenv/domains/iqraacademy.com.pk/public_html/crm/3.11"

echo "📁 Changing to CRM directory: $CRM_DIR"
cd "$CRM_DIR" || {
    echo "❌ Failed to change to CRM directory"
    exit 1
}

# Export environment variables from .env if present
if [ -f .env ]; then
  echo "⚙️  Loading environment from .env"
  # shellcheck disable=SC2046
  export $(grep -v '^#' .env | grep '=' | xargs -0 -d '\n' -I{} echo {}) || true
elif [ -f .env.production ]; then
  echo "⚙️  Loading environment from .env.production"
  export $(grep -v '^#' .env.production | grep '=' | xargs -0 -d '\n' -I{} echo {}) || true
else
  echo "ℹ️ No .env or .env.production found; relying on system environment variables"
fi

# Try to activate virtual environment (optional)
if [ -d "$VENV_PATH" ]; then
  echo "🔄 Attempting to activate virtual environment..."
  if [ -f "$VENV_PATH/bin/activate" ]; then
    # shellcheck disable=SC1090
    source "$VENV_PATH/bin/activate" || echo "⚠️ Could not activate venv; will try direct python execution"
  elif [ -f "$VENV_PATH/bin/activate.sh" ]; then
    # shellcheck disable=SC1090
    source "$VENV_PATH/bin/activate.sh" || echo "⚠️ Could not activate venv via activate.sh; will try direct python execution"
  else
    echo "ℹ️ Venv activation script not found; continuing"
  fi
else
  echo "ℹ️ Virtual environment directory not found: $VENV_PATH"
fi

# Normalize CRLF line endings in the Python script (if any)
sed -i 's/\r$//' create_superuser.py || true

# Function to test a Python executable
try_python() {
  local py=$1
  if [ -x "$py" ] || command -v "$py" >/dev/null 2>&1; then
    echo "🔎 Testing Python: $py"
    if "$py" -c 'import sys; print("OK", sys.version)' >/dev/null 2>&1; then
      echo "✅ Using Python: $py"
      "$py" create_superuser.py
      return $?
    else
      echo "⚠️ Python executable exists but failed to run: $py"
    fi
  else
    echo "ℹ️ Python not found: $py"
  fi
  return 1
}

# Candidate Python interpreters (ordered)
candidates=(
  "$VENV_PATH/bin/python"
  "$VENV_PATH/bin/python3"
  python3
  python
  /usr/local/bin/python3
  /usr/bin/python3
)

# Show current python info if available
echo "🐍 System Python versions (if any):"
(command -v python3 >/dev/null 2>&1 && python3 --version) || echo "- python3 not in PATH"
(command -v python >/dev/null 2>&1 && python --version) || echo "- python not in PATH"

# Try candidates
SUCCESS=0
for py in "${candidates[@]}"; do
  if try_python "$py"; then
    SUCCESS=1
    break
  fi
done

if [ "$SUCCESS" -eq 1 ]; then
  echo "✅ Script execution completed"
  exit 0
fi

# Final fallback: try running via env python from venv path if present
if [ -f "$VENV_PATH/pyvenv.cfg" ]; then
  echo "🔄 Final fallback: attempting env python from venv"
  if [ -x "$VENV_PATH/bin/python" ]; then
    "$VENV_PATH/bin/python" create_superuser.py || true
  fi
fi

echo "❌ All Python execution attempts failed"
echo "📋 Troubleshooting:"
echo "  1) Verify the correct virtualenv path in this script"
echo "  2) Confirm a working Python interpreter exists (python3 or python)"
echo "  3) Ensure .env contains correct DB_USER and DB_PASSWORD"
echo "  4) Consider running manually:"
echo "     cd $CRM_DIR && $VENV_PATH/bin/python create_superuser.py"
exit 1