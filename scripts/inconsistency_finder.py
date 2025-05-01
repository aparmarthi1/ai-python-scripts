import argparse
import glob
import os
from docx import Document
import ollama
from itertools import combinations
import requests
import re

def check_ollama_server():
    """Check if the Ollama server is running on the default port (11434)."""
    url = "http://localhost:11434"
    try:
        response = requests.get(url)
        if response.status_code == 200 and response.text == "Ollama is running":
            return True
        return False
    except requests.ConnectionError:
        return False

def read_txt_file(file_path):
    """Read lines from a text file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return [(line.strip(), idx + 1) for idx, line in enumerate(f) if line.strip()]
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return []

def read_docx_file(file_path):
    """Read paragraphs from a docx file."""
    try:
        doc = Document(file_path)
        return [(para.text.strip(), idx + 1) for idx, para in enumerate(doc.paragraphs) if para.text.strip()]
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return []

def extract_content(file_path):
    """Extract content from a file based on its extension."""
    ext = os.path.splitext(file_path)[1].lower()
    if ext == '.txt':
        return read_txt_file(file_path)
    elif ext == '.docx':
        return read_docx_file(file_path)
    else:
        print(f"Unsupported file type: {file_path}")
        return []

def is_relevant_line(line):
    """Check if a line explicitly mentions 'return policy'."""
    return 'return policy' in line.lower()

def check_inconsistency(line1, line2, file1, file2, line_num1, line_num2):
    """Use Ollama to check if two lines are semantically inconsistent."""
    if not check_ollama_server():
        print("Error: Ollama server is not running on port 11434. Start it with 'ollama serve &'.")
        return "Error"
    
    prompt = (
        f"Compare the numerical or temporal values (e.g., number of days, quantities, amounts) in the following two statements. "
        f"Return 'Inconsistent' if the numerical or temporal values differ (e.g., different number of days), along with a brief explanation identifying the specific difference. "
        f"Ignore differences in wording, procedural steps (e.g., contacting support, packaging requirements), or unrelated conditions. "
        f"Return 'Consistent' if the statements have no numerical or temporal differences or are unrelated:\n"
        f"Statement 1: {line1}\n"
        f"Statement 2: {line2}\n"
        f"Example: If one statement says '30 days' and another says '60 days,' return 'Inconsistent: The durations differ (30 days vs. 60 days).'"
    )
    try:
        response = ollama.chat(model='llama3.2', messages=[
            {'role': 'user', 'content': prompt}
        ])
        result = response['message']['content'].strip()
        # Post-process to ensure only numerical/temporal inconsistencies are flagged
        if "Inconsistent" in result:
            if not re.search(r'\b(days|duration|quantit|amount)\b', result.lower()):
                result = "Consistent: Post-processed to ignore non-numerical/temporal inconsistency."
        return result
    except Exception as e:
        print(f"Error with Ollama model: {e}")
        return "Error"

def find_inconsistencies(file_pattern):
    """Find inconsistencies across files matching the pattern."""
    if not check_ollama_server():
        print("Error: Ollama server is not running on port 11434. Start it with 'ollama serve &'.")
        return

    files = glob.glob(file_pattern)
    if not files:
        print("No files found matching the pattern.")
        return

    # Extract content from all files
    file_contents = {}
    for file in files:
        content = extract_content(file)
        if content:
            # Filter only relevant lines
            relevant_content = [(line, num) for line, num in content if is_relevant_line(line)]
            if relevant_content:
                file_contents[file] = relevant_content
            else:
                print(f"No relevant lines found in {file} (skipping).")

    if len(file_contents) < 2:
        print("Need at least two files with relevant lines to compare.")
        return

    # Compare pairs of files
    inconsistencies = []
    for file1, file2 in combinations(file_contents.keys(), 2):
        content1 = file_contents[file1]
        content2 = file_contents[file2]

        # Compare each relevant line in file1 with each relevant line in file2
        for line1, line_num1 in content1:
            for line2, line_num2 in content2:
                result = check_inconsistency(line1, line2, file1, file2, line_num1, line_num2)
                if "Inconsistent" in result:
                    inconsistencies.append({
                        'file1': file1,
                        'line1': line_num1,
                        'text1': line1,
                        'file2': file2,
                        'line2': line_num2,
                        'text2': line2,
                        'explanation': result
                    })

    # Report inconsistencies
    if inconsistencies:
        print("\nInconsistencies found:")
        for inc in inconsistencies:
            print(f"\nFile: {inc['file1']}, Line {inc['line1']}: {inc['text1']}")
            print(f"File: {inc['file2']}, Line {inc['line2']}: {inc['text2']}")
            print(f"Explanation: {inc['explanation']}")
    else:
        print("No inconsistencies found.")

def main():
    parser = argparse.ArgumentParser(description="Find inconsistencies in files using Ollama.")
    parser.add_argument('pattern', help="File pattern (e.g., *.docx or *.txt)")
    args = parser.parse_args()

    find_inconsistencies(args.pattern)

if __name__ == "__main__":
    main()
