import time
import requests
import sys
# Replace with your actual file path and API URL
# csv_file_path = '/Users/aaronroy/Downloads/sample.csv'
csv_file_path = sys.argv[1]
api_base_url = 'http://127.0.0.1:8000'

# 1. Upload CSV file
def upload_csv():
    with open(csv_file_path, 'rb') as file:
        response = requests.post(f'{api_base_url}/process-file/', files={'file': file})
    if response.status_code == 200:
        return response.json()  # Return the response payload (which should include the file_id)
    else:
        print(f"Error uploading CSV: {response.text}")
        return None

# 2. Check status
def check_status(file_id):
    response = requests.get(f'{api_base_url}/status/{file_id}')
    if response.status_code == 200:
        return response.json()  # Return the status payload
    else:
        print(f"Error checking status: {response.text}")
        return None

# 3. Download the processed file
def download_processed_file(file_id):
    response = requests.get(f'{api_base_url}/download/{file_id}')
    if response.status_code == 200:
        with open('processed_file.csv', 'wb') as f:
            f.write(response.content)
        print("Processed file downloaded as 'processed_file.csv'")
    else:
        print(f"Error downloading processed file: {response.text}")

# Main script flow
def main():
    print("Uploading CSV file...")
    upload_response = upload_csv()
    if upload_response is None:
        print("Failed to upload CSV. Exiting.")
        return

    file_id = upload_response.get('file_id')
    if not file_id:
        print("No file_id returned. Exiting.")
        return

    print(f"File uploaded successfully with file_id: {file_id}")

    # Wait for the processing to complete
    print("Checking status...")
    while True:
        status_response = check_status(file_id)
        if status_response is None:
            print("Failed to check status. Exiting.")
            return

        status = status_response.get('status')
        print(f"Current status: {status}")

        if status == 'completed':
            print("Processing completed. Downloading the processed file...")
            download_processed_file(file_id)
            break
        else:
            print("Processing not complete. Retrying in 5 seconds...")
            time.sleep(5)

if __name__ == '__main__':
    main()
