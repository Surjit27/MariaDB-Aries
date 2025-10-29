"""
AI Pipeline for Query Generation
Handles context management, schema extraction, and AI-powered SQL generation
"""

import os
import json
import time
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
import google.generativeai as genai

class AIConversationContext:
    """Manages temporary conversation context for AI interactions."""
    
    def __init__(self):
        self.conversations = {}  # session_id -> conversation data
        self.active_session = None
        
    def create_session(self, db_name: str, selected_tables: List[str] = None) -> str:
        """Create a new conversation session."""
        session_id = f"session_{int(time.time() * 1000)}"
        self.conversations[session_id] = {
            'created_at': datetime.now().isoformat(),
            'db_name': db_name,
            'selected_tables': selected_tables or [],
            'attached_schema': {},
            'chat_history': [],
            'current_query': None
        }
        self.active_session = session_id
        return session_id
    
    def add_message(self, session_id: str, role: str, content: str):
        """Add a message to conversation history."""
        if session_id in self.conversations:
            self.conversations[session_id]['chat_history'].append({
                'role': role,
                'content': content,
                'timestamp': datetime.now().isoformat()
            })
    
    def attach_schema(self, session_id: str, table_name: str, schema_info: Dict):
        """Attach table schema to conversation context."""
        if session_id in self.conversations:
            self.conversations[session_id]['attached_schema'][table_name] = schema_info
            if table_name not in self.conversations[session_id]['selected_tables']:
                self.conversations[session_id]['selected_tables'].append(table_name)
    
    def set_current_query(self, session_id: str, query: str):
        """Set the current query being worked on."""
        if session_id in self.conversations:
            self.conversations[session_id]['current_query'] = query
    
    def get_context(self, session_id: str) -> Dict:
        """Get conversation context."""
        return self.conversations.get(session_id, {})
    
    def close_session(self, session_id: str):
        """Close and delete a conversation session."""
        if session_id in self.conversations:
            del self.conversations[session_id]
        if self.active_session == session_id:
            self.active_session = None
    
    def get_active_session(self) -> Optional[str]:
        """Get the active session ID."""
        return self.active_session


class SchemaExtractor:
    """Extracts and formats database schema for AI context."""
    
    def __init__(self, db_manager):
        self.db_manager = db_manager
    
    def extract_full_schema(self, db_name: str) -> Dict[str, Any]:
        """Extract complete schema for a database."""
        try:
            if not self.db_manager.current_db or self.db_manager.current_db != db_name:
                self.db_manager.open_database(db_name)
            
            tables = self.db_manager.get_tables()
            schema = {
                'database_name': db_name,
                'tables': [],
                'relationships': []
            }
            
            for table_name in tables:
                table_info = self.extract_table_schema(table_name)
                if table_info:
                    schema['tables'].append(table_info)
            
            # Extract relationships
            schema['relationships'] = self.extract_relationships(tables)
            
            return schema
            
        except Exception as e:
            print(f"Error extracting schema: {e}")
            return {
                'database_name': db_name,
                'tables': [],
                'relationships': []
            }
    
    def extract_table_schema(self, table_name: str) -> Optional[Dict]:
        """Extract schema for a specific table."""
        try:
            if not self.db_manager.connection:
                return None
            
            # Get column information
            self.db_manager.cursor.execute(f"PRAGMA table_info({table_name})")
            columns = self.db_manager.cursor.fetchall()
            
            table_info = {
                'table_name': table_name,
                'columns': []
            }
            
            for col in columns:
                col_info = {
                    'name': col[1],
                    'type': col[2],
                    'nullable': not bool(col[3]),
                    'default_value': col[4],
                    'primary_key': bool(col[5])
                }
                table_info['columns'].append(col_info)
            
            # Get sample data (first 3 rows)
            try:
                self.db_manager.cursor.execute(f"SELECT * FROM {table_name} LIMIT 3")
                sample_data = self.db_manager.cursor.fetchall()
                table_info['sample_data'] = [list(row) for row in sample_data]
            except:
                table_info['sample_data'] = []
            
            # Get row count
            try:
                self.db_manager.cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                row_count = self.db_manager.cursor.fetchone()[0]
                table_info['row_count'] = row_count
            except:
                table_info['row_count'] = 0
            
            return table_info
            
        except Exception as e:
            print(f"Error extracting table schema for {table_name}: {e}")
            return None
    
    def extract_relationships(self, tables: List[str]) -> List[Dict]:
        """Extract foreign key relationships between tables."""
        relationships = []
        
        try:
            for table_name in tables:
                self.db_manager.cursor.execute(f"PRAGMA foreign_key_list({table_name})")
                foreign_keys = self.db_manager.cursor.fetchall()
                
                for fk in foreign_keys:
                    relationships.append({
                        'from_table': table_name,
                        'from_column': fk[3],
                        'to_table': fk[2],
                        'to_column': fk[4],
                        'on_update': fk[5],
                        'on_delete': fk[6]
                    })
        except Exception as e:
            print(f"Error extracting relationships: {e}")
        
        return relationships
    
    def extract_selected_tables_schema(self, table_names: List[str]) -> Dict[str, Any]:
        """Extract schema for only selected tables."""
        schema = {
            'database_name': self.db_manager.current_db or 'Unknown',
            'tables': [],
            'relationships': []
        }
        
        for table_name in table_names:
            table_info = self.extract_table_schema(table_name)
            if table_info:
                schema['tables'].append(table_info)
        
        # Extract only relationships involving selected tables
        all_relationships = self.extract_relationships(table_names)
        schema['relationships'] = [
            rel for rel in all_relationships
            if rel['from_table'] in table_names and rel['to_table'] in table_names
        ]
        
        return schema


class AIQueryGenerator:
    """Generates SQL queries using AI with full context awareness."""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.model_name = 'gemini-2.5-flash'
        self.max_tokens = 2000
        self.temperature = 0.7
        
        try:
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel(self.model_name)
            print(f"✅ AI Query Generator initialized with model: {self.model_name}")
        except Exception as e:
            print(f"❌ Error initializing AI Query Generator: {e}")
            self.model = None
    
    def is_available(self) -> bool:
        """Check if AI is available."""
        return self.model is not None
    
    def generate_new_query(self, user_prompt: str, schema: Dict[str, Any], 
                          chat_history: List[Dict] = None) -> Dict[str, Any]:
        """Generate a completely new SQL query."""
        
        prompt = self._build_new_query_prompt(user_prompt, schema, chat_history)
        
        try:
            response = self.model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=self.temperature,
                    max_output_tokens=self.max_tokens,
                )
            )
            
            return self._parse_ai_response(response.text, query_type="new")
            
        except Exception as e:
            print(f"Error generating query: {e}")
            return {
                'success': False,
                'error': str(e),
                'query': None,
                'explanation': None
            }
    
    def modify_existing_query(self, existing_query: str, user_prompt: str, 
                             schema: Dict[str, Any], chat_history: List[Dict] = None) -> Dict[str, Any]:
        """Modify an existing SQL query based on user request."""
        
        prompt = self._build_modify_query_prompt(existing_query, user_prompt, schema, chat_history)
        
        try:
            response = self.model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=self.temperature,
                    max_output_tokens=self.max_tokens,
                )
            )
            
            return self._parse_ai_response(response.text, query_type="modify")
            
        except Exception as e:
            print(f"Error modifying query: {e}")
            return {
                'success': False,
                'error': str(e),
                'query': None,
                'explanation': None
            }
    
    def append_to_query(self, existing_query: str, user_prompt: str, 
                       schema: Dict[str, Any], chat_history: List[Dict] = None) -> Dict[str, Any]:
        """Append additional logic to existing query."""
        
        prompt = self._build_append_query_prompt(existing_query, user_prompt, schema, chat_history)
        
        try:
            response = self.model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=self.temperature,
                    max_output_tokens=self.max_tokens,
                )
            )
            
            return self._parse_ai_response(response.text, query_type="append")
            
        except Exception as e:
            print(f"Error appending to query: {e}")
            return {
                'success': False,
                'error': str(e),
                'query': None,
                'explanation': None
            }
    
    def _build_new_query_prompt(self, user_prompt: str, schema: Dict[str, Any], 
                                chat_history: List[Dict] = None) -> str:
        """Build prompt for generating new query."""
        
        prompt = f"""You are an expert SQL query generator. Generate a clean, efficient SQL query based on the user's request.

DATABASE SCHEMA:
"""
        prompt += self._format_schema(schema)
        
        if chat_history:
            prompt += "\n\nCONVERSATION HISTORY:\n"
            for msg in chat_history[-5:]:  # Last 5 messages
                prompt += f"{msg['role']}: {msg['content']}\n"
        
        prompt += f"""

USER REQUEST: {user_prompt}

INSTRUCTIONS:
1. Generate a valid SQL query that fulfills the user's request
2. Use proper SQL syntax compatible with SQLite
3. Include appropriate JOINs if multiple tables are needed
4. Use proper WHERE clauses for filtering
5. Consider performance and use appropriate indexes
6. Return ONLY the SQL query with NO markdown formatting or code blocks
7. After the query, provide a brief explanation (2-3 sentences max)

FORMAT YOUR RESPONSE EXACTLY LIKE THIS:

SQL_QUERY:
[Your SQL query here - plain text, no backticks, no markdown]

EXPLANATION:
[2-3 sentence explanation of what the query does]

CONFIDENCE: [0.0 to 1.0]

COMPLEXITY: [Simple/Medium/Complex]
"""
        
        return prompt
    
    def _build_modify_query_prompt(self, existing_query: str, user_prompt: str, 
                                   schema: Dict[str, Any], chat_history: List[Dict] = None) -> str:
        """Build prompt for modifying existing query."""
        
        prompt = f"""You are an expert SQL query modifier. Modify the existing SQL query based on the user's request.

DATABASE SCHEMA:
"""
        prompt += self._format_schema(schema)
        
        prompt += f"""

EXISTING QUERY:
{existing_query}

USER REQUEST FOR MODIFICATION: {user_prompt}

INSTRUCTIONS:
1. Modify the existing query to incorporate the user's requested changes
2. Maintain the structure of the original query where possible
3. Ensure the modified query is valid SQL
4. Explain what you changed and why

FORMAT YOUR RESPONSE EXACTLY LIKE THIS:

SQL_QUERY:
[Your modified SQL query here - plain text, no backticks]

EXPLANATION:
[Explain what was changed and why - 2-3 sentences]

CHANGES_MADE:
[List the specific changes made]

CONFIDENCE: [0.0 to 1.0]

COMPLEXITY: [Simple/Medium/Complex]
"""
        
        return prompt
    
    def _build_append_query_prompt(self, existing_query: str, user_prompt: str, 
                                   schema: Dict[str, Any], chat_history: List[Dict] = None) -> str:
        """Build prompt for appending to existing query."""
        
        prompt = f"""You are an expert SQL query enhancer. Append additional logic to the existing SQL query.

DATABASE SCHEMA:
"""
        prompt += self._format_schema(schema)
        
        prompt += f"""

EXISTING QUERY:
{existing_query}

USER REQUEST TO APPEND: {user_prompt}

INSTRUCTIONS:
1. Add the requested functionality to the end of the existing query
2. Use UNION, subqueries, or additional clauses as appropriate
3. Maintain the integrity of the original query
4. Ensure the combined query is valid SQL

FORMAT YOUR RESPONSE EXACTLY LIKE THIS:

SQL_QUERY:
[Your enhanced SQL query here - plain text, no backticks]

EXPLANATION:
[Explain what was added - 2-3 sentences]

CONFIDENCE: [0.0 to 1.0]

COMPLEXITY: [Simple/Medium/Complex]
"""
        
        return prompt
    
    def _format_schema(self, schema: Dict[str, Any]) -> str:
        """Format schema information for the prompt."""
        schema_text = f"Database: {schema.get('database_name', 'Unknown')}\n\n"
        
        # Format tables
        tables = schema.get('tables', [])
        if tables:
            schema_text += "TABLES:\n"
            for table in tables:
                table_name = table.get('table_name', 'unknown')
                row_count = table.get('row_count', 0)
                schema_text += f"\n📊 Table: {table_name} ({row_count} rows)\n"
                
                columns = table.get('columns', [])
                if columns:
                    schema_text += "Columns:\n"
                    for col in columns:
                        col_info = f"  • {col['name']} ({col['type']})"
                        if col.get('primary_key'):
                            col_info += " [PRIMARY KEY]"
                        if not col.get('nullable', True):
                            col_info += " [NOT NULL]"
                        if col.get('default_value'):
                            col_info += f" [DEFAULT: {col['default_value']}]"
                        schema_text += col_info + "\n"
                
                # Sample data
                sample_data = table.get('sample_data', [])
                if sample_data:
                    schema_text += f"Sample Data (first 3 rows):\n"
                    for row in sample_data[:3]:
                        schema_text += f"  {row}\n"
        
        # Format relationships
        relationships = schema.get('relationships', [])
        if relationships:
            schema_text += "\nRELATIONSHIPS (Foreign Keys):\n"
            for rel in relationships:
                schema_text += f"  • {rel['from_table']}.{rel['from_column']} → {rel['to_table']}.{rel['to_column']}\n"
        
        return schema_text
    
    def _parse_ai_response(self, response_text: str, query_type: str) -> Dict[str, Any]:
        """Parse AI response and extract structured information."""
        
        result = {
            'success': True,
            'query': None,
            'explanation': None,
            'confidence': 0.9,
            'complexity': 'Medium',
            'changes_made': None,
            'query_type': query_type
        }
        
        try:
            # Extract SQL query
            if "SQL_QUERY:" in response_text:
                query_start = response_text.find("SQL_QUERY:") + len("SQL_QUERY:")
                query_end = response_text.find("EXPLANATION:", query_start)
                if query_end == -1:
                    query_end = len(response_text)
                
                query = response_text[query_start:query_end].strip()
                # Remove markdown code blocks if present
                query = query.replace("```sql", "").replace("```", "").strip()
                result['query'] = query
            
            # Extract explanation
            if "EXPLANATION:" in response_text:
                exp_start = response_text.find("EXPLANATION:") + len("EXPLANATION:")
                exp_end = response_text.find("CONFIDENCE:", exp_start)
                if exp_end == -1:
                    exp_end = response_text.find("COMPLEXITY:", exp_start)
                if exp_end == -1:
                    exp_end = len(response_text)
                
                explanation = response_text[exp_start:exp_end].strip()
                result['explanation'] = explanation
            
            # Extract confidence
            if "CONFIDENCE:" in response_text:
                conf_start = response_text.find("CONFIDENCE:") + len("CONFIDENCE:")
                conf_end = response_text.find("\n", conf_start)
                if conf_end == -1:
                    conf_end = len(response_text)
                
                try:
                    confidence = float(response_text[conf_start:conf_end].strip())
                    result['confidence'] = max(0.0, min(1.0, confidence))
                except:
                    pass
            
            # Extract complexity
            if "COMPLEXITY:" in response_text:
                comp_start = response_text.find("COMPLEXITY:") + len("COMPLEXITY:")
                comp_end = response_text.find("\n", comp_start)
                if comp_end == -1:
                    comp_end = len(response_text)
                
                complexity = response_text[comp_start:comp_end].strip()
                result['complexity'] = complexity
            
            # Extract changes made (for modify queries)
            if "CHANGES_MADE:" in response_text:
                changes_start = response_text.find("CHANGES_MADE:") + len("CHANGES_MADE:")
                changes_end = response_text.find("CONFIDENCE:", changes_start)
                if changes_end == -1:
                    changes_end = len(response_text)
                
                changes = response_text[changes_start:changes_end].strip()
                result['changes_made'] = changes
            
            # If no structured response, try to extract plain query
            if not result['query']:
                # Try to find SQL keywords
                lines = response_text.split('\n')
                for line in lines:
                    line_upper = line.strip().upper()
                    if line_upper.startswith(('SELECT', 'INSERT', 'UPDATE', 'DELETE', 'CREATE', 'DROP', 'ALTER')):
                        result['query'] = line.strip()
                        break
            
        except Exception as e:
            print(f"Error parsing AI response: {e}")
            result['success'] = False
            result['error'] = str(e)
        
        return result


class AIPipeline:
    """Main AI Pipeline orchestrator."""
    
    def __init__(self, db_manager, api_key: str):
        self.db_manager = db_manager
        self.context_manager = AIConversationContext()
        self.schema_extractor = SchemaExtractor(db_manager)
        self.query_generator = AIQueryGenerator(api_key)
    
    def is_available(self) -> bool:
        """Check if AI pipeline is available."""
        return self.query_generator.is_available()
    
    def start_ai_session(self, db_name: str, selected_tables: List[str] = None, 
                        current_query: str = None) -> str:
        """Start a new AI conversation session."""
        session_id = self.context_manager.create_session(db_name, selected_tables)
        
        # Extract and attach schema for selected tables
        if selected_tables:
            schema = self.schema_extractor.extract_selected_tables_schema(selected_tables)
        else:
            schema = self.schema_extractor.extract_full_schema(db_name)
        
        # Store schema in context
        for table in schema['tables']:
            self.context_manager.attach_schema(
                session_id, 
                table['table_name'], 
                table
            )
        
        # Set current query if provided
        if current_query:
            self.context_manager.set_current_query(session_id, current_query)
        
        return session_id
    
    def generate_query(self, session_id: str, user_prompt: str, 
                      action: str = "new") -> Dict[str, Any]:
        """
        Generate or modify SQL query based on action type.
        
        Actions:
        - "new": Generate completely new query
        - "modify": Modify existing query in editor
        - "append": Append to existing query
        """
        
        context = self.context_manager.get_context(session_id)
        if not context:
            return {
                'success': False,
                'error': 'Invalid session ID',
                'query': None,
                'explanation': None
            }
        
        # Build schema from attached tables
        schema = {
            'database_name': context['db_name'],
            'tables': list(context['attached_schema'].values()),
            'relationships': []
        }
        
        # Get chat history
        chat_history = context.get('chat_history', [])
        
        # Add user message to history
        self.context_manager.add_message(session_id, 'user', user_prompt)
        
        # Generate based on action type
        if action == "new":
            result = self.query_generator.generate_new_query(
                user_prompt, schema, chat_history
            )
        elif action == "modify":
            existing_query = context.get('current_query', '')
            if not existing_query:
                return {
                    'success': False,
                    'error': 'No existing query to modify',
                    'query': None,
                    'explanation': None
                }
            result = self.query_generator.modify_existing_query(
                existing_query, user_prompt, schema, chat_history
            )
        elif action == "append":
            existing_query = context.get('current_query', '')
            if not existing_query:
                return {
                    'success': False,
                    'error': 'No existing query to append to',
                    'query': None,
                    'explanation': None
                }
            result = self.query_generator.append_to_query(
                existing_query, user_prompt, schema, chat_history
            )
        else:
            return {
                'success': False,
                'error': f'Unknown action: {action}',
                'query': None,
                'explanation': None
            }
        
        # Add AI response to history
        if result.get('success'):
            ai_message = f"Generated Query:\n{result.get('query', 'N/A')}\n\nExplanation: {result.get('explanation', 'N/A')}"
            self.context_manager.add_message(session_id, 'assistant', ai_message)
        
        return result
    
    def close_session(self, session_id: str):
        """Close AI conversation session."""
        self.context_manager.close_session(session_id)
    
    def get_active_session(self) -> Optional[str]:
        """Get active session ID."""
        return self.context_manager.get_active_session()
