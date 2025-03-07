import os
from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse

import uuid
import openai
from typing import List
import logging
from dotenv import load_dotenv
import sqlite3

from contextlib import asynccontextmanager
from models import Article, AgentRequest
from fastapi.middleware.cors import CORSMiddleware
from util import process_file, clear_temp_dir, create_agent, create_db
from typing import List

# Load environment variables from .env file
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Application started")
    logger.info(f"OpenAI API key {'is set' if openai.api_key else 'is NOT set'}")
    
    # Create database with tables and store connection in app state
    app.state.db_connection = create_db()
    # Create agent
    app.state.agent_executor = create_agent(app.state.db_connection)
    
    yield
    
    # Shutdown - directly close the connection
    if app.state.db_connection:
        app.state.db_connection.close()
        
    # Remove the database file
    if os.path.exists("mydatabase.db"):
        os.remove("mydatabase.db")
        logger.info("Database removed")

# Initialize FastAPI app
app = FastAPI(title="Article Processing API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create temp directory for file storage if it doesn't exist
os.makedirs("temp", exist_ok=True)


@app.post("/process-file/")
async def upload_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...)
):
    """
    Endpoint to upload and process a CSV file.
    
    Args:
        file: The CSV file to process
        
    Returns:
        dict: A message indicating the processing has started
    """
    # Check for valid file extensions
    if not (file.filename.endswith('.csv') or file.filename.endswith('.xls') or file.filename.endswith('.xlsx')):
        raise HTTPException(status_code=400, detail="Only CSV, XLS, and XLSX files are accepted")
    
    # Clear temp directory before saving new file
    clear_temp_dir()
    
    # Generate a unique file ID and temporary file path
    file_id = str(uuid.uuid4())
    temp_file_path = f"temp/{file_id}_{file.filename}"
    
    # Save the uploaded file to the temporary directory
    with open(temp_file_path, "wb") as buffer:
        buffer.write(await file.read())
    
    try:
        # Process the file asynchronously 
        background_tasks.add_task(process_file, temp_file_path, app.state.db_connection)  
        
        
        return {
            "message": "File processing started",
            "file_id": file_id,
            "filename": file.filename,
            "status_endpoint": f"/status/{file_id}"
        }
    
    except HTTPException as e:
        # Handle the HTTPException raised in process_file, returning the error back to the user
        raise e
    except Exception as e:
        # Generic error handling in case of unexpected issues
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")

@app.get("/status/{file_id}")
async def check_status(file_id: str):
    """
    Check the status of a processing task.
    
    Args:
        file_id: The ID of the processing task
        
    Returns:
        dict: The status of the processing task
    """

    temp_dir = f"temp"
    # Check if original file exists
    original_files = [f for f in os.listdir(temp_dir) if f.startswith(file_id)]
    logger.info(temp_dir)

    logger.info(original_files[0])
    if not original_files:
        raise HTTPException(status_code=404, detail="File not found")
    
    original_filename = original_files[0]
    
    # Check if processed file exists
    processed_path = f"{temp_dir}/processed_{original_filename}"
    logger.info(processed_path)

    if os.path.exists(processed_path):
        return {
            "status": "completed",
            "file_id": file_id,
            "download_url": f"/download/{file_id}",
            "":""
        }
    else:
        return {
            "status": "processing",
            "file_id": file_id
        }


@app.get("/download/{file_id}")
async def download_file(file_id: str):
    """
    Download the processed file in the correct format (CSV or Excel) based on the original file extension.
    
    Args:
        file_id: The ID of the processing task
        
    Returns:
        FileResponse: processed file in the appropriate format
    """
    temp_dir = "temp"
    
    # Find the original file based on the file_id
    original_filenames = [f for f in os.listdir(temp_dir) if f.startswith(file_id)]
    if not original_filenames:
        raise HTTPException(status_code=404, detail="Original file not found.")
    
    original_filename = original_filenames[0]
    
    # Determine the processed file path
    processed_path = f"{temp_dir}/processed_{original_filename}"
    
    if not os.path.exists(processed_path):
        raise HTTPException(status_code=404, detail="Processed file not found. It may still be processing.")
    
    # Get the original file's extension to determine the download format
    file_extension = original_filename.split('.')[-1].lower()
    logger.info("File extendo: " + file_extension)
    # Set the download format and MIME type based on the original file extension
    if file_extension in ['xls', 'xlsx']:  # If the original file is an Excel file
        output_filename = f"processed_{original_filename.replace('.xls', '').replace('.xlsx', '')}.xlsx"
        media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    else:  # If the original file is a CSV file or any other format
        output_filename = f"processed_{original_filename.replace('.csv', '')}.csv"
        media_type = "text/csv"
    
    # Return the processed file with the appropriate format and MIME type
    return FileResponse(
        path=processed_path,
        filename=output_filename,
        media_type=media_type
    )


@app.post("/invoke-agent/")
async def invoke_agent(request: AgentRequest):
    """
    Invoke the SQL agent with a user query.
    
    Args:
        request: The request body containing the query to be processed by the SQL agent
        
    Returns:
        dict: The response from the agent
    """
    response = app.state.agent_executor.invoke({"input": request.input_query})
    return {"response": response}

@app.get("/articles/", response_model=List[Article])
async def get_articles():
    """
    Get all articles with their associated tags.
    
    Returns:
        List[Article]: A list of all articles with their tags
    """
    conn = app.state.db_connection
    cursor = conn.cursor()
    # Get all articles
    cursor.execute("""
        SELECT id, article_summary, author_name, likes, shares, views
        FROM articles
    """)
    articles_data = cursor.fetchall()
    
    articles = []
    for article in articles_data:
        article_id, summary, author, likes, shares, views = article
        
        # Get tags for this article
        cursor.execute("""
            SELECT t.id, t.tag_name
            FROM tags t
            JOIN article_tags at ON t.id = at.tag_id
            WHERE at.article_id = ?
        """, (article_id,))
        tags_data = cursor.fetchall()
        
        # Format tags
        tags = [{"id": tag[0], "tag_name": tag[1]} for tag in tags_data]
        
        # Create article dict with tags
        article_dict = {
            "id": article_id,
            "article_summary": summary,
            "author_name": author,
            "likes": likes,
            "shares": shares,
            "views": views,
            "tags": tags
        }
        
        articles.append(article_dict)
    
    return articles

@app.get("/test")
async def test_endpoint():
    return {"message": "API is working!"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
