import azure.functions as func
from azure.cosmos import CosmosClient
from datetime import datetime, timedelta
import logging

app = func.FunctionApp()

@app.schedule(schedule="0 */5 * * * *", arg_name="timer", run_on_startup=True)
def check_tasks(timer: func.TimerRequest) -> None:
    cosmos_client = CosmosClient(os.getenv("COSMOS_ENDPOINT"), os.getenv("COSMOS_KEY"))
    database = cosmos_client.get_database_client("TasksDB")
    container = database.get_container_client("Tasks")
    
    # Query tasks due within the next hour
    query = "SELECT * FROM c WHERE c.due_date <= @due_date"
    params = [{"name": "@due_date", "value": (datetime.now() + timedelta(hours=1)).isoformat()}]
    tasks = list(container.query_items(query=query, parameters=params, enable_cross_partition_query=True))
    
    for task in tasks:
        logging.info(f"Alert: Task '{task['task']}' is due by {task['due_date']} (Priority: {task['priority']})")
