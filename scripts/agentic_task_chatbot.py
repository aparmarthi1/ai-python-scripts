from flask import Flask, request, render_template
from openai import AzureOpenAI
from azure.cosmos import CosmosClient, PartitionKey
import os
from datetime import datetime

app = Flask(__name__)

# Azure OpenAI setup
openai_client = AzureOpenAI(
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    api_version="2024-02-15-preview"
)

# Azure Cosmos DB setup
cosmos_client = CosmosClient(os.getenv("COSMOS_ENDPOINT"), os.getenv("COSMOS_KEY"))
database = cosmos_client.get_database_client("TasksDB")
container = database.get_container_client("Tasks")

def task_parser_agent(user_input):
    """Worker Agent 1: Parse user input into structured task data."""
    try:
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a Task Parser Agent. Parse the user's task request into a JSON object with task name, due date (ISO format), and priority (low/medium/high based on keywords like 'urgent'). Example: {'task': 'Meeting', 'due_date': '2025-07-06T10:00:00', 'priority': 'Medium'}"},
                {"role": "user", "content": user_input}
            ]
        )
        return eval(response.choices[0].message.content)  # Assuming JSON response
    except Exception as e:
        return {"error": f"Task parsing failed: {str(e)}"}

def suggestion_agent(task_data):
    """Worker Agent 2: Generate a proactive suggestion based on task data."""
    if "error" in task_data:
        return {"suggestion": "Unable to generate suggestion due to parsing error."}
    try:
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a Suggestion Agent. Based on the task data, suggest a proactive follow-up action (e.g., reminder, related task). Return JSON: {'suggestion': str}"},
                {"role": "user", "content": str(task_data)}
            ]
        )
        return eval(response.choices[0].message.content)  # Assuming JSON response
    except Exception as e:
        return {"suggestion": f"Suggestion generation failed: {str(e)}"}

def master_coordinating_agent(user_input):
    """Master Agent: Coordinate task parsing, suggestion generation, and storage."""
    # Step 1: Delegate to Task Parser Agent
    task_data = task_parser_agent(user_input)
    if "error" in task_data:
        return {"response": task_data["error"], "suggestion": None}
    
    # Step 2: Delegate to Suggestion Agent
    suggestion_data = suggestion_agent(task_data)
    
    # Step 3: Store task in Cosmos DB
    task_record = {
        "id": str(datetime.now().timestamp()),
        "task": task_data["task"],
        "due_date": task_data["due_date"],
        "priority": task_data["priority"],
        "created_at": datetime.now().isoformat()
    }
    try:
        container.create_item(task_record)
        response = f"Task '{task_data['task']}' scheduled for {task_data['due_date']} (Priority: {task_data['priority']})."
    except Exception as e:
        response = f"Failed to store task: {str(e)}"
    
    return {"response": response, "suggestion": suggestion_data.get("suggestion")}

@app.route("/", methods=["GET", "POST"])
def index():
    response = None
    suggestion = None
    if request.method == "POST":
        user_input = request.form["task"]
        result = master_coordinating_agent(user_input)
        response = result["response"]
        suggestion = result["suggestion"]
    
    return render_template("index.html", response=response, suggestion=suggestion)

if __name__ == "__main__":
    app.run(debug=True)
