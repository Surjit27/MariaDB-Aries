import os
import json
import time
from typing import Optional, Dict, Any, List
from dotenv import load_dotenv
import google.generativeai as genai
from ai.models import (
    AIRequest, AIResponse, SQLQueryResponse, DatabaseSchema, 
    QueryType, AIResponse
)

# Load environment variables
load_dotenv()

class EnhancedGeminiIntegration:
    """Enhanced Gemini AI integration with structured output using Pydantic models."""
    
    def __init__(self):
        """Initialize the Gemini integration."""
        self.api_key = os.getenv('GEMINI_API_KEY')
        self.model_name = os.getenv('AI_MODEL', 'gemini-pro')
        self.max_tokens = int(os.getenv('AI_MAX_TOKENS', '1000'))
        self.temperature = float(os.getenv('AI_TEMPERATURE', '0.7'))
        
        if not self.api_key:
            print("Warning: GEMINI_API_KEY not found in environment variables")
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
    
    def generate_sql_query(self, user_prompt: str, database_schema: Dict[str, Any], 
                          context: Optional[str] = None) -> AIResponse:
        """Generate SQL query from natural language prompt with structured output."""
        start_time = time.time()
        
        if not self.is_available():
            return AIResponse(
                success=False,
                error_message="AI integration not available - check API key",
                processing_time=time.time() - start_time
            )
        
        try:
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
            
            # Generate response from Gemini
            response = self.model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=self.temperature,
                    max_output_tokens=self.max_tokens,
                )
            )
            
            # Parse the response
            sql_response = self._parse_gemini_response(response.text)
            
            processing_time = time.time() - start_time
            
            return AIResponse(
                success=True,
                sql_response=sql_response,
                processing_time=processing_time
            )
            
        except Exception as e:
            processing_time = time.time() - start_time
            return AIResponse(
                success=False,
                error_message=f"Error generating SQL query: {str(e)}",
                processing_time=processing_time
            )
    
    def _create_structured_prompt(self, request: AIRequest) -> str:
        """Create a structured prompt for Gemini with database schema and context."""
        
        prompt = f"""
You are an expert SQL query generator. Your task is to convert natural language prompts into accurate SQL queries.

DATABASE SCHEMA:
Database: {request.database_schema.database_name}

Tables and Columns:
"""
        
        # Add table information
        for table in request.database_schema.tables:
            prompt += f"\nTable: {table['table_name']}\n"
            prompt += "Columns:\n"
            for column in table['columns']:
                col_info = f"  - {column['name']} ({column['type']})"
                if column.get('primary_key'):
                    col_info += " [PRIMARY KEY]"
                if column.get('nullable') == False:
                    col_info += " [NOT NULL]"
                if column.get('unique'):
                    col_info += " [UNIQUE]"
                prompt += col_info + "\n"
        
        # Add relationships
        if request.database_schema.relationships:
            prompt += "\nRelationships:\n"
            for rel in request.database_schema.relationships:
                prompt += f"  - {rel['from_table']}.{rel['from_column']} -> {rel['to_table']}.{rel['to_column']}\n"
        
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

RESPONSE FORMAT:
Return your response in the following JSON format:
{{
    "query": "SELECT * FROM table_name WHERE condition",
    "query_type": "SELECT",
    "explanation": "Brief explanation of what this query does",
    "tables_involved": ["table1", "table2"],
    "columns_involved": ["column1", "column2"],
    "complexity_level": "Simple|Medium|Complex",
    "estimated_execution_time": "< 1ms",
    "suggestions": ["suggestion1", "suggestion2"],
    "confidence_score": 0.95
}}

SQL QUERY:
"""
        
        return prompt
    
    def _parse_gemini_response(self, response_text: str) -> SQLQueryResponse:
        """Parse Gemini response and return structured SQL query response."""
        try:
            # Try to extract JSON from the response
            # Look for JSON between ```json and ``` or just raw JSON
            if "```json" in response_text:
                json_start = response_text.find("```json") + 7
                json_end = response_text.find("```", json_start)
                json_text = response_text[json_start:json_end].strip()
            elif "```" in response_text:
                json_start = response_text.find("```") + 3
                json_end = response_text.find("```", json_start)
                json_text = response_text[json_start:json_end].strip()
            else:
                # Try to find JSON object in the response
                json_start = response_text.find("{")
                json_end = response_text.rfind("}") + 1
                json_text = response_text[json_start:json_end]
            
            # Parse JSON
            response_data = json.loads(json_text)
            
            # Create SQLQueryResponse object
            return SQLQueryResponse(**response_data)
            
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            # Fallback: extract just the SQL query
            lines = response_text.split('\n')
            sql_query = ""
            for line in lines:
                line = line.strip()
                if line.upper().startswith(('SELECT', 'INSERT', 'UPDATE', 'DELETE', 'CREATE', 'DROP', 'ALTER')):
                    sql_query = line
                    break
            
            if not sql_query:
                sql_query = "SELECT 1"  # Fallback query
            
            return SQLQueryResponse(
                query=sql_query,
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
            return response.text.strip()
            
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
            suggestions = [line.strip() for line in response.text.split('\n') if line.strip()]
            return suggestions[:5]  # Limit to 5 suggestions
            
        except Exception as e:
            print(f"Error getting suggestions: {e}")
            return []
    
    def optimize_query(self, sql_query: str, database_schema: Dict[str, Any]) -> str:
        """Suggest optimizations for a SQL query."""
        if not self.is_available():
            return "AI integration not available"
        
        try:
            prompt = f"""
Analyze this SQL query and suggest optimizations:

{sql_query}

Database Schema: {json.dumps(database_schema, indent=2)}

Provide specific optimization suggestions including:
1. Index recommendations
2. Query structure improvements
3. Performance considerations
4. Best practices

Keep suggestions practical and actionable.
"""
            
            response = self.model.generate_content(prompt)
            return response.text.strip()
            
        except Exception as e:
            return f"Error optimizing query: {str(e)}"
