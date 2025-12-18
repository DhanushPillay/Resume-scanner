# Resume Scanner - Frontend

This is the standalone frontend for the Resume Scanner AI application. It connects to your deployed backend API via REST endpoints.

## 📁 Project Structure

```
frontend/
├── index.html      # Main HTML page
├── css/
│   └── style.css   # Styles
└── js/
    ├── config.js   # ⚠️ API URL configuration
    └── app.js      # Application logic
```

## 🚀 Setup

### 1. Configure API URL

Edit `js/config.js` and update `API_BASE_URL` to your deployed backend:

```javascript
const CONFIG = {
    // Change this to your Render URL
    API_BASE_URL: 'https://resume-scanner-api.onrender.com',
    ...
};
```

### 2. Deploy Frontend

**Option A: GitHub Pages (Free)**
1. Push this folder to a GitHub repo
2. Go to Settings → Pages → Deploy from branch
3. Select `main` branch and `/frontend` folder

**Option B: Netlify (Free)**
1. Go to [netlify.com](https://netlify.com)
2. Drag and drop this folder
3. Done!

**Option C: Vercel (Free)**
1. Install Vercel CLI: `npm i -g vercel`
2. Run `vercel` in this folder
3. Follow prompts

**Option D: Open Locally**
Just open `index.html` in a browser (for testing)

## 🔧 Backend Requirements

Your backend (Render) must:

1. **Have CORS enabled** (already configured in `api.py`)
2. **Expose these endpoints:**
   - `POST /api/analyze` - Upload resume
   - `POST /api/chat` - Chat messages
   - `GET /api/candidates` - List candidates
   - `GET /api/health` - Health check

3. **Set environment variables on your platform:**
   - `GROQ_API_KEY` - For AI chat
   - `GITHUB_TOKEN` - For GitHub verification

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    FRONTEND                              │
│         (Netlify / GitHub Pages / Vercel)               │
│                                                          │
│   index.html + style.css + app.js + config.js           │
│                                                          │
│   User uploads resume → calls API → displays results    │
└───────────────────────────┬─────────────────────────────┘
                            │ HTTPS REST API
                            ▼
┌─────────────────────────────────────────────────────────┐
│                    BACKEND API                           │
│                     (Render)                             │
│                                                          │
│   Flask + Gunicorn                                       │
│   /api/analyze  - Resume parsing & verification         │
│   /api/chat     - AI-powered HR assistant               │
│   /api/health   - Connection status                     │
│                                                          │
│   Environment Variables:                                 │
│   - GROQ_API_KEY                                         │
│   - GITHUB_TOKEN                                         │
└─────────────────────────────────────────────────────────┘
```

## ⚠️ Security Notes

- **Never put API keys in frontend code**
- API keys are safely stored in backend environment variables
- Frontend only calls your backend, never external APIs directly
- CORS is configured to allow requests from any origin

## 🧪 Local Development

1. Start backend locally:
   ```bash
   cd ..
   python api.py
   ```

2. Open `index.html` in your browser
   - Config auto-detects localhost and uses `http://localhost:5000`
