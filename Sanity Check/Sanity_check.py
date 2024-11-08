import re
import csv

def load_valid_strings(filename):
    """Load valid strings from a text file."""
    with open(filename, 'r', encoding='utf-8') as file:
        return [line.strip() for line in file if line.strip()]

def load_tsv(filename):
    """Load TSV file and convert it into a list of dictionaries."""
    with open(filename, 'r', encoding='utf-8') as file:
        reader = csv.DictReader(file, delimiter='\t')
        return [row for row in reader]

def check_kaaraka_sambandha(kaaraka_sambandha, morph_in_context, index, data):
    # Check for the first occurrence of कर्ता in kaaraka_sambandha
    match = re.search(r'कर्ता,(\d+\.\d+(\.\d+)?)', kaaraka_sambandha)
    if not 'अभिहित_कर्ता' in kaaraka_sambandha and match:
        target_index = match.group(1)  # This will capture indexes like 9.1 or 9.1.1
        target_item = next((d for d in data if str(d.get('index', '')) == target_index), None)
        if target_item:
            target_morph_in_context = target_item.get('morph_in_context', '')
            if '1' in morph_in_context and not ('कर्तरि' or 'क्तवतु') in target_morph_in_context:
                print(f'Error: Index {index} has कर्ता, but index {target_index} does not have कर्तरि.')
            elif '3' in morph_in_context and not ('कर्मणि' or 'क्त' or 'तव्यत्' or 'अनीयर्') in target_morph_in_context:
                print(f'Error: Index {index} has कर्ता, but index {target_index} does not have कर्मणि.')
            elif '6' in morph_in_context and not any(word in target_morph_in_context for word in ['ल्युट्', 'घञ्']):
                print(f'Error: Index {index} has कर्ता, but index {target_index} does not have ल्युट् or घञ्')

def check_constraints(data, valid_strings_file):
    pattern = re.compile(r'(?:पुं;|स्त्री;|नपुं;)(\d+);')
    valid_strings = load_valid_strings(valid_strings_file)

    for index, item in enumerate(data):
        morph_in_context = item.get('morph_in_context', '')
        color_code = item.get('color_code', '')
        kaaraka_sambandha = item.get('kaaraka_sambandha', '')
        possible_relations = item.get('possible_relations', '')
        indx = item.get('index', '')
        word = item.get('word', '')

        if word in ["-","","."]:
            continue

        if "अभिहित" in kaaraka_sambandha:
            continue

        if not 'अभिहित_कर्ता' in kaaraka_sambandha:
            check_kaaraka_sambandha(kaaraka_sambandha, morph_in_context, indx, data)

        if kaaraka_sambandha in ["-", ""]:
            # Check if 'index' appears in any other 'kaaraka_sambandha' across all data
            is_hanging_node = not any(indx in other_item.get('kaaraka_sambandha', '') for other_item in data if other_item != item)
            if is_hanging_node:
                print(f'Error in Index: {indx} Hanging node detected')

        if '/' in morph_in_context:
            print(f'Error in Index: {indx} - morph_in_context contains a "/"')

        if '#' in kaaraka_sambandha:
            print(f'Error in Index: {indx} - kaaraka_sambandha contains a "#"')

        patterns = r'\b{}\b'.format(re.escape(str(indx)))
        if any(re.search(patterns, str(item)) for item in kaaraka_sambandha):
            print(f'Error in Index: {indx} Self Loop Detected')

        if '{अव्य}' in morph_in_context and color_code != 'NA':
            print(f'Error in Index: {indx} check Morph Analysis and Color Code')

        if 'कर्तरि;' in morph_in_context and color_code != 'KP':
            print(f'Error in Index: {indx} check Morph Analysis and Color Code')

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
            if color_code == "KP" and possible_relations == "-" and "अभिहित" in kaaraka_list:
                continue
            if kaaraka_sambandha in ["-", ""]:
                continue
            print(f'Error in Index: {indx} - kaaraka_sambandha not found in possible_relations')
        
        if not any(valid_str in kaaraka_sambandha and valid_str in possible_relations for valid_str in valid_strings):
            if kaaraka_sambandha == "-" and possible_relations == "-":
                continue
            print(f'Error in Index: {indx} - No valid string found in kaaraka_sambandha or in possible_relations')

        if 'हेतुः' in kaaraka_sambandha and not ('3' in morph_in_context or '5' in morph_in_context or 'तसिल्' in morph_in_context):
            print(f'Error in Index: {indx} - check kaaraka_sambandha and morph_in_context')

        if 'करण,' in kaaraka_sambandha and not '3' in morph_in_context:
            print(f'Error in Index: {indx} - check kaaraka_sambandha and morph_in_context')

        if any(phrase in kaaraka_sambandha for phrase in ['विषयाधिकरणम्', 'देशाधिकरणम्', 'कालाधिकरणम्', 'अधिकरणम्']) and not ('7' in morph_in_context or 'अव्य' in morph_in_context):
            print(f'Error in Index: {indx} - check kaaraka_sambandha and morph_in_context')

        if 'सम्प्रदानम्' in kaaraka_sambandha and not '4' in morph_in_context:
            print(f'Error in Index: {indx} - check kaaraka_sambandha and morph_in_context')

        if 'अपादानम्' in kaaraka_sambandha and not '5' in morph_in_context:
            print(f'Error in Index: {indx} - check kaaraka_sambandha and morph_in_context')

        if 'पूर्वकालः' in kaaraka_sambandha and not any(phrase in morph_in_context for phrase in ['क्त्वा', 'ल्यप्']):
            print(f'Error in Index: {indx} - check kaaraka_sambandha and morph_in_context')

        if 'षष्ठीसम्बन्धः' in kaaraka_sambandha and not '6' in morph_in_context:
            print(f'Error in Index: {indx} - check kaaraka_sambandha and morph_in_context')

        if 'भावलक्षणसप्तमी' in kaaraka_sambandha and not '7' in morph_in_context:
            print(f'Error in Index: {indx} - check kaaraka_sambandha and morph_in_context')

        if 'वर्तमानसमानकालः' in kaaraka_sambandha and not any(phrase in morph_in_context for phrase in ['शतृ', 'शानच्']):
            print(f'Error in Index: {indx} - check kaaraka_sambandha and morph_in_context')

        if 'प्रयोजककर्ता' in kaaraka_sambandha:
            match = re.search(r'प्रयोजककर्ता,(\d+\.\d+)', kaaraka_sambandha)
            if match:
                target_index = match.group(1)
                if '1' in morph_in_context:
                    target_item = next((d for d in data if str(d.get('index', '')) == target_index), None)
                    if target_item and 'णिच्' not in target_item.get('morph_in_context', ''):
                        print(f'Error: Index {indx} has प्रयोजककर्ता, but index {target_index} does not have णिच्')
                if not ('1' in morph_in_context or '3' in morph_in_context):
                    print(f'Error in Index: {indx} - check kaaraka_sambandha and morph_in_context')

        if 'प्रयोज्यकर्ता' in kaaraka_sambandha:
            match = re.search(r'प्रयोज्यकर्ता,(\d+\.\d+)', kaaraka_sambandha)
            if match:
                target_index = match.group(1)
                if '3' in morph_in_context:
                    target_item = next((d for d in data if str(d.get('index', '')) == target_index), None)
                    if target_item and 'णिच्' not in target_item.get('morph_in_context', ''):
                        print(f'Error: Index {indx} has प्रयोज्यकर्ता, but index {target_index} does not have णिच्')
                if not ('2' in morph_in_context or '3' in morph_in_context):
                    print(f'Error in Index: {indx} - check kaaraka_sambandha and morph_in_context')

        integers_in_morph = pattern.findall(morph_in_context)
        if integers_in_morph and not any(number in color_code for number in integers_in_morph):
            print(f'Error in Index: {indx} check the following details:')
            print(f'Morph Analysis: {morph_in_context}')
            print(f'Color Code: {color_code}')

# Example usage
data = load_tsv('Sanity Check/02_05_2-06_1.tsv')
check_constraints(data, 'Sanity Check/valid_strings.txt')

# slef lopp 3 digit error
