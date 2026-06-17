import streamlit as st
import pandas as pd
import plotly.express as px
from loguru import logger

from app.database.mongodb.connection import mongo_db
from app.services.matching_service import MatchingService


@st.cache_resource
def get_matching_service():
    return MatchingService()


def render_matching_page():
    st.title("AI Candidate Matching Engine")
    
    db = mongo_db.get_db()
    jobs = list(db["jobs"].find({}, {"title": 1, "_id": 1}).sort("created_at", -1))
    
    if not jobs:
        st.warning("No jobs available in the system. Please create a Job Description first via API.")
        return
        
    job_options = {str(job["_id"]): job["title"] for job in jobs}
    
    st.markdown("### Job Selection")
    selected_job_id = st.selectbox(
        "Select a Job to find the best matching candidates:", 
        options=list(job_options.keys()), 
        format_func=lambda x: job_options[x]
    )
    
    if st.button("Find Best Candidates", type="primary"):
        with st.spinner("Analyzing semantics, calculating vector distances and analyzing skill gaps..."):
            try:
                matching_svc = get_matching_service()
                match_response = matching_svc.match_candidates_for_job(selected_job_id)
                results = match_response.results
                
                if not results:
                    st.info("No candidates found that meet the similarity threshold.")
                else:
                    st.success(f"Found {len(results)} highly matching candidates!")
                    
                    display_data = []
                    for rank, cand in enumerate(results, 1):
                        profile = cand.candidate_profile
                        display_data.append({
                            "Rank": rank,
                            "Name": profile.personal_info.get("name", "Unknown Candidate"),
                            "Email": profile.personal_info.get("email", "N/A"),
                            "Match Score": cand.similarity_score,
                            "Skill Gaps (Missing)": ", ".join(cand.skill_gaps) if cand.skill_gaps else "Perfect Match"
                        })
                        
                    df_results = pd.DataFrame(display_data)
                    
                    st.markdown("### Top Candidates Score Comparison")
                    fig = px.bar(
                        df_results.head(5), x="Name", y="Match Score", 
                        color="Match Score", color_continuous_scale="Greens", range_y=[0, 100]
                    )
                    st.plotly_chart(fig, use_container_width=True)
                    
                    st.markdown("### Detailed Candidate Ranking & Skill Gaps")
                    st.dataframe(
                        df_results, 
                        column_config={"Match Score": st.column_config.ProgressColumn("Match Score (%)", format="%.2f", min_value=0, max_value=100)},
                        hide_index=True, use_container_width=True
                    )
            except Exception as e:
                logger.error(f"Error during Streamlit matching process: {e}")
                st.error(f"An error occurred: {str(e)}")