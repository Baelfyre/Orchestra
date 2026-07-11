import os
import sys
import re

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import helpers

def main():
    root = helpers.get_project_root()

    patterns = [
        re.compile(r'ux-diagram-architect', re.IGNORECASE),
        re.compile(r'meister-virtuoso', re.IGNORECASE),
        re.compile(r'Meister Virtuoso', re.IGNORECASE),
        re.compile(r'AOOP', re.IGNORECASE),
        re.compile(r'MotorPH', re.IGNORECASE),
        re.compile(r'HiveMind', re.IGNORECASE),
        re.compile(r'Art Appreciation', re.IGNORECASE),
        re.compile(r'C:[\\/]Users[\\/]', re.IGNORECASE),
        re.compile(r'/home/', re.IGNORECASE),
        re.compile(r'production\s+secrets?', re.IGNORECASE),
        re.compile(r'api[_ -]?keys?\s*[:=]\s*\S+', re.IGNORECASE)
    ]

    findings = []

    for dirpath, dirnames, filenames in os.walk(root):
        # Exclude hidden directories and specific allowed docs
        dirnames[:] = [d for d in dirnames if d not in ['.git', 'brain', '.agents', 'adapters']]
        for filename in filenames:
            filepath = os.path.join(dirpath, filename)
            # Skip the current script
            if os.path.abspath(filepath) == os.path.abspath(__file__):
                continue

            # Skip powershell script since it contains the patterns and would trigger it
            if filename == "check-stale-references.ps1":
                continue

            # Skip known exceptions
            rel_path = os.path.relpath(filepath, root).replace('\\', '/')
            if rel_path.startswith('skills/clockwork/') or rel_path.startswith('docs/governance/postmortems/'):
                continue

            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    for line_number, line in enumerate(f, 1):
                        for pattern in patterns:
                            if pattern.search(line):
                                findings.append(f"{filepath}:{line_number}: {line.strip()}")
                                break # Move to next line
            except UnicodeDecodeError:
                # Skip binary files or non-utf8 files
                pass

    if findings:
        helpers.write_color_host('WARNING', 'Stale or disallowed references found:')
        for finding in findings:
            helpers.write_color_host('ERROR', finding)
        sys.exit(1)

    helpers.write_color_host('SUCCESS', 'No stale or disallowed references found.')
    sys.exit(0)

if __name__ == "__main__":
    main()
