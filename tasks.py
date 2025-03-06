# tasks.py
import json
from crewai import Task
from agents import job_searcher_agent, job_researcher, resume_evaluator

def job_search_task(user_role, user_location, num_results=5):
    return Task(
        description=f"Find {num_results} job opportunities for '{user_role}' in '{user_location}'.",
        agent=job_searcher_agent,
        function=lambda _: job_searcher_agent.tools[0](json.dumps({"role": user_role, "location": user_location, "num_results": num_results})),
        expected_output="A JSON string with job listings."
    )


def jd_research_task(job_title, job_description):
    research_prompt = f"""
    Research the key qualifications, skills, and requirements for the position of "{job_title}" 
    with this job description:
    {job_description}.
    
    In your analysis, include:
    1. Essential technical skills and qualifications
    2. Required education and experience levels
    3. Important soft skills
    4. Industry-specific knowledge or certifications
    5. Current trends or emerging skills in demand for this role
    
    Format your response as a structured report with clear sections. Be comprehensive but focus on 
    the most important qualifications that employers typically look for.
    """
    
    return Task(
        description=research_prompt,
        agent=job_researcher,
        expected_output="A comprehensive report on job requirements"
    )

# Create evaluation task
def evaluation_task(job_requirements, resume_text):
    evaluation_prompt = f"""
    You are an AI Resume Evaluator with expertise in ATS compliance, clarity, and impactful writing.
    
    First, review these job requirements:
    {job_requirements}
    
    Now, evaluate the following resume against these requirements:
    {resume_text}
    
    Provide your evaluation with:
    1. **Overall Score (out of 10)**
    2. **Match Assessment** (How well does the resume match the job requirements?)
    3. **Strengths** (What is well-written and aligns with the requirements?)
    4. **Weaknesses** (What needs improvement or is missing compared to the requirements?)
    5. **ATS Optimization Tips** (How can it rank better in ATS systems?)
    6. **Improvement Recommendations** (Specific suggestions to better align with the job requirements)
    
    Be specific, honest, and constructive in your feedback, focusing on actionable improvements.
    """
    
    return Task(
        description=evaluation_prompt,
        agent=resume_evaluator,
        expected_output="A detailed resume evaluation report"
        # context=[job_requirements]
    )

