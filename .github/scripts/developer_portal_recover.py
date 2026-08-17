from pathlib import Path
import re

source = Path('.github/workflows/developer-portal-build-once.yml').read_text(encoding='utf-8')
match = re.search(r"          python - <<'PY'\n(.*?)\n          PY", source, flags=re.S)
if not match:
    raise SystemExit('bounded Developer Portal Python block not found')
lines = []
for line in match.group(1).splitlines():
    lines.append(line[10:] if line.startswith('          ') else line)
code = '\n'.join(lines) + '\n'
exec(compile(code, '<developer-portal-build>', 'exec'), {})
