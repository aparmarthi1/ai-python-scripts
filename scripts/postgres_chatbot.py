# Name: postgresdb_chatbot.py
# Description: A Python script that creates a chatbot for querying an Azure Database for PostgreSQL Flexible Server using a locally installed Large Language Model (LLM) via Ollama. The script reads PostgreSQL connection details from a file (postgres_connection.txt), connects to the database, and uses the LLM to convert natural language queries into SQL. It executes these queries and displays results in a user-friendly chat interface. The database schema includes tables: Authors (author_id, first_name, last_name, nationality), Books (book_id, title, author_id, publication_year, genre), and Borrowers (borrower_id, book_id, borrower_name, borrow_date).
# Python Version: 3.8 or higher
# Libraries Used:
#   - psycopg2: To connect to Azure PostgreSQL database
#   - ollama: To interact with the locally installed LLM
#   - re: To extract SQL queries from LLM responses
#   - os: To check for the existence of postgres_connection.txt
#   - sys: To handle program exit on errors
#   - subprocess: To check if Ollama server is running
# Ollama Version: Latest version compatible with LLaMA 3.2 (e.g., 0.3.12 or higher)
# Local Model: LLaMA 3.2 (must be installed locally via Ollama; configurable in script)
#
# Usage:
#   - Run the script from the command line: python3 postgressdb_chatbot.py
#   - The script expects a file named postgres_connection.txt in the current directory with the following format:
#     host="your_host"
#     port="your_port"
#     database="your_database"
#     username="your_username"
#     password="your_password"
#   - Example postgres_connection.txt:
#     host="myfreepostgresdb.postgres.database.azure.com"
#     port="5432"
#     database="postgres"
#     username="pgadmin@myfreepostgresdb"
#     password="your_password"
#   - The script checks if the Ollama server is running and if the specified LLM model is available.
#   - If the server or model is not available, it provides instructions to start/install Ollama.
#   - The chat interface opens with a greeting, accepts natural language queries, generates SQL, executes them, and displays results.
#   - Type 'exit' to quit the chat interface.
#
# Installation and Setup:
#   1. Install Python 3.8+.
#   2. Install required libraries:
#      pip install psycopg2-binary ollama
#   3. Set up Azure PostgreSQL Database:
#      - Create a free Azure Database for PostgreSQL Flexible Server instance in the Azure portal.
#      - Select Burstable B1MS instance and ≤32 GB storage to stay within free tier limits.
#      - Configure public access and add your client IP to the firewall rules.
#      - Note the host, port, database, username, and password from the Azure portal.
#   4. Install Ollama locally:
#      - Download and install Ollama from https://ollama.com/download (available for macOS).
#      - Example for macOS:
#        curl -fsSL https://ollama.com/install.sh | sh
#   5. Pull the LLaMA 3.2 model:
#      ollama pull llama3.2
#   6. Start the Ollama server before running the script:
#      ollama serve
#      - Run this in a separate terminal window to keep the server active.
#
# Script Workflow:
#   1. Checks for the existence of postgres_connection.txt and reads connection details.
#   2. Validates the Ollama server and LLM model availability.
#   3. Establishes a connection to the Azure PostgreSQL database using psycopg2.
#   4. Initializes a chat interface with a greeting.
#   5. Accepts natural language queries, uses the LLM to generate SQL, and executes queries on the database.
#   6. Displays query results in a readable format or an error message if the query fails.
#   7. Closes the database connection when the user exits or an error occurs.
#
# Error Handling:
#   - Checks for missing or invalid postgres_connection.txt.
#   - Verifies Ollama server and model availability with clear setup instructions.
#   - Handles database connection errors and invalid SQL queries.
#   - Provides user-friendly error messages for unanswerable queries.
#
# Notes:
#   - The default LLM model is LLaMA 3.2. Change MODEL_NAME constant to use a more capable model (e.g., 'mistral:7b') if SQL generation is inaccurate.
#   - Ensure sufficient memory (e.g., 8GB+ RAM) for running LLaMA 3.2 locally on macOS; 16GB+ recommended for larger models like mistral:7b.
#   - The Azure free account provides 750 hours of PostgreSQL Flexible Server (Burstable B1MS) and 32 GB storage for 12 months.
#   - For complex queries, refine the LLM prompt or try a more advanced model if SQL generation is inaccurate.
#   - Clean up Azure resources after testing to avoid charges beyond the free tier.

import psycopg2
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

def read_connection_details(file_path='postgres_connection.txt'):
    """Read PostgreSQL connection details from postgres_connection.txt."""
    if not os.path.exists(file_path):
        print(f"Error: {file_path} not found in the current directory.")
        print("Please create postgres_connection.txt with the following format:")
        print('host="your_host"')
        print('port="your_port"')
        print('database="your_database"')
        print('username="your_username"')
        print('password="your_password"')
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
        required_keys = ['host', 'port', 'database', 'username', 'password']
        missing_keys = [key for key in required_keys if key not in config]
        if missing_keys:
            print(f"Error: Missing keys in {file_path}: {', '.join(missing_keys)}")
            sys.exit(1)
        return config
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        sys.exit(1)

def connect_to_postgres(config):
    """Establish connection to Azure PostgreSQL database."""
    try:
        connection = psycopg2.connect(
            host=config['host'],
            port=config['port'],
            database=config['database'],
            user=config['username'],
            password=config['password'],
            sslmode='require'  # Azure PostgreSQL requires SSL
        )
        print("Successfully connected to Azure PostgreSQL database.")
        return connection
    except psycopg2.Error as e:
        print(f"Error connecting to PostgreSQL database: {e}")
        print("Ensure the following:")
        print("- PostgreSQL server details (host, port, database, username, password) are correct.")
        print("- Your client IP is added to the server's firewall rules in the Azure portal.")
        print("- The PostgreSQL server is running and accessible.")
        sys.exit(1)

def generate_sql(query, model_name=MODEL_NAME):
    """Generate SQL from natural language query using LLM."""
    prompt = f"""
    You are an expert in PostgreSQL with access to the following database schema:
    - Authors (author_id SERIAL PRIMARY KEY, first_name VARCHAR(50), last_name VARCHAR(50), nationality VARCHAR(50))
    - Books (book_id SERIAL PRIMARY KEY, title VARCHAR(100), author_id INTEGER REFERENCES Authors(author_id), publication_year INTEGER, genre VARCHAR(50))
    - Borrowers (borrower_id SERIAL PRIMARY KEY, book_id INTEGER REFERENCES Books(book_id), borrower_name VARCHAR(100), borrow_date DATE)

    Your task is to convert the user's natural language query into a valid PostgreSQL query. The query is: "{query}"

    Instructions:
    - Return ONLY the SQL query, enclosed in triple backticks: ```sql <query> ```sql
    - Do NOT include explanations, prose, or multiple queries.
    - Do NOT end the query with a semicolon (;).
    - Use table aliases (e.g., b for Books, a for Authors).
    - Authors are linked to Books via author_id (Books.author_id = Authors.author_id).
    - For date-based queries (e.g., month/year), use EXTRACT on borrow_date (e.g., EXTRACT(MONTH FROM borrow_date) = 5).
    - Do NOT assume columns exist outside the schema (e.g., no 'author' column in Books).
    - If the query cannot be converted, return: ```sql -- Cannot generate SQL for this query ```sql
    - Avoid unnecessary JOINs or columns unless required by the query.

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

    Query: "list book in Fantasy genre"
    ```sql
    SELECT b.title
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
            columns = [desc[0].upper() for desc in cursor.description]
            results = cursor.fetchall()
            cursor.close()
            if not results:
                return columns, "No results found for this query."
            return columns, results
        else:
            connection.commit()
            cursor.close()
            return None, "Query executed successfully."
    except psycopg2.Error as e:
        return None, f"Error executing query: {str(e)}"

def main():
    """Main function to run the PostgreSQL DB chatbot."""
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
    
    # Read PostgreSQL connection details
    config = read_connection_details()
    
    # Connect to PostgreSQL database
    connection = connect_to_postgres(config)
    
    try:
        # Initialize chat interface
        print("\n=== PostgreSQL Database Chatbot ===")
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
