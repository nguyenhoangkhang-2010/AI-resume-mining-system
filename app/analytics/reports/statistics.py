import streamlit as st
import pandas as pd
import plotly.express as px
from collections import Counter

from app.database.mongodb.connection import mongo_db


def render_statistics_page():
    st.title("Recruitment Analytics & Statistics")
    
    db = mongo_db.get_db()
    
    total_jobs = db["jobs"].count_documents({})
    total_candidates = db["candidates"].count_documents({})
    total_resumes = db["resumes"].count_documents({})
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Jobs Created", total_jobs)
    col2.metric("Total Qualified Candidates", total_candidates)
    col3.metric("Resumes Processed", total_resumes)
    
    st.markdown("---")
    
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
        st.info("Not enough skill data to display distribution. Please upload more resumes.")