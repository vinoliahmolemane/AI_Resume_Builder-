import os
import json
import re
from jinja2 import Environment, FileSystemLoader
from xhtml2pdf import pisa
from docx import Document
from bs4 import BeautifulSoup
import cohere

COHERE_API_KEY = os.getenv("COHERE_API_KEY")
cohere_client = cohere.Client(COHERE_API_KEY) if COHERE_API_KEY else None

def get_templates():
    return [f.split('.')[0] for f in os.listdir("templates") if f.endswith(".html")]

def generate_resume(name, email, phone, linkedin, github, summary, skills, experience, education,
                    template="classic", job_description="", theme="Light"):
    env = Environment(loader=FileSystemLoader("templates"))
    template_file = env.get_template(f"{template}.html")

    skills_list = [s.strip() for s in skills.split(",") if s.strip()]
    context = {
        "name": name,
        "email": email,
        "phone": phone,
        "linkedin": linkedin,
        "github": github,
        "summary": summary,
        "skills": skills_list,
        "experience": experience,
        "education": education,
        "theme": theme
    }

    resume_html = template_file.render(context)

    # Use Cohere to optimize job description keywords if possible
    if cohere_client and job_description:
        ats_score = cohere_keyword_match(cohere_client, skills_list, job_description)
    else:
        ats_score = simple_keyword_match(skills_list, job_description) if job_description else 0

    return resume_html, ats_score

def simple_keyword_match(skills, job_desc):
    job_keywords = re.findall(r'\b\w+\b', job_desc.lower())
    matched = [skill.lower() for skill in skills if skill.lower() in job_keywords]
    return (len(matched) / len(skills)) * 100 if skills else 0

def cohere_keyword_match(client, skills, job_desc):
    # Basic prompt to count matched keywords
    prompt = f"Skills: {', '.join(skills)}\nJob Description: {job_desc}\n" \
             "Count how many of the skills appear in the job description and provide the percentage match."

    response = client.generate(
        model="command-xlarge-nightly",
        prompt=prompt,
        max_tokens=20,
        temperature=0.0,
        stop_sequences=["--"]
    )
    # Parse percentage from response text (fallback to simple match)
    try:
        text = response.generations[0].text.strip()
        # Try to extract a number from response
        import re
        match = re.search(r'(\d+\.?\d*)%', text)
        if match:
            return float(match.group(1))
        else:
            return simple_keyword_match(skills, job_desc)
    except Exception:
        return simple_keyword_match(skills, job_desc)

def save_feedback(name, feedback):
    data = {"name": name, "feedback": feedback}
    os.makedirs("data", exist_ok=True)
    with open("data/feedback.json", "a", encoding="utf-8") as f:
        json.dump(data, f)
        f.write("\n")

def html_to_pdf(source_html_path, output_pdf_path):
    with open(source_html_path, 'r', encoding='utf-8') as html_file:
        html_content = html_file.read()
    with open(output_pdf_path, 'wb') as pdf_file:
        pisa_status = pisa.CreatePDF(src=html_content, dest=pdf_file)
    return pisa_status.err

def html_to_docx(source_html_path, output_docx_path):
    with open(source_html_path, 'r', encoding='utf-8') as html_file:
        html_content = html_file.read()
    soup = BeautifulSoup(html_content, 'html.parser')
    text = soup.get_text(separator="\n")
    doc = Document()
    doc.add_paragraph(text)
    doc.save(output_docx_path)
