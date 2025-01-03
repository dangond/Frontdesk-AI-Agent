import requests
import json

def send_task_to_endpoint(task_json, endpoint_url):
    """For sending task info to the admin portal."""
    try:
        headers = {
            "Content-Type": "application/json"
        }

        # Send the POST request
        response = requests.post(endpoint_url, headers=headers, data=json.dumps(task_json))

        # Log the response
        if response.status_code == 200 or response.status_code == 201:
            print("Task successfully sent to the endpoint.")
            print("Response:", response.json())
        else:
            print(f"Failed to send the task. Status Code: {response.status_code}")
            print("Response:", response.text)

        return response

    except Exception as e:
        print(f"An error occurred while sending the task: {e}")
        return None
