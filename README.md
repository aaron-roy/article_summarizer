# Application Overview

This application processes CSV and Excel files to generate article summaries and tags using OpenAI's API. It also provides a chat interface for querying the processed data.

```
yourrepository/
├── backend/
│   ├── main.py
│   ├── util.py
│   ├── models.py
│   ├── __init__.py
│   └── ...
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── ArticleCarousel.jsx
│   │   │   ├── ChatAssistant.jsx
│   │   │   └── FileProcessor.jsx
│   │   ├── main.jsx
│   │   └── App.jsx
│   ├── public/
│   └── ...
├── requirements.txt
└── README.md
```

Explanation of Important Files
- backend/main.py: This is the main entry point for the backend server. It initializes the FastAPI application and defines the API endpoints for file processing, status checking, downloading processed files, retrieving articles, and invoking the chat agent.
- backend/util.py: Contains utility functions used by the backend, such as creating and closing database connections, processing files, summarizing articles using OpenAI's API, and clearing temporary directories.
- backend/models.py: Defines the data models using Pydantic for request and response validation. It includes models for articles, tags, and agent requests.
- frontend/src/components/ArticleCarousel.jsx: A React component that displays articles in a carousel format, allowing users to browse through the processed articles.
frontend/src/components/ChatAssistant.jsx: A React component that provides a chat interface for users to interact with the processed data. It sends user queries to the backend and displays the responses.
- frontend/src/components/FileProcessor.jsx: A React component that handles file uploads, status checking, and downloading of processed files. It also integrates the chat assistant and article carousel components.
frontend/src/main.jsx: The entry point for the React application, rendering the main App component.
- .env: A file for storing environment variables, such as API keys, which are loaded into the application using dotenv.
requirements.txt: Lists the Python dependencies required for the backend, which can be installed using pip.
- README.md: Provides an overview of the application, installation instructions, and usage guidelines.


## Installation

1. **Clone the repository:**
   ```bash
   git clone git@github.com:aaron-roy/article_summarizer.git
   cd article_summarizer
   ```

2. **Create a virtual environment for backend directory:**
   ```bash
   cd backend
   python -m venv venv
   ```

3. **Activate the virtual environment:**
   - On Windows:
     ```bash
     venv\Scripts\activate
     ```
   - On macOS and Linux:
     ```bash
     source venv/bin/activate
     ```

4. **Install the required dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

5. **Run the backend server:**
   The backend is powered by FastAPI. To start the server, use the following command:
   ```bash
   uvicorn backend.main:app --reload --port 8000
   ```

6. **Run the frontend:**
   Navigate to the `frontend` directory and start the React application:
   ```bash
   cd frontend
   npm install
   npm start
   ```

   If you are using Vite for the frontend, you can start the development server with:
   ```bash
   npm run dev
   ```

## Application Structure

The application is divided into two main parts:

- **Backend:** Contains all Python files and handles file processing, database operations, and API endpoints.
- **Frontend:** A React application that provides a user interface for uploading files, viewing summaries, and interacting with the chat assistant.

## Summarization Approach

The application uses OpenAI's API to generate concise summaries and relevant tags for each article in the uploaded file. The process involves:

1. **File Upload:** Users can upload CSV or Excel files containing articles.
2. **Data Processing:** The backend reads the file, processes each article to generate summaries and tags, and stores the results in a SQLite database.
3. **OpenAI API:** The `summarize_article` function calls the OpenAI API to generate summaries and tags for each article.

## Chat Interface

The chat interface allows users to query the processed data. Here's how it works:

1. **User Interaction:** Users can ask questions about the article summaries through the chat interface.
2. **Agent Invocation:** The backend uses LangChain and OpenAI to convert user queries into SQL commands.
3. **Database Query:** The SQL commands are executed against the SQLite database to retrieve relevant data.
4. **Response Generation:** The results are formatted and sent back to the user through the chat interface.

## API Endpoints

The backend provides several FastAPI routes:

- **POST /process-file/**: Upload and process a file.
- **GET /status/{file_id}**: Check the processing status of a file.
- **GET /download/{file_id}**: Download the processed file.
- **GET /articles/**: Retrieve all articles and their tags from the database.
- **POST /invoke-agent/**: Convert user queries into SQL and execute them against the database.

## Usage

1. **Upload a File:**
   Use the frontend interface to upload a CSV or Excel file.

2. **Check Processing Status:**
   Monitor the status of the file processing through the frontend.

3. **Download Processed File:**
   Once processing is complete, download the file with summaries and tags.

4. **Interact with Chat Assistant:**
   Use the chat interface to ask questions about the processed data.

## Example Commands

- **Upload a CSV file:**
  ```bash
  curl -X POST -F "file=@/path/to/yourfile.csv" http://127.0.0.1:8000/process-file/
  ```

- **Check the status of a file:**
  ```bash
  curl http://127.0.0.1:8000/status/YOUR_FILE_ID
  ```

- **Download the processed file:**
  ```bash
  curl -o processed_file.csv http://127.0.0.1:8000/download/YOUR_FILE_ID
  ```

This README provides a comprehensive overview of the application, its structure, and how to use it effectively. Feel free to customize it further to suit your needs.
