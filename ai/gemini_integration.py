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
            
            # Check if parsing failed (returns None) or invalid SQL detected
            if sql_response is None:
                print("🔍 SQL parsing failed or invalid SQL detected (e.g., DISTINCT aggregates)")
                return None
            
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
            
            # First, try to extract SQL from SQL_QUERY: marker
            sql_query_marker = "SQL_QUERY:"
            if sql_query_marker in response_text.upper():
                # Find the actual marker with correct case
                for marker_variant in ["SQL_QUERY:", "SQL_QUERY", "sql_query:", "sql_query"]:
                    if marker_variant in response_text:
                        marker_pos = response_text.find(marker_variant)
                        sql_start = marker_pos + len(marker_variant)
                        print(f"🔍 Found marker '{marker_variant}' at position {marker_pos}, SQL starts at {sql_start}")
                        # Extract everything after the marker until EXPLANATION: or end
                        remaining = response_text[sql_start:]
                        print(f"🔍 Remaining text after marker: {repr(remaining[:100])}")
                        exp_marker = remaining.upper().find("EXPLANATION:")
                        if exp_marker != -1:
                            sql_query = remaining[:exp_marker].strip()
                            print(f"🔍 Found EXPLANATION at position {exp_marker}, extracted SQL: {repr(sql_query[:100])}")
                        else:
                            sql_query = remaining.strip()
                            print(f"🔍 No EXPLANATION marker, extracted all remaining: {repr(sql_query[:100])}")
                        # Clean up any leading/trailing punctuation (but keep the SQL)
                        sql_query = sql_query.strip(':\n\r\t ')
                        # Remove any leading/trailing quotes if present
                        if sql_query.startswith('"') and sql_query.endswith('"'):
                            sql_query = sql_query[1:-1]
                        if sql_query.startswith("'") and sql_query.endswith("'"):
                            sql_query = sql_query[1:-1]
                        print(f"🔍 Final extracted from SQL_QUERY marker: {repr(sql_query[:100])}")
                        if sql_query.strip():
                            break  # Successfully extracted, break from marker loop
            
            # If not found via marker, look for SQL keywords directly
            if not sql_query.strip():
                in_sql = False
                for i, line in enumerate(lines):
                    line = line.strip()
                    print(f"🔍 Line {i}: {repr(line)}")
                    
                    # Check if this line starts a SQL statement (after removing any prefix)
                    line_for_check = line
                    # Remove common prefixes
                    for prefix in ["SQL_QUERY:", "SQL_QUERY", "sql_query:", "sql_query", "QUERY:", "query:"]:
                        if line_for_check.upper().startswith(prefix):
                            line_for_check = line_for_check[len(prefix):].strip()
                            print(f"🔍 Removed prefix '{prefix}', checking: {repr(line_for_check[:50])}")
                            break
                    
                    # Check for SQL keywords (including CREATE TRIGGER, CREATE FUNCTION, etc.)
                    sql_keywords = ('SELECT', 'INSERT', 'UPDATE', 'DELETE', 'CREATE', 'DROP', 'ALTER', 
                                   'WITH', 'TRUNCATE', 'REPLACE', 'MERGE')
                    if line_for_check.upper().startswith(sql_keywords):
                        in_sql = True
                        sql_query = line_for_check  # Use cleaned line
                        print(f"🔍 Found SQL start: {repr(line_for_check[:100])}")
                    elif in_sql and line:  # Continue collecting SQL lines
                        sql_query += " " + line
                        print(f"🔍 Adding to SQL: {repr(line[:50])}")
                    elif in_sql and not line:  # Empty line, continue
                        sql_query += "\n"
                    elif in_sql and line.upper().startswith(('EXPLANATION', 'NOTE', 'NOTE:', 'COMMENT')):
                        # End of SQL statement if we hit explanation
                        break
            
            # Clean up SQL query (remove markdown code fences)
            sql_query = sql_query.replace("```sql", "").replace("```", "").strip()
            
            print(f"🔍 Final SQL query: {repr(sql_query.strip())}")
            
            # Only use fallback if we truly got nothing from the AI
            # If response_text exists but parsing failed, it's a parsing issue, not AI failure
            if not sql_query.strip():
                if response_text and len(response_text.strip()) > 10:
                    # We got a response but couldn't parse it - return None to indicate parsing error
                    print("🔍 Warning: Got AI response but couldn't parse SQL from it")
                    print(f"🔍 Response was: {response_text[:200]}...")
                    # Try one more time with a more lenient approach
                    # Look for any line that starts with SELECT, INSERT, etc.
                    lines = response_text.split('\n')
                    for line in lines:
                        line_upper = line.strip().upper()
                        if line_upper.startswith(('SELECT', 'INSERT', 'UPDATE', 'DELETE', 'CREATE', 'DROP', 'ALTER', 'WITH')):
                            sql_query = line.strip()
                            print(f"🔍 Found SQL via fallback search: {sql_query[:50]}...")
                            break
                    
                    if not sql_query.strip():
                        # Still nothing - return None so the caller can handle it properly
                        return None
                else:
                    # No response from AI at all - use fallback
                    sql_query = "SELECT 1"  # Fallback query
                    print("🔍 Using fallback query (no AI response)")
            
            # Validate for common SQLite errors before returning
            if sql_query and sql_query.strip():
                sql_upper = sql_query.upper()
                # Check for invalid DISTINCT aggregates (multiple arguments)
                import re
                distinct_aggregate_pattern = r'\b(COUNT|SUM|AVG|MAX|MIN)\s*\(\s*DISTINCT\s+[^,)]+,\s+[^)]+\)'
                if re.search(distinct_aggregate_pattern, sql_query, re.IGNORECASE):
                    print(f"🔍 Warning: Detected invalid DISTINCT aggregate in SQL")
                    print(f"🔍 SQL: {sql_query[:200]}...")
                    # Return None so caller can request a fix
                    return None
            
            # Determine query type from the SQL
            query_type = QueryType.SELECT
            sql_upper = sql_query.strip().upper()
            if sql_upper.startswith('INSERT'):
                query_type = QueryType.INSERT
            elif sql_upper.startswith('UPDATE'):
                query_type = QueryType.UPDATE
            elif sql_upper.startswith('DELETE'):
                query_type = QueryType.DELETE
            elif sql_upper.startswith('CREATE'):
                query_type = QueryType.SELECT  # CREATE statements (triggers, functions, etc.)
            elif sql_upper.startswith('DROP'):
                query_type = QueryType.DELETE
            elif sql_upper.startswith('ALTER'):
                query_type = QueryType.UPDATE
            
            return SQLQueryResponse(
                query=sql_query.strip(),
                query_type=query_type,
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