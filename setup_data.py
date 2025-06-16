import sqlite3
from datetime import datetime

def setup_clinic_data():
    """Initialize the clinic database with essential preset data"""
    
    conn = sqlite3.connect("clinic_database.db")
    cursor = conn.cursor()
    
    # Clear existing data
    cursor.execute("DELETE FROM preset_medications")
    cursor.execute("DELETE FROM doctors")
    
    # Insert preset medications
    medications = [
        # Antibiotics
        ("Amoxicillin", "250mg, 500mg, 875mg", "no", "Antibiotics"),
        ("Azithromycin", "250mg, 500mg", "no", "Antibiotics"),
        ("Ciprofloxacin", "250mg, 500mg", "no", "Antibiotics"),
        ("Doxycycline", "100mg", "no", "Antibiotics"),
        ("Cephalexin", "250mg, 500mg", "no", "Antibiotics"),
        ("Clindamycin", "150mg, 300mg", "no", "Antibiotics"),
        ("Metronidazole", "250mg, 500mg", "no", "Antibiotics"),
        ("Trimethoprim-Sulfamethoxazole", "80mg-400mg, 160mg-800mg", "yes", "Antibiotics"),
        
        # Pain Relief
        ("Acetaminophen", "325mg, 500mg, 650mg", "no", "Pain Relief"),
        ("Ibuprofen", "200mg, 400mg, 600mg, 800mg", "no", "Pain Relief"),
        ("Naproxen", "220mg, 375mg, 500mg", "no", "Pain Relief"),
        ("Aspirin", "81mg, 325mg", "no", "Pain Relief"),
        ("Tramadol", "50mg, 100mg", "no", "Pain Relief"),
        
        # Cardiovascular
        ("Lisinopril", "5mg, 10mg, 20mg, 40mg", "yes", "Cardiovascular"),
        ("Amlodipine", "2.5mg, 5mg, 10mg", "no", "Cardiovascular"),
        ("Metoprolol", "25mg, 50mg, 100mg", "no", "Cardiovascular"),
        ("Hydrochlorothiazide", "12.5mg, 25mg, 50mg", "yes", "Cardiovascular"),
        ("Atorvastatin", "10mg, 20mg, 40mg, 80mg", "yes", "Cardiovascular"),
        
        # Diabetes
        ("Metformin", "500mg, 850mg, 1000mg", "yes", "Diabetes"),
        ("Glipizide", "5mg, 10mg", "yes", "Diabetes"),
        ("Insulin NPH", "U-100", "yes", "Diabetes"),
        ("Insulin Regular", "U-100", "yes", "Diabetes"),
        
        # Respiratory
        ("Albuterol Inhaler", "90mcg/puff", "no", "Respiratory"),
        ("Fluticasone Inhaler", "44mcg, 110mcg, 220mcg", "no", "Respiratory"),
        ("Prednisone", "5mg, 10mg, 20mg", "no", "Respiratory"),
        ("Guaifenesin", "100mg, 200mg, 400mg", "no", "Respiratory"),
        ("Dextromethorphan", "15mg, 30mg", "no", "Respiratory"),
        
        # Gastrointestinal
        ("Omeprazole", "10mg, 20mg, 40mg", "no", "Gastrointestinal"),
        ("Famotidine", "10mg, 20mg, 40mg", "no", "Gastrointestinal"),
        ("Ondansetron", "4mg, 8mg", "no", "Gastrointestinal"),
        ("Loperamide", "2mg", "no", "Gastrointestinal"),
        ("Bismuth Subsalicylate", "262mg", "no", "Gastrointestinal"),
        
        # Dermatology
        ("Hydrocortisone Cream", "0.5%, 1%, 2.5%", "no", "Dermatology"),
        ("Mupirocin Ointment", "2%", "no", "Dermatology"),
        ("Clotrimazole Cream", "1%", "no", "Dermatology"),
        ("Ketoconazole Cream", "2%", "no", "Dermatology"),
        
        # Ophthalmology
        ("Ciprofloxacin Eye Drops", "0.3%", "no", "Ophthalmology"),
        ("Prednisolone Eye Drops", "1%", "no", "Ophthalmology"),
        ("Artificial Tears", "Various", "no", "Ophthalmology"),
        
        # Women's Health
        ("Levonorgestrel", "1.5mg", "no", "Women's Health"),
        ("Iron Sulfate", "65mg", "no", "Women's Health"),
        ("Folic Acid", "0.4mg, 5mg", "no", "Women's Health"),
        
        # Mental Health
        ("Sertraline", "25mg, 50mg, 100mg", "no", "Mental Health"),
        ("Fluoxetine", "10mg, 20mg, 40mg", "no", "Mental Health"),
        ("Lorazepam", "0.5mg, 1mg, 2mg", "no", "Mental Health"),
        
        # Vitamins/Supplements
        ("Vitamin D3", "1000IU, 2000IU, 5000IU", "no", "Vitamins"),
        ("Vitamin B12", "100mcg, 500mcg, 1000mcg", "no", "Vitamins"),
        ("Multivitamin", "Adult, Children", "no", "Vitamins"),
        ("Calcium Carbonate", "500mg, 600mg", "no", "Vitamins"),
        
        # Topical/Other
        ("Bacitracin Ointment", "500 units/g", "no", "Topical"),
        ("Triple Antibiotic Ointment", "400 units/g", "no", "Topical"),
        ("Calamine Lotion", "8%", "no", "Topical"),
        ("Zinc Oxide", "20%, 40%", "no", "Topical")
    ]
    
    for med in medications:
        cursor.execute('''
            INSERT INTO preset_medications (medication_name, common_dosages, requires_lab, category, active)
            VALUES (?, ?, ?, ?, TRUE)
        ''', med)
    
    # Insert doctors
    doctors = [
        "Dr. Sarah Johnson",
        "Dr. Michael Rodriguez", 
        "Dr. Emily Chen",
        "Dr. David Thompson",
        "Dr. Lisa Martinez",
        "Dr. James Wilson",
        "Dr. Maria Garcia",
        "Dr. Robert Kim"
    ]
    
    for doctor in doctors:
        cursor.execute('''
            INSERT OR IGNORE INTO doctors (name, is_active, created_at)
            VALUES (?, TRUE, ?)
        ''', (doctor, datetime.now().isoformat()))
    
    conn.commit()
    conn.close()
    print("✅ Clinic data setup complete!")

if __name__ == "__main__":
    setup_clinic_data()