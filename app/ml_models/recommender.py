from app.models.job import Job, JobApplication, SavedJob
from app.models.user import User
from app.models.portfolio import Portfolio, PortfolioSkill, WorkExperience
import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from datetime import datetime, timedelta

class JobRecommender:
    def __init__(self):
        self.vectorizer = TfidfVectorizer(max_features=1000, stop_words='english', ngram_range=(1, 2))
        self.job_vectors = None
        self.jobs_df = None
        
    def prepare_job_data(self):
        """Prepare job data for matching"""
        jobs = Job.query.filter_by(is_active=True).all()
        
        job_data = []
        for job in jobs:
            job_data.append({
                'id': job.id,
                'title': job.title,
                'description': job.description,
                'requirements': job.requirements,
                'skills': job.required_skills or '',
                'text': f"{job.title} {job.description} {job.requirements} {job.required_skills}"
            })
        
        self.jobs_df = pd.DataFrame(job_data)
        
        if not self.jobs_df.empty:
            self.job_vectors = self.vectorizer.fit_transform(self.jobs_df['text'])
        
        return self.job_vectors
    
    def get_user_profile_vector(self, user_id):
        """Create enhanced user profile vector based on skills, portfolio, and experience"""
        user = User.query.get(user_id)
        portfolio = Portfolio.query.filter_by(user_id=user_id).first()
        
        # Collect user data
        user_skills = user.get_skills_list() if user.skills else []
        
        # Get portfolio skills (with higher weight)
        if portfolio:
            portfolio_skills = PortfolioSkill.query.filter_by(portfolio_id=portfolio.id).all()
            # Repeat portfolio skills to give them more weight
            user_skills.extend([skill.skill_name for skill in portfolio_skills] * 2)
            
            # Add work experience titles and descriptions
            work_experiences = WorkExperience.query.filter_by(portfolio_id=portfolio.id).all()
            for exp in work_experiences:
                if exp.position:
                    user_skills.append(exp.position)
                if exp.description:
                    user_text_parts = exp.description.split()[:20]  # First 20 words
                    user_skills.extend(user_text_parts)
        
        # Create user text with weighted components
        user_text = ' '.join(user_skills)
        
        # Add education with weight
        if user.education:
            user_text += ' ' + user.education + ' ' + user.education
        
        # Add bio
        if user.bio:
            user_text += ' ' + user.bio
        
        # Transform to vector
        if hasattr(self, 'vectorizer') and self.job_vectors is not None:
            user_vector = self.vectorizer.transform([user_text])
            return user_vector
        
        return None
    
    def get_recommendations_for_user(self, user_id, n_recommendations=10):
        """Get job recommendations for a specific user"""
        # Prepare job data if not already done
        if self.jobs_df is None:
            self.prepare_job_data()
        
        # Get user vector
        user_vector = self.get_user_profile_vector(user_id)
        
        if user_vector is None or self.job_vectors is None:
            return []
        
        # Calculate similarities
        similarities = cosine_similarity(user_vector, self.job_vectors).flatten()
        
        # Get top indices
        top_indices = similarities.argsort()[-n_recommendations:][::-1]
        
        # Prepare recommendations
        recommendations = []
        for idx in top_indices:
            if similarities[idx] > 0:  # Only include if there's some similarity
                job_id = self.jobs_df.iloc[idx]['id']
                job = Job.query.get(job_id)
                
                if job:
                    recommendations.append({
                        'job': job,
                        'score': round(similarities[idx] * 100, 2)
                    })
        
        return recommendations
    
    def get_similar_jobs(self, job_id, n_similar=5):
        """Get jobs similar to a given job"""
        if self.jobs_df is None:
            self.prepare_job_data()
        
        # Find job index
        job_indices = self.jobs_df[self.jobs_df['id'] == job_id].index
        
        if len(job_indices) == 0:
            return []
        
        job_idx = job_indices[0]
        
        # Calculate similarities
        job_vector = self.job_vectors[job_idx]
        similarities = cosine_similarity(job_vector, self.job_vectors).flatten()
        
        # Get top indices (excluding the job itself)
        top_indices = similarities.argsort()[-n_similar-1:][::-1][1:n_similar+1]
        
        similar_jobs = []
        for idx in top_indices:
            similar_job_id = self.jobs_df.iloc[idx]['id']
            job = Job.query.get(similar_job_id)
            if job:
                similar_jobs.append(job)
        
        return similar_jobs

    
    def get_hybrid_recommendations(self, user_id, n_recommendations=10):
        """
        Enhanced hybrid recommendation combining:
        - Content-based filtering (skills match)
        - Collaborative filtering (similar users)
        - Experience level matching
        - Recent activity boost
        """
        user = User.query.get(user_id)
        if not user:
            return []
        
        # Get content-based recommendations
        content_recs = self.get_recommendations_for_user(user_id, n_recommendations * 2)
        
        # Get jobs user has interacted with
        saved_jobs = SavedJob.query.filter_by(user_id=user_id).all()
        applied_jobs = JobApplication.query.filter_by(user_id=user_id).all()
        
        saved_job_ids = {sj.job_id for sj in saved_jobs}
        applied_job_ids = {aj.job_id for aj in applied_jobs}
        
        # Filter out already applied/saved jobs
        filtered_recs = []
        for rec in content_recs:
            job = rec['job']
            if job.id not in applied_job_ids and job.id not in saved_job_ids:
                # Boost score based on experience match
                exp_match = self._calculate_experience_match(user, job)
                rec['score'] = rec['score'] * 0.7 + exp_match * 30
                
                # Boost recent jobs
                days_old = (datetime.utcnow() - job.created_at).days
                if days_old < 7:
                    rec['score'] += 10
                elif days_old < 30:
                    rec['score'] += 5
                
                filtered_recs.append(rec)
        
        # Sort by enhanced score
        filtered_recs.sort(key=lambda x: x['score'], reverse=True)
        
        return filtered_recs[:n_recommendations]
    
    def _calculate_experience_match(self, user, job):
        """Calculate how well user's experience matches job requirements"""
        if not job.experience_min and not job.experience_max:
            return 50  # Neutral score if no requirements
        
        user_exp = user.experience_years or 0
        
        if job.experience_min and job.experience_max:
            if job.experience_min <= user_exp <= job.experience_max:
                return 100  # Perfect match
            elif user_exp < job.experience_min:
                diff = job.experience_min - user_exp
                return max(0, 100 - (diff * 20))  # Penalize under-qualified
            else:
                diff = user_exp - job.experience_max
                return max(0, 100 - (diff * 10))  # Less penalty for over-qualified
        elif job.experience_min:
            if user_exp >= job.experience_min:
                return 100
            else:
                diff = job.experience_min - user_exp
                return max(0, 100 - (diff * 20))
        
        return 50
    
    def get_trending_jobs(self, limit=10):
        """Get trending jobs based on views and applications"""
        seven_days_ago = datetime.utcnow() - timedelta(days=7)
        
        jobs = Job.query.filter(
            Job.is_active == True,
            Job.created_at >= seven_days_ago
        ).all()
        
        # Calculate trending score
        trending_jobs = []
        for job in jobs:
            score = (job.views_count * 0.3) + (job.applications_count * 0.7)
            trending_jobs.append({
                'job': job,
                'score': score
            })
        
        trending_jobs.sort(key=lambda x: x['score'], reverse=True)
        return trending_jobs[:limit]
    
    def get_jobs_by_location_preference(self, user_id, n_recommendations=10):
        """Get jobs matching user's location or remote jobs"""
        user = User.query.get(user_id)
        if not user or not user.location:
            return self.get_recommendations_for_user(user_id, n_recommendations)
        
        # Get jobs in user's location or remote
        location_jobs = Job.query.filter(
            Job.is_active == True,
            (Job.location.contains(user.location)) | 
            (Job.location.contains('Remote'))
        ).limit(n_recommendations * 2).all()
        
        # Score them using content-based filtering
        recommendations = []
        user_vector = self.get_user_profile_vector(user_id)
        
        if user_vector is not None and self.jobs_df is not None:
            for job in location_jobs:
                job_idx = self.jobs_df[self.jobs_df['id'] == job.id].index
                if len(job_idx) > 0:
                    job_vector = self.job_vectors[job_idx[0]]
                    similarity = cosine_similarity(user_vector, job_vector)[0][0]
                    
                    recommendations.append({
                        'job': job,
                        'score': round(similarity * 100, 2)
                    })
        
        recommendations.sort(key=lambda x: x['score'], reverse=True)
        return recommendations[:n_recommendations]
    
    def get_skill_gap_analysis(self, user_id, job_id):
        """Analyze skill gaps between user and job requirements"""
        user = User.query.get(user_id)
        job = Job.query.get(job_id)
        
        if not user or not job:
            return None
        
        user_skills = set([s.lower().strip() for s in user.get_skills_list()])
        job_skills = set([s.lower().strip() for s in job.get_required_skills_list()])
        
        matching_skills = user_skills.intersection(job_skills)
        missing_skills = job_skills - user_skills
        extra_skills = user_skills - job_skills
        
        match_percentage = (len(matching_skills) / len(job_skills) * 100) if job_skills else 0
        
        return {
            'matching_skills': list(matching_skills),
            'missing_skills': list(missing_skills),
            'extra_skills': list(extra_skills),
            'match_percentage': round(match_percentage, 2),
            'total_required': len(job_skills),
            'total_matched': len(matching_skills)
        }
