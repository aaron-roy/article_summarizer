import os
import pandas as pd
from fastapi import HTTPException, status
import openai
from typing import List
import logging
from dotenv import load_dotenv
import sqlite3
from langchain.chat_models import init_chat_model
from langchain_community.agent_toolkits import create_sql_agent
from langchain_community.utilities import SQLDatabase

import sqlite3




# Load environment variables from .env file
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configure OpenAI API key
openai.api_key = os.environ.get("OPENAI_API_KEY")
if not openai.api_key:
    logger.warning("OPENAI_API_KEY environment variable not set. You'll need to set it before making API calls.")



# Create a connection to the SQLite database
def create_db():
    # First ensure any existing connection is closed
    """Create database and tables."""
    # Cleanup code is still helpful for robustness
    if os.path.exists("mydatabase.db"):
        os.remove("mydatabase.db")
    
    conn = sqlite3.connect("mydatabase.db")
    cursor = conn.cursor()
    
    # Create tables
    cursor.execute('''
    CREATE TABLE articles (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        article_summary TEXT,
        author_name VARCHAR(255),
        likes BIGINT,
        shares BIGINT,
        views BIGINT
    );
    ''')
    
    cursor.execute('''
    CREATE TABLE tags (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tag_name VARCHAR(255) UNIQUE
    );
    ''')
    
    cursor.execute('''
    CREATE TABLE article_tags (
        article_id INTEGER,
        tag_id INTEGER,
        PRIMARY KEY (article_id, tag_id),
        FOREIGN KEY (article_id) REFERENCES articles(id) ON DELETE CASCADE,
        FOREIGN KEY (tag_id) REFERENCES tags(id) ON DELETE CASCADE
    );
    ''')
    
    conn.commit()
    return conn


def create_agent(db_connection):
    """Create and initialize the LangChain SQL agent with the given database connection."""
    # Create SQLDatabase instance for LangChain
    db = SQLDatabase.from_uri("sqlite:///mydatabase.db")
    
    # Initialize the chat model
    llm = init_chat_model("gpt-4o-mini", model_provider="openai")
    
    # Create SQL agent with SQLDatabase instance
    agent = create_sql_agent(llm, db=db, agent_type="openai-tools", verbose=True)
    
    return agent


async def summarize_article(content: str) -> tuple[str, List[str]]:
    """
    Generate a summary and tags for an article using OpenAI API.
    
    Args:
        content: The article content to summarize
        
    Returns:
        tuple: (summary, tags)
    """
    try:
        # Call OpenAI API to generate summary
        summary_response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that generates concise summaries of articles."},
                {"role": "user", "content": f"Please summarize the following article in 2-3 sentences:\n\n{content}"}
            ],
            temperature=0.7,
            max_tokens=100
        )
        
        # Call OpenAI API to generate tags
        tags_response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that generates relevant tags for articles."},
                {"role": "user", "content": f"Please generate 3-5 relevant tags for the following article. Return only the tags as a comma-separated list:\n\n{content}"}
            ],
            temperature=0.7,
            max_tokens=50
        )
        
        summary = summary_response.choices[0].message.content.strip()
        tags = tags_response.choices[0].message.content.strip().split(',')
        tags = [tag.strip() for tag in tags]
        
        return summary, tags
    
    except Exception as e:
        logger.error(f"Error calling OpenAI API: {str(e)}")
        return "Failed to generate summary.", ["error"]

async def process_file(file_path: str, db_connection) -> str:
    """
    Process each article in the file (CSV or Excel) and add summary and tags columns.
    
    Args:
        file_path: Path to the file (CSV or Excel)
        
    Returns:
        str: Path to the processed file
        
    Raises:
        HTTPException: If the file does not have the required columns.
    """
    try:
        # Clear existing data in the tables
        cursor = db_connection.cursor()
        cursor.execute("DELETE FROM articles")
        cursor.execute("DELETE FROM tags")
        cursor.execute("DELETE FROM article_tags")
        # Reset the auto-increment counter for 'articles' table
        cursor.execute("DELETE FROM sqlite_sequence WHERE name='articles'")
        db_connection.commit()
        
        # Read the file (CSV or Excel)
        logger.info(""+os.path.splitext(os.path.basename(file_path))[1])
        file_name = os.path.splitext(os.path.basename(file_path))[0]
        file_extension = os.path.splitext(file_path)[1].lower()
        
        if file_extension == '.csv':
            df = pd.read_csv(file_path)
        elif file_extension in ['.xls', '.xlsx']:
            # Use openpyxl for reading .xlsx and xlrd for .xls
            if file_extension == '.xls':
                df = pd.read_excel(file_path, engine='xlrd')
            else:
                df = pd.read_excel(file_path, engine='openpyxl')
        else:
            raise ValueError("Unsupported file format. Please upload a CSV or Excel file.")
        
        # Check if required columns exist
        required_columns = ['Article Content', 'Author Name', 'Likes', 'Shares', 'Views']
        missing_columns = [col for col in required_columns if col not in df.columns]

        if missing_columns:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File is missing required columns: {', '.join(missing_columns)}"
            )
        
        # Initialize new columns for summary and tags
        df['Summary'] = ""
        df['Tags'] = ""
        
        # Process each article
        for idx, row in df.iterrows():
            logger.info(f"Processing article {idx+1}/{len(df)}")
            
            article_content = row['Article Content']
            author_name = row['Author Name']
            likes = row['Likes']
            shares = row['Shares']
            views = row['Views']
            
            summary, tags = await summarize_article(article_content)

            # Update the DataFrame with the summary and tags
            df.at[idx, 'Summary'] = summary
            df.at[idx, 'Tags'] = ', '.join(tags)
            # Insert article details into the articles table
            cursor.execute('''
            INSERT INTO articles (article_summary, author_name, likes, shares, views)
            VALUES (?, ?, ?, ?, ?)
            ''', (summary, author_name, likes, shares, views))
            
            article_id = cursor.lastrowid
            
            # Insert tags into the tags table and create relationships
            for tag in tags:
                cursor.execute('''
                INSERT OR IGNORE INTO tags (tag_name) VALUES (?)
                ''', (tag,))
                cursor.execute('''
                INSERT INTO article_tags (article_id, tag_id)
                VALUES (?, (SELECT id FROM tags WHERE tag_name = ?))
                ''', (article_id, tag))
            
            
        
        db_connection.commit()

        ##############
        # The following code is for only creating a processed file of the original file extension
        ##############
        # Save the processed file (same extension as the input file)
        output_path = f"temp/processed_{os.path.basename(file_path)}"
        if file_extension == '.csv':
            df.to_csv(output_path, index=False)
        elif file_extension in ['.xls', '.xlsx']:
            df.to_excel(output_path, index=False, engine='openpyxl')
        return output_path


        ##############
        # The following code is commented out but is for creating a processed file of both Excel and CSV
        ##############
        # Save the processed files (both CSV and Excel)
        # output_csv_path = f"temp/processed_{file_name}.csv"
        # output_excel_path = f"temp/processed_{file_name}.xlsx"

        # df.to_csv(output_csv_path, index=False)
        # df.to_excel(output_excel_path, index=False, engine='openpyxl')

        # return output_csv_path


    except Exception as e:
        logger.error(f"Error processing file: {e}")
        raise HTTPException(status_code=500, detail="An error occurred while processing the file.")
    
def clear_temp_dir():
    temp_dir = "temp"
    # Check if the temp directory exists
    if os.path.exists(temp_dir):
        # Remove all CSV files in the temp directory
        for filename in os.listdir(temp_dir):
            file_path = os.path.join(temp_dir, filename)
            if os.path.isfile(file_path):
                os.remove(file_path)