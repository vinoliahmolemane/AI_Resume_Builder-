import streamlit as st
from utils import (
    generate_resume,
    save_feedback,
    get_templates,
    html_to_pdf,
    html_to_docx,
    suggest_keywords
)
import os

st.set_page_config(page_title="AI Resume Builder", layout="centered")

st.title("🤖 AI Resume Builder")
st.write("Create a customized, ATS-friendly resume in minutes.")

# Sidebar
st.sidebar.header("Choose Template & Theme")
template_name = st.sidebar.selectbox("Resume Style", get_templates())
theme = st.sidebar.selectbox("Theme", ["Light", "Dark"])

export_format = st.sidebar.radio("Export Format", ["PDF", "DOCX", "HTML"])
enable_job_match = st.sidebar.checkbox("Enable Job Description Matching")
enable_suggestions = st.sidebar.checkbox("Enable Smart Suggestions")

# User inputs
st.subheader("📝 Enter Your Information")
name = st.text_input("Full Name")
email = st.text_input("Email")
phone = st.text_input("Phone Number")
linkedin = st.text_input("LinkedIn URL")
github = st.text_input("GitHub URL")
summary = st.text_area("Professional Summary")
skills = st.text_area("Skills (comma separated)")
experience = st.text_area("Work Experience")
education = st.text_area("Education")

job_desc = ""
if enable_job_match:
    st.subheader("📄 Paste Job Description")
    job_desc = st.text_area("Job Description")

# Smart Suggestions
if enable_suggestions and job_desc:
    st.subheader("💡 Smart Suggestions")
    suggestions = suggest_keywords(job_desc, skills)
    if suggestions:
        st.info(f"Consider adding these relevant keywords to improve your match: {', '.join(suggestions)}")
    else:
        st.success("Your resume already contains most of the relevant keywords!")

if st.button("Generate Resume"):
    if not name or not email:
        st.error("Please enter at least your name and email to generate a resume.")
    else:
        resume_html, ats_score = generate_resume(
            name, email, phone, linkedin, github,
            summary, skills, experience, education,
            template=template_name,
            job_description=job_desc,
            theme=theme
        )
        os.makedirs("resumes", exist_ok=True)
        html_path = f"resumes/{name.replace(' ', '_').lower()}_{template_name}.html"
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(resume_html)

        # Export
        if export_format == "PDF":
            pdf_path = html_path.replace(".html", ".pdf")
            err = html_to_pdf(html_path, pdf_path)
            if err:
                st.warning("PDF generation failed. Downloading HTML instead.")
                export_format = "HTML"
            else:
                with open(pdf_path, "rb") as f:
                    st.download_button("Download PDF", f, file_name=os.path.basename(pdf_path), mime="application/pdf")
        elif export_format == "DOCX":
            docx_path = html_path.replace(".html", ".docx")
            html_to_docx(html_path, docx_path)
            with open(docx_path, "rb") as f:
                st.download_button("Download DOCX", f, file_name=os.path.basename(docx_path), mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
        else:
            st.download_button("Download HTML", resume_html.encode('utf-8'), file_name=os.path.basename(html_path), mime="text/html")

        # Preview
        st.subheader("🔍 Resume Preview")
        st.components.v1.html(resume_html, height=600, scrolling=True)

        if enable_job_match and job_desc:
            st.success(f"Resume matches **{ats_score:.2f}%** of job description keywords.")

# Feedback
st.subheader("💬 Provide Feedback")
user_feedback = st.text_area("Was this resume helpful? Any improvements?")
if st.button("Submit Feedback"):
    if not name:
        st.error("Please enter your name before submitting feedback.")
    elif not user_feedback.strip():
        st.error("Please enter feedback before submitting.")
    else:
        save_feedback(name, user_feedback)
        st.success("Thank you for your feedback!")
