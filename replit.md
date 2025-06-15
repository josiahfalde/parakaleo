# Medical Clinic Charting Application

## Overview

This is a Streamlit-based medical clinic charting application designed for mobile and tablet use. The application provides a user-friendly interface for medical professionals to manage patient data, create visualizations, and generate reports. The system is built with Python/Streamlit and includes data processing capabilities with support for Excel and CSV file formats.

## System Architecture

### Frontend Architecture
- **Framework**: Streamlit web framework
- **Design**: Mobile-first responsive design with custom CSS
- **UI Components**: Custom styled buttons, forms, and cards optimized for touch interfaces
- **Layout**: Wide layout with collapsed sidebar for better mobile experience

### Backend Architecture
- **Runtime**: Python 3.11
- **Web Server**: Streamlit server running on port 5000
- **Data Storage**: SQLite3 database for local data persistence
- **File Processing**: Pandas-based data processing with support for Excel (.xlsx, .xls) and CSV files

### Data Layer
- **Database**: SQLite3 for lightweight, serverless data storage
- **Data Processing**: Pandas DataFrames for data manipulation and analysis
- **File Support**: Excel (openpyxl, xlrd engines) and CSV with multiple encoding support (UTF-8, Latin-1)

## Key Components

### Core Application (`app.py`)
- Main Streamlit application entry point
- Mobile-optimized UI configuration
- Patient data management interface
- Custom CSS for responsive design

### Data Processing Module (`utils/data_processor.py`)
- **DataProcessor Class**: Handles file loading, data cleaning, and processing
- **File Loading**: Multi-format support (CSV, Excel) with error handling
- **Data Cleaning**: Automatic removal of empty rows/columns, column name standardization
- **Type Conversion**: Intelligent numeric data type detection and conversion

### Visualization System (`utils/visualization_templates.py`)
- **VisualizationTemplates Class**: Creates mobile-friendly charts and graphs
- **Chart Types**: Bar charts, line charts with customizable color palettes
- **Mobile Optimization**: Responsive layouts with appropriate font sizes and margins
- **Interactive Features**: Custom hover templates and styling

### Export Functionality (`utils/export_handler.py`)
- **ExportHandler Class**: Manages data and visualization exports
- **Format Support**: PNG, SVG, and HTML export options
- **Fallback System**: HTML export when Kaleido (PNG/SVG engine) is unavailable
- **Export Optimization**: Configurable dimensions and styling for different output formats

## Data Flow

1. **File Upload**: Users upload CSV or Excel files through Streamlit interface
2. **Data Processing**: DataProcessor loads and cleans the data, handling encoding issues
3. **Data Storage**: Processed data is stored in SQLite database for persistence
4. **Visualization**: VisualizationTemplates creates interactive charts from processed data
5. **Export**: ExportHandler converts visualizations to various formats for download

## External Dependencies

### Core Dependencies
- **Streamlit**: Web application framework and UI components
- **Pandas**: Data manipulation and analysis
- **SQLite3**: Built-in Python database interface
- **Plotly**: Interactive visualization library

### File Processing
- **openpyxl**: Modern Excel file (.xlsx) reading and writing
- **xlrd**: Legacy Excel file (.xls) support
- **kaleido**: Image export engine for Plotly (optional, with HTML fallback)

### Development Environment
- **UV**: Modern Python package manager for dependency management
- **Nix**: Reproducible development environment

## Deployment Strategy

### Platform
- **Target**: Replit Autoscale deployment
- **Runtime**: Python 3.11 with Nix package management
- **Port Configuration**: Internal port 5000, external port 80

### Workflow Management
- **Parallel Execution**: Streamlit server and package installation run concurrently
- **Package Management**: Automated installation of visualization dependencies (plotly, openpyxl, xlrd, kaleido)
- **Server Configuration**: Headless server mode optimized for web deployment

### Configuration
- **Mobile Optimization**: Responsive design prioritizing mobile and tablet interfaces
- **Performance**: Lightweight SQLite database for fast local operations
- **Reliability**: Multiple encoding support and fallback export methods

## Changelog

- June 13, 2025. Initial setup

## User Preferences

Preferred communication style: Simple, everyday language.