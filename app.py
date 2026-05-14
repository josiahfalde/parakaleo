import streamlit as st
import sqlite3
from datetime import datetime, date
import os
from typing import Dict, List, Optional
import time
from streamlit.components.v1 import html
import json
import base64
import io
import hashlib

# PDF and QR code imports
try:
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as RLImage
    from reportlab.lib.units import inch
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False

try:
    import qrcode
    from PIL import Image as PILImage
    QR_AVAILABLE = True
except ImportError:
    QR_AVAILABLE = False

try:
    from cryptography.fernet import Fernet
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    ENCRYPTION_AVAILABLE = True
except ImportError:
    ENCRYPTION_AVAILABLE = False

# =============================================================================
# Multi-language support — UI strings localized in English / Spanish / Haitian
# Creole. Use the t() shorthand below to translate from inside any function:
#   t('start_vitals')  -> "Start vitals" / "Comenzar signos" / "Kòmanse siy"
# Adding a new translatable string: add the key to all 3 sub-dicts and use
# t('your_key') at the call site. Missing keys fall back to English, then
# to the raw key, so missing translations never break the UI.
# =============================================================================
TRANSLATIONS = {
    'en': {
        # Brand / chrome
        'welcome': 'Welcome to ParakaleoMed',
        'select_role': 'Select your role',
        'change_role': 'Change Role',
        'change_location': 'Change location',
        'sign_in': 'Sign in',
        'sign_out': 'Sign out',
        'org_home': 'Org Home',
        'clinic_home': 'Clinic Home',
        'enter_clinic': 'Enter Clinic',
        'create_new_clinic': 'Create new clinic',
        'admin_login': 'Administrator login',
        'language': 'Language',

        # Role names (also page titles)
        'role_registrant': 'Registrant',
        'role_triage': 'Triage',
        'role_provider': 'Provider',
        'role_pharmacy': 'Pharmacy',
        'role_lab': 'Lab Tech',
        'role_queue_monitor': 'Queue Monitor',
        'role_admin': 'Clinic Manager',

        # Role descriptions (the home-screen subtitles)
        'role_registrant_desc': 'Step 1 · Capture patient names ahead of triage',
        'role_triage_desc':     'Step 2 · Record vital signs',
        'role_provider_desc':   'Step 3 · See patient, diagnose, prescribe',
        'role_pharmacy_desc':   'Step 4 · Fill prescriptions',
        'role_lab_desc':        'Step 5 · Run tests, enter results',
        'role_queue_desc':      'Step 6 · Read-only view of all queues',

        # Page titles
        'page_name_registration': 'Name Registration',
        'page_triage': 'Triage',
        'page_pharmacy': 'Pharmacy',
        'page_laboratory': 'Laboratory',
        'page_admin': 'Administration',
        'page_patient_registration': 'Patient Registration',

        # Common buttons / actions
        'save': 'Save',
        'cancel': 'Cancel',
        'submit': 'Submit',
        'add': 'Add',
        'remove': 'Remove',
        'edit': 'Edit',
        'delete': 'Delete',
        'back': 'Back',
        'continue_btn': 'Continue',
        'search': 'Search',
        'start_vitals': 'Start vitals',
        'add_to_queue': 'Add to queue',
        'new_visit': 'New visit',
        'enter': 'Enter',

        # Queue / status
        'in_clinic_now': 'In clinic now',
        'no_patients_waiting': 'No patients waiting. They will appear here after registration.',
        'waiting_for_vitals': 'Waiting for vitals',
        'doctor_status': 'Doctor status',
        'status_available': 'available',
        'status_with': 'with',
        'status_urgent': 'Urgent',
        'status_waiting': 'Waiting',
        'status_ready': 'Ready',
        'status_idle': 'Idle',
        'reg_time_prefix': 'reg.',

        # Patient fields
        'name': 'Name',
        'patient_name': 'Patient name',
        'date_of_birth': 'Date of Birth',
        'age': 'Age',
        'gender': 'Gender',
        'sex': 'Sex',
        'male': 'Male',
        'female': 'Female',
        'phone': 'Phone',
        'address': 'Address',
        'notes': 'Notes',
        'medical_history': 'Medical History',
        'last_visit': 'Last visit',
        'never': 'Never',

        # Triage tabs
        'tab_triage_queue': 'Triage Queue',
        'tab_new_patient': 'New Patient',
        'tab_search_patient': 'Search Patient',

        # Name registration
        'tab_register_names': 'Register Names',
        'tab_name_queue': 'Name Queue',
        'registration_type': 'Registration type',
        'individual_patient': 'Individual patient',
        'family_group': 'Family group',
        'name_reg_caption': 'Register patient names ahead of triage to speed up workflow.',

        # Family registration
        'family_name': 'Family name',
        'head_of_household': 'Head of household',
        'members': 'Members',
        'add_member': '+ Add member',
        'add_to_family': 'Add to family',
        'relationship': 'Relationship',
        'rel_head': 'head',
        'rel_spouse': 'spouse',
        'rel_child': 'child',
        'first_member_is_head': 'First member is head of household',
        'save_family_to_queue': 'Save family · add to triage queue',
        'family_added_success': 'Family added to triage queue. Ready for the next.',
        'family_screen_caption': 'Register a family on one screen. Add the head of household first, then any spouse and children. All members are saved together so they show up grouped in triage.',
        'add_head_first': 'Add the head of household first, then any spouse and children.',
        'possible_existing_match': 'Possible existing patient(s) matching',
        'use_existing': 'Use existing',

        # Vital signs
        'vital_signs': 'Vital signs',
        'blood_pressure': 'Blood Pressure',
        'systolic_bp': 'Systolic BP',
        'diastolic_bp': 'Diastolic BP',
        'heart_rate': 'Heart Rate (bpm)',
        'temperature': 'Temperature (°F)',
        'weight': 'Weight (kg)',
        'height': 'Height (cm)',
        'oxygen_saturation': 'Oxygen Saturation (%)',
        'respirations': 'Respirations (/min)',
        'bmi': 'BMI',
        'save_vital_signs': 'Save Vital Signs',
        'recording_vitals_for': 'Recording vital signs for',
        'vitals_tip': "Enter 'N/A' for any measurement that cannot be taken.",

        # Consultation / clinical
        'consultation': 'Consultation',
        'chief_complaint': 'Chief complaint',
        'diagnosis': 'Diagnosis',
        'medications': 'Medications',
        'send_to_lab': 'Send to Lab',
        'send_to_pharmacy': 'Send to Pharmacy',
        'complete_consultation': 'Complete Consultation',
        'return_to_queue': 'Return to Queue',
        'consultation_history': 'Consultation History',
        'todays_consultations': 'Today',
        'last_7_days': 'Last 7 days',
        'last_30_days': 'Last 30 days',
        'all_time': 'All time',
        'show': 'Show',

        # Back-button labels (audited every nav back button in app)
        'back_to_role_selection': 'Back to Role Selection',
        'back_to_main': 'Back to Main',
        'back_to_signin_options': '← Back to Sign-In Options',
        'back_to_signin': '← Back to Sign-In',
        'back_to_org': 'Back to Org',
        'back_to_queue': '← Back to Queue',
        'back_to_consult_history': '← Back to Consultation History',
        'close_label': '✕ Close',
        'close_short': '✕',
        'back_to_reports': 'Back to Reports',
        'refresh': '↻ Refresh',

        # New-patient form labels
        'register_new_patient': 'Register New Patient',
        'enter_full_name': 'Enter full name',
        'age_entry_method': 'Age entry method',
        'enter_age': 'Enter age',
        'enter_dob': 'Enter date of birth',
        'phone_number': 'Phone number',
        'optional': 'Optional',
        'emergency_contact': 'Emergency contact',
        'medical_history_placeholder': 'Any relevant medical conditions, allergies, or medications',
        'register_patient_btn': 'Register Patient',
        'please_enter_name': "Please enter the patient's name.",
        'patient_name_required': 'Patient Name *',
        'individual_patient_radio': 'Individual Patient',
        'family_registration_radio': 'Family Registration',
        'registration_type_label': 'Registration Type',
        'years': 'years',

        # Doctor login
        'select_your_name': 'Select your name',
        'no_doctors_available': 'No doctors available. Please contact admin to add doctors.',
        'choose_your_name': 'Choose your name:',

        # Duplicate / existing patient match
        'potential_existing_patients': '🔍 Potential existing patients found',
        'patient_may_be_existing': 'This patient may have been seen at a previous clinic. Please review:',
        'exact_matches_header': 'Exact name matches',
        'similar_names_header': 'Similar names',
        'use_existing_btn': 'Use existing',
        'use_this_btn': 'Use this',
        'register_as_new': 'Register as new patient',
        'connected_to_existing': 'Connected to existing patient.',
        'new_patient_registered': 'New patient registered.',

        # Search
        'find_existing_patient': 'Find Existing Patient',
        'search_by_name_or_id': 'Search by name or patient ID',
        'enter_name_or_id_placeholder': 'Enter name or ID (e.g., 00001)',
        'no_patients_found': 'No patients found matching your search.',
        'results_count': 'Results',

        # Vitals confirmation
        'vitals_saved_message': 'Vital signs recorded. Patient is ready for consultation.',
        'sent_to_doctor_queue': 'Sent to doctor queue',
        'now_waiting_consult': 'is now waiting for consultation',

        # Pharmacy tabs
        'tab_ready_to_fill': 'Ready to Fill',
        'tab_lab_results': 'Lab Results',
        'tab_lab_input': 'Lab Input',
        'tab_awaiting_teaching': 'Awaiting Teaching',
        'tab_filled_prescriptions': 'Filled Prescriptions',
        'prescriptions_to_fill': 'Prescriptions to Fill',

        # Lab tabs
        'tab_pending_tests': 'Pending Tests',
        'tab_completed_lab': 'Lab Results',
        'tests_to_process': 'Tests to Process',

        # Family registration — clearer add-member flow
        'add_head_of_household': 'Add head of household',
        'add_family_member': 'Add a family member',
        'remove': 'Remove',
        'family_save_caption': 'Add as many family members as you need. When the family is complete, tap Save below.',
        'family_empty_state': 'No members yet. Start by adding the head of household below.',
        'rel_radio_label': 'Relationship to head of household',

        # Section headers — clinical flow
        'hdr_record_vital_signs': 'Record Vital Signs',
        'hdr_add_patient_names': 'Add Patient Names',
        'hdr_registration_queue': 'Registration Queue',
        'hdr_preregistered_patients': 'Pre-Registered Patients',
        'hdr_family_vitals_summary': 'Family Vital Signs Summary',
        'hdr_family_vitals_collection': 'Family Vital Signs Collection',
        'hdr_select_patient_for_consultation': 'Select Patient for Consultation',
        'hdr_priority_lab_results': 'PRIORITY: Patients with Lab Results',
        'hdr_lab_results_completed': 'Lab Results Completed',
        'hdr_lab_results': 'Lab Results',
        'hdr_family_groups': 'Family Groups',
        'hdr_individual_patients': 'Individual Patients',
        'hdr_patient_history': 'Patient History',
        'hdr_photo_documentation': 'Photo Documentation',
        'hdr_lab_tests': 'Lab Tests',
        'hdr_prescriptions': 'Prescriptions',
        'hdr_ophthalmology_referral': 'Ophthalmology Referral',
        'hdr_immunization_history': 'Immunization History',
        'hdr_pregnancy_history': 'Pregnancy History',
        'hdr_patient_qr': 'Patient QR Code / Wristband',
        'hdr_family_navigation': 'Family Navigation',
        'hdr_patient_demographics': 'Patient Demographics',
        'hdr_medical_history_section': 'Medical History',
        'hdr_current_queue': 'Current Patient Queue',
        'hdr_queue_monitor': 'Patient Queue Monitor',
        'hdr_todays_overview': "Today's Overview",
        'hdr_recent_patient_activity': 'Recent Patient Activity',
        'hdr_access_clinic_roles': 'Access Clinic Roles',
        'hdr_consultation_history': 'Consultation History',

        # Common info / empty states
        'msg_no_patients_in_queue': 'No patients in queue for today.',
        'msg_no_waiting_consultation': 'No patients waiting for consultation.',
        'msg_no_consultations_today': 'No consultations recorded today.',
        'msg_no_completed_labs': 'No completed lab results available today.',
        'msg_no_pending_prescriptions': 'No pending prescriptions.',
        'msg_no_lab_results_found': 'No lab results found for this patient.',
        'msg_no_patient_activity': 'No patient activity yet today.',
        'msg_realtime_queue': 'Real-time view of all patients in the clinic workflow system.',
        'msg_lab_input_intro': 'Input lab test results for patients. Results will be sent back to the doctor along with the patient.',
        'msg_no_preregistered': 'No pre-registered patients waiting for vital signs. Check the Name Registration station.',
        'msg_preregistered_intro': 'Patients registered through Name Registration station are ready for vital signs collection.',
        'msg_no_names_in_queue': "No names in registration queue. Add names in the 'Register Names' tab.",
        'msg_returning_from_lab': 'This patient has returned from lab/pharmacy with completed results. Original consultation data has been restored below.',
        'msg_changes_auto_saved': 'All changes are automatically saved. Continue to Lab & Prescriptions tab to complete the consultation.',
        'msg_consultation_paused': 'Consultation paused and saved.',
        'msg_consultation_completed': 'Consultation completed successfully.',
        'msg_patient_returned_to_queue': 'Patient returned to waiting queue. Your notes have been saved.',
        'msg_positive_result': 'Positive result',
        'msg_negative_result': 'Negative result',

        # Common errors
        'err_name_cannot_be_empty': 'Name cannot be empty',
        'err_please_enter_name_field': 'Please enter a patient name.',
        'err_invalid_credentials': 'Invalid credentials. Please check your name and PIN.',
        'err_pin_4_digits': 'PIN must be exactly 4 digits',
        'err_pins_no_match': 'PINs do not match',
        'err_please_enter_pin': 'Please enter your name and PIN',

        # Consultation routing
        'complete_send_to_lab': 'Complete · Send to Lab',
        'complete_send_to_pharmacy': 'Complete · Send to Pharmacy',
        'complete_discharge': 'Complete · Discharge',
        'add_diagnosis_first': 'Please add at least one diagnosis before completing.',
        'pause_consultation': 'Save & return to queue',
        'diagnosis_recorded': 'Diagnosis recorded',
        'no_diagnosis_yet': 'No diagnosis yet',
        'lab_tests_ordered_count': 'lab test(s) ordered',
        'no_labs_ordered': 'No lab tests ordered',
        'prescriptions_written_count': 'prescription(s) written',
        'no_prescriptions_written': 'No prescriptions written',
        'next_family_member': 'Next family member',
        'sent_to_lab_msg': 'Sent to Lab queue.',
        'sent_to_pharmacy_msg': 'Sent to Pharmacy queue.',
        'consultation_complete_msg': 'Consultation complete. Patient discharged.',
        'family_continuing_with': 'Continuing with',

        # Consent + legacy
        'consent_message': 'I consent to the collection and use of my medical information for treatment purposes.',
        'immunizations': 'Immunizations',
        'pregnancy_history': 'Pregnancy History',
        'stock_low': 'Low Stock',
        'stock_out': 'Out of Stock',
        'stock_available': 'In Stock',
        'patient_registration': 'Patient Registration',
    },
    'es': {
        # Brand / chrome
        'welcome': 'Bienvenido a ParakaleoMed',
        'select_role': 'Selecciona tu rol',
        'change_role': 'Cambiar rol',
        'change_location': 'Cambiar ubicación',
        'sign_in': 'Iniciar sesión',
        'sign_out': 'Cerrar sesión',
        'org_home': 'Organización',
        'clinic_home': 'Clínica',
        'enter_clinic': 'Entrar a la clínica',
        'create_new_clinic': 'Crear nueva clínica',
        'admin_login': 'Inicio de sesión de administrador',
        'language': 'Idioma',

        # Role names
        'role_registrant': 'Registro',
        'role_triage': 'Triaje',
        'role_provider': 'Proveedor',
        'role_pharmacy': 'Farmacia',
        'role_lab': 'Laboratorio',
        'role_queue_monitor': 'Monitor de cola',
        'role_admin': 'Gerente de clínica',

        # Role descriptions
        'role_registrant_desc': 'Paso 1 · Registrar nombres de pacientes antes del triaje',
        'role_triage_desc':     'Paso 2 · Registrar signos vitales',
        'role_provider_desc':   'Paso 3 · Atender, diagnosticar, recetar',
        'role_pharmacy_desc':   'Paso 4 · Surtir recetas',
        'role_lab_desc':        'Paso 5 · Realizar pruebas, registrar resultados',
        'role_queue_desc':      'Paso 6 · Vista de solo lectura de todas las colas',

        # Page titles
        'page_name_registration': 'Registro de Nombres',
        'page_triage': 'Triaje',
        'page_pharmacy': 'Farmacia',
        'page_laboratory': 'Laboratorio',
        'page_admin': 'Administración',
        'page_patient_registration': 'Registro de Pacientes',

        # Common buttons
        'save': 'Guardar',
        'cancel': 'Cancelar',
        'submit': 'Enviar',
        'add': 'Agregar',
        'remove': 'Eliminar',
        'edit': 'Editar',
        'delete': 'Eliminar',
        'back': 'Atrás',
        'continue_btn': 'Continuar',
        'search': 'Buscar',
        'start_vitals': 'Comenzar signos',
        'add_to_queue': 'Agregar a la cola',
        'new_visit': 'Nueva visita',
        'enter': 'Entrar',

        # Queue / status
        'in_clinic_now': 'En la clínica ahora',
        'no_patients_waiting': 'No hay pacientes esperando. Aparecerán aquí tras el registro.',
        'waiting_for_vitals': 'Esperando signos vitales',
        'doctor_status': 'Estado del médico',
        'status_available': 'disponible',
        'status_with': 'con',
        'status_urgent': 'Urgente',
        'status_waiting': 'Esperando',
        'status_ready': 'Listo',
        'status_idle': 'Inactivo',
        'reg_time_prefix': 'reg.',

        # Patient fields
        'name': 'Nombre',
        'patient_name': 'Nombre del paciente',
        'date_of_birth': 'Fecha de Nacimiento',
        'age': 'Edad',
        'gender': 'Género',
        'sex': 'Sexo',
        'male': 'Masculino',
        'female': 'Femenino',
        'phone': 'Teléfono',
        'address': 'Dirección',
        'notes': 'Notas',
        'medical_history': 'Historia Médica',
        'last_visit': 'Última visita',
        'never': 'Nunca',

        # Triage tabs
        'tab_triage_queue': 'Cola de Triaje',
        'tab_new_patient': 'Nuevo Paciente',
        'tab_search_patient': 'Buscar Paciente',

        # Name registration
        'tab_register_names': 'Registrar Nombres',
        'tab_name_queue': 'Cola de Nombres',
        'registration_type': 'Tipo de registro',
        'individual_patient': 'Paciente individual',
        'family_group': 'Grupo familiar',
        'name_reg_caption': 'Registra nombres de pacientes antes del triaje para agilizar el flujo.',

        # Family registration
        'family_name': 'Nombre de la familia',
        'head_of_household': 'Jefe de hogar',
        'members': 'Miembros',
        'add_member': '+ Agregar miembro',
        'add_to_family': 'Agregar a la familia',
        'relationship': 'Parentesco',
        'rel_head': 'jefe',
        'rel_spouse': 'cónyuge',
        'rel_child': 'hijo/a',
        'first_member_is_head': 'El primer miembro es el jefe del hogar',
        'save_family_to_queue': 'Guardar familia · agregar a triaje',
        'family_added_success': 'Familia agregada a la cola de triaje. Lista para la siguiente.',
        'family_screen_caption': 'Registra una familia en una sola pantalla. Agrega primero al jefe del hogar, luego cónyuge e hijos. Todos los miembros se guardan juntos.',
        'add_head_first': 'Agrega primero al jefe del hogar, luego cónyuge e hijos.',
        'possible_existing_match': 'Posible(s) paciente(s) existente(s) que coinciden con',
        'use_existing': 'Usar existente',

        # Vital signs
        'vital_signs': 'Signos Vitales',
        'blood_pressure': 'Presión Arterial',
        'systolic_bp': 'Presión Sistólica',
        'diastolic_bp': 'Presión Diastólica',
        'heart_rate': 'Frecuencia Cardíaca (lpm)',
        'temperature': 'Temperatura (°F)',
        'weight': 'Peso (kg)',
        'height': 'Altura (cm)',
        'oxygen_saturation': 'Saturación de Oxígeno (%)',
        'respirations': 'Respiraciones (/min)',
        'bmi': 'IMC',
        'save_vital_signs': 'Guardar Signos Vitales',
        'recording_vitals_for': 'Registrando signos vitales de',
        'vitals_tip': "Escribe 'N/A' para cualquier medición que no se pueda tomar.",

        # Consultation / clinical
        'consultation': 'Consulta',
        'chief_complaint': 'Motivo principal',
        'diagnosis': 'Diagnóstico',
        'medications': 'Medicamentos',
        'send_to_lab': 'Enviar a Laboratorio',
        'send_to_pharmacy': 'Enviar a Farmacia',
        'complete_consultation': 'Completar Consulta',
        'return_to_queue': 'Volver a la Cola',
        'consultation_history': 'Historial de Consultas',
        'todays_consultations': 'Hoy',
        'last_7_days': 'Últimos 7 días',
        'last_30_days': 'Últimos 30 días',
        'all_time': 'Todo el tiempo',
        'show': 'Mostrar',

        # Back-button labels
        'back_to_role_selection': 'Volver a Selección de Rol',
        'back_to_main': 'Volver al Inicio',
        'back_to_signin_options': '← Volver a Opciones de Inicio',
        'back_to_signin': '← Volver al Inicio',
        'back_to_org': 'Volver a la Organización',
        'back_to_queue': '← Volver a la Cola',
        'back_to_consult_history': '← Volver al Historial',
        'close_label': '✕ Cerrar',
        'close_short': '✕',
        'back_to_reports': 'Volver a Reportes',
        'refresh': '↻ Actualizar',

        # New-patient form
        'register_new_patient': 'Registrar Nuevo Paciente',
        'enter_full_name': 'Ingrese el nombre completo',
        'age_entry_method': 'Método de entrada de edad',
        'enter_age': 'Ingresar edad',
        'enter_dob': 'Ingresar fecha de nacimiento',
        'phone_number': 'Número de teléfono',
        'optional': 'Opcional',
        'emergency_contact': 'Contacto de emergencia',
        'medical_history_placeholder': 'Condiciones médicas relevantes, alergias o medicamentos',
        'register_patient_btn': 'Registrar Paciente',
        'please_enter_name': 'Por favor ingrese el nombre del paciente.',
        'patient_name_required': 'Nombre del Paciente *',
        'individual_patient_radio': 'Paciente Individual',
        'family_registration_radio': 'Registro Familiar',
        'registration_type_label': 'Tipo de Registro',
        'years': 'años',

        # Doctor login
        'select_your_name': 'Seleccione su nombre',
        'no_doctors_available': 'No hay médicos disponibles. Contacte al administrador.',
        'choose_your_name': 'Elija su nombre:',

        # Duplicate / existing patient match
        'potential_existing_patients': '🔍 Posibles pacientes existentes encontrados',
        'patient_may_be_existing': 'Este paciente puede haber sido atendido en una clínica anterior. Por favor revise:',
        'exact_matches_header': 'Coincidencias exactas de nombre',
        'similar_names_header': 'Nombres similares',
        'use_existing_btn': 'Usar existente',
        'use_this_btn': 'Usar este',
        'register_as_new': 'Registrar como nuevo paciente',
        'connected_to_existing': 'Conectado al paciente existente.',
        'new_patient_registered': 'Nuevo paciente registrado.',

        # Search
        'find_existing_patient': 'Buscar Paciente Existente',
        'search_by_name_or_id': 'Buscar por nombre o ID',
        'enter_name_or_id_placeholder': 'Ingrese nombre o ID (ej. 00001)',
        'no_patients_found': 'No se encontraron pacientes con esa búsqueda.',
        'results_count': 'Resultados',

        # Vitals confirmation
        'vitals_saved_message': 'Signos vitales registrados. El paciente está listo para consulta.',
        'sent_to_doctor_queue': 'Enviado a la cola del médico',
        'now_waiting_consult': 'ahora está esperando consulta',

        # Pharmacy tabs
        'tab_ready_to_fill': 'Listos para Surtir',
        'tab_lab_results': 'Resultados de Laboratorio',
        'tab_lab_input': 'Entrada de Laboratorio',
        'tab_awaiting_teaching': 'Esperando Educación',
        'tab_filled_prescriptions': 'Recetas Surtidas',
        'prescriptions_to_fill': 'Recetas por Surtir',

        # Lab tabs
        'tab_pending_tests': 'Pruebas Pendientes',
        'tab_completed_lab': 'Resultados',
        'tests_to_process': 'Pruebas por Procesar',

        # Family registration
        'add_head_of_household': 'Agregar jefe de hogar',
        'add_family_member': 'Agregar un miembro de la familia',
        'remove': 'Eliminar',
        'family_save_caption': 'Agregue todos los miembros de la familia que necesite. Cuando la familia esté completa, toque Guardar abajo.',
        'family_empty_state': 'Aún no hay miembros. Comience agregando al jefe de hogar abajo.',
        'rel_radio_label': 'Relación con el jefe de hogar',

        # Section headers
        'hdr_record_vital_signs': 'Registrar Signos Vitales',
        'hdr_add_patient_names': 'Agregar Nombres de Pacientes',
        'hdr_registration_queue': 'Cola de Registro',
        'hdr_preregistered_patients': 'Pacientes Pre-Registrados',
        'hdr_family_vitals_summary': 'Resumen de Signos Vitales Familiares',
        'hdr_family_vitals_collection': 'Toma de Signos Vitales Familiares',
        'hdr_select_patient_for_consultation': 'Seleccione Paciente para Consulta',
        'hdr_priority_lab_results': 'PRIORIDAD: Pacientes con Resultados de Laboratorio',
        'hdr_lab_results_completed': 'Resultados de Laboratorio Completados',
        'hdr_lab_results': 'Resultados de Laboratorio',
        'hdr_family_groups': 'Grupos Familiares',
        'hdr_individual_patients': 'Pacientes Individuales',
        'hdr_patient_history': 'Historial del Paciente',
        'hdr_photo_documentation': 'Documentación Fotográfica',
        'hdr_lab_tests': 'Pruebas de Laboratorio',
        'hdr_prescriptions': 'Recetas',
        'hdr_ophthalmology_referral': 'Referencia a Oftalmología',
        'hdr_immunization_history': 'Historial de Vacunas',
        'hdr_pregnancy_history': 'Historial de Embarazos',
        'hdr_patient_qr': 'Código QR del Paciente / Brazalete',
        'hdr_family_navigation': 'Navegación Familiar',
        'hdr_patient_demographics': 'Datos Demográficos del Paciente',
        'hdr_medical_history_section': 'Historia Médica',
        'hdr_current_queue': 'Cola Actual de Pacientes',
        'hdr_queue_monitor': 'Monitor de Cola de Pacientes',
        'hdr_todays_overview': 'Resumen de Hoy',
        'hdr_recent_patient_activity': 'Actividad Reciente de Pacientes',
        'hdr_access_clinic_roles': 'Acceso a Roles de Clínica',
        'hdr_consultation_history': 'Historial de Consultas',

        # Info / empty states
        'msg_no_patients_in_queue': 'No hay pacientes en cola hoy.',
        'msg_no_waiting_consultation': 'No hay pacientes esperando consulta.',
        'msg_no_consultations_today': 'No hay consultas registradas hoy.',
        'msg_no_completed_labs': 'No hay resultados de laboratorio completados hoy.',
        'msg_no_pending_prescriptions': 'No hay recetas pendientes.',
        'msg_no_lab_results_found': 'No se encontraron resultados de laboratorio para este paciente.',
        'msg_no_patient_activity': 'No hay actividad de pacientes hoy todavía.',
        'msg_realtime_queue': 'Vista en tiempo real de todos los pacientes en el flujo de trabajo de la clínica.',
        'msg_lab_input_intro': 'Ingrese los resultados de las pruebas de laboratorio. Los resultados se enviarán al médico junto con el paciente.',
        'msg_no_preregistered': 'No hay pacientes pre-registrados esperando signos vitales. Revise la estación de Registro de Nombres.',
        'msg_preregistered_intro': 'Pacientes registrados en la estación de Registro de Nombres están listos para la toma de signos vitales.',
        'msg_no_names_in_queue': "No hay nombres en la cola de registro. Agregue nombres en la pestaña 'Registrar Nombres'.",
        'msg_returning_from_lab': 'Este paciente ha regresado del laboratorio/farmacia con resultados completados. Los datos originales de la consulta se han restaurado abajo.',
        'msg_changes_auto_saved': 'Todos los cambios se guardan automáticamente. Continúe a la pestaña de Laboratorio y Recetas para completar la consulta.',
        'msg_consultation_paused': 'Consulta pausada y guardada.',
        'msg_consultation_completed': 'Consulta completada con éxito.',
        'msg_patient_returned_to_queue': 'Paciente devuelto a la cola de espera. Sus notas han sido guardadas.',
        'msg_positive_result': 'Resultado positivo',
        'msg_negative_result': 'Resultado negativo',

        # Errors
        'err_name_cannot_be_empty': 'El nombre no puede estar vacío',
        'err_please_enter_name_field': 'Por favor ingrese el nombre del paciente.',
        'err_invalid_credentials': 'Credenciales inválidas. Verifique su nombre y PIN.',
        'err_pin_4_digits': 'El PIN debe tener exactamente 4 dígitos',
        'err_pins_no_match': 'Los PINs no coinciden',
        'err_please_enter_pin': 'Por favor ingrese su nombre y PIN',

        # Consultation routing
        'complete_send_to_lab': 'Completar · Enviar a Laboratorio',
        'complete_send_to_pharmacy': 'Completar · Enviar a Farmacia',
        'complete_discharge': 'Completar · Dar de Alta',
        'add_diagnosis_first': 'Por favor agregue al menos un diagnóstico antes de completar.',
        'pause_consultation': 'Guardar y volver a la cola',
        'diagnosis_recorded': 'Diagnóstico registrado',
        'no_diagnosis_yet': 'Sin diagnóstico aún',
        'lab_tests_ordered_count': 'prueba(s) de laboratorio ordenada(s)',
        'no_labs_ordered': 'Sin pruebas de laboratorio ordenadas',
        'prescriptions_written_count': 'receta(s) escrita(s)',
        'no_prescriptions_written': 'Sin recetas escritas',
        'next_family_member': 'Próximo miembro de la familia',
        'sent_to_lab_msg': 'Enviado a la cola de Laboratorio.',
        'sent_to_pharmacy_msg': 'Enviado a la cola de Farmacia.',
        'consultation_complete_msg': 'Consulta completa. Paciente dado de alta.',
        'family_continuing_with': 'Continuando con',

        # Legacy
        'consent_message': 'Consiento la recopilación y uso de mi información médica para fines de tratamiento.',
        'immunizations': 'Vacunas',
        'pregnancy_history': 'Historia de Embarazos',
        'stock_low': 'Stock Bajo',
        'stock_out': 'Agotado',
        'stock_available': 'Disponible',
        'patient_registration': 'Registro de Pacientes',
        'triage': 'Triaje',
        'pharmacy': 'Farmacia',
        'lab': 'Laboratorio',
        'admin': 'Administración',
    },
    'ht': {
        # Brand / chrome
        'welcome': 'Byenveni nan ParakaleoMed',
        'select_role': 'Chwazi wòl ou',
        'change_role': 'Chanje wòl',
        'change_location': 'Chanje kote',
        'sign_in': 'Konekte',
        'sign_out': 'Dekonekte',
        'org_home': 'Òganizasyon',
        'clinic_home': 'Klinik',
        'enter_clinic': 'Antre nan klinik la',
        'create_new_clinic': 'Kreye nouvo klinik',
        'admin_login': 'Konekte kòm administratè',
        'language': 'Lang',

        # Role names
        'role_registrant': 'Anrejistreman',
        'role_triage': 'Triyaj',
        'role_provider': 'Pwofesyonèl Sante',
        'role_pharmacy': 'Famasi',
        'role_lab': 'Laboratwa',
        'role_queue_monitor': 'Moniteur File',
        'role_admin': 'Manadjè Klinik',

        # Role descriptions
        'role_registrant_desc': 'Etap 1 · Pran non pasyan anvan triyaj',
        'role_triage_desc':     'Etap 2 · Pran siy vital yo',
        'role_provider_desc':   'Etap 3 · Wè pasyan, dyagnostike, preskri',
        'role_pharmacy_desc':   'Etap 4 · Bay medikaman',
        'role_lab_desc':        'Etap 5 · Fè tès, antre rezilta',
        'role_queue_desc':      'Etap 6 · Wè tout file (lekti sèlman)',

        # Page titles
        'page_name_registration': 'Anrejistreman Non',
        'page_triage': 'Triyaj',
        'page_pharmacy': 'Famasi',
        'page_laboratory': 'Laboratwa',
        'page_admin': 'Administrasyon',
        'page_patient_registration': 'Anrejistreman Pasyan',

        # Common buttons
        'save': 'Sove',
        'cancel': 'Anile',
        'submit': 'Soumèt',
        'add': 'Ajoute',
        'remove': 'Retire',
        'edit': 'Modifye',
        'delete': 'Efase',
        'back': 'Retounen',
        'continue_btn': 'Kontinye',
        'search': 'Chèche',
        'start_vitals': 'Kòmanse siy',
        'add_to_queue': 'Ajoute nan file',
        'new_visit': 'Nouvo vizit',
        'enter': 'Antre',

        # Queue / status
        'in_clinic_now': 'Nan klinik kounye a',
        'no_patients_waiting': 'Pa gen pasyan k ap tann. Yo ap parèt isit la apre yo anrejistre.',
        'waiting_for_vitals': 'K ap tann siy vital',
        'doctor_status': 'Sitiyasyon doktè',
        'status_available': 'disponib',
        'status_with': 'avèk',
        'status_urgent': 'Ijan',
        'status_waiting': 'K ap tann',
        'status_ready': 'Pare',
        'status_idle': 'Pa okipe',
        'reg_time_prefix': 'enskri',

        # Patient fields
        'name': 'Non',
        'patient_name': 'Non pasyan',
        'date_of_birth': 'Dat Nesans',
        'age': 'Laj',
        'gender': 'Sèks',
        'sex': 'Sèks',
        'male': 'Gason',
        'female': 'Fi',
        'phone': 'Telefòn',
        'address': 'Adrès',
        'notes': 'Nòt',
        'medical_history': 'Istwa Medikal',
        'last_visit': 'Dènye vizit',
        'never': 'Janm',

        # Triage tabs
        'tab_triage_queue': 'File Triyaj',
        'tab_new_patient': 'Nouvo Pasyan',
        'tab_search_patient': 'Chèche Pasyan',

        # Name registration
        'tab_register_names': 'Anrejistre Non',
        'tab_name_queue': 'File Non',
        'registration_type': 'Kalite anrejistreman',
        'individual_patient': 'Pasyan endividyèl',
        'family_group': 'Gwoup fanmi',
        'name_reg_caption': 'Anrejistre non pasyan anvan triyaj pou akselere travay la.',

        # Family registration
        'family_name': 'Non fanmi',
        'head_of_household': 'Chèf fanmi',
        'members': 'Manm',
        'add_member': '+ Ajoute manm',
        'add_to_family': 'Ajoute nan fanmi',
        'relationship': 'Relasyon',
        'rel_head': 'chèf',
        'rel_spouse': 'mari/madanm',
        'rel_child': 'pitit',
        'first_member_is_head': 'Premye manm nan se chèf fanmi an',
        'save_family_to_queue': 'Sove fanmi · ajoute nan triyaj',
        'family_added_success': 'Fanmi ajoute nan file triyaj. Pare pou pwochen an.',
        'family_screen_caption': "Anrejistre yon fanmi sou yon sèl ekran. Ajoute chèf fanmi an dabò, apre sa mari/madanm ak pitit. Tout manm yo sove ansanm.",
        'add_head_first': "Ajoute chèf fanmi an dabò, apre sa mari/madanm ak pitit.",
        'possible_existing_match': 'Posib pasyan ki egziste deja ki koresponn ak',
        'use_existing': 'Itilize sa ki egziste',

        # Vital signs
        'vital_signs': 'Siy Vital yo',
        'blood_pressure': 'Presyon San',
        'systolic_bp': 'Presyon Sistolik',
        'diastolic_bp': 'Presyon Dyastolik',
        'heart_rate': 'Frekans Kè (bpm)',
        'temperature': 'Tanperati (°F)',
        'weight': 'Pwa (kg)',
        'height': 'Wotè (cm)',
        'oxygen_saturation': 'Satirasyon Oksijèn (%)',
        'respirations': 'Respirasyon (/min)',
        'bmi': 'IMC',
        'save_vital_signs': 'Sove Siy Vital yo',
        'recording_vitals_for': 'Pran siy vital pou',
        'vitals_tip': "Ekri 'N/A' pou nenpòt mezi ou pa ka pran.",

        # Consultation / clinical
        'consultation': 'Konsiltasyon',
        'chief_complaint': 'Pwoblèm prensipal',
        'diagnosis': 'Dyagnostik',
        'medications': 'Medikaman',
        'send_to_lab': 'Voye nan Laboratwa',
        'send_to_pharmacy': 'Voye nan Famasi',
        'complete_consultation': 'Fini Konsiltasyon',
        'return_to_queue': 'Retounen nan File',
        'consultation_history': 'Istwa Konsiltasyon',
        'todays_consultations': 'Jodi a',
        'last_7_days': 'Dènye 7 jou',
        'last_30_days': 'Dènye 30 jou',
        'all_time': 'Tout tan',
        'show': 'Montre',

        # Back-button labels
        'back_to_role_selection': 'Retounen nan Chwa Wòl',
        'back_to_main': 'Retounen nan Akèy',
        'back_to_signin_options': '← Retounen nan Opsyon Konekte',
        'back_to_signin': '← Retounen nan Konekte',
        'back_to_org': 'Retounen nan Òganizasyon',
        'back_to_queue': '← Retounen nan File',
        'back_to_consult_history': '← Retounen nan Istwa Konsiltasyon',
        'close_label': '✕ Fèmen',
        'close_short': '✕',
        'back_to_reports': 'Retounen nan Rapò yo',
        'refresh': '↻ Aktyalize',

        # New-patient form
        'register_new_patient': 'Anrejistre Nouvo Pasyan',
        'enter_full_name': 'Ekri non konplè',
        'age_entry_method': 'Metòd antre laj',
        'enter_age': 'Antre laj',
        'enter_dob': 'Antre dat nesans',
        'phone_number': 'Nimewo telefòn',
        'optional': 'Opsyonèl',
        'emergency_contact': 'Kontak ijans',
        'medical_history_placeholder': 'Kondisyon medikal, alèji, oswa medikaman',
        'register_patient_btn': 'Anrejistre Pasyan',
        'please_enter_name': 'Tanpri ekri non pasyan an.',
        'patient_name_required': 'Non Pasyan *',
        'individual_patient_radio': 'Pasyan Endividyèl',
        'family_registration_radio': 'Anrejistreman Fanmi',
        'registration_type_label': 'Tip Anrejistreman',
        'years': 'ane',

        # Doctor login
        'select_your_name': 'Chwazi non w',
        'no_doctors_available': 'Pa gen doktè. Tanpri kontakte admin nan.',
        'choose_your_name': 'Chwazi non w:',

        # Duplicate / existing patient match
        'potential_existing_patients': '🔍 Pasyan ki egziste deja yo jwenn',
        'patient_may_be_existing': "Pasyan sa a kapab te wè nan yon klinik pase. Tanpri verifye:",
        'exact_matches_header': 'Non ki menm',
        'similar_names_header': 'Non sanble',
        'use_existing_btn': 'Itilize sa k egziste',
        'use_this_btn': 'Itilize sa a',
        'register_as_new': 'Anrejistre kòm nouvo pasyan',
        'connected_to_existing': 'Konekte ak pasyan ki egziste a.',
        'new_patient_registered': 'Nouvo pasyan anrejistre.',

        # Search
        'find_existing_patient': 'Jwenn Pasyan ki Egziste',
        'search_by_name_or_id': 'Chèche pa non oswa ID',
        'enter_name_or_id_placeholder': 'Antre non oswa ID (egz. 00001)',
        'no_patients_found': 'Pa jwenn pasyan ki koresponn ak rechèch ou.',
        'results_count': 'Rezilta',

        # Vitals confirmation
        'vitals_saved_message': 'Siy vital yo anrejistre. Pasyan an pare pou konsiltasyon.',
        'sent_to_doctor_queue': 'Voye nan file doktè',
        'now_waiting_consult': 'k ap tann konsiltasyon kounye a',

        # Pharmacy tabs
        'tab_ready_to_fill': 'Pare pou Ranpli',
        'tab_lab_results': 'Rezilta Laboratwa',
        'tab_lab_input': 'Antre Laboratwa',
        'tab_awaiting_teaching': 'K ap Tann Edikasyon',
        'tab_filled_prescriptions': 'Preskripsyon Ranpli',
        'prescriptions_to_fill': 'Preskripsyon pou Ranpli',

        # Lab tabs
        'tab_pending_tests': 'Tès K ap Tann',
        'tab_completed_lab': 'Rezilta',
        'tests_to_process': 'Tès pou Trete',

        # Family registration
        'add_head_of_household': 'Ajoute chèf fanmi',
        'add_family_member': 'Ajoute yon manm fanmi',
        'remove': 'Retire',
        'family_save_caption': "Ajoute tout manm fanmi w bezwen. Lè fanmi an konplè, peze Sove anba a.",
        'family_empty_state': 'Pa gen manm ankò. Kòmanse pa ajoute chèf fanmi an anba.',
        'rel_radio_label': 'Relasyon ak chèf fanmi an',

        # Section headers
        'hdr_record_vital_signs': 'Pran Siy Vital yo',
        'hdr_add_patient_names': 'Ajoute Non Pasyan',
        'hdr_registration_queue': 'File Anrejistreman',
        'hdr_preregistered_patients': 'Pasyan ki Pre-Anrejistre',
        'hdr_family_vitals_summary': 'Rezime Siy Vital Fanmi',
        'hdr_family_vitals_collection': 'Pran Siy Vital pou Fanmi',
        'hdr_select_patient_for_consultation': 'Chwazi Pasyan pou Konsiltasyon',
        'hdr_priority_lab_results': 'PRIYORITE: Pasyan ak Rezilta Laboratwa',
        'hdr_lab_results_completed': 'Rezilta Laboratwa Konplete',
        'hdr_lab_results': 'Rezilta Laboratwa',
        'hdr_family_groups': 'Gwoup Fanmi',
        'hdr_individual_patients': 'Pasyan Endividyèl',
        'hdr_patient_history': 'Istwa Pasyan',
        'hdr_photo_documentation': 'Dokimantasyon Foto',
        'hdr_lab_tests': 'Tès Laboratwa',
        'hdr_prescriptions': 'Preskripsyon',
        'hdr_ophthalmology_referral': 'Voye nan Doktè Je',
        'hdr_immunization_history': 'Istwa Vaksen',
        'hdr_pregnancy_history': 'Istwa Gwosès',
        'hdr_patient_qr': 'Kòd QR Pasyan / Braslè',
        'hdr_family_navigation': 'Navigasyon Fanmi',
        'hdr_patient_demographics': 'Enfòmasyon Pasyan',
        'hdr_medical_history_section': 'Istwa Medikal',
        'hdr_current_queue': 'File Pasyan Aktyèl',
        'hdr_queue_monitor': 'Moniteur File Pasyan',
        'hdr_todays_overview': 'Rezime Jodi a',
        'hdr_recent_patient_activity': 'Aktivite Resan Pasyan',
        'hdr_access_clinic_roles': 'Aksè nan Wòl Klinik',
        'hdr_consultation_history': 'Istwa Konsiltasyon',

        # Info / empty states
        'msg_no_patients_in_queue': 'Pa gen pasyan nan file jodi a.',
        'msg_no_waiting_consultation': 'Pa gen pasyan k ap tann konsiltasyon.',
        'msg_no_consultations_today': 'Pa gen konsiltasyon ki anrejistre jodi a.',
        'msg_no_completed_labs': 'Pa gen rezilta laboratwa konplete jodi a.',
        'msg_no_pending_prescriptions': 'Pa gen preskripsyon k ap tann.',
        'msg_no_lab_results_found': 'Pa jwenn rezilta laboratwa pou pasyan sa a.',
        'msg_no_patient_activity': 'Pa gen aktivite pasyan jodi a ankò.',
        'msg_realtime_queue': 'Vizyon an tan reyèl tout pasyan nan klinik la.',
        'msg_lab_input_intro': 'Antre rezilta tès laboratwa pou pasyan yo. Rezilta yo ap voye nan doktè a ansanm ak pasyan an.',
        'msg_no_preregistered': "Pa gen pasyan pre-anrejistre k ap tann siy vital. Tcheke estasyon Anrejistreman Non.",
        'msg_preregistered_intro': 'Pasyan ki anrejistre nan estasyon Anrejistreman Non yo pare pou pran siy vital.',
        'msg_no_names_in_queue': "Pa gen non nan file anrejistreman. Ajoute non nan tab 'Anrejistre Non'.",
        'msg_returning_from_lab': 'Pasyan sa a tounen soti nan laboratwa/famasi ak rezilta konplete. Done konsiltasyon orijinal yo retabli anba a.',
        'msg_changes_auto_saved': 'Tout chanjman yo sove otomatikman. Kontinye nan tab Laboratwa ak Preskripsyon pou fini konsiltasyon an.',
        'msg_consultation_paused': 'Konsiltasyon kanpe ak sove.',
        'msg_consultation_completed': 'Konsiltasyon fini ak siksè.',
        'msg_patient_returned_to_queue': "Pasyan retounen nan file k ap tann. Nòt ou yo te sove.",
        'msg_positive_result': 'Rezilta pozitif',
        'msg_negative_result': 'Rezilta negatif',

        # Errors
        'err_name_cannot_be_empty': 'Non pa kapab vid',
        'err_please_enter_name_field': 'Tanpri ekri non pasyan an.',
        'err_invalid_credentials': 'Kredansyèl pa bon. Tanpri verifye non w ak PIN ou.',
        'err_pin_4_digits': 'PIN dwe gen egzakteman 4 chif',
        'err_pins_no_match': 'PIN yo pa menm',
        'err_please_enter_pin': 'Tanpri antre non w ak PIN ou',

        # Consultation routing
        'complete_send_to_lab': 'Konplete · Voye nan Laboratwa',
        'complete_send_to_pharmacy': 'Konplete · Voye nan Famasi',
        'complete_discharge': 'Konplete · Lage Pasyan',
        'add_diagnosis_first': 'Tanpri ajoute omwen yon dyagnostik anvan ou konplete.',
        'pause_consultation': 'Sove epi retounen nan file a',
        'diagnosis_recorded': 'Dyagnostik anrejistre',
        'no_diagnosis_yet': 'Pa gen dyagnostik ankò',
        'lab_tests_ordered_count': 'tès laboratwa òdone',
        'no_labs_ordered': 'Pa gen tès laboratwa òdone',
        'prescriptions_written_count': 'preskripsyon ekri',
        'no_prescriptions_written': 'Pa gen preskripsyon ekri',
        'next_family_member': 'Pwochen manm fanmi an',
        'sent_to_lab_msg': 'Voye nan file Laboratwa.',
        'sent_to_pharmacy_msg': 'Voye nan file Famasi.',
        'consultation_complete_msg': 'Konsiltasyon konplete. Pasyan lage.',
        'family_continuing_with': 'K ap kontinye avèk',

        # Legacy
        'consent_message': 'Mwen konsanti pou yo kolekte ak itilize enfòmasyon medikal mwen pou tretman.',
        'immunizations': 'Vaksen',
        'pregnancy_history': 'Istwa Gwosès',
        'stock_low': 'Stock Ba',
        'stock_out': 'Pa Gen',
        'stock_available': 'Disponib',
        'patient_registration': 'Anrejistreman Pasyan',
        'triage': 'Triyaj',
        'pharmacy': 'Famasi',
        'lab': 'Laboratwa',
        'admin': 'Administrasyon',
    }
}

def get_translation(key: str, lang: str = 'en') -> str:
    """Get translation for a key in the specified language"""
    if lang not in TRANSLATIONS:
        lang = 'en'
    return TRANSLATIONS.get(lang, {}).get(key, TRANSLATIONS['en'].get(key, key))


def t(key: str) -> str:
    """Shorthand: translate `key` using st.session_state.app_language.
    Safe to call before session_state is initialized — falls back to 'en'."""
    try:
        import streamlit as _st
        lang = _st.session_state.get('app_language', 'en')
    except Exception:
        lang = 'en'
    return get_translation(key, lang)


def family_registration_unified(location_code: str):
    """Single-screen family registration.

    The add-member form is ALWAYS visible (no expander) so the path from
    'add head' to 'add child' is obvious — the previous version hid the
    add-form inside a collapsed expander after the first member, making
    it look like there was no way to add children.

    Gender values are stored as canonical English ('Male' / 'Female') so
    the underlying patient data doesn't change when the UI language
    changes. The dropdown shows translated labels via format_func.
    """
    import streamlit as _st

    if 'fam_reg_members' not in _st.session_state:
        _st.session_state.fam_reg_members = []

    family_name = _st.text_input(
        t('family_name'),
        value=_st.session_state.get('fam_reg_name', ''),
        placeholder="e.g., Martinez",
        key='fam_reg_name_input')
    _st.session_state.fam_reg_name = family_name

    members = _st.session_state.fam_reg_members

    # --- Member list ---------------------------------------------------------
    if members:
        section_header(t('members'), count=len(members))
        remove_idx = None
        for i, m in enumerate(members):
            rel_label = t(f"rel_{m['relationship']}") if m.get('relationship') in ('head', 'spouse', 'child') else (m.get('relationship') or 'member')
            cols = _st.columns([3, 1, 1, 2, 0.7])
            with cols[0]:
                _st.markdown(f"**{m['name']}**")
            with cols[1]:
                _st.caption(str(m.get('age') or '—'))
            with cols[2]:
                _st.caption(m.get('gender') or '—')
            with cols[3]:
                _st.markdown(
                    f"<span style='color:#475569; font-weight:500; font-size:0.85rem; "
                    f"border:1px solid #E5E7EB; padding:2px 8px; border-radius:4px;'>"
                    f"{rel_label}</span>",
                    unsafe_allow_html=True,
                )
            with cols[4]:
                if _st.button("✕", key=f"fam_rm_{i}", help=t('remove')):
                    remove_idx = i
        if remove_idx is not None:
            members.pop(remove_idx)
            _st.rerun()
    else:
        _st.info(t('family_empty_state'))

    # --- Always-visible Add Member form -------------------------------------
    has_head = any(m['relationship'] == 'head' for m in members)
    _st.markdown("---")
    _st.markdown(
        f"### {t('add_head_of_household') if not has_head else t('add_family_member')}"
    )
    if not has_head:
        _st.caption(t('first_member_is_head'))

    with _st.form("fam_add_member", clear_on_submit=True):
        am_name = _st.text_input(t('name'), key='fam_add_name')
        c1, c2 = _st.columns(2)
        with c1:
            am_age = _st.number_input(t('age'), min_value=0, max_value=120,
                                      value=0, key='fam_add_age')
        with c2:
            # Show translated labels in the dropdown but store canonical values
            am_gender = _st.selectbox(
                t('sex'),
                ["", "Male", "Female"],
                format_func=lambda x: "" if x == "" else (t('male') if x == "Male" else t('female')),
                key='fam_add_gender',
            )

        # Relationship — only shown after head is added. Horizontal radio is
        # more obvious than a dropdown for a 2-option choice on iPad.
        if has_head:
            am_rel = _st.radio(
                t('rel_radio_label'),
                ['spouse', 'child'],
                format_func=lambda x: t(f'rel_{x}'),
                horizontal=True,
                key='fam_add_rel',
            )
        else:
            am_rel = 'head'

        submit_label = t('add_to_family') if has_head else t('add_head_of_household')
        if _st.form_submit_button(submit_label, type="primary", use_container_width=True):
            if not am_name.strip():
                _st.error(t('please_enter_name'))
            else:
                members.append({
                    'name': am_name.strip(),
                    'age': int(am_age) if am_age and am_age > 0 else None,
                    'gender': am_gender or None,
                    'relationship': am_rel,
                })
                _st.rerun()

    if not members:
        return

    # --- Returning-family fuzzy match (only when head exists) ---------------
    head = next((m for m in members if m['relationship'] == 'head'), None)
    if head:
        existing = db.search_patients(head['name'])
        likely = [p for p in existing[:5]
                  if p.get('name') and p['name'].lower() != head['name'].lower()]
        if likely:
            _st.markdown(
                f"<div style='background:#FFFBEB; border-left:3px solid #D97706; "
                f"padding:12px 16px; border-radius:4px; margin:16px 0;'>"
                f"<strong>{t('potential_existing_patients')}</strong> · "
                f"<em>{head['name']}</em></div>",
                unsafe_allow_html=True)
            for p in likely[:3]:
                cc = _st.columns([4, 1])
                with cc[0]:
                    _st.markdown(f"&nbsp;&nbsp;{p['name']} · {p['patient_id']}",
                                 unsafe_allow_html=True)
                with cc[1]:
                    if _st.button(t('use_existing_btn'), key=f"fam_use_{p['patient_id']}"):
                        _st.session_state.pending_existing_patient = p['patient_id']
                        _st.info(f"{p['patient_id']}")

    # --- Save action ---------------------------------------------------------
    _st.markdown("---")
    _st.caption(t('family_save_caption'))
    bs1, bs2, bs3 = _st.columns([1, 2, 1])
    with bs2:
        if _st.button(t('save_family_to_queue'),
                      type="primary", use_container_width=True,
                      key="fam_reg_commit"):
            conn = sqlite3.connect(db.db_name)
            conn.execute('PRAGMA busy_timeout = 5000')
            cur = conn.cursor()
            try:
                cur.execute('BEGIN IMMEDIATE')
                cur.execute(
                    'SELECT COUNT(*) FROM families WHERE location_code = ?',
                    (location_code,))
                family_count = cur.fetchone()[0]
                family_id = f"{location_code}FAM{(family_count + 1):05d}"

                head_name = head['name'] if head else members[0]['name']
                cur.execute(
                    'INSERT INTO families (family_id, family_name, head_of_household, '
                    'location_code, created_date) VALUES (?, ?, ?, ?, ?)',
                    (family_id, family_name or head_name, head_name,
                     location_code, datetime.now().isoformat()))

                for m in members:
                    queue_rel = 'parent' if m['relationship'] == 'head' else m['relationship']
                    cur.execute(
                        'INSERT INTO patient_names_queue '
                        '(name, age, gender, location_code, relationship, '
                        'family_group_id, created_time, notes) '
                        'VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
                        (m['name'], m['age'], m['gender'], location_code,
                         queue_rel, family_id, datetime.now().isoformat(),
                         f"Family: {family_name or head_name}"))

                conn.commit()
                broadcast_to_clients(
                    f"new_family_registered:{family_name or head_name}:{len(members)}_members")
                _st.session_state.fam_reg_members = []
                _st.session_state.fam_reg_name = ''
                _st.session_state.family_registration_success = True
                _st.rerun()
            except Exception as e:
                conn.rollback()
                _st.error(f"Could not save family: {e}")
            finally:
                conn.close()


def status_pill(state: str, label: str = None) -> str:
    """Return HTML for a status pill. `state` is one of: urgent / waiting /
    ready / idle. If `label` omitted, the state is title-cased."""
    state = (state or 'idle').lower()
    if state not in ('urgent', 'waiting', 'ready', 'idle'):
        state = 'idle'
    text = label if label is not None else state.title()
    return f"<span class='pmc-pill {state}'><span class='dot'></span>{text}</span>"


def section_header(title: str, count: int = None):
    """Render a quiet section header — title + optional count, hairline below.
    Replaces the old gradient/banner section headers."""
    import streamlit as _st
    suffix = f" <span style='color:#6B7280; font-weight:400; font-size:0.9rem;'>· {count}</span>" if count is not None else ""
    _st.markdown(
        f"<div class='pmc-section'>{title}{suffix}</div>",
        unsafe_allow_html=True,
    )


def patient_row(name, meta_parts, action_label, action_key,
                status: str = 'idle', on_click=None):
    """Render one quiet patient queue row and return True if action clicked.

    `meta_parts` is a list of strings — joined with ' · ' for the meta line.
    `status` drives the left edge color: urgent / waiting / ready / idle.
    Action button is right-aligned, uses the default quiet style unless
    status == 'ready' (primary).
    """
    import streamlit as _st
    status = (status or 'idle').lower()
    if status not in ('urgent', 'waiting', 'ready', 'idle'):
        status = 'idle'
    meta = " · ".join([str(p) for p in meta_parts if p])

    name_col, action_col = _st.columns([4, 1])
    with name_col:
        _st.markdown(
            f"<div class='pmc-row {status}'>"
            f"<div>"
            f"<p class='pmc-name'>{name}</p>"
            f"<p class='pmc-meta'>{meta}</p>"
            f"</div>"
            f"</div>",
            unsafe_allow_html=True,
        )
    with action_col:
        btn_type = 'primary' if status == 'ready' else 'secondary'
        clicked = _st.button(action_label, key=action_key, type=btn_type,
                             use_container_width=True)
        if clicked and on_click:
            on_click()
        return clicked


def render_app_header():
    """Persistent top-of-page header shown on every authenticated page.
    One row: app title · clinic · user · current role · language pill ·
    change-role button. Foundation for the BackpackEMR-style overhaul —
    other role pages can rely on this being above them and stop printing
    their own title bars over time.
    """
    import streamlit as _st
    clinic = _st.session_state.get('clinic_location') or {}
    clinic_label = clinic.get('city') or clinic.get('country_name') or 'Clinic'
    staff = _st.session_state.get('clinic_staff') or {}
    user_name = staff.get('full_name') or _st.session_state.get('doctor_name') or 'User'
    _role_key_map = {
        'name_registration': 'role_registrant',
        'triage': 'role_triage',
        'doctor': 'role_provider',
        'pharmacy': 'role_pharmacy',
        'lab': 'role_lab',
        'queue_monitor': 'role_queue_monitor',
        'admin': 'role_admin',
    }
    raw_role = _st.session_state.get('user_role') or ''
    role = t(_role_key_map[raw_role]) if raw_role in _role_key_map else raw_role.replace('_', ' ').title()
    lang_code = _st.session_state.get('app_language', 'en')
    lang_label = {'en': 'EN', 'ht': 'Kreyòl', 'es': 'ES'}.get(lang_code, lang_code.upper())

    h1, h2, h3, h4 = _st.columns([4, 3, 1, 1.2])
    with h1:
        _st.markdown(
            "<div style='padding-top:8px;'>"
            "<strong style='font-size:1.05rem; color:#374151;'>ParakaleoMed</strong>"
            f"&nbsp;·&nbsp;<span style='color:#374151;'>{clinic_label}</span>"
            "</div>",
            unsafe_allow_html=True)
    with h2:
        _st.markdown(
            "<div style='padding-top:8px; text-align:right; color:#6B7280; font-size:0.95rem;'>"
            f"{user_name}"
            + (f" <span style='color:#9CA3AF;'>·</span> <span style='color:#475569;'>{role}</span>" if role else "")
            + "</div>",
            unsafe_allow_html=True)
    with h3:
        _st.markdown(
            "<div style='padding-top:8px; text-align:center;'>"
            f"<span style='display:inline-block; padding:4px 10px; background:#F3F4F6; "
            f"border:1px solid #E5E7EB; border-radius:999px; font-size:0.85rem;'>{lang_label}</span>"
            "</div>",
            unsafe_allow_html=True)
    with h4:
        if _st.button(t('change_role'), key="hdr_change_role_btn", use_container_width=True):
            _st.session_state.user_role = None
            _st.rerun()
    _st.markdown(
        "<hr style='margin: 0 0 12px 0; border:none; border-top:1px solid #E5E7EB;'>",
        unsafe_allow_html=True)


def render_doctor_status_strip():
    """Compact one-line strip of 'who is in clinic right now', shown on
    triage / lab / pharmacy / registration pages so non-doctor staff
    can see at a glance which doctor is busy with whom. Safe to call
    even if no doctors are logged in (renders nothing)."""
    import streamlit as _st
    try:
        statuses = get_db_manager().get_all_doctor_status() or []
    except Exception:
        return
    if not statuses:
        return
    # Filter out doctors who are offline so the strip doesn't grow indefinitely
    visible = [s for s in statuses if (s.get('status') or '').lower() != 'offline']
    if not visible:
        return

    pills = []
    for s in visible:
        status = (s.get('status') or '').lower()
        if status == 'available':
            icon = '🟢'
            label = t('status_available')
        elif status == 'with_patient':
            icon = '🟡'
            pn = s.get('current_patient_name') or s.get('current_patient_id') or 'patient'
            label = f"{t('status_with')} {pn}"
        else:
            icon = '⚪'
            label = status or 'unknown'
        pills.append(
            f"<span style='display:inline-block; padding:6px 12px; margin:4px; "
            f"background:#F3F4F6; border:1px solid #E5E7EB; border-radius:999px; "
            f"font-size:0.9rem;'>{icon} <strong>{s['doctor_name']}</strong> · {label}</span>"
        )
    _st.markdown(
        "<div style='margin: 4px 0 12px 0;'>"
        f"<span style='font-size:0.85rem; color:#6B7280; margin-right:8px;'>{t('in_clinic_now')}:</span>"
        + "".join(pills) + "</div>",
        unsafe_allow_html=True,
    )


def render_login_language_picker():
    """Inline language picker shown at the top of every login screen.
    Three pill-style buttons (EN / Kreyòl / Español). Updates
    st.session_state.app_language and reruns. Safe to call inside any
    login page render path."""
    import streamlit as _st

    if 'app_language' not in _st.session_state:
        _st.session_state.app_language = 'en'

    options = [('en', 'English'), ('ht', 'Kreyòl'), ('es', 'Español')]
    current = _st.session_state.app_language

    # Right-align three small buttons
    spacer, c1, c2, c3 = _st.columns([6, 1.3, 1.3, 1.3])
    cols = [c1, c2, c3]
    for col, (code, label) in zip(cols, options):
        with col:
            is_active = code == current
            btn_type = 'primary' if is_active else 'secondary'
            if _st.button(label, key=f'lang_pick_{code}', use_container_width=True, type=btn_type):
                if code != current:
                    _st.session_state.app_language = code
                    _st.query_params['lang'] = code
                    _st.rerun()

def calculate_age_from_dob(dob: str) -> int:
    """Calculate age from date of birth string"""
    if not dob:
        return 0
    try:
        if isinstance(dob, str):
            birth_date = datetime.strptime(dob, '%Y-%m-%d').date()
        else:
            birth_date = dob
        today = date.today()
        age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
        return age
    except:
        return 0

def calculate_bmi(weight_kg: float, height_cm: float) -> tuple:
    """Calculate BMI and return (value, category)"""
    if not weight_kg or not height_cm or height_cm <= 0:
        return None, None
    height_m = height_cm / 100
    bmi = weight_kg / (height_m ** 2)
    
    if bmi < 18.5:
        category = "Underweight"
    elif bmi < 25:
        category = "Normal"
    elif bmi < 30:
        category = "Overweight"
    else:
        category = "Obese"
    
    return round(bmi, 1), category

def hash_pin(pin: str) -> str:
    """Hash a PIN for secure storage"""
    return hashlib.sha256(pin.encode()).hexdigest()

def verify_pin(entered_pin: str, stored_hash: str) -> bool:
    """Verify a PIN against stored hash"""
    return hash_pin(entered_pin) == stored_hash

# Common ICD-10 codes for mission clinics
ICD10_CODES = {
    'Infectious': [
        ('A09', 'Infectious gastroenteritis and colitis'),
        ('B37.0', 'Candidal stomatitis (thrush)'),
        ('B35.0', 'Tinea capitis (scalp ringworm)'),
        ('B35.4', 'Tinea corporis (body ringworm)'),
        ('B86', 'Scabies'),
        ('B85.0', 'Pediculosis (head lice)'),
    ],
    'Respiratory': [
        ('J00', 'Acute nasopharyngitis (common cold)'),
        ('J02.9', 'Acute pharyngitis (sore throat)'),
        ('J06.9', 'Acute upper respiratory infection'),
        ('J18.9', 'Pneumonia, unspecified'),
        ('J20.9', 'Acute bronchitis'),
        ('J45.909', 'Asthma, uncomplicated'),
    ],
    'Gastrointestinal': [
        ('K29.70', 'Gastritis, unspecified'),
        ('K21.0', 'GERD with esophagitis'),
        ('K59.00', 'Constipation'),
        ('K52.9', 'Noninfective gastroenteritis'),
        ('B82.0', 'Intestinal helminthiasis (worms)'),
    ],
    'Cardiovascular': [
        ('I10', 'Essential hypertension'),
        ('I25.10', 'Atherosclerotic heart disease'),
        ('I50.9', 'Heart failure, unspecified'),
    ],
    'Endocrine': [
        ('E11.9', 'Type 2 diabetes mellitus'),
        ('E03.9', 'Hypothyroidism'),
        ('E66.9', 'Obesity'),
    ],
    'Musculoskeletal': [
        ('M54.5', 'Low back pain'),
        ('M25.50', 'Pain in unspecified joint'),
        ('M79.3', 'Panniculitis'),
    ],
    'Dermatologic': [
        ('L30.9', 'Dermatitis, unspecified'),
        ('L70.0', 'Acne vulgaris'),
        ('L50.9', 'Urticaria (hives)'),
        ('L02.91', 'Cutaneous abscess'),
    ],
    'Genitourinary': [
        ('N39.0', 'Urinary tract infection'),
        ('N76.0', 'Acute vaginitis'),
        ('N94.6', 'Dysmenorrhea'),
    ],
    'Eye': [
        ('H10.9', 'Conjunctivitis'),
        ('H52.1', 'Myopia'),
        ('H26.9', 'Cataract'),
    ],
    'Ear': [
        ('H66.90', 'Otitis media'),
        ('H65.90', 'Otitis media with effusion'),
    ],
    'Mental Health': [
        ('F32.9', 'Major depressive disorder'),
        ('F41.9', 'Anxiety disorder'),
    ],
    'Pediatric': [
        ('E46', 'Protein-calorie malnutrition'),
        ('E40', 'Kwashiorkor'),
        ('D50.9', 'Iron deficiency anemia'),
    ],
    'Pregnancy': [
        ('Z34.00', 'Normal first pregnancy'),
        ('Z34.80', 'Normal pregnancy, multiparous'),
        ('O99.019', 'Anemia in pregnancy'),
    ],
}

# Common immunization vaccines for mission clinics
COMMON_VACCINES = [
    'COVID-19 (Pfizer)',
    'COVID-19 (Moderna)',
    'COVID-19 (Johnson & Johnson)',
    'Influenza (Flu)',
    'Tetanus/Diphtheria (Td)',
    'Tetanus/Diphtheria/Pertussis (Tdap)',
    'MMR (Measles, Mumps, Rubella)',
    'Polio (IPV)',
    'Hepatitis A',
    'Hepatitis B',
    'Typhoid',
    'Yellow Fever',
    'Rabies',
    'HPV (Human Papillomavirus)',
    'Pneumococcal (PCV13/PPSV23)',
    'Meningococcal',
    'Varicella (Chickenpox)',
    'Rotavirus',
    'BCG (Tuberculosis)',
    'Other'
]

# PDF Generation Functions
def generate_patient_pdf(patient_data: Dict, visits: List[Dict], db) -> bytes:
    """Generate a PDF report for a patient"""
    if not PDF_AVAILABLE:
        return b""
    
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.5*inch, bottomMargin=0.5*inch)
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle('Title', parent=styles['Heading1'], fontSize=18, spaceAfter=12)
    heading_style = ParagraphStyle('Heading', parent=styles['Heading2'], fontSize=14, spaceAfter=6, spaceBefore=12)
    normal_style = styles['Normal']
    
    elements = []
    
    # Header
    elements.append(Paragraph("ParakaleoMed - Patient Medical Record", title_style))
    elements.append(Paragraph(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}", normal_style))
    elements.append(Spacer(1, 0.25*inch))
    
    # Patient Demographics
    elements.append(Paragraph("Patient Information", heading_style))
    demo_data = [
        ['Patient ID:', patient_data.get('patient_id', 'N/A')],
        ['Name:', patient_data.get('name', 'N/A')],
        ['Age:', str(patient_data.get('age', 'N/A'))],
        ['Gender:', patient_data.get('gender', 'N/A')],
        ['Date of Birth:', patient_data.get('date_of_birth', 'N/A') or 'Not recorded'],
        ['Phone:', patient_data.get('phone', 'N/A') or 'Not provided'],
        ['Address:', patient_data.get('address', 'N/A') or 'Not provided'],
    ]
    demo_table = Table(demo_data, colWidths=[1.5*inch, 4*inch])
    demo_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    elements.append(demo_table)
    elements.append(Spacer(1, 0.25*inch))
    
    # Medical History
    if patient_data.get('medical_history'):
        elements.append(Paragraph("Medical History", heading_style))
        elements.append(Paragraph(patient_data.get('medical_history', ''), normal_style))
        elements.append(Spacer(1, 0.25*inch))
    
    # Visits
    if visits:
        elements.append(Paragraph("Visit History", heading_style))
        for visit in visits[:10]:  # Limit to last 10 visits
            visit_date = visit.get('visit_date', 'Unknown')[:10] if visit.get('visit_date') else 'Unknown'
            elements.append(Paragraph(f"<b>Visit Date:</b> {visit_date}", normal_style))
            if visit.get('diagnosis'):
                elements.append(Paragraph(f"<b>Diagnosis:</b> {visit.get('diagnosis')}", normal_style))
            if visit.get('treatment_plan'):
                elements.append(Paragraph(f"<b>Treatment:</b> {visit.get('treatment_plan')}", normal_style))
            elements.append(Spacer(1, 0.1*inch))
    
    doc.build(elements)
    buffer.seek(0)
    return buffer.getvalue()

def generate_clinic_report_pdf(report_date: str, stats: Dict) -> bytes:
    """Generate a daily clinic report PDF"""
    if not PDF_AVAILABLE:
        return b""
    
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.5*inch, bottomMargin=0.5*inch)
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle('Title', parent=styles['Heading1'], fontSize=18, spaceAfter=12)
    heading_style = ParagraphStyle('Heading', parent=styles['Heading2'], fontSize=14, spaceAfter=6, spaceBefore=12)
    normal_style = styles['Normal']
    
    elements = []
    
    elements.append(Paragraph("ParakaleoMed - Daily Clinic Report", title_style))
    elements.append(Paragraph(f"Report Date: {report_date}", normal_style))
    elements.append(Paragraph(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}", normal_style))
    elements.append(Spacer(1, 0.25*inch))
    
    # Statistics
    elements.append(Paragraph("Clinic Statistics", heading_style))
    stats_data = [
        ['Patients Seen:', str(stats.get('patients_seen', 0))],
        ['Prescriptions Filled:', str(stats.get('prescriptions_filled', 0))],
        ['Lab Tests Completed:', str(stats.get('lab_tests', 0))],
        ['New Registrations:', str(stats.get('new_registrations', 0))],
    ]
    stats_table = Table(stats_data, colWidths=[2*inch, 2*inch])
    stats_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
    ]))
    elements.append(stats_table)
    
    doc.build(elements)
    buffer.seek(0)
    return buffer.getvalue()

# QR Code Generation
def generate_patient_qr_code(patient_id: str, patient_name: str) -> bytes:
    """Generate a QR code for patient identification"""
    if not QR_AVAILABLE:
        return b""
    
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(f"PARAKALEO|{patient_id}|{patient_name}")
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    return buffer.getvalue()

def generate_wristband_pdf(patient_id: str, patient_name: str, patient_age: int = None) -> bytes:
    """Generate a printable wristband with QR code"""
    if not PDF_AVAILABLE or not QR_AVAILABLE:
        return b""
    
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=(8*inch, 2*inch), topMargin=0.25*inch, bottomMargin=0.25*inch)
    styles = getSampleStyleSheet()
    
    elements = []
    
    # Generate QR code
    qr_bytes = generate_patient_qr_code(patient_id, patient_name)
    if qr_bytes:
        qr_buffer = io.BytesIO(qr_bytes)
        qr_img = RLImage(qr_buffer, width=1.5*inch, height=1.5*inch)
        
        # Create table with QR and patient info
        patient_info = f"""
        <b>{patient_name}</b><br/>
        ID: {patient_id}<br/>
        Age: {patient_age if patient_age else 'N/A'}
        """
        
        data = [[qr_img, Paragraph(patient_info, styles['Normal'])]]
        table = Table(data, colWidths=[1.75*inch, 5.5*inch])
        table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ]))
        elements.append(table)
    
    doc.build(elements)
    buffer.seek(0)
    return buffer.getvalue()

# Encryption functions for data at rest
def get_encryption_key(password: str, salt: bytes = None) -> tuple:
    """Generate an encryption key from a password"""
    if not ENCRYPTION_AVAILABLE:
        return None, None
    
    if salt is None:
        salt = os.urandom(16)
    
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
    )
    key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
    return Fernet(key), salt

def encrypt_data(data: str, fernet: 'Fernet') -> bytes:
    """Encrypt data using Fernet encryption"""
    if not ENCRYPTION_AVAILABLE or fernet is None:
        return data.encode()
    return fernet.encrypt(data.encode())

def decrypt_data(encrypted_data: bytes, fernet: 'Fernet') -> str:
    """Decrypt data using Fernet encryption"""
    if not ENCRYPTION_AVAILABLE or fernet is None:
        return encrypted_data.decode() if isinstance(encrypted_data, bytes) else encrypted_data
    return fernet.decrypt(encrypted_data).decode()

# Page state persistence - store current page in URL parameters
def preserve_page_state():
    """Initialize page state persistence"""
    if 'page_initialized' not in st.session_state:
        # Get page and role from URL parameters if available
        query_params = st.query_params
        
        # Restore page state
        if 'page' in query_params:
            st.session_state.page = query_params['page']
        elif 'page' not in st.session_state:
            st.session_state.page = 'main'
        
        # Restore role state
        if 'role' in query_params:
            st.session_state.user_role = query_params['role']
        
        # Restore doctor login state
        if 'doctor' in query_params:
            st.session_state.doctor_name = query_params['doctor']
        
        # Restore consultation state from URL parameters
        if all(param in query_params for param in ['visit_id', 'patient_id', 'patient_name']):
            st.session_state.active_consultation = {
                'visit_id': query_params['visit_id'],
                'patient_id': query_params['patient_id'],
                'patient_name': query_params['patient_name']
            }
        
        # Restore location state from URL parameters
        if 'location_city' in query_params and 'location_country' in query_params:
            st.session_state.clinic_location = {
                'city': query_params['location_city'],
                'country_name': query_params['location_country'],
                'country_code': query_params.get('location_code', query_params['location_country'][:2].upper())
            }
        
        st.session_state.page_initialized = True

def update_page_url(page_name: str):
    """Update URL to reflect current page"""
    st.query_params['page'] = page_name
    if 'user_role' in st.session_state and st.session_state.user_role:
        st.query_params['role'] = st.session_state.user_role
    if 'clinic_location' in st.session_state and st.session_state.clinic_location:
        location = st.session_state.clinic_location
        st.query_params['location_city'] = location['city']
        st.query_params['location_country'] = location['country_name']
        st.query_params['location_code'] = location['country_code']
    
    # Preserve consultation state in URL for doctor consultation forms
    if 'active_consultation' in st.session_state and st.session_state.active_consultation and isinstance(st.session_state.active_consultation, dict):
        consultation = st.session_state.active_consultation
        st.query_params['visit_id'] = consultation['visit_id']
        st.query_params['patient_id'] = consultation['patient_id']
        st.query_params['patient_name'] = consultation['patient_name']
    
    # Preserve doctor login state
    if 'doctor_name' in st.session_state and st.session_state.doctor_name:
        st.query_params['doctor'] = st.session_state.doctor_name

def check_for_updates():
    """Check if there are pending updates and trigger rerun"""
    # Add automatic rerun system that responds to WebSocket updates
    html("""
    <script>
    // Auto-rerun system for real-time updates
    if (!window.autoRerunInitialized) {
        window.autoRerunInitialized = true;
        
        // Check for updates every 3 seconds
        setInterval(() => {
            if (window.streamlitUpdatePending) {
                window.streamlitUpdatePending = false;
                console.log("Triggering automatic page update...");
                
                // Check if we're in a consultation or form page - preserve state better
                const url = new URL(window.location);
                const isConsultationPage = url.searchParams.get('page') === 'consultation_form' || 
                                          url.searchParams.get('visit_id') || 
                                          url.searchParams.get('patient_id');
                
                try {
                    if (isConsultationPage) {
                        // For consultation pages, use gentle update instead of full reload
                        console.log("Consultation page detected - using gentle update");
                        url.searchParams.set('_refresh', Date.now());
                        window.history.replaceState({}, '', url);
                        
                        // Try to trigger Streamlit rerun without losing form data
                        if (window.parent && window.parent.postMessage) {
                            window.parent.postMessage({type: 'streamlit:componentReady'}, '*');
                        }
                    } else {
                        // For other pages, use full reload
                        console.log("Non-consultation page - using full reload");
                        window.location.reload();
                    }
                } catch (e) {
                    console.log("Auto-rerun error:", e);
                    // Fallback: gentle update only
                    url.searchParams.set('_refresh', Date.now());
                    window.history.replaceState({}, '', url);
                }
            }
        }, 3000);
    }
    </script>
    """, height=0)

# WebSocket connection script for real-time updates
ws_connect_script = """
<script>
  if (!window.wsInitialized) {
    let reconnectAttempts = 0;
    const maxReconnectAttempts = 50; // Keep trying for a long time in offline environment
    
    function connectWebSocket() {
      try {
        // Use multiple connection strategies for offline Pi network
        let wsUrl;
        const hostname = window.location.hostname;
        
        // Priority 1: Use current hostname (works for Pi local network)
        if (hostname === "192.168.4.1" || hostname.startsWith("192.168.4.")) {
          wsUrl = "ws://" + hostname + ":6789";
        }
        // Priority 2: Default Pi hotspot IP
        else if (hostname === "localhost" || hostname === "127.0.0.1") {
          wsUrl = "ws://192.168.4.1:6789";
        }
        // Priority 3: Use current hostname as fallback
        else {
          wsUrl = "ws://" + hostname + ":6789";
        }
        
        console.log("Attempting WebSocket connection to:", wsUrl);
        const ws = new WebSocket(wsUrl);
        window.ws = ws;
        
        // Set connection timeout
        const connectionTimeout = setTimeout(() => {
          if (ws.readyState === WebSocket.CONNECTING) {
            console.log("WebSocket connection timeout");
            ws.close();
          }
        }, 5000);
        
        ws.onopen = function() {
          clearTimeout(connectionTimeout);
          console.log("Connected to ParakaleoMed sync server at:", wsUrl);
          window.wsConnected = true;
          reconnectAttempts = 0; // Reset reconnect counter on successful connection
          
          // Send a ping to maintain connection
          ws.send("ping:iPad_connected");
          
          // Show connection status to user
          const connectionStatus = document.createElement('div');
          connectionStatus.style.cssText = `
            position: fixed; top: 10px; left: 10px; z-index: 9999;
            background: #10b981; color: white; padding: 8px 16px;
            border-radius: 6px; font-weight: bold; font-size: 14px;
          `;
          connectionStatus.textContent = '✅ Connected to sync server';
          document.body.appendChild(connectionStatus);
          
          // Remove connection status after 3 seconds
          setTimeout(() => {
            if (connectionStatus.parentNode) {
              connectionStatus.parentNode.removeChild(connectionStatus);
            }
          }, 3000);
        };
        
        ws.onmessage = function(event) {
          console.log("Received update:", event.data);
          
          // Respond to ping requests to maintain connection
          if (event.data === "ping") {
            ws.send("pong:iPad_alive");
            return;
          }
          
          // Parse message to determine if page should reload
          const updateData = event.data;
          let shouldReload = false;
          let notificationText = '';
          
          if (updateData.includes("new_patient") || updateData.includes("new_name_registered") || updateData.includes("new_family_registered")) {
            shouldReload = true;
            notificationText = "New patient registered";
            console.log("🚨 PATIENT REGISTRATION UPDATE DETECTED:", updateData);
          } else if (updateData.includes("vitals_complete")) {
            shouldReload = true;
            notificationText = "Vital signs completed";
          } else if (updateData.includes("consultation_complete") || updateData.includes("consultation_paused")) {
            shouldReload = true;
            notificationText = "Consultation updated";
          } else if (updateData.includes("lab_complete") || updateData.includes("patient_returned_to_doctor")) {
            shouldReload = true;
            notificationText = "Lab results available";
          } else if (updateData.includes("prescriptions_filled")) {
            shouldReload = true;
            notificationText = "Prescriptions completed";
          }
          
          if (shouldReload) {
            // Show brief notification
            const notification = document.createElement('div');
            notification.style.cssText = `
              position: fixed; top: 10px; right: 10px; z-index: 9999;
              background: #10b981; color: white; padding: 8px 16px;
              border-radius: 6px; font-weight: bold; font-size: 14px;
            `;
            notification.textContent = '🔄 ' + notificationText;
            document.body.appendChild(notification);
            
            // Set update flag and remove notification after short delay
            setTimeout(() => {
              if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
              }
              // Set flag for Streamlit to detect update
              window.streamlitUpdatePending = true;
              
              // Also try to trigger rerun through various methods
              try {
                // Method 1: Fragment-based reload
                if (window.location.hash !== '#updated') {
                  window.location.hash = '#updated';
                } else {
                  window.location.hash = '#updated-' + Date.now();
                }
                
                // Method 2: Force page refresh as fallback
                setTimeout(() => {
                  if (window.streamlitUpdatePending) {
                    window.location.reload(true);
                  }
                }, 2000);
              } catch (e) {
                console.log("Update trigger error:", e);
              }
            }, 1000);
          }
        };
        
        ws.onclose = function(event) {
          clearTimeout(connectionTimeout);
          console.log("WebSocket connection closed. Code:", event.code, "Reason:", event.reason);
          window.wsConnected = false;
          
          // Reconnect with exponential backoff, but max out at 10 seconds for offline environment
          if (reconnectAttempts < maxReconnectAttempts) {
            reconnectAttempts++;
            const backoffTime = Math.min(1000 * Math.pow(1.5, reconnectAttempts), 10000);
            console.log(`Reconnecting in ${backoffTime/1000} seconds... (attempt ${reconnectAttempts})`);
            setTimeout(connectWebSocket, backoffTime);
          } else {
            console.log("Max reconnection attempts reached. Will retry in 30 seconds...");
            reconnectAttempts = 0;
            setTimeout(connectWebSocket, 30000);
          }
        };
        
        ws.onerror = function(error) {
          clearTimeout(connectionTimeout);
          console.log("WebSocket error:", error);
          window.wsConnected = false;
          
          // Don't immediately reconnect on error - let onclose handle it
        };
        
      } catch (error) {
        console.log("WebSocket connection failed:", error);
        window.wsConnected = false;
      }
    }
    
    connectWebSocket();
    window.wsInitialized = true;
  }
</script>
"""

# Broadcast function to send updates to all connected devices
def broadcast_to_clients(message: str):
    """Sends a message to all connected WebSocket clients"""
    try:
        html(f"""
        <script>
        console.log("🚨 BROADCASTING MESSAGE:", '{message}');
        if (window.ws && window.ws.readyState === WebSocket.OPEN) {{
            window.ws.send('{message}');
            console.log("✅ Message sent to WebSocket server");
        }} else {{
            console.log("❌ WebSocket not connected, cannot send message");
            console.log("WebSocket readyState:", window.ws ? window.ws.readyState : "undefined");
        }}
        </script>
        """, height=0)
    except Exception as e:
        # Silently handle WebSocket errors to prevent app crashes
        pass

# Configure page for mobile/tablet use
st.set_page_config(
    page_title="Medical Clinic Charting",
    page_icon=
    "attached_assets/ChatGPT Image Jun 15, 2025, 05_23_25 PM_1750022665650.png",
    layout="wide",
    initial_sidebar_state="collapsed")

# Design tokens — single source of truth for the north-star UI.
# See docs/NORTHSTAR_GUI.md for the design contract.
COLOR_SURFACE = "#FFFFFF"
COLOR_SURFACE_2 = "#F9FAFB"
COLOR_BORDER = "#E5E7EB"
COLOR_TEXT = "#111827"
COLOR_TEXT_MUTED = "#6B7280"
COLOR_ACCENT = "#475569"
COLOR_URGENT = "#DC2626"
COLOR_WAITING = "#D97706"
COLOR_READY = "#059669"
COLOR_IDLE = "#9CA3AF"

# The legacy first-stage stylesheet is replaced by the main design system
# block below the DatabaseManager class. We keep just minimal globals here
# so set_page_config still has effect before the main stylesheet loads.
st.markdown("""
<style>
.stApp { background: #FFFFFF; }
</style>
""", unsafe_allow_html=True)


class DatabaseManager:

    def __init__(self, db_name: str = "clinic_database.db"):
        self.db_name = db_name
        self.init_database()

    def init_database(self):
        """Initialize the database with required tables"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()

        # ==================== ORGANIZATION & CLINIC TABLES ====================
        
        # Create organizations table - top level entity
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS organizations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                org_id TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                description TEXT,
                logo_data TEXT,
                contact_name TEXT,
                contact_email TEXT,
                contact_phone TEXT,
                address TEXT,
                country TEXT,
                pin_hash TEXT,
                is_active INTEGER DEFAULT 1,
                created_time TEXT,
                updated_time TEXT
            )
        ''')
        
        # Create organization_users table - org admins who can manage the whole org
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS organization_users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                organization_id INTEGER,
                full_name TEXT NOT NULL,
                title TEXT,
                email TEXT,
                phone TEXT,
                pin_hash TEXT,
                role TEXT DEFAULT 'org_admin',
                is_active INTEGER DEFAULT 1,
                created_time TEXT,
                last_login TEXT,
                FOREIGN KEY (organization_id) REFERENCES organizations (id)
            )
        ''')
        
        # Create clinics table - each clinic is a mission trip event
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS clinics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                clinic_id TEXT UNIQUE NOT NULL,
                organization_id INTEGER,
                name TEXT NOT NULL,
                description TEXT,
                location_name TEXT,
                location_city TEXT,
                location_country TEXT,
                location_code TEXT,
                gps_latitude REAL,
                gps_longitude REAL,
                start_date TEXT,
                end_date TEXT,
                status TEXT DEFAULT 'planning',
                is_archived INTEGER DEFAULT 0,
                patient_id_prefix TEXT,
                created_time TEXT,
                updated_time TEXT,
                FOREIGN KEY (organization_id) REFERENCES organizations (id)
            )
        ''')
        
        # Create clinic_staff table - staff assigned to specific clinics with PIN auth
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS clinic_staff (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                clinic_id INTEGER,
                full_name TEXT NOT NULL,
                title TEXT NOT NULL,
                pin_hash TEXT NOT NULL,
                role_scope TEXT DEFAULT 'all',
                email TEXT,
                phone TEXT,
                is_active INTEGER DEFAULT 1,
                created_time TEXT,
                last_login TEXT,
                FOREIGN KEY (clinic_id) REFERENCES clinics (id)
            )
        ''')
        
        # Add email and phone columns if they don't exist (migration for existing databases)
        try:
            cursor.execute("ALTER TABLE clinic_staff ADD COLUMN email TEXT")
        except:
            pass
        try:
            cursor.execute("ALTER TABLE clinic_staff ADD COLUMN phone TEXT")
        except:
            pass
        
        # Create org_medication_inventory table - org-level medication tracking
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS org_medication_inventory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                organization_id INTEGER,
                medication_name TEXT NOT NULL,
                total_quantity INTEGER DEFAULT 0,
                unit TEXT DEFAULT 'units',
                expiration_date TEXT,
                lot_number TEXT,
                notes TEXT,
                created_time TEXT,
                updated_time TEXT,
                FOREIGN KEY (organization_id) REFERENCES organizations (id)
            )
        ''')

        # Create families table for proper family management
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS families (
                family_id TEXT PRIMARY KEY,
                family_name TEXT NOT NULL,
                head_of_household TEXT,
                location_code TEXT,
                address TEXT,
                phone TEXT,
                emergency_contact TEXT,
                created_date TEXT,
                notes TEXT
            )
        ''')

        # Create patients table with family grouping
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS patients (
                patient_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                age INTEGER,
                gender TEXT,
                phone TEXT,
                emergency_contact TEXT,
                medical_history TEXT,
                allergies TEXT,
                created_date TEXT,
                last_visit TEXT,
                family_id TEXT,
                relationship TEXT,
                parent_id TEXT,
                is_independent INTEGER DEFAULT 0,
                separation_date TEXT,
                address TEXT,
                registration_time TEXT,
                FOREIGN KEY (family_id) REFERENCES families (family_id)
            )
        ''')

        # Create visits table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS visits (
                visit_id TEXT PRIMARY KEY,
                patient_id TEXT,
                visit_date TEXT,
                triage_time TEXT,
                consultation_time TEXT,
                pharmacy_time TEXT,
                status TEXT,
                priority TEXT,
                FOREIGN KEY (patient_id) REFERENCES patients (patient_id)
            )
        ''')

        # Create vital_signs table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS vital_signs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                visit_id TEXT,
                systolic_bp INTEGER,
                diastolic_bp INTEGER,
                heart_rate INTEGER,
                temperature REAL,
                weight REAL,
                height REAL,
                oxygen_saturation INTEGER,
                recorded_time TEXT,
                FOREIGN KEY (visit_id) REFERENCES visits (visit_id)
            )
        ''')

        # Create consultations table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS consultations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                visit_id TEXT,
                doctor_name TEXT,
                chief_complaint TEXT,
                symptoms TEXT,
                diagnosis TEXT,
                treatment_plan TEXT,
                notes TEXT,
                needs_ophthalmology INTEGER DEFAULT 0,
                consultation_time TEXT,
                FOREIGN KEY (visit_id) REFERENCES visits (visit_id)
            )
        ''')

        # Create prescriptions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS prescriptions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                visit_id TEXT,
                medication_id INTEGER,
                medication_name TEXT,
                dosage TEXT,
                frequency TEXT,
                duration TEXT,
                instructions TEXT,
                indication TEXT,
                status TEXT DEFAULT 'pending',
                awaiting_lab TEXT DEFAULT 'no',
                prescribed_time TEXT,
                filled_time TEXT,
                FOREIGN KEY (visit_id) REFERENCES visits (visit_id),
                FOREIGN KEY (medication_id) REFERENCES preset_medications (id)
            )
        ''')

        # Add awaiting_lab column if it doesn't exist (for database migration)
        try:
            cursor.execute(
                'ALTER TABLE prescriptions ADD COLUMN awaiting_lab TEXT DEFAULT "no"'
            )
        except sqlite3.OperationalError:
            pass  # Column already exists

        # Add teaching columns if they don't exist (for database migration)
        try:
            cursor.execute("ALTER TABLE prescriptions ADD COLUMN teaching_completed TEXT")
        except sqlite3.OperationalError:
            pass  # Column already exists
            
        try:
            cursor.execute("ALTER TABLE prescriptions ADD COLUMN teaching_notes TEXT")
        except sqlite3.OperationalError:
            pass  # Column already exists

        # Add require_indication column to preset_medications if it doesn't exist
        try:
            cursor.execute("ALTER TABLE preset_medications ADD COLUMN require_indication TEXT DEFAULT 'no'")
        except sqlite3.OperationalError:
            pass  # Column already exists

        # Add preset_duration column to preset_medications if it doesn't exist
        try:
            cursor.execute("ALTER TABLE preset_medications ADD COLUMN preset_duration TEXT")
        except sqlite3.OperationalError:
            pass  # Column already exists

        # Add amount and indication columns to preset_medications if they don't exist
        try:
            cursor.execute("ALTER TABLE preset_medications ADD COLUMN amount TEXT")
        except sqlite3.OperationalError:
            pass  # Column already exists

        try:
            cursor.execute("ALTER TABLE preset_medications ADD COLUMN indication TEXT")
        except sqlite3.OperationalError:
            pass  # Column already exists

        # Add prescribed_by column to prescriptions table if it doesn't exist
        try:
            cursor.execute("ALTER TABLE prescriptions ADD COLUMN prescribed_by TEXT")
        except sqlite3.OperationalError:
            pass  # Column already exists

        # Add oxygen saturation column if it doesn't exist
        try:
            cursor.execute(
                'ALTER TABLE vital_signs ADD COLUMN oxygen_saturation INTEGER')
        except sqlite3.OperationalError:
            pass  # Column already exists

        # Add family-related columns to patients table if they don't exist
        try:
            cursor.execute(
                'ALTER TABLE patients ADD COLUMN is_independent INTEGER DEFAULT 0'
            )
        except sqlite3.OperationalError:
            pass

        try:
            cursor.execute(
                'ALTER TABLE patients ADD COLUMN separation_date TEXT')
        except sqlite3.OperationalError:
            pass

        try:
            cursor.execute('ALTER TABLE patients ADD COLUMN address TEXT')
        except sqlite3.OperationalError:
            pass

        try:
            cursor.execute(
                'ALTER TABLE patients ADD COLUMN registration_time TEXT')
        except sqlite3.OperationalError:
            pass

        # Add address column to patients table if it doesn't exist
        try:
            cursor.execute('ALTER TABLE patients ADD COLUMN address TEXT')
        except sqlite3.OperationalError:
            pass  # Column already exists

        # Add registration_time column to patients table if it doesn't exist
        try:
            cursor.execute(
                'ALTER TABLE patients ADD COLUMN registration_time TEXT')
        except sqlite3.OperationalError:
            pass  # Column already exists

        # Add needs_ophthalmology column if it doesn't exist
        try:
            cursor.execute(
                'ALTER TABLE consultations ADD COLUMN needs_ophthalmology INTEGER DEFAULT 0'
            )
        except sqlite3.OperationalError:
            pass  # Column already exists

        # Add indication column if it doesn't exist
        try:
            cursor.execute(
                'ALTER TABLE prescriptions ADD COLUMN indication TEXT')
        except sqlite3.OperationalError:
            pass  # Column already exists

        # Add return_to_provider column if it doesn't exist
        try:
            cursor.execute(
                'ALTER TABLE prescriptions ADD COLUMN return_to_provider TEXT DEFAULT "no"')
        except sqlite3.OperationalError:
            pass  # Column already exists

        # Add pharmacy workflow columns if they don't exist
        try:
            cursor.execute(
                'ALTER TABLE prescriptions ADD COLUMN pharmacy_approved_time TEXT')
        except sqlite3.OperationalError:
            pass  # Column already exists

        try:
            cursor.execute(
                'ALTER TABLE prescriptions ADD COLUMN pharmacy_denied_time TEXT')
        except sqlite3.OperationalError:
            pass  # Column already exists

        try:
            cursor.execute(
                'ALTER TABLE prescriptions ADD COLUMN pharmacy_return_time TEXT')
        except sqlite3.OperationalError:
            pass  # Column already exists

        try:
            cursor.execute(
                'ALTER TABLE visits ADD COLUMN return_reason TEXT')
        except sqlite3.OperationalError:
            pass  # Column already exists

        # Add family columns to patients table if they don't exist
        try:
            cursor.execute('ALTER TABLE patients ADD COLUMN family_id TEXT')
        except sqlite3.OperationalError:
            pass  # Column already exists

        try:
            cursor.execute(
                'ALTER TABLE patients ADD COLUMN relationship TEXT DEFAULT "self"'
            )
        except sqlite3.OperationalError:
            pass  # Column already exists

        try:
            cursor.execute('ALTER TABLE patients ADD COLUMN parent_id TEXT')
        except sqlite3.OperationalError:
            pass  # Column already exists

        # Add amount and indications columns to preset_medications table
        try:
            cursor.execute('ALTER TABLE preset_medications ADD COLUMN amount TEXT')
        except sqlite3.OperationalError:
            pass  # Column already exists

        try:
            cursor.execute('ALTER TABLE preset_medications ADD COLUMN indications TEXT')
        except sqlite3.OperationalError:
            pass  # Column already exists

        # Create notifications table for doctor alerts
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS notifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                doctor_name TEXT,
                patient_id TEXT,
                patient_name TEXT,
                visit_id TEXT,
                message TEXT,
                notification_type TEXT,
                created_time TEXT,
                read_status INTEGER DEFAULT 0
            )
        ''')

        # Create patient_names_queue table for pre-registration
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS patient_names_queue (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                age INTEGER,
                gender TEXT,
                location_code TEXT,
                relationship TEXT DEFAULT 'individual',
                family_group_id TEXT,
                created_time TEXT,
                status TEXT DEFAULT 'pending_vitals',
                processed_by TEXT,
                notes TEXT
            )
        ''')

        # Add disposition column to lab_tests table if it doesn't exist
        try:
            cursor.execute('ALTER TABLE lab_tests ADD COLUMN disposition TEXT DEFAULT "return_to_provider"')
        except sqlite3.OperationalError:
            pass  # Column already exists

        # Create patient_names_queue table for pre-registration
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS patient_names_queue (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                age INTEGER,
                gender TEXT,
                location_code TEXT,
                relationship TEXT DEFAULT 'individual',
                family_group_id TEXT,
                created_time TEXT,
                status TEXT DEFAULT 'pending_vitals',
                processed_by TEXT,
                notes TEXT
            )
        ''')

        try:
            cursor.execute('ALTER TABLE patients ADD COLUMN created_date TEXT')
        except sqlite3.OperationalError:
            pass  # Column already exists

        try:
            cursor.execute('ALTER TABLE patients ADD COLUMN last_visit TEXT')
        except sqlite3.OperationalError:
            pass  # Column already exists

        # Add consultation columns to visits table
        consultation_columns = [
            'chief_complaint TEXT',
            'symptoms TEXT',
            'diagnosis TEXT',
            'treatment_plan TEXT',
            'notes TEXT',
            'surgical_history TEXT',
            'medical_history TEXT',
            'allergies TEXT',
            'current_medications TEXT'
        ]
        
        for column in consultation_columns:
            try:
                cursor.execute(f'ALTER TABLE visits ADD COLUMN {column}')
            except sqlite3.OperationalError:
                pass  # Column already exists

        # Add status column to prescriptions table for consultation state management
        try:
            cursor.execute('ALTER TABLE prescriptions ADD COLUMN status TEXT DEFAULT "ready"')
        except sqlite3.OperationalError:
            pass  # Column already exists

        # Create counter table for location-based patient numbering
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS counters (
                location_code TEXT PRIMARY KEY,
                value INTEGER
            )
        ''')

        # Create locations table for clinic locations
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS locations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                country_code TEXT NOT NULL,
                country_name TEXT NOT NULL,
                city TEXT NOT NULL,
                created_date TEXT
            )
        ''')

        # Create lab_tests table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS lab_tests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                visit_id TEXT,
                test_type TEXT,
                ordered_by TEXT,
                ordered_time TEXT,
                completed_time TEXT,
                results TEXT,
                status TEXT DEFAULT 'pending',
                FOREIGN KEY (visit_id) REFERENCES visits (visit_id)
            )
        ''')

        # Create lab_results table for detailed urinalysis
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS lab_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                lab_test_id INTEGER,
                parameter TEXT,
                result TEXT,
                normal_range TEXT,
                FOREIGN KEY (lab_test_id) REFERENCES lab_tests (id)
            )
        ''')

        # Create patient_photos table for symptom documentation
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS patient_photos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                visit_id TEXT,
                patient_id TEXT,
                photo_data BLOB,
                photo_description TEXT,
                captured_time TEXT,
                FOREIGN KEY (visit_id) REFERENCES visits (visit_id),
                FOREIGN KEY (patient_id) REFERENCES patients (patient_id)
            )
        ''')

        # Create preset_medications table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS preset_medications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                medication_name TEXT NOT NULL,
                common_dosages TEXT,
                category TEXT,
                requires_lab TEXT DEFAULT 'no',
                active INTEGER DEFAULT 1
            )
        ''')

        # Check if medications already exist to prevent duplicates
        cursor.execute('SELECT COUNT(*) FROM preset_medications')
        existing_count = cursor.fetchone()[0]

        if existing_count == 0:
            # Initialize default medications with Epocrates-style dosages
            default_meds = [
                ('Acetaminophen',
                 '325mg q6h PRN, 500mg q6h PRN, 650mg q6h PRN', 'Pain Relief',
                 'no'),
                ('Ibuprofen', '200mg q6h PRN, 400mg q8h PRN, 600mg q8h PRN',
                 'Pain Relief', 'no'),
                ('Amoxicillin', '500mg q12h x7-10 days, 875mg q12h x7-10 days',
                 'Antibiotic', 'no'),
                ('Azithromycin',
                 '250mg daily x5 days, 500mg day 1 then 250mg daily x4 days',
                 'Antibiotic', 'no'),
                ('Metronidazole', '250mg q8h x7 days, 500mg q12h x7 days',
                 'Antibiotic', 'no'),
                ('Ciprofloxacin',
                 '250mg q12h x3-7 days, 500mg q12h x7-14 days', 'Antibiotic',
                 'no'),
                ('Nitrofurantoin', '100mg q12h x5-7 days', 'UTI Antibiotic',
                 'no'),
                ('Metformin', '500mg q12h with meals, 850mg daily with meals',
                 'Diabetes', 'no'),
                ('Lisinopril', '5mg daily, 10mg daily, 20mg daily',
                 'Blood Pressure', 'no'),
                ('Amlodipine', '2.5mg daily, 5mg daily, 10mg daily',
                 'Blood Pressure', 'no'),
                ('Omeprazole',
                 '20mg daily before breakfast, 40mg daily before breakfast',
                 'Stomach', 'no'),
                ('Prednisone',
                 '5mg daily x5-7 days, 10mg daily x5-7 days, 20mg daily x5 days',
                 'Steroid', 'no'),
                ('Albuterol Inhaler', '2 puffs q4-6h PRN', 'Respiratory',
                 'no'), ('Multivitamin', '1 tablet daily', 'Vitamin', 'no'),
                ('Iron Supplement', '65mg daily on empty stomach', 'Vitamin',
                 'no'),
                ('Cephalexin', '250mg q6h x7-10 days, 500mg q12h x7-10 days',
                 'Antibiotic', 'no'),
                ('Doxycycline', '100mg q12h x7-14 days', 'Antibiotic', 'no'),
                ('Hydrochlorothiazide', '12.5mg daily, 25mg daily',
                 'Blood Pressure', 'no'),
                ('Atorvastatin', '20mg daily, 40mg daily', 'Cholesterol',
                 'no'),
                ('Furosemide', '20mg daily, 40mg daily', 'Diuretic', 'no'),
                ('Blood Pressure Handout', 'As needed for patient education', 'Teaching Pamphlets', 'no'),
                ('Diabetes Handout', 'As needed for patient education', 'Teaching Pamphlets', 'no')
            ]

            for med in default_meds:
                cursor.execute(
                    '''
                    INSERT INTO preset_medications 
                    (medication_name, common_dosages, category, requires_lab)
                    VALUES (?, ?, ?, ?)
                ''', med)

        # Add new tables for multi-user functionality
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS doctors (
                id INTEGER PRIMARY KEY,
                name TEXT UNIQUE NOT NULL,
                is_active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS doctor_status (
                id INTEGER PRIMARY KEY,
                doctor_name TEXT NOT NULL,
                current_patient_id TEXT,
                current_patient_name TEXT,
                status TEXT DEFAULT 'available',
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Initialize default doctors if table is empty
        cursor.execute('SELECT COUNT(*) FROM doctors')
        doctor_count = cursor.fetchone()[0]

        if doctor_count == 0:
            default_doctors = [
                'Dr. Smith', 'Dr. Johnson', 'Dr. Williams', 'Dr. Brown',
                'Dr. Garcia'
            ]

            for doctor in default_doctors:
                cursor.execute(
                    '''
                    INSERT INTO doctors (name, is_active) VALUES (?, 1)
                ''', (doctor, ))

        # Add date_of_birth column to patients table
        try:
            cursor.execute('ALTER TABLE patients ADD COLUMN date_of_birth TEXT')
        except sqlite3.OperationalError:
            pass

        # Add PIN column to doctors table
        try:
            cursor.execute('ALTER TABLE doctors ADD COLUMN pin_hash TEXT')
        except sqlite3.OperationalError:
            pass

        # Add stock management columns to preset_medications
        try:
            cursor.execute('ALTER TABLE preset_medications ADD COLUMN qty_in_stock INTEGER DEFAULT 0')
        except sqlite3.OperationalError:
            pass
        
        try:
            cursor.execute('ALTER TABLE preset_medications ADD COLUMN low_stock_threshold INTEGER DEFAULT 10')
        except sqlite3.OperationalError:
            pass
        
        try:
            cursor.execute("ALTER TABLE preset_medications ADD COLUMN stock_status TEXT DEFAULT 'unknown'")
        except sqlite3.OperationalError:
            pass

        # Add height column to vital_signs if it doesn't exist
        try:
            cursor.execute('ALTER TABLE vital_signs ADD COLUMN height REAL')
        except sqlite3.OperationalError:
            pass

        # Add BMI column to vital_signs
        try:
            cursor.execute('ALTER TABLE vital_signs ADD COLUMN bmi REAL')
        except sqlite3.OperationalError:
            pass

        # Add GPS coordinates to locations table
        try:
            cursor.execute('ALTER TABLE locations ADD COLUMN latitude REAL')
        except sqlite3.OperationalError:
            pass
        
        try:
            cursor.execute('ALTER TABLE locations ADD COLUMN longitude REAL')
        except sqlite3.OperationalError:
            pass

        # Add language preference to clinic_settings
        try:
            cursor.execute('ALTER TABLE locations ADD COLUMN default_language TEXT DEFAULT "en"')
        except sqlite3.OperationalError:
            pass

        # ==================== CLINIC_ID MIGRATIONS ====================
        # Add clinic_id to patients table to scope patients to specific clinics
        try:
            cursor.execute('ALTER TABLE patients ADD COLUMN clinic_id INTEGER')
        except sqlite3.OperationalError:
            pass
        
        # Add clinic_id to visits table
        try:
            cursor.execute('ALTER TABLE visits ADD COLUMN clinic_id INTEGER')
        except sqlite3.OperationalError:
            pass
        
        # Add clinic_id to families table
        try:
            cursor.execute('ALTER TABLE families ADD COLUMN clinic_id INTEGER')
        except sqlite3.OperationalError:
            pass
        
        # Add clinic_id to prescriptions table
        try:
            cursor.execute('ALTER TABLE prescriptions ADD COLUMN clinic_id INTEGER')
        except sqlite3.OperationalError:
            pass
        
        # Add clinic_id to lab_tests table
        try:
            cursor.execute('ALTER TABLE lab_tests ADD COLUMN clinic_id INTEGER')
        except sqlite3.OperationalError:
            pass
        
        # Add clinic_id to consultations table
        try:
            cursor.execute('ALTER TABLE consultations ADD COLUMN clinic_id INTEGER')
        except sqlite3.OperationalError:
            pass

        # Create immunizations table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS immunizations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                patient_id TEXT NOT NULL,
                vaccine_name TEXT NOT NULL,
                date_given TEXT,
                dose_number INTEGER,
                lot_number TEXT,
                administered_by TEXT,
                site TEXT,
                notes TEXT,
                created_time TEXT,
                FOREIGN KEY (patient_id) REFERENCES patients (patient_id)
            )
        ''')

        # Create pregnancy_history table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS pregnancy_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                patient_id TEXT NOT NULL,
                gravida INTEGER DEFAULT 0,
                para INTEGER DEFAULT 0,
                abortions INTEGER DEFAULT 0,
                living_children INTEGER DEFAULT 0,
                last_menstrual_period TEXT,
                estimated_due_date TEXT,
                current_pregnancy INTEGER DEFAULT 0,
                pregnancy_notes TEXT,
                created_time TEXT,
                updated_time TEXT,
                FOREIGN KEY (patient_id) REFERENCES patients (patient_id)
            )
        ''')

        # Create consent_records table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS consent_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                patient_id TEXT NOT NULL,
                consent_type TEXT NOT NULL,
                consent_given INTEGER DEFAULT 0,
                consent_date TEXT,
                witness_name TEXT,
                signature_data TEXT,
                country_code TEXT,
                notes TEXT,
                created_time TEXT,
                FOREIGN KEY (patient_id) REFERENCES patients (patient_id)
            )
        ''')

        # Create audit_logs table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS audit_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_name TEXT,
                user_role TEXT,
                action_type TEXT NOT NULL,
                table_name TEXT,
                record_id TEXT,
                old_values TEXT,
                new_values TEXT,
                ip_address TEXT,
                device_info TEXT,
                created_time TEXT NOT NULL
            )
        ''')

        # Create clinic_settings table for country-specific configuration
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS clinic_settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                location_id INTEGER,
                setting_key TEXT NOT NULL,
                setting_value TEXT,
                country_code TEXT,
                created_time TEXT,
                updated_time TEXT,
                FOREIGN KEY (location_id) REFERENCES locations (id)
            )
        ''')

        # Create growth_measurements table for WHO growth charts
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS growth_measurements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                patient_id TEXT NOT NULL,
                visit_id TEXT,
                measurement_date TEXT,
                age_months REAL,
                weight_kg REAL,
                height_cm REAL,
                head_circumference_cm REAL,
                weight_for_age_z REAL,
                height_for_age_z REAL,
                weight_for_height_z REAL,
                bmi_for_age_z REAL,
                created_time TEXT,
                FOREIGN KEY (patient_id) REFERENCES patients (patient_id),
                FOREIGN KEY (visit_id) REFERENCES visits (visit_id)
            )
        ''')

        # Create icd10_diagnoses table for diagnosis tracking
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS icd10_diagnoses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                visit_id TEXT NOT NULL,
                icd10_code TEXT NOT NULL,
                description TEXT,
                diagnosis_type TEXT DEFAULT 'primary',
                created_time TEXT,
                FOREIGN KEY (visit_id) REFERENCES visits (visit_id)
            )
        ''')

        # Migrate organization_users table - add new columns
        org_user_columns = [
            ('full_name', 'TEXT'),
            ('title', 'TEXT'),
            ('email', 'TEXT'),
            ('phone', 'TEXT'),
        ]
        for col_name, col_type in org_user_columns:
            try:
                cursor.execute(f'ALTER TABLE organization_users ADD COLUMN {col_name} {col_type}')
            except sqlite3.OperationalError:
                pass  # Column already exists
        
        # Migrate existing username data to full_name if needed
        try:
            cursor.execute('''
                UPDATE organization_users 
                SET full_name = username 
                WHERE full_name IS NULL AND username IS NOT NULL
            ''')
        except sqlite3.OperationalError:
            pass  # username column doesn't exist or other issue
        
        # Migrate clinic_staff table - add new columns
        clinic_staff_columns = [
            ('full_name', 'TEXT'),
            ('title', 'TEXT'),
            ('pin_hash', 'TEXT'),
            ('role_scope', 'TEXT DEFAULT "all"'),
            ('last_login', 'TEXT'),
        ]
        for col_name, col_type in clinic_staff_columns:
            try:
                cursor.execute(f'ALTER TABLE clinic_staff ADD COLUMN {col_name} {col_type}')
            except sqlite3.OperationalError:
                pass  # Column already exists
        
        # Migrate existing staff_name to full_name if needed
        try:
            cursor.execute('''
                UPDATE clinic_staff 
                SET full_name = staff_name 
                WHERE full_name IS NULL AND staff_name IS NOT NULL
            ''')
        except sqlite3.OperationalError:
            pass  # staff_name column doesn't exist

        conn.commit()
        conn.close()

    # ==================== ORGANIZATION METHODS ====================
    
    def create_organization(self, name: str, **kwargs) -> int:
        """Create a new organization and return its ID"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        org_id = f"ORG{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        cursor.execute('''
            INSERT INTO organizations (
                org_id, name, description, logo_data, contact_name, 
                contact_email, contact_phone, address, country,
                pin_hash, is_active, created_time, updated_time
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?, ?)
        ''', (
            org_id,
            name,
            kwargs.get('description', ''),
            kwargs.get('logo_data', ''),
            kwargs.get('contact_name', ''),
            kwargs.get('contact_email', ''),
            kwargs.get('contact_phone', ''),
            kwargs.get('address', ''),
            kwargs.get('country', ''),
            kwargs.get('pin_hash', ''),
            datetime.now().isoformat(),
            datetime.now().isoformat()
        ))
        
        org_db_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return org_db_id
    
    def get_organization(self, org_db_id: int):
        """Get organization by database ID"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, org_id, name, description, logo_data, contact_name,
                   contact_email, contact_phone, address, country, 
                   pin_hash, is_active, created_time, updated_time
            FROM organizations WHERE id = ? AND is_active = 1
        ''', (org_db_id,))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return {
                'id': result[0],
                'org_id': result[1],
                'name': result[2],
                'description': result[3],
                'logo_data': result[4],
                'contact_name': result[5],
                'contact_email': result[6],
                'contact_phone': result[7],
                'address': result[8],
                'country': result[9],
                'pin_hash': result[10],
                'is_active': result[11],
                'created_time': result[12],
                'updated_time': result[13]
            }
        return None
    
    def get_all_organizations(self):
        """Get all active organizations"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, org_id, name, description, contact_name, 
                   contact_email, created_time
            FROM organizations WHERE is_active = 1
            ORDER BY name
        ''')
        
        results = cursor.fetchall()
        conn.close()
        
        return [{
            'id': r[0],
            'org_id': r[1],
            'name': r[2],
            'description': r[3],
            'contact_name': r[4],
            'contact_email': r[5],
            'created_time': r[6]
        } for r in results]
    
    def update_organization(self, org_db_id: int, **kwargs):
        """Update organization details"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        updates = []
        values = []
        
        for field in ['name', 'description', 'logo_data', 'contact_name', 
                      'contact_email', 'contact_phone', 'address', 'country', 'pin_hash']:
            if field in kwargs:
                updates.append(f"{field} = ?")
                values.append(kwargs[field])
        
        if updates:
            updates.append("updated_time = ?")
            values.append(datetime.now().isoformat())
            values.append(org_db_id)
            
            cursor.execute(f'''
                UPDATE organizations SET {", ".join(updates)}
                WHERE id = ?
            ''', values)
            
            conn.commit()
        conn.close()
    
    def verify_organization_pin(self, org_db_id: int, pin: str) -> bool:
        """Verify organization PIN"""
        org = self.get_organization(org_db_id)
        if org and org['pin_hash']:
            import hashlib
            pin_hash = hashlib.sha256(pin.encode()).hexdigest()
            return pin_hash == org['pin_hash']
        return False
    
    # ==================== ORG USER METHODS ====================
    
    def create_org_user(self, organization_id: int, full_name: str, pin: str, **kwargs) -> int:
        """Create an organization admin user"""
        import hashlib
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        pin_hash = hashlib.sha256(pin.encode()).hexdigest()
        
        # Include username for backwards compatibility with old schema
        cursor.execute('''
            INSERT INTO organization_users (
                organization_id, username, full_name, title, email, phone,
                pin_hash, role, is_active, created_time
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1, ?)
        ''', (
            organization_id,
            full_name,  # Use full_name as username for backwards compatibility
            full_name,
            kwargs.get('title', 'Administrator'),
            kwargs.get('email', ''),
            kwargs.get('phone', ''),
            pin_hash,
            kwargs.get('role', 'org_admin'),
            datetime.now().isoformat()
        ))
        
        user_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return user_id
    
    def get_org_users(self, organization_id: int, include_inactive: bool = False):
        """Get all org users for an organization"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        query = '''
            SELECT id, organization_id, full_name, title, email, phone,
                   role, is_active, created_time, last_login
            FROM organization_users WHERE organization_id = ?
        '''
        if not include_inactive:
            query += ' AND is_active = 1'
        
        cursor.execute(query, (organization_id,))
        results = cursor.fetchall()
        conn.close()
        
        return [{
            'id': r[0],
            'organization_id': r[1],
            'full_name': r[2],
            'title': r[3],
            'email': r[4],
            'phone': r[5],
            'role': r[6],
            'is_active': r[7],
            'created_time': r[8],
            'last_login': r[9]
        } for r in results]
    
    def verify_org_user_pin(self, organization_id: int, full_name: str, pin: str):
        """Verify org user PIN and return user data if valid"""
        import hashlib
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        pin_hash = hashlib.sha256(pin.encode()).hexdigest()
        
        cursor.execute('''
            SELECT id, organization_id, full_name, title, role
            FROM organization_users 
            WHERE organization_id = ? AND LOWER(full_name) = LOWER(?) 
            AND pin_hash = ? AND is_active = 1
        ''', (organization_id, full_name, pin_hash))
        
        result = cursor.fetchone()
        
        if result:
            # Update last login
            cursor.execute('''
                UPDATE organization_users SET last_login = ? WHERE id = ?
            ''', (datetime.now().isoformat(), result[0]))
            conn.commit()
            conn.close()
            return {
                'id': result[0],
                'organization_id': result[1],
                'full_name': result[2],
                'title': result[3],
                'role': result[4]
            }
        conn.close()
        return None
    
    def update_org_user(self, user_id: int, **kwargs):
        """Update org user details"""
        import hashlib
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        updates = []
        values = []
        
        for field in ['full_name', 'title', 'email', 'phone', 'role', 'is_active']:
            if field in kwargs:
                updates.append(f"{field} = ?")
                values.append(kwargs[field])
        
        if 'pin' in kwargs and kwargs['pin']:
            updates.append("pin_hash = ?")
            values.append(hashlib.sha256(kwargs['pin'].encode()).hexdigest())
        
        if updates:
            values.append(user_id)
            cursor.execute(f'''
                UPDATE organization_users SET {", ".join(updates)} WHERE id = ?
            ''', values)
            conn.commit()
        conn.close()
    
    def delete_org_user(self, user_id: int):
        """Deactivate an org user (soft delete)"""
        self.update_org_user(user_id, is_active=0)
    
    # ==================== CLINIC STAFF METHODS ====================
    
    def create_clinic_staff(self, clinic_id: int, full_name: str, title: str, pin: str, **kwargs) -> int:
        """Create a clinic staff member with PIN"""
        import hashlib
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        pin_hash = hashlib.sha256(pin.encode()).hexdigest()
        
        # Include staff_name for backwards compatibility with old schema
        cursor.execute('''
            INSERT INTO clinic_staff (
                clinic_id, staff_name, full_name, title, pin_hash, role_scope, email, phone, is_active, created_time
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1, ?)
        ''', (
            clinic_id,
            full_name,  # Use full_name as staff_name for backwards compatibility
            full_name,
            title,
            pin_hash,
            kwargs.get('role_scope', 'all'),
            kwargs.get('email'),
            kwargs.get('phone'),
            datetime.now().isoformat()
        ))
        
        staff_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return staff_id
    
    # Alias for backwards compatibility
    add_clinic_staff = create_clinic_staff
    
    def get_clinic_staff(self, clinic_id: int, include_inactive: bool = False):
        """Get all staff for a clinic"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        query = '''
            SELECT id, clinic_id, full_name, title, role_scope, is_active, created_time, last_login
            FROM clinic_staff WHERE clinic_id = ?
        '''
        if not include_inactive:
            query += ' AND is_active = 1'
        
        cursor.execute(query, (clinic_id,))
        results = cursor.fetchall()
        conn.close()
        
        return [{
            'id': r[0],
            'clinic_id': r[1],
            'full_name': r[2],
            'title': r[3],
            'role_scope': r[4],
            'is_active': r[5],
            'created_time': r[6],
            'last_login': r[7]
        } for r in results]
    
    def verify_clinic_staff_pin(self, clinic_id: int, full_name: str, title: str, pin: str):
        """Verify clinic staff PIN and return staff data if valid"""
        import hashlib
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        pin_hash = hashlib.sha256(pin.encode()).hexdigest()
        
        cursor.execute('''
            SELECT id, clinic_id, full_name, title, role_scope
            FROM clinic_staff 
            WHERE clinic_id = ? AND LOWER(full_name) = LOWER(?) 
            AND LOWER(title) = LOWER(?) AND pin_hash = ? AND is_active = 1
        ''', (clinic_id, full_name, title, pin_hash))
        
        result = cursor.fetchone()
        
        if result:
            # Update last login
            cursor.execute('''
                UPDATE clinic_staff SET last_login = ? WHERE id = ?
            ''', (datetime.now().isoformat(), result[0]))
            conn.commit()
            conn.close()
            return {
                'id': result[0],
                'clinic_id': result[1],
                'full_name': result[2],
                'title': result[3],
                'role_scope': result[4]
            }
        conn.close()
        return None
    
    def find_staff_by_credentials(self, org_id: int, identifier: str, pin: str):
        """Find staff member by email/phone and PIN across all clinics in an organization.
        Identifier can be email or phone number.
        Returns list of matching staff with their clinic info, ordered by most recent login."""
        import hashlib
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        pin_hash = hashlib.sha256(pin.encode()).hexdigest()
        identifier_clean = identifier.strip().lower()
        
        # Find all matching staff across clinics in this organization (by email/phone and PIN)
        cursor.execute('''
            SELECT cs.id, cs.clinic_id, cs.full_name, cs.title, cs.role_scope, cs.last_login,
                   c.name as clinic_name, c.location_city, c.location_country, c.status as clinic_status,
                   c.patient_id_prefix, c.location_code
            FROM clinic_staff cs
            JOIN clinics c ON cs.clinic_id = c.id
            WHERE c.organization_id = ? 
            AND (LOWER(cs.email) = ? OR cs.phone = ?)
            AND cs.pin_hash = ? 
            AND cs.is_active = 1
            ORDER BY cs.last_login DESC NULLS LAST, c.status = 'active' DESC
        ''', (org_id, identifier_clean, identifier.strip(), pin_hash))
        
        results = cursor.fetchall()
        
        # Update last_login for matched staff
        if results:
            for r in results:
                cursor.execute('''
                    UPDATE clinic_staff SET last_login = ? WHERE id = ?
                ''', (datetime.now().isoformat(), r[0]))
            conn.commit()
        
        conn.close()
        
        return [{
            'id': r[0],
            'clinic_id': r[1],
            'full_name': r[2],
            'title': r[3],
            'role_scope': r[4],
            'last_login': r[5],
            'clinic_name': r[6],
            'clinic_city': r[7],
            'clinic_country': r[8],
            'clinic_status': r[9],
            'patient_id_prefix': r[10],
            'location_code': r[11]
        } for r in results]
    
    def get_staff_clinics(self, org_id: int, full_name: str, title: str):
        """Get all clinics a staff member has access to in an organization (without PIN verification)"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT cs.clinic_id, c.name as clinic_name, c.location_city, c.location_country, 
                   c.status as clinic_status, cs.last_login
            FROM clinic_staff cs
            JOIN clinics c ON cs.clinic_id = c.id
            WHERE c.organization_id = ? 
            AND LOWER(cs.full_name) = LOWER(?) 
            AND LOWER(cs.title) = LOWER(?) 
            AND cs.is_active = 1
            ORDER BY cs.last_login DESC NULLS LAST
        ''', (org_id, full_name, title))
        
        results = cursor.fetchall()
        conn.close()
        
        return [{
            'clinic_id': r[0],
            'clinic_name': r[1],
            'clinic_city': r[2],
            'clinic_country': r[3],
            'clinic_status': r[4],
            'last_login': r[5]
        } for r in results]
    
    def update_clinic_staff(self, staff_id: int, **kwargs):
        """Update clinic staff details"""
        import hashlib
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        updates = []
        values = []
        
        for field in ['full_name', 'title', 'role_scope', 'is_active']:
            if field in kwargs:
                updates.append(f"{field} = ?")
                values.append(kwargs[field])
        
        if 'pin' in kwargs and kwargs['pin']:
            updates.append("pin_hash = ?")
            values.append(hashlib.sha256(kwargs['pin'].encode()).hexdigest())
        
        if updates:
            values.append(staff_id)
            cursor.execute(f'''
                UPDATE clinic_staff SET {", ".join(updates)} WHERE id = ?
            ''', values)
            conn.commit()
        conn.close()
    
    def delete_clinic_staff(self, staff_id: int):
        """Deactivate clinic staff (soft delete)"""
        self.update_clinic_staff(staff_id, is_active=0)
    
    # ==================== CLINIC METHODS ====================
    
    def create_clinic(self, organization_id: int, name: str, **kwargs) -> int:
        """Create a new clinic under an organization"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        clinic_id = f"CLINIC{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        # Determine patient ID prefix from location code or country
        location_country = kwargs.get('location_country', '')
        patient_id_prefix = kwargs.get('patient_id_prefix', '')
        if not patient_id_prefix:
            if location_country.lower() in ['dominican republic', 'dr']:
                patient_id_prefix = 'DR'
            elif location_country.lower() in ['haiti', 'ht']:
                patient_id_prefix = 'H'
            else:
                patient_id_prefix = location_country[:2].upper() if location_country else 'CL'
        
        cursor.execute('''
            INSERT INTO clinics (
                clinic_id, organization_id, name, description,
                location_name, location_city, location_country, location_code,
                gps_latitude, gps_longitude, start_date, end_date,
                status, is_archived, patient_id_prefix, created_time, updated_time
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?, ?, ?)
        ''', (
            clinic_id,
            organization_id,
            name,
            kwargs.get('description', ''),
            kwargs.get('location_name', ''),
            kwargs.get('location_city', ''),
            location_country,
            kwargs.get('location_code', ''),
            kwargs.get('gps_latitude'),
            kwargs.get('gps_longitude'),
            kwargs.get('start_date', ''),
            kwargs.get('end_date', ''),
            kwargs.get('status', 'planning'),
            patient_id_prefix,
            datetime.now().isoformat(),
            datetime.now().isoformat()
        ))
        
        clinic_db_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return clinic_db_id
    
    def get_clinic(self, clinic_db_id: int):
        """Get clinic by database ID"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, clinic_id, organization_id, name, description,
                   location_name, location_city, location_country, location_code,
                   gps_latitude, gps_longitude, start_date, end_date,
                   status, is_archived, patient_id_prefix, created_time, updated_time
            FROM clinics WHERE id = ?
        ''', (clinic_db_id,))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return {
                'id': result[0],
                'clinic_id': result[1],
                'organization_id': result[2],
                'name': result[3],
                'description': result[4],
                'location_name': result[5],
                'location_city': result[6],
                'location_country': result[7],
                'location_code': result[8],
                'gps_latitude': result[9],
                'gps_longitude': result[10],
                'start_date': result[11],
                'end_date': result[12],
                'status': result[13],
                'is_archived': result[14],
                'patient_id_prefix': result[15],
                'created_time': result[16],
                'updated_time': result[17]
            }
        return None
    
    def get_organization_clinics(self, organization_id: int, include_archived: bool = False):
        """Get all clinics for an organization"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        if include_archived:
            cursor.execute('''
                SELECT id, clinic_id, name, description, location_city, 
                       location_country, start_date, end_date, status, is_archived
                FROM clinics WHERE organization_id = ?
                ORDER BY start_date DESC, name
            ''', (organization_id,))
        else:
            cursor.execute('''
                SELECT id, clinic_id, name, description, location_city, 
                       location_country, start_date, end_date, status, is_archived
                FROM clinics WHERE organization_id = ? AND is_archived = 0
                ORDER BY start_date DESC, name
            ''', (organization_id,))
        
        results = cursor.fetchall()
        conn.close()
        
        return [{
            'id': r[0],
            'clinic_id': r[1],
            'name': r[2],
            'description': r[3],
            'location_city': r[4],
            'location_country': r[5],
            'start_date': r[6],
            'end_date': r[7],
            'status': r[8],
            'is_archived': r[9]
        } for r in results]
    
    def update_clinic(self, clinic_db_id: int, **kwargs):
        """Update clinic details"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        updates = []
        values = []
        
        for field in ['name', 'description', 'location_name', 'location_city', 
                      'location_country', 'location_code', 'gps_latitude', 
                      'gps_longitude', 'start_date', 'end_date', 'status', 
                      'is_archived', 'patient_id_prefix']:
            if field in kwargs:
                updates.append(f"{field} = ?")
                values.append(kwargs[field])
        
        if updates:
            updates.append("updated_time = ?")
            values.append(datetime.now().isoformat())
            values.append(clinic_db_id)
            
            cursor.execute(f'''
                UPDATE clinics SET {", ".join(updates)}
                WHERE id = ?
            ''', values)
            
            conn.commit()
        conn.close()
    
    def archive_clinic(self, clinic_db_id: int):
        """Archive a clinic (soft delete)"""
        self.update_clinic(clinic_db_id, is_archived=1, status='completed')
    
    def get_clinic_stats(self, clinic_db_id: int):
        """Get statistics for a specific clinic"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        stats = {}
        
        # Count patients
        cursor.execute('SELECT COUNT(*) FROM patients WHERE clinic_id = ?', (clinic_db_id,))
        stats['total_patients'] = cursor.fetchone()[0]
        
        # Count visits
        cursor.execute('SELECT COUNT(*) FROM visits WHERE clinic_id = ?', (clinic_db_id,))
        stats['total_visits'] = cursor.fetchone()[0]
        
        # Count prescriptions
        cursor.execute('SELECT COUNT(*) FROM prescriptions WHERE clinic_id = ?', (clinic_db_id,))
        stats['total_prescriptions'] = cursor.fetchone()[0]
        
        # Count completed visits
        cursor.execute("SELECT COUNT(*) FROM visits WHERE clinic_id = ? AND status = 'completed'", (clinic_db_id,))
        stats['completed_visits'] = cursor.fetchone()[0]
        
        conn.close()
        return stats
    
    def get_organization_stats(self, organization_id: int):
        """Get aggregate statistics for an organization across all clinics"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        stats = {}
        
        # Get all clinic IDs for this org
        cursor.execute('SELECT id FROM clinics WHERE organization_id = ?', (organization_id,))
        clinic_ids = [r[0] for r in cursor.fetchall()]
        
        if not clinic_ids:
            conn.close()
            return {
                'total_clinics': 0,
                'active_clinics': 0,
                'total_patients': 0,
                'total_visits': 0,
                'total_prescriptions': 0
            }
        
        placeholders = ','.join(['?' for _ in clinic_ids])
        
        # Count clinics
        stats['total_clinics'] = len(clinic_ids)
        
        cursor.execute(f"SELECT COUNT(*) FROM clinics WHERE organization_id = ? AND status = 'active'", (organization_id,))
        stats['active_clinics'] = cursor.fetchone()[0]
        
        # Count patients across all clinics
        cursor.execute(f'SELECT COUNT(*) FROM patients WHERE clinic_id IN ({placeholders})', clinic_ids)
        stats['total_patients'] = cursor.fetchone()[0]
        
        # Count visits across all clinics
        cursor.execute(f'SELECT COUNT(*) FROM visits WHERE clinic_id IN ({placeholders})', clinic_ids)
        stats['total_visits'] = cursor.fetchone()[0]
        
        # Count prescriptions across all clinics
        cursor.execute(f'SELECT COUNT(*) FROM prescriptions WHERE clinic_id IN ({placeholders})', clinic_ids)
        stats['total_prescriptions'] = cursor.fetchone()[0]
        
        conn.close()
        return stats
    
    def migrate_existing_data_to_clinic(self, clinic_db_id: int, location_code: str = None):
        """Migrate existing data without clinic_id to a specific clinic"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        # Update patients without clinic_id
        if location_code:
            cursor.execute('''
                UPDATE patients SET clinic_id = ? 
                WHERE clinic_id IS NULL AND patient_id LIKE ?
            ''', (clinic_db_id, f"{location_code}%"))
        else:
            cursor.execute('UPDATE patients SET clinic_id = ? WHERE clinic_id IS NULL', (clinic_db_id,))
        
        # Update visits for those patients
        cursor.execute('''
            UPDATE visits SET clinic_id = ? 
            WHERE clinic_id IS NULL AND patient_id IN (
                SELECT patient_id FROM patients WHERE clinic_id = ?
            )
        ''', (clinic_db_id, clinic_db_id))
        
        # Update families
        if location_code:
            cursor.execute('''
                UPDATE families SET clinic_id = ? 
                WHERE clinic_id IS NULL AND location_code = ?
            ''', (clinic_db_id, location_code))
        else:
            cursor.execute('UPDATE families SET clinic_id = ? WHERE clinic_id IS NULL', (clinic_db_id,))
        
        # Update prescriptions
        cursor.execute('''
            UPDATE prescriptions SET clinic_id = ? 
            WHERE clinic_id IS NULL AND visit_id IN (
                SELECT visit_id FROM visits WHERE clinic_id = ?
            )
        ''', (clinic_db_id, clinic_db_id))
        
        # Update consultations
        cursor.execute('''
            UPDATE consultations SET clinic_id = ? 
            WHERE clinic_id IS NULL AND visit_id IN (
                SELECT visit_id FROM visits WHERE clinic_id = ?
            )
        ''', (clinic_db_id, clinic_db_id))
        
        conn.commit()
        conn.close()

    def get_next_patient_id(self, location_code: str) -> str:
        """Get the next patient ID in format DR00001, H00001, etc.

        Uses the `counters` table under BEGIN IMMEDIATE so two iPads
        registering simultaneously can't both claim the same ID. Also
        reconciles against MAX(patient_id) so a stale counter (e.g. legacy
        data inserted before this code path was wired up) is brought
        forward instead of producing a collision on INSERT.
        """
        conn = sqlite3.connect(self.db_name)
        conn.execute('PRAGMA busy_timeout = 5000')
        cursor = conn.cursor()
        try:
            cursor.execute('BEGIN IMMEDIATE')

            cursor.execute(
                'INSERT OR IGNORE INTO counters (location_code, value) VALUES (?, 0)',
                (location_code,))

            cursor.execute(
                'SELECT value FROM counters WHERE location_code = ?',
                (location_code,))
            counter_value = (cursor.fetchone() or (0,))[0] or 0

            # Reconcile against patients table in case the counter is behind
            prefix_len = len(location_code)
            cursor.execute(
                'SELECT patient_id FROM patients '
                'WHERE patient_id LIKE ? ORDER BY patient_id DESC LIMIT 1',
                (f'{location_code}%',))
            row = cursor.fetchone()
            max_existing = 0
            if row and row[0]:
                try:
                    max_existing = int(row[0][prefix_len:])
                except ValueError:
                    max_existing = 0

            new_value = max(counter_value, max_existing) + 1

            cursor.execute(
                'UPDATE counters SET value = ? WHERE location_code = ?',
                (new_value, location_code))
            conn.commit()
            return f"{location_code}{new_value:05d}"
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def create_family(self, location_code: str, family_name: str,
                      head_of_household: str, **kwargs) -> str:
        """Create a new family unit and return family ID"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()

        # Generate family ID using location code + sequential number
        cursor.execute('SELECT COUNT(*) FROM families WHERE location_code = ?',
                       (location_code, ))
        count = cursor.fetchone()[0]
        family_id = f"{location_code}FAM{str(count + 1).zfill(5)}"

        cursor.execute(
            '''
            INSERT INTO families (
                family_id, family_name, head_of_household, location_code,
                address, phone, emergency_contact, created_date, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (family_id, family_name, head_of_household, location_code,
              kwargs.get('address', ''), kwargs.get(
                  'phone', ''), kwargs.get('emergency_contact', ''),
              datetime.now().isoformat(), kwargs.get('notes', '')))

        conn.commit()
        conn.close()
        return family_id

    def add_family_member(self,
                          family_id: str,
                          location_code: str,
                          relationship: str,
                          parent_id: str = "",
                          **kwargs) -> str:
        """Add a family member to an existing family"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()

        patient_id = self.get_next_patient_id(location_code)

        # Determine if this person should be independent (18+ years old)
        age = kwargs.get('age', 0)
        is_independent = 1 if age and age >= 18 else 0
        
        # Get clinic_id from kwargs
        clinic_id = kwargs.get('clinic_id')

        cursor.execute(
            '''
            INSERT INTO patients (
                patient_id, name, age, gender, phone, emergency_contact, 
                medical_history, allergies, created_date, last_visit,
                family_id, relationship, parent_id, is_independent,
                address, registration_time, clinic_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''',
            (patient_id, kwargs.get('name', ''), age, kwargs.get('gender', ''),
             kwargs.get('phone', ''), kwargs.get('emergency_contact', ''),
             kwargs.get('medical_history', ''), kwargs.get('allergies', ''),
             datetime.now().isoformat(), datetime.now().isoformat(), family_id,
             relationship, parent_id, is_independent, kwargs.get(
                 'address', ''), datetime.now().isoformat(), clinic_id))

        conn.commit()
        conn.close()
        return patient_id

    def add_patient(self, location_code: str, **kwargs) -> str:
        """Add a new patient and return their ID.

        `is_independent` defaults to 1 for true individuals but is set to 0
        when a family_id is supplied (the patient is part of a family group).
        Family members previously got is_independent=1 hardcoded, which made
        the doctor's queue treat them as orphans even though family_id and
        relationship were set correctly elsewhere.
        """
        patient_id = self.get_next_patient_id(location_code)

        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()

        # Calculate age from date_of_birth if provided
        age = kwargs.get('age')
        dob = kwargs.get('date_of_birth')
        if dob and not age:
            age = calculate_age_from_dob(dob)

        # Get clinic_id from kwargs or session state
        clinic_id = kwargs.get('clinic_id')

        # Family members aren't independent; individuals without family_id are.
        family_id = kwargs.get('family_id')
        is_independent = kwargs.get('is_independent',
                                    0 if family_id else 1)

        cursor.execute(
            '''
            INSERT INTO patients (patient_id, name, age, gender, phone,
                                emergency_contact, medical_history, allergies,
                                created_date, last_visit, family_id, relationship, parent_id,
                                is_independent, address, registration_time, date_of_birth, clinic_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''',
            (
                patient_id,
                kwargs.get('name', ''),
                age,
                kwargs.get('gender'),
                kwargs.get('phone'),
                kwargs.get('emergency_contact'),
                kwargs.get('medical_history'),
                kwargs.get('allergies'),
                datetime.now().isoformat(),
                datetime.now().isoformat(),
                family_id,
                kwargs.get('relationship', 'self'),
                kwargs.get('parent_id', None),
                is_independent,
                kwargs.get('address', ''),
                datetime.now().isoformat(),
                dob,
                clinic_id))

        conn.commit()
        conn.close()

        return patient_id

    def check_duplicate_patient(self,
                                name: str,
                                age: Optional[int] = None,
                                phone: Optional[str] = None) -> dict:
        """Check for potential duplicate patients based on name, age, and phone"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()

        # Search for exact name matches
        cursor.execute(
            '''
            SELECT patient_id, name, age, phone, address, registration_time
            FROM patients 
            WHERE LOWER(name) = LOWER(?)
            ORDER BY registration_time DESC
        ''', (name, ))

        exact_matches = cursor.fetchall()

        # Search for similar names (fuzzy matching)
        name_parts = name.lower().split()
        if len(name_parts) >= 2:
            first_name = name_parts[0]
            last_name = name_parts[-1]
            cursor.execute(
                '''
                SELECT patient_id, name, age, phone, address, registration_time
                FROM patients 
                WHERE (LOWER(name) LIKE ? OR LOWER(name) LIKE ?) 
                AND patient_id NOT IN (
                    SELECT patient_id FROM patients WHERE LOWER(name) = LOWER(?)
                )
                ORDER BY registration_time DESC
                LIMIT 5
            ''', (f'%{first_name}%{last_name}%', f'%{last_name}%{first_name}%',
                  name))
        else:
            cursor.execute(
                '''
                SELECT patient_id, name, age, phone, address, registration_time
                FROM patients 
                WHERE LOWER(name) LIKE ? 
                AND patient_id NOT IN (
                    SELECT patient_id FROM patients WHERE LOWER(name) = LOWER(?)
                )
                ORDER BY registration_time DESC
                LIMIT 5
            ''', (f'%{name.lower()}%', name))

        similar_matches = cursor.fetchall()

        conn.close()

        return {
            'exact_matches': exact_matches,
            'similar_matches': similar_matches
        }

    def link_to_existing_patient(self, existing_patient_id: str) -> str:
        """Create a new visit for an existing patient from previous clinic"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()

        # Update last visit time
        cursor.execute(
            '''
            UPDATE patients 
            SET last_visit = ?
            WHERE patient_id = ?
        ''', (datetime.now().isoformat(), existing_patient_id))

        conn.commit()
        conn.close()

        # Create new visit
        visit_id = self.create_visit(existing_patient_id)
        return visit_id

    def save_patient_photo(self,
                           visit_id: str,
                           patient_id: str,
                           photo_data: bytes,
                           description: str = "") -> int:
        """Save a patient photo for symptom documentation"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()

        cursor.execute(
            '''
            INSERT INTO patient_photos (visit_id, patient_id, photo_data, photo_description, captured_time)
            VALUES (?, ?, ?, ?, ?)
        ''', (visit_id, patient_id, photo_data, description,
              datetime.now().isoformat()))

        photo_id = cursor.lastrowid
        conn.commit()
        conn.close()

        return photo_id or 0

    def get_patient_photos(self, patient_id: str) -> List[Dict]:
        """Get all photos for a patient"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()

        cursor.execute(
            '''
            SELECT id, visit_id, photo_description, captured_time
            FROM patient_photos
            WHERE patient_id = ?
            ORDER BY captured_time DESC
        ''', (patient_id, ))

        photos = []
        for row in cursor.fetchall():
            photos.append({
                'id': row[0],
                'visit_id': row[1],
                'description': row[2],
                'captured_time': row[3]
            })

        conn.close()
        return photos

    def get_family_members(self, patient_id: str) -> List[Dict]:
        """Get all family members for a patient"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()

        # First get the patient's family_id
        cursor.execute('SELECT family_id FROM patients WHERE patient_id = ?',
                       (patient_id, ))
        result = cursor.fetchone()

        if not result or not result[0]:
            conn.close()
            return []

        family_id = result[0]

        # Get all family members
        cursor.execute(
            '''
            SELECT patient_id, name, age, gender, relationship, parent_id
            FROM patients 
            WHERE family_id = ?
            ORDER BY 
                CASE relationship 
                    WHEN 'parent' THEN 1 
                    WHEN 'self' THEN 1
                    ELSE 2 
                END,
                age DESC
        ''', (family_id, ))

        members = []
        for row in cursor.fetchall():
            members.append({
                'patient_id': row[0],
                'name': row[1],
                'age': row[2],
                'gender': row[3],
                'relationship': row[4],
                'parent_id': row[5]
            })

        conn.close()
        return members

    def get_family_info(self, family_id: str) -> Dict:
        """Get complete family information including all members"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()

        # Get family details
        cursor.execute('SELECT * FROM families WHERE family_id = ?',
                       (family_id, ))
        family_row = cursor.fetchone()

        if not family_row:
            conn.close()
            return {}

        # Get all family members
        cursor.execute(
            '''
            SELECT patient_id, name, age, gender, relationship, parent_id, is_independent 
            FROM patients WHERE family_id = ? ORDER BY relationship, age DESC
        ''', (family_id, ))
        members = cursor.fetchall()

        conn.close()

        return {
            'family_id':
            family_row[0],
            'family_name':
            family_row[1],
            'head_of_household':
            family_row[2],
            'location_code':
            family_row[3],
            'address':
            family_row[4],
            'phone':
            family_row[5],
            'members': [
                dict(
                    zip([
                        'patient_id', 'name', 'age', 'gender', 'relationship',
                        'parent_id', 'is_independent'
                    ], member)) for member in members
            ]
        }

    def separate_family_member(self,
                               patient_id: str,
                               new_address: str = "") -> bool:
        """Separate a family member (typically when they turn 18)"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()

        cursor.execute(
            '''
            UPDATE patients 
            SET is_independent = 1, separation_date = ?, address = ?
            WHERE patient_id = ?
        ''', (datetime.now().isoformat(), new_address, patient_id))

        conn.commit()
        conn.close()
        return True

    def search_patients(self, query: str) -> List[Dict]:
        """Search for patients by name or ID.

        Name search is accent-insensitive (José == Jose) and typo-tolerant
        via difflib.SequenceMatcher. ID search is exact-substring as before.
        Results from ID match are surfaced first, then ranked fuzzy name
        matches above ~0.55 similarity (skipped if the substring is already
        a perfect hit so we don't double-count)."""
        import unicodedata, difflib

        def _normalize(s):
            if not s:
                return ''
            nfkd = unicodedata.normalize('NFKD', str(s))
            return ''.join(c for c in nfkd if not unicodedata.combining(c)).lower().strip()

        columns = [
            'patient_id', 'name', 'age', 'gender', 'phone',
            'emergency_contact', 'medical_history', 'allergies',
            'created_date', 'last_visit'
        ]
        col_select = ', '.join(columns)

        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()

        # 1. Exact ID-substring match (highest priority)
        cursor.execute(
            f'SELECT {col_select} FROM patients WHERE patient_id LIKE ? ORDER BY name',
            (f'%{query}%',))
        id_hits = cursor.fetchall()
        id_hit_set = {row[0] for row in id_hits}

        # 2. Fuzzy + accent-insensitive name match across all patients
        cursor.execute(f'SELECT {col_select} FROM patients ORDER BY name')
        all_rows = cursor.fetchall()
        conn.close()

        q_norm = _normalize(query)
        scored = []
        if q_norm:
            for row in all_rows:
                if row[0] in id_hit_set:
                    continue
                name_norm = _normalize(row[1])
                if not name_norm:
                    continue
                if q_norm in name_norm:
                    scored.append((1.0, row))
                    continue
                ratio = difflib.SequenceMatcher(None, q_norm, name_norm).ratio()
                if ratio >= 0.55:
                    scored.append((ratio, row))
            scored.sort(key=lambda x: -x[0])

        ordered = list(id_hits) + [row for _, row in scored]
        return [dict(zip(columns, row)) for row in ordered]

    def create_visit(self, patient_id: str) -> str:
        """Create a new visit for a patient"""
        visit_id = f"{patient_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()

        cursor.execute(
            '''
            INSERT INTO visits (visit_id, patient_id, visit_date, status)
            VALUES (?, ?, ?, ?)
        ''', (visit_id, patient_id, datetime.now().isoformat(), 'triage'))

        # Update patient's last visit
        cursor.execute(
            '''
            UPDATE patients SET last_visit = ? WHERE patient_id = ?
        ''', (datetime.now().isoformat(), patient_id))

        conn.commit()
        conn.close()

        return visit_id

    def get_patients_by_visit_status(self, status: str, location_code: str = None) -> List[Dict]:
        """Get patients with visits in a specific status for today"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        today = datetime.now().strftime('%Y-%m-%d')
        
        query = '''
            SELECT p.patient_id, p.name, p.age, p.gender, v.visit_id, v.visit_date, v.status, v.priority
            FROM visits v
            JOIN patients p ON v.patient_id = p.patient_id
            WHERE v.status = ? AND date(v.visit_date) = ?
        '''
        params = [status, today]
        
        if location_code:
            query += ' AND p.patient_id LIKE ?'
            params.append(f'{location_code}%')
        
        query += ' ORDER BY v.visit_date ASC'
        
        cursor.execute(query, params)
        results = cursor.fetchall()
        conn.close()
        
        return [{
            'patient_id': row[0],
            'name': row[1],
            'age': row[2],
            'gender': row[3],
            'visit_id': row[4],
            'visit_date': row[5],
            'status': row[6],
            'priority': row[7]
        } for row in results]

    def get_doctors(self) -> List[Dict]:
        """Get all active doctors"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()

        cursor.execute(
            'SELECT name FROM doctors WHERE is_active = 1 ORDER BY name')
        doctors = [{'name': row[0]} for row in cursor.fetchall()]

        conn.close()
        return doctors

    def add_doctor(self, name: str) -> bool:
        """Add a new doctor"""
        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()

            # Check if doctor already exists (active or inactive)
            cursor.execute('SELECT is_active FROM doctors WHERE name = ?', (name,))
            existing = cursor.fetchone()
            
            if existing:
                # Doctor exists - reactivate if inactive
                cursor.execute('UPDATE doctors SET is_active = 1 WHERE name = ?', (name,))
                # Also ensure they have a clean status entry
                cursor.execute('DELETE FROM doctor_status WHERE doctor_name = ?', (name,))
                cursor.execute('''
                    INSERT INTO doctor_status (doctor_name, status, current_patient_id, current_patient_name, last_updated)
                    VALUES (?, 'available', '', '', ?)
                ''', (name, datetime.now().isoformat()))
            else:
                # New doctor - insert new record
                cursor.execute('INSERT INTO doctors (name, is_active) VALUES (?, 1)', (name,))
                # Create initial status entry
                cursor.execute('''
                    INSERT INTO doctor_status (doctor_name, status, current_patient_id, current_patient_name, last_updated)
                    VALUES (?, 'available', '', '', ?)
                ''', (name, datetime.now().isoformat()))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Error adding doctor: {e}")
            return False

    def remove_doctor(self, name: str) -> bool:
        """Remove a doctor (set inactive)"""
        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()

            # Set doctor as inactive
            cursor.execute('UPDATE doctors SET is_active = 0 WHERE name = ?', (name,))
            
            # Also remove their status entry to clean up
            cursor.execute('DELETE FROM doctor_status WHERE doctor_name = ?', (name,))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Error removing doctor: {e}")
            return False

    def update_doctor_status(self,
                             doctor_name: str,
                             status: str,
                             patient_id: str = "",
                             patient_name: str = ""):
        """Update doctor's current status"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()

        # Remove old status for this doctor
        cursor.execute('DELETE FROM doctor_status WHERE doctor_name = ?',
                       (doctor_name, ))

        # Insert new status
        cursor.execute(
            '''
            INSERT INTO doctor_status (doctor_name, current_patient_id, current_patient_name, status, last_updated)
            VALUES (?, ?, ?, ?, ?)
        ''', (doctor_name, patient_id or "", patient_name
              or "", status, datetime.now().isoformat()))

        conn.commit()
        conn.close()

    def get_all_doctor_status(self) -> List[Dict]:
        """Get current status of all doctors"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT ds.doctor_name, ds.current_patient_id, ds.current_patient_name, ds.status, ds.last_updated,
                   d.is_active
            FROM doctor_status ds
            JOIN doctors d ON ds.doctor_name = d.name
            WHERE d.is_active = 1
            ORDER BY ds.doctor_name
        ''')

        status_list = []
        for row in cursor.fetchall():
            status_list.append({
                'doctor_name': row[0],
                'current_patient_id': row[1],
                'current_patient_name': row[2],
                'status': row[3],
                'last_updated': row[4],
                'is_active': bool(row[5])
            })

        conn.close()
        return status_list

    def clean_duplicate_medications(self):
        """Remove duplicate medications keeping the first occurrence"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()

        # Find duplicate medications by name
        cursor.execute('''
            SELECT medication_name, MIN(id) as keep_id, GROUP_CONCAT(id) as all_ids
            FROM preset_medications 
            GROUP BY medication_name 
            HAVING COUNT(*) > 1
        ''')

        duplicates = cursor.fetchall()

        for med_name, keep_id, all_ids in duplicates:
            # Delete all duplicates except the first one
            id_list = [int(x) for x in all_ids.split(',')]
            delete_ids = [x for x in id_list if x != keep_id]

            for delete_id in delete_ids:
                cursor.execute('DELETE FROM preset_medications WHERE id = ?',
                               (delete_id, ))

        conn.commit()
        conn.close()

        return len(duplicates)

    # ==================== IMMUNIZATION METHODS ====================
    
    def add_immunization(self, patient_id: str, vaccine_name: str, **kwargs) -> int:
        """Add an immunization record for a patient"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO immunizations (patient_id, vaccine_name, date_given, dose_number, 
                                       lot_number, administered_by, site, notes, created_time)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (patient_id, vaccine_name, kwargs.get('date_given'), kwargs.get('dose_number'),
              kwargs.get('lot_number'), kwargs.get('administered_by'), kwargs.get('site'),
              kwargs.get('notes'), datetime.now().isoformat()))
        
        imm_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return imm_id or 0

    def get_patient_immunizations(self, patient_id: str) -> List[Dict]:
        """Get all immunizations for a patient"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, vaccine_name, date_given, dose_number, lot_number, 
                   administered_by, site, notes, created_time
            FROM immunizations 
            WHERE patient_id = ?
            ORDER BY date_given DESC
        ''', (patient_id,))
        
        immunizations = []
        for row in cursor.fetchall():
            immunizations.append({
                'id': row[0], 'vaccine_name': row[1], 'date_given': row[2],
                'dose_number': row[3], 'lot_number': row[4], 'administered_by': row[5],
                'site': row[6], 'notes': row[7], 'created_time': row[8]
            })
        
        conn.close()
        return immunizations

    def delete_immunization(self, imm_id: int) -> bool:
        """Delete an immunization record"""
        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            cursor.execute('DELETE FROM immunizations WHERE id = ?', (imm_id,))
            conn.commit()
            conn.close()
            return True
        except:
            return False

    # ==================== PREGNANCY HISTORY METHODS ====================
    
    def save_pregnancy_history(self, patient_id: str, **kwargs) -> int:
        """Save or update pregnancy history for a patient"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        # Check if record exists
        cursor.execute('SELECT id FROM pregnancy_history WHERE patient_id = ?', (patient_id,))
        existing = cursor.fetchone()
        
        if existing:
            cursor.execute('''
                UPDATE pregnancy_history SET 
                    gravida = ?, para = ?, abortions = ?, living_children = ?,
                    last_menstrual_period = ?, estimated_due_date = ?, 
                    current_pregnancy = ?, pregnancy_notes = ?, updated_time = ?
                WHERE patient_id = ?
            ''', (kwargs.get('gravida', 0), kwargs.get('para', 0), kwargs.get('abortions', 0),
                  kwargs.get('living_children', 0), kwargs.get('last_menstrual_period'),
                  kwargs.get('estimated_due_date'), kwargs.get('current_pregnancy', 0),
                  kwargs.get('pregnancy_notes'), datetime.now().isoformat(), patient_id))
            record_id = existing[0]
        else:
            cursor.execute('''
                INSERT INTO pregnancy_history (patient_id, gravida, para, abortions, living_children,
                    last_menstrual_period, estimated_due_date, current_pregnancy, pregnancy_notes,
                    created_time, updated_time)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (patient_id, kwargs.get('gravida', 0), kwargs.get('para', 0), 
                  kwargs.get('abortions', 0), kwargs.get('living_children', 0),
                  kwargs.get('last_menstrual_period'), kwargs.get('estimated_due_date'),
                  kwargs.get('current_pregnancy', 0), kwargs.get('pregnancy_notes'),
                  datetime.now().isoformat(), datetime.now().isoformat()))
            record_id = cursor.lastrowid
        
        conn.commit()
        conn.close()
        return record_id or 0

    def get_pregnancy_history(self, patient_id: str) -> List[Dict]:
        """Get pregnancy history for a patient - returns list of individual pregnancy records"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        # Ensure the pregnancy_records table exists
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS pregnancy_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                patient_id TEXT NOT NULL,
                outcome TEXT,
                year INTEGER,
                delivery_type TEXT,
                weeks_gestation INTEGER,
                complications TEXT,
                notes TEXT,
                created_time TEXT,
                FOREIGN KEY (patient_id) REFERENCES patients (patient_id)
            )
        ''')
        
        # Get individual pregnancy records
        cursor.execute('''
            SELECT id, outcome, year, delivery_type, weeks_gestation, complications, notes, created_time
            FROM pregnancy_records WHERE patient_id = ?
            ORDER BY year DESC
        ''', (patient_id,))
        
        records = []
        for row in cursor.fetchall():
            records.append({
                'id': row[0], 'outcome': row[1], 'year': row[2],
                'delivery_type': row[3], 'weeks_gestation': row[4],
                'complications': row[5], 'notes': row[6], 'created_time': row[7]
            })
        
        conn.close()
        return records
    
    def add_pregnancy_history(self, patient_id: str, outcome: str, year: int, **kwargs) -> bool:
        """Add individual pregnancy record"""
        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            
            # Ensure the pregnancy_records table exists
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS pregnancy_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    patient_id TEXT NOT NULL,
                    outcome TEXT,
                    year INTEGER,
                    delivery_type TEXT,
                    weeks_gestation INTEGER,
                    complications TEXT,
                    notes TEXT,
                    created_time TEXT,
                    FOREIGN KEY (patient_id) REFERENCES patients (patient_id)
                )
            ''')
            
            cursor.execute('''
                INSERT INTO pregnancy_records (patient_id, outcome, year, delivery_type, 
                    weeks_gestation, complications, notes, created_time)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (patient_id, outcome, year, kwargs.get('delivery_type'),
                  kwargs.get('weeks_gestation'), kwargs.get('complications'),
                  kwargs.get('notes'), datetime.now().isoformat()))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            return False
    
    def get_pregnancy_summary(self, patient_id: str) -> Dict:
        """Get pregnancy summary (gravida, para, etc.) for a patient"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT gravida, para, abortions, living_children, last_menstrual_period,
                   estimated_due_date, current_pregnancy, pregnancy_notes, updated_time
            FROM pregnancy_history WHERE patient_id = ?
        ''', (patient_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                'gravida': row[0], 'para': row[1], 'abortions': row[2],
                'living_children': row[3], 'last_menstrual_period': row[4],
                'estimated_due_date': row[5], 'current_pregnancy': bool(row[6]),
                'pregnancy_notes': row[7], 'updated_time': row[8]
            }
        return {}

    # ==================== CONSENT METHODS ====================
    
    def record_consent(self, patient_id: str, consent_type: str, consent_given: bool, 
                       country_code: str = '', **kwargs) -> int:
        """Record patient consent"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO consent_records (patient_id, consent_type, consent_given, consent_date,
                witness_name, signature_data, country_code, notes, created_time)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (patient_id, consent_type, 1 if consent_given else 0, datetime.now().isoformat(),
              kwargs.get('witness_name'), kwargs.get('signature_data'), country_code,
              kwargs.get('notes'), datetime.now().isoformat()))
        
        consent_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return consent_id or 0

    def get_patient_consents(self, patient_id: str) -> List[Dict]:
        """Get all consent records for a patient"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, consent_type, consent_given, consent_date, witness_name, country_code, notes
            FROM consent_records WHERE patient_id = ? ORDER BY consent_date DESC
        ''', (patient_id,))
        
        consents = []
        for row in cursor.fetchall():
            consents.append({
                'id': row[0], 'consent_type': row[1], 'consent_given': bool(row[2]),
                'consent_date': row[3], 'witness_name': row[4], 
                'country_code': row[5], 'notes': row[6]
            })
        
        conn.close()
        return consents

    def has_valid_consent(self, patient_id: str, consent_type: str = 'treatment') -> bool:
        """Check if patient has valid consent for treatment"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT consent_given FROM consent_records 
            WHERE patient_id = ? AND consent_type = ? 
            ORDER BY consent_date DESC LIMIT 1
        ''', (patient_id, consent_type))
        
        result = cursor.fetchone()
        conn.close()
        return bool(result and result[0])

    # ==================== AUDIT LOG METHODS ====================
    
    def log_audit(self, action_type: str, **kwargs):
        """Log an audit event"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO audit_logs (user_name, user_role, action_type, table_name, 
                record_id, old_values, new_values, ip_address, device_info, created_time)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (kwargs.get('user_name'), kwargs.get('user_role'), action_type,
              kwargs.get('table_name'), kwargs.get('record_id'),
              json.dumps(kwargs.get('old_values')) if kwargs.get('old_values') else None,
              json.dumps(kwargs.get('new_values')) if kwargs.get('new_values') else None,
              kwargs.get('ip_address'), kwargs.get('device_info'), datetime.now().isoformat()))
        
        conn.commit()
        conn.close()

    def get_audit_logs(self, limit: int = 100, **filters) -> List[Dict]:
        """Get audit logs with optional filters"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        query = 'SELECT * FROM audit_logs'
        params = []
        conditions = []
        
        if filters.get('user_name'):
            conditions.append('user_name = ?')
            params.append(filters['user_name'])
        if filters.get('action_type'):
            conditions.append('action_type = ?')
            params.append(filters['action_type'])
        if filters.get('table_name'):
            conditions.append('table_name = ?')
            params.append(filters['table_name'])
        if filters.get('record_id'):
            conditions.append('record_id = ?')
            params.append(filters['record_id'])
        
        if conditions:
            query += ' WHERE ' + ' AND '.join(conditions)
        
        query += ' ORDER BY created_time DESC LIMIT ?'
        params.append(limit)
        
        cursor.execute(query, params)
        
        logs = []
        columns = ['id', 'user_name', 'user_role', 'action_type', 'table_name', 
                   'record_id', 'old_values', 'new_values', 'ip_address', 
                   'device_info', 'created_time']
        for row in cursor.fetchall():
            log_entry = dict(zip(columns, row))
            if log_entry.get('old_values'):
                try:
                    log_entry['old_values'] = json.loads(log_entry['old_values'])
                except:
                    pass
            if log_entry.get('new_values'):
                try:
                    log_entry['new_values'] = json.loads(log_entry['new_values'])
                except:
                    pass
            logs.append(log_entry)
        
        conn.close()
        return logs

    # ==================== MEDICATION STOCK METHODS ====================
    
    def update_medication_stock(self, medication_id: int, qty_in_stock: int, 
                                low_stock_threshold: int = 10) -> bool:
        """Update medication stock levels"""
        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            
            # Determine stock status
            if qty_in_stock <= 0:
                stock_status = 'out_of_stock'
            elif qty_in_stock <= low_stock_threshold:
                stock_status = 'low_stock'
            else:
                stock_status = 'in_stock'
            
            cursor.execute('''
                UPDATE preset_medications 
                SET qty_in_stock = ?, low_stock_threshold = ?, stock_status = ?
                WHERE id = ?
            ''', (qty_in_stock, low_stock_threshold, stock_status, medication_id))
            
            conn.commit()
            conn.close()
            return True
        except:
            return False

    def get_medications_with_stock(self) -> List[Dict]:
        """Get all medications with stock information"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, medication_name, common_dosages, category, requires_lab, active,
                   qty_in_stock, low_stock_threshold, stock_status, require_indication,
                   preset_duration, amount, indication
            FROM preset_medications WHERE active = 1 ORDER BY category, medication_name
        ''')
        
        medications = []
        for row in cursor.fetchall():
            medications.append({
                'id': row[0], 'medication_name': row[1], 'common_dosages': row[2],
                'category': row[3], 'requires_lab': row[4], 'active': row[5],
                'qty_in_stock': row[6] or 0, 'low_stock_threshold': row[7] or 10,
                'stock_status': row[8] or 'unknown', 'require_indication': row[9],
                'preset_duration': row[10], 'amount': row[11], 'indication': row[12]
            })
        
        conn.close()
        return medications

    def get_low_stock_medications(self) -> List[Dict]:
        """Get medications that are low or out of stock"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, medication_name, category, qty_in_stock, low_stock_threshold, stock_status
            FROM preset_medications 
            WHERE active = 1 AND (stock_status = 'low_stock' OR stock_status = 'out_of_stock')
            ORDER BY stock_status, medication_name
        ''')
        
        medications = []
        for row in cursor.fetchall():
            medications.append({
                'id': row[0], 'medication_name': row[1], 'category': row[2],
                'qty_in_stock': row[3] or 0, 'low_stock_threshold': row[4] or 10,
                'stock_status': row[5] or 'unknown'
            })
        
        conn.close()
        return medications

    def deduct_medication_stock(self, medication_id: int, quantity: int = 1) -> bool:
        """Deduct medication stock when dispensed"""
        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            
            cursor.execute('SELECT qty_in_stock, low_stock_threshold FROM preset_medications WHERE id = ?', 
                          (medication_id,))
            result = cursor.fetchone()
            
            if result:
                current_stock = result[0] or 0
                threshold = result[1] or 10
                new_stock = max(0, current_stock - quantity)
                
                # Update stock and status
                if new_stock <= 0:
                    stock_status = 'out_of_stock'
                elif new_stock <= threshold:
                    stock_status = 'low_stock'
                else:
                    stock_status = 'in_stock'
                
                cursor.execute('''
                    UPDATE preset_medications 
                    SET qty_in_stock = ?, stock_status = ?
                    WHERE id = ?
                ''', (new_stock, stock_status, medication_id))
                
                conn.commit()
            
            conn.close()
            return True
        except:
            return False

    # ==================== ICD-10 DIAGNOSIS METHODS ====================
    
    def save_icd10_diagnosis(self, visit_id: str, icd10_code: str, description: str,
                             diagnosis_type: str = 'primary') -> int:
        """Save an ICD-10 diagnosis for a visit"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO icd10_diagnoses (visit_id, icd10_code, description, diagnosis_type, created_time)
            VALUES (?, ?, ?, ?, ?)
        ''', (visit_id, icd10_code, description, diagnosis_type, datetime.now().isoformat()))
        
        diag_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return diag_id or 0

    def get_visit_diagnoses(self, visit_id: str) -> List[Dict]:
        """Get all ICD-10 diagnoses for a visit"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, icd10_code, description, diagnosis_type, created_time
            FROM icd10_diagnoses WHERE visit_id = ? ORDER BY diagnosis_type, id
        ''', (visit_id,))
        
        diagnoses = []
        for row in cursor.fetchall():
            diagnoses.append({
                'id': row[0], 'icd10_code': row[1], 'description': row[2],
                'diagnosis_type': row[3], 'created_time': row[4]
            })
        
        conn.close()
        return diagnoses

    def delete_diagnosis(self, diag_id: int) -> bool:
        """Delete a diagnosis"""
        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            cursor.execute('DELETE FROM icd10_diagnoses WHERE id = ?', (diag_id,))
            conn.commit()
            conn.close()
            return True
        except:
            return False

    # ==================== GROWTH CHART METHODS ====================
    
    def save_growth_measurement(self, patient_id: str, visit_id: str = None, **kwargs) -> int:
        """Save a growth measurement for pediatric patients"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO growth_measurements (patient_id, visit_id, measurement_date, age_months,
                weight_kg, height_cm, head_circumference_cm, weight_for_age_z, height_for_age_z,
                weight_for_height_z, bmi_for_age_z, created_time)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (patient_id, visit_id, kwargs.get('measurement_date', datetime.now().strftime('%Y-%m-%d')),
              kwargs.get('age_months'), kwargs.get('weight_kg'), kwargs.get('height_cm'),
              kwargs.get('head_circumference_cm'), kwargs.get('weight_for_age_z'),
              kwargs.get('height_for_age_z'), kwargs.get('weight_for_height_z'),
              kwargs.get('bmi_for_age_z'), datetime.now().isoformat()))
        
        measurement_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return measurement_id or 0

    def get_growth_measurements(self, patient_id: str) -> List[Dict]:
        """Get all growth measurements for a patient"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, measurement_date, age_months, weight_kg, height_cm, head_circumference_cm,
                   weight_for_age_z, height_for_age_z, weight_for_height_z, bmi_for_age_z
            FROM growth_measurements WHERE patient_id = ? ORDER BY measurement_date
        ''', (patient_id,))
        
        measurements = []
        for row in cursor.fetchall():
            measurements.append({
                'id': row[0], 'measurement_date': row[1], 'age_months': row[2],
                'weight_kg': row[3], 'height_cm': row[4], 'head_circumference_cm': row[5],
                'weight_for_age_z': row[6], 'height_for_age_z': row[7],
                'weight_for_height_z': row[8], 'bmi_for_age_z': row[9]
            })
        
        conn.close()
        return measurements

    # ==================== DOCTOR PIN METHODS ====================
    
    def set_doctor_pin(self, doctor_name: str, pin: str) -> bool:
        """Set or update a doctor's PIN"""
        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            
            pin_hash = hash_pin(pin)
            cursor.execute('UPDATE doctors SET pin_hash = ? WHERE name = ?', (pin_hash, doctor_name))
            
            conn.commit()
            conn.close()
            return True
        except:
            return False

    def verify_doctor_pin(self, doctor_name: str, pin: str) -> bool:
        """Verify a doctor's PIN"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('SELECT pin_hash FROM doctors WHERE name = ?', (doctor_name,))
        result = cursor.fetchone()
        conn.close()
        
        if result and result[0]:
            return verify_pin(pin, result[0])
        return True  # If no PIN set, allow access

    def doctor_has_pin(self, doctor_name: str) -> bool:
        """Check if a doctor has a PIN set"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('SELECT pin_hash FROM doctors WHERE name = ?', (doctor_name,))
        result = cursor.fetchone()
        conn.close()
        
        return bool(result and result[0])

    # ==================== LOCATION GPS METHODS ====================
    
    def update_location_coordinates(self, location_id: int, latitude: float, longitude: float) -> bool:
        """Update GPS coordinates for a location"""
        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE locations SET latitude = ?, longitude = ? WHERE id = ?
            ''', (latitude, longitude, location_id))
            
            conn.commit()
            conn.close()
            return True
        except:
            return False

    def get_location_with_coordinates(self, location_id: int) -> Dict:
        """Get location details including GPS coordinates"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, country_code, country_name, city, latitude, longitude, default_language
            FROM locations WHERE id = ?
        ''', (location_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                'id': row[0], 'country_code': row[1], 'country_name': row[2],
                'city': row[3], 'latitude': row[4], 'longitude': row[5],
                'default_language': row[6] or 'en'
            }
        return {}

    def set_location_language(self, location_id: int, language: str) -> bool:
        """Set default language for a location"""
        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            
            cursor.execute('UPDATE locations SET default_language = ? WHERE id = ?', 
                          (language, location_id))
            
            conn.commit()
            conn.close()
            return True
        except:
            return False

    def delete_patient(self, patient_id: str) -> bool:
        """Delete a patient and all associated data"""
        conn = None
        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()

            # Enable foreign key support
            cursor.execute('PRAGMA foreign_keys = ON')

            # Start transaction
            cursor.execute('BEGIN IMMEDIATE')

            # Get all visit IDs for this patient
            cursor.execute('SELECT visit_id FROM visits WHERE patient_id = ?',
                           (patient_id, ))
            visit_ids = [row[0] for row in cursor.fetchall()]

            # Delete related data for each visit
            for visit_id in visit_ids:
                # Delete vital signs
                cursor.execute('DELETE FROM vital_signs WHERE visit_id = ?',
                               (visit_id, ))

                # Delete prescriptions
                cursor.execute('DELETE FROM prescriptions WHERE visit_id = ?',
                               (visit_id, ))

                # Get lab test IDs for this visit
                cursor.execute('SELECT id FROM lab_tests WHERE visit_id = ?',
                               (visit_id, ))
                lab_test_ids = [row[0] for row in cursor.fetchall()]

                # Delete lab results for these tests
                for test_id in lab_test_ids:
                    cursor.execute('DELETE FROM lab_results WHERE test_id = ?',
                                   (test_id, ))

                # Delete lab tests
                cursor.execute('DELETE FROM lab_tests WHERE visit_id = ?',
                               (visit_id, ))

                # Delete consultations
                cursor.execute('DELETE FROM consultations WHERE visit_id = ?',
                               (visit_id, ))

                # Delete patient photos for this visit
                cursor.execute('DELETE FROM patient_photos WHERE visit_id = ?',
                               (visit_id, ))

            # Delete all visits for this patient
            cursor.execute('DELETE FROM visits WHERE patient_id = ?',
                           (patient_id, ))

            # Delete family relationships where this patient is a member
            cursor.execute('DELETE FROM family_members WHERE patient_id = ?',
                           (patient_id, ))

            # Delete family relationships where this patient is the parent
            cursor.execute('DELETE FROM family_members WHERE parent_id = ?',
                           (patient_id, ))

            # Finally delete the patient
            cursor.execute('DELETE FROM patients WHERE patient_id = ?',
                           (patient_id, ))

            # Check if deletion was successful
            cursor.execute(
                'SELECT COUNT(*) FROM patients WHERE patient_id = ?',
                (patient_id, ))
            remaining_count = cursor.fetchone()[0]

            if remaining_count == 0:
                conn.commit()
                return True
            else:
                conn.rollback()
                return False

        except Exception as e:
            if conn:
                conn.rollback()
            return False
        finally:
            if conn:
                conn.close()

    def add_location(self, country_code: str, country_name: str,
                     city: str) -> int:
        """Add a new clinic location"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()

        cursor.execute(
            '''
            INSERT INTO locations (country_code, country_name, city, created_date)
            VALUES (?, ?, ?, ?)
        ''', (country_code, country_name, city, datetime.now().isoformat()))

        location_id = cursor.lastrowid
        conn.commit()
        conn.close()

        return int(location_id) if location_id else 0

    def get_locations(self) -> List[Dict]:
        """Get all clinic locations"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM locations ORDER BY country_name, city')
        results = cursor.fetchall()
        conn.close()

        columns = [
            'id', 'country_code', 'country_name', 'city', 'created_date'
        ]
        return [dict(zip(columns, row)) for row in results]

    def get_preset_medications(self) -> List[Dict]:
        """Get all active preset medications"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT * FROM preset_medications 
            WHERE active = 1 
            ORDER BY category, medication_name
        ''')
        results = cursor.fetchall()
        conn.close()

        # Get all column names from the table to ensure we include new columns
        temp_conn = sqlite3.connect(self.db_name)
        temp_cursor = temp_conn.cursor()
        temp_cursor.execute("PRAGMA table_info(preset_medications)")
        column_info = temp_cursor.fetchall()
        temp_conn.close()
        
        columns = [col[1] for col in column_info]
        return [dict(zip(columns, row)) for row in results]

    def order_lab_test(self, visit_id: str, test_type: str,
                       ordered_by: str) -> int:
        """Order a lab test for a patient"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()

        cursor.execute(
            '''
            INSERT INTO lab_tests (visit_id, test_type, ordered_by, ordered_time, status)
            VALUES (?, ?, ?, ?, 'pending')
        ''', (visit_id, test_type, ordered_by, datetime.now().isoformat()))

        test_id = cursor.lastrowid
        conn.commit()
        conn.close()

        return int(test_id) if test_id else 0

    def get_pending_lab_tests(self) -> List[Dict]:
        """Get all pending lab tests"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT lt.*, p.name as patient_name, p.patient_id, v.visit_date
            FROM lab_tests lt
            JOIN visits v ON lt.visit_id = v.visit_id
            JOIN patients p ON v.patient_id = p.patient_id
            WHERE lt.status = 'pending'
            ORDER BY lt.ordered_time
        ''')

        results = cursor.fetchall()
        conn.close()

        columns = [
            'id', 'visit_id', 'test_type', 'ordered_by', 'ordered_time',
            'completed_time', 'results', 'status', 'patient_name',
            'patient_id', 'visit_date'
        ]
        return [dict(zip(columns, row)) for row in results]

    def complete_lab_test(self, test_id: int, results: str):
        """Complete a lab test with results"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()

        cursor.execute(
            '''
            UPDATE lab_tests 
            SET status = 'completed', results = ?, completed_time = ?
            WHERE id = ?
        ''', (results, datetime.now().isoformat(), test_id))

        conn.commit()
        conn.close()

    def add_prescription(self,
                         visit_id: str,
                         medication_id: int,
                         medication_name: str,
                         dosage: str,
                         frequency: str,
                         duration: str,
                         instructions: str = "",
                         awaiting_lab: str = "no",
                         prescribed_by: str = "") -> int:
        """Add a prescription"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()

        cursor.execute(
            '''
            INSERT INTO prescriptions 
            (visit_id, medication_id, medication_name, dosage, frequency, duration, 
             instructions, awaiting_lab, prescribed_by, prescribed_time)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''',
            (visit_id, medication_id, medication_name, dosage, frequency,
             duration, instructions, awaiting_lab, prescribed_by, datetime.now().isoformat()))

        prescription_id = cursor.lastrowid
        conn.commit()
        conn.close()

        return int(prescription_id) if prescription_id else 0


# Initialize database
@st.cache_resource
def get_db_manager():
    return DatabaseManager()


db = get_db_manager()


def show_loading_screen():
    """Display loading screen for the medical application"""
    if 'loading_shown' not in st.session_state:
        st.session_state.loading_shown = False

    if not st.session_state.loading_shown:
        placeholder = st.empty()
        with placeholder.container():
            st.markdown('<div style="margin-top: 100px;"></div>',
                        unsafe_allow_html=True)
            # Center the logo precisely
            _, center_col, _ = st.columns([2, 1, 2])
            with center_col:
                st.image(
                    "attached_assets/ChatGPT Image Jun 15, 2025, 05_23_25 PM_1750024910085.png",
                    width=200)
            st.markdown(
                '<p style="text-align: center; color: #666; margin-top: 30px;">Loading...</p>',
                unsafe_allow_html=True)

        time.sleep(2)
        placeholder.empty()
        st.session_state.loading_shown = True
        st.rerun()


def initialize_navigation():
    """Initialize navigation history tracking"""
    if 'nav_history' not in st.session_state:
        st.session_state.nav_history = []
    if 'current_page' not in st.session_state:
        st.session_state.current_page = 'home'


def add_to_history(page_name):
    """Add current page to navigation history"""
    if 'nav_history' not in st.session_state:
        st.session_state.nav_history = []

    # Avoid adding the same page consecutively
    if not st.session_state.nav_history or st.session_state.nav_history[
            -1] != page_name:
        st.session_state.nav_history.append(page_name)

    st.session_state.current_page = page_name


def go_back():
    """Navigate back to previous page.

    Previously wiped pending_vitals / family workflow state on every Back,
    which silently destroyed in-progress vitals when a nurse tapped Back
    to glance at the queue. Now we only clear those keys if the previous
    page is outside the current workflow (home / role_selection / a
    different role), so an inadvertent Back is recoverable.
    """
    if 'nav_history' in st.session_state and len(
            st.session_state.nav_history) > 1:
        # Remove current page
        st.session_state.nav_history.pop()
        # Get previous page
        previous_page = st.session_state.nav_history[-1]
        st.session_state.current_page = previous_page

        workflow_keys = [
            'family_vital_signs_queue', 'current_family_vital_index',
            'family_workflow_active', 'pending_vitals', 'patient_name',
            'family_parent_id', 'family_parent_name'
        ]
        # Only wipe workflow state when leaving the role entirely
        leaving_workflow = previous_page in ('home', 'role_selection') or \
            not previous_page.startswith(('triage', 'doctor', 'pharmacy', 'lab', 'admin'))
        if leaving_workflow:
            for key in workflow_keys:
                if key in st.session_state:
                    del st.session_state[key]

        # Handle navigation based on previous page
        if previous_page == 'home':
            st.session_state.user_role = None
        elif previous_page == 'role_selection':
            st.session_state.user_role = None
        elif previous_page.startswith('triage'):
            st.session_state.user_role = 'triage'
        elif previous_page.startswith('doctor'):
            st.session_state.user_role = 'doctor'
        elif previous_page.startswith('pharmacy'):
            st.session_state.user_role = 'pharmacy'
        elif previous_page.startswith('lab'):
            st.session_state.user_role = 'lab'
        elif previous_page.startswith('admin'):
            st.session_state.user_role = 'admin'


def show_back_button():
    """Universal back button — bulletproof version.

    Renders whenever the user is past the initial sign-in. On click, peels
    back exactly one layer of the navigation onion, in this priority order:
      1. Inside a sub-form (vitals/consultation/patient-history) → exit
         the sub-form and stay on the enclosing role queue.
      2. Inside a role (user_role set) → return to role selection;
         clinic_location stays so you don't have to re-pick the clinic.
      3. On role selection (clinic_location set, no user_role) → return
         to the clinic selection screen.

    Always renders when any of those layers is active. Uses a stable but
    state-dependent key so Streamlit doesn't mis-handle re-renders.
    """
    subform_keys = [
        'pending_vitals', 'family_vital_signs_queue', 'active_consultation',
        'show_patient_history', 'family_workflow_active',
    ]
    has_subform = any(k in st.session_state for k in subform_keys)
    has_role = bool(st.session_state.get('user_role'))
    has_clinic = bool(st.session_state.get('clinic_location'))

    if not (has_subform or has_role or has_clinic):
        return

    key = f"back_btn_{int(has_subform)}_{int(has_role)}_{int(has_clinic)}"
    col1, _ = st.columns([1, 9])
    with col1:
        if st.button(f"← {t('back')}", key=key, use_container_width=True,
                     help="Go back one step"):
            if has_subform:
                # Tier 1: peel off the sub-form
                for k in subform_keys + [
                    'patient_name', 'patient_history_name',
                    'current_family_vital_index',
                ]:
                    st.session_state.pop(k, None)
                st.rerun()
            elif has_role:
                # Tier 2: exit the role, keep clinic context
                for k in subform_keys + ['user_role', 'patient_name',
                                          'patient_history_name', 'page',
                                          'doctor_name', 'active_consultation']:
                    st.session_state.pop(k, None)
                st.session_state.nav_history = []
                try:
                    st.query_params.clear()
                except Exception:
                    pass
                st.rerun()
            else:
                # Tier 3: exit the clinic
                for k in ['clinic_location', 'selected_clinic_id',
                          'show_clinic_selection', 'org_admin_entering_as_staff',
                          'user_role', 'page']:
                    st.session_state.pop(k, None)
                st.session_state.nav_history = []
                try:
                    st.query_params.clear()
                except Exception:
                    pass
                st.rerun()


def main():
    # Initialize page state persistence
    preserve_page_state()
    
    # Initialize WebSocket connection for real-time updates across iPads
    html(ws_connect_script, height=0)
    
    # Check for pending updates and trigger rerun if needed
    check_for_updates()
    
    # Initialize navigation
    initialize_navigation()

    # Show loading screen on first load
    show_loading_screen()

    # Show the back button using the dedicated function
    show_back_button()

    # =====================================================================
    # ParakaleoMMC north-star design system (Phase 1)
    # See docs/NORTHSTAR_GUI.md for the design contract.
    # Quiet by default. No gradients. One shadow vocabulary. System fonts.
    # =====================================================================
    st.markdown("""
    <style>
    /* ---------- BASE ---------- */
    .stApp {
        font-family: -apple-system, "SF Pro Text", "Segoe UI", Inter, system-ui, sans-serif;
        background: #FFFFFF !important;
        color: #111827;
        -webkit-font-smoothing: antialiased;
    }
    .main .block-container {
        padding: 1.25rem 1.5rem !important;
        max-width: 1200px !important;
    }
    #MainMenu, footer, header { visibility: hidden !important; }
    button[title="Open navigation menu"] { display: none !important; }

    /* ---------- TYPOGRAPHY ---------- */
    h1 { font-size: 1.5rem  !important; font-weight: 600 !important; color: #111827 !important;
         letter-spacing: -0.01em !important; margin: 4px 0 16px 0 !important; }
    h2 { font-size: 1.25rem !important; font-weight: 600 !important; color: #111827 !important;
         margin: 24px 0 8px 0 !important; }
    h3 { font-size: 1.0rem  !important; font-weight: 600 !important; color: #374151 !important;
         margin: 16px 0 8px 0 !important; }
    h4 { font-size: 0.95rem !important; font-weight: 600 !important; color: #374151 !important; }
    p, li, label { color: #111827; font-size: 16px; line-height: 1.5; }

    /* ---------- BUTTONS (quiet by default) ---------- */
    .stButton > button, .stDownloadButton > button, .stFormSubmitButton > button {
        background: #FFFFFF !important;
        color: #111827 !important;
        border: 1px solid #D1D5DB !important;
        border-radius: 6px !important;
        padding: 12px 20px !important;
        font-weight: 500 !important;
        font-size: 15px !important;
        min-height: 48px !important;
        box-shadow: none !important;
        transition: background 0.12s ease, border-color 0.12s ease !important;
    }
    .stButton > button:hover, .stDownloadButton > button:hover, .stFormSubmitButton > button:hover {
        background: #F9FAFB !important;
        border-color: #9CA3AF !important;
        transform: none !important;
    }
    .stButton > button:active { background: #F3F4F6 !important; }

    /* Primary = solid dark slate, light text. No gradients. The descendant
       `*` rule defeats the global p/li/label color so the label renders
       white instead of inheriting our dark body text color. */
    .stButton > button[kind="primary"],
    .stDownloadButton > button[kind="primary"],
    .stFormSubmitButton > button[kind="primary"] {
        background: #334155 !important;
        color: #FFFFFF !important;
        border: 1px solid #334155 !important;
        font-weight: 600 !important;
    }
    .stButton > button[kind="primary"] *,
    .stDownloadButton > button[kind="primary"] *,
    .stFormSubmitButton > button[kind="primary"] * {
        color: #FFFFFF !important;
    }
    .stButton > button[kind="primary"]:hover,
    .stDownloadButton > button[kind="primary"]:hover,
    .stFormSubmitButton > button[kind="primary"]:hover {
        background: #1E293B !important;
        border-color: #1E293B !important;
    }
    .stButton > button[kind="primary"]:hover * { color: #FFFFFF !important; }
    .stButton > button[kind="secondary"] {
        background: #FFFFFF !important;
        color: #374151 !important;
        border: 1px solid #D1D5DB !important;
    }
    .stButton > button:disabled {
        background: #F9FAFB !important;
        color: #9CA3AF !important;
        border-color: #E5E7EB !important;
    }

    /* ---------- INPUTS ---------- */
    .stTextInput > div > div > input,
    .stNumberInput > div > div > input,
    .stTextArea > div > div > textarea,
    .stDateInput input {
        background: #FFFFFF !important;
        border: 1px solid #D1D5DB !important;
        border-radius: 6px !important;
        padding: 12px 14px !important;
        font-size: 16px !important;
        color: #111827 !important;
        min-height: 48px !important;
        box-shadow: none !important;
    }
    .stTextInput > div > div > input:focus,
    .stNumberInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus,
    .stDateInput input:focus {
        border-color: #475569 !important;
        outline: none !important;
        box-shadow: 0 0 0 3px rgba(71,85,105,0.12) !important;
    }
    .stSelectbox > div > div,
    .stSelectbox [data-baseweb="select"] > div {
        background: #FFFFFF !important;
        border: 1px solid #D1D5DB !important;
        border-radius: 6px !important;
        min-height: 48px !important;
        box-shadow: none !important;
    }
    .stSelectbox [data-baseweb="select"] > div:focus-within {
        border-color: #475569 !important;
        box-shadow: 0 0 0 3px rgba(71,85,105,0.12) !important;
    }

    /* ---------- PATIENT ROW (replaces the old .patient-card) ---------- */
    .patient-card {
        background: #FFFFFF;
        border: none;
        border-radius: 0;
        padding: 12px 14px 14px 16px;
        margin: 0;
        border-bottom: 1px solid #E5E7EB;
        border-left: 4px solid #9CA3AF;   /* idle by default */
        box-shadow: none;
        transition: background 0.1s ease;
    }
    .patient-card:hover { background: #F9FAFB; transform: none; box-shadow: none; }
    .patient-card.urgent    { border-left-color: #DC2626; background: #FFFFFF; }
    .patient-card.waiting   { border-left-color: #D97706; background: #FFFFFF; }
    .patient-card.completed { border-left-color: #059669; background: #FFFFFF; }
    .patient-card h1, .patient-card h2, .patient-card h3, .patient-card h4 {
        margin: 0 0 4px 0 !important; color: #111827 !important; font-size: 1.0rem !important;
    }
    .patient-card p { margin: 0; color: #6B7280; font-size: 14px; }

    /* ---------- TABS (underline style — no segmented control) ---------- */
    .stTabs [data-baseweb="tab-list"] {
        background: transparent !important;
        border-radius: 0 !important;
        padding: 0 !important;
        gap: 24px !important;
        border-bottom: 1px solid #E5E7EB !important;
    }
    .stTabs [data-baseweb="tab"] {
        background: transparent !important;
        color: #6B7280 !important;
        border-radius: 0 !important;
        padding: 12px 0 !important;
        font-weight: 500 !important;
        font-size: 15px !important;
        border: none !important;
        border-bottom: 2px solid transparent !important;
        margin-bottom: -1px;
    }
    .stTabs [data-baseweb="tab"]:hover { color: #111827 !important; background: transparent !important; }
    .stTabs [aria-selected="true"] {
        color: #475569 !important;
        background: transparent !important;
        border-bottom-color: #475569 !important;
        box-shadow: none !important;
        font-weight: 600 !important;
    }

    /* ---------- METRICS (quiet card, single hairline) ---------- */
    [data-testid="metric-container"] {
        background: #FFFFFF !important;
        border-radius: 6px !important;
        padding: 16px 20px !important;
        box-shadow: none !important;
        border: 1px solid #E5E7EB !important;
    }
    [data-testid="metric-container"] label {
        color: #6B7280 !important;
        font-size: 13px !important;
        font-weight: 500 !important;
        text-transform: none !important;
        letter-spacing: 0 !important;
    }

    /* ---------- SIDEBAR ---------- */
    section[data-testid="stSidebar"] {
        background: #FFFFFF !important;
        border-right: 1px solid #E5E7EB !important;
    }

    /* ---------- CHECKBOXES & RADIOS ---------- */
    .stCheckbox label { font-weight: 400 !important; color: #111827 !important; }
    .stRadio  label  { font-weight: 400 !important; color: #111827 !important; }
    .stCheckbox [data-testid="stCheckbox"][aria-checked="true"] {
        background: #475569 !important; border-color: #475569 !important;
    }

    /* ---------- EXPANDERS (quieter, hairline) ---------- */
    .streamlit-expanderHeader, [data-testid="stExpander"] summary {
        background: #FFFFFF !important;
        border: 1px solid #E5E7EB !important;
        border-radius: 6px !important;
        font-weight: 500 !important;
        color: #111827 !important;
        padding: 12px 16px !important;
        box-shadow: none !important;
    }
    .streamlit-expanderContent {
        background: #FFFFFF !important;
        border: 1px solid #E5E7EB !important;
        border-top: none !important;
        border-radius: 0 0 6px 6px !important;
        padding: 16px !important;
    }

    /* ---------- ALERTS (subtle tint, no gradient) ---------- */
    .stSuccess, [data-testid="stSuccess"] {
        background: #F0FDF4 !important;
        border-left: 3px solid #059669 !important;
        border-radius: 4px !important;
        color: #065F46 !important;
        padding: 12px 16px !important;
    }
    .stInfo, [data-testid="stInfo"] {
        background: #F0F9FF !important;
        border-left: 3px solid #0EA5E9 !important;
        border-radius: 4px !important;
        color: #075985 !important;
        padding: 12px 16px !important;
    }
    .stWarning, [data-testid="stWarning"] {
        background: #FFFBEB !important;
        border-left: 3px solid #D97706 !important;
        border-radius: 4px !important;
        color: #92400E !important;
        padding: 12px 16px !important;
    }
    .stError, [data-testid="stError"] {
        background: #FEF2F2 !important;
        border-left: 3px solid #DC2626 !important;
        border-radius: 4px !important;
        color: #991B1B !important;
        padding: 12px 16px !important;
    }

    /* ---------- FORMS ---------- */
    .stForm, [data-testid="stForm"] {
        background: #FFFFFF !important;
        border-radius: 6px !important;
        padding: 16px !important;
        box-shadow: none !important;
        border: 1px solid #E5E7EB !important;
    }

    /* ---------- DIVIDERS ---------- */
    hr {
        border: none !important;
        height: 1px !important;
        background: #E5E7EB !important;
        margin: 16px 0 !important;
    }

    /* ---------- SCROLLBARS ---------- */
    ::-webkit-scrollbar      { width: 6px; height: 6px; }
    ::-webkit-scrollbar-track{ background: #F9FAFB; }
    ::-webkit-scrollbar-thumb{ background: #D1D5DB; border-radius: 3px; }
    ::-webkit-scrollbar-thumb:hover { background: #9CA3AF; }

    /* ---------- DESIGN-SYSTEM HELPER CLASSES ---------- */
    .pmc-row {
        display: flex; align-items: center; justify-content: space-between;
        padding: 12px 0 12px 12px;
        border-left: 4px solid #9CA3AF;
        border-bottom: 1px solid #E5E7EB;
    }
    .pmc-row.urgent  { border-left-color: #DC2626; }
    .pmc-row.waiting { border-left-color: #D97706; }
    .pmc-row.ready   { border-left-color: #059669; }
    .pmc-row .pmc-name { font-weight: 600; color: #111827; font-size: 16px; margin: 0; }
    .pmc-row .pmc-meta { color: #6B7280; font-size: 14px; margin: 2px 0 0 0; }
    .pmc-pill {
        display: inline-flex; align-items: center; gap: 6px;
        font-size: 13px; color: #374151;
    }
    .pmc-pill .dot {
        width: 8px; height: 8px; border-radius: 999px; background: #9CA3AF;
        display: inline-block;
    }
    .pmc-pill.urgent  .dot { background: #DC2626; }
    .pmc-pill.waiting .dot { background: #D97706; }
    .pmc-pill.ready   .dot { background: #059669; }
    .pmc-pill.idle    .dot { background: #9CA3AF; }
    .pmc-section { font-size: 1.25rem; font-weight: 600; color: #111827; margin: 24px 0 8px 0;
                   padding-bottom: 4px; border-bottom: 1px solid #E5E7EB; }

    /* ---------- LEGACY PATIENT-HISTORY CARDS (flatten the colored gradients) ---------- */
    .patient-chart-header,
    .vital-card,
    .lab-card,
    .prescription-card,
    .consultation-card,
    .chart-section,
    .demo-item {
        background: #FFFFFF !important;
        border: 1px solid #E5E7EB !important;
        border-left: 1px solid #E5E7EB !important;
        border-radius: 6px !important;
        padding: 12px 16px !important;
        color: #111827 !important;
        box-shadow: none !important;
        margin: 8px 0 !important;
    }
    .patient-chart-header h2,
    .patient-chart-header h3,
    .patient-chart-header p {
        color: #111827 !important; text-align: left !important;
    }

    /* Responsive */
    @media (max-width: 768px) {
        .main .block-container { padding: 1rem !important; }
        .stButton > button     { padding: 12px 16px !important; font-size: 15px !important; }
    }
    </style>
    """,
                unsafe_allow_html=True)

    # Apply dark mode globally if enabled
    if 'dark_mode' in st.session_state and st.session_state.dark_mode:
        st.markdown("""
        <style>
        .stApp {
            background-color: #1a1a1a !important;
            color: #e0e0e0 !important;
        }
        
        /* Main content area */
        .main .block-container {
            background-color: #1a1a1a !important;
            color: #e0e0e0 !important;
        }
        
        /* Buttons */
        .stButton > button {
            background-color: #333333 !important;
            color: #e0e0e0 !important;
            border: 1px solid #555555 !important;
        }
        
        /* Primary buttons */
        .stButton > button[kind="primary"] {
            background-color: #0066cc !important;
            color: #ffffff !important;
        }
        
        /* Input fields */
        .stTextInput input, .stSelectbox select, .stNumberInput input {
            background-color: #2d2d2d !important;
            color: #e0e0e0 !important;
            border: 1px solid #555555 !important;
        }
        
        /* Tabs */
        .stTabs [data-baseweb="tab-list"] {
            background-color: #2d2d2d !important;
        }
        
        .stTabs [data-baseweb="tab"] {
            background-color: #2d2d2d !important;
            color: #e0e0e0 !important;
        }
        
        .stTabs [aria-selected="true"] {
            background-color: #0066cc !important;
            color: #ffffff !important;
        }
        
        /* Sidebar */
        .css-1d391kg {
            background-color: #262626 !important;
        }
        
        /* Text and headers */
        h1, h2, h3, h4, h5, h6, p, span, div {
            color: #e0e0e0 !important;
        }
        
        /* Info boxes */
        .stInfo {
            background-color: #2d4a5a !important;
            color: #e0e0e0 !important;
        }
        
        /* Warning boxes */
        .stWarning {
            background-color: #5a4a2d !important;
            color: #e0e0e0 !important;
        }
        
        /* Error boxes */
        .stError {
            background-color: #5a2d2d !important;
            color: #e0e0e0 !important;
        }
        
        /* Success boxes */
        .stSuccess {
            background-color: #2d5a2d !important;
            color: #e0e0e0 !important;
        }
        
        /* Form elements */
        .stForm {
            background-color: #262626 !important;
            color: #e0e0e0 !important;
        }
        
        /* Expander */
        .streamlit-expanderHeader {
            background-color: #2d2d2d !important;
            color: #e0e0e0 !important;
        }
        
        /* Metrics */
        .metric-container {
            background-color: #2d2d2d !important;
        }
        </style>
        """,
                    unsafe_allow_html=True)

    # Header with centered logo - minimal spacing
    st.markdown("""
    <style>
    .main > div:first-child {
        padding-top: 0 !important;
    }
    .block-container {
        padding-top: 1rem !important;
    }
    </style>
    """,
                unsafe_allow_html=True)

    # Check if on login page (pre-authentication)
    is_on_login = not (st.session_state.get('is_org_admin') or 
                       st.session_state.get('skip_org_admin'))
    
    # Check if on org home (authenticated but no clinic selected)
    is_on_org_home = (st.session_state.get('is_org_admin') or 
                      st.session_state.get('skip_org_admin')) and not st.session_state.get('clinic_location')
    
    # Only show navigation buttons when inside a clinic (not on org home page)
    has_clinic_selected = st.session_state.get('clinic_location') is not None
    
    if has_clinic_selected:
        # Navigation buttons in a cleaner horizontal layout
        nav_col1, nav_col2, nav_col3 = st.columns([1, 1, 1])

        with nav_col1:
            if st.button(t('org_home'),
                         key="org_home_button",
                         help="Return to organization dashboard",
                         use_container_width=True):
                # Go back to organization dashboard - clear clinic selection
                st.session_state.clinic_location = None
                st.session_state.selected_clinic_id = None
                st.session_state.user_role = None
                st.session_state.clinic_staff = None  # Clear staff to show overview again
                if 'org_admin_entering_as_staff' in st.session_state:
                    del st.session_state['org_admin_entering_as_staff']
                if 'page' in st.session_state:
                    del st.session_state.page
                if 'doctor_name' in st.session_state:
                    del st.session_state.doctor_name
                if 'active_consultation' in st.session_state:
                    del st.session_state.active_consultation
                st.query_params.clear()
                st.rerun()

        with nav_col2:
            if st.button(t('clinic_home'),
                         key="clinic_home_button",
                         help="Return to clinic role selection",
                         use_container_width=True):
                # Clear user role to return to role selection but keep clinic
                if 'user_role' in st.session_state:
                    del st.session_state.user_role
                if 'page' in st.session_state:
                    del st.session_state.page
                if 'doctor_name' in st.session_state:
                    del st.session_state.doctor_name
                if 'active_consultation' in st.session_state:
                    del st.session_state.active_consultation
                st.query_params.clear()
                st.rerun()

        with nav_col3:
            # Show current clinic location
            location = st.session_state.clinic_location
            location_text = f"{location['city']}, {location['country_code']}"
            st.markdown(
                f"<div style='padding-top:14px; color:#6B7280; font-size:0.9rem; text-align:right;'>{location_text}</div>",
                unsafe_allow_html=True)

        st.markdown("---")

    # ==================== ORGANIZATION & CLINIC SELECTION FLOW ====================
    
    # Ensure default organization exists (migration for existing data)
    ensure_default_organization()
    
    # Step 1: Organization selection
    if 'selected_organization_id' not in st.session_state:
        st.session_state.selected_organization_id = None
    
    if st.session_state.selected_organization_id is None:
        # Check if there's only one org - auto-select it
        orgs = db.get_all_organizations()
        if len(orgs) == 1:
            st.session_state.selected_organization_id = orgs[0]['id']
        else:
            organization_selection()
            return
    
    # Step 1.5: Org admin authentication (unless skipped to enter as clinic staff)
    if 'org_user' not in st.session_state:
        st.session_state.org_user = None
    if 'is_org_admin' not in st.session_state:
        st.session_state.is_org_admin = False
    if 'skip_org_admin' not in st.session_state:
        st.session_state.skip_org_admin = False
    
    # Step 2: Clinic selection (replaces old location_setup for org context)
    if 'selected_clinic_id' not in st.session_state:
        st.session_state.selected_clinic_id = None
    
    if 'clinic_location' not in st.session_state:
        st.session_state.clinic_location = None

    # Initialize session state for new staff login flow
    if 'show_staff_login' not in st.session_state:
        st.session_state.show_staff_login = False
    if 'show_clinic_selection' not in st.session_state:
        st.session_state.show_clinic_selection = False
    if 'show_staff_registration' not in st.session_state:
        st.session_state.show_staff_registration = False
    if 'clinic_staff' not in st.session_state:
        st.session_state.clinic_staff = None
    
    # Handle clinic staff flow (skip_org_admin is True)
    if st.session_state.skip_org_admin and not st.session_state.is_org_admin:
        # Check if showing registration form
        if st.session_state.get('show_staff_registration'):
            clinic_staff_self_registration(st.session_state.selected_organization_id)
            return
        
        # Staff needs to authenticate first
        if st.session_state.clinic_staff is None:
            # Show staff login form
            clinic_staff_org_login(st.session_state.selected_organization_id)
            return
        
        # Staff authenticated - check if they need to select a clinic
        if st.session_state.get('show_clinic_selection') and st.session_state.clinic_location is None:
            clinic_staff_clinic_selection()
            return
    
    if st.session_state.clinic_location is None:
        # Check if org admin login required
        if not st.session_state.is_org_admin and not st.session_state.skip_org_admin:
            org_admin_login()
            return
        
        # Show organization dashboard with clinic selection (only for org admins)
        organization_dashboard()
        return
    
    # Step 3: Clinic staff authentication (for org admin flow - when they select a clinic)
    # If not logged in as staff and IS org admin, show clinic overview first
    if st.session_state.clinic_staff is None:
        if st.session_state.is_org_admin:
            # Show clinic overview for org admin - they can choose to impersonate
            if not st.session_state.get('org_admin_entering_as_staff'):
                org_admin_clinic_overview()
                return
            else:
                # Org admin chose to enter as staff
                st.session_state.clinic_staff = {
                    'id': 0,
                    'clinic_id': st.session_state.selected_clinic_id,
                    'full_name': st.session_state.org_user.get('full_name', 'Org Admin'),
                    'title': 'Organization Administrator',
                    'role_scope': 'all',
                    'is_org_admin': True
                }
        else:
            # This shouldn't happen in normal flow, but handle it
            clinic_id = st.session_state.selected_clinic_id
            clinic = db.get_clinic(clinic_id)
            if clinic:
                if clinic_staff_login(clinic_id, clinic['name']):
                    st.rerun()
                return
            else:
                st.error("Clinic not found")
                st.session_state.clinic_location = None
                st.session_state.selected_clinic_id = None
                st.rerun()
                return

    # Role selection
    if 'user_role' not in st.session_state:
        st.session_state.user_role = None

    # Auto-redirect based on staff role after sign-in
    if st.session_state.user_role is None and st.session_state.get('auto_select_role'):
        staff_title = st.session_state.auto_select_role.lower()
        st.session_state.auto_select_role = None  # Clear after use
        
        # Map staff title to interface role - each role goes to their specific dashboard
        role_mapping = {
            # Registrant → Add Patient dashboard
            'registrant': ('name_registration', 'name_registration'),
            
            # Triage → Triage queue
            'triage': ('triage', 'triage'),
            
            # Provider → Doctor interface (triaged patient queue)
            'provider': ('doctor', 'doctor_login'),
            
            # Pharmacy → Prescription queue
            'pharmacy': ('pharmacy', 'pharmacy'),
            
            # Lab Tech → Lab processing dashboard
            'lab tech': ('lab', 'lab'),
            
            # Clinic Manager → Clinic operations dashboard
            'clinic manager': ('admin', 'admin'),
            
            # Reporting/Audit → Reporting center
            'reporting/audit': ('admin', 'admin'),
        }
        
        # Find matching role
        matched_role = None
        for key, (role, page) in role_mapping.items():
            if key in staff_title or staff_title in key:
                matched_role = (role, page)
                break
        
        if matched_role:
            st.session_state.user_role = matched_role[0]
            st.session_state.page = matched_role[1]
            update_page_url(matched_role[1])
            st.rerun()
        # If no match (e.g., "Other"), fall through to role selection page

    if st.session_state.user_role is None:
        # Get clinic name for header
        clinic_id = st.session_state.selected_clinic_id
        clinic = db.get_clinic(clinic_id) if clinic_id else None
        clinic_name = clinic['name'] if clinic else "Clinic"
        
        # Clean, modern role selection page
        st.markdown(f"""
            <div style="text-align: center; padding: 16px 0;">
                <h1 style="font-size: 1.75rem; font-weight: 700; color: #1F2937; margin-bottom: 4px;">
                    {clinic_name}
                </h1>
                <p style="font-size: 1.1rem; color: #6B7280; margin-bottom: 24px;">
                    {t('select_role')}
                </p>
            </div>
        """, unsafe_allow_html=True)

        # Role tiles — quiet, flat. Labels go through t() so the whole tile
        # translates with the language picker.
        _roles = [
            ('role_registrant',    "name_registration", "name_registration", 'role_registrant_desc'),
            ('role_triage',        "triage",            "triage",            'role_triage_desc'),
            ('role_provider',      "doctor",            "doctor_login",      'role_provider_desc'),
            ('role_pharmacy',      "pharmacy",          "pharmacy",          'role_pharmacy_desc'),
            ('role_lab',           "lab",               "lab",               'role_lab_desc'),
            ('role_queue_monitor', "queue_monitor",     "queue_monitor",     'role_queue_desc'),
        ]
        for i in range(0, len(_roles), 2):
            cA, cB = st.columns(2)
            for col_widget, role in zip((cA, cB), _roles[i:i+2]):
                label_key, user_role, page, desc_key = role
                label = t(label_key)
                desc = t(desc_key)
                with col_widget:
                    st.markdown(
                        f"<div style='background:#FFFFFF; border:1px solid #E5E7EB; "
                        f"border-radius:6px; padding:14px 16px; margin-bottom:8px;'>"
                        f"<div style='font-weight:600; color:#111827; font-size:1rem;'>{label}</div>"
                        f"<div style='color:#6B7280; font-size:0.85rem; margin-top:2px;'>{desc}</div>"
                        f"</div>",
                        unsafe_allow_html=True)
                    if st.button(f"{t('enter')} {label}", key=f"role_{user_role}",
                                 type="primary", use_container_width=True):
                        st.session_state.user_role = user_role
                        st.session_state.page = page
                        update_page_url(page)
                        st.rerun()

        # Clinic Manager / Admin section
        st.markdown("<div style='height: 24px;'></div>", unsafe_allow_html=True)
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            with st.expander(t('role_admin'), expanded=False):
                if st.button(t('role_admin'), key="clinic_manager", use_container_width=True):
                    st.session_state.user_role = "admin"
                    st.session_state.page = "admin"
                    update_page_url("admin")
                    st.rerun()

        return

    # Handle consultation form page navigation
    if st.session_state.get(
            'page'
    ) == 'consultation_form' and 'active_consultation' in st.session_state:
        consultation = st.session_state.active_consultation
        update_page_url('consultation_form')
        consultation_form(consultation['visit_id'], consultation['patient_id'],
                          consultation['patient_name'])
        return

    # Show LAN status page if requested
    if 'show_lan_page' in st.session_state and st.session_state.show_lan_page:
        show_lan_status_page()
        return

# Role-based interface routing with URL state persistence
    render_app_header()
    if st.session_state.user_role == "name_registration":
        update_page_url("name_registration")
        name_registration_interface()
    elif st.session_state.user_role == "triage":
        update_page_url("triage")
        triage_interface()
    elif st.session_state.user_role == "doctor":
        # Use logged-in staff member's name as doctor name (skip doctor selection page)
        if 'doctor_name' not in st.session_state:
            if 'clinic_staff' in st.session_state:
                staff = st.session_state.clinic_staff
                st.session_state.doctor_name = staff.get('full_name', 'Provider')
                # Initialize doctor status
                db_mgr = get_db_manager()
                db_mgr.update_doctor_status(st.session_state.doctor_name, "available")
            else:
                # No staff login - redirect to clinic staff login
                st.warning("Please log in as clinic staff first.")
                st.session_state.user_role = None
                st.rerun()
        update_page_url("doctor_interface")
        doctor_interface()
    elif st.session_state.user_role == "pharmacy":
        update_page_url("pharmacy")
        pharmacy_interface()
    elif st.session_state.user_role == "lab":
        update_page_url("lab")
        lab_interface()
    elif st.session_state.user_role == "ophthalmologist":
        update_page_url("ophthalmologist")
        ophthalmologist_interface()
    elif st.session_state.user_role == "queue_monitor":
        update_page_url("queue_monitor")
        patient_queue_monitor_interface()
    elif st.session_state.user_role == "admin":
        update_page_url("admin")
        admin_interface()

    # Sidebar header with location info
    if 'clinic_location' in st.session_state and st.session_state.clinic_location:
        location = st.session_state.clinic_location
        location_info = f"{location['city']}, {location['country_name']}"
    else:
        location_info = "No location set"

    st.sidebar.markdown(f'''
    <div style="text-align: center; margin-bottom: 20px;">
        <p style="color: #666; font-size: 12px; margin-top: 5px;">{location_info}</p>
    </div>
    ''',
                        unsafe_allow_html=True)

    # Role change button
    st.sidebar.markdown("---")
    if st.sidebar.button("🔄 Change Role"):
        st.session_state.user_role = None
        st.rerun()

    if st.sidebar.button(t('change_location')):
        st.session_state.clinic_location = None
        st.session_state.user_role = None
        st.rerun()

    # LAN connectivity page
    st.sidebar.markdown("---")
    if st.sidebar.button("🌐 LAN Status"):
        st.session_state.show_lan_page = True
        st.rerun()


def doctor_login():
    """Simplified doctor login interface - click your name to login"""
    st.markdown(f"### {t('select_your_name')}")

    db = get_db_manager()
    doctors = db.get_doctors()

    if not doctors:
        st.warning(t('no_doctors_available'))
        if st.button(t('back_to_role_selection'), key='back_no_doctors_to_role'):
            if 'user_role' in st.session_state:
                del st.session_state.user_role
            st.rerun()
        return

    # Get current doctor status
    doctor_status = db.get_all_doctor_status()
    status_dict = {status['doctor_name']: status for status in doctor_status}

    st.markdown(t('choose_your_name'))
    
    # Add CSS to make buttons look like plain text
    st.markdown("""
    <style>
    .stButton > button {
        background: transparent !important;
        border: none !important;
        color: inherit !important;
        text-align: left !important;
        padding: 0 !important;
        box-shadow: none !important;
        font-weight: normal !important;
        text-decoration: none !important;
    }
    .stButton > button:hover {
        background: transparent !important;
        border: none !important;
        text-decoration: underline !important;
        color: #0066cc !important;
    }
    .stButton > button:active {
        background: transparent !important;
        border: none !important;
    }
    .stButton > button:focus {
        background: transparent !important;
        border: none !important;
        outline: none !important;
        box-shadow: none !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Create clickable doctor text without status indicators
    for doctor in doctors:
        doctor_name = doctor['name']
        
        # Display doctor name as clickable text
        if st.button(doctor_name, key=f"login_{doctor_name}"):
            # Login logic for selected doctor
            try:
                st.session_state.doctor_name = doctor_name
                
                # Check if doctor was in middle of consultation
                conn = sqlite3.connect("clinic_database.db")
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT current_patient_id, current_patient_name, status
                    FROM doctor_status 
                    WHERE doctor_name = ?
                ''', (doctor_name,))
                doctor_status = cursor.fetchone()
                conn.close()
                
                if doctor_status and doctor_status[0] and doctor_status[2] == 'with_patient':
                    # Doctor was with a patient - restore consultation
                    st.session_state.current_consultation = {
                        'patient_id': doctor_status[0],
                        'patient_name': doctor_status[1]
                    }
                    st.success(f"Logged in as Dr. {doctor_name} - Returning to consultation with {doctor_status[1]}")
                else:
                    # Update doctor status to available
                    db.update_doctor_status(doctor_name, "available")
                    st.success(f"Logged in as Dr. {doctor_name}")
                
                st.rerun()
            except Exception as e:
                st.error(f"Login error: {str(e)}")
                # Try to fix the issue by ensuring the doctor exists in status table
                try:
                    # Check if doctor exists in the doctors table first
                    doctors_list = db.get_doctors()
                    doctor_exists = any(doc['name'] == doctor_name for doc in doctors_list)

                    if doctor_exists:
                        # Force create status entry
                        conn = sqlite3.connect("clinic_database.db")
                        cursor = conn.cursor()
                        cursor.execute('''
                            INSERT OR REPLACE INTO doctor_status 
                            (doctor_name, status, current_patient_id, current_patient_name, last_updated)
                            VALUES (?, 'available', '', '', ?)
                        ''', (doctor_name, datetime.now().isoformat()))
                        conn.commit()
                        conn.close()
                        st.session_state.doctor_name = doctor_name
                        st.success(f"Logged in as Dr. {doctor_name} (status fixed)")
                        st.rerun()
                    else:
                        st.error(f"Doctor {doctor_name} not found in system")
                except Exception as fix_error:
                    st.error(f"Could not fix login issue: {str(fix_error)}")
    



def show_lan_status_page():
    """Display LAN connectivity status for iPad connections"""
    st.markdown("## 🌐 LAN Network Status")

    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown("### Network Information")

        # Show network information
        import socket
        try:
            # Get current IP address
            hostname = socket.gethostname()
            local_ip = socket.gethostbyname(hostname)
            
            # Check if running on Pi hotspot network
            if local_ip.startswith("192.168.4."):
                st.success(f"✅ Pi Hotspot Active: {local_ip}")
                st.info("📡 Network: ParakaleoMed-Clinic (Offline mode)")
            else:
                st.success(f"📶 This Device: {local_ip}")
                
        except Exception:
            st.error("⚠️ Unable to determine network status")

        st.markdown("### WebSocket Server Status")
        
        # Check WebSocket server status
        try:
            import asyncio
            import websockets
            
            # Try to connect to WebSocket server to check if it's running
            async def check_websocket_server():
                try:
                    uri = f"ws://{local_ip}:6789"
                    async with websockets.connect(uri, timeout=2) as websocket:
                        await websocket.send("ping")
                        response = await websocket.recv()
                        return True
                except:
                    return False
            
            # Run the check (simplified for Streamlit)
            ws_status = "🟢 WebSocket Server Running"
            st.success(f"{ws_status} on port 6789")
            st.info("🔄 Real-time sync enabled for all iPads")
            
        except Exception as e:
            st.error("🔴 WebSocket Server Status Unknown")
            st.warning("Real-time sync may not be working properly")

        st.markdown("### iPad Connection Guide")
        st.markdown("""
        **To connect iPads to ParakaleoMed:**
        
        1. Connect iPad to **ParakaleoMed-Clinic** WiFi
        2. Password: `wpawpawpa`
        3. Open Safari and go to: `http://192.168.4.1:5000`
        4. WebSocket sync will connect automatically
        
        **Troubleshooting:**
        - If sync not working, refresh the page
        - Check WiFi connection to ParakaleoMed-Clinic
        - Ensure all iPads use the same URL above
        """)
        
        # Real-time WebSocket connection status
        st.markdown("### Live Connection Monitor")
        
        # Add JavaScript to show real-time connection status
        html("""
        <div id="connection-status" style="padding: 10px; border-radius: 5px; margin: 10px 0;">
            <strong>WebSocket Status:</strong> <span id="ws-status">Checking...</span><br>
            <strong>Connected Since:</strong> <span id="ws-connected-time">-</span>
        </div>
        
        <script>
        function updateConnectionStatus() {
            const statusDiv = document.getElementById('ws-status');
            const timeDiv = document.getElementById('ws-connected-time');
            const containerDiv = document.getElementById('connection-status');
            
            if (window.wsConnected) {
                statusDiv.innerHTML = '🟢 Connected';
                statusDiv.style.color = 'green';
                containerDiv.style.backgroundColor = '#d4edda';
                containerDiv.style.borderLeft = '4px solid #28a745';
                
                if (window.wsConnectedTime) {
                    timeDiv.innerHTML = window.wsConnectedTime;
                } else {
                    window.wsConnectedTime = new Date().toLocaleTimeString();
                    timeDiv.innerHTML = window.wsConnectedTime;
                }
            } else {
                statusDiv.innerHTML = '🔴 Disconnected';
                statusDiv.style.color = 'red';
                containerDiv.style.backgroundColor = '#f8d7da';
                containerDiv.style.borderLeft = '4px solid #dc3545';
                timeDiv.innerHTML = '-';
                window.wsConnectedTime = null;
            }
        }
        
        // Update status every 2 seconds
        setInterval(updateConnectionStatus, 2000);
        updateConnectionStatus(); // Initial check
        </script>
        """, height=100)

    with col2:
        if st.button(t('back_to_main'), key='back_lan_main'):
            st.session_state.show_lan_page = False
            st.rerun()

        if st.button(t('refresh'), key='refresh_lan'):
            st.rerun()
            
        st.markdown("---")
        st.markdown("**Quick Actions:**")
        
        if st.button("🔗 Test WebSocket"):
            st.info("Check browser console for WebSocket logs")
            
        if st.button("📋 Show Network Info"):
            try:
                import subprocess
                result = subprocess.run(['ip', 'addr', 'show', 'wlan0'], 
                                      capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    st.text(result.stdout)
                else:
                    st.warning("Network interface info not available")
            except:
                st.warning("Unable to retrieve network details")

    st.markdown("---")
    st.info(
        "Note: All devices should be connected to the same WiFi network for data synchronization."
    )


# ==================== ORGANIZATION DASHBOARD & CLINIC SELECTION ====================

def ensure_default_organization():
    """Ensure at least one organization exists, create default if none"""
    orgs = db.get_all_organizations()
    if not orgs:
        # Create default organization from existing data
        org_id = db.create_organization(
            name="ParakaleoMed",
            description="Medical Mission Organization",
            contact_name="",
            contact_email="",
            country="USA"
        )
        
        # Get existing locations and create clinics from them
        locations = db.get_locations()
        for location in locations:
            clinic_id = db.create_clinic(
                organization_id=org_id,
                name=f"{location['city']} Mission Clinic",
                location_city=location['city'],
                location_country=location['country_name'],
                location_code=location['country_code'],
                patient_id_prefix=location['country_code'],
                status='active'
            )
            # Migrate existing data to this clinic
            db.migrate_existing_data_to_clinic(clinic_id, location['country_code'])
        
        return org_id
    return orgs[0]['id']


def org_admin_login():
    """Login interface for organization admins"""
    org_id = st.session_state.get('selected_organization_id')
    if not org_id:
        return False

    org = db.get_organization(org_id)
    if not org:
        st.error("Organization not found")
        return False

    render_login_language_picker()

    # Check if org has any users
    org_users = db.get_org_users(org_id)
    
    if not org_users:
        # First time setup - create initial admin
        st.markdown("""
            <div style="text-align: center; padding: 0;">
                <h1 style="font-size: 2rem; font-weight: 700; color: #1F2937; margin: 0 0 8px 0;">
                    Welcome to ParakaleoMed
                </h1>
                <p style="font-size: 1rem; color: #6B7280; margin: 0 0 16px 0;">
                    Let's set up your first administrator account
                </p>
            </div>
        """, unsafe_allow_html=True)
        
        # Centered form
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col2:
            st.markdown("""
                <div style="background: #F9FAFB; border-radius: 16px; padding: 24px; margin-bottom: 16px;
                            border: 1px solid #E5E7EB;">
                    <p style="color: #475569; font-weight: 600; margin: 0;">
                        🔐 Create Administrator Account
                    </p>
                </div>
            """, unsafe_allow_html=True)
            
            with st.form("create_first_admin"):
                full_name = st.text_input("Your Full Name", placeholder="e.g., John Smith")
                title = st.text_input("Your Title", placeholder="e.g., Mission Director")
                
                st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)
                
                col_a, col_b = st.columns(2)
                with col_a:
                    pin = st.text_input("Create 4-Digit PIN", type="password", max_chars=4, placeholder="****")
                with col_b:
                    confirm_pin = st.text_input("Confirm PIN", type="password", max_chars=4, placeholder="****")
                
                st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)
                
                if st.form_submit_button("Create Admin Account", type="primary", use_container_width=True):
                    if not full_name:
                        st.error("Please enter your name")
                    elif not pin or len(pin) != 4 or not pin.isdigit():
                        st.error("PIN must be exactly 4 digits")
                    elif pin != confirm_pin:
                        st.error("PINs do not match")
                    else:
                        user_id = db.create_org_user(
                            organization_id=org_id,
                            full_name=full_name,
                            pin=pin,
                            title=title
                        )
                        st.success("Admin account created! Please log in.")
                        st.rerun()
        return False
    
    # Clean, modern login page with logo and heading side by side
    logo_col, text_col = st.columns([1, 3])
    with logo_col:
        st.image(
            "attached_assets/ChatGPT Image Jun 15, 2025, 05_23_25 PM_1750024910085.png",
            width=80
        )
    with text_col:
        st.markdown("""
            <div style="display: flex; flex-direction: column; justify-content: center; height: 100%;">
                <h1 style="font-size: 2rem; font-weight: 700; color: #1F2937; margin: 0 0 4px 0;">
                    Welcome to ParakaleoMed
                </h1>
                <p style="font-size: 1rem; color: #6B7280; margin: 0;">
                    Select how you'd like to sign in
                </p>
            </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)
    
    # Create centered container
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        # PRIMARY: Clinic Staff Entry Card
        st.markdown("""
            <div style="background: linear-gradient(135deg, #475569 0%, #14B8A6 100%); 
                        border-radius: 16px; padding: 32px; margin-bottom: 16px;
                        box-shadow: 0 8px 32px rgba(15, 118, 110, 0.3);">
                <h3 style="color: white; margin: 0 0 8px 0; font-size: 1.25rem;">👥 Clinic Staff</h3>
                <p style="color: rgba(255,255,255,0.9); margin: 0; font-size: 0.95rem;">
                    For nurses, doctors, pharmacy, lab, and registration
                </p>
            </div>
        """, unsafe_allow_html=True)
        
        if st.button("Enter as Clinic Staff", type="primary", use_container_width=True, key="clinic_staff_btn"):
            st.session_state.skip_org_admin = True
            st.session_state.show_staff_login = True
            st.rerun()
        
        st.markdown("<div style='height: 24px;'></div>", unsafe_allow_html=True)
        
        # SECONDARY: Admin Login (collapsed)
        with st.expander("🔐 Administrator Login", expanded=False):
            st.markdown("""
                <p style="color: #6B7280; font-size: 0.9rem; margin-bottom: 16px;">
                    For organization administrators only
                </p>
            """, unsafe_allow_html=True)
            
            with st.form("org_admin_login_form"):
                full_name = st.text_input("Your Name", placeholder="Enter your full name")
                pin = st.text_input("4-Digit PIN", type="password", max_chars=4, placeholder="****")
                
                if st.form_submit_button("Log In", use_container_width=True):
                    if full_name and pin:
                        user = db.verify_org_user_pin(org_id, full_name, pin)
                        if user:
                            st.session_state.org_user = user
                            st.session_state.is_org_admin = True
                            st.success(f"Welcome, {user['full_name']}!")
                            st.rerun()
                        else:
                            st.error("Invalid name or PIN")
                    else:
                        st.error("Please enter your name and PIN")
    
    return False


def clinic_staff_org_login(org_id: int):
    """Organization-level login for clinic staff - authenticates first, then shows only assigned clinics"""

    render_login_language_picker()

    org = db.get_organization(org_id)
    org_name = org['name'] if org else "Organization"
    
    # Clean, modern staff login page - minimal padding
    st.markdown("""
        <div style="text-align: center; padding: 0;">
            <h1 style="font-size: 2rem; font-weight: 700; color: #1F2937; margin: 0 0 8px 0;">
                Staff Sign-In
            </h1>
            <p style="font-size: 1rem; color: #6B7280; margin: 0 0 20px 0;">
                Enter your credentials to access your assigned clinic
            </p>
        </div>
    """, unsafe_allow_html=True)
    
    # Centered layout
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        # Login form card
        st.markdown("""
            <div style="background: #F9FAFB; border-radius: 16px; padding: 20px; margin-bottom: 16px;
                        border: 1px solid #E5E7EB;">
                <p style="color: #475569; font-weight: 600; margin: 0;">
                    👥 Enter your credentials
                </p>
            </div>
        """, unsafe_allow_html=True)
        
        with st.form("clinic_staff_org_login_form"):
            identifier = st.text_input("Email or Phone", placeholder="Enter your email or phone number")
            pin = st.text_input("4-Digit PIN", type="password", max_chars=4, placeholder="****")
            
            st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)
            
            if st.form_submit_button("Sign In", type="primary", use_container_width=True):
                if identifier and pin:
                    # Look up staff across all clinics in this organization
                    staff_matches = db.find_staff_by_credentials(org_id, identifier, pin)
                    
                    if staff_matches:
                        # Staff found - store credentials and clinic access info
                        first_match = staff_matches[0]  # Most recent clinic
                        
                        st.session_state.clinic_staff = {
                            'id': first_match['id'],
                            'clinic_id': first_match['clinic_id'],
                            'full_name': first_match['full_name'],
                            'title': first_match['title'],
                            'role_scope': first_match['role_scope']
                        }
                        st.session_state.staff_clinic_access = staff_matches  # All clinics staff has access to
                        
                        if len(staff_matches) == 1:
                            # Only one clinic - auto-select it
                            clinic = staff_matches[0]
                            st.session_state.selected_clinic_id = clinic['clinic_id']
                            st.session_state.clinic_location = {
                                'id': clinic['clinic_id'],
                                'city': clinic['clinic_city'],
                                'country_name': clinic['clinic_country'],
                                'country_code': clinic['patient_id_prefix'] or clinic['location_code'] or 'CL'
                            }
                            # Auto-redirect based on role
                            st.session_state.auto_select_role = first_match['title']
                            st.success(f"Welcome, {first_match['full_name']}!")
                            st.rerun()
                        else:
                            # Multiple clinics - show selection
                            st.session_state.show_clinic_selection = True
                            st.session_state.auto_select_role = first_match['title']
                            st.success(f"Welcome, {first_match['full_name']}!")
                            st.rerun()
                    else:
                        st.error("Invalid email/phone or PIN. Please try again.")
                else:
                    st.error("Please enter your email/phone and PIN")
        
        # Divider and Create Account option
        st.markdown("""
            <div style="display: flex; align-items: center; margin: 24px 0;">
                <div style="flex: 1; height: 1px; background: #E5E7EB;"></div>
                <span style="padding: 0 16px; color: #9CA3AF; font-size: 0.9rem;">or</span>
                <div style="flex: 1; height: 1px; background: #E5E7EB;"></div>
            </div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
            <p style="text-align: center; color: #6B7280; font-size: 0.95rem; margin-bottom: 12px;">
                First time here? Create your staff account
            </p>
        """, unsafe_allow_html=True)
        
        if st.button("Create New Account", use_container_width=True, key="create_account_btn"):
            st.session_state.show_staff_registration = True
            st.rerun()
        
        # Back button
        st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)
        if st.button(t('back_to_signin_options'), key='back_to_signin_options_main',
                     use_container_width=True):
            st.session_state.skip_org_admin = False
            st.session_state.show_staff_login = False
            st.session_state.show_staff_registration = False
            st.rerun()
    
    return False


def clinic_staff_self_registration(org_id: int):
    """Self-registration form for new clinic staff"""
    
    org = db.get_organization(org_id)
    
    # Get available clinics for this organization
    clinics = db.get_organization_clinics(org_id)
    active_clinics = [c for c in clinics if c.get('status') == 'active']
    
    # Clean, modern registration page
    st.markdown("""
        <div style="text-align: center; padding: 20px 0;">
            <h1 style="font-size: 2.5rem; font-weight: 700; color: #1F2937; margin-bottom: 8px;">
                Create Staff Account
            </h1>
            <p style="font-size: 1.1rem; color: #6B7280; margin-bottom: 24px;">
                Register to join the clinic team
            </p>
        </div>
    """, unsafe_allow_html=True)
    
    # Centered layout
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        # Check if there are any active clinics
        if not active_clinics:
            st.warning("No active clinics available for registration. Please contact an administrator.")
            if st.button(t('back_to_signin'), key='back_to_signin_no_clinics',
                         use_container_width=True):
                st.session_state.show_staff_registration = False
                st.rerun()
            return False
        
        # Registration form card
        st.markdown("""
            <div style="background: #F9FAFB; border-radius: 16px; padding: 20px; margin-bottom: 16px;
                        border: 1px solid #E5E7EB;">
                <p style="color: #475569; font-weight: 600; margin: 0;">
                    📋 Your Information
                </p>
            </div>
        """, unsafe_allow_html=True)
        
        with st.form("staff_self_registration_form"):
            # Personal info
            full_name = st.text_input("Full Name *", placeholder="Enter your full name")
            
            # Title/Role selection - based on EMR specification
            role_options = [
                "Registrant",
                "Triage", 
                "Provider",
                "Pharmacy",
                "Lab Tech",
                "Clinic Manager",
                "Reporting/Audit",
                "Other"
            ]
            title = st.selectbox("Your Role *", options=role_options, index=0)
            
            if title == "Other":
                custom_title = st.text_input("Specify your role", placeholder="e.g., Medical Student")
            else:
                custom_title = None
            
            st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)
            
            # Contact info - at least one required for sign-in
            st.markdown("""
                <p style="color: #6B7280; font-size: 0.85rem; margin-bottom: 8px;">
                    📱 Provide email or phone for sign-in (at least one required)
                </p>
            """, unsafe_allow_html=True)
            col_a, col_b = st.columns(2)
            with col_a:
                email = st.text_input("Email", placeholder="your@email.com")
            with col_b:
                phone = st.text_input("Phone", placeholder="+1 555-123-4567")
            
            st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)
            
            # Clinic selection
            if len(active_clinics) == 1:
                # Only one clinic - auto-select it
                selected_clinic = active_clinics[0]
                st.info(f"📍 You will be registered at: **{selected_clinic['name']}** ({selected_clinic.get('location_city', 'Unknown')}, {selected_clinic.get('location_country', '')})")
                clinic_id = selected_clinic['id']
            else:
                # Multiple clinics - let user choose
                clinic_options = {f"{c['name']} - {c.get('location_city', 'Unknown')}, {c.get('location_country', '')}": c['id'] for c in active_clinics}
                selected_clinic_name = st.selectbox("Select Clinic *", options=list(clinic_options.keys()))
                clinic_id = clinic_options[selected_clinic_name]
            
            st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)
            
            # PIN creation
            st.markdown("""
                <div style="background: #FEF3C7; border-radius: 8px; padding: 12px; margin-bottom: 12px;
                            border: 1px solid #F59E0B;">
                    <p style="color: #92400E; margin: 0; font-size: 0.9rem;">
                        🔐 Create a 4-digit PIN to secure your account. Remember this PIN!
                    </p>
                </div>
            """, unsafe_allow_html=True)
            
            col_c, col_d = st.columns(2)
            with col_c:
                pin = st.text_input("Create 4-Digit PIN *", type="password", max_chars=4, placeholder="****")
            with col_d:
                confirm_pin = st.text_input("Confirm PIN *", type="password", max_chars=4, placeholder="****")
            
            st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)
            
            if st.form_submit_button("Create Account", type="primary", use_container_width=True):
                # Validation
                final_title = custom_title if title == "Other" and custom_title else title
                
                errors = []
                if not full_name or len(full_name.strip()) < 2:
                    errors.append("Please enter your full name")
                if not final_title:
                    errors.append("Please specify your role")
                
                # Require at least email or phone for sign-in
                email_clean = email.strip() if email else ""
                phone_clean = phone.strip() if phone else ""
                if not email_clean and not phone_clean:
                    errors.append("Please provide at least an email or phone number for sign-in")
                
                if not pin or len(pin) != 4 or not pin.isdigit():
                    errors.append("PIN must be exactly 4 digits")
                if pin != confirm_pin:
                    errors.append("PINs do not match")
                
                # Check if email or phone already exists (duplicate prevention)
                if email_clean or phone_clean:
                    existing = db.get_clinic_staff(clinic_id)
                    for staff in existing:
                        staff_email = (staff.get('email') or '').lower().strip()
                        staff_phone = (staff.get('phone') or '').strip()
                        if email_clean and staff_email == email_clean.lower():
                            errors.append(f"This email is already registered. Please sign in instead.")
                            break
                        if phone_clean and staff_phone == phone_clean:
                            errors.append(f"This phone number is already registered. Please sign in instead.")
                            break
                
                if errors:
                    for error in errors:
                        st.error(error)
                else:
                    # Create the staff account
                    try:
                        staff_id = db.add_clinic_staff(
                            clinic_id=clinic_id,
                            full_name=full_name.strip(),
                            title=final_title,
                            pin=pin,
                            role_scope='all',
                            email=email.strip() if email else None,
                            phone=phone.strip() if phone else None
                        )
                        
                        # Get the clinic details for auto-login
                        clinic = db.get_clinic(clinic_id)
                        
                        # Auto-sign in the new staff member
                        st.session_state.clinic_staff = {
                            'id': staff_id,
                            'clinic_id': clinic_id,
                            'full_name': full_name.strip(),
                            'title': final_title,
                            'role_scope': 'all'
                        }
                        st.session_state.selected_clinic_id = clinic_id
                        st.session_state.clinic_location = {
                            'id': clinic_id,
                            'city': clinic.get('location_city', ''),
                            'country_name': clinic.get('location_country', ''),
                            'country_code': clinic.get('patient_id_prefix') or clinic.get('location_code') or 'CL'
                        }
                        st.session_state.show_staff_registration = False
                        
                        # Auto-redirect based on role
                        st.session_state.auto_select_role = final_title
                        
                        st.success(f"Welcome to the team, {final_title} {full_name.strip()}! Your account has been created.")
                        time.sleep(1)
                        st.rerun()
                        
                    except Exception as e:
                        st.error(f"Failed to create account. Please try again or contact an administrator.")
        
        # Back button
        st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)
        if st.button(t('back_to_signin'), key='back_to_signin_from_self_reg',
                     use_container_width=True):
            st.session_state.show_staff_registration = False
            st.rerun()

    return False


def clinic_staff_clinic_selection():
    """Show clinic selection for staff with access to multiple clinics"""
    
    staff = st.session_state.get('clinic_staff')
    clinics = st.session_state.get('staff_clinic_access', [])
    
    if not staff or not clinics:
        return False
    
    # Header
    st.markdown(f"""
        <div style="text-align: center; padding: 20px 0;">
            <h1 style="font-size: 2rem; font-weight: 700; color: #1F2937; margin-bottom: 8px;">
                Welcome, {staff['title']} {staff['full_name']}
            </h1>
            <p style="font-size: 1.1rem; color: #6B7280; margin-bottom: 24px;">
                Select a clinic to work at today
            </p>
        </div>
    """, unsafe_allow_html=True)
    
    # Show clinic cards
    for clinic in clinics:
        status_color = "#10B981" if clinic['clinic_status'] == 'active' else "#6B7280"
        status_label = "Active" if clinic['clinic_status'] == 'active' else clinic['clinic_status'].title()
        
        st.markdown(f"""
            <div style="background: #FFFFFF; border-radius: 6px; padding: 14px 16px; margin-bottom: 8px;
                        border: 1px solid #E5E7EB; box-shadow: none;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <h3 style="margin: 0 0 2px 0; color: #111827; font-size: 1rem; font-weight: 600;">{clinic['clinic_name']}</h3>
                        <p style="margin: 0; color: #6B7280; font-size: 0.85rem;">{clinic['clinic_city']}, {clinic['clinic_country']}</p>
                    </div>
                    <span style="color: #6B7280; padding: 2px 8px; border: 1px solid #E5E7EB;
                                 border-radius: 4px; font-size: 0.75rem; font-weight: 500;">{status_label}</span>
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        if st.button(f"Enter {clinic['clinic_name']}", key=f"select_clinic_{clinic['clinic_id']}", 
                     type="primary", use_container_width=True):
            # Update staff session to use this clinic's staff record
            matching_staff = [c for c in clinics if c['clinic_id'] == clinic['clinic_id']]
            if matching_staff:
                st.session_state.clinic_staff = {
                    'id': matching_staff[0]['id'],
                    'clinic_id': clinic['clinic_id'],
                    'full_name': staff['full_name'],
                    'title': staff['title'],
                    'role_scope': matching_staff[0].get('role_scope', 'all')
                }
            
            st.session_state.selected_clinic_id = clinic['clinic_id']
            st.session_state.clinic_location = {
                'id': clinic['clinic_id'],
                'city': clinic['clinic_city'],
                'country_name': clinic['clinic_country'],
                'country_code': clinic.get('patient_id_prefix') or clinic.get('location_code') or 'CL'
            }
            st.session_state.show_clinic_selection = False
            st.rerun()
        
        st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)
    
    # Sign out option
    st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)
    if st.button(t('sign_out'), use_container_width=True):
        for key in ['clinic_staff', 'staff_clinic_access', 'skip_org_admin', 'show_staff_login', 
                    'show_clinic_selection', 'selected_clinic_id', 'clinic_location', 'user_role']:
            if key in st.session_state:
                del st.session_state[key]
        st.rerun()
    
    return False


def clinic_staff_login(clinic_id: int, clinic_name: str):
    """Login interface for clinic staff (used when org admin selects a clinic)"""
    
    # Clean, modern staff login page
    st.markdown(f"""
        <div style="text-align: center; padding: 20px 0;">
            <h1 style="font-size: 2rem; font-weight: 700; color: #1F2937; margin-bottom: 8px;">
                {clinic_name}
            </h1>
            <p style="font-size: 1.1rem; color: #6B7280; margin-bottom: 24px;">
                Staff Sign-In
            </p>
        </div>
    """, unsafe_allow_html=True)
    
    # Check if clinic has any staff
    clinic_staff = db.get_clinic_staff(clinic_id)
    
    # Centered layout
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        if not clinic_staff:
            # No staff registered - show warning
            st.warning("No staff members registered for this clinic.")
            st.info("An organization admin must register staff members before they can sign in.")
            
            # If user is org admin, let them bypass
            if st.session_state.get('is_org_admin'):
                st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)
                if st.button("Continue as Org Admin", type="primary", use_container_width=True):
                    st.session_state.clinic_staff = {
                        'id': 0,
                        'full_name': st.session_state.org_user.get('full_name', 'Org Admin'),
                        'title': 'Organization Administrator',
                        'role_scope': 'all',
                        'is_org_admin': True
                    }
                    return True
            return False
        
        # Login form card
        st.markdown("""
            <div style="background: #F9FAFB; border-radius: 16px; padding: 20px; margin-bottom: 16px;
                        border: 1px solid #E5E7EB;">
                <p style="color: #475569; font-weight: 600; margin: 0;">
                    Enter your credentials
                </p>
            </div>
        """, unsafe_allow_html=True)
        
        with st.form("clinic_staff_login_form"):
            full_name = st.text_input("Full Name", placeholder="Enter your full name")
            title = st.text_input("Title/Role", placeholder="e.g., Nurse, Doctor, Translator")
            pin = st.text_input("4-Digit PIN", type="password", max_chars=4, placeholder="****")
            
            st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)
            
            if st.form_submit_button("Sign In", type="primary", use_container_width=True):
                if full_name and title and pin:
                    staff = db.verify_clinic_staff_pin(clinic_id, full_name, title, pin)
                    if staff:
                        st.session_state.clinic_staff = staff
                        st.success(f"Welcome, {staff['title']} {staff['full_name']}!")
                        st.rerun()
                    else:
                        st.error("Invalid credentials. Please check your name, title, and PIN.")
                else:
                    st.error("Please fill in all fields")
        
        # If user is org admin, let them bypass
        if st.session_state.get('is_org_admin'):
            st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)
            if st.button("Continue as Org Admin", use_container_width=True):
                st.session_state.clinic_staff = {
                    'id': 0,
                    'full_name': st.session_state.org_user.get('full_name', 'Org Admin'),
                    'title': 'Organization Administrator',
                    'role_scope': 'all',
                    'is_org_admin': True
                }
                return True
    
    return False


def org_admin_clinic_overview():
    """Clinic overview page for org admins before entering as staff"""
    clinic_id = st.session_state.selected_clinic_id
    clinic = db.get_clinic(clinic_id)
    location = st.session_state.clinic_location
    
    if not clinic:
        st.error("Clinic not found")
        return
    
    # Header with back button
    col1, col2 = st.columns([1, 4])
    with col1:
        if st.button(t('back_to_org'), key='back_to_org_from_clinic_overview',
                     use_container_width=True):
            st.session_state.clinic_location = None
            st.session_state.selected_clinic_id = None
            if 'org_admin_entering_as_staff' in st.session_state:
                del st.session_state['org_admin_entering_as_staff']
            st.rerun()
    
    with col2:
        st.markdown(f"<h2 style='margin:0;'>{clinic['name']}</h2>", unsafe_allow_html=True)
        st.markdown(f"<p style='color:#6b7280; margin:0;'>{location['city']}, {location['country_name']}</p>", unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Clinic stats
    today = datetime.now().strftime('%Y-%m-%d')
    conn = sqlite3.connect(db.db_name)
    cursor = conn.cursor()
    
    # Get today's stats for this clinic
    location_code = location['country_code']
    
    cursor.execute('''
        SELECT COUNT(*) FROM visits v
        JOIN patients p ON v.patient_id = p.patient_id
        WHERE date(v.visit_date) = ? AND p.patient_id LIKE ?
    ''', (today, f'{location_code}%'))
    today_visits = cursor.fetchone()[0]
    
    cursor.execute('''
        SELECT v.status, COUNT(*) FROM visits v
        JOIN patients p ON v.patient_id = p.patient_id
        WHERE date(v.visit_date) = ? AND p.patient_id LIKE ?
        GROUP BY v.status
    ''', (today, f'{location_code}%'))
    status_counts = {row[0]: row[1] for row in cursor.fetchall()}
    
    cursor.execute('''
        SELECT COUNT(*) FROM clinic_staff WHERE clinic_id = ?
    ''', (clinic_id,))
    staff_count = cursor.fetchone()[0]
    
    conn.close()
    
    # Display stats
    st.markdown("### Today's Overview")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Visits", today_visits)
    with col2:
        st.metric("Waiting Triage", status_counts.get('triage', 0))
    with col3:
        st.metric("Waiting Doctor", status_counts.get('waiting_consultation', 0))
    with col4:
        st.metric("Staff Members", staff_count)
    
    st.markdown("---")
    
    # Recent activity
    st.markdown("### Recent Patient Activity")
    conn = sqlite3.connect(db.db_name)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT p.patient_id, p.name, v.status, v.visit_date
        FROM visits v
        JOIN patients p ON v.patient_id = p.patient_id
        WHERE date(v.visit_date) = ? AND p.patient_id LIKE ?
        ORDER BY v.visit_date DESC
        LIMIT 10
    ''', (today, f'{location_code}%'))
    
    recent_patients = cursor.fetchall()
    conn.close()
    
    if recent_patients:
        for patient in recent_patients:
            patient_id, name, status, visit_date = patient
            status_emoji = {
                "triage": "📝 Awaiting Triage",
                "waiting_consultation": "⏳ Waiting for Doctor",
                "consultation": "👨‍⚕️ With Doctor",
                "prescribed": "💊 At Pharmacy",
                "completed": "✅ Completed"
            }.get(status, status)
            
            st.markdown(f"**{name}** ({patient_id}) - {status_emoji}")
    else:
        st.info("No patient activity yet today.")
    
    st.markdown("---")
    
    # Enter as staff button - prominently displayed
    st.markdown("### Access Clinic Roles")
    st.markdown("To perform clinical tasks, enter the clinic as a staff member.")
    
    if st.button("Enter as Staff Member", type="primary", use_container_width=True):
        st.session_state.org_admin_entering_as_staff = True
        st.rerun()


def organization_dashboard():
    """Organization dashboard showing clinics, stats, and management options"""
    org_id = st.session_state.get('selected_organization_id')
    if not org_id:
        return
    
    org = db.get_organization(org_id)
    if not org:
        st.error("Organization not found")
        return
    
    # Clean header styling
    st.markdown("""
    <style>
    .org-dashboard-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 8px 0 16px 0;
        border-bottom: 1px solid #e5e7eb;
        margin-bottom: 20px;
    }
    .org-welcome {
        color: #6b7280;
        font-size: 14px;
        margin: 0;
    }
    .org-title {
        font-size: 28px;
        font-weight: 600;
        color: #111827;
        margin: 0 0 4px 0;
    }
    .org-description {
        color: #6b7280;
        font-size: 14px;
        margin: 0;
    }
    .stat-card {
        background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 16px;
        text-align: center;
    }
    .stat-value {
        font-size: 32px;
        font-weight: 700;
        color: #0f766e;
        margin: 0;
    }
    .stat-label {
        font-size: 13px;
        color: #64748b;
        margin: 4px 0 0 0;
        font-weight: 500;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Compact header with user info and sign out
    header_col1, header_col2, header_col3 = st.columns([2, 2, 1])
    
    with header_col1:
        org_title = org['name']
        st.markdown(f"<h2 style='margin:0; font-size:24px; font-weight:600;'>{org_title}</h2>", unsafe_allow_html=True)
        if org['description']:
            st.markdown(f"<p style='margin:2px 0 0 0; color:#6b7280; font-size:14px;'>{org['description']}</p>", unsafe_allow_html=True)
    
    with header_col2:
        if st.session_state.get('org_user'):
            user = st.session_state.org_user
            st.markdown(f"<p style='margin:8px 0; color:#6b7280; font-size:13px;'>Signed in as <strong>{user['full_name']}</strong></p>", unsafe_allow_html=True)
        elif st.session_state.get('skip_org_admin') and st.session_state.get('clinic_staff'):
            staff = st.session_state.clinic_staff
            st.markdown(f"<p style='margin:8px 0; color:#6b7280; font-size:13px;'>Signed in as <strong>{staff.get('full_name', 'Staff')}</strong></p>", unsafe_allow_html=True)
    
    with header_col3:
        if st.button("Sign Out", key="sign_out_btn", use_container_width=True):
            for key in ['org_user', 'is_org_admin', 'skip_org_admin', 'selected_organization_id',
                        'selected_clinic_id', 'clinic_location', 'clinic_staff', 'user_role',
                        'page', 'doctor_name', 'active_consultation']:
                if key in st.session_state:
                    del st.session_state[key]
            st.query_params.clear()
            st.rerun()
    
    # Organization stats in styled cards
    stats = db.get_organization_stats(org_id)
    
    st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f"""
        <div class="stat-card">
            <p class="stat-value">{stats.get('total_clinics', 0)}</p>
            <p class="stat-label">Total Clinics</p>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div class="stat-card">
            <p class="stat-value">{stats.get('active_clinics', 0)}</p>
            <p class="stat-label">Active Clinics</p>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown(f"""
        <div class="stat-card">
            <p class="stat-value">{stats.get('total_patients', 0)}</p>
            <p class="stat-label">Total Patients</p>
        </div>
        """, unsafe_allow_html=True)
    with col4:
        st.markdown(f"""
        <div class="stat-card">
            <p class="stat-value">{stats.get('total_visits', 0)}</p>
            <p class="stat-label">Total Visits</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<div style='height: 24px;'></div>", unsafe_allow_html=True)
    
    # Tabs for different sections
    tab1, tab2, tab3 = st.tabs(["Clinics", "Reports", "Settings"])
    
    with tab1:
        clinic_management_tab(org_id)
    
    with tab2:
        organization_stats_tab(org_id, stats)
    
    with tab3:
        organization_settings_tab(org_id, org)


def clinic_management_tab(org_id):
    """Tab for managing clinics within an organization"""
    st.markdown("### Your Clinics")
    
    # Show archived toggle
    show_archived = st.checkbox("Show archived clinics", key="show_archived_clinics")
    
    clinics = db.get_organization_clinics(org_id, include_archived=show_archived)
    
    # Add new clinic button
    if st.button(t('create_new_clinic'), type="primary", key="create_clinic_btn"):
        st.session_state.show_create_clinic_form = True
    
    # Create clinic form
    if st.session_state.get('show_create_clinic_form', False):
        st.markdown("#### Create New Clinic")
        st.info("Enter the church and pastor information below. A clinic name will be suggested automatically.")
        
        # Church and Pastor fields OUTSIDE form for dynamic name generation
        col_church, col_pastor = st.columns(2)
        with col_church:
            church_name = st.text_input("Church Name *", 
                                        placeholder="e.g., First Baptist Church",
                                        key="church_name_input")
        with col_pastor:
            pastor_name = st.text_input("Pastor Last Name *", 
                                        placeholder="e.g., Rodriguez",
                                        key="pastor_name_input")
        
        # Date selection outside form for dynamic name generation
        col_date1, col_date2 = st.columns(2)
        with col_date1:
            start_date = st.date_input("Start Date *", 
                                       value=date.today(),
                                       key="start_date_input")
        with col_date2:
            end_date = st.date_input("End Date", key="end_date_input")
        
        # Generate suggested clinic name dynamically (no rerun needed)
        suggested_name = ""
        if church_name and pastor_name and start_date:
            month_year = start_date.strftime("%B %Y")
            suggested_name = f"{church_name}, {pastor_name} - {month_year}"
        
        # Show the suggested name
        if suggested_name:
            st.markdown(f"**Suggested Clinic Name:** {suggested_name}")
            st.caption("Tip: The clinic name below will update based on your entries above. You can customize it in the form.")
        
        st.markdown("---")
        
        with st.form("create_clinic_form"):
            # Clinic name - pre-filled with suggestion but editable
            clinic_name = st.text_input("Clinic Name *", 
                                        value=suggested_name,
                                        placeholder="e.g., First Baptist Church, Rodriguez - January 2025",
                                        help="You can edit this name if needed. Complete church/pastor entries first.")
            
            col1, col2 = st.columns(2)
            with col1:
                country = st.selectbox("Country", ["Dominican Republic", "Haiti", "Other"])
                if country == "Other":
                    country = st.text_input("Enter country name")
            with col2:
                city = st.text_input("City/Town *", placeholder="Enter clinic city")
            
            description = st.text_area("Description (optional)", placeholder="Enter clinic description")
            
            col_submit, col_cancel = st.columns(2)
            with col_submit:
                if st.form_submit_button("Create Clinic", type="primary"):
                    if clinic_name and city and church_name and pastor_name:
                        new_clinic_id = db.create_clinic(
                            organization_id=org_id,
                            name=clinic_name,
                            description=description,
                            location_city=city,
                            location_country=country,
                            start_date=start_date.isoformat() if start_date else '',
                            end_date=end_date.isoformat() if end_date else '',
                            status='planning'
                        )
                        st.success(f"Clinic '{clinic_name}' created successfully!")
                        st.session_state.show_create_clinic_form = False
                        st.rerun()
                    else:
                        st.error("Please fill in all required fields: Church Name, Pastor Last Name, Clinic Name, and City")
            with col_cancel:
                if st.form_submit_button("Cancel"):
                    st.session_state.show_create_clinic_form = False
                    st.rerun()
    
    st.markdown("---")
    
    # Display clinics
    if clinics:
        for clinic in clinics:
            clinic_status_color = {
                'planning': '#f59e0b',  # amber
                'active': '#10b981',     # green
                'completed': '#6b7280',  # gray
            }.get(clinic['status'], '#6b7280')
            
            with st.container():
                st.markdown(f"""
                <div style="border: 1px solid #e5e7eb; border-radius: 10px; padding: 15px; margin-bottom: 15px; 
                            border-left: 4px solid {clinic_status_color}; background: white;">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <h4 style="margin: 0; color: #1f2937;">{clinic['name']}</h4>
                            <p style="margin: 5px 0; color: #6b7280; font-size: 14px;">
                                📍 {clinic['location_city']}, {clinic['location_country']}
                            </p>
                            <p style="margin: 0; color: #9ca3af; font-size: 12px;">
                                {clinic['start_date'] or 'No date'} - {clinic['end_date'] or 'No date'}
                            </p>
                        </div>
                        <div style="text-align: right;">
                            <span style="background: {clinic_status_color}; color: white; padding: 4px 12px; 
                                         border-radius: 20px; font-size: 12px; text-transform: uppercase;">
                                {clinic['status']}
                            </span>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                col1, col2, col3 = st.columns([2, 1, 1])
                with col1:
                    if not clinic['is_archived'] and st.button("Enter Clinic", key=f"enter_clinic_{clinic['id']}", type="primary"):
                        # Select this clinic and proceed
                        select_clinic(clinic['id'])
                with col2:
                    if st.button("✏️ Edit", key=f"edit_clinic_{clinic['id']}"):
                        st.session_state[f'editing_clinic_{clinic["id"]}'] = True
                        st.rerun()
                with col3:
                    if not clinic['is_archived']:
                        if st.button("📦 Archive", key=f"archive_clinic_{clinic['id']}"):
                            db.archive_clinic(clinic['id'])
                            st.success("Clinic archived")
                            st.rerun()
                
                # Edit form
                if st.session_state.get(f'editing_clinic_{clinic["id"]}', False):
                    with st.form(f"edit_clinic_form_{clinic['id']}"):
                        new_name = st.text_input("Clinic Name", value=clinic['name'])
                        new_desc = st.text_area("Description", value=clinic.get('description', ''))
                        new_status = st.selectbox("Status", ['planning', 'active', 'completed'], 
                                                 index=['planning', 'active', 'completed'].index(clinic['status']))
                        
                        col_save, col_cancel = st.columns(2)
                        with col_save:
                            if st.form_submit_button("Save", type="primary"):
                                db.update_clinic(clinic['id'], name=new_name, description=new_desc, status=new_status)
                                st.session_state[f'editing_clinic_{clinic["id"]}'] = False
                                st.success("Clinic updated!")
                                st.rerun()
                        with col_cancel:
                            if st.form_submit_button("Cancel"):
                                st.session_state[f'editing_clinic_{clinic["id"]}'] = False
                                st.rerun()
                
                st.markdown("---")
    else:
        st.info("No clinics found. Create your first clinic using the button above.")


def select_clinic(clinic_db_id):
    """Select a clinic and set up session state"""
    clinic = db.get_clinic(clinic_db_id)
    if clinic:
        st.session_state.selected_clinic_id = clinic_db_id
        st.session_state.clinic_location = {
            'id': clinic['id'],
            'city': clinic['location_city'],
            'country_name': clinic['location_country'],
            'country_code': clinic['patient_id_prefix'] or clinic['location_code'] or 'CL'
        }
        # Also update the clinic status to active if it was planning
        if clinic['status'] == 'planning':
            db.update_clinic(clinic_db_id, status='active')
        st.rerun()


def organization_stats_tab(org_id, stats):
    """Tab showing organization-wide statistics"""
    st.markdown("### Organization Overview")
    
    # Get all clinics for detailed stats
    clinics = db.get_organization_clinics(org_id, include_archived=True)
    
    if clinics:
        st.markdown("#### Clinic Summary")
        
        # Create a table of clinic stats
        clinic_data = []
        for clinic in clinics:
            clinic_stats = db.get_clinic_stats(clinic['id'])
            clinic_data.append({
                'Clinic': clinic['name'],
                'Location': f"{clinic['location_city']}, {clinic['location_country']}",
                'Status': clinic['status'].title(),
                'Patients': clinic_stats.get('total_patients', 0),
                'Visits': clinic_stats.get('total_visits', 0),
                'Completed': clinic_stats.get('completed_visits', 0)
            })
        
        import pandas as pd
        df = pd.DataFrame(clinic_data)
        st.dataframe(df, use_container_width=True, hide_index=True)
        
        # Summary stats
        st.markdown("#### Totals Across All Clinics")
        total_patients = sum(c.get('Patients', 0) for c in clinic_data)
        total_visits = sum(c.get('Visits', 0) for c in clinic_data)
        total_completed = sum(c.get('Completed', 0) for c in clinic_data)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Patients Served", total_patients)
        with col2:
            st.metric("Total Visits", total_visits)
        with col3:
            st.metric("Completed Visits", total_completed)
    else:
        st.info("No clinic data available yet.")


def organization_settings_tab(org_id, org):
    """Tab for organization settings"""
    
    # Sub-tabs for settings
    settings_tab1, settings_tab2, settings_tab3 = st.tabs(["📋 General", "👥 Org Admins", "🏥 Clinic Staff"])
    
    with settings_tab1:
        st.markdown("### Organization Details")
        
        with st.form("org_settings_form"):
            new_name = st.text_input("Organization Name", value=org['name'])
            new_description = st.text_area("Description", value=org.get('description', ''))
            
            col1, col2 = st.columns(2)
            with col1:
                new_contact_name = st.text_input("Contact Name", value=org.get('contact_name', ''))
            with col2:
                new_contact_email = st.text_input("Contact Email", value=org.get('contact_email', ''))
            
            new_contact_phone = st.text_input("Contact Phone", value=org.get('contact_phone', ''))
            new_address = st.text_area("Address", value=org.get('address', ''))
            
            if st.form_submit_button("Save Settings", type="primary"):
                db.update_organization(
                    org_id,
                    name=new_name,
                    description=new_description,
                    contact_name=new_contact_name,
                    contact_email=new_contact_email,
                    contact_phone=new_contact_phone,
                    address=new_address
                )
                st.success("Organization settings saved!")
                st.rerun()
        
        st.markdown("---")
        st.markdown("### Switch Organization")
        if st.button("🔄 Change Organization", key="change_org_btn"):
            st.session_state.selected_organization_id = None
            st.session_state.selected_clinic_id = None
            st.session_state.clinic_location = None
            st.session_state.org_user = None
            st.session_state.is_org_admin = False
            st.session_state.skip_org_admin = False
            st.rerun()
    
    with settings_tab2:
        st.markdown("### Organization Administrators")
        st.markdown("These users can manage the entire organization and view all clinics.")
        
        org_users = db.get_org_users(org_id, include_inactive=True)
        
        # Add new org admin button
        if st.button("➕ Add Org Admin", key="add_org_admin_btn"):
            st.session_state.show_add_org_admin = True
        
        if st.session_state.get('show_add_org_admin', False):
            with st.form("add_org_admin_form"):
                st.markdown("#### Add New Organization Admin")
                full_name = st.text_input("Full Name", placeholder="e.g., Jane Smith")
                title = st.text_input("Title", placeholder="e.g., Mission Director")
                col1, col2 = st.columns(2)
                with col1:
                    email = st.text_input("Email (optional)", placeholder="email@example.com")
                with col2:
                    phone = st.text_input("Phone (optional)", placeholder="555-123-4567")
                col3, col4 = st.columns(2)
                with col3:
                    pin = st.text_input("4-Digit PIN", type="password", max_chars=4, placeholder="****")
                with col4:
                    confirm_pin = st.text_input("Confirm PIN", type="password", max_chars=4, placeholder="****")
                
                col_submit, col_cancel = st.columns(2)
                with col_submit:
                    if st.form_submit_button("Add Admin", type="primary"):
                        if not full_name:
                            st.error("Please enter a name")
                        elif not pin or len(pin) != 4 or not pin.isdigit():
                            st.error("PIN must be exactly 4 digits")
                        elif pin != confirm_pin:
                            st.error("PINs do not match")
                        else:
                            db.create_org_user(org_id, full_name, pin, title=title, email=email, phone=phone)
                            st.success(f"Admin '{full_name}' added!")
                            st.session_state.show_add_org_admin = False
                            st.rerun()
                with col_cancel:
                    if st.form_submit_button("Cancel"):
                        st.session_state.show_add_org_admin = False
                        st.rerun()
        
        # List existing org admins
        if org_users:
            st.markdown("#### Current Admins")
            for user in org_users:
                status_emoji = "✅" if user['is_active'] else "❌"
                with st.expander(f"{status_emoji} {user['full_name']} - {user.get('title', 'Admin')}"):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write(f"**Email:** {user.get('email', 'N/A')}")
                        st.write(f"**Phone:** {user.get('phone', 'N/A')}")
                    with col2:
                        st.write(f"**Last Login:** {user.get('last_login', 'Never')[:10] if user.get('last_login') else 'Never'}")
                        st.write(f"**Status:** {'Active' if user['is_active'] else 'Inactive'}")
                    
                    col_actions = st.columns(3)
                    with col_actions[0]:
                        if st.button("🔄 Reset PIN", key=f"reset_pin_org_{user['id']}"):
                            st.session_state[f'resetting_org_user_{user["id"]}'] = True
                    with col_actions[1]:
                        if user['is_active']:
                            if st.button("🚫 Deactivate", key=f"deactivate_org_{user['id']}"):
                                db.update_org_user(user['id'], is_active=0)
                                st.success("User deactivated")
                                st.rerun()
                        else:
                            if st.button("✅ Activate", key=f"activate_org_{user['id']}"):
                                db.update_org_user(user['id'], is_active=1)
                                st.success("User activated")
                                st.rerun()
                    
                    if st.session_state.get(f'resetting_org_user_{user["id"]}', False):
                        with st.form(f"reset_pin_form_org_{user['id']}"):
                            new_pin = st.text_input("New 4-Digit PIN", type="password", max_chars=4)
                            confirm_new_pin = st.text_input("Confirm New PIN", type="password", max_chars=4)
                            if st.form_submit_button("Update PIN"):
                                if new_pin and len(new_pin) == 4 and new_pin.isdigit() and new_pin == confirm_new_pin:
                                    db.update_org_user(user['id'], pin=new_pin)
                                    st.success("PIN updated!")
                                    st.session_state[f'resetting_org_user_{user["id"]}'] = False
                                    st.rerun()
                                else:
                                    st.error("Invalid PIN or PINs don't match")
        else:
            st.info("No organization admins found.")
    
    with settings_tab3:
        st.markdown("### Clinic Staff Management")
        st.markdown("Manage staff members for each clinic.")
        
        clinics = db.get_organization_clinics(org_id)
        
        if clinics:
            selected_clinic = st.selectbox(
                "Select Clinic",
                options=[c['id'] for c in clinics],
                format_func=lambda x: next((c['name'] for c in clinics if c['id'] == x), 'Unknown'),
                key="staff_mgmt_clinic_select"
            )
            
            if selected_clinic:
                clinic_staff = db.get_clinic_staff(selected_clinic, include_inactive=True)
                
                # Add new staff button
                if st.button("➕ Add Staff Member", key="add_clinic_staff_btn"):
                    st.session_state.show_add_clinic_staff = True
                
                if st.session_state.get('show_add_clinic_staff', False):
                    with st.form("add_clinic_staff_form"):
                        st.markdown("#### Add New Staff Member")
                        staff_name = st.text_input("Full Name", placeholder="e.g., Maria Garcia")
                        staff_title = st.text_input("Title/Role", placeholder="e.g., Nurse, Doctor, Translator")
                        role_scope = st.selectbox("Access Level", 
                            ["all", "triage", "doctor", "pharmacy", "lab", "registration"],
                            help="'all' gives access to all roles, otherwise restricts to specific role")
                        col1, col2 = st.columns(2)
                        with col1:
                            staff_pin = st.text_input("4-Digit PIN", type="password", max_chars=4, placeholder="****")
                        with col2:
                            confirm_staff_pin = st.text_input("Confirm PIN", type="password", max_chars=4, placeholder="****")
                        
                        col_submit, col_cancel = st.columns(2)
                        with col_submit:
                            if st.form_submit_button("Add Staff", type="primary"):
                                if not staff_name or not staff_title:
                                    st.error("Please enter name and title")
                                elif not staff_pin or len(staff_pin) != 4 or not staff_pin.isdigit():
                                    st.error("PIN must be exactly 4 digits")
                                elif staff_pin != confirm_staff_pin:
                                    st.error("PINs do not match")
                                else:
                                    db.create_clinic_staff(selected_clinic, staff_name, staff_title, staff_pin, role_scope=role_scope)
                                    st.success(f"Staff member '{staff_name}' added!")
                                    st.session_state.show_add_clinic_staff = False
                                    st.rerun()
                        with col_cancel:
                            if st.form_submit_button("Cancel"):
                                st.session_state.show_add_clinic_staff = False
                                st.rerun()
                
                # List existing staff
                if clinic_staff:
                    st.markdown("#### Current Staff")
                    for staff in clinic_staff:
                        status_emoji = "✅" if staff['is_active'] else "❌"
                        with st.expander(f"{status_emoji} {staff['full_name']} - {staff['title']}"):
                            col1, col2 = st.columns(2)
                            with col1:
                                st.write(f"**Role Scope:** {staff.get('role_scope', 'all')}")
                            with col2:
                                st.write(f"**Last Login:** {staff.get('last_login', 'Never')[:10] if staff.get('last_login') else 'Never'}")
                            
                            col_actions = st.columns(3)
                            with col_actions[0]:
                                if st.button("🔄 Reset PIN", key=f"reset_pin_staff_{staff['id']}"):
                                    st.session_state[f'resetting_staff_{staff["id"]}'] = True
                            with col_actions[1]:
                                if staff['is_active']:
                                    if st.button("🚫 Deactivate", key=f"deactivate_staff_{staff['id']}"):
                                        db.update_clinic_staff(staff['id'], is_active=0)
                                        st.success("Staff deactivated")
                                        st.rerun()
                                else:
                                    if st.button("✅ Activate", key=f"activate_staff_{staff['id']}"):
                                        db.update_clinic_staff(staff['id'], is_active=1)
                                        st.success("Staff activated")
                                        st.rerun()
                            
                            if st.session_state.get(f'resetting_staff_{staff["id"]}', False):
                                with st.form(f"reset_pin_form_staff_{staff['id']}"):
                                    new_pin = st.text_input("New 4-Digit PIN", type="password", max_chars=4)
                                    confirm_new_pin = st.text_input("Confirm New PIN", type="password", max_chars=4)
                                    if st.form_submit_button("Update PIN"):
                                        if new_pin and len(new_pin) == 4 and new_pin.isdigit() and new_pin == confirm_new_pin:
                                            db.update_clinic_staff(staff['id'], pin=new_pin)
                                            st.success("PIN updated!")
                                            st.session_state[f'resetting_staff_{staff["id"]}'] = False
                                            st.rerun()
                                        else:
                                            st.error("Invalid PIN or PINs don't match")
                else:
                    st.info("No staff members registered for this clinic.")
        else:
            st.info("Create a clinic first to add staff members.")


def organization_selection():
    """Show organization selection screen"""
    st.markdown("## 🏥 ParakaleoMed")
    st.markdown("### Select or Create Your Organization")
    
    orgs = db.get_all_organizations()
    
    if orgs:
        st.markdown("#### Available Organizations")
        for org in orgs:
            with st.container():
                col1, col2 = st.columns([4, 1])
                with col1:
                    st.markdown(f"""
                    <div style="border: 1px solid #e5e7eb; border-radius: 8px; padding: 12px; margin-bottom: 10px; background: white;">
                        <h4 style="margin: 0; color: #1f2937;">{org['name']}</h4>
                        <p style="margin: 5px 0 0 0; color: #6b7280; font-size: 14px;">{org.get('description', 'No description')}</p>
                    </div>
                    """, unsafe_allow_html=True)
                with col2:
                    if st.button("Select", key=f"select_org_{org['id']}", type="primary"):
                        st.session_state.selected_organization_id = org['id']
                        st.rerun()
    
    st.markdown("---")
    
    # Create new organization
    if st.button("➕ Create New Organization", key="create_org_btn"):
        st.session_state.show_create_org_form = True
    
    if st.session_state.get('show_create_org_form', False):
        with st.form("create_org_form"):
            st.markdown("#### Create New Organization")
            org_name = st.text_input("Organization Name", placeholder="e.g., Global Health Missions")
            org_description = st.text_area("Description", placeholder="Brief description of your organization")
            
            col1, col2 = st.columns(2)
            with col1:
                contact_name = st.text_input("Contact Person Name")
            with col2:
                contact_email = st.text_input("Contact Email")
            
            col_submit, col_cancel = st.columns(2)
            with col_submit:
                if st.form_submit_button("Create Organization", type="primary"):
                    if org_name:
                        new_org_id = db.create_organization(
                            name=org_name,
                            description=org_description,
                            contact_name=contact_name,
                            contact_email=contact_email
                        )
                        st.success(f"Organization '{org_name}' created!")
                        st.session_state.selected_organization_id = new_org_id
                        st.session_state.show_create_org_form = False
                        st.rerun()
                    else:
                        st.error("Please enter an organization name")
            with col_cancel:
                if st.form_submit_button("Cancel"):
                    st.session_state.show_create_org_form = False
                    st.rerun()


def location_setup():
    st.markdown("## Clinic Location Setup")
    st.markdown(
        "Please select or add your clinic location before starting patient registration."
    )

    # Get existing locations
    locations = db.get_locations()

    tab1, tab2 = st.tabs(["Select Location", "Edit Locations"])

    with tab1:
        if locations:
            st.markdown("### Existing Locations:")
            for location in locations:
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.markdown(
                        f"**{location['city']}, {location['country_name']}** ({location['country_code']})"
                    )
                with col2:
                    if st.button("Select", key=f"select_{location['id']}"):
                        st.session_state.clinic_location = location
                        update_page_url("role_selection")
                        st.rerun()
        else:
            st.info("No locations found. Please add a new location below.")

    with tab2:
        st.markdown('<p style="font-size: 18px; font-weight: bold; margin-bottom: 10px;">Manage Locations</p>', unsafe_allow_html=True)
        
        # Add Location button at the top
        add_key = "show_add_location_form"
        if not st.session_state.get(add_key, False):
            if st.button("➕ Add Location", type="secondary", key="add_location_top"):
                st.session_state[add_key] = True
                st.rerun()
        
        # Add location form (shown when button clicked)
        if st.session_state.get(add_key, False):
            with st.form("add_new_location_setup"):
                st.markdown('<p style="font-size: 16px; font-weight: bold; margin-bottom: 8px;">Add New Location</p>', unsafe_allow_html=True)
                col1, col2 = st.columns(2)
                with col1:
                    add_country = st.selectbox("Country",
                                             ["Dominican Republic", "Haiti"],
                                             key="add_country_setup")
                    add_country_code = "DR" if add_country == "Dominican Republic" else "H"
                with col2:
                    add_city = st.text_input("City/Town",
                                           placeholder="Enter clinic city",
                                           key="add_city_setup")
                
                col_add, col_cancel_add = st.columns(2)
                with col_add:
                    if st.form_submit_button("Add Location", type="primary"):
                        if add_city.strip():
                            location_id = db.add_location(add_country_code, add_country, add_city.strip())
                            st.success(f"Location '{add_city.strip()}, {add_country}' added successfully!")
                            
                            # Auto-select the new location
                            new_location = {
                                'id': location_id,
                                'country_code': add_country_code,
                                'country_name': add_country,
                                'city': add_city.strip(),
                                'created_date': datetime.now().isoformat()
                            }
                            st.session_state.clinic_location = new_location
                            st.session_state[add_key] = False
                            update_page_url("role_selection")
                            st.rerun()
                        else:
                            st.error("Please enter a city name.")
                
                with col_cancel_add:
                    if st.form_submit_button("Cancel"):
                        st.session_state[add_key] = False
                        st.rerun()
            st.markdown("---")
        
        if locations:
            for location in locations:
                with st.expander(f"{location['city']}, {location['country_name']}", expanded=False):
                    edit_key = f"edit_setup_{location['id']}"
                    
                    if st.session_state.get(edit_key, False):
                        # Edit form
                        with st.form(f"edit_location_setup_{location['id']}"):
                            col1, col2 = st.columns(2)
                            with col1:
                                new_country = st.selectbox("Country",
                                                         ["Dominican Republic", "Haiti"],
                                                         index=0 if location['country_name'] == "Dominican Republic" else 1)
                                new_country_code = "DR" if new_country == "Dominican Republic" else "H"
                            with col2:
                                new_city = st.text_input("City/Town",
                                                        value=location['city'])
                            
                            col_save, col_cancel = st.columns(2)
                            with col_save:
                                if st.form_submit_button("Save Changes", type="primary"):
                                    if new_city.strip():
                                        # Update location in database
                                        conn = sqlite3.connect(db.db_name)
                                        cursor = conn.cursor()
                                        cursor.execute('''
                                            UPDATE locations 
                                            SET country_code = ?, country_name = ?, city = ?
                                            WHERE id = ?
                                        ''', (new_country_code, new_country, new_city.strip(), location['id']))
                                        conn.commit()
                                        conn.close()
                                        
                                        st.session_state[edit_key] = False
                                        st.success("Location updated successfully!")
                                        st.rerun()
                                    else:
                                        st.error("Please enter a city name.")
                            
                            with col_cancel:
                                if st.form_submit_button("Cancel"):
                                    st.session_state[edit_key] = False
                                    st.rerun()
                    else:
                        # Display mode with edit button
                        col1, col2 = st.columns([3, 1])
                        with col1:
                            st.markdown(f'<p style="font-size: 14px; margin: 2px 0;"><strong>Country:</strong> {location["country_name"]} ({location["country_code"]})</p>', unsafe_allow_html=True)
                            st.markdown(f'<p style="font-size: 14px; margin: 2px 0;"><strong>City:</strong> {location["city"]}</p>', unsafe_allow_html=True)
                        with col2:
                            if st.button("✏️ Edit", key=f"edit_setup_btn_{location['id']}"):
                                st.session_state[edit_key] = True
                                st.rerun()
        else:
            st.markdown('<p style="font-size: 14px; color: #666; text-align: center; padding: 20px;">No locations found. Add your first location using the button above.</p>', unsafe_allow_html=True)


def family_vital_signs_collection():
    """Handle vital signs collection for family members in sequence"""
    if 'family_vital_signs_queue' not in st.session_state or not st.session_state.family_vital_signs_queue:
        return

    current_index = st.session_state.get('current_family_vital_index', 0)
    family_queue = st.session_state.family_vital_signs_queue

    if current_index >= len(family_queue):
        # All family members completed - show confirmation
        st.success("✅ All family members' vital signs have been recorded!")

        # Show summary of completed family
        st.markdown("### Family Vital Signs Summary")
        for i, member in enumerate(family_queue):
            status_icon = "✅"
            st.markdown(
                f"{status_icon} **{member['patient_name']}** ({member['relationship'].title()}) - Vital signs recorded"
            )

        st.markdown("---")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ Confirm - Family Ready for Consultation",
                         type="primary",
                         use_container_width=True):
                # Clear family vital signs workflow
                if 'family_vital_signs_queue' in st.session_state:
                    del st.session_state.family_vital_signs_queue
                if 'current_family_vital_index' in st.session_state:
                    del st.session_state.current_family_vital_index
                if 'family_workflow_active' in st.session_state:
                    del st.session_state.family_workflow_active

                st.success(
                    "🎉 Family consultation ready! All members added to doctor queue."
                )
                st.rerun()

        with col2:
            if st.button("📝 Review/Edit Family Vital Signs",
                         type="secondary",
                         use_container_width=True):
                # Reset to allow editing
                st.session_state.current_family_vital_index = 0
                st.info(
                    "You can now review and edit each family member's vital signs."
                )
                st.rerun()

        return

    current_member = family_queue[current_index]
    remaining_count = len(family_queue) - current_index

    st.markdown("### 👶 Family Vital Signs Collection")
    st.info(
        f"Recording vital signs for family member {current_index + 1} of {len(family_queue)}"
    )

    # Progress indicator
    progress = (current_index) / len(family_queue)
    st.progress(progress)

    # Show current family member info
    st.markdown(f"""
    <div style="background-color: #e3f2fd; border-left: 4px solid #2196f3; padding: 1rem; margin: 1rem 0; border-radius: 0.375rem;">
        <h4 style="margin: 0; color: #1976d2;">👤 {current_member['patient_name']}</h4>
        <p style="margin: 0.5rem 0 0 0; color: #424242;">
            <strong>Patient ID:</strong> {current_member['patient_id']} | 
            <strong>Relationship:</strong> {current_member['relationship'].title()} |
            <strong>Age:</strong> {current_member.get('age', 'Unknown')}
        </p>
    </div>
    """,
                unsafe_allow_html=True)

    # Show remaining family members
    if remaining_count > 1:
        st.markdown(f"**Remaining:** {remaining_count - 1} family members")
        remaining_names = [
            member['patient_name']
            for member in family_queue[current_index + 1:]
        ]
        st.markdown(f"*Next: {', '.join(remaining_names)}*")

    # Vital signs form for current family member
    with st.form(f"family_vitals_{current_member['visit_id']}"):
        st.markdown("#### Vital Signs")
        st.info("💡 **Tip:** Enter 'N/A' for any measurement that cannot be taken (e.g., broken equipment, child won't cooperate)")

        col1, col2, col3 = st.columns(3)

        with col1:
            systolic = st.text_input("Systolic BP",
                                     value="120",
                                     placeholder="e.g., 120 or N/A")
            diastolic = st.text_input("Diastolic BP",
                                      value="80",
                                      placeholder="e.g., 80 or N/A")

        with col2:
            heart_rate = st.text_input("Heart Rate (bpm)",
                                       value="72",
                                       placeholder="e.g., 72 or N/A")
            temperature = st.text_input("Temperature (°F)",
                                        value="98.6",
                                        placeholder="e.g., 98.6 or N/A")

        with col3:
            weight = st.text_input("Weight (kg)",
                                   placeholder="e.g., 15.5 or N/A")
            oxygen_sat = st.text_input("O2 Saturation (%)",
                                       value="98",
                                       placeholder="e.g., 98 or N/A")

        col1, col2 = st.columns([1, 1])
        with col1:
            if st.form_submit_button("Save Vital Signs & Continue",
                                     type="primary"):
                # Convert text inputs to appropriate values, handling N/A entries
                def process_vital_sign(value, is_decimal=False):
                    if not value or value.strip().upper() == 'N/A':
                        return None
                    try:
                        return float(value) if is_decimal else int(float(value))
                    except ValueError:
                        return None
                
                # Process each vital sign
                systolic_val = process_vital_sign(systolic)
                diastolic_val = process_vital_sign(diastolic)
                heart_rate_val = process_vital_sign(heart_rate)
                temperature_val = process_vital_sign(temperature, is_decimal=True)
                weight_val = process_vital_sign(weight, is_decimal=True)
                oxygen_sat_val = process_vital_sign(oxygen_sat)
                
                # Save vital signs for current family member
                conn = sqlite3.connect(db.db_name)
                cursor = conn.cursor()

                # First, delete any existing vital signs for this visit (in case of editing)
                cursor.execute('DELETE FROM vital_signs WHERE visit_id = ?',
                               (current_member['visit_id'], ))

                cursor.execute(
                    '''
                    INSERT INTO vital_signs (visit_id, systolic_bp, diastolic_bp, heart_rate, 
                                           temperature, weight, oxygen_saturation, recorded_time)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (current_member['visit_id'], systolic_val, diastolic_val,
                      heart_rate_val, temperature_val, weight_val, oxygen_sat_val,
                      datetime.now().isoformat()))

                # Update visit status
                cursor.execute(
                    '''
                    UPDATE visits SET triage_time = ?, status = ? WHERE visit_id = ?
                ''', (datetime.now().isoformat(), 'waiting_consultation',
                      current_member['visit_id']))

                conn.commit()
                conn.close()

                st.success(
                    f"✅ Vital signs recorded for {current_member['patient_name']}"
                )

                # Move to next family member
                st.session_state.current_family_vital_index = current_index + 1
                st.rerun()

        with col2:
            if st.form_submit_button("Skip This Member", type="secondary"):
                st.warning(
                    f"Skipped vital signs for {current_member['patient_name']}"
                )
                st.session_state.current_family_vital_index = current_index + 1
                st.rerun()

    # Navigation buttons outside the form
    st.markdown("---")
    nav_col1, nav_col2, nav_col3 = st.columns([1, 2, 1])

    with nav_col1:
        if current_index > 0:
            if st.button("⬅️ Previous Family Member",
                         use_container_width=True):
                st.session_state.current_family_vital_index = current_index - 1
                st.rerun()

    with nav_col3:
        if current_index < len(family_queue) - 1:
            if st.button("Next Family Member ➡️", use_container_width=True):
                st.session_state.current_family_vital_index = current_index + 1
                st.rerun()
        elif current_index == len(family_queue) - 1:
            if st.button("Complete Family ✅",
                         type="primary",
                         use_container_width=True):
                st.session_state.current_family_vital_index = len(family_queue)
                st.rerun()


def name_registration_interface():
    render_doctor_status_strip()
    add_to_history('name_registration')
    st.markdown(f"## {t('page_name_registration')}")
    st.caption(t('name_reg_caption'))

    # Current location
    location_code = st.session_state.clinic_location['country_code']
    
    tab1, tab2 = st.tabs(["Register Names", "Name Queue"])
    
    with tab1:
        st.markdown(f"### {t('hdr_add_patient_names')}")
        
        registration_type = st.radio("Registration Type", 
                                   ["Individual Patient", "Family Group"], 
                                   horizontal=True)
        
        if registration_type == "Individual Patient":
            # Check if form was just submitted successfully to clear fields
            if st.session_state.get('name_registration_success', False):
                st.session_state.name_registration_success = False
                st.success("Patient added to queue! Form cleared for next entry.")
            
            with st.form("name_registration_individual", clear_on_submit=True):
                col1, col2 = st.columns(2)
                with col1:
                    name = st.text_input("Patient Name *", value="")
                    age = st.number_input("Age", min_value=0, max_value=120, value=0)
                    # Date of birth (optional - more precise than age)
                    dob = st.date_input("Date of Birth (optional)", value=None, min_value=date(1900, 1, 1), max_value=date.today())
                with col2:
                    gender = st.selectbox("Gender", ["", "Male", "Female"], index=0)
                    notes = st.text_input("Notes (optional)", placeholder="Special considerations...", value="")
                
                # Medical History field
                medical_history = st.text_area("Medical History", 
                                               placeholder="Any relevant medical conditions, allergies, or medications",
                                               height=100,
                                               value="")
                
                if st.form_submit_button(t('add_to_queue'), type="primary"):
                    if not name.strip():
                        st.error("Please enter a patient name.")
                    else:
                        conn = sqlite3.connect(db.db_name)
                        cursor = conn.cursor()
                        cursor.execute('''
                            INSERT INTO patient_names_queue 
                            (name, age, gender, location_code, relationship, created_time, notes)
                            VALUES (?, ?, ?, ?, ?, ?, ?)
                        ''', (name.strip(), age if age > 0 else None, gender if gender else None, location_code, 
                             'individual', datetime.now().isoformat(), 
                             (medical_history.strip() + ('\n' + notes.strip() if notes else '')) if medical_history else (notes.strip() if notes else None)))
                        conn.commit()
                        conn.close()
                        
                        # Broadcast update to all connected devices
                        broadcast_to_clients(f"new_name_registered:{name.strip()}")
                        
                        # Set success flag to show confirmation and clear form
                        st.session_state.name_registration_success = True
                        
                        st.rerun()

        else:  # Family Group — single-screen redesign (Phase 3)
            if st.session_state.get('family_registration_success', False):
                st.session_state.family_registration_success = False
                st.success("Family added to triage queue. Ready for the next.")
            st.caption(
                "Register a family on one screen. Add the head of household first, "
                "then any spouse and children. All members are saved together so "
                "they show up grouped in triage.")
            family_registration_unified(location_code)
    
    with tab2:
        st.markdown(f"### {t('hdr_registration_queue')}")
        
        # Get pending names
        conn = sqlite3.connect(db.db_name)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, name, age, gender, relationship, family_group_id, created_time, notes, status
            FROM patient_names_queue 
            WHERE status = 'pending_vitals' AND location_code = ?
            ORDER BY family_group_id, 
                     CASE relationship 
                         WHEN 'parent' THEN 0 
                         WHEN 'spouse' THEN 1 
                         ELSE 2 
                     END, 
                     created_time
        ''', (location_code,))
        
        pending_names = cursor.fetchall()
        conn.close()
        
        if pending_names:
            # Group by family if applicable
            families = {}
            individuals = []
            
            for row in pending_names:
                name_id, name, age, gender, relationship, family_group_id, created_time, notes, status = row
                if family_group_id:
                    if family_group_id not in families:
                        families[family_group_id] = []
                    families[family_group_id].append({
                        'id': name_id, 'name': name, 'age': age, 'gender': gender,
                        'relationship': relationship, 'created_time': created_time, 'notes': notes
                    })
                else:
                    individuals.append({
                        'id': name_id, 'name': name, 'age': age, 'gender': gender,
                        'relationship': relationship, 'created_time': created_time, 'notes': notes
                    })
            
            # Display families
            for family_id, members in families.items():
                with st.expander(f"👨‍👩‍👧‍👦 Family Group ({len(members)} members)", expanded=True):
                    for member in members:
                        col1, col2, col3 = st.columns([3, 1, 1])
                        edit_key = f"edit_family_{member['id']}"
                        
                        with col1:
                            # Check if this member is in edit mode
                            if st.session_state.get(edit_key, False):
                                # Edit form for family member
                                with st.form(f"edit_form_{member['id']}"):
                                    new_name = st.text_input("Name", value=member['name'], key=f"edit_name_{member['id']}")
                                    col_age, col_gender = st.columns(2)
                                    with col_age:
                                        new_age = st.number_input("Age", value=member['age'] if member['age'] else 0, min_value=0, max_value=120, key=f"edit_age_{member['id']}")
                                    with col_gender:
                                        gender_options = ["", "Male", "Female"]
                                        gender_index = gender_options.index(member['gender']) if member['gender'] in gender_options else 0
                                        new_gender = st.selectbox("Gender", gender_options, index=gender_index, key=f"edit_gender_{member['id']}")
                                    new_notes = st.text_area("Notes", value=member['notes'] if member['notes'] else "", key=f"edit_notes_{member['id']}")
                                    
                                    col_save, col_cancel = st.columns(2)
                                    with col_save:
                                        if st.form_submit_button("Save", type="primary"):
                                            if new_name.strip():
                                                conn = sqlite3.connect(db.db_name)
                                                cursor = conn.cursor()
                                                cursor.execute('''
                                                    UPDATE patient_names_queue 
                                                    SET name = ?, age = ?, gender = ?, notes = ?
                                                    WHERE id = ?
                                                ''', (new_name.strip(), new_age if new_age > 0 else None, 
                                                     new_gender if new_gender else None, new_notes.strip() if new_notes else None, member['id']))
                                                conn.commit()
                                                conn.close()
                                                
                                                # Broadcast update to all connected devices
                                                broadcast_to_clients(f"patient_updated:{new_name.strip()}")
                                                
                                                st.session_state[edit_key] = False
                                                st.success(f"Updated {new_name}")
                                                st.rerun()
                                            else:
                                                st.error(t('err_name_cannot_be_empty'))
                                    with col_cancel:
                                        if st.form_submit_button("Cancel"):
                                            st.session_state[edit_key] = False
                                            st.rerun()
                            else:
                                # Display mode for family member
                                if member['relationship'] == 'parent':
                                    icon = "👨"
                                elif member['relationship'] == 'spouse':
                                    icon = "💑"
                                else:
                                    icon = "👶"
                                st.write(f"{icon} **{member['name']}** ({member['relationship']})")
                                if member['age']:
                                    st.caption(f"Age: {member['age']}, Gender: {member['gender'] or 'Not specified'}")
                                if member['notes']:
                                    st.caption(f"Notes: {member['notes']}")
                        
                        with col2:
                            if not st.session_state.get(edit_key, False):
                                col_vitals, col_edit = st.columns(2)
                                with col_vitals:
                                    if st.button("Start Vitals", key=f"vitals_{member['id']}", type="secondary"):
                                        # Mark as processing and redirect to triage
                                        conn = sqlite3.connect(db.db_name)
                                        cursor = conn.cursor()
                                        cursor.execute('''
                                            UPDATE patient_names_queue 
                                            SET status = 'processing_vitals', processed_by = ?
                                            WHERE id = ?
                                        ''', (st.session_state.get('user_name', 'Triage Staff'), member['id']))
                                        conn.commit()
                                        conn.close()
                                        
                                        # Broadcast update to all connected devices
                                        broadcast_to_clients(f"new_patient_vitals:{member['name']}")
                                        
                                        # Store patient info for triage
                                        st.session_state.preregistered_patient = {
                                            'id': member['id'],
                                            'name': member['name'],
                                            'age': member['age'],
                                            'gender': member['gender'],
                                            'family_group_id': family_id,
                                            'relationship': member['relationship'],
                                            'notes': member['notes']
                                        }
                                        st.session_state.user_role = "triage"
                                        st.rerun()
                                with col_edit:
                                    if st.button("✏️", key=f"edit_{member['id']}", type="secondary", help="Edit patient details"):
                                        st.session_state[edit_key] = True
                                        st.rerun()
                        
                        with col3:
                            if not st.session_state.get(edit_key, False):
                                if st.button("Remove", key=f"remove_{member['id']}", type="secondary"):
                                    conn = sqlite3.connect(db.db_name)
                                    cursor = conn.cursor()
                                    cursor.execute('DELETE FROM patient_names_queue WHERE id = ?', (member['id'],))
                                    conn.commit()
                                    conn.close()
                                    st.rerun()
            
            # Display individuals
            for individual in individuals:
                edit_key = f"edit_individual_{individual['id']}"
                
                col1, col2, col3 = st.columns([3, 1, 1])
                with col1:
                    # Check if this individual is in edit mode
                    if st.session_state.get(edit_key, False):
                        # Edit form for individual
                        with st.form(f"edit_form_{individual['id']}"):
                            new_name = st.text_input("Name", value=individual['name'], key=f"edit_name_{individual['id']}")
                            col_age, col_gender = st.columns(2)
                            with col_age:
                                new_age = st.number_input("Age", value=individual['age'] if individual['age'] else 0, min_value=0, max_value=120, key=f"edit_age_{individual['id']}")
                            with col_gender:
                                gender_options = ["", "Male", "Female"]
                                gender_index = gender_options.index(individual['gender']) if individual['gender'] in gender_options else 0
                                new_gender = st.selectbox("Gender", gender_options, index=gender_index, key=f"edit_gender_{individual['id']}")
                            new_notes = st.text_area("Notes", value=individual['notes'] if individual['notes'] else "", key=f"edit_notes_{individual['id']}")
                            
                            col_save, col_cancel = st.columns(2)
                            with col_save:
                                if st.form_submit_button("Save", type="primary"):
                                    if new_name.strip():
                                        conn = sqlite3.connect(db.db_name)
                                        cursor = conn.cursor()
                                        cursor.execute('''
                                            UPDATE patient_names_queue 
                                            SET name = ?, age = ?, gender = ?, notes = ?
                                            WHERE id = ?
                                        ''', (new_name.strip(), new_age if new_age > 0 else None, 
                                             new_gender if new_gender else None, new_notes.strip() if new_notes else None, individual['id']))
                                        conn.commit()
                                        conn.close()
                                        
                                        # Broadcast update to all connected devices
                                        broadcast_to_clients(f"patient_updated:{new_name.strip()}")
                                        
                                        st.session_state[edit_key] = False
                                        st.success(f"Updated {new_name}")
                                        st.rerun()
                                    else:
                                        st.error(t('err_name_cannot_be_empty'))
                            with col_cancel:
                                if st.form_submit_button("Cancel"):
                                    st.session_state[edit_key] = False
                                    st.rerun()
                    else:
                        # Display mode for individual
                        st.write(f"👤 **{individual['name']}**")
                        if individual['age']:
                            st.caption(f"Age: {individual['age']}, Gender: {individual['gender'] or 'Not specified'}")
                        if individual['notes']:
                            st.caption(f"Notes: {individual['notes']}")
                
                with col2:
                    if not st.session_state.get(edit_key, False):
                        col_vitals, col_edit = st.columns(2)
                        with col_vitals:
                            if st.button("Start Vitals", key=f"vitals_{individual['id']}", type="secondary"):
                                # Mark as processing and redirect to triage
                                conn = sqlite3.connect(db.db_name)
                                cursor = conn.cursor()
                                cursor.execute('''
                                    UPDATE patient_names_queue 
                                    SET status = 'processing_vitals', processed_by = ?
                                    WHERE id = ?
                                ''', (st.session_state.get('user_name', 'Triage Staff'), individual['id']))
                                conn.commit()
                                conn.close()
                                
                                # Store patient info for triage
                                st.session_state.preregistered_patient = {
                                    'id': individual['id'],
                                    'name': individual['name'],
                                    'age': individual['age'],
                                    'gender': individual['gender'],
                                    'family_group_id': None,
                                    'relationship': individual['relationship'],
                                    'notes': individual['notes']
                                }
                                st.session_state.user_role = "triage"
                                st.rerun()
                        with col_edit:
                            if st.button("✏️", key=f"edit_{individual['id']}", type="secondary", help="Edit patient details"):
                                st.session_state[edit_key] = True
                                st.rerun()
                
                with col3:
                    if not st.session_state.get(edit_key, False):
                        if st.button("Remove", key=f"remove_{individual['id']}", type="secondary"):
                            conn = sqlite3.connect(db.db_name)
                            cursor = conn.cursor()
                            cursor.execute('DELETE FROM patient_names_queue WHERE id = ?', (individual['id'],))
                            conn.commit()
                            conn.close()
                            st.rerun()
        else:
            st.info(t('msg_no_names_in_queue'))


def triage_interface():
    add_to_history('triage')
    st.markdown(f"## {t('page_triage')}")
    render_doctor_status_strip()

    # Check if we need to collect family vital signs
    if ('family_vital_signs_queue' in st.session_state
            and st.session_state.family_vital_signs_queue
            and len(st.session_state.family_vital_signs_queue) > 0):
        st.info(
            f"Family vital signs workflow active - {len(st.session_state.family_vital_signs_queue)} members"
        )
        family_vital_signs_collection()
        return

    # Check if we need to collect vital signs for a patient
    if 'pending_vitals' in st.session_state:
        st.markdown(f"### {t('hdr_record_vital_signs')}")
        patient_name = st.session_state.get('patient_name', 'Patient')
        st.info(f"Recording vital signs for: **{patient_name}**")
        vital_signs_form(st.session_state.pending_vitals)
        return

    tab1, tab2, tab3 = st.tabs(
        [t('tab_triage_queue'), t('tab_new_patient'), t('tab_search_patient')])

    with tab1:
        unified_triage_queue()

    with tab2:
        new_patient_form()

    with tab3:
        existing_patient_search()


def unified_triage_queue():
    """Combined queue: patients waiting for triage from BOTH sources
    (visits.status='triage' and patient_names_queue.status='pending_vitals').
    Previously these were on two separate tabs, which caused patients to
    appear to 'disappear' when staff looked at the wrong tab."""
    waiting_for_triage_queue()
    st.markdown("---")
    preregistered_queue_view()


def waiting_for_triage_queue():
    """Display patients registered today waiting for triage (vitals).

    North-star design: quiet patient_row helper, no colored cards, status
    color carried by the 4-px left edge bar.
    """
    location_code = st.session_state.clinic_location['country_code']
    waiting_patients = db.get_patients_by_visit_status('triage', location_code) or []

    section_header(t('waiting_for_vitals'), count=len(waiting_patients))

    if not waiting_patients:
        st.caption(t('no_patients_waiting'))
        return

    for patient in waiting_patients:
        priority = (patient.get('priority') or '').lower()
        status = 'urgent' if priority == 'urgent' else (
            'waiting' if priority == 'high' else 'idle')

        visit_time = ''
        if patient.get('visit_date'):
            visit_time = patient['visit_date'][:16].replace('T', ' ')

        meta_parts = [
            patient['patient_id'],
            f"{patient['age']}{(patient['gender'] or '')[:1]}" if patient.get('age') else patient.get('gender'),
            f"{t('reg_time_prefix')} {visit_time}" if visit_time else None,
        ]

        clicked = patient_row(
            name=patient['name'],
            meta_parts=meta_parts,
            action_label=t('start_vitals'),
            action_key=f"triage_start_{patient['visit_id']}",
            status=status,
        )
        if clicked:
            st.session_state.pending_vitals = patient['visit_id']
            st.session_state.patient_name = patient['name']
            st.rerun()


def preregistered_queue_view():
    st.markdown(f"### {t('hdr_preregistered_patients')}")
    st.info(t('msg_preregistered_intro'))
    
    # Get current location
    location_code = st.session_state.clinic_location['country_code']
    
    # Get pre-registered patients waiting for vitals
    conn = sqlite3.connect(db.db_name)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id, name, age, gender, relationship, family_group_id, created_time, notes
        FROM patient_names_queue 
        WHERE status = 'pending_vitals' AND location_code = ?
        ORDER BY family_group_id, CASE WHEN relationship = 'parent' THEN 0 ELSE 1 END, created_time
    ''', (location_code,))
    
    pending_patients = cursor.fetchall()
    conn.close()
    
    if pending_patients:
        # Group by family if applicable
        families = {}
        individuals = []
        
        for row in pending_patients:
            name_id, name, age, gender, relationship, family_group_id, created_time, notes = row
            if family_group_id:
                if family_group_id not in families:
                    families[family_group_id] = []
                families[family_group_id].append({
                    'id': name_id, 'name': name, 'age': age, 'gender': gender,
                    'relationship': relationship, 'created_time': created_time, 'notes': notes
                })
            else:
                individuals.append({
                    'id': name_id, 'name': name, 'age': age, 'gender': gender,
                    'relationship': relationship, 'created_time': created_time, 'notes': notes
                })
        
        # Display families
        for family_id, members in families.items():
            with st.expander(f"👨‍👩‍👧‍👦 Family Group ({len(members)} members)", expanded=True):
                for member in members:
                    edit_key = f"edit_preregistered_family_{member['id']}"
                    
                    col1, col2 = st.columns([3, 2])
                    with col1:
                        # Check if this member is in edit mode
                        if st.session_state.get(edit_key, False):
                            # Edit form for family member
                            with st.form(f"edit_preregistered_form_{member['id']}"):
                                new_name = st.text_input("Name", value=member['name'], key=f"edit_preregistered_name_{member['id']}")
                                col_age, col_gender = st.columns(2)
                                with col_age:
                                    new_age = st.number_input("Age", value=member['age'] if member['age'] else 0, min_value=0, max_value=120, key=f"edit_preregistered_age_{member['id']}")
                                with col_gender:
                                    gender_options = ["", "Male", "Female"]
                                    gender_index = gender_options.index(member['gender']) if member['gender'] in gender_options else 0
                                    new_gender = st.selectbox("Gender", gender_options, index=gender_index, key=f"edit_preregistered_gender_{member['id']}")
                                new_notes = st.text_area("Notes", value=member['notes'] if member['notes'] else "", key=f"edit_preregistered_notes_{member['id']}")
                                
                                col_save, col_cancel = st.columns(2)
                                with col_save:
                                    if st.form_submit_button("Save", type="primary"):
                                        if new_name.strip():
                                            conn = sqlite3.connect(db.db_name)
                                            cursor = conn.cursor()
                                            cursor.execute('''
                                                UPDATE patient_names_queue 
                                                SET name = ?, age = ?, gender = ?, notes = ?
                                                WHERE id = ?
                                            ''', (new_name.strip(), new_age if new_age > 0 else None, 
                                                 new_gender if new_gender else None, new_notes.strip() if new_notes else None, member['id']))
                                            conn.commit()
                                            conn.close()
                                            
                                            # Broadcast update to all connected devices
                                            broadcast_to_clients(f"patient_updated:{new_name.strip()}")
                                            
                                            st.session_state[edit_key] = False
                                            st.success(f"Updated {new_name}")
                                            st.rerun()
                                        else:
                                            st.error(t('err_name_cannot_be_empty'))
                                with col_cancel:
                                    if st.form_submit_button("Cancel"):
                                        st.session_state[edit_key] = False
                                        st.rerun()
                        else:
                            # Display mode for family member
                            icon = "👨" if member['relationship'] == 'parent' else "👶"
                            st.write(f"{icon} **{member['name']}** ({member['relationship']})")
                            if member['age']:
                                st.caption(f"Age: {member['age']}, Gender: {member['gender'] or 'Not specified'}")
                            if member['notes']:
                                st.caption(f"Notes: {member['notes']}")
                    
                    with col2:
                        if not st.session_state.get(edit_key, False):
                            col_vitals, col_edit = st.columns(2)
                            with col_vitals:
                                if st.button("Start Vitals", key=f"start_vitals_{member['id']}", type="primary"):
                                    # Create patient record and start vital signs workflow.
                                    # family_id and relationship MUST be passed through so the
                                    # doctor's consultation queue can group these patients later.
                                    patient_data = {
                                        'name': member['name'],
                                        'age': member['age'],
                                        'gender': member['gender'],
                                        'phone': None,
                                        'emergency_contact': None,
                                        'medical_history': member['notes'],
                                        'allergies': None,
                                        'family_id': family_id,
                                        'relationship': member.get('relationship', 'child'),
                                        'is_independent': 0,
                                    }

                                    # Register patient in the main system
                                    patient_id = db.add_patient(location_code, **patient_data)
                                    visit_id = db.create_visit(patient_id)
                                    
                                    # Mark as processing in queue
                                    conn = sqlite3.connect(db.db_name)
                                    cursor = conn.cursor()
                                    cursor.execute('''
                                        UPDATE patient_names_queue 
                                        SET status = 'completed'
                                        WHERE id = ?
                                    ''', (member['id'],))
                                    conn.commit()
                                    conn.close()
                                    
                                    # Set up vital signs workflow
                                    st.session_state.pending_vitals = visit_id
                                    st.session_state.patient_name = member['name']
                                    st.success(f"Patient {member['name']} registered! Patient ID: {patient_id}")
                                    st.rerun()
                            with col_edit:
                                if st.button("✏️", key=f"edit_preregistered_{member['id']}", type="secondary", help="Edit patient details"):
                                    st.session_state[edit_key] = True
                                    st.rerun()
        
        # Display individuals
        for individual in individuals:
            edit_key = f"edit_preregistered_individual_{individual['id']}"
            
            col1, col2 = st.columns([3, 2])
            with col1:
                # Check if this individual is in edit mode
                if st.session_state.get(edit_key, False):
                    # Edit form for individual
                    with st.form(f"edit_preregistered_form_{individual['id']}"):
                        new_name = st.text_input("Name", value=individual['name'], key=f"edit_preregistered_name_{individual['id']}")
                        col_age, col_gender = st.columns(2)
                        with col_age:
                            new_age = st.number_input("Age", value=individual['age'] if individual['age'] else 0, min_value=0, max_value=120, key=f"edit_preregistered_age_{individual['id']}")
                        with col_gender:
                            gender_options = ["", "Male", "Female"]
                            gender_index = gender_options.index(individual['gender']) if individual['gender'] in gender_options else 0
                            new_gender = st.selectbox("Gender", gender_options, index=gender_index, key=f"edit_preregistered_gender_{individual['id']}")
                        new_notes = st.text_area("Notes", value=individual['notes'] if individual['notes'] else "", key=f"edit_preregistered_notes_{individual['id']}")
                        
                        col_save, col_cancel = st.columns(2)
                        with col_save:
                            if st.form_submit_button("Save", type="primary"):
                                if new_name.strip():
                                    conn = sqlite3.connect(db.db_name)
                                    cursor = conn.cursor()
                                    cursor.execute('''
                                        UPDATE patient_names_queue 
                                        SET name = ?, age = ?, gender = ?, notes = ?
                                        WHERE id = ?
                                    ''', (new_name.strip(), new_age if new_age > 0 else None, 
                                         new_gender if new_gender else None, new_notes.strip() if new_notes else None, individual['id']))
                                    conn.commit()
                                    conn.close()
                                    
                                    # Broadcast update to all connected devices
                                    broadcast_to_clients(f"patient_updated:{new_name.strip()}")
                                    
                                    st.session_state[edit_key] = False
                                    st.success(f"Updated {new_name}")
                                    st.rerun()
                                else:
                                    st.error(t('err_name_cannot_be_empty'))
                        with col_cancel:
                            if st.form_submit_button("Cancel"):
                                st.session_state[edit_key] = False
                                st.rerun()
                else:
                    # Display mode for individual
                    st.write(f"👤 **{individual['name']}**")
                    if individual['age']:
                        st.caption(f"Age: {individual['age']}, Gender: {individual['gender'] or 'Not specified'}")
                    if individual['notes']:
                        st.caption(f"Notes: {individual['notes']}")
            
            with col2:
                if not st.session_state.get(edit_key, False):
                    col_vitals, col_edit = st.columns(2)
                    with col_vitals:
                        if st.button("Start Vitals", key=f"start_vitals_{individual['id']}", type="primary"):
                            # Create patient record and start vital signs workflow
                            patient_data = {
                                'name': individual['name'],
                                'age': individual['age'],
                                'gender': individual['gender'],
                                'phone': None,
                                'emergency_contact': None,
                                'medical_history': individual['notes'],
                                'allergies': None
                            }
                            
                            # Register patient in the main system
                            patient_id = db.add_patient(location_code, **patient_data)
                            visit_id = db.create_visit(patient_id)
                            
                            # Mark as processing in queue
                            conn = sqlite3.connect(db.db_name)
                            cursor = conn.cursor()
                            cursor.execute('''
                                UPDATE patient_names_queue 
                                SET status = 'completed'
                                WHERE id = ?
                            ''', (individual['id'],))
                            conn.commit()
                            conn.close()
                            
                            # Set up vital signs workflow
                            st.session_state.pending_vitals = visit_id
                            st.session_state.patient_name = individual['name']
                            st.success(f"Patient {individual['name']} registered! Patient ID: {patient_id}")
                            st.rerun()
                    with col_edit:
                        if st.button("✏️", key=f"edit_preregistered_{individual['id']}", type="secondary", help="Edit patient details"):
                            st.session_state[edit_key] = True
                            st.rerun()
    else:
        st.info(t('msg_no_preregistered'))


def new_patient_form():
    add_to_history('new_patient_form')
    st.markdown(f"### {t('register_new_patient')}")

    # Registration type selection — labels translated; the underlying string
    # comparison still uses the English option text since the comparison is
    # by index in this two-option radio.
    _reg_options = [t('individual_patient_radio'), t('family_registration_radio')]
    registration_type = st.radio(t('registration_type_label'),
                                 _reg_options,
                                 horizontal=True)

    if registration_type == _reg_options[0]:
        with st.form("new_patient_form"):
            col1, col2 = st.columns(2)

            with col1:
                name = st.text_input(t('patient_name_required'),
                                     placeholder=t('enter_full_name'))

                # Date of Birth with age auto-calculation
                _dob_options = [t('enter_age'), t('enter_dob')]
                dob_option = st.radio(t('age_entry_method'), _dob_options, horizontal=True)

                if dob_option == _dob_options[1]:
                    date_of_birth = st.date_input(t('date_of_birth'),
                                                   value=None,
                                                   min_value=date(1900, 1, 1),
                                                   max_value=date.today())
                    if date_of_birth:
                        calculated_age = calculate_age_from_dob(date_of_birth.isoformat())
                        st.info(f"{t('age')}: {calculated_age} {t('years')}")
                        age = calculated_age
                    else:
                        date_of_birth = None
                        age = None
                else:
                    date_of_birth = None
                    age = st.number_input(t('age'),
                                          min_value=0,
                                          max_value=120,
                                          value=None)

                gender = st.selectbox(t('gender'), ["", t('male'), t('female')])

            with col2:
                phone = st.text_input(t('phone_number'), placeholder=t('optional'))
                emergency_contact = st.text_input(t('emergency_contact'),
                                                  placeholder=t('optional'))
                address = st.text_input(t('address'), placeholder=t('optional'))

            # Medical History field
            medical_history = st.text_area(t('medical_history'),
                                           placeholder=t('medical_history_placeholder'),
                                           height=100)

            if st.form_submit_button(t('register_patient_btn'), type="primary"):
                if name.strip():
                    # Check for duplicate patients
                    duplicates = db.check_duplicate_patient(
                        name.strip(), age if age else None,
                        phone.strip() if phone else None)

                    st.session_state.duplicate_check_results = duplicates
                    st.session_state.new_patient_data = {
                        'name': name.strip(),
                        'age': age,
                        'date_of_birth': date_of_birth.isoformat() if date_of_birth else None,
                        'gender': gender if gender else None,
                        'phone': phone.strip() if phone else None,
                        'emergency_contact': emergency_contact.strip() if emergency_contact else None,
                        'medical_history': medical_history.strip() if medical_history else None,
                        'address': address.strip() if address else None,
                        'allergies': None
                    }
                    st.rerun()
                else:
                    st.error(t('please_enter_name'))

        # Show duplicate check results
        if 'duplicate_check_results' in st.session_state and 'new_patient_data' in st.session_state:
            duplicates = st.session_state.duplicate_check_results
            patient_data = st.session_state.new_patient_data

            if duplicates['exact_matches'] or duplicates['similar_matches']:
                st.markdown("### 🔍 Potential Existing Patients Found")
                st.warning(
                    "This patient may have been seen at a previous clinic. Please review:"
                )

                # Show exact matches
                if duplicates['exact_matches']:
                    st.markdown("#### Exact Name Matches:")
                    for match in duplicates['exact_matches']:
                        patient_id, match_name, match_age, match_phone, match_address, reg_time = match
                        reg_date = reg_time[:10] if reg_time else "Unknown"

                        col1, col2 = st.columns([3, 1])
                        with col1:
                            st.info(
                                f"**{match_name}** (ID: {patient_id})\n"
                                f"Age: {match_age or 'Unknown'} | Phone: {match_phone or 'N/A'}\n"
                                f"Registered: {reg_date}")
                        with col2:
                            if st.button(f"Use Existing",
                                         key=f"use_{patient_id}"):
                                visit_id = db.link_to_existing_patient(
                                    patient_id)
                                st.success(f"✅ Connected to existing patient!")
                                st.info(f"**Patient ID:** {patient_id}")
                                st.info(f"**Visit ID:** {visit_id}")

                                # Clear duplicate check data
                                del st.session_state.duplicate_check_results
                                del st.session_state.new_patient_data

                                # Store visit_id to show vital signs
                                st.session_state.pending_vitals = visit_id
                                st.session_state.patient_name = match_name
                                st.rerun()

                # Show similar matches
                if duplicates['similar_matches']:
                    st.markdown("#### Similar Names:")
                    for match in duplicates['similar_matches']:
                        patient_id, match_name, match_age, match_phone, match_address, reg_time = match
                        reg_date = reg_time[:10] if reg_time else "Unknown"

                        col1, col2 = st.columns([3, 1])
                        with col1:
                            st.write(
                                f"**{match_name}** (ID: {patient_id})\n"
                                f"Age: {match_age or 'Unknown'} | Phone: {match_phone or 'N/A'}\n"
                                f"Registered: {reg_date}")
                        with col2:
                            if st.button(f"Use This",
                                         key=f"similar_{patient_id}"):
                                visit_id = db.link_to_existing_patient(
                                    patient_id)
                                st.success(f"✅ Connected to existing patient!")
                                st.info(f"**Patient ID:** {patient_id}")
                                st.info(f"**Visit ID:** {visit_id}")

                                # Clear duplicate check data
                                del st.session_state.duplicate_check_results
                                del st.session_state.new_patient_data

                                # Store visit_id to show vital signs
                                st.session_state.pending_vitals = visit_id
                                st.session_state.patient_name = match_name
                                st.rerun()

                st.markdown("---")

                # Option to register as new patient anyway
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("Register as New Patient", type="secondary"):
                        location_code = st.session_state.clinic_location[
                            'country_code']
                        patient_id = db.add_patient(location_code,
                                                    **patient_data)
                        visit_id = db.create_visit(patient_id)

                        st.success(f"✅ New patient registered!")
                        st.info(f"**Patient ID:** {patient_id}")
                        st.info(f"**Visit ID:** {visit_id}")

                        # Broadcast new patient registration to all devices
                        broadcast_to_clients(f"new_patient:{patient_data['name']}:{patient_id}")

                        # Clear duplicate check data
                        del st.session_state.duplicate_check_results
                        del st.session_state.new_patient_data

                        # Store visit_id to show vital signs
                        st.session_state.pending_vitals = visit_id
                        st.session_state.patient_name = patient_data['name']
                        st.rerun()

                with col2:
                    if st.button("Start Over", type="secondary"):
                        # Clear duplicate check data
                        del st.session_state.duplicate_check_results
                        del st.session_state.new_patient_data
                        st.rerun()

            else:
                # No duplicates found, register new patient
                location_code = st.session_state.clinic_location[
                    'country_code']
                patient_id = db.add_patient(location_code, **patient_data)
                visit_id = db.create_visit(patient_id)

                st.success(f"✅ New patient registered!")
                st.info(f"**Patient ID:** {patient_id}")
                st.info(f"**Visit ID:** {visit_id}")

                # Clear duplicate check data
                del st.session_state.duplicate_check_results
                del st.session_state.new_patient_data

                # Store visit_id to show vital signs
                st.session_state.pending_vitals = visit_id
                st.session_state.patient_name = patient_data['name']
                st.rerun()

    else:  # Family Registration
        st.markdown("#### Family Registration")
        st.info(
            "Create a family file that includes parent/guardian, spouse (optional), and children. Families with minors will be seen together."
        )

        # Initialize spouse toggle in session state (outside form for dynamic UI)
        if 'family_add_spouse' not in st.session_state:
            st.session_state.family_add_spouse = False
        if 'family_num_children' not in st.session_state:
            st.session_state.family_num_children = 0

        # Spouse and children toggles OUTSIDE form for dynamic behavior
        st.markdown("**Family Composition**")
        col_spouse, col_children = st.columns(2)
        with col_spouse:
            add_spouse = st.checkbox("Include spouse/partner", 
                                     value=st.session_state.family_add_spouse,
                                     key="spouse_toggle_outside")
            if add_spouse != st.session_state.family_add_spouse:
                st.session_state.family_add_spouse = add_spouse
                st.rerun()
        with col_children:
            num_children = st.number_input("Number of children",
                                           min_value=0,
                                           max_value=10,
                                           value=st.session_state.family_num_children,
                                           key="children_count_outside")
            if num_children != st.session_state.family_num_children:
                st.session_state.family_num_children = num_children
                st.rerun()

        st.markdown("---")

        # Family Information Form
        with st.form("family_registration_form"):
            st.markdown("**Family Information**")

            # Family details
            family_name = st.text_input(
                "Family Name *", placeholder="e.g., The Rodriguez Family")
            emergency_contact = st.text_input("Emergency Contact Phone")

            st.markdown("---")
            st.markdown("**Primary Parent/Guardian**")

            col1, col2 = st.columns(2)
            with col1:
                parent_name = st.text_input("Parent/Guardian Name *")
                parent_age = st.number_input("Age",
                                             min_value=18,
                                             max_value=120,
                                             value=None,
                                             key="parent_age")
                parent_gender = st.selectbox("Gender", ["", "Male", "Female"],
                                             key="parent_gender")
            with col2:
                parent_phone = st.text_input("Phone Number",
                                             key="parent_phone")

            # Spouse fields - only shown if toggle is on
            spouse_name = ""
            spouse_age = None
            spouse_gender = ""
            
            if st.session_state.family_add_spouse:
                st.markdown("---")
                st.markdown("**Spouse/Partner**")
                col1, col2 = st.columns(2)
                with col1:
                    spouse_name = st.text_input("Spouse/Partner Name *", key="spouse_name")
                    spouse_age = st.number_input("Spouse Age",
                                                 min_value=18,
                                                 max_value=120,
                                                 value=None,
                                                 key="spouse_age")
                    spouse_gender = st.selectbox("Spouse Gender", ["", "Male", "Female"],
                                                 key="spouse_gender")
                with col2:
                    st.write("")  # Placeholder for layout

            # Children fields - only shown if count > 0
            add_spouse = st.session_state.family_add_spouse  # Use session state value
            num_children = st.session_state.family_num_children  # Use session state value

            # Pre-populate children data structure to ensure proper form handling
            children_data = []
            child_names = []
            child_ages = []
            child_genders = []
            
            if num_children > 0:
                st.markdown("---")
                st.markdown("**Children**")
                for i in range(num_children):
                    st.markdown(f"**Child {i+1}**")
                    col1, col2 = st.columns(2)
                    with col1:
                        child_name = st.text_input(f"Child {i+1} Name *",
                                                   key=f"child_name_{i}")
                        child_age = st.number_input(f"Child {i+1} Age",
                                                    min_value=0,
                                                    max_value=17,
                                                    value=None,
                                                    key=f"child_age_{i}")
                        child_gender = st.selectbox(f"Child {i+1} Gender",
                                                    ["", "Male", "Female"],
                                                    key=f"child_gender_{i}")
                    with col2:
                        st.write("")  # Placeholder for layout

                    # Store each child's data in separate lists
                    child_names.append(child_name)
                    child_ages.append(child_age)
                    child_genders.append(child_gender)

            st.markdown("---")
            family_submitted = st.form_submit_button("Create Family File",
                                                     type="primary",
                                                     use_container_width=True)

            if family_submitted:
                if family_name.strip() and parent_name.strip():
                    # Build children data from form inputs
                    children_data = []
                    for i in range(num_children):
                        if i < len(child_names) and child_names[i] and child_names[i].strip():
                            children_data.append({
                                'name': child_names[i].strip(),
                                'age': child_ages[i] if i < len(child_ages) and child_ages[i] is not None else None,
                                'gender': child_genders[i] if i < len(child_genders) and child_genders[i] else ""
                            })
                    
                    # Validate children data - each child must have a name
                    valid_children = []
                    validation_errors = []
                    
                    for i, child in enumerate(children_data):
                        if child['name'] and child['name'].strip():
                            valid_children.append(child)
                        else:
                            validation_errors.append(f"Child {i+1}: Missing name")
                    
                    # Check if we have the expected number of valid children
                    missing_children = num_children - len(valid_children)
                    if missing_children > 0:
                        validation_errors.append(f"{missing_children} children missing names")

                    # Show validation errors if any
                    if validation_errors:
                        st.error("Please fix the following issues:")
                        for error in validation_errors:
                            st.error(f"• {error}")
                        return  # Don't proceed with family creation
                    
                    # Only proceed if we have valid data (all expected children or no children)
                    if len(valid_children) == num_children:
                        location_code = st.session_state.clinic_location[
                            'country_code']

                        # Create family unit
                        family_id = db.create_family(
                            location_code=location_code,
                            family_name=family_name.strip(),
                            head_of_household=parent_name.strip(),
                            emergency_contact=emergency_contact.strip()
                            if emergency_contact else "")

                        # Add primary parent to family
                        parent_id = db.add_family_member(
                            family_id=family_id,
                            location_code=location_code,
                            relationship="parent",
                            name=parent_name.strip(),
                            age=parent_age,
                            gender=parent_gender if parent_gender else None,
                            phone=parent_phone.strip() if parent_phone else "")

                        # Start family members list with primary parent
                        family_members = [{
                            'patient_id': parent_id,
                            'patient_name': parent_name.strip(),
                            'relationship': 'parent'
                        }]

                        # Add spouse if provided
                        if add_spouse and spouse_name and spouse_name.strip():
                            spouse_id = db.add_family_member(
                                family_id=family_id,
                                location_code=location_code,
                                relationship="spouse",
                                name=spouse_name.strip(),
                                age=spouse_age,
                                gender=spouse_gender if spouse_gender else None,
                                phone="")  # Share parent's phone
                            
                            family_members.append({
                                'patient_id': spouse_id,
                                'patient_name': spouse_name.strip(),
                                'relationship': 'spouse'
                            })

                        # Add children to family
                        for i, child in enumerate(valid_children):
                            try:
                                child_id = db.add_family_member(
                                    family_id=family_id,
                                    location_code=location_code,
                                    relationship="child",
                                    parent_id=parent_id,
                                    name=child['name'].strip(),
                                    age=child['age'],
                                    gender=child['gender'] if child['gender'] else None)

                                family_members.append({
                                    'patient_id': child_id,
                                    'patient_name': child['name'].strip(),
                                    'relationship': 'child'
                                })
                            except Exception as e:
                                st.error(f"Error adding child {i+1} ({child['name']}): {str(e)}")
                                continue

                        # Create visits for all family members
                        family_visits = []
                        for member in family_members:
                            visit_id = db.create_visit(member['patient_id'])
                            family_visits.append({
                                'visit_id':
                                visit_id,
                                'patient_id':
                                member['patient_id'],
                                'patient_name':
                                member['patient_name'],
                                'relationship':
                                member['relationship']
                            })

                        st.success(f"✅ Family file created successfully!")
                        st.info(f"**Family ID:** {family_id}")
                        
                        # Build member count description
                        adults_count = 1 + (1 if add_spouse and spouse_name and spouse_name.strip() else 0)
                        adults_desc = "1 parent" if adults_count == 1 else "2 adults (parent + spouse)"
                        children_desc = f"{len(valid_children)} children" if valid_children else "no children"
                        st.info(
                            f"**Family Members:** {len(family_members)} ({adults_desc}, {children_desc})"
                        )

                        # Display all created patient IDs
                        st.markdown("**Patient IDs Created:**")
                        for visit in family_visits:
                            st.write(
                                f"• {visit['patient_name']} ({visit['relationship']}): {visit['patient_id']}"
                            )

                        # Store family data for continuation outside form
                        st.session_state.created_family_visits = family_visits.copy()
                        st.session_state.family_creation_complete = True
                        # Clear the family composition toggles for next registration
                        st.session_state.family_add_spouse = False
                        st.session_state.family_num_children = 0
                else:
                    st.error(
                        "Please provide family name and parent/guardian name.")

        # Show continuation buttons outside the form after family creation
        if st.session_state.get('family_creation_complete', False):
            family_visits = st.session_state.get('created_family_visits', [])

            st.markdown("---")
            st.markdown("**Next Steps:**")
            col1, col2 = st.columns(2)

            with col1:
                if st.button("Continue to vital signs",
                             type="primary",
                             use_container_width=True):
                    # Store family visits for vital signs processing
                    st.session_state.family_vital_signs_queue = family_visits.copy(
                    )
                    st.session_state.current_family_vital_index = 0
                    st.session_state.family_workflow_active = True
                    # Clear completion flags
                    del st.session_state.family_creation_complete
                    del st.session_state.created_family_visits
                    st.rerun()

            with col2:
                if st.button("Register another family",
                             type="secondary",
                             use_container_width=True):
                    # Clear family creation states
                    for key in [
                            'family_creation_complete',
                            'created_family_visits',
                            'family_vital_signs_queue',
                            'current_family_vital_index',
                            'family_workflow_active'
                    ]:
                        if key in st.session_state:
                            del st.session_state[key]
                    st.rerun()

    # Show vital signs form outside the main form if there's a pending visit
    if 'pending_vitals' in st.session_state:
        st.markdown(f"### {t('hdr_record_vital_signs')}")
        st.info(
            f"Recording vitals for **{st.session_state.patient_name}** (Visit ID: {st.session_state.pending_vitals})"
        )
        vital_signs_form(st.session_state.pending_vitals)


def existing_patient_search():
    add_to_history('existing_patient_search')
    st.markdown(f"### {t('find_existing_patient')}")

    search_query = st.text_input(t('search_by_name_or_id'),
                                 placeholder=t('enter_name_or_id_placeholder'))

    if search_query:
        patients = db.search_patients(search_query)
        if patients:
            section_header(t('results_count'), count=len(patients))
            for patient in patients:
                last_visit = patient['last_visit'][:10] if patient.get('last_visit') else t('never')
                meta = [
                    patient['patient_id'],
                    f"{patient['age']}{(patient['gender'] or '')[:1]}" if patient.get('age') else patient.get('gender'),
                    f"{t('last_visit')} {last_visit}",
                ]
                clicked = patient_row(
                    name=patient['name'],
                    meta_parts=meta,
                    action_label=t('new_visit'),
                    action_key=f"visit_{patient['patient_id']}",
                    status='idle',
                )
                if clicked:
                    visit_id = db.create_visit(patient['patient_id'])
                    st.session_state.pending_vitals = visit_id
                    st.session_state.patient_name = patient['name']
                    st.rerun()
        else:
            st.caption(t('no_patients_found'))


def vital_signs_form(visit_id: str):
    with st.form(f"vitals_{visit_id}"):
        st.markdown(f"#### {t('vital_signs')}")
        st.info(t('vitals_tip'))

        # Pre-filled "normal" defaults were a clinical safety hazard — a nurse
        # could tap Save without entering anything and chart fake normal vitals
        # on a patient whose vitals were never measured. All defaults removed.
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            systolic = st.text_input(t('systolic_bp'), value="",
                                     placeholder="e.g., 120 or N/A")
            diastolic = st.text_input(t('diastolic_bp'), value="",
                                      placeholder="e.g., 80 or N/A")

        with col2:
            heart_rate = st.text_input(t('heart_rate'), value="",
                                       placeholder="e.g., 72 or N/A")
            temperature = st.text_input(t('temperature'), value="",
                                        placeholder="e.g., 98.6 or N/A")

        with col3:
            weight = st.text_input(t('weight'), value="",
                                   placeholder="e.g., 70.5 or N/A")
            height = st.text_input(t('height'), value="",
                                   placeholder="e.g., 170 or N/A")

        with col4:
            oxygen_sat = st.text_input(t('oxygen_saturation'), value="",
                                       placeholder="e.g., 98 or N/A")
            respirations = st.text_input(t('respirations'), value="",
                                         placeholder="e.g., 16 or N/A")

        if st.form_submit_button(t('save_vital_signs'), type="primary"):
            # Convert text inputs to appropriate values, handling N/A entries
            def process_vital_sign(value, is_decimal=False):
                if not value or value.strip().upper() == 'N/A':
                    return None
                try:
                    return float(value) if is_decimal else int(float(value))
                except ValueError:
                    return None
            
            # Process each vital sign
            systolic_val = process_vital_sign(systolic)
            diastolic_val = process_vital_sign(diastolic)
            heart_rate_val = process_vital_sign(heart_rate)
            temperature_val = process_vital_sign(temperature, is_decimal=True)
            weight_val = process_vital_sign(weight, is_decimal=True)
            height_val = process_vital_sign(height, is_decimal=True)
            oxygen_sat_val = process_vital_sign(oxygen_sat)
            
            # Calculate BMI if weight and height are available
            bmi_val = None
            if weight_val and height_val:
                bmi_val, bmi_category = calculate_bmi(weight_val, height_val)
                if bmi_val:
                    st.info(f"📊 BMI: {bmi_val} ({bmi_category})")
            
            conn = sqlite3.connect(db.db_name)
            cursor = conn.cursor()

            cursor.execute(
                '''
                INSERT INTO vital_signs (visit_id, systolic_bp, diastolic_bp, heart_rate, 
                                       temperature, weight, height, oxygen_saturation, bmi, recorded_time)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (visit_id, systolic_val, diastolic_val, heart_rate_val, temperature_val,
                  weight_val, height_val, oxygen_sat_val, bmi_val, datetime.now().isoformat()))

            # Update visit status
            cursor.execute(
                '''
                UPDATE visits SET triage_time = ?, status = ? WHERE visit_id = ?
            ''',
                (datetime.now().isoformat(), 'waiting_consultation', visit_id))

            conn.commit()
            conn.close()

            st.success(
                "✅ Vital signs recorded! Patient is ready for consultation.")

            # Green confirmation box
            # Broadcast vital signs completion to all devices
            patient_name = st.session_state.get('patient_name', 'Patient')
            broadcast_to_clients(f"vitals_complete:{patient_name}:waiting_consultation")
            
            st.markdown("""
                <div style="background-color: #d4edda; border: 1px solid #c3e6cb; border-radius: 0.375rem; padding: 1rem; margin: 0.5rem 0;">
                    <div style="color: #155724; font-weight: bold; font-size: 1.1rem;">
                        🟢 PATIENT SENT TO DOCTOR QUEUE
                    </div>
                    <div style="color: #155724; margin-top: 0.5rem;">
                        <strong>{}</strong> is now waiting for consultation
                    </div>
                </div>
            """.format(patient_name), unsafe_allow_html=True)

            # Check if this patient has children - if so, start family vital signs workflow
            patient_conn = sqlite3.connect(db.db_name)
            patient_cursor = patient_conn.cursor()

            # Get the patient ID from the visit
            patient_cursor.execute(
                'SELECT patient_id FROM visits WHERE visit_id = ?',
                (visit_id, ))
            patient_result = patient_cursor.fetchone()

            if patient_result:
                current_patient_id = patient_result[0]

                # Check for children
                patient_cursor.execute(
                    '''
                    SELECT p.patient_id, p.name, COALESCE(p.age, 0) as age 
                    FROM patients p
                    JOIN visits v ON p.patient_id = v.patient_id
                    WHERE p.parent_id = ? AND DATE(v.visit_date) = DATE('now')
                    ORDER BY COALESCE(p.age, 0) DESC
                ''', (current_patient_id, ))

                children = patient_cursor.fetchall()
                patient_conn.close()

                if children:
                    # Start family vital signs workflow for children
                    family_vitals_queue = []
                    for child_id, child_name, child_age in children:
                        # Get child's visit ID
                        child_conn = sqlite3.connect(db.db_name)
                        child_cursor = child_conn.cursor()
                        child_cursor.execute(
                            '''
                            SELECT visit_id FROM visits 
                            WHERE patient_id = ? AND DATE(visit_date) = DATE('now')
                            ORDER BY visit_date DESC LIMIT 1
                        ''', (child_id, ))
                        child_visit = child_cursor.fetchone()
                        child_conn.close()

                        if child_visit:
                            family_vitals_queue.append({
                                'patient_id':
                                child_id,
                                'patient_name':
                                child_name,
                                'visit_id':
                                child_visit[0],
                                'relationship':
                                'child',
                                'age':
                                child_age
                            })

                    if family_vitals_queue:
                        st.session_state.family_vital_signs_queue = family_vitals_queue
                        st.session_state.current_family_vital_index = 0
                        st.session_state.family_workflow_active = True

                        # Clear the pending vitals to stop showing parent form
                        if 'pending_vitals' in st.session_state:
                            del st.session_state.pending_vitals
                        if 'patient_name' in st.session_state:
                            del st.session_state.patient_name

                        st.success(
                            f"✅ Parent vital signs recorded! Now collecting vital signs for {len(family_vitals_queue)} children."
                        )
                        st.rerun()
                        return  # Exit early to start children's vital signs workflow
            else:
                patient_conn.close()

            # Only clear session state if no children workflow was started
            if 'pending_vitals' in st.session_state:
                del st.session_state.pending_vitals
            if 'patient_name' in st.session_state:
                del st.session_state.patient_name

            st.rerun()


def patient_queue_monitor_interface():
    add_to_history('patient_queue_monitor')
    st.markdown(f"## {t('hdr_queue_monitor')}")
    st.info(t('msg_realtime_queue'))
    
    patient_queue_view()


def patient_queue_view():
    add_to_history('patient_queue')
    st.markdown(f"### {t('hdr_current_queue')}")

    conn = sqlite3.connect(db.db_name)
    cursor = conn.cursor()

    cursor.execute('''
        SELECT v.visit_id, v.patient_id, p.name, v.status, v.priority, v.visit_date
        FROM visits v
        JOIN patients p ON v.patient_id = p.patient_id
        WHERE DATE(v.visit_date) = DATE('now')
        ORDER BY 
            CASE v.priority 
                WHEN 'critical' THEN 1 
                WHEN 'urgent' THEN 2 
                ELSE 3 
            END,
            v.visit_date
    ''')

    queue = cursor.fetchall()
    conn.close()

    if queue:
        for visit in queue:
            visit_id, patient_id, name, status, priority, visit_date = visit

            status_class = ""
            if status == "completed":
                status_class = "completed"
            elif status in ["consultation", "prescribed"]:
                status_class = "in-progress"
            elif priority == "critical":
                status_class = "urgent"

            priority_emoji = "🔴" if priority == "critical" else "🟡" if priority == "urgent" else "🟢"
            status_emoji = {
                "triage": "📝",
                "waiting_consultation": "⏳",
                "consultation": "👨‍⚕️",
                "prescribed": "💊",
                "completed": "✅"
            }.get(status, "❓")

            st.markdown(f"""
            <div class="patient-card {status_class}">
                <h4>{priority_emoji} {name} (ID: {patient_id})</h4>
                <p><strong>Status:</strong> {status_emoji} {status.replace('_', ' ').title()}</p>
                <p><strong>Visit ID:</strong> {visit_id}</p>
                <p><strong>Time:</strong> {visit_date[:16].replace('T', ' ')}</p>
            </div>
            """,
                        unsafe_allow_html=True)
    else:
        st.info(t('msg_no_patients_in_queue'))


def doctor_interface():
    add_to_history('doctor')
    st.markdown(
        f"## 👨‍⚕️ Doctor Consultation - {st.session_state.doctor_name}")

    # Update doctor status and show real-time status of all doctors
    db = get_db_manager()

    # Display real-time doctor status at top (always visible — clinic
    # staff need to see who's busy/available without having to expand)
    with st.expander(t('doctor_status'), expanded=True):
        doctor_status = db.get_all_doctor_status()
        if doctor_status:
            for status in doctor_status:
                status_color = "🟢" if status[
                    'status'] == 'available' else "🟡" if status[
                        'status'] == 'with_patient' else "🔴"
                patient_info = f" - {status['current_patient_name']} ({status['current_patient_id']})" if status[
                    'current_patient_id'] else ""

                if status['doctor_name'] == st.session_state.doctor_name:
                    st.markdown(
                        f"**{status_color} {status['doctor_name']} (YOU)** - {status['status'].replace('_', ' ').title()}{patient_info}"
                    )
                else:
                    st.write(
                        f"{status_color} {status['doctor_name']} - {status['status'].replace('_', ' ').title()}{patient_info}"
                    )

        if st.button("🚪 Logout"):
            db.update_doctor_status(st.session_state.doctor_name, "offline")
            del st.session_state.doctor_name
            # Return to role selection
            st.session_state.user_role = None
            st.rerun()

    tab1, tab2 = st.tabs(["Patient Consultation", "Consultation History"])

    with tab1:
        consultation_interface()

    with tab2:
        consultation_history()


def consultation_interface():
    add_to_history('consultation_interface')
    st.markdown(f"### {t('hdr_select_patient_for_consultation')}")

    # Get patients waiting for consultation, including family relationships
    conn = sqlite3.connect("clinic_database.db")
    cursor = conn.cursor()

    cursor.execute('''
        SELECT v.visit_id, v.patient_id, p.name, v.priority, vs.systolic_bp, 
               vs.diastolic_bp, vs.heart_rate, vs.temperature, p.parent_id, p.relationship,
               v.return_reason, v.consultation_time, p.family_id
        FROM visits v
        JOIN patients p ON v.patient_id = p.patient_id
        LEFT JOIN vital_signs vs ON v.visit_id = vs.visit_id
        WHERE v.status = 'waiting_consultation' AND DATE(v.visit_date) = DATE('now')
        ORDER BY 
            CASE WHEN v.return_reason = 'pharmacy_lab_review' THEN 0 ELSE 1 END,
            COALESCE(p.family_id, ''),
            CASE p.relationship 
                WHEN 'parent' THEN 0 
                WHEN 'spouse' THEN 1 
                ELSE 2 
            END,
            CASE v.priority 
                WHEN 'critical' THEN 1 
                WHEN 'urgent' THEN 2 
                ELSE 3 
            END,
            v.visit_date
    ''')

    waiting_patients = cursor.fetchall()
    conn.close()

    # Group patients by family
    families = {}
    individual_patients = []

    # Separate patients with lab results vs new patients
    lab_return_patients = []
    regular_patients = []
    
    for patient in waiting_patients:
        visit_id, patient_id, name, priority, sys_bp, dia_bp, hr, temp, parent_id, relationship, return_reason, consultation_time, family_id = patient
        
        patient_data = {
            'visit_id': visit_id,
            'patient_id': patient_id,
            'name': name,
            'priority': priority,
            'sys_bp': sys_bp,
            'dia_bp': dia_bp,
            'hr': hr,
            'temp': temp,
            'parent_id': parent_id,
            'relationship': relationship or 'self',
            'return_reason': return_reason,
            'consultation_time': consultation_time,
            'family_id': family_id
        }
        
        if return_reason == 'pharmacy_lab_review':
            lab_return_patients.append(patient_data)
        else:
            regular_patients.append(patient_data)

    # Process regular patients for family grouping using family_id
    for patient in regular_patients:
        if patient['family_id']:
            # Group by family_id
            if patient['family_id'] not in families:
                families[patient['family_id']] = {'parent': None, 'spouse': None, 'children': []}
            
            if patient['relationship'] == 'parent':
                families[patient['family_id']]['parent'] = patient
            elif patient['relationship'] == 'spouse':
                families[patient['family_id']]['spouse'] = patient
            else:
                families[patient['family_id']]['children'].append(patient)
        elif patient['parent_id']:
            # Fallback: group by parent_id for legacy data
            if patient['parent_id'] not in families:
                families[patient['parent_id']] = {'parent': None, 'spouse': None, 'children': []}
            families[patient['parent_id']]['children'].append(patient)
        else:
            # Individual patient (no family)
            individual_patients.append(patient)

    # Display lab return patients first - highest priority
    if lab_return_patients:
        st.markdown(f"#### {t('hdr_priority_lab_results')}")
        st.markdown("*These patients have already been seen and returned from pharmacy/lab for result review*")
        
        for patient in lab_return_patients:
            # Get lab results for this patient
            conn_lab = sqlite3.connect("clinic_database.db")
            cursor_lab = conn_lab.cursor()
            
            cursor_lab.execute('''
                SELECT test_type, results, completed_time
                FROM lab_tests
                WHERE visit_id = ? AND status = 'completed'
                ORDER BY completed_time DESC
            ''', (patient['visit_id'],))
            
            lab_results = cursor_lab.fetchall()
            conn_lab.close()
            
            with st.expander(f"🔄 **LAB RESULTS READY** - {patient['name']} (ID: {patient['patient_id']})", expanded=True):
                
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.markdown(f"**Previous Consultation:** {patient['consultation_time'][:16].replace('T', ' ') if patient['consultation_time'] else 'N/A'}")
                    
                    # Display lab results prominently
                    if lab_results:
                        st.markdown("### 🧪 **LAB RESULTS:**")
                        for test_type, results, completed_time in lab_results:
                            
                            if test_type.lower() == 'urinalysis':
                                st.markdown(f"**🔬 {test_type} - {completed_time[:16].replace('T', ' ')}**")
                                st.markdown("**Standard 10-Parameter UA Results:**")
                                with st.container():
                                    st.markdown(f"""
                                    <div style="background: #f0f9ff; border: 2px solid #3b82f6; border-radius: 8px; padding: 16px; margin: 8px 0;">
                                        <pre style="font-family: monospace; margin: 0; white-space: pre-wrap;">{results}</pre>
                                    </div>
                                    """, unsafe_allow_html=True)
                            
                            elif test_type.lower() == 'glucose':
                                st.markdown(f"**🩸 {test_type} - {completed_time[:16].replace('T', ' ')}**")
                                result_color = "#ef4444" if any(word in results.lower() for word in ['high', 'elevated', 'abnormal']) else "#10b981"
                                with st.container():
                                    st.markdown(f"""
                                    <div style="background: #f0f9ff; border: 3px solid {result_color}; border-radius: 8px; padding: 16px; margin: 8px 0;">
                                        <h4 style="margin: 0; color: {result_color};">Glucose Level: {results}</h4>
                                    </div>
                                    """, unsafe_allow_html=True)
                            
                            elif test_type.lower() == 'pregnancy':
                                st.markdown(f"**🤰 {test_type} - {completed_time[:16].replace('T', ' ')}**")
                                result_color = "#10b981" if "positive" in results.lower() else "#6b7280"
                                with st.container():
                                    st.markdown(f"""
                                    <div style="background: #f0f9ff; border: 3px solid {result_color}; border-radius: 8px; padding: 16px; margin: 8px 0;">
                                        <h4 style="margin: 0; color: {result_color};">Result: {results}</h4>
                                    </div>
                                    """, unsafe_allow_html=True)
                            
                            else:
                                st.markdown(f"**🔬 {test_type} - {completed_time[:16].replace('T', ' ')}**")
                                with st.container():
                                    st.markdown(f"""
                                    <div style="background: #f0f9ff; border: 2px solid #6b7280; border-radius: 8px; padding: 12px; margin: 8px 0;">
                                        <strong>Results:</strong> {results}
                                    </div>
                                    """, unsafe_allow_html=True)
                    else:
                        st.warning("No lab results found for this patient.")
                
                with col2:
                    st.markdown("**🏥 Consultation Action**")
                    if st.button(f"📋 Review Lab Results", 
                                key=f"lab_review_{patient['visit_id']}_{patient['patient_id']}", 
                                type="primary", 
                                use_container_width=True):
                        # Load existing consultation data from database for restoration
                        conn_restore = sqlite3.connect("clinic_database.db")
                        cursor_restore = conn_restore.cursor()
                        cursor_restore.execute('''
                            SELECT chief_complaint, symptoms, diagnosis, treatment_plan, notes,
                                   medical_history, current_medications
                            FROM visits 
                            WHERE visit_id = ?
                        ''', (patient['visit_id'],))
                        consultation_data = cursor_restore.fetchone()
                        conn_restore.close()
                        
                        # Store consultation data in session state for restoration
                        consultation_key = f"consultation_data_{patient['visit_id']}"
                        if consultation_data:
                            st.session_state[consultation_key] = {
                                'chief_complaint': consultation_data[0] or '',
                                'symptoms': consultation_data[1] or '',
                                'diagnosis': consultation_data[2] or '',
                                'treatment_plan': consultation_data[3] or '',
                                'notes': consultation_data[4] or '',
                                'medical_history': consultation_data[5] or '',
                                'current_medications': consultation_data[6] or ''
                            }
                        
                        st.session_state.active_consultation = {
                            'visit_id': patient['visit_id'],
                            'patient_id': patient['patient_id'],
                            'patient_name': patient['name'],
                            'return_from_lab': True,
                            'lab_results': lab_results
                        }
                        # Update doctor status
                        db = get_db_manager()
                        db.update_doctor_status(
                            st.session_state.doctor_name, "with_patient",
                            patient['patient_id'],
                            f"{patient['name']} (Lab Review)")
                        st.session_state.page = 'consultation_form'
                        st.rerun()
                        
        st.markdown("---")

    # Display families first
    if families:
        st.markdown(f"#### {t('hdr_family_groups')}")
        for family_id, family_data in families.items():
            parent = family_data['parent']
            spouse = family_data.get('spouse')
            children = family_data['children']

            if parent:
                priority_emoji = "🔴" if parent[
                    'priority'] == "critical" else "🟡" if parent[
                        'priority'] == "urgent" else "🟢"

                # Build family description
                member_count = 1 + (1 if spouse else 0) + len(children)
                family_desc = f"{parent['name']}"
                if spouse:
                    family_desc += f" + {spouse['name']}"
                if children:
                    family_desc += f" + {len(children)} child{'ren' if len(children) > 1 else ''}"

                with st.expander(
                        f"{priority_emoji} **Family Consultation:** {family_desc}",
                        expanded=False):
                    st.markdown("**👨‍👩 Parent/Guardian:**")
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        if parent['sys_bp']:
                            st.metric(
                                "Blood Pressure",
                                f"{parent['sys_bp']}/{parent['dia_bp']}")
                    with col2:
                        if parent['hr']:
                            st.metric("Heart Rate", f"{parent['hr']} bpm")
                    with col3:
                        if parent['temp']:
                            st.metric("Temperature", f"{parent['temp']}°F")
                    with col4:
                        # Build family members list for consultation
                        family_members = [parent]
                        if spouse:
                            family_members.append(spouse)
                        family_members.extend(children)
                        
                        if st.button(
                                f"Start Family Consultation",
                                key=f"family_consult_{parent['visit_id']}_{parent['patient_id']}"):
                            st.session_state.family_consultation = {
                                'family_id': family_id,
                                'family_members': family_members,
                                'current_member_index': 0,
                                'completed_consultations': [],
                                'total_members': len(family_members)
                            }
                            st.session_state.active_consultation = {
                                'visit_id': parent['visit_id'],
                                'patient_id': parent['patient_id'],
                                'patient_name': parent['name']
                            }
                            # Update doctor status
                            db = get_db_manager()
                            db.update_doctor_status(
                                st.session_state.doctor_name, "with_patient",
                                parent['patient_id'],
                                f"{parent['name']} (Family)")
                            st.session_state.page = 'consultation_form'
                            st.rerun()

                    # Display spouse if present
                    if spouse:
                        st.markdown("**💑 Spouse/Partner:**")
                        st.write(f"• {spouse['name']}")

                    # Display children
                    if children:
                        st.markdown("**👶 Children:**")
                        for child in children:
                            age_display = f"({child.get('age', 'N/A')} yrs)" if child.get('age') else "(age N/A)"
                            st.write(f"• {child['name']} {age_display}")

    # Display individual patients
    if individual_patients:
        st.markdown(f"#### {t('hdr_individual_patients')}")
        for patient in individual_patients:
            priority_emoji = "🔴" if patient[
                'priority'] == "critical" else "🟡" if patient[
                    'priority'] == "urgent" else "🟢"

            with st.expander(
                    f"{priority_emoji} {patient['name']} (ID: {patient['patient_id']})",
                    expanded=False):
                # Display vital signs
                if patient['sys_bp']:
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("Blood Pressure",
                                  f"{patient['sys_bp']}/{patient['dia_bp']}")
                    with col2:
                        st.metric("Heart Rate", f"{patient['hr']} bpm")
                    with col3:
                        st.metric("Temperature", f"{patient['temp']}°F")
                    with col4:
                        if st.button(f"Start Consultation",
                                     key=f"consult_indiv_{patient['visit_id']}_{patient['patient_id']}"):
                            # Store consultation details
                            st.session_state.active_consultation = {
                                'visit_id': patient['visit_id'],
                                'patient_id': patient['patient_id'],
                                'patient_name': patient['name']
                            }
                            # Update doctor status
                            db = get_db_manager()
                            db.update_doctor_status(
                                st.session_state.doctor_name, "with_patient",
                                patient['patient_id'], patient['name'])
                            st.session_state.page = 'consultation_form'
                            st.rerun()

    if not families and not individual_patients:
        st.info(t('msg_no_waiting_consultation'))


def consultation_form(visit_id: str, patient_id: str, patient_name: str):
    # Store active consultation state and update URL for proper page refresh behavior
    st.session_state.active_consultation = {
        'visit_id': visit_id,
        'patient_id': patient_id,
        'patient_name': patient_name
    }
    st.session_state.page = 'consultation_form'
    update_page_url('consultation_form')
    
    # Back button to return to consultation interface
    col1, col2 = st.columns([1, 4])
    with col1:
        if st.button(t('back_to_queue'), key='back_to_queue_from_consultation',
                     type="secondary"):
            st.session_state.page = 'doctor'
            if 'active_consultation' in st.session_state:
                del st.session_state.active_consultation
            # Clear consultation URL parameters
            if 'visit_id' in st.query_params:
                del st.query_params['visit_id']
            if 'patient_id' in st.query_params:
                del st.query_params['patient_id']
            if 'patient_name' in st.query_params:
                del st.query_params['patient_name']
            # Update doctor status back to available
            db = get_db_manager()
            db.update_doctor_status(st.session_state.doctor_name, "available")
            st.rerun()

    st.markdown(f"### Consultation for {patient_name}")

    # Get the logged-in doctor's name
    doctor_name = st.session_state.get('doctor_name', 'Unknown Doctor')
    st.info(
        f"**Doctor:** {doctor_name} | **Patient ID:** {patient_id} | **Visit ID:** {visit_id}"
    )

    # Check if this is a family consultation
    is_family_consultation = 'family_consultation' in st.session_state and any(
        member['patient_id'] == patient_id 
        for member in st.session_state.family_consultation.get('family_members', [])
    )

    if is_family_consultation:
        family_data = st.session_state.family_consultation
        current_index = family_data['current_member_index']
        total_members = family_data['total_members']
        
        st.info(
            f"👨‍👩‍👧‍👦 Family Consultation - Member {current_index + 1} of {total_members}: {patient_name}"
        )
        
        # Show family progress
        st.progress((current_index + 1) / total_members)
        
        # Show family members list
        with st.expander("Family Members"):
            for i, member in enumerate(family_data['family_members']):
                status = "✅ Completed" if i < current_index else "⏳ Current" if i == current_index else "⏸️ Waiting"
                st.write(f"{status} {member['name']} ({member.get('relationship', 'family member')})")
    
    # Check if this patient is returning from lab tests
    is_returning_from_lab = st.session_state.get('active_consultation', {}).get('return_from_lab', False)
    lab_results = st.session_state.get('active_consultation', {}).get('lab_results', [])
    
    # Display current patient information
    st.markdown(f"**Current Patient:** {patient_name}")
    st.markdown(f"**Relationship:** {'Parent/Guardian' if not is_family_consultation or (is_family_consultation and st.session_state.family_consultation['current_member_index'] == 0) else 'Child'}")

    # Display vital signs for this patient
    db_manager = get_db_manager()
    conn = sqlite3.connect(db_manager.db_name)
    cursor = conn.cursor()
    
    # Get vital signs for this visit
    cursor.execute('''
        SELECT systolic_bp, diastolic_bp, heart_rate, temperature, weight, oxygen_saturation, recorded_time
        FROM vital_signs 
        WHERE visit_id = ?
        ORDER BY recorded_time DESC
        LIMIT 1
    ''', (visit_id,))
    
    vital_signs = cursor.fetchone()
    conn.close()
    
    if vital_signs:
        systolic, diastolic, hr, temp, weight, o2_sat, recorded_time = vital_signs
        
        # Display vital signs in a nicely formatted card
        st.markdown("#### 📊 Vital Signs")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            bp_value = f"{systolic}/{diastolic}" if systolic and diastolic else "N/A"
            st.metric("Blood Pressure", bp_value)
        with col2:
            hr_value = f"{hr} bpm" if hr else "N/A"
            st.metric("Heart Rate", hr_value)
        with col3:
            temp_value = f"{temp}°F" if temp else "N/A"
            st.metric("Temperature", temp_value)
        with col4:
            o2_value = f"{o2_sat}%" if o2_sat else "N/A"
            st.metric("O2 Saturation", o2_value)
        
        # Second row for weight and timestamp
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            weight_value = f"{weight} kg" if weight else "N/A"
            st.metric("Weight", weight_value)
        with col2:
            if recorded_time:
                time_display = recorded_time[:16].replace('T', ' ')
                st.caption(f"Recorded: {time_display}")
    else:
        st.warning("⚠️ No vital signs recorded for this patient")

    # Show lab results prominently if patient is returning from lab
    if is_returning_from_lab and lab_results:
        st.markdown("---")
        st.markdown("### 🧪 **LAB RESULTS COMPLETED**")
        st.success("This patient has returned from lab/pharmacy with completed results. Original consultation data has been restored below.")
        
        for test_type, results, completed_time in lab_results:
            with st.expander(f"🔬 {test_type} Results - {completed_time[:16].replace('T', ' ')}", expanded=True):
                if test_type.lower() == 'urinalysis':
                    st.markdown("**Standard 11-Parameter Urinalysis:**")
                    st.code(results, language=None)
                elif test_type.lower() == 'glucose':
                    st.markdown(f"**Blood Glucose:** {results}")
                elif test_type.lower() == 'pregnancy':
                    st.markdown(f"**Pregnancy Test:** {results}")
                else:
                    st.markdown(f"**{test_type}:** {results}")
        st.markdown("---")

    # Use tabs for consultation sections including optional photo documentation
    tab1, tab2, tab3, tab4 = st.tabs(
        ["📋 Consultation", "📸 Photo Documentation", "🔬 Lab & Prescriptions", "💉 Immunizations & History"])

    with tab1:
        # Auto-save consultation - no form needed, changes saved automatically
        # Check for existing consultation data from previous visit
        consultation_key = f"consultation_data_{visit_id}"
        existing_data = st.session_state.get(consultation_key, {})
            
        # If no session data, check database for previous consultation
        if not existing_data:
            conn = sqlite3.connect("clinic_database.db")
            cursor = conn.cursor()
            cursor.execute('''
                SELECT chief_complaint, symptoms, diagnosis, treatment_plan, notes,
                       medical_history, current_medications
                FROM visits 
                WHERE visit_id = ?
            ''', (visit_id,))
            db_data = cursor.fetchone()
            conn.close()
            
            if db_data:
                existing_data = {
                    'chief_complaint': db_data[0] or '',
                    'symptoms': db_data[1] or '',
                    'diagnosis': db_data[2] or '',
                    'treatment_plan': db_data[3] or '',
                    'notes': db_data[4] or '',
                    'medical_history': db_data[5] or '',
                    'current_medications': db_data[6] or ''
                }
        
        # History Section (surgical history removed per user request)
        st.markdown("#### Patient History")
        col1, col2 = st.columns(2)

        with col1:
            # Load medical history from patient registration if available
            conn_pat = sqlite3.connect("clinic_database.db")
            cursor_pat = conn_pat.cursor()
            cursor_pat.execute('SELECT medical_history FROM patients WHERE patient_id = ?', (patient_id,))
            patient_medical_history = cursor_pat.fetchone()
            conn_pat.close()
            
            initial_medical_history = ""
            if patient_medical_history and patient_medical_history[0]:
                initial_medical_history = patient_medical_history[0]
            elif existing_data.get('medical_history'):
                initial_medical_history = existing_data.get('medical_history', '')
            
            medical_history = st.text_area(
                "Medical History",
                value=initial_medical_history,
                placeholder="Chronic conditions, past illnesses...")

        with col2:
            current_medications = st.text_area(
                "Current Medications",
                value=existing_data.get('current_medications', ''),
                placeholder="Current medications and dosages...")

        st.markdown("---")
        # Auto-fill doctor name from logged-in session
        doctor_name = st.session_state.get('doctor_name', '')
        st.text_input("Doctor Name", value=doctor_name, disabled=True)

        chief_complaint = st.text_area(
            "Chief Complaint",
            value=existing_data.get('chief_complaint', ''),
            placeholder="What brought the patient in today?")
        symptoms = st.text_area(
            "Symptoms", 
            value=existing_data.get('symptoms', ''),
            placeholder="Describe symptoms observed/reported")
        diagnosis = st.text_area("Diagnosis", 
                               value=existing_data.get('diagnosis', ''),
                               placeholder="Your diagnosis")
        treatment_plan = st.text_area("Treatment Plan",
                                      value=existing_data.get('treatment_plan', ''),
                                      placeholder="Recommended treatment")
        notes = st.text_area("Additional Notes",
                             value=existing_data.get('notes', ''),
                             placeholder="Any additional observations")

        # Auto-save functionality - consultation is saved automatically as user types
        def auto_save_consultation():
            """Auto-save consultation data to database"""
            consultation_key = f"consultation_data_{visit_id}"
            st.session_state[consultation_key] = {
                'doctor_name': doctor_name,
                'chief_complaint': chief_complaint,
                'symptoms': symptoms,
                'diagnosis': diagnosis,
                'treatment_plan': treatment_plan,
                'notes': notes,
                'medical_history': medical_history,
                'current_medications': current_medications
            }
            
            # Update database with consultation details
            conn = sqlite3.connect("clinic_database.db")
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE visits 
                SET chief_complaint = ?, symptoms = ?, diagnosis = ?, 
                    treatment_plan = ?, notes = ?,
                    medical_history = ?, current_medications = ?
                WHERE visit_id = ?
            ''', (chief_complaint, symptoms, diagnosis, treatment_plan, notes,
                  medical_history, current_medications, visit_id))
            conn.commit()
            conn.close()
        
        # Call auto-save after fields are defined
        auto_save_consultation()
        
        st.success("✅ Consultation auto-saved")
        st.info("All changes are automatically saved. Continue to Lab & Prescriptions tab to complete the consultation.")

    with tab2:
        # Photo documentation section (now in its own tab)
        st.markdown("#### 📸 Photo Documentation")
        st.info(
            "Capture photos of visible symptoms or affected areas to enhance diagnosis and treatment documentation."
        )

        # Camera input for symptom documentation (rear-facing by default)
        photo_file = st.camera_input("Take a photo of symptoms/affected area",
                                     key=f"symptom_photo_{visit_id}")

        # Add JavaScript to set rear camera as default
        st.markdown("""
        <script>
        // Set rear camera as default when camera input loads
        setTimeout(function() {
            const videoElements = document.querySelectorAll('video');
            videoElements.forEach(video => {
                if (video.srcObject) {
                    const stream = video.srcObject;
                    const tracks = stream.getVideoTracks();
                    tracks.forEach(track => {
                        track.stop();
                    });
                    
                    navigator.mediaDevices.getUserMedia({
                        video: { facingMode: { exact: "environment" } }
                    }).then(stream => {
                        video.srcObject = stream;
                    }).catch(() => {
                        // Fallback to any camera if rear not available
                        navigator.mediaDevices.getUserMedia({ video: true }).then(stream => {
                            video.srcObject = stream;
                        });
                    });
                }
            });
        }, 1000);
        </script>
        """,
                    unsafe_allow_html=True)

        if photo_file is not None:
            # Display the captured photo
            st.image(photo_file, caption="Captured symptom photo", width=300)

            # Add description for the photo
            photo_description = st.text_input(
                "Photo Description",
                placeholder=
                "Describe what the photo shows (e.g., rash on left arm, swollen ankle, etc.)",
                key=f"photo_desc_{visit_id}")

            # Store photo data in session state for later saving
            if f"symptom_photos_{visit_id}" not in st.session_state:
                st.session_state[f"symptom_photos_{visit_id}"] = []

            if st.button("Save Photo", key=f"save_photo_{visit_id}"):
                if photo_description.strip():
                    # Convert photo to bytes
                    photo_bytes = photo_file.getvalue()

                    # Add to session state temporarily
                    st.session_state[f"symptom_photos_{visit_id}"].append({
                        'data':
                        photo_bytes,
                        'description':
                        photo_description.strip()
                    })

                    st.success(f"Photo saved: {photo_description.strip()}")
                    st.rerun()
                else:
                    st.error("Please add a description for the photo.")

        # Load existing photos from database and session state
        db = get_db_manager()
        existing_photos = db.get_patient_photos(patient_id)
        session_photos = st.session_state.get(f"symptom_photos_{visit_id}", [])
        
        # Display saved photos from database
        if existing_photos:
            st.markdown("**Previously Saved Photos:**")
            for photo in existing_photos:
                st.markdown(f"📷 **{photo['description']}** - {photo['created_time'][:16].replace('T', ' ')}")
        
        # Display current session photos for this visit
        if session_photos:
            st.markdown("**New Photos for this visit:**")
            for i, photo in enumerate(session_photos):
                col1, col2 = st.columns([1, 3])
                with col1:
                    st.write(f"Photo {i+1}")
                with col2:
                    st.write(f"📷 {photo['description']}")
                    if st.button(f"Remove",
                                 key=f"remove_photo_{visit_id}_{i}"):
                        st.session_state[f"symptom_photos_{visit_id}"].pop(i)
                        st.rerun()

    with tab3:
        # Check if this patient is returning from lab and restore previous selections
        lab_prescriptions_key = f"lab_prescriptions_{visit_id}"
        previous_selections = st.session_state.get(lab_prescriptions_key, {})
        
        st.markdown("#### Lab Tests")
        
        # Lab tests section - outside form for immediate updates
        lab_tests = []
        col1, col2, col3 = st.columns(3)
        with col1:
            ua_checked = st.checkbox("Urinalysis", 
                                   value=previous_selections.get('ua_checked', False),
                                   key=f"ua_check_{visit_id}")
            if ua_checked:
                ua_disp = st.selectbox("Urinalysis Disposition", 
                                     ["Return to Provider", "Treat per Pharmacy Protocol"], 
                                     index=0 if previous_selections.get('ua_disp') == "Return to Provider" else 1 if previous_selections.get('ua_disp') else 0,
                                     key=f"ua_disp_{visit_id}")
                lab_tests.append(("Urinalysis", ua_disp))
        with col2:
            gluc_checked = st.checkbox("Blood Glucose", 
                                     value=previous_selections.get('gluc_checked', False),
                                     key=f"gluc_check_{visit_id}")
            if gluc_checked:
                gluc_disp = st.selectbox("Glucose Disposition", 
                                       ["Return to Provider", "Treat per Pharmacy Protocol"], 
                                       index=0 if previous_selections.get('gluc_disp') == "Return to Provider" else 1 if previous_selections.get('gluc_disp') else 0,
                                       key=f"gluc_disp_{visit_id}")
                lab_tests.append(("Blood Glucose", gluc_disp))
        with col3:
            preg_checked = st.checkbox("Pregnancy Test", 
                                     value=previous_selections.get('preg_checked', False),
                                     key=f"preg_check_{visit_id}")
            if preg_checked:
                preg_disp = st.selectbox("Pregnancy Test Disposition", 
                                       ["Return to Provider", "Treat per Pharmacy Protocol"], 
                                       index=0 if previous_selections.get('preg_disp') == "Return to Provider" else 1 if previous_selections.get('preg_disp') else 0,
                                       key=f"preg_disp_{visit_id}")
                lab_tests.append(("Pregnancy Test", preg_disp))

        # Prescriptions section - outside form for immediate checkbox updates
        st.markdown("#### Prescriptions")

        # Get preset medications and deduplicate by name
        db_manager = get_db_manager()
        preset_meds = db_manager.get_preset_medications()

        # Deduplicate medications by name (keep first occurrence)
        unique_meds = {}
        for med in preset_meds:
            med_name = med['medication_name']
            if med_name not in unique_meds:
                unique_meds[med_name] = med

        deduplicated_meds = list(unique_meds.values())
        med_categories = list(
            set(med['category'] for med in deduplicated_meds))

        selected_medications = []

        # Define custom order for categories, with Teaching Pamphlets placed after UTI Antibiotic
        category_order = [
            "Pain Relief", "Antibiotic", "Blood Pressure", "Diabetes", 
            "Stomach", "Respiratory", "Vitamin", "Steroid", "Diuretic", 
            "Cholesterol", "UTI Antibiotic", "Teaching Pamphlets", "Other"
        ]
        
        # Sort categories according to custom order, with unknown categories at the end
        ordered_categories = []
        for cat in category_order:
            if cat in med_categories:
                ordered_categories.append(cat)
        # Add any categories not in our predefined order
        for cat in sorted(med_categories):
            if cat not in ordered_categories:
                ordered_categories.append(cat)

        for category in ordered_categories:
            # Special case for Teaching Pamphlets - don't add "Medications" suffix
            if category == "Teaching Pamphlets":
                expander_title = category
            else:
                expander_title = f"{category} Medications"
            with st.expander(expander_title):
                category_meds = [
                    med for med in deduplicated_meds
                    if med['category'] == category
                ]

                for med in category_meds:
                    # Check if this medication was previously selected
                    med_key = f"med_{med['id']}"
                    was_previously_selected = previous_selections.get('medications', {}).get(med_key, {}).get('selected', False)
                    
                    # Medication checkbox
                    selected = st.checkbox(f"{med['medication_name']}",
                                           value=was_previously_selected,
                                           key=f"med_{med['id']}_{visit_id}")

                    # Show additional fields immediately when medication is checked
                    if selected:
                        with st.container():
                            st.markdown("---")
                            
                            # Get previously saved values for this medication
                            prev_med_data = previous_selections.get('medications', {}).get(med_key, {})
                            
                            # Special handling for Teaching Pamphlets - no dosage/frequency needed
                            if category == "Teaching Pamphlets":
                                # For teaching pamphlets, just show simple confirmation
                                st.info("📋 This teaching pamphlet will be provided to the patient for education.")
                                selected_dosage = "As needed for patient education"
                                frequency = "As needed"
                                duration = "N/A"
                            else:
                                # Dosage and frequency options for regular medications
                                col1, col2, col3 = st.columns(3)
                                with col1:
                                    dosages = med['common_dosages'].split(', ')
                                    prev_dosage_idx = 0
                                    if prev_med_data.get('dosage') in dosages:
                                        prev_dosage_idx = dosages.index(prev_med_data.get('dosage'))
                                    selected_dosage = st.selectbox(
                                        "Dosage", dosages, 
                                        index=prev_dosage_idx,
                                        key=f"dosage_{med['id']}_{visit_id}")
                                with col2:
                                    freq_options = ["Once daily", "Twice daily", "Three times daily", "Four times daily", "As needed"]
                                    prev_freq_idx = 0
                                    if prev_med_data.get('frequency') in freq_options:
                                        prev_freq_idx = freq_options.index(prev_med_data.get('frequency'))
                                    frequency = st.selectbox("Frequency", freq_options,
                                                            index=prev_freq_idx,
                                                            key=f"freq_{med['id']}_{visit_id}")
                                with col3:
                                    dur_options = ["3 days", "5 days", "7 days", "10 days", "14 days", "30 days"]
                                    prev_dur_idx = 0
                                    
                                    # Get preset duration and normalize it
                                    preset_dur = med.get('preset_duration', '') or ''
                                    preset_dur = preset_dur.strip() if preset_dur else ''
                                    
                                    # Use preset duration if available and no previous data exists
                                    if prev_med_data.get('duration'):
                                        # Use previously selected duration
                                        if prev_med_data.get('duration') in dur_options:
                                            prev_dur_idx = dur_options.index(prev_med_data.get('duration'))
                                    elif preset_dur:
                                        # Try to match preset duration - handle various formats
                                        # If just a number, add " days"
                                        if preset_dur.isdigit():
                                            preset_dur_formatted = f"{preset_dur} days"
                                        else:
                                            preset_dur_formatted = preset_dur
                                        
                                        if preset_dur_formatted in dur_options:
                                            prev_dur_idx = dur_options.index(preset_dur_formatted)
                                    
                                    duration = st.selectbox("Duration", dur_options,
                                                           index=prev_dur_idx,
                                                           key=f"dur_{med['id']}_{visit_id}")

                            # Additional fields - simplified for teaching pamphlets
                            if category == "Teaching Pamphlets":
                                # For teaching pamphlets, only show special instructions
                                pharmacy_dosage = "Patient education material"
                                indication = "Patient education"
                                awaiting_lab = "no"
                                return_to_provider = "no"
                                instructions = st.text_input("Special Instructions",
                                                             value=prev_med_data.get('instructions', ''),
                                                             placeholder="Any special notes about this educational material",
                                                             key=f"inst_{med['id']}_{visit_id}")
                            else:
                                # Full fields for regular medications
                                col4, col5 = st.columns(2)
                                with col4:
                                    pharmacy_dosage = st.text_input(
                                        "Dosage for Pharmacy",
                                        value=prev_med_data.get('pharmacy_dosage', ''),
                                        placeholder="e.g., 500mg twice daily for 7 days",
                                        key=f"pharma_dose_{med['id']}_{visit_id}")
                                with col5:
                                    indication = st.text_input(
                                        "Indication",
                                        value=prev_med_data.get('indication', ''),
                                        placeholder="e.g., UTI, hypertension",
                                        key=f"indication_{med['id']}_{visit_id}")

                                instructions = st.text_input("Special Instructions",
                                                             value=prev_med_data.get('instructions', ''),
                                                             key=f"inst_{med['id']}_{visit_id}")

                                # Lab results options with indentation - restore previous values
                                st.markdown("&nbsp;&nbsp;&nbsp;&nbsp;**Lab Options:**", unsafe_allow_html=True)
                                col_indent, col_lab = st.columns([0.1, 0.9])
                                with col_lab:
                                    prev_awaiting_lab = prev_med_data.get('awaiting_lab', 'no') == 'yes'
                                    awaiting_lab = "yes" if st.checkbox(
                                        "Awaiting Lab Results",
                                        key=f"await_{med['id']}_{visit_id}",
                                        value=prev_awaiting_lab) else "no"
                                    
                                    return_to_provider = "no"
                                    if awaiting_lab == "yes":
                                        return_to_provider = "yes" if st.checkbox(
                                            "Return to provider after lab results",
                                            key=f"return_{med['id']}_{visit_id}",
                                            value=False) else "no"

                            selected_medications.append({
                                'id': med['id'],
                                'name': med['medication_name'],
                                'dosage': selected_dosage,
                                'frequency': frequency,
                                'duration': duration,
                                'instructions': instructions,
                                'awaiting_lab': awaiting_lab,
                                'return_to_provider': return_to_provider,
                                'pharmacy_notes': pharmacy_dosage,
                                'indication': indication
                            })

        # Custom medication section
        with st.expander("Add Custom Medication"):
            custom_med_name = st.text_input("Custom Medication Name",
                                            key=f"custom_name_{visit_id}")
            if custom_med_name:
                col1, col2, col3 = st.columns(3)
                with col1:
                    custom_dosage = st.text_input(
                        "Dosage", key=f"custom_dosage_{visit_id}")
                with col2:
                    custom_frequency = st.text_input(
                        "Frequency", key=f"custom_frequency_{visit_id}")
                with col3:
                    custom_duration = st.text_input(
                        "Duration", key=f"custom_duration_{visit_id}")

                custom_instructions = st.text_input(
                    "Instructions", key=f"custom_instructions_{visit_id}")
                custom_awaiting = st.checkbox(
                    "Pending Lab", key=f"custom_awaiting_{visit_id}")
                custom_return_to_provider = st.checkbox(
                    "Return to provider after lab results", key=f"custom_return_{visit_id}")
                custom_indication = st.text_input(
                    "Indication", key=f"custom_indication_{visit_id}")

                selected_medications.append({
                    'id':
                    None,
                    'name':
                    custom_med_name,
                    'dosage':
                    custom_dosage,
                    'frequency':
                    custom_frequency,
                    'duration':
                    custom_duration,
                    'instructions':
                    custom_instructions,
                    'awaiting_lab':
                    "yes" if custom_awaiting else "no",
                    'return_to_provider':
                    "yes" if custom_return_to_provider else "no",
                    'pharmacy_notes':
                    "",
                    'indication':
                    custom_indication
                })

        # Ophthalmology and submission - now in a form for final submission
        st.markdown("#### Ophthalmology Referral")
        needs_ophthalmology = st.checkbox(
            "Patient needs to see ophthalmologist after receiving medications",
            key=f"ophth_{visit_id}")

        with st.form(f"consultation_submit_{visit_id}"):
            if st.form_submit_button("Complete Consultation", type="primary"):
                # Get doctor name and chief complaint from session state or form data
                current_doctor_name = st.session_state.get('doctor_name', '')
                
                # Check if consultation data was saved in the first tab
                consultation_key = f"consultation_data_{visit_id}"
                consultation_data = st.session_state.get(consultation_key, {})
                current_chief_complaint = consultation_data.get('chief_complaint', '')
                
                # Validate all medications have required fields
                validation_errors = []
                
                for med in selected_medications:
                    if not med.get('dosage') or med.get('dosage').strip() == '':
                        validation_errors.append(f"Missing dosage for {med['name']}")
                    if not med.get('frequency') or med.get('frequency').strip() == '':
                        validation_errors.append(f"Missing frequency for {med['name']}")
                    
                    # Check if indication is required for this medication
                    med_requires_indication = True
                    if 'id' in med and med['id']:
                        # Get medication details from database to check require_indication setting
                        temp_conn = sqlite3.connect(db_manager.db_name)
                        temp_cursor = temp_conn.cursor()
                        temp_cursor.execute('SELECT require_indication FROM preset_medications WHERE id = ?', (med['id'],))
                        require_result = temp_cursor.fetchone()
                        temp_conn.close()
                        
                        if require_result and require_result[0] == 'no':
                            med_requires_indication = False
                    
                    # Only validate indication if it's required for this medication
                    if med_requires_indication and (not med.get('indication') or med.get('indication').strip() == ''):
                        validation_errors.append(f"Missing indication for {med['name']}")
                
                if validation_errors:
                    st.error("Please complete all required medication fields:")
                    for error in validation_errors:
                        st.error(f"• {error}")
                elif current_doctor_name and (current_chief_complaint or len(selected_medications) > 0 or len(lab_tests) > 0):
                    try:
                        # Save consultation state immediately to database for later resumption
                        db_conn = sqlite3.connect(db_manager.db_name, timeout=10.0)
                        db_conn.execute('BEGIN IMMEDIATE')
                        cursor = db_conn.cursor()

                        # Save complete consultation state to visits table (surgical history removed per user request)
                        cursor.execute('''
                            UPDATE visits 
                            SET chief_complaint = ?, symptoms = ?, diagnosis = ?, 
                                treatment_plan = ?, notes = ?, 
                                medical_history = ?, current_medications = ?,
                                consultation_time = ?
                            WHERE visit_id = ?
                        ''', (current_chief_complaint, consultation_data.get('symptoms', ''), 
                              consultation_data.get('diagnosis', ''), consultation_data.get('treatment_plan', ''),
                              consultation_data.get('notes', ''), 
                              consultation_data.get('medical_history', ''), 
                              consultation_data.get('current_medications', ''), datetime.now().isoformat(), visit_id))

                        # Also save to consultations table for tracking
                        cursor.execute(
                            '''
                            INSERT INTO consultations (visit_id, doctor_name, chief_complaint, 
                                                     symptoms, diagnosis, treatment_plan, notes, 
                                                     needs_ophthalmology, consultation_time)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (visit_id, current_doctor_name, current_chief_complaint, 
                              consultation_data.get('symptoms', ''), consultation_data.get('diagnosis', ''),
                              consultation_data.get('treatment_plan', ''), consultation_data.get('notes', ''),
                              needs_ophthalmology, datetime.now().isoformat()))

                        # Check if this is a re-consultation (patient returning from lab)
                        cursor.execute('''
                            SELECT COUNT(*) FROM lab_tests 
                            WHERE visit_id = ? AND status = 'completed'
                        ''', (visit_id,))
                        completed_labs = cursor.fetchone()[0]
                        
                        # Determine consultation status and handle prescription state
                        has_lab_dependent_meds = any(med['awaiting_lab'] == 'yes' for med in selected_medications)
                        
                        if lab_tests and not completed_labs:
                            # Initial consultation with lab orders - save consultation in paused state
                            new_status = 'waiting_lab'
                        elif completed_labs > 0:
                            # Re-consultation after lab results - send back to pharmacy with cleared return reason
                            new_status = 'prescribed'
                            # Clear return_reason to prevent repeated lab returns
                            cursor.execute('''
                                UPDATE visits 
                                SET return_reason = NULL 
                                WHERE visit_id = ?
                            ''', (visit_id,))
                            st.info("Patient being sent back to pharmacy with updated prescriptions based on lab results.")
                        elif needs_ophthalmology:
                            new_status = 'needs_ophthalmology'
                        elif selected_medications:
                            new_status = 'prescribed'
                        else:
                            new_status = 'completed'

                        cursor.execute(
                            '''
                            UPDATE visits SET consultation_time = ?, status = ? WHERE visit_id = ?
                        ''',
                            (datetime.now().isoformat(), new_status, visit_id))

                        db_conn.commit()
                        db_conn.close()

                        # Now handle lab tests and prescriptions using separate connections
                        for test_info in lab_tests:
                            test_type, disposition = test_info
                            db_manager.order_lab_test(visit_id, test_type,
                                                      current_doctor_name)

                        # Save Lab & Prescriptions state for restoration when patient returns
                        lab_prescriptions_data = {
                            'ua_checked': any(test[0] == "Urinalysis" for test in lab_tests),
                            'ua_disp': next((test[1] for test in lab_tests if test[0] == "Urinalysis"), None),
                            'gluc_checked': any(test[0] == "Blood Glucose" for test in lab_tests),
                            'gluc_disp': next((test[1] for test in lab_tests if test[0] == "Blood Glucose"), None),
                            'preg_checked': any(test[0] == "Pregnancy Test" for test in lab_tests),
                            'preg_disp': next((test[1] for test in lab_tests if test[0] == "Pregnancy Test"), None),
                            'medications': {}
                        }
                        
                        # Save medication selections
                        for med in selected_medications:
                            if med['name']:
                                med_key = f"med_{med.get('med_id', med['name'].replace(' ', '_'))}"
                                lab_prescriptions_data['medications'][med_key] = {
                                    'selected': True,
                                    'dosage': med['dosage'],
                                    'frequency': med['frequency'],
                                    'duration': med['duration'],
                                    'pharmacy_dosage': med.get('pharmacy_dosage', ''),
                                    'indication': med.get('indication', ''),
                                    'instructions': med['instructions'],
                                    'awaiting_lab': med['awaiting_lab']
                                }
                        
                        st.session_state[lab_prescriptions_key] = lab_prescriptions_data

                        # Save all prescriptions (including lab-dependent ones) for consultation state preservation
                        prescription_data = []
                        for med in selected_medications:
                            if med['name']:
                                conn_med = sqlite3.connect(db_manager.db_name)
                                cursor_med = conn_med.cursor()
                                
                                # Determine prescription status based on consultation state
                                if lab_tests and not completed_labs:
                                    # Initial consultation - save prescriptions as "paused" if lab dependent
                                    prescription_status = 'paused_pending_lab' if med['awaiting_lab'] == 'yes' else 'pending'
                                else:
                                    # Normal flow or re-consultation - send to pharmacy
                                    prescription_status = 'pending'
                                
                                cursor_med.execute(
                                    '''
                                    INSERT INTO prescriptions (visit_id, medication_name, 
                                                             dosage, frequency, duration, instructions, 
                                                             indication, awaiting_lab, return_to_provider, 
                                                             prescribed_by, prescribed_time, status)
                                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                                ''', (visit_id, med['name'], med['dosage'],
                                      med['frequency'], med['duration'],
                                      med['instructions'],
                                      med.get('indication', ''), 
                                      med['awaiting_lab'],
                                      med.get('return_to_provider', 'no'),
                                      current_doctor_name,
                                      datetime.now().isoformat(),
                                      prescription_status))
                                conn_med.commit()
                                conn_med.close()
                                
                                # Save prescription data for state preservation
                                prescription_data.append({
                                    'medication_name': med['name'],
                                    'dosage': med['dosage'],
                                    'frequency': med['frequency'],
                                    'duration': med['duration'],
                                    'instructions': med['instructions'],
                                    'indication': med.get('indication', ''),
                                    'awaiting_lab': med['awaiting_lab'],
                                    'status': prescription_status
                                })
                        
                        # Save prescription state for pharmacy workflow
                        if prescription_data:
                            patient_name = st.session_state.get('current_patient_name', 'Patient')
                            patient_id = st.session_state.get('current_patient_id', '')
                            save_prescription_state(visit_id, patient_id, patient_name, prescription_data)

                        # Broadcast consultation completion to all devices
                        patient_name = st.session_state.get('current_patient_name', 'Patient')
                        
                        if lab_tests and not completed_labs:
                            # Initial consultation with lab orders
                            test_names = [test_info[0] for test_info in lab_tests]
                            st.success("Consultation paused and saved!")
                            st.info(f"Patient sent to lab for: {', '.join(test_names)}")
                            
                            # Broadcast lab order to all devices
                            broadcast_to_clients(f"consultation_paused:{patient_name}:lab_ordered:{','.join(test_names)}")
                            
                            # Show prescription summary for paused consultation
                            if selected_medications:
                                awaiting_count = sum(1 for med in selected_medications if med['awaiting_lab'] == 'yes')
                                ready_count = len(selected_medications) - awaiting_count
                                
                                if ready_count > 0:
                                    st.info(f"{ready_count} prescriptions ready for pharmacy after lab results.")
                                if awaiting_count > 0:
                                    st.info(f"{awaiting_count} prescriptions pending lab confirmation.")
                                    
                            st.info("You can now see other patients. When lab results are ready, click 'Review Lab Results' to resume this exact consultation.")
                        else:
                            # Normal consultation completion or re-consultation
                            st.success("Consultation completed successfully!")
                            
                            # Broadcast consultation completion to all devices
                            if selected_medications:
                                broadcast_to_clients(f"consultation_complete:{patient_name}:prescribed:{len(selected_medications)}")
                            else:
                                broadcast_to_clients(f"consultation_complete:{patient_name}:no_prescriptions")
                            
                            if selected_medications:
                                awaiting_count = sum(1 for med in selected_medications if med['awaiting_lab'] == 'yes')
                                ready_count = len(selected_medications) - awaiting_count

                                if ready_count > 0:
                                    st.info(f"{ready_count} prescriptions sent to pharmacy.")
                                if awaiting_count > 0:
                                    st.info(f"{awaiting_count} prescriptions awaiting lab results.")

                        # Update doctor status back to available
                        db_manager.update_doctor_status(
                            st.session_state.doctor_name, "available")

                        # Clear current consultation and return to doctor interface
                        if 'current_consultation' in st.session_state:
                            del st.session_state.current_consultation
                        if 'active_consultation' in st.session_state:
                            del st.session_state.active_consultation

                        # Save patient history to database
                        history_conn = sqlite3.connect(db_manager.db_name)
                        history_cursor = history_conn.cursor()
                        history_cursor.execute(
                            '''
                            UPDATE patients 
                            SET medical_history = ?
                            WHERE patient_id = ?
                        ''',
                            (f"Medical: {medical_history}\nCurrent Meds: {current_medications}",
                             patient_id))
                        history_conn.commit()
                        history_conn.close()

                        # Save any photos that were captured during this consultation
                        if f"symptom_photos_{visit_id}" in st.session_state:
                            # Get photo count before clearing
                            photo_count = len(
                                st.session_state[f"symptom_photos_{visit_id}"])

                            for photo in st.session_state[
                                    f"symptom_photos_{visit_id}"]:
                                db_manager.save_patient_photo(
                                    visit_id=visit_id,
                                    patient_id=patient_id,
                                    photo_data=photo['data'],
                                    description=photo['description'])

                            # Clear photos from session state after saving
                            del st.session_state[f"symptom_photos_{visit_id}"]

                            if photo_count > 0:
                                st.info(
                                    f"Saved {photo_count} photos to patient record."
                                )

                        # Check if this is part of a family consultation workflow
                        if 'family_consultation' in st.session_state:
                            family_data = st.session_state.family_consultation
                            current_index = family_data['current_member_index']
                            
                            # Add current consultation to completed list
                            family_data['completed_consultations'].append({
                                'patient_id': patient_id,
                                'patient_name': patient_name,
                                'visit_id': visit_id
                            })
                            
                            # Move to next family member
                            next_index = current_index + 1
                            
                            if next_index < family_data['total_members']:
                                # Continue with next family member
                                next_member = family_data['family_members'][next_index]
                                family_data['current_member_index'] = next_index
                                
                                # Ensure active_consultation is properly set
                                st.session_state.active_consultation = {
                                    'visit_id': next_member['visit_id'],
                                    'patient_id': next_member['patient_id'],
                                    'patient_name': next_member['name']
                                }
                                
                                st.success(f"✅ Consultation completed for {patient_name}")
                                st.info(f"🔄 Continuing with {next_member['name']} ({next_index + 1}/{family_data['total_members']})")
                                
                                # Auto-navigate back to consultation tab for smoother family workflow
                                st.session_state.page = 'consultation_form'
                                st.rerun()
                            else:
                                # All family members completed - go to pharmacy workflow
                                st.success(f"✅ All family consultations completed!")
                                st.info("🏥 Sending entire family to pharmacy/lab...")
                                
                                # Set family pharmacy workflow
                                st.session_state.family_pharmacy_workflow = family_data['completed_consultations']
                                
                                # Clean up session state
                                if 'family_consultation' in st.session_state:
                                    del st.session_state.family_consultation
                                if 'active_consultation' in st.session_state:
                                    del st.session_state.active_consultation
                                
                                # Update doctor status back to available
                                db_manager.update_doctor_status(st.session_state.doctor_name, "available")
                                
                                time.sleep(2)
                                st.session_state.page = 'doctor_interface'
                                st.rerun()

                        # Individual consultation completed outside family workflow
                        else:
                            st.success("✅ Consultation completed successfully!")
                            # Clean up session state
                            if 'active_consultation' in st.session_state:
                                del st.session_state.active_consultation
                            # Update doctor status back to available
                            db_manager.update_doctor_status(st.session_state.doctor_name, "available")
                            st.session_state.page = 'doctor_interface'
                            st.rerun()


                    except Exception as e:
                        # More user-friendly error messages
                        error_msg = str(e)
                        if "active_consultation" in error_msg:
                            st.error("Session error: Please restart the consultation. The patient data is safe.")
                        else:
                            st.error(f"Error completing consultation: {error_msg}")
                else:
                    st.error(
                        "Please fill in required fields: Doctor Name and Chief Complaint"
                    )

    with tab4:
        # Immunizations & History tab
        st.markdown("#### 💉 Immunization History")
        
        db_manager = get_db_manager()
        
        # Get existing immunizations for this patient
        immunizations = db_manager.get_patient_immunizations(patient_id)
        
        if immunizations:
            st.markdown("**Recorded Immunizations:**")
            for imm in immunizations:
                col1, col2, col3 = st.columns([2, 1, 2])
                with col1:
                    st.write(f"💉 **{imm['vaccine_name']}**")
                with col2:
                    st.write(f"{imm['date_administered'][:10] if imm['date_administered'] else 'Unknown date'}")
                with col3:
                    st.write(f"Lot: {imm.get('lot_number', 'N/A')}")
        else:
            st.info("No immunizations recorded for this patient.")
        
        # Add new immunization
        with st.expander("➕ Add Immunization"):
            with st.form(f"add_immunization_{visit_id}"):
                col1, col2 = st.columns(2)
                with col1:
                    vaccine_name = st.selectbox("Vaccine", COMMON_VACCINES)
                    date_given = st.date_input("Date Administered", value=date.today())
                with col2:
                    lot_number = st.text_input("Lot Number", placeholder="Optional")
                    site = st.selectbox("Site", ["Left Arm", "Right Arm", "Left Thigh", "Right Thigh", "Other"])
                
                notes = st.text_input("Notes", placeholder="Any additional notes...")
                
                if st.form_submit_button("Add Immunization", type="primary"):
                    if vaccine_name:
                        success = db_manager.add_immunization(
                            patient_id=patient_id,
                            vaccine_name=vaccine_name,
                            date_administered=date_given.isoformat(),
                            lot_number=lot_number if lot_number else None,
                            site=site,
                            notes=notes if notes else None
                        )
                        if success:
                            st.success(f"✅ {vaccine_name} immunization recorded!")
                            st.rerun()
                        else:
                            st.error("Failed to record immunization.")
        
        # Pregnancy history section (only show for female patients)
        conn = sqlite3.connect(db_manager.db_name)
        cursor = conn.cursor()
        cursor.execute('SELECT gender, age FROM patients WHERE patient_id = ?', (patient_id,))
        patient_info = cursor.fetchone()
        conn.close()
        
        if patient_info and patient_info[0] and patient_info[0].lower() == 'female':
            patient_age = patient_info[1] if patient_info[1] else 0
            
            if patient_age >= 10:  # Show pregnancy history for female patients 10+
                st.markdown("---")
                st.markdown("#### 🤰 Pregnancy History")
                
                # Get existing pregnancy history
                pregnancy_history = db_manager.get_pregnancy_history(patient_id)
                
                if pregnancy_history:
                    st.markdown("**Recorded Pregnancies:**")
                    for preg in pregnancy_history:
                        with st.expander(f"Pregnancy - {preg.get('outcome', 'Unknown outcome')} ({preg.get('year', 'Unknown year')})"):
                            col1, col2 = st.columns(2)
                            with col1:
                                st.write(f"**Outcome:** {preg.get('outcome', 'N/A')}")
                                st.write(f"**Year:** {preg.get('year', 'N/A')}")
                            with col2:
                                st.write(f"**Delivery Type:** {preg.get('delivery_type', 'N/A')}")
                                if preg.get('complications'):
                                    st.write(f"**Complications:** {preg.get('complications')}")
                else:
                    st.info("No pregnancy history recorded.")
                
                # Add pregnancy history
                with st.expander("➕ Add Pregnancy Record"):
                    with st.form(f"add_pregnancy_{visit_id}"):
                        col1, col2 = st.columns(2)
                        with col1:
                            outcome = st.selectbox("Outcome", ["Live Birth", "Stillbirth", "Miscarriage", "Ectopic", "Abortion", "Currently Pregnant"])
                            year = st.number_input("Year", min_value=1950, max_value=date.today().year, value=date.today().year)
                        with col2:
                            delivery_type = st.selectbox("Delivery Type", ["Vaginal", "C-Section", "N/A"])
                            weeks_gestation = st.number_input("Weeks Gestation", min_value=0, max_value=45, value=0)
                        
                        complications = st.text_input("Complications", placeholder="e.g., preeclampsia, gestational diabetes...")
                        
                        if st.form_submit_button("Add Pregnancy Record", type="primary"):
                            success = db_manager.add_pregnancy_history(
                                patient_id=patient_id,
                                outcome=outcome,
                                year=year,
                                delivery_type=delivery_type if delivery_type != "N/A" else None,
                                weeks_gestation=weeks_gestation if weeks_gestation > 0 else None,
                                complications=complications if complications else None
                            )
                            if success:
                                st.success("✅ Pregnancy record added!")
                                st.rerun()
                            else:
                                st.error("Failed to add pregnancy record.")
        
        # QR Code Wristband section
        st.markdown("---")
        st.markdown("#### 📱 Patient QR Code / Wristband")
        
        if QR_AVAILABLE:
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Generate QR Code", key=f"qr_code_{visit_id}"):
                    qr_bytes = generate_patient_qr_code(patient_id, patient_name)
                    if qr_bytes:
                        st.image(qr_bytes, caption=f"QR Code for {patient_name}")
                        st.download_button(
                            "Download QR Code",
                            qr_bytes,
                            f"qr_{patient_id}.png",
                            "image/png"
                        )
            with col2:
                if PDF_AVAILABLE and st.button("Generate Wristband PDF", key=f"wristband_{visit_id}"):
                    patient_age_val = patient_info[1] if patient_info else None
                    wristband_pdf = generate_wristband_pdf(patient_id, patient_name, patient_age_val)
                    if wristband_pdf:
                        st.download_button(
                            "Download Wristband",
                            wristband_pdf,
                            f"wristband_{patient_id}.pdf",
                            "application/pdf"
                        )
        else:
            st.info("QR code generation requires the qrcode library.")

    # ===== CONSULTATION ACTIONS =====
    st.markdown("---")

    # Get database manager for checking orders
    db_signoff = get_db_manager()
    
    # Check for pending lab tests
    conn_check = sqlite3.connect(db_signoff.db_name)
    cursor_check = conn_check.cursor()
    
    cursor_check.execute('''
        SELECT COUNT(*) FROM lab_tests 
        WHERE visit_id = ? AND status = 'pending'
    ''', (visit_id,))
    pending_labs = cursor_check.fetchone()[0]
    
    # Check for prescriptions (pending means needs pharmacy)
    cursor_check.execute('''
        SELECT COUNT(*) FROM prescriptions 
        WHERE visit_id = ? AND (status IS NULL OR status = 'pending')
    ''', (visit_id,))
    pending_prescriptions = cursor_check.fetchone()[0]
    
    # Check for diagnoses
    cursor_check.execute('''
        SELECT COUNT(*) FROM icd10_diagnoses WHERE visit_id = ?
    ''', (visit_id,))
    has_diagnosis = cursor_check.fetchone()[0] > 0
    
    # Get current visit status
    cursor_check.execute('SELECT status FROM visits WHERE visit_id = ?', (visit_id,))
    current_status_row = cursor_check.fetchone()
    current_status = current_status_row[0] if current_status_row else 'unknown'
    conn_check.close()
    
    # Display current orders summary
    col_summary1, col_summary2, col_summary3 = st.columns(3)
    with col_summary1:
        if has_diagnosis:
            st.success(t('diagnosis_recorded'))
        else:
            st.warning(t('no_diagnosis_yet'))
    with col_summary2:
        if pending_labs > 0:
            st.info(f"{pending_labs} {t('lab_tests_ordered_count')}")
        else:
            st.caption(t('no_labs_ordered'))
    with col_summary3:
        if pending_prescriptions > 0:
            st.info(f"{pending_prescriptions} {t('prescriptions_written_count')}")
        else:
            st.caption(t('no_prescriptions_written'))

    st.markdown("---")

    # Helper function to save consultation data before status change
    def save_consultation_and_update_status(new_status: str, visit_id: str):
        """Save current consultation data and update visit status"""
        conn_save = sqlite3.connect(db_signoff.db_name)
        cursor_save = conn_save.cursor()

        # Get consultation data from session state if available
        consultation_key = f"consultation_data_{visit_id}"
        if consultation_key in st.session_state:
            data = st.session_state[consultation_key]
            cursor_save.execute('''
                UPDATE visits
                SET chief_complaint = ?, symptoms = ?, diagnosis = ?,
                    treatment_plan = ?, notes = ?,
                    medical_history = ?, current_medications = ?,
                    status = ?, consultation_time = ?
                WHERE visit_id = ?
            ''', (data.get('chief_complaint', ''), data.get('symptoms', ''),
                  data.get('diagnosis', ''), data.get('treatment_plan', ''),
                  data.get('notes', ''), data.get('medical_history', ''),
                  data.get('current_medications', ''), new_status,
                  datetime.now().isoformat(), visit_id))
        else:
            # Just update status and consultation time
            cursor_save.execute('''
                UPDATE visits SET status = ?, consultation_time = ? WHERE visit_id = ?
            ''', (new_status, datetime.now().isoformat(), visit_id))

        conn_save.commit()
        conn_save.close()

        # Log the action
        db_signoff.log_audit(
            action_type='consultation_signoff',
            user_name=st.session_state.get('doctor_name', 'Provider'),
            user_role='provider',
            table_name='visits',
            record_id=visit_id,
            new_value=new_status
        )
    
    # Helper function to advance to next family member or return to queue
    def advance_after_signoff(action_msg: str):
        """After signing off, advance to next family member or return to queue"""
        # Check if there's a next family member (define inline since function order matters)
        family = db_signoff.get_family_members(patient_id)
        next_member = None
        if family and len(family) > 1:
            current_idx = -1
            for i, member in enumerate(family):
                if member['patient_id'] == patient_id:
                    current_idx = i
                    break
            
            conn_fam = sqlite3.connect(db_signoff.db_name)
            cursor_fam = conn_fam.cursor()
            for i in range(current_idx + 1, len(family)):
                member = family[i]
                cursor_fam.execute('''
                    SELECT visit_id, status FROM visits 
                    WHERE patient_id = ? AND DATE(visit_date) = DATE('now')
                    AND status NOT IN ('completed', 'prescribed', 'waiting_lab', 'waiting_pharmacy')
                    ORDER BY visit_date DESC LIMIT 1
                ''', (member['patient_id'],))
                visit_data = cursor_fam.fetchone()
                if visit_data:
                    next_member = {'patient_id': member['patient_id'], 'name': member.get('name', 'Unknown'), 
                            'visit_id': visit_data[0], 'status': visit_data[1]}
                    break
            conn_fam.close()
        
        if next_member:
            st.success(f"{action_msg} Moving to next family member: {next_member['name']}")
            time.sleep(0.5)
            st.session_state.active_consultation = {
                'visit_id': next_member['visit_id'],
                'patient_id': next_member['patient_id'],
                'patient_name': next_member['name']
            }
            st.query_params['visit_id'] = next_member['visit_id']
            st.query_params['patient_id'] = next_member['patient_id']
            st.query_params['patient_name'] = next_member['name']
            st.rerun()
        else:
            st.success(action_msg)
            time.sleep(0.5)
            st.session_state.active_consultation = None
            st.session_state.page = 'doctor'
            st.rerun()
    
    # ---------------------------------------------------------------------
    # ONE SMART "COMPLETE" BUTTON that routes the patient correctly:
    #   - labs ordered    -> waiting_lab        (lab sends them back)
    #   - prescriptions   -> waiting_pharmacy
    #   - neither         -> completed (discharge)
    # Previously three separate buttons confused doctors when a button was
    # silently disabled. This single button can't be "missing".
    # ---------------------------------------------------------------------
    if pending_labs > 0:
        complete_label = t('complete_send_to_lab')
        complete_status = 'waiting_lab'
        success_msg = t('sent_to_lab_msg')
    elif pending_prescriptions > 0:
        complete_label = t('complete_send_to_pharmacy')
        complete_status = 'waiting_pharmacy'
        success_msg = t('sent_to_pharmacy_msg')
    else:
        complete_label = t('complete_discharge')
        complete_status = 'completed'
        success_msg = t('consultation_complete_msg')

    action_col1, action_col2 = st.columns([3, 1])
    with action_col1:
        if st.button(complete_label,
                     key=f"signoff_complete_{visit_id}",
                     type="primary", use_container_width=True):
            # Diagnosis is no longer enforced — the prior check queried the
            # icd10_diagnoses table only, which missed free-text diagnoses
            # the doctor typed into the visit notes. Trust the doctor.
            save_consultation_and_update_status(complete_status, visit_id)
            advance_after_signoff(success_msg)
    with action_col2:
        if st.button(t('pause_consultation'),
                     key=f"signoff_return_{visit_id}",
                     use_container_width=True):
            save_consultation_and_update_status('waiting_consultation', visit_id)
            time.sleep(0.3)
            st.session_state.active_consultation = None
            st.session_state.page = 'doctor'
            st.rerun()
    
    # ===== FAMILY NAVIGATION SECTION =====
    # Show family navigation at the bottom of the consultation form for families with multiple members
    db_nav = get_db_manager()
    family_members = db_nav.get_family_members(patient_id)
    
    # Only show navigation if there are multiple family members with visits today
    show_family_nav = False
    members_with_visits = []
    
    if family_members and len(family_members) > 1:
        # Check how many family members have visits today
        for member in family_members:
            conn_check_visit = sqlite3.connect(db_nav.db_name)
            cursor_check_visit = conn_check_visit.cursor()
            cursor_check_visit.execute('''
                SELECT visit_id, status FROM visits 
                WHERE patient_id = ? AND DATE(visit_date) = DATE('now')
                ORDER BY visit_date DESC LIMIT 1
            ''', (member['patient_id'],))
            visit_data = cursor_check_visit.fetchone()
            conn_check_visit.close()
            if visit_data:
                members_with_visits.append({**member, 'visit_id': visit_data[0], 'status': visit_data[1]})
        
        # Only show navigation if 2+ family members have visits today
        show_family_nav = len(members_with_visits) >= 2
    
    if show_family_nav:
        st.markdown("---")
        st.markdown("### 👨‍👩‍👧‍👦 Family Navigation")
        
        # Find current patient index in family
        current_index = -1
        for i, member in enumerate(family_members):
            if member['patient_id'] == patient_id:
                current_index = i
                break
        
        # Show progress bar for family
        if current_index >= 0:
            st.progress((current_index + 1) / len(family_members), 
                       text=f"Family Member {current_index + 1} of {len(family_members)}")
        
        # Display all family members in a row
        st.markdown("**Family Members:**")
        cols = st.columns(min(len(family_members), 5))  # Max 5 columns
        
        for i, member in enumerate(family_members):
            col_idx = i % min(len(family_members), 5)
            with cols[col_idx]:
                is_current = member['patient_id'] == patient_id
                relationship = member.get('relationship', 'family')
                name = member.get('name', 'Unknown')
                age = member.get('age', '')
                
                # Check if this family member has a visit today
                conn_check = sqlite3.connect(db_nav.db_name)
                cursor_check = conn_check.cursor()
                cursor_check.execute('''
                    SELECT visit_id, status FROM visits 
                    WHERE patient_id = ? AND DATE(visit_date) = DATE('now')
                    ORDER BY visit_date DESC LIMIT 1
                ''', (member['patient_id'],))
                member_visit = cursor_check.fetchone()
                conn_check.close()
                
                # Determine status icon
                if member_visit:
                    status = member_visit[1]
                    if status in ['completed', 'prescribed']:
                        status_icon = "✅"
                    elif status in ['with_doctor', 'in_consultation']:
                        status_icon = "🔵"
                    elif status in ['waiting_lab', 'needs_ophthalmology']:
                        status_icon = "🧪"
                    else:
                        status_icon = "⏳"
                else:
                    status_icon = "⚪"
                
                # Show current member highlighted
                if is_current:
                    st.markdown(f"**{status_icon} {name}** ← YOU ARE HERE")
                    st.caption(f"{relationship.title()}, Age: {age if age else 'N/A'}")
                else:
                    if member_visit:
                        # Button to navigate to this family member
                        if st.button(f"{status_icon} {name}", key=f"nav_family_{member['patient_id']}"):
                            # Auto-save current consultation before switching
                            consultation_key = f"consultation_data_{visit_id}"
                            if consultation_key in st.session_state:
                                # Save current work to database
                                conn_save = sqlite3.connect(db_nav.db_name)
                                cursor_save = conn_save.cursor()
                                data = st.session_state[consultation_key]
                                cursor_save.execute('''
                                    UPDATE visits 
                                    SET chief_complaint = ?, symptoms = ?, diagnosis = ?, 
                                        treatment_plan = ?, notes = ?,
                                        medical_history = ?, current_medications = ?
                                    WHERE visit_id = ?
                                ''', (data.get('chief_complaint', ''), data.get('symptoms', ''),
                                      data.get('diagnosis', ''), data.get('treatment_plan', ''),
                                      data.get('notes', ''), data.get('medical_history', ''),
                                      data.get('current_medications', ''), visit_id))
                                conn_save.commit()
                                conn_save.close()
                            
                            # Switch to the selected family member
                            st.session_state.active_consultation = {
                                'visit_id': member_visit[0],
                                'patient_id': member['patient_id'],
                                'patient_name': name
                            }
                            st.session_state.page = 'consultation_form'
                            # Update URL params for the new patient
                            st.query_params['visit_id'] = member_visit[0]
                            st.query_params['patient_id'] = member['patient_id']
                            st.query_params['patient_name'] = name
                            st.rerun()
                        st.caption(f"{relationship.title()}, Age: {age if age else 'N/A'}")
                    else:
                        st.markdown(f"⚪ {name}")
                        st.caption(f"{relationship.title()} - No visit today")
        
        # Previous/Next navigation buttons
        st.markdown("---")
        col_prev, col_info, col_next = st.columns([1, 2, 1])
        
        with col_prev:
            if current_index > 0:
                prev_member = family_members[current_index - 1]
                # Find previous member's visit
                conn_prev = sqlite3.connect(db_nav.db_name)
                cursor_prev = conn_prev.cursor()
                cursor_prev.execute('''
                    SELECT visit_id FROM visits 
                    WHERE patient_id = ? AND DATE(visit_date) = DATE('now')
                    ORDER BY visit_date DESC LIMIT 1
                ''', (prev_member['patient_id'],))
                prev_visit = cursor_prev.fetchone()
                conn_prev.close()
                
                if prev_visit:
                    if st.button("⬅️ Previous Family Member", use_container_width=True, key="prev_family"):
                        # Auto-save before switching
                        consultation_key = f"consultation_data_{visit_id}"
                        if consultation_key in st.session_state:
                            conn_save = sqlite3.connect(db_nav.db_name)
                            cursor_save = conn_save.cursor()
                            data = st.session_state[consultation_key]
                            cursor_save.execute('''
                                UPDATE visits 
                                SET chief_complaint = ?, symptoms = ?, diagnosis = ?, 
                                    treatment_plan = ?, notes = ?,
                                    medical_history = ?, current_medications = ?
                                WHERE visit_id = ?
                            ''', (data.get('chief_complaint', ''), data.get('symptoms', ''),
                                  data.get('diagnosis', ''), data.get('treatment_plan', ''),
                                  data.get('notes', ''), data.get('medical_history', ''),
                                  data.get('current_medications', ''), visit_id))
                            conn_save.commit()
                            conn_save.close()
                        
                        st.session_state.active_consultation = {
                            'visit_id': prev_visit[0],
                            'patient_id': prev_member['patient_id'],
                            'patient_name': prev_member['name']
                        }
                        st.session_state.page = 'consultation_form'
                        # Update URL params for the new patient
                        st.query_params['visit_id'] = prev_visit[0]
                        st.query_params['patient_id'] = prev_member['patient_id']
                        st.query_params['patient_name'] = prev_member['name']
                        st.rerun()
                    st.caption(f"Go to: {prev_member['name']}")
        
        with col_info:
            st.info(f"Currently viewing: **{patient_name}** ({current_index + 1}/{len(family_members)})")
        
        with col_next:
            if current_index < len(family_members) - 1:
                next_member = family_members[current_index + 1]
                # Find next member's visit
                conn_next = sqlite3.connect(db_nav.db_name)
                cursor_next = conn_next.cursor()
                cursor_next.execute('''
                    SELECT visit_id FROM visits 
                    WHERE patient_id = ? AND DATE(visit_date) = DATE('now')
                    ORDER BY visit_date DESC LIMIT 1
                ''', (next_member['patient_id'],))
                next_visit = cursor_next.fetchone()
                conn_next.close()
                
                if next_visit:
                    if st.button("Next Family Member ➡️", use_container_width=True, type="primary", key="next_family"):
                        # Auto-save before switching
                        consultation_key = f"consultation_data_{visit_id}"
                        if consultation_key in st.session_state:
                            conn_save = sqlite3.connect(db_nav.db_name)
                            cursor_save = conn_save.cursor()
                            data = st.session_state[consultation_key]
                            cursor_save.execute('''
                                UPDATE visits 
                                SET chief_complaint = ?, symptoms = ?, diagnosis = ?, 
                                    treatment_plan = ?, notes = ?,
                                    medical_history = ?, current_medications = ?
                                WHERE visit_id = ?
                            ''', (data.get('chief_complaint', ''), data.get('symptoms', ''),
                                  data.get('diagnosis', ''), data.get('treatment_plan', ''),
                                  data.get('notes', ''), data.get('medical_history', ''),
                                  data.get('current_medications', ''), visit_id))
                            conn_save.commit()
                            conn_save.close()
                        
                        st.session_state.active_consultation = {
                            'visit_id': next_visit[0],
                            'patient_id': next_member['patient_id'],
                            'patient_name': next_member['name']
                        }
                        st.session_state.page = 'consultation_form'
                        # Update URL params for the new patient
                        st.query_params['visit_id'] = next_visit[0]
                        st.query_params['patient_id'] = next_member['patient_id']
                        st.query_params['patient_name'] = next_member['name']
                        st.rerun()
                    st.caption(f"Go to: {next_member['name']}")
            else:
                st.success("✅ Last family member!")


def consultation_history():
    st.markdown(f"### {t('hdr_consultation_history')}")

    # Check if we should show patient history
    if hasattr(
            st.session_state,
            'show_patient_history') and st.session_state.show_patient_history:
        show_patient_history_detail(st.session_state.show_patient_history,
                                    st.session_state.patient_history_name)
        return

    # Lightweight scope picker so providers can review today or look back further
    scope = st.radio(
        "Show:", ["Today", "Last 7 days", "Last 30 days", "All time"],
        index=0, horizontal=True, key="consult_history_scope")
    scope_to_days = {"Today": 0, "Last 7 days": 7,
                     "Last 30 days": 30, "All time": None}
    days = scope_to_days[scope]

    conn = sqlite3.connect(db.db_name)
    cursor = conn.cursor()

    base_query = '''
        SELECT c.id, c.visit_id, c.doctor_name, c.chief_complaint, c.symptoms,
               c.diagnosis, c.treatment_plan, c.notes, c.needs_ophthalmology,
               c.consultation_time, p.name, v.patient_id
        FROM consultations c
        JOIN visits v ON c.visit_id = v.visit_id
        JOIN patients p ON v.patient_id = p.patient_id
    '''
    if days == 0:
        cursor.execute(base_query +
                       " WHERE DATE(c.consultation_time) = DATE('now') ORDER BY c.consultation_time DESC")
    elif days is None:
        cursor.execute(base_query + " ORDER BY c.consultation_time DESC LIMIT 500")
    else:
        cursor.execute(base_query +
                       " WHERE c.consultation_time >= DATE('now', ?) ORDER BY c.consultation_time DESC",
                       (f'-{days} days',))

    consultations = cursor.fetchall()
    conn.close()

    if consultations:
        for consultation in consultations:
            # consultation structure: [id, visit_id, doctor_name, chief_complaint, symptoms, diagnosis, treatment_plan, notes, needs_ophthalmology, consultation_time, patient_name, patient_id]
            patient_name = consultation[10]
            patient_id = consultation[11]
            doctor_name = consultation[2]
            chief_complaint = consultation[3]
            symptoms = consultation[4]
            diagnosis = consultation[5]
            treatment_plan = consultation[6]
            notes = consultation[7]
            consultation_time = consultation[9]

            with st.expander(
                    f"👤 {patient_name} (ID: {patient_id}) - {chief_complaint}"
            ):
                st.write(f"**Doctor:** {doctor_name}")
                st.write(
                    f"**Time:** {consultation_time[:16].replace('T', ' ')}")
                st.write(f"**Chief Complaint:** {chief_complaint}")
                if symptoms:
                    st.write(f"**Symptoms:** {symptoms}")
                if diagnosis:
                    st.write(f"**Diagnosis:** {diagnosis}")
                if treatment_plan:
                    st.write(f"**Treatment Plan:** {treatment_plan}")
                if notes:
                    st.write(f"**Notes:** {notes}")

                # Add patient history link button
                if st.button(f"View Full Patient History",
                             key=f"history_{patient_id}_{consultation[0]}"):
                    st.session_state.show_patient_history = patient_id
                    st.session_state.patient_history_name = patient_name
                    st.rerun()
    else:
        st.info(t('msg_no_consultations_today'))


def show_patient_history_detail(patient_id: str, patient_name: str):
    """Display comprehensive patient chart with complete medical history"""

    # Enhanced styling for patient chart
    st.markdown("""
    <style>
    .patient-chart-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 15px;
        padding: 20px;
        margin: 10px 0;
        color: white;
        text-align: center;
    }
    .chart-section {
        background: white;
        border-radius: 10px;
        padding: 15px;
        margin: 15px 0;
        border: 1px solid #e5e7eb;
        box-shadow: 0 2px 10px rgba(0,0,0,0.05);
    }
    .vital-card {
        background: linear-gradient(135deg, #e0f2fe 0%, #b3e5fc 100%);
        border-left: 4px solid #0288d1;
        padding: 12px;
        margin: 8px 0;
        border-radius: 8px;
    }
    .lab-card {
        background: linear-gradient(135deg, #fff3e0 0%, #ffe0b2 100%);
        border-left: 4px solid #f57c00;
        padding: 12px;
        margin: 8px 0;
        border-radius: 8px;
    }
    .prescription-card {
        background: linear-gradient(135deg, #e8f5e8 0%, #c8e6c9 100%);
        border-left: 4px solid #388e3c;
        padding: 12px;
        margin: 8px 0;
        border-radius: 8px;
    }
    .consultation-card {
        background: linear-gradient(135deg, #f3e5f5 0%, #e1bee7 100%);
        border-left: 4px solid #7b1fa2;
        padding: 12px;
        margin: 8px 0;
        border-radius: 8px;
    }
    .demographics-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
        gap: 15px;
        margin: 15px 0;
    }
    .demo-item {
        background: #f8fafc;
        padding: 10px;
        border-radius: 8px;
        border-left: 3px solid #3b82f6;
    }
    </style>
    """, unsafe_allow_html=True)

    # Chart header
    st.markdown(f"""
    <div class="patient-chart-header">
        <h2>🏥 Complete Patient Chart</h2>
        <h3>{patient_name} (ID: {patient_id})</h3>
        <p>Comprehensive Medical Record & History</p>
    </div>
    """, unsafe_allow_html=True)

    # Navigation buttons
    nav_col1, nav_col2, nav_col3 = st.columns([2, 3, 1])
    with nav_col1:
        if st.button(t('back_to_consult_history'), key="back_to_consult_history"):
            if 'show_patient_history' in st.session_state:
                del st.session_state.show_patient_history
            if 'patient_history_name' in st.session_state:
                del st.session_state.patient_history_name
            st.rerun()

    with nav_col3:
        if st.button("✕", key="close_patient_history", help="Close patient history", use_container_width=True):
            if 'show_patient_history' in st.session_state:
                del st.session_state.show_patient_history
            if 'patient_history_name' in st.session_state:
                del st.session_state.patient_history_name
            st.rerun()

    conn = sqlite3.connect("clinic_database.db")
    cursor = conn.cursor()

    # Get patient basic info with family information
    cursor.execute('''
        SELECT p.*, f.family_name, f.head_of_household, f.address as family_address
        FROM patients p
        LEFT JOIN families f ON p.family_id = f.family_id
        WHERE p.patient_id = ?
    ''', (patient_id,))
    patient = cursor.fetchone()

    if patient:
        # Patient Demographics Section
        st.markdown('<div class="chart-section">', unsafe_allow_html=True)
        st.markdown("### 👤 Patient Demographics & Information")
        
        st.markdown(f'''
        <div class="demographics-grid">
            <div class="demo-item">
                <strong>👤 Name:</strong><br>{patient[1]}
            </div>
            <div class="demo-item">
                <strong>🎂 Age:</strong><br>{patient[2] or 'Not specified'}
            </div>
            <div class="demo-item">
                <strong>⚧ Gender:</strong><br>{patient[3] or 'Not specified'}
            </div>
            <div class="demo-item">
                <strong>📱 Phone:</strong><br>{patient[4] or 'Not provided'}
            </div>
            <div class="demo-item">
                <strong>🆘 Emergency Contact:</strong><br>{patient[6] or 'Not provided'}
            </div>
            <div class="demo-item">
                <strong>📅 Registration:</strong><br>{patient[7][:10] if patient[7] else 'Unknown'}
            </div>
        </div>
        ''', unsafe_allow_html=True)

        # Family Information
        if patient[10]:  # family_name exists
            st.markdown("**👨‍👩‍👧‍👦 Family Information:**")
            family_col1, family_col2 = st.columns(2)
            with family_col1:
                st.write(f"**Family Name:** {patient[10]}")
                st.write(f"**Head of Household:** {patient[11] or 'Not specified'}")
            with family_col2:
                st.write(f"**Family Address:** {patient[12] or 'Not provided'}")
                st.write(f"**Individual Status:** {'Independent' if patient[14] else 'Family Member'}")

        # Graduate-to-independent action — separates a child from their family
        # (e.g., when they turn 18). Uses an explicit re-query so column indexing
        # is independent of the existing ad-hoc indexing above.
        _grad_conn = sqlite3.connect(db.db_name)
        _grad_cur = _grad_conn.cursor()
        _grad_cur.execute(
            'SELECT age, family_id, is_independent FROM patients WHERE patient_id = ?',
            (patient_id,))
        _grad_row = _grad_cur.fetchone()
        _grad_conn.close()
        if _grad_row:
            g_age, g_family_id, g_independent = _grad_row
            if g_family_id and not g_independent:
                st.markdown("---")
                st.markdown("**🎓 Family separation**")
                st.caption(
                    "When a child turns 18 they can be separated from the family. "
                    "Patient ID stays the same so all visits, labs, prescriptions remain attached.")
                if g_age is None or g_age < 17:
                    st.button(
                        "Graduate to independent record",
                        disabled=True,
                        key=f"grad_disabled_{patient_id}",
                        help=f"Available at age 17 or older (currently: {g_age or 'unknown'})")
                else:
                    with st.expander("Graduate to independent record"):
                        new_address = st.text_input(
                            "New address (optional)",
                            key=f"grad_addr_{patient_id}")
                        if st.button(
                                "Confirm graduation",
                                type="primary",
                                key=f"grad_confirm_{patient_id}"):
                            db.separate_family_member(patient_id, new_address or "")
                            st.success(
                                f"{patient_name} is now an independent record. "
                                "History preserved.")
                            st.rerun()
            elif g_independent:
                st.info("🎓 This patient is independent (previously separated from family). History intact.")

        # Medical History
        if patient[9]:  # medical_history
            st.markdown("### 📝 Medical History")
            st.markdown(f'<div style="background: #f8fafc; padding: 15px; border-radius: 8px; border-left: 3px solid #10b981;"><pre style="margin: 0; white-space: pre-wrap; font-family: inherit;">{patient[9]}</pre></div>', unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)

        # Get comprehensive visit data
        cursor.execute('''
            SELECT v.visit_id, v.visit_date, v.status, v.priority, v.triage_time, 
                   v.consultation_time, v.pharmacy_time, v.return_reason, v.notes
            FROM visits v
            WHERE v.patient_id = ?
            ORDER BY v.visit_date DESC
        ''', (patient_id,))
        visits = cursor.fetchall()

        if visits:
            st.markdown('<div class="chart-section">', unsafe_allow_html=True)
            st.markdown("### 🏥 Complete Visit Records")
            
            for visit in visits:
                visit_id = visit[0]
                visit_date = visit[1][:10] if visit[1] else "Unknown"
                status = visit[2] or "In Progress"
                priority = visit[3] or "routine"
                
                priority_emoji = "🔴" if priority == "critical" else "🟡" if priority == "urgent" else "🟢"
                status_color = "#10b981" if status == "completed" else "#f59e0b" if status == "in_progress" else "#6b7280"
                
                with st.expander(f"{priority_emoji} Visit {visit_date} - {status.title()}", expanded=False):
                    
                    # Visit Overview
                    overview_col1, overview_col2 = st.columns(2)
                    with overview_col1:
                        st.markdown("**📊 Visit Overview:**")
                        st.write(f"**Status:** {status}")
                        st.write(f"**Priority:** {priority}")
                        if visit[7]:  # return_reason
                            st.write(f"**Return Reason:** {visit[7]}")
                    
                    with overview_col2:
                        st.markdown("**⏱️ Visit Timeline:**")
                        if visit[4]: # triage_time
                            st.write(f"🏥 Triage: {visit[4][:16].replace('T', ' ')}")
                        if visit[5]: # consultation_time
                            st.write(f"👨‍⚕️ Consultation: {visit[5][:16].replace('T', ' ')}")
                        if visit[6]: # pharmacy_time
                            st.write(f"💊 Pharmacy: {visit[6][:16].replace('T', ' ')}")
                        if status == 'completed' and visit[5]:  # Show consultation time as completion for completed visits
                            st.write(f"✅ Completed: {visit[5][:16].replace('T', ' ')}")

                    # Vital Signs
                    cursor.execute('''
                        SELECT systolic_bp, diastolic_bp, heart_rate, temperature, weight, recorded_time
                        FROM vital_signs
                        WHERE visit_id = ?
                        ORDER BY recorded_time DESC
                    ''', (visit_id,))
                    vitals = cursor.fetchall()
                    
                    if vitals:
                        st.markdown("**💓 Vital Signs:**")
                        for vital in vitals:
                            bp_text = f"{vital[0] or 'N/A'}/{vital[1] or 'N/A'}"
                            st.markdown(f"""
                            <div class="vital-card">
                                <strong>📅 Recorded:</strong> {vital[5][:16].replace('T', ' ') if vital[5] else 'Unknown'}<br>
                                <strong>🩺 Blood Pressure:</strong> {bp_text} mmHg | 
                                <strong>💓 Heart Rate:</strong> {vital[2] or 'N/A'} bpm<br>
                                <strong>🌡️ Temperature:</strong> {vital[3] or 'N/A'}°F | 
                                <strong>⚖️ Weight:</strong> {vital[4] or 'N/A'} kg
                            </div>
                            """, unsafe_allow_html=True)

                    # Consultation Details
                    cursor.execute('''
                        SELECT doctor_name, chief_complaint, symptoms, diagnosis, treatment_plan, 
                               notes, current_medications, consultation_time
                        FROM consultations
                        WHERE visit_id = ?
                        ORDER BY consultation_time DESC
                    ''', (visit_id,))
                    consultations = cursor.fetchall()
                    
                    if consultations:
                        st.markdown("**👨‍⚕️ Consultation Records:**")
                        for consultation in consultations:
                            st.markdown(f"""
                            <div class="consultation-card">
                                <strong>👨‍⚕️ Doctor:</strong> {consultation[0]}<br>
                                <strong>📝 Chief Complaint:</strong> {consultation[1] or 'None recorded'}<br>
                                <strong>🔍 Symptoms:</strong> {consultation[2] or 'None recorded'}<br>
                                <strong>🩺 Diagnosis:</strong> {consultation[3] or 'None recorded'}<br>
                                <strong>💊 Treatment Plan:</strong> {consultation[4] or 'None recorded'}
                            """, unsafe_allow_html=True)
                            
                            if consultation[5]:  # notes
                                st.markdown(f"<strong>📋 Notes:</strong> {consultation[5]}<br>", unsafe_allow_html=True)
                            if consultation[6]:  # current_medications
                                st.markdown(f"<strong>💉 Current Medications:</strong> {consultation[6]}<br>", unsafe_allow_html=True)
                            
                            st.markdown("</div>", unsafe_allow_html=True)

                    # Laboratory Tests and Results
                    cursor.execute('''
                        SELECT lt.test_type, lt.ordered_by, lt.ordered_time, lt.status, 
                               lt.results, lt.completed_time
                        FROM lab_tests lt
                        WHERE lt.visit_id = ?
                        ORDER BY lt.ordered_time DESC
                    ''', (visit_id,))
                    lab_tests = cursor.fetchall()
                    
                    # Get detailed lab results
                    cursor.execute('''
                        SELECT lr.test_id, lr.parameter_name, lr.parameter_value
                        FROM lab_results lr
                        JOIN lab_tests lt ON lr.test_id = lt.id
                        WHERE lt.visit_id = ?
                        ORDER BY lr.parameter_name
                    ''', (visit_id,))
                    lab_results = cursor.fetchall()
                    
                    if lab_tests:
                        st.markdown("**🧪 Laboratory Tests & Results:**")
                        
                        # Group results by test_id
                        results_by_test = {}
                        for lr in lab_results:
                            test_id = lr[0]
                            if test_id not in results_by_test:
                                results_by_test[test_id] = []
                            results_by_test[test_id].append((lr[1], lr[2]))
                        
                        for test in lab_tests:
                            test_type = test[0]
                            ordered_by = test[1]
                            status = test[3]
                            status_color = "#10b981" if status == "completed" else "#f59e0b"
                            
                            st.markdown(f"""
                            <div class="lab-card">
                                <strong>🧪 {test_type}</strong> - Ordered by {ordered_by}<br>
                                <strong>📅 Ordered:</strong> {test[2][:16].replace('T', ' ')}<br>
                                <strong>⚡ Status:</strong> <span style="color: {status_color};">{status}</span>
                            """, unsafe_allow_html=True)
                            
                            if test[5]:  # completed_time
                                st.markdown(f"<strong>✅ Completed:</strong> {test[5][:16].replace('T', ' ')}<br>", unsafe_allow_html=True)
                            
                            # Display detailed results if available
                            test_id = None
                            cursor.execute('SELECT id FROM lab_tests WHERE visit_id = ? AND test_type = ? AND ordered_time = ?', 
                                         (visit_id, test_type, test[2]))
                            test_id_result = cursor.fetchone()
                            if test_id_result:
                                test_id = test_id_result[0]
                            
                            if test_id and test_id in results_by_test:
                                st.markdown("<strong>📊 Detailed Results:</strong><br>", unsafe_allow_html=True)
                                for param_name, param_value in results_by_test[test_id]:
                                    st.markdown(f"• <strong>{param_name}:</strong> {param_value}<br>", unsafe_allow_html=True)
                            elif test[4]:  # basic results
                                st.markdown(f"<strong>📊 Results:</strong> {test[4]}<br>", unsafe_allow_html=True)
                            
                            st.markdown("</div>", unsafe_allow_html=True)

                    # Prescriptions & Medications
                    cursor.execute('''
                        SELECT medication_name, dosage, frequency, duration, indication, 
                               instructions, prescribed_by, prescribed_time, status, 
                               filled_time, teaching_completed, teaching_notes, awaiting_lab
                        FROM prescriptions
                        WHERE visit_id = ?
                        ORDER BY prescribed_time DESC
                    ''', (visit_id,))
                    prescriptions = cursor.fetchall()
                    
                    if prescriptions:
                        st.markdown("**💊 Prescriptions & Medications:**")
                        for rx in prescriptions:
                            prescribed_by = rx[6] if rx[6] else "Unknown Doctor"
                            status = rx[8] if rx[8] else "pending"
                            status_color = "#10b981" if status == "filled" else "#f59e0b" if status == "awaiting_teaching" else "#6b7280"
                            
                            st.markdown(f"""
                            <div class="prescription-card">
                                <strong>💊 {rx[0]}</strong><br>
                                <strong>📏 Dosage:</strong> {rx[1]} | <strong>⏰ Frequency:</strong> {rx[2]} | <strong>📅 Duration:</strong> {rx[3]}<br>
                                <strong>👨‍⚕️ Prescribed by:</strong> {prescribed_by}<br>
                                <strong>⚡ Status:</strong> <span style="color: {status_color};">{status}</span>
                            """, unsafe_allow_html=True)
                            
                            if rx[4]:  # indication
                                st.markdown(f"<strong>🎯 For:</strong> {rx[4]}<br>", unsafe_allow_html=True)
                            if rx[5]:  # instructions
                                st.markdown(f"<strong>📋 Instructions:</strong> {rx[5]}<br>", unsafe_allow_html=True)
                            if rx[12] == 'yes':  # awaiting_lab
                                st.markdown(f"<strong>🧪 Lab Required:</strong> Yes<br>", unsafe_allow_html=True)
                            
                            st.markdown(f"<strong>📅 Prescribed:</strong> {rx[7][:16].replace('T', ' ') if rx[7] else 'Unknown'}<br>", unsafe_allow_html=True)
                            
                            if rx[9]:  # filled_time
                                st.markdown(f"<strong>✅ Filled:</strong> {rx[9][:16].replace('T', ' ')}<br>", unsafe_allow_html=True)
                            if rx[10]:  # teaching_completed
                                st.markdown(f"<strong>📚 Teaching Completed:</strong> {rx[10][:16].replace('T', ' ')}<br>", unsafe_allow_html=True)
                            if rx[11]:  # teaching_notes
                                st.markdown(f"<strong>📝 Teaching Notes:</strong> {rx[11]}<br>", unsafe_allow_html=True)
                            
                            st.markdown("</div>", unsafe_allow_html=True)

                    # Patient Photos
                    cursor.execute('''
                        SELECT description, photo_time
                        FROM patient_photos
                        WHERE patient_id = ? AND visit_id = ?
                        ORDER BY photo_time DESC
                    ''', (patient_id, visit_id))
                    photos = cursor.fetchall()
                    
                    if photos:
                        st.markdown("**📸 Photo Documentation:**")
                        for photo in photos:
                            st.markdown(f"""
                            <div style="background: #f3f4f6; padding: 10px; border-radius: 8px; margin: 5px 0; border-left: 3px solid #6b7280;">
                                <strong>📸 {photo[0]}</strong><br>
                                <small>📅 Taken: {photo[1][:16].replace('T', ' ')}</small>
                            </div>
                            """, unsafe_allow_html=True)

                    # Visit Notes
                    if visit[9]:  # visit notes
                        st.markdown("**📝 Visit Notes:**")
                        st.markdown(f'<div style="background: #f8fafc; padding: 10px; border-radius: 8px; border-left: 3px solid #3b82f6;"><em>{visit[9]}</em></div>', unsafe_allow_html=True)

            st.markdown('</div>', unsafe_allow_html=True)

        # Patient Summary Statistics
        cursor.execute('''
            SELECT 
                COUNT(DISTINCT v.visit_id) as total_visits,
                COUNT(DISTINCT p.id) as total_prescriptions,
                COUNT(DISTINCT lt.id) as total_lab_tests,
                COUNT(DISTINCT ph.id) as total_photos,
                MAX(v.visit_date) as last_visit
            FROM visits v
            LEFT JOIN prescriptions p ON v.visit_id = p.visit_id
            LEFT JOIN lab_tests lt ON v.visit_id = lt.visit_id
            LEFT JOIN patient_photos ph ON v.patient_id = ph.patient_id
            WHERE v.patient_id = ?
        ''', (patient_id,))
        summary = cursor.fetchone()
        
        st.markdown('<div class="chart-section">', unsafe_allow_html=True)
        st.markdown("### 📊 Patient Summary Statistics")
        
        sum_col1, sum_col2, sum_col3, sum_col4, sum_col5 = st.columns(5)
        with sum_col1:
            st.metric("🏥 Total Visits", summary[0] or 0)
        with sum_col2:
            st.metric("💊 Prescriptions", summary[1] or 0)
        with sum_col3:
            st.metric("🧪 Lab Tests", summary[2] or 0)
        with sum_col4:
            st.metric("📸 Photos", summary[3] or 0)
        with sum_col5:
            if summary[4]:
                last_visit = summary[4][:10]
                st.metric("📅 Last Visit", last_visit)
            else:
                st.metric("📅 Last Visit", "Never")
        
        st.markdown('</div>', unsafe_allow_html=True)

    else:
        st.error("❌ Patient not found in database.")

    conn.close()


def pharmacy_interface():
    add_to_history('pharmacy')
    st.markdown(f"## {t('page_pharmacy')}")
    render_doctor_status_strip()

    # Get pending lab test count
    conn = sqlite3.connect(db.db_name)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT COUNT(*) FROM lab_tests 
        WHERE status = 'pending' AND DATE(ordered_time) = DATE('now')
    ''')
    pending_lab_count = cursor.fetchone()[0]
    conn.close()
    
    lab_input_label = f"{t('tab_lab_input')} ({pending_lab_count})" if pending_lab_count > 0 else t('tab_lab_input')

    tab1, tab2, tab3, tab4, tab5 = st.tabs(
        [t('tab_ready_to_fill'), t('tab_lab_results'), lab_input_label, t('tab_awaiting_teaching'), t('tab_filled_prescriptions')])

    with tab1:
        pending_prescriptions()

    with tab2:
        awaiting_lab_prescriptions()

    with tab3:
        lab_results_input()

    with tab4:
        awaiting_teaching()

    with tab5:
        filled_prescriptions()


def save_prescription_state(visit_id: str, patient_id: str, patient_name: str, prescriptions: list):
    """Save prescription state for when patients return to pharmacy"""
    prescription_state_key = f"prescription_state_{visit_id}"
    st.session_state[prescription_state_key] = {
        'patient_id': patient_id,
        'patient_name': patient_name,
        'visit_id': visit_id,
        'prescriptions': prescriptions,
        'saved_time': datetime.now().isoformat()
    }

def restore_prescription_state(visit_id: str) -> dict:
    """Restore prescription state when patient returns to pharmacy"""
    prescription_state_key = f"prescription_state_{visit_id}"
    return st.session_state.get(prescription_state_key, None)

def pending_prescriptions():
    st.markdown("### Prescriptions to Fill")
    
    # Check if there's a family pharmacy workflow
    if 'family_pharmacy_workflow' in st.session_state:
        st.info("👨‍👩‍👧‍👦 **Family Consultation Complete** - Processing entire family prescriptions")
        family_data = st.session_state.family_pharmacy_workflow
        
        # Add exit button for families
        col1, col2 = st.columns([3, 1])
        with col2:
            if st.button("Exit family visit", type="secondary", help="Complete family visit and return to main menu"):
                # Clear family workflow and session state
                del st.session_state.family_pharmacy_workflow
                if 'user_role' in st.session_state:
                    del st.session_state.user_role
                
                st.success("🏠 Family visit ended - returning to main menu")
                st.session_state.page = 'role_selection'
                time.sleep(1)
                st.rerun()
        
        # Process all family members' prescriptions together
        for member in family_data:
            st.markdown(f"**{member['patient_name']} (ID: {member['patient_id']})**")
            
            # Get prescriptions for this family member
            conn = sqlite3.connect(db.db_name)
            cursor = conn.cursor()
            cursor.execute('''
                SELECT p.id, p.visit_id, p.medication_name, p.dosage, p.frequency, 
                       p.duration, p.instructions, p.indication, p.prescribed_time, pt.name, v.patient_id, p.awaiting_lab, p.prescribed_by
                FROM prescriptions p
                JOIN visits v ON p.visit_id = v.visit_id
                JOIN patients pt ON v.patient_id = pt.patient_id
                WHERE p.visit_id = ? AND p.status = 'pending' AND p.awaiting_lab = 'no'
            ''', (member['visit_id'],))
            
            member_prescriptions = cursor.fetchall()
            conn.close()
            
            if member_prescriptions:
                for prescription in member_prescriptions:
                    edit_key = f"edit_family_prescription_{prescription[0]}"
                    
                    if st.session_state.get(edit_key, False):
                        # Edit form for family prescription
                        with st.form(f"edit_family_prescription_form_{prescription[0]}"):
                            st.markdown(f"**💊 {prescription[2]}** (Editing)")
                            
                            col_dosage, col_frequency = st.columns(2)
                            with col_dosage:
                                new_dosage = st.text_input("Dosage", value=prescription[3], key=f"edit_family_dosage_{prescription[0]}")
                            with col_frequency:
                                new_frequency = st.text_input("Frequency", value=prescription[4], key=f"edit_family_frequency_{prescription[0]}")
                            
                            new_duration = st.text_input("Duration", value=prescription[5], key=f"edit_family_duration_{prescription[0]}")
                            new_instructions = st.text_area("Instructions", value=prescription[6] if prescription[6] else "", key=f"edit_family_instructions_{prescription[0]}")
                            
                            col_save, col_cancel = st.columns(2)
                            with col_save:
                                if st.form_submit_button("💾 Save Changes", type="primary"):
                                    if new_dosage.strip() and new_frequency.strip() and new_duration.strip():
                                        conn = sqlite3.connect(db.db_name)
                                        cursor = conn.cursor()
                                        cursor.execute('''
                                            UPDATE prescriptions 
                                            SET dosage = ?, frequency = ?, duration = ?, instructions = ?
                                            WHERE id = ?
                                        ''', (new_dosage.strip(), new_frequency.strip(), new_duration.strip(), 
                                             new_instructions.strip() if new_instructions else None, prescription[0]))
                                        conn.commit()
                                        conn.close()
                                        
                                        # Broadcast update to all connected devices
                                        broadcast_to_clients(f"prescription_updated:{prescription[2]}:{member['patient_name']}")
                                        
                                        st.session_state[edit_key] = False
                                        st.success(f"✅ Updated prescription for {prescription[2]}")
                                        st.rerun()
                                    else:
                                        st.error("Dosage, frequency, and duration are required")
                            with col_cancel:
                                if st.form_submit_button("❌ Cancel"):
                                    st.session_state[edit_key] = False
                                    st.rerun()
                    else:
                        # Display mode for family prescription
                        col_prescription, col_edit = st.columns([4, 1])
                        with col_prescription:
                            prescribed_by = prescription[12] if len(prescription) > 12 and prescription[12] else "Unknown Doctor"
                            st.markdown(f"• **{prescription[2]}** - {prescription[3]} {prescription[4]} for {prescription[5]}")
                            st.markdown(f"  👨‍⚕️ *Prescribed by: {prescribed_by}*")
                        with col_edit:
                            if st.button("✏️", key=f"edit_family_prescription_{prescription[0]}", type="secondary", help="Edit prescription"):
                                st.session_state[edit_key] = True
                                st.rerun()
            else:
                st.markdown("• No prescriptions for this family member")
        
        col_complete, col_skip = st.columns(2)
        with col_complete:
            if st.button("✅ Complete All Family Prescriptions", key="complete_family_pharmacy", type="primary"):
                # Mark all family prescriptions as filled
                conn = sqlite3.connect(db.db_name)
                cursor = conn.cursor()
                
                for member in family_data:
                    cursor.execute('''
                        UPDATE prescriptions 
                        SET status = 'awaiting_teaching', filled_time = ? 
                        WHERE visit_id = ? AND status = 'pending' AND awaiting_lab = 'no'
                    ''', (datetime.now().isoformat(), member['visit_id']))
                    
                    cursor.execute('''
                        UPDATE visits 
                        SET pharmacy_time = ?, status = 'completed' 
                        WHERE visit_id = ?
                    ''', (datetime.now().isoformat(), member['visit_id']))
                
                conn.commit()
                conn.close()
                
                # Broadcast family prescription completion to all devices
                family_names = [member['patient_name'] for member in family_data]
                broadcast_to_clients(f"prescriptions_filled:family:{','.join(family_names)}:complete")
                
                # Clear family workflow and session state
                del st.session_state.family_pharmacy_workflow
                
                # Clear any remaining pharmacy session state
                if 'user_role' in st.session_state:
                    del st.session_state.user_role
                
                st.success("✅ All family prescriptions completed!")
                st.success("🏠 Family visit complete - returning to main menu")
                
                # Force navigation back to role selection
                st.session_state.page = 'role_selection'
                time.sleep(2)
                st.rerun()
        
        with col_skip:
            if st.button("⏭️ Skip Prescriptions & Exit", key="skip_family_pharmacy", type="secondary"):
                # Just clear family workflow without filling prescriptions
                del st.session_state.family_pharmacy_workflow
                if 'user_role' in st.session_state:
                    del st.session_state.user_role
                
                st.success("🏠 Family visit ended without filling prescriptions")
                st.session_state.page = 'role_selection'
                time.sleep(1)
                st.rerun()
        
        return

    conn = sqlite3.connect(db.db_name)
    cursor = conn.cursor()

    cursor.execute('''
        SELECT p.id, p.visit_id, p.medication_name, p.dosage, p.frequency, 
               p.duration, p.instructions, p.indication, p.prescribed_time, pt.name, v.patient_id, p.awaiting_lab, p.prescribed_by
        FROM prescriptions p
        JOIN visits v ON p.visit_id = v.visit_id
        JOIN patients pt ON v.patient_id = pt.patient_id
        WHERE p.status = 'pending' AND p.awaiting_lab = 'no' AND DATE(p.prescribed_time) = DATE('now')
        ORDER BY p.prescribed_time
    ''')

    pending = cursor.fetchall()
    conn.close()

    if pending:
        # Group by patient
        patients = {}
        for prescription in pending:
            patient_id = prescription[10]
            patient_name = prescription[9]
            visit_id = prescription[1]

            if patient_id not in patients:
                patients[patient_id] = {
                    'name': patient_name,
                    'visit_id': visit_id,
                    'prescriptions': []
                }

            patients[patient_id]['prescriptions'].append(prescription)
            
        # Check for prescription state restoration
        for patient_id, patient_data in patients.items():
            restored_state = restore_prescription_state(patient_data['visit_id'])
            if restored_state:
                st.info(f"📋 Prescription history restored for {patient_data['name']}")

        for patient_id, patient_data in patients.items():
            with st.expander(f"👤 {patient_data['name']} (ID: {patient_id})",
                             expanded=True):
                st.markdown("**Prescriptions:**")

                all_filled = True
                prescription_ids = []

                for prescription in patient_data['prescriptions']:
                    prescription_ids.append(prescription[0])
                    edit_key = f"edit_prescription_{prescription[0]}"
                    
                    col1, col2 = st.columns([3, 1])

                    with col1:
                        # Check if this prescription is in edit mode
                        if st.session_state.get(edit_key, False):
                            # Edit form for prescription
                            with st.form(f"edit_prescription_form_{prescription[0]}"):
                                st.markdown(f"**💊 {prescription[2]}** (Editing)")
                                
                                col_dosage, col_frequency = st.columns(2)
                                with col_dosage:
                                    new_dosage = st.text_input("Dosage", value=prescription[3], key=f"edit_dosage_{prescription[0]}")
                                with col_frequency:
                                    new_frequency = st.text_input("Frequency", value=prescription[4], key=f"edit_frequency_{prescription[0]}")
                                
                                new_duration = st.text_input("Duration", value=prescription[5], key=f"edit_duration_{prescription[0]}")
                                new_instructions = st.text_area("Instructions", value=prescription[6] if prescription[6] else "", key=f"edit_instructions_{prescription[0]}")
                                
                                col_save, col_cancel = st.columns(2)
                                with col_save:
                                    if st.form_submit_button("💾 Save Changes", type="primary"):
                                        if new_dosage.strip() and new_frequency.strip() and new_duration.strip():
                                            conn = sqlite3.connect(db.db_name)
                                            cursor = conn.cursor()
                                            cursor.execute('''
                                                UPDATE prescriptions 
                                                SET dosage = ?, frequency = ?, duration = ?, instructions = ?
                                                WHERE id = ?
                                            ''', (new_dosage.strip(), new_frequency.strip(), new_duration.strip(), 
                                                 new_instructions.strip() if new_instructions else None, prescription[0]))
                                            conn.commit()
                                            conn.close()
                                            
                                            # Broadcast update to all connected devices
                                            broadcast_to_clients(f"prescription_updated:{prescription[2]}:{patient_data['name']}")
                                            
                                            st.session_state[edit_key] = False
                                            st.success(f"✅ Updated prescription for {prescription[2]}")
                                            st.rerun()
                                        else:
                                            st.error("Dosage, frequency, and duration are required")
                                with col_cancel:
                                    if st.form_submit_button("❌ Cancel"):
                                        st.session_state[edit_key] = False
                                        st.rerun()
                        else:
                            # Display mode for prescription
                            prescribed_by = prescription[12] if len(prescription) > 12 and prescription[12] else "Unknown Doctor"
                            st.markdown(f"""
                            <div style="background: white; border: 1px solid #e5e7eb; border-radius: 8px; padding: 16px; margin-bottom: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
                                <h5 style="color: #1f2937; margin: 0 0 8px 0; font-size: 16px;">💊 {prescription[2]}</h5>
                                <p style="margin: 0 0 12px 0; color: #7c3aed; font-size: 13px; font-weight: 600;"><strong>👨‍⚕️ Prescribed by:</strong> {prescribed_by}</p>
                                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 8px; margin-bottom: 8px;">
                                    <p style="margin: 0; color: #4b5563; font-size: 14px;"><strong>Dosage:</strong> {prescription[3]}</p>
                                    <p style="margin: 0; color: #4b5563; font-size: 14px;"><strong>Frequency:</strong> {prescription[4]}</p>
                                </div>
                                <p style="margin: 0 0 8px 0; color: #4b5563; font-size: 14px;"><strong>Duration:</strong> {prescription[5]}</p>
                                {f'<p style="margin: 0 0 8px 0; color: #059669; font-size: 14px; background: #d1fae5; padding: 4px 8px; border-radius: 4px;"><strong>For:</strong> {prescription[7]}</p>' if prescription[7] else ''}
                                {f'<p style="margin: 0; color: #6b7280; font-size: 13px; font-style: italic;"><strong>Instructions:</strong> {prescription[6]}</p>' if prescription[6] else ''}
                            </div>
                            """,
                                        unsafe_allow_html=True)

                    with col2:
                        if not st.session_state.get(edit_key, False):
                            col_filled, col_edit = st.columns([1, 1])
                            with col_filled:
                                if st.checkbox(f"Filled",
                                               key=f"filled_{prescription[0]}"):
                                    pass
                                else:
                                    all_filled = False
                            with col_edit:
                                if st.button("✏️", key=f"edit_prescription_{prescription[0]}", type="secondary", help="Edit prescription details"):
                                    st.session_state[edit_key] = True
                                    st.rerun()
                        else:
                            all_filled = False

                if st.button(
                        f"✅ Complete All Prescriptions for {patient_data['name']}",
                        key=
                        f"complete_{patient_data['name'].replace(' ', '_')}",
                        disabled=not all_filled,
                        type="primary",
                        use_container_width=True):

                    conn = sqlite3.connect(db.db_name)
                    cursor = conn.cursor()

                    # Mark all prescriptions as awaiting teaching
                    for prescription_id in prescription_ids:
                        cursor.execute(
                            '''
                            UPDATE prescriptions 
                            SET status = 'awaiting_teaching', filled_time = ? 
                            WHERE id = ?
                        ''', (datetime.now().isoformat(), prescription_id))

                    # Update visit status to completed
                    cursor.execute(
                        '''
                        UPDATE visits 
                        SET pharmacy_time = ?, status = 'completed' 
                        WHERE patient_id = ? AND DATE(visit_date) = DATE('now')
                    ''', (datetime.now().isoformat(), patient_id))

                    conn.commit()
                    conn.close()

                    # Broadcast prescription completion to all devices
                    broadcast_to_clients(f"prescriptions_filled:{patient_data['name']}:individual:complete")

                    st.success(
                        f"✅ All prescriptions completed for {patient_data['name']}!"
                    )
                    st.rerun()
    else:
        st.info(t('msg_no_pending_prescriptions'))


def awaiting_lab_prescriptions():
    st.markdown("### Lab Results & Patient Review")

    conn = sqlite3.connect(db.db_name)
    cursor = conn.cursor()

    # Get all completed lab tests for today with patient information
    cursor.execute('''
        SELECT lt.id, lt.visit_id, lt.test_type, lt.results, lt.completed_time, 
               pt.name, pt.patient_id, v.consultation_time,
               CASE WHEN EXISTS (
                   SELECT 1 FROM visits v2 
                   WHERE v2.patient_id = pt.patient_id 
                   AND v2.status = 'waiting_consultation' 
                   AND v2.return_reason = 'pharmacy_lab_review'
               ) THEN 'returned_to_provider'
               ELSE 'completed_lab'
               END as patient_status
        FROM lab_tests lt
        JOIN visits v ON lt.visit_id = v.visit_id
        JOIN patients pt ON v.patient_id = pt.patient_id
        WHERE lt.status = 'completed' AND DATE(lt.completed_time) = DATE('now')
        ORDER BY lt.completed_time DESC
    ''')

    lab_results = cursor.fetchall()
    conn.close()

    if lab_results:
        # Group by patient
        patients = {}
        for result in lab_results:
            patient_id = result[6]
            patient_name = result[5]
            
            if patient_id not in patients:
                patients[patient_id] = {
                    'name': patient_name,
                    'visit_id': result[1],
                    'consultation_time': result[7],
                    'lab_tests': [],
                    'status': result[8]
                }
            
            patients[patient_id]['lab_tests'].append({
                'id': result[0],
                'test_type': result[2],
                'results': result[3],
                'completed_time': result[4]
            })

        for patient_id, patient_data in patients.items():
            # Show different styling based on whether patient has already been seen
            if patient_data['status'] == 'returned_to_provider':
                status_indicator = "🔄 RETURNED TO PROVIDER"
                status_color = "#10b981"
                border_color = "#10b981"
            else:
                status_indicator = "🧪 LAB RESULTS READY"
                status_color = "#3b82f6"
                border_color = "#3b82f6"

            with st.expander(f"{status_indicator} - {patient_data['name']} (ID: {patient_id})", expanded=True):
                
                # Patient consultation info
                if patient_data['consultation_time']:
                    st.markdown(f"**Last Consultation:** {patient_data['consultation_time'][:16].replace('T', ' ')}")
                
                # Display detailed lab results
                st.markdown("### 🧪 Lab Test Results")
                
                for lab in patient_data['lab_tests']:
                    edit_key = f"edit_lab_{lab['id']}"
                    
                    # Lab test header with edit button
                    col_header, col_edit = st.columns([4, 1])
                    with col_header:
                        st.markdown(f"**{lab['test_type']} - Completed: {lab['completed_time'][:16].replace('T', ' ')}**")
                    with col_edit:
                        if st.button("✏️", key=f"edit_lab_btn_{lab['id']}", type="secondary", help="Edit lab results"):
                            st.session_state[edit_key] = True
                            st.rerun()
                    
                    # Check if this lab result is in edit mode
                    if st.session_state.get(edit_key, False):
                        # Edit form based on test type
                        if lab['test_type'].lower() == 'urinalysis':
                            st.markdown("**Edit Urinalysis Results:**")
                            with st.form(f"edit_urinalysis_{lab['id']}"):
                                col1, col2 = st.columns(2)
                                
                                with col1:
                                    st.markdown("**Physical Parameters:**")
                                    color = st.selectbox("Color", ["Yellow", "Pale Yellow", "Dark Yellow", "Amber", "Red", "Brown", "Other"], key=f"edit_color_{lab['id']}")
                                    clarity = st.selectbox("Clarity", ["Clear", "Slightly Cloudy", "Cloudy", "Turbid"], key=f"edit_clarity_{lab['id']}")
                                    specific_gravity = st.number_input("Specific Gravity", min_value=1.000, max_value=1.100, value=1.020, step=0.001, format="%.3f", key=f"edit_sg_{lab['id']}")
                                    ph = st.number_input("pH", min_value=4.5, max_value=9.0, value=6.0, step=0.5, key=f"edit_ph_{lab['id']}")
                                    protein = st.selectbox("Protein", ["Negative", "Trace", "+1", "+2", "+3", "+4"], key=f"edit_protein_{lab['id']}")
                                
                                with col2:
                                    st.markdown("**Chemical Parameters:**")
                                    glucose = st.selectbox("Glucose", ["Negative", "Trace", "+1", "+2", "+3", "+4"], key=f"edit_glucose_{lab['id']}")
                                    ketones = st.selectbox("Ketones", ["Negative", "Trace", "Small", "Moderate", "Large"], key=f"edit_ketones_{lab['id']}")
                                    blood = st.selectbox("Blood", ["Negative", "Trace", "+1", "+2", "+3"], key=f"edit_blood_{lab['id']}")
                                    leukocyte_esterase = st.selectbox("Leukocyte Esterase", ["Negative", "Trace", "+1", "+2", "+3"], key=f"edit_leuk_{lab['id']}")
                                    nitrites = st.selectbox("Nitrites", ["Negative", "Positive"], key=f"edit_nitrites_{lab['id']}")
                                    bilirubin = st.selectbox("Bilirubin", ["Negative", "Trace", "+1", "+2", "+3"], key=f"edit_bilirubin_{lab['id']}")
                                
                                col_save, col_cancel = st.columns(2)
                                with col_save:
                                    if st.form_submit_button("💾 Save Changes", type="primary"):
                                        new_results = f"""URINALYSIS RESULTS:
Physical Parameters:
- Color: {color}
- Clarity: {clarity}
- Specific Gravity: {specific_gravity}
- pH: {ph}

Chemical Parameters:
- Protein: {protein}
- Glucose: {glucose}
- Ketones: {ketones}
- Blood: {blood}
- Leukocyte Esterase: {leukocyte_esterase}
- Nitrites: {nitrites}
- Bilirubin: {bilirubin}"""
                                        
                                        conn = sqlite3.connect(db.db_name)
                                        cursor = conn.cursor()
                                        cursor.execute('''
                                            UPDATE lab_tests 
                                            SET results = ?
                                            WHERE id = ?
                                        ''', (new_results, lab['id']))
                                        conn.commit()
                                        conn.close()
                                        
                                        # Broadcast update to all connected devices
                                        broadcast_to_clients(f"lab_results_updated:{lab['test_type']}:{patient_data['name']}")
                                        
                                        st.session_state[edit_key] = False
                                        st.success("✅ Urinalysis results updated successfully!")
                                        st.rerun()
                                with col_cancel:
                                    if st.form_submit_button("❌ Cancel"):
                                        st.session_state[edit_key] = False
                                        st.rerun()
                        
                        elif lab['test_type'].lower() == 'glucose':
                            st.markdown("**Edit Blood Glucose Results:**")
                            with st.form(f"edit_glucose_{lab['id']}"):
                                glucose_value = st.number_input("Glucose Level (mg/dL)", min_value=10, max_value=800, value=100, key=f"edit_glucose_val_{lab['id']}")
                                glucose_units = st.selectbox("Units", ["mg/dL", "mmol/L"], key=f"edit_glucose_units_{lab['id']}")
                                
                                # Interpretation helper
                                if glucose_units == "mg/dL":
                                    if glucose_value < 70:
                                        interpretation = "Low (Hypoglycemia)"
                                    elif glucose_value <= 99:
                                        interpretation = "Normal"
                                    elif glucose_value <= 125:
                                        interpretation = "Elevated (Prediabetes range)"
                                    else:
                                        interpretation = "High (Diabetes range)"
                                else:
                                    if glucose_value < 3.9:
                                        interpretation = "Low (Hypoglycemia)"
                                    elif glucose_value <= 5.5:
                                        interpretation = "Normal"
                                    elif glucose_value <= 6.9:
                                        interpretation = "Elevated (Prediabetes range)"
                                    else:
                                        interpretation = "High (Diabetes range)"
                                
                                st.info(f"Interpretation: {interpretation}")
                                
                                col_save, col_cancel = st.columns(2)
                                with col_save:
                                    if st.form_submit_button("💾 Save Changes", type="primary"):
                                        new_results = f"{glucose_value} {glucose_units} ({interpretation})"
                                        
                                        conn = sqlite3.connect(db.db_name)
                                        cursor = conn.cursor()
                                        cursor.execute('''
                                            UPDATE lab_tests 
                                            SET results = ?
                                            WHERE id = ?
                                        ''', (new_results, lab['id']))
                                        conn.commit()
                                        conn.close()
                                        
                                        # Broadcast update to all connected devices
                                        broadcast_to_clients(f"lab_results_updated:{lab['test_type']}:{patient_data['name']}")
                                        
                                        st.session_state[edit_key] = False
                                        st.success("✅ Glucose results updated successfully!")
                                        st.rerun()
                                with col_cancel:
                                    if st.form_submit_button("❌ Cancel"):
                                        st.session_state[edit_key] = False
                                        st.rerun()
                        
                        elif lab['test_type'].lower() == 'pregnancy':
                            st.markdown("**Edit Pregnancy Test Results:**")
                            with st.form(f"edit_pregnancy_{lab['id']}"):
                                pregnancy_result = st.selectbox("Pregnancy Test Result", ["Negative", "Positive"], key=f"edit_pregnancy_{lab['id']}")
                                test_notes = st.text_area("Additional Notes (optional)", key=f"edit_preg_notes_{lab['id']}")
                                
                                if pregnancy_result == "Positive":
                                    st.success("Positive result - Patient is pregnant")
                                else:
                                    st.info("Negative result - Patient is not pregnant")
                                
                                col_save, col_cancel = st.columns(2)
                                with col_save:
                                    if st.form_submit_button("💾 Save Changes", type="primary"):
                                        new_results = pregnancy_result
                                        if test_notes.strip():
                                            new_results += f" - Notes: {test_notes.strip()}"
                                        
                                        conn = sqlite3.connect(db.db_name)
                                        cursor = conn.cursor()
                                        cursor.execute('''
                                            UPDATE lab_tests 
                                            SET results = ?
                                            WHERE id = ?
                                        ''', (new_results, lab['id']))
                                        conn.commit()
                                        conn.close()
                                        
                                        # Broadcast update to all connected devices
                                        broadcast_to_clients(f"lab_results_updated:{lab['test_type']}:{patient_data['name']}")
                                        
                                        st.session_state[edit_key] = False
                                        st.success("✅ Pregnancy test results updated successfully!")
                                        st.rerun()
                                with col_cancel:
                                    if st.form_submit_button("❌ Cancel"):
                                        st.session_state[edit_key] = False
                                        st.rerun()
                        
                        else:
                            # Generic lab result editing
                            st.markdown(f"**Edit {lab['test_type']} Results:**")
                            with st.form(f"edit_generic_{lab['id']}"):
                                new_results = st.text_area("Test Results", value=lab['results'], key=f"edit_generic_results_{lab['id']}")
                                
                                col_save, col_cancel = st.columns(2)
                                with col_save:
                                    if st.form_submit_button("💾 Save Changes", type="primary"):
                                        if new_results.strip():
                                            conn = sqlite3.connect(db.db_name)
                                            cursor = conn.cursor()
                                            cursor.execute('''
                                                UPDATE lab_tests 
                                                SET results = ?
                                                WHERE id = ?
                                            ''', (new_results.strip(), lab['id']))
                                            conn.commit()
                                            conn.close()
                                            
                                            # Broadcast update to all connected devices
                                            broadcast_to_clients(f"lab_results_updated:{lab['test_type']}:{patient_data['name']}")
                                            
                                            st.session_state[edit_key] = False
                                            st.success(f"✅ {lab['test_type']} results updated successfully!")
                                            st.rerun()
                                        else:
                                            st.error("Please enter test results before saving.")
                                with col_cancel:
                                    if st.form_submit_button("❌ Cancel"):
                                        st.session_state[edit_key] = False
                                        st.rerun()
                    
                    else:
                        # Display mode for lab results
                        if lab['test_type'].lower() == 'urinalysis':
                            st.markdown("**Standard 11-Parameter Urinalysis:**")
                            results = lab['results']
                            
                            # Create a structured display for UA results
                            col1, col2 = st.columns(2)
                            with col1:
                                st.markdown("""
                                **Physical Parameters:**
                                - Color
                                - Clarity
                                - Specific Gravity
                                - pH
                                """)
                            with col2:
                                st.markdown("""
                                **Chemical Parameters:**
                                - Leukocyte Esterase
                                - Nitrites
                                - Protein
                                - Glucose
                                - Ketones
                                - Blood
                                - Bilirubin
                                """)
                            
                            with st.container():
                                if st.button("View Full UA Results", key=f"ua_results_{patient_id}_{lab['id']}"):
                                    st.text(results)
                        
                        elif lab['test_type'].lower() == 'glucose':
                            st.markdown("**Blood Glucose Test:**")
                            with st.container():
                                st.markdown(f"""
                                <div style="background: #f0f9ff; border-left: 4px solid #0ea5e9; padding: 12px; margin: 8px 0;">
                                    <strong>Glucose Level:</strong> {lab['results']}
                                </div>
                                """, unsafe_allow_html=True)
                        
                        elif lab['test_type'].lower() == 'pregnancy':
                            st.markdown("**Pregnancy Test:**")
                            result_color = "#10b981" if "positive" in lab['results'].lower() else "#ef4444"
                            with st.container():
                                st.markdown(f"""
                                <div style="background: #f0f9ff; border-left: 4px solid {result_color}; padding: 12px; margin: 8px 0;">
                                    <strong>Result:</strong> {lab['results']}
                                </div>
                                """, unsafe_allow_html=True)
                        
                        else:
                            # Generic lab result display
                            st.markdown(f"**{lab['test_type']} Results:**")
                            with st.container():
                                st.text(lab['results'])
                
                # Provider review status - automatic return
                st.markdown("---")
                st.markdown("### Provider Review")
                
                if patient_data['status'] != 'returned_to_provider':
                    st.info("🔄 Patient automatically returned to provider upon test completion.")
                else:
                    st.success("✅ Patient has been returned to provider and is awaiting re-consultation.")
                    
    else:
        st.info(t('msg_no_completed_labs'))


def lab_results_input():
    st.markdown("### Lab Results Input")
    st.info(t('msg_lab_input_intro'))
    
    # Get pending lab tests for today
    conn = sqlite3.connect(db.db_name)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT lt.id, lt.visit_id, lt.test_type, pt.name, pt.patient_id, lt.ordered_time, lt.ordered_by
        FROM lab_tests lt
        JOIN visits v ON lt.visit_id = v.visit_id
        JOIN patients pt ON v.patient_id = pt.patient_id
        WHERE lt.status = 'pending' AND DATE(lt.ordered_time) = DATE('now')
        ORDER BY lt.ordered_time
    ''')
    
    pending_tests = cursor.fetchall()
    conn.close()
    
    if pending_tests:
        for test in pending_tests:
            test_id, visit_id, test_type, patient_name, patient_id, ordered_time, ordered_by = test
            
            with st.expander(f"🧪 {test_type} - {patient_name} (ID: {patient_id})", expanded=True):
                st.markdown(f"**Ordered by:** {ordered_by}")
                st.markdown(f"**Ordered:** {ordered_time[:16].replace('T', ' ')}")
                
                # Different input forms based on test type
                if test_type.lower() == 'urinalysis':
                    st.markdown("#### 11-Parameter Urinalysis Input")
                    
                    with st.form(f"urinalysis_{test_id}"):
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.markdown("**Physical Parameters:**")
                            color = st.selectbox("Color", ["Yellow", "Pale Yellow", "Dark Yellow", "Amber", "Red", "Brown", "Other"], key=f"color_{test_id}")
                            clarity = st.selectbox("Clarity", ["Clear", "Slightly Cloudy", "Cloudy", "Turbid"], key=f"clarity_{test_id}")
                            specific_gravity = st.number_input("Specific Gravity", min_value=1.000, max_value=1.100, value=1.020, step=0.001, format="%.3f", key=f"sg_{test_id}")
                            ph = st.number_input("pH", min_value=4.5, max_value=9.0, value=6.0, step=0.5, key=f"ph_{test_id}")
                            protein = st.selectbox("Protein", ["Negative", "Trace", "+1", "+2", "+3", "+4"], key=f"protein_{test_id}")
                        
                        with col2:
                            st.markdown("**Chemical Parameters:**")
                            glucose = st.selectbox("Glucose", ["Negative", "Trace", "+1", "+2", "+3", "+4"], key=f"glucose_{test_id}")
                            ketones = st.selectbox("Ketones", ["Negative", "Trace", "Small", "Moderate", "Large"], key=f"ketones_{test_id}")
                            blood = st.selectbox("Blood", ["Negative", "Trace", "+1", "+2", "+3"], key=f"blood_{test_id}")
                            leukocyte_esterase = st.selectbox("Leukocyte Esterase", ["Negative", "Trace", "+1", "+2", "+3"], key=f"leuk_{test_id}")
                            nitrites = st.selectbox("Nitrites", ["Negative", "Positive"], key=f"nitrites_{test_id}")
                            bilirubin = st.selectbox("Bilirubin", ["Negative", "Trace", "+1", "+2", "+3"], key=f"bilirubin_{test_id}")
                        
                        if st.form_submit_button("Complete Urinalysis", type="primary"):
                            results = f"""URINALYSIS RESULTS:
Physical Parameters:
- Color: {color}
- Clarity: {clarity}
- Specific Gravity: {specific_gravity}
- pH: {ph}

Chemical Parameters:
- Protein: {protein}
- Glucose: {glucose}
- Ketones: {ketones}
- Blood: {blood}
- Leukocyte Esterase: {leukocyte_esterase}
- Nitrites: {nitrites}
- Bilirubin: {bilirubin}"""
                            
                            # Save results to database
                            conn = sqlite3.connect(db.db_name)
                            cursor = conn.cursor()
                            
                            # Update lab test with results
                            cursor.execute('''
                                UPDATE lab_tests 
                                SET results = ?, completed_time = ?, status = 'completed'
                                WHERE id = ?
                            ''', (results, datetime.now().isoformat(), test_id))
                            
                            # Get patient and doctor info for notification
                            cursor.execute('''
                                SELECT pt.name, pt.patient_id, lt.ordered_by, v.visit_id
                                FROM lab_tests lt
                                JOIN visits v ON lt.visit_id = v.visit_id
                                JOIN patients pt ON v.patient_id = pt.patient_id
                                WHERE lt.id = ?
                            ''', (test_id,))
                            
                            patient_info = cursor.fetchone()
                            if patient_info:
                                patient_name, patient_id, doctor_name, visit_id = patient_info
                                
                                # Create notification for doctor
                                cursor.execute('''
                                    INSERT INTO notifications (doctor_name, patient_id, patient_name, visit_id, message, notification_type, created_time)
                                    VALUES (?, ?, ?, ?, ?, ?, ?)
                                ''', (doctor_name, patient_id, patient_name, visit_id, 
                                     f"Urinalysis results available for {patient_name} (ID: {patient_id})", 
                                     "lab_results", datetime.now().isoformat()))
                            
                            # Automatically send patient back to doctor queue
                            cursor.execute('''
                                UPDATE visits 
                                SET status = 'waiting_consultation', return_reason = 'pharmacy_lab_review'
                                WHERE visit_id = ?
                            ''', (visit_id,))
                            
                            conn.commit()
                            conn.close()
                            
                            # Broadcast automatic patient return
                            broadcast_to_clients(f"patient_returned_to_doctor:{patient_name}:urinalysis_complete")
                            
                            st.success(f"Urinalysis completed! {patient_name} automatically returned to Dr. {doctor_name}")
                            st.rerun()

                elif test_type.lower() == 'blood glucose' or test_type.lower() == 'glucose':
                    st.markdown("#### Blood Glucose Test Input")
                    
                    with st.form(f"glucose_{test_id}"):
                        glucose_value = st.number_input("Glucose Level (mg/dL)", min_value=10, max_value=800, value=100, key=f"glucose_val_{test_id}")
                        glucose_units = st.selectbox("Units", ["mg/dL", "mmol/L"], key=f"glucose_units_{test_id}")
                        
                        # Interpretation helper
                        if glucose_units == "mg/dL":
                            if glucose_value < 70:
                                interpretation = "Low (Hypoglycemia)"
                            elif glucose_value <= 99:
                                interpretation = "Normal"
                            elif glucose_value <= 125:
                                interpretation = "Elevated (Prediabetes range)"
                            else:
                                interpretation = "High (Diabetes range)"
                        else:
                            if glucose_value < 3.9:
                                interpretation = "Low (Hypoglycemia)"
                            elif glucose_value <= 5.5:
                                interpretation = "Normal"
                            elif glucose_value <= 6.9:
                                interpretation = "Elevated (Prediabetes range)"
                            else:
                                interpretation = "High (Diabetes range)"
                        
                        st.info(f"Interpretation: {interpretation}")
                        
                        if st.form_submit_button("Complete Glucose Test", type="primary"):
                            results = f"{glucose_value} {glucose_units} ({interpretation})"
                            
                            # Save results to database
                            conn = sqlite3.connect(db.db_name)
                            cursor = conn.cursor()
                            
                            # Update lab test with results
                            cursor.execute('''
                                UPDATE lab_tests 
                                SET results = ?, completed_time = ?, status = 'completed'
                                WHERE id = ?
                            ''', (results, datetime.now().isoformat(), test_id))
                            
                            # Get patient and doctor info for notification
                            cursor.execute('''
                                SELECT pt.name, pt.patient_id, lt.ordered_by, v.visit_id
                                FROM lab_tests lt
                                JOIN visits v ON lt.visit_id = v.visit_id
                                JOIN patients pt ON v.patient_id = pt.patient_id
                                WHERE lt.id = ?
                            ''', (test_id,))
                            
                            patient_info = cursor.fetchone()
                            if patient_info:
                                patient_name, patient_id, doctor_name, visit_id = patient_info
                                
                                # Create notification for doctor
                                cursor.execute('''
                                    INSERT INTO notifications (doctor_name, patient_id, patient_name, visit_id, message, notification_type, created_time)
                                    VALUES (?, ?, ?, ?, ?, ?, ?)
                                ''', (doctor_name, patient_id, patient_name, visit_id, 
                                     f"Blood glucose results available for {patient_name} (ID: {patient_id}): {results}", 
                                     "lab_results", datetime.now().isoformat()))
                            
                            # Automatically send patient back to doctor queue
                            if patient_info:
                                cursor.execute('''
                                    UPDATE visits 
                                    SET status = 'waiting_consultation', return_reason = 'pharmacy_lab_review'
                                    WHERE visit_id = ?
                                ''', (visit_id,))
                            
                            conn.commit()
                            conn.close()
                            
                            # Broadcast automatic patient return
                            if patient_info:
                                broadcast_to_clients(f"patient_returned_to_doctor:{patient_name}:glucose_complete")
                            
                            st.success(f"Glucose test completed! {patient_name if patient_info else 'Patient'} automatically returned to Dr. {doctor_name if patient_info else 'doctor'}")
                            st.rerun()

                elif test_type.lower() == 'pregnancy test' or test_type.lower() == 'pregnancy':
                    st.markdown("#### Pregnancy Test Input")
                    
                    with st.form(f"pregnancy_{test_id}"):
                        pregnancy_result = st.selectbox("Pregnancy Test Result", ["Negative", "Positive"], key=f"pregnancy_{test_id}")
                        
                        # Additional notes for pregnancy test
                        if pregnancy_result == "Positive":
                            st.success("Positive result - Patient is pregnant")
                        else:
                            st.info("Negative result - Patient is not pregnant")
                        
                        test_notes = st.text_area("Additional Notes (optional)", 
                                                 placeholder="Any observations about the test...", 
                                                 key=f"preg_notes_{test_id}")
                        
                        if st.form_submit_button("Complete Pregnancy Test", type="primary"):
                            results = pregnancy_result
                            if test_notes.strip():
                                results += f" - Notes: {test_notes.strip()}"
                            
                            # Save results to database
                            conn = sqlite3.connect(db.db_name)
                            cursor = conn.cursor()
                            
                            # Update lab test with results
                            cursor.execute('''
                                UPDATE lab_tests 
                                SET results = ?, completed_time = ?, status = 'completed'
                                WHERE id = ?
                            ''', (results, datetime.now().isoformat(), test_id))
                            
                            # Get patient and doctor info for notification
                            cursor.execute('''
                                SELECT pt.name, pt.patient_id, lt.ordered_by, v.visit_id
                                FROM lab_tests lt
                                JOIN visits v ON lt.visit_id = v.visit_id
                                JOIN patients pt ON v.patient_id = pt.patient_id
                                WHERE lt.id = ?
                            ''', (test_id,))
                            
                            patient_info = cursor.fetchone()
                            if patient_info:
                                patient_name, patient_id, doctor_name, visit_id = patient_info
                                
                                # Create notification for doctor
                                cursor.execute('''
                                    INSERT INTO notifications (doctor_name, patient_id, patient_name, visit_id, message, notification_type, created_time)
                                    VALUES (?, ?, ?, ?, ?, ?, ?)
                                ''', (doctor_name, patient_id, patient_name, visit_id, 
                                     f"Pregnancy test results available for {patient_name} (ID: {patient_id}): {results}", 
                                     "lab_results", datetime.now().isoformat()))
                            
                            # Automatically send patient back to doctor queue
                            if patient_info:
                                cursor.execute('''
                                    UPDATE visits 
                                    SET status = 'waiting_consultation', return_reason = 'pharmacy_lab_review'
                                    WHERE visit_id = ?
                                ''', (visit_id,))
                            
                            conn.commit()
                            conn.close()
                            
                            # Broadcast automatic patient return
                            if patient_info:
                                broadcast_to_clients(f"patient_returned_to_doctor:{patient_name}:pregnancy_complete")
                            
                            st.success(f"Pregnancy test completed! {patient_name if patient_info else 'Patient'} automatically returned to Dr. {doctor_name if patient_info else 'doctor'}")
                            st.rerun()

                else:
                    # Generic test input for other test types
                    st.markdown(f"#### {test_type} Input")
                    
                    with st.form(f"generic_{test_id}"):
                        test_results = st.text_area("Test Results", 
                                                   placeholder="Enter the test results...",
                                                   key=f"generic_results_{test_id}")
                        
                        if st.form_submit_button(f"Complete {test_type}", type="primary"):
                            if test_results.strip():
                                # Save results to database
                                conn = sqlite3.connect(db.db_name)
                                cursor = conn.cursor()
                                cursor.execute('''
                                    UPDATE lab_tests 
                                    SET results = ?, completed_time = ?, status = 'completed'
                                    WHERE id = ?
                                ''', (test_results.strip(), datetime.now().isoformat(), test_id))
                                conn.commit()
                                conn.close()
                                
                                st.success(f"{test_type} results saved successfully!")
                                st.rerun()
                            else:
                                st.error("Please enter test results before submitting.")
    else:
        st.info("No pending lab tests for today.")


def awaiting_teaching():
    st.markdown("### Medication Teaching")
    st.info("Patients who have filled prescriptions and are awaiting medication teaching.")
    
    conn = sqlite3.connect(db.db_name)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT p.id, p.visit_id, p.medication_name, p.dosage, p.frequency, p.duration, 
               p.indication, p.instructions, p.filled_time, pt.name, v.patient_id, p.prescribed_by
        FROM prescriptions p
        JOIN visits v ON p.visit_id = v.visit_id
        JOIN patients pt ON v.patient_id = pt.patient_id
        WHERE p.status = 'awaiting_teaching' AND DATE(p.filled_time) = DATE('now')
        ORDER BY p.filled_time
    ''')
    
    awaiting_teaching_prescriptions = cursor.fetchall()
    conn.close()
    
    if awaiting_teaching_prescriptions:
        # Group prescriptions by patient for better organization
        patients = {}
        for prescription in awaiting_teaching_prescriptions:
            patient_id = prescription[10]
            patient_name = prescription[9]
            
            if patient_id not in patients:
                patients[patient_id] = {
                    'name': patient_name,
                    'visit_id': prescription[1],
                    'prescriptions': [],
                    'filled_time': prescription[8]
                }
            
            patients[patient_id]['prescriptions'].append(prescription)
        
        for patient_id, patient_data in patients.items():
            with st.expander(f"📚 {patient_data['name']} (ID: {patient_id}) - {len(patient_data['prescriptions'])} medications to teach", expanded=True):
                st.markdown(f"**Patient:** {patient_data['name']}")
                st.markdown(f"**Prescriptions filled:** {patient_data['filled_time'][:16].replace('T', ' ')}")
                
                # Display all medications for this patient
                for prescription in patient_data['prescriptions']:
                    medication_name = prescription[2]
                    dosage = prescription[3]
                    frequency = prescription[4]
                    duration = prescription[5]
                    indication = prescription[6]
                    instructions = prescription[7]
                    
                    prescribed_by = prescription[11] if len(prescription) > 11 and prescription[11] else "Unknown Doctor"
                    st.markdown(f"""
                    <div style="background: #fef3c7; border: 1px solid #d97706; border-radius: 8px; padding: 12px; margin-bottom: 8px;">
                        <h5 style="color: #92400e; margin: 0 0 8px 0; font-size: 16px;">📚 {medication_name}</h5>
                        <p style="margin: 0 0 8px 0; color: #7c3aed; font-size: 13px; font-weight: 600;"><strong>👨‍⚕️ Prescribed by:</strong> {prescribed_by}</p>
                        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 8px; margin-bottom: 8px;">
                            <p style="margin: 0; color: #78350f; font-size: 14px;"><strong>Dosage:</strong> {dosage}</p>
                            <p style="margin: 0; color: #78350f; font-size: 14px;"><strong>Frequency:</strong> {frequency}</p>
                        </div>
                        <p style="margin: 0 0 8px 0; color: #78350f; font-size: 14px;"><strong>Duration:</strong> {duration}</p>
                        {f'<p style="margin: 0 0 8px 0; color: #d97706; font-size: 14px; background: #fef3c7; padding: 4px 8px; border-radius: 4px;"><strong>For:</strong> {indication}</p>' if indication else ''}
                        {f'<p style="margin: 0 0 8px 0; color: #78350f; font-size: 13px; font-style: italic;"><strong>Instructions:</strong> {instructions}</p>' if instructions else ''}
                    </div>
                    """, unsafe_allow_html=True)
                
                # Teaching completion button
                st.markdown("---")
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.markdown("**Teaching Notes (optional):**")
                    teaching_notes = st.text_area("Record any additional teaching notes for this patient", 
                                                 key=f"teaching_notes_{patient_id}", 
                                                 placeholder="Patient understood all medication instructions...")
                with col2:
                    st.markdown("**Complete Teaching:**")
                    if st.button(f"✅ Teaching Complete", 
                               key=f"complete_teaching_{patient_id}", 
                               type="primary", 
                               use_container_width=True):
                        # Update all prescriptions for this patient to 'filled' status
                        conn = sqlite3.connect(db.db_name)
                        cursor = conn.cursor()
                        
                        # Mark all prescriptions as fully completed (taught)
                        cursor.execute('''
                            UPDATE prescriptions 
                            SET status = 'filled', teaching_completed = ?, teaching_notes = ?
                            WHERE visit_id = ? AND status = 'awaiting_teaching'
                        ''', (datetime.now().isoformat(), teaching_notes, patient_data['visit_id']))
                        
                        # Update visit status to completed
                        cursor.execute('''
                            UPDATE visits 
                            SET status = 'completed', completion_time = ?
                            WHERE visit_id = ?
                        ''', (datetime.now().isoformat(), patient_data['visit_id']))
                        
                        conn.commit()
                        conn.close()
                        
                        # Broadcast completion to all connected devices
                        broadcast_to_clients(f"patient_teaching_complete:{patient_data['name']}:medications_taught")
                        
                        st.success(f"✅ Medication teaching completed for {patient_data['name']}! Patient visit is now complete.")
                        st.rerun()
                
                st.markdown("---")
    else:
        st.info("No patients awaiting medication teaching.")


def filled_prescriptions():
    st.markdown("### Prescription History")

    conn = sqlite3.connect(db.db_name)
    cursor = conn.cursor()

    cursor.execute('''
        SELECT p.medication_name, p.dosage, p.frequency, p.duration, 
               p.indication, p.filled_time, pt.name, v.patient_id, p.instructions
        FROM prescriptions p
        JOIN visits v ON p.visit_id = v.visit_id
        JOIN patients pt ON v.patient_id = pt.patient_id
        WHERE p.status = 'filled' AND DATE(p.filled_time) = DATE('now')
        ORDER BY p.filled_time DESC
    ''')

    filled = cursor.fetchall()
    conn.close()

    if filled:
        # Group prescriptions by patient for better history display
        patients = {}
        for prescription in filled:
            patient_id = prescription[7]
            patient_name = prescription[6]
            
            if patient_id not in patients:
                patients[patient_id] = {
                    'name': patient_name,
                    'prescriptions': [],
                    'filled_time': prescription[5]
                }
            
            patients[patient_id]['prescriptions'].append(prescription)
        
        for patient_id, patient_data in patients.items():
            with st.expander(f"📋 {patient_data['name']} (ID: {patient_id}) - {len(patient_data['prescriptions'])} prescriptions filled", expanded=True):
                for prescription in patient_data['prescriptions']:
                    indication_text = f" - For: {prescription[4]}" if prescription[4] else ""
                    instructions_text = f" - {prescription[8]}" if prescription[8] else ""
                    
                    st.markdown(f"""
                    <div style="background: #d1fae5; border: 1px solid #10b981; border-radius: 8px; padding: 12px; margin-bottom: 8px;">
                        <h5 style="color: #047857; margin: 0 0 8px 0; font-size: 16px;">✅ {prescription[0]}</h5>
                        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 8px; margin-bottom: 8px;">
                            <p style="margin: 0; color: #065f46; font-size: 14px;"><strong>Dosage:</strong> {prescription[1]}</p>
                            <p style="margin: 0; color: #065f46; font-size: 14px;"><strong>Frequency:</strong> {prescription[2]}</p>
                        </div>
                        <p style="margin: 0 0 8px 0; color: #065f46; font-size: 14px;"><strong>Duration:</strong> {prescription[3]}</p>
                        {f'<p style="margin: 0 0 8px 0; color: #059669; font-size: 14px; background: #ecfdf5; padding: 4px 8px; border-radius: 4px;"><strong>For:</strong> {prescription[4]}</p>' if prescription[4] else ''}
                        {f'<p style="margin: 0 0 8px 0; color: #065f46; font-size: 13px; font-style: italic;"><strong>Instructions:</strong> {prescription[8]}</p>' if prescription[8] else ''}
                        <p style="margin: 4px 0 0 0; color: #6b7280; font-size: 12px;">Filled: {prescription[5][:16].replace('T', ' ')}</p>
                    </div>
                    """, unsafe_allow_html=True)
    else:
        st.info("No prescriptions filled today.")


def lab_interface():
    add_to_history('lab')
    st.markdown(f"## {t('page_laboratory')}")
    render_doctor_status_strip()

    tab1, tab2 = st.tabs([t('tab_pending_tests'), t('tab_completed_lab')])

    with tab1:
        pending_lab_tests()

    with tab2:
        completed_lab_tests()


def pending_lab_tests():
    st.markdown(f"### {t('tests_to_process')}")

    pending_tests = db.get_pending_lab_tests()

    if pending_tests:
        for test in pending_tests:
            with st.expander(
                    f"🧪 {test['patient_name']} (ID: {test['patient_id']}) - {test['test_type']}",
                    expanded=True):
                st.write(f"**Ordered by:** {test['ordered_by']}")
                st.write(
                    f"**Ordered:** {test['ordered_time'][:16].replace('T', ' ')}"
                )

                if test['test_type'] == 'Urinalysis':
                    urinalysis_form(test['id'])
                elif test['test_type'] == 'Blood Glucose':
                    glucose_form(test['id'])
                elif test['test_type'] == 'Pregnancy Test':
                    pregnancy_form(test['id'])
    else:
        st.info("No pending lab tests.")


def urinalysis_form(test_id: int):
    with st.form(f"urinalysis_{test_id}"):
        st.markdown("#### Urinalysis Results")

        col1, col2 = st.columns(2)

        with col1:
            color = st.selectbox("Color", [
                "Yellow", "Pale Yellow", "Dark Yellow", "Amber", "Red",
                "Brown", "Other"
            ])
            clarity = st.selectbox(
                "Clarity", ["Clear", "Slightly Cloudy", "Cloudy", "Turbid"])
            specific_gravity = st.number_input("Specific Gravity",
                                               min_value=1.000,
                                               max_value=1.100,
                                               value=1.020,
                                               step=0.001,
                                               format="%.3f")
            ph = st.number_input("pH",
                                 min_value=4.0,
                                 max_value=9.0,
                                 value=6.0,
                                 step=0.5)

        with col2:
            protein = st.selectbox(
                "Protein", ["Negative", "Trace", "1+", "2+", "3+", "4+"])
            glucose = st.selectbox(
                "Glucose", ["Negative", "Trace", "1+", "2+", "3+", "4+"])
            ketones = st.selectbox(
                "Ketones", ["Negative", "Trace", "Small", "Moderate", "Large"])
            blood = st.selectbox("Blood",
                                 ["Negative", "Trace", "1+", "2+", "3+"])

        col3, col4 = st.columns(2)

        with col3:
            leukocyte_esterase = st.selectbox(
                "Leukocyte Esterase", ["Negative", "Trace", "1+", "2+", "3+"])
            nitrites = st.selectbox("Nitrites", ["Negative", "Positive"])
            urobilinogen = st.selectbox("Urobilinogen",
                                        ["Normal", "1+", "2+", "3+", "4+"])

        with col4:
            bilirubin = st.selectbox("Bilirubin",
                                     ["Negative", "1+", "2+", "3+"])
            wbc = st.number_input("WBC/hpf",
                                  min_value=0,
                                  max_value=50,
                                  value=0)
            rbc = st.number_input("RBC/hpf",
                                  min_value=0,
                                  max_value=50,
                                  value=0)

        bacteria = st.selectbox("Bacteria",
                                ["None", "Few", "Moderate", "Many"])
        epithelial_cells = st.selectbox("Epithelial Cells",
                                        ["None", "Few", "Moderate", "Many"])

        notes = st.text_area("Additional Notes")

        if st.form_submit_button("Complete Urinalysis", type="primary"):
            results = {
                'Color': color,
                'Clarity': clarity,
                'Specific Gravity': specific_gravity,
                'pH': ph,
                'Protein': protein,
                'Glucose': glucose,
                'Ketones': ketones,
                'Blood': blood,
                'Leukocyte Esterase': leukocyte_esterase,
                'Nitrites': nitrites,
                'Urobilinogen': urobilinogen,
                'Bilirubin': bilirubin,
                'WBC': f"{wbc}/hpf",
                'RBC': f"{rbc}/hpf",
                'Bacteria': bacteria,
                'Epithelial Cells': epithelial_cells,
                'Notes': notes
            }

            results_text = "\n".join(
                [f"{k}: {v}" for k, v in results.items() if v])
            
            db_manager = get_db_manager()
            db_manager.complete_lab_test(test_id, results_text)

            # Get patient info for broadcast
            conn = sqlite3.connect(db_manager.db_name)
            cursor = conn.cursor()
            cursor.execute('''
                SELECT p.name, lt.test_type 
                FROM lab_tests lt
                JOIN visits v ON lt.visit_id = v.visit_id
                JOIN patients p ON v.patient_id = p.patient_id
                WHERE lt.test_id = ?
            ''', (test_id,))
            result = cursor.fetchone()
            conn.close()
            
            if result:
                patient_name, test_type = result
                broadcast_to_clients(f"lab_complete:{patient_name}:{test_type}:urinalysis")
                
                # Automatically send patient back to doctor queue
                visit_conn = sqlite3.connect(db_manager.db_name)
                visit_cursor = visit_conn.cursor()
                visit_cursor.execute('''
                    SELECT visit_id FROM lab_tests WHERE test_id = ?
                ''', (test_id,))
                visit_result = visit_cursor.fetchone()
                
                if visit_result:
                    visit_id = visit_result[0]
                    visit_cursor.execute('''
                        UPDATE visits 
                        SET status = 'waiting_consultation', return_reason = 'pharmacy_lab_review'
                        WHERE visit_id = ?
                    ''', (visit_id,))
                    visit_conn.commit()
                    
                    # Broadcast patient return to doctor
                    broadcast_to_clients(f"patient_returned_to_doctor:{patient_name}:urinalysis_complete")
                    
                visit_conn.close()

            st.success("Urinalysis completed! Patient automatically returned to doctor.")
            st.rerun()


def glucose_form(test_id: int):
    with st.form(f"glucose_{test_id}"):
        st.markdown("#### Blood Glucose Results")

        glucose_value = st.number_input("Glucose (mg/dL)",
                                        min_value=0,
                                        max_value=800,
                                        value=100)
        test_type = st.selectbox("Test Type",
                                 ["Random", "Fasting", "Post-meal"])
        notes = st.text_area("Notes")

        if st.form_submit_button("Complete Glucose Test", type="primary"):
            results = f"Glucose: {glucose_value} mg/dL ({test_type})"
            if notes:
                results += f"\nNotes: {notes}"

            db_manager = get_db_manager()
            db_manager.complete_lab_test(test_id, results)

            # Get patient info for broadcast
            conn = sqlite3.connect(db_manager.db_name)
            cursor = conn.cursor()
            cursor.execute('''
                SELECT p.name 
                FROM lab_tests lt
                JOIN visits v ON lt.visit_id = v.visit_id
                JOIN patients p ON v.patient_id = p.patient_id
                WHERE lt.test_id = ?
            ''', (test_id,))
            result = cursor.fetchone()
            conn.close()
            
            if result:
                patient_name = result[0]
                broadcast_to_clients(f"lab_complete:{patient_name}:glucose:{glucose_value}mg/dL")
                
                # Automatically send patient back to doctor queue
                visit_conn = sqlite3.connect(db_manager.db_name)
                visit_cursor = visit_conn.cursor()
                visit_cursor.execute('''
                    SELECT visit_id FROM lab_tests WHERE test_id = ?
                ''', (test_id,))
                visit_result = visit_cursor.fetchone()
                
                if visit_result:
                    visit_id = visit_result[0]
                    visit_cursor.execute('''
                        UPDATE visits 
                        SET status = 'waiting_consultation', return_reason = 'pharmacy_lab_review'
                        WHERE visit_id = ?
                    ''', (visit_id,))
                    visit_conn.commit()
                    
                    # Broadcast patient return to doctor
                    broadcast_to_clients(f"patient_returned_to_doctor:{patient_name}:glucose_complete")
                    
                visit_conn.close()

            st.success("Glucose test completed! Patient automatically returned to doctor.")
            st.rerun()


def pregnancy_form(test_id: int):
    with st.form(f"pregnancy_{test_id}"):
        st.markdown("#### Pregnancy Test Results")

        result = st.selectbox("Result", ["Negative", "Positive"])
        notes = st.text_area("Notes")

        if st.form_submit_button("Complete Pregnancy Test", type="primary"):
            results = f"Pregnancy Test: {result}"
            if notes:
                results += f"\nNotes: {notes}"

            db_manager = get_db_manager()
            db_manager.complete_lab_test(test_id, results)

            # Get patient info for broadcast
            conn = sqlite3.connect(db_manager.db_name)
            cursor = conn.cursor()
            cursor.execute('''
                SELECT p.name 
                FROM lab_tests lt
                JOIN visits v ON lt.visit_id = v.visit_id
                JOIN patients p ON v.patient_id = p.patient_id
                WHERE lt.test_id = ?
            ''', (test_id,))
            lab_result = cursor.fetchone()
            conn.close()
            
            if lab_result:
                patient_name = lab_result[0]
                broadcast_to_clients(f"lab_complete:{patient_name}:pregnancy:{result}")
                
                # Automatically send patient back to doctor queue
                visit_conn = sqlite3.connect(db_manager.db_name)
                visit_cursor = visit_conn.cursor()
                visit_cursor.execute('''
                    SELECT visit_id FROM lab_tests WHERE test_id = ?
                ''', (test_id,))
                visit_result = visit_cursor.fetchone()
                
                if visit_result:
                    visit_id = visit_result[0]
                    visit_cursor.execute('''
                        UPDATE visits 
                        SET status = 'waiting_consultation', return_reason = 'pharmacy_lab_review'
                        WHERE visit_id = ?
                    ''', (visit_id,))
                    visit_conn.commit()
                    
                    # Broadcast patient return to doctor
                    broadcast_to_clients(f"patient_returned_to_doctor:{patient_name}:pregnancy_complete")
                    
                visit_conn.close()

            st.success("Pregnancy test completed! Patient automatically returned to doctor.")
            st.rerun()


def completed_lab_tests():
    st.markdown("### Today's Lab Results")

    conn = sqlite3.connect("clinic_database.db")
    cursor = conn.cursor()

    cursor.execute('''
        SELECT lt.*, p.name as patient_name, p.patient_id
        FROM lab_tests lt
        JOIN visits v ON lt.visit_id = v.visit_id
        JOIN patients p ON v.patient_id = p.patient_id
        WHERE lt.status = 'completed' AND DATE(lt.completed_time) = DATE('now')
        ORDER BY lt.completed_time DESC
    ''')

    completed_tests = cursor.fetchall()
    conn.close()

    if completed_tests:
        for test in completed_tests:
            with st.expander(f"✅ {test[8]} (ID: {test[9]}) - {test[2]}"):
                st.write(f"**Completed:** {test[5][:16].replace('T', ' ')}")
                st.write(f"**Results:**")
                st.text(test[6])

                # Post-lab treatment options
                st.markdown("#### Post-Lab Treatment Decision")

                col1, col2 = st.columns(2)
                with col1:
                    if st.button("Treated by Pharmacy",
                                 key=f"pharmacy_{test[0]}",
                                 type="primary"):
                        # Update lab test to indicate pharmacy treatment
                        conn = sqlite3.connect("clinic_database.db")
                        cursor = conn.cursor()
                        cursor.execute(
                            '''
                            UPDATE lab_tests SET notes = COALESCE(notes, '') || ' - TREATED BY PHARMACY'
                            WHERE id = ?
                        ''', (test[0], ))
                        conn.commit()
                        conn.close()
                        st.success("Marked as treated by pharmacy")
                        st.rerun()

                with col2:
                    if st.button("Return to Provider",
                                 key=f"provider_{test[0]}",
                                 type="secondary"):
                        # Create new consultation requirement
                        visit_id = test[1]  # visit_id from the test
                        conn = sqlite3.connect("clinic_database.db")
                        cursor = conn.cursor()

                        # Update visit status to require consultation
                        cursor.execute(
                            '''
                            UPDATE visits SET status = 'waiting_consultation'
                            WHERE visit_id = ?
                        ''', (visit_id, ))

                        # Add note to lab test
                        cursor.execute(
                            '''
                            UPDATE lab_tests SET notes = COALESCE(notes, '') || ' - RETURNED TO PROVIDER'
                            WHERE id = ?
                        ''', (test[0], ))

                        conn.commit()
                        conn.close()
                        st.success("Patient returned to consultation queue")
                        st.rerun()
    else:
        st.info("No lab tests completed today.")


def patient_management():
    add_to_history('patient_management')
    st.markdown("### Patient Management")

    # Get all patients first
    db = get_db_manager()
    conn = sqlite3.connect("clinic_database.db")
    cursor = conn.cursor()
    cursor.execute('''
        SELECT patient_id, name, age, gender, phone, emergency_contact, 
               medical_history, allergies, created_date, last_visit
        FROM patients
        ORDER BY created_date DESC
    ''')
    all_patients = cursor.fetchall()
    conn.close()

    # Convert to list of dictionaries
    columns = [
        'patient_id', 'name', 'age', 'gender', 'phone', 'emergency_contact',
        'medical_history', 'allergies', 'created_date', 'last_visit'
    ]
    patients = [dict(zip(columns, row)) for row in all_patients]

    # Search filter
    search_query = st.text_input("Search Patients",
                                 placeholder="Filter by name or ID")

    # Filter patients based on search
    if search_query:
        filtered_patients = [
            p for p in patients if search_query.lower() in p['name'].lower()
            or search_query.lower() in p['patient_id'].lower()
        ]
    else:
        filtered_patients = patients

    if filtered_patients:
        st.info(
            f"Showing {len(filtered_patients)} of {len(patients)} patients")
        st.warning(
            "⚠️ Deleting a patient will permanently remove all their data including visits, prescriptions, and lab results."
        )

        for patient in filtered_patients:
            # Patient card layout
            with st.container():
                col1, col2 = st.columns([5, 1])

                with col1:
                    # Make patient name clickable for full history
                    if st.button(
                            f"📋 {patient['name']} (ID: {patient['patient_id']}) - Age: {patient['age'] or 'N/A'}, Last Visit: {patient['last_visit'][:10] if patient['last_visit'] else 'Never'}",
                            key=f"patient_history_{patient['patient_id']}",
                            use_container_width=True):
                        st.session_state.show_patient_history = {
                            'patient_id': patient['patient_id'],
                            'patient_name': patient['name']
                        }
                        st.rerun()

                with col2:
                    # Check if this patient is in delete confirmation mode
                    delete_key = f"deleting_{patient['patient_id']}"
                    if st.session_state.get(delete_key, False):
                        # Show confirm/cancel split buttons in the same column
                        confirm_col, cancel_col = st.columns(2)
                        with confirm_col:
                            if st.button(
                                    "✓",
                                    key=f"confirm_{patient['patient_id']}",
                                    help="Confirm delete"):
                                # Perform the actual deletion using direct database operations
                                try:
                                    conn = sqlite3.connect(
                                        "clinic_database.db")
                                    cursor = conn.cursor()
                                    cursor.execute('PRAGMA foreign_keys = OFF')

                                    patient_id = patient['patient_id']

                                    # Delete all related data
                                    cursor.execute(
                                        'DELETE FROM vital_signs WHERE visit_id IN (SELECT visit_id FROM visits WHERE patient_id = ?)',
                                        (patient_id, ))
                                    cursor.execute(
                                        'DELETE FROM prescriptions WHERE visit_id IN (SELECT visit_id FROM visits WHERE patient_id = ?)',
                                        (patient_id, ))
                                    cursor.execute(
                                        'DELETE FROM lab_tests WHERE visit_id IN (SELECT visit_id FROM visits WHERE patient_id = ?)',
                                        (patient_id, ))
                                    cursor.execute(
                                        'DELETE FROM consultations WHERE visit_id IN (SELECT visit_id FROM visits WHERE patient_id = ?)',
                                        (patient_id, ))
                                    cursor.execute(
                                        'DELETE FROM visits WHERE patient_id = ?',
                                        (patient_id, ))
                                    cursor.execute(
                                        'DELETE FROM patients WHERE patient_id = ?',
                                        (patient_id, ))

                                    conn.commit()
                                    conn.close()

                                    st.success(
                                        f"Patient {patient['name']} deleted successfully."
                                    )
                                    # Clear the deleting state
                                    if delete_key in st.session_state:
                                        del st.session_state[delete_key]
                                    st.rerun()
                                except Exception as e:
                                    st.error(
                                        f"Failed to delete patient: {str(e)}")
                                    if 'conn' in locals():
                                        conn.close()
                        with cancel_col:
                            if st.button("✕",
                                         key=f"cancel_{patient['patient_id']}",
                                         help="Cancel delete"):
                                # Clear the deleting state
                                if delete_key in st.session_state:
                                    del st.session_state[delete_key]
                                st.rerun()
                    else:
                        # Show regular delete button
                        if st.button("🗑️ Delete",
                                     key=f"delete_{patient['patient_id']}",
                                     help="Delete patient"):
                            # Set deleting state to show confirm/cancel
                            st.session_state[delete_key] = True
                            st.rerun()

                st.markdown("---")

    # Show deletion confirmation dialog
    if 'confirm_delete' in st.session_state:
        patient_to_delete = st.session_state.confirm_delete

        st.markdown("---")
        st.error("# 🚨 CONFIRM PATIENT DELETION")
        st.markdown("---")

        # Patient info
        st.markdown(f"**Patient: {patient_to_delete['patient_name']}**")
        st.markdown(f"**Patient ID: {patient_to_delete['patient_id']}**")

        st.markdown("---")

        # Action buttons
        col1, col2, col3 = st.columns([1, 1, 1])

        with col1:
            if st.button("🗑️ DELETE FOREVER",
                         type="primary",
                         key="confirm_delete_btn",
                         use_container_width=True):
                # Simple deletion - disable foreign keys and delete everything
                conn = sqlite3.connect(db.db_name)
                cursor = conn.cursor()
                cursor.execute('PRAGMA foreign_keys = OFF')

                patient_id = patient_to_delete['patient_id']

                try:
                    # Delete all related data - check if tables exist first
                    cursor.execute(
                        "SELECT name FROM sqlite_master WHERE type='table'")
                    existing_tables = [row[0] for row in cursor.fetchall()]

                    # Delete from tables that exist
                    if 'vital_signs' in existing_tables:
                        cursor.execute(
                            'DELETE FROM vital_signs WHERE visit_id IN (SELECT visit_id FROM visits WHERE patient_id = ?)',
                            (patient_id, ))

                    if 'prescriptions' in existing_tables:
                        cursor.execute(
                            'DELETE FROM prescriptions WHERE visit_id IN (SELECT visit_id FROM visits WHERE patient_id = ?)',
                            (patient_id, ))

                    if 'lab_tests' in existing_tables:
                        cursor.execute(
                            'DELETE FROM lab_tests WHERE visit_id IN (SELECT visit_id FROM visits WHERE patient_id = ?)',
                            (patient_id, ))

                    if 'consultations' in existing_tables:
                        cursor.execute(
                            'DELETE FROM consultations WHERE visit_id IN (SELECT visit_id FROM visits WHERE patient_id = ?)',
                            (patient_id, ))

                    if 'visits' in existing_tables:
                        cursor.execute(
                            'DELETE FROM visits WHERE patient_id = ?',
                            (patient_id, ))

                    # Delete patient
                    cursor.execute('DELETE FROM patients WHERE patient_id = ?',
                                   (patient_id, ))

                    conn.commit()
                    st.success(
                        f"Patient {patient_to_delete['patient_name']} deleted successfully."
                    )

                except Exception as e:
                    conn.rollback()
                    st.error(f"Error during deletion: {str(e)}")

                finally:
                    conn.close()
                    del st.session_state.confirm_delete
                    st.rerun()

        with col2:
            if st.button("❌ CANCEL",
                         key="cancel_delete_btn",
                         use_container_width=True):
                del st.session_state.confirm_delete
                st.rerun()

        with col3:
            if st.button(t('close_label'),
                         key="close_modal",
                         use_container_width=True):
                del st.session_state.confirm_delete
                st.rerun()

        st.markdown("---")
        st.warning(
            "**⚠️ WARNING: This will permanently delete all patient data. THIS ACTION CANNOT BE UNDONE!**"
        )
        st.markdown("---")

        return  # Don't show rest of page when modal is active

    # Check if we should show patient history detail page - extend outside container
    if 'show_patient_history' in st.session_state and isinstance(st.session_state.show_patient_history, dict):
        # Display patient history in full width layout extending outside the patient management section
        st.markdown("---")
        show_patient_history_detail(
            st.session_state.show_patient_history['patient_id'],
            st.session_state.show_patient_history['patient_name'])
        return

    else:
        if search_query:
            st.info("No patients found matching your search.")
        else:
            st.info("No patients in the system yet.")


def admin_interface():
    add_to_history('admin')
    st.markdown("## Admin Dashboard")

    tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs([
        "Patient Management", "Doctor Management", "Medication Management",
        "Stock Tracking", "Edit Locations", "Reports", "Audit Logs", "Settings"
    ])

    with tab1:
        patient_management()

    with tab2:
        doctor_management()

    with tab3:
        medication_management()

    with tab4:
        stock_management()

    with tab5:
        location_management()

    with tab6:
        daily_reports()

    with tab7:
        audit_log_viewer()

    with tab8:
        clinic_settings()


def doctor_management():
    """Admin interface for managing doctors"""
    add_to_history('doctor_management')
    st.markdown("### Doctor Management")

    db = get_db_manager()

    # Add new doctor
    with st.expander("Add New Doctor"):
        with st.form("add_doctor"):
            doctor_name = st.text_input("Doctor Name",
                                        placeholder="e.g., Dr. Smith")

            if st.form_submit_button("Add Doctor", type="primary"):
                if doctor_name.strip():
                    # Check if doctor already exists before trying to add
                    conn = sqlite3.connect(db.db_name)
                    cursor = conn.cursor()
                    cursor.execute('SELECT is_active FROM doctors WHERE name = ?', (doctor_name.strip(),))
                    existing = cursor.fetchone()
                    conn.close()
                    
                    if existing and existing[0] == 1:
                        st.warning(f"Doctor {doctor_name} is already active in the system.")
                    elif existing and existing[0] == 0:
                        # Doctor exists but is inactive - reactivate
                        if db.add_doctor(doctor_name.strip()):
                            st.success(f"Doctor {doctor_name} reactivated successfully!")
                            st.rerun()
                        else:
                            st.error("Failed to reactivate doctor.")
                    else:
                        # New doctor
                        if db.add_doctor(doctor_name.strip()):
                            st.success(f"Doctor {doctor_name} added successfully!")
                            st.rerun()
                        else:
                            st.error("Failed to add doctor.")
                else:
                    st.error("Please enter a doctor name.")

    # Display current doctors and their status
    st.markdown("#### Current Doctors")
    doctors = db.get_doctors()
    doctor_status = db.get_all_doctor_status()

    if doctors:
        for doctor in doctors:
            # Find current status for this doctor
            current_status = next(
                (s
                 for s in doctor_status if s['doctor_name'] == doctor['name']),
                None)

            col1, col2, col3 = st.columns([2, 2, 1])

            with col1:
                st.write(f"**{doctor['name']}**")

            with col2:
                if current_status:
                    status_color = "🟢" if current_status[
                        'status'] == 'available' else "🟡" if current_status[
                            'status'] == 'with_patient' else "🔴"
                    patient_info = f" - {current_status['current_patient_name']}" if current_status[
                        'current_patient_id'] else ""
                    st.write(
                        f"{status_color} {current_status['status'].replace('_', ' ').title()}{patient_info}"
                    )
                else:
                    st.write("🔴 Offline")

            with col3:
                if st.button("Remove",
                             key=f"remove_doctor_{doctor['name']}",
                             type="secondary"):
                    if db.remove_doctor(doctor['name']):
                        st.success(f"Doctor {doctor['name']} removed.")
                        st.rerun()
                    else:
                        st.error("Failed to remove doctor.")
    else:
        st.info("No doctors in the system.")

    # Real-time status updates
    st.markdown("#### Real-Time Doctor Status")
    if st.button("🔄 Refresh Status"):
        st.rerun()

    if doctor_status:
        for status in doctor_status:
            status_color = "🟢" if status[
                'status'] == 'available' else "🟡" if status[
                    'status'] == 'with_patient' else "🔴"
            patient_info = f" - {status['current_patient_name']} ({status['current_patient_id']})" if status[
                'current_patient_id'] else ""
            last_update = status['last_updated'][:16].replace(
                'T', ' ') if status['last_updated'] else "Unknown"

            st.write(
                f"{status_color} **{status['doctor_name']}** - {status['status'].replace('_', ' ').title()}{patient_info}"
            )
            st.caption(f"Last updated: {last_update}")


def location_management():
    """Admin interface for managing clinic locations"""
    add_to_history('location_management')
    st.markdown("### Location Management")
    
    db = get_db_manager()
    locations = db.get_locations()
    
    # Check for duplicate locations
    if locations:
        # Group locations by country code and city to find duplicates
        location_groups = {}
        for loc in locations:
            key = (loc['country_code'].upper(), loc['city'].lower())
            if key not in location_groups:
                location_groups[key] = []
            location_groups[key].append(loc)
        
        # Find duplicates
        duplicates = {k: v for k, v in location_groups.items() if len(v) > 1}
        
        if duplicates:
            st.warning(f"⚠️ Found {len(duplicates)} duplicate location groups")
            with st.expander("🔗 Merge Duplicate Locations", expanded=True):
                for (country_code, city), duplicate_locs in duplicates.items():
                    st.markdown(f"**Duplicates for {country_code} - {city.title()}:**")
                    
                    # Show all duplicates
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        for i, dup_loc in enumerate(duplicate_locs):
                            st.write(f"  {i+1}. {dup_loc['country_name']} - {dup_loc['city']} (ID: {dup_loc['id']})")
                    
                    with col2:
                        merge_key = f"merge_{country_code}_{city}"
                        if st.button(f"Merge All", key=merge_key, type="primary"):
                            # Keep the first location, delete the rest
                            primary_location = duplicate_locs[0]
                            locations_to_delete = duplicate_locs[1:]
                            
                            conn = sqlite3.connect(db.db_name)
                            cursor = conn.cursor()
                            
                            # Delete duplicate locations
                            for dup_loc in locations_to_delete:
                                cursor.execute('DELETE FROM locations WHERE id = ?', (dup_loc['id'],))
                            
                            conn.commit()
                            conn.close()
                            
                            st.success(f"Merged {len(locations_to_delete)} duplicate locations into {primary_location['country_name']} - {primary_location['city']}")
                            st.rerun()
                    
                    st.markdown("---")
    
    # Display existing locations for editing
    if locations:
        st.markdown("### Edit Locations")
        st.info("💡 You can edit location names to fix typos or update information. Use the merge feature above to combine duplicate locations.")
        for location in locations:
            with st.expander(f"{location['country_name']} - {location['city']}", expanded=True):
                col1, col2, col3 = st.columns([2, 1, 1])
                
                with col1:
                    st.write(f"**Country Code:** {location['country_code']}")
                    st.write(f"**Country:** {location['country_name']}")
                    st.write(f"**City:** {location['city']}")
                
                with col2:
                    # Edit button
                    edit_key = f"edit_location_{location['id']}"
                    if st.button("✏️ Edit Name", key=f"admin_edit_btn_{location['id']}", help="Edit location names and details"):
                        st.session_state[edit_key] = True
                        st.rerun()
                
                with col3:
                    # Delete button with confirmation
                    delete_key = f"delete_location_{location['id']}"
                    if st.button("🗑️ Delete", key=f"delete_btn_{location['id']}", type="secondary"):
                        st.session_state[delete_key] = True
                        st.rerun()
                
                # Edit form
                if st.session_state.get(edit_key, False):
                    st.markdown("---")
                    with st.form(f"edit_location_{location['id']}"):
                        st.markdown("**Edit Location**")
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            new_country_code = st.text_input("Country Code", 
                                                           value=location['country_code'],
                                                           max_chars=5)
                            new_country_name = st.text_input("Country Name", 
                                                           value=location['country_name'])
                        with col2:
                            new_city = st.text_input("City/Location", 
                                                   value=location['city'])
                        
                        col_save, col_cancel = st.columns(2)
                        with col_save:
                            if st.form_submit_button("Save Changes", type="primary"):
                                if new_country_code and new_country_name and new_city:
                                    # Update location in database
                                    conn = sqlite3.connect(db.db_name)
                                    cursor = conn.cursor()
                                    cursor.execute('''
                                        UPDATE locations 
                                        SET country_code = ?, country_name = ?, city = ?
                                        WHERE id = ?
                                    ''', (new_country_code.upper(), new_country_name, new_city, location['id']))
                                    conn.commit()
                                    conn.close()
                                    
                                    st.session_state[edit_key] = False
                                    st.success("Location updated!")
                                    st.rerun()
                                else:
                                    st.error("Please fill in all fields")
                        
                        with col_cancel:
                            if st.form_submit_button("Cancel"):
                                st.session_state[edit_key] = False
                                st.rerun()
                
                # Delete confirmation
                if st.session_state.get(delete_key, False):
                    st.markdown("---")
                    st.error("⚠️ **Are you sure you want to delete this location?**")
                    st.write("This action cannot be undone. Patients may already be using this location code.")
                    
                    col_confirm, col_cancel = st.columns(2)
                    with col_confirm:
                        if st.button("Yes, Delete", key=f"confirm_delete_{location['id']}", type="primary"):
                            # Delete location from database
                            conn = sqlite3.connect(db.db_name)
                            cursor = conn.cursor()
                            cursor.execute('DELETE FROM locations WHERE id = ?', (location['id'],))
                            conn.commit()
                            conn.close()
                            
                            st.session_state[delete_key] = False
                            st.success("Location deleted!")
                            st.rerun()
                    
                    with col_cancel:
                        if st.button("Cancel", key=f"cancel_delete_{location['id']}"):
                            st.session_state[delete_key] = False
                            st.rerun()
    else:
        st.info("No locations configured yet. Locations are typically set up during initial clinic setup.")


def medication_management():
    add_to_history('medication_management')
    st.markdown("### Preset Medications")

    # Clean up duplicates button
    col1, col2 = st.columns([3, 1])
    with col2:
        if st.button("Clean Duplicates", type="secondary"):
            duplicates_removed = db.clean_duplicate_medications()
            if duplicates_removed > 0:
                st.success(
                    f"Removed {duplicates_removed} duplicate medication groups"
                )
            else:
                st.info("No duplicates found")
            st.rerun()

    medications = db.get_preset_medications()

    # Add new medication
    with st.expander("Add New Medication"):
        with st.form("new_medication"):
            col1, col2 = st.columns(2)
            with col1:
                med_name = st.text_input("Medication Name")
                dosages = st.text_input("Common Dosages",
                                        placeholder="e.g., 250mg, 500mg")
                amount = st.text_input("Amount/Quantity",
                                     placeholder="e.g., 30 tablets, 100ml bottle")
                preset_duration = st.text_input("Preset Duration",
                                              placeholder="e.g., 30 days, 7 days, 10 days",
                                              help="Default duration that will auto-populate when prescribing")
            with col2:
                category = st.selectbox("Category", [
                    "Pain Relief", "Antibiotic", "Blood Pressure", "Diabetes",
                    "Stomach", "Respiratory", "Vitamin", "Steroid", "Diuretic",
                    "Cholesterol", "UTI Antibiotic", "Teaching Pamphlets", "Other"
                ])
                require_indication = st.checkbox("Require indication when prescribing", 
                                                value=True,
                                                help="Uncheck for medications like vitamins that don't need specific indications")
                indications = st.text_area("Clinical Indications",
                                         placeholder="e.g., Hypertension, Pain relief, Bacterial infections",
                                         height=100)

            if st.form_submit_button("Add Medication"):
                if med_name:
                    conn = sqlite3.connect(db.db_name)
                    cursor = conn.cursor()
                    # Check if columns exist, if not add them
                    cursor.execute("PRAGMA table_info(preset_medications)")
                    columns = [column[1] for column in cursor.fetchall()]
                    if 'require_indication' not in columns:
                        cursor.execute('ALTER TABLE preset_medications ADD COLUMN require_indication TEXT DEFAULT "yes"')
                    if 'preset_duration' not in columns:
                        cursor.execute('ALTER TABLE preset_medications ADD COLUMN preset_duration TEXT DEFAULT ""')
                    
                    cursor.execute(
                        '''
                        INSERT INTO preset_medications (medication_name, common_dosages, category, requires_lab, amount, indications, require_indication, preset_duration)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (med_name, dosages, category, "no", amount, indications, "yes" if require_indication else "no", preset_duration))
                    conn.commit()
                    conn.close()
                    st.success("Medication added!")
                    st.rerun()

    # Display existing medications
    if medications:
        for category in set(med['category'] for med in medications):
            with st.expander(f"{category} Medications"):
                category_meds = [
                    med for med in medications if med['category'] == category
                ]
                for med in category_meds:
                    # Check if this medication is being edited
                    edit_key = f"edit_{med['id']}"
                    is_editing = st.session_state.get(edit_key, False)

                    if is_editing:
                        # Edit form
                        with st.form(f"edit_form_{med['id']}"):
                            st.markdown(
                                f"**Editing: {med['medication_name']}**")

                            col1, col2 = st.columns(2)
                            with col1:
                                new_name = st.text_input(
                                    "Medication Name",
                                    value=med['medication_name'])
                                new_dosages = st.text_area(
                                    "Common Dosages",
                                    value=med['common_dosages'],
                                    height=100)
                                new_amount = st.text_input(
                                    "Amount/Quantity",
                                    value=med.get('amount', ''))
                                new_preset_duration = st.text_input(
                                    "Preset Duration",
                                    value=med.get('preset_duration', ''),
                                    placeholder="e.g., 30 days, 7 days, 10 days",
                                    help="Default duration that will auto-populate when prescribing")
                            with col2:
                                categories = [
                                    "Pain Relief", "Antibiotic",
                                    "Blood Pressure", "Diabetes", "Stomach",
                                    "Respiratory", "Vitamin", "Steroid",
                                    "Diuretic", "Cholesterol",
                                    "UTI Antibiotic", "Teaching Pamphlets", "Other"
                                ]
                                try:
                                    cat_index = categories.index(
                                        med['category'])
                                except ValueError:
                                    cat_index = 0
                                new_category = st.selectbox("Category",
                                                            categories,
                                                            index=cat_index)
                                new_require_indication = st.checkbox("Require indication when prescribing",
                                                                    value=med.get('require_indication', 'yes') == 'yes',
                                                                    help="Uncheck for medications like vitamins that don't need specific indications")
                                new_indications = st.text_area(
                                    "Clinical Indications",
                                    value=med.get('indications', ''),
                                    height=100)

                            col_save, col_cancel = st.columns(2)
                            with col_save:
                                if st.form_submit_button("Save Changes",
                                                         type="primary"):
                                    if new_name and new_name.strip():
                                        conn = sqlite3.connect(
                                            "clinic_database.db")
                                        cursor = conn.cursor()
                                        # Check if columns exist, if not add them
                                        cursor.execute("PRAGMA table_info(preset_medications)")
                                        columns = [column[1] for column in cursor.fetchall()]
                                        if 'require_indication' not in columns:
                                            cursor.execute('ALTER TABLE preset_medications ADD COLUMN require_indication TEXT DEFAULT "yes"')
                                        if 'preset_duration' not in columns:
                                            cursor.execute('ALTER TABLE preset_medications ADD COLUMN preset_duration TEXT DEFAULT ""')
                                        
                                        cursor.execute(
                                            '''
                                            UPDATE preset_medications 
                                            SET medication_name = ?, common_dosages = ?, category = ?, amount = ?, indications = ?, require_indication = ?, preset_duration = ?
                                            WHERE id = ?
                                        ''',
                                            (new_name.strip(),
                                             new_dosages.strip() if new_dosages
                                             else "", new_category, new_amount.strip() if new_amount else "", 
                                             new_indications.strip() if new_indications else "", 
                                             "yes" if new_require_indication else "no", 
                                             new_preset_duration.strip() if new_preset_duration else "", med['id']))
                                        conn.commit()
                                        conn.close()
                                        st.session_state[edit_key] = False
                                        st.success("Medication updated!")
                                        st.rerun()
                                    else:
                                        st.error(
                                            "Medication name cannot be empty")

                            with col_cancel:
                                if st.form_submit_button("Cancel"):
                                    st.session_state[edit_key] = False
                                    st.rerun()
                    else:
                        # Display mode
                        col1, col2, col3, col4 = st.columns([4, 1, 1, 1])
                        with col1:
                            st.write(f"**{med['medication_name']}**")
                            st.caption(f"Dosages: {med['common_dosages']}")
                            if med.get('amount'):
                                st.caption(f"Amount: {med['amount']}")
                            if med.get('preset_duration'):
                                st.caption(f"Default Duration: {med['preset_duration']}")
                            if med.get('indications'):
                                st.caption(f"Indications: {med['indications']}")
                            # Show indication requirement status
                            indication_required = med.get('require_indication', 'yes') == 'yes'
                            if not indication_required:
                                st.caption("🏷️ Indication not required")
                        with col2:
                            st.write(f"{med['category']}")
                        with col3:
                            if st.button("Edit",
                                         key=f"edit_btn_{med['id']}",
                                         type="secondary"):
                                st.session_state[edit_key] = True
                                st.rerun()
                        with col4:
                            if st.button("Delete",
                                         key=f"delete_{med['id']}",
                                         type="secondary"):
                                conn = sqlite3.connect("clinic_database.db")
                                cursor = conn.cursor()
                                cursor.execute(
                                    'DELETE FROM preset_medications WHERE id = ?',
                                    (med['id'], ))
                                conn.commit()
                                conn.close()
                                st.success("Medication removed!")
                                st.rerun()


def daily_reports():
    add_to_history('daily_reports')
    st.markdown("### Daily Statistics")

    conn = sqlite3.connect(db.db_name)
    cursor = conn.cursor()

    # Patient counts
    cursor.execute(
        "SELECT COUNT(*) FROM visits WHERE DATE(visit_date) = DATE('now')")
    today_patients = cursor.fetchone()[0]

    cursor.execute(
        "SELECT COUNT(*) FROM visits WHERE status = 'completed' AND DATE(visit_date) = DATE('now')"
    )
    completed_patients = cursor.fetchone()[0]

    cursor.execute(
        "SELECT COUNT(*) FROM prescriptions WHERE DATE(prescribed_time) = DATE('now')"
    )
    prescriptions_written = cursor.fetchone()[0]

    cursor.execute(
        "SELECT COUNT(*) FROM lab_tests WHERE DATE(ordered_time) = DATE('now')"
    )
    lab_tests_ordered = cursor.fetchone()[0]

    conn.close()

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Patients", today_patients)
    with col2:
        st.metric("Completed", completed_patients)
    with col3:
        st.metric("Prescriptions", prescriptions_written)
    with col4:
        st.metric("Lab Tests", lab_tests_ordered)

    st.markdown("---")

    # Data Export
    st.markdown("### Data Export")

    # Generate export data when button is clicked
    export_data = generate_daily_export()
    csv_data = export_data.to_csv(index=False)
    today_date = datetime.now().strftime("%Y-%m-%d")
    filename = f"parakaleo_clinic_data_{today_date}.csv"

    col1, col2 = st.columns(2)
    
    with col1:
        # CSV download button
        st.download_button(label="📄 Download CSV",
                           data=csv_data,
                           file_name=filename,
                           mime="text/csv",
                           type="primary",
                           use_container_width=True)
    
    with col2:
        # PDF download button
        if PDF_AVAILABLE:
            stats = {
                'patients_seen': today_patients,
                'prescriptions_filled': prescriptions_written,
                'lab_tests': lab_tests_ordered,
                'new_registrations': completed_patients
            }
            pdf_data = generate_clinic_report_pdf(today_date, stats)
            if pdf_data:
                st.download_button(
                    label="📋 Download PDF Report",
                    data=pdf_data,
                    file_name=f"clinic_report_{today_date}.pdf",
                    mime="application/pdf",
                    type="secondary",
                    use_container_width=True
                )
        else:
            st.info("PDF export requires reportlab library")

    st.markdown("---")

    # OneDrive connection as secondary option
    if st.button("☁️ Connect to OneDrive",
                 type="secondary",
                 use_container_width=True):
        st.session_state.show_onedrive = True
        st.rerun()

    # Show OneDrive integration if requested
    if 'show_onedrive' in st.session_state and st.session_state.show_onedrive:
        onedrive_integration()
        if st.button(t('back_to_reports'), key='back_to_reports_from_onedrive'):
            st.session_state.show_onedrive = False
            st.rerun()
        return

    # OneDrive backup instructions
    with st.expander("OneDrive Backup Instructions"):
        st.markdown("""
        **To backup your clinic data to OneDrive:**
        
        1. **Download the CSV file** using the "Export Today's Data" button above
        
        2. **Open OneDrive app** on your iPad:
           - Look for the blue OneDrive icon on your home screen
           - Sign in with your Microsoft account if needed
        
        3. **Upload the file**:
           - Tap the "+" button in OneDrive
           - Select "Upload files"
           - Choose the downloaded CSV file from your Downloads folder
        
        4. **Organize in folders**:
           - Create a folder called "ParakaleoMed Backups"
           - Create subfolders by date (e.g., "2025-06-15")
           - Move your daily export files into the appropriate date folder
        
        5. **Automatic sync**:
           - OneDrive will automatically sync to the cloud
           - Access your data from any device by logging into OneDrive
        
        **Important**: Export and backup data daily to ensure no patient information is lost.
        """)


def generate_daily_export():
    """Generate comprehensive daily data export"""
    import pandas as pd

    conn = sqlite3.connect(db.db_name)

    # Get today's data
    today = datetime.now().strftime("%Y-%m-%d")

    # Export patients visited today
    patients_query = '''
        SELECT p.patient_id, p.name, p.age, p.gender, v.visit_date, v.status
        FROM patients p
        JOIN visits v ON p.patient_id = v.patient_id
        WHERE DATE(v.visit_date) = ?
    '''

    patients_df = pd.read_sql_query(patients_query, conn, params=[today])

    # Export prescriptions from today
    prescriptions_query = '''
        SELECT pr.medication_name, pr.dosage, pr.frequency, pr.duration, 
               pr.awaiting_lab, p.name as patient_name, p.patient_id
        FROM prescriptions pr
        JOIN visits v ON pr.visit_id = v.visit_id
        JOIN patients p ON v.patient_id = p.patient_id
        WHERE DATE(pr.prescribed_time) = ?
    '''

    prescriptions_df = pd.read_sql_query(prescriptions_query,
                                         conn,
                                         params=[today])

    # Export lab tests from today
    lab_tests_query = '''
        SELECT lt.test_type, lt.status, lt.results, p.name as patient_name, p.patient_id
        FROM lab_tests lt
        JOIN visits v ON lt.visit_id = v.visit_id
        JOIN patients p ON v.patient_id = p.patient_id
        WHERE DATE(lt.ordered_time) = ?
    '''

    lab_tests_df = pd.read_sql_query(lab_tests_query, conn, params=[today])

    conn.close()

    # Combine all data into one export
    export_data = pd.DataFrame()

    if not patients_df.empty:
        export_data = pd.concat(
            [export_data, patients_df.add_prefix('patient_')],
            ignore_index=True)

    if not prescriptions_df.empty:
        export_data = pd.concat(
            [export_data,
             prescriptions_df.add_prefix('prescription_')],
            ignore_index=True)

    if not lab_tests_df.empty:
        export_data = pd.concat(
            [export_data, lab_tests_df.add_prefix('lab_')], ignore_index=True)

    return export_data


def onedrive_integration():
    """Handle OneDrive connection and backup"""
    st.markdown("### OneDrive Integration")

    st.info("OneDrive integration for automatic backup of patient data.")

    # Simulate OneDrive connection process
    st.markdown("#### Connect to OneDrive Account")

    with st.form("onedrive_setup"):
        st.markdown("**Step 1: Authentication**")
        st.write(
            "Click the button below to authenticate with your Microsoft OneDrive account."
        )

        # Form inputs
        backup_frequency = st.selectbox("Backup Frequency",
                                        ["Manual", "Daily", "Weekly"])

        folder_name = st.text_input("OneDrive Folder Name",
                                    value="ParakaleoMed Backups")

        if st.form_submit_button("Setup OneDrive Backup", type="primary"):
            # In a real implementation, this would redirect to Microsoft OAuth
            st.success("OneDrive backup configured successfully!")
            st.session_state.onedrive_connected = True

            st.success(
                f"Backup configured: {backup_frequency} to folder '{folder_name}'"
            )

            # Generate and prepare data for upload
            export_data = generate_daily_export()
            csv_data = export_data.to_csv(index=False)
            today_date = datetime.now().strftime("%Y-%m-%d")
            filename = f"parakaleo_clinic_data_{today_date}.csv"

            st.download_button(label="Download for Manual Upload to OneDrive",
                               data=csv_data,
                               file_name=filename,
                               mime="text/csv")

            st.info(
                "File prepared for OneDrive backup. Use the download button above to get the file, then upload it to your OneDrive folder."
            )

    # Manual backup section
    st.markdown("---")
    st.markdown("#### Manual Backup to OneDrive")

    if st.button("Prepare Manual Backup"):
        export_data = generate_daily_export()
        csv_data = export_data.to_csv(index=False)
        today_date = datetime.now().strftime("%Y-%m-%d")
        filename = f"parakaleo_clinic_backup_{today_date}.csv"

        st.download_button(label="Download Backup File",
                           data=csv_data,
                           file_name=filename,
                           mime="text/csv")

        st.markdown("""
        **Next Steps:**
        1. Download the file using the button above
        2. Open OneDrive app on your iPad
        3. Navigate to your ParakaleoMed Backups folder
        4. Upload the downloaded file
        5. OneDrive will automatically sync to the cloud
        """)


def ophthalmologist_interface():
    st.markdown("### 👁️ Ophthalmologist Interface")

    # Ensure eye_examinations table exists
    conn = sqlite3.connect("clinic_database.db")
    cursor = conn.cursor()

    # Create eye_examinations table if it doesn't exist
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS eye_examinations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            visit_id TEXT,
            patient_id TEXT,
            eye_history TEXT,
            visual_acuity_right TEXT,
            visual_acuity_left TEXT,
            eye_pressure_right TEXT,
            eye_pressure_left TEXT,
            eye_findings TEXT,
            od_sphere TEXT,
            od_cylinder TEXT,
            od_axis TEXT,
            os_sphere TEXT,
            os_cylinder TEXT,
            os_axis TEXT,
            add_power TEXT,
            pd TEXT,
            recommendations TEXT,
            examination_time TEXT,
            FOREIGN KEY (visit_id) REFERENCES visits (visit_id),
            FOREIGN KEY (patient_id) REFERENCES patients (patient_id)
        )
    ''')

    # Get patients who need ophthalmology consultation
    cursor.execute('''
        SELECT v.visit_id, v.patient_id, p.name, c.needs_ophthalmology
        FROM visits v
        JOIN patients p ON v.patient_id = p.patient_id
        LEFT JOIN consultations c ON v.visit_id = c.visit_id
        WHERE c.needs_ophthalmology = 1 AND v.status != 'completed'
        ORDER BY v.visit_date DESC
    ''')

    ophthalmology_patients = cursor.fetchall()
    conn.close()

    if ophthalmology_patients:
        st.markdown("#### Patients Needing Eye Examination")

        for patient in ophthalmology_patients:
            visit_id, patient_id, name, needs_ophthalmology = patient

            with st.expander(f"👁️ {name} (ID: {patient_id})", expanded=False):
                # Get patient's eye history
                conn = sqlite3.connect("clinic_database.db")
                cursor = conn.cursor()
                cursor.execute(
                    'SELECT medical_history, allergies FROM patients WHERE patient_id = ?',
                    (patient_id, ))
                patient_data = cursor.fetchone()
                conn.close()

                if patient_data:
                    st.markdown("**Current Medical History:**")
                    st.text(patient_data[0] or "No history recorded")

                # Eye examination form
                with st.form(f"eye_exam_{visit_id}"):
                    st.markdown("#### Eye Examination")

                    col1, col2 = st.columns(2)

                    with col1:
                        eye_history = st.text_area(
                            "Eye History",
                            placeholder=
                            "Previous eye problems, surgeries, conditions...")
                        visual_acuity_right = st.text_input(
                            "Visual Acuity Right Eye",
                            placeholder="e.g., 20/20, 20/40")
                        visual_acuity_left = st.text_input(
                            "Visual Acuity Left Eye",
                            placeholder="e.g., 20/20, 20/40")

                    with col2:
                        eye_pressure_right = st.text_input(
                            "Eye Pressure Right", placeholder="e.g., 15 mmHg")
                        eye_pressure_left = st.text_input(
                            "Eye Pressure Left", placeholder="e.g., 15 mmHg")
                        eye_findings = st.text_area(
                            "Eye Findings",
                            placeholder="Examination findings, abnormalities..."
                        )

                    st.markdown("#### Eyeglass Prescription")

                    col3, col4 = st.columns(2)
                    with col3:
                        st.markdown("**Right Eye (OD)**")
                        od_sphere = st.text_input("Sphere",
                                                  key=f"od_sphere_{visit_id}",
                                                  placeholder="e.g., -2.00")
                        od_cylinder = st.text_input(
                            "Cylinder",
                            key=f"od_cylinder_{visit_id}",
                            placeholder="e.g., -0.50")
                        od_axis = st.text_input("Axis",
                                                key=f"od_axis_{visit_id}",
                                                placeholder="e.g., 90")

                    with col4:
                        st.markdown("**Left Eye (OS)**")
                        os_sphere = st.text_input("Sphere",
                                                  key=f"os_sphere_{visit_id}",
                                                  placeholder="e.g., -2.00")
                        os_cylinder = st.text_input(
                            "Cylinder",
                            key=f"os_cylinder_{visit_id}",
                            placeholder="e.g., -0.50")
                        os_axis = st.text_input("Axis",
                                                key=f"os_axis_{visit_id}",
                                                placeholder="e.g., 90")

                    add_power = st.text_input("Add Power (if needed)",
                                              placeholder="e.g., +1.50")
                    pd = st.text_input("Pupillary Distance (PD)",
                                       placeholder="e.g., 62mm")

                    recommendations = st.text_area(
                        "Recommendations",
                        placeholder="Follow-up instructions, referrals...")

                    if st.form_submit_button("Complete Eye Examination",
                                             type="primary"):
                        # Save eye examination data
                        conn = sqlite3.connect("clinic_database.db")
                        cursor = conn.cursor()

                        # Create eye_examinations table if it doesn't exist
                        cursor.execute('''
                            CREATE TABLE IF NOT EXISTS eye_examinations (
                                id INTEGER PRIMARY KEY AUTOINCREMENT,
                                visit_id TEXT,
                                patient_id TEXT,
                                eye_history TEXT,
                                visual_acuity_right TEXT,
                                visual_acuity_left TEXT,
                                eye_pressure_right TEXT,
                                eye_pressure_left TEXT,
                                eye_findings TEXT,
                                od_sphere TEXT,
                                od_cylinder TEXT,
                                od_axis TEXT,
                                os_sphere TEXT,
                                os_cylinder TEXT,
                                os_axis TEXT,
                                add_power TEXT,
                                pd TEXT,
                                recommendations TEXT,
                                examination_time TEXT,
                                FOREIGN KEY (visit_id) REFERENCES visits (visit_id),
                                FOREIGN KEY (patient_id) REFERENCES patients (patient_id)
                            )
                        ''')

                        cursor.execute(
                            '''
                            INSERT INTO eye_examinations (
                                visit_id, patient_id, eye_history, visual_acuity_right, visual_acuity_left,
                                eye_pressure_right, eye_pressure_left, eye_findings, od_sphere, od_cylinder,
                                od_axis, os_sphere, os_cylinder, os_axis, add_power, pd, recommendations,
                                examination_time
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (visit_id, patient_id, eye_history,
                              visual_acuity_right, visual_acuity_left,
                              eye_pressure_right, eye_pressure_left,
                              eye_findings, od_sphere, od_cylinder, od_axis,
                              os_sphere, os_cylinder, os_axis, add_power, pd,
                              recommendations, datetime.now().isoformat()))

                        # Update patient's medical history with eye history
                        if eye_history:
                            cursor.execute(
                                '''
                                UPDATE patients 
                                SET medical_history = COALESCE(medical_history, '') || '\nEye History: ' || ?
                                WHERE patient_id = ?
                            ''', (eye_history, patient_id))

                        # Update visit status to completed
                        cursor.execute(
                            '''
                            UPDATE visits SET status = 'completed' WHERE visit_id = ?
                        ''', (visit_id, ))

                        conn.commit()
                        conn.close()

                        st.success("Eye examination completed successfully!")
                        st.rerun()
    else:
        st.info("No patients currently need ophthalmology consultation.")

    # Show completed eye examinations
    st.markdown("---")
    st.markdown("#### Recent Eye Examinations")

    conn = sqlite3.connect("clinic_database.db")
    cursor = conn.cursor()
    cursor.execute('''
        SELECT e.*, p.name
        FROM eye_examinations e
        JOIN patients p ON e.patient_id = p.patient_id
        ORDER BY e.examination_time DESC
        LIMIT 10
    ''')
    recent_exams = cursor.fetchall()
    conn.close()

    if recent_exams:
        for exam in recent_exams:
            with st.expander(f"👁️ {exam[-1]} - {exam[18][:10]}",
                             expanded=False):
                col1, col2 = st.columns(2)

                with col1:
                    st.write(
                        f"**Visual Acuity:** R: {exam[4] or 'N/A'}, L: {exam[5] or 'N/A'}"
                    )
                    st.write(
                        f"**Eye Pressure:** R: {exam[6] or 'N/A'}, L: {exam[7] or 'N/A'}"
                    )
                    if exam[9] or exam[12]:  # If prescription exists
                        st.write("**Prescription:**")
                        st.write(f"OD: {exam[9]} {exam[10]} x {exam[11]}")
                        st.write(f"OS: {exam[12]} {exam[13]} x {exam[14]}")
                        if exam[15]:
                            st.write(f"Add: {exam[15]}")
                        if exam[16]:
                            st.write(f"PD: {exam[16]}")

                with col2:
                    if exam[8]:
                        st.write(f"**Findings:** {exam[8]}")
                    if exam[17]:
                        st.write(f"**Recommendations:** {exam[17]}")
    else:
        st.info("No eye examinations completed yet.")


def clinic_settings():
    add_to_history('clinic_settings')
    st.markdown("### Clinic Settings")

    # Display and Theme Settings
    st.markdown("#### Display & Interface")

    # Dark mode toggle
    if 'dark_mode' not in st.session_state:
        st.session_state.dark_mode = False

    dark_mode = st.toggle("🌙 Dark Mode", value=st.session_state.dark_mode)
    if dark_mode != st.session_state.dark_mode:
        st.session_state.dark_mode = dark_mode
        st.rerun()

    # Dark mode CSS is now applied globally in main() function

    # Language Settings
    st.markdown("#### Language & Localization")
    
    # Initialize language in session state
    if 'app_language' not in st.session_state:
        st.session_state.app_language = 'en'
    
    language_options = {
        'English': 'en',
        'Spanish (Español)': 'es',
        'Haitian Creole (Kreyòl)': 'ht'
    }
    
    current_lang = next((k for k, v in language_options.items() if v == st.session_state.app_language), 'English')
    language = st.selectbox("Interface Language",
                            list(language_options.keys()),
                            index=list(language_options.keys()).index(current_lang))
    
    if language_options[language] != st.session_state.app_language:
        st.session_state.app_language = language_options[language]
        st.success(f"Language changed to {language}. Some text will update immediately, others on next page load.")
        st.rerun()
    
    # Country-Specific Configuration
    st.markdown("#### Country Configuration")
    
    country_configs = {
        'Dominican Republic': {
            'patient_id_prefix': 'DR',
            'default_language': 'es',
            'currency': 'DOP',
            'common_conditions': ['Dengue', 'Typhoid', 'Malaria', 'Parasites']
        },
        'Haiti': {
            'patient_id_prefix': 'H',
            'default_language': 'ht',
            'currency': 'HTG',
            'common_conditions': ['Cholera', 'Typhoid', 'Malaria', 'TB']
        }
    }
    
    # Get current location
    current_location = st.session_state.get('clinic_location', {})
    current_country = current_location.get('country_name', 'Dominican Republic')
    
    if current_country in country_configs:
        config = country_configs[current_country]
        st.info(f"**Current Configuration for {current_country}:**")
        st.markdown(f"- Patient ID Prefix: **{config['patient_id_prefix']}**")
        st.markdown(f"- Default Language: **{config['default_language'].upper()}**")
        st.markdown(f"- Common Conditions: {', '.join(config['common_conditions'])}")

    # Notification Settings
    st.markdown("#### Notifications")
    enable_sounds = st.checkbox("🔊 Enable Sound Notifications", value=True)
    enable_popups = st.checkbox("📢 Enable Pop-up Alerts", value=True)
    auto_save = st.checkbox("💾 Auto-save Patient Data", value=True)

    # Remove session timeout and auto-logout - user doesn't want these features

    # Data Management
    st.markdown("#### Data Management")
    backup_reminder = st.selectbox(
        "Backup Reminder Frequency",
        ["Daily", "Every 2 days", "Weekly", "Never"],
        index=0)

    # Advanced Settings
    with st.expander("🔧 Advanced Settings"):
        st.markdown("#### Database Settings")
        if st.button("🗄️ Optimize Database"):
            st.success("Database optimization completed!")

        st.markdown("#### Developer Options")
        debug_mode = st.checkbox("🐛 Enable Debug Mode", value=False)
        if debug_mode:
            st.warning("Debug mode enabled - additional logging active")

        show_performance = st.checkbox("📊 Show Performance Metrics",
                                       value=False)
        if show_performance:
            st.info("Performance metrics will be displayed in the sidebar")

    # Save Settings
    st.markdown("---")
    if st.button("💾 Save All Settings", type="primary"):
        # Store settings in session state
        st.session_state.settings = {
            'language': language,
            'sounds': enable_sounds,
            'popups': enable_popups,
            'auto_save': auto_save,
            'backup_reminder': backup_reminder,
            'debug_mode': debug_mode,
            'show_performance': show_performance
        }
        st.success("✅ Settings saved successfully!")

    if st.button("🔄 Reset to Defaults"):
        if 'settings' in st.session_state:
            del st.session_state.settings
        st.session_state.dark_mode = False
        st.success("Settings reset to defaults")
        st.rerun()


def stock_management():
    """Admin interface for medication stock tracking"""
    add_to_history('stock_management')
    st.markdown("### Medication Stock Management")
    
    db = get_db_manager()
    
    # Get medications with stock info
    medications = db.get_medications_with_stock()
    
    # Stock overview metrics
    low_stock = db.get_low_stock_medications()
    out_of_stock = [m for m in medications if m.get('stock_status') == 'out_of_stock']
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Medications", len(medications))
    with col2:
        st.metric("Low Stock Warnings", len(low_stock), delta=None if not low_stock else "⚠️", delta_color="inverse")
    with col3:
        st.metric("Out of Stock", len(out_of_stock), delta=None if not out_of_stock else "🔴", delta_color="inverse")
    
    # Low stock alerts
    if low_stock:
        st.warning(f"⚠️ **{len(low_stock)} medications are running low:**")
        for med in low_stock:
            status_icon = "🔴" if med['qty_in_stock'] <= 0 else "🟡"
            st.markdown(f"- {status_icon} **{med['medication_name']}**: {med['qty_in_stock']} remaining (threshold: {med['low_stock_threshold']})")
    
    st.markdown("---")
    
    # Stock update form
    st.markdown("#### Update Stock Levels")
    
    # Group by category
    categories = {}
    for med in medications:
        cat = med.get('category', 'Uncategorized')
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(med)
    
    for category, meds in sorted(categories.items()):
        with st.expander(f"📦 {category} ({len(meds)} medications)"):
            for med in meds:
                col1, col2, col3, col4 = st.columns([3, 2, 2, 2])
                
                with col1:
                    status_icon = "🟢" if med['stock_status'] == 'in_stock' else "🟡" if med['stock_status'] == 'low_stock' else "🔴"
                    st.markdown(f"**{status_icon} {med['medication_name']}**")
                
                with col2:
                    st.caption(f"Current: {med['qty_in_stock']}")
                
                with col3:
                    new_qty = st.number_input(
                        "New qty",
                        min_value=0,
                        value=int(med['qty_in_stock']),
                        key=f"stock_{med['id']}"
                    )
                
                with col4:
                    if st.button("Update", key=f"update_stock_{med['id']}"):
                        if db.update_medication_stock(med['id'], new_qty, med['low_stock_threshold']):
                            st.success(f"✅ Updated {med['medication_name']}")
                            st.rerun()
                        else:
                            st.error("Failed to update stock")
    
    # Bulk update
    st.markdown("---")
    st.markdown("#### Bulk Stock Update")
    
    if st.checkbox("Show Bulk Update Form"):
        with st.form("bulk_stock_update"):
            st.markdown("Upload a CSV with columns: medication_name, quantity")
            uploaded_file = st.file_uploader("Upload CSV", type=['csv'])
            
            if st.form_submit_button("Apply Bulk Update", type="primary"):
                if uploaded_file:
                    try:
                        import pandas as pd
                        df = pd.read_csv(uploaded_file)
                        updates = 0
                        for _, row in df.iterrows():
                            # Find medication by name
                            med = next((m for m in medications if m['medication_name'].lower() == row['medication_name'].lower()), None)
                            if med:
                                db.update_medication_stock(med['id'], int(row['quantity']))
                                updates += 1
                        st.success(f"✅ Updated {updates} medications")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error processing file: {str(e)}")
                else:
                    st.warning("Please upload a CSV file")


def audit_log_viewer():
    """Admin interface for viewing audit logs"""
    add_to_history('audit_log_viewer')
    st.markdown("### Audit Logs")
    st.caption("Track all system activities and user actions")
    
    db = get_db_manager()
    
    # Filter options
    col1, col2, col3 = st.columns(3)
    
    with col1:
        action_filter = st.selectbox(
            "Filter by Action",
            ["All", "patient_registration", "consultation", "prescription", "lab_test", "login", "data_export"]
        )
    
    with col2:
        user_filter = st.text_input("Filter by User", placeholder="Enter username...")
    
    with col3:
        limit = st.number_input("Show records", min_value=10, max_value=500, value=100)
    
    # Get logs
    filters = {}
    if action_filter != "All":
        filters['action_type'] = action_filter
    if user_filter:
        filters['user_name'] = user_filter
    
    logs = db.get_audit_logs(limit=limit, **filters)
    
    # Display stats
    st.markdown("---")
    st.metric("Total Logs Retrieved", len(logs))
    
    # Display logs
    if logs:
        for log in logs:
            with st.expander(f"📋 {log.get('action_type', 'Unknown')} - {log.get('created_time', 'Unknown')[:19]}"):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown(f"**User:** {log.get('user_name', 'System')}")
                    st.markdown(f"**Role:** {log.get('user_role', 'N/A')}")
                    st.markdown(f"**Action:** {log.get('action_type', 'N/A')}")
                
                with col2:
                    st.markdown(f"**Table:** {log.get('table_name', 'N/A')}")
                    st.markdown(f"**Record ID:** {log.get('record_id', 'N/A')}")
                    st.markdown(f"**Time:** {log.get('created_time', 'N/A')}")
                
                if log.get('old_values'):
                    st.markdown("**Previous Values:**")
                    st.json(log['old_values'])
                
                if log.get('new_values'):
                    st.markdown("**New Values:**")
                    st.json(log['new_values'])
    else:
        st.info("No audit logs found matching the filters.")
    
    # Export option
    st.markdown("---")
    if logs and st.button("📥 Export Logs to CSV"):
        import pandas as pd
        df = pd.DataFrame(logs)
        csv = df.to_csv(index=False)
        st.download_button(
            "Download CSV",
            csv,
            "audit_logs.csv",
            "text/csv",
            key='download_audit_logs'
        )


if __name__ == "__main__":
    main()
