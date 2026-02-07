import re
import copy
from typing import Dict, List


class ResumeEnhancer:
    """Apply suggestions to resume data using rule-based transformations"""
    
    def __init__(self, original_data: Dict, suggestions: List[Dict], job_role: str, job_desc: str):
        self.original_data = copy.deepcopy(original_data)
        self.enhanced_data = copy.deepcopy(original_data)
        self.suggestions = suggestions
        self.job_role = job_role
        self.job_desc = job_desc
    
    def apply_changes(self) -> Dict:
        """Apply all accepted suggestions to resume data"""
        
        for suggestion in self.suggestions:
            section = suggestion.get('section', '')
            change = suggestion.get('change', '')
            
            if section == 'skills':
                self._apply_skills_change(change)
            elif section == 'summary':
                self._apply_summary_change(change)
            elif section == 'experience':
                self._apply_experience_change(change)
            elif section == 'personal':
                self._apply_personal_change(change)
            elif section == 'education':
                self._apply_education_change(change)
            elif section == 'projects':
                self._apply_projects_change(change)
        
        return self.enhanced_data
    
    def _apply_skills_change(self, change: str):
        """Apply changes to skills section"""
        # Extract skills from the change text
        # Pattern: "Add these keywords: X, Y, Z"
        skills_to_add = self._extract_items_from_text(change)
        
        if skills_to_add:
            current_skills = self.enhanced_data.get('skills', [])
            current_skills_lower = [s.lower() for s in current_skills]
            
            # Add new skills (avoid duplicates)
            for skill in skills_to_add:
                if skill.lower() not in current_skills_lower:
                    current_skills.append(skill.title())
            
            self.enhanced_data['skills'] = current_skills
    
    def _apply_summary_change(self, change: str):
        """Apply changes to summary section"""
        # Extract summary from change text
        # Pattern: "Add a professional summary: 'SUMMARY TEXT'"
        summary = self._extract_quoted_text(change)
        
        if summary:
            self.enhanced_data['summary'] = summary
        elif not self.enhanced_data.get('summary'):
            # Generate default summary if none extracted
            self.enhanced_data['summary'] = self._generate_default_summary()
    
    def _apply_experience_change(self, change: str):
        """Apply changes to experience section"""
        experiences = self.enhanced_data.get('experience', [])
        
        # Check if it's about adding quantifiable achievements
        if 'quantifiable' in change.lower() or 'metrics' in change.lower():
            self._add_quantifiable_metrics(experiences)
        
        # Check if it's about expanding bullet points
        elif 'expand' in change.lower() or 'bullet points' in change.lower():
            self._expand_experience_bullets(experiences)
        
        # Check if it's about adding new experience
        elif 'add' in change.lower() and ('work experience' in change.lower() or 'internship' in change.lower()):
            # Can't add experience without data, just ensure structure is present
            if not experiences:
                self.enhanced_data['experience'] = []
        
        self.enhanced_data['experience'] = experiences
    
    def _apply_personal_change(self, change: str):
        """Apply changes to personal information section"""
        personal = self.enhanced_data.get('personal', {})
        
        # Extract what needs to be added
        if 'email' in change.lower() and not personal.get('email'):
            personal['email'] = '[Your Email]'
        if 'phone' in change.lower() and not personal.get('phone'):
            personal['phone'] = '[Your Phone]'
        if 'linkedin' in change.lower() and not personal.get('linkedin'):
            personal['linkedin'] = '[Your LinkedIn]'
        
        self.enhanced_data['personal'] = personal
    
    def _apply_education_change(self, change: str):
        """Apply changes to education section"""
        education = self.enhanced_data.get('education', [])
        
        if not education and 'add' in change.lower():
            # Add placeholder for education
            education.append({
                'degree': '[Your Degree]',
                'institution': '[Your Institution]',
                'year': '[Year]',
                'gpa': ''
            })
        
        self.enhanced_data['education'] = education
    
    def _apply_projects_change(self, change: str):
        """Apply changes to projects section"""
        projects = self.enhanced_data.get('projects', [])
        
        if not projects and 'add' in change.lower():
            # Add placeholder for project
            projects.append({
                'name': '[Project Name]',
                'description': '[Project Description]',
                'tech': [],
                'points': ['[Key achievement or feature]']
            })
        
        self.enhanced_data['projects'] = projects
    
    def _extract_items_from_text(self, text: str) -> List[str]:
        """Extract comma-separated items from text"""
        # Look for patterns like: "Add X, Y, Z" or "keywords: A, B, C"
        
        # Try to find colon-separated list (:)
        if ':' in text:
            parts = text.split(':', 1)
            if len(parts) > 1:
                text = parts[1]
        
        # Split by common delimiters
        items = re.split(r'[,;]|\sand\s', text)
        
        # Clean each item
        cleaned_items = []
        for item in items:
            # Remove common prefixes/suffixes and quotes
            item = re.sub(r'^(add|include|these|keywords?|skills?)\s+', '', item.lower(), flags=re.IGNORECASE)
            item = item.strip(' ."\'')
            
            # Keep only reasonable skill names (2-30 chars, alphanumeric with some special chars)
            if 2 <= len(item) <= 30 and re.search(r'[a-z]', item, re.IGNORECASE):
                cleaned_items.append(item)
        
        return cleaned_items[:10]  # Max 10 items
    
    def _extract_quoted_text(self, text: str) -> str:
        """Extract text within quotes"""
        # Look for text in single or double quotes
        match = re.search(r"['\"](.+?)['\"]", text)
        if match:
            return match.group(1)
        
        # If no quotes, try to extract after colon
        if ':' in text:
            parts = text.split(':', 1)
            if len(parts) > 1:
                return parts[1].strip(' ."\'')
        
        return ""
    
    def _generate_default_summary(self) -> str:
        """Generate a default professional summary"""
        role = self.job_role.title()
        skills = self.enhanced_data.get('skills', [])[:3]
        exp_count = len(self.enhanced_data.get('experience', []))
        
        if exp_count >= 2:
            exp_text = f"Experienced {role}"
        elif exp_count == 1:
            exp_text = f"{role}"
        else:
            exp_text = f"Motivated {role}"
        
        if skills:
            skills_text = f" with expertise in {', '.join(skills)}"
        else:
            skills_text = " with strong technical skills"
        
        summary = f"{exp_text}{skills_text}. Proven track record of delivering high-quality solutions and collaborating effectively in team environments."
        
        return summary
    
    def _add_quantifiable_metrics(self, experiences: List[Dict]):
        """Add placeholder metrics to experience bullet points"""
        for exp in experiences:
            points = exp.get('points', [])
            enhanced_points = []
            
            for point in points:
                # If point already has numbers, keep it
                if re.search(r'\d', point):
                    enhanced_points.append(point)
                else:
                    # Add suggestion for metric
                    # Try to identify action verbs and add metric suggestions
                    if any(verb in point.lower() for verb in ['developed', 'created', 'built', 'designed']):
                        enhanced_point = point.rstrip('.') + " [Add metric: e.g., reducing load time by 40%]"
                    elif any(verb in point.lower() for verb in ['improved', 'optimized', 'enhanced']):
                        enhanced_point = point.rstrip('.') + " [Add metric: e.g., increasing efficiency by 30%]"
                    elif any(verb in point.lower() for verb in ['led', 'managed', 'coordinated']):
                        enhanced_point = point.rstrip('.') + " [Add metric: e.g., leading a team of 5 developers]"
                    else:
                        enhanced_point = point
                    
                    enhanced_points.append(enhanced_point)
            
            exp['points'] = enhanced_points
    
    def _expand_experience_bullets(self, experiences: List[Dict]):
        """Expand experience bullet points with more details"""
        for exp in experiences[:2]:  # Focus on first 2 experiences
            points = exp.get('points', [])
            
            # If less than 3 points, add placeholders
            while len(points) < 3:
                points.append(f"[Add another key achievement or responsibility for {exp.get('title', 'this role')}]")
            
            # Enhance existing points if they're too short
            enhanced_points = []
            for point in points:
                if len(point) < 50 and not point.startswith('['):
                    # Add context suggestion
                    enhanced_point = point.rstrip('.') + " [Expand with: tools used, impact achieved, or scale of work]"
                    enhanced_points.append(enhanced_point)
                else:
                    enhanced_points.append(point)
            
            exp['points'] = enhanced_points


def apply_suggestions_rule_based(original_data: Dict, suggestions: List[Dict], job_role: str, job_desc: str) -> Dict:
    """
    Apply suggestions to resume data using rule-based approach
    Returns enhanced resume data
    """
    enhancer = ResumeEnhancer(original_data, suggestions, job_role, job_desc)
    return enhancer.apply_changes()