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
    "session_datetime": "Session Date",
    "is_present": "Present Rate",
    "age_band": "Age Band",
    "failed_concepts": "Failed Concepts",
    "group_id": "Group ID",
    "risk_score": "Risk Score",
    "full_name": "Student Name",
    "date": "Date"
}

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
    attendance['session_datetime'] = pd.to_datetime(attendance['session_datetime'])
    concepts['timestamp'] = pd.to_datetime(concepts['timestamp'])
    group_trends['date'] = pd.to_datetime(group_trends['date'])
    
    return df, concept_stats, clean_grades, assignments, attendance, concepts, q12_data, group_trends

df, concept_stats, clean_grades, assignments, attendance, concepts, q12_data, group_trends = load_all_data()

color_map = {"Cluster 3": "#4B7FA1", "Cluster 2": "#D56D58", "Cluster 1": "#6B9080", "Cluster 0": "#F4A261"}

# --- 3. DASHBOARD PAGES ---

def page_main_dashboard():
    col_text, col_logo = st.columns([4, 1])
    with col_text:
        st.title("Kayfa-Internship Task 2: Data Analysis and Recommendations")
        st.markdown("An interactive exploratory analysis identifying curriculum weak spots and at-risk student profiles.")
    with col_logo:
        if os.path.exists("kayfa_logo_light.png"):
            st.image("kayfa_logo_light.png", width="stretch")
            
    st.divider()

    c1, c2, c3 = st.columns(3)
    c1.metric("Total Enrolled Students", f"{len(df):,}")
    c2.metric("Platform Average Grade", f"{df['avg_grade'].mean():.1f}%")
    c3.metric("Platform Attendance Rate", f"{df['attendance_rate'].mean() * 100:.1f}%")
    
    st.markdown("<br>", unsafe_allow_html=True)
    c4, c5, c6 = st.columns(3)
    c4.metric("Severely At-Risk Students", f"{len(df[df['cluster_name'] == 'Cluster 2']):,}", "Cluster 2 Segment", delta_color="inverse")
    c5.metric("Lowest Performing Course", "Digital Marketing", "Urgent curriculum review needed", delta_color="off")
    c6.metric("Highest Failure Concept", "Recursion", "85.3% Failure Rate", delta_color="inverse")
    st.divider()

    tab1, tab2 = st.tabs(["📊 Segment Distributions", "📈 Grade Distribution"])
    with tab1:
        pie_counts = df['cluster_name'].value_counts().reset_index()
        pie_counts.columns = ['Segment', 'Count']
        st.plotly_chart(px.pie(pie_counts, values='Count', names='Segment', hole=0.4, color='Segment', color_discrete_map=color_map, labels=CHART_LABELS), width="stretch")
    with tab2:
        st.plotly_chart(px.box(df, x="category", y="avg_grade", color="category", labels=CHART_LABELS), width="stretch")

def page_q1():
    st.title("1️⃣ Q1: Attendance Anomalies")
    st.markdown("What is the attendance rate per group, and which groups sit well below the platform average?")
    platform_avg = df['attendance_rate'].mean()
    group_att = df.groupby('group_name')['attendance_rate'].mean().reset_index().sort_values('attendance_rate')
    fig = px.bar(group_att, x='attendance_rate', y='group_name', orientation='h', color='attendance_rate', color_continuous_scale="RdYlGn", labels=CHART_LABELS)
    fig.add_vline(x=platform_avg, line_dash="dash", line_color="white", annotation_text=f"Avg: {platform_avg:.1%}")
    fig.update_layout(xaxis_tickformat='.1%')
    st.plotly_chart(fig, width="stretch")
    st.markdown("<div class='insight-box'><strong>Insight:</strong> The platform average attendance is 76.8%. Group 10 (C007) and Group 07 (C005) are severe underperformers, dropping to ~65% and ~60% respectively.</div>", unsafe_allow_html=True)

def page_q2():
    st.title("2️⃣ Q2: Score Volatility")
    st.markdown("How are scores distributed by assessment type? Where is performance most volatile?")
    st.plotly_chart(px.box(clean_grades, x='type', y='score', color='type', labels=CHART_LABELS), width="stretch")
    st.markdown("<div class='insight-box'><strong>Insight:</strong> Assignments show the highest volatility and the lowest overall performance, indicating students struggle significantly more with take-home assignments than structured exams.</div>", unsafe_allow_html=True)

def page_q3():
    st.title("3️⃣ Q3: Course Grade Spread")
    st.markdown("Which course has the highest and lowest average grade?")
    course_order = df.groupby('course_name')['avg_grade'].median().sort_values().index
    st.plotly_chart(px.box(df, x='course_name', y='avg_grade', color='course_name', category_orders={'course_name': course_order}, labels=CHART_LABELS), width="stretch")
    st.markdown("<div class='insight-box'><strong>Insight:</strong> Machine Learning Basics has the highest median grade (~73), while Digital Marketing is the lowest performing by a wide margin (median below 60).</div>", unsafe_allow_html=True)

def page_q4():
    st.title("4️⃣ Q4: Attendance vs Grades")
    st.markdown("Is there a relationship between a student’s attendance rate and their average grade?")
    corr = df['attendance_rate'].corr(df['avg_grade'])
    fig = px.scatter(df, x='attendance_rate', y='avg_grade', opacity=0.7, labels=CHART_LABELS)
    fig.update_layout(xaxis_tickformat='.0%')
    st.plotly_chart(fig, width="stretch")
    st.markdown(f"<div class='insight-box'><strong>Insight:</strong> There is a moderate positive relationship (Pearson correlation: {corr:.2f}). As attendance increases, grades generally trend higher, but simply showing up doesn't guarantee a perfect score.</div>", unsafe_allow_html=True)

def page_q5():
    st.title("5️⃣ Q5: Engagement Drivers")
    st.markdown("Does engagement relate to academic performance?")
    corr_matrix = df[['avg_grade', 'attendance_rate', 'video_duration_mins', 'forum_post']].corr().round(2)
    # Rename index and columns to avoid snake_case on the heatmap axes
    corr_matrix.columns = [CHART_LABELS.get(c, c) for c in corr_matrix.columns]
    corr_matrix.index = [CHART_LABELS.get(c, c) for c in corr_matrix.index]
    st.plotly_chart(px.imshow(corr_matrix, text_auto=True, color_continuous_scale='RdBu_r', aspect="auto"), width="stretch")
    st.markdown("<div class='insight-box'><strong>Insight:</strong> Attendance is the strongest predictor of grades (0.47), followed closely by video watch time (0.40). Simply logging into the platform is the weakest indicator.</div>", unsafe_allow_html=True)

def page_q6():
    st.title("6️⃣ Q6: Curriculum Weak Spots")
    st.markdown("Which concepts have the highest failure rate?")
    top_failed = concept_stats[concept_stats['total_attempts'] > 15].sort_values('failure_rate', ascending=False).head(10)
    fig = px.bar(top_failed, x='concept_name', y='failure_rate', color='course_id', text_auto='.1%', labels=CHART_LABELS)
    fig.update_layout(yaxis_tickformat='.0%')
    st.plotly_chart(fig, width="stretch")
    st.markdown("<div class='insight-box'><strong>Insight:</strong> 'Recursion' (Course C002) is the absolute biggest curriculum weak spot, boasting a massive 85.3% failure rate.</div>", unsafe_allow_html=True)

def page_q7():
    st.title("7️⃣ Q7: Mastery Over Time")
    st.markdown("For that weakest concept (Recursion), how does cohort mastery change over time?")
    weak_data = concepts[concepts['concept_name'] == 'Recursion'].sort_values('timestamp')
    mastery_trend = weak_data.groupby('assessment_id').agg(avg_score=('score_pct', 'mean'), date=('timestamp', 'min')).sort_values('date').reset_index()
    st.plotly_chart(px.line(mastery_trend, x='assessment_id', y='avg_score', markers=True, labels=CHART_LABELS), width="stretch")
    st.markdown("<div class='insight-box'><strong>Insight:</strong> Mastery remains completely stagnant. Across three different assessments throughout the term, the average score hovers in a totally flat line (~45%).</div>", unsafe_allow_html=True)

def page_q8():
    st.title("8️⃣ Q8: The Cost of Procrastination")
    st.markdown("Do students who submit assignments late tend to score lower?")
    assign_grades = assignments.merge(clean_grades[['student_id', 'assessment_id', 'score']], on=['student_id', 'assessment_id'], how='inner')
    st.plotly_chart(px.box(assign_grades, x='is_late', y='score', color='is_late', labels=CHART_LABELS), width="stretch")
    st.markdown("<div class='insight-box'><strong>Insight:</strong> Yes, late submitters score significantly lower. The median score for on-time submissions is roughly 67, while late submissions drop to 62.</div>", unsafe_allow_html=True)

def page_q9():
    st.title("9️⃣ Q9: The Holiday Dip")
    st.markdown("Plot attendance over the 6-month term. Is there a window where the cohort dips at once?")
    weekly_att = attendance.groupby(pd.Grouper(key='session_datetime', freq='W-MON'))['is_present'].mean().reset_index()
    fig = px.line(weekly_att, x='session_datetime', y='is_present', markers=True, labels=CHART_LABELS)
    fig.update_layout(yaxis_tickformat='.0%')
    st.plotly_chart(fig, width="stretch")
    st.markdown("<div class='insight-box'><strong>Insight:</strong> A massive dip occurs in mid-March 2026, where attendance plummets from 80% to 52%. This perfectly aligns with the end of Ramadan and the Eid al-Fitr holidays.</div>", unsafe_allow_html=True)

def page_q10():
    st.title("🔟 Q10: Demographics & Age")
    st.markdown("Bucket students into age bands. Does age relate to outcomes here?")
    bins = [0, 19, 24, 29, 100]
    labels = ['Under 20', '20-24', '25-29', '30+']
    df['age_band'] = pd.cut(df['age'], bins=bins, labels=labels)
    age_stats = df.groupby('age_band')[['avg_grade', 'attendance_rate']].mean().reset_index()
    st.plotly_chart(px.bar(age_stats, x='age_band', y='avg_grade', color='attendance_rate', text_auto='.1f', labels=CHART_LABELS), width="stretch")
    st.markdown("<div class='insight-box'><strong>Insight:</strong> Older adult learners are more reliable. The 30+ age band jumps to the highest attendance rate (over 80%) and the highest average grade (74.5).</div>", unsafe_allow_html=True)

def page_q11():
    st.title("1️⃣1️⃣ Q11: Behavioral Segmentation")
    st.markdown("Describe the segments based on attendance, engagement, grades, and failed concepts.")
    features = ['attendance_rate', 'avg_grade', 'video_duration_mins', 'failed_concepts']
    cluster_profile = df.groupby('cluster_name')[features].mean().reset_index()
    cluster_melted = cluster_profile.melt(id_vars='cluster_name', var_name='Metric', value_name='Average Value')
    # Clean the snake_case from the melted column
    cluster_melted['Metric'] = cluster_melted['Metric'].replace(CHART_LABELS)
    st.plotly_chart(px.bar(cluster_melted, x='cluster_name', y='Average Value', color='Metric', barmode='group', labels=CHART_LABELS), width="stretch")
    st.markdown("<div class='insight-box'><strong>Insight:</strong> Cluster 2 is the 'Disengaged At-Risk' cohort (lowest attendance, massive failed concepts). Cluster 3 represents our 'High-Achievers' (high attendance, high grades, low failures).</div>", unsafe_allow_html=True)

def page_q12():
    st.title("1️⃣2️⃣ Q12: Administrative Integrity")
    st.markdown("Compute true group sizes and compare them to self-reported counts.")
    q12_melted = q12_data.melt(id_vars=['group_id'], value_vars=['stated_num_students', 'actual_num'], var_name='Metric', value_name='Headcount')
    # Clean the snake_case from the melted column
    q12_melted['Metric'] = q12_melted['Metric'].replace({'stated_num_students': 'Stated Capacity', 'actual_num': 'Actual Enrollment'})
    st.plotly_chart(px.bar(q12_melted, x='group_id', y='Headcount', color='Metric', barmode='group', labels=CHART_LABELS), width="stretch")
    st.markdown("<div class='insight-box'><strong>Insight:</strong> Group 05 wildly overreported their class size by 30 students. Group 03 and Group 10 also severely overreported. These instructors must be audited.</div>", unsafe_allow_html=True)

def page_q13():
    st.title("1️⃣3️⃣ Q13: The Ghost Class Transfer")
    st.markdown("Group 10 (Cybersecurity) is unviable with only 1 student. Who is their closest concept-profile counterpart?")
    c1, c2 = st.columns(2)
    c1.metric("Unviable Student", "Adel AbdelHamid", "Group 10 (Cybersecurity)")
    c2.metric("Closest Match (Target Transfer)", "Menna Saad", "Group 08 (Machine Learning)")
    st.markdown("<div class='insight-box'><strong>Insight:</strong> By calculating Euclidean distance across all concept mastery scores, Adel's cognitive profile is mathematically closest to Menna Saad. Group 10 should be dissolved and Adel transferred to Group 08.</div>", unsafe_allow_html=True)

def page_q14():
    st.title("🚨 Q14: Urgent Intervention List")
    st.markdown("Top 10 at-risk students based on combined low attendance, low engagement, and failed concepts.")
    top_10 = df.sort_values('risk_score', ascending=True).tail(10)
    fig = px.bar(top_10, x='risk_score', y='full_name', orientation='h', color='risk_score', hover_data=['group_name', 'failed_concepts'], labels=CHART_LABELS)
    st.plotly_chart(fig, width="stretch")
    st.markdown("<div class='insight-box'><strong>Insight:</strong> Visualizing the risk scores highlights Hassan Nasr as the #1 flight risk. More critically, 8 out of the top 10 at-risk students belong to Group 07, indicating a systemic instructor failure.</div>", unsafe_allow_html=True)

def page_q15():
    st.title("📉 Q15: Cohort Trajectories")
    st.markdown("Track each group’s average grade across successive assessments. Who is trending down?")
    st.plotly_chart(px.line(group_trends, x='date', y='score', color='group_name', markers=True, labels=CHART_LABELS), width="stretch")
    st.markdown("<div class='insight-box'><strong>Insight:</strong> Group 07 (C005) is in a severe, sustained downward slide. They sit at the absolute bottom of platform performance and fail to recover after the holiday dip.</div>", unsafe_allow_html=True)

def page_hr_advice():
    st.title("💡 Strategic Academic & HR Action Plan")
    st.markdown("Based on the data-driven insights from the 15 analytical questions, here is the prioritized roadmap for intervention.")

    # 1. Immediate Interventions
    st.header("1. Immediate Interventions (Urgent)")
    c1, c2 = st.columns(2)
    with c1:
        st.error("🚨 Address the 'Group 07' Systemic Failure")
        st.markdown("""
        - **Data Point:** Q14 & Q15 show Group 07 is in a sustained downward slide and contains 80% of our top 10 at-risk students.
        - **Action:** Launch an immediate performance audit of the instructors assigned to Group 07. Initiate a mandatory 1-on-1 intervention for the at-risk students identified.
        """)
    with c2:
        st.warning("⚠️ Resolve Ghost Groups & Audits")
        st.markdown("""
        - **Data Point:** Q12 revealed groups (G05, G03, G10) significantly over-reported headcount. 
        - **Action:** Perform an administrative audit to align stated headcount with actual enrollments. Dissolve unviable ghost groups (like G10) and reallocate resources/students (Adel -> G08) immediately.
        """)

    # 2. Curriculum & Learning Design
    st.header("2. Curriculum & Learning Design")
    st.info("📚 Fix the 'Recursion' Knowledge Gap")
    st.markdown("""
    - **Data Point:** Q6 & Q7 show 'Recursion' has an 85% failure rate, and mastery is stagnant across the term.
    - **Action:** The current pedagogy for Recursion is failing. **Stop existing instruction immediately.** Redevelop the curriculum module to include more hands-on practical coding exercises rather than theoretical content.
    """)
    
    # 3. Student Engagement & Retention
    st.header("3. Student Engagement & Retention")
    col3, col4 = st.columns(2)
    with col3:
        st.success("🎯 Targeted Proactive Support")
        st.markdown("""
        - **Data Point:** Q8 (Late submissions = lower scores) and Q4/Q5 (Attendance = grades).
        - **Action:** Implement automated 'nudge' emails for students who consistently submit assignments close to the deadline or show early signs of attendance drops.
        """)
    with col4:
        st.markdown("#### Segmented Outreach")
        st.markdown("""
        - **Cluster 2 (At-Risk):** Mandatory academic mentoring.
        - **Cluster 1 (Social Learners):** Increase forum engagement/peer-to-peer activities.
        - **Cluster 3 (High-Achievers):** Provide advanced elective materials to maintain interest.
        """)

    # 4. Long-Term Policy
    st.header("4. Policy Adjustments")
    st.markdown("""
    - **Age-Based Engagement:** Since the 30+ demographic is our most reliable cohort (Q10), tailor future recruitment efforts toward this segment.
    - **Holiday Resiliency:** Q9 shows a massive dip during holiday windows. Proactively adjust course timelines to ensure major assessments do not fall immediately before or after religious holiday periods to prevent the "holiday slide."
    """)

# --- 4. RENDER NAVIGATION ---
pg = st.navigation(
    {
        "Executive Overview": [
            st.Page(page_main_dashboard, title="Main Dashboard", icon="📊"),
            st.Page(page_hr_advice, title="Recommendations", icon="💡")
        ],
        "Platform Analytics (Q1-Q8)": [
            st.Page(page_q1, title="Q1: Group Attendance", icon="1️⃣"),
            st.Page(page_q2, title="Q2: Score Volatility", icon="2️⃣"),
            st.Page(page_q3, title="Q3: Course Grade Spread", icon="3️⃣"),
            st.Page(page_q4, title="Q4: Attendance vs Grades", icon="4️⃣"),
            st.Page(page_q5, title="Q5: Engagement Drivers", icon="5️⃣"),
            st.Page(page_q6, title="Q6: Curriculum Weak Spots", icon="6️⃣"),
            st.Page(page_q7, title="Q7: Mastery Over Time", icon="7️⃣"),
            st.Page(page_q8, title="Q8: Cost of Procrastination", icon="8️⃣")
        ],
        "Advanced Insights (Q9-Q15)": [
            st.Page(page_q9, title="Q9: The Holiday Dip", icon="9️⃣"),
            st.Page(page_q10, title="Q10: Demographics & Age", icon="🔟"),
            st.Page(page_q11, title="Q11: Behavioral Segmentation", icon="1️⃣"),
            st.Page(page_q12, title="Q12: Administrative Integrity", icon="2️⃣"),
            st.Page(page_q13, title="Q13: Ghost Class Transfer", icon="3️⃣"),
            st.Page(page_q14, title="Q14: Intervention List", icon="🚨"),
            st.Page(page_q15, title="Q15: Cohort Trajectories", icon="📉")
        ]
    }
)
pg.run()
