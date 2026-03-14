#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
mkdir -p "$ROOT/data/sample-docs"
cat > "$ROOT/data/sample-docs/sample_alarm_guide.txt" <<'TXT'
Alarm guide
- verify safety interlocks
- clear overload relay
- reset faults before restart
TXT
cat > "$ROOT/data/sample-docs/sample_sop.txt" <<'TXT'
SOP
- verify permissives
- confirm sensor feedback
- review device state in PLC
TXT
printf 'Sample docs refreshed in %s\n' "$ROOT/data/sample-docs"
