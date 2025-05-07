# Name: doc_based_chatbot.py
# Description: A Python script that creates a document-based chatbot using a locally installed LLaMA 3.2 model via Ollama. The script reads .txt, .docx, or .csv files provided as command-line arguments, processes their content, and answers user questions based solely on the documents. It includes a chat interface with a greeting and handles cases where questions cannot be answered from the documents.
# Python Version: 3.8 or higher
# Libraries Used:
#   - ollama: To interact with the locally installed LLaMA 3.2 model
#   - docx: To read .docx files (python-docx)
#   - pandas: To read .csv files
#   - sys: To handle command-line arguments
#   - os: To check file existence and extensions
#   - subprocess: To check if Ollama server is running
# Ollama Version: Latest version compatible with LLaMA 3.2 (e.g., 0.3.12 or higher)
# Local Model: LLaMA 3.2 (must be installed locally via Ollama)
#
# Usage:
#   - Run the script from the command line with one or more document files (.txt, .docx, .csv) as arguments.
#   - Example: python3 doc_based_chatbot.py document1.txt document2.docx data.csv
#   - The script checks if the Ollama server is running and if the LLaMA 3.2 model is available.
#   - If the server is not running, it provides instructions to start/install Ollama.
#   - After reading documents, it opens a chat interface, issues a greeting, and waits for user questions.
#   - Questions are answered based only on document content. If a question cannot be answered, it responds: "I do not have information for that question."
#   - Type 'exit' to quit the chat interface.
#
# Installation and Setup:
#   1. Install Python 3.8+.
#   2. Install required libraries:
#      pip install ollama python-docx pandas
#   3. Install Ollama locally:
#      - Download and install Ollama from https://ollama.com/download (available for Linux, macOS, Windows).
#      - Example for macOS/Linux:
#        curl -fsSL https://ollama.com/install.sh | sh
#      - For Windows, download the installer from the website.
#   4. Pull the LLaMA 3.2 model:
#      ollama pull llama3.2
#   5. Start the Ollama server before running the script:
#      ollama serve
#      - Run this in a separate terminal window to keep the server active.
#   - Note: Ensure the Ollama server is running in the background before executing the script.
#
# Script Workflow:
#   1. Checks if the Ollama server is running using subprocess.
#   2. Validates command-line arguments (at least one valid .txt, .docx, or .csv file).
#   3. Reads and processes document content:
#      - .txt: Reads raw text.
#      - .docx: Extracts text from paragraphs.
#      - .csv: Converts rows to readable text.
#   4. Combines document content into a single context for the LLaMA model.
#   5. Initializes a chat interface with a greeting.
#   6. Uses Ollama to generate answers based on document context.
#   7. Handles unanswerable questions with a default response.
#
# Error Handling:
#   - Checks for invalid file extensions or missing files.
#   - Verifies Ollama server and model availability.
#   - Provides clear error messages and setup instructions.
#
# Notes:
#   - The script assumes LLaMA 3.2 is installed via Ollama. Replace 'llama3.2' with another model name if needed.
#   - Ensure sufficient memory (e.g., 8GB+ RAM) for running LLaMA 3.2 locally.
#   - Keep the Ollama server running in a separate terminal.

import sys
import os
import subprocess
import ollama
import docx
import pandas as pd

def check_ollama_server():
    # Check if Ollama server is running by attempting to list models
    try:
        subprocess.check_output(['ollama', 'list'])
        return True
    except subprocess.CalledProcessError:
        return False
    except FileNotFoundError:
        return False

def check_ollama_model(model_name='llama3.2'):
    # Check if the specified model is available
    try:
        models = subprocess.check_output(['ollama', 'list']).decode('utf-8')
        return model_name in models
    except subprocess.CalledProcessError:
        return False
    except FileNotFoundError:
        return False

def read_txt_file(file_path):
    # Read content from a .txt file
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return ""

def read_docx_file(file_path):
    # Read content from a .docx file
    try:
        doc = docx.Document(file_path)
        content = [para.text for para in doc.paragraphs if para.text.strip()]
        return "\n".join(content)
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return ""

def read_csv_file(file_path):
    # Read content from a .csv file
    try:
        df = pd.read_csv(file_path)
        # Convert DataFrame to a readable string
        content = []
        for index, row in df.iterrows():
            row_str = ", ".join([f"{col}: {val}" for col, val in row.items()])
            content.append(f"Row {index + 1}: {row_str}")
        return "\n".join(content)
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return ""

def read_documents(file_paths):
    # Process all provided documents and combine their content
    content = []
    valid_extensions = {'.txt', '.docx', '.csv'}
    
    for file_path in file_paths:
        if not os.path.exists(file_path):
            print(f"File not found: {file_path}")
            continue
        ext = os.path.splitext(file_path)[1].lower()
        if ext not in valid_extensions:
            print(f"Unsupported file type: {file_path}. Supported types: .txt, .docx, .csv")
            continue
        
        if ext == '.txt':
            text = read_txt_file(file_path)
        elif ext == '.docx':
            text = read_docx_file(file_path)
        elif ext == '.csv':
            text = read_csv_file(file_path)
        
        if text:
            content.append(f"--- Content from {file_path} ---\n{text}")
    
    return "\n\n".join(content)

def generate_response(question, context, model_name='llama3.2'):
    # Generate a response using Ollama based on document context
    prompt = (
        f"You are a chatbot that answers questions based solely on the provided document content. "
        f"Do not use external knowledge. If the question cannot be answered using the document, "
        f"respond with: 'I do not have information for that question.'\n\n"
        f"Document Content:\n{context}\n\n"
        f"Question: {question}\n\n"
        f"Answer:"
    )
    
    try:
        response = ollama.generate(model=model_name, prompt=prompt)
        answer = response['response'].strip()
        # Check if the response is empty or generic to catch unanswerable questions
        if not answer or answer.lower() in ['unknown', 'not provided', 'no information']:
            return "I do not have information for that question."
        return answer
    except Exception as e:
        print(f"Error generating response: {e}")
        return "I do not have information for that question."

def main():
    # Main function to run the chatbot
    # Check if Ollama server is running
    if not check_ollama_server():
        print("Ollama server is not running. Please follow these steps:")
        print("1. Install Ollama from https://ollama.com/download")
        print("2. Pull the LLaMA 3.2 model: ollama pull llama3.2")
        print("3. Start the Ollama server: ollama serve")
        print("Run the server in a separate terminal and try again.")
        sys.exit(1)
    
    # Check if LLaMA 3.2 model is available
    if not check_ollama_model('llama3.2'):
        print("LLaMA 3.2 model is not installed. Please run:")
        print("ollama pull llama3.2")
        print("Then restart the script.")
        sys.exit(1)
    
    # Check command-line arguments
    if len(sys.argv) < 2:
        print("Usage: python3 doc_based_chatbot.py <file1> [<file2> ...]")
        print("Supported file types: .txt, .docx, .csv")
        sys.exit(1)
    
    # Read documents
    file_paths = sys.argv[1:]
    context = read_documents(file_paths)
    
    if not context:
        print("No valid content was read from the provided files. Please check the files and try again.")
        sys.exit(1)
    
    # Initialize chat interface
    print("\n=== Document-Based Chatbot ===")
    print("Hello! I'm ready to answer questions based on the provided documents.")
    print("Type your question, or 'exit' to quit.")
    print("================================\n")
    
    while True:
        question = input("You: ").strip()
        if question.lower() == 'exit':
            print("Goodbye!")
            break
        if not question:
            print("Please enter a question.")
            continue
        
        # Generate and display response
        response = generate_response(question, context)
        print(f"Bot: {response}\n")

if __name__ == '__main__':
    main()
