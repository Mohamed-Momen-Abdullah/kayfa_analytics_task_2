import streamlit as st
import pandas as pd
import plotly.express as px
import pymongo
import os

# --- 1. CONFIG & SETUP ---
st.set_page_config(page_title="Kayfa Analytics Dashboard", layout="wide")

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

# --- GLOBAL CHART LABELS ---
CHART_LABELS = {
    "cluster_name": "Segment",
    "avg_grade": "Average Grade",
    "category": "Category",
    "attendance_rate": "Attendance Rate",
    "group_name": "Group Name",
    "type": "Assessment Type",
    "score": "Score",
    "course_name": "Course Name",
    "video_duration_mins": "Video Duration (mins)",
    "forum_post": "Forum Posts",
    "concept_name": "Concept Name",
    "failure_rate": "Failure Rate",
    "course_id": "Course ID",
    "assessment_id": "Assessment ID",
    "avg_score": "Average Score",
    "is_late": "Submitted Late",
    "session_datetime": "Session
