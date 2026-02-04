import streamlit as st
import mysql.connector
import pandas as pd
import matplotlib.pyplot as plt

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Student Performance Pro",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CUSTOM CSS FOR STYLING ---
st.markdown("""
    <style>
    .main {
        background-color: #f5f7f9;
    }
    .stMetric {
        background-color: #ffffff;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.1);
        text-align: center;
    }
    h1, h2, h3 {
        color: #2c3e50;
    }
    .stButton>button {
        border-radius: 5px;
        font-weight: bold;
    }
    </style>
    """, unsafe_allow_html=True)

# --- DATABASE CONNECTION ---
# ⚠️ CHANGE THESE CREDENTIALS TO MATCH YOUR MYSQL SETUP
db_config = {
    'host': 'localhost',
    'user': 'root', 
    'password': 'root',  
    'database': 'student_db'
}

def get_connection():
    try:
        conn = mysql.connector.connect(**db_config)
        return conn
    except mysql.connector.Error as err:
        st.error(f"Error: {err}")
        return None

# --- DATABASE FUNCTIONS ---
def create_student(name, age, subject, marks):
    conn = get_connection()
    if conn:
        cursor = conn.cursor()
        query = "INSERT INTO students (name, age, subject, marks) VALUES (%s, %s, %s, %s)"
        cursor.execute(query, (name, age, subject, marks))
        conn.commit()
        conn.close()
        st.success(f"✅ Student {name} added successfully!")

def view_all_students():
    conn = get_connection()
    if conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM students")
        data = cursor.fetchall()
        conn.close()
        return data
    return []

def update_student(id, new_marks):
    conn = get_connection()
    if conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE students SET marks = %s WHERE id = %s", (new_marks, id))
        conn.commit()
        conn.close()
        st.success("✅ Marks updated successfully!")

def delete_student(id):
    conn = get_connection()
    if conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM students WHERE id = %s", (id,))
        conn.commit()
        conn.close()
        st.warning("🗑️ Student record deleted.")

# --- SIDEBAR MENU ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3407/3407024.png", width=100)
    st.title("Navigation")
    menu = ["Dashboard 📊", "Add Student ➕", "Manage Records 📝"]
    choice = st.radio("Go to", menu)
    
    st.markdown("---")
    st.info("Student Performance Management System v1.0")

# --- MAIN APPLICATION LOGIC ---

if choice == "Add Student ➕":
    st.header("➕ Add New Student Record")
    st.markdown("Fill in the details below to add a new student to the database.")
    
    with st.form("add_form"):
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("Student Name")
            # We allow input, but validate logically later
            age = st.number_input("Age", min_value=1, step=1)
        with col2:
            # UPDATED: Text input instead of dropdown so user can type any subject
            subject = st.text_input("Subject") 
            marks = st.number_input("Marks (0-100)", min_value=0, max_value=100)
            
        submitted = st.form_submit_button("Save Record")
        
        if submitted:
            # --- VALIDATION LOGIC ---
            
            # 1. Check if fields are empty
            if not name or not subject:
                st.error("⚠️ Please fill in all fields (Name and Subject).")
            
            # 2. Check Name (Letters only, allowing spaces)
            elif not name.replace(" ", "").isalpha():
                st.error("🚨 Name must contain letters only (no numbers or symbols).")
            
            # 3. Check Age Limit
            elif age > 100:
                st.error("🚨 Age cannot be more than 100.")
            
            # 4. If all checks pass -> Save to DB
            else:
                create_student(name, age, subject, marks)

elif choice == "Manage Records 📝":
    st.header("📝 Manage Student Records")
    data = view_all_students()
    
    # Check if data exists
    if data:
        df = pd.DataFrame(data, columns=['ID', 'Name', 'Age', 'Subject', 'Marks'])
        
        # Add Pass/Fail Column for display
        df['Status'] = df['Marks'].apply(lambda x: 'Pass' if x >= 40 else 'Fail')
        
        # Display Table with color coding
        st.dataframe(df.style.map(lambda x: 'color: red' if x == 'Fail' else 'color: green', subset=['Status']), use_container_width=True)

        st.markdown("### Update or Delete")
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Update Marks")
            student_id = st.selectbox("Select Student ID to Update", df['ID'].unique(), key="update_id")
            new_mark = st.number_input("New Marks", min_value=0, max_value=100)
            if st.button("Update Marks"):
                update_student(student_id, new_mark)
                st.rerun()

        with col2:
            st.subheader("Delete Student")
            delete_id = st.selectbox("Select Student ID to Delete", df['ID'].unique(), key="delete_id")
            if st.button("Delete Record", type="primary"):
                delete_student(delete_id)
                st.rerun()
    else:
        st.info("No records found. Go to 'Add Student' to create one.")

elif choice == "Dashboard 📊":
    st.title("📊 Performance Dashboard")
    
    data = view_all_students()
    
    if data:
        df = pd.DataFrame(data, columns=['ID', 'Name', 'Age', 'Subject', 'Marks'])
        
        # --- KEY METRICS ---
        total_students = len(df)
        avg_marks = round(df['Marks'].mean(), 2)
        top_scorer = df.loc[df['Marks'].idxmax()]['Name']
        pass_percentage = round((len(df[df['Marks'] >= 40]) / total_students) * 100, 2)
        
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("🎓 Total Students", total_students)
        m2.metric("⭐ Average Marks", f"{avg_marks}")
        m3.metric("🏆 Top Scorer", top_scorer)
        m4.metric("📈 Pass Percentage", f"{pass_percentage}%")
        
        st.markdown("---")
        
        # --- CHARTS ---
        col1, col2 = st.columns(2)
        
        # Bar Chart: Average Marks per Subject
        with col1:
            st.subheader("Average Marks per Subject")
            subject_avg = df.groupby('Subject')['Marks'].mean()
            
            fig1, ax1 = plt.subplots(figsize=(5,4))
            colors = ['#ff9999','#66b3ff','#99ff99','#ffcc99','#c2c2f0']
            
            # Handle case if fewer subjects than colors
            if len(subject_avg) > len(colors):
                colors = colors * (len(subject_avg) // len(colors) + 1)
                
            subject_avg.plot(kind='bar', color=colors[:len(subject_avg)], ax=ax1, edgecolor='black')
            ax1.set_ylabel("Average Marks")
            ax1.set_xlabel("Subject")
            plt.xticks(rotation=45)
            plt.grid(axis='y', linestyle='--', alpha=0.7)
            st.pyplot(fig1)
            
        # Pie Chart: Pass vs Fail
        with col2:
            st.subheader("Pass vs Fail Ratio")
            pass_count = len(df[df['Marks'] >= 40])
            fail_count = len(df[df['Marks'] < 40])
            
            if pass_count + fail_count > 0:
                fig2, ax2 = plt.subplots(figsize=(5,4))
                ax2.pie([pass_count, fail_count], labels=['Pass', 'Fail'], 
                        autopct='%1.1f%%', startangle=90, 
                        colors=['#66b3ff', '#ff9999'], explode=(0.05, 0))
                ax2.axis('equal')
                st.pyplot(fig2)
            else:
                st.write("Not enough data for Pass/Fail analysis.")
    else:
        st.warning("No data available. Go to the 'Add Student' tab to insert data.")