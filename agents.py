# agents.py
import os
import json
import requests
from dotenv import load_dotenv
from crewai import Agent, Task, Crew
from langchain_openai import ChatOpenAI
from langchain.tools import tool
from langchain.prompts import SystemMessagePromptTemplate, ChatPromptTemplate

# Load environment variables
load_dotenv()


class JobSearchTools:
    @tool("Job Search Tool")
    def search_jobs(input_json: str) -> str:
        """Search for job listings using the Adzuna API."""
        try:
            input_data = json.loads(input_json)
            role, location, num_results = input_data['role'], input_data['location'], input_data.get('num_results', 5)
        except (json.JSONDecodeError, KeyError):
            return "Error: Invalid input format. Expected: {'role': '...', 'location': '...', 'num_results': ...}"

        url = f"http://api.adzuna.com/v1/api/jobs/us/search/1?app_id={os.getenv('ADZUNA_APP_ID')}&app_key={os.getenv('ADZUNA_APP_KEY')}&results_per_page={num_results}&what={role}&where={location}&content-type=application/json"
        
        try:
            response = requests.get(url)
            response.raise_for_status()
            jobs = [{
                "Role": job.get("title", "N/A"),
                "Company": job.get("company", {}).get("display_name", "N/A"),
                "Location": job.get("location", {}).get("display_name", "N/A"),
                "Link": job.get("redirect_url", "#"),
                "Description": job.get("description", "No description available.")
            } for job in response.json().get('results', [])[:num_results]]
            
            save_results_to_file(jobs)
            return json.dumps(jobs, indent=4) if jobs else "No jobs found."
        except requests.exceptions.RequestException:
            return "Error fetching jobs."

def save_results_to_file(job_list):
    """Save job results as JSON in a file instead of plain text."""
    with open("task_output.txt", "w") as file:
        json.dump(job_list, file, indent=4)  


# Save a job to favorites
def save_job(job):
    with open("saved_jobs.json", "w") as file:
        json.dump(job, file, indent=4)

# Load saved job
def get_saved_job():
    try:
        with open("saved_jobs.json", "r") as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        return None


# Define the simpler system message
system_template = """You are an AI-powered job search assistant. You retrieve job listings from the Adzuna API. Ensure the jobs match the role title as closely as possible.

Rules:
1. Always respond in proper JSON format
2. Prioritize job listings that exactly match the user's specified role
3. Do not include duplicate job listings in your results
4. Do not make up information about job listings
5. Only use the tools provided to you

Example response format:
[
    {"Role": "Software Engineer", "Company": "Google", "Location": "San Francisco, CA", "Link": "https://job-link.com"},
    {"Role": "Data Scientist", "Company": "Meta", "Location": "Menlo Park, CA", "Link": "https://job-link.com"}
]

Now generate a response matching this structure."""

system_message_prompt = SystemMessagePromptTemplate.from_template(system_template)

# Create a chat prompt with only the system message
chat_prompt = ChatPromptTemplate.from_messages([system_message_prompt])

# Update your agent configuration
job_searcher_agent = Agent(
    role='Job Searcher',
    goal='Identify and provide relevant job opportunities based on user input.',
    backstory="An AI recruitment assistant that finds the best job listings based on role and location, leveraging real-time job data to optimize career searches.",
    llm=ChatOpenAI(
        model="gpt-4-turbo-preview"
    ),
    tools=[JobSearchTools().search_jobs],
    prompt=chat_prompt
)

job_researcher = Agent(
    role="Job Requirements Analyst",
    goal="Research and compile comprehensive requirements and qualifications for specific job titles",
    backstory="""You are an expert in job market analysis with extensive experience in identifying 
    key qualifications, skills, and requirements for various positions across different industries. 
    Your analysis is thorough and precise, focusing on both technical skills and soft skills required.""",
    verbose=True,
    allow_delegation=False,
    llm=ChatOpenAI(
        model="gpt-4-turbo-preview",
        temperature=0.7
    )
)

resume_evaluator = Agent(
    role="Professional Resume Evaluator",
    goal="Evaluate resumes against job requirements and provide detailed scoring and improvement suggestions",
    backstory="""You are a senior hiring manager and resume expert with years of experience in 
    evaluating candidates' resumes across multiple industries. You understand both ATS systems and 
    human evaluation factors. You provide honest, constructive feedback to help candidates improve.""",
    verbose=True,
    allow_delegation=False,
    llm=ChatOpenAI(
        model="gpt-4-turbo-preview",
        temperature=0.7
    )
)
