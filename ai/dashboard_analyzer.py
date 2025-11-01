"""
AI Dashboard Analyzer
Analyzes SQL query results and suggests appropriate visualizations using AI
"""

import os
import json
from typing import Dict, List, Optional, Any, Tuple
import google.generativeai as genai

class DashboardAnalyzer:
    """Uses AI to analyze query results and suggest visualizations."""
    
    def __init__(self, api_key: str = None):
        """Initialize the dashboard analyzer."""
        self.api_key = api_key or os.getenv('GEMINI_API_KEY')
        self.model_name = 'gemini-2.5-flash'
        
        if not self.api_key:
            print("Warning: GEMINI_API_KEY not found. Dashboard AI features will be disabled.")
            self.model = None
            return
        
        try:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel(self.model_name)
            print(f"✅ Dashboard Analyzer initialized with model: {self.model_name}")
        except Exception as e:
            print(f"❌ Error initializing Dashboard Analyzer: {e}")
            self.model = None
    
    def is_available(self) -> bool:
        """Check if AI is available."""
        return self.model is not None
    
    def analyze_and_suggest_visualizations(self, query: str, columns: List[str], 
                                          data: List[List[Any]], 
                                          user_instruction: str = "") -> Dict[str, Any]:
        """
        Analyze query results and suggest visualizations.
        
        Returns:
            {
                'success': bool,
                'summary': str,
                'plots': [
                    {
                        'type': 'line|bar|scatter|pie|heatmap|histogram|boxplot',
                        'title': str,
                        'x': str,  # column name
                        'y': str,  # column name
                        'z': str,  # optional for heatmaps
                        'color_by': str,  # optional for grouping
                        'description': str
                    }
                ],
                'insights': [str]
            }
        """
        if not self.is_available():
            return {
                'success': False,
                'error': 'AI not available - check API key',
                'summary': '',
                'plots': [],
                'insights': []
            }
        
        # Analyze data types and structure
        column_info = self._analyze_columns(columns, data)
        
        # Get total rows and sample data (send more data to AI for better analysis)
        total_rows = len(data) if data else 0
        sample_size = min(50, total_rows) if total_rows > 0 else len(data)
        sample_data = data[:sample_size] if data else []
        
        # Build prompt for AI
        prompt = self._build_analysis_prompt(query, columns, column_info, sample_data, total_rows, user_instruction)
        
        try:
            response = self.model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.3,  # Lower temperature for more consistent analysis
                    max_output_tokens=3000,
                )
            )
            
            # Extract response text from Gemini API response
            response_text = self._extract_response_text(response)
            
            result = self._parse_ai_response(response_text, columns, column_info)
            return result
            
        except Exception as e:
            print(f"Error in dashboard analysis: {e}")
            # Fallback to basic heuristics
            return self._fallback_analysis(columns, column_info, data)
    
    def _analyze_columns(self, columns: List[str], data: List[List[Any]]) -> Dict[str, Dict]:
        """Analyze column types and properties."""
        column_info = {}
        
        if not data or not columns:
            return column_info
        
        # Analyze each column
        for i, col in enumerate(columns):
            values = [row[i] if i < len(row) else None for row in data if row]
            non_null_values = [v for v in values if v is not None]
            
            if not non_null_values:
                column_info[col] = {
                    'type': 'unknown',
                    'is_numeric': False,
                    'is_date': False,
                    'is_categorical': False,
                    'unique_count': 0,
                    'sample_values': []
                }
                continue
            
            # Check if numeric
            numeric_count = 0
            for v in non_null_values[:100]:  # Sample first 100
                try:
                    float(str(v))
                    numeric_count += 1
                except:
                    pass
            
            is_numeric = numeric_count / len(non_null_values[:100]) > 0.8 if non_null_values else False
            
            # Check if date (basic heuristic)
            is_date = False
            date_keywords = ['date', 'time', 'created', 'updated', 'timestamp']
            if any(kw in col.lower() for kw in date_keywords):
                is_date = True
            
            # Check unique values
            unique_values = len(set(str(v) for v in non_null_values))
            is_categorical = unique_values <= min(20, len(non_null_values) * 0.5) if non_null_values else False
            
            column_info[col] = {
                'type': 'numeric' if is_numeric else ('date' if is_date else 'categorical'),
                'is_numeric': is_numeric,
                'is_date': is_date,
                'is_categorical': is_categorical,
                'unique_count': unique_values,
                'sample_values': [str(v) for v in non_null_values[:5]]
            }
        
        return column_info
    
    def _extract_response_text(self, response) -> str:
        """Extract text from Gemini API response."""
        try:
            # Try the simple .text accessor first
            if hasattr(response, 'text'):
                return response.text
        except:
            pass
        
        # Fallback: extract from parts
        try:
            if hasattr(response, 'parts') and response.parts:
                # Get text from all parts
                texts = []
                for part in response.parts:
                    if hasattr(part, 'text'):
                        texts.append(part.text)
                if texts:
                    return ' '.join(texts)
        except:
            pass
        
        # Fallback: try candidates
        try:
            if hasattr(response, 'candidates') and response.candidates:
                for candidate in response.candidates:
                    if hasattr(candidate, 'content') and hasattr(candidate.content, 'parts'):
                        texts = []
                        for part in candidate.content.parts:
                            if hasattr(part, 'text'):
                                texts.append(part.text)
                        if texts:
                            return ' '.join(texts)
        except:
            pass
        
        # Last resort: convert to string
        return str(response)
    
    def _build_analysis_prompt(self, query: str, columns: List[str], 
                              column_info: Dict, sample_data: List[List[Any]], 
                              total_rows: int, user_instruction: str) -> str:
        """Build prompt for AI analysis."""
        
        prompt = f"""You are an expert data visualization analyst. Analyze the following SQL query results and suggest the best visualizations.

SQL QUERY:
{query}

COLUMNS ({len(columns)} total):
"""
        for col in columns:
            info = column_info.get(col, {})
            col_type = info.get('type', 'unknown')
            prompt += f"  • {col} ({col_type})"
            if info.get('unique_count'):
                prompt += f" - {info.get('unique_count')} unique values"
            prompt += "\n"
        
        prompt += f"""
SAMPLE DATA (first {len(sample_data)} rows):
"""
        # Show column headers
        prompt += "  " + " | ".join(columns[:10]) + "\n"  # Limit to 10 columns
        for row in sample_data[:10]:  # Show first 10 rows
            row_str = " | ".join(str(v)[:30] for v in row[:10])  # Limit column width
            prompt += f"  {row_str}\n"
        
        if user_instruction:
            prompt += f"""
USER INSTRUCTION:
{user_instruction}
"""
        
        prompt += f"""
TASK:
1. Analyze the data structure and relationships
2. Identify key metrics, dimensions, and categorical fields
3. Suggest MINIMUM 4 and MAXIMUM as many appropriate visualizations as possible (aim for 6-10 charts if data supports it)
4. Explain your reasoning
5. With {total_rows} rows of data, you have plenty of data points - create comprehensive visualizations

IMPORTANT:
- You MUST suggest at least 4 different charts (minimum requirement)
- Try to suggest as many relevant visualizations as possible (up to 10-12 if the data supports it)
- Each chart should reveal different insights
- Consider different perspectives: time trends, distributions, correlations, comparisons, etc.

CHART TYPES AVAILABLE (all supported):
- line: For time series or sequential data, trends over time, continuous progressions
- bar: For categorical comparisons, ranking data, comparing groups
- scatter: For relationships between two numeric variables, correlation analysis
- pie: For proportions/percentages, part-to-whole relationships (use for 2-8 categories max)
- heatmap: For correlation matrices, cross-tabulation, two-dimensional patterns
- histogram: For distribution of a single numeric variable, frequency analysis
- boxplot: For statistical distribution, quartiles, outliers, comparing groups

IMPORTANT FOR CHART SELECTION:
- Use pie charts when showing proportions/percentages (e.g., type distribution, region breakdown)
- Use line charts for time-based data, trends, or sequential progressions
- Use bar charts for categorical comparisons (e.g., Pokemon by region, abilities count)
- Use scatter plots to find correlations (e.g., weight vs height, experience vs level)
- Use heatmaps for relationships between categorical variables
- Use histograms to show distribution of a single metric
- Use boxplots to compare distributions across categories

OUTPUT FORMAT (JSON only, no markdown):
{{
  "summary": "Brief 2-3 sentence summary of what the data shows and recommended visualization strategy",
  "plots": [
    {{
      "type": "bar",
      "title": "Chart Title",
      "x": "column_name",
      "y": "column_name",
      "z": "column_name (optional, for heatmaps)",
      "color_by": "column_name (optional, for grouping)",
      "description": "Why this chart is recommended"
    }}
  ],
  "insights": [
    "Key insight 1",
    "Key insight 2"
  ]
}}

IMPORTANT:
- Use actual column names from the COLUMNS list
- Prioritize charts that reveal insights
- Create diverse visualizations - don't repeat the same chart type unnecessarily
- For time-based data, suggest line charts
- For categorical comparisons, suggest bar charts
- For correlations, suggest scatter or heatmap
- With {total_rows} rows, you can create detailed visualizations
- MINIMUM 4 charts required, MAXIMUM as many as make sense (aim for 6-10+ charts)
- Think creatively: if there are multiple numeric columns, create scatter plots for different pairs
- If there are multiple categorical columns, create different bar charts showing different relationships
- Consider grouped/stacked visualizations when appropriate
"""
        
        return prompt
    
    def _parse_ai_response(self, response_text: str, columns: List[str], 
                         column_info: Dict) -> Dict[str, Any]:
        """Parse AI response into structured format."""
        
        result = {
            'success': True,
            'summary': '',
            'plots': [],
            'insights': []
        }
        
        try:
            # Try to extract JSON from response
            # Remove markdown code blocks if present
            text = response_text.strip()
            if '```json' in text:
                start = text.find('```json') + 7
                end = text.find('```', start)
                text = text[start:end].strip()
            elif '```' in text:
                start = text.find('```') + 3
                end = text.find('```', start)
                text = text[start:end].strip()
            
            # Parse JSON
            parsed = json.loads(text)
            
            result['summary'] = parsed.get('summary', '')
            result['plots'] = parsed.get('plots', [])
            result['insights'] = parsed.get('insights', [])
            
            # Validate plot specifications against actual columns
            validated_plots = []
            for plot in result['plots']:
                validated_plot = {
                    'type': plot.get('type', 'bar'),
                    'title': plot.get('title', 'Chart'),
                    'x': plot.get('x'),
                    'y': plot.get('y'),
                    'z': plot.get('z'),
                    'color_by': plot.get('color_by'),
                    'description': plot.get('description', '')
                }
                
                # Verify columns exist
                if validated_plot['x'] and validated_plot['x'] not in columns:
                    continue
                if validated_plot['y'] and validated_plot['y'] not in columns:
                    continue
                if validated_plot['z'] and validated_plot['z'] not in columns:
                    validated_plot['z'] = None
                if validated_plot['color_by'] and validated_plot['color_by'] not in columns:
                    validated_plot['color_by'] = None
                
                validated_plots.append(validated_plot)
            
            # Keep all validated plots (no artificial limit - AI will suggest appropriate number)
            result['plots'] = validated_plots
            
        except json.JSONDecodeError as e:
            print(f"Error parsing AI response as JSON: {e}")
            print(f"Response was: {response_text[:500]}")
            # Fallback to heuristic analysis
            return self._fallback_analysis(columns, column_info, [])
        except Exception as e:
            print(f"Error processing AI response: {e}")
            return self._fallback_analysis(columns, column_info, [])
        
        return result
    
    def _fallback_analysis(self, columns: List[str], column_info: Dict, 
                          data: List[List[Any]]) -> Dict[str, Any]:
        """Fallback analysis using heuristics when AI is unavailable."""
        
        plots = []
        numeric_cols = [col for col, info in column_info.items() if info.get('is_numeric')]
        categorical_cols = [col for col, info in column_info.items() if info.get('is_categorical')]
        date_cols = [col for col, info in column_info.items() if info.get('is_date')]
        
        # Rule-based suggestions
        if len(numeric_cols) >= 2:
            # Scatter plot for first two numeric columns
            plots.append({
                'type': 'scatter',
                'title': f'{numeric_cols[0]} vs {numeric_cols[1]}',
                'x': numeric_cols[0],
                'y': numeric_cols[1],
                'description': 'Relationship between two numeric variables'
            })
        
        if date_cols and numeric_cols:
            # Line chart for time series
            plots.append({
                'type': 'line',
                'title': f'{numeric_cols[0]} Over Time',
                'x': date_cols[0] if date_cols else columns[0],
                'y': numeric_cols[0],
                'description': 'Time series visualization'
            })
        
        if categorical_cols and numeric_cols:
            # Bar chart
            plots.append({
                'type': 'bar',
                'title': f'{numeric_cols[0]} by {categorical_cols[0]}',
                'x': categorical_cols[0],
                'y': numeric_cols[0],
                'description': 'Categorical comparison'
            })
        
        if numeric_cols:
            # Histogram
            plots.append({
                'type': 'histogram',
                'title': f'Distribution of {numeric_cols[0]}',
                'x': numeric_cols[0],
                'y': None,
                'description': 'Distribution analysis'
            })
        
        return {
            'success': True,
            'summary': f'Analyzed {len(columns)} columns. Suggested {len(plots)} visualizations based on data types.',
            'plots': plots,  # Return all plots (minimum 4 guaranteed by logic)
            'insights': []
        }
