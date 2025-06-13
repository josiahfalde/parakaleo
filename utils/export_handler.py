import plotly.graph_objects as go
import plotly.io as pio
import base64
import io
from typing import Union

class ExportHandler:
    """Handles export functionality for visualizations."""
    
    def __init__(self):
        # Configure plotly for better exports
        pio.kaleido.scope.mathjax = None
    
    def fig_to_png(self, fig: go.Figure, width: int = 1200, height: int = 800) -> bytes:
        """Convert figure to PNG bytes."""
        try:
            # Update figure for export
            export_fig = go.Figure(fig)
            export_fig.update_layout(
                width=width,
                height=height,
                font=dict(size=14),
                margin=dict(l=80, r=80, t=100, b=80)
            )
            
            # Convert to PNG
            img_bytes = export_fig.to_image(format="png", width=width, height=height)
            return img_bytes
            
        except Exception as e:
            raise Exception(f"Error exporting PNG: {str(e)}")
    
    def fig_to_svg(self, fig: go.Figure, width: int = 1200, height: int = 800) -> str:
        """Convert figure to SVG string."""
        try:
            # Update figure for export
            export_fig = go.Figure(fig)
            export_fig.update_layout(
                width=width,
                height=height,
                font=dict(size=14),
                margin=dict(l=80, r=80, t=100, b=80)
            )
            
            # Convert to SVG
            svg_string = export_fig.to_image(format="svg", width=width, height=height).decode('utf-8')
            return svg_string
            
        except Exception as e:
            raise Exception(f"Error exporting SVG: {str(e)}")
    
    def fig_to_html(self, fig: go.Figure) -> str:
        """Convert figure to interactive HTML."""
        try:
            # Create a full HTML page with the interactive plot
            html_string = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <meta name="viewport" content="width=device-width, initial-scale=1">
                <title>Data Visualization</title>
                <style>
                    body {{
                        font-family: "Segoe UI", Tahoma, Geneva, Verdana, sans-serif;
                        margin: 0;
                        padding: 20px;
                        background-color: #f8f9fa;
                    }}
                    .container {{
                        max-width: 1200px;
                        margin: 0 auto;
                        background-color: white;
                        border-radius: 10px;
                        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                        padding: 20px;
                    }}
                    .header {{
                        text-align: center;
                        margin-bottom: 30px;
                        border-bottom: 2px solid #e9ecef;
                        padding-bottom: 20px;
                    }}
                    .header h1 {{
                        color: #333;
                        margin: 0;
                    }}
                    .header p {{
                        color: #666;
                        margin: 10px 0 0 0;
                    }}
                    .chart-container {{
                        width: 100%;
                        height: 600px;
                    }}
                    @media (max-width: 768px) {{
                        body {{
                            padding: 10px;
                        }}
                        .container {{
                            padding: 15px;
                        }}
                        .chart-container {{
                            height: 400px;
                        }}
                    }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>📊 Data Visualization</h1>
                        <p>Created with Designer Data Viz Tool</p>
                    </div>
                    <div class="chart-container">
                        {fig.to_html(include_plotlyjs='cdn', div_id="chart", config={{'responsive': True, 'displayModeBar': True}})}
                    </div>
                </div>
                
                <script>
                    // Make chart responsive
                    window.addEventListener('resize', function() {{
                        Plotly.Plots.resize('chart');
                    }});
                </script>
            </body>
            </html>
            """
            
            return html_string
            
        except Exception as e:
            raise Exception(f"Error exporting HTML: {str(e)}")
    
    def create_download_link(self, data: Union[str, bytes], filename: str, 
                           mime_type: str) -> str:
        """Create a download link for data."""
        if isinstance(data, str):
            b64_data = base64.b64encode(data.encode()).decode()
        else:
            b64_data = base64.b64encode(data).decode()
        
        href = f"data:{mime_type};base64,{b64_data}"
        return href
