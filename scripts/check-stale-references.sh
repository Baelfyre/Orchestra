#!/usr/bin/env sh
set -eu

ROOT=${1:-"$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"}
SELF=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)/$(basename -- "$0")
stale_pattern='ux-diagram-''architect|meister-''virtuoso|Meister ''Virtuoso|AO''OP|Motor''PH|Hive''Mind|Art ''Appreciation|C:[\\/]+Users[\\/]|/ho''me/'
sensitive_pattern='production[[:space:]]+sec''rets?|api[_ -]?ke''ys?[[:space:]]*[:=][[:space:]]*[^[:space:]]+'
findings=''

scan() {
  pattern=$1
  flags=$2
  find "$ROOT" -type f ! -path "$ROOT/.git/*" ! -path "$SELF" -exec grep "$flags" "$pattern" {} +
}

findings=$(scan "$stale_pattern" -InE || true; scan "$sensitive_pattern" -IinE || true)
if [ -n "$findings" ]; then
  printf '%s\n' "$findings"
  exit 1
fi

echo 'No stale or disallowed references found.'
