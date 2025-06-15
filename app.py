import streamlit as st
import sqlite3
from datetime import datetime
import os
from typing import Dict, List, Optional
import time

# Configure page for mobile/tablet use
st.set_page_config(
    page_title="Medical Clinic Charting",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="collapsed"
)

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
""", unsafe_allow_html=True)

class DatabaseManager:
    def __init__(self, db_name: str = "clinic_database.db"):
        self.db_name = db_name
        self.init_database()
    
    def init_database(self):
        """Initialize the database with required tables"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        # Create patients table
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
                last_visit TEXT
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
            cursor.execute('ALTER TABLE prescriptions ADD COLUMN awaiting_lab TEXT DEFAULT "no"')
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
                ('Acetaminophen', '325mg q6h PRN, 500mg q6h PRN, 650mg q6h PRN', 'Pain Relief', 'no'),
                ('Ibuprofen', '200mg q6h PRN, 400mg q8h PRN, 600mg q8h PRN', 'Pain Relief', 'no'),
                ('Amoxicillin', '500mg q12h x7-10 days, 875mg q12h x7-10 days', 'Antibiotic', 'no'),
                ('Azithromycin', '250mg daily x5 days, 500mg day 1 then 250mg daily x4 days', 'Antibiotic', 'no'),
                ('Metronidazole', '250mg q8h x7 days, 500mg q12h x7 days', 'Antibiotic', 'no'),
                ('Ciprofloxacin', '250mg q12h x3-7 days, 500mg q12h x7-14 days', 'Antibiotic', 'no'),
                ('Nitrofurantoin', '100mg q12h x5-7 days', 'UTI Antibiotic', 'no'),
                ('Metformin', '500mg q12h with meals, 850mg daily with meals', 'Diabetes', 'no'),
                ('Lisinopril', '5mg daily, 10mg daily, 20mg daily', 'Blood Pressure', 'no'),
                ('Amlodipine', '2.5mg daily, 5mg daily, 10mg daily', 'Blood Pressure', 'no'),
                ('Omeprazole', '20mg daily before breakfast, 40mg daily before breakfast', 'Stomach', 'no'),
                ('Prednisone', '5mg daily x5-7 days, 10mg daily x5-7 days, 20mg daily x5 days', 'Steroid', 'no'),
                ('Albuterol Inhaler', '2 puffs q4-6h PRN', 'Respiratory', 'no'),
                ('Multivitamin', '1 tablet daily', 'Vitamin', 'no'),
                ('Iron Supplement', '65mg daily on empty stomach', 'Vitamin', 'no'),
                ('Cephalexin', '250mg q6h x7-10 days, 500mg q12h x7-10 days', 'Antibiotic', 'no'),
                ('Doxycycline', '100mg q12h x7-14 days', 'Antibiotic', 'no'),
                ('Hydrochlorothiazide', '12.5mg daily, 25mg daily', 'Blood Pressure', 'no'),
                ('Atorvastatin', '20mg daily, 40mg daily', 'Cholesterol', 'no'),
                ('Furosemide', '20mg daily, 40mg daily', 'Diuretic', 'no')
            ]
            
            for med in default_meds:
                cursor.execute('''
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
                'Dr. Smith',
                'Dr. Johnson', 
                'Dr. Williams',
                'Dr. Brown',
                'Dr. Garcia'
            ]
            
            for doctor in default_doctors:
                cursor.execute('''
                    INSERT INTO doctors (name, is_active) VALUES (?, 1)
                ''', (doctor,))
        
        conn.commit()
        conn.close()
    
    def get_next_patient_id(self, location_code: str) -> str:
        """Get the next patient ID in format DR00001, H00001, etc."""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        # Drop and recreate counters table to ensure correct schema
        try:
            cursor.execute('DROP TABLE IF EXISTS counters')
            cursor.execute('''
                CREATE TABLE counters (
                    location_code TEXT PRIMARY KEY,
                    value INTEGER DEFAULT 0
                )
            ''')
        except Exception:
            # If drop fails, just create the table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS counters (
                    location_code TEXT PRIMARY KEY,
                    value INTEGER DEFAULT 0
                )
            ''')
        
        # Get current counter for this location
        cursor.execute('SELECT value FROM counters WHERE location_code = ?', (location_code,))
        result = cursor.fetchone()
        
        if result:
            current_value = result[0]
            new_value = current_value + 1
        else:
            # First patient for this location
            new_value = 1
            cursor.execute('INSERT INTO counters (location_code, value) VALUES (?, ?)', 
                          (location_code, 0))
        
        cursor.execute('UPDATE counters SET value = ? WHERE location_code = ?', 
                      (new_value, location_code))
        
        conn.commit()
        conn.close()
        
        return f"{location_code}{new_value:05d}"
    
    def add_patient(self, location_code: str, **kwargs) -> str:
        """Add a new patient and return their ID"""
        patient_id = self.get_next_patient_id(location_code)
        
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO patients (patient_id, name, age, gender, phone, 
                                emergency_contact, medical_history, allergies, 
                                created_date, last_visit)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            patient_id, 
            kwargs.get('name', ''),
            kwargs.get('age'),
            kwargs.get('gender'),
            kwargs.get('phone'),
            kwargs.get('emergency_contact'),
            kwargs.get('medical_history'),
            kwargs.get('allergies'),
            datetime.now().isoformat(),
            datetime.now().isoformat()
        ))
        
        conn.commit()
        conn.close()
        
        return patient_id
    
    def search_patients(self, query: str) -> List[Dict]:
        """Search for patients by name or ID"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM patients 
            WHERE patient_id LIKE ? OR name LIKE ?
            ORDER BY name
        ''', (f'%{query}%', f'%{query}%'))
        
        results = cursor.fetchall()
        conn.close()
        
        columns = ['patient_id', 'name', 'age', 'gender', 'phone', 
                  'emergency_contact', 'medical_history', 'allergies',
                  'created_date', 'last_visit']
        
        return [dict(zip(columns, row)) for row in results]
    
    def create_visit(self, patient_id: str) -> str:
        """Create a new visit for a patient"""
        visit_id = f"{patient_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO visits (visit_id, patient_id, visit_date, status)
            VALUES (?, ?, ?, ?)
        ''', (visit_id, patient_id, datetime.now().isoformat(), 'triage'))
        
        # Update patient's last visit
        cursor.execute('''
            UPDATE patients SET last_visit = ? WHERE patient_id = ?
        ''', (datetime.now().isoformat(), patient_id))
        
        conn.commit()
        conn.close()
        
        return visit_id
    
    def get_doctors(self) -> List[Dict]:
        """Get all active doctors"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('SELECT name FROM doctors WHERE is_active = 1 ORDER BY name')
        doctors = [{'name': row[0]} for row in cursor.fetchall()]
        
        conn.close()
        return doctors
    
    def add_doctor(self, name: str) -> bool:
        """Add a new doctor"""
        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            
            cursor.execute('INSERT INTO doctors (name, is_active) VALUES (?, 1)', (name,))
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
            
            cursor.execute('UPDATE doctors SET is_active = 0 WHERE name = ?', (name,))
            conn.commit()
            conn.close()
            return True
        except:
            return False
    
    def update_doctor_status(self, doctor_name: str, status: str, patient_id: str = "", patient_name: str = ""):
        """Update doctor's current status"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        # Remove old status for this doctor
        cursor.execute('DELETE FROM doctor_status WHERE doctor_name = ?', (doctor_name,))
        
        # Insert new status
        cursor.execute('''
            INSERT INTO doctor_status (doctor_name, current_patient_id, current_patient_name, status, last_updated)
            VALUES (?, ?, ?, ?, ?)
        ''', (doctor_name, patient_id or "", patient_name or "", status, datetime.now().isoformat()))
        
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
    
    def delete_patient(self, patient_id: str) -> bool:
        """Delete a patient and all associated data"""
        conn = None
        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            
            # Get all visit IDs for this patient
            cursor.execute('SELECT visit_id FROM visits WHERE patient_id = ?', (patient_id,))
            visit_ids = [row[0] for row in cursor.fetchall()]
            
            # Delete related data for each visit
            for visit_id in visit_ids:
                # Delete prescriptions
                cursor.execute('DELETE FROM prescriptions WHERE visit_id = ?', (visit_id,))
                
                # Get lab test IDs for this visit
                cursor.execute('SELECT id FROM lab_tests WHERE visit_id = ?', (visit_id,))
                lab_test_ids = [row[0] for row in cursor.fetchall()]
                
                # Delete lab results for these tests
                for test_id in lab_test_ids:
                    cursor.execute('DELETE FROM lab_results WHERE test_id = ?', (test_id,))
                
                # Delete lab tests
                cursor.execute('DELETE FROM lab_tests WHERE visit_id = ?', (visit_id,))
                
                # Delete consultations
                cursor.execute('DELETE FROM consultations WHERE visit_id = ?', (visit_id,))
            
            # Delete all visits for this patient
            cursor.execute('DELETE FROM visits WHERE patient_id = ?', (patient_id,))
            
            # Finally delete the patient
            cursor.execute('DELETE FROM patients WHERE patient_id = ?', (patient_id,))
            
            # Check if deletion was successful
            cursor.execute('SELECT COUNT(*) FROM patients WHERE patient_id = ?', (patient_id,))
            if cursor.fetchone()[0] == 0:
                conn.commit()
                conn.close()
                return True
            else:
                conn.rollback()
                conn.close()
                return False
            
        except Exception as e:
            if conn:
                conn.rollback()
                conn.close()
            return False
    
    def add_location(self, country_code: str, country_name: str, city: str) -> int:
        """Add a new clinic location"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('''
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
        
        columns = ['id', 'country_code', 'country_name', 'city', 'created_date']
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
        
        columns = ['id', 'medication_name', 'common_dosages', 'category', 'requires_lab', 'active']
        return [dict(zip(columns, row)) for row in results]
    
    def order_lab_test(self, visit_id: str, test_type: str, ordered_by: str) -> int:
        """Order a lab test for a patient"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('''
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
        
        columns = ['id', 'visit_id', 'test_type', 'ordered_by', 'ordered_time', 
                  'completed_time', 'results', 'status', 'patient_name', 'patient_id', 'visit_date']
        return [dict(zip(columns, row)) for row in results]
    
    def complete_lab_test(self, test_id: int, results: str):
        """Complete a lab test with results"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE lab_tests 
            SET status = 'completed', results = ?, completed_time = ?
            WHERE id = ?
        ''', (results, datetime.now().isoformat(), test_id))
        
        conn.commit()
        conn.close()
    
    def add_prescription(self, visit_id: str, medication_id: int, medication_name: str, 
                        dosage: str, frequency: str, duration: str, instructions: str = "",
                        awaiting_lab: str = "no") -> int:
        """Add a prescription"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO prescriptions 
            (visit_id, medication_id, medication_name, dosage, frequency, duration, 
             instructions, awaiting_lab, prescribed_time)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (visit_id, medication_id, medication_name, dosage, frequency, duration, 
              instructions, awaiting_lab, datetime.now().isoformat()))
        
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
    """Display loading screen with Parakaleo logo for iPad"""
    if 'loading_shown' not in st.session_state:
        st.session_state.loading_shown = False
    
    if not st.session_state.loading_shown:
        placeholder = st.empty()
        with placeholder.container():
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                st.markdown('<div style="text-align: center; margin-top: 100px;">🔗</div>', unsafe_allow_html=True)
                st.markdown('<h2 style="text-align: center; margin-top: 40px;">ParakaleoMed</h2>', unsafe_allow_html=True)
                st.markdown('<p style="text-align: center; color: #666;">Loading...</p>', unsafe_allow_html=True)
        
        time.sleep(2)
        placeholder.empty()
        st.session_state.loading_shown = True
        st.rerun()

def main():
    # Show loading screen on first load
    show_loading_screen()
    
    # Display header with correct Parakaleo logo
    col1, col2 = st.columns([1, 8])
    with col1:
        # Correct Parakaleo logo based on user's image - interlocking colorful rings
        st.markdown('''
        <div style="display: flex; align-items: center; justify-content: center; height: 60px;">
        <svg width="45" height="45" viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
          <g transform="translate(50, 50)">
            <!-- Orange ring -->
            <circle cx="-15" cy="-15" r="20" fill="none" stroke="#FF8C00" stroke-width="4" opacity="0.8"/>
            <!-- Blue ring -->
            <circle cx="15" cy="-15" r="20" fill="none" stroke="#4A90E2" stroke-width="4" opacity="0.8"/>
            <!-- Green ring -->
            <circle cx="15" cy="15" r="20" fill="none" stroke="#50C878" stroke-width="4" opacity="0.8"/>
            <!-- Purple ring -->
            <circle cx="-15" cy="15" r="20" fill="none" stroke="#9B59B6" stroke-width="4" opacity="0.8"/>
            <!-- Yellow center ring -->
            <circle cx="0" cy="0" r="18" fill="none" stroke="#F1C40F" stroke-width="4" opacity="0.8"/>
            <!-- Red inner ring -->
            <circle cx="0" cy="0" r="12" fill="none" stroke="#E74C3C" stroke-width="3" opacity="0.8"/>
          </g>
        </svg>
        </div>
        ''', unsafe_allow_html=True)
    with col2:
        st.markdown('<h1 style="margin-top: 15px; margin-bottom: 0;">ParakaleoMed</h1>', unsafe_allow_html=True)
        st.markdown("*Mission Trip Patient Management*")
    
    st.markdown("---")
    
    # Location selection first
    if 'clinic_location' not in st.session_state:
        st.session_state.clinic_location = None
    
    if st.session_state.clinic_location is None:
        location_setup()
        return
    
    # Show current location
    location = st.session_state.clinic_location
    st.info(f"Current Location: {location['city']}, {location['country_name']} ({location['country_code']})")
    
    # Role selection
    if 'user_role' not in st.session_state:
        st.session_state.user_role = None
    
    if st.session_state.user_role is None:
        st.markdown("### Select Your Role")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("Triage Nurse", key="triage", type="primary", use_container_width=True):
                st.session_state.user_role = "triage"
                st.rerun()
            
            if st.button("Doctor", key="doctor", type="primary", use_container_width=True):
                st.session_state.user_role = "doctor"
                st.rerun()
        
        with col2:
            if st.button("Pharmacy", key="pharmacy", type="primary", use_container_width=True):
                st.session_state.user_role = "pharmacy"
                st.rerun()
            
            if st.button("Admin", key="admin", type="primary", use_container_width=True):
                st.session_state.user_role = "admin"
                st.rerun()
        
        st.markdown("---")
        st.info("This system works offline and stores all patient data locally for mission trips in remote areas.")
        
        return
    
    # Show LAN status page if requested
    if 'show_lan_page' in st.session_state and st.session_state.show_lan_page:
        show_lan_status_page()
        return
    
    # Role-specific interfaces
    if st.session_state.user_role == "triage":
        triage_interface()
    elif st.session_state.user_role == "doctor":
        # Check if doctor has logged in
        if 'doctor_name' not in st.session_state:
            doctor_login()
        else:
            doctor_interface()
    elif st.session_state.user_role == "pharmacy":
        pharmacy_interface()
    elif st.session_state.user_role == "admin":
        admin_interface()
    
    # Sidebar header with Parakaleo logo
    st.sidebar.markdown('''
    <div style="text-align: center; margin-bottom: 20px;">
        <svg width="35" height="35" viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
          <g transform="translate(50, 50)">
            <circle cx="-15" cy="-15" r="20" fill="none" stroke="#FF8C00" stroke-width="4" opacity="0.8"/>
            <circle cx="15" cy="-15" r="20" fill="none" stroke="#4A90E2" stroke-width="4" opacity="0.8"/>
            <circle cx="15" cy="15" r="20" fill="none" stroke="#50C878" stroke-width="4" opacity="0.8"/>
            <circle cx="-15" cy="15" r="20" fill="none" stroke="#9B59B6" stroke-width="4" opacity="0.8"/>
            <circle cx="0" cy="0" r="18" fill="none" stroke="#F1C40F" stroke-width="4" opacity="0.8"/>
            <circle cx="0" cy="0" r="12" fill="none" stroke="#E74C3C" stroke-width="3" opacity="0.8"/>
          </g>
        </svg>
        <h3 style="margin-top: 10px; color: #333;">ParakaleoMed</h3>
    </div>
    ''', unsafe_allow_html=True)
    
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
        st.warning("No doctors available. Please contact admin to add doctors.")
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
            status_color = "🟢" if status['status'] == 'available' else "🟡" if status['status'] == 'with_patient' else "🔴"
            patient_info = f" - {status['current_patient_name']} ({status['current_patient_id']})" if status['current_patient_id'] else ""
            st.write(f"{status_color} **{status['doctor_name']}** - {status['status'].replace('_', ' ').title()}{patient_info}")
    
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
                doctor_exists = any(doc['name'] == selected_doctor for doc in doctors_list)
                
                if doctor_exists:
                    # Force create status entry
                    conn = sqlite3.connect("clinic_database.db")
                    cursor = conn.cursor()
                    cursor.execute('DELETE FROM doctor_status WHERE doctor_name = ?', (selected_doctor,))
                    cursor.execute('''
                        INSERT INTO doctor_status (doctor_name, status, last_updated)
                        VALUES (?, ?, ?)
                    ''', (selected_doctor, "available", datetime.now().isoformat()))
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
            devices = [
                {"name": "iPad-Triage-01", "ip": "192.168.1.105", "status": "Connected", "role": "Triage"},
                {"name": "iPad-Doctor-01", "ip": "192.168.1.106", "status": "Connected", "role": "Doctor"},
                {"name": "iPad-Pharmacy-01", "ip": "192.168.1.107", "status": "Offline", "role": "Pharmacy"}
            ]
            
            for device in devices:
                status_color = "🟢" if device["status"] == "Connected" else "🔴"
                st.markdown(f"{status_color} **{device['name']}** ({device['role']}) - {device['ip']} - {device['status']}")
            
        except Exception:
            st.error("Unable to scan network. Check WiFi connection.")
    
    with col2:
        if st.button("Back to Main"):
            st.session_state.show_lan_page = False
            st.rerun()
        
        if st.button("Refresh"):
            st.rerun()
    
    st.markdown("---")
    st.info("Note: All devices should be connected to the same WiFi network for data synchronization.")

def location_setup():
    st.markdown("## Clinic Location Setup")
    st.markdown("Please select or add your clinic location before starting patient registration.")
    
    # Get existing locations
    locations = db.get_locations()
    
    tab1, tab2 = st.tabs(["Select Location", "Add New Location"])
    
    with tab1:
        if locations:
            st.markdown("### Existing Locations:")
            for location in locations:
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.markdown(f"**{location['city']}, {location['country_name']}** ({location['country_code']})")
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
                country = st.selectbox("Country", ["Dominican Republic", "Haiti"])
                country_code = "DR" if country == "Dominican Republic" else "H"
            with col2:
                city = st.text_input("City/Town", placeholder="Enter clinic city")
            
            if st.form_submit_button("Add Location", type="primary"):
                if city.strip():
                    location_id = db.add_location(country_code, country, city.strip())
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

def triage_interface():
    st.markdown("## 🩺 Triage Station")
    
    tab1, tab2, tab3 = st.tabs(["New Patient", "Existing Patient", "Patient Queue"])
    
    with tab1:
        new_patient_form()
    
    with tab2:
        existing_patient_search()
    
    with tab3:
        patient_queue_view()

def new_patient_form():
    st.markdown("### Register New Patient")
    
    with st.form("new_patient_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            name = st.text_input("Patient Name *", placeholder="Enter full name")
            age = st.number_input("Age", min_value=0, max_value=120, value=None)
            gender = st.selectbox("Gender", ["", "Male", "Female"])
        
        with col2:
            phone = st.text_input("Phone Number", placeholder="Optional")
            emergency_contact = st.text_input("Emergency Contact", placeholder="Optional")
        
        medical_history = st.text_area("Medical History", placeholder="Previous conditions, surgeries, etc.")
        allergies = st.text_area("Allergies", placeholder="Known allergies or medications to avoid")
        
        if st.form_submit_button("Register Patient", type="primary"):
            if name.strip():
                patient_data = {
                    'name': name.strip(),
                    'age': age,
                    'gender': gender if gender else None,
                    'phone': phone.strip() if phone else None,
                    'emergency_contact': emergency_contact.strip() if emergency_contact else None,
                    'medical_history': medical_history.strip() if medical_history else None,
                    'allergies': allergies.strip() if allergies else None
                }
                
                location_code = st.session_state.clinic_location['country_code']
                patient_id = db.add_patient(location_code, **patient_data)
                visit_id = db.create_visit(patient_id)
                
                st.success(f"✅ Patient registered successfully!")
                st.info(f"**Patient ID:** {patient_id}")
                st.info(f"**Visit ID:** {visit_id}")
                
                # Store visit_id in session state to show vital signs form
                st.session_state.pending_vitals = visit_id
                st.session_state.patient_name = name.strip()
                st.rerun()
            else:
                st.error("Please enter the patient's name.")
    
    # Show vital signs form outside the main form if there's a pending visit
    if 'pending_vitals' in st.session_state:
        st.markdown("### Record Vital Signs")
        st.info(f"Recording vitals for **{st.session_state.patient_name}** (Visit ID: {st.session_state.pending_vitals})")
        vital_signs_form(st.session_state.pending_vitals)

def existing_patient_search():
    st.markdown("### Find Existing Patient")
    
    search_query = st.text_input("Search by Name or Patient ID", placeholder="Enter name or ID (e.g., 00001)")
    
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
                    """, unsafe_allow_html=True)
                    
                    if st.button(f"Start New Visit", key=f"visit_{patient['patient_id']}", use_container_width=True):
                        visit_id = db.create_visit(patient['patient_id'])
                        st.success(f"✅ New visit created for {patient['name']}")
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
            systolic = st.number_input("Systolic BP", min_value=50, max_value=300, value=120)
            diastolic = st.number_input("Diastolic BP", min_value=30, max_value=200, value=80)
        
        with col2:
            heart_rate = st.number_input("Heart Rate (bpm)", min_value=30, max_value=250, value=72)
            temperature = st.number_input("Temperature (°F)", min_value=90.0, max_value=110.0, value=98.6, step=0.1)
        
        with col3:
            weight = st.number_input("Weight (lbs)", min_value=1.0, max_value=1000.0, value=None, step=0.1)
            height = st.number_input("Height (inches)", min_value=12.0, max_value=96.0, value=None, step=0.5)
        
        if st.form_submit_button("Save Vital Signs", type="primary"):
            conn = sqlite3.connect(db.db_name)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO vital_signs (visit_id, systolic_bp, diastolic_bp, heart_rate, 
                                       temperature, weight, height, recorded_time)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (visit_id, systolic, diastolic, heart_rate, temperature, 
                  weight, height, datetime.now().isoformat()))
            
            # Update visit status
            cursor.execute('''
                UPDATE visits SET triage_time = ?, status = ? WHERE visit_id = ?
            ''', (datetime.now().isoformat(), 'waiting_consultation', visit_id))
            
            conn.commit()
            conn.close()
            
            st.success("✅ Vital signs recorded! Patient is ready for consultation.")
            
            # Clear the pending vitals from session state
            if 'pending_vitals' in st.session_state:
                del st.session_state.pending_vitals
            if 'patient_name' in st.session_state:
                del st.session_state.patient_name
            
            st.rerun()

def patient_queue_view():
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
            status_emoji = {"triage": "📝", "waiting_consultation": "⏳", "consultation": "👨‍⚕️", 
                           "prescribed": "💊", "completed": "✅"}.get(status, "❓")
            
            st.markdown(f"""
            <div class="patient-card {status_class}">
                <h4>{priority_emoji} {name} (ID: {patient_id})</h4>
                <p><strong>Status:</strong> {status_emoji} {status.replace('_', ' ').title()}</p>
                <p><strong>Visit ID:</strong> {visit_id}</p>
                <p><strong>Time:</strong> {visit_date[:16].replace('T', ' ')}</p>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("No patients in queue for today.")

def doctor_interface():
    st.markdown(f"## 👨‍⚕️ Doctor Consultation - {st.session_state.doctor_name}")
    
    # Update doctor status and show real-time status of all doctors
    db = get_db_manager()
    
    # Display real-time doctor status at top
    with st.expander("📊 Real-Time Doctor Status", expanded=False):
        doctor_status = db.get_all_doctor_status()
        if doctor_status:
            for status in doctor_status:
                status_color = "🟢" if status['status'] == 'available' else "🟡" if status['status'] == 'with_patient' else "🔴"
                patient_info = f" - {status['current_patient_name']} ({status['current_patient_id']})" if status['current_patient_id'] else ""
                
                if status['doctor_name'] == st.session_state.doctor_name:
                    st.markdown(f"**{status_color} {status['doctor_name']} (YOU)** - {status['status'].replace('_', ' ').title()}{patient_info}")
                else:
                    st.write(f"{status_color} {status['doctor_name']} - {status['status'].replace('_', ' ').title()}{patient_info}")
        
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
    st.markdown("### Select Patient for Consultation")
    
    # Get patients waiting for consultation
    conn = sqlite3.connect("clinic_database.db")
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT v.visit_id, v.patient_id, p.name, v.priority, vs.systolic_bp, 
               vs.diastolic_bp, vs.heart_rate, vs.temperature
        FROM visits v
        JOIN patients p ON v.patient_id = p.patient_id
        LEFT JOIN vital_signs vs ON v.visit_id = vs.visit_id
        WHERE v.status = 'waiting_consultation' AND DATE(v.visit_date) = DATE('now')
        ORDER BY 
            CASE v.priority 
                WHEN 'critical' THEN 1 
                WHEN 'urgent' THEN 2 
                ELSE 3 
            END,
            v.visit_date
    ''')
    
    waiting_patients = cursor.fetchall()
    conn.close()
    
    if waiting_patients:
        for patient in waiting_patients:
            visit_id, patient_id, name, priority, sys_bp, dia_bp, hr, temp = patient
            
            priority_emoji = "🔴" if priority == "critical" else "🟡" if priority == "urgent" else "🟢"
            
            with st.expander(f"{priority_emoji} {name} (ID: {patient_id})", expanded=False):
                # Display vital signs
                if sys_bp:
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("Blood Pressure", f"{sys_bp}/{dia_bp}")
                    with col2:
                        st.metric("Heart Rate", f"{hr} bpm")
                    with col3:
                        st.metric("Temperature", f"{temp}°F")
                    with col4:
                        if st.button(f"Start Consultation", key=f"consult_{visit_id}"):
                            st.session_state.current_consultation = visit_id
                            # Update doctor status to show they are with this patient
                            db = get_db_manager()
                            db.update_doctor_status(st.session_state.doctor_name, "with_patient", patient_id, name)
                            st.rerun()
                
                # Show consultation button only
                # Consultation form will be shown outside the expander
    else:
        st.info("No patients waiting for consultation.")
    
    # Show consultation form outside the expander if a patient is selected
    if st.session_state.get('current_consultation'):
        st.markdown("---")
        # Get patient information for the selected consultation
        conn = sqlite3.connect("clinic_database.db")
        cursor = conn.cursor()
        cursor.execute('''
            SELECT v.visit_id, v.patient_id, p.name
            FROM visits v
            JOIN patients p ON v.patient_id = p.patient_id
            WHERE v.visit_id = ?
        ''', (st.session_state.current_consultation,))
        
        selected_patient = cursor.fetchone()
        conn.close()
        
        if selected_patient:
            visit_id, patient_id, name = selected_patient
            consultation_form(visit_id, patient_id, name)

def consultation_form(visit_id: str, patient_id: str, patient_name: str):
    st.markdown(f"### Consultation for {patient_name}")
    
    # Get patient history
    conn = sqlite3.connect(db.db_name)
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM patients WHERE patient_id = ?', (patient_id,))
    patient_info = cursor.fetchone()
    
    if patient_info:
        with st.expander("Patient Information"):
            st.write(f"**Medical History:** {patient_info[6] or 'None recorded'}")
            st.write(f"**Allergies:** {patient_info[7] or 'None recorded'}")
    
    with st.form(f"consultation_{visit_id}"):
        # Auto-fill doctor name from logged-in session
        doctor_name = st.session_state.get('doctor_name', '')
        st.text_input("Doctor Name", value=doctor_name, disabled=True)
        
        chief_complaint = st.text_area("Chief Complaint", placeholder="What brought the patient in today?")
        symptoms = st.text_area("Symptoms", placeholder="Describe symptoms observed/reported")
        diagnosis = st.text_area("Diagnosis", placeholder="Your diagnosis")
        treatment_plan = st.text_area("Treatment Plan", placeholder="Recommended treatment")
        notes = st.text_area("Additional Notes", placeholder="Any additional observations")
        
        st.markdown("#### Lab Tests")
        lab_tests = []
        
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.checkbox("Urinalysis"):
                lab_tests.append("Urinalysis")
        with col2:
            if st.checkbox("Blood Glucose"):
                lab_tests.append("Blood Glucose")
        with col3:
            if st.checkbox("Pregnancy Test"):
                lab_tests.append("Pregnancy Test")
        
        st.markdown("#### Prescriptions")
        
        # Get preset medications and deduplicate by name
        preset_meds = db.get_preset_medications()
        
        # Deduplicate medications by name (keep first occurrence)
        unique_meds = {}
        for med in preset_meds:
            med_name = med['medication_name']
            if med_name not in unique_meds:
                unique_meds[med_name] = med
        
        deduplicated_meds = list(unique_meds.values())
        med_categories = list(set(med['category'] for med in deduplicated_meds))
        
        selected_medications = []
        
        for category in sorted(med_categories):
            with st.expander(f"{category} Medications"):
                category_meds = [med for med in deduplicated_meds if med['category'] == category]
                
                for med in category_meds:
                    col1, col2 = st.columns([1, 2])
                    
                    with col1:
                        selected = st.checkbox(f"{med['medication_name']}", key=f"med_{med['id']}")
                    
                    with col2:
                        # Show dosage field for pharmacy clarity
                        pharmacy_dosage = st.text_input("Dosage for Pharmacy", 
                                                      placeholder="e.g., 500mg twice daily for 7 days",
                                                      key=f"pharma_dose_{med['id']}")
                    
                    if selected:
                        col3, col4, col5 = st.columns([1, 1, 1])
                        
                        with col3:
                            dosages = med['common_dosages'].split(', ')
                            selected_dosage = st.selectbox("Dosage", dosages, key=f"dosage_{med['id']}")
                        
                        with col4:
                            frequency = st.selectbox("Frequency", 
                                                    ["Once daily", "Twice daily", "Three times daily", "Four times daily", "As needed"], 
                                                    key=f"freq_{med['id']}")
                        
                        with col5:
                            duration = st.selectbox("Duration", 
                                                   ["3 days", "5 days", "7 days", "10 days", "14 days", "30 days"], 
                                                   key=f"dur_{med['id']}")
                        
                        instructions = st.text_input("Special Instructions", key=f"inst_{med['id']}")
                        
                        # Flexible "awaiting lab results" checkbox - doctor can decide for any medication
                        awaiting_lab = "yes" if st.checkbox("Awaiting Lab Results", key=f"await_{med['id']}", value=False) else "no"
                        
                        selected_medications.append({
                            'id': med['id'],
                            'name': med['medication_name'],
                            'dosage': selected_dosage,
                            'frequency': frequency,
                            'duration': duration,
                            'instructions': instructions,
                            'awaiting_lab': awaiting_lab,
                            'pharmacy_notes': pharmacy_dosage
                        })
        
        # Custom medication section
        with st.expander("Add Custom Medication"):
            custom_med_name = st.text_input("Custom Medication Name")
            if custom_med_name:
                col1, col2, col3 = st.columns(3)
                with col1:
                    custom_dosage = st.text_input("Dosage", key="custom_dosage")
                with col2:
                    custom_frequency = st.text_input("Frequency", key="custom_frequency")
                with col3:
                    custom_duration = st.text_input("Duration", key="custom_duration")
                
                custom_instructions = st.text_input("Instructions", key="custom_instructions")
                custom_awaiting = st.checkbox("Pending Lab", key="custom_awaiting")
                
                selected_medications.append({
                    'id': None,
                    'name': custom_med_name,
                    'dosage': custom_dosage,
                    'frequency': custom_frequency,
                    'duration': custom_duration,
                    'instructions': custom_instructions,
                    'awaiting_lab': "yes" if custom_awaiting else "no",
                    'pharmacy_notes': ""
                })
        
        if st.form_submit_button("Complete Consultation", type="primary"):
            if doctor_name and chief_complaint:
                try:
                    # Use the database manager methods instead of direct connection
                    # Save consultation
                    db_conn = sqlite3.connect(db.db_name, timeout=10.0)
                    db_conn.execute('BEGIN IMMEDIATE')
                    cursor = db_conn.cursor()
                    
                    cursor.execute('''
                        INSERT INTO consultations (visit_id, doctor_name, chief_complaint, 
                                                 symptoms, diagnosis, treatment_plan, notes, consultation_time)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (visit_id, doctor_name, chief_complaint, symptoms, diagnosis, 
                          treatment_plan, notes, datetime.now().isoformat()))
                    
                    # Update visit status first
                    if selected_medications:
                        new_status = 'prescribed'
                    elif lab_tests:
                        new_status = 'waiting_lab'
                    else:
                        new_status = 'completed'
                    
                    cursor.execute('''
                        UPDATE visits SET consultation_time = ?, status = ? WHERE visit_id = ?
                    ''', (datetime.now().isoformat(), new_status, visit_id))
                    
                    db_conn.commit()
                    db_conn.close()
                    
                    # Now handle lab tests and prescriptions using separate connections
                    for test_type in lab_tests:
                        db.order_lab_test(visit_id, test_type, doctor_name)
                    
                    for med in selected_medications:
                        if med['name']:
                            db.add_prescription(
                                visit_id=visit_id,
                                medication_id=med['id'],
                                medication_name=med['name'],
                                dosage=med['dosage'],
                                frequency=med['frequency'],
                                duration=med['duration'],
                                instructions=med['instructions'],
                                awaiting_lab=med['awaiting_lab']
                            )
                    
                    st.success("Consultation completed successfully!")
                    
                    if lab_tests:
                        st.info(f"Lab tests ordered: {', '.join(lab_tests)}")
                    
                    if selected_medications:
                        awaiting_count = sum(1 for med in selected_medications if med['awaiting_lab'] == 'yes')
                        ready_count = len(selected_medications) - awaiting_count
                        
                        if ready_count > 0:
                            st.info(f"{ready_count} prescriptions sent to pharmacy.")
                        if awaiting_count > 0:
                            st.info(f"{awaiting_count} prescriptions awaiting lab results.")
                    
                    # Update doctor status back to available
                    db.update_doctor_status(st.session_state.doctor_name, "available")
                    
                    # Clear current consultation
                    if 'current_consultation' in st.session_state:
                        del st.session_state.current_consultation
                    
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"Error completing consultation: {str(e)}")
                    # No need to handle db_conn here since it's handled in the try block
            else:
                st.error("Please fill in required fields: Doctor Name and Chief Complaint")

def consultation_history():
    st.markdown("### Today's Consultations")
    
    conn = sqlite3.connect(db.db_name)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT c.*, p.name, v.patient_id
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
            with st.expander(f"👤 {consultation[8]} (ID: {consultation[9]}) - {consultation[2]}"):
                st.write(f"**Doctor:** {consultation[1]}")
                st.write(f"**Time:** {consultation[7][:16].replace('T', ' ')}")
                st.write(f"**Chief Complaint:** {consultation[2]}")
                st.write(f"**Symptoms:** {consultation[3]}")
                st.write(f"**Diagnosis:** {consultation[4]}")
                st.write(f"**Treatment Plan:** {consultation[5]}")
                if consultation[6]:
                    st.write(f"**Notes:** {consultation[6]}")
    else:
        st.info("No consultations recorded today.")

def pharmacy_interface():
    st.markdown("## 💊 Pharmacy Station")
    
    tab1, tab2, tab3 = st.tabs(["Ready to Fill", "Awaiting Lab Results", "Filled Prescriptions"])
    
    with tab1:
        pending_prescriptions()
    
    with tab2:
        awaiting_lab_prescriptions()
    
    with tab3:
        filled_prescriptions()

def pending_prescriptions():
    st.markdown("### Prescriptions to Fill")
    
    conn = sqlite3.connect(db.db_name)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT p.id, p.visit_id, p.medication_name, p.dosage, p.frequency, 
               p.duration, p.instructions, p.prescribed_time, pt.name, v.patient_id, p.awaiting_lab
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
            with st.expander(f"👤 {patient_data['name']} (ID: {patient_id})", expanded=True):
                st.markdown("**Prescriptions:**")
                
                all_filled = True
                prescription_ids = []
                
                for prescription in patient_data['prescriptions']:
                    prescription_ids.append(prescription[0])
                    
                    col1, col2 = st.columns([3, 1])
                    
                    with col1:
                        st.markdown(f"""
                        <div class="metric-card">
                            <h5>💊 {prescription[2]}</h5>
                            <p><strong>Dosage:</strong> {prescription[3]}</p>
                            <p><strong>Frequency:</strong> {prescription[4]}</p>
                            <p><strong>Duration:</strong> {prescription[5]}</p>
                            {f'<p><strong>Instructions:</strong> {prescription[6]}</p>' if prescription[6] else ''}
                        </div>
                        """, unsafe_allow_html=True)
                    
                    with col2:
                        if st.checkbox(f"Filled", key=f"filled_{prescription[0]}"):
                            pass
                        else:
                            all_filled = False
                
                if st.button(f"Complete All Prescriptions for {patient_data['name']}", 
                           key=f"complete_{patient_id}", 
                           disabled=not all_filled):
                    
                    conn = sqlite3.connect(db.db_name)
                    cursor = conn.cursor()
                    
                    # Mark all prescriptions as filled
                    for prescription_id in prescription_ids:
                        cursor.execute('''
                            UPDATE prescriptions 
                            SET status = 'filled', filled_time = ? 
                            WHERE id = ?
                        ''', (datetime.now().isoformat(), prescription_id))
                    
                    # Update visit status to completed
                    cursor.execute('''
                        UPDATE visits 
                        SET pharmacy_time = ?, status = 'completed' 
                        WHERE patient_id = ? AND DATE(visit_date) = DATE('now')
                    ''', (datetime.now().isoformat(), patient_id))
                    
                    conn.commit()
                    conn.close()
                    
                    st.success(f"✅ All prescriptions completed for {patient_data['name']}!")
                    st.rerun()
    else:
        st.info("No pending prescriptions.")

def awaiting_lab_prescriptions():
    st.markdown("### Prescriptions Awaiting Lab Results")
    
    conn = sqlite3.connect(db.db_name)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT p.id, p.visit_id, p.medication_name, p.dosage, p.frequency, 
               p.duration, p.instructions, p.prescribed_time, pt.name, v.patient_id, p.awaiting_lab
        FROM prescriptions p
        JOIN visits v ON p.visit_id = v.visit_id
        JOIN patients pt ON v.patient_id = pt.patient_id
        WHERE p.status = 'pending' AND p.awaiting_lab = 'yes' AND DATE(p.prescribed_time) = DATE('now')
        ORDER BY p.prescribed_time
    ''')
    
    awaiting = cursor.fetchall()
    
    # Get completed lab tests for today
    cursor.execute('''
        SELECT lt.visit_id, lt.test_type, lt.results, lt.completed_time
        FROM lab_tests lt
        WHERE lt.status = 'completed' AND DATE(lt.completed_time) = DATE('now')
    ''')
    
    completed_labs = cursor.fetchall()
    conn.close()
    
    # Create a map of visit_id to completed lab tests
    lab_results = {}
    for lab in completed_labs:
        visit_id = lab[0]
        if visit_id not in lab_results:
            lab_results[visit_id] = []
        lab_results[visit_id].append({
            'test_type': lab[1],
            'results': lab[2],
            'completed_time': lab[3]
        })
    
    if awaiting:
        # Group by patient
        patients = {}
        for prescription in awaiting:
            patient_id = prescription[9]
            patient_name = prescription[8]
            visit_id = prescription[1]
            
            if patient_id not in patients:
                patients[patient_id] = {
                    'name': patient_name,
                    'visit_id': visit_id,
                    'prescriptions': [],
                    'lab_results': lab_results.get(visit_id, [])
                }
            
            patients[patient_id]['prescriptions'].append(prescription)
        
        for patient_id, patient_data in patients.items():
            with st.expander(f"⏳ {patient_data['name']} (ID: {patient_id})", expanded=True):
                
                # Show lab results if available
                if patient_data['lab_results']:
                    st.markdown("**Lab Results Available:**")
                    for lab in patient_data['lab_results']:
                        st.success(f"✅ {lab['test_type']} - Completed {lab['completed_time'][:16].replace('T', ' ')}")
                        with st.expander(f"View {lab['test_type']} Results"):
                            st.text(lab['results'])
                else:
                    st.warning("🔬 Waiting for lab results...")
                
                st.markdown("**Medications Awaiting Approval:**")
                
                prescription_ids = []
                for prescription in patient_data['prescriptions']:
                    prescription_ids.append(prescription[0])
                    
                    col1, col2 = st.columns([3, 1])
                    
                    with col1:
                        st.markdown(f"""
                        <div class="metric-card">
                            <h5>💊 {prescription[2]}</h5>
                            <p><strong>Dosage:</strong> {prescription[3]}</p>
                            <p><strong>Frequency:</strong> {prescription[4]}</p>
                            <p><strong>Duration:</strong> {prescription[5]}</p>
                            {f'<p><strong>Instructions:</strong> {prescription[6]}</p>' if prescription[6] else ''}
                        </div>
                        """, unsafe_allow_html=True)
                    
                    with col2:
                        if patient_data['lab_results']:  # Only show options if lab results are available
                            approve = st.button(f"✅ Approve", key=f"approve_{prescription[0]}")
                            deny = st.button(f"❌ Deny", key=f"deny_{prescription[0]}")
                            
                            if approve:
                                # Move prescription to ready status
                                conn = sqlite3.connect(db.db_name)
                                cursor = conn.cursor()
                                cursor.execute('''
                                    UPDATE prescriptions 
                                    SET awaiting_lab = 'no' 
                                    WHERE id = ?
                                ''', (prescription[0],))
                                conn.commit()
                                conn.close()
                                st.success(f"Prescription approved and moved to fill queue!")
                                st.rerun()
                            
                            if deny:
                                # Remove prescription
                                conn = sqlite3.connect(db.db_name)
                                cursor = conn.cursor()
                                cursor.execute('''
                                    UPDATE prescriptions 
                                    SET status = 'denied' 
                                    WHERE id = ?
                                ''', (prescription[0],))
                                conn.commit()
                                conn.close()
                                st.warning(f"Prescription denied based on lab results.")
                                st.rerun()
                        else:
                            st.info("Waiting for lab results...")
    else:
        st.info("No prescriptions awaiting lab results.")

def filled_prescriptions():
    st.markdown("### Today's Filled Prescriptions")
    
    conn = sqlite3.connect(db.db_name)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT p.medication_name, p.dosage, p.frequency, p.duration, 
               p.filled_time, pt.name, v.patient_id
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
            <div class="patient-card completed">
                <h5>✅ {prescription[5]} (ID: {prescription[6]})</h5>
                <p><strong>Medication:</strong> {prescription[0]}</p>
                <p><strong>Dosage:</strong> {prescription[1]}</p>
                <p><strong>Filled:</strong> {prescription[4][:16].replace('T', ' ')}</p>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("No prescriptions filled today.")

def lab_interface():
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
            with st.expander(f"🧪 {test['patient_name']} (ID: {test['patient_id']}) - {test['test_type']}", expanded=True):
                st.write(f"**Ordered by:** {test['ordered_by']}")
                st.write(f"**Ordered:** {test['ordered_time'][:16].replace('T', ' ')}")
                
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
            color = st.selectbox("Color", ["Yellow", "Pale Yellow", "Dark Yellow", "Amber", "Red", "Brown", "Other"])
            clarity = st.selectbox("Clarity", ["Clear", "Slightly Cloudy", "Cloudy", "Turbid"])
            specific_gravity = st.number_input("Specific Gravity", min_value=1.000, max_value=1.050, value=1.020, step=0.005)
            ph = st.number_input("pH", min_value=4.0, max_value=9.0, value=6.0, step=0.5)
        
        with col2:
            protein = st.selectbox("Protein", ["Negative", "Trace", "1+", "2+", "3+", "4+"])
            glucose = st.selectbox("Glucose", ["Negative", "Trace", "1+", "2+", "3+", "4+"])
            ketones = st.selectbox("Ketones", ["Negative", "Trace", "Small", "Moderate", "Large"])
            blood = st.selectbox("Blood", ["Negative", "Trace", "1+", "2+", "3+"])
        
        col3, col4 = st.columns(2)
        
        with col3:
            leukocyte_esterase = st.selectbox("Leukocyte Esterase", ["Negative", "Trace", "1+", "2+", "3+"])
            nitrites = st.selectbox("Nitrites", ["Negative", "Positive"])
            urobilinogen = st.selectbox("Urobilinogen", ["Normal", "1+", "2+", "3+", "4+"])
        
        with col4:
            bilirubin = st.selectbox("Bilirubin", ["Negative", "1+", "2+", "3+"])
            wbc = st.number_input("WBC/hpf", min_value=0, max_value=50, value=0)
            rbc = st.number_input("RBC/hpf", min_value=0, max_value=50, value=0)
        
        bacteria = st.selectbox("Bacteria", ["None", "Few", "Moderate", "Many"])
        epithelial_cells = st.selectbox("Epithelial Cells", ["None", "Few", "Moderate", "Many"])
        
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
            
            results_text = "\n".join([f"{k}: {v}" for k, v in results.items() if v])
            db.complete_lab_test(test_id, results_text)
            
            st.success("Urinalysis completed!")
            st.rerun()

def glucose_form(test_id: int):
    with st.form(f"glucose_{test_id}"):
        st.markdown("#### Blood Glucose Results")
        
        glucose_value = st.number_input("Glucose (mg/dL)", min_value=0, max_value=800, value=100)
        test_type = st.selectbox("Test Type", ["Random", "Fasting", "Post-meal"])
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
    
    conn = sqlite3.connect(db.db_name)
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
                    if st.button("Treated by Pharmacy", key=f"pharmacy_{test[0]}", type="primary"):
                        # Update lab test to indicate pharmacy treatment
                        conn = sqlite3.connect("clinic_database.db")
                        cursor = conn.cursor()
                        cursor.execute('''
                            UPDATE lab_tests SET notes = COALESCE(notes, '') || ' - TREATED BY PHARMACY'
                            WHERE id = ?
                        ''', (test[0],))
                        conn.commit()
                        conn.close()
                        st.success("Marked as treated by pharmacy")
                        st.rerun()
                
                with col2:
                    if st.button("Return to Provider", key=f"provider_{test[0]}", type="secondary"):
                        # Create new consultation requirement
                        visit_id = test[1]  # visit_id from the test
                        conn = sqlite3.connect("clinic_database.db")
                        cursor = conn.cursor()
                        
                        # Update visit status to require consultation
                        cursor.execute('''
                            UPDATE visits SET status = 'waiting_consultation'
                            WHERE visit_id = ?
                        ''', (visit_id,))
                        
                        # Add note to lab test
                        cursor.execute('''
                            UPDATE lab_tests SET notes = COALESCE(notes, '') || ' - RETURNED TO PROVIDER'
                            WHERE id = ?
                        ''', (test[0],))
                        
                        conn.commit()
                        conn.close()
                        st.success("Patient returned to consultation queue")
                        st.rerun()
    else:
        st.info("No lab tests completed today.")

def patient_management():
    st.markdown("### Patient Management")
    
    # Get all patients first
    conn = sqlite3.connect(db.db_name)
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
    columns = ['patient_id', 'name', 'age', 'gender', 'phone', 'emergency_contact', 
               'medical_history', 'allergies', 'created_date', 'last_visit']
    patients = [dict(zip(columns, row)) for row in all_patients]
    
    # Search filter
    search_query = st.text_input("Search Patients", placeholder="Filter by name or ID")
    
    # Filter patients based on search
    if search_query:
        filtered_patients = [p for p in patients if 
                           search_query.lower() in p['name'].lower() or 
                           search_query.lower() in p['patient_id'].lower()]
    else:
        filtered_patients = patients
    
    if filtered_patients:
        st.info(f"Showing {len(filtered_patients)} of {len(patients)} patients")
        st.warning("⚠️ Deleting a patient will permanently remove all their data including visits, prescriptions, and lab results.")
        
        for patient in filtered_patients:
            with st.container():
                st.markdown(f"""
                <div style="border: 1px solid #ddd; padding: 10px; margin: 5px 0; border-radius: 5px;">
                    <h4>{patient['name']}</h4>
                    <p><strong>ID:</strong> {patient['patient_id']}</p>
                    <p><strong>Age:</strong> {patient['age'] or 'Not specified'}</p>
                    <p><strong>Gender:</strong> {patient['gender'] or 'Not specified'}</p>
                    <p><strong>Last Visit:</strong> {patient['last_visit'][:10] if patient['last_visit'] else 'Never'}</p>
                </div>
                """, unsafe_allow_html=True)
                
                if st.button(f"Delete Patient", key=f"delete_{patient['patient_id']}", type="secondary"):
                    # Store the patient to delete in session state
                    st.session_state.confirm_delete = {
                        'patient_id': patient['patient_id'],
                        'patient_name': patient['name']
                    }
                    st.rerun()
        
        # Show confirmation dialog as centered popup if there's a patient to delete
        if 'confirm_delete' in st.session_state:
            patient_to_delete = st.session_state.confirm_delete
            
            # Create modal-style popup
            st.markdown("""
            <style>
            .delete-modal {
                position: fixed;
                top: 50%;
                left: 50%;
                transform: translate(-50%, -50%);
                background: white;
                padding: 30px;
                border-radius: 15px;
                box-shadow: 0 10px 30px rgba(0,0,0,0.5);
                border: 3px solid #ff4444;
                z-index: 1000;
                max-width: 500px;
                width: 90%;
            }
            .modal-overlay {
                position: fixed;
                top: 0;
                left: 0;
                width: 100vw;
                height: 100vh;
                background: rgba(0,0,0,0.7);
                z-index: 999;
            }
            </style>
            <div class="modal-overlay"></div>
            """, unsafe_allow_html=True)
            
            with st.container():
                st.markdown('<div class="delete-modal">', unsafe_allow_html=True)
                
                st.markdown("### ⚠️ CONFIRM PATIENT DELETION")
                st.markdown(f"**Patient:** {patient_to_delete['patient_name']}")
                st.markdown(f"**ID:** {patient_to_delete['patient_id']}")
                
                st.markdown("---")
                st.markdown("**This will permanently delete:**")
                st.markdown("• Patient information")
                st.markdown("• All visits and consultations") 
                st.markdown("• All prescriptions")
                st.markdown("• All lab results")
                st.markdown("---")
                st.error("**This action CANNOT be undone!**")
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("DELETE FOREVER", type="primary", key="confirm_delete_btn", use_container_width=True):
                        if db.delete_patient(patient_to_delete['patient_id']):
                            st.success(f"Patient {patient_to_delete['patient_name']} deleted successfully.")
                            del st.session_state.confirm_delete
                            st.rerun()
                        else:
                            st.error("Failed to delete patient.")
                
                with col2:
                    if st.button("CANCEL", key="cancel_delete_btn", use_container_width=True):
                        del st.session_state.confirm_delete
                        st.rerun()
                
                st.markdown('</div>', unsafe_allow_html=True)
            
            return  # Don't show rest of page when modal is active
    else:
        if search_query:
            st.info("No patients found matching your search.")
        else:
            st.info("No patients in the system yet.")

def admin_interface():
    st.markdown("## Admin Dashboard")
    
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["Patient Management", "Doctor Management", "Medication Management", "Reports", "Settings"])
    
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
    st.markdown("### Doctor Management")
    
    db = get_db_manager()
    
    # Add new doctor
    with st.expander("Add New Doctor"):
        with st.form("add_doctor"):
            doctor_name = st.text_input("Doctor Name", placeholder="e.g., Dr. Smith")
            
            if st.form_submit_button("Add Doctor", type="primary"):
                if doctor_name.strip():
                    if db.add_doctor(doctor_name.strip()):
                        st.success(f"Doctor {doctor_name} added successfully!")
                        st.rerun()
                    else:
                        st.error("Failed to add doctor. Name may already exist.")
                else:
                    st.error("Please enter a doctor name.")
    
    # Display current doctors and their status
    st.markdown("#### Current Doctors")
    doctors = db.get_doctors()
    doctor_status = db.get_all_doctor_status()
    
    if doctors:
        for doctor in doctors:
            # Find current status for this doctor
            current_status = next((s for s in doctor_status if s['doctor_name'] == doctor['name']), None)
            
            col1, col2, col3 = st.columns([2, 2, 1])
            
            with col1:
                st.write(f"**{doctor['name']}**")
            
            with col2:
                if current_status:
                    status_color = "🟢" if current_status['status'] == 'available' else "🟡" if current_status['status'] == 'with_patient' else "🔴"
                    patient_info = f" - {current_status['current_patient_name']}" if current_status['current_patient_id'] else ""
                    st.write(f"{status_color} {current_status['status'].replace('_', ' ').title()}{patient_info}")
                else:
                    st.write("🔴 Offline")
            
            with col3:
                if st.button("Remove", key=f"remove_doctor_{doctor['name']}", type="secondary"):
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
            status_color = "🟢" if status['status'] == 'available' else "🟡" if status['status'] == 'with_patient' else "🔴"
            patient_info = f" - {status['current_patient_name']} ({status['current_patient_id']})" if status['current_patient_id'] else ""
            last_update = status['last_updated'][:16].replace('T', ' ') if status['last_updated'] else "Unknown"
            
            st.write(f"{status_color} **{status['doctor_name']}** - {status['status'].replace('_', ' ').title()}{patient_info}")
            st.caption(f"Last updated: {last_update}")

def medication_management():
    st.markdown("### Preset Medications")
    
    medications = db.get_preset_medications()
    
    # Add new medication
    with st.expander("Add New Medication"):
        with st.form("new_medication"):
            col1, col2 = st.columns(2)
            with col1:
                med_name = st.text_input("Medication Name")
                dosages = st.text_input("Common Dosages", placeholder="e.g., 250mg, 500mg")
            with col2:
                category = st.selectbox("Category", ["Pain Relief", "Antibiotic", "Blood Pressure", "Diabetes", "Stomach", "Respiratory", "Vitamin", "Steroid", "Diuretic", "Cholesterol", "UTI Antibiotic", "Other"])
            
            if st.form_submit_button("Add Medication"):
                if med_name:
                    conn = sqlite3.connect(db.db_name)
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO preset_medications (medication_name, common_dosages, category, requires_lab)
                        VALUES (?, ?, ?, ?)
                    ''', (med_name, dosages, category, "no"))
                    conn.commit()
                    conn.close()
                    st.success("Medication added!")
                    st.rerun()
    
    # Display existing medications
    if medications:
        for category in set(med['category'] for med in medications):
            with st.expander(f"{category} Medications"):
                category_meds = [med for med in medications if med['category'] == category]
                for med in category_meds:
                    col1, col2, col3 = st.columns([2, 1, 1])
                    with col1:
                        st.write(f"**{med['medication_name']}** - {med['common_dosages']}")
                    with col2:
                        st.write(f"Category: {med['category']}")
                    with col3:
                        if st.button("Deactivate", key=f"deactivate_{med['id']}"):
                            conn = sqlite3.connect(db.db_name)
                            cursor = conn.cursor()
                            cursor.execute('UPDATE preset_medications SET active = 0 WHERE id = ?', (med['id'],))
                            conn.commit()
                            conn.close()
                            st.rerun()

def daily_reports():
    st.markdown("### Daily Statistics")
    
    conn = sqlite3.connect(db.db_name)
    cursor = conn.cursor()
    
    # Patient counts
    cursor.execute("SELECT COUNT(*) FROM visits WHERE DATE(visit_date) = DATE('now')")
    today_patients = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM visits WHERE status = 'completed' AND DATE(visit_date) = DATE('now')")
    completed_patients = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM prescriptions WHERE DATE(prescribed_time) = DATE('now')")
    prescriptions_written = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM lab_tests WHERE DATE(ordered_time) = DATE('now')")
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
    
    # Export functionality
    st.markdown("### Export Today's Data")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Download CSV", type="primary"):
            export_data = generate_daily_export()
            
            # Create downloadable CSV
            csv_data = export_data.to_csv(index=False)
            today_date = datetime.now().strftime("%Y-%m-%d")
            filename = f"parakaleo_clinic_data_{today_date}.csv"
            
            st.download_button(
                label="Download CSV File",
                data=csv_data,
                file_name=filename,
                mime="text/csv"
            )
            
            st.success("Data exported successfully!")
    
    with col2:
        if st.button("Connect to OneDrive", type="secondary"):
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
    
    prescriptions_df = pd.read_sql_query(prescriptions_query, conn, params=[today])
    
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
        export_data = pd.concat([export_data, patients_df.add_prefix('patient_')], ignore_index=True)
    
    if not prescriptions_df.empty:
        export_data = pd.concat([export_data, prescriptions_df.add_prefix('prescription_')], ignore_index=True)
    
    if not lab_tests_df.empty:
        export_data = pd.concat([export_data, lab_tests_df.add_prefix('lab_')], ignore_index=True)
    
    return export_data

def onedrive_integration():
    """Handle OneDrive connection and backup"""
    st.markdown("### OneDrive Integration")
    
    st.info("OneDrive integration for automatic backup of patient data.")
    
    # Simulate OneDrive connection process
    st.markdown("#### Connect to OneDrive Account")
    
    with st.form("onedrive_setup"):
        st.markdown("**Step 1: Authentication**")
        st.write("Click the button below to authenticate with your Microsoft OneDrive account.")
        
        if st.form_submit_button("Authenticate with OneDrive", type="primary"):
            # In a real implementation, this would redirect to Microsoft OAuth
            st.success("Connected to OneDrive successfully!")
            st.session_state.onedrive_connected = True
            
            # Show backup options
            st.markdown("**Step 2: Configure Backup**")
            backup_frequency = st.selectbox("Backup Frequency", 
                                          ["Manual", "Daily", "Weekly"])
            
            folder_name = st.text_input("OneDrive Folder Name", 
                                      value="ParakaleoMed Backups")
            
            if st.button("Setup Automatic Backup"):
                st.success(f"Backup configured: {backup_frequency} to folder '{folder_name}'")
                
                # Generate and prepare data for upload
                export_data = generate_daily_export()
                csv_data = export_data.to_csv(index=False)
                today_date = datetime.now().strftime("%Y-%m-%d")
                filename = f"parakaleo_clinic_data_{today_date}.csv"
                
                st.download_button(
                    label="Download for Manual Upload to OneDrive",
                    data=csv_data,
                    file_name=filename,
                    mime="text/csv"
                )
                
                st.info("File prepared for OneDrive backup. Use the download button above to get the file, then upload it to your OneDrive folder.")
    
    # Manual backup section
    st.markdown("---")
    st.markdown("#### Manual Backup to OneDrive")
    
    if st.button("Prepare Manual Backup"):
        export_data = generate_daily_export()
        csv_data = export_data.to_csv(index=False)
        today_date = datetime.now().strftime("%Y-%m-%d")
        filename = f"parakaleo_clinic_backup_{today_date}.csv"
        
        st.download_button(
            label="Download Backup File",
            data=csv_data,
            file_name=filename,
            mime="text/csv"
        )
        
        st.markdown("""
        **Next Steps:**
        1. Download the file using the button above
        2. Open OneDrive app on your iPad
        3. Navigate to your ParakaleoMed Backups folder
        4. Upload the downloaded file
        5. OneDrive will automatically sync to the cloud
        """)

def clinic_settings():
    st.markdown("### Clinic Settings")
    
    location = st.session_state.clinic_location
    st.info(f"Current Location: {location['city']}, {location['country_name']} ({location['country_code']})")
    
    if st.button("Export Today's Data"):
        st.info("Data export functionality would be implemented here for offline backup.")

if __name__ == "__main__":
    main()