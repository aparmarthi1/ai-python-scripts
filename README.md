# AI Python Scripts

A collection of Python scripts for AI-driven text analysis, including summarization and inconsistency detection.

## Folder Structure
- **scripts/**: Contains Python scripts.
  - **summary.py**: Generates summaries of text files using LLaMA 3.2.
  - **inconsistency_finder.py**: Detects numerical/temporal inconsistencies in text files.
- **docs/**: Documentation files.
  - **usage.txt**: Detailed usage instructions.

## Setup
1. Install dependencies: `pip install -r requirements.txt`
2. Start Ollama server: `ollama serve > /dev/null 2>&1 &`
3. Run scripts, e.g., `python scripts/summary.py file.txt`

## Requirements
- Python 3.12+
- Ollama with LLaMA 3.2
- Libraries: `python-docx`, `ollama`, `requests`

## Usage
See `docs/usage.txt` for detailed instructions.
