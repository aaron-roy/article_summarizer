from typing import List
from pydantic import BaseModel

class Tag(BaseModel):
    id: int
    tag_name: str

class Article(BaseModel):
    id: int
    article_summary: str
    author_name: str
    likes: int
    shares: int
    views: int
    tags: List[Tag] = []

# Define a Pydantic model for the request body
class AgentRequest(BaseModel):
    input_query: str