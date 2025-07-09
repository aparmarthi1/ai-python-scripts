from flask import Flask, request, render_template
from azure.cosmos import CosmosClient
from openai import AzureOpenAI
import os
from datetime import datetime

app = Flask(__name__)

# Initialize Azure OpenAI client
openai_client = AzureOpenAI(
    azure_endpoint=os.getenv("OPENAI_ENDPOINT"),
    api_key=os.getenv("OPENAI_KEY"),
    api_version="2024-07-01-preview"
)

# Initialize Cosmos DB client
cosmos_client = CosmosClient(os.getenv("COSMOS_ENDPOINT"), os.getenv("COSMOS_KEY"))
database = cosmos_client.get_database_client("TasksDB")
container = database.get_container_client("Tasks")

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        user_input = request.form['task']  # Updated to match index.html
        try:
            # Parse task with gpt-4o-mini
            response = openai_client.chat.completions.create(
                model=os.getenv("OPENAI_DEPLOYMENT"),  # agenticai-openai-gpt-4o-mini
                messages=[
                    {"role": "system", "content": "Parse the task input into task name, due date (ISO format), and priority (Low/Medium/High). Return JSON."},
                    {"role": "user", "content": user_input}
                ]
            )
            task_data = response.choices[0].message.content
            task_data = eval(task_data)  # Assuming LLM returns JSON string
            task_data['id'] = str(datetime.now().timestamp())
            task_data['created_at'] = datetime.now().isoformat()

            # Generate suggestion (optional, based on index.html)
            suggestion_response = openai_client.chat.completions.create(
                model=os.getenv("OPENAI_DEPLOYMENT"),
                messages=[
                    {"role": "system", "content": "Provide a brief suggestion for the task (e.g., reminders or follow-ups)."},
                    {"role": "user", "content": f"Suggest something for: {user_input}"}
                ]
            )
            suggestion = suggestion_response.choices[0].message.content

            # Store task in Cosmos DB
            container.create_item(task_data)
            return render_template('index.html', response="Task added successfully!", suggestion=suggestion)
        except Exception as e:
            return render_template('index.html', response=f"Error: {str(e)}")
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)
