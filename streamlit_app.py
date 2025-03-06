# streamlit_app.py
import streamlit as st
import requests
import tempfile
import os
import fitz  # PyMuPDF
import json
import time

# Configure page
st.set_page_config(layout="wide", page_title="AI Career Guide")

# API URLs
API_SEARCH_URL = "http://127.0.0.1:8000/search_jobs"
API_SAVE_URL = "http://127.0.0.1:8000/save_job"
API_GET_DESCRIPTION_URL = "http://127.0.0.1:8000/get_saved_job_description"
API_EVALUATE_URL = "http://localhost:8000/evaluate"

# Initialize session state variables
if "saved_job" not in st.session_state:
    st.session_state["saved_job"] = None
if "job_results" not in st.session_state:
    st.session_state["job_results"] = []
if "job_desc" not in st.session_state:
    st.session_state["job_desc"] = None
if "evaluation_result" not in st.session_state:
    st.session_state["evaluation_result"] = None

# Function to extract text from PDF
def extract_text_from_pdf(pdf_file):
    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmpfile:
        tmpfile.write(pdf_file.getvalue())
        pdf_path = tmpfile.name
    
    text = ""
    try:
        doc = fitz.open(pdf_path)
        for page in doc:
            text += page.get_text()
        doc.close()
    except Exception as e:
        st.error(f"Error extracting text from PDF: {e}")
    finally:
        if os.path.exists(pdf_path):
            os.remove(pdf_path)
    
    return text

# Function for searching jobs
def search_jobs():
    if not st.session_state.job_title or not st.session_state.job_location:
        st.warning("Please enter both a job title and location.")
        return
    
    payload = {
        "role": st.session_state.job_title, 
        "location": st.session_state.job_location, 
        "num_results": st.session_state.num_results
    }
    
    with st.spinner("Searching for jobs..."):
        response = requests.post(API_SEARCH_URL, json=payload)
        
        if response.status_code == 200:
            try:
                job_results = response.json().get("results", [])
                if isinstance(job_results, list):
                    st.session_state["job_results"] = job_results  
                    st.success("Job search complete!")
                else:
                    st.error("Unexpected response format. Expected a list of job results.")
            except Exception as e:
                st.error(f"Error processing API response: {e}")
        else:
            st.error(f"Error: {response.status_code} - {response.text}")

# Function to save a job
def save_job(job_index):
    job = st.session_state["job_results"][job_index]
    try:
        response = requests.post(API_SAVE_URL, json={"job": job})
        if response.status_code == 200:
            st.session_state["saved_job"] = job  
            st.success("Job saved successfully!")
        else:
            st.error(f"Error saving job: {response.status_code}")
    except Exception as e:
        st.error(f"Failed to save job: {e}")

# Function to get job description
def get_job_description():
    try:
        desc_response = requests.get(API_GET_DESCRIPTION_URL)
        if desc_response.status_code == 200:
            st.session_state["job_desc"] = desc_response.json()
        else:
            st.warning("No job description found.")
    except Exception as e:
        st.error(f"Failed to fetch job description: {e}")

# Function to evaluate resume
def evaluate_resume():
    if not st.session_state.resume_file:
        st.warning("Please upload a resume file.")
        return
    
    if not st.session_state.saved_job:
        st.warning("Please select a job first.")
        return
    
    job_title = st.session_state.saved_job['Role']
    
    with st.spinner("Analyzing your resume... This may take a minute or two."):
        # Extract text from resume
        resume_text = extract_text_from_pdf(st.session_state.resume_file)
        
        if not resume_text:
            st.error("Could not extract text from the PDF. Please try another file.")
            return
        
        try:
            # Get job description
            job_description = "No description available"
            if st.session_state.job_desc:
                job_description = st.session_state.job_desc.get("Description", "No description available")
            
            # Prepare request data
            request_data = {
                "job_title": job_title,
                "job_des": job_description,
                "resume_text": resume_text
            }
            
            # Send request to API
            response = requests.post(API_EVALUATE_URL, json=request_data)
            
            if response.status_code == 200:
                st.session_state["evaluation_result"] = response.json()
            else:
                st.error(f"Error from API: {response.status_code} - {response.text}")
        
        except Exception as e:
            st.error(f"Error connecting to the API: {str(e)}")
            st.info("Make sure the backend server is running at the correct address.")

# Main app header
st.markdown("## 🚀 **AI-Powered Career Guide**")

with st.expander("About this tool"):
    st.write("""
    This AI-powered assistant helps you optimize your job search by evaluating your resume, finding relevant job opportunities, and providing tailored CV improvement tips.  

    **How it works:**  
    1. Enter your job preferences and upload your resume.  
    2. The system researches qualifications and requirements for your target job.  
    3. It evaluates your resume against these requirements.  
    4. You receive personalized feedback and job-specific CV optimization tips.   

    **Privacy note:** Your resume data is only used for analysis and is not stored permanently.  
    """)

# Create two columns for the main layout
col1, col2 = st.columns([2, 2])

# Left column - Job Search
with col1:
    st.subheader("🔎 Job Search Assistant")
    st.write("Enter your job preferences and find the best job opportunities!")

    # Form for job search
    with st.form(key="job_search_form"):
        st.session_state.job_title = st.text_input("Enter Job Title:", placeholder="e.g., Data Scientist")
        st.session_state.job_location = st.text_input("Enter Job Location:", placeholder="e.g., Copenhagen")
        st.session_state.num_results = st.number_input("Number of Results:", min_value=1, max_value=10, value=5)
        submit_button = st.form_submit_button(label="🔍 Search Jobs")
        
        if submit_button:
            search_jobs()
    
    # Show results
    if st.session_state["job_results"]:
        st.write("### Search Results")
        for i, job in enumerate(st.session_state["job_results"]):
            with st.expander(f"{i+1}. {job['Role']} at {job['Company']} ({job['Location']})"):
                st.write(f"**Role:** {job['Role']}")
                st.write(f"**Company:** {job['Company']}")
                st.write(f"**Location:** {job['Location']}")
                st.write(f"[Apply Here]({job['Link']})")
                
                if st.button(f"Show Full Description", key=f"desc_{i}"):
                    st.write(f"**Description:** {job.get('Description', 'No description available')}")
                
                if st.button(f"💾 Save This Job", key=f"save_{i}"):
                    save_job(i)
    
    # Show saved job
    if st.session_state["saved_job"]:
        st.write("### Saved Job Details")
        saved_job = st.session_state["saved_job"]
        st.write(f"**Role:** {saved_job['Role']}")
        st.write(f"**Company:** {saved_job['Company']}")
        st.write(f"**Location:** {saved_job['Location']}")
        st.write(f"[Job Link]({saved_job['Link']})")
        
        if st.button("📜 Get Job Description"):
            get_job_description()
        
        if st.session_state["job_desc"]:
            with st.expander("Job Description", expanded=True):
                st.write(st.session_state["job_desc"].get("Description", "No description available"))

# Right column - Resume Evaluator 
with col2:
    st.subheader("📄 Resume Evaluator")
    st.write("Upload your resume to get personalized feedback")
    
    # Resume upload
    st.session_state.resume_file = st.file_uploader("Upload Your Resume (PDF format)", type=["pdf"])
    
    # Evaluate button
    if st.button("Evaluate Resume"):
        evaluate_resume()
    
    # Show evaluation results if available
    if st.session_state["evaluation_result"]:
        result = st.session_state["evaluation_result"]
        
        # Display job requirements
        with st.expander("Job Requirements Analysis", expanded=True):
            st.markdown(result["job_requirements"])
        
        # Display evaluation results
        st.subheader("Resume Evaluation Results")
        st.markdown(result["evaluation_result"])
        
        # Add download button for the results
        combined_result = f"# Job Requirements\n\n{result['job_requirements']}\n\n# Resume Evaluation\n\n{result['evaluation_result']}"
        st.download_button(
            "Download Complete Report",
            combined_result,
            file_name="resume_evaluation_report.md",
            mime="text/markdown"
        )
