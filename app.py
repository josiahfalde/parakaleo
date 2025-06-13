import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import base64
import io
from datetime import datetime
import json

# Import utility modules
from utils.data_processor import DataProcessor
from utils.visualization_templates import VisualizationTemplates
from utils.export_handler import ExportHandler

# Configure page
st.set_page_config(
    page_title="Designer Data Viz Tool",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'data' not in st.session_state:
    st.session_state.data = None
if 'filtered_data' not in st.session_state:
    st.session_state.filtered_data = None
if 'current_viz' not in st.session_state:
    st.session_state.current_viz = None
if 'color_palette' not in st.session_state:
    st.session_state.color_palette = px.colors.qualitative.Set3

# Initialize utility classes
data_processor = DataProcessor()
viz_templates = VisualizationTemplates()
export_handler = ExportHandler()

def main():
    # Header
    st.title("📊 Designer Data Viz Tool")
    st.markdown("*Create beautiful, shareable visualizations on the go*")
    
    # Mobile-friendly tabs
    tab1, tab2, tab3, tab4 = st.tabs(["📁 Data", "🔍 Explore", "🎨 Visualize", "📤 Export"])
    
    with tab1:
        data_upload_section()
    
    with tab2:
        if st.session_state.data is not None:
            data_exploration_section()
        else:
            st.info("Please upload data first in the Data tab.")
    
    with tab3:
        if st.session_state.data is not None:
            visualization_section()
        else:
            st.info("Please upload data first in the Data tab.")
    
    with tab4:
        if st.session_state.current_viz is not None:
            export_section()
        else:
            st.info("Please create a visualization first in the Visualize tab.")

def data_upload_section():
    st.header("Upload Your Data")
    
    # File uploader
    uploaded_file = st.file_uploader(
        "Choose a file",
        type=['csv', 'xlsx', 'xls'],
        help="Upload CSV or Excel files up to 200MB"
    )
    
    if uploaded_file is not None:
        try:
            with st.spinner("Processing your file..."):
                # Process the uploaded file
                df = data_processor.load_file(uploaded_file)
                st.session_state.data = df
                st.session_state.filtered_data = df.copy()
            
            st.success(f"✅ File uploaded successfully! {len(df)} rows, {len(df.columns)} columns")
            
            # Display basic info
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Rows", len(df))
            with col2:
                st.metric("Columns", len(df.columns))
            with col3:
                st.metric("Size", f"{uploaded_file.size / 1024:.1f} KB")
            
            # Data preview
            st.subheader("Data Preview")
            st.dataframe(df.head(10), use_container_width=True)
            
            # Column info
            st.subheader("Column Information")
            col_info = data_processor.get_column_info(df)
            st.dataframe(col_info, use_container_width=True)
            
        except Exception as e:
            st.error(f"Error processing file: {str(e)}")

def data_exploration_section():
    st.header("Explore Your Data")
    
    df = st.session_state.data
    
    # Data filtering section
    st.subheader("Filter Data")
    
    # Create filters based on column types
    filters = {}
    
    # Numeric columns
    numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
    if numeric_cols:
        st.write("**Numeric Filters:**")
        for col in numeric_cols[:3]:  # Limit to 3 for mobile
            min_val, max_val = float(df[col].min()), float(df[col].max())
            if min_val != max_val:
                filters[col] = st.slider(
                    f"{col}",
                    min_value=min_val,
                    max_value=max_val,
                    value=(min_val, max_val),
                    key=f"slider_{col}"
                )
    
    # Categorical columns
    categorical_cols = df.select_dtypes(include=['object']).columns.tolist()
    if categorical_cols:
        st.write("**Categorical Filters:**")
        for col in categorical_cols[:3]:  # Limit to 3 for mobile
            unique_values = df[col].dropna().unique().tolist()
            if len(unique_values) <= 20:  # Only show if reasonable number of options
                filters[col] = st.multiselect(
                    f"{col}",
                    options=unique_values,
                    default=unique_values,
                    key=f"multiselect_{col}"
                )
    
    # Apply filters
    filtered_df = data_processor.apply_filters(df, filters)
    st.session_state.filtered_data = filtered_df
    
    if len(filtered_df) != len(df):
        st.info(f"Filtered from {len(df)} to {len(filtered_df)} rows")
    
    # Quick stats
    st.subheader("Quick Statistics")
    if not filtered_df.empty:
        stats = data_processor.get_quick_stats(filtered_df)
        
        # Display stats in a mobile-friendly way
        for col, stat in stats.items():
            if stat['type'] == 'numeric':
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric(f"{col} Mean", f"{stat['mean']:.2f}")
                with col2:
                    st.metric(f"{col} Median", f"{stat['median']:.2f}")
                with col3:
                    st.metric(f"{col} Min", f"{stat['min']:.2f}")
                with col4:
                    st.metric(f"{col} Max", f"{stat['max']:.2f}")
    
    # Updated data preview
    st.subheader("Filtered Data Preview")
    st.dataframe(filtered_df.head(10), use_container_width=True)

def visualization_section():
    st.header("Create Visualizations")
    
    df = st.session_state.filtered_data
    
    if df.empty:
        st.warning("No data available after filtering.")
        return
    
    # Visualization type selection
    viz_type = st.selectbox(
        "Choose Visualization Type",
        ["Bar Chart", "Line Chart", "Scatter Plot", "Pie Chart", "Histogram", "Box Plot", "Heatmap"]
    )
    
    # Color palette selection
    st.subheader("Brand Colors")
    palette_options = {
        "Vibrant": px.colors.qualitative.Set1,
        "Pastel": px.colors.qualitative.Pastel1,
        "Bold": px.colors.qualitative.Bold,
        "Safe": px.colors.qualitative.Safe,
        "Designer": ["#FF6B6B", "#4ECDC4", "#45B7D1", "#96CEB4", "#FFEAA7", "#DDA0DD", "#98D8C8"]
    }
    
    selected_palette = st.selectbox("Select Color Palette", list(palette_options.keys()), index=6)
    st.session_state.color_palette = palette_options[selected_palette]
    
    # Show color preview
    color_preview = st.columns(len(st.session_state.color_palette[:7]))
    for i, color in enumerate(st.session_state.color_palette[:7]):
        with color_preview[i]:
            st.markdown(f"<div style='background-color: {color}; height: 30px; border-radius: 5px;'></div>", unsafe_allow_html=True)
    
    # Column selection based on visualization type
    numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
    categorical_cols = df.select_dtypes(include=['object']).columns.tolist()
    
    if viz_type in ["Bar Chart", "Line Chart"]:
        col1, col2 = st.columns(2)
        with col1:
            x_col = st.selectbox("X-axis", categorical_cols + numeric_cols)
        with col2:
            y_col = st.selectbox("Y-axis", numeric_cols)
        
        if x_col and y_col:
            fig = viz_templates.create_bar_line_chart(df, x_col, y_col, viz_type.lower().replace(" ", "_"), st.session_state.color_palette)
    
    elif viz_type == "Scatter Plot":
        col1, col2, col3 = st.columns(3)
        with col1:
            x_col = st.selectbox("X-axis", numeric_cols)
        with col2:
            y_col = st.selectbox("Y-axis", numeric_cols)
        with col3:
            color_col = st.selectbox("Color by", [None] + categorical_cols)
        
        if x_col and y_col:
            fig = viz_templates.create_scatter_plot(df, x_col, y_col, color_col, st.session_state.color_palette)
    
    elif viz_type == "Pie Chart":
        if categorical_cols:
            category_col = st.selectbox("Category", categorical_cols)
            value_col = st.selectbox("Values (optional)", [None] + numeric_cols)
            
            if category_col:
                fig = viz_templates.create_pie_chart(df, category_col, value_col, st.session_state.color_palette)
        else:
            st.warning("No categorical columns available for pie chart.")
            return
    
    elif viz_type == "Histogram":
        if numeric_cols:
            col = st.selectbox("Column", numeric_cols)
            bins = st.slider("Number of bins", 10, 50, 20)
            
            if col:
                fig = viz_templates.create_histogram(df, col, bins, st.session_state.color_palette)
        else:
            st.warning("No numeric columns available for histogram.")
            return
    
    elif viz_type == "Box Plot":
        if numeric_cols:
            y_col = st.selectbox("Y-axis", numeric_cols)
            x_col = st.selectbox("Group by (optional)", [None] + categorical_cols)
            
            if y_col:
                fig = viz_templates.create_box_plot(df, y_col, x_col, st.session_state.color_palette)
        else:
            st.warning("No numeric columns available for box plot.")
            return
    
    elif viz_type == "Heatmap":
        if len(numeric_cols) >= 2:
            selected_cols = st.multiselect("Select columns", numeric_cols, default=numeric_cols[:5])
            
            if len(selected_cols) >= 2:
                fig = viz_templates.create_heatmap(df[selected_cols], st.session_state.color_palette)
            else:
                st.warning("Please select at least 2 columns.")
                return
        else:
            st.warning("Need at least 2 numeric columns for heatmap.")
            return
    
    # Display the visualization
    if 'fig' in locals():
        # Customize for mobile
        fig.update_layout(
            height=500,
            font=dict(size=12),
            margin=dict(l=50, r=50, t=50, b=50)
        )
        
        st.plotly_chart(fig, use_container_width=True)
        st.session_state.current_viz = fig
        
        # Add title and description
        st.subheader("Customize Your Visualization")
        chart_title = st.text_input("Chart Title", value=f"{viz_type} - {datetime.now().strftime('%Y-%m-%d')}")
        chart_description = st.text_area("Description (optional)", placeholder="Add a description for your visualization...")
        
        if chart_title:
            fig.update_layout(title=chart_title)
            st.session_state.current_viz = fig

def export_section():
    st.header("Export & Share")
    
    fig = st.session_state.current_viz
    
    if fig is None:
        st.warning("No visualization to export.")
        return
    
    # Export options
    st.subheader("Export Options")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # PNG Export
        if st.button("📷 Download PNG", use_container_width=True):
            png_bytes = export_handler.fig_to_png(fig)
            st.download_button(
                label="Download PNG",
                data=png_bytes,
                file_name=f"visualization_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png",
                mime="image/png"
            )
    
    with col2:
        # SVG Export
        if st.button("🎨 Download SVG", use_container_width=True):
            svg_string = export_handler.fig_to_svg(fig)
            st.download_button(
                label="Download SVG",
                data=svg_string,
                file_name=f"visualization_{datetime.now().strftime('%Y%m%d_%H%M%S')}.svg",
                mime="image/svg+xml"
            )
    
    # HTML Export for sharing
    st.subheader("Share Your Visualization")
    
    if st.button("🔗 Generate Shareable Link", use_container_width=True):
        html_string = export_handler.fig_to_html(fig)
        
        # Create a shareable HTML file
        b64_html = base64.b64encode(html_string.encode()).decode()
        href = f"data:text/html;base64,{b64_html}"
        
        st.markdown(f"""
        <a href="{href}" download="visualization_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html">
            <button style="background-color: #FF6B6B; color: white; padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer; width: 100%;">
                📁 Download Interactive HTML
            </button>
        </a>
        """, unsafe_allow_html=True)
        
        st.info("💡 The HTML file contains your interactive visualization that can be shared via email or hosted on any website.")
    
    # Display current visualization one more time
    st.subheader("Current Visualization")
    st.plotly_chart(fig, use_container_width=True)

if __name__ == "__main__":
    main()
