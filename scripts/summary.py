
#!/usr/bin/env python3

"""
Script Name: summary.py

Description:
This script summarizes text documents or forex trading CSVs in the current directory using a locally installed Ollama model.
For text files (e.g., .txt, .docx, .pdf, .rtf, .md, .html), it generates a concise summary.
For CSVs, it calculates forex trading metrics (total trades, total profit/loss, net profit, profitable/loss-making trade percentages, currency pairs) and summarizes them.
Summaries are printed to the terminal and saved to files named 'summary_<original_filename>.txt'.

Functionality:
- Supports multiple file formats: .txt, .docx, .pdf, .rtf, .md, .html, .csv.
- For CSVs, identifies profit/loss columns and computes trading metrics.
- Uses Ollama's local LLM for summarization, ensuring data privacy.
- Processes files matching a user-specified wildcard pattern (e.g., '*.txt', '*.csv').

Arguments:
- pattern (optional): Wildcard pattern for files to summarize (e.g., '*.txt', '*.csv', '*.pdf').
  Default: '*.txt' if no pattern is provided.
- -m, --model (optional): Ollama model for summarization.
  Default: llama3.2.
  Example: -m llama3.1:70b

Usage:
Run the script from the command line in the directory containing the files to summarize.
Examples:
    python summary.py                  # Summarize all *.txt files
    python summary.py file.txt         # Summarize file.txt
    python summary.py *.csv            # Summarize all *.csv files (with trading metrics)
    python summary.py *.pdf            # Summarize all *.pdf files
    python summary.py project*.docx    # Summarize files matching project*.docx
    python summary.py -m llama3.1 *.rtf # Use llama3.1 model to summarize *.rtf files
    python summary.py -h               # Show help message

Python Version:
- Written for Python 3.12
- Compatible with Python 3.8 or higher
- Verify with: python3 --version
- Install Python: https://www.python.org/downloads/

Required Python Libraries:
- ollama: Interface with Ollama's local LLM
- python-docx: Read .docx files
- pdfplumber: Extract text from .pdf files
- striprtf: Parse .rtf files
- markdown: Convert Markdown to plain text
- beautifulsoup4: Parse .html files
- requests: Check Ollama server status
- pandas: Process .csv files
Install libraries in a virtual environment:
    python3 -m venv venv
    source venv/bin/activate  # On macOS/Linux
    pip install ollama python-docx pdfplumber striprtf markdown beautifulsoup4 requests pandas

LLM Model:
- Default model: llama3.2
- Alternative models: Any Ollama-compatible model (e.g., llama3.1, mistral)
- Specify via --model argument (e.g., -m llama3.1:70b)

Ollama Installation and Setup:
1. Install Ollama:
   - Download from https://ollama.ai/download (macOS/Linux/Windows)
   - Follow installation instructions for your OS
2. Pull the model:
    ollama pull llama3.2
3. Start the Ollama server in the background:
    ollama serve > /dev/null 2>&1 &
4. Verify the server is running:
    curl http://localhost:11434  # Should return "Ollama is running"
5. Check port 11434:
    lsof -i :11434
   If in use, kill the process: kill <PID>, then restart the server
6. Confirm Ollama process:
    ps aux | grep ollama
Note: The Ollama server must be running before executing the script.
"""

import argparse
import glob
import os
from pathlib import Path
import ollama
from docx import Document
import pdfplumber
from striprtf.striprtf import rtf_to_text
from bs4 import BeautifulSoup
import sys
import markdown
import requests
import pandas as pd

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

def extract_text_from_file(file_path):
    """Extract text from a file based on its extension."""
    ext = Path(file_path).suffix.lower()
    
    try:
        if ext == '.txt':
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        elif ext in ['.doc', '.docx']:
            doc = Document(file_path)
            return '\n'.join([para.text for para in doc.paragraphs if para.text.strip()])
        elif ext == '.pdf':
            with pdfplumber.open(file_path) as pdf:
                return '\n'.join([page.extract_text() or '' for page in pdf.pages])
        elif ext == '.rtf':
            with open(file_path, 'r', encoding='utf-8') as f:
                rtf_content = f.read()
                return rtf_to_text(rtf_content)
        elif ext == '.md':
            with open(file_path, 'r', encoding='utf-8') as f:
                md_text = f.read()
                return markdown.markdown(md_text, output_format='plain')
        elif ext == '.html':
            with open(file_path, 'r', encoding='utf-8') as f:
                soup = BeautifulSoup(f, 'html.parser')
                return soup.get_text(separator='\n', strip=True)
        elif ext == '.csv':
            df = pd.read_csv(file_path)
            return df.to_string(index=False)
        else:
            raise ValueError(f"Unsupported file extension: {ext}")
    except Exception as e:
        print(f"Error reading {file_path}: {str(e)}")
        return None

def summarize_csv(df, model='llama3.2'):
    """Generate a forex-focused summary for a CSV trading log."""
    if not check_ollama_server():
        print("Error: Ollama server is not running on port 11434. Start it with 'ollama serve &'.")
        return None
    
    try:
        # Identify profit/loss column (case-insensitive)
        profit_col = None
        for col in df.columns:
            if col.lower() in ['profit', 'p/l', 'pnl', 'profit/loss']:
                profit_col = col
                break
        if not profit_col:
            raise ValueError("No 'Profit' or similar column found in CSV.")
        
        # Calculate metrics
        total_trades = len(df)
        profits = df[profit_col][df[profit_col] > 0]
        losses = df[profit_col][df[profit_col] < 0]
        total_profit = profits.sum() if not profits.empty else 0
        total_loss = losses.sum() if not losses.empty else 0
        net_profit = df[profit_col].sum()
        profitable_trades = len(profits)
        loss_trades = len(losses)
        percent_profitable = (profitable_trades / total_trades * 100) if total_trades > 0 else 0
        percent_loss = (loss_trades / total_trades * 100) if total_trades > 0 else 0
        
        # Prepare metrics text
        metrics = (
            f"Total Trades: {total_trades}\n"
            f"Total Profit: ${total_profit:.2f}\n"
            f"Total Loss: ${total_loss:.2f}\n"
            f"Net Profit/Loss: ${net_profit:.2f}\n"
            f"Profitable Trades: {profitable_trades} ({percent_profitable:.2f}%)\n"
            f"Loss-Making Trades: {loss_trades} ({percent_loss:.2f}%)\n"
            f"Currency Pairs: {', '.join(df['Pair'].unique()) if 'Pair' in df.columns else 'N/A'}"
        )
        
        # Send to Ollama for summarization
        prompt = (
            "Generate a concise summary of the following forex trading log metrics. "
            "Include total trades, total profit, total loss, net profit/loss, percentage of profitable and loss-making trades, and mention key currency pairs if available:\n\n"
            f"{metrics}"
        )
        response = ollama.chat(model=model, messages=[
            {'role': 'user', 'content': prompt}
        ])
        return response['message']['content'].strip()
    except Exception as e:
        print(f"Error summarizing CSV: {str(e)}")
        return None

def summarize_text(text, model='llama3.2'):
    """Generate a summary of non-CSV text using the specified Ollama model."""
    if not check_ollama_server():
        print("Error: Ollama server is not running on port 11434. Start it with 'ollama serve &'.")
        return None
    try:
        response = ollama.chat(model=model, messages=[
            {'role': 'user', 'content': f'Summarize this text in a concise paragraph:\n\n{text}'}
        ])
        return response['message']['content'].strip()
    except Exception as e:
        print(f"Error summarizing text: {str(e)}")
        return None

def write_summary(file_path, summary):
    """Write the summary to a file named summary_<original_filename>.txt."""
    base_name = Path(file_path).stem
    summary_file = f"summary_{base_name}.txt"
    try:
        with open(summary_file, 'w', encoding='utf-8') as f:
            f.write(summary)
        return summary_file
    except Exception as e:
        print(f"Error writing summary to {summary_file}: {str(e)}")
        return None

def main():
    parser = argparse.ArgumentParser(
        description="Summarize text documents or forex trading CSVs in the current directory using Ollama.",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument(
        'pattern', 
        nargs='?', 
        default='*.txt', 
        help="Wildcard pattern for files to summarize (e.g., '*.txt', '*.csv', '*.pdf').\n"
             "Default: '*.txt' if no pattern is provided."
    )
    parser.add_argument(
        '-m', '--model', 
        default='llama3.2', 
        help="Ollama model to use for summarization (default: llama3.2)."
    )

    try:
        args = parser.parse_args()
    except Exception as e:
        print(f"Error parsing arguments: {str(e)}")
        sys.exit(1)

    if not args.pattern.startswith('*') and not os.path.exists(args.pattern):
        print(f"Error: File '{args.pattern}' does not exist in {os.getcwd()}")
        sys.exit(1)

    files = glob.glob(args.pattern)
    if not files:
        print(f"No files found matching pattern '{args.pattern}' in the current directory.")
        sys.exit(1)

    for file_path in files:
        if not os.path.exists(file_path):
            print(f"Skipping {file_path}: File does not exist.")
            continue

        ext = Path(file_path).suffix.lower()
        if ext == '.csv':
            try:
                df = pd.read_csv(file_path)
                summary = summarize_csv(df, model=args.model)
            except Exception as e:
                print(f"Error processing CSV {file_path}: {str(e)}")
                continue
        else:
            text = extract_text_from_file(file_path)
            if text is None or not text.strip():
                print(f"Skipping {file_path}: No text content found.")
                continue
            summary = summarize_text(text, model=args.model)

        if summary is None:
            print(f"Skipping {file_path}: Failed to generate summary.")
            continue

        print(f"Summary of {file_path}:\n{summary}\n")

        summary_file = write_summary(file_path, summary)
        if summary_file:
            print(f"Summary saved to {summary_file}")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Unexpected error in script execution: {str(e)}")
        sys.exit(1)
