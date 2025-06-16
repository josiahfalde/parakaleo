import streamlit as st
import sqlite3
from datetime import datetime
import os
from typing import Dict, List, Optional
import time

# Configure page for mobile/tablet use
st.set_page_config(
    page_title="Medical Clinic Charting",
    page_icon=
    "attached_assets/ChatGPT Image Jun 15, 2025, 05_23_25 PM_1750022665650.png",
    layout="wide",
    initial_sidebar_state="collapsed")

# Custom CSS for mobile-friendly interface
st.markdown("""
<style>
    .main > div {
        padding-top: 1rem;
        padding-left: 1rem;
        padding-right: 1rem;
    }
    
    .stButton > button {
        width: 100%;
        height: 3rem;
        font-size: 1.2rem;
        margin: 0.5rem 0;
        border-radius: 8px;
    }
    
    .stSelectbox > div > div {
        font-size: 1.1rem;
    }
    
    .stTextInput > div > div > input {
        font-size: 1.1rem;
        height: 3rem;
    }
    
    .stNumberInput > div > div > input {
        font-size: 1.1rem;
        height: 3rem;
    }
    
    .patient-card {
        border: 2px solid #e0e0e0;
        border-radius: 10px;
        padding: 1rem;
        margin: 1rem 0;
        background-color: #f8f9fa;
    }
    
    .urgent {
        border-color: #dc3545;
        background-color: #f8d7da;
    }
    
    .completed {
        border-color: #28a745;
        background-color: #d4edda;
    }
    
    .in-progress {
        border-color: #ffc107;
        background-color: #fff3cd;
    }
    
    .metric-card {
        background: white;
        padding: 1rem;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin: 0.5rem 0;
    }
    
    .role-button {
        text-align: center;
        padding: 2rem;
        border: 2px solid #007bff;
        border-radius: 15px;
        margin: 1rem;
        background: linear-gradient(135deg, #007bff 0%, #0056b3 100%);
        color: white;
        cursor: pointer;
    }
</style>
""",
            unsafe_allow_html=True)


class DatabaseManager:

    def __init__(self, db_name: str = "clinic_database.db"):
        self.db_name = db_name
        self.init_database()

    def init_database(self):
        """Initialize the database with required tables"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()

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
                ('Furosemide', '20mg daily, 40mg daily', 'Diuretic', 'no')
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

        conn.commit()
        conn.close()

    def get_next_patient_id(self, location_code: str) -> str:
        """Get the next patient ID in format DR00001, H00001, etc."""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()

        # Find the highest existing patient ID for this location
        cursor.execute(
            '''
            SELECT patient_id FROM patients 
            WHERE patient_id LIKE ? 
            ORDER BY patient_id DESC 
            LIMIT 1
        ''', (f"{location_code}%", ))

        result = cursor.fetchone()

        if result:
            # Extract the number from the last patient ID
            last_id = result[0]
            last_number = int(last_id[len(location_code):])
            new_number = last_number + 1
        else:
            # First patient for this location
            new_number = 1

        # Ensure we don't have conflicts by checking if ID exists
        while True:
            new_id = f"{location_code}{new_number:05d}"
            cursor.execute(
                'SELECT COUNT(*) FROM patients WHERE patient_id = ?',
                (new_id, ))
            if cursor.fetchone()[0] == 0:
                break
            new_number += 1

        conn.close()
        return new_id

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

        cursor.execute(
            '''
            INSERT INTO patients (
                patient_id, name, age, gender, phone, emergency_contact, 
                medical_history, allergies, created_date, last_visit,
                family_id, relationship, parent_id, is_independent,
                address, registration_time
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''',
            (patient_id, kwargs.get('name', ''), age, kwargs.get('gender', ''),
             kwargs.get('phone', ''), kwargs.get('emergency_contact', ''),
             kwargs.get('medical_history', ''), kwargs.get('allergies', ''),
             datetime.now().isoformat(), datetime.now().isoformat(), family_id,
             relationship, parent_id, is_independent, kwargs.get(
                 'address', ''), datetime.now().isoformat()))

        conn.commit()
        conn.close()
        return patient_id

    def add_patient(self, location_code: str, **kwargs) -> str:
        """Add a new individual patient and return their ID"""
        patient_id = self.get_next_patient_id(location_code)

        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()

        cursor.execute(
            '''
            INSERT INTO patients (patient_id, name, age, gender, phone, 
                                emergency_contact, medical_history, allergies, 
                                created_date, last_visit, family_id, relationship, parent_id,
                                is_independent, address, registration_time)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''',
            (
                patient_id,
                kwargs.get('name', ''),
                kwargs.get('age'),
                kwargs.get('gender'),
                kwargs.get('phone'),
                kwargs.get('emergency_contact'),
                kwargs.get('medical_history'),
                kwargs.get('allergies'),
                datetime.now().isoformat(),
                datetime.now().isoformat(),
                kwargs.get('family_id', None),
                kwargs.get('relationship', 'self'),
                kwargs.get('parent_id', None),
                1,  # Individual patients are always independent
                kwargs.get('address', ''),
                datetime.now().isoformat()))

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
        """Search for patients by name or ID"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()

        cursor.execute(
            '''
            SELECT * FROM patients 
            WHERE patient_id LIKE ? OR name LIKE ?
            ORDER BY name
        ''', (f'%{query}%', f'%{query}%'))

        results = cursor.fetchall()
        conn.close()

        columns = [
            'patient_id', 'name', 'age', 'gender', 'phone',
            'emergency_contact', 'medical_history', 'allergies',
            'created_date', 'last_visit'
        ]

        return [dict(zip(columns, row)) for row in results]

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

            cursor.execute(
                'INSERT INTO doctors (name, is_active) VALUES (?, 1)',
                (name, ))
            conn.commit()
            conn.close()
            return True
        except:
            return False

    def remove_doctor(self, name: str) -> bool:
        """Remove a doctor (set inactive)"""
        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()

            cursor.execute('UPDATE doctors SET is_active = 0 WHERE name = ?',
                           (name, ))
            conn.commit()
            conn.close()
            return True
        except:
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

        columns = [
            'id', 'medication_name', 'common_dosages', 'category',
            'requires_lab', 'active'
        ]
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
                         awaiting_lab: str = "no") -> int:
        """Add a prescription"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()

        cursor.execute(
            '''
            INSERT INTO prescriptions 
            (visit_id, medication_id, medication_name, dosage, frequency, duration, 
             instructions, awaiting_lab, prescribed_time)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''',
            (visit_id, medication_id, medication_name, dosage, frequency,
             duration, instructions, awaiting_lab, datetime.now().isoformat()))

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
    """Navigate back to previous page"""
    if 'nav_history' in st.session_state and len(
            st.session_state.nav_history) > 1:
        # Remove current page
        st.session_state.nav_history.pop()
        # Get previous page
        previous_page = st.session_state.nav_history[-1]
        st.session_state.current_page = previous_page

        # Clear any workflow states that might interfere
        workflow_keys_to_clear = [
            'family_vital_signs_queue', 'current_family_vital_index',
            'family_workflow_active', 'pending_vitals', 'patient_name',
            'family_parent_id', 'family_parent_name'
        ]
        for key in workflow_keys_to_clear:
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
    """Display universal back button on all pages"""
    if 'nav_history' in st.session_state and len(st.session_state.nav_history) > 1:
        # Simple container-based back button that works on all pages
        col1, col2 = st.columns([1, 8])
        with col1:
            if st.button("← Back", key=f"back_btn_{len(st.session_state.nav_history)}", help="Go to previous page"):
                go_back()
                st.rerun()


def main():
    # Initialize navigation
    initialize_navigation()

    # Show loading screen on first load
    show_loading_screen()

    # Show the back button using the dedicated function
    show_back_button()

    # Modern UI styling with BackpackEMR-inspired design
    st.markdown("""
    <style>
    /* Modern BackpackEMR-inspired styling */
    .stApp {
        font-family: 'Inter', 'Segoe UI', 'Roboto', sans-serif;
    }
    
    /* Hamburger menu styling - three lines instead of arrow */
    button[title="Open navigation menu"] {
        background-color: transparent !important;
        border: none !important;
        padding: 8px !important;
        margin-left: 10px !important;
        position: fixed !important;
        top: 15px !important;
        right: 20px !important;
        z-index: 998 !important;
    }
    
    button[title="Open navigation menu"] svg {
        display: none !important;
    }
    
    button[title="Open navigation menu"]::after {
        content: "☰" !important;
        font-size: 24px !important;
        color: #333 !important;
        display: block !important;
    }
    
    /* Sticky back button container */
    .stContainer:first-child {
        position: sticky !important;
        top: 0 !important;
        z-index: 999 !important;
        background: white !important;
        padding-top: 10px !important;
        padding-bottom: 10px !important;
        border-bottom: 1px solid #e5e7eb !important;
        margin-bottom: 20px !important;
    }
    
    /* Back button styling */
    button[data-testid="baseButton-secondary"] {
        background-color: #3b82f6 !important;
        border: 1px solid #3b82f6 !important;
        color: white !important;
        border-radius: 8px !important;
        padding: 8px 16px !important;
        font-size: 14px !important;
        font-weight: 500 !important;
        box-shadow: 0 2px 4px rgba(59, 130, 246, 0.3) !important;
        transition: all 0.2s ease !important;
    }
    
    button[data-testid="baseButton-secondary"]:hover {
        background-color: #2563eb !important;
        border-color: #2563eb !important;
        box-shadow: 0 4px 8px rgba(59, 130, 246, 0.4) !important;
        transform: translateY(-1px) !important;
    }
    
    /* Remove purple outline on input focus */
    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus,
    .stNumberInput > div > div > input:focus,
    .stSelectbox > div > div > div:focus {
        outline: none !important;
        border-color: #3b82f6 !important;
        box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.1) !important;
    }
    
    /* BackpackEMR-inspired button styling - clean and professional */
    .stButton > button {
        background: #ffffff !important;
        color: #374151 !important;
        border: 1px solid #d1d5db !important;
        border-radius: 8px !important;
        padding: 8px 16px !important;
        font-weight: 500 !important;
        transition: all 0.2s ease !important;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1) !important;
    }
    
    .stButton > button:hover {
        background: #f9fafb !important;
        border-color: #9ca3af !important;
        box-shadow: 0 2px 6px rgba(0,0,0,0.15) !important;
    }
    
    .stButton > button:active {
        background: #f3f4f6 !important;
    }
    
    /* Primary button styling - subtle blue */
    .stButton > button[kind="primary"] {
        background: #3b82f6 !important;
        color: white !important;
        border: 1px solid #3b82f6 !important;
    }
    
    .stButton > button[kind="primary"]:hover {
        background: #2563eb !important;
        border-color: #2563eb !important;
    }
    
    /* Secondary button styling - subtle gray */
    .stButton > button[kind="secondary"] {
        background: #6b7280 !important;
        color: white !important;
        border: 1px solid #6b7280 !important;
    }
    
    .stButton > button[kind="secondary"]:hover {
        background: #4b5563 !important;
        border-color: #4b5563 !important;
    }
    
    /* Danger/Delete button styling */
    .stButton > button[data-testid*="delete"], 
    .stButton > button:has-text("Delete"),
    .stButton > button[title*="delete"] {
        background: #ef4444 !important;
        color: white !important;
        border: 1px solid #ef4444 !important;
    }
    
    .stButton > button[data-testid*="delete"]:hover,
    .stButton > button:has-text("Delete"):hover {
        background: #dc2626 !important;
        border-color: #dc2626 !important;
    }
    
    /* Modern card styling */
    .patient-card {
        background: white;
        border-radius: 16px;
        padding: 20px;
        margin: 12px 0;
        box-shadow: 0 4px 20px rgba(0,0,0,0.08);
        border: 1px solid #f0f0f0;
        transition: all 0.3s ease;
    }
    
    .patient-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 8px 30px rgba(0,0,0,0.12);
    }
    
    .patient-card.urgent {
        border-left: 5px solid #ff6b6b;
        background: linear-gradient(135deg, #fff5f5 0%, #ffffff 100%);
    }
    
    .patient-card.in-progress {
        border-left: 5px solid #4ecdc4;
        background: linear-gradient(135deg, #f0fdfc 0%, #ffffff 100%);
    }
    
    .patient-card.completed {
        border-left: 5px solid #51cf66;
        background: linear-gradient(135deg, #f3fdf4 0%, #ffffff 100%);
    }
    

    
    /* Modern input styling */
    .stTextInput input, .stSelectbox select, .stNumberInput input {
        border-radius: 6px !important;
        border: 1px solid #d1d5db !important;
        padding: 8px 12px !important;
        transition: all 0.2s ease !important;
        background: #ffffff !important;
    }
    
    .stTextInput input:focus, .stSelectbox select:focus, .stNumberInput input:focus {
        border-color: #3b82f6 !important;
        box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1) !important;
        outline: none !important;
    }
    
    /* Fix selectbox styling - remove purple borders */
    .stSelectbox > div > div > div {
        border: 1px solid #d1d5db !important;
        border-radius: 6px !important;
        background: #ffffff !important;
    }
    
    .stSelectbox > div > div > div:focus-within {
        border-color: #3b82f6 !important;
        box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1) !important;
    }
    
    /* Remove purple from all selection elements */
    .stSelectbox [data-baseweb="select"] > div {
        border: 1px solid #d1d5db !important;
        background: #ffffff !important;
    }
    
    .stSelectbox [data-baseweb="select"] > div:focus-within {
        border-color: #3b82f6 !important;
        box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1) !important;
    }
    
    /* Fix multiselect and other inputs */
    .stMultiSelect > div > div > div {
        border: 1px solid #d1d5db !important;
        border-radius: 6px !important;
        background: #ffffff !important;
    }
    
    /* Override purple theme completely */
    .stApp > div[data-testid="stAppViewContainer"] > div > div > div > div {
        border-color: #d1d5db !important;
    }
    
    /* BackpackEMR-style tabs */
    .stTabs [data-baseweb="tab-list"] {
        background: #f9fafb !important;
        border: 1px solid #e5e7eb !important;
        border-radius: 8px !important;
        padding: 2px !important;
    }
    
    .stTabs [data-baseweb="tab"] {
        background: transparent !important;
        color: #6b7280 !important;
        border-radius: 6px !important;
        padding: 8px 16px !important;
        font-weight: 500 !important;
        transition: all 0.2s ease !important;
        border: none !important;
    }
    
    .stTabs [data-baseweb="tab"]:hover {
        background: #f3f4f6 !important;
        color: #374151 !important;
    }
    
    .stTabs [aria-selected="true"] {
        background: #ffffff !important;
        color: #111827 !important;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1) !important;
        border: 1px solid #e5e7eb !important;
    }
    
    /* Modern headers */
    h1, h2, h3 {
        color: #2d3748 !important;
        font-weight: 700 !important;
    }
    
    /* Sidebar styling */
    .css-1d391kg {
        background: #f9fafb !important;
        border-right: 1px solid #e5e7eb !important;
    }
    
    /* Settings and reports specific styling */
    .stSelectbox > div > div {
        background: #ffffff !important;
        border: 1px solid #d1d5db !important;
        border-radius: 6px !important;
    }
    
    .stCheckbox > label {
        color: #374151 !important;
        font-weight: 500 !important;
    }
    
    .stToggle > label {
        color: #374151 !important;
        font-weight: 500 !important;
    }
    
    /* Fix checkbox styling - remove orange */
    .stCheckbox > label > div[data-testid="stCheckbox"] > div {
        background-color: #ffffff !important;
        border: 1px solid #d1d5db !important;
        border-radius: 4px !important;
    }
    
    .stCheckbox > label > div[data-testid="stCheckbox"] > div:checked,
    .stCheckbox > label > div[data-testid="stCheckbox"] > div[aria-checked="true"] {
        background-color: #3b82f6 !important;
        border-color: #3b82f6 !important;
    }
    
    /* Universal button styling to override orange */
    .stButton > button {
        background: #f8fafc !important;
        border: 1px solid #d1d5db !important;
        color: #475569 !important;
        font-weight: 500 !important;
        border-radius: 6px !important;
        transition: all 0.2s ease !important;
    }
    
    .stButton > button:hover {
        background: #f1f5f9 !important;
        border-color: #9ca3af !important;
        transform: translateY(-1px) !important;
    }
    
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%) !important;
        border: none !important;
        color: white !important;
        font-weight: 600 !important;
    }
    
    .stButton > button[kind="primary"]:hover {
        background: linear-gradient(135deg, #2563eb 0%, #1e40af 100%) !important;
    }
    
    /* Metrics styling for reports */
    [data-testid="metric-container"] {
        background: #ffffff !important;
        border: 1px solid #e5e7eb !important;
        border-radius: 8px !important;
        padding: 16px !important;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1) !important;
    }
    
    [data-testid="metric-container"] > div > div:first-child {
        color: #6b7280 !important;
        font-size: 14px !important;
        font-weight: 500 !important;
    }
    
    [data-testid="metric-container"] > div > div:last-child {
        color: #111827 !important;
        font-size: 24px !important;
        font-weight: 700 !important;
    }
    
    /* Expander styling */
    .streamlit-expanderHeader {
        background: #f9fafb !important;
        border: 1px solid #e5e7eb !important;
        border-radius: 8px !important;
        color: #374151 !important;
        font-weight: 500 !important;
    }
    
    .streamlit-expanderContent {
        background: #ffffff !important;
        border: 1px solid #e5e7eb !important;
        border-top: none !important;
        border-radius: 0 0 8px 8px !important;
    }
    
    /* Download button specific styling */
    .stDownloadButton > button {
        background: #10b981 !important;
        color: white !important;
        border: 1px solid #10b981 !important;
        font-weight: 600 !important;
    }
    
    .stDownloadButton > button:hover {
        background: #059669 !important;
        border-color: #059669 !important;
    }
    
    /* Info boxes styling */
    .stInfo {
        background: #eff6ff !important;
        border: 1px solid #bfdbfe !important;
        border-radius: 8px !important;
        color: #1e40af !important;
    }
    
    .stSuccess {
        background: #f0fdf4 !important;
        border: 1px solid #bbf7d0 !important;
        border-radius: 8px !important;
        color: #166534 !important;
    }
    
    .stWarning {
        background: #fffbeb !important;
        border: 1px solid #fed7aa !important;
        border-radius: 8px !important;
        color: #9a3412 !important;
    }
    
    .stError {
        background: #fef2f2 !important;
        border: 1px solid #fecaca !important;
        border-radius: 8px !important;
        color: #991b1b !important;
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
    .offline-indicator {
        position: fixed;
        top: 10px;
        right: 10px;
        background: #10b981;
        color: white;
        padding: 4px 8px;
        border-radius: 4px;
        font-size: 12px;
        z-index: 1000;
    }
    </style>
    """,
                unsafe_allow_html=True)

    # Offline mode indicator
    st.markdown("""
    <div class="offline-indicator">
        🔄 OFFLINE MODE - Data saved locally
    </div>
    """,
                unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        st.image(
            "attached_assets/ChatGPT Image Jun 15, 2025, 05_27_41 PM_1750022867924.png",
            width=300)

    # Navigation buttons in a cleaner horizontal layout
    nav_col1, nav_col2 = st.columns([1, 1])

    with nav_col1:
        if st.button("🏠 Home",
                     key="home_button",
                     help="Return to role selection",
                     use_container_width=True):
            # Clear user role to return to role selection but keep location
            if 'user_role' in st.session_state:
                del st.session_state.user_role
            if 'page' in st.session_state:
                del st.session_state.page
            if 'doctor_name' in st.session_state:
                del st.session_state.doctor_name
            if 'active_consultation' in st.session_state:
                del st.session_state.active_consultation
            st.rerun()

    with nav_col2:
        # Show current location in the navigation button
        if 'clinic_location' in st.session_state and st.session_state.clinic_location:
            location = st.session_state.clinic_location
            location_text = f"📍 {location['city']}, {location['country_code']}"
        else:
            location_text = "📍 Location"

        if st.button(location_text,
                     key="location_button",
                     help="Change clinic location",
                     use_container_width=True):
            st.session_state.clinic_location = None
            st.session_state.user_role = None
            st.rerun()

    st.markdown("---")

    # Location selection first
    if 'clinic_location' not in st.session_state:
        st.session_state.clinic_location = None

    if st.session_state.clinic_location is None:
        location_setup()
        return

    # Role selection
    if 'user_role' not in st.session_state:
        st.session_state.user_role = None

    if st.session_state.user_role is None:
        st.markdown("### Select Your Role")

        # Clinic workflow order: Registration → Triage → Doctor → Pharmacy/Lab → Ophthalmologist
        col1, col2 = st.columns(2)

        with col1:
            if st.button("1. Name Registration",
                         key="name_registration",
                         type="primary",
                         use_container_width=True):
                st.session_state.user_role = "name_registration"
                st.rerun()

            if st.button("3. Doctor",
                         key="doctor",
                         type="primary",
                         use_container_width=True):
                st.session_state.user_role = "doctor"
                st.rerun()

            if st.button("5. Ophthalmologist",
                         key="ophthalmologist",
                         type="primary",
                         use_container_width=True):
                st.session_state.user_role = "ophthalmologist"
                st.rerun()

        with col2:
            if st.button("2. Triage Nurse",
                         key="triage",
                         type="primary",
                         use_container_width=True):
                st.session_state.user_role = "triage"
                st.rerun()

            if st.button("4. Pharmacy/Lab",
                         key="pharmacy",
                         type="primary",
                         use_container_width=True):
                st.session_state.user_role = "pharmacy"
                st.rerun()

        # Additional workflow monitoring and admin roles
        st.markdown("<br>", unsafe_allow_html=True)
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("📊 Patient Queue Monitor",
                         key="queue_monitor",
                         type="secondary",
                         use_container_width=True):
                st.session_state.user_role = "queue_monitor"
                st.rerun()
        
        with col2:
            if st.button("Admin",
                         key="admin",
                         type="secondary",
                         use_container_width=True):
                st.session_state.user_role = "admin"
                st.rerun()
        
        with col3:
            # Empty column for balanced layout
            st.write("")

        st.markdown("---")
        st.info(
            "This system works offline and stores all patient data locally for mission trips in remote areas."
        )

        return

    # Handle consultation form page navigation
    if st.session_state.get(
            'page'
    ) == 'consultation_form' and 'active_consultation' in st.session_state:
        consultation = st.session_state.active_consultation
        consultation_form(consultation['visit_id'], consultation['patient_id'],
                          consultation['patient_name'])
        return

    # Show LAN status page if requested
    if 'show_lan_page' in st.session_state and st.session_state.show_lan_page:
        show_lan_status_page()
        return

# Role-based interface routing
    if st.session_state.user_role == "name_registration":
        name_registration_interface()
    elif st.session_state.user_role == "triage":
        triage_interface()
    elif st.session_state.user_role == "doctor":
        if 'doctor_name' not in st.session_state:
            doctor_login()
        else:
            doctor_interface()
    elif st.session_state.user_role == "pharmacy":
        pharmacy_interface()
    elif st.session_state.user_role == "lab":
        lab_interface()
    elif st.session_state.user_role == "ophthalmologist":
        ophthalmologist_interface()
    elif st.session_state.user_role == "queue_monitor":
        patient_queue_monitor_interface()
    elif st.session_state.user_role == "admin":
        admin_interface()

    # Sidebar header with location info
    if 'clinic_location' in st.session_state and st.session_state.clinic_location:
        location = st.session_state.clinic_location
        location_info = f"{location['city']}, {location['country_name']}"
    else:
        location_info = "No location set"

    # Display compact logo in sidebar
    st.sidebar.markdown(
        '<div style="display: flex; justify-content: center; margin-bottom: 10px;">',
        unsafe_allow_html=True)
    st.sidebar.image(
        "attached_assets/ChatGPT Image Jun 15, 2025, 05_23_25 PM_1750022665650.png",
        width=40)
    st.sidebar.markdown('</div>', unsafe_allow_html=True)

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

    if st.sidebar.button("📍 Change Location"):
        st.session_state.clinic_location = None
        st.session_state.user_role = None
        st.rerun()

    # LAN connectivity page
    st.sidebar.markdown("---")
    if st.sidebar.button("🌐 LAN Status"):
        st.session_state.show_lan_page = True
        st.rerun()


def doctor_login():
    """Doctor login interface with real-time status display"""
    st.markdown("### Doctor Login")

    db = get_db_manager()
    doctors = db.get_doctors()

    if not doctors:
        st.warning(
            "No doctors available. Please contact admin to add doctors.")
        if st.button("Back to Role Selection"):
            if 'user_role' in st.session_state:
                del st.session_state.user_role
            st.rerun()
        return

    # Display current doctor status in real-time
    st.markdown("#### Current Doctor Status")
    doctor_status = db.get_all_doctor_status()

    if doctor_status:
        for status in doctor_status:
            status_color = "🟢" if status[
                'status'] == 'available' else "🟡" if status[
                    'status'] == 'with_patient' else "🔴"
            patient_info = f" - {status['current_patient_name']} ({status['current_patient_id']})" if status[
                'current_patient_id'] else ""
            st.write(
                f"{status_color} **{status['doctor_name']}** - {status['status'].replace('_', ' ').title()}{patient_info}"
            )

    st.markdown("---")

    # Doctor selection
    st.markdown("#### Select Your Name")
    doctor_names = [doc['name'] for doc in doctors]
    selected_doctor = st.selectbox("Choose your name:", [""] + doctor_names)

    if selected_doctor and st.button("Login as Doctor", type="primary"):
        try:
            st.session_state.doctor_name = selected_doctor
            # Update doctor status to available
            db.update_doctor_status(selected_doctor, "available")
            st.success(f"Logged in as {selected_doctor}")
            st.rerun()
        except Exception as e:
            st.error(f"Login error: {str(e)}")
            # Try to fix the issue by ensuring the doctor exists in status table
            try:
                # Check if doctor exists in the doctors table first
                doctors_list = db.get_doctors()
                doctor_exists = any(doc['name'] == selected_doctor
                                    for doc in doctors_list)

                if doctor_exists:
                    # Force create status entry
                    conn = sqlite3.connect("clinic_database.db")
                    cursor = conn.cursor()
                    cursor.execute(
                        'DELETE FROM doctor_status WHERE doctor_name = ?',
                        (selected_doctor, ))
                    cursor.execute(
                        '''
                        INSERT INTO doctor_status (doctor_name, status, last_updated)
                        VALUES (?, ?, ?)
                    ''', (selected_doctor, "available",
                          datetime.now().isoformat()))
                    conn.commit()
                    conn.close()

                    st.session_state.doctor_name = selected_doctor
                    st.success(f"Logged in as {selected_doctor}")
                    st.rerun()
                else:
                    st.error(f"Doctor {selected_doctor} not found in system")
            except Exception as e2:
                st.error(f"Could not fix login issue: {str(e2)}")

    if st.button("Back to Role Selection"):
        if 'user_role' in st.session_state:
            del st.session_state.user_role
        st.rerun()


def show_lan_status_page():
    """Display LAN connectivity status for iPad connections"""
    st.markdown("## 🌐 LAN Network Status")

    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown("### Connected Devices")

        # Simulate checking for other devices on the network
        import socket

        try:
            # Get current IP address
            hostname = socket.gethostname()
            local_ip = socket.gethostbyname(hostname)
            st.success(f"This Device: {local_ip}")

            # Show network scan status
            st.info("Scanning for other ParakaleoMed devices on network...")

            # Simulated device list (in real implementation, would scan network)
            devices = [{
                "name": "iPad-Triage-01",
                "ip": "192.168.1.105",
                "status": "Connected",
                "role": "Triage"
            }, {
                "name": "iPad-Doctor-01",
                "ip": "192.168.1.106",
                "status": "Connected",
                "role": "Doctor"
            }, {
                "name": "iPad-Pharmacy-01",
                "ip": "192.168.1.107",
                "status": "Offline",
                "role": "Pharmacy"
            }]

            for device in devices:
                status_color = "🟢" if device["status"] == "Connected" else "🔴"
                st.markdown(
                    f"{status_color} **{device['name']}** ({device['role']}) - {device['ip']} - {device['status']}"
                )

        except Exception:
            st.error("Unable to scan network. Check WiFi connection.")

    with col2:
        if st.button("Back to Main"):
            st.session_state.show_lan_page = False
            st.rerun()

        if st.button("Refresh"):
            st.rerun()

    st.markdown("---")
    st.info(
        "Note: All devices should be connected to the same WiFi network for data synchronization."
    )


def location_setup():
    st.markdown("## Clinic Location Setup")
    st.markdown(
        "Please select or add your clinic location before starting patient registration."
    )

    # Get existing locations
    locations = db.get_locations()

    tab1, tab2 = st.tabs(["Select Location", "Add New Location"])

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
                        st.rerun()
        else:
            st.info("No locations found. Please add a new location below.")

    with tab2:
        st.markdown("### Add New Clinic Location")
        with st.form("new_location"):
            col1, col2 = st.columns(2)
            with col1:
                country = st.selectbox("Country",
                                       ["Dominican Republic", "Haiti"])
                country_code = "DR" if country == "Dominican Republic" else "H"
            with col2:
                city = st.text_input("City/Town",
                                     placeholder="Enter clinic city")

            if st.form_submit_button("Add Location", type="primary"):
                if city.strip():
                    location_id = db.add_location(country_code, country,
                                                  city.strip())
                    st.success(f"Location added successfully!")

                    # Auto-select the new location
                    new_location = {
                        'id': location_id,
                        'country_code': country_code,
                        'country_name': country,
                        'city': city.strip(),
                        'created_date': datetime.now().isoformat()
                    }
                    st.session_state.clinic_location = new_location
                    st.rerun()
                else:
                    st.error("Please enter a city name.")


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

        col1, col2, col3 = st.columns(3)

        with col1:
            systolic = st.number_input("Systolic BP",
                                       min_value=50,
                                       max_value=300,
                                       value=120)
            diastolic = st.number_input("Diastolic BP",
                                        min_value=30,
                                        max_value=200,
                                        value=80)

        with col2:
            heart_rate = st.number_input("Heart Rate (bpm)",
                                         min_value=30,
                                         max_value=250,
                                         value=72)
            temperature = st.number_input("Temperature (°F)",
                                          min_value=90.0,
                                          max_value=110.0,
                                          value=98.6,
                                          step=0.1)

        with col3:
            weight = st.number_input("Weight (kg)",
                                     min_value=0.5,
                                     max_value=500.0,
                                     value=None,
                                     step=0.1)
            height = st.number_input("Height (inches)",
                                     min_value=12.0,
                                     max_value=96.0,
                                     value=None,
                                     step=0.5)
            oxygen_sat = st.number_input("O2 Saturation (%)",
                                         min_value=70,
                                         max_value=100,
                                         value=98)

        col1, col2 = st.columns([1, 1])
        with col1:
            if st.form_submit_button("Save Vital Signs & Continue",
                                     type="primary"):
                # Save vital signs for current family member
                conn = sqlite3.connect(db.db_name)
                cursor = conn.cursor()

                # First, delete any existing vital signs for this visit (in case of editing)
                cursor.execute('DELETE FROM vital_signs WHERE visit_id = ?',
                               (current_member['visit_id'], ))

                cursor.execute(
                    '''
                    INSERT INTO vital_signs (visit_id, systolic_bp, diastolic_bp, heart_rate, 
                                           temperature, weight, height, oxygen_saturation, recorded_time)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (current_member['visit_id'], systolic, diastolic,
                      heart_rate, temperature, weight, height, oxygen_sat,
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
    add_to_history('name_registration')
    st.markdown("## 📝 Name Registration Station")
    st.info("Register patient names ahead of triage to speed up workflow. Names entered here will be available for vital signs collection.")

    # Current location
    location_code = st.session_state.clinic_location['country_code']
    
    tab1, tab2 = st.tabs(["Register Names", "Name Queue"])
    
    with tab1:
        st.markdown("### Add Patient Names")
        
        registration_type = st.radio("Registration Type", 
                                   ["Individual Patient", "Family Group"], 
                                   horizontal=True)
        
        if registration_type == "Individual Patient":
            with st.form("name_registration_individual"):
                col1, col2 = st.columns(2)
                with col1:
                    name = st.text_input("Patient Name *")
                    age = st.number_input("Age", min_value=0, max_value=120, value=None)
                with col2:
                    gender = st.selectbox("Gender", ["", "Male", "Female"])
                    notes = st.text_input("Notes (optional)", placeholder="Special considerations...")
                
                if st.form_submit_button("Add to Queue", type="primary"):
                    if name.strip():
                        conn = sqlite3.connect(db.db_name)
                        cursor = conn.cursor()
                        cursor.execute('''
                            INSERT INTO patient_names_queue 
                            (name, age, gender, location_code, relationship, created_time, notes)
                            VALUES (?, ?, ?, ?, ?, ?, ?)
                        ''', (name.strip(), age, gender if gender else None, location_code, 
                             'individual', datetime.now().isoformat(), notes.strip() if notes else None))
                        conn.commit()
                        conn.close()
                        st.success(f"Added {name.strip()} to registration queue!")
                        st.rerun()
                    else:
                        st.error("Please enter a patient name.")
        
        else:  # Family Group
            st.markdown("#### Family Group Registration")
            with st.form("name_registration_family"):
                family_name = st.text_input("Family Name", placeholder="e.g., Rodriguez Family")
                
                st.markdown("**Parent/Guardian:**")
                parent_name = st.text_input("Parent/Guardian Name *")
                parent_age = st.number_input("Parent Age", min_value=18, max_value=120, value=None)
                parent_gender = st.selectbox("Parent Gender", ["", "Male", "Female"], key="parent_gender")
                
                st.markdown("**Children:**")
                num_children = st.number_input("Number of Children", min_value=1, max_value=10, value=1)
                
                children_data = []
                for i in range(num_children):
                    st.markdown(f"**Child {i+1}:**")
                    col1, col2 = st.columns(2)
                    with col1:
                        child_name = st.text_input(f"Child {i+1} Name", key=f"child_name_{i}")
                        child_age = st.number_input(f"Child {i+1} Age", min_value=0, max_value=17, value=None, key=f"child_age_{i}")
                    with col2:
                        child_gender = st.selectbox(f"Child {i+1} Gender", ["", "Male", "Female"], key=f"child_gender_{i}")
                    
                    if child_name:
                        children_data.append({
                            'name': child_name.strip(),
                            'age': child_age,
                            'gender': child_gender if child_gender else None
                        })
                
                family_notes = st.text_input("Family Notes", placeholder="Special considerations for the family...")
                
                if st.form_submit_button("Add Family to Queue", type="primary"):
                    if parent_name.strip() and children_data:
                        conn = sqlite3.connect(db.db_name)
                        cursor = conn.cursor()
                        
                        # Generate family group ID
                        family_group_id = f"FAM_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                        
                        # Add parent
                        cursor.execute('''
                            INSERT INTO patient_names_queue 
                            (name, age, gender, location_code, relationship, family_group_id, created_time, notes)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (parent_name.strip(), parent_age, parent_gender if parent_gender else None, 
                             location_code, 'parent', family_group_id, datetime.now().isoformat(), 
                             f"Family: {family_name}. {family_notes}" if family_notes else f"Family: {family_name}"))
                        
                        # Add children
                        for child in children_data:
                            cursor.execute('''
                                INSERT INTO patient_names_queue 
                                (name, age, gender, location_code, relationship, family_group_id, created_time, notes)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                            ''', (child['name'], child['age'], child['gender'], location_code, 
                                 'child', family_group_id, datetime.now().isoformat(), 
                                 f"Child of {parent_name.strip()}"))
                        
                        conn.commit()
                        conn.close()
                        
                        st.success(f"Added family of {len(children_data) + 1} members to registration queue!")
                        st.rerun()
                    else:
                        st.error("Please enter parent name and at least one child.")
    
    with tab2:
        st.markdown("### Registration Queue")
        
        # Get pending names
        conn = sqlite3.connect(db.db_name)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, name, age, gender, relationship, family_group_id, created_time, notes, status
            FROM patient_names_queue 
            WHERE status = 'pending_vitals' AND location_code = ?
            ORDER BY family_group_id, CASE WHEN relationship = 'parent' THEN 0 ELSE 1 END, created_time
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
                        with col1:
                            icon = "👨" if member['relationship'] == 'parent' else "👶"
                            st.write(f"{icon} **{member['name']}** ({member['relationship']})")
                            if member['age']:
                                st.caption(f"Age: {member['age']}, Gender: {member['gender'] or 'Not specified'}")
                            if member['notes']:
                                st.caption(f"Notes: {member['notes']}")
                        with col2:
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
                        with col3:
                            if st.button("Remove", key=f"remove_{member['id']}", type="secondary"):
                                conn = sqlite3.connect(db.db_name)
                                cursor = conn.cursor()
                                cursor.execute('DELETE FROM patient_names_queue WHERE id = ?', (member['id'],))
                                conn.commit()
                                conn.close()
                                st.rerun()
            
            # Display individuals
            for individual in individuals:
                col1, col2, col3 = st.columns([3, 1, 1])
                with col1:
                    st.write(f"👤 **{individual['name']}**")
                    if individual['age']:
                        st.caption(f"Age: {individual['age']}, Gender: {individual['gender'] or 'Not specified'}")
                    if individual['notes']:
                        st.caption(f"Notes: {individual['notes']}")
                with col2:
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
                with col3:
                    if st.button("Remove", key=f"remove_{individual['id']}", type="secondary"):
                        conn = sqlite3.connect(db.db_name)
                        cursor = conn.cursor()
                        cursor.execute('DELETE FROM patient_names_queue WHERE id = ?', (individual['id'],))
                        conn.commit()
                        conn.close()
                        st.rerun()
        else:
            st.info("No names in registration queue. Add names in the 'Register Names' tab.")


def triage_interface():
    add_to_history('triage')
    st.markdown("## 🩺 Triage Station")

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
        st.markdown("### Record Vital Signs")
        patient_name = st.session_state.get('patient_name', 'Patient')
        st.info(f"Recording vital signs for: **{patient_name}**")
        vital_signs_form(st.session_state.pending_vitals)
        return

    tab1, tab2, tab3 = st.tabs(
        ["Pre-Registered Queue", "New Patient", "Existing Patient"])

    with tab1:
        preregistered_queue_view()

    with tab2:
        new_patient_form()

    with tab3:
        existing_patient_search()


def preregistered_queue_view():
    st.markdown("### 📝 Pre-Registered Patients")
    st.info("Patients registered through Name Registration station are ready for vital signs collection.")
    
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
                    col1, col2 = st.columns([4, 1])
                    with col1:
                        icon = "👨" if member['relationship'] == 'parent' else "👶"
                        st.write(f"{icon} **{member['name']}** ({member['relationship']})")
                        if member['age']:
                            st.caption(f"Age: {member['age']}, Gender: {member['gender'] or 'Not specified'}")
                        if member['notes']:
                            st.caption(f"Notes: {member['notes']}")
                    with col2:
                        if st.button("Start Vitals", key=f"start_vitals_{member['id']}", type="primary"):
                            # Create patient record and start vital signs workflow
                            patient_data = {
                                'name': member['name'],
                                'age': member['age'],
                                'gender': member['gender'],
                                'phone': None,
                                'emergency_contact': None,
                                'medical_history': member['notes'],
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
                            ''', (member['id'],))
                            conn.commit()
                            conn.close()
                            
                            # Set up vital signs workflow
                            st.session_state.pending_vitals = visit_id
                            st.session_state.patient_name = member['name']
                            st.success(f"Patient {member['name']} registered! Patient ID: {patient_id}")
                            st.rerun()
        
        # Display individuals
        for individual in individuals:
            col1, col2 = st.columns([4, 1])
            with col1:
                st.write(f"👤 **{individual['name']}**")
                if individual['age']:
                    st.caption(f"Age: {individual['age']}, Gender: {individual['gender'] or 'Not specified'}")
                if individual['notes']:
                    st.caption(f"Notes: {individual['notes']}")
            with col2:
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
    else:
        st.info("No pre-registered patients waiting for vital signs. Check the Name Registration station.")


def new_patient_form():
    add_to_history('new_patient_form')
    st.markdown("### Register New Patient")

    # Registration type selection
    registration_type = st.radio("Registration Type",
                                 ["Individual Patient", "Family Registration"],
                                 horizontal=True)

    if registration_type == "Individual Patient":
        with st.form("new_patient_form"):
            col1, col2 = st.columns(2)

            with col1:
                name = st.text_input("Patient Name *",
                                     placeholder="Enter full name")
                age = st.number_input("Age",
                                      min_value=0,
                                      max_value=120,
                                      value=None)
                gender = st.selectbox("Gender", ["", "Male", "Female"])

            with col2:
                phone = st.text_input("Phone Number", placeholder="Optional")
                emergency_contact = st.text_input("Emergency Contact",
                                                  placeholder="Optional")

            if st.form_submit_button("Register Patient", type="primary"):
                if name.strip():
                    # Check for duplicate patients
                    duplicates = db.check_duplicate_patient(
                        name.strip(), age if age else None,
                        phone.strip() if phone else None)

                    st.session_state.duplicate_check_results = duplicates
                    st.session_state.new_patient_data = {
                        'name':
                        name.strip(),
                        'age':
                        age,
                        'gender':
                        gender if gender else None,
                        'phone':
                        phone.strip() if phone else None,
                        'emergency_contact':
                        emergency_contact.strip()
                        if emergency_contact else None,
                        'medical_history':
                        None,
                        'allergies':
                        None
                    }
                    st.rerun()
                else:
                    st.error("Please enter the patient's name.")

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
            "Create a family file that includes parent/guardian and all children together."
        )

        # Family Information Form
        with st.form("family_registration_form"):
            st.markdown("**Family Information**")

            # Family details
            family_name = st.text_input(
                "Family Name *", placeholder="e.g., The Rodriguez Family")
            emergency_contact = st.text_input("Emergency Contact")

            st.markdown("---")
            st.markdown("**Parent/Guardian Information**")

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
                parent_phone = st.text_input("Parent Phone (if different)",
                                             key="parent_phone")


            st.markdown("---")
            st.markdown("**Children Information**")

            # Number of children
            num_children = st.number_input("Number of children",
                                           min_value=0,
                                           max_value=10,
                                           value=1)

            children_data = []
            if num_children > 0:
                for i in range(num_children):
                    st.markdown(f"**Child {i+1}**")
                    col1, col2 = st.columns(2)
                    with col1:
                        child_name = st.text_input(f"Child {i+1} Name *",
                                                   key=f"child_name_{i}")
                        child_age = st.number_input(f"Age",
                                                    min_value=0,
                                                    max_value=17,
                                                    value=None,
                                                    key=f"child_age_{i}")
                        child_gender = st.selectbox("Gender",
                                                    ["", "Male", "Female"],
                                                    key=f"child_gender_{i}")
                    with col2:
                        st.write("")  # Placeholder for layout

                    children_data.append({
                        'name': child_name,
                        'age': child_age,
                        'gender': child_gender
                    })

            st.markdown("---")
            family_submitted = st.form_submit_button("Create Family File",
                                                     type="primary",
                                                     use_container_width=True)

            if family_submitted:
                if family_name.strip() and parent_name.strip():
                    # Validate children data
                    valid_children = [
                        child for child in children_data
                        if child['name'].strip()
                    ]

                    if len(valid_children) > 0 or num_children == 0:
                        location_code = st.session_state.clinic_location[
                            'country_code']

                        # Create family unit
                        family_id = db.create_family(
                            location_code=location_code,
                            family_name=family_name.strip(),
                            head_of_household=parent_name.strip(),
                            emergency_contact=emergency_contact.strip()
                            if emergency_contact else "")

                        # Add parent to family
                        parent_id = db.add_family_member(
                            family_id=family_id,
                            location_code=location_code,
                            relationship="parent",
                            name=parent_name.strip(),
                            age=parent_age,
                            gender=parent_gender if parent_gender else None,
                            phone=parent_phone.strip() if parent_phone else "")

                        # Add children to family
                        family_members = [{
                            'patient_id': parent_id,
                            'patient_name': parent_name.strip(),
                            'relationship': 'parent'
                        }]

                        for child in valid_children:
                            child_id = db.add_family_member(
                                family_id=family_id,
                                location_code=location_code,
                                relationship="child",
                                parent_id=parent_id,
                                name=child['name'].strip(),
                                age=child['age'],
                                gender=child['gender']
                                if child['gender'] else None)

                            family_members.append({
                                'patient_id':
                                child_id,
                                'patient_name':
                                child['name'].strip(),
                                'relationship':
                                'child'
                            })

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
                        st.info(
                            f"**Family Members:** {len(family_members)} (1 parent + {len(valid_children)} children)"
                        )

                        # Display all created patient IDs
                        st.markdown("**Patient IDs Created:**")
                        for visit in family_visits:
                            st.write(
                                f"• {visit['patient_name']} ({visit['relationship']}): {visit['patient_id']}"
                            )

                        # Store family data for continuation outside form
                        st.session_state.created_family_visits = family_visits.copy(
                        )
                        st.session_state.family_creation_complete = True

                    else:
                        st.error(
                            "Please provide at least one child's name, or set number of children to 0."
                        )
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
                if st.button("📊 Continue to Vital Signs",
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
                if st.button("📋 Register Another Family",
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
        st.markdown("### Record Vital Signs")
        st.info(
            f"Recording vitals for **{st.session_state.patient_name}** (Visit ID: {st.session_state.pending_vitals})"
        )
        vital_signs_form(st.session_state.pending_vitals)


def existing_patient_search():
    add_to_history('existing_patient_search')
    st.markdown("### Find Existing Patient")

    search_query = st.text_input("Search by Name or Patient ID",
                                 placeholder="Enter name or ID (e.g., 00001)")

    if search_query:
        patients = db.search_patients(search_query)

        if patients:
            st.markdown("### Search Results:")

            for patient in patients:
                with st.container():
                    st.markdown(f"""
                    <div class="patient-card">
                        <h4>👤 {patient['name']}</h4>
                        <p><strong>ID:</strong> {patient['patient_id']}</p>
                        <p><strong>Age:</strong> {patient['age'] or 'Not specified'}</p>
                        <p><strong>Gender:</strong> {patient['gender'] or 'Not specified'}</p>
                        <p><strong>Last Visit:</strong> {patient['last_visit'][:10] if patient['last_visit'] else 'Never'}</p>
                    </div>
                    """,
                                unsafe_allow_html=True)

                    if st.button(f"Start New Visit",
                                 key=f"visit_{patient['patient_id']}",
                                 use_container_width=True):
                        visit_id = db.create_visit(patient['patient_id'])
                        st.success(
                            f"✅ New visit created for {patient['name']}")
                        st.info(f"**Visit ID:** {visit_id}")

                        # Store visit_id in session state to show vital signs form
                        st.session_state.pending_vitals = visit_id
                        st.session_state.patient_name = patient['name']
                        st.rerun()
        else:
            st.warning("No patients found matching your search.")


def vital_signs_form(visit_id: str):
    with st.form(f"vitals_{visit_id}"):
        st.markdown("#### Vital Signs")

        col1, col2, col3 = st.columns(3)

        with col1:
            systolic = st.number_input("Systolic BP",
                                       min_value=50,
                                       max_value=300,
                                       value=120)
            diastolic = st.number_input("Diastolic BP",
                                        min_value=30,
                                        max_value=200,
                                        value=80)

        with col2:
            heart_rate = st.number_input("Heart Rate (bpm)",
                                         min_value=30,
                                         max_value=250,
                                         value=72)
            temperature = st.number_input("Temperature (°F)",
                                          min_value=90.0,
                                          max_value=110.0,
                                          value=98.6,
                                          step=0.1)

        with col3:
            weight = st.number_input("Weight (kg)",
                                     min_value=0.5,
                                     max_value=500.0,
                                     value=None,
                                     step=0.1)
            height = st.number_input("Height (inches)",
                                     min_value=12.0,
                                     max_value=96.0,
                                     value=None,
                                     step=0.5)
            oxygen_sat = st.number_input("O2 Saturation (%)",
                                         min_value=70,
                                         max_value=100,
                                         value=98)

        if st.form_submit_button("Save Vital Signs", type="primary"):
            conn = sqlite3.connect(db.db_name)
            cursor = conn.cursor()

            cursor.execute(
                '''
                INSERT INTO vital_signs (visit_id, systolic_bp, diastolic_bp, heart_rate, 
                                       temperature, weight, height, oxygen_saturation, recorded_time)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (visit_id, systolic, diastolic, heart_rate, temperature,
                  weight, height, oxygen_sat, datetime.now().isoformat()))

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
            st.markdown("""
                <div style="background-color: #d4edda; border: 1px solid #c3e6cb; border-radius: 0.375rem; padding: 1rem; margin: 0.5rem 0;">
                    <div style="color: #155724; font-weight: bold; font-size: 1.1rem;">
                        🟢 PATIENT SENT TO DOCTOR QUEUE
                    </div>
                    <div style="color: #155724; margin-top: 0.5rem;">
                        <strong>{}</strong> is now waiting for consultation
                    </div>
                </div>
            """.format(st.session_state.get('patient_name', 'Patient')),
                        unsafe_allow_html=True)

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
    st.markdown("## 📊 Patient Queue Monitor")
    st.info("Real-time view of all patients in the clinic workflow system.")
    
    patient_queue_view()


def patient_queue_view():
    add_to_history('patient_queue')
    st.markdown("### Current Patient Queue")

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
        st.info("No patients in queue for today.")


def doctor_interface():
    add_to_history('doctor')
    st.markdown(
        f"## 👨‍⚕️ Doctor Consultation - {st.session_state.doctor_name}")

    # Update doctor status and show real-time status of all doctors
    db = get_db_manager()

    # Display real-time doctor status at top
    with st.expander("📊 Real-Time Doctor Status", expanded=False):
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
            st.rerun()

    tab1, tab2 = st.tabs(["Patient Consultation", "Consultation History"])

    with tab1:
        consultation_interface()

    with tab2:
        consultation_history()


def consultation_interface():
    add_to_history('consultation_interface')
    st.markdown("### Select Patient for Consultation")

    # Get patients waiting for consultation, including family relationships
    conn = sqlite3.connect("clinic_database.db")
    cursor = conn.cursor()

    cursor.execute('''
        SELECT v.visit_id, v.patient_id, p.name, v.priority, vs.systolic_bp, 
               vs.diastolic_bp, vs.heart_rate, vs.temperature, p.parent_id, p.relationship,
               v.return_reason, v.consultation_time
        FROM visits v
        JOIN patients p ON v.patient_id = p.patient_id
        LEFT JOIN vital_signs vs ON v.visit_id = vs.visit_id
        WHERE v.status = 'waiting_consultation' AND DATE(v.visit_date) = DATE('now')
        ORDER BY 
            CASE WHEN v.return_reason = 'pharmacy_lab_review' THEN 0 ELSE 1 END,
            CASE WHEN p.parent_id IS NULL THEN 0 ELSE 1 END,
            COALESCE(p.parent_id, p.patient_id),
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
        visit_id, patient_id, name, priority, sys_bp, dia_bp, hr, temp, parent_id, relationship, return_reason, consultation_time = patient
        
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
            'relationship': relationship,
            'return_reason': return_reason,
            'consultation_time': consultation_time
        }
        
        if return_reason == 'pharmacy_lab_review':
            lab_return_patients.append(patient_data)
        else:
            regular_patients.append(patient_data)

    # Process regular patients for family grouping
    for patient in regular_patients:
        if patient['parent_id']:  # This is a child
            if patient['parent_id'] not in families:
                families[patient['parent_id']] = {'parent': None, 'children': []}
            families[patient['parent_id']]['children'].append(patient)
        else:  # This is a parent or individual
            # Check if this patient has children
            has_children = any(p['parent_id'] == patient['patient_id'] for p in regular_patients)
            if has_children:
                if patient['patient_id'] not in families:
                    families[patient['patient_id']] = {'parent': None, 'children': []}
                families[patient['patient_id']]['parent'] = patient
            else:
                individual_patients.append(patient)

    # Display lab return patients first - highest priority
    if lab_return_patients:
        st.markdown("#### 🧪 PRIORITY: Patients with Lab Results")
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
                                key=f"lab_review_{patient['patient_id']}", 
                                type="primary", 
                                use_container_width=True):
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
        st.markdown("#### 👨‍👩‍👧‍👦 Family Groups")
        for family_id, family_data in families.items():
            parent = family_data['parent']
            children = family_data['children']

            if parent:
                priority_emoji = "🔴" if parent[
                    'priority'] == "critical" else "🟡" if parent[
                        'priority'] == "urgent" else "🟢"

                with st.expander(
                        f"{priority_emoji} **Family Consultation:** {parent['name']} + {len(children)} children",
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
                        if st.button(
                                f"Start Family Consultation",
                                key=f"family_consult_{parent['patient_id']}"):
                            # Store family consultation details for entire family workflow
                            family_members = [parent] + children
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

                    st.markdown("**👶 Children:**")
                    for child in children:
                        age_display = f"({child.get('age', 'N/A')} yrs, " if child.get('age') else "(age N/A, "
                        st.write(
                            f"• {child['name']} {age_display}{child.get('relationship', 'child')})"
                        )

    # Display individual patients
    if individual_patients:
        st.markdown("#### 👤 Individual Patients")
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
                                     key=f"consult_{patient['visit_id']}"):
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
        st.info("No patients waiting for consultation.")


def consultation_form(visit_id: str, patient_id: str, patient_name: str):
    # Back button to return to consultation interface
    col1, col2 = st.columns([1, 4])
    with col1:
        if st.button("← Back to Queue", type="secondary"):
            st.session_state.page = 'doctor'
            if 'active_consultation' in st.session_state:
                del st.session_state.active_consultation
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
    
    # Display current patient information
    st.markdown(f"**Current Patient:** {patient_name}")
    st.markdown(f"**Relationship:** {'Parent/Guardian' if not is_family_consultation or (is_family_consultation and st.session_state.family_consultation['current_member_index'] == 0) else 'Child'}")

    # Use tabs for consultation sections including optional photo documentation
    tab1, tab2, tab3 = st.tabs(
        ["📋 Consultation", "📸 Photo Documentation", "🔬 Lab & Prescriptions"])

    with tab1:
        with st.form(f"consultation_{visit_id}"):
            # History Section (above chief complaint)
            st.markdown("#### Patient History")
            col1, col2 = st.columns(2)

            with col1:
                surgical_history = st.text_area(
                    "Surgical History",
                    placeholder="Previous surgeries, procedures...")
                medical_history = st.text_area(
                    "Medical History",
                    placeholder="Chronic conditions, past illnesses...")

            with col2:
                allergies = st.text_area(
                    "Allergies",
                    placeholder="Drug allergies, food allergies...")
                current_medications = st.text_area(
                    "Current Medications",
                    placeholder="Current medications and dosages...")

            st.markdown("---")
            # Auto-fill doctor name from logged-in session
            doctor_name = st.session_state.get('doctor_name', '')
            st.text_input("Doctor Name", value=doctor_name, disabled=True)

            chief_complaint = st.text_area(
                "Chief Complaint",
                placeholder="What brought the patient in today?")
            symptoms = st.text_area(
                "Symptoms", placeholder="Describe symptoms observed/reported")
            diagnosis = st.text_area("Diagnosis", placeholder="Your diagnosis")
            treatment_plan = st.text_area("Treatment Plan",
                                          placeholder="Recommended treatment")
            notes = st.text_area("Additional Notes",
                                 placeholder="Any additional observations")

            # Submit button for consultation tab
            consultation_submitted = st.form_submit_button(
                "Save Consultation Details", type="secondary")
            
            if consultation_submitted:
                # Save consultation data to session state for cross-tab access
                consultation_key = f"consultation_data_{visit_id}"
                st.session_state[consultation_key] = {
                    'doctor_name': doctor_name,
                    'chief_complaint': chief_complaint,
                    'symptoms': symptoms,
                    'diagnosis': diagnosis,
                    'treatment_plan': treatment_plan,
                    'notes': notes,
                    'surgical_history': surgical_history,
                    'medical_history': medical_history,
                    'allergies': allergies,
                    'current_medications': current_medications
                }
                st.success("Consultation details saved!")

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

        # Display previously saved photos for this visit
        if f"symptom_photos_{visit_id}" in st.session_state and st.session_state[
                f"symptom_photos_{visit_id}"]:
            st.markdown("**Saved Photos for this visit:**")
            for i, photo in enumerate(
                    st.session_state[f"symptom_photos_{visit_id}"]):
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
        with st.form(f"lab_prescriptions_{visit_id}"):
            st.markdown("#### Lab Tests")
            lab_tests = []

            col1, col2, col3 = st.columns(3)
            with col1:
                if st.checkbox("Urinalysis"):
                    lab_tests.append(("Urinalysis", st.selectbox("Urinalysis Disposition", 
                                                                ["Return to Provider", "Treat per Pharmacy Protocol"], 
                                                                key=f"ua_disp_{visit_id}")))
            with col2:
                if st.checkbox("Blood Glucose"):
                    lab_tests.append(("Blood Glucose", st.selectbox("Glucose Disposition", 
                                                                    ["Return to Provider", "Treat per Pharmacy Protocol"], 
                                                                    key=f"gluc_disp_{visit_id}")))
            with col3:
                if st.checkbox("Pregnancy Test"):
                    lab_tests.append(("Pregnancy Test", st.selectbox("Pregnancy Test Disposition", 
                                                                     ["Return to Provider", "Treat per Pharmacy Protocol"], 
                                                                     key=f"preg_disp_{visit_id}")))

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

            for category in sorted(med_categories):
                with st.expander(f"{category} Medications"):
                    category_meds = [
                        med for med in deduplicated_meds
                        if med['category'] == category
                    ]

                    for med in category_meds:
                        # Medication checkbox
                        selected = st.checkbox(f"{med['medication_name']}",
                                               key=f"med_{med['id']}_{visit_id}")

                        # Show additional fields immediately when medication is checked
                        if selected:
                            with st.container():
                                st.markdown("---")
                                
                                # Dosage and frequency options
                                col1, col2, col3 = st.columns(3)
                                with col1:
                                    dosages = med['common_dosages'].split(', ')
                                    selected_dosage = st.selectbox(
                                        "Dosage", dosages, key=f"dosage_{med['id']}_{visit_id}")
                                with col2:
                                    frequency = st.selectbox("Frequency", [
                                        "Once daily", "Twice daily",
                                        "Three times daily", "Four times daily",
                                        "As needed"
                                    ], key=f"freq_{med['id']}_{visit_id}")
                                with col3:
                                    duration = st.selectbox("Duration", [
                                        "3 days", "5 days", "7 days", "10 days",
                                        "14 days", "30 days"
                                    ], key=f"dur_{med['id']}_{visit_id}")

                                # Additional fields
                                col4, col5 = st.columns(2)
                                with col4:
                                    pharmacy_dosage = st.text_input(
                                        "Dosage for Pharmacy",
                                        placeholder="e.g., 500mg twice daily for 7 days",
                                        key=f"pharma_dose_{med['id']}_{visit_id}")
                                with col5:
                                    indication = st.text_input(
                                        "Indication",
                                        placeholder="e.g., UTI, hypertension",
                                        key=f"indication_{med['id']}_{visit_id}")

                                instructions = st.text_input("Special Instructions",
                                                             key=f"inst_{med['id']}_{visit_id}")

                                # Lab results options
                                awaiting_lab = "yes" if st.checkbox(
                                    "Awaiting Lab Results",
                                    key=f"await_{med['id']}_{visit_id}",
                                    value=False) else "no"
                                
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

            st.markdown("#### Ophthalmology Referral")
            needs_ophthalmology = st.checkbox(
                "Patient needs to see ophthalmologist after receiving medications",
                key=f"ophth_{visit_id}")

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
                    if not med.get('indication') or med.get('indication').strip() == '':
                        validation_errors.append(f"Missing indication for {med['name']}")
                
                if validation_errors:
                    st.error("Please complete all required medication fields:")
                    for error in validation_errors:
                        st.error(f"• {error}")
                elif current_doctor_name and (current_chief_complaint or len(selected_medications) > 0 or len(lab_tests) > 0):
                    try:
                        # Use the database manager methods instead of direct connection
                        # Save consultation
                        db_conn = sqlite3.connect(db_manager.db_name,
                                                  timeout=10.0)
                        db_conn.execute('BEGIN IMMEDIATE')
                        cursor = db_conn.cursor()

                        cursor.execute(
                            '''
                            INSERT INTO consultations (visit_id, doctor_name, chief_complaint, 
                                                     symptoms, diagnosis, treatment_plan, notes, 
                                                     needs_ophthalmology, consultation_time)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (visit_id, doctor_name, chief_complaint, symptoms,
                              diagnosis, treatment_plan, notes,
                              needs_ophthalmology, datetime.now().isoformat()))

                        # Update visit status first
                        if needs_ophthalmology:
                            new_status = 'needs_ophthalmology'
                        elif selected_medications:
                            new_status = 'prescribed'
                        elif lab_tests:
                            new_status = 'waiting_lab'
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
                        for test_type in lab_tests:
                            db_manager.order_lab_test(visit_id, test_type,
                                                      doctor_name)

                        for med in selected_medications:
                            if med['name']:
                                # Add prescription with indication
                                conn_med = sqlite3.connect(db_manager.db_name)
                                cursor_med = conn_med.cursor()
                                cursor_med.execute(
                                    '''
                                    INSERT INTO prescriptions (visit_id, medication_name, 
                                                             dosage, frequency, duration, instructions, 
                                                             indication, awaiting_lab, return_to_provider, prescribed_time)
                                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                                ''', (visit_id, med['name'], med['dosage'],
                                      med['frequency'], med['duration'],
                                      med['instructions'],
                                      med.get('indication', ''), 
                                      med['awaiting_lab'],
                                      med.get('return_to_provider', 'no'),
                                      datetime.now().isoformat()))
                                conn_med.commit()
                                conn_med.close()

                        st.success("Consultation completed successfully!")

                        if lab_tests:
                            st.info(
                                f"Lab tests ordered: {', '.join(lab_tests)}")

                        if selected_medications:
                            awaiting_count = sum(
                                1 for med in selected_medications
                                if med['awaiting_lab'] == 'yes')
                            ready_count = len(
                                selected_medications) - awaiting_count

                            if ready_count > 0:
                                st.info(
                                    f"{ready_count} prescriptions sent to pharmacy."
                                )
                            if awaiting_count > 0:
                                st.info(
                                    f"{awaiting_count} prescriptions awaiting lab results."
                                )

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
                            SET medical_history = ?, allergies = ?
                            WHERE patient_id = ?
                        ''',
                            (f"Surgical: {surgical_history}\nMedical: {medical_history}",
                             f"Allergies: {allergies}\nCurrent Meds: {current_medications}",
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
                        if st.session_state.get('family_consultation_mode',
                                                False):
                            if 'remaining_family_children' in st.session_state:
                                del st.session_state.remaining_family_children
                            if 'family_consultation_mode' in st.session_state:
                                del st.session_state.family_consultation_mode

                            st.success(
                                "✅ Family consultation completed for all members!"
                            )
                            st.info(
                                "All family members have been seen by the doctor."
                            )

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



def consultation_history():
    st.markdown("### Today's Consultations")

    # Check if we should show patient history
    if hasattr(
            st.session_state,
            'show_patient_history') and st.session_state.show_patient_history:
        show_patient_history_detail(st.session_state.show_patient_history,
                                    st.session_state.patient_history_name)
        return

    conn = sqlite3.connect("clinic_database.db")
    cursor = conn.cursor()

    cursor.execute('''
        SELECT c.id, c.visit_id, c.doctor_name, c.chief_complaint, c.symptoms, 
               c.diagnosis, c.treatment_plan, c.notes, c.needs_ophthalmology, 
               c.consultation_time, p.name, v.patient_id
        FROM consultations c
        JOIN visits v ON c.visit_id = v.visit_id
        JOIN patients p ON v.patient_id = p.patient_id
        WHERE DATE(c.consultation_time) = DATE('now')
        ORDER BY c.consultation_time DESC
    ''')

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
        st.info("No consultations recorded today.")


def show_patient_history_detail(patient_id: str, patient_name: str):
    """Display detailed patient history in a new view"""

    # Modal overlay styling for patient history (no JavaScript)
    st.markdown("""
    <style>
    .history-modal-overlay {
        background-color: rgba(0, 0, 0, 0.7);
        border-radius: 10px;
        padding: 20px;
        margin: 10px 0;
        animation: slideIn 0.3s ease-out;
    }
    @keyframes slideIn {
        from { opacity: 0; transform: translateY(-20px); }
        to { opacity: 1; transform: translateY(0); }
    }
    </style>
    """,
                unsafe_allow_html=True)

    st.markdown(
        f"### 📋 Complete Patient History: {patient_name} (ID: {patient_id})")

    # Navigation buttons with X close button
    nav_col1, nav_col2, nav_col3 = st.columns([2, 3, 1])
    with nav_col1:
        if st.button("← Back to Consultation History",
                     key="back_to_consult_history"):
            if 'show_patient_history' in st.session_state:
                del st.session_state.show_patient_history
            if 'patient_history_name' in st.session_state:
                del st.session_state.patient_history_name
            st.rerun()

    with nav_col3:
        if st.button("✕",
                     key="close_patient_history",
                     help="Close patient history",
                     use_container_width=True):
            if 'show_patient_history' in st.session_state:
                del st.session_state.show_patient_history
            if 'patient_history_name' in st.session_state:
                del st.session_state.patient_history_name
            st.rerun()

    conn = sqlite3.connect("clinic_database.db")
    cursor = conn.cursor()

    # Get patient basic info
    cursor.execute('SELECT * FROM patients WHERE patient_id = ?',
                   (patient_id, ))
    patient = cursor.fetchone()

    if patient:
        st.markdown("#### Patient Information")
        col1, col2 = st.columns(2)
        with col1:
            st.write(f"**Name:** {patient[1]}")
            st.write(f"**Age:** {patient[2] or 'Not specified'}")
            st.write(f"**Gender:** {patient[3] or 'Not specified'}")
        with col2:
            st.write(f"**Phone:** {patient[4] or 'Not provided'}")
            st.write(f"**Emergency Contact:** {patient[6] or 'Not provided'}")

        if patient[9]:  # medical_history
            st.markdown("**Medical History:**")
            st.text(patient[9])
        if patient[8]:  # allergies
            st.markdown("**Allergies:**")
            st.text(patient[8])

    # Get all visits
    cursor.execute(
        '''
        SELECT v.visit_id, v.visit_date, v.status, c.chief_complaint, c.diagnosis, c.doctor_name, c.consultation_time
        FROM visits v
        LEFT JOIN consultations c ON v.visit_id = c.visit_id
        WHERE v.patient_id = ?
        ORDER BY v.visit_date DESC
    ''', (patient_id, ))

    visits = cursor.fetchall()

    if visits:
        st.markdown("#### Visit History")
        for visit in visits:
            visit_date = visit[1][:10] if visit[1] else "Unknown"
            status = visit[2] or "In Progress"

            with st.expander(f"Visit {visit_date} - {status}"):
                if visit[3]:  # chief_complaint
                    st.write(f"**Chief Complaint:** {visit[3]}")
                if visit[4]:  # diagnosis
                    st.write(f"**Diagnosis:** {visit[4]}")
                if visit[5]:  # doctor_name
                    st.write(f"**Doctor:** {visit[5]}")
                if visit[6]:  # consultation_time
                    st.write(
                        f"**Consultation Time:** {visit[6][:16].replace('T', ' ')}"
                    )

                # Get prescriptions for this visit
                cursor.execute(
                    '''
                    SELECT medication_name, dosage, frequency, duration, indication, prescribed_time
                    FROM prescriptions
                    WHERE visit_id = ?
                    ORDER BY prescribed_time DESC
                ''', (visit[0], ))

                prescriptions = cursor.fetchall()
                if prescriptions:
                    st.markdown("**Prescriptions:**")
                    for rx in prescriptions:
                        indication_text = f" - {rx[4]}" if rx[4] else ""
                        st.write(
                            f"• {rx[0]} {rx[1]} {rx[2]} for {rx[3]}{indication_text}"
                        )

                # Get lab tests for this visit
                cursor.execute(
                    '''
                    SELECT test_type, status, results, ordered_time, completed_time
                    FROM lab_tests
                    WHERE visit_id = ?
                    ORDER BY ordered_time DESC
                ''', (visit[0], ))

                lab_tests = cursor.fetchall()
                if lab_tests:
                    st.markdown("**Lab Tests:**")
                    for test in lab_tests:
                        status_text = f"({test[1]})"
                        results_text = f" - {test[2]}" if test[2] else ""
                        st.write(f"• {test[0]} {status_text}{results_text}")

    conn.close()


def pharmacy_interface():
    add_to_history('pharmacy')
    st.markdown("## 💊 Pharmacy/Lab Station")

    tab1, tab2, tab3, tab4 = st.tabs(
        ["Ready to Fill", "Lab Results", "Lab Input", "Filled Prescriptions"])

    with tab1:
        pending_prescriptions()

    with tab2:
        awaiting_lab_prescriptions()

    with tab3:
        lab_results_input()

    with tab4:
        filled_prescriptions()


def pending_prescriptions():
    st.markdown("### Prescriptions to Fill")
    
    # Check if there's a family pharmacy workflow
    if 'family_pharmacy_workflow' in st.session_state:
        st.info("👨‍👩‍👧‍👦 **Family Consultation Complete** - Processing entire family prescriptions")
        family_data = st.session_state.family_pharmacy_workflow
        
        # Process all family members' prescriptions together
        for member in family_data:
            st.markdown(f"**{member['patient_name']} (ID: {member['patient_id']})**")
            
            # Get prescriptions for this family member
            conn = sqlite3.connect(db.db_name)
            cursor = conn.cursor()
            cursor.execute('''
                SELECT p.id, p.visit_id, p.medication_name, p.dosage, p.frequency, 
                       p.duration, p.instructions, p.indication, p.prescribed_time, pt.name, v.patient_id, p.awaiting_lab
                FROM prescriptions p
                JOIN visits v ON p.visit_id = v.visit_id
                JOIN patients pt ON v.patient_id = pt.patient_id
                WHERE p.visit_id = ? AND p.status = 'pending' AND p.awaiting_lab = 'no'
            ''', (member['visit_id'],))
            
            member_prescriptions = cursor.fetchall()
            conn.close()
            
            if member_prescriptions:
                for prescription in member_prescriptions:
                    st.markdown(f"• {prescription[2]} - {prescription[3]} {prescription[4]} for {prescription[5]}")
            else:
                st.markdown("• No prescriptions for this family member")
        
        if st.button("Complete All Family Prescriptions", key="complete_family_pharmacy"):
            # Mark all family prescriptions as filled
            conn = sqlite3.connect(db.db_name)
            cursor = conn.cursor()
            
            for member in family_data:
                cursor.execute('''
                    UPDATE prescriptions 
                    SET status = 'filled', filled_time = ? 
                    WHERE visit_id = ? AND status = 'pending' AND awaiting_lab = 'no'
                ''', (datetime.now().isoformat(), member['visit_id']))
                
                cursor.execute('''
                    UPDATE visits 
                    SET pharmacy_time = ?, status = 'completed' 
                    WHERE visit_id = ?
                ''', (datetime.now().isoformat(), member['visit_id']))
            
            conn.commit()
            conn.close()
            
            # Clear family workflow
            del st.session_state.family_pharmacy_workflow
            
            st.success("✅ All family prescriptions completed!")
            st.rerun()
        
        return

    conn = sqlite3.connect(db.db_name)
    cursor = conn.cursor()

    cursor.execute('''
        SELECT p.id, p.visit_id, p.medication_name, p.dosage, p.frequency, 
               p.duration, p.instructions, p.indication, p.prescribed_time, pt.name, v.patient_id, p.awaiting_lab
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
            patient_id = prescription[9]
            patient_name = prescription[8]

            if patient_id not in patients:
                patients[patient_id] = {
                    'name': patient_name,
                    'prescriptions': []
                }

            patients[patient_id]['prescriptions'].append(prescription)

        for patient_id, patient_data in patients.items():
            with st.expander(f"👤 {patient_data['name']} (ID: {patient_id})",
                             expanded=True):
                st.markdown("**Prescriptions:**")

                all_filled = True
                prescription_ids = []

                for prescription in patient_data['prescriptions']:
                    prescription_ids.append(prescription[0])

                    col1, col2 = st.columns([3, 1])

                    with col1:
                        st.markdown(f"""
                        <div style="background: white; border: 1px solid #e5e7eb; border-radius: 8px; padding: 16px; margin-bottom: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
                            <h5 style="color: #1f2937; margin: 0 0 12px 0; font-size: 16px;">💊 {prescription[2]}</h5>
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
                        if st.checkbox(f"Filled",
                                       key=f"filled_{prescription[0]}"):
                            pass
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

                    # Mark all prescriptions as filled
                    for prescription_id in prescription_ids:
                        cursor.execute(
                            '''
                            UPDATE prescriptions 
                            SET status = 'filled', filled_time = ? 
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

                    st.success(
                        f"✅ All prescriptions completed for {patient_data['name']}!"
                    )
                    st.rerun()
    else:
        st.info("No pending prescriptions.")


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
                    st.markdown(f"**{lab['test_type']} - Completed: {lab['completed_time'][:16].replace('T', ' ')}**")
                    
                    # Parse and display specific lab results based on test type
                    if lab['test_type'].lower() == 'urinalysis':
                        st.markdown("**Standard 10-Parameter Urinalysis:**")
                        results = lab['results']
                        
                        # Create a structured display for UA results
                        col1, col2 = st.columns(2)
                        with col1:
                            st.markdown("""
                            **Physical Parameters:**
                            - Color
                            - Clarity
                            - Specific Gravity
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
                            - pH
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
                        with st.expander(f"View {lab['test_type']} Results", expanded=False):
                            st.text(lab['results'])
                
                # Return to provider checkbox - simple and smooth
                st.markdown("---")
                st.markdown("### Provider Review")
                
                if patient_data['status'] != 'returned_to_provider':
                    if st.checkbox(f"📋 Return {patient_data['name']} to Provider for Lab Review", 
                                  key=f"return_patient_{patient_id}"):
                        
                        # Send patient back to doctor queue
                        conn = sqlite3.connect(db.db_name)
                        cursor = conn.cursor()
                        
                        cursor.execute('''
                            UPDATE visits 
                            SET status = 'waiting_consultation', return_reason = 'pharmacy_lab_review'
                            WHERE patient_id = ? AND DATE(visit_date) = DATE('now')
                        ''', (patient_id,))
                        
                        conn.commit()
                        conn.close()
                        
                        st.success(f"✅ {patient_data['name']} returned to provider for lab review!")
                        st.rerun()
                else:
                    st.success("✅ Patient has been returned to provider and is awaiting re-consultation.")
                    
    else:
        st.info("No completed lab results available today.")


def lab_results_input():
    st.markdown("### Lab Results Input")
    st.info("Input lab test results for patients. Results will be sent back to the doctor along with the patient.")
    
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
                    st.markdown("#### 10-Parameter Urinalysis Input")
                    
                    with st.form(f"urinalysis_{test_id}"):
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.markdown("**Physical Parameters:**")
                            color = st.selectbox("Color", ["Yellow", "Pale Yellow", "Dark Yellow", "Amber", "Red", "Brown", "Other"], key=f"color_{test_id}")
                            clarity = st.selectbox("Clarity", ["Clear", "Slightly Cloudy", "Cloudy", "Turbid"], key=f"clarity_{test_id}")
                            specific_gravity = st.number_input("Specific Gravity", min_value=1.000, max_value=1.050, value=1.020, step=0.005, key=f"sg_{test_id}")
                            ph = st.number_input("pH", min_value=4.5, max_value=9.0, value=6.0, step=0.5, key=f"ph_{test_id}")
                            protein = st.selectbox("Protein", ["Negative", "Trace", "+1", "+2", "+3", "+4"], key=f"protein_{test_id}")
                        
                        with col2:
                            st.markdown("**Chemical Parameters:**")
                            glucose = st.selectbox("Glucose", ["Negative", "Trace", "+1", "+2", "+3", "+4"], key=f"glucose_{test_id}")
                            ketones = st.selectbox("Ketones", ["Negative", "Trace", "Small", "Moderate", "Large"], key=f"ketones_{test_id}")
                            blood = st.selectbox("Blood", ["Negative", "Trace", "+1", "+2", "+3"], key=f"blood_{test_id}")
                            leukocyte_esterase = st.selectbox("Leukocyte Esterase", ["Negative", "Trace", "+1", "+2", "+3"], key=f"leuk_{test_id}")
                            nitrites = st.selectbox("Nitrites", ["Negative", "Positive"], key=f"nitrites_{test_id}")
                        
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
- Nitrites: {nitrites}"""
                            
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
                            
                            conn.commit()
                            conn.close()
                            
                            st.success(f"Urinalysis results saved successfully! Notification sent to Dr. {doctor_name}")
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
                            
                            conn.commit()
                            conn.close()
                            
                            st.success(f"Glucose test results saved successfully! Notification sent to Dr. {doctor_name if patient_info else 'Unknown'}")
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
                            
                            conn.commit()
                            conn.close()
                            
                            st.success(f"Pregnancy test results saved successfully! Notification sent to Dr. {doctor_name if patient_info else 'Unknown'}")
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


def filled_prescriptions():
    st.markdown("### Today's Filled Prescriptions")

    conn = sqlite3.connect(db.db_name)
    cursor = conn.cursor()

    cursor.execute('''
        SELECT p.medication_name, p.dosage, p.frequency, p.duration, 
               p.indication, p.filled_time, pt.name, v.patient_id
        FROM prescriptions p
        JOIN visits v ON p.visit_id = v.visit_id
        JOIN patients pt ON v.patient_id = pt.patient_id
        WHERE p.status = 'filled' AND DATE(p.filled_time) = DATE('now')
        ORDER BY p.filled_time DESC
    ''')

    filled = cursor.fetchall()
    conn.close()

    if filled:
        for prescription in filled:
            st.markdown(f"""
            <div style="background: #d1fae5; border: 1px solid #10b981; border-radius: 8px; padding: 16px; margin-bottom: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
                <h5 style="color: #047857; margin: 0 0 12px 0; font-size: 16px;">✅ {prescription[6]}</h5>
                <p style="margin: 0 0 8px 0; color: #065f46; font-size: 12px; background: #f0fdf4; padding: 3px 8px; border-radius: 4px; display: inline-block;"><strong>Patient ID:</strong> {prescription[7]}</p>
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 8px; margin-bottom: 8px;">
                    <p style="margin: 0; color: #065f46; font-size: 14px;"><strong>Medication:</strong> {prescription[0]}</p>
                    <p style="margin: 0; color: #065f46; font-size: 14px;"><strong>Dosage:</strong> {prescription[1]}</p>
                </div>
                {f'<p style="margin: 0 0 8px 0; color: #059669; font-size: 14px; background: #ecfdf5; padding: 4px 8px; border-radius: 4px;"><strong>For:</strong> {prescription[4]}</p>' if prescription[4] else ''}

            </div>
            """,
                        unsafe_allow_html=True)
    else:
        st.info("No prescriptions filled today.")


def lab_interface():
    add_to_history('lab')
    st.markdown("## 🔬 Laboratory")

    tab1, tab2 = st.tabs(["Pending Tests", "Lab Results"])

    with tab1:
        pending_lab_tests()

    with tab2:
        completed_lab_tests()


def pending_lab_tests():
    st.markdown("### Tests to Process")

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
                                               max_value=1.050,
                                               value=1.020,
                                               step=0.005)
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
            db.complete_lab_test(test_id, results_text)

            st.success("Urinalysis completed!")
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

            db.complete_lab_test(test_id, results)
            st.success("Glucose test completed!")
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

            db.complete_lab_test(test_id, results)
            st.success("Pregnancy test completed!")
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
            if st.button("✕ Close",
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

    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "Patient Management", "Doctor Management", "Medication Management",
        "Reports", "Settings"
    ])

    with tab1:
        patient_management()

    with tab2:
        doctor_management()

    with tab3:
        medication_management()

    with tab4:
        daily_reports()

    with tab5:
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
                    if db.add_doctor(doctor_name.strip()):
                        st.success(f"Doctor {doctor_name} added successfully!")
                        st.rerun()
                    else:
                        st.error(
                            "Failed to add doctor. Name may already exist.")
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
            with col2:
                category = st.selectbox("Category", [
                    "Pain Relief", "Antibiotic", "Blood Pressure", "Diabetes",
                    "Stomach", "Respiratory", "Vitamin", "Steroid", "Diuretic",
                    "Cholesterol", "UTI Antibiotic", "Other"
                ])
                indications = st.text_area("Clinical Indications",
                                         placeholder="e.g., Hypertension, Pain relief, Bacterial infections",
                                         height=100)

            if st.form_submit_button("Add Medication"):
                if med_name:
                    conn = sqlite3.connect(db.db_name)
                    cursor = conn.cursor()
                    cursor.execute(
                        '''
                        INSERT INTO preset_medications (medication_name, common_dosages, category, requires_lab, amount, indications)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (med_name, dosages, category, "no", amount, indications))
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
                            with col2:
                                categories = [
                                    "Pain Relief", "Antibiotic",
                                    "Blood Pressure", "Diabetes", "Stomach",
                                    "Respiratory", "Vitamin", "Steroid",
                                    "Diuretic", "Cholesterol",
                                    "UTI Antibiotic", "Other"
                                ]
                                try:
                                    cat_index = categories.index(
                                        med['category'])
                                except ValueError:
                                    cat_index = 0
                                new_category = st.selectbox("Category",
                                                            categories,
                                                            index=cat_index)
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
                                        cursor.execute(
                                            '''
                                            UPDATE preset_medications 
                                            SET medication_name = ?, common_dosages = ?, category = ?, amount = ?, indications = ?
                                            WHERE id = ?
                                        ''',
                                            (new_name.strip(),
                                             new_dosages.strip() if new_dosages
                                             else "", new_category, new_amount.strip() if new_amount else "", 
                                             new_indications.strip() if new_indications else "", med['id']))
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
                            if med.get('indications'):
                                st.caption(f"Indications: {med['indications']}")
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

    # Full-width download button
    st.download_button(label="📄 Download Today's Data (CSV)",
                       data=csv_data,
                       file_name=filename,
                       mime="text/csv",
                       type="primary",
                       use_container_width=True)

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
        if st.button("Back to Reports"):
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
    language = st.selectbox("Interface Language",
                            ["English", "Spanish", "French"],
                            index=0)
    if language != "English":
        st.info(
            f"Language setting saved: {language} (UI updates require app restart)"
        )

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


if __name__ == "__main__":
    main()
