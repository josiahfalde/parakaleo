import plotly.express as px
import plotly.graph_objects as go
import plotly.figure_factory as ff
from plotly.subplots import make_subplots
import pandas as pd
from typing import List, Optional

class VisualizationTemplates:
    """Creates designer-friendly visualization templates."""
    
    def __init__(self):
        self.mobile_layout = {
            'font': {'size': 12},
            'margin': {'l': 50, 'r': 50, 't': 80, 'b': 50},
            'height': 500,
            'paper_bgcolor': 'white',
            'plot_bgcolor': 'white'
        }
    
    def create_bar_line_chart(self, df: pd.DataFrame, x_col: str, y_col: str, 
                             chart_type: str, color_palette: List[str]) -> go.Figure:
        """Create bar or line chart."""
        if chart_type == "bar_chart":
            # Aggregate data if necessary
            if df[x_col].dtype == 'object':
                agg_df = df.groupby(x_col)[y_col].sum().reset_index()
            else:
                agg_df = df
            
            fig = px.bar(
                agg_df, 
                x=x_col, 
                y=y_col,
                color_discrete_sequence=color_palette
            )
            
            # Add hover template
            fig.update_traces(
                hovertemplate=f"<b>{x_col}</b>: %{{x}}<br><b>{y_col}</b>: %{{y}}<extra></extra>"
            )
            
        else:  # line_chart
            fig = px.line(
                df, 
                x=x_col, 
                y=y_col,
                color_discrete_sequence=color_palette
            )
            
            # Enhance line styling
            fig.update_traces(
                line=dict(width=3),
                hovertemplate=f"<b>{x_col}</b>: %{{x}}<br><b>{y_col}</b>: %{{y}}<extra></extra>"
            )
        
        # Apply mobile-friendly styling
        fig.update_layout(**self.mobile_layout)
        fig.update_layout(
            title=f"{chart_type.replace('_', ' ').title()}: {y_col} by {x_col}",
            xaxis_title=x_col,
            yaxis_title=y_col
        )
        
        return fig
    
    def create_scatter_plot(self, df: pd.DataFrame, x_col: str, y_col: str, 
                           color_col: Optional[str], color_palette: List[str]) -> go.Figure:
        """Create scatter plot."""
        if color_col:
            fig = px.scatter(
                df, 
                x=x_col, 
                y=y_col, 
                color=color_col,
                color_discrete_sequence=color_palette
            )
        else:
            fig = px.scatter(
                df, 
                x=x_col, 
                y=y_col,
                color_discrete_sequence=color_palette
            )
        
        # Enhance markers
        fig.update_traces(
            marker=dict(size=8, opacity=0.7),
            hovertemplate=f"<b>{x_col}</b>: %{{x}}<br><b>{y_col}</b>: %{{y}}<extra></extra>"
        )
        
        fig.update_layout(**self.mobile_layout)
        fig.update_layout(
            title=f"Scatter Plot: {y_col} vs {x_col}",
            xaxis_title=x_col,
            yaxis_title=y_col
        )
        
        return fig
    
    def create_pie_chart(self, df: pd.DataFrame, category_col: str, 
                        value_col: Optional[str], color_palette: List[str]) -> go.Figure:
        """Create pie chart."""
        if value_col:
            # Aggregate by category and value
            pie_data = df.groupby(category_col)[value_col].sum().reset_index()
            fig = px.pie(
                pie_data, 
                values=value_col, 
                names=category_col,
                color_discrete_sequence=color_palette
            )
        else:
            # Count occurrences
            pie_data = df[category_col].value_counts().reset_index()
            pie_data.columns = [category_col, 'count']
            fig = px.pie(
                pie_data, 
                values='count', 
                names=category_col,
                color_discrete_sequence=color_palette
            )
        
        fig.update_traces(
            textposition='inside',
            textinfo='percent+label',
            hovertemplate="<b>%{label}</b><br>Value: %{value}<br>Percentage: %{percent}<extra></extra>"
        )
        
        fig.update_layout(**self.mobile_layout)
        fig.update_layout(
            title=f"Distribution of {category_col}",
            showlegend=True
        )
        
        return fig
    
    def create_histogram(self, df: pd.DataFrame, col: str, bins: int, 
                        color_palette: List[str]) -> go.Figure:
        """Create histogram."""
        fig = px.histogram(
            df, 
            x=col, 
            nbins=bins,
            color_discrete_sequence=color_palette
        )
        
        fig.update_traces(
            hovertemplate=f"<b>{col}</b>: %{{x}}<br><b>Count</b>: %{{y}}<extra></extra>"
        )
        
        fig.update_layout(**self.mobile_layout)
        fig.update_layout(
            title=f"Distribution of {col}",
            xaxis_title=col,
            yaxis_title="Count"
        )
        
        return fig
    
    def create_box_plot(self, df: pd.DataFrame, y_col: str, x_col: Optional[str], 
                       color_palette: List[str]) -> go.Figure:
        """Create box plot."""
        if x_col:
            fig = px.box(
                df, 
                x=x_col, 
                y=y_col,
                color_discrete_sequence=color_palette
            )
        else:
            fig = px.box(
                df, 
                y=y_col,
                color_discrete_sequence=color_palette
            )
        
        fig.update_traces(
            hovertemplate=f"<b>{y_col}</b><br>Q1: %{{q1}}<br>Median: %{{median}}<br>Q3: %{{q3}}<extra></extra>"
        )
        
        fig.update_layout(**self.mobile_layout)
        fig.update_layout(
            title=f"Box Plot of {y_col}" + (f" by {x_col}" if x_col else ""),
            xaxis_title=x_col if x_col else "",
            yaxis_title=y_col
        )
        
        return fig
    
    def create_heatmap(self, df: pd.DataFrame, color_palette: List[str]) -> go.Figure:
        """Create correlation heatmap."""
        # Calculate correlation matrix
        corr_matrix = df.corr()
        
        # Create heatmap
        fig = go.Figure(data=go.Heatmap(
            z=corr_matrix.values,
            x=corr_matrix.columns,
            y=corr_matrix.columns,
            colorscale='RdBu',
            zmid=0,
            hovertemplate="<b>%{x}</b> vs <b>%{y}</b><br>Correlation: %{z:.2f}<extra></extra>"
        ))
        
        fig.update_layout(**self.mobile_layout)
        fig.update_layout(
            title="Correlation Heatmap",
            xaxis_title="Variables",
            yaxis_title="Variables"
        )
        
        return fig
