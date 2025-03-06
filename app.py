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


if __name__ == "__main__":
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)

