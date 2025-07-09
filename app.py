import os
import streamlit as st
import tempfile
import shutil
import subprocess

st.set_page_config(
    page_title="Resume Ranker",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# === Header with Logo ===
st.markdown(
    """
    <div style='text-align:center'>
        <img src='https://static.vecteezy.com/system/resources/previews/020/935/561/non_2x/ranking-icon-for-your-website-mobile-presentation-and-logo-design-free-vector.jpg' 
             width='150' style='margin-bottom: 10px;'/>
        <h1 style='color:#4CAF50'>Resume Ranker HR Assistant 🤖</h1>
        <p style='color:gray;font-size:18px;'>Upload a job description and candidate resumes.<br> 
        The app will rank them intelligently and explain its choices!</p>
    </div>
    <hr style='border:1px solid #ddd'>
    """,
    unsafe_allow_html=True
)

# === Upload job description ===
st.markdown("### 📝 Upload Job Description")
jd_file = st.file_uploader("Upload a `.txt` file", type=["txt"])

# === Upload resumes ===
st.markdown("### 👤 Upload Resumes")
resumes_files = st.file_uploader(
    "Upload `.txt` or `.pdf` resumes (you can select multiple)",
    type=["txt", "pdf"],
    accept_multiple_files=True
)

# === Run button ===
run_button = st.button("🚀 Run Resume Ranking", use_container_width=True)

if run_button:
    if not jd_file:
        st.error("⚠️ Please upload a job description.")
        st.stop()
    if not resumes_files:
        st.error("⚠️ Please upload at least one resume.")
        st.stop()

    with tempfile.TemporaryDirectory() as tmpdir:
        jd_path = os.path.join(tmpdir, "job_description.txt")
        resumes_dir = os.path.join(tmpdir, "resumes")
        os.makedirs(resumes_dir, exist_ok=True)

        # Save JD
        with open(jd_path, "wb") as f:
            f.write(jd_file.read())

        # Save resumes
        for rf in resumes_files:
            resume_path = os.path.join(resumes_dir, rf.name)
            with open(resume_path, "wb") as f:
                f.write(rf.read())

        # Copy to data/
        if os.path.exists("data"):
            shutil.rmtree("data")
        os.makedirs("data/resumes", exist_ok=True)
        shutil.copy(jd_path, "data/job_description.txt")
        for f in os.listdir(resumes_dir):
            shutil.copy(os.path.join(resumes_dir, f), f"data/resumes/{f}")

        with st.spinner("🔎 Running resume ranking... this may take a few moments..."):
            result = subprocess.run(
                ["python", "rsagent.py"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

        # Show output
        st.markdown("---")
        if os.path.exists("output.txt"):
            st.subheader("✅ Top Resumes & Reasoning")
            with open("output.txt", "r") as f:
                output_text = f.read()
            st.text_area("Results", output_text, height=400, key="results")

            # Optional: Expandable logs if needed
            with st.expander("📋 Show Logs"):
                st.code(result.stdout + "\n" + result.stderr)
        else:
            st.error("❌ Something went wrong — no output file was generated.")
            with st.expander("📋 Show Logs"):
                st.code(result.stdout + "\n" + result.stderr)

# === Footer ===
st.markdown(
    """
    <hr>
    <div style='text-align:center; color:gray; font-size:14px;'>
        🚀 Made by me for HR professionals — Resume Ranker
    </div>
    """,
    unsafe_allow_html=True
)
