# 🔍 Resume Scanner AI

A powerful AI-driven resume verification platform that parses resumes, verifies company and candidate details, performs comprehensive risk analysis, and provides an interactive chat interface for exploring results.

![Resume Scanner AI](https://img.shields.io/badge/Version-2.0-blue) ![Python](https://img.shields.io/badge/Python-3.9+-green) ![Streamlit](https://img.shields.io/badge/Streamlit-1.28+-red)

## ✨ Features

### 📄 Module 1: Smart Parser (The Eyes)
- **Multi-Format Support**: Accepts PDF and DOCX files
- **Auto-Entity Extraction**:
  - Candidate Name, Email, Phone Number
  - Company Names (Work Experience)
  - Job Titles (Designations)
  - GitHub, LinkedIn, and Portfolio URLs
  - Technical Skills Detection
- **Text Cleaning**: Removes formatting artifacts for clean data

### 🏢 Module 2: Company Verification (The Truth Engine)
- **Legal Registration Check**: Queries OpenCorporates to verify company registration
- **Digital Presence Check**: 
  - Website accessibility verification
  - LinkedIn Company Page detection
- **Domain Forensics**:
  - WhoIs Lookup for domain creation date
  - **Timeline Mismatch Detection**: Flags if claims predate company existence

### 💻 Module 3: Candidate Verification (The Background Check)
- **GitHub Deep-Scan**:
  - User validity verification
  - Account age analysis
  - Activity metrics (repos, followers, recent activity)
  - **Language-Skill Match**: Compares claimed skills vs actual code
- **LinkedIn Verification**:
  - Profile existence check
  - Name matching with URL slug

### 🎯 Module 4: Risk Analysis (The BS Detector)
- **Ghost Company Alert**: Flags companies with no legal record AND no website
- **Timeline Mismatch**: Detects employment claims before company existed
- **Hyper-Inflation Detection**: Flags senior claims with minimal GitHub presence
- **Trust Score**: 0-100 weighted score based on verification results
- **Risk Level Classification**: CRITICAL, HIGH, MEDIUM, LOW

### 💬 Chat Interface
- Natural language queries about candidates
- Compare multiple resumes
- Ask about specific verification results
- Get recommendations and summaries

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Download Spacy Model

```bash
python -m spacy download en_core_web_sm
```

### 3. Configure Environment Variables

Create a `.env` file in the project root:

```env
# Required for GitHub verification
GITHUB_TOKEN=your_github_personal_access_token

# OPTIONAL - Company verification uses FREE sources by default!
# Only needed if you have a paid OpenCorporates subscription
OPENCORPORATES_API_TOKEN=
```

**Getting API Tokens:**
- **GitHub Token**: Go to GitHub → Settings → Developer Settings → Personal Access Tokens → Generate new token (classic) with `read:user` scope

**FREE Company Verification Sources (Built-in):**
- 🇬🇧 **UK Companies House** - Free UK company registry
- 🇺🇸 **SEC EDGAR** - Free US public companies database
- 🔍 **DuckDuckGo API** - Free web presence check
- 🔎 **Google Suggest** - Free company recognition check
- 🌐 **WhoIs Lookup** - Free domain forensics
- 💼 **LinkedIn Check** - Free company page detection

### 4. Run the Application

```bash
streamlit run app.py
```

The app will open in your browser at `http://localhost:8501`

## 📖 Usage Guide

### Uploading Resumes
1. Use the sidebar to drag & drop PDF/DOCX files
2. Click "🚀 Process Resumes"
3. Wait for analysis to complete

### Chat Commands
Ask natural language questions like:
- "Show me all candidates"
- "Who has the highest trust score?"
- "Compare all resumes"
- "What are the risk flags?"
- "Tell me about [candidate name]"
- "Show GitHub stats"
- "Check company verifications"

### Understanding Trust Scores

| Score Range | Risk Level | Meaning |
|-------------|------------|---------|
| 70-100 | 🟢 LOW | Most claims verified |
| 50-69 | 🟡 MEDIUM | Some verification issues |
| 30-49 | 🟠 HIGH | Elevated risk |
| 0-29 | 🔴 CRITICAL | Multiple serious failures |

### Risk Flags

| Flag Type | Severity | Description |
|-----------|----------|-------------|
| GHOST_COMPANY | CRITICAL | No legal record + no website |
| TIMELINE_MISMATCH | HIGH | Claims predate company existence |
| HYPER_INFLATION | HIGH | Senior claims with weak GitHub |
| SKILL_MISMATCH | MEDIUM | Claimed skills not in GitHub |
| INVALID_GITHUB | MEDIUM | GitHub profile doesn't exist |
| NAME_MISMATCH | LOW | LinkedIn name doesn't match |

## 🛠️ Technical Architecture

```
resume-scanner/
├── app.py                 # Main Streamlit application
├── src/
│   ├── __init__.py
│   ├── parser.py          # Resume parsing & entity extraction
│   ├── company_validator.py   # Company verification logic
│   ├── candidate_validator.py # GitHub & LinkedIn verification
│   └── risk_engine.py     # Risk analysis & scoring
├── requirements.txt
├── .env                   # API tokens (create this)
└── README.md
```

## ⚠️ Limitations

- **LinkedIn Verification**: LinkedIn aggressively blocks automated access. Profile checks may return false negatives.
- **OpenCorporates**: Free tier has rate limits. Some companies may not be in the database.
- **NLP Accuracy**: Entity extraction depends on resume formatting. Results may vary.
- **API Limits**: GitHub API has rate limits (60 requests/hour unauthenticated, 5000/hour with token)

## 🔐 Privacy & Security

- All processing is done locally on your machine
- No resume data is sent to external servers (except API verification calls)
- API tokens are stored in local `.env` file only

## 📝 License

MIT License - See LICENSE file for details

## 🤝 Contributing

Contributions are welcome! Please feel free to submit pull requests.

---

**Built with ❤️ using Streamlit, Spacy, and Plotly**
