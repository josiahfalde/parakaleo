import pandas as pd
import streamlit as st
from typing import Dict, Any, Optional

class DataProcessor:
    """Handles data loading, processing, and filtering operations."""
    
    def load_file(self, uploaded_file) -> pd.DataFrame:
        """Load data from uploaded file."""
        file_extension = uploaded_file.name.split('.')[-1].lower()
        
        try:
            if file_extension == 'csv':
                # Try different encodings
                try:
                    df = pd.read_csv(uploaded_file, encoding='utf-8')
                except UnicodeDecodeError:
                    uploaded_file.seek(0)
                    df = pd.read_csv(uploaded_file, encoding='latin-1')
            
            elif file_extension in ['xlsx', 'xls']:
                df = pd.read_excel(uploaded_file, engine='openpyxl' if file_extension == 'xlsx' else 'xlrd')
            
            else:
                raise ValueError(f"Unsupported file format: {file_extension}")
            
            # Basic data cleaning
            df = self._clean_data(df)
            
            return df
            
        except Exception as e:
            raise Exception(f"Error loading file: {str(e)}")
    
    def _clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Perform basic data cleaning operations."""
        # Remove completely empty rows and columns
        df = df.dropna(how='all').dropna(axis=1, how='all')
        
        # Clean column names
        df.columns = df.columns.astype(str).str.strip()
        
        # Convert numeric columns
        for col in df.columns:
            if df[col].dtype == 'object':
                # Try to convert to numeric
                try:
                    # Remove common non-numeric characters
                    cleaned_series = df[col].astype(str).str.replace(r'[^\d.-]', '', regex=True)
                    numeric_series = pd.to_numeric(cleaned_series, errors='coerce')
                    
                    # If more than 50% of values are numeric, convert the column
                    if numeric_series.notna().sum() / len(df) > 0.5:
                        df[col] = numeric_series
                except:
                    pass
        
        return df
    
    def get_column_info(self, df: pd.DataFrame) -> pd.DataFrame:
        """Get information about columns in the dataframe."""
        info_data = []
        
        for col in df.columns:
            dtype = str(df[col].dtype)
            non_null_count = df[col].count()
            null_count = df[col].isnull().sum()
            unique_count = df[col].nunique()
            
            # Sample values
            sample_values = df[col].dropna().head(3).tolist()
            sample_str = ', '.join([str(x)[:20] + '...' if len(str(x)) > 20 else str(x) for x in sample_values])
            
            info_data.append({
                'Column': col,
                'Type': dtype,
                'Non-Null': non_null_count,
                'Null': null_count,
                'Unique': unique_count,
                'Sample Values': sample_str
            })
        
        return pd.DataFrame(info_data)
    
    def apply_filters(self, df: pd.DataFrame, filters: Dict[str, Any]) -> pd.DataFrame:
        """Apply filters to the dataframe."""
        filtered_df = df.copy()
        
        for col, filter_value in filters.items():
            if col in df.columns:
                if isinstance(filter_value, tuple) and len(filter_value) == 2:
                    # Numeric range filter
                    min_val, max_val = filter_value
                    filtered_df = filtered_df[
                        (filtered_df[col] >= min_val) & (filtered_df[col] <= max_val)
                    ]
                elif isinstance(filter_value, list):
                    # Categorical filter
                    if filter_value:  # Only apply if list is not empty
                        filtered_df = filtered_df[filtered_df[col].isin(filter_value)]
        
        return filtered_df
    
    def get_quick_stats(self, df: pd.DataFrame) -> Dict[str, Dict[str, Any]]:
        """Get quick statistics for numeric columns."""
        stats = {}
        
        numeric_cols = df.select_dtypes(include=['number']).columns
        
        for col in numeric_cols:
            if not df[col].empty:
                stats[col] = {
                    'type': 'numeric',
                    'mean': df[col].mean(),
                    'median': df[col].median(),
                    'min': df[col].min(),
                    'max': df[col].max(),
                    'std': df[col].std()
                }
        
        return stats
