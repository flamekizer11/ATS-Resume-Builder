import re
from typing import Dict, List
from collections import Counter


class SuggestionGenerator:
    """Generate resume improvement suggestions using rule-based heuristics"""
    
    def __init__(self, resume_data: Dict, job_role: str, job_desc: str, score_breakdown: Dict):
        self.resume_data = resume_data
        self.job_role = job_role.lower()
        self.job_desc = job_desc.lower() if job_desc else ""
        self.score_breakdown = score_breakdown
        self.suggestions = []
        self.suggestion_id = 0
    
    def generate_suggestions(self) -> List[Dict]:
        """Generate prioritized suggestions"""
        
        # Generate suggestions based on gaps
        if self.score_breakdown['keyword_match'] < 20:
            self._suggest_keywords()
        
        if self.score_breakdown['skills_relevance'] < 18:
            self._suggest_skills()
        
        if self.score_breakdown['format_quality'] < 15:
            self._suggest_format_improvements()
        
        if self.score_breakdown['experience_alignment'] < 10:
            self._suggest_experience_improvements()
        
        if self.score_breakdown['completeness'] < 8:
            self._suggest_completeness()
        
        # Always suggest quantifiable achievements if missing
        self._suggest_quantifiable_achievements()
        
        # Sort by priority
        priority_order = {'high': 0, 'medium': 1, 'low': 2}
        self.suggestions.sort(key=lambda x: priority_order.get(x['priority'], 2))
        
        return self.suggestions[:5]  # Return top 5 suggestions
    
    def _add_suggestion(self, section: str, change: str, reason: str, impact: str, priority: str):
        """Add a suggestion to the list"""
        self.suggestions.append({
            'id': self.suggestion_id,
            'section': section,
            'change': change[:100] + '...' if len(change) > 100 else change,
            'reason': reason[:150] + '...' if len(reason) > 150 else reason,
            'impact': impact[:100] + '...' if len(impact) > 100 else impact,
            'priority': priority
        })
        self.suggestion_id += 1
    
    def _suggest_keywords(self):
        """Suggest adding missing keywords from job description"""
        if not self.job_desc:
            return
        
        # Extract keywords from job description
        jd_keywords = self._extract_important_keywords(self.job_desc)
        resume_text = str(self.resume_data).lower()
        
        # Find missing keywords
        missing = [kw for kw in jd_keywords if kw not in resume_text]
        
        if missing:
            # Group by relevance
            top_missing = missing[:5]
            
            self._add_suggestion(
                section='skills',
                change=f"Add these keywords to your skills section: {', '.join(top_missing[:3])}",
                reason=f"These terms appear frequently in the job description but are missing from your resume",
                impact='+6-8 score (keyword match improvement)',
                priority='high'
            )
    
    def _suggest_skills(self):
        """Suggest adding role-specific skills"""
        expected_skills = self._get_expected_skills_for_role()
        current_skills = [s.lower() for s in self.resume_data.get('skills', [])]
        
        # Find missing critical skills
        missing_skills = [s for s in expected_skills if not any(s in cs for cs in current_skills)]
        
        if missing_skills:
            top_missing = missing_skills[:4]
            
            self._add_suggestion(
                section='skills',
                change=f"Add these relevant skills: {', '.join(top_missing)}",
                reason=f"These are essential skills for {self.job_role} roles",
                impact='+5-7 score (skills relevance improvement)',
                priority='high'
            )
    
    def _suggest_format_improvements(self):
        """Suggest format improvements"""
        
        # Check for missing summary
        if not self.resume_data.get('summary') or len(self.resume_data.get('summary', '')) < 50:
            summary_example = self._generate_summary_example()
            self._add_suggestion(
                section='summary',
                change=f"Add a professional summary at the top: '{summary_example}'",
                reason="Professional summary is critical for ATS and catches recruiter attention",
                impact='+4-6 score (format quality + completeness)',
                priority='high'
            )
        
        # Check for weak contact info
        personal = self.resume_data.get('personal', {})
        missing_contact = []
        if not personal.get('email'):
            missing_contact.append('email')
        if not personal.get('phone'):
            missing_contact.append('phone number')
        if not personal.get('linkedin'):
            missing_contact.append('LinkedIn profile')
        
        if missing_contact:
            self._add_suggestion(
                section='personal',
                change=f"Add missing contact information: {', '.join(missing_contact)}",
                reason="Complete contact information helps recruiters reach you easily",
                impact='+2-3 score (completeness)',
                priority='medium'
            )
    
    def _suggest_experience_improvements(self):
        """Suggest improvements to experience section"""
        experiences = self.resume_data.get('experience', [])
        
        if not experiences:
            self._add_suggestion(
                section='experience',
                change="Add at least 1-2 relevant work experiences or internships",
                reason="Work experience is crucial for most job applications",
                impact='+8-10 score (experience alignment + completeness)',
                priority='high'
            )
            return
        
        # Check for weak bullet points
        for i, exp in enumerate(experiences[:2]):  # Check first 2 experiences
            points = exp.get('points', [])
            
            if len(points) < 3:
                self._add_suggestion(
                    section='experience',
                    change=f"Expand '{exp.get('title', 'experience')}' section with 3-5 detailed bullet points",
                    reason="Detailed accomplishments demonstrate your impact and value",
                    impact='+3-4 score (experience quality)',
                    priority='medium'
                )
                break
    
    def _suggest_quantifiable_achievements(self):
        """Suggest adding quantifiable metrics"""
        experiences = self.resume_data.get('experience', [])
        has_metrics = False
        
        for exp in experiences:
            for point in exp.get('points', []):
                if self._has_numbers(point):
                    has_metrics = True
                    break
            if has_metrics:
                break
        
        if not has_metrics and experiences:
            self._add_suggestion(
                section='experience',
                change="Add quantifiable achievements to your experience bullets (e.g., 'Increased efficiency by 30%', 'Reduced costs by $10K')",
                reason="Numbers and metrics make your achievements more credible and impactful",
                impact='+4-6 score (experience quality)',
                priority='high'
            )
    
    def _suggest_completeness(self):
        """Suggest adding missing sections"""
        
        if not self.resume_data.get('education'):
            self._add_suggestion(
                section='education',
                change="Add your education details (degree, institution, graduation year)",
                reason="Education section is expected in most resumes",
                impact='+2-3 score (completeness)',
                priority='medium'
            )
        
        if not self.resume_data.get('projects') and len(self.resume_data.get('experience', [])) < 2:
            self._add_suggestion(
                section='projects',
                change="Add 1-2 relevant projects to showcase your skills",
                reason="Projects demonstrate practical application of your skills",
                impact='+3-5 score (experience alignment)',
                priority='medium'
            )
    
    def _extract_important_keywords(self, text: str) -> List[str]:
        """Extract important keywords from job description"""
        # Technical terms and skills to prioritize
        tech_terms = {
            'python', 'java', 'javascript', 'react', 'node', 'sql', 'aws', 'docker',
            'kubernetes', 'api', 'machine learning', 'data', 'cloud', 'agile', 'scrum',
            'git', 'ci/cd', 'microservices', 'rest', 'testing', 'angular', 'vue'
        }
        
        # Extract all words
        words = re.findall(r'\b[a-z]+\b', text)
        word_freq = Counter(words)
        
        # Prioritize technical terms and frequently mentioned words
        keywords = []
        for word, freq in word_freq.most_common(30):
            if word in tech_terms or freq > 2:
                keywords.append(word)
        
        return keywords[:10]
    
    def _get_expected_skills_for_role(self) -> List[str]:
        """Get expected skills based on job role"""
        role_skills_map = {
            'software engineer': ['python', 'java', 'javascript', 'git', 'sql', 'api', 'testing'],
            'data scientist': ['python', 'machine learning', 'sql', 'statistics', 'pandas', 'tensorflow'],
            'frontend developer': ['react', 'javascript', 'html', 'css', 'typescript'],
            'backend developer': ['python', 'java', 'node.js', 'sql', 'api', 'docker'],
            'full stack': ['react', 'node.js', 'javascript', 'sql', 'api', 'git'],
            'devops': ['docker', 'kubernetes', 'ci/cd', 'aws', 'linux', 'terraform'],
            'data engineer': ['python', 'sql', 'spark', 'kafka', 'etl', 'aws'],
        }
        
        for role_key, skills in role_skills_map.items():
            if role_key in self.job_role:
                return skills
        
        return ['problem solving', 'teamwork', 'communication']
    
    def _generate_summary_example(self) -> str:
        """Generate example professional summary"""
        role = self.job_role.title()
        exp_count = len(self.resume_data.get('experience', []))
        skills = self.resume_data.get('skills', [])[:3]
        
        if exp_count >= 2:
            exp_text = f"{exp_count}+ years of experience"
        elif exp_count == 1:
            exp_text = "1 year of experience"
        else:
            exp_text = "Aspiring professional"
        
        skills_text = ', '.join(skills) if skills else "modern technologies"
        
        return f"{exp_text} as a {role}, skilled in {skills_text} and delivering high-quality solutions"
    
    def _has_numbers(self, text: str) -> bool:
        """Check if text contains numbers/metrics"""
        return bool(re.search(r'\d', text))


def generate_suggestions_rule_based(resume_data: Dict, job_role: str, job_desc: str, score_breakdown: Dict) -> List[Dict]:
    """
    Generate improvement suggestions using rule-based approach
    """
    generator = SuggestionGenerator(resume_data, job_role, job_desc, score_breakdown)
    return generator.generate_suggestions()