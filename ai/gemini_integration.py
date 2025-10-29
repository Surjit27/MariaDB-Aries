import os
import json
import time
from typing import Optional, Dict, Any, List
import google.generativeai as genai

# Add the project root to the Python path
import sys
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.append(project_root)

from ai.models import (
    AIRequest, AIResponse, SQLQueryResponse, DatabaseSchema, 
    QueryType, AIResponse
)

class GeminiIntegration:
    """Enhanced Gemini AI integration with structured output using Pydantic models."""
    
    def __init__(self):
        """Initialize the Gemini integration."""
        self.api_key = os.getenv('GEMINI_API_KEY')
        self.model_name = os.getenv('AI_MODEL', 'gemini-2.5-flash')
        self.max_tokens = int(os.getenv('AI_MAX_TOKENS', '4000'))
        self.temperature = float(os.getenv('AI_TEMPERATURE', '0.7'))
        
        if not self.api_key:
            print("Warning: GEMINI_API_KEY not found in environment variables. AI features will be disabled.")
            self.model = None
            return
        
        try:
            # Configure Gemini
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel(self.model_name)
            print(f"✅ Gemini AI initialized successfully with model: {self.model_name}")
        except Exception as e:
            print(f"❌ Error initializing Gemini AI: {e}")
            self.model = None
    
    def is_available(self) -> bool:
        """Check if AI integration is available."""
        return self.model is not None
    
    def _get_response_text(self, response) -> str:
        """Extract text from Gemini response, handling both simple and complex responses."""
        print(f"🔍 Response object type: {type(response)}")
        print(f"🔍 Response attributes: {dir(response)}")
        
        try:
            # Try the simple text accessor first
            text = response.text
            print(f"🔍 Simple text accessor worked: {repr(text)}")
            return text
        except ValueError as e:
            print(f"🔍 Simple text accessor failed: {e}")
            # If that fails, use the parts accessor
            try:
                if hasattr(response, 'parts') and response.parts:
                    print(f"🔍 Using parts accessor, {len(response.parts)} parts")
                    text = ''.join(part.text for part in response.parts if hasattr(part, 'text'))
                    print(f"🔍 Parts text: {repr(text)}")
                    return text
                elif hasattr(response, 'candidates') and response.candidates:
                    print(f"🔍 Using candidates accessor, {len(response.candidates)} candidates")
                    candidate = response.candidates[0]
                    if hasattr(candidate, 'content') and hasattr(candidate.content, 'parts'):
                        print(f"🔍 Candidate content parts: {len(candidate.content.parts)}")
                        text = ''.join(part.text for part in candidate.content.parts if hasattr(part, 'text'))
                        print(f"🔍 Candidate text: {repr(text)}")
                        return text
                print(f"🔍 Fallback to str(response): {str(response)}")
                return str(response)
            except Exception as e:
                print(f"Error extracting response text: {e}")
                return "Error: Could not extract response text"
    
    def generate_sql_query(self, user_prompt: str, database_schema: Dict[str, Any] = None, 
                          context: Optional[str] = None) -> Optional[str]:
        """Generate SQL query from natural language prompt."""
        if not self.is_available():
            print("AI integration not available - check API key")
            return None
        
        try:
            # If no schema provided, create a basic one
            if not database_schema:
                database_schema = {
                    "database_name": "current_database",
                    "tables": [],
                    "relationships": []
                }
            
            # Create database schema object
            db_schema = DatabaseSchema(**database_schema)
            
            # Create AI request
            ai_request = AIRequest(
                user_prompt=user_prompt,
                database_schema=db_schema,
                context=context
            )
            
            # Generate the prompt for Gemini
            prompt = self._create_structured_prompt(ai_request)
            
            # Generate response from Gemini with better configuration
            response = self.model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=self.temperature,
                    max_output_tokens=self.max_tokens,
                    candidate_count=1,
                    stop_sequences=None,  # Don't stop early
                )
            )
            
            # Parse the response and return just the SQL query
            response_text = self._get_response_text(response)
            print(f"🔍 Raw AI Response: {repr(response_text)}")
            print(f"🔍 Response Length: {len(response_text)}")
            print(f"🔍 Response Lines: {response_text.count(chr(10)) + 1}")
            
            sql_response = self._parse_gemini_response(response_text)
            print(f"🔍 Parsed SQL Query: {repr(sql_response.query)}")
            print(f"🔍 Parsed Query Length: {len(sql_response.query)}")
            
            return sql_response.query
            
        except Exception as e:
            print(f"Error generating SQL query: {str(e)}")
            return None

    def _create_structured_prompt(self, request: AIRequest) -> str:
        """Create a structured prompt for Gemini with database schema and context."""
        
        # Handle both Pydantic model and dictionary schema
        if hasattr(request.database_schema, 'database_name'):
            # Pydantic model
            db_name = request.database_schema.database_name
            tables = request.database_schema.tables
            relationships = request.database_schema.relationships
        else:
            # Dictionary schema
            db_name = request.database_schema.get('database_name', 'Unknown')
            tables = request.database_schema.get('tables', [])
            relationships = request.database_schema.get('relationships', [])
        
        prompt = f"""
You are an expert SQL query generator. Your task is to convert natural language prompts into accurate SQL queries.

DATABASE SCHEMA:
Database: {db_name}

Tables and Columns:
"""
        
        # Add table information
        for table in tables:
            if isinstance(table, dict):
                table_name = table.get('table_name', 'unknown')
                columns = table.get('columns', [])
            else:
                # Handle case where table is just a string name
                table_name = str(table)
                columns = []
            
            prompt += f"\nTable: {table_name}\n"
            if columns:
                prompt += "Columns:\n"
                for column in columns:
                    if isinstance(column, dict):
                        col_info = f"  - {column.get('name', 'unknown')} ({column.get('type', 'TEXT')})"
                        if column.get('primary_key'):
                            col_info += " [PRIMARY KEY]"
                        if column.get('nullable') == False:
                            col_info += " [NOT NULL]"
                        if column.get('unique'):
                            col_info += " [UNIQUE]"
                        prompt += col_info + "\n"
            else:
                prompt += "  (No column information available)\n"
        
        # Add relationships
        if relationships:
            prompt += "\nRelationships:\n"
            for rel in relationships:
                if isinstance(rel, dict):
                    prompt += f"  - {rel.get('from_table', 'unknown')}.{rel.get('from_column', 'unknown')} -> {rel.get('to_table', 'unknown')}.{rel.get('to_column', 'unknown')}\n"
        
        # Add context if provided
        if request.context:
            prompt += f"\nAdditional Context:\n{request.context}\n"
        
        # Add the user prompt
        prompt += f"""
USER REQUEST: {request.user_prompt}

INSTRUCTIONS:
1. Generate a valid SQL query that fulfills the user's request
2. Use proper SQL syntax compatible with SQLite
3. Include appropriate JOINs if multiple tables are needed
4. Use proper WHERE clauses for filtering
5. Consider performance and use appropriate indexes
6. Return ONLY the SQL query, no explanations

SQL QUERY:
"""
        
        return prompt
    
    def _parse_gemini_response(self, response_text: str) -> SQLQueryResponse:
        """Parse Gemini response and return structured SQL query response."""
        print(f"🔍 Parsing response text: {repr(response_text)}")
        
        try:
            # Try to extract JSON from the response
            if "```json" in response_text:
                print("🔍 Found ```json markers")
                json_start = response_text.find("```json") + 7
                json_end = response_text.find("```", json_start)
                json_text = response_text[json_start:json_end].strip()
                print(f"🔍 Extracted JSON: {repr(json_text)}")
            elif "```" in response_text:
                print("🔍 Found ``` markers")
                json_start = response_text.find("```") + 3
                json_end = response_text.find("```", json_start)
                json_text = response_text[json_start:json_end].strip()
                print(f"🔍 Extracted JSON: {repr(json_text)}")
            else:
                print("🔍 No code blocks found, looking for JSON object")
                # Try to find JSON object in the response
                json_start = response_text.find("{")
                json_end = response_text.rfind("}") + 1
                json_text = response_text[json_start:json_end]
                print(f"🔍 Extracted JSON: {repr(json_text)}")
            
            # Parse JSON
            response_data = json.loads(json_text)
            print(f"🔍 Parsed JSON data: {response_data}")
            
            # Create SQLQueryResponse object
            return SQLQueryResponse(**response_data)
            
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            print(f"🔍 JSON parsing failed: {e}")
            print("🔍 Using fallback: extract just the SQL query")
            
            # Fallback: extract just the SQL query
            lines = response_text.split('\n')
            print(f"🔍 Response has {len(lines)} lines")
            
            sql_query = ""
            in_sql = False
            for i, line in enumerate(lines):
                line = line.strip()
                print(f"🔍 Line {i}: {repr(line)}")
                
                # Check if this line starts a SQL statement
                if line.upper().startswith(('SELECT', 'INSERT', 'UPDATE', 'DELETE', 'CREATE', 'DROP', 'ALTER')):
                    in_sql = True
                    sql_query = line
                    print(f"🔍 Found SQL start: {line}")
                elif in_sql and line:  # Continue collecting SQL lines
                    sql_query += " " + line
                    print(f"🔍 Adding to SQL: {line}")
                elif in_sql and not line:  # Empty line, continue
                    sql_query += "\n"
                elif in_sql and not line.upper().startswith(('SELECT', 'INSERT', 'UPDATE', 'DELETE', 'CREATE', 'DROP', 'ALTER')):
                    # End of SQL statement
                    break
            
            print(f"🔍 Final SQL query: {repr(sql_query.strip())}")
            
            if not sql_query.strip():
                sql_query = "SELECT 1"  # Fallback query
                print("🔍 Using fallback query")
            
            return SQLQueryResponse(
                query=sql_query.strip(),
                query_type=QueryType.SELECT,
                explanation="Generated SQL query from natural language prompt",
                tables_involved=[],
                columns_involved=[],
                complexity_level="Simple",
                estimated_execution_time="< 1ms",
                suggestions=["Review the generated query for accuracy"],
                confidence_score=0.5
            )
    
    def explain_sql(self, sql_query: str) -> str:
        """Explain what a SQL query does."""
        if not self.is_available():
            return "AI integration not available"
        
        try:
            prompt = f"""
Explain what this SQL query does in simple terms:

{sql_query}

Provide a clear, concise explanation of:
1. What tables are involved
2. What data is being retrieved/modified
3. Any conditions or filters applied
4. The expected result

Keep the explanation under 200 words.
"""
            
            response = self.model.generate_content(prompt)
            return self._get_response_text(response).strip()
            
        except Exception as e:
            return f"Error explaining SQL query: {str(e)}"
    
    def get_suggestions(self, partial_query: str) -> List[str]:
        """Get autocomplete suggestions for a partial SQL query."""
        if not self.is_available():
            return []
        
        try:
            prompt = f"""
Complete this partial SQL query with appropriate suggestions:

{partial_query}

Provide 3-5 completion suggestions. Return only the SQL keywords or phrases, one per line.
"""
            
            response = self.model.generate_content(prompt)
            response_text = self._get_response_text(response)
            suggestions = [line.strip() for line in response_text.split('\n') if line.strip()]
            return suggestions[:5]  # Limit to 5 suggestions
            
        except Exception as e:
            print(f"Error getting suggestions: {e}")
            return []