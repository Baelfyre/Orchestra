import os
import json
import datetime
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from orchestra_runtime.repositories import ManifestRepository, SkillSourceRepository

def get_project_root():
    return str(PROJECT_ROOT)

def get_aliases():
    root = Path(get_project_root())
    return ManifestRepository(root).load_aliases()

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
    manifest_repo = ManifestRepository(Path(path).parent if Path(path).name == "plugin.json" else Path(root))
    if os.path.abspath(path) == os.path.join(root, 'plugin.json'):
        return manifest_repo.load_manifest()
    if not os.path.exists(path):
        raise FileNotFoundError(f"Manifest file not found at: {path}")
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def parse_frontmatter(path):
    if not os.path.exists(path):
        raise FileNotFoundError(f"File not found: {path}")
    return SkillSourceRepository.parse_frontmatter(Path(path))

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
