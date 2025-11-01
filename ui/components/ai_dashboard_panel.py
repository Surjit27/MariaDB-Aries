"""
AI Dashboard Panel
Main UI component for displaying AI-generated dashboards
"""

import tkinter as tk
import ttkbootstrap as ttk
from tkinter import messagebox, simpledialog
import threading
import os
import sys

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from ai.dashboard_analyzer import DashboardAnalyzer
from ui.components.visualization_engine import VisualizationEngine

class AIDashboardPanel(ttk.Frame):
    """Panel for displaying AI-generated dashboards."""
    
    def __init__(self, parent, db_manager=None, ai_integration=None):
        """Initialize the dashboard panel."""
        super().__init__(parent)
        self.db_manager = db_manager
        self.ai_integration = ai_integration
        self.current_query = ""
        self.current_columns = []
        self.current_data = []
        
        # Initialize components
        api_key = os.getenv('GEMINI_API_KEY', '')
        self.dashboard_analyzer = DashboardAnalyzer(api_key)
        self.viz_engine = VisualizationEngine()
        
        self.create_widgets()
    
    def create_widgets(self):
        """Create the dashboard UI."""
        # Header frame
        header_frame = ttk.Frame(self)
        header_frame.pack(fill=tk.X, padx=10, pady=10)
        
        title_label = ttk.Label(header_frame, text="🤖 AI Dashboard Builder", 
                               font=("Arial", 16, "bold"))
        title_label.pack(side=tk.LEFT, padx=(0, 20))
        
        subtitle_label = ttk.Label(header_frame, 
                                   text="Automatically generate visualizations from your SQL queries", 
                                   font=("Arial", 10), foreground="#666666")
        subtitle_label.pack(side=tk.LEFT)
        
        # Toolbar
        toolbar_frame = ttk.Frame(self)
        toolbar_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.generate_btn = ttk.Button(toolbar_frame, text="🤖 Generate Dashboard with AI", 
                                      command=self.generate_dashboard,
                                      bootstyle="primary")
        self.generate_btn.pack(side=tk.LEFT, padx=5)
        
        self.customize_btn = ttk.Button(toolbar_frame, text="⚙️ Customize Visualization", 
                                        command=self.customize_visualization,
                                        state=tk.DISABLED)
        self.customize_btn.pack(side=tk.LEFT, padx=5)
        
        self.refresh_btn = ttk.Button(toolbar_frame, text="🔄 Refresh", 
                                     command=self.refresh_dashboard,
                                     state=tk.DISABLED)
        self.refresh_btn.pack(side=tk.LEFT, padx=5)
        
        ttk.Separator(toolbar_frame, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=10)
        
        self.export_btn = ttk.Button(toolbar_frame, text="💾 Export Dashboard", 
                                    command=self.export_dashboard,
                                    state=tk.DISABLED)
        self.export_btn.pack(side=tk.LEFT, padx=5)
        
        # Main content area with scrollable canvas
        self.create_scrollable_area()
        
        # Status bar
        self.status_label = ttk.Label(self, text="Ready - No dashboard generated yet", 
                                      font=("Arial", 9), foreground="#666666")
        self.status_label.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=5)
    
    def create_scrollable_area(self):
        """Create scrollable area for dashboard content."""
        # Create canvas and scrollbar
        canvas_frame = ttk.Frame(self)
        canvas_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.canvas = tk.Canvas(canvas_frame, bg="#ffffff")
        scrollbar_y = ttk.Scrollbar(canvas_frame, orient=tk.VERTICAL, command=self.canvas.yview)
        scrollbar_x = ttk.Scrollbar(canvas_frame, orient=tk.HORIZONTAL, command=self.canvas.xview)
        
        self.canvas.configure(yscrollcommand=scrollbar_y.set, xscrollcommand=scrollbar_x.set)
        
        # Pack scrollbars
        scrollbar_y.pack(side=tk.RIGHT, fill=tk.Y)
        scrollbar_x.pack(side=tk.BOTTOM, fill=tk.X)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Create scrollable frame inside canvas
        self.scrollable_frame = ttk.Frame(self.canvas)
        self.canvas_window = self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        
        # Bind scroll events
        self.scrollable_frame.bind("<Configure>", self._on_frame_configure)
        self.canvas.bind("<Configure>", self._on_canvas_configure)
        
        # Mouse wheel scrolling
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        
        # Empty state
        self.show_empty_state()
    
    def _on_frame_configure(self, event):
        """Update scroll region when frame size changes."""
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
    
    def _on_canvas_configure(self, event):
        """Update canvas window width when canvas size changes."""
        canvas_width = event.width
        self.canvas.itemconfig(self.canvas_window, width=canvas_width)
    
    def _on_mousewheel(self, event):
        """Handle mouse wheel scrolling."""
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
    
    def show_empty_state(self):
        """Show empty state when no dashboard is generated."""
        # Clear existing widgets
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        
        empty_frame = ttk.Frame(self.scrollable_frame)
        empty_frame.pack(expand=True, fill=tk.BOTH, pady=50)
        
        empty_label = ttk.Label(empty_frame, 
                                text="📊 No Dashboard Generated Yet\n\n"
                                     "1. Write and run a SQL query in the SQL Editor\n"
                                     "2. Click 'Generate Dashboard with AI' to automatically create visualizations",
                                font=("Arial", 12),
                                justify=tk.CENTER,
                                foreground="#999999")
        empty_label.pack(expand=True)
    
    def set_query_results(self, query: str, columns: list, data: list):
        """Set the current query results for dashboard generation."""
        self.current_query = query
        self.current_columns = columns
        self.current_data = data
    
    def generate_dashboard(self):
        """Generate dashboard from current query results."""
        if not self.current_data or not self.current_columns:
            messagebox.showwarning("No Data", 
                                 "No query results available.\n\n"
                                 "Please run a SQL query first and then generate the dashboard.")
            return
        
        if not self.dashboard_analyzer.is_available():
            messagebox.showerror("AI Not Available", 
                                "AI dashboard generation requires a valid Gemini API key.\n\n"
                                "Please configure your API key in Settings.")
            return
        
        # Ask for optional user instruction
        user_instruction = simpledialog.askstring(
            "Dashboard Customization",
            "Enter optional instructions for the dashboard (e.g., 'focus on sales trends'):\n"
            "(Leave empty for automatic analysis)",
            parent=self
        ) or ""
        
        # Update status
        self.status_label.config(text="🔄 Analyzing data and generating visualizations...")
        self.generate_btn.config(state=tk.DISABLED)
        
        # Run analysis in separate thread to avoid blocking UI
        def run_analysis():
            try:
                result = self.dashboard_analyzer.analyze_and_suggest_visualizations(
                    self.current_query,
                    self.current_columns,
                    self.current_data,
                    user_instruction
                )
                
                # Update UI in main thread - capture result in lambda default parameter
                self.after(0, lambda r=result: self._display_dashboard(r))
                
            except Exception as e:
                # Capture error message in lambda default parameter to avoid closure issues
                error_msg = str(e)
                self.after(0, lambda msg=error_msg: self._handle_analysis_error(msg))
        
        thread = threading.Thread(target=run_analysis, daemon=True)
        thread.start()
    
    def _display_dashboard(self, result: dict):
        """Display the generated dashboard."""
        self.generate_btn.config(state=tk.NORMAL)
        self.customize_btn.config(state=tk.NORMAL)
        self.refresh_btn.config(state=tk.NORMAL)
        self.export_btn.config(state=tk.NORMAL)
        
        if not result.get('success'):
            error_msg = result.get('error', 'Unknown error occurred')
            messagebox.showerror("Analysis Error", f"Failed to analyze data: {error_msg}")
            self.status_label.config(text="❌ Failed to generate dashboard")
            return
        
        # Clear existing widgets
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        
        # Display AI Plan Summary
        summary_frame = ttk.LabelFrame(self.scrollable_frame, text="🧩 AI Plan Summary", padding=15)
        summary_frame.pack(fill=tk.X, padx=10, pady=10)
        
        summary_text = result.get('summary', 'No summary available')
        summary_label = ttk.Label(summary_frame, text=summary_text, 
                                 font=("Arial", 10), wraplength=800, justify=tk.LEFT)
        summary_label.pack(anchor=tk.W)
        
        # Display insights if available
        insights = result.get('insights', [])
        if insights:
            insights_frame = ttk.LabelFrame(self.scrollable_frame, text="💡 Key Insights", padding=15)
            insights_frame.pack(fill=tk.X, padx=10, pady=5)
            
            for insight in insights:
                insight_label = ttk.Label(insights_frame, text=f"• {insight}", 
                                         font=("Arial", 9), foreground="#0066CC",
                                         wraplength=800, justify=tk.LEFT)
                insight_label.pack(anchor=tk.W, pady=2)
        
        # Display visualizations
        plots = result.get('plots', [])
        if not plots:
            no_plots_label = ttk.Label(self.scrollable_frame, 
                                      text="No visualizations were suggested.", 
                                      font=("Arial", 11), foreground="#999999")
            no_plots_label.pack(pady=50)
            self.status_label.config(text="⚠️ No visualizations generated")
            return
        
        # Create grid for charts
        charts_frame = ttk.LabelFrame(self.scrollable_frame, text="📈 Visualizations", padding=10)
        charts_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create a grid layout (2 columns)
        rows = (len(plots) + 1) // 2
        for i, plot_config in enumerate(plots):
            row = i // 2
            col = i % 2
            
            # Create chart frame
            chart_frame = ttk.Frame(charts_frame)
            chart_frame.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")
            
            # Create chart
            try:
                chart_type = plot_config.get('type', 'bar')
                fig, canvas = self.viz_engine.create_chart(
                    chart_type,
                    self.current_data,
                    self.current_columns,
                    plot_config,
                    chart_frame
                )
                
                if canvas:
                    canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
                
                # Add description label
                desc = plot_config.get('description', '')
                if desc:
                    desc_label = ttk.Label(chart_frame, text=desc, 
                                          font=("Arial", 8), foreground="#666666",
                                          wraplength=400)
                    desc_label.pack(pady=(5, 0))
                
            except Exception as e:
                error_label = ttk.Label(chart_frame, 
                                       text=f"Error creating chart: {str(e)}", 
                                       foreground="red")
                error_label.pack()
                print(f"Error creating chart {i}: {e}")
        
        # Configure grid weights
        charts_frame.grid_columnconfigure(0, weight=1)
        charts_frame.grid_columnconfigure(1, weight=1)
        
        # Update status
        self.status_label.config(text=f"✅ Dashboard generated with {len(plots)} visualizations")
        
        # Update scroll region
        self.scrollable_frame.update_idletasks()
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
    
    def _handle_analysis_error(self, error_msg: str):
        """Handle analysis errors."""
        self.generate_btn.config(state=tk.NORMAL)
        messagebox.showerror("Analysis Error", f"Failed to analyze data: {error_msg}")
        self.status_label.config(text="❌ Failed to generate dashboard")
    
    def customize_visualization(self):
        """Open customization dialog."""
        messagebox.showinfo("Coming Soon", 
                           "Visualization customization feature coming soon!\n\n"
                           "You can refresh the dashboard with new instructions.")
    
    def refresh_dashboard(self):
        """Refresh the dashboard with new analysis."""
        self.generate_dashboard()
    
    def export_dashboard(self):
        """Export dashboard as image or report."""
        from tkinter import filedialog
        
        filename = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[("PNG files", "*.png"), ("PDF files", "*.pdf"), ("All files", "*.*")],
            title="Export Dashboard"
        )
        
        if filename:
            messagebox.showinfo("Coming Soon", 
                               "Dashboard export feature coming soon!\n\n"
                               "This will export all visualizations to a single file.")
