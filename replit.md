# Medical Clinic Charting Application

## Overview

This is a comprehensive Streamlit-based medical clinic charting application designed for mobile medical missions in the Dominican Republic and Haiti. The system provides location-based patient numbering (DR00001, H00001), comprehensive lab testing (urinalysis, glucose, pregnancy), preset medication management with lab-dependent prescribing, and multi-role interfaces for triage nurses, doctors, lab technicians, pharmacy staff, and administrators.

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
- **Main Streamlit Application**: Entry point with role-based interface selection
- **Location Management**: Setup and selection of clinic locations (DR/Haiti with city-based organization)
- **Multi-Role Interfaces**: Triage nurse, doctor, lab tech, pharmacy, and admin roles
- **Mobile-Optimized UI**: Custom CSS for touch interfaces and responsive design

### Database Layer (SQLite3)
- **Patient Management**: Location-based patient numbering (DR00001, H00001 format)
- **Visit Tracking**: Complete patient visit lifecycle from triage to completion
- **Lab Tests**: Comprehensive urinalysis, glucose, and pregnancy test management
- **Prescription System**: Preset medications with lab-dependent prescribing workflow
- **Location Organization**: Folder-based patient registry by country and city

### Clinical Workflow Components
- **Triage Interface**: Patient registration, vital signs capture, priority assignment
- **Doctor Interface**: Comprehensive consultation with preset medication selection and lab ordering
- **Lab Interface**: Detailed test processing with full urinalysis parameters (leukocytes, nitrites, etc.)
- **Pharmacy Interface**: Prescription filling with "awaiting lab results" approval workflow
- **Admin Interface**: Medication management, daily reports, and clinic settings

### Preset Medication System
- **Pre-configured Medications**: Common clinic medications with dosages and categories
- **Lab-Dependent Prescribing**: Medications marked as requiring lab results before dispensing
- **Awaiting Lab Workflow**: Two-stage approval system for lab-dependent medications
- **Custom Medications**: Ability to add medications not in preset list

## Clinical Workflow

1. **Location Setup**: Select clinic location (Dominican Republic or Haiti with specific city)
2. **Patient Registration**: Triage nurse registers patient with location-based ID (DR00001, H00001)
3. **Vital Signs Collection**: Blood pressure, heart rate, temperature, weight, height recording
4. **Doctor Consultation**: Complete medical assessment with symptoms, diagnosis, treatment plan
5. **Lab Test Ordering**: Doctor orders urinalysis, glucose, or pregnancy tests as needed
6. **Prescription Management**: Select from preset medications with lab-dependent approval workflow
7. **Lab Processing**: Lab tech processes tests with detailed parameter entry (urinalysis components)
8. **Pharmacy Review**: Pharmacist reviews prescriptions, approves lab-dependent medications
9. **Medication Dispensing**: Final prescription filling and patient completion
10. **Administrative Oversight**: Daily reports, medication management, and system configuration

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

- June 15, 2025. Enhanced UI and settings management
  - Improved patient deletion system with working popup confirmation
  - Added comprehensive clinic settings with dark mode, language options, and session management
  - Optimized download button layout for better screen utilization
  - Removed redundant location displays and consolidated to navigation and sidebar
  - Enhanced deletion function with proper cascade handling for all related data
- June 13, 2025. Initial setup

## User Preferences

Preferred communication style: Simple, everyday language.