import azure.functions as func
import json
import requests
import os
import logging
from datetime import date, timedelta
from azure.cosmos import CosmosClient

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# DeepSeek API configuration
DS_API_URL = os.getenv("DS_API_URL")
DS_API_KEY = os.getenv("DS_API_KEY")
headers = {"Authorization": f"Bearer {DS_API_KEY}", "Content-Type": "application/json"}

def parse_task_fallback(task_input):
    """Fallback parsing if DeepSeek API fails."""
    try:
        tomorrow = (date.today() + timedelta(days=1)).isoformat() + "T10:00:00Z"
        return {
            "task_name": task_input[:50],
            "due_date": tomorrow,
            "priority": "Medium",
            "processed": True
        }
    except Exception as e:
        logger.error(f"Fallback parsing error: {str(e)}")
        raise Exception("Failed to parse task with fallback")

def call_deepseek_api(prompt, max_retries=3, initial_delay=5):
    """Call DeepSeek API with retry logic for 503 errors."""
    for attempt in range(max_retries):
        try:
            payload = {
                "model": "deepseek-r1",
                "messages": [
                    {"role": "system", "content": "You are a helpful assistant that outputs JSON."},
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": 200,
                "temperature": 0.5
            }
            response = requests.post(DS_API_URL + "/v1/chat/completions", headers=headers, json=payload, timeout=60)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            if response.status_code == 503:
                logger.warning(f"503 error on attempt {attempt + 1}: {str(e)}")
                import time
                time.sleep(initial_delay * (2 ** attempt))
                continue
            else:
                logger.error(f"API error: {str(e)}")
                raise Exception(f"API Error: {str(e)}")
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error: {str(e)}")
            raise Exception(f"Request Error: {str(e)}")
    raise Exception("Max retries reached for DeepSeek API")

def main(req: func.DocumentList) -> func.Document:
    """Cosmos DB trigger to process new tasks."""
    logger.info("Function triggered by Cosmos DB change.")
    if not req:
        logger.warning("No documents received.")
        return None

    try:
        client = CosmosClient(os.getenv("COSMOS_ENDPOINT"), os.getenv("COSMOS_KEY"))
        database = client.get_database_client(os.getenv("COSMOS_DATABASE_NAME"))
        container = database.get_container_client(os.getenv("COSMOS_CONTAINER_NAME"))

        for doc in req:
            task_input = doc.get("task_name", "")
            if not task_input or doc.get("processed", False):
                continue

            parse_prompt = (
                f"Return a JSON object with fields: task_name (string), due_date (ISO format string, e.g., '2025-07-18T10:00:00Z'), and priority (string, one of 'Low', 'Medium', 'High'). Output only the JSON object, enclosed in ```json\n...\n```.\n"
                f"Task: {task_input}\n"
                f"Example: ```json\n{{\"task_name\": \"Schedule a meeting\", \"due_date\": \"2025-07-18T10:00:00Z\", \"priority\": \"Medium\"}}\n```"
            )
            try:
                parse_response = call_deepseek_api(parse_prompt)
                generated_text = parse_response["choices"][0]["message"]["content"]
                json_start = generated_text.find("```json\n") + 8
                json_end = generated_text.rfind("\n```")
                if json_start > 7 and json_end > json_start:
                    json_str = generated_text[json_start:json_end]
                    task_data = json.loads(json_str)
                else:
                    logger.warning(f"Invalid JSON format: {generated_text}. Using fallback.")
                    task_data = parse_task_fallback(task_input)
            except (json.JSONDecodeError, IndexError, KeyError, Exception) as e:
                logger.warning(f"Invalid JSON response: {parse_response}. Using fallback.")
                task_data = parse_task_fallback(task_input)

            task_data["id"] = doc["id"]
            task_data["created_at"] = doc.get("created_at")
            task_data["processed"] = True
            container.upsert_item(task_data)
            logger.info(f"Processed task: {task_data['task_name']}")

        return func.DocumentList(req)
    except Exception as e:
        logger.error(f"Error processing documents: {str(e)}")
        raise
