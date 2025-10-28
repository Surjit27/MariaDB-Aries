from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from enum import Enum

class QueryType(str, Enum):
    """Enum for different SQL query types."""
    SELECT = "SELECT"
    INSERT = "INSERT"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    CREATE_TABLE = "CREATE_TABLE"
    CREATE_INDEX = "CREATE_INDEX"
    DROP_TABLE = "DROP_TABLE"
    ALTER_TABLE = "ALTER_TABLE"
    JOIN = "JOIN"
    AGGREGATE = "AGGREGATE"
    SUBQUERY = "SUBQUERY"

class SQLQueryResponse(BaseModel):
    """Pydantic model for structured SQL query response from Gemini."""
    
    query: str = Field(
        description="The generated SQL query",
        example="SELECT * FROM users WHERE age > 18"
    )
    
    query_type: QueryType = Field(
        description="The type of SQL query generated",
        example=QueryType.SELECT
    )
    
    explanation: str = Field(
        description="Explanation of what the query does",
        example="This query selects all users who are older than 18 years"
    )
    
    tables_involved: List[str] = Field(
        description="List of tables involved in the query",
        example=["users", "orders"]
    )
    
    columns_involved: List[str] = Field(
        description="List of columns involved in the query",
        example=["id", "name", "age", "email"]
    )
    
    complexity_level: str = Field(
        description="Complexity level of the query (Simple, Medium, Complex)",
        example="Simple"
    )
    
    estimated_execution_time: str = Field(
        description="Estimated execution time",
        example="< 1ms"
    )
    
    suggestions: List[str] = Field(
        description="Suggestions for optimization or improvement",
        example=["Consider adding an index on the age column for better performance"]
    )
    
    confidence_score: float = Field(
        description="Confidence score for the generated query (0.0 to 1.0)",
        ge=0.0,
        le=1.0,
        example=0.95
    )

class DatabaseSchema(BaseModel):
    """Pydantic model for database schema information."""
    
    database_name: str = Field(description="Name of the database")
    
    tables: List[Dict[str, Any]] = Field(
        description="List of tables with their schemas",
        example=[
            {
                "table_name": "users",
                "columns": [
                    {"name": "id", "type": "INTEGER", "primary_key": True},
                    {"name": "name", "type": "TEXT", "nullable": False},
                    {"name": "email", "type": "TEXT", "unique": True}
                ]
            }
        ]
    )
    
    relationships: List[Dict[str, Any]] = Field(
        description="Foreign key relationships between tables",
        example=[
            {
                "from_table": "orders",
                "from_column": "user_id",
                "to_table": "users",
                "to_column": "id"
            }
        ]
    )

class AIRequest(BaseModel):
    """Pydantic model for AI request."""
    
    user_prompt: str = Field(
        description="User's natural language prompt",
        example="Show me all users who made orders in the last month"
    )
    
    database_schema: DatabaseSchema = Field(
        description="Current database schema information"
    )
    
    context: Optional[str] = Field(
        description="Additional context for the query",
        default=None
    )
    
    query_type_hint: Optional[QueryType] = Field(
        description="Hint about the expected query type",
        default=None
    )

class AIResponse(BaseModel):
    """Pydantic model for AI response."""
    
    success: bool = Field(description="Whether the AI request was successful")
    
    sql_response: Optional[SQLQueryResponse] = Field(
        description="Structured SQL query response",
        default=None
    )
    
    error_message: Optional[str] = Field(
        description="Error message if the request failed",
        default=None
    )
    
    processing_time: float = Field(
        description="Time taken to process the request in seconds",
        example=1.23
    )
