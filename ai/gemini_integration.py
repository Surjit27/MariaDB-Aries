import os
import requests
import json
from typing import Optional, Dict, Any

class GeminiIntegration:
    def __init__(self):
        """Initialize Gemini API integration with API key."""
        # Use the provided API key
        self.api_key = "AIzaSyAmvcfhifqrmmJ7ia_1p2m61Q1WEYzIrtY"
        self.base_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent"
        if not self.api_key:
            print("Warning: API key not available. AI features will be disabled.")

    def generate_sql_query(self, prompt: str, schema: Optional[Dict[str, Any]] = None) -> Optional[str]:
        """Generate an SQL query based on a user prompt and optional schema description."""
        if not self.api_key:
            print("Cannot generate SQL: API key not provided.")
            return None

        # Prepare the request payload for Google Gemini API
        schema_info = ""
        if schema:
            schema_info = f"\n\nDatabase Schema:\n{json.dumps(schema, indent=2)}"
        
        full_prompt = f"""You are a SQL expert. Generate a SQL query based on the following request:

{prompt}

{schema_info}

Please provide ONLY the SQL query without any explanations or markdown formatting. The query should be ready to execute."""

        payload = {
            "contents": [{
                "parts": [{
                    "text": full_prompt
                }]
            }],
            "generationConfig": {
                "temperature": 0.1,
                "topK": 1,
                "topP": 0.8,
                "maxOutputTokens": 1024
            }
        }

        # Set headers with API key
        headers = {
            "Content-Type": "application/json"
        }

        try:
            # Make request to Gemini API
            url = f"{self.base_url}?key={self.api_key}"
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            response.raise_for_status()
            
            # Parse response
            data = response.json()
            if 'candidates' in data and len(data['candidates']) > 0:
                generated_text = data['candidates'][0]['content']['parts'][0]['text']
                # Clean up the response to extract just the SQL
                sql_query = generated_text.strip()
                if sql_query:
                    print("Successfully generated SQL query.")
                    return sql_query
                else:
                    print("No SQL query returned by API.")
                    return None
            else:
                print("No valid response from API.")
                return None
        except requests.exceptions.RequestException as e:
            print(f"Error generating SQL query: {e}")
            return None
        except Exception as e:
            print(f"Unexpected error: {e}")
            return None

    def set_api_key(self, api_key: str) -> None:
        """Manually set the API key if not loaded from environment variables."""
        self.api_key = api_key
        print("API key manually set.")
    
    def get_suggestions(self, partial_text: str, context: str = "") -> list:
        """Get AI suggestions for SQL completion."""
        if not self.api_key:
            return []
        
        prompt = f"""Complete this SQL query. Provide 3-5 suggestions for the next part:

Partial SQL: {partial_text}
Context: {context}

Return only the completion suggestions, one per line, without explanations."""
        
        try:
            payload = {
                "contents": [{
                    "parts": [{"text": prompt}]
                }],
                "generationConfig": {
                    "temperature": 0.3,
                    "maxOutputTokens": 200
                }
            }
            
            url = f"{self.base_url}?key={self.api_key}"
            response = requests.post(url, json=payload, headers={"Content-Type": "application/json"}, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            if 'candidates' in data and len(data['candidates']) > 0:
                suggestions_text = data['candidates'][0]['content']['parts'][0]['text']
                suggestions = [s.strip() for s in suggestions_text.split('\n') if s.strip()]
                return suggestions[:5]  # Limit to 5 suggestions
            return []
        except Exception as e:
            print(f"Error getting suggestions: {e}")
            return []
    
    def explain_sql(self, sql_query: str) -> str:
        """Get AI explanation of an SQL query."""
        if not self.api_key:
            return "AI explanation not available."
        
        prompt = f"""Explain this SQL query in simple terms:

{sql_query}

Provide a clear, concise explanation of what this query does."""
        
        try:
            payload = {
                "contents": [{
                    "parts": [{"text": prompt}]
                }],
                "generationConfig": {
                    "temperature": 0.2,
                    "maxOutputTokens": 300
                }
            }
            
            url = f"{self.base_url}?key={self.api_key}"
            response = requests.post(url, json=payload, headers={"Content-Type": "application/json"}, timeout=15)
            response.raise_for_status()
            
            data = response.json()
            if 'candidates' in data and len(data['candidates']) > 0:
                explanation = data['candidates'][0]['content']['parts'][0]['text']
                return explanation.strip()
            return "Could not generate explanation."
        except Exception as e:
            print(f"Error explaining SQL: {e}")
            return "Error generating explanation."
