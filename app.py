import streamlit as st
import pandas as pd
import os
import re
import tempfile
import hashlib
from datetime import datetime
from dotenv import load_dotenv
from src.parser import ResumeParser
from src.company_validator import CompanyValidator
from src.candidate_validator import CandidateValidator
from src.risk_engine import RiskEngine

# Load environment variables
load_dotenv()

# Page Config
st.set_page_config(
    page_title="Resume Scanner AI",
    page_icon="✓",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Minimal Dark Theme - Gemini Style
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&display=swap');
    
    /* Base - Clean dark background */
    .stApp {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        background: #1a1a1a;
    }
    
    /* Hide all Streamlit branding */
    #MainMenu, footer, header, .stDeployButton {display: none !important; visibility: hidden !important;}
    
    /* Center content */
    .main .block-container {
        max-width: 800px;
        padding: 0 1rem;
        margin: 0 auto;
    }
    
    /* Minimal greeting */
    .greeting {
        text-align: center;
        padding-top: 20vh;
        margin-bottom: 2rem;
    }
    
    .greeting h1 {
        color: #e8e8e8;
        font-size: 2rem;
        font-weight: 400;
        margin: 0;
        letter-spacing: -0.5px;
    }
    
    .greeting .highlight {
        background: linear-gradient(135deg, #8b5cf6 0%, #a78bfa 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    
    /* Trust badges */
    .trust-badge {
        display: inline-block;
        padding: 0.4rem 1rem;
        border-radius: 20px;
        font-weight: 500;
        font-size: 0.9rem;
    }
    
    .trust-high { background: rgba(34, 197, 94, 0.15); color: #4ade80; }
    .trust-medium { background: rgba(234, 179, 8, 0.15); color: #fbbf24; }
    .trust-low { background: rgba(239, 68, 68, 0.15); color: #f87171; }
    
    /* Report sections */
    .report-section {
        background: #252525;
        border: 1px solid #333;
        border-radius: 12px;
        padding: 1rem 1.25rem;
        margin: 0.75rem 0;
    }
    
    .report-section h4 {
        color: #a78bfa;
        margin: 0 0 0.75rem 0;
        font-size: 0.9rem;
        font-weight: 500;
        padding-bottom: 0.5rem;
        border-bottom: 1px solid #333;
    }
    
    /* Hide file uploader initially - show via expander */
    [data-testid="stFileUploader"] {
        background: #252525;
        border: 1px solid #333;
        border-radius: 12px;
        padding: 0.75rem;
    }
    
    /* Chat messages - minimal */
    [data-testid="stChatMessage"] {
        background: transparent;
        border: none;
        padding: 0.75rem 0;
    }
    
    /* Chat input - centered pill style */
    [data-testid="stChatInput"] {
        max-width: 700px;
        margin: 0 auto;
    }
    
    [data-testid="stChatInput"] > div {
        background: #2a2a2a;
        border: 1px solid #3a3a3a;
        border-radius: 24px;
        padding: 0.25rem 0.5rem;
    }
    
    [data-testid="stChatInput"] input {
        background: transparent;
        color: #e8e8e8;
    }
    
    [data-testid="stChatInput"] button {
        background: #8b5cf6;
        border-radius: 50%;
    }
    
    /* Tables */
    table { width: 100%; border-collapse: collapse; margin: 0.5rem 0; }
    th { background: #2a2a2a; color: #a78bfa; font-weight: 500; padding: 0.6rem; text-align: left; }
    td { padding: 0.5rem 0.6rem; border-bottom: 1px solid #333; color: #d4d4d4; }
    
    /* Text colors */
    .stMarkdown { color: #d4d4d4; }
    a { color: #a78bfa; text-decoration: none; }
    a:hover { color: #c4b5fd; }
    
    /* Buttons - minimal */
    .stButton > button {
        background: #2a2a2a;
        color: #e8e8e8;
        border: 1px solid #3a3a3a;
        border-radius: 8px;
        padding: 0.5rem 1rem;
        font-weight: 400;
    }
    
    .stButton > button:hover {
        background: #333;
        border-color: #444;
    }
    
    /* Expander */
    .streamlit-expanderHeader {
        background: #252525;
        border-radius: 8px;
    }
</style>
""", unsafe_allow_html=True)

# Initialize modules
@st.cache_resource
def init_modules():
    return (
        ResumeParser(),
        CompanyValidator(opencorporates_api_token=os.getenv("OPENCORPORATES_API_TOKEN")),
        CandidateValidator(github_token=os.getenv("GITHUB_TOKEN")),
        RiskEngine()
    )

parser, company_validator, candidate_validator, risk_engine = init_modules()

# Session State
if "messages" not in st.session_state:
    st.session_state.messages = []
if "candidates" not in st.session_state:
    st.session_state.candidates = {}
if "processed_files" not in st.session_state:
    st.session_state.processed_files = set()  # Track processed file hashes

# ============ HELPER FUNCTIONS ============

def get_file_hash(file):
    """Get hash of file to avoid re-processing."""
    file.seek(0)
    content = file.read()
    file.seek(0)
    return hashlib.md5(content).hexdigest()

def extract_urls(text):
    """Extract GitHub and LinkedIn URLs from text."""
    github_pattern = r'https?://(?:www\.)?github\.com/([a-zA-Z0-9_-]+)/?'
    linkedin_pattern = r'https?://(?:www\.)?linkedin\.com/in/([a-zA-Z0-9_-]+)/?'
    
    return {
        "github": re.findall(github_pattern, text),
        "linkedin": re.findall(linkedin_pattern, text),
        "github_urls": re.findall(r'https?://(?:www\.)?github\.com/[a-zA-Z0-9_-]+/?', text),
        "linkedin_urls": re.findall(r'https?://(?:www\.)?linkedin\.com/in/[a-zA-Z0-9_-]+/?', text)
    }

def process_resume_file(file):
    """Process uploaded resume and return analysis."""
    file_type = file.name.split('.')[-1].lower()
    if file_type not in ['pdf', 'docx']:
        return None, "Unsupported file format. Please upload PDF or DOCX."
    
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=f'.{file_type}') as tmp:
            tmp.write(file.getvalue())
            tmp_path = tmp.name
        
        with open(tmp_path, 'rb') as f:
            data = parser.parse(f, file_type)
        
        os.unlink(tmp_path)
        
        if not data:
            return None, "Could not parse the resume. Please check the file."
        
        # Verify companies (focus on registration)
        company_verifications = []
        for company in data.get('companies', [])[:5]:
            res = company_validator.verify_company(company)
            company_verifications.append(res)
        
        # Verify candidate (deep GitHub analysis)
        candidate_verification = candidate_validator.verify_candidate(data)
        
        # Risk analysis
        risk_analysis = risk_engine.analyze_risk(data, company_verifications, candidate_verification)
        
        result = {
            "filename": file.name,
            "parsed_data": data,
            "company_verifications": company_verifications,
            "candidate_verification": candidate_verification,
            "risk_analysis": risk_analysis,
            "processed_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        # Store in session
        name = data.get('name', 'Unknown')
        st.session_state.candidates[name] = result
        
        return result, None
        
    except Exception as e:
        return None, f"Error processing file: {str(e)}"

def get_trust_badge_class(score):
    if score >= 70:
        return "trust-high"
    elif score >= 50:
        return "trust-medium"
    return "trust-low"

def format_github_response(gh_data, claimed_skills=None):
    """Format GitHub analysis with deep repo analysis and skill matching."""
    if not gh_data.get('valid'):
        return f"❌ **GitHub Profile Not Found**\n\n{gh_data.get('error', 'Unknown error')}"
    
    # Rating based on activity
    repos = gh_data.get('public_repos', 0)
    age = gh_data.get('account_age_days', 0)
    rating = min(5, max(1, (repos // 10) + (age // 365) + 1))
    stars = "⭐" * rating
    
    age_text = f"{gh_data.get('account_age_months', 0)} months"
    if age > 365:
        age_text = f"{age // 365}+ years"
    
    activity = "🔥 Active" if gh_data.get('recent_activity_count', 0) > 0 else "😴 Inactive"
    
    response = f"""
## ✅ GitHub Profile Verified

**@{gh_data.get('username')}** • Account Age: {age_text} • {activity}

<div class="report-section">
<h4>📊 Profile Statistics</h4>

| Metric | Value |
|--------|-------|
| Public Repos | {repos} ({gh_data.get('original_repos', repos)} original, {gh_data.get('forked_repos', 0)} forked) |
| Followers | {gh_data.get('followers', 0)} |
| Languages | {', '.join(gh_data.get('top_languages', [])[:5]) or 'None'} |
| Recent Activity | {gh_data.get('recent_activity_count', 0)} repos updated in 6 months |

**Developer Rating:** {stars}
</div>
"""
    
    # Skill matching section
    if gh_data.get('skill_matches') or gh_data.get('skill_mismatches'):
        response += """
<div class="report-section">
<h4>🎯 Resume vs GitHub Skill Match</h4>
"""
        if gh_data.get('skill_matches'):
            response += "\n**✅ Skills Verified in GitHub:**\n"
            for match in gh_data['skill_matches']:
                response += f"- <span class='skill-match'>✓ {match['skill']}</span> - {match['evidence']}\n"
        
        if gh_data.get('skill_mismatches'):
            response += "\n**❌ Skills NOT Found in GitHub:**\n"
            for mismatch in gh_data['skill_mismatches']:
                response += f"- <span class='skill-mismatch'>✗ {mismatch['skill']}</span> - {mismatch['message']}\n"
        
        response += "</div>"
    
    # Top repos
    if gh_data.get('repos_details'):
        response += """
<div class="report-section">
<h4>📁 Top Repositories</h4>

| Repository | Language | Stars |
|------------|----------|-------|
"""
        for repo in gh_data['repos_details'][:5]:
            fork_badge = " (fork)" if repo.get('is_fork') else ""
            response += f"| {repo['name']}{fork_badge} | {repo.get('language', 'N/A')} | {repo.get('stars', 0)} |\n"
        response += "</div>"
    
    # Warnings
    if gh_data.get('hyper_inflation_flags'):
        response += "\n\n⚠️ **Concerns:**\n"
        for flag in gh_data['hyper_inflation_flags']:
            response += f"- {flag['message']}\n"
    
    return response

def format_resume_report(result):
    """Format complete resume analysis as a detailed report."""
    data = result['parsed_data']
    risk = result['risk_analysis']
    gh = result['candidate_verification'].get('github', {})
    li = result['candidate_verification'].get('linkedin', {})
    companies = result['company_verifications']
    
    score = risk['trust_score']
    badge_class = get_trust_badge_class(score)
    level = risk['risk_level']
    
    response = f"""
# 📄 Candidate Report: {data.get('name', 'Unknown')}

<div class="trust-badge {badge_class}">
{level['icon']} Trust Score: {score}/100 - {level['level']} RISK
</div>

---

<div class="report-section">
<h4>📋 Basic Information</h4>

| Field | Value |
|-------|-------|
| **Name** | {data.get('name', 'N/A')} |
| **Email** | {data.get('email', 'N/A')} |
| **Phone** | {data.get('phone', 'N/A')} |
| **Experience** | {data.get('total_experience', {}).get('experience_text', 'Not calculated')} |
| **Claimed Skills** | {', '.join(data.get('skills', [])[:8]) or 'None detected'} |

</div>

<div class="report-section">
<h4>🎓 Education</h4>
"""
    
    # Education section
    education = data.get('education', [])
    if education:
        for edu in education[:3]:
            if edu.get('degree'):
                edu_text = f"**{edu.get('degree', '')}**"
                if edu.get('field'):
                    edu_text += f" in {edu.get('field')}"
                if edu.get('institution'):
                    edu_text += f" - {edu.get('institution')}"
                if edu.get('year'):
                    edu_text += f" ({edu.get('year')})"
                response += f"\n- {edu_text}"
            elif edu.get('institution'):
                response += f"\n- {edu.get('institution')}"
    else:
        response += "\nNo education details detected."
    
    response += "\n</div>"
    
    # Company verification section - only show if companies were found
    if companies:
        response += """
<div class="report-section">
<h4>🏢 Company Registration Verification</h4>
"""
        for comp in companies:
            status = comp.get('status', 'UNKNOWN')
            if status == "REGISTERED":
                icon = "✅"
                status_text = f"Registered ({comp.get('registrations_found', [{}])[0].get('source', 'Unknown')})"
            elif status == "LIKELY_REGISTERED":
                icon = "🟡"
                status_text = "Likely exists (not fully confirmed)"
            else:
                icon = "❌"
                status_text = "NOT FOUND in registries"
            
            response += f"\n- {icon} **{comp['company']}**: {status_text}"
            
            # Show which registries were checked
            if comp.get('sources_checked'):
                response += f"\n  - *Checked: {', '.join(comp['sources_checked'][:3])}*"
        
        response += "\n</div>"
    
    # GitHub Verification
    response += """
<div class="report-section">
<h4>💻 GitHub Verification</h4>
"""
    
    if gh and gh.get('valid'):
        response += f"""
✅ **Profile Verified**: @{gh.get('username')}

| Metric | Value |
|--------|-------|
| Repos | {gh.get('public_repos', 0)} ({gh.get('original_repos', 0)} original) |
| Account Age | {gh.get('account_age_months', 0)} months |
| Top Languages | {', '.join(gh.get('top_languages', [])[:4]) or 'None'} |
"""
        
        # Skill matching
        if gh.get('skill_matches'):
            response += f"\n**Skills Verified:** {len(gh['skill_matches'])} matches\n"
            for m in gh['skill_matches'][:3]:
                response += f"- ✅ {m['skill']}\n"
        
        if gh.get('skill_mismatches'):
            response += f"\n**Skills NOT Verified:** {len(gh['skill_mismatches'])} concerns\n"
            for m in gh['skill_mismatches'][:3]:
                response += f"- ❌ {m['skill']}: {m['message']}\n"
        
        if gh.get('hyper_inflation_flags'):
            response += "\n**⚠️ Activity Concerns:**\n"
            for flag in gh['hyper_inflation_flags'][:2]:
                response += f"- {flag['message']}\n"
    else:
        response += f"\n❌ GitHub not verified: {gh.get('error', 'Not provided') if gh else 'Not provided'}"
    
    response += "</div>"
    
    # LinkedIn
    response += """
<div class="report-section">
<h4>🔷 LinkedIn Verification</h4>
"""
    
    if li and li.get('valid'):
        name_status = "✅ Matches" if li.get('slug_match') else "⚠️ Mismatch"
        response += f"\n✅ Profile accessible | Name: {name_status}"
    else:
        response += f"\n❌ Not verified: {li.get('error', 'Not provided') if li else 'Not provided'}"
    
    response += "</div>"
    
    # Risk Flags
    if risk['risk_flags']:
        response += """
<div class="report-section">
<h4>🚨 Risk Flags</h4>
"""
        for flag in risk['risk_flags'][:5]:
            icon = "🔴" if flag['severity'] in ['CRITICAL', 'HIGH'] else "🟡" if flag['severity'] == 'MEDIUM' else "🔵"
            response += f"\n{icon} **[{flag['severity']}]** {flag['message']}"
        response += "</div>"
    else:
        response += """
<div class="report-section">
<h4>✅ No Major Risk Flags</h4>

All checks passed! This candidate appears legitimate.
</div>
"""
    
    # Final Summary
    response += f"""
---

### 📝 Summary

{risk.get('summary', 'Analysis complete.')}

**Recommendation:** {"✅ Proceed with interview" if score >= 70 else "⚠️ Verify concerns before proceeding" if score >= 50 else "❌ Significant concerns - investigate further"}
"""
    
    return response

def generate_hiring_recommendation(candidate_name, role=None):
    """Generate hiring recommendation."""
    # Find candidate (fuzzy match)
    matched_name = None
    for name in st.session_state.candidates:
        if candidate_name.lower() in name.lower() or name.lower() in candidate_name.lower():
            matched_name = name
            break
    
    if not matched_name:
        return f"I don't have data for **{candidate_name}**. Please upload their resume or share their GitHub/LinkedIn first."
    
    result = st.session_state.candidates[matched_name]
    score = result['risk_analysis']['trust_score']
    flags = result['risk_analysis']['risk_flags']
    gh = result['candidate_verification'].get('github', {})
    
    # Determine recommendation
    if score >= 70 and len(flags) == 0:
        verdict = "✅ **STRONGLY RECOMMENDED**"
    elif score >= 70:
        verdict = "✅ **RECOMMENDED** (minor concerns)"
    elif score >= 50:
        verdict = "⚠️ **PROCEED WITH CAUTION**"
    else:
        verdict = "❌ **NOT RECOMMENDED**"
    
    response = f"""
## 🎯 Hiring Recommendation: {matched_name}

{verdict}

**Trust Score:** {score}/100

### ✅ Strengths
"""
    
    strengths = []
    if gh and gh.get('valid'):
        if gh.get('account_age_days', 0) > 365:
            strengths.append(f"Established GitHub ({gh.get('account_age_days', 0) // 365}+ years)")
        if gh.get('public_repos', 0) > 10:
            strengths.append(f"Active developer ({gh.get('public_repos', 0)} repos)")
        if gh.get('skill_matches'):
            strengths.append(f"{len(gh['skill_matches'])} claimed skills verified in GitHub")
    
    verified = sum(1 for c in result['company_verifications'] if c.get('status') == 'REGISTERED')
    if verified > 0:
        strengths.append(f"{verified} employers verified in registries")
    
    for s in strengths or ["Limited data available"]:
        response += f"\n- {s}"
    
    if flags:
        response += "\n\n### ⚠️ Concerns\n"
        for flag in flags[:3]:
            response += f"\n- {flag['message']}"
    
    if gh and gh.get('skill_mismatches'):
        response += "\n\n### ❌ Unverified Skills\n"
        for m in gh['skill_mismatches'][:3]:
            response += f"\n- {m['skill']}: Not found in GitHub repos"
    
    return response

def compare_candidates(names):
    """Compare multiple candidates."""
    available = []
    for name in names:
        for stored_name in st.session_state.candidates:
            if name.lower() in stored_name.lower():
                available.append(stored_name)
                break
    
    if len(available) < 2:
        return "I need at least 2 candidates to compare. Please upload more resumes."
    
    response = "## 📊 Candidate Comparison\n\n| Metric |"
    for name in available:
        response += f" {name.split()[0]} |"
    response += "\n|--------|" + "--------|" * len(available) + "\n"
    
    # Trust Score
    response += "| **Trust Score** |"
    scores = [st.session_state.candidates[n]['risk_analysis']['trust_score'] for n in available]
    for i, name in enumerate(available):
        winner = " ⭐" if scores[i] == max(scores) else ""
        response += f" {scores[i]}/100{winner} |"
    response += "\n"
    
    # GitHub
    response += "| **GitHub Repos** |"
    for name in available:
        gh = st.session_state.candidates[name]['candidate_verification'].get('github', {})
        repos = gh.get('public_repos', 0) if gh and gh.get('valid') else "N/A"
        response += f" {repos} |"
    response += "\n"
    
    # Skills Verified
    response += "| **Skills Verified** |"
    for name in available:
        gh = st.session_state.candidates[name]['candidate_verification'].get('github', {})
        matches = len(gh.get('skill_matches', [])) if gh else 0
        response += f" {matches} |"
    response += "\n"
    
    # Companies Registered
    response += "| **Employers Verified** |"
    for name in available:
        verified = sum(1 for c in st.session_state.candidates[name]['company_verifications'] 
                      if c.get('status') == 'REGISTERED')
        response += f" {verified} |"
    response += "\n"
    
    # Risk Flags
    response += "| **Risk Flags** |"
    flag_counts = [len(st.session_state.candidates[n]['risk_analysis']['risk_flags']) for n in available]
    for i, name in enumerate(available):
        winner = " ⭐" if flag_counts[i] == min(flag_counts) else ""
        response += f" {flag_counts[i]}{winner} |"
    response += "\n"
    
    # Winner
    winner_idx = scores.index(max(scores))
    response += f"\n\n🏆 **Recommendation:** {available[winner_idx]} (highest trust score: {scores[winner_idx]}/100)"
    
    return response

def detect_intent(message):
    """Detect user intent from message."""
    msg_lower = message.lower()
    
    urls = extract_urls(message)
    if urls['github'] or urls['linkedin']:
        return 'analyze_links', urls
    
    hire_keywords = ['should i hire', 'good to hire', 'recommend', 'hire ', 'qualified', 'worth hiring']
    if any(kw in msg_lower for kw in hire_keywords):
        return 'hiring_recommendation', message
    
    compare_keywords = ['compare', 'vs', 'versus', 'better', 'who is more', 'which one']
    if any(kw in msg_lower for kw in compare_keywords):
        return 'compare', message
    
    for name in st.session_state.candidates:
        if name.lower() in msg_lower:
            return 'candidate_query', name
    
    if any(kw in msg_lower for kw in ['all candidates', 'list', 'show all', 'who']):
        return 'list_candidates', None
    
    return 'general', message

def generate_response(message, file_data=None):
    """Generate AI response."""
    
    if file_data:
        result, error = process_resume_file(file_data)
        if error:
            return f"❌ {error}"
        return format_resume_report(result)
    
    intent, data = detect_intent(message)
    
    if intent == 'analyze_links':
        response = ""
        
        for url in data.get('github_urls', []):
            gh_result = candidate_validator.verify_github(url, [])
            response += format_github_response(gh_result)
            
            if gh_result.get('valid'):
                name = gh_result.get('name') or gh_result.get('username', 'Unknown')
                st.session_state.candidates[name] = {
                    'parsed_data': {'name': name, 'urls': {'github': url}, 'skills': []},
                    'candidate_verification': {'github': gh_result, 'linkedin': None},
                    'company_verifications': [],
                    'risk_analysis': {
                        'trust_score': min(100, 50 + gh_result.get('public_repos', 0) + gh_result.get('account_age_days', 0) // 30),
                        'risk_flags': [{'severity': f['severity'], 'message': f['message']} for f in gh_result.get('hyper_inflation_flags', [])],
                        'risk_level': {'icon': '✅', 'level': 'LOW', 'message': 'GitHub verified'},
                        'summary': f"GitHub profile verified for @{gh_result.get('username')}"
                    }
                }
        
        for url in data.get('linkedin_urls', []):
            li_result = candidate_validator.verify_linkedin(url, "Unknown")
            status = "✅ Accessible" if li_result.get('valid') else "❌ Not accessible"
            response += f"\n\n**LinkedIn:** {status}"
        
        return response if response else "I couldn't find valid links in your message."
    
    elif intent == 'hiring_recommendation':
        for name in st.session_state.candidates:
            if name.lower() in message.lower() or name.split()[0].lower() in message.lower():
                return generate_hiring_recommendation(name)
        if st.session_state.candidates:
            best = max(st.session_state.candidates.keys(),
                      key=lambda n: st.session_state.candidates[n]['risk_analysis']['trust_score'])
            return generate_hiring_recommendation(best)
        return "Please share a resume or GitHub profile first!"
    
    elif intent == 'compare':
        names = list(st.session_state.candidates.keys())
        if len(names) >= 2:
            return compare_candidates(names[:4])
        return "I need at least 2 candidates to compare. Please share more profiles!"
    
    elif intent == 'candidate_query':
        if data in st.session_state.candidates:
            return format_resume_report(st.session_state.candidates[data])
        return f"I don't have data for {data}."
    
    elif intent == 'list_candidates':
        if not st.session_state.candidates:
            return "No candidates yet. Upload a resume or share a GitHub/LinkedIn link!"
        
        response = "## 📋 Analyzed Candidates\n\n"
        for name, cand in st.session_state.candidates.items():
            score = cand['risk_analysis']['trust_score']
            emoji = "🟢" if score >= 70 else "🟡" if score >= 50 else "🔴"
            response += f"- {emoji} **{name}** - Trust Score: {score}/100\n"
        response += "\n*Ask about any candidate or say 'compare' for comparison!*"
        return response
    
    else:
        return """
I can help you verify candidates! Here's what to do:

📄 **Upload a Resume** - Drop a PDF/DOCX file above
🔗 **Paste a GitHub Link** - Like `https://github.com/username`
🔗 **Paste a LinkedIn Link** - Like `https://linkedin.com/in/name`
❓ **Ask Questions** - "Should I hire John?" or "Compare candidates"

**Try pasting a GitHub link to get started!**
"""

# ============ MAIN UI ============

# Show greeting only when no messages (like Gemini)
if not st.session_state.messages:
    st.markdown("""
    <div class="greeting">
        <h1>What can I help you with, <span class="highlight">today</span>?</h1>
    </div>
    """, unsafe_allow_html=True)

# File uploader in expander (hidden by default like Gemini's +)
with st.expander("Upload Resume", expanded=False):
    uploaded_file = st.file_uploader(
        "PDF or DOCX",
        type=['pdf', 'docx'],
        key="file_upload",
        label_visibility="collapsed"
    )

# Process file only if it's new
if uploaded_file:
    file_hash = get_file_hash(uploaded_file)
    
    if file_hash not in st.session_state.processed_files:
        st.session_state.processed_files.add(file_hash)
        
        st.session_state.messages.append({
            "role": "user",
            "content": f"Uploaded: **{uploaded_file.name}**"
        })
        
        with st.spinner("Analyzing..."):
            response = generate_response("", file_data=uploaded_file)
        
        st.session_state.messages.append({
            "role": "assistant",
            "content": response
        })
        st.rerun()

# Display chat
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"], unsafe_allow_html=True)

# Chat input
if prompt := st.chat_input("Ask anything..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    with st.chat_message("user"):
        st.markdown(prompt)
    
    with st.chat_message("assistant"):
        with st.spinner(""):
            response = generate_response(prompt)
        st.markdown(response, unsafe_allow_html=True)
    
    st.session_state.messages.append({"role": "assistant", "content": response})
