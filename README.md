# AI Resume Mining & Candidate Matching System

An end-to-end AI-powered recruitment platform that automatically processes resumes, extracts candidate information, generates semantic embeddings, performs intelligent candidate-job matching, and provides analytics for recruiters.

## Overview

Recruitment teams often spend significant time manually reviewing resumes and matching candidates to job requirements.

This project leverages Natural Language Processing (NLP), Embedding Models, Vector Search, and Machine Learning techniques to automate candidate screening and recommendation.

The system can:

* Parse Resume PDFs
* Extract Skills, Education, and Experience
* Generate Semantic Embeddings
* Store Candidate Vectors using FAISS
* Match Candidates to Job Descriptions
* Rank Candidates by Similarity Score
* Identify Missing Skills (Skill Gap Analysis)
* Visualize Recruitment Insights

---

## Features

### Resume Processing

* PDF Resume Parsing
* Text Extraction
* Resume Cleaning & Normalization
* Structured Candidate Profile Generation

### Information Extraction

* Skill Extraction
* Education Extraction
* Experience Extraction
* Keyword Extraction

### AI Matching Engine

* Sentence Transformer Embeddings
* Semantic Similarity Search
* Candidate Ranking
* Job-Candidate Matching

### Analytics

* Candidate Statistics
* Skill Distribution Analysis
* Recruitment Reports
* Interactive Dashboards

### API Services

* Resume Upload API
* Candidate Search API
* Job Matching API
* Recommendation API

---

## System Architecture

```text
Resume PDF
    │
    ▼
Resume Parser
    │
    ▼
Text Cleaning
    │
    ▼
Information Extraction
(Skills, Education, Experience)
    │
    ▼
Sentence Transformer
    │
    ▼
Embedding Vector
    │
 ┌──┴─────┐
 │        │
 ▼        ▼
MongoDB  FAISS
 │        │
 └──┬─────┘
    ▼
Matching Engine
    ▼
Ranking Engine
    ▼
Analytics Dashboard
```

---

## Project Structure

```text
AI_ResumeMining_CandidateMatchingSystem
│
├── app
│   ├── analytics
│   ├── api
│   ├── core
│   ├── database
│   ├── embeddings
│   ├── extraction
│   ├── matching
│   ├── resume_processing
│   ├── models
│   ├── schemas
│   ├── services
│   ├── utils
│   └── vector_store
│
├── data
├── faiss_index
├── docker
├── logs
├── notebooks
├── tests
│
├── requirements.txt
├── README.md
└── run.py
```

---

## Tech Stack

### Backend

* Python
* FastAPI
* Uvicorn

### Database

* MongoDB
* PyMongo

### NLP & AI

* PyTorch
* Transformers
* Sentence Transformers

### Vector Search

* FAISS

### Data Processing

* Pandas
* NumPy
* Scikit-Learn

### Visualization

* Streamlit
* Plotly

### Utilities

* Loguru
* Python Dotenv

---

## Installation

### Clone Repository

```bash
git clone https://github.com/your-username/AI-Resume-Mining-System.git

cd AI-Resume-Mining-System
```

### Create Environment

```bash
conda create -n ai_resume python=3.11

conda activate ai_resume
```

### Install Dependencies

```bash
pip install -r requirements.txt
```

---

## Environment Variables

Create a `.env` file:

```env
MONGO_URI=mongodb://localhost:27017

DB_NAME=resume_mining_db

MODEL_NAME=sentence-transformers/all-MiniLM-L6-v2

FAISS_INDEX_PATH=faiss_index/candidate.index
```

---

## Running the Project

### Start FastAPI Server

```bash
uvicorn app.main:app --reload
```

### Start Dashboard

```bash
streamlit run app/analytics/dashboards/dashboard.py
```

---

## API Endpoints

### Resume APIs

| Method | Endpoint               |
| ------ | ---------------------- |
| POST   | /api/v1/resumes/upload |
| GET    | /api/v1/resumes        |
| GET    | /api/v1/resumes/{id}   |

### Matching APIs

| Method | Endpoint                |
| ------ | ----------------------- |
| POST   | /api/v1/match           |
| GET    | /api/v1/rankings        |
| GET    | /api/v1/recommendations |

---

## Machine Learning Pipeline

### Resume Processing

1. Upload Resume
2. Extract Text
3. Clean Text
4. Extract Information

### Embedding Pipeline

1. Candidate Profile
2. Sentence Transformer
3. Embedding Generation
4. FAISS Storage

### Matching Pipeline

1. Job Description Embedding
2. Candidate Embedding
3. Cosine Similarity
4. Ranking
5. Recommendation

---

## Future Improvements

* RAG-based Candidate Search
* LLM-powered Candidate Summarization
* Multi-language Resume Support
* Real-time Candidate Recommendations
* Cloud Deployment
* Kubernetes Support
* AWS/GCP Integration

---

## Author

Nguyen Hoang Khang

Information Technology Student

Interested in:

* Data Engineering
* Artificial Intelligence
* Machine Learning
* NLP
* Backend Development

---

## License

This project is intended for educational and portfolio purposes.