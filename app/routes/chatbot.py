from flask import Blueprint, request, jsonify, render_template, session
from flask_login import current_user, login_required
from app.models.job import Job, JobCategory, SavedJob, JobApplication
from app.models.user import User
from app.ml_models.recommender import JobRecommender
from app import db
from datetime import datetime, timedelta
import re
import logging

bp = Blueprint('chatbot', __name__, url_prefix='/chatbot')

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class JobSearchChatbot:
    """Advanced AI-powered chatbot for job search assistance with database integration"""
    
    def __init__(self):
        self.recommender = JobRecommender()
        self.conversation_history = []
        
    def process_message(self, message, user_id=None, session_data=None):
        """Process user message with error handling and return appropriate response"""
        try:
            # Sanitize input
            message = self._sanitize_input(message)
            if not message:
                return self._error_response("Please enter a valid message")
            
            # Store in conversation history
            self.conversation_history.append({'role': 'user', 'message': message, 'timestamp': datetime.utcnow()})
            
            # Check if we're in an interactive session
            if session_data and session_data.get('mode') == 'interactive_search':
                return self._handle_interactive_search(message, session_data)
            
            message_lower = message.lower().strip()
            
            # Greeting patterns
            if any(word in message_lower for word in ['hello', 'hi', 'hey', 'greetings', 'start']):
                return self._greeting_response(user_id)
            
            # Interactive job finder (check before general help)
            if any(phrase in message_lower for phrase in ['find job', 'help me find', 'job for me', 'looking for job', 'need job', 'want job']):
                return self._start_interactive_search()
            
            # Help patterns
            if any(word in message_lower for word in ['help', 'what can you do', 'how to use', 'guide']):
                return self._help_response()
            
            # Recent/Latest jobs
            if any(word in message_lower for word in ['recent', 'latest', 'new', 'newest', 'fresh']):
                return self._get_recent_jobs()
            
            # All jobs
            if any(phrase in message_lower for phrase in ['all jobs', 'browse jobs', 'show all', 'list jobs']):
                return self._get_all_jobs()
            
            # Skill gap analysis
            if any(phrase in message_lower for phrase in ['skill gap', 'missing skills', 'what skills', 'skills needed']):
                return self._skill_gap_help(user_id)
            
            # Interview preparation
            if any(word in message_lower for word in ['interview', 'preparation', 'interview tips', 'prepare']):
                return self._interview_prep()
            
            # Salary negotiation
            if any(phrase in message_lower for phrase in ['salary negotiation', 'negotiate salary', 'salary tips']):
                return self._salary_negotiation_tips()
            
            # Career advice
            if any(phrase in message_lower for phrase in ['career advice', 'career tips', 'career growth']):
                return self._career_advice()
            
            # Job search patterns
            if any(word in message_lower for word in ['find', 'search', 'looking for', 'show me']):
                return self._search_jobs(message, user_id)
            
            # Recommendation patterns
            if any(word in message_lower for word in ['recommend', 'suggest', 'match', 'suitable', 'for me']):
                return self._get_recommendations(user_id)
            
            # Skill-based search
            if 'skill' in message_lower:
                return self._search_by_skills(message)
            
            # Location-based search
            if any(word in message_lower for word in ['location', 'where', 'remote']):
                return self._search_by_location(message)
            
            # Salary-based search
            if any(word in message_lower for word in ['salary', 'pay', 'wage', 'compensation']):
                return self._search_by_salary(message)
            
            # Category search
            if any(word in message_lower for word in ['category', 'type', 'field']):
                return self._search_by_category(message)
            
            # Application help
            if any(word in message_lower for word in ['apply', 'application']):
                return self._application_help()
            
            # Profile help
            if any(word in message_lower for word in ['profile', 'resume']):
                return self._profile_help()
            
            # My applications
            if any(phrase in message_lower for phrase in ['my applications', 'applied jobs', 'application status']):
                return self._my_applications(user_id)
            
            # Saved jobs
            if any(phrase in message_lower for phrase in ['saved jobs', 'bookmarked', 'favorites']):
                return self._my_saved_jobs(user_id)
            
            # Default response
            return self._default_response()
            
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")
            return self._error_response("Something went wrong. Please try again.")

    
    def _sanitize_input(self, message):
        """Sanitize user input"""
        if not message or not isinstance(message, str):
            return ""
        # Remove excessive whitespace and limit length
        message = ' '.join(message.split())
        return message[:500]  # Limit to 500 characters
    
    def _error_response(self, error_message):
        """Generate error response"""
        return {
            'message': error_message,
            'suggestions': ['Try again', 'Show all jobs', 'Get help']
        }
    
    def _greeting_response(self, user_id):
        """Generate personalized greeting response"""
        try:
            user_name = ""
            if user_id:
                user = User.query.get(user_id)
                if user and user.full_name:
                    user_name = f", {user.full_name.split()[0]}"
            
            # Get job statistics
            total_jobs = Job.query.filter_by(is_active=True).count()
            recent_jobs = Job.query.filter(
                Job.is_active == True,
                Job.created_at >= datetime.utcnow() - timedelta(days=7)
            ).count()
            
            return {
                'message': f"Hello{user_name}! I'm your AI job search assistant.\n\nWe currently have {total_jobs} active jobs, with {recent_jobs} posted in the last week!\n\nI can help you:\n• Find jobs matching your skills\n• Get personalized recommendations\n• Browse recent postings\n• Search by location, salary, or category\n• Analyze skill gaps for specific jobs\n• Provide interview preparation tips\n• Offer salary negotiation advice\n\nWhat would you like to explore?",
                'suggestions': [
                    'Show recent jobs',
                    'Recommend jobs for me',
                    'Help me find a job',
                    'Interview tips'
                ]
            }
        except Exception as e:
            logger.error(f"Error in greeting: {str(e)}")
            return self._error_response("Welcome! How can I help you today?")

    
    def _help_response(self):
        """Generate comprehensive help response"""
        return {
            'message': """I can help you with:

Interactive Job Finder: "Help me find a job" - I'll ask questions to find perfect matches

Job Browsing:
• "Show recent jobs" - Latest postings
• "Show all jobs" - Browse all positions
• "Find [role] jobs" - Search specific roles

Smart Search:
• "Jobs in [location]" - Location-based search
• "Remote jobs" - Work from anywhere
• "Jobs paying over [amount]" - Salary-based search
• "Jobs requiring [skill]" - Skill-based search

Personalized:
• "Recommend jobs for me" - AI-powered recommendations
• "My applications" - Track your applications
• "Saved jobs" - View bookmarked positions

Career Help:
• "Interview tips" - Preparation guidance
• "Salary negotiation" - Negotiation strategies
• "Career advice" - Growth tips
• "Skill gap analysis" - Identify missing skills

Profile:
• "How to improve my profile?" - Profile optimization
• "Application tips" - Better applications

Just ask me naturally, and I'll help you find what you're looking for!""",
            'suggestions': [
                'Help me find a job',
                'Show recent jobs',
                'Interview tips',
                'Recommend jobs'
            ]
        }

    
    def _start_interactive_search(self):
        """Start interactive job search session"""
        return {
            'message': """Great! I'll help you find the perfect job. Let me ask you a few questions.

Question 1 of 4: What type of job are you looking for?
For example: Software Developer, Designer, Marketing Manager, Data Analyst, etc.

Type your desired job title or role:""",
            'session': {
                'mode': 'interactive_search',
                'step': 1,
                'data': {}
            },
            'suggestions': [
                'Software Developer',
                'Data Analyst',
                'Marketing Manager',
                'UI/UX Designer'
            ]
        }
    
    def _handle_interactive_search(self, message, session_data):
        """Handle interactive search conversation flow"""
        try:
            step = session_data.get('step', 1)
            data = session_data.get('data', {})
            
            if step == 1:
                # Collect job title
                data['job_title'] = message
                return {
                    'message': f"""Perfect! Looking for {message} positions.

Question 2 of 4: What are your key skills?
List your main skills separated by commas.

For example: Python, JavaScript, React, SQL""",
                    'session': {
                        'mode': 'interactive_search',
                        'step': 2,
                        'data': data
                    },
                    'suggestions': [
                        'Python, Django, SQL',
                        'JavaScript, React, Node.js',
                        'Java, Spring Boot, MySQL',
                        'Skip this question'
                    ]
                }
            
            elif step == 2:
                # Collect skills
                if message.lower() != 'skip this question':
                    data['skills'] = message
                return {
                    'message': """Question 3 of 4: Where would you like to work?

Type a city/country name or "Remote" for remote positions:""",
                    'session': {
                        'mode': 'interactive_search',
                        'step': 3,
                        'data': data
                    },
                    'suggestions': [
                        'Remote',
                        'Mumbai, India',
                        'Bangalore, India',
                        'Delhi, India',
                        'New York, USA',
                        'London, UK',
                        'Singapore',
                        'Any location'
                    ]
                }
            
            elif step == 3:
                # Collect location
                if message.lower() != 'any location':
                    data['location'] = message
                return {
                    'message': """Question 4 of 4: What's your expected salary range?

Type minimum salary (e.g., "80000" or "80k") or "Skip":""",
                    'session': {
                        'mode': 'interactive_search',
                        'step': 4,
                        'data': data
                    },
                    'suggestions': [
                        '60000',
                        '80000',
                        '100000',
                        'Skip'
                    ]
                }
            
            elif step == 4:
                # Collect salary and search
                if message.lower() != 'skip':
                    # Extract number from message
                    salary_match = re.findall(r'\d+', message)
                    if salary_match:
                        data['min_salary'] = int(salary_match[0])
                        if data['min_salary'] < 1000:  # Assume it's in thousands
                            data['min_salary'] *= 1000
                
                # Now search based on collected data
                return self._search_with_criteria(data)
            
            return self._default_response()
            
        except Exception as e:
            logger.error(f"Error in interactive search: {str(e)}")
            return self._error_response("Something went wrong. Let's start over.")

    
    def _search_with_criteria(self, criteria):
        """Search jobs based on collected criteria with proper error handling"""
        try:
            query = Job.query.filter_by(is_active=True)
            
            # Filter by job title (case-insensitive)
            if criteria.get('job_title'):
                query = query.filter(
                    db.or_(
                        Job.title.ilike(f"%{criteria['job_title']}%"),
                        Job.description.ilike(f"%{criteria['job_title']}%")
                    )
                )
            
            # Filter by skills (case-insensitive)
            if criteria.get('skills'):
                skills = [s.strip() for s in criteria['skills'].split(',')]
                for skill in skills:
                    if skill:
                        query = query.filter(Job.required_skills.ilike(f"%{skill}%"))
            
            # Filter by location (case-insensitive)
            if criteria.get('location'):
                query = query.filter(Job.location.ilike(f"%{criteria['location']}%"))
            
            # Filter by salary
            if criteria.get('min_salary'):
                query = query.filter(Job.salary_min >= criteria['min_salary'])
            
            jobs = query.order_by(Job.created_at.desc()).limit(10).all()
            
            # Build summary message
            summary_parts = []
            if criteria.get('job_title'):
                summary_parts.append(f"Role: {criteria['job_title']}")
            if criteria.get('skills'):
                summary_parts.append(f"Skills: {criteria['skills']}")
            if criteria.get('location'):
                summary_parts.append(f"Location: {criteria['location']}")
            if criteria.get('min_salary'):
                summary_parts.append(f"Min Salary: ${criteria['min_salary']:,}")
            
            summary = "\n".join(summary_parts)
            
            if jobs:
                job_list = self._format_job_list(jobs)
                return {
                    'message': f"""Based on your requirements:

{summary}

I found {len(jobs)} matching jobs:

{job_list}""",
                    'jobs': [{'id': j.id, 'title': j.title, 'company': j.company, 'location': j.location} for j in jobs],
                    'session': None,
                    'suggestions': [
                        'Find another job',
                        'Show more details',
                        'Get recommendations'
                    ]
                }
            else:
                return {
                    'message': f"""Based on your requirements:

{summary}

I couldn't find exact matches. Here are some suggestions:

• Try broader search terms
• Consider related job titles
• Expand location preferences
• Adjust salary expectations

Would you like to try again?""",
                    'session': None,
                    'suggestions': [
                        'Help me find a job',
                        'Show all jobs',
                        'Browse by category',
                        'Get recommendations'
                    ]
                }
        except Exception as e:
            logger.error(f"Error in search with criteria: {str(e)}")
            return self._error_response("Search failed. Please try again.")

    
    def _get_recent_jobs(self):
        """Get recently posted jobs with error handling"""
        try:
            week_ago = datetime.utcnow() - timedelta(days=7)
            jobs = Job.query.filter(
                Job.is_active == True,
                Job.created_at >= week_ago
            ).order_by(Job.created_at.desc()).limit(10).all()
            
            if jobs:
                job_list = self._format_job_list(jobs)
                return {
                    'message': f"Here are {len(jobs)} jobs posted in the last week:\n\n{job_list}",
                    'jobs': [{'id': j.id, 'title': j.title, 'company': j.company, 'location': j.location, 'posted': self._time_ago(j.created_at)} for j in jobs],
                    'suggestions': [
                        'Show more details',
                        'Filter by location',
                        'Recommend similar',
                        'Browse all jobs'
                    ]
                }
            else:
                return {
                    'message': "No new jobs posted in the last week. Check out all available positions!",
                    'suggestions': [
                        'Browse all jobs',
                        'Search by skills',
                        'Remote jobs',
                        'Get recommendations'
                    ]
                }
        except Exception as e:
            logger.error(f"Error getting recent jobs: {str(e)}")
            return self._error_response("Could not fetch recent jobs.")
    
    def _get_all_jobs(self):
        """Get all active jobs with pagination"""
        try:
            jobs = Job.query.filter_by(is_active=True).order_by(Job.created_at.desc()).limit(15).all()
            
            if jobs:
                total_count = Job.query.filter_by(is_active=True).count()
                job_list = self._format_job_list(jobs)
                
                message = f"Showing {len(jobs)} of {total_count} active jobs:\n\n{job_list}"
                if total_count > 15:
                    message += f"\n\nVisit the jobs page to see all {total_count} positions!"
                
                return {
                    'message': message,
                    'jobs': [{'id': j.id, 'title': j.title, 'company': j.company, 'location': j.location} for j in jobs],
                    'suggestions': [
                        'Filter by skills',
                        'Remote jobs only',
                        'Recommend for me',
                        'Search specific role'
                    ]
                }
            else:
                return {
                    'message': "No active jobs available at the moment. Check back soon!",
                    'suggestions': [
                        'Update my profile',
                        'View categories'
                    ]
                }
        except Exception as e:
            logger.error(f"Error getting all jobs: {str(e)}")
            return self._error_response("Could not fetch jobs.")

    
    def _search_jobs(self, message, user_id):
        """Search for jobs based on message content with improved matching"""
        try:
            keywords = self._extract_keywords(message)
            
            if not keywords:
                return {
                    'message': "I'd love to help you search! Could you tell me what kind of job you're looking for? For example: 'Find Python developer jobs' or 'Show me marketing positions'",
                    'suggestions': [
                        'Software developer jobs',
                        'Remote positions',
                        'Entry level jobs',
                        'Senior positions'
                    ]
                }
            
            # Search jobs with case-insensitive matching
            query = Job.query.filter_by(is_active=True)
            
            for keyword in keywords:
                query = query.filter(
                    db.or_(
                        Job.title.ilike(f"%{keyword}%"),
                        Job.description.ilike(f"%{keyword}%"),
                        Job.required_skills.ilike(f"%{keyword}%")
                    )
                )
            
            jobs = query.order_by(Job.created_at.desc()).limit(10).all()
            
            if jobs:
                job_list = self._format_job_list(jobs)
                return {
                    'message': f"I found {len(jobs)} jobs matching '{' '.join(keywords)}':\n\n{job_list}",
                    'jobs': [{'id': j.id, 'title': j.title, 'company': j.company, 'location': j.location} for j in jobs],
                    'suggestions': [
                        'Show me more details',
                        'Recommend similar jobs',
                        'Filter by location',
                        'Search something else'
                    ]
                }
            else:
                return {
                    'message': f"I couldn't find jobs matching '{' '.join(keywords)}'. Try:\n• Using different keywords\n• Broadening your search\n• Checking our job categories",
                    'suggestions': [
                        'Show all jobs',
                        'Browse by category',
                        'Remote jobs',
                        'Recent postings'
                    ]
                }
        except Exception as e:
            logger.error(f"Error searching jobs: {str(e)}")
            return self._error_response("Search failed. Please try again.")
    
    def _get_recommendations(self, user_id):
        """Get personalized job recommendations with ML integration"""
        try:
            if not user_id:
                return {
                    'message': "To get personalized recommendations, please log in first. I'll analyze your skills and experience to find the best matches for you!",
                    'suggestions': [
                        'Browse all jobs',
                        'Search by category',
                        'Remote jobs'
                    ]
                }
            
            user = User.query.get(user_id)
            if not user:
                return self._error_response("User not found.")
            
            if not user.skills:
                return {
                    'message': "I'd love to recommend jobs, but I need to know your skills first! Please update your profile with your skills and experience.",
                    'suggestions': [
                        'Go to profile settings',
                        'Browse all jobs',
                        'Search by category'
                    ]
                }
            
            # Try ML recommendations
            try:
                self.recommender.prepare_job_data()
                recommendations = self.recommender.get_hybrid_recommendations(user_id, 5)
                
                if recommendations:
                    job_list = self._format_recommendation_list(recommendations)
                    return {
                        'message': f"Based on your profile, here are my top recommendations:\n\n{job_list}",
                        'jobs': [{'id': r['job'].id, 'title': r['job'].title, 'company': r['job'].company, 'score': r['score']} for r in recommendations],
                        'suggestions': [
                            'Show more recommendations',
                            'Filter by location',
                            'View job details',
                            'Update my skills'
                        ]
                    }
            except Exception as ml_error:
                logger.error(f"ML recommendation failed: {str(ml_error)}")
                # Fallback to simple skill matching
                return self._fallback_recommendations(user)
            
            return {
                'message': "I'm working on finding the perfect matches for you. In the meantime, check out our featured jobs!",
                'suggestions': [
                    'Browse all jobs',
                    'Update my profile',
                    'Search by skills'
                ]
            }
        except Exception as e:
            logger.error(f"Error getting recommendations: {str(e)}")
            return self._error_response("Could not generate recommendations.")

    
    def _fallback_recommendations(self, user):
        """Fallback recommendation when ML fails"""
        try:
            user_skills = user.get_skills_list()
            if not user_skills:
                return self._get_all_jobs()
            
            query = Job.query.filter_by(is_active=True)
            for skill in user_skills[:3]:  # Use top 3 skills
                query = query.filter(Job.required_skills.ilike(f"%{skill}%"))
            
            jobs = query.order_by(Job.created_at.desc()).limit(5).all()
            
            if jobs:
                job_list = self._format_job_list(jobs)
                return {
                    'message': f"Based on your skills ({', '.join(user_skills[:3])}), here are some matches:\n\n{job_list}",
                    'jobs': [{'id': j.id, 'title': j.title, 'company': j.company} for j in jobs],
                    'suggestions': ['Show more', 'Update skills', 'Browse all']
                }
            else:
                return self._get_all_jobs()
        except Exception as e:
            logger.error(f"Fallback recommendation failed: {str(e)}")
            return self._get_all_jobs()
    
    def _search_by_skills(self, message):
        """Search jobs by skills with improved matching"""
        try:
            skills = self._extract_keywords(message)
            
            if not skills:
                return {
                    'message': "What skills are you looking for? For example: 'Python', 'JavaScript', 'Design', 'Marketing'",
                    'suggestions': [
                        'Python jobs',
                        'JavaScript positions',
                        'Design roles',
                        'Marketing jobs'
                    ]
                }
            
            query = Job.query.filter_by(is_active=True)
            for skill in skills:
                query = query.filter(Job.required_skills.ilike(f"%{skill}%"))
            
            jobs = query.order_by(Job.created_at.desc()).limit(10).all()
            
            if jobs:
                job_list = self._format_job_list(jobs)
                return {
                    'message': f"Jobs requiring {', '.join(skills)}:\n\n{job_list}",
                    'jobs': [{'id': j.id, 'title': j.title, 'company': j.company} for j in jobs],
                    'suggestions': [
                        'Show more',
                        'Add more skills',
                        'Filter by location'
                    ]
                }
            else:
                return {
                    'message': f"No jobs found requiring {', '.join(skills)}. Try related skills or browse all jobs.",
                    'suggestions': [
                        'Browse all jobs',
                        'Try different skills',
                        'View categories'
                    ]
                }
        except Exception as e:
            logger.error(f"Error searching by skills: {str(e)}")
            return self._error_response("Skill search failed.")

    
    def _search_by_location(self, message):
        """Search jobs by location with support for Indian and international cities"""
        try:
            message_lower = message.lower()
            
            # Check for remote
            if 'remote' in message_lower:
                jobs = Job.query.filter(
                    Job.is_active == True,
                    Job.location.ilike('%Remote%')
                ).order_by(Job.created_at.desc()).limit(10).all()
                
                if jobs:
                    job_list = self._format_job_list(jobs)
                    return {
                        'message': f"Remote jobs available:\n\n{job_list}",
                        'jobs': [{'id': j.id, 'title': j.title, 'company': j.company} for j in jobs],
                        'suggestions': [
                            'Show more remote jobs',
                            'Filter by skills',
                            'View details'
                        ]
                    }
            
            # Extract location keywords
            locations = self._extract_keywords(message)
            if locations:
                query = Job.query.filter_by(is_active=True)
                for loc in locations:
                    query = query.filter(Job.location.ilike(f"%{loc}%"))
                jobs = query.order_by(Job.created_at.desc()).limit(10).all()
                
                if jobs:
                    job_list = self._format_job_list(jobs)
                    return {
                        'message': f"Jobs in {', '.join(locations)}:\n\n{job_list}",
                        'jobs': [{'id': j.id, 'title': j.title, 'company': j.company} for j in jobs],
                        'suggestions': [
                            'Show more',
                            'Filter by skills',
                            'Remote jobs'
                        ]
                    }
            
            return {
                'message': """Which location are you interested in?

Indian Cities:
• Mumbai, Bangalore, Delhi, Pune, Hyderabad, Chennai, Kolkata

International:
• New York, London, Singapore, Dubai, Toronto, Sydney

Or type "Remote" for remote positions""",
                'suggestions': [
                    'Remote',
                    'Mumbai, India',
                    'Bangalore, India',
                    'New York, USA',
                    'London, UK',
                    'Singapore'
                ]
            }
        except Exception as e:
            logger.error(f"Error searching by location: {str(e)}")
            return self._error_response("Location search failed.")
    
    def _search_by_salary(self, message):
        """Search jobs by salary with proper number extraction"""
        try:
            # Extract salary numbers
            numbers = re.findall(r'\d+', message)
            
            if numbers:
                min_salary = int(numbers[0])
                # Handle different formats (k, thousand, etc.)
                if min_salary < 1000:
                    min_salary *= 1000
                
                jobs = Job.query.filter(
                    Job.is_active == True,
                    Job.salary_min >= min_salary
                ).order_by(Job.salary_min.desc()).limit(10).all()
                
                if jobs:
                    job_list = self._format_job_list(jobs)
                    return {
                        'message': f"Jobs with salary ${min_salary:,}+:\n\n{job_list}",
                        'jobs': [{'id': j.id, 'title': j.title, 'company': j.company, 'salary': f"${j.salary_min:,} - ${j.salary_max:,}"} for j in jobs],
                        'suggestions': [
                            'Show more',
                            'Filter by location',
                            'Recommend for me'
                        ]
                    }
                else:
                    return {
                        'message': f"No jobs found with salary ${min_salary:,}+. Try a lower range or browse all jobs.",
                        'suggestions': [
                            'Browse all jobs',
                            'Try lower salary',
                            'Get recommendations'
                        ]
                    }
            
            return {
                'message': "What's your expected salary range? For example: 'Jobs paying over 80000' or 'Positions with 100k+ salary'",
                'suggestions': [
                    'Jobs over 80000',
                    'Jobs over 100000',
                    'High salary positions'
                ]
            }
        except Exception as e:
            logger.error(f"Error searching by salary: {str(e)}")
            return self._error_response("Salary search failed.")

    
    def _search_by_category(self, message):
        """Search jobs by category"""
        try:
            categories = JobCategory.query.all()
            
            # Try to match category in message
            for category in categories:
                if category.name.lower() in message.lower():
                    jobs = Job.query.filter_by(
                        is_active=True,
                        category_id=category.id
                    ).order_by(Job.created_at.desc()).limit(10).all()
                    
                    if jobs:
                        job_list = self._format_job_list(jobs)
                        return {
                            'message': f"{category.name} jobs:\n\n{job_list}",
                            'jobs': [{'id': j.id, 'title': j.title, 'company': j.company} for j in jobs],
                            'suggestions': [
                                'Show more',
                                'Filter by location',
                                'Recommend similar'
                            ]
                        }
            
            # Show available categories
            if categories:
                category_list = '\n'.join([f"• {cat.name}" for cat in categories])
                return {
                    'message': f"Available job categories:\n\n{category_list}\n\nWhich category interests you?",
                    'suggestions': [cat.name for cat in categories[:4]]
                }
            else:
                return self._get_all_jobs()
        except Exception as e:
            logger.error(f"Error searching by category: {str(e)}")
            return self._error_response("Category search failed.")
    
    def _skill_gap_help(self, user_id):
        """Provide skill gap analysis guidance"""
        if not user_id:
            return {
                'message': "To analyze skill gaps, please log in first. I'll compare your skills with job requirements and show you what to learn!",
                'suggestions': ['Browse jobs', 'Show all jobs']
            }
        
        return {
            'message': """Skill Gap Analysis helps you understand what skills you need to learn for your dream job!

How it works:
1. Find a job you're interested in
2. View the job details page
3. I'll show you:
   • Skills you already have
   • Skills you need to learn
   • Your match percentage
   • Learning resources

This helps you focus your learning and become a perfect candidate!

Would you like to browse jobs to analyze?""",
            'suggestions': [
                'Browse all jobs',
                'Find specific role',
                'Show recent jobs',
                'Career advice'
            ]
        }

    
    def _interview_prep(self):
        """Provide interview preparation tips"""
        return {
            'message': """Interview Preparation Tips:

Before the Interview:
• Research the company thoroughly
• Review the job description carefully
• Prepare answers for common questions
• Practice your elevator pitch
• Prepare questions to ask the interviewer
• Test your tech setup (for virtual interviews)

Common Questions to Prepare:
• Tell me about yourself
• Why do you want this job?
• What are your strengths and weaknesses?
• Describe a challenging situation you faced
• Where do you see yourself in 5 years?

Technical Interviews:
• Review fundamental concepts
• Practice coding problems
• Explain your thought process clearly
• Ask clarifying questions
• Test your code thoroughly

During the Interview:
• Arrive 10-15 minutes early
• Dress professionally
• Make eye contact and smile
• Listen carefully to questions
• Take a moment to think before answering
• Be honest about what you don't know

After the Interview:
• Send a thank-you email within 24 hours
• Reflect on what went well
• Follow up if you don't hear back in a week

Remember: Confidence comes from preparation!""",
            'suggestions': [
                'Career advice',
                'Salary negotiation tips',
                'Find jobs to apply',
                'Application tips'
            ]
        }
    
    def _salary_negotiation_tips(self):
        """Provide salary negotiation strategies"""
        return {
            'message': """Salary Negotiation Tips:

Research Phase:
• Research industry standards for your role
• Check salary ranges on job sites
• Consider your experience level
• Factor in location and company size
• Know your minimum acceptable salary

Before Negotiating:
• Wait for the offer before discussing salary
• Let them make the first offer
• Don't reveal your current salary
• Consider the total compensation package
• Benefits, bonuses, stock options matter too

During Negotiation:
• Express enthusiasm for the role first
• Use data to support your request
• Give a salary range, not a single number
• Be confident but not aggressive
• Consider asking for time to think

What to Say:
• "Based on my research and experience, I was expecting a range of [X-Y]"
• "I'm excited about this opportunity. Can we discuss the compensation?"
• "I'd like to understand the full benefits package"

If They Can't Meet Your Number:
• Ask about performance reviews and raises
• Negotiate signing bonus
• Request additional vacation days
• Ask for professional development budget
• Consider remote work options

Remember: Everything is negotiable, and companies expect you to negotiate!""",
            'suggestions': [
                'Interview tips',
                'Career advice',
                'Find high-paying jobs',
                'Application tips'
            ]
        }

    
    def _career_advice(self):
        """Provide career growth advice"""
        return {
            'message': """Career Growth Advice:

Building Your Career:
• Set clear short-term and long-term goals
• Continuously learn new skills
• Build a strong professional network
• Seek mentorship opportunities
• Document your achievements

Skill Development:
• Focus on in-demand skills in your field
• Take online courses and certifications
• Work on side projects
• Contribute to open source
• Attend industry events and conferences

Professional Branding:
• Keep your LinkedIn profile updated
• Build a portfolio showcasing your work
• Write blog posts or articles
• Speak at meetups or conferences
• Engage with your professional community

Job Search Strategy:
• Quality over quantity in applications
• Customize your resume for each role
• Network actively
• Follow up on applications
• Learn from rejections

Career Advancement:
• Take on challenging projects
• Volunteer for leadership roles
• Seek feedback regularly
• Build relationships with decision-makers
• Consider lateral moves for growth

Work-Life Balance:
• Set boundaries
• Prioritize your health
• Make time for hobbies
• Build a support system
• Know when to say no

Remember: Career growth is a marathon, not a sprint!""",
            'suggestions': [
                'Interview tips',
                'Salary negotiation',
                'Find jobs',
                'Update profile'
            ]
        }
    
    def _application_help(self):
        """Provide application guidance"""
        return {
            'message': """How to Apply for Jobs:

Step-by-Step Process:
1. Find a Job: Browse or search for positions
2. View Details: Click on a job to see full description
3. Click Apply: Hit the 'Apply Now' button
4. Write Cover Letter: Explain why you're a great fit
5. Submit: Your application will be sent to the employer

Writing a Great Cover Letter:
• Address the hiring manager by name if possible
• Show enthusiasm for the role and company
• Highlight 2-3 relevant achievements
• Explain why you're a perfect fit
• Keep it concise (3-4 paragraphs)
• Proofread carefully

Resume Tips:
• Tailor it to each job
• Use action verbs
• Quantify achievements
• Keep it to 1-2 pages
• Use a clean, professional format
• Include relevant keywords

Before Applying:
• Complete your profile
• Upload your latest resume
• Add a professional photo
• List all relevant skills
• Include portfolio links

After Applying:
• Track your applications
• Follow up after 1 week
• Prepare for interviews
• Stay organized

Tips for Success:
• Apply early (within first 48 hours)
• Customize each application
• Highlight relevant skills
• Show genuine interest
• Be professional

A complete profile gets 3x more employer views!""",
            'suggestions': [
                'Find jobs to apply',
                'Update my profile',
                'View my applications',
                'Interview tips'
            ]
        }

    
    def _profile_help(self):
        """Provide profile optimization tips"""
        return {
            'message': """Make Your Profile Stand Out:

Essential Elements:
• Profile Picture: Upload a professional photo
• Resume: Add your latest CV (PDF format)
• Experience: List your work history with details
• Education: Add your qualifications
• Skills: Tag all your relevant skills
• Links: Add GitHub, LinkedIn, portfolio

Profile Optimization:
• Use a professional headline
• Write a compelling bio
• Highlight key achievements
• Use industry keywords
• Keep information current
• Add certifications

Portfolio Tips:
• Showcase your best work
• Include project descriptions
• Add links to live demos
• Explain your role in each project
• Use high-quality images
• Keep it updated

Skills Section:
• List technical skills
• Include soft skills
• Add proficiency levels
• Focus on in-demand skills
• Update regularly

Why It Matters:
• Complete profiles get 3x more views
• Employers search by skills
• Shows professionalism
• Increases match accuracy
• Better recommendations

Quick Wins:
• Add a professional photo today
• Update your skills list
• Write a 2-3 sentence bio
• Upload your resume
• Add at least one portfolio project

Ready to optimize your profile?""",
            'suggestions': [
                'Go to profile settings',
                'Create portfolio',
                'Find jobs',
                'Career advice'
            ]
        }
    
    def _my_applications(self, user_id):
        """Show user's job applications"""
        try:
            if not user_id:
                return {
                    'message': "Please log in to view your applications.",
                    'suggestions': ['Browse jobs', 'Show all jobs']
                }
            
            applications = JobApplication.query.filter_by(user_id=user_id).order_by(JobApplication.applied_at.desc()).limit(10).all()
            
            if applications:
                app_list = []
                for i, app in enumerate(applications, 1):
                    job = app.job
                    status_emoji = {
                        'pending': 'Pending',
                        'reviewed': 'Reviewed',
                        'accepted': 'Accepted',
                        'rejected': 'Rejected'
                    }.get(app.status, app.status)
                    
                    app_list.append(
                        f"{i}. {job.title} at {job.company}\n"
                        f"   Status: {status_emoji} | Applied: {self._time_ago(app.applied_at)}\n"
                        f"   View: /jobs/{job.id}"
                    )
                
                return {
                    'message': f"Your Recent Applications ({len(applications)}):\n\n" + '\n\n'.join(app_list),
                    'suggestions': [
                        'Find more jobs',
                        'Saved jobs',
                        'Application tips',
                        'Interview prep'
                    ]
                }
            else:
                return {
                    'message': "You haven't applied to any jobs yet. Let me help you find great opportunities!",
                    'suggestions': [
                        'Browse all jobs',
                        'Get recommendations',
                        'Recent jobs',
                        'Help me find a job'
                    ]
                }
        except Exception as e:
            logger.error(f"Error getting applications: {str(e)}")
            return self._error_response("Could not fetch applications.")

    
    def _my_saved_jobs(self, user_id):
        """Show user's saved jobs"""
        try:
            if not user_id:
                return {
                    'message': "Please log in to view your saved jobs.",
                    'suggestions': ['Browse jobs', 'Show all jobs']
                }
            
            saved = SavedJob.query.filter_by(user_id=user_id).order_by(SavedJob.saved_at.desc()).limit(10).all()
            
            if saved:
                job_list = []
                for i, s in enumerate(saved, 1):
                    job = s.job
                    if job and job.is_active:
                        job_list.append(
                            f"{i}. {job.title} at {job.company}\n"
                            f"   Location: {job.location} | Saved: {self._time_ago(s.saved_at)}\n"
                            f"   View: /jobs/{job.id}"
                        )
                
                if job_list:
                    return {
                        'message': f"Your Saved Jobs ({len(job_list)}):\n\n" + '\n\n'.join(job_list),
                        'suggestions': [
                            'Apply to saved jobs',
                            'Find more jobs',
                            'My applications',
                            'Get recommendations'
                        ]
                    }
            
            return {
                'message': "You haven't saved any jobs yet. When you find interesting positions, click the save button to bookmark them!",
                'suggestions': [
                    'Browse all jobs',
                    'Get recommendations',
                    'Recent jobs',
                    'Help me find a job'
                ]
            }
        except Exception as e:
            logger.error(f"Error getting saved jobs: {str(e)}")
            return self._error_response("Could not fetch saved jobs.")
    
    def _default_response(self):
        """Default response when intent is unclear"""
        return {
            'message': "I'm not sure I understood that. I can help you:\n• Find jobs\n• Get recommendations\n• Search by skills or location\n• Answer questions about applications\n• Provide career advice\n• Interview preparation\n\nWhat would you like to do?",
            'suggestions': [
                'Find jobs',
                'Recommend jobs',
                'Help me search',
                'Career advice'
            ]
        }
    
    def _time_ago(self, dt):
        """Convert datetime to human readable time ago"""
        try:
            now = datetime.utcnow()
            diff = now - dt
            
            if diff.days > 0:
                return f"{diff.days}d ago"
            elif diff.seconds >= 3600:
                return f"{diff.seconds // 3600}h ago"
            elif diff.seconds >= 60:
                return f"{diff.seconds // 60}m ago"
            else:
                return "Just now"
        except:
            return "Recently"
    
    def _extract_keywords(self, message):
        """Extract meaningful keywords from message"""
        stop_words = {'find', 'search', 'show', 'me', 'looking', 'for', 'jobs', 'job', 'position', 'positions', 'the', 'a', 'an', 'in', 'at', 'with', 'and', 'or', 'is', 'are', 'what', 'where', 'how'}
        words = message.lower().split()
        keywords = [w for w in words if w not in stop_words and len(w) > 2]
        return keywords

    
    def _format_job_list(self, jobs):
        """Format job list for display"""
        job_strings = []
        for i, job in enumerate(jobs, 1):
            salary = f"${job.salary_min:,} - ${job.salary_max:,}" if job.salary_min else "Salary not specified"
            job_strings.append(
                f"{i}. {job.title} at {job.company}\n"
                f"   Location: {job.location} | Salary: {salary}\n"
                f"   View: /jobs/{job.id}"
            )
        return '\n\n'.join(job_strings)
    
    def _format_recommendation_list(self, recommendations):
        """Format recommendation list with match scores"""
        rec_strings = []
        for i, rec in enumerate(recommendations, 1):
            job = rec['job']
            score = int(rec['score'])
            rec_strings.append(
                f"{i}. {job.title} at {job.company} ({score}% match)\n"
                f"   Location: {job.location} | Match Score: {score}%\n"
                f"   View: /jobs/{job.id}"
            )
        return '\n\n'.join(rec_strings)


# Flask Routes
@bp.route('/')
def chatbot_page():
    """Render chatbot interface (standalone page)"""
    return render_template('chatbot/chat.html')

@bp.route('/message', methods=['POST'])
def process_message():
    """Process chatbot message via AJAX"""
    try:
        data = request.json
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        message = data.get('message', '')
        session_data = data.get('session')
        
        user_id = current_user.id if current_user.is_authenticated else None
        
        chatbot = JobSearchChatbot()
        response = chatbot.process_message(message, user_id, session_data)
        
        return jsonify(response)
    
    except Exception as e:
        logger.error(f"Error in process_message route: {str(e)}")
        return jsonify({
            'message': 'An error occurred. Please try again.',
            'suggestions': ['Try again', 'Show all jobs']
        }), 500
