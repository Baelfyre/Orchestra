import os
import sys
import argparse
import json
import uuid
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import helpers

def get_active_process_path(target_pid):
    try:
        import psutil
        p = psutil.Process(target_pid)
        return p.name()
    except Exception:
        # Fallback if psutil is removed/unavailable
        if helpers._pid_exists(target_pid):
            return "Unknown (pid exists)"
        return None

def check_lock(lock_file):
    if not os.path.isfile(lock_file):
        return None
    try:
        with open(lock_file, 'r', encoding='utf-8') as f:
            lock = json.load(f)

        lock_pid = lock.get('pid')
        timestamp_str = lock.get('timestamp')

        timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        age = datetime.now(timezone.utc) - timestamp

        if age.total_seconds() >= 3600:
            helpers.write_color_host('WARNING', "Stale lock detected (older than 1 hour).")
            return None

        p_name = get_active_process_path(lock_pid)
        if p_name is None:
            helpers.write_color_host('WARNING', f"Stale lock detected (process PID {lock_pid} is not running).")
            return None

        return lock
    except Exception:
        return None

def acquire_lock(lock_file, session_id, process_id):
    existing = check_lock(lock_file)
    if existing:
        raise RuntimeError(f"LOCK_COLLISION: Active lock held by Session '{existing.get('session_id')}' (PID: {existing.get('pid')}) acquired at {existing.get('timestamp')}.")

    lock_data = {
        "session_id": session_id if session_id else str(uuid.uuid4()),
        "pid": int(process_id) if process_id else os.getpid(),
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

    amalgam_folder = os.path.dirname(lock_file)
    os.makedirs(amalgam_folder, exist_ok=True)

    with open(lock_file, 'w', encoding='utf-8') as f:
        json.dump(lock_data, f)

    helpers.write_color_host('SUCCESS', f"Lock acquired successfully for Session '{lock_data['session_id']}'.")

def release_lock(lock_file):
    if os.path.isfile(lock_file):
        try:
            os.remove(lock_file)
            helpers.write_color_host('SUCCESS', "Lock released successfully.")
        except OSError:
            pass
    else:
        helpers.write_color_host('INFO', "No active lock file found to release.")

def log_decision(root, details):
    if not details or not details.strip():
        raise ValueError("LogDecision requires --details.")

    log_path = os.path.join(root, "DECISION_LOG.md")
    date_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"\n- [{date_str}] (PID: {os.getpid()}) {details}"

    with open(log_path, 'a', encoding='utf-8') as f:
        f.write(log_entry)

    helpers.write_color_host('SUCCESS', "Decision appended safely to DECISION_LOG.md")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--action", choices=['Acquire', 'Release', 'Check', 'LogDecision'], required=True)
    parser.add_argument("--session-id", default="")
    parser.add_argument("--details", default="")
    parser.add_argument("--pid", type=int, default=0)
    args, _ = parser.parse_known_args()

    root = helpers.get_project_root()
    lock_file = os.path.join(root, ".amalgam", "lock.json")

    if args.action == 'Check':
        active = check_lock(lock_file)
        if active:
            helpers.write_color_host('WARNING', f"Active lock held by Session '{active.get('session_id')}'.")
            sys.exit(1)
        else:
            helpers.write_color_host('SUCCESS', "No active lock.")
            sys.exit(0)

    elif args.action == 'Acquire':
        try:
            acquire_lock(lock_file, args.session_id, args.pid)
            sys.exit(0)
        except Exception as e:
            helpers.write_color_host('ERROR', str(e))
            sys.exit(1)

    elif args.action == 'Release':
        release_lock(lock_file)
        sys.exit(0)

    elif args.action == 'LogDecision':
        try:
            log_decision(root, args.details)
            sys.exit(0)
        except Exception as e:
            helpers.write_color_host('ERROR', str(e))
            sys.exit(1)

if __name__ == "__main__":
    main()
