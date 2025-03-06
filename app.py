# app.py
import os
import json
import requests
from dotenv import load_dotenv
from crewai import Agent, Task, Crew, Process
from langchain_openai import ChatOpenAI
from langchain.tools import tool
from langchain.prompts import PromptTemplate
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn
from agents import save_job, get_saved_job, job_researcher, resume_evaluator
from tasks import job_search_task, jd_research_task, evaluation_task

app = FastAPI()

class SaveJobRequest(BaseModel):
    job: dict

@app.post("/save_job")
def save_favorite_job(request: SaveJobRequest):
    save_job(request.job)
    return {"message": "Job saved successfully!"}

@app.get("/get_saved_job")
def fetch_saved_job():
    job = get_saved_job()
    if not job:
        raise HTTPException(status_code=404, detail="No saved job found.")
    return job

@app.get("/get_saved_job_description")
def fetch_saved_job_description():
    job = get_saved_job()
    if not job:
        raise HTTPException(status_code=404, detail="No saved job found.")
    return {"Role": job["Role"], "Company": job["Company"], "Description": job["Description"]}

class JobSearchRequest(BaseModel):
    role: str
    location: str
    num_results: int = 5

@app.post("/search_jobs")
def search_jobs(request: JobSearchRequest):
    try:
        task = job_search_task(request.role, request.location, request.num_results)
        Crew(tasks=[task]).kickoff()
        with open("task_output.txt", "r") as file:
            results = file.read()
        try:
            job_list = json.loads(results.strip())  
            if isinstance(job_list, list):  
                return {"results": job_list}
            else:
                raise ValueError("CrewAI returned an invalid format (not a list).")
        except json.JSONDecodeError:
            print("DEBUG: Raw CrewAI Output ->", results)  
            raise HTTPException(status_code=500, detail="Invalid JSON format from CrewAI.")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



class ResumeEvaluationRequest(BaseModel):
    job_title: str
    job_des: str
    resume_text: str

class ResumeEvaluationResponse(BaseModel):
    job_requirements: str
    evaluation_result: str

@app.post("/evaluate", response_model=ResumeEvaluationResponse)
async def evaluate_resume(request: ResumeEvaluationRequest):
    try:        
        # Create and run research task
        research_task = jd_research_task(request.job_title, request.job_des)
        research_crew = Crew(
            agents=[job_researcher],
            tasks=[research_task],
            verbose=True,
            process=Process.sequential
        )

        job_requirements_output = research_crew.kickoff()


        # Extract the string from the CrewOutput object
        if hasattr(job_requirements_output, 'raw'):
            job_requirements = job_requirements_output.raw
        else:
            # For older versions or if the structure is different
            job_requirements = str(job_requirements_output)
        
        print('evaluation crew')
        # Create and run evaluation task
        eval_task = evaluation_task(job_requirements, request.resume_text)
        evaluation_crew = Crew(
            agents=[resume_evaluator],
            tasks=[eval_task],
            verbose=True,
            process=Process.sequential
        )

        evaluation_output = evaluation_crew.kickoff()
        evaluation_result = getattr(evaluation_output, 'raw', str(evaluation_output))
        
        return ResumeEvaluationResponse(
            job_requirements=job_requirements,
            evaluation_result=evaluation_result
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing request: {str(e)}")


@app.post("/search_jobs_mock")
def search_jobs_mock(request: JobSearchRequest):
    # Sample mock data
    if request.role == "Financial Controller" and request.location == "Copenhagen":
        mock_results = [
            {
                "Role": "Financial Controller",
                "Company": "Maersk",
                "Location": "Copenhagen, Denmark",
                "Link": "https://www.maersk.com/careers",
                "Description": "As a Financial Controller at Maersk, you will play a critical role in ensuring the accuracy of financial reporting, compliance with international accounting standards, and supporting strategic decision-making. Your responsibilities will include preparing financial statements, conducting variance analysis, and optimizing internal financial processes. You will work closely with cross-functional teams to enhance cost efficiency and support budgeting and forecasting activities in a global shipping and logistics environment."
            },
            {
                "Role": "Senior Financial Controller",
                "Company": "Novo Nordisk",
                "Location": "Copenhagen, Denmark",
                "Link": "https://www.novonordisk.com/careers",
                "Description": "Novo Nordisk is seeking a Senior Financial Controller to oversee financial operations and ensure compliance with IFRS and internal controls. You will be responsible for consolidating financial data, analyzing business performance, and providing financial insights to senior management. Additionally, you will play a key role in process optimization, risk management, and regulatory reporting. This position is ideal for a finance professional with strong analytical skills and experience in multinational corporate environments."
            },
            {
                "Role": "Group Financial Controller",
                "Company": "Carlsberg Group",
                "Location": "Copenhagen, Denmark",
                "Link": "https://www.carlsberggroup.com/careers",
                "Description": "Carlsberg Group is looking for an experienced Group Financial Controller to take ownership of the company's financial consolidation and reporting processes across multiple business units. You will ensure compliance with international financial regulations, oversee internal audits, and collaborate with senior stakeholders on strategic financial initiatives. This role requires proficiency in SAP and a deep understanding of financial planning, taxation, and regulatory frameworks. If you have a background in FMCG or manufacturing, this could be the perfect opportunity for you."
            },
            {
                "Role": "Financial Controller",
                "Company": "Ørsted",
                "Location": "Copenhagen, Denmark",
                "Link": "https://www.orsted.com/careers",
                "Description": "Ørsted is hiring a Financial Controller to support its financial reporting, investment evaluations, and risk management functions. In this role, you will be responsible for maintaining financial accuracy in accordance with IFRS, supporting M&A activities, and ensuring compliance with industry-specific regulations. You will work closely with senior finance professionals to drive business performance and sustainability initiatives within the renewable energy sector. Strong financial modeling and analytical skills are essential."
            },
            {
                "Role": "Financial Controller",
                "Company": "Deloitte Denmark",
                "Location": "Copenhagen, Denmark",
                "Link": "https://www2.deloitte.com/dk/en/careers",
                "Description": "Deloitte is looking for a highly motivated Financial Controller to support financial reporting, auditing, and advisory services for a diverse client portfolio. You will play a key role in preparing financial statements, conducting financial due diligence, and advising clients on accounting best practices. The role requires a solid understanding of Danish GAAP, IFRS, and tax regulations. If you thrive in a dynamic, client-focused environment and enjoy problem-solving in finance, this role offers exciting career development opportunities."
            }
        ]
    elif request.role == "Data Scientist" and request.location == "Newyork":
        mock_results = [
            {
                "Role": "Business Data Scientist",
                "Company": "Success Academy Charter Schools",
                "Location": "New York City, New York",
                "Link": "https://www.adzuna.com/land/ad/4893845997?se=8tHy8Qb67xGiLBbyy3A-oA&utm_medium=api&utm_source=9b959fd9&v=0AAC81604EE4412C01279DFC100233FF4CA76143",
                "Description": "Thanks for your interest in Success Academy Running the largest, fastest-growing, and highest-performing network of public charter schools in New York City takes a village - families, children, teachers, staff and faculty, advocates and supporters alike. We would love to welcome you to our community We work tirelessly every day to ensure each child in NYC has access to a fun, rigorous, whole-child education regardless of zip code or economic status. When you join SA, you play a part in giving e\u2026"
            },
            {
                "Role": "Senior Data Scientist",
                "Company": "Labcorp",
                "Location": "Grand Central, Manhattan",
                "Link": "https://www.adzuna.com/land/ad/5074893173?se=8tHy8Qb67xGiLBbyy3A-oA&utm_medium=api&utm_source=9b959fd9&v=F69E7DEDE784B061CB3E9E6091AB4CB5F9CDC811",
                "Description": "Imagine being involved with innovative projects that change the course of our industry daily At Labcorp, one of the world\u2019s largest and most comprehensive pharmaceutical solutions service companies, you will have an opportunity to build an exciting career while you make a direct impact on the lives of millions. Labcorp is recruiting a Senior Data Scientist for a dynamic team in North Carolina. This position can also potentially be a Remote position. Summary: To produce innovative solutions driv\u2026"
            },
            {
                "Role": "Principal Data Scientist",
                "Company": "InVitro Cell Research, LLC",
                "Location": "Fort Lee, Bergen County",
                "Link": "https://www.adzuna.com/land/ad/5040718039?se=8tHy8Qb67xGiLBbyy3A-oA&utm_medium=api&utm_source=9b959fd9&v=34B26948A3077A1BABABC20A557ACD3B937A5D4C",
                "Description": "We're hiring a Principal Data Scientist with expertise in predictive statistics (analytics and modeling, especially as applied to diagnostics), bioinformatics and machine learning. Because you will be working with medical and biological datasets, a background in biomedical sciences is required. Fluency in R and Python is definitely preferred. Please notice that this is not a financial-sector job . However, if you're looking for a challenging, deeply rewarding position applying advanced data ana\u2026"
            },
            {
                "Role": "Senior Data Scientist",
                "Company": "InVitro Cell Research, LLC",
                "Location": "Fort Lee, Bergen County",
                "Link": "https://www.adzuna.com/land/ad/5039580461?se=8tHy8Qb67xGiLBbyy3A-oA&utm_medium=api&utm_source=9b959fd9&v=63BCCC51D4B664270D84638A7EBBBC2AEC2072CE",
                "Description": "We're hiring Senior Data Scientists with expertise in integrating and analyzing multi-omic datasets to identify diagnostic disease signatures and find actionable targets for drug development. These scientists would work in ICR's Translational Bioinformatics Group, focusing on rare and hard-to-diagnose diseases. Strong programming and statistics backgrounds are required, and machine learning experience is preferred. With ICR, you'll get to: Perform high-impact, high-reward rare and hard-to-diagn\u2026"
            },
            {
                "Role": "Senior Data Scientist",
                "Company": "Formation Bio",
                "Location": "New York City, New York",
                "Link": "https://www.adzuna.com/land/ad/5050465293?se=8tHy8Qb67xGiLBbyy3A-oA&utm_medium=api&utm_source=9b959fd9&v=50ABE26B52958CB617CEB4EBA04EC5A448E44FCB",
                "Description": "About Formation Bio Formation Bio is a tech and AI driven pharma company differentiated by radically more efficient drug development. Advancements in AI and drug discovery are creating more candidate drugs than the industry can progress because of the high cost and time of clinical trials. Recognizing that this development bottleneck may ultimately limit the number of new medicines that can reach patients, Formation Bio, founded in 2016 as TrialSpark Inc., has built technology platforms, proces\u2026"
            }
        ]
                
    else:
        mock_results = [
            {
                "Role": "Senior Software Engineer",
                "Company": "TechCorp Inc.",
                "Location": "San Francisco, CA",
                "salary": "$150,000 - $180,000",
                "Description": "We're looking for a Senior Software Engineer to join our growing team. You'll be responsible for designing, developing and maintaining high-performance software applications.",
                "requirements": "5+ years of experience in software development, proficient in Python and JavaScript, experience with cloud services.",
                "Link": "https://example.com/jobs/senior-software-engineer",
                "date_posted": "2023-03-01"
            },
            {
                "Role": "Full Stack Developer",
                "Company": "InnovateTech",
                "Location": "San Francisco, CA",
                "salary": "$120,000 - $145,000",
                "Description": "Join our dynamic team to build cutting-edge web applications using modern frameworks and technologies.",
                "requirements": "3+ years experience with React, Node.js, and SQL/NoSQL databases. Strong problem-solving skills.",
                "Link": "https://example.com/jobs/full-stack-developer",
                "date_posted": "2023-03-02"
            },
            {
                "Role": "DevOps Engineer",
                "Company": "CloudSystems",
                "Location": "San Francisco, CA (Remote)",
                "salary": "$130,000 - $160,000",
                "Description": "Help us build and maintain our cloud infrastructure and deployment pipelines.",
                "requirements": "Experience with AWS/Azure, Docker, Kubernetes, and CI/CD pipelines. Knowledge of Infrastructure as Code.",
                "Link": "https://example.com/jobs/devops-engineer",
                "date_posted": "2023-03-03"
            },
            {
                "Role": "Machine Learning Engineer",
                "Company": "AI Innovations",
                "Location": "San Francisco, CA",
                "salary": "$160,000 - $190,000",
                "Description": "Design and implement machine learning models to solve complex business problems.",
                "requirements": "MS or PhD in Computer Science or related field. Experience with TensorFlow, PyTorch, and NLP.",
                "Link": "https://example.com/jobs/ml-engineer",
                "date_posted": "2023-03-04"
            },
            {
                "Role": "Product Manager",
                "Company": "ProductHub",
                "Location": "San Francisco, CA",
                "salary": "$140,000 - $170,000",
                "Description": "Lead product development from conception to launch, working closely with engineering and design teams.",
                "requirements": "3+ years of product management experience. Strong analytical and communication skills.",
                "Link": "https://example.com/jobs/product-manager",
                "date_posted": "2023-03-05"
            }
            ]
    return {"results": mock_results}

if __name__ == "__main__":
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)

