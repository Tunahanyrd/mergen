#!/usr/bin/env bash
# Mergen Wrapper Script - Prevents Qt version conflicts
# Forces use of system Qt libraries instead of bundled ones

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Unset LD_LIBRARY_PATH to use system Qt
unset LD_LIBRARY_PATH

# Use system Qt plugins
export QT_PLUGIN_PATH=/usr/lib64/qt6/plugins:/usr/lib/qt6/plugins

# Execute the actual binary
exec "$SCRIPT_DIR/mergen.bin" "$@"
