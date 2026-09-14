#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
python3 -m py_compile web/server.py
python3 - <<'PY'
import yaml
for f in ('docker-compose.yml','umbrel-app.yml'):
    with open(f,'r',encoding='utf-8') as h: yaml.safe_load(h)
print('YAML: OK')
PY
if command -v node >/dev/null 2>&1; then
  python3 - <<'PY' > /tmp/mergeforge-inline.js
from pathlib import Path
s=Path('web/index.html').read_text()
print(s.split('<script>',1)[1].split('</script>',1)[0])
PY
  node --check /tmp/mergeforge-inline.js
  rm -f /tmp/mergeforge-inline.js
fi
find . -maxdepth 3 -type f -perm /111 -print
printf 'Validation complete.\n'
