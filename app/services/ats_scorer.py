import re
from typing import Dict, List, Tuple
from collections import Counter
import math


class ATSScorer:
    """Calculate ATS score using rule-based keyword matching and heuristics"""
    
    # Common ATS-friendly role skills mapping that can be expanded with more roles and skills as needed just in case fallback to role-based skills if job description doesn't provide enough keywords
    ROLE_SKILLS = {
        'software engineer': ['python', 'java', 'javascript', 'git', 'sql', 'api', 'testing', 'agile', 'oop', 'data structures'],
        'data scientist': ['python', 'machine learning', 'sql', 'statistics', 'pandas', 'numpy', 'tensorflow', 'r', 'visualization', 'deep learning'],
        'frontend developer': ['react', 'javascript', 'html', 'css', 'typescript', 'vue', 'angular', 'responsive', 'ui/ux', 'webpack'],
        'backend developer': ['python', 'java', 'node.js', 'sql', 'api', 'docker', 'kubernetes', 'microservices', 'rest', 'mongodb'],
        'full stack developer': ['react', 'node.js', 'javascript', 'sql', 'api', 'git', 'docker', 'mongodb', 'rest', 'html/css'],
        'devops engineer': ['docker', 'kubernetes', 'ci/cd', 'aws', 'linux', 'terraform', 'jenkins', 'ansible', 'monitoring', 'scripting'],
        'data engineer': ['python', 'sql', 'spark', 'kafka', 'etl', 'data pipeline', 'aws', 'airflow', 'big data', 'hadoop'],
        'ml engineer': ['python', 'tensorflow', 'pytorch', 'machine learning', 'deep learning', 'mlops', 'docker', 'kubernetes', 'model deployment'],
        'product manager': ['agile', 'scrum', 'roadmap', 'stakeholder', 'analytics', 'user research', 'jira', 'sql', 'a/b testing'],
        'qa engineer': ['testing', 'automation', 'selenium', 'api testing', 'test cases', 'bug tracking', 'ci/cd', 'quality assurance'],
    }
    
    def __init__(self, resume_data: Dict, job_role: str, job_desc: str = ""):
        self.resume_data = resume_data
        self.job_role = job_role.lower()
        self.job_desc = job_desc.lower()
        self.resume_text = self._get_resume_text().lower()
    
    def _get_resume_text(self) -> str:
        """Convert resume data to searchable text"""
        import json
        return json.dumps(self.resume_data)
    
    def calculate_score(self) -> Tuple[int, Dict[str, int], str]:
        """
        Calculate ATS score with breakdown
        Returns: (total_score, breakdown, explanation)
        """
        breakdown = {
            'keyword_match': self._score_keyword_match(),
            'skills_relevance': self._score_skills_relevance(),
            'format_quality': self._score_format_quality(),
            'experience_alignment': self._score_experience_alignment(),
            'completeness': self._score_completeness()
        }
        
        total_score = sum(breakdown.values())
        explanation = self._generate_explanation(breakdown)
        
        return total_score, breakdown, explanation
    
    def _score_keyword_match(self) -> int:
        """Score based on job description keyword matching (30 points max)"""
        if not self.job_desc:
            return 15  # Default score if no job description provided though can be adjusted based on role-based skills if needed
        
        # Extract keywords from job description
        keywords = self._extract_keywords(self.job_desc)
        
        if not keywords:
            return 15
        
        # Count matches in resume
        matches = sum(1 for kw in keywords if kw in self.resume_text)
        match_rate = matches / len(keywords)
        
        # Calculate score with diminishing returns
        score = int(match_rate * 30)
        return min(30, score)
    
    # Score skills relevance based on role and job description (25 points max) 
    # - If job description provides clear skills, score based on those
    # - If not, fallback to role-based expected skills
    
    def _score_skills_relevance(self) -> int:
        """Score based on relevant skills for the role (25 points max)"""
        # Get expected skills for role
        role_skills = self._get_expected_skills()
        user_skills = [s.lower() for s in self.resume_data.get('skills', [])]
        
        if not role_skills:
            # If role not in mapping, use generic scoring
            return min(25, len(user_skills) * 2)
        
        matches = sum(1 for rs in role_skills if any(rs in us for us in user_skills))
        match_rate = matches / len(role_skills)
        
        # Bonus for having extra relevant skills
        extra_bonus = min(5, len(user_skills) - len(role_skills))
        
        score = int(match_rate * 20) + max(0, extra_bonus)
        return min(25, score)
    
    # Score resume format and structure (20 points max)
    # - Professional summary presence and quality
    # - Skills section completeness and relevance
    # - Experience section clarity and detail
    def _score_format_quality(self) -> int:
        """Score resume format and structure (20 points max)"""
        score = 0
        
        # Has professional summary (5 points)
        if self.resume_data.get('summary') and len(self.resume_data['summary']) > 50:
            score += 5
        
        # Has adequate skills listed (5 points)
        if len(self.resume_data.get('skills', [])) >= 5:
            score += 5
        elif len(self.resume_data.get('skills', [])) >= 3:
            score += 3
        
        # Experience bullet points are detailed (5 points)
        exp_quality = self._check_experience_quality()
        score += exp_quality
        
        # Contact information complete (5 points)
        personal = self.resume_data.get('personal', {})
        contact_score = sum([
            2 if personal.get('email') else 0,
            1 if personal.get('phone') else 0,
            1 if personal.get('linkedin') else 0,
            1 if personal.get('name') else 0,
        ])
        score += min(5, contact_score)
        
        return min(20, score)
    

    # Score work experience relevance (15 points max)
    # - Number of relevant experiences
    # - Quality of experience descriptions (quantifiable achievements, clarity)
    def _score_experience_alignment(self) -> int:
        """Score work experience relevance (15 points max)"""
        experiences = self.resume_data.get('experience', [])
        
        if not experiences:
            # Check projects as alternative
            projects = self.resume_data.get('projects', [])
            if projects:
                return min(10, len(projects) * 3)
            return 0
        
        score = 0
        
        # Number of experiences (max 5 points)
        score += min(5, len(experiences) * 2)
        
        # Quality of experience descriptions (max 10 points)
        for exp in experiences:
            points = exp.get('points', [])
            if len(points) >= 3:
                score += 3
            elif len(points) >= 1:
                score += 2
            
            # Check for quantifiable achievements
            for point in points:
                if self._has_quantifiable_achievement(point):
                    score += 1
                    break  # Max 1 point per experience
        
        return min(15, score)
    
    # Score resume completeness (10 points max)
    # - Presence of key sections (personal info, skills, experience, education)
    # - Optional sections (certifications, achievements) add small bonus
    def _score_completeness(self) -> int:
        """Score resume completeness (10 points max)"""
        score = 0
        
        # Required sections
        if self.resume_data.get('personal', {}).get('name'):
            score += 2
        if self.resume_data.get('skills'):
            score += 2
        if self.resume_data.get('experience') or self.resume_data.get('projects'):
            score += 3
        if self.resume_data.get('education'):
            score += 2
        if self.resume_data.get('certifications'):
            score += 0.5
        if self.resume_data.get('achievements'):
            score += 0.5
        
        return min(10, int(score))
    
    # Helper methods for keyword extraction, skill relevance, experience quality, and explanation generation
    # - Keyword extraction focuses on identifying important terms from the job description while filtering out common stop words and less relevant terms.
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract important keywords from job description"""
        # Remove common stop words
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 
            'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'be',
            'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'should',
            'could', 'may', 'might', 'must', 'can', 'this', 'that', 'these', 'those'
        }
        
        # Extract words and filter out short/common words and counter frequency
        words = re.findall(r'\b[a-z]+\b', text.lower())
        filtered = [w for w in words if len(w) > 3 and w not in stop_words]
        word_freq = Counter(filtered)
        
        # Get top keywords (mentioned more than once or technical terms) mentioned in job description more than 20 times or are in the tech terms list
        tech_terms = set(self._get_all_tech_terms())
        keywords = []
        
        for word, freq in word_freq.most_common(30):
            if freq > 1 or word in tech_terms:
                keywords.append(word)
        
        return keywords[:20] 
    

    # Get expected skills for the job role based on predefined mapping and job description analysis
    # - This method first tries to find an exact match for the job role in the predefined ROLE_SKILLS mapping. 
    # - If no exact match is found, it looks for partial matches (e.g., "software engineer" might match "senior software engineer"). 
    # - If still no match is found, it attempts to extract relevant skills directly from the job description using keyword analysis.
    def _get_expected_skills(self) -> List[str]:
        """Get expected skills for job role"""
        # Try exact match first
        if self.job_role in self.ROLE_SKILLS:
            return self.ROLE_SKILLS[self.job_role]
        
        # Try partial match
        for role, skills in self.ROLE_SKILLS.items():
            if role in self.job_role or self.job_role in role:
                return skills
        
        # Extract from job description if available
        if self.job_desc:
            return self._extract_skills_from_jd()
        
        return []
    
    def _extract_skills_from_jd(self) -> List[str]:
        """Extract technical skills from job description"""
        tech_terms = self._get_all_tech_terms()
        found_skills = []
        
        for term in tech_terms:
            if term in self.job_desc:
                found_skills.append(term)
        
        return found_skills[:15]
    
    def _get_all_tech_terms(self) -> List[str]:
        """Get comprehensive list of technical terms"""
        all_skills = set()
        for skills in self.ROLE_SKILLS.values():
            all_skills.update(skills)
        
        # Add more common tech terms
        additional_terms = [
            'python', 'java', 'javascript', 'typescript', 'c++', 'c#', 'ruby', 'php', 'swift', 'kotlin',
            'react', 'angular', 'vue', 'node.js', 'express', 'django', 'flask', 'spring', 'laravel',
            'sql', 'mysql', 'postgresql', 'mongodb', 'redis', 'elasticsearch', 'cassandra',
            'aws', 'azure', 'gcp', 'docker', 'kubernetes', 'terraform', 'ansible',
            'git', 'github', 'gitlab', 'ci/cd', 'jenkins', 'travis',
            'api', 'rest', 'graphql', 'microservices', 'serverless',
            'machine learning', 'deep learning', 'tensorflow', 'pytorch', 'scikit-learn',
            'html', 'css', 'sass', 'tailwind', 'bootstrap',
            'agile', 'scrum', 'jira', 'confluence'
        ]
        
        all_skills.update(additional_terms)
        return list(all_skills)
    
    def _check_experience_quality(self) -> int:
        """Check quality of experience descriptions"""
        score = 0
        experiences = self.resume_data.get('experience', [])
        
        for exp in experiences[:3]:  # Check top 3 experiences
            points = exp.get('points', [])
            
            # Has multiple bullet points
            if len(points) >= 3:
                score += 1
            
            # Bullet points are detailed (> 50 chars)
            detailed = sum(1 for p in points if len(p) > 50)
            if detailed >= 2:
                score += 1
        
        return min(5, score)
    

    # Check if experience bullet point contains quantifiable achievements (numbers, percentages, metrics)
    # - This method uses regular expressions to look for patterns that indicate quantifiable achievements, such as numbers followed by percentage signs, monetary values, or phrases indicating improvement or growth. 
    # - If any of these patterns are found in the experience bullet points, it contributes positively to the experience alignment score.
    def _has_quantifiable_achievement(self, text: str) -> bool:
        """Check if text contains quantifiable achievements"""
        # Look for numbers, percentages, metrics
        patterns = [
            r'\d+%',  # Percentages
            r'\d+x',  # Multiples
            r'\$\d+',  # Money
            r'\d+\+',  # Numbers with +
            r'increased.*\d+',
            r'reduced.*\d+',
            r'improved.*\d+',
            r'grew.*\d+',
        ]
        
        for pattern in patterns:
            if re.search(pattern, text.lower()):
                return True
        return False
    
    def _generate_explanation(self, breakdown: Dict[str, int]) -> str:
        """Generate human-readable explanation of score"""
        total = sum(breakdown.values())
        
        strengths = []
        gaps = []
        
        # Analyze each component
        if breakdown['keyword_match'] >= 20:
            strengths.append("strong keyword alignment with job description")
        elif breakdown['keyword_match'] < 15:
            gaps.append("limited keyword match with job requirements")
        
        if breakdown['skills_relevance'] >= 18:
            strengths.append("relevant technical skills")
        elif breakdown['skills_relevance'] < 12:
            gaps.append("missing key technical skills")
        
        if breakdown['format_quality'] >= 15:
            strengths.append("well-structured format")
        elif breakdown['format_quality'] < 10:
            gaps.append("formatting improvements needed")
        
        if breakdown['experience_alignment'] >= 10:
            strengths.append("solid work experience")
        elif breakdown['experience_alignment'] < 7:
            gaps.append("experience section needs enhancement")
        
        # Build explanation
        if total >= 75:
            intro = "Strong resume with"
        elif total >= 60:
            intro = "Good foundation with"
        else:
            intro = "Resume shows potential but has"
        
        explanation = f"{intro} {', '.join(strengths) if strengths else 'room for improvement'}."
        
        if gaps:
            explanation += f" Areas to improve: {', '.join(gaps)}."
        
        return explanation


def calculate_ats_score_rule_based(resume_data: Dict, job_role: str, job_desc: str = "") -> Tuple[int, Dict, str]:
    """
    Calculate ATS score using rule-based approach
    Returns: (score, breakdown, explanation)
    """
    scorer = ATSScorer(resume_data, job_role, job_desc)
    return scorer.calculate_score()