#!/usr/bin/env python3

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

    if '-h' in sys.argv or '--help' in sys.argv:
        print("""
Summarize Text Documents and Forex Trading CSVs with Ollama
=========================================================

**Purpose**:
This script (`summary.py`) summarizes text documents or forex trading CSVs in the current directory using a locally installed Ollama model.
It processes files matching a specified wildcard pattern (e.g., '*.txt', '*.csv', '*.pdf') or all '*.txt' files by default.
For CSVs, it calculates trading metrics (total profit/loss, net profit, trade count, percentage of profitable/loss-making trades).
Summaries are displayed in the terminal and saved to files named 'summary_<original_filename>.txt'.

**Usage**:
    python summary.py [pattern] [-m model]
    python summary.py -h  # Show this help message

**Examples**:
    python summary.py             # Summarize all *.txt files
    python summary.py file.txt    # Summarize file.txt
    python summary.py *.csv       # Summarize all *.csv files (with trading metrics)
    python summary.py *.pdf       # Summarize all *.pdf files
    python summary.py project*.doc # Summarize files matching project*.doc
    python summary.py *.rtf       # Summarize all *.rtf files
    python summary.py -m llama3.1:70b *.csv  # Use a different model

**Setup Requirements**:
1. **Python Version**:
   - Tested on Python 3.12. Ensure Python 3.8+ is installed (run `python3 --version`).
   - Install from https://www.python.org if needed.

2. **Ollama**:
   - Install Ollama locally (https://ollama.ai/download) for macOS/Linux/Windows.
   - Pull the desired model: `ollama pull llama3.2`.
   - Start the Ollama server with minimal logs: `ollama serve > /dev/null 2>&1 &`.
   - Verify server: `curl http://localhost:11434` (should return "Ollama is running").
   - Check port: `lsof -i :11434`. If port 11434 is in use, kill the process (`kill <PID>`) and restart.
   - Check running processes: `ps aux | grep ollama`.

3. **Python Libraries**:
   - Install required libraries in a virtual environment:
     ```bash
     python3 -m venv venv
     source venv/bin/activate  # On macOS/Linux
     pip install ollama python-docx pdfplumber striprtf markdown beautifulsoup4 requests
""")
