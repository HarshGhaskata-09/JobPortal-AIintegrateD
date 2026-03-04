# Job Recommender System

An AI-powered job recommendation platform connecting job seekers with employers using machine learning algorithms.

## Features

- **Job Seekers**: Profile management, AI recommendations, job search, application tracking
- **Employers**: Post jobs, manage applications, candidate search, analytics
- **Admin**: User management, job moderation, platform statistics
- **AI Chatbot**: Interactive job finder, career advice, interview tips

## Quick Start

### Installation

1. **Create virtual environment**
   ```bash
   python -m venv venv
   ```

2. **Activate virtual environment**
   ```bash
   # Windows
   .\venv\Scripts\activate
   
   # Linux/Mac
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run application**
   ```bash
   python -m app.run
   ```

5. **Access application**
   - URL: `http://localhost:5000`
   - Admin: `admin@jobportal.com` / `Admin@123`

## Technology Stack

- **Backend**: Flask, SQLAlchemy, SQLite
- **Frontend**: Bootstrap 5, JavaScript
- **ML**: Scikit-learn, Pandas, NumPy
- **Auth**: Flask-Login, Bcrypt

## Project Structure

```
job-recommender/
├── app/                 # Application code
│   ├── models/         # Database models
│   ├── routes/         # Route handlers
│   ├── ml_models/      # ML recommendation engine
│   ├── templates/      # HTML templates
│   ├── static/         # CSS, JS, images
│   └── utils/          # Helper functions
├── data/               # CSV datasets
├── instance/           # SQLite database
├── venv/               # Virtual environment
├── config.py           # Configuration
├── requirements.txt    # Dependencies
├── README.md          # This file
└── SETUP.txt          # Detailed setup guide
```

## User Roles

1. **Job Seekers** - Search jobs, apply, get recommendations
2. **Employers** - Post jobs, manage applications
3. **Admin** - Platform management and moderation

## Admin Access

- Login with admin credentials
- Click profile dropdown → "Admin Dashboard"
- Or visit: `http://localhost:5000/admin`

## Key Features

### AI Chatbot
- Interactive job finder
- Natural language search
- Career guidance
- Interview preparation
- Salary negotiation tips

### Job Recommendations
- ML-powered matching
- Skill-based filtering
- Experience level matching
- Location preferences

### Search & Filters
- Full-text search
- Location (Indian + International)
- Salary range
- Job category
- Skills required

## Documentation

For detailed setup instructions, configuration, and troubleshooting, see **SETUP.txt**

## Security

- Password hashing (Bcrypt)
- CSRF protection
- SQL injection prevention
- XSS protection
- Secure file uploads

## Support

- Email: harshghaskata155@gmail.com
- Check SETUP.txt for detailed documentation

---

**Version**: 1.0.0  
**Last Updated**: March 2026  
**Developed by**: Job Recruiter Team