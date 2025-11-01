"""
Dedicated SQL Query Explainer
Provides detailed explanations of SQL queries using AI
"""

import os
from typing import Optional
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

class QueryExplainer:
    """Dedicated service for explaining SQL queries with detailed analysis."""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize the query explainer."""
        self.api_key = api_key or os.getenv('GEMINI_API_KEY', '')
        # Use the same model as other integrations for consistency
        self.model_name = os.getenv('AI_MODEL', 'gemini-2.5-flash')
        self.is_available = False
        
        if GEMINI_AVAILABLE and self.api_key:
            try:
                genai.configure(api_key=self.api_key)
                self.model = genai.GenerativeModel(self.model_name)
                self.is_available = True
            except Exception as e:
                print(f"Query Explainer initialization error: {e}")
                self.is_available = False
    
    def is_api_available(self) -> bool:
        """Check if the explainer is available."""
        return self.is_available
    
    def explain_query(self, sql_query: str, database_schema: Optional[dict] = None) -> str:
        """
        Explain a SQL query in detail using a specialized prompt.
        
        Args:
            sql_query: The SQL query to explain
            database_schema: Optional database schema context
            
        Returns:
            Detailed explanation of the query
        """
        if not self.is_available:
            return "Query explainer not available. Please configure your API key in Settings."
        
        if not sql_query or not sql_query.strip():
            return "No query provided for explanation."
        
        try:
            # Build comprehensive explanation prompt
            prompt = self._build_explanation_prompt(sql_query, database_schema)
            
            # Generate explanation
            response = self.model.generate_content(prompt)
            explanation = self._extract_response_text(response)
            
            return explanation.strip() if explanation else "Unable to generate explanation."
            
        except Exception as e:
            return f"Error explaining query: {str(e)}"
    
    def _build_explanation_prompt(self, sql_query: str, database_schema: Optional[dict] = None) -> str:
        """Build a comprehensive prompt for query explanation."""
        
        prompt = """You are an expert SQL query analyzer. Analyze and explain this SQL query in detail.

SQL QUERY TO EXPLAIN:
```
{sql_query}
```

""".format(sql_query=sql_query.strip())
        
        # Add schema context if available
        if database_schema:
            prompt += "DATABASE SCHEMA CONTEXT:\n"
            prompt += self._format_schema(database_schema)
            prompt += "\n\n"
        
        prompt += """REQUIRED EXPLANATION FORMAT:
Provide a clear, structured explanation covering:

1. **Query Purpose**: What is this query trying to accomplish?
2. **Tables Involved**: List all tables referenced in the query
3. **Data Retrieved/Modified**: What specific data is being selected, inserted, updated, or deleted?
4. **Conditions/Filters**: Describe any WHERE, HAVING, or other filtering conditions
5. **Joins & Relationships**: Explain any JOINs and how tables are connected
6. **Aggregations**: If present, explain GROUP BY, aggregate functions (COUNT, SUM, AVG, etc.)
7. **Sorting**: Describe any ORDER BY clauses
8. **Expected Result**: What will the output look like?
9. **Potential Issues**: Identify any syntax errors, logical issues, or potential problems
10. **Optimization Notes**: Brief suggestions for improvement if applicable

FORMATTING:
- Use clear, concise sentences
- Use bullet points or numbered lists for readability
- Keep the explanation under 300 words
- Be specific about table and column names mentioned in the query
- If there are syntax errors, explain them clearly

Provide the explanation in a friendly, educational tone that helps users understand their SQL query.
"""
        
        return prompt
    
    def _format_schema(self, schema: dict) -> str:
        """Format database schema for the prompt."""
        if not schema:
            return ""
        
        formatted = ""
        if isinstance(schema, dict):
            database_name = schema.get('database_name', 'Unknown')
            formatted += f"Database: {database_name}\n\n"
            
            if 'tables' in schema:
                tables = schema['tables']
                # Handle both list and dict formats
                if isinstance(tables, list):
                    # Schema format: tables is a list of table dicts
                    for table_info in tables:
                        table_name = table_info.get('table_name', 'unknown')
                        formatted += f"\nTable: {table_name}\n"
                        
                        if 'columns' in table_info:
                            columns = table_info['columns']
                            # Handle both list and dict formats for columns
                            if isinstance(columns, list):
                                # Columns is a list of column dicts
                                for col_info in columns:
                                    col_name = col_info.get('name', 'unknown')
                                    col_type = col_info.get('type', 'TEXT')
                                    col_str = f"  - {col_name}: {col_type}"
                                    if col_info.get('primary_key'):
                                        col_str += " [PRIMARY KEY]"
                                    if not col_info.get('nullable', True):
                                        col_str += " [NOT NULL]"
                                    formatted += col_str + "\n"
                            elif isinstance(columns, dict):
                                # Columns is a dict (legacy format)
                                for col_name, col_info in columns.items():
                                    col_type = col_info.get('type', 'TEXT') if isinstance(col_info, dict) else str(col_info)
                                    formatted += f"  - {col_name}: {col_type}\n"
                elif isinstance(tables, dict):
                    # Legacy format: tables is a dict
                    for table_name, table_info in tables.items():
                        formatted += f"\nTable: {table_name}\n"
                        if isinstance(table_info, dict) and 'columns' in table_info:
                            columns = table_info['columns']
                            if isinstance(columns, dict):
                                for col_name, col_info in columns.items():
                                    col_type = col_info.get('type', 'TEXT') if isinstance(col_info, dict) else str(col_info)
                                    formatted += f"  - {col_name}: {col_type}\n"
                            elif isinstance(columns, list):
                                for col_info in columns:
                                    col_name = col_info.get('name', 'unknown')
                                    col_type = col_info.get('type', 'TEXT')
                                    formatted += f"  - {col_name}: {col_type}\n"
            
            # Add relationships if available
            if 'relationships' in schema:
                relationships = schema['relationships']
                if isinstance(relationships, list) and relationships:
                    formatted += "\n\nRelationships:\n"
                    for rel in relationships:
                        from_table = rel.get('from_table', 'unknown')
                        from_col = rel.get('from_column', 'unknown')
                        to_table = rel.get('to_table', 'unknown')
                        to_col = rel.get('to_column', 'unknown')
                        formatted += f"  - {from_table}.{from_col} → {to_table}.{to_col}\n"
        
        return formatted
    
    def _extract_response_text(self, response) -> str:
        """Extract text from Gemini API response."""
        try:
            # Handle different response formats
            if hasattr(response, 'text'):
                return response.text
            elif hasattr(response, 'candidates'):
                if response.candidates and len(response.candidates) > 0:
                    candidate = response.candidates[0]
                    if hasattr(candidate, 'content'):
                        parts = candidate.content.parts
                        if parts and len(parts) > 0:
                            return parts[0].text
            elif isinstance(response, str):
                return response
            else:
                return str(response)
        except Exception as e:
            print(f"Error extracting response text: {e}")
            return "Unable to extract explanation from response."

