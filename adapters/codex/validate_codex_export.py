import os
import sys
import re
import json

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    codex_skills_dir = os.path.join(script_dir, "skills")
    root = os.path.dirname(os.path.dirname(script_dir))
    
    manifest_path = os.path.join(root, "plugin.json")
    if not os.path.isfile(manifest_path):
        print(f"\033[91mERROR: plugin.json not found at {manifest_path}\033[0m")
        sys.exit(1)
        
    with open(manifest_path, 'r', encoding='utf-8') as f:
        manifest = json.load(f)
        
    skills = [s.get('slug') for s in manifest.get('skills', []) if s.get('activation_level') != 'Governor']
    
    errors = 0
    
    for skill in skills:
        if not skill:
            continue
            
        skill_dir = os.path.join(codex_skills_dir, skill)
        if not os.path.isdir(skill_dir):
            print(f"\033[91mERROR: Missing exported skill folder: {skill_dir}\033[0m")
            errors += 1
            continue
            
        skill_file = os.path.join(skill_dir, "SKILL.md")
        if not os.path.isfile(skill_file):
            print(f"\033[91mERROR: Missing SKILL.md in exported {skill}\033[0m")
            errors += 1
        else:
            with open(skill_file, 'r', encoding='utf-8') as f:
                content = f.read()
                
            fm_match = re.search(r'(?s)^---\r?\n(.*?)\r?\n---', content)
            if fm_match:
                fm = fm_match.group(1)
                lines = fm.splitlines()
                for line in lines:
                    if not re.match(r'^name:', line) and not re.match(r'^description:', line):
                        print(f"\033[91mERROR: Exported SKILL.md for {skill} contains non-compliant frontmatter: {line}\033[0m")
                        errors += 1
                if not re.search(rf"^name:\s*{re.escape(skill)}", fm, re.MULTILINE):
                    print(f"\033[91mERROR: Exported SKILL.md for {skill} has mismatched name in frontmatter\033[0m")
                    errors += 1
            else:
                print(f"\033[91mERROR: Could not parse frontmatter in exported SKILL.md for {skill}\033[0m")
                errors += 1
                
        out_file = os.path.join(skill_dir, "OUTPUT_FORMATS.md")
        if not os.path.isfile(out_file):
            print(f"\033[91mERROR: Missing OUTPUT_FORMATS.md in exported {skill}\033[0m")
            errors += 1
            
        stale_routing = os.path.join(skill_dir, "ROUTING_MATRIX.md")
        if os.path.isfile(stale_routing):
            print(f"\033[91mERROR: Found stale ROUTING_MATRIX.md in exported {skill}\033[0m")
            errors += 1
            
        if skill == 'conductor':
            map_file = os.path.join(skill_dir, "ROUTING_MAP.md")
            if not os.path.isfile(map_file):
                print(f"\033[91mERROR: Missing ROUTING_MAP.md in exported conductor\033[0m")
                errors += 1
                
    if errors > 0:
        print(f"\033[91mERROR: Codex export validation failed with {errors} errors.\033[0m")
        sys.exit(1)
        
    print("\033[92mSUCCESS: Codex export validation passed!\033[0m")
    sys.exit(0)

if __name__ == "__main__":
    main()
