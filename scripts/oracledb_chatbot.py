# Name: oracledb_chatbot.py
# Description: A Python script that creates a chatbot for querying an Oracle Autonomous Database using a locally installed Large Language Model (LLM) via Ollama. The script reads Oracle connection details from a file (oracle_connection.txt), connects to the database, and uses the LLM to convert natural language queries into SQL. It executes these queries and displays results in a user-friendly chat interface. The database schema includes tables: Authors (author_id, first_name, last_name, nationality), Books (book_id, title, author_id, publication_year, genre), and Borrowers (borrower_id, book_id, borrower_name, borrow_date).
# Python Version: 3.8 or higher
# Libraries Used:
#   - oracledb: To connect to Oracle Autonomous Database
#   - ollama: To interact with the locally installed LLM
#   - re: To extract SQL queries from LLM responses
#   - os: To check for the existence of oracle_connection.txt
#   - sys: To handle program exit on errors
#   - subprocess: To check if Ollama server is running
# Ollama Version: Latest version compatible with LLaMA 3.2 (e.g., 0.3.12 or higher)
# Local Model: LLaMA 3.2 (must be installed locally via Ollama; configurable in script)
#
# Usage:
#   - Run the script from the command line: python3 oracledb_chatbot.py
#   - The script expects a file named oracle_connection.txt in the current directory with the following format:
#     username="your_username"
#     password="your_password"
#     dsn="your_service_name"
#     wallet_path="full_path_to_wallet_directory"
#     wallet_password="your_wallet_password"
#   - Example oracle_connection.txt:
#     username="ADMIN"
#     password="your_password"
#     dsn="g59000506af6ca7_oracledb_low"
#     wallet_path="/Users/Anand/Downloads/Wallet_oracledb"
#     wallet_password="your_wallet_password"
#   - The script checks if the Ollama server is running and if the specified LLM model is available.
#   - If the server or model is not available, it provides instructions to start/install Ollama.
#   - The chat interface opens with a greeting, accepts natural language queries, generates SQL, executes them, and displays results.
#   - Type 'exit' to quit the chat interface.
#
# Installation and Setup:
#   1. Install Python 3.8+.
#   2. Install required libraries:
#      pip install oracledb ollama
#   3. Install Oracle Instant Client:
#      - Download the Oracle Instant Client for macOS (e.g., 19c or higher) from https://www.oracle.com/database/technologies/instant-client/macos-intel-x86-downloads.html
#      - Extract and set environment variables:
#        export ORACLE_HOME=~/instantclient_19_8
#        export PATH=$ORACLE_HOME:$PATH
#   4. Configure Oracle Autonomous Database Wallet:
#      - Download the wallet from the Oracle Cloud Console for your Autonomous Database.
#      - Unzip it to a directory (e.g., /Users/Anand/Downloads/Wallet_oracledb).
#      - Set the TNS_ADMIN environment variable:
#        export TNS_ADMIN=/Users/Anand/Downloads/Wallet_oracledb
#   5. Install Ollama locally:
#      - Download and install Ollama from https://ollama.com/download (available for macOS).
#      - Example for macOS:
#        curl -fsSL https://ollama.com/install.sh | sh
#   6. Pull the LLaMA 3.2 model:
#      ollama pull llama3.2
#   7. Start the Ollama server before running the script:
#      ollama serve
#      - Run this in a separate terminal window to keep the server active.
#   - Note: Ensure the Ollama server and Oracle Instant Client are properly configured before running the script.
#
# Script Workflow:
#   1. Checks for the existence of oracle_connection.txt and reads connection details.
#   2. Validates the Ollama server and LLM model availability.
#   3. Establishes a connection to the Oracle Autonomous Database using oracledb.
#   4. Initializes a chat interface with a greeting.
#   5. Accepts natural language queries, uses the LLM to generate SQL, and executes queries on the database.
#   6. Displays query results in a readable format or an error message if the query fails.
#   7. Closes the database connection when the user exits or an error occurs.
#
# Error Handling:
#   - Checks for missing or invalid oracle_connection.txt, including required wallet_password.
#   - Verifies Ollama server and model availability with clear setup instructions.
#   - Handles database connection errors and invalid SQL queries.
#   - Provides user-friendly error messages for unanswerable queries.
#
# Notes:
#   - The default LLM model is LLaMA 3.2. Change MODEL_NAME constant to use a more capable model (e.g., 'mistral:7b') if SQL generation is inaccurate.
#   - Ensure sufficient memory (e.g., 8GB+ RAM) for running LLaMA 3.2 locally on macOS; 16GB+ recommended for larger models like mistral:7b.
#   - The Oracle Autonomous Database Free Tier is supported, but ensure the database is running and accessible.
#   - For complex queries, refine the LLM prompt or try a more advanced model if SQL generation is inaccurate.
#   - The wallet_password is required for encrypted wallets, as used in this setup.

import oracledb
import ollama
import re
import os
import sys
import subprocess

# Configuration
MODEL_NAME = 'llama3.2'  # Matches your installed model

def check_ollama_server():
    """Check if Ollama server is running by attempting to list models."""
    try:
        subprocess.check_output(['ollama', 'list'])
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def check_ollama_model(model_name=MODEL_NAME):
    """Check if the specified model is available."""
    try:
        models = subprocess.check_output(['ollama', 'list']).decode('utf-8')
        return model_name in models
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def read_connection_details(file_path='oracle_connection.txt'):
    """Read Oracle connection details from oracle_connection.txt."""
    if not os.path.exists(file_path):
        print(f"Error: {file_path} not found in the current directory.")
        print("Please create oracle_connection.txt with the following format:")
        print('username="your_username"')
        print('password="your_password"')
        print('dsn="your_service_name"')
        print('wallet_path="full_path_to_wallet_directory"')
        print('wallet_password="your_wallet_password"')
        sys.exit(1)
    
    config = {}
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                # Remove comments and strip whitespace
                line = line.split('#')[0].strip()
                if '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip().strip('"')
                    config[key] = value
        required_keys = ['username', 'password', 'dsn', 'wallet_path', 'wallet_password']
        missing_keys = [key for key in required_keys if key not in config]
        if missing_keys:
            print(f"Error: Missing keys in {file_path}: {', '.join(missing_keys)}")
            sys.exit(1)
        return config
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        sys.exit(1)

def connect_to_oracle(config):
    """Establish connection to Oracle Autonomous Database."""
    try:
        connect_params = {
            'user': config['username'],
            'password': config['password'],
            'dsn': config['dsn'],
            'config_dir': config['wallet_path'],
            'wallet_location': config['wallet_path'],
            'wallet_password': config['wallet_password']
        }
        connection = oracledb.connect(**connect_params)
        print("Successfully connected to Oracle Autonomous Database.")
        return connection
    except oracledb.Error as e:
        print(f"Error connecting to Oracle Database: {e}")
        print("Ensure the following:")
        print("- Oracle Instant Client is installed and configured.")
        print("- Wallet files are in the specified wallet_path.")
        print("- TNS_ADMIN environment variable is set to the wallet_path.")
        print("- The wallet_password is correct.")
        print("- The database is running and accessible in Oracle Cloud Console.")
        sys.exit(1)

def generate_sql(query, model_name=MODEL_NAME):
    """Generate SQL from natural language query using LLM."""
    prompt = f"""
    You are an expert in Oracle SQL with access to the following database schema:
    - Authors (author_id, first_name, last_name, nationality)
    - Books (book_id, title, author_id, publication_year, genre)
    - Borrowers (borrower_id, book_id, borrower_name, borrow_date)

    Your task is to convert the user's natural language query into a valid Oracle SQL query. The query is: "{query}"

    Instructions:
    - Return ONLY the SQL query, enclosed in triple backticks: ```sql <query> ```sql
    - Do NOT include explanations, prose, or multiple queries.
    - Do NOT end the query with a semicolon (;).
    - Use table aliases (e.g., b for Books, a for Authors).
    - Authors are linked to Books via author_id (Books.author_id = Authors.author_id).
    - For date-based queries (e.g., month/year), use EXTRACT on borrow_date (e.g., EXTRACT(MONTH FROM borrow_date) = 5).
    - Do NOT assume columns exist outside the schema (e.g., no 'author' column in Books).
    - If the query cannot be converted, return: ```sql -- Cannot generate SQL for this query ```sql

    Examples:
    Query: "list all books by George Orwell"
    ```sql
    SELECT b.title
    FROM Books b
    JOIN Authors a ON b.author_id = a.author_id
    WHERE a.last_name = 'Orwell'
    ```sql

    Query: "Who borrowed books in May 2025"
    ```sql
    SELECT b.borrower_name, b.borrow_date
    FROM Borrowers b
    JOIN Books bo ON b.book_id = bo.book_id
    WHERE EXTRACT(MONTH FROM b.borrow_date) = 5
    AND EXTRACT(YEAR FROM b.borrow_date) = 2025
    ```sql

    Query: "How many books are in the Fantasy genre?"
    ```sql
    SELECT COUNT(b.book_id)
    FROM Books b
    WHERE b.genre = 'Fantasy'
    ```sql
    """
    try:
        response = ollama.generate(model=model_name, prompt=prompt)
        raw_response = response['response'].strip()
        print(f"Debug: LLM raw response:\n{raw_response}\n")  # Debug output
        # Extract SQL query
        sql_match = re.search(r'```sql\s*(.*?)\s*```', raw_response, re.DOTALL)
        if sql_match:
            sql = sql_match.group(1).strip()
            # Remove semicolon if present
            sql = sql.rstrip(';').strip()
            print(f"Debug: Cleaned SQL:\n{sql}\n")  # Debug cleaned SQL
            if sql.startswith('-- Cannot generate'):
                print("LLM indicated query cannot be generated.")
                return None
            return sql
        print("Warning: LLM response did not contain a valid SQL query.")
        return None
    except Exception as e:
        print(f"Error generating SQL: {e}")
        return None

def execute_query(connection, sql):
    """Execute SQL query and return results."""
    try:
        cursor = connection.cursor()
        cursor.execute(sql)
        if sql.strip().upper().startswith("SELECT"):
            columns = [col[0] for col in cursor.description]
            results = cursor.fetchall()
            cursor.close()
            if not results:
                return columns, "No results found for this query."
            return columns, results
        else:
            connection.commit()
            cursor.close()
            return None, "Query executed successfully."
    except oracledb.Error as e:
        return None, f"Error executing query: {str(e)}"

def main():
    """Main function to run the Oracle DB chatbot."""
    # Check if Ollama server is running
    if not check_ollama_server():
        print("Ollama server is not running. Please follow these steps:")
        print("1. Install Ollama from https://ollama.com/download")
        print(f"2. Pull the {MODEL_NAME} model: ollama pull {MODEL_NAME}")
        print("3. Start the Ollama server: ollama serve")
        print("Run the server in a separate terminal and try again.")
        sys.exit(1)
    
    # Check if the specified model is available
    if not check_ollama_model(MODEL_NAME):
        print(f"{MODEL_NAME} model is not installed. Please run:")
        print(f"ollama pull {MODEL_NAME}")
        print("Then restart the script.")
        sys.exit(1)
    
    # Read Oracle connection details
    config = read_connection_details()
    
    # Connect to Oracle Database
    connection = connect_to_oracle(config)
    
    try:
        # Initialize chat interface
        print("\n=== Oracle Database Chatbot ===")
        print("Hello! I'm ready to answer questions about the library database.")
        print("Ask about books, authors, or borrowers. Type 'exit' to quit.")
        print("Example questions:")
        print("- List all books by George Orwell.")
        print("- Who borrowed books in May 2025?")
        print("- How many books are in the Fantasy genre?")
        print("================================\n")
        
        while True:
            user_query = input("You: ").strip()
            if user_query.lower() == 'exit':
                print("Goodbye!")
                break
            if not user_query:
                print("Please enter a question.")
                continue
            
            # Generate SQL using LLM
            sql = generate_sql(user_query)
            if not sql:
                print("Sorry, I couldn't generate a valid SQL query. Please try again.")
                continue
            
            print(f"Generated SQL: {sql}")
            
            # Execute SQL query
            columns, results = execute_query(connection, sql)
            if isinstance(results, str):
                print(f"Bot: {results}\n")
            else:
                print("\nBot: Results:")
                print(columns)
                for row in results:
                    print(row)
                print()
    
    finally:
        # Ensure connection is closed
        connection.close()
        print("Database connection closed.")

if __name__ == '__main__':
    main()
