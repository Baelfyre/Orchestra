import os
import json
import datetime

def get_project_root():
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def get_aliases():
    root = get_project_root()
    alias_path = os.path.join(root, 'aliases.json')
    if os.path.exists(alias_path):
        with open(alias_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def resolve_slug(slug):
    aliases = get_aliases()
    return aliases.get(slug, slug)

def test_file_not_empty(path):
    if not os.path.isfile(path):
        return False
    try:
        return os.path.getsize(path) >= 10
    except OSError:
        return False

def write_color_host(msg_type, message):
    colors = {
        'SUCCESS': '\033[92m', # Green
        'WARNING': '\033[93m', # Yellow
        'ERROR': '\033[91m',   # Red
        'INFO': '\033[96m',    # Cyan
    }
    reset = '\033[0m'
    color = colors.get(msg_type, '\033[96m')
    print(f"{color}[{msg_type}] {message}{reset}")

def get_json_manifest(path=""):
    root = get_project_root()
    if not path:
        path = os.path.join(root, 'plugin.json')
    if not os.path.exists(path):
        raise FileNotFoundError(f"Manifest file not found at: {path}")
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def parse_frontmatter(path):
    import re
    if not os.path.exists(path):
        raise FileNotFoundError(f"File not found: {path}")
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    match = re.search(r'^---\s*(.*?)\s*---', content, re.MULTILINE | re.DOTALL)
    if match:
        frontmatter_text = match.group(1)
        fields = {}
        for line in frontmatter_text.splitlines():
            m = re.match(r'^([^:]+):\s*(.*)$', line)
            if m:
                key = m.group(1).strip()
                val = m.group(2).strip()
                fields[key] = val
        return fields
    raise ValueError(f"Frontmatter not found in file: {path}")

def test_workflow_locked():
    root = get_project_root()
    lock_file = os.path.join(root, '.amalgam', 'lock.json')
    if not os.path.exists(lock_file):
        return False
    try:
        with open(lock_file, 'r', encoding='utf-8') as f:
            lock = json.load(f)
        lock_pid = lock.get('pid')
        timestamp_str = lock.get('timestamp')
        
        # Parse ISO 8601 timestamp (simplified)
        from datetime import datetime
        try:
            timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            age = datetime.now(timestamp.tzinfo) - timestamp
            if age.total_seconds() >= 3600:
                return False
        except Exception:
            pass

        if _pid_exists(lock_pid):
            return True
    except Exception:
        pass
    return False

def _pid_exists(pid):
    if pid <= 0:
        return False
    if os.name == 'nt':
        import ctypes
        kernel32 = ctypes.windll.kernel32
        PROCESS_QUERY_INFORMATION = 0x0400
        process = kernel32.OpenProcess(PROCESS_QUERY_INFORMATION, False, pid)
        if process:
            kernel32.CloseHandle(process)
            return True
        return False
    else:
        try:
            os.kill(pid, 0)
            return True
        except OSError:
            return False
