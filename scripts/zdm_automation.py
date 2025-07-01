import subprocess
import json
import time

def check_zdm_job(job_id, zdm_cli_path="/u01/app/zdm/bin/zdmcli"):
    """
    Check the status of a ZDM job and return the output.
    Args:
        job_id (str): The ID of the ZDM job to query.
        zdm_cli_path (str): Path to the ZDM CLI executable.
    Returns:
        dict: Parsed job status information.
    """
    try:
        result = subprocess.run(
            [zdm_cli_path, "query", "job", "-jobid", job_id],
            capture_output=True,
            text=True,
            check=True
        )
        # Parse output (assuming JSON-like format for simplicity)
        output = result.stdout
        return {"job_id": job_id, "status": output}
    except subprocess.CalledProcessError as e:
        return {"job_id": job_id, "error": str(e), "output": e.output}

def monitor_zdm_jobs(job_ids, interval=60, max_attempts=10):
    """
    Monitor multiple ZDM jobs at regular intervals.
    Args:
        job_ids (list): List of ZDM job IDs to monitor.
        interval (int): Time interval between checks (seconds).
        max_attempts (int): Maximum number of attempts to check status.
    """
    for attempt in range(max_attempts):
        for job_id in job_ids:
            status = check_zdm_job(job_id)
            print(f"Attempt {attempt + 1}: Job {job_id} status: {status}")
            if "error" in status:
                print(f"Error for Job {job_id}: {status['error']}")
        time.sleep(interval)

if __name__ == "__main__":
    # Example usage: Monitor ZDM jobs
    job_ids = ["12345", "67890"]  # Replace with actual job IDs
    monitor_zdm_jobs(job_ids)

