import os
import sys
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import scripts.helpers as helpers

def main():
    root = helpers.get_project_root()
    evals_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "governance-conformance-fixtures.json")
    
    if not os.path.isfile(evals_file):
        helpers.write_color_host('ERROR', f"Evals fixture not found at {evals_file}")
        sys.exit(1)
        
    with open(evals_file, 'r', encoding='utf-8') as f:
        evals = json.load(f)
        
    failed = False
    helpers.write_color_host('INFO', "Governance instruction conformance checks: Validating static behavioral expectations in source rules...")
    
    import re
    
    for ev in evals:
        skill = ev.get('skill', '')
        scenario = ev.get('scenario', '')
        pattern = ev.get('pattern', '')
        
        source_path = os.path.join(root, "skills", skill, "SKILL.md")
        agent_path = os.path.join(root, ".agents", "skills", skill, "SKILL.md")
        
        skill_path = None
        if os.path.isfile(source_path):
            skill_path = source_path
        elif os.path.isfile(agent_path):
            skill_path = agent_path
            helpers.write_color_host('WARNING', f"Validating local .agents copy for {skill}, source missing in skills/")
        else:
            helpers.write_color_host('ERROR', f"FAIL: {scenario} -> Skill file not found: {source_path}")
            failed = True
            continue
            
        with open(skill_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        if re.search(pattern, content):
            helpers.write_color_host('SUCCESS', f"PASS: {scenario}")
        else:
            helpers.write_color_host('ERROR', f"FAIL: {scenario} -> Rule missing or contradicted in {skill}/SKILL.md")
            failed = True
            
    if failed:
        helpers.write_color_host('ERROR', "Governance instruction conformance checks failed!")
        sys.exit(1)
    else:
        helpers.write_color_host('SUCCESS', "All static behavioral expectation checks passed.")
        sys.exit(0)

if __name__ == "__main__":
    main()
