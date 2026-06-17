import sys
from pathlib import Path
import streamlit as st
from loguru import logger

root_path = Path(__file__).parent.parent.parent.parent
if str(root_path) not in sys.path:
    sys.path.insert(0, str(root_path))

from app.database.mongodb.connection import mongo_db
from app.analytics.reports import statistics, matching_view

@st.cache_resource
def init_db():
    try:
        mongo_db.connect()
        return True
    except Exception as e:
        st.error(f"Failed to connect to Database: {e}")
        return False

init_db()

st.set_page_config(page_title="AI Recruitment Dashboard", page_icon="📊", layout="wide")

st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", ["Analytics & Statistics", "Candidate Matching"])

if page == "Analytics & Statistics":
    statistics.render_statistics_page()
elif page == "Candidate Matching":
    matching_view.render_matching_page()