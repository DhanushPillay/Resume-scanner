"""
Resume Scanner API - Flask Backend
Provides REST API endpoints for the Resume Scanner application.
"""

from flask import Flask, request, jsonify, render_template, send_from_directory
from flask_cors import CORS
import os
import tempfile
import hashlib
import json
from dotenv import load_dotenv
from groq import Groq

from src.parser import ResumeParser
from src.company_validator import CompanyValidator
from src.candidate_validator import CandidateValidator
from src.risk_engine import RiskEngine

# Load environment variables
load_dotenv()

app = Flask(__name__, static_folder='static', template_folder='templates')
CORS(app)

# Initialize modules
parser = ResumeParser()
company_validator = CompanyValidator(opencorporates_api_token=os.getenv("OPENCORPORATES_API_TOKEN"))
candidate_validator = CandidateValidator(github_token=os.getenv("GITHUB_TOKEN"))
risk_engine = RiskEngine()

# Initialize Groq AI
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# In-memory storage
candidates = {}
chat_history = []

def get_file_hash(file_content):
    """Generate hash for file content."""
    return hashlib.md5(file_content).hexdigest()

def analyze_resume(file_content, filename):
    """Analyze a resume file and return results."""
    # Save to temp file
    suffix = '.pdf' if filename.lower().endswith('.pdf') else '.docx'
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(file_content)
        tmp_path = tmp.name
    
    try:
        # Parse resume
        with open(tmp_path, 'rb') as f:
            file_type = 'pdf' if suffix == '.pdf' else 'docx'
            parsed_data = parser.parse(f, file_type)
        
        # Verify companies
        company_verifications = []
        for company in parsed_data.get('companies', [])[:5]:
            verification = company_validator.verify_company(company)
            company_verifications.append({
                'company': company,
                'status': verification.get('status', 'UNKNOWN'),
                'sources_checked': verification.get('sources_checked', []),
                'registrations_found': verification.get('registrations_found', [])
            })
        
        # Verify candidate (GitHub/LinkedIn)
        candidate_verification = {'github': None, 'linkedin': None}
        urls = parsed_data.get('urls', {})
        
        if urls.get('github'):
            candidate_verification['github'] = candidate_validator.verify_github(
                urls['github'], 
                parsed_data.get('skills', [])
            )
        
        if urls.get('linkedin'):
            candidate_verification['linkedin'] = candidate_validator.verify_linkedin(
                urls['linkedin'],
                parsed_data.get('name', '')
            )
        
        # Calculate risk
        risk_analysis = risk_engine.analyze_risk(
            parsed_data,
            company_verifications,
            candidate_verification
        )
        
        # Store candidate
        name = parsed_data.get('name', 'Unknown')
        result = {
            'parsed_data': parsed_data,
            'company_verifications': company_verifications,
            'candidate_verification': candidate_verification,
            'risk_analysis': risk_analysis
        }
        candidates[name] = result
        
        return result
        
    finally:
        os.unlink(tmp_path)

def get_ai_response(user_message):
    """Use Groq AI to generate intelligent responses for HR."""
    # Build context from candidates
    candidates_context = ""
    if candidates:
        for name, data in candidates.items():
            parsed = data['parsed_data']
            risk = data['risk_analysis']
            candidates_context += f"""
Candidate: {name}
- Trust Score: {risk['trust_score']}/100
- Risk Level: {risk['risk_level']['level']}
- Skills: {', '.join(parsed.get('skills', [])[:10])}
- Experience: {parsed.get('total_experience', {}).get('experience_text', 'Unknown')}
- Email: {parsed.get('email', 'N/A')}
"""
            gh = data['candidate_verification'].get('github', {})
            if gh and gh.get('valid'):
                candidates_context += f"- GitHub: @{gh.get('username')} ({gh.get('public_repos', 0)} repos)\n"
    
    system_prompt = f"""You are an AI HR assistant for Resume Scanner. You help HR professionals analyze candidates and make hiring decisions.

Current analyzed candidates:
{candidates_context if candidates_context else "No candidates analyzed yet."}

Your capabilities:
- Analyze and compare candidates
- Provide hiring recommendations
- Answer questions about candidate skills, experience, risk scores
- Explain risk flags and trust scores
- Help with interview questions

Be concise, professional, and helpful. Format responses in HTML for display."""

    try:
        chat_history.append({"role": "user", "content": user_message})
        
        messages = [{"role": "system", "content": system_prompt}] + chat_history[-10:]
        
        response = groq_client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=messages,
            max_tokens=1000,
            temperature=0.7
        )
        
        ai_response = response.choices[0].message.content
        chat_history.append({"role": "assistant", "content": ai_response})
        
        return ai_response
    except Exception as e:
        return f"<p>AI is currently unavailable. Error: {str(e)}</p>"

def format_response(result):
    """Format analysis result as HTML."""
    data = result['parsed_data']
    risk = result['risk_analysis']
    
    score = risk['trust_score']
    level = risk['risk_level']
    
    # Trust badge color
    if score >= 70:
        badge_class = 'trust-high'
    elif score >= 50:
        badge_class = 'trust-medium'
    else:
        badge_class = 'trust-low'
    
    html = f"""
    <div class="report">
        <h2>{data.get('name', 'Unknown')}</h2>
        <div class="trust-badge {badge_class}">
            Trust Score: {score}/100 - {level['level']} RISK
        </div>
        
        <div class="section">
            <h3>Basic Info</h3>
            <p><strong>Email:</strong> {data.get('email', 'N/A')}</p>
            <p><strong>Phone:</strong> {data.get('phone', 'N/A')}</p>
            <p><strong>Experience:</strong> {data.get('total_experience', {}).get('experience_text', 'N/A')}</p>
            <p><strong>Skills:</strong> {', '.join(data.get('skills', [])[:10]) or 'None detected'}</p>
        </div>
    """
    
    # Education
    education = data.get('education', [])
    if education:
        html += '<div class="section"><h3>Education</h3>'
        for edu in education[:3]:
            edu_text = edu.get('degree', '')
            if edu.get('field'):
                edu_text += f" in {edu.get('field')}"
            if edu.get('institution'):
                edu_text += f" - {edu.get('institution')}"
            html += f"<p>{edu_text}</p>"
        html += '</div>'
    
    # Companies
    companies = result['company_verifications']
    if companies:
        html += '<div class="section"><h3>Company Verification</h3>'
        for comp in companies:
            status = comp.get('status', 'UNKNOWN')
            icon = '✓' if status == 'REGISTERED' else '?' if status == 'LIKELY_REGISTERED' else '✗'
            html += f"<p>{icon} <strong>{comp['company']}</strong>: {status}</p>"
        html += '</div>'
    
    # GitHub
    gh = result['candidate_verification'].get('github', {})
    if gh and gh.get('valid'):
        html += f"""
        <div class="section">
            <h3>GitHub Verified</h3>
            <p>@{gh.get('username')} - {gh.get('public_repos', 0)} repos</p>
            <p>Languages: {', '.join(gh.get('top_languages', [])[:4]) or 'None'}</p>
        </div>
        """
    
    # Risk flags
    flags = risk.get('risk_flags', [])
    if flags:
        html += '<div class="section"><h3>Risk Flags</h3>'
        for flag in flags[:5]:
            severity = flag.get('severity', 'INFO')
            html += f"<p class='flag-{severity.lower()}'>[{severity}] {flag['message']}</p>"
        html += '</div>'
    
    html += f"<p class='summary'>{risk.get('summary', '')}</p></div>"
    
    return html

@app.route('/')
def index():
    """Serve the main page."""
    return render_template('index.html')

@app.route('/api/analyze', methods=['POST'])
def analyze():
    """Analyze uploaded resume."""
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    # Check file type
    if not file.filename.lower().endswith(('.pdf', '.docx')):
        return jsonify({'error': 'Invalid file type. Use PDF or DOCX'}), 400
    
    try:
        file_content = file.read()
        result = analyze_resume(file_content, file.filename)
        html_response = format_response(result)
        
        return jsonify({
            'success': True,
            'html': html_response,
            'data': {
                'name': result['parsed_data'].get('name'),
                'score': result['risk_analysis']['trust_score']
            }
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/chat', methods=['POST'])
def chat():
    """Handle chat messages with AI."""
    data = request.json
    message = data.get('message', '').strip()
    
    if not message:
        return jsonify({'error': 'No message provided'}), 400
    
    # Check for GitHub/LinkedIn links first
    import re
    github_match = re.search(r'github\.com/([a-zA-Z0-9_-]+)', message)
    linkedin_match = re.search(r'linkedin\.com/in/([a-zA-Z0-9_-]+)', message)
    
    response_html = ""
    
    if github_match:
        username = github_match.group(1)
        url = f"https://github.com/{username}"
        result = candidate_validator.verify_github(url, [])
        
        if result.get('valid'):
            response_html = f"""
            <div class="section">
                <h3>GitHub Profile: @{result.get('username')}</h3>
                <p><strong>Repos:</strong> {result.get('public_repos', 0)} ({result.get('original_repos', 0)} original)</p>
                <p><strong>Account Age:</strong> {result.get('account_age_months', 0)} months</p>
                <p><strong>Languages:</strong> {', '.join(result.get('top_languages', [])[:5]) or 'None'}</p>
            </div>
            """
        else:
            response_html = f"<p>Could not verify GitHub profile: {result.get('error', 'Unknown error')}</p>"
    
    elif linkedin_match:
        slug = linkedin_match.group(1)
        url = f"https://linkedin.com/in/{slug}"
        result = candidate_validator.verify_linkedin(url, "")
        status = "Accessible" if result.get('valid') else "Not accessible"
        response_html = f"<p><strong>LinkedIn:</strong> {status}</p>"
    
    else:
        # Use AI for all other messages
        response_html = get_ai_response(message)
    
    return jsonify({'html': response_html})

@app.route('/api/candidates', methods=['GET'])
def get_candidates():
    """Get list of analyzed candidates."""
    return jsonify({
        'candidates': [
            {
                'name': name,
                'score': data['risk_analysis']['trust_score']
            }
            for name, data in candidates.items()
        ]
    })

if __name__ == '__main__':
    app.run(debug=True, port=5000)
