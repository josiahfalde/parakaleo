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

- June 16, 2025. Prescription UI and family workflow improvements
  - Restored prescription checkbox functionality with popup options appearing after medication selection
  - Fixed family consultation workflow to process all family members (parent and children) sequentially 
  - Enhanced family consultation interface with progress tracking and member status display
  - Improved error handling with user-friendly messages for session state issues
  - Enhanced pharmacy/lab styling with better readability for timestamps and patient IDs
  - Updated pharmacy references to "Pharmacy/Lab Station" throughout application
  - Added automatic navigation back to consultation tab for smoother family workflow
  - Fixed patient history display to extend outside patient management section
  - Streamlined triage interface by removing medical history and allergies fields (moved to doctor consultation)
  - Enhanced prescription checkbox system to show popup fields immediately when medication is checked
  - Implemented autosave for consultation documents eliminating need for manual save buttons
  - Removed back button from top left for cleaner interface design
  - Fixed family workflow navigation to automatically return to consultation tab for next member
  - Added comprehensive lab results input system in pharmacy/lab with 10-parameter urinalysis, glucose testing, and pregnancy tests
  - Implemented detailed lab result forms with clinical interpretation and structured data entry
  - Removed filled prescription timestamps from display for cleaner interface
  - Enhanced lab workflow to send completed results back to doctors with patients
  - Added amount and indications fields to medication management admin section for complete drug information
  - Implemented name pre-registration system for parallel workflow efficiency
  - Added lab test disposition options (Return to Provider vs Treat per Pharmacy Protocol)
  - Created notification system to alert doctors when lab results are completed
  - Enhanced medication validation to require dosage, frequency, and indication before pharmacy submission
  - Reordered role selection buttons to match clinic workflow: Name Registration → Triage → Doctor → Pharmacy/Lab → Ophthalmologist → Admin
  - Added numbered workflow indicators (1-5) to role buttons for clear process guidance
  - Separated patient queue from triage station into dedicated "Patient Queue Monitor" role
  - Streamlined triage interface to focus on patient registration and vital signs collection
  - Improved home screen layout with uniform 2x3 button arrangement and centered admin button
  - Fixed medication checkbox popup system by moving prescriptions outside form structure for immediate updates
  - Enhanced lab options indentation with visual grouping for clearer provider interface
  - Corrected consultation completion error by properly handling lab test tuple data structure
  - Ensured patients returned from pharmacy/lab appear as priority cases at top of consultation queue
  - Implemented doctor session persistence to restore consultation state when doctors log back in
  - Removed save button from consultation form and implemented automatic session state saving
  - Fixed nested expander error in pharmacy lab results display
  - Corrected database manager references in lab test forms (urinalysis, glucose, pregnancy)
  - Enhanced doctor login to check for existing consultations and restore session automatically
  - Implemented re-consultation workflow to restore previous consultation data when patients return from lab
  - Added submit button to consultation form with proper database updating for re-consultations
  - Enhanced lab review workflow to send patients back to pharmacy after doctor reviews lab results
  - Improved consultation data persistence by checking both session state and database for existing information
  - Implemented consultation pause functionality allowing doctors to resume exact consultation state when lab results return
  - Added prescription status tracking (ready, paused_pending_lab) for proper workflow state management
  - Enhanced consultation workflow to save all prescription data when patients sent for lab tests
  - Created "pause button" effect for consultations allowing doctors to move to other patients while awaiting lab results
- June 20, 2025. Real-time WebSocket synchronization implementation
  - Added WebSocket client-server architecture for real-time updates across all clinic iPads
  - Implemented broadcast functionality for patient status changes, new registrations, and workflow updates
  - Created websocket_server.py for handling multi-device synchronization on port 6789
  - Added broadcast calls throughout patient workflow: registration, vital signs completion, consultation updates
  - Enhanced clinic setup with automatic WebSocket server startup alongside medical app
  - Enabled real-time notifications when patients move between triage, consultation, lab, and pharmacy stations
  - Fixed consultation state restoration issue where returning lab patients lost their original consultation data
  - Implemented proper page state persistence to maintain current page on browser refresh
  - Enhanced WebSocket client-server handshake to resolve connection errors and enable cross-device notifications
  - Added URL parameter tracking to preserve user location and role across page refreshes
  - Implemented Lab & Prescriptions tab state preservation to maintain selected medications and lab orders when patients return from lab tests
  - Added automatic patient return from lab input to doctor queue without requiring checkbox confirmation
  - Enhanced consultation workflow to save and restore all medication selections, dosages, frequencies, and lab test choices
  - Streamlined lab workflow by automatically sending patients back to doctors upon test completion (urinalysis, glucose, pregnancy)
  - Fixed patient routing to prevent repeated lab returns by clearing return_reason after re-consultation
  - Enhanced photo documentation preservation to display previously saved photos when patients return from lab
  - Implemented complete medication selection state restoration including dosages, frequencies, and lab-dependent flags
  - Enhanced name registration form to clear input fields after successful patient registration to prevent duplicates
  - Added clear_on_submit parameter and success confirmation messages for both individual and family registration forms
  - Fixed pharmacy workflow issue where patients weren't appearing in "Ready to Fill" after doctor consultation completion
  - Corrected prescription status from 'ready' to 'pending' to match pharmacy interface expectations
  - Implemented prescription history preservation system similar to consultation history functionality
  - Added save_prescription_state() and restore_prescription_state() functions for pharmacy workflow continuity
  - Enhanced filled prescriptions display to group by patient and show comprehensive prescription history
  - Added prescription state restoration notifications when patients return to pharmacy stations
  - Removed manual checkbox confirmation requirement from lab test completion workflow
  - Implemented automatic patient return to doctors upon lab test completion (urinalysis, glucose, pregnancy)
  - Enhanced lab input forms to automatically send patients back to doctor queue without manual intervention
  - Eliminated all manual checkboxes from lab workflow for seamless patient flow automation
- June 15, 2025. Family structure redesign and navigation improvements
  - Completely redesigned family registration to create proper family units instead of individual patient records
  - Added families table with family_id, family_name, head_of_household, and address tracking
  - Enhanced patients table with family_id links, is_independent flag, and separation_date for age 18+ transitions
  - Moved back button from top right to top left next to hamburger menu as requested
  - Fixed family vital signs workflow to process each family member sequentially
  - Implemented create_family() and add_family_member() methods for proper family management
  - Children are now properly linked to parents within family files but separable at age 18
- June 15, 2025. Modern UI redesign and navigation improvements
  - Implemented BackpackEMR-inspired design with gradient buttons and hover animations
  - Added always-visible back button system with fixed positioning outside scroll area
  - Enhanced family registration workflow to allow multiple children before creating visits
  - Implemented family consultation grouping in doctor interface
  - Fixed delete button to split into confirm/cancel buttons on click
  - Updated hamburger menu to three horizontal lines positioned top-right
  - Modernized patient cards with colored borders and smooth transitions
- June 15, 2025. Enhanced UI and settings management
  - Improved patient deletion system with working popup confirmation
  - Added comprehensive clinic settings with dark mode, language options, and session management
  - Optimized download button layout for better screen utilization
  - Removed redundant location displays and consolidated to navigation and sidebar
  - Enhanced deletion function with proper cascade handling for all related data
- June 13, 2025. Initial setup

## User Preferences

Preferred communication style: Simple, everyday language.