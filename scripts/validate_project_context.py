import os
import sys
import argparse
import re
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import helpers

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", default="Implementation Mode")
    parser.add_argument("--context-file", default="PROJECT_CONTEXT.md")
    args, _ = parser.parse_known_args()
    
    root = helpers.get_project_root()
    context_path = os.path.join(root, args.context_file)
    
    if not os.path.isfile(context_path):
        if "Audit Mode" in args.mode or "Release Mode" in args.mode:
            helpers.write_color_host('ERROR', f"The Steward: {args.context_file} is missing. Cannot proceed with {args.mode} without context.")
            sys.exit(1)
        else:
            helpers.write_color_host('WARNING', f"The Steward: {args.context_file} is missing. This is allowed for {args.mode} but governance cannot be enforced.")
            sys.exit(0)
            
    with open(context_path, 'r', encoding='utf-8') as f:
        content = f.read()
        
    required_fields = [
        "Project Type",
        "Goal",
        "Release Target",
        "Data Use",
        "Dependencies",
        "Constraints"
    ]
    
    missing_fields = []
    
    for field in required_fields:
        # Match something like "Project Type: value" or "**Project Type:** value"
        pattern = re.compile(rf"{re.escape(field)}\s*:.*[^\s]", re.IGNORECASE)
        if not pattern.search(content):
            missing_fields.append(field)
            
    if missing_fields:
        missing_list = ", ".join(missing_fields)
        if "Audit Mode" in args.mode or "Release Mode" in args.mode:
            helpers.write_color_host('ERROR', f"The Steward: Project Context is incomplete. Missing required fields: {missing_list}")
            sys.exit(1)
        else:
            helpers.write_color_host('WARNING', f"The Steward: Project Context is incomplete. Missing required fields: {missing_list}. Proceeding for {args.mode}.")
            sys.exit(0)
            
    helpers.write_color_host('SUCCESS', "The Steward: Project Context is complete.")
    sys.exit(0)

if __name__ == "__main__":
    main()
