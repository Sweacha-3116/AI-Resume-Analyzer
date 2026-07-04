from flask import Flask, render_template, request, send_file
import os
import re
import pdfplumber

from reportlab.platypus import SimpleDocTemplate, Paragraph
from reportlab.lib.styles import getSampleStyleSheet

from skills import SKILLS
from database import (
    create_database,
    save_resume,
    get_all_resumes,
    get_dashboard_data
)
app = Flask(__name__)

UPLOAD_FOLDER = "uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
create_database()


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/upload", methods=["POST"])
def upload():

    # Resume Check
    if "resume" not in request.files:
        return "No Resume Selected"

    file = request.files["resume"]

    if file.filename == "":
        return "Please Select Resume"

    # Save Resume
    filepath = os.path.join(
        app.config["UPLOAD_FOLDER"],
        file.filename
    )

    file.save(filepath)

    # Job Description
    job_description = request.form.get(
        "job_description",
        ""
    )

    # Extract Text
    text = ""

    with pdfplumber.open(filepath) as pdf:

        for page in pdf.pages:

            page_text = page.extract_text()

            if page_text:
                text += page_text + "\n"

    # ==========================
    # Skills Detection
    # ==========================

    found_skills = []

    for skill in SKILLS:

        if skill.lower() in text.lower():
            found_skills.append(skill)

    missing_skills = []

    for skill in SKILLS:

        if skill not in found_skills:
            missing_skills.append(skill)

    # ==========================
    # ATS Score
    # ==========================

    total_skills = len(SKILLS)

    matched = len(found_skills)

    ats_score = int(
        (matched / total_skills) * 100
    )

    # ==========================
    # Resume Rating
    # ==========================

    if ats_score >= 90:

        rating = "🟢 Excellent"

    elif ats_score >= 70:

        rating = "🔵 Good"

    elif ats_score >= 50:

        rating = "🟡 Average"

    else:

        rating = "🔴 Poor"
            # ==========================
    # Email Detection
    # ==========================

    email_match = re.search(
        r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}",
        text
    )

    email = email_match.group() if email_match else "Not Found"

    # ==========================
    # Phone Detection
    # ==========================

    phone_match = re.search(r"\b\d{10}\b", text)

    phone = phone_match.group() if phone_match else "Not Found"

    # ==========================
    # Name Detection
    # ==========================

    lines = text.split("\n")

    name = "Not Found"

    for line in lines:
        line = line.strip()

        if len(line) > 2:
            name = line
            break

    # ==========================
    # Suggestions
    # ==========================

    suggestions = []

    if ats_score < 50:
        suggestions.append("Improve your ATS score.")

    if "GitHub" not in text:
        suggestions.append("Add your GitHub profile.")

    if "LinkedIn" not in text:
        suggestions.append("Add your LinkedIn profile.")

    # ==========================
    # Job Match
    # ==========================

    matched_skills = []

    required_skills = []

    for skill in SKILLS:

        if skill.lower() in job_description.lower():
            required_skills.append(skill)

        if (
            skill.lower() in job_description.lower()
            and skill in found_skills
        ):
            matched_skills.append(skill)

    missing_job_skills = []

    for skill in required_skills:

        if skill not in matched_skills:
            missing_job_skills.append(skill)

    if len(required_skills) > 0:

        job_match_score = int(
            (len(matched_skills) / len(required_skills)) * 100
        )

    else:

        job_match_score = 0
            # ==========================
    # Store Report Data
    # ==========================
        # ==========================
    # AI Feedback
    # ==========================

    feedback = []

    if ats_score >= 80:
        feedback.append("✅ Excellent ATS Score. Your resume is well optimized.")
    elif ats_score >= 60:
        feedback.append("👍 Good ATS Score. A few improvements can make it stronger.")
    else:
        feedback.append("⚠ ATS Score is low. Add more relevant technical skills.")

    if len(found_skills) >= 8:
        feedback.append("✅ Your resume contains a good number of technical skills.")
    else:
        feedback.append("⚠ Add more technical skills related to your field.")

    if job_match_score >= 80:
        feedback.append("✅ Your resume matches the job description very well.")
    elif job_match_score >= 50:
        feedback.append("👍 Your resume partially matches the job description.")
    else:
        feedback.append("⚠ Improve your resume according to the job description.")

    if email != "Not Found":
        feedback.append("✅ Professional email found.")
    else:
        feedback.append("⚠ Add a professional email address.")

    if phone != "Not Found":
        feedback.append("✅ Contact number found.")
    else:
        feedback.append("⚠ Add your contact number.")
            # ==========================
    # Resume Strength
    # ==========================

    if ats_score >= 90:
        strength = "⭐⭐⭐⭐⭐ Excellent"

    elif ats_score >= 75:
        strength = "⭐⭐⭐⭐ Very Good"

    elif ats_score >= 60:
        strength = "⭐⭐⭐ Good"

    elif ats_score >= 40:
        strength = "⭐⭐ Average"

    else:
        strength = "⭐ Needs Improvement"

    app.config["REPORT_DATA"] = {
        # ==========================

        "name": name,
        "email": email,
        "phone": phone,
        "ats_score": ats_score,
        "rating": rating,
        "strength": strength,
        "found_skills": found_skills,
        "missing_skills": missing_skills,
        "matched_skills": matched_skills,
        "missing_job_skills": missing_job_skills,
        "suggestions": suggestions,
        "feedback": feedback,
    }

    # ==========================
    # Show Result Page
    # ==========================
    # ==========================
    # Show Result Page
    # ==========================

    save_resume(
        name,
        email,
        phone,
        ats_score,
        job_match_score,
        rating
    )

    return render_template(
        "result.html",
        ats_score=ats_score,
        rating=rating,
        strength=strength,
        found_skills=found_skills,
        missing_skills=missing_skills,
        matched_skills=matched_skills,
        missing_job_skills=missing_job_skills,
        suggestions=suggestions,
        text=text,
        name=name,
        email=email,
        phone=phone,
        job_match_score=job_match_score,
        feedback=feedback,
    )


# ==========================
# Download PDF Report
# ==========================

@app.route("/download")
def download():

    report = app.config.get("REPORT_DATA")

    if not report:
        return "No Report Available"

    filename = "Resume_Report.pdf"

    doc = SimpleDocTemplate(filename)

    styles = getSampleStyleSheet()

    story = []

    # Title
    story.append(Paragraph("<b>AI Resume Analyzer Report</b>", styles["Heading1"]))
    story.append(Paragraph("<br/>", styles["BodyText"]))

    # Personal Details
    story.append(Paragraph(f"<b>Name:</b> {report['name']}", styles["BodyText"]))
    story.append(Paragraph(f"<b>Email:</b> {report['email']}", styles["BodyText"]))
    story.append(Paragraph(f"<b>Phone:</b> {report['phone']}", styles["BodyText"]))

    story.append(Paragraph("<br/>", styles["BodyText"]))

    # Scores
    story.append(Paragraph(f"<b>ATS Score:</b> {report['ats_score']}%", styles["BodyText"]))
    story.append(Paragraph(f"<b>Resume Rating:</b> {report['rating']}", styles["BodyText"]))
    story.append(Paragraph(f"<b>Resume Strength:</b> {report['strength']}", styles["BodyText"]))

    story.append(Paragraph("<br/>", styles["BodyText"]))

    # Skills Found
    story.append(Paragraph("<b>Skills Found</b>", styles["Heading2"]))

    for skill in report["found_skills"]:
        story.append(Paragraph("• " + skill, styles["BodyText"]))

    story.append(Paragraph("<br/>", styles["BodyText"]))

    # Missing Skills
    story.append(Paragraph("<b>Missing Skills</b>", styles["Heading2"]))

    for skill in report["missing_skills"]:
        story.append(Paragraph("• " + skill, styles["BodyText"]))

    story.append(Paragraph("<br/>", styles["BodyText"]))

    # Suggestions
    story.append(Paragraph("<b>Suggestions</b>", styles["Heading2"]))

    for suggestion in report["suggestions"]:
        story.append(Paragraph("• " + suggestion, styles["BodyText"]))

    story.append(Paragraph("<br/>", styles["BodyText"]))

    # Feedback
    story.append(Paragraph("<b>AI Feedback</b>", styles["Heading2"]))

    for item in report["feedback"]:
        story.append(Paragraph(item, styles["BodyText"]))

    doc.build(story)

    return send_file(filename, as_attachment=True)

@app.route("/history")
def history():

    resumes = get_all_resumes()

    return render_template(
        "history.html",
        resumes=resumes
    )


@app.route("/dashboard")
def dashboard():

    data = get_dashboard_data()

    total = data[0] if data[0] else 0
    avg_ats = round(data[1], 1) if data[1] else 0
    highest = data[2] if data[2] else 0
    avg_match = round(data[3], 1) if data[3] else 0

    return render_template(
        "dashboard.html",
        total=total,
        avg_ats=avg_ats,
        highest=highest,
        avg_match=avg_match
    )

    resumes = get_all_resumes()

    return render_template(
        "history.html",
        resumes=resumes
    )



    report = app.config.get("REPORT_DATA")

    if not report:
        return "No Report Available"

    filename = "Resume_Report.pdf"

    doc = SimpleDocTemplate(filename)

    styles = getSampleStyleSheet()

    story = []

    story.append(Paragraph("<b>AI Resume Analyzer Report</b>", styles["Heading1"]))
    story.append(Paragraph(f"<b>Name:</b> {report['name']}", styles["BodyText"]))
    story.append(Paragraph(f"<b>Email:</b> {report['email']}", styles["BodyText"]))
    story.append(Paragraph(f"<b>Phone:</b> {report['phone']}", styles["BodyText"]))

    story.append(Paragraph("<br/>", styles["BodyText"]))

    story.append(Paragraph(f"<b>ATS Score:</b> {report['ats_score']}%", styles["BodyText"]))
    story.append(Paragraph(f"<b>Resume Rating:</b> {report['rating']}", styles["BodyText"]))

    story.append(Paragraph("<br/>", styles["BodyText"]))

    story.append(Paragraph("<b>Skills Found:</b>", styles["Heading2"]))

    for skill in report["found_skills"]:
        story.append(Paragraph(skill, styles["BodyText"]))

    story.append(Paragraph("<br/>", styles["BodyText"]))

    story.append(Paragraph("<b>Missing Skills:</b>", styles["Heading2"]))

    for skill in report["missing_skills"]:
        story.append(Paragraph(skill, styles["BodyText"]))

    story.append(Paragraph("<br/>", styles["BodyText"]))

    story.append(Paragraph("<b>Suggestions:</b>", styles["Heading2"]))

    for suggestion in report["suggestions"]:
        story.append(Paragraph(suggestion, styles["BodyText"]))

    doc.build(story)

    return send_file(filename, as_attachment=True)


# ==========================
# Run App
# ==========================

if __name__ == "__main__":
    app.run(debug=True)
        