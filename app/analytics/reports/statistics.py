import streamlit as st
import pandas as pd
import plotly.express as px
from collections import Counter

from app.database.mongodb.connection import mongo_db


INVALID_SCHOOL_KEYWORDS = {
    "achievement",
    "achievements",
    "award",
    "awards",
    "gpa",
    "cgpa",
    "cumulative",
    "coursework",
    "projects",
    "skills",
    "summary",
    "profile",
    "experience",
    "internship",
    "certification",
    "certificate",
    "scholarship",
    "dean",
    "honor",
    "honours",
}


def normalize_school_name(name: str) -> str | None:
    if not name:
        return None

    school = name.strip()

    lower = school.lower()

    if any(keyword in lower for keyword in INVALID_SCHOOL_KEYWORDS):
        return None

    return school

def render_statistics_page():
    st.title("Recruitment Analytics & Statistics")
    
    st.caption(
        "Interactive analytics generated from processed resumes and job descriptions."
    )
    
    overview_tab, skills_tab, education_tab = st.tabs(
        [
            "Overview",
            "Skills",
            "Education"
        ]
    )
    with st.spinner("Loading recruitment analytics..."):

        db = mongo_db.get_db()

        total_jobs = db["jobs"].count_documents({})
        total_candidates = db["candidates"].count_documents({})
        total_resumes = db["resumes"].count_documents({})
    
    with overview_tab:

        col1, col2, col3 = st.columns(3)

        col1.metric(
            "Total Jobs",
            total_jobs
        )

        col2.metric(
            "Candidates",
            total_candidates
        )

        col3.metric(
            "Processed Resumes",
            total_resumes
        )
        
        candidate_docs = list(
            db["candidates"].find({}, {"skills": 1})
        )

        skill_counts = [
            len(c.get("skills", []))
            for c in candidate_docs
        ]

        avg_skills = (
            sum(skill_counts) / len(skill_counts)
            if skill_counts
            else 0
        )

        st.metric(
            "Average Skills per Candidate",
            f"{avg_skills:.1f}"
        )
    
        st.divider()
    
    with skills_tab:
        st.subheader("Top Skills Distribution in Talent Pool")
        candidates = list(db["candidates"].find({}, {"skills": 1}))
        
        all_skills = [skill.strip().title() for c in candidates for skill in c.get("skills", [])]
            
        if all_skills:
            skill_counts = Counter(all_skills)
            df_skills = pd.DataFrame(skill_counts.most_common(15), columns=["Skill", "Count"])
            df_skills = df_skills.sort_values(by="Count", ascending=True)  # Sort ascending for horizontal bar chart
            
            fig = px.bar(df_skills, x="Count", y="Skill", orientation='h', color="Count", color_continuous_scale="Blues")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("No candidate skills available yet. Upload resumes to generate analytics.")
            
        st.subheader("Top Required Skills")
        
        job_docs = list(
            db["jobs"].find({}, {"required_skills": 1})
        )

        required_skills = [
            skill.strip().title()
            for job in job_docs
            for skill in job.get("required_skills", [])
        ]

        if required_skills:

            required_counter = Counter(required_skills)

            df_required = pd.DataFrame(
                required_counter.most_common(15),
                columns=["Skill", "Count"]
            )

            df_required = df_required.sort_values(
                by="Count",
                ascending=True
            )

            fig = px.bar(
                df_required,
                x="Count",
                y="Skill",
                orientation="h",
                color="Count",
                color_continuous_scale="Greens"
            )

            st.plotly_chart(
                fig,
                use_container_width=True
            )

        else:
            st.warning("No job skills available. Create a job description first.")

    with education_tab:

        st.subheader("Top Universities")

        education_list = []

        parsed_count = 0
        unknown_count = 0

        for candidate in db["candidates"].find({}, {"education": 1}):

            for edu in candidate.get("education", []):

                school = normalize_school_name(
                    edu.get("school")
                )

                if school:
                    parsed_count += 1
                    education_list.append(school)
                else:
                    unknown_count += 1

        col1, col2 = st.columns(2)

        col1.metric(
            "Valid Schools",
            parsed_count
        )

        col2.metric(
            "Filtered Entries",
            unknown_count
        )

        st.caption(
            "Education statistics after filtering noisy extraction results."
        )


        if education_list:

            edu_counter = Counter(education_list)

            df = pd.DataFrame(
                edu_counter.most_common(10),
                columns=[
                    "School",
                    "Candidates"
                ]
            )

            fig = px.bar(
                df,
                x="Candidates",
                y="School",
                orientation="h",
                color="Candidates",
                color_continuous_scale="Oranges"
            )

            st.plotly_chart(
                fig,
                use_container_width=True
            )

        else:
            st.warning("No education data available. Upload more resumes to generate insights.")