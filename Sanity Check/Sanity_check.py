import re
import csv

# Color mapping: N1-N8, NA, KP, CP -> hex codes
COLORS = {
    "N1": "#00BFFF",    # Blue
    "N2": "#93DB70",    # Green
    "N3": "#40E0D0",    # Turquoise
    "N4": "#B0E2FF",    # Light Blue
    "N5": "#B4FFB4",    # Light Green
    "N6": "#87CEEB",    # Sky Blue
    "N7": "#C6E2EB",    # Light Cyan
    "N8": "#6FFFC3",    # Light Green
    "NA": "#FF99FF",    # Pink
    "KP": "#FF1975",    # Red
    "CP": "#FFFF00",    # Yellow
}

# Hex to number mapping for N1-N8 (for morph validation)
HEX_TO_NUMBER = {
    "#00BFFF": "1", "#93DB70": "2", "#40E0D0": "3", "#B0E2FF": "4",
    "#B4FFB4": "5", "#87CEEB": "6", "#C6E2EB": "7", "#6FFFC3": "8",
}

def normalize_bgcolor(bgcolor):
    """Convert N1/N2/... to hex, or return as-is if already hex."""
    return COLORS.get(bgcolor, bgcolor)

def load_valid_strings(filename):
    """Load valid strings from a text file."""
    with open(filename, 'r', encoding='utf-8') as file:
        return [line.strip() for line in file if line.strip()]

def load_data(filename):
    """Load TSV or CSV file and convert it into a list of dictionaries.
    Auto-detects delimiter (tab for TSV, comma for CSV)."""
    with open(filename, 'r', encoding='utf-8') as file:
        sample = file.read(8192)
        file.seek(0)
        try:
            dialect = csv.Sniffer().sniff(sample, delimiters='\t,')
        except csv.Error:
            # Fallback: use extension
            dialect = csv.excel_tab() if filename.lower().endswith('.tsv') else csv.excel()
        reader = csv.DictReader(file, dialect=dialect)
        rows = []
        for i, row in enumerate(reader):
            row['_line_number'] = 2 + i  # Line 1 = header, so first data row = line 2
            rows.append(row)
        return rows

def check_kaaraka_sambandha(kaaraka_sambandha, morph_in_context, line_number, data):
    # Check for the first occurrence of कर्ता in kaaraka_sambandha
    match = re.search(r'कर्ता,(\d+\.\d+(\.\d+)?)', kaaraka_sambandha)
    if not 'अभिहित_कर्ता' in kaaraka_sambandha and match:
        target_index = match.group(1)  # This will capture indexes like 9.1 or 9.1.1
        target_item = next((d for d in data if str(d.get('anvaya_no', '')) == target_index), None)
        if target_item:
            target_morph_in_context = target_item.get('morph_in_context', '')
            target_line = target_item.get('_line_number', target_index)
            if '1' in morph_in_context and not ('क्तवतु') in target_morph_in_context and not ('कर्तरि') in target_morph_in_context:
                print(f'Error: Line {line_number} has कर्ता, but line {target_line} does not have कर्तरि or क्तवतु.')
            elif '3' in morph_in_context and not ('कर्मणि') in target_morph_in_context and not ('क्त') in target_morph_in_context and not ('तव्यत्') in target_morph_in_context and not ('अनीयर्') in target_morph_in_context: 
                print(f'Error: Line {line_number} has कर्ता, but line {target_line} does not have कर्मणि or क्त or तव्यत् or अनीयर्.')
            elif '6' in morph_in_context and not any(word in target_morph_in_context for word in ['ल्युट्', 'घञ्']):
                print(f'Error: Line {line_number} has कर्ता, but line {target_line} does not have ल्युट् or घञ्')

def check_constraints(data, valid_strings_file):
    pattern = re.compile(r'(?:पुं;|स्त्री;|नपुं;)(\d+);')
    valid_strings = load_valid_strings(valid_strings_file)

    for i, item in enumerate(data):
        morph_in_context = item.get('morph_in_context', '')
        bgcolor = normalize_bgcolor(item.get('bgcolor', ''))
        kaaraka_sambandha = item.get('kaaraka_sambandha', '')
        possible_relations = item.get('possible_relations', '')
        anvaya_no = item.get('anvaya_no', '')
        line_number = item.get('_line_number', anvaya_no)
        word = item.get('word', '')

        # Check for extra spaces in any field
        for field, value in item.items():
            if isinstance(value, str) and (re.search(r'\s{2,}', value) or value != value.strip()):
                print(f"Error in line {line_number} - Extra spaces detected in field '{field}'.")

        if word in ["-","","."]:
            continue

        # New condition: Check if anvaya_no has a format X.Y or X.Y.Z and the word ends with "-"
        if re.match(r'^\d+\.\d+(\.\d+)?$', anvaya_no) and word.endswith('-'):
            # Extract the prefix (X) from the anvaya_no
            prefix = anvaya_no.split('.')[0]
            
            # Now, check if kaaraka_sambandha contains X.any_number (with any number after the dot)
            if not any(f"{prefix}." in kaaraka_sambandha for kaaraka in kaaraka_sambandha.split(';')):
                print(f'Error in line {line_number} - kaaraka_sambandha should contain {prefix}.any_number')

        if "अभिहित" in kaaraka_sambandha:
            continue

        if not 'अभिहित_कर्ता' in kaaraka_sambandha:
            check_kaaraka_sambandha(kaaraka_sambandha, morph_in_context, line_number, data)

        if kaaraka_sambandha in ["-", ""]:
            # Check if 'anvaya_no' appears in any other 'kaaraka_sambandha' across all data
            is_hanging_node = not any(anvaya_no in other_item.get('kaaraka_sambandha', '') for other_item in data if other_item != item)
            if is_hanging_node:
                print(f'Error in line {line_number} Hanging node detected')

        if '/' in morph_in_context:
            print(f'Error in line {line_number} - morph_in_context contains a "/"')

        if '#' in kaaraka_sambandha:
            print(f'Error in line {line_number} - kaaraka_sambandha contains a "#"')

        patterns = r'\b{}\b'.format(re.escape(str(anvaya_no)))
        if any(re.search(patterns, str(item)) for item in kaaraka_sambandha):
            print(f'Error in line {line_number} Self Loop Detected')

        if '{अव्य}' in morph_in_context and bgcolor != COLORS['NA']:
            print(f'Error in line {line_number} check Morph Analysis and Color Code')

        if 'कर्तरि;' in morph_in_context and bgcolor != COLORS['KP']:
            print(f'Error in line {line_number} check Morph Analysis and Color Code')

        delimiter = '#' if '#' in possible_relations else ';'

        # Split using the chosen delimiter
        kaaraka_list = kaaraka_sambandha.split(delimiter)
        possible_list = possible_relations.split(delimiter)

        # Check if each item in kaaraka_list has a corresponding item in possible_list with valid prefix, suffix, or number variations
        if not all(
            any(
                # Ensure item has both parts before accessing by index
                len(parts := item.split(',')) == 2 and
                possible.endswith(parts[1]) and (
                    possible.startswith(parts[0]) or 
                    possible.startswith(f"सुप्_{parts[0]}") or
                    re.match(rf"^{parts[0]}\d*,{parts[1]}$", possible)  # Matches हेतुः3, प्रयोजनम्1, etc.
                )
                for possible in possible_list
            )
            for item in kaaraka_list
        ):
            if bgcolor == COLORS['KP'] and possible_relations == "-" and "अभिहित" in kaaraka_list:
                continue
            if kaaraka_sambandha in ["-", ""]:
                continue
            print(f'Error in line {line_number} - kaaraka_sambandha not found in possible_relations')
        
        if not any(valid_str in kaaraka_sambandha and valid_str in possible_relations for valid_str in valid_strings):
            if kaaraka_sambandha == "-" and possible_relations == "-":
                continue
            print(f'Error in line {line_number} - No valid string found in kaaraka_sambandha or in possible_relations')

        if 'हेतुः' in kaaraka_sambandha and not ('3' in morph_in_context or '5' in morph_in_context or 'तसिल्' in morph_in_context):
            print(f'Error in line {line_number} - check kaaraka_sambandha and morph_in_context')

        if 'करण,' in kaaraka_sambandha and not '3' in morph_in_context:
            print(f'Error in line {line_number} - check kaaraka_sambandha and morph_in_context')

        if any(phrase in kaaraka_sambandha for phrase in ['विषयाधिकरणम्', 'देशाधिकरणम्', 'कालाधिकरणम्', 'अधिकरणम्']) and not ('7' in morph_in_context or 'अव्य' in morph_in_context):
            print(f'Error in line {line_number} - check kaaraka_sambandha and morph_in_context')

        if 'सम्प्रदानम्' in kaaraka_sambandha and not '4' in morph_in_context:
            print(f'Error in line {line_number} - check kaaraka_sambandha and morph_in_context')

        if 'अपादानम्' in kaaraka_sambandha and not '5' in morph_in_context:
            print(f'Error in line {line_number} - check kaaraka_sambandha and morph_in_context')

        if 'पूर्वकालः' in kaaraka_sambandha and not any(phrase in morph_in_context for phrase in ['क्त्वा', 'ल्यप्']):
            print(f'Error in line {line_number} - check kaaraka_sambandha and morph_in_context')

        if 'षष्ठीसम्बन्धः' in kaaraka_sambandha and not '6' in morph_in_context:
            print(f'Error in line {line_number} - check kaaraka_sambandha and morph_in_context')

        if 'भावलक्षणसप्तमी' in kaaraka_sambandha and not '7' in morph_in_context:
            print(f'Error in line {line_number} - check kaaraka_sambandha and morph_in_context')

        if 'वर्तमानसमानकालः' in kaaraka_sambandha and not any(phrase in morph_in_context for phrase in ['शतृ', 'शानच्']):
            print(f'Error in line {line_number} - check kaaraka_sambandha and morph_in_context')

        if 'प्रयोजककर्ता' in kaaraka_sambandha:
            match = re.search(r'प्रयोजककर्ता,(\d+\.\d+)', kaaraka_sambandha)
            if match:
                target_index = match.group(1)
                if '1' in morph_in_context:
                    target_item = next((d for d in data if str(d.get('anvaya_no', '')) == target_index), None)
                    if target_item and 'णिच्' not in target_item.get('morph_in_context', ''):
                        target_line = target_item.get('_line_number', target_index)
                        print(f'Error: Line {line_number} has प्रयोजककर्ता, but line {target_line} does not have णिच्')
                if not ('1' in morph_in_context or '3' in morph_in_context):
                    print(f'Error in line {line_number} - check kaaraka_sambandha and morph_in_context')

        if 'प्रयोज्यकर्ता' in kaaraka_sambandha:
            match = re.search(r'प्रयोज्यकर्ता,(\d+\.\d+)', kaaraka_sambandha)
            if match:
                target_index = match.group(1)
                if '3' in morph_in_context:
                    target_item = next((d for d in data if str(d.get('anvaya_no', '')) == target_index), None)
                    if target_item and 'णिच्' not in target_item.get('morph_in_context', ''):
                        target_line = target_item.get('_line_number', target_index)
                        print(f'Error: Line {line_number} has प्रयोज्यकर्ता, but line {target_line} does not have णिच्')
                if not ('2' in morph_in_context or '3' in morph_in_context):
                    print(f'Error in line {line_number} - check kaaraka_sambandha and morph_in_context')

        integers_in_morph = pattern.findall(morph_in_context)
        bgcolor_has_morph = (any(number in bgcolor for number in integers_in_morph) or
                             (bgcolor in HEX_TO_NUMBER and HEX_TO_NUMBER[bgcolor] in integers_in_morph))
        if integers_in_morph and not bgcolor_has_morph:
            print(f'Error in line {line_number} check the following details:')
            print(f'Morph Analysis: {morph_in_context}')
            print(f'bgcolor: {bgcolor}')

# Example usage - auto-finds .tsv and .csv files in the script's folder
if __name__ == '__main__':
    import os
    script_dir = os.path.dirname(os.path.abspath(__file__))
    data_files = sorted(
        f for f in os.listdir(script_dir)
        if f.endswith(('.tsv', '.csv'))
    )
    valid_strings_file = os.path.join(script_dir, 'valid_strings.txt')
    if not data_files:
        print('No .tsv or .csv files found in this folder.')
    for data_file in data_files:
        filepath = os.path.join(script_dir, data_file)
        print(f'\n--- Checking {data_file} ---\n')
        data = load_data(filepath)
        check_constraints(data, valid_strings_file)

# slef lopp 3 digit error
