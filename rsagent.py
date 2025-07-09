import os
import sys
import logging
from dotenv import load_dotenv
import requests

from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings

from openai import OpenAI, OpenAIError

# ─── Setup Logging ─────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s — %(levelname)s — %(message)s"
)

# ─── Load .env for token ───────────────────────────────────────
load_dotenv()
TOGETHER_API_KEY = os.getenv("TOGETHER_API_KEY")
if not TOGETHER_API_KEY:
    logging.error("Missing TOGETHER_API_KEY in environment. Please set it.")
    sys.exit(1)

client = OpenAI(
    api_key=TOGETHER_API_KEY,
    base_url="https://api.together.xyz/v1"
)

# ─── Function: Call Together.ai API ───────────────────────────
def query_together(prompt: str) -> str:
    try:
        response = client.chat.completions.create(
            model="meta-llama/Llama-3-8b-chat-hf",  
            messages=[
                {"role": "system", "content": "You are a helpful HR assistant."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=1000,
        )
        return response.choices[0].message.content
    except OpenAIError as e:
        logging.error(f"Failed to query Together.ai API: {e}")
        sys.exit(1)


# ─── Main Function ─────────────────────────────────────────────
def main():
    JD_PATH = "data/job_description.txt"
    RESUME_DIR = "data/resumes/"
    OUTPUT_FILE = "output.txt"

    if not os.path.exists(JD_PATH):
        logging.error(f"Job description file not found at: {JD_PATH}")
        sys.exit(1)

    if not os.path.isdir(RESUME_DIR):
        logging.error(f"Resumes folder not found at: {RESUME_DIR}")
        sys.exit(1)

    # 📄 Load job description
    logging.info("Loading job description...")
    with open(JD_PATH, "r") as f:
        jd = f.read().strip()

    if not jd:
        logging.error("Job description file is empty.")
        sys.exit(1)

    # 📄 Load resumes
    logging.info("Loading resumes...")
    resumes = []
    files = os.listdir(RESUME_DIR)
    if not files:
        logging.error("No files found in resumes folder.")
        sys.exit(1)

    for filename in files:
        path = os.path.join(RESUME_DIR, filename)
        loader = PyPDFLoader(path) if filename.endswith(".pdf") else TextLoader(path)
        try:
            docs = loader.load()
            resumes.extend(docs)
            logging.info(f"Loaded {filename}")
        except Exception as e:
            logging.warning(f"Failed to load {filename}: {e}")

    if not resumes:
        logging.error("No valid resumes loaded.")
        sys.exit(1)

    # 🪄 Split & embed
    logging.info("Splitting resumes...")
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
    docs = splitter.split_documents(resumes)

    logging.info("Creating vector store...")
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    db = Chroma.from_documents(docs, embeddings)

    # 🔍 Find top matches
    logging.info("Searching for top matching resumes...")
    results = db.similarity_search(jd, k=3)

    if not results:
        logging.error("No resumes found similar to the job description.")
        sys.exit(1)

    # 📄 Prepare prompt
    resumes_text = "\n\n".join(
        [f"Resume {i+1}:\n{doc.page_content}" for i, doc in enumerate(results)]
    )

    prompt = f"""
You are an HR assistant. You have the following job description:
{jd}

And you have found the following resumes:
{resumes_text}

Rank these resumes from best to worst for the job, explain why each was ranked where it was, and suggest the top 3.
"""

    # 🤖 Query Together
    logging.info("Querying Together.ai API...")
    output = query_together(prompt)

    # 💾 Save output
    logging.info("===== Top 3 Resumes with Reasoning =====")
    print(output)

    with open(OUTPUT_FILE, "w") as f:
        f.write(output)

    logging.info(f"Results saved to: {OUTPUT_FILE}")
    logging.info("✅ Done!")


if __name__ == "__main__":
    main()
