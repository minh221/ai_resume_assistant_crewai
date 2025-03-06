# AI Resume Evaluator & Job Search Assistant

## Overview
This project is an AI-powered application that assists users in evaluating their resumes and finding relevant job opportunities. It consists of two key components:

1. **Job Search Agent** - Fetches job listings based on user-defined roles and locations.
2. **Resume Evaluator Agent** - Analyzes a user's resume against industry qualifications and provides feedback.

The application is built using **CrewAI, Flowise AI, Streamlit, and OpenAI/DeepSeek LLMs**.

---

## Features

### **1️⃣ Job Search Agent**
- Users input their **desired job title** and **location**.
- The AI fetches job listings from APIs like Adzuna.
- Displays relevant jobs in a structured JSON format.
  
### **2️⃣ Resume Evaluator Agent**
- Users upload their resume (PDF/DOCX).
- AI compares the resume against common qualifications for the specified job role.
- Provides feedback and suggestions to improve the resume.
  
### **3️⃣ Interactive UI with Streamlit**
- Users can easily upload resumes and search for jobs.
- Displays feedback and job results in a user-friendly manner.

---

## Tech Stack
- **Python** (FastAPI, CrewAI, Flowise AI, Streamlit)
- **LLMs** (OpenAI GPT-4, DeepSeek via OpenRouter)
- **APIs** (Adzuna for job search)
- **Libraries**: `requests`, `json`, `pdfplumber`, `langchain`, `CrewAI`

---

## Installation & Setup
### **1️⃣ Clone the Repository**
```bash
 git clone https://github.com/minh221/ai-resume-assistant-crewai.git
 cd ai-resume-assistant-crewai
```

### **2️⃣ Install Dependencies**
```bash
pip install -r requirements.txt
```

### **3️⃣ Set API Keys**
Create a `.env` file and add the required API keys:
```env
OPENAI_API_KEY=your_openai_key
ADZUNA_APP_ID=your_app_id
ADZUNA_API_KEY=your_adzuna_key
```

### **4️⃣ Run the Streamlit App**
```bash
streamlit run app.py
```

---

## Usage

1. **Enter job title & location**: Fetches job listings and save a job you interest
2. **Upload your resume**: AI provides feedback.
3. **View results**: Resume tips & job opportunities appear on the UI.

---


