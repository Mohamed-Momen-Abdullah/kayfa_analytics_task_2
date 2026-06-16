import streamlit as st
import pandas as pd
import plotly.express as px
import pymongo
import os

# --- 1. CONFIG & SETUP ---
st.set_page_config(page_title="Kayfa Analytics Dashboard", layout="wide")

# Fixed the deprecation warning here by using width="stretch" instead of use_container_width
st.sidebar.image("kayfa_logo_light.png", width="stretch")

st.markdown(
    """
    <style>
        [data-testid="stSidebarUserContent"] {
            position: absolute !important; top: 2rem !important; left: 0px !important;
            width: 100% !important; padding-left: 1.5rem !important; padding-right: 1.5rem !important;
            z-index: 999 !important;
        }
        [data-testid="stSidebarNav"] { padding-top: 7rem !important; }
        [data-testid="stHeader"] { background: transparent !important; }
        .stApp {
            background-image: linear-gradient(to bottom, rgba(14, 165, 233, 0.5) 0%, transparent 70%);
            background-attachment: fixed;
        }
        .insight-box {
            background-color: rgba(59, 130, 246, 0.1); border-left: 4px solid #3b82f6;
            padding: 15px; border-radius: 4px; margin-bottom: 20px;
        }
    </style>
    """, unsafe_allow_html=True
)

# --- 2. LOAD ALL DATA FROM MONGODB ---
@st.cache_resource
def init_connection():
    return pymongo.MongoClient(st.secrets["mongo"]["uri"])

client = init_connection()

@st.cache_data(ttl=600)
def load_all_data():
    db = client["kayfa_analytics"]
    
    # Load all tables
    df = pd.DataFrame(list(db.master_roster.find({}, {'_id': 0})))
    concept_stats = pd.DataFrame(list(db.concept_stats.find({}, {'_id': 0})))
    clean_grades = pd.DataFrame(list(db.clean_grades.find({}, {'_id': 0})))
    assignments = pd.DataFrame(list(db.assignments.find({}, {'_id': 0})))
    attendance = pd.DataFrame(list(db.attendance.find({}, {'_id': 0})))
    concepts = pd.DataFrame(list(db.concepts.find({}, {'_id': 0})))
    q12_data = pd.DataFrame(list(db.q12_data.find({}, {'_id': 0})))
    group_trends = pd.DataFrame(list(db.group_trends.find({}, {'_id': 0})))
    
    # Restore datetime objects for time-series charts
    attendance['session_datetime'] = pd.to_datetime(attendance['session_datetime
