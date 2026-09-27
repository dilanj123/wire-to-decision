#!/usr/bin/env bash
set -euo pipefail

# WIRE-004 TOOLCHAIN SETUP ONLY.
# No Homebrew or global EDA fallback is permitted by this script.
suite_root="${WIRE_OSS_CAD_SUITE_ROOT:-${WIRE_TO_DECISION_OSS_CAD_SUITE:-/Users/Dilan/eda/wire-to-decision/oss-cad-suite}}"
if [[ ! -f "$suite_root/environment" ]]; then
    echo "ERROR: OSS CAD Suite environment not found: $suite_root/environment" >&2
    echo "Set WIRE_TO_DECISION_OSS_CAD_SUITE to an exact installed suite path." >&2
    exit 1
fi

source "$suite_root/environment"
export WIRE_TO_DECISION_OSS_CAD_SUITE="$suite_root"
echo "WIRE_TO_DECISION_OSS_CAD_SUITE=$WIRE_TO_DECISION_OSS_CAD_SUITE"
echo "WIRE_OSS_CAD_SUITE_ROOT=$WIRE_TO_DECISION_OSS_CAD_SUITE"
echo "PATH=$PATH"
