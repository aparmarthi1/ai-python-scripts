## Server Metrics Failure Predictor (Azure AI)
## Purpose: Predicts server failure likelihood in the next 24 hours using Azure OpenAI's gpt-4o-mini model.
## Prerequisites: Python 3.7+, openai, pandas, numpy; Azure OpenAI resource with gpt-4o-mini deployed.
## Input: server_data.csv with columns: timestamp, host, cpu_usage_percent, memory_usage_percent, disk_io_mb_s, network_io_mb_s, storage_used_gb.
## Output: predictions.csv with columns: host, prediction, confidence, explanation; displayed on console.
## Usage: python3 scripts/server_metrics_failure_predictor_azure_ai.py server_data.csv
## Configuration: Requires azure_foundry.txt in /scripts with endpoint, key, model, deployment.
## Sample Files: server_data.csv (sample metrics data).
## GitHub: https://github.com/aparmarthi1/ai-python-scripts/blob/main/scripts/server_metrics_failure_predictor_azure_ai.py
import pandas as pd
import json
import numpy as np
from openai import AzureOpenAI
import sys

## Configuration constants
CONFIG_FILE = "scripts/azure_foundry.txt"  ## Azure OpenAI credentials
OUTPUT_FILE = "scripts/predictions.csv"    ## Output CSV for predictions
CPU_THRESHOLD = 80                         ## Flag CPU usage above 80%
MEMORY_THRESHOLD = 80                      ## Flag memory usage above 80%
DISK_IO_THRESHOLD = 20                     ## Flag disk I/O above 20 MB/s
STORAGE_CAPACITY = 500                     ## Storage capacity in GB
DATA_WINDOW = 100                          ## Analyze last 100 rows per host

## Load configuration from azure_foundry.txt
def load_config():
    config = {}
    with open(CONFIG_FILE, 'r') as file:
        for line in file:
            key, value = line.strip().split('=', 1)
            config[key.strip()] = value.strip()
    return config

## Load and validate server_data.csv
def load_server_data(csv_file):
    df = pd.read_csv(csv_file)
    required_columns = ['timestamp', 'host', 'cpu_usage_percent', 'memory_usage_percent', 'disk_io_mb_s', 'network_io_mb_s', 'storage_used_gb']
    if not all(col in df.columns for col in required_columns):
        raise ValueError(f"CSV must contain columns: {required_columns}")
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    return df

## Compute metrics and trends for each host
def preprocess_data(df):
    summaries = {}
    for host in df['host'].unique():
        host_data = df[df['host'] == host].tail(DATA_WINDOW)
        ## Calculate CPU trend
        cpu_trend = np.polyfit(range(len(host_data)), host_data['cpu_usage_percent'], 1)[0] if len(host_data) > 1 else 0
        ## Flag issues based on thresholds
        errors = []
        if (host_data['cpu_usage_percent'] > CPU_THRESHOLD).any():
            errors.append(f"High CPU usage detected: {host_data['cpu_usage_percent'].max():.2f}%")
        if (host_data['memory_usage_percent'] > MEMORY_THRESHOLD).any():
            errors.append(f"High memory usage detected: {host_data['memory_usage_percent'].max():.2f}%")
        if (host_data['disk_io_mb_s'] > DISK_IO_THRESHOLD).any():
            errors.append(f"High disk I/O detected: {host_data['disk_io_mb_s'].max():.2f} MB/s")
        if (host_data['storage_used_gb'] / STORAGE_CAPACITY > 0.9).any():
            errors.append(f"High storage usage detected: {host_data['storage_used_gb'].max():.2f} GB")
        summaries[host] = {
            'avg_cpu_usage': host_data['cpu_usage_percent'].mean(),
            'max_cpu_usage': host_data['cpu_usage_percent'].max(),
            'cpu_trend': cpu_trend,
            'avg_memory_usage': host_data['memory_usage_percent'].mean(),
            'max_memory_usage': host_data['memory_usage_percent'].max(),
            'avg_disk_io': host_data['disk_io_mb_s'].mean(),
            'avg_network_io': host_data['network_io_mb_s'].mean(),
            'storage_used': host_data['storage_used_gb'].iloc[-1],
            'storage_capacity': STORAGE_CAPACITY,
            'error_count': len(errors),
            'recent_errors': errors if errors else ["No critical issues detected"]
        }
    return summaries

## Predict failure likelihood using Azure OpenAI
def predict_failure(config, summary, host):
    client = AzureOpenAI(
        azure_endpoint=config['AZURE_AI_FOUNDRY_ENDPOINT'],
        api_key=config['AZURE_AI_FOUNDRY_KEY'],
        api_version="2024-06-01"
    )
    prompt = f"""
    Analyze server metrics for {host}:
    - Avg CPU: {summary['avg_cpu_usage']:.2f}%
    - Max CPU: {summary['max_cpu_usage']:.2f}%
    - CPU Trend: {summary['cpu_trend']:.2f}%/min
    - Avg Memory: {summary['avg_memory_usage']:.2f}%
    - Max Memory: {summary['max_memory_usage']:.2f}%
    - Avg Disk I/O: {summary['avg_disk_io']:.2f} MB/s
    - Avg Network I/O: {summary['avg_network_io']:.2f} MB/s
    - Storage: {summary['storage_used']:.2f}/{summary['storage_capacity']} GB
    - Errors: {summary['recent_errors']}
    Predict failure likelihood (High/Medium/Low) with confidence (0-100%) and explanation.
    """
    response = client.chat.completions.create(
        model=config['AZURE_AI_FOUNDRY_MODEL'],
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content

## Save predictions to predictions.csv
def save_predictions(predictions):
    df = pd.DataFrame([
        {
            'host': host,
            'prediction': pred.split('Prediction: ')[1].split('\n')[0],
            'confidence': pred.split('Confidence: ')[1].split('\n')[0],
            'explanation': pred.split('Explanation: ')[1]
        } for host, pred in predictions.items()
    ])
    df.to_csv(OUTPUT_FILE, index=False)
    return df.to_dict('records')

## Main function to process server metrics and predict failures
def main():
    ## Check command-line argument for CSV file
    if len(sys.argv) != 2:
        print("Usage: python3 server_metrics_failure_predictor_azure_ai.py <csv_file>")
        sys.exit(1)
    csv_file = sys.argv[1]
    
    ## Load configuration and data
    config = load_config()
    df = load_server_data(csv_file)
    
    ## Preprocess data
    summaries = preprocess_data(df)
    print("Server Data Summaries:")
    print(json.dumps(summaries, indent=2))
    
    ## Predict failures
    predictions = {}
    for host, summary in summaries.items():
        print(f"Predicting failure for {host}...")
        pred = predict_failure(config, summary, host)
        print(f"Prediction Result for {host}:\n{pred}")
        predictions[host] = pred
    
    ## Save and print predictions
    results = save_predictions(predictions)
    print("\nPredictions saved to", OUTPUT_FILE)
    print("\nSummary of Predictions:")
    for result in results:
        print(f"Host: {result['host']}")
        print(f"Prediction: {result['prediction']}")
        print(f"Confidence: {result['confidence']}")
        print(f"Explanation: {result['explanation']}\n")

if __name__ == '__main__':
    main()
