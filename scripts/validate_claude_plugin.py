import os
import json
import glob
import sys

def check_file_exists(path):
    if not os.path.exists(path):
        print(f"FAIL: Missing file {path}")
        return False
    print(f"PASS: Found file {path}")
    return True

def read_json(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def main():
    workspace_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    plugin_json_path = os.path.join(workspace_root, '.claude-plugin', 'plugin.json')
    marketplace_json_path = os.path.join(workspace_root, '.claude-plugin', 'marketplace.json')

    success = True
    success &= check_file_exists(plugin_json_path)
    success &= check_file_exists(marketplace_json_path)

    if not success:
        sys.exit(1)

    plugin_data = read_json(plugin_json_path)
    marketplace_data = read_json(marketplace_json_path)

    if plugin_data.get('name') != 'orchestra':
        print("FAIL: Plugin name is not 'orchestra'")
        success = False
    else:
        print("PASS: Plugin name is 'orchestra'")

    if marketplace_data.get('name') != 'orchestra':
        print("FAIL: Marketplace name is not 'orchestra'")
        success = False
    else:
        print("PASS: Marketplace name is 'orchestra'")

    plugins = marketplace_data.get('plugins', [])
    orchestra_plugin = next((p for p in plugins if p.get('name') == 'orchestra'), None)
    if not orchestra_plugin:
        print("FAIL: Marketplace does not contain a plugin entry named 'orchestra'")
        success = False
    else:
        print("PASS: Marketplace contains a plugin entry named 'orchestra'")

        if orchestra_plugin.get('source') != '.':
            print("FAIL: Marketplace plugin source is not '.'")
            success = False
        else:
            print("PASS: Marketplace plugin source is '.'")

        if plugin_data.get('version') != orchestra_plugin.get('version'):
            print(f"FAIL: Version mismatch. Plugin: {plugin_data.get('version')}, Marketplace: {orchestra_plugin.get('version')}")
            success = False
        else:
            print("PASS: Manifest version and marketplace plugin version match")

    # Check skills/*/SKILL.md
    skills_dir = os.path.join(workspace_root, 'skills')
    if os.path.exists(skills_dir):
        skill_folders = [f for f in os.listdir(skills_dir) if os.path.isdir(os.path.join(skills_dir, f))]
        for folder in skill_folders:
            skill_md_path = os.path.join(skills_dir, folder, 'SKILL.md')
            if not os.path.exists(skill_md_path):
                print(f"FAIL: Missing {skill_md_path}")
                success = False
            else:
                pass # print(f"PASS: Found {folder}/SKILL.md")
        print("PASS: Checked skills/*/SKILL.md existence")

    # Check commands/*.md readability
    commands_dir = os.path.join(workspace_root, 'commands')
    if os.path.exists(commands_dir):
        command_files = glob.glob(os.path.join(commands_dir, '*.md'))
        for cmd_file in command_files:
            try:
                with open(cmd_file, 'r', encoding='utf-8') as f:
                    f.read()
            except Exception as e:
                print(f"FAIL: Cannot read {cmd_file}: {e}")
                success = False
        print("PASS: Checked commands/*.md readability")

    # Check for hardcoded paths or escapes
    # We'll do a simple grep-like check in all tracked files inside .claude-plugin, commands, skills, hooks, scripts
    check_dirs = ['skills', 'commands', 'hooks', 'scripts', '.claude-plugin']
    for d in check_dirs:
        dir_path = os.path.join(workspace_root, d)
        if not os.path.exists(dir_path):
            continue
        for root, _, files in os.walk(dir_path):
            for file in files:
                file_path = os.path.join(root, file)
                # Skip binary files or pyc
                if file.endswith('.pyc') or file.endswith('.ico') or file.endswith('.png'):
                    continue
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        lines = f.readlines()
                        for i, line in enumerate(lines):
                            if '..' in line and '.claude-plugin' in file_path:
                                # Naive check for escaping plugin root.
                                print(f"WARNING: Potential path escape '..' found in {file_path}:{i+1}")
                            if 'C:\\' in line or '/Users/' in line:
                                print(f"WARNING: Potential hardcoded local repo path in {file_path}:{i+1}")
                except Exception:
                    pass
    print("PASS: Scanned for path escapes and hardcoded paths (warnings above)")

    if success:
        print("All checks passed.")
        sys.exit(0)
    else:
        print("Some checks failed.")
        sys.exit(1)

if __name__ == '__main__':
    main()
