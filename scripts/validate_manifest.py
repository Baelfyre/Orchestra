import os
import sys
import re

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import helpers

def main():
    root = helpers.get_project_root()
    
    # Parse arguments if any, defaulting to ./plugin.json
    manifest_path = os.path.join(root, "plugin.json")
    for i, arg in enumerate(sys.argv):
        if arg.lower() in ["-manifestpath", "--manifestpath"] and i + 1 < len(sys.argv):
            path_arg = sys.argv[i + 1]
            if os.path.isabs(path_arg):
                manifest_path = path_arg
            else:
                manifest_path = os.path.join(root, path_arg)
                
    manifest = helpers.get_json_manifest(manifest_path)
    manifest_skills = manifest.get('skills', [])
    
    skills_dir = os.path.join(root, "skills")
    skill_folders = []
    if os.path.isdir(skills_dir):
        for item in os.listdir(skills_dir):
            if os.path.isdir(os.path.join(skills_dir, item)):
                skill_folders.append(item)
                
    skill_index_path = os.path.join(root, "SKILL_INDEX.md")
    skill_index_lines = []
    if os.path.exists(skill_index_path):
        with open(skill_index_path, 'r', encoding='utf-8') as f:
            skill_index_lines = f.readlines()
            
    errors = 0
    helpers.write_color_host('INFO', 'Manifest Validator: Cross-checking folders with manifest entries...')
    
    # Check that every manifest skill has a real folder
    for ms in manifest_skills:
        slug = ms.get('slug', '')
        folder_path = os.path.join(skills_dir, slug)
        if not os.path.isdir(folder_path):
            helpers.write_color_host('ERROR', f"Manifest lists skill '{slug}' but folder does not exist.")
            errors += 1
            
    # Iterate through actual folders and compare to manifest
    for skill_name in skill_folders:
        skill_folder_path = os.path.join(skills_dir, skill_name)
        skill_md_path = os.path.join(skill_folder_path, "SKILL.md")
        
        if not os.path.isfile(skill_md_path):
            continue
            
        ms = next((s for s in manifest_skills if s.get('slug') == skill_name), None)
        if not ms:
            helpers.write_color_host('ERROR', f"Skill folder '{skill_name}' exists but is not listed in the manifest.")
            errors += 1
            continue
            
        expected_skill_path = os.path.join(root, ms.get('skill_path', '').replace('/', os.sep))
        if not os.path.isfile(expected_skill_path):
            helpers.write_color_host('ERROR', f"Manifest skill_path '{ms.get('skill_path')}' for '{skill_name}' does not exist.")
            errors += 1
            
        expected_icon_path = os.path.join(root, ms.get('icon_path', '').replace('/', os.sep))
        if not os.path.isfile(expected_icon_path):
            helpers.write_color_host('ERROR', f"Manifest icon_path '{ms.get('icon_path')}' for '{skill_name}' does not exist.")
            errors += 1
            
        try:
            frontmatter = helpers.parse_frontmatter(skill_md_path)
            fields = ["name","description","slug","role","primary_use","avoid_when","activation_level","depends_on","output_formats"]
            
            skill_output_formats = []
            for field in fields:
                val = frontmatter.get(field)
                manifest_val = ms.get(field)
                
                if val is None:
                    helpers.write_color_host('ERROR', f"Missing field '{field}' in frontmatter of {skill_name}")
                    errors += 1
                    continue
                    
                if field == "output_formats":
                    val = re.sub(r'\[|\]', '', val)
                    arr = [x.strip() for x in val.split(',') if x.strip()]
                    skill_output_formats = arr
                    m_arr = manifest_val if isinstance(manifest_val, list) else []
                    
                    val_str = ','.join(arr)
                    m_val_str = ','.join([str(x) for x in m_arr])
                    
                    if val_str != m_val_str:
                        helpers.write_color_host('ERROR', f"Mismatch in {skill_name} -> output_formats. Frontmatter: '{val_str}', Manifest: '{m_val_str}'")
                        errors += 1
                else:
                    if str(val) != str(manifest_val):
                        helpers.write_color_host('ERROR', f"Mismatch in {skill_name} -> {field}. Frontmatter: '{val}', Manifest: '{manifest_val}'")
                        errors += 1
                        
            # Check OUTPUT_FORMATS.md headings
            formats_path = os.path.join(skill_folder_path, "OUTPUT_FORMATS.md")
            if os.path.isfile(formats_path):
                with open(formats_path, 'r', encoding='utf-8') as f:
                    formats_content = f.read()
                for fmt in skill_output_formats:
                    escaped_format = re.escape(fmt)
                    if not re.search(f"(?m)^##\\s+{escaped_format}(?:\\s*$|\\s*[:\\(].*$)", formats_content, re.IGNORECASE):
                        helpers.write_color_host('ERROR', f"Output format drift: Heading '## {fmt}' missing in OUTPUT_FORMATS.md for {skill_name}")
                        errors += 1
                        
            # Check SKILL_INDEX.md row sync
            escaped_slug = re.escape(skill_name)
            index_row = next((line for line in skill_index_lines if re.search(f"\\|\\s*`{escaped_slug}`\\s*\\|", line)), None)
            if index_row:
                columns = index_row.split('|')
                if len(columns) >= 9:
                    index_formats_raw = columns[-3] # In python, splitting '|  |  |' gives empty strings at start/end.
                    # Wait, powershell splits `| a | b |` into `['', ' a ', ' b ', '']`.
                    # So index -2 is the second to last element. 
                    index_formats_raw = columns[-2].replace('`', '')
                    index_arr = [x.strip() for x in index_formats_raw.split(',') if x.strip()]
                    index_val_str = ','.join(index_arr)
                    val_str = ','.join(skill_output_formats)
                    
                    if index_val_str != val_str:
                        helpers.write_color_host('ERROR', f"SKILL_INDEX.md drift: Output formats for {skill_name} do not match frontmatter. Expected: '{val_str}', Found: '{index_val_str}'")
                        errors += 1
                else:
                    helpers.write_color_host('ERROR', f"Invalid column count in SKILL_INDEX.md for {skill_name}")
                    errors += 1
            else:
                helpers.write_color_host('ERROR', f"Could not find row for {skill_name} in SKILL_INDEX.md")
                errors += 1
                
        except Exception as e:
            helpers.write_color_host('ERROR', f"Could not parse frontmatter in {skill_md_path}: {str(e)}")
            errors += 1
            
    if errors > 0:
        helpers.write_color_host('ERROR', f"Manifest validation failed with {errors} errors.")
        sys.exit(1)
        
    helpers.write_color_host('SUCCESS', "Manifest validation successful. All skills perfectly match the frontmatter source of truth.")
    sys.exit(0)

if __name__ == "__main__":
    main()
