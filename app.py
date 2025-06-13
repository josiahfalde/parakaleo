import streamlit as st
import sqlite3
from datetime import datetime
import os
from typing import Dict, List, Optional

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
                medication_name TEXT,
                dosage TEXT,
                frequency TEXT,
                duration TEXT,
                instructions TEXT,
                status TEXT DEFAULT 'pending',
                prescribed_time TEXT,
                filled_time TEXT,
                FOREIGN KEY (visit_id) REFERENCES visits (visit_id)
            )
        ''')
        
        # Create counter table for patient numbering
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS counters (
                name TEXT PRIMARY KEY,
                value INTEGER
            )
        ''')
        
        # Initialize patient counter if it doesn't exist
        cursor.execute('INSERT OR IGNORE INTO counters (name, value) VALUES (?, ?)', 
                      ('patient_counter', 0))
        
        conn.commit()
        conn.close()
    
    def get_next_patient_id(self) -> str:
        """Get the next patient ID in format 00001, 00002, etc."""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('SELECT value FROM counters WHERE name = ?', ('patient_counter',))
        current_value = cursor.fetchone()[0]
        new_value = current_value + 1
        
        cursor.execute('UPDATE counters SET value = ? WHERE name = ?', 
                      (new_value, 'patient_counter'))
        
        conn.commit()
        conn.close()
        
        return f"{new_value:05d}"
    
    def add_patient(self, **kwargs) -> str:
        """Add a new patient and return their ID"""
        patient_id = self.get_next_patient_id()
        
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
    
    def create_visit(self, patient_id: str, priority: str = 'normal') -> str:
        """Create a new visit for a patient"""
        visit_id = f"{patient_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO visits (visit_id, patient_id, visit_date, status, priority)
            VALUES (?, ?, ?, ?, ?)
        ''', (visit_id, patient_id, datetime.now().isoformat(), 'triage', priority))
        
        # Update patient's last visit
        cursor.execute('''
            UPDATE patients SET last_visit = ? WHERE patient_id = ?
        ''', (datetime.now().isoformat(), patient_id))
        
        conn.commit()
        conn.close()
        
        return visit_id

# Initialize database
@st.cache_resource
def get_db_manager():
    return DatabaseManager()

db = get_db_manager()

def main():
    st.title("🏥 Medical Clinic Charting System")
    st.markdown("### Mission Trip Patient Management")
    
    # Role selection
    if 'user_role' not in st.session_state:
        st.session_state.user_role = None
    
    if st.session_state.user_role is None:
        st.markdown("#### Select Your Role:")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("🩺 Triage Nurse", key="triage", type="primary"):
                st.session_state.user_role = "triage"
                st.rerun()
        
        with col2:
            if st.button("👨‍⚕️ Doctor", key="doctor", type="primary"):
                st.session_state.user_role = "doctor"
                st.rerun()
        
        with col3:
            if st.button("💊 Pharmacy", key="pharmacy", type="primary"):
                st.session_state.user_role = "pharmacy"
                st.rerun()
        
        st.markdown("---")
        st.info("This system works offline and stores all patient data locally for mission trips in remote areas.")
        
        return
    
    # Role-specific interfaces
    if st.session_state.user_role == "triage":
        triage_interface()
    elif st.session_state.user_role == "doctor":
        doctor_interface()
    elif st.session_state.user_role == "pharmacy":
        pharmacy_interface()
    
    # Role change button
    st.sidebar.markdown("---")
    if st.sidebar.button("🔄 Change Role"):
        st.session_state.user_role = None
        st.rerun()

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
            gender = st.selectbox("Gender", ["", "Male", "Female", "Other"])
        
        with col2:
            phone = st.text_input("Phone Number", placeholder="Optional")
            emergency_contact = st.text_input("Emergency Contact", placeholder="Optional")
        
        medical_history = st.text_area("Medical History", placeholder="Previous conditions, surgeries, etc.")
        allergies = st.text_area("Allergies", placeholder="Known allergies or medications to avoid")
        
        priority = st.selectbox("Priority Level", ["Normal", "Urgent", "Critical"])
        
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
                
                patient_id = db.add_patient(**patient_data)
                visit_id = db.create_visit(patient_id, priority.lower())
                
                st.success(f"✅ Patient registered successfully!")
                st.info(f"**Patient ID:** {patient_id}")
                st.info(f"**Visit ID:** {visit_id}")
                
                # Show vital signs form
                st.markdown("### Record Vital Signs")
                vital_signs_form(visit_id)
            else:
                st.error("Please enter the patient's name.")

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
                    
                    col1, col2 = st.columns([1, 1])
                    with col1:
                        priority = st.selectbox(f"Priority for {patient['name']}", 
                                              ["Normal", "Urgent", "Critical"], 
                                              key=f"priority_{patient['patient_id']}")
                    
                    with col2:
                        if st.button(f"Start New Visit", key=f"visit_{patient['patient_id']}"):
                            visit_id = db.create_visit(patient['patient_id'], priority.lower())
                            st.success(f"✅ New visit created for {patient['name']}")
                            st.info(f"**Visit ID:** {visit_id}")
                            
                            # Show vital signs form
                            st.markdown("### Record Vital Signs")
                            vital_signs_form(visit_id)
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
    st.markdown("## 👨‍⚕️ Doctor Consultation")
    
    tab1, tab2 = st.tabs(["Patient Consultation", "Consultation History"])
    
    with tab1:
        consultation_interface()
    
    with tab2:
        consultation_history()

def consultation_interface():
    st.markdown("### Select Patient for Consultation")
    
    # Get patients waiting for consultation
    conn = sqlite3.connect(db.db_name)
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
                            st.rerun()
                
                # Show consultation form if this patient is selected
                if st.session_state.get('current_consultation') == visit_id:
                    consultation_form(visit_id, patient_id, name)
    else:
        st.info("No patients waiting for consultation.")

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
        doctor_name = st.text_input("Doctor Name", placeholder="Your name")
        
        chief_complaint = st.text_area("Chief Complaint", placeholder="What brought the patient in today?")
        symptoms = st.text_area("Symptoms", placeholder="Describe symptoms observed/reported")
        diagnosis = st.text_area("Diagnosis", placeholder="Your diagnosis")
        treatment_plan = st.text_area("Treatment Plan", placeholder="Recommended treatment")
        notes = st.text_area("Additional Notes", placeholder="Any additional observations")
        
        st.markdown("#### Prescriptions")
        
        # Prescription fields
        num_medications = st.number_input("Number of Medications", min_value=0, max_value=10, value=1)
        
        medications = []
        for i in range(int(num_medications)):
            st.markdown(f"**Medication {i+1}:**")
            col1, col2 = st.columns(2)
            
            with col1:
                med_name = st.text_input(f"Medication Name", key=f"med_name_{i}")
                dosage = st.text_input(f"Dosage", key=f"dosage_{i}")
            
            with col2:
                frequency = st.text_input(f"Frequency", key=f"frequency_{i}")
                duration = st.text_input(f"Duration", key=f"duration_{i}")
            
            instructions = st.text_input(f"Special Instructions", key=f"instructions_{i}")
            
            if med_name:
                medications.append({
                    'name': med_name,
                    'dosage': dosage,
                    'frequency': frequency,
                    'duration': duration,
                    'instructions': instructions
                })
        
        if st.form_submit_button("Complete Consultation", type="primary"):
            if doctor_name and chief_complaint:
                # Save consultation
                cursor.execute('''
                    INSERT INTO consultations (visit_id, doctor_name, chief_complaint, 
                                             symptoms, diagnosis, treatment_plan, notes, consultation_time)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (visit_id, doctor_name, chief_complaint, symptoms, diagnosis, 
                      treatment_plan, notes, datetime.now().isoformat()))
                
                # Save prescriptions
                for med in medications:
                    cursor.execute('''
                        INSERT INTO prescriptions (visit_id, medication_name, dosage, 
                                                 frequency, duration, instructions, prescribed_time)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (visit_id, med['name'], med['dosage'], med['frequency'], 
                          med['duration'], med['instructions'], datetime.now().isoformat()))
                
                # Update visit status
                new_status = 'prescribed' if medications else 'completed'
                cursor.execute('''
                    UPDATE visits SET consultation_time = ?, status = ? WHERE visit_id = ?
                ''', (datetime.now().isoformat(), new_status, visit_id))
                
                conn.commit()
                conn.close()
                
                st.success("✅ Consultation completed successfully!")
                if medications:
                    st.info("📋 Prescriptions sent to pharmacy.")
                
                # Clear current consultation
                if 'current_consultation' in st.session_state:
                    del st.session_state.current_consultation
                
                st.rerun()
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
    
    tab1, tab2 = st.tabs(["Pending Prescriptions", "Filled Prescriptions"])
    
    with tab1:
        pending_prescriptions()
    
    with tab2:
        filled_prescriptions()

def pending_prescriptions():
    st.markdown("### Prescriptions to Fill")
    
    conn = sqlite3.connect(db.db_name)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT p.id, p.visit_id, p.medication_name, p.dosage, p.frequency, 
               p.duration, p.instructions, p.prescribed_time, pt.name, v.patient_id
        FROM prescriptions p
        JOIN visits v ON p.visit_id = v.visit_id
        JOIN patients pt ON v.patient_id = pt.patient_id
        WHERE p.status = 'pending' AND DATE(p.prescribed_time) = DATE('now')
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

if __name__ == "__main__":
    main()