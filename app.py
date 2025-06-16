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

# Custom CSS for BackpackEMR-inspired design
st.markdown("""
<style>
    .main { padding-top: 1rem; }
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.5rem 1rem;
        font-weight: 600;
        transition: all 0.3s ease;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
    }
    .back-button {
        position: fixed;
        top: 1rem;
        left: 1rem;
        z-index: 999;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.5rem 1rem;
        font-weight: 600;
        cursor: pointer;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
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

        # Create families table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS families (
                family_id TEXT PRIMARY KEY,
                family_name TEXT NOT NULL,
                head_of_household TEXT NOT NULL,
                address TEXT,
                created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Create patients table with family support
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS patients (
                patient_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                age INTEGER,
                gender TEXT,
                phone TEXT,
                address TEXT,
                emergency_contact TEXT,
                relationship TEXT,
                parent_id TEXT,
                family_id TEXT,
                is_independent BOOLEAN DEFAULT FALSE,
                separation_date TIMESTAMP,
                allergies TEXT,
                medical_history TEXT,
                created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_visit TIMESTAMP,
                FOREIGN KEY (family_id) REFERENCES families (family_id)
            )
        ''')

        # Create visits table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS visits (
                visit_id TEXT PRIMARY KEY,
                patient_id TEXT NOT NULL,
                visit_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                chief_complaint TEXT,
                priority TEXT DEFAULT 'normal',
                sys_bp INTEGER,
                dia_bp INTEGER,
                heart_rate INTEGER,
                temp REAL,
                weight REAL,
                height REAL,
                triage_time TIMESTAMP,
                consultation_time TIMESTAMP,
                pharmacy_time TIMESTAMP,
                status TEXT DEFAULT 'waiting_consultation',
                FOREIGN KEY (patient_id) REFERENCES patients (patient_id)
            )
        ''')

        # Create consultations table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS consultations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                visit_id TEXT NOT NULL,
                doctor_name TEXT NOT NULL,
                chief_complaint TEXT,
                symptoms TEXT,
                diagnosis TEXT,
                treatment_plan TEXT,
                notes TEXT,
                needs_ophthalmology BOOLEAN DEFAULT FALSE,
                consultation_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (visit_id) REFERENCES visits (visit_id)
            )
        ''')

        # Create prescriptions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS prescriptions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                visit_id TEXT NOT NULL,
                medication_name TEXT NOT NULL,
                dosage TEXT,
                frequency TEXT,
                duration TEXT,
                instructions TEXT,
                indication TEXT,
                awaiting_lab TEXT DEFAULT 'no',
                prescribed_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status TEXT DEFAULT 'pending',
                filled_time TIMESTAMP,
                FOREIGN KEY (visit_id) REFERENCES visits (visit_id)
            )
        ''')

        # Create lab_tests table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS lab_tests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                visit_id TEXT NOT NULL,
                test_type TEXT NOT NULL,
                ordered_by TEXT NOT NULL,
                ordered_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status TEXT DEFAULT 'pending',
                results TEXT,
                completed_time TIMESTAMP,
                FOREIGN KEY (visit_id) REFERENCES visits (visit_id)
            )
        ''')

        # Create locations table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS locations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                country_code TEXT NOT NULL,
                country_name TEXT NOT NULL,
                city TEXT NOT NULL,
                created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Create doctors table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS doctors (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                status TEXT DEFAULT 'available',
                current_patient_id TEXT,
                current_patient_name TEXT,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                active BOOLEAN DEFAULT TRUE
            )
        ''')

        # Create preset_medications table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS preset_medications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                medication_name TEXT NOT NULL,
                common_dosages TEXT,
                requires_lab TEXT DEFAULT 'no',
                category TEXT,
                active BOOLEAN DEFAULT TRUE
            )
        ''')

        conn.commit()
        conn.close()

    def get_next_patient_id(self, location_code: str) -> str:
        """Get the next patient ID in format DR00001, H00001, etc."""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT patient_id FROM patients 
            WHERE patient_id LIKE ? 
            ORDER BY patient_id DESC LIMIT 1
        ''', (f"{location_code}%",))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            last_id = result[0]
            number = int(last_id[len(location_code):]) + 1
        else:
            number = 1
        
        return f"{location_code}{number:05d}"

    def create_family(self, location_code: str, family_name: str, head_of_household: str, **kwargs) -> str:
        """Create a new family unit and return family ID"""
        family_id = self.get_next_patient_id(location_code)
        
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO families (family_id, family_name, head_of_household, address)
            VALUES (?, ?, ?, ?)
        ''', (family_id, family_name, head_of_household, kwargs.get('address', '')))
        
        conn.commit()
        conn.close()
        
        return family_id

    def add_family_member(self, family_id: str, location_code: str, relationship: str, parent_id: str = "", **kwargs) -> str:
        """Add a family member to an existing family"""
        patient_id = self.get_next_patient_id(location_code)
        
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO patients (patient_id, name, age, gender, phone, address, 
                                emergency_contact, relationship, parent_id, family_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (patient_id, kwargs.get('name', ''), kwargs.get('age'), 
              kwargs.get('gender', ''), kwargs.get('phone', ''), 
              kwargs.get('address', ''), kwargs.get('emergency_contact', ''),
              relationship, parent_id, family_id))
        
        conn.commit()
        conn.close()
        
        return patient_id

    def search_patients(self, query: str) -> List[Dict]:
        """Search for patients by name or ID"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT patient_id, name, age, gender, phone, created_date, last_visit
            FROM patients 
            WHERE name LIKE ? OR patient_id LIKE ?
            ORDER BY created_date DESC
        ''', (f'%{query}%', f'%{query}%'))
        
        results = cursor.fetchall()
        conn.close()
        
        return [{'patient_id': r[0], 'name': r[1], 'age': r[2], 'gender': r[3], 
                'phone': r[4], 'created_date': r[5], 'last_visit': r[6]} for r in results]

    def create_visit(self, patient_id: str) -> str:
        """Create a new visit for a patient"""
        visit_id = f"V{datetime.now().strftime('%Y%m%d%H%M%S')}{patient_id[-3:]}"
        
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO visits (visit_id, patient_id, visit_date, status)
            VALUES (?, ?, ?, ?)
        ''', (visit_id, patient_id, datetime.now().isoformat(), 'waiting_consultation'))
        
        # Update patient's last visit
        cursor.execute('''
            UPDATE patients SET last_visit = ? WHERE patient_id = ?
        ''', (datetime.now().isoformat(), patient_id))
        
        conn.commit()
        conn.close()
        
        return visit_id

    def get_preset_medications(self) -> List[Dict]:
        """Get all active preset medications"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, medication_name, common_dosages, requires_lab, category
            FROM preset_medications 
            WHERE active = TRUE
            ORDER BY category, medication_name
        ''')
        
        results = cursor.fetchall()
        conn.close()
        
        return [{'id': r[0], 'medication_name': r[1], 'common_dosages': r[2], 
                'requires_lab': r[3], 'category': r[4]} for r in results]

    def get_doctors(self) -> List[Dict]:
        """Get all active doctors"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT name, status, current_patient_id, current_patient_name
            FROM doctors 
            WHERE active = TRUE
            ORDER BY name
        ''')
        
        results = cursor.fetchall()
        conn.close()
        
        return [{'name': r[0], 'status': r[1], 'current_patient_id': r[2], 
                'current_patient_name': r[3]} for r in results]

    def update_doctor_status(self, doctor_name: str, status: str, patient_id: str = "", patient_name: str = ""):
        """Update doctor's current status"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE doctors 
            SET status = ?, current_patient_id = ?, current_patient_name = ?, last_updated = ?
            WHERE name = ?
        ''', (status, patient_id, patient_name, datetime.now().isoformat(), doctor_name))
        
        conn.commit()
        conn.close()

def get_db_manager():
    if 'db_manager' not in st.session_state:
        st.session_state.db_manager = DatabaseManager()
    return st.session_state.db_manager

def show_back_button():
    """Display universal back button"""
    if st.button("← Back", key="back_btn"):
        go_back()

def go_back():
    """Navigate back to previous page"""
    if 'navigation_history' in st.session_state and st.session_state.navigation_history:
        previous_page = st.session_state.navigation_history.pop()
        st.session_state.page = previous_page
        st.rerun()
    else:
        st.session_state.page = 'main'
        st.rerun()

def add_to_history(page_name):
    """Add current page to navigation history"""
    if 'navigation_history' not in st.session_state:
        st.session_state.navigation_history = []
    if 'page' in st.session_state and st.session_state.page != page_name:
        st.session_state.navigation_history.append(st.session_state.page)

def main():
    """Main application entry point"""
    
    # Initialize session state
    if 'page' not in st.session_state:
        st.session_state.page = 'main'
    
    # Show back button on all pages except main
    if st.session_state.page != 'main':
        show_back_button()
    
    # Main navigation
    if st.session_state.page == 'main':
        show_main_menu()
    elif st.session_state.page == 'doctor_login':
        doctor_login()
    elif st.session_state.page == 'triage':
        triage_interface()
    elif st.session_state.page == 'doctor_interface':
        doctor_interface()
    elif st.session_state.page == 'consultation_form':
        if 'active_consultation' in st.session_state:
            consultation_form(
                st.session_state.active_consultation['visit_id'],
                st.session_state.active_consultation['patient_id'],
                st.session_state.active_consultation['patient_name']
            )
    elif st.session_state.page == 'pharmacy':
        pharmacy_interface()
    elif st.session_state.page == 'lab':
        lab_interface()

def show_main_menu():
    """Display main menu with role selection"""
    st.title("🏥 Medical Clinic Charting System")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("👩‍⚕️ Doctor Login", use_container_width=True):
            add_to_history('main')
            st.session_state.page = 'doctor_login'
            st.rerun()
        
        if st.button("🏥 Triage Nurse", use_container_width=True):
            add_to_history('main')
            st.session_state.page = 'triage'
            st.rerun()
    
    with col2:
        if st.button("💊 Pharmacy", use_container_width=True):
            add_to_history('main')
            st.session_state.page = 'pharmacy'
            st.rerun()
        
        if st.button("🔬 Lab", use_container_width=True):
            add_to_history('main')
            st.session_state.page = 'lab'
            st.rerun()

def doctor_login():
    """Doctor login interface"""
    st.title("👩‍⚕️ Doctor Login")
    
    db_manager = get_db_manager()
    doctors = db_manager.get_doctors()
    
    if not doctors:
        st.info("No doctors registered. Contact administrator.")
        return
    
    doctor_names = [doc['name'] for doc in doctors]
    selected_doctor = st.selectbox("Select Doctor", doctor_names)
    
    if st.button("Login", type="primary"):
        st.session_state.doctor_name = selected_doctor
        add_to_history('doctor_login')
        st.session_state.page = 'doctor_interface'
        st.rerun()

def triage_interface():
    """Triage nurse interface"""
    st.title("🏥 Triage Interface")
    
    tab1, tab2 = st.tabs(["New Registration", "Existing Patient"])
    
    with tab1:
        new_patient_form()
    
    with tab2:
        existing_patient_search()

def new_patient_form():
    """New patient registration form"""
    st.markdown("### Register New Patient/Family")
    
    registration_type = st.radio("Registration Type", ["Individual", "Family"])
    
    if registration_type == "Family":
        family_registration()
    else:
        individual_registration()

def family_registration():
    """Family registration workflow"""
    st.markdown("#### Family Registration")
    
    with st.form("family_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            family_name = st.text_input("Family Name")
            parent_name = st.text_input("Parent/Guardian Name")
            parent_age = st.number_input("Parent Age", min_value=1, max_value=120, value=30)
            parent_gender = st.selectbox("Parent Gender", ["Male", "Female", "Other"])
        
        with col2:
            location = st.selectbox("Location", ["DR", "H"])
            address = st.text_area("Address")
            emergency_contact = st.text_input("Emergency Contact")
            chief_complaint = st.text_area("Chief Complaint")
        
        # Child information
        st.markdown("#### Children")
        num_children = st.number_input("Number of Children", min_value=0, max_value=10, value=0)
        
        children_data = []
        for i in range(num_children):
            st.markdown(f"**Child {i+1}**")
            child_col1, child_col2 = st.columns(2)
            
            with child_col1:
                child_name = st.text_input(f"Child {i+1} Name", key=f"child_name_{i}")
                child_age = st.number_input(f"Child {i+1} Age", min_value=0, max_value=17, value=5, key=f"child_age_{i}")
            
            with child_col2:
                child_gender = st.selectbox(f"Child {i+1} Gender", ["Male", "Female", "Other"], key=f"child_gender_{i}")
                child_complaint = st.text_input(f"Child {i+1} Chief Complaint", key=f"child_complaint_{i}")
            
            if child_name:
                children_data.append({
                    'name': child_name,
                    'age': child_age,
                    'gender': child_gender,
                    'chief_complaint': child_complaint
                })
        
        # Vital signs for parent
        st.markdown("#### Parent Vital Signs")
        vital_col1, vital_col2, vital_col3, vital_col4 = st.columns(4)
        
        with vital_col1:
            sys_bp = st.number_input("Systolic BP", min_value=50, max_value=250, value=120)
            dia_bp = st.number_input("Diastolic BP", min_value=30, max_value=150, value=80)
        
        with vital_col2:
            heart_rate = st.number_input("Heart Rate", min_value=40, max_value=200, value=72)
            temp = st.number_input("Temperature (°F)", min_value=95.0, max_value=110.0, value=98.6, step=0.1)
        
        with vital_col3:
            weight = st.number_input("Weight (lbs)", min_value=50.0, max_value=500.0, value=150.0, step=0.1)
            height = st.number_input("Height (in)", min_value=24.0, max_value=84.0, value=66.0, step=0.1)
        
        with vital_col4:
            priority = st.selectbox("Priority", ["normal", "urgent", "critical"])
        
        if st.form_submit_button("Register Family", type="primary"):
            if family_name and parent_name:
                db_manager = get_db_manager()
                
                # Create family
                family_id = db_manager.create_family(
                    location, family_name, parent_name, address=address
                )
                
                # Add parent as family member
                parent_id = db_manager.add_family_member(
                    family_id, location, "parent", "",
                    name=parent_name, age=parent_age, gender=parent_gender,
                    address=address, emergency_contact=emergency_contact
                )
                
                # Create visit for parent
                parent_visit_id = db_manager.create_visit(parent_id)
                
                # Add children
                children_visits = []
                for child in children_data:
                    child_id = db_manager.add_family_member(
                        family_id, location, "child", parent_id,
                        name=child['name'], age=child['age'], gender=child['gender'],
                        address=address, emergency_contact=emergency_contact
                    )
                    child_visit_id = db_manager.create_visit(child_id)
                    children_visits.append({
                        'patient_id': child_id,
                        'visit_id': child_visit_id,
                        'name': child['name'],
                        'age': child['age'],
                        'chief_complaint': child['chief_complaint']
                    })
                
                # Update parent visit with vital signs
                conn = sqlite3.connect(db_manager.db_name)
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE visits 
                    SET chief_complaint = ?, priority = ?, sys_bp = ?, dia_bp = ?, 
                        heart_rate = ?, temp = ?, weight = ?, height = ?, triage_time = ?
                    WHERE visit_id = ?
                ''', (chief_complaint, priority, sys_bp, dia_bp, heart_rate, temp, 
                      weight, height, datetime.now().isoformat(), parent_visit_id))
                conn.commit()
                conn.close()
                
                st.success(f"✅ Family registered successfully! Family ID: {family_id}")
                st.info(f"Parent: {parent_name} (ID: {parent_id})")
                for child in children_visits:
                    st.info(f"Child: {child['name']} (ID: {child['patient_id']})")

def individual_registration():
    """Individual patient registration"""
    st.markdown("#### Individual Registration")
    
    with st.form("individual_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            name = st.text_input("Patient Name")
            age = st.number_input("Age", min_value=1, max_value=120, value=30)
            gender = st.selectbox("Gender", ["Male", "Female", "Other"])
            location = st.selectbox("Location", ["DR", "H"])
        
        with col2:
            phone = st.text_input("Phone Number")
            address = st.text_area("Address")
            emergency_contact = st.text_input("Emergency Contact")
            chief_complaint = st.text_area("Chief Complaint")
        
        # Vital signs
        st.markdown("#### Vital Signs")
        vital_col1, vital_col2, vital_col3, vital_col4 = st.columns(4)
        
        with vital_col1:
            sys_bp = st.number_input("Systolic BP", min_value=50, max_value=250, value=120)
            dia_bp = st.number_input("Diastolic BP", min_value=30, max_value=150, value=80)
        
        with vital_col2:
            heart_rate = st.number_input("Heart Rate", min_value=40, max_value=200, value=72)
            temp = st.number_input("Temperature (°F)", min_value=95.0, max_value=110.0, value=98.6, step=0.1)
        
        with vital_col3:
            weight = st.number_input("Weight (lbs)", min_value=50.0, max_value=500.0, value=150.0, step=0.1)
            height = st.number_input("Height (in)", min_value=24.0, max_value=84.0, value=66.0, step=0.1)
        
        with vital_col4:
            priority = st.selectbox("Priority", ["normal", "urgent", "critical"])
        
        if st.form_submit_button("Register Patient", type="primary"):
            if name:
                db_manager = get_db_manager()
                patient_id = db_manager.get_next_patient_id(location)
                
                # Create patient
                conn = sqlite3.connect(db_manager.db_name)
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO patients (patient_id, name, age, gender, phone, address, emergency_contact)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (patient_id, name, age, gender, phone, address, emergency_contact))
                
                # Create visit
                visit_id = db_manager.create_visit(patient_id)
                
                # Update visit with vital signs
                cursor.execute('''
                    UPDATE visits 
                    SET chief_complaint = ?, priority = ?, sys_bp = ?, dia_bp = ?, 
                        heart_rate = ?, temp = ?, weight = ?, height = ?, triage_time = ?
                    WHERE visit_id = ?
                ''', (chief_complaint, priority, sys_bp, dia_bp, heart_rate, temp, 
                      weight, height, datetime.now().isoformat(), visit_id))
                
                conn.commit()
                conn.close()
                
                st.success(f"✅ Patient registered successfully! Patient ID: {patient_id}")

def existing_patient_search():
    """Search for existing patients"""
    st.markdown("### Search Existing Patients")
    
    search_query = st.text_input("Search by name or patient ID")
    
    if search_query:
        db_manager = get_db_manager()
        results = db_manager.search_patients(search_query)
        
        if results:
            for patient in results:
                with st.expander(f"{patient['name']} (ID: {patient['patient_id']})"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write(f"**Age:** {patient['age'] or 'N/A'}")
                        st.write(f"**Gender:** {patient['gender'] or 'N/A'}")
                        st.write(f"**Phone:** {patient['phone'] or 'N/A'}")
                    
                    with col2:
                        if st.button(f"Create New Visit", key=f"visit_{patient['patient_id']}"):
                            visit_id = db_manager.create_visit(patient['patient_id'])
                            st.success(f"New visit created! Visit ID: {visit_id}")

def doctor_interface():
    """Doctor interface showing waiting patients"""
    st.title(f"👩‍⚕️ Doctor Interface - Dr. {st.session_state.doctor_name}")
    
    # Get waiting patients
    db_manager = get_db_manager()
    conn = sqlite3.connect(db_manager.db_name)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT v.visit_id, v.patient_id, p.name, v.chief_complaint, v.priority, 
               v.sys_bp, v.dia_bp, v.heart_rate, v.temp, v.weight, v.height,
               p.family_id
        FROM visits v
        JOIN patients p ON v.patient_id = p.patient_id
        WHERE v.status = 'waiting_consultation'
        ORDER BY v.triage_time
    ''')
    
    waiting_patients = cursor.fetchall()
    conn.close()
    
    if not waiting_patients:
        st.info("No patients waiting for consultation.")
        return
    
    # Group by family if applicable
    family_groups = {}
    individual_patients = []
    
    for patient in waiting_patients:
        if patient[11]:  # family_id exists
            family_id = patient[11]
            if family_id not in family_groups:
                family_groups[family_id] = []
            family_groups[family_id].append({
                'visit_id': patient[0], 'patient_id': patient[1], 'name': patient[2],
                'chief_complaint': patient[3], 'priority': patient[4],
                'sys_bp': patient[5], 'dia_bp': patient[6], 'heart_rate': patient[7],
                'temp': patient[8], 'weight': patient[9], 'height': patient[10]
            })
        else:
            individual_patients.append({
                'visit_id': patient[0], 'patient_id': patient[1], 'name': patient[2],
                'chief_complaint': patient[3], 'priority': patient[4],
                'sys_bp': patient[5], 'dia_bp': patient[6], 'heart_rate': patient[7],
                'temp': patient[8], 'weight': patient[9], 'height': patient[10]
            })
    
    # Display family consultations
    if family_groups:
        st.markdown("#### 👨‍👩‍👧‍👦 Family Consultations")
        for family_id, members in family_groups.items():
            # Find parent/guardian
            parent = next((m for m in members if 'parent' in m.get('name', '').lower()), members[0])
            children = [m for m in members if m != parent]
            
            with st.expander(f"Family {family_id} - {len(members)} members"):
                st.markdown(f"**👤 Parent/Guardian: {parent['name']}**")
                
                if parent.get('sys_bp'):
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("Blood Pressure", f"{parent['sys_bp']}/{parent['dia_bp']}")
                    with col2:
                        st.metric("Heart Rate", f"{parent['heart_rate']} bpm")
                    with col3:
                        st.metric("Temperature", f"{parent['temp']}°F")
                    with col4:
                        if st.button(f"Start Family Consultation", key=f"family_consult_{family_id}"):
                            # Store family consultation data for entire family workflow
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
                            db_manager.update_doctor_status(
                                st.session_state.doctor_name, "with_patient",
                                parent['patient_id'], f"{parent['name']} (Family)")
                            st.session_state.page = 'consultation_form'
                            st.rerun()
                
                if children:
                    st.markdown("**👶 Children:**")
                    for child in children:
                        st.write(f"• {child['name']} ({child.get('age', 'N/A')} yrs)")
    
    # Display individual patients
    if individual_patients:
        st.markdown("#### 👤 Individual Patients")
        for patient in individual_patients:
            priority_emoji = "🔴" if patient['priority'] == "critical" else "🟡" if patient['priority'] == "urgent" else "🟢"
            
            with st.expander(f"{priority_emoji} {patient['name']} (ID: {patient['patient_id']})"):
                if patient['sys_bp']:
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("Blood Pressure", f"{patient['sys_bp']}/{patient['dia_bp']}")
                    with col2:
                        st.metric("Heart Rate", f"{patient['heart_rate']} bpm")
                    with col3:
                        st.metric("Temperature", f"{patient['temp']}°F")
                    with col4:
                        if st.button(f"Start Consultation", key=f"consult_{patient['patient_id']}"):
                            st.session_state.active_consultation = {
                                'visit_id': patient['visit_id'],
                                'patient_id': patient['patient_id'],
                                'patient_name': patient['name']
                            }
                            db_manager.update_doctor_status(
                                st.session_state.doctor_name, "with_patient",
                                patient['patient_id'], patient['name'])
                            st.session_state.page = 'consultation_form'
                            st.rerun()

def consultation_form(visit_id: str, patient_id: str, patient_name: str):
    """Consultation form with enhanced medication workflow"""
    st.title(f"📋 Consultation: {patient_name}")
    
    db_manager = get_db_manager()
    doctor_name = st.session_state.doctor_name
    
    # Check if this is a family consultation
    is_family_consultation = 'family_consultation' in st.session_state and any(
        member['patient_id'] == patient_id 
        for member in st.session_state.family_consultation.get('family_members', [])
    )
    
    if is_family_consultation:
        family_data = st.session_state.family_consultation
        current_index = family_data['current_member_index']
        total_members = family_data['total_members']
        st.info(f"👨‍👩‍👧‍👦 Family Consultation ({current_index + 1}/{total_members})")
    
    with st.form("consultation_form"):
        # Basic consultation fields
        col1, col2 = st.columns(2)
        
        with col1:
            chief_complaint = st.text_area("Chief Complaint", height=100)
            symptoms = st.text_area("Symptoms", height=100)
            diagnosis = st.text_area("Diagnosis", height=100)
        
        with col2:
            treatment_plan = st.text_area("Treatment Plan", height=100)
            notes = st.text_area("Notes", height=100)
            surgical_history = st.text_area("Surgical History", height=50)
            medical_history = st.text_area("Medical History", height=50)
            allergies = st.text_area("Allergies", height=50)
            current_medications = st.text_area("Current Medications", height=50)
        
        # Lab tests
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
        
        # Prescriptions with immediate field display
        st.markdown("#### Prescriptions")
        
        preset_meds = db_manager.get_preset_medications()
        
        # Deduplicate medications by name
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
                    selected = st.checkbox(f"{med['medication_name']}", key=f"med_{med['id']}_{visit_id}")
                    
                    if selected:
                        # Show detailed medication fields immediately after selection
                        col2a, col2b = st.columns(2)
                        with col2a:
                            pharmacy_dosage = st.text_input(
                                "Dosage for Pharmacy",
                                placeholder="e.g., 500mg twice daily for 7 days",
                                key=f"pharma_dose_{med['id']}_{visit_id}")
                        with col2b:
                            indication = st.text_input(
                                "Indication",
                                placeholder="e.g., UTI, hypertension",
                                key=f"indication_{med['id']}_{visit_id}")
                        
                        col3, col4, col5 = st.columns([1, 1, 1])
                        
                        with col3:
                            dosages = med['common_dosages'].split(', ')
                            selected_dosage = st.selectbox("Dosage", dosages, key=f"dosage_{med['id']}_{visit_id}")
                        
                        with col4:
                            frequency = st.selectbox("Frequency", [
                                "Once daily", "Twice daily", "Three times daily", 
                                "Four times daily", "As needed"
                            ], key=f"freq_{med['id']}_{visit_id}")
                        
                        with col5:
                            duration = st.selectbox("Duration", [
                                "3 days", "5 days", "7 days", "10 days", "14 days", "30 days"
                            ], key=f"dur_{med['id']}_{visit_id}")
                        
                        instructions = st.text_area(
                            "Special Instructions",
                            placeholder="Take with food, etc.",
                            key=f"instructions_{med['id']}_{visit_id}")
                        
                        # Lab dependency checkbox
                        awaiting_lab = st.checkbox(
                            "Requires lab results before dispensing",
                            value=(med['requires_lab'] == 'yes'),
                            key=f"awaiting_{med['id']}_{visit_id}")
                        
                        if med['requires_lab'] == 'yes' and awaiting_lab:
                            return_to_provider = st.checkbox(
                                "Return to provider if abnormal",
                                key=f"return_{med['id']}_{visit_id}")
                        
                        selected_medications.append({
                            'name': med['medication_name'],
                            'dosage': selected_dosage,
                            'frequency': frequency,
                            'duration': duration,
                            'instructions': instructions,
                            'awaiting_lab': "yes" if awaiting_lab else "no",
                            'indication': indication,
                            'pharmacy_notes': pharmacy_dosage
                        })
        
        # Custom medication
        st.markdown("#### Add Custom Medication")
        with st.expander("Custom Medication"):
            custom_med_name = st.text_input("Medication Name")
            if custom_med_name:
                custom_dosage = st.text_input("Dosage")
                custom_frequency = st.text_input("Frequency")
                custom_duration = st.text_input("Duration")
                custom_instructions = st.text_area("Instructions")
                custom_indication = st.text_input("Indication")
                custom_awaiting = st.checkbox("Requires lab results")
                
                selected_medications.append({
                    'name': custom_med_name,
                    'dosage': custom_dosage,
                    'frequency': custom_frequency,
                    'duration': custom_duration,
                    'instructions': custom_instructions,
                    'awaiting_lab': "yes" if custom_awaiting else "no",
                    'indication': custom_indication,
                    'pharmacy_notes': ""
                })
        
        # Ophthalmology referral
        st.markdown("#### Ophthalmology Referral")
        needs_ophthalmology = st.checkbox(
            "Patient needs to see ophthalmologist after receiving medications",
            key=f"ophth_{visit_id}")
        
        if st.form_submit_button("Complete Consultation", type="primary"):
            if doctor_name and chief_complaint:
                try:
                    # Save consultation
                    conn = sqlite3.connect(db_manager.db_name)
                    cursor = conn.cursor()
                    
                    cursor.execute('''
                        INSERT INTO consultations (visit_id, doctor_name, chief_complaint, 
                                                 symptoms, diagnosis, treatment_plan, notes, 
                                                 needs_ophthalmology, consultation_time)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (visit_id, doctor_name, chief_complaint, symptoms, diagnosis, 
                          treatment_plan, notes, needs_ophthalmology, datetime.now().isoformat()))
                    
                    # Update visit status
                    if needs_ophthalmology:
                        new_status = 'needs_ophthalmology'
                    elif selected_medications:
                        new_status = 'prescribed'
                    elif lab_tests:
                        new_status = 'waiting_lab'
                    else:
                        new_status = 'completed'
                    
                    cursor.execute('''
                        UPDATE visits SET consultation_time = ?, status = ? WHERE visit_id = ?
                    ''', (datetime.now().isoformat(), new_status, visit_id))
                    
                    conn.commit()
                    conn.close()
                    
                    # Order lab tests
                    for test_type in lab_tests:
                        conn = sqlite3.connect(db_manager.db_name)
                        cursor = conn.cursor()
                        cursor.execute('''
                            INSERT INTO lab_tests (visit_id, test_type, ordered_by, ordered_time)
                            VALUES (?, ?, ?, ?)
                        ''', (visit_id, test_type, doctor_name, datetime.now().isoformat()))
                        conn.commit()
                        conn.close()
                    
                    # Add prescriptions
                    for med in selected_medications:
                        if med['name']:
                            conn = sqlite3.connect(db_manager.db_name)
                            cursor = conn.cursor()
                            cursor.execute('''
                                INSERT INTO prescriptions (visit_id, medication_name, dosage, 
                                                         frequency, duration, instructions, 
                                                         indication, awaiting_lab, prescribed_time)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                            ''', (visit_id, med['name'], med['dosage'], med['frequency'], 
                                  med['duration'], med['instructions'], med['indication'], 
                                  med['awaiting_lab'], datetime.now().isoformat()))
                            conn.commit()
                            conn.close()
                    
                    # Update patient history
                    conn = sqlite3.connect(db_manager.db_name)
                    cursor = conn.cursor()
                    cursor.execute('''
                        UPDATE patients 
                        SET medical_history = ?, allergies = ?
                        WHERE patient_id = ?
                    ''', (f"Surgical: {surgical_history}\nMedical: {medical_history}",
                          f"Allergies: {allergies}\nCurrent Meds: {current_medications}",
                          patient_id))
                    conn.commit()
                    conn.close()
                    
                    # Handle family consultation workflow
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
                            
                            st.session_state.active_consultation = {
                                'visit_id': next_member['visit_id'],
                                'patient_id': next_member['patient_id'],
                                'patient_name': next_member['name']
                            }
                            
                            st.success(f"✅ Consultation completed for {patient_name}")
                            st.info(f"🔄 Continuing with {next_member['name']} ({next_index + 1}/{family_data['total_members']})")
                            time.sleep(1)
                            st.rerun()
                        else:
                            # All family members completed - go to pharmacy workflow
                            st.success(f"✅ All family consultations completed!")
                            st.info("🏥 Sending entire family to pharmacy...")
                            
                            # Set family pharmacy workflow
                            st.session_state.family_pharmacy_workflow = family_data['completed_consultations']
                            del st.session_state.family_consultation
                            del st.session_state.active_consultation
                            
                            # Update doctor status back to available
                            db_manager.update_doctor_status(st.session_state.doctor_name, "available")
                            
                            time.sleep(2)
                            st.session_state.page = 'doctor_interface'
                            st.rerun()
                    else:
                        # Individual consultation completed
                        st.success("✅ Consultation completed successfully!")
                        db_manager.update_doctor_status(st.session_state.doctor_name, "available")
                        st.session_state.page = 'doctor_interface'
                        st.rerun()
                        
                except Exception as e:
                    st.error(f"Error completing consultation: {str(e)}")
            else:
                st.error("Please fill in required fields: Doctor Name and Chief Complaint")

def pharmacy_interface():
    """Pharmacy interface with family workflow support"""
    st.title("💊 Pharmacy Interface")
    
    tab1, tab2, tab3 = st.tabs(["Ready to Fill", "Awaiting Lab Results", "Filled Prescriptions"])
    
    with tab1:
        pending_prescriptions()
    
    with tab2:
        awaiting_lab_prescriptions()
    
    with tab3:
        filled_prescriptions()

def pending_prescriptions():
    """Handle prescriptions ready to fill with family workflow support"""
    st.markdown("### Prescriptions to Fill")
    
    # Check if there's a family pharmacy workflow
    if 'family_pharmacy_workflow' in st.session_state:
        st.info("👨‍👩‍👧‍👦 **Family Consultation Complete** - Processing entire family prescriptions")
        family_data = st.session_state.family_pharmacy_workflow
        
        # Process all family members' prescriptions together
        for member in family_data:
            st.markdown(f"**{member['patient_name']} (ID: {member['patient_id']})**")
            
            # Get prescriptions for this family member
            conn = sqlite3.connect("clinic_database.db")
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
            conn = sqlite3.connect("clinic_database.db")
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
    
    # Regular individual prescription handling
    conn = sqlite3.connect("clinic_database.db")
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
            patient_id = prescription[10]
            patient_name = prescription[9]
            
            if patient_id not in patients:
                patients[patient_id] = {
                    'name': patient_name,
                    'prescriptions': []
                }
            
            patients[patient_id]['prescriptions'].append(prescription)
        
        for patient_id, patient_data in patients.items():
            with st.expander(f"💊 {patient_data['name']} (ID: {patient_id})", expanded=True):
                
                st.markdown("**Medications to Fill:**")
                
                prescription_ids = []
                for prescription in patient_data['prescriptions']:
                    prescription_ids.append(prescription[0])
                    
                    col1, col2 = st.columns([3, 1])
                    
                    with col1:
                        st.markdown(f"""
                        <div style="background: #e7f3ff; border: 1px solid #2196f3; border-radius: 8px; padding: 16px; margin-bottom: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
                            <h5 style="color: #1976d2; margin: 0 0 12px 0; font-size: 16px;">💊 {prescription[2]}</h5>
                            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 8px; margin-bottom: 8px;">
                                <p style="margin: 0; color: #424242; font-size: 14px;"><strong>Dosage:</strong> {prescription[3]}</p>
                                <p style="margin: 0; color: #424242; font-size: 14px;"><strong>Frequency:</strong> {prescription[4]}</p>
                            </div>
                            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 8px; margin-bottom: 8px;">
                                <p style="margin: 0; color: #424242; font-size: 14px;"><strong>Duration:</strong> {prescription[5]}</p>
                                <p style="margin: 0; color: #424242; font-size: 14px;"><strong>Indication:</strong> {prescription[7] or 'Not specified'}</p>
                            </div>
                            <p style="margin: 0; color: #616161; font-size: 13px; font-style: italic;"><strong>Instructions:</strong> {prescription[6] or 'Standard instructions'}</p>
                        </div>
                        """, unsafe_allow_html=True)
                
                if st.button(f"✅ Fill All Prescriptions for {patient_data['name']}", 
                           key=f"fill_{patient_id}", type="primary"):
                    # Mark all prescriptions as filled
                    conn = sqlite3.connect("clinic_database.db")
                    cursor = conn.cursor()
                    
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
    """Handle prescriptions awaiting lab results"""
    st.markdown("### Prescriptions Awaiting Lab Results")
    
    conn = sqlite3.connect("clinic_database.db")
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT p.id, p.visit_id, p.medication_name, p.dosage, p.frequency, 
               p.duration, p.instructions, p.indication, p.prescribed_time, pt.name, v.patient_id, p.awaiting_lab
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
            patient_id = prescription[10]
            patient_name = prescription[9]
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
                    
                    st.markdown(f"""
                    <div style="background: #fef3c7; border: 1px solid #f59e0b; border-radius: 8px; padding: 16px; margin-bottom: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
                        <h5 style="color: #92400e; margin: 0 0 12px 0; font-size: 16px;">⏳ {prescription[2]} (Awaiting Lab)</h5>
                        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 8px; margin-bottom: 8px;">
                            <p style="margin: 0; color: #78350f; font-size: 14px;"><strong>Dosage:</strong> {prescription[3]}</p>
                            <p style="margin: 0; color: #78350f; font-size: 14px;"><strong>Frequency:</strong> {prescription[4]}</p>
                        </div>
                        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 8px; margin-bottom: 8px;">
                            <p style="margin: 0; color: #78350f; font-size: 14px;"><strong>Duration:</strong> {prescription[5]}</p>
                            <p style="margin: 0; color: #78350f; font-size: 14px;"><strong>Indication:</strong> {prescription[7] or 'Not specified'}</p>
                        </div>
                        <p style="margin: 0; color: #a16207; font-size: 13px; font-style: italic;"><strong>Instructions:</strong> {prescription[6] or 'Standard instructions'}</p>
                    </div>
                    """, unsafe_allow_html=True)
                
                if patient_data['lab_results']:
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        if st.button(f"✅ Approve & Fill", key=f"approve_{patient_id}", type="primary"):
                            conn = sqlite3.connect("clinic_database.db")
                            cursor = conn.cursor()
                            
                            for prescription_id in prescription_ids:
                                cursor.execute('''
                                    UPDATE prescriptions 
                                    SET status = 'filled', awaiting_lab = 'no', filled_time = ? 
                                    WHERE id = ?
                                ''', (datetime.now().isoformat(), prescription_id))
                            
                            cursor.execute('''
                                UPDATE visits 
                                SET pharmacy_time = ?, status = 'completed' 
                                WHERE patient_id = ? AND DATE(visit_date) = DATE('now')
                            ''', (datetime.now().isoformat(), patient_id))
                            
                            conn.commit()
                            conn.close()
                            
                            st.success(f"✅ Prescriptions approved and filled for {patient_data['name']}!")
                            st.rerun()
                    
                    with col2:
                        if st.button(f"❌ Deny", key=f"deny_{patient_id}"):
                            conn = sqlite3.connect("clinic_database.db")
                            cursor = conn.cursor()
                            
                            for prescription_id in prescription_ids:
                                cursor.execute('''
                                    UPDATE prescriptions 
                                    SET status = 'denied', awaiting_lab = 'no' 
                                    WHERE id = ?
                                ''', (prescription_id,))
                            
                            conn.commit()
                            conn.close()
                            
                            st.error(f"❌ Prescriptions denied for {patient_data['name']}")
                            st.rerun()
                    
                    with col3:
                        if st.button(f"🔄 Return to Provider", key=f"return_{patient_id}"):
                            st.info(f"🔄 {patient_data['name']}'s prescriptions returned to provider for review")
    else:
        st.info("No prescriptions awaiting lab results.")

def filled_prescriptions():
    """Show filled prescriptions"""
    st.markdown("### Today's Filled Prescriptions")
    
    conn = sqlite3.connect("clinic_database.db")
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
            <div style="background: #e8f5e8; border: 1px solid #4caf50; border-radius: 8px; padding: 16px; margin-bottom: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
                <h5 style="color: #2e7d32; margin: 0 0 12px 0; font-size: 16px;">✅ {prescription[0]} - {prescription[5]} (ID: {prescription[6]})</h5>
                <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 8px;">
                    <p style="margin: 0; color: #388e3c; font-size: 14px;"><strong>Dosage:</strong> {prescription[1]}</p>
                    <p style="margin: 0; color: #388e3c; font-size: 14px;"><strong>Frequency:</strong> {prescription[2]}</p>
                    <p style="margin: 0; color: #388e3c; font-size: 14px;"><strong>Duration:</strong> {prescription[3]}</p>
                </div>
                <p style="margin: 8px 0 0 0; color: #546e7a; font-size: 13px;">Filled: {prescription[4][:16].replace('T', ' ')}</p>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("No prescriptions filled today.")

def lab_interface():
    """Lab interface for processing tests"""
    st.title("🔬 Lab Interface")
    
    tab1, tab2 = st.tabs(["Pending Tests", "Completed Tests"])
    
    with tab1:
        pending_lab_tests()
    
    with tab2:
        completed_lab_tests()

def pending_lab_tests():
    """Show pending lab tests"""
    st.markdown("### Pending Lab Tests")
    
    conn = sqlite3.connect("clinic_database.db")
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT lt.id, lt.visit_id, lt.test_type, lt.ordered_by, lt.ordered_time, 
               pt.name, v.patient_id
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
            test_id, visit_id, test_type, ordered_by, ordered_time, patient_name, patient_id = test
            
            with st.expander(f"🔬 {test_type} - {patient_name} (ID: {patient_id})"):
                st.write(f"**Ordered by:** Dr. {ordered_by}")
                st.write(f"**Ordered time:** {ordered_time[:16].replace('T', ' ')}")
                
                if test_type == "Urinalysis":
                    urinalysis_form(test_id)
                elif test_type == "Blood Glucose":
                    glucose_form(test_id)
                elif test_type == "Pregnancy Test":
                    pregnancy_form(test_id)
    else:
        st.info("No pending lab tests.")

def urinalysis_form(test_id: int):
    """Detailed urinalysis form"""
    with st.form(f"urinalysis_{test_id}"):
        st.markdown("#### Urinalysis Results")
        
        col1, col2 = st.columns(2)
        
        with col1:
            color = st.selectbox("Color", ["Yellow", "Pale Yellow", "Dark Yellow", "Amber", "Red", "Brown", "Clear"])
            clarity = st.selectbox("Clarity", ["Clear", "Slightly Cloudy", "Cloudy", "Turbid"])
            specific_gravity = st.number_input("Specific Gravity", min_value=1.000, max_value=1.050, value=1.020, step=0.001)
            ph = st.number_input("pH", min_value=4.0, max_value=9.0, value=6.0, step=0.1)
            protein = st.selectbox("Protein", ["Negative", "Trace", "1+", "2+", "3+", "4+"])
            glucose = st.selectbox("Glucose", ["Negative", "Trace", "1+", "2+", "3+", "4+"])
        
        with col2:
            ketones = st.selectbox("Ketones", ["Negative", "Trace", "Small", "Moderate", "Large"])
            blood = st.selectbox("Blood", ["Negative", "Trace", "1+", "2+", "3+"])
            bilirubin = st.selectbox("Bilirubin", ["Negative", "1+", "2+", "3+"])
            urobilinogen = st.selectbox("Urobilinogen", ["Normal", "2+", "4+", "8+"])
            nitrites = st.selectbox("Nitrites", ["Negative", "Positive"])
            leukocytes = st.selectbox("Leukocyte Esterase", ["Negative", "Trace", "1+", "2+", "3+"])
        
        notes = st.text_area("Additional Notes")
        
        if st.form_submit_button("Complete Urinalysis", type="primary"):
            results = f"""
            Color: {color}
            Clarity: {clarity}
            Specific Gravity: {specific_gravity}
            pH: {ph}
            Protein: {protein}
            Glucose: {glucose}
            Ketones: {ketones}
            Blood: {blood}
            Bilirubin: {bilirubin}
            Urobilinogen: {urobilinogen}
            Nitrites: {nitrites}
            Leukocyte Esterase: {leukocytes}
            Notes: {notes}
            """
            
            conn = sqlite3.connect("clinic_database.db")
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE lab_tests 
                SET status = 'completed', results = ?, completed_time = ?
                WHERE id = ?
            ''', (results.strip(), datetime.now().isoformat(), test_id))
            conn.commit()
            conn.close()
            
            st.success("✅ Urinalysis completed!")
            st.rerun()

def glucose_form(test_id: int):
    """Blood glucose test form"""
    with st.form(f"glucose_{test_id}"):
        st.markdown("#### Blood Glucose Results")
        
        glucose_value = st.number_input("Glucose Level (mg/dL)", min_value=20, max_value=600, value=100)
        test_time = st.selectbox("Test Time", ["Fasting", "Random", "2-hour Post-meal"])
        notes = st.text_area("Notes")
        
        if st.form_submit_button("Complete Glucose Test", type="primary"):
            results = f"Glucose: {glucose_value} mg/dL ({test_time})\nNotes: {notes}"
            
            conn = sqlite3.connect("clinic_database.db")
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE lab_tests 
                SET status = 'completed', results = ?, completed_time = ?
                WHERE id = ?
            ''', (results, datetime.now().isoformat(), test_id))
            conn.commit()
            conn.close()
            
            st.success("✅ Glucose test completed!")
            st.rerun()

def pregnancy_form(test_id: int):
    """Pregnancy test form"""
    with st.form(f"pregnancy_{test_id}"):
        st.markdown("#### Pregnancy Test Results")
        
        result = st.selectbox("Result", ["Positive", "Negative"])
        notes = st.text_area("Notes")
        
        if st.form_submit_button("Complete Pregnancy Test", type="primary"):
            results = f"Pregnancy Test: {result}\nNotes: {notes}"
            
            conn = sqlite3.connect("clinic_database.db")
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE lab_tests 
                SET status = 'completed', results = ?, completed_time = ?
                WHERE id = ?
            ''', (results, datetime.now().isoformat(), test_id))
            conn.commit()
            conn.close()
            
            st.success("✅ Pregnancy test completed!")
            st.rerun()

def completed_lab_tests():
    """Show completed lab tests"""
    st.markdown("### Today's Completed Lab Tests")
    
    conn = sqlite3.connect("clinic_database.db")
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT lt.test_type, lt.results, lt.completed_time, pt.name, v.patient_id
        FROM lab_tests lt
        JOIN visits v ON lt.visit_id = v.visit_id
        JOIN patients pt ON v.patient_id = pt.patient_id
        WHERE lt.status = 'completed' AND DATE(lt.completed_time) = DATE('now')
        ORDER BY lt.completed_time DESC
    ''')
    
    completed_tests = cursor.fetchall()
    conn.close()
    
    if completed_tests:
        for test in completed_tests:
            test_type, results, completed_time, patient_name, patient_id = test
            
            with st.expander(f"✅ {test_type} - {patient_name} (ID: {patient_id})"):
                st.write(f"**Completed:** {completed_time[:16].replace('T', ' ')}")
                st.markdown("**Results:**")
                st.text(results)
    else:
        st.info("No lab tests completed today.")

if __name__ == "__main__":
    main()