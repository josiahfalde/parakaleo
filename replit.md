# ParakaleoMed - Compressed Requirements & Implementation Document

---

## Overview
ParakaleoMed is an offline-first medical clinic charting application built with Streamlit and SQLite, designed for mobile medical missions in the Dominican Republic and Haiti. Its purpose is to provide comprehensive clinical workflow management, from patient registration to pharmacy dispensing, in remote locations. Key capabilities include location-based patient numbering, a multi-station workflow (Registrant → Triage → Provider → Pharmacy → Lab), family-based consultation workflows, lab testing, preset medication management, multi-language support (English, Spanish, Creole), and real-time synchronization via WebSocket. The project aims to streamline medical operations in underserved areas, offering a robust and intuitive solution for clinic staff.

## User Preferences
- **Communication Style:** Simple, everyday language
- **Target Users:** Non-technical clinic staff

## System Architecture

### UI/UX Decisions
The application features a modern Apple/Airbnb-inspired aesthetic with a neutral base color (#F9FAFB) and a teal accent (#0F766E). It utilizes the Inter font and incorporates pill-style buttons with gradients, rounded corners (12-16px border radius), cards with elevation and hover effects, and smooth cubic-bezier transitions. The layout is mobile-first, responsive, and optimized for iPad, using Streamlit's wide layout with a collapsible sidebar. Role selection is handled via gradient-colored cards for Registrant, Triage, Provider, Pharmacy, Lab Tech, and Queue Monitor.

### Technical Implementations
ParakaleoMed is built with a Python 3.11 backend, using Streamlit as the web application framework. Data is stored locally using SQLite3, ensuring offline functionality. Real-time synchronization between devices (e.g., iPads and Raspberry Pi) is handled via a WebSocket server, employing conflict resolution (latest valid change wins) and automatic retries. Data at rest is secured with AES-256 encryption, and data in transit uses TLS 1.2+. The system supports various user roles with granular permissions and field-level protections, along with comprehensive audit logging for all critical actions.

### Feature Specifications
- **Patient Management:** CRUD operations for patient profiles, unique ID generation (e.g., DR00001), family linkage, and robust search functionality.
- **Clinical Encounter Workflow:** Multi-station workflow with encounter state management (Created, In Progress, Awaiting, Completed) and status-based handoff signaling.
- **Medical History:** Tracking of chronic conditions, surgeries, medications, allergies, immunizations, and pregnancy history.
- **Vitals & Measurements:** Comprehensive vital sign capture including temperature, BP, weight, height (with auto-calculated BMI), pulse, respirations, and SpO2.
- **Diagnosis:** ICD-10 lookup with category filtering and primary/secondary diagnosis designation.
- **Treatment & Orders:** Management of medication orders from a clinic-specific formulary (with stock awareness), lab orders, and procedure logging.
- **Pharmacy Module:** Dispensing workflow, stock management, and integration with lab orders and results.
- **Offline-First Capabilities:** Full system usability without internet, local encrypted datastore, async sync queue, and support for iPads connecting to a Raspberry Pi AP.
- **Consultation Sign-Off:** Provides context-aware options for providers to complete consultations, including sending to lab/pharmacy or completing, with built-in validation.
- **Family Navigation:** Streamlined workflow for families with multiple members visiting on the same day, featuring status icons and auto-advance functionality.
- **Reporting:** Generation of patient summary reports (PDF), clinic-level reports (patient counts, medication dispensing, diagnoses, demographics), and export options (PDF, CSV/Excel).
- **Security:** Role-based access control, field-level protections, encounter locking, in-field PIN quick unlock, and comprehensive audit logging.
- **Country-Aware Configuration:** Support for country-specific settings (e.g., DR, Haiti) including consent requirements, field validation, and language defaults.

### System Design Choices
The system is designed for multi-device support (tablets, phones, laptops) with a browser-only interface. The database schema includes key tables such as `patients`, `visits`, `vital_signs`, `prescriptions`, `lab_tests`, `icd10_diagnoses`, `clinic_staff`, and `audit_logs`. Clinic naming follows a specific convention: `{Church Name}, {Pastor Last Name} - {Month Year}`.

## External Dependencies
- **Streamlit:** Web application framework
- **Pandas:** Data manipulation
- **SQLite3:** Database interface
- **Plotly:** Interactive visualizations
- **openpyxl:** Excel (.xlsx) handling
- **xlrd:** Legacy Excel (.xls) handling
- **ReportLab:** PDF generation
- **qrcode:** QR code generation
- **cryptography:** AES-256 encryption
- **websockets:** Real-time sync
- **Pillow:** Image processing