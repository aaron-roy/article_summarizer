# Upload the CSV file
curl -X POST -F "file=@/Users/aaronroy/Downloads/sample.csv" http://127.0.0.1:8000/process-csv/

# Check the status (replace YOUR_FILE_ID with the file_id from the previous response)
curl http://127.0.0.1:8000/status/YOUR_FILE_ID

# Download the processed file (when status is "completed")
curl -o processed_file.csv http://127.0.0.1:8000/download/YOUR_FILE_ID