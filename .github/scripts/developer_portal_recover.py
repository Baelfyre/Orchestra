from pathlib import Path
import re
import textwrap

source = Path('.github/workflows/developer-portal-build-once.yml').read_text(encoding='utf-8')
match = re.search(r"          python - <<'PY'\n(.*?)\n          PY", source, flags=re.S)
if not match:
    raise SystemExit('bounded Developer Portal Python block not found')
code = textwrap.dedent(match.group(1))
exec(compile(code, '<developer-portal-build>', 'exec'), {})
