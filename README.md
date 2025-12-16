# Resume Scanner AI

AI-powered resume analysis tool with GitHub/LinkedIn verification and company registration checks.

## Features

- **Resume Parsing** - Extract skills, education, experience from PDF/DOCX
- **GitHub Deep Scan** - Analyze repos, languages, activity
- **LinkedIn Verification** - Check profile accessibility
- **Company Registry Check** - Verify employers (UK, US, India)
- **Risk Assessment** - Trust score with detailed flags

## Tech Stack

- **Backend**: Flask, Python, spaCy
- **Frontend**: HTML, CSS, JavaScript
- **APIs**: GitHub API, OpenCorporates

## Local Development

```bash
# Install dependencies
pip install -r requirements.txt
python download_model.py

# Set environment variables
cp .env.example .env
# Edit .env with your API keys

# Run
python api.py
```

## Deployment (Render)

1. Push to GitHub
2. Connect repo to [Render](https://render.com)
3. Set environment variables:
   - `GITHUB_TOKEN`
   - `OPENCORPORATES_API_TOKEN` (optional)
4. Deploy

## Project Structure

```
Resume-scanner/
├── api.py              # Flask API
├── templates/
│   └── index.html      # Frontend
├── static/
│   ├── css/style.css   # Styles
│   └── js/app.js       # Frontend JS
├── src/
│   ├── parser.py       # Resume parsing
│   ├── candidate_validator.py
│   ├── company_validator.py
│   └── risk_engine.py
├── render.yaml         # Render config
├── Procfile            # Process file
└── requirements.txt
```

## License

MIT
