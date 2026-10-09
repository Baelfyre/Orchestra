#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from orchestra_runtime.protocol.certification import (
    CertificationError,
    certify_adapter,
    certify_all_adapters,
)


def _print_human(evidence: dict[str, object]) -> None:
    print(f"Adapter: {evidence['requested_adapter_id']}")
    print(f"PRAP: {evidence['protocol_version']} ({evidence['certification_status']})")
    print(f"Compatibility: {evidence['compatibility_status']}")
    print(f"Host maturity: {evidence['observed_host_maturity']}")
    print('Certification promotes host maturity: false')
    print('Runtime authority granted: false')
    print('Runtime capabilities granted: false')
    print('Mutation performed: false')
    print('Installed integration refresh performed: false')


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog='orchestra-certify-adapter',
        description='Produce deterministic read-only PRAP v1 compatibility certification evidence.',
    )
    selection = parser.add_mutually_exclusive_group(required=True)
    selection.add_argument('--adapter', help='Canonical adapter id to certify')
    selection.add_argument('--all', action='store_true', help='Certify all contract-declared adapter targets')
    parser.add_argument('--json', action='store_true', help='Emit machine-readable certification evidence')
    args = parser.parse_args(argv)

    try:
        if args.all:
            records = [item.to_dict() for item in certify_all_adapters(root=ROOT)]
            if args.json:
                print(json.dumps(records, indent=2, sort_keys=True))
            else:
                for index, record in enumerate(records):
                    if index:
                        print()
                    _print_human(record)
        else:
            record = certify_adapter(args.adapter, root=ROOT).to_dict()
            if args.json:
                print(json.dumps(record, indent=2, sort_keys=True))
            else:
                _print_human(record)
    except CertificationError as exc:
        print(f'ORCHESTRA_PRAP_CERTIFICATION=FAIL:{exc}', file=sys.stderr)
        return 2

    print('ORCHESTRA_PRAP_CERTIFICATION=READ_ONLY_PASS', file=sys.stderr)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
