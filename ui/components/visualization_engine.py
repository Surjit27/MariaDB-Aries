"""
Visualization Engine
Creates charts from data using matplotlib
"""
from __future__ import annotations

try:
    import matplotlib
    matplotlib.use('TkAgg')  # Use TkAgg backend for Tkinter
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    from matplotlib.figure import Figure
    import numpy as np
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False
    print("Warning: matplotlib not available. Dashboard visualizations will not work.")

try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False
    print("Warning: pandas not available. Dashboard visualizations will not work.")

from typing import List, Dict, Any, Optional, Tuple

class VisualizationEngine:
    """Engine for creating visualizations from query results."""
    
    def __init__(self):
        """Initialize visualization engine."""
        if not MATPLOTLIB_AVAILABLE or not PANDAS_AVAILABLE:
            self.available = False
            return
        self.available = True
        # Set style
        plt.style.use('default')
        self.colors = plt.cm.Set3.colors
        self.figure_size = (6, 4)
    
    def create_chart(self, chart_type: str, data: List[List[Any]], columns: List[str],
                     plot_config: Dict[str, Any], parent_frame=None) -> Tuple[Optional[Any], Optional[Any]]:
        """
        Create a chart based on type and configuration.
        
        Args:
            chart_type: Type of chart (line, bar, scatter, pie, heatmap, histogram, boxplot)
            data: The data rows
            columns: Column names
            plot_config: Configuration dict with keys: x, y, z, color_by, title
            parent_frame: Optional parent frame for embedding
            
        Returns:
            Tuple of (matplotlib Figure, FigureCanvasTkAgg) or (None, None) if not available
        """
        
        if not self.available:
            fig = None
            if MATPLOTLIB_AVAILABLE:
                fig = Figure(figsize=self.figure_size, dpi=100)
                ax = fig.add_subplot(111)
                ax.text(0.5, 0.5, "matplotlib/pandas not installed", 
                       ha='center', va='center', transform=ax.transAxes)
            canvas = None
            return fig, canvas
        
        # Convert data to pandas DataFrame for easier manipulation
        df = self._data_to_dataframe(data, columns)
        
        # Create figure
        fig = Figure(figsize=self.figure_size, dpi=100)
        ax = fig.add_subplot(111)
        
        x_col = plot_config.get('x')
        y_col = plot_config.get('y')
        z_col = plot_config.get('z')
        color_by = plot_config.get('color_by')
        title = plot_config.get('title', 'Chart')
        
        # Validate columns exist in dataframe
        if x_col and x_col not in df.columns:
            ax.text(0.5, 0.5, f"Error: Column '{x_col}' not found", 
                   ha='center', va='center', transform=ax.transAxes)
            fig.suptitle(title, fontsize=10)
            canvas = FigureCanvasTkAgg(fig, parent_frame) if parent_frame else None
            return fig, canvas
        
        try:
            if chart_type == 'line':
                self._create_line_chart(ax, df, x_col, y_col, color_by, title)
            elif chart_type == 'bar':
                self._create_bar_chart(ax, df, x_col, y_col, color_by, title)
            elif chart_type == 'scatter':
                self._create_scatter_chart(ax, df, x_col, y_col, color_by, title)
            elif chart_type == 'pie':
                self._create_pie_chart(ax, df, x_col, y_col, title)
            elif chart_type == 'heatmap':
                self._create_heatmap(ax, df, x_col, y_col, z_col, title)
            elif chart_type == 'histogram':
                self._create_histogram(ax, df, x_col, title)
            elif chart_type == 'boxplot':
                self._create_boxplot(ax, df, x_col, y_col, title)
            else:
                ax.text(0.5, 0.5, f"Unknown chart type: {chart_type}", 
                       ha='center', va='center', transform=ax.transAxes)
            
            fig.suptitle(title, fontsize=11, fontweight='bold')
            fig.tight_layout()
            
        except Exception as e:
            ax.clear()
            ax.text(0.5, 0.5, f"Error creating chart:\n{str(e)}", 
                   ha='center', va='center', transform=ax.transAxes, fontsize=9)
            fig.suptitle(title, fontsize=10)
        
        # Create canvas if parent frame provided
        canvas = FigureCanvasTkAgg(fig, parent_frame) if parent_frame else None
        
        return fig, canvas
    
    def _data_to_dataframe(self, data: List[List[Any]], columns: List[str]) -> pd.DataFrame:
        """Convert data rows to pandas DataFrame."""
        try:
            # Ensure all rows have same length as columns
            normalized_data = []
            for row in data:
                normalized_row = list(row) if isinstance(row, (list, tuple)) else [row]
                # Pad or truncate to match column count
                while len(normalized_row) < len(columns):
                    normalized_row.append(None)
                normalized_row = normalized_row[:len(columns)]
                normalized_data.append(normalized_row)
            
            df = pd.DataFrame(normalized_data, columns=columns)
            
            # Try to convert numeric columns
            for col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='ignore')
            
            return df
            
        except Exception as e:
            print(f"Error converting to DataFrame: {e}")
            return pd.DataFrame()
    
    def _create_line_chart(self, ax, df: pd.DataFrame, x_col: str, y_col: str, 
                           color_by: Optional[str], title: str):
        """Create a line chart."""
        if not x_col or not y_col:
            return
        
        if color_by and color_by in df.columns:
            # Group by color_by and plot multiple lines
            for group_name, group_df in df.groupby(color_by):
                ax.plot(group_df[x_col], group_df[y_col], marker='o', label=str(group_name), linewidth=2)
            ax.legend(fontsize=8, loc='best')
        else:
            ax.plot(df[x_col], df[y_col], marker='o', linewidth=2, color='#0066CC')
        
        ax.set_xlabel(x_col, fontsize=9)
        ax.set_ylabel(y_col, fontsize=9)
        ax.grid(True, alpha=0.3)
        ax.tick_params(labelsize=8)
    
    def _create_bar_chart(self, ax, df: pd.DataFrame, x_col: str, y_col: str, 
                         color_by: Optional[str], title: str):
        """Create a bar chart."""
        if not x_col or not y_col:
            return
        
        if color_by and color_by in df.columns:
            # Grouped bar chart
            groups = df.groupby([x_col, color_by])[y_col].sum().unstack(fill_value=0)
            groups.plot(kind='bar', ax=ax, width=0.8)
            ax.legend(title=color_by, fontsize=8, loc='best')
        else:
            # Simple bar chart
            bar_data = df.groupby(x_col)[y_col].sum() if len(df[x_col].unique()) < len(df) else df[y_col]
            if isinstance(bar_data, pd.Series):
                ax.bar(range(len(bar_data)), bar_data.values, color='#0066CC')
                ax.set_xticks(range(len(bar_data)))
                ax.set_xticklabels(bar_data.index, rotation=45, ha='right', fontsize=8)
            else:
                ax.bar(range(len(df)), df[y_col], color='#0066CC')
                ax.set_xticks(range(len(df)))
                ax.set_xticklabels([str(x) for x in df[x_col]], rotation=45, ha='right', fontsize=8)
        
        ax.set_xlabel(x_col, fontsize=9)
        ax.set_ylabel(y_col, fontsize=9)
        ax.grid(True, alpha=0.3, axis='y')
        ax.tick_params(labelsize=8)
    
    def _create_scatter_chart(self, ax, df: pd.DataFrame, x_col: str, y_col: str, 
                             color_by: Optional[str], title: str):
        """Create a scatter chart."""
        if not x_col or not y_col:
            return
        
        if color_by and color_by in df.columns:
            # Color by category
            categories = df[color_by].unique()
            for i, cat in enumerate(categories):
                mask = df[color_by] == cat
                ax.scatter(df.loc[mask, x_col], df.loc[mask, y_col], 
                          label=str(cat), alpha=0.6, s=50)
            ax.legend(fontsize=8, loc='best')
        else:
            ax.scatter(df[x_col], df[y_col], alpha=0.6, s=50, color='#0066CC')
        
        ax.set_xlabel(x_col, fontsize=9)
        ax.set_ylabel(y_col, fontsize=9)
        ax.grid(True, alpha=0.3)
        ax.tick_params(labelsize=8)
    
    def _create_pie_chart(self, ax, df: pd.DataFrame, x_col: str, y_col: str, title: str):
        """Create a pie chart."""
        if not x_col or not y_col:
            return
        
        # Aggregate data
        pie_data = df.groupby(x_col)[y_col].sum()
        
        # Limit to top 8 for readability
        if len(pie_data) > 8:
            top_data = pie_data.nlargest(8)
            others_sum = pie_data.sum() - top_data.sum()
            pie_data = pd.concat([top_data, pd.Series([others_sum], index=['Others'])])
        
        colors = plt.cm.Set3(np.linspace(0, 1, len(pie_data)))
        ax.pie(pie_data.values, labels=pie_data.index, autopct='%1.1f%%', 
               colors=colors, startangle=90, textprops={'fontsize': 8})
        ax.axis('equal')
    
    def _create_heatmap(self, ax, df: pd.DataFrame, x_col: str, y_col: str, 
                       z_col: Optional[str], title: str):
        """Create a heatmap."""
        if not x_col or not y_col:
            return
        
        try:
            # Create pivot table
            if z_col and z_col in df.columns:
                pivot = df.pivot_table(values=z_col, index=y_col, columns=x_col, aggfunc='mean')
            else:
                # Count occurrences
                pivot = pd.crosstab(df[y_col], df[x_col])
            
            if pivot.empty:
                ax.text(0.5, 0.5, "No data for heatmap", ha='center', va='center', transform=ax.transAxes)
                return
            
            im = ax.imshow(pivot.values, cmap='YlOrRd', aspect='auto')
            ax.set_xticks(range(len(pivot.columns)))
            ax.set_xticklabels([str(c) for c in pivot.columns], rotation=45, ha='right', fontsize=7)
            ax.set_yticks(range(len(pivot.index)))
            ax.set_yticklabels([str(r) for r in pivot.index], fontsize=7)
            ax.set_xlabel(x_col, fontsize=9)
            ax.set_ylabel(y_col, fontsize=9)
            
            # Add colorbar
            fig = ax.get_figure()
            if fig:
                fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
        except Exception as e:
            ax.text(0.5, 0.5, f"Error creating heatmap:\n{str(e)}", 
                   ha='center', va='center', transform=ax.transAxes, fontsize=8)
    
    def _create_histogram(self, ax, df: pd.DataFrame, x_col: str, title: str):
        """Create a histogram."""
        if not x_col:
            return
        
        ax.hist(df[x_col].dropna(), bins=min(20, len(df[x_col].unique())), 
               color='#0066CC', edgecolor='black', alpha=0.7)
        ax.set_xlabel(x_col, fontsize=9)
        ax.set_ylabel('Frequency', fontsize=9)
        ax.grid(True, alpha=0.3, axis='y')
        ax.tick_params(labelsize=8)
    
    def _create_boxplot(self, ax, df: pd.DataFrame, x_col: str, y_col: str, title: str):
        """Create a boxplot."""
        if not x_col or not y_col:
            return
        
        if x_col in df.columns and y_col in df.columns:
            # Group by x_col if it's categorical
            if df[x_col].dtype == 'object' or df[x_col].nunique() < 10:
                groups = [group[y_col].dropna().values for name, group in df.groupby(x_col)]
                ax.boxplot(groups, labels=df.groupby(x_col).groups.keys())
                ax.set_xticklabels(ax.get_xticklabels(), rotation=45, ha='right', fontsize=8)
            else:
                ax.boxplot(df[y_col].dropna().values)
        else:
            ax.boxplot(df[y_col].dropna().values)
        
        ax.set_xlabel(x_col, fontsize=9)
        ax.set_ylabel(y_col, fontsize=9)
        ax.grid(True, alpha=0.3, axis='y')
        ax.tick_params(labelsize=8)
