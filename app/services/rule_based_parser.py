import re
import spacy
from typing import Dict, List
from collections import Counter

try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    nlp = None
    print("spaCy model not found. Install with: python -m spacy download en_core_web_sm")


class RuleBasedParser:
    """Extract resume data using rule-based patterns"""

    # Common section headers - expanded patterns
    SECTION_PATTERNS = {
        'summary': r'(professional\s+summary|summary|objective|profile|about\s+me|career\s+summary|personal\s+statement)',
        'experience': r'(work\s+experience|experience|employment|work\s+history|professional\s+experience|career\s+history)',
        'education': r'(education|academic|qualifications|educational\s+background|academic\s+background)',
        'skills': r'(skills|technical\s+skills|core\s+competencies|expertise|technical\s+expertise|key\s+skills)',
        'projects': r'(projects|personal\s+projects|academic\s+projects|key\s+projects|notable\s+projects)',
        'certifications': r'(certifications?|licenses?|certificates?|professional\s+certifications)',
        'achievements': r'(achievements?|awards?|honors?|accomplishments?|recognitions?)',
    }

    # Constants for parsing
    SECTION_BLOCK_SEPARATOR = r'\n\s*\n'
    DURATION_PATTERN = r'\b(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\w*\s+\d{4}\s*(?:-|to|–)\s*(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\w*\s+\d{4}|\b\d{4}\s*(?:-|to|–)\s*\d{4}'
    MIN_BLOCK_LENGTH = 50

    # Common skills to extract hardcoded for better recall (can be expanded)
    # if removed it will cause significant drop in skill extraction recall as many skills are mentioned in experience/project descriptions rather than a dedicated skills section
    # and relying solely on patterns will miss many skills that are not in a dedicated skills section or not mentioned in a standard way
    SKILLS_LIST = [
        'python', 'java', 'javascript', 'c++', 'sql', 'html', 'css', 'react', 'angular',
        'node.js', 'django', 'flask', 'machine learning', 'data analysis', 'excel',
        'power bi', 'tableau', 'aws', 'docker', 'git', 'agile', 'scrum'
    ]

    # Technology keywords for projects
    TECH_KEYWORDS = ['python', 'java', 'react', 'node', 'sql', 'html', 'css', 'javascript', 'angular']

    def __init__(self, text: str):
        self.text = text
        self.lines = [line.strip() for line in text.split('\n') if line.strip()]

    def parse(self) -> Dict:
        """Parse resume text into structured data"""
        return {
            'personal': self._extract_personal(),
            'summary': self._extract_summary(),
            'skills': self._extract_skills(),
            'experience': self._extract_experience(),
            'education': self._extract_education(),
            'projects': self._extract_projects(),
            'certifications': self._extract_certifications(),
            'achievements': self._extract_achievements(),
        }

    def _extract_personal(self) -> Dict:
        """Extract personal information from top of resume"""
        personal = {
            'name': '',
            'email': '',
            'phone': '',
            'linkedin': '',
            'location': '',
        }

        personal['email'] = self._extract_email()
        personal['phone'] = self._extract_phone()
        personal['linkedin'] = self._extract_linkedin()
        personal['name'] = self._extract_name()
        personal['location'] = self._extract_location()

        return personal

    def _extract_email(self) -> str:
        """Extract email address from text"""
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        match = re.search(email_pattern, self.text)
        return match.group() if match else ''

    def _extract_phone(self) -> str:
        """Extract phone number from text"""
        phone_pattern = r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b'
        match = re.search(phone_pattern, self.text)
        return match.group() if match else ''

    def _extract_linkedin(self) -> str:
        """Extract LinkedIn profile URL"""
        linkedin_pattern = r'linkedin\.com/in/[^\s]+'
        match = re.search(linkedin_pattern, self.text, re.IGNORECASE)
        return match.group() if match else ''

    def _extract_location(self) -> str:
        """Extract location from resume"""
        # Look for common location patterns in the first few lines
        location_keywords = ['mumbai', 'delhi', 'pune', 'chennai', 'bangalore', 'hyderabad',
                           'india', 'usa', 'uk', 'canada', 'australia']

        for line in self.lines[:10]:  # Check first 10 lines
            line_lower = line.lower()
            for location in location_keywords:
                if location in line_lower:
                    # Extract the location word(s) and clean up
                    words = line.split()
                    for i, word in enumerate(words):
                        if location in word.lower():
                            # Return 1-2 words around the location, cleaned
                            start = max(0, i-1)
                            end = min(len(words), i+2)
                            location_text = ' '.join(words[start:end])
                            # Remove | and extra spaces
                            location_text = location_text.replace('|', '').strip()
                            return location_text

        return ''

    def _extract_name(self) -> str:
        """Extract name from first few lines"""
        for line in self.lines[:5]:
            if self._is_likely_name(line):
                return line
        return ''

    def _is_likely_name(self, line: str) -> bool:
        """Check if a line looks like a name"""
        if not line:
            return False

        # Skip lines with contact keywords
        contact_keywords = ['email', 'phone', 'linkedin', 'address', 'location']
        if any(keyword in line.lower() for keyword in contact_keywords):
            return False

        # Check for 2-4 words, title case
        words = line.split()
        if 2 <= len(words) <= 4:
            return all(word and word[0].isupper() for word in words)

        return False

    def _extract_summary(self) -> str:
        """Extract professional summary"""
        return self._extract_section_content('summary')

    def _extract_skills(self) -> List[str]:
        """Extract skills from resume - comprehensive extraction from all sections"""
        skills = set()  # Use set to avoid duplicates

        # Get skills from dedicated skills section
        skills_section = self._extract_section_content('skills')
        if skills_section:
            skills.update(self._extract_skills_from_text(skills_section))

        # Extract skills from projects
        projects = self._extract_projects()
        for project in projects:
            skills.update(self._extract_skills_from_text(project.get('description', '')))
            skills.update(self._extract_skills_from_text(project.get('name', '')))

        # Extract skills from certifications
        certifications = self._extract_certifications()
        for cert in certifications:
            skills.update(self._extract_skills_from_text(cert))

        # Extract skills from experience
        experience = self._extract_experience()
        for exp in experience:
            skills.update(self._extract_skills_from_text(exp.get('title', '')))
            for point in exp.get('points', []):
                skills.update(self._extract_skills_from_text(point))

        # Extract skills from achievements
        achievements = self._extract_achievements()
        for achievement in achievements:
            skills.update(self._extract_skills_from_text(achievement))

        # Remove duplicates and sort
        return sorted(list(skills))

    def _extract_skills_from_text(self, text: str) -> List[str]:
        """Extract technical skills from any text using patterns and known skills"""
        found_skills = set()

        if not text:
            return []

        # Convert to lowercase for matching
        text_lower = text.lower()

        # First, match against known skills list
        for skill in self.SKILLS_LIST:
            if re.search(r'\b' + re.escape(skill.lower()) + r'\b', text_lower):
                found_skills.add(skill.title())

        # Additional comprehensive skill patterns
        # This list can be expanded with more specific tools, frameworks, and technologies relevant to the target job roles
        # This is used when skills are not mentioned in a dedicated skills section or not mentioned in a standard way and relying solely on patterns will miss many skills that are mentioned in experience/project descriptions
        # when not using API calls and totally relying on offline patterns will miss many skills that are mentioned in experience/project descriptions
        
        extended_skills = [
            # Programming & Frameworks
            'scikit-learn', 'xgboost', 'catboost', 'optuna', 'mlflow', 'langchain', 'fastapi',
            'transformers', 'llms', 'gpt-4o-mini', 'neo4j', 'cypher', 'pinecone', 'asyncio',
            'pytorch', 'tensorflow', 'keras', 'pandas', 'numpy', 'matplotlib', 'seaborn',
            'jupyter', 'docker', 'kubernetes', 'jenkins', 'github actions', 'spark', 'hadoop',
            'kafka', 'redis', 'mongodb', 'postgresql', 'mysql', 'sqlite',

            # Cloud & DevOps
            'aws s3', 'aws ec2', 'aws lambda', 'azure', 'gcp', 'heroku', 'vercel',

            # ML/DL/NLP
            'machine learning', 'deep learning', 'natural language processing', 'nlp',
            'computer vision', 'reinforcement learning', 'supervised learning', 'unsupervised learning',
            'regression', 'classification', 'clustering', 'dimensionality reduction', 'feature engineering',
            'hyperparameter tuning', 'cross-validation', 'ensemble methods', 'neural networks',
            'convolutional neural networks', 'recurrent neural networks', 'transformers',
            'bert', 'gpt', 'rag', 'retrieval-augmented generation', 'vector embeddings',
            'semantic search', 'knowledge graphs',

            # Data Science
            'data analysis', 'data visualization', 'eda', 'exploratory data analysis',
            'statistical analysis', 'a/b testing', 'hypothesis testing', 'time series analysis',

            # MLOps
            'model deployment', 'model monitoring', 'model versioning', 'ci/cd', 'pipeline',
            'experiment tracking', 'model registry', 'feature store',

            # Other Technical
            'api development', 'rest api', 'graphql', 'microservices', 'agile', 'scrum',
            'git', 'version control', 'linux', 'bash', 'powershell'
        ]

        for skill in extended_skills:
            if skill in text_lower:
                # Title case the skill name
                found_skills.add(' '.join(word.capitalize() for word in skill.split()))

        # Extract skills using regex patterns for common tech terms
        tech_patterns = [
            r'\b(?:python|java|javascript|typescript|c\+\+|c#|go|rust|php|ruby|swift|kotlin)\b',
            r'\b(?:react|angular|vue|node\.js|express|django|flask|spring|hibernate)\b',
            r'\b(?:html|css|sass|less|bootstrap|tailwind)\b',
            r'\b(?:sql|mysql|postgresql|mongodb|redis|cassandra|elasticsearch)\b',
            r'\b(?:aws|azure|gcp|heroku|digitalocean|linode)\b',
            r'\b(?:docker|kubernetes|terraform|ansible|puppet|chef)\b',
            r'\b(?:jenkins|github actions|gitlab ci|circleci|travis)\b'
        ]

        for pattern in tech_patterns:
            matches = re.findall(pattern, text_lower, re.IGNORECASE)
            for match in matches:
                found_skills.add(match.title() if isinstance(match, str) else str(match).title())

        return list(found_skills)

    def _extract_experience(self) -> List[Dict]:
        """Extract work experience"""
        exp_section = self._extract_section_content('experience')

        if not exp_section:
            return []

        experiences = []
        blocks = re.split(self.SECTION_BLOCK_SEPARATOR, exp_section)

        for block in blocks:
            if len(block.strip()) < self.MIN_BLOCK_LENGTH:
                continue

            exp_data = self._parse_experience_block(block)
            if exp_data['title'] or exp_data['points']:
                experiences.append(exp_data)

        return experiences

    def _parse_experience_block(self, block: str) -> Dict:
        """Parse a single experience block into structured data"""
        lines = block.strip().split('\n')
        if not lines:
            return self._create_empty_experience()

        exp = self._create_empty_experience()

        # Parse the first line which typically contains: Title | Company or Company, Title, Duration | Location
        first_line = lines[0].strip()

        # Handle "Title | Company" format first (common in DOCX)
        if '|' in first_line and not first_line.count('|') > 1:  # Avoid location separators
            parts = first_line.split('|', 1)
            exp['title'] = parts[0].strip()
            exp['company'] = parts[1].strip()
        else:
            # Pattern: "Company, Title DateRange | Location"
            # Example: "Pantech Prolab Pvt. Ltd., Intern 11/2023 – 02/2024 | Chennai, Tamil Nadu"

            # Extract location if present (after | )
            if '|' in first_line:
                parts = first_line.split('|', 1)
                first_line = parts[0].strip()
                exp['location'] = parts[1].strip()

            # Extract duration (date ranges)
            duration_match = re.search(r'\d{1,2}/\d{4}\s*[–-]\s*\d{1,2}/\d{4}', first_line)
            if duration_match:
                exp['duration'] = duration_match.group()
                # Remove duration from the line for cleaner parsing
                first_line = first_line.replace(duration_match.group(), '').strip()
                # Clean up extra commas/spaces
                first_line = re.sub(r',\s*,', ',', first_line)
                first_line = re.sub(r'\s+', ' ', first_line)

            # Now parse company and title
            # Pattern: "Company, Title"
            if ',' in first_line:
                parts = first_line.split(',', 1)
                exp['company'] = parts[0].strip()
                exp['title'] = parts[1].strip()
            else:
                # Fallback: assume whole line is title
                exp['title'] = first_line

        # Check next line for duration if not found in first line
        if not exp['duration'] and len(lines) > 1:
            second_line = lines[1].strip()
            duration_match = re.search(r'\d{1,2}/\d{4}\s*[–-]\s*\d{1,2}/\d{4}', second_line)
            if duration_match:
                exp['duration'] = duration_match.group()

        # Extract bullet points from remaining lines (skip duration line if it was separate)
        start_idx = 1
        if exp['duration'] and len(lines) > 1 and lines[1].strip() == exp['duration']:
            start_idx = 2
        exp['points'] = self._extract_points_from_lines(lines[start_idx:])

        return exp

    def _create_empty_experience(self) -> Dict:
        """Create empty experience dictionary"""
        return {
            'title': '',
            'company': '',
            'duration': '',
            'location': '',
            'points': []
        }

    def _extract_duration_from_text(self, text: str) -> str:
        """Extract duration pattern from text"""
        match = re.search(self.DURATION_PATTERN, text, re.IGNORECASE)
        return match.group() if match else ''

    def _extract_points_from_lines(self, lines: List[str]) -> List[str]:
        """Extract bullet points from lines"""
        points = []
        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Remove bullet markers
            if line.startswith(('-', '•', '◦', '▪')):
                points.append(line[1:].strip())
            elif len(line) > 20:  # Longer lines as points
                points.append(line)

        return points

    def _extract_education(self) -> List[Dict]:
        """Extract education information with improved parsing"""
        edu_section = self._extract_section_content('education')

        if not edu_section:
            return []

        education = []
        blocks = re.split(self.SECTION_BLOCK_SEPARATOR, edu_section)

        for block in blocks:
            lines = block.strip().split('\n')
            if not lines:
                continue

            edu = self._parse_education_block(block)
            if edu['degree'] or edu['institution']:
                education.append(edu)

        return education

    def _parse_education_block(self, block: str) -> Dict:
        """Parse a single education block"""
        edu = {
            'degree': '',
            'institution': '',
            'year': '',
            'gpa': ''
        }

        lines = block.strip().split('\n')

        # Process each line
        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Extract GPA
            gpa_match = re.search(r'GPA[:\s]*([\d.]+)', line, re.IGNORECASE)
            if gpa_match:
                edu['gpa'] = gpa_match.group(1)
                continue

            # Extract year
            year_match = re.search(r'\b(19|20)\d{2}\b', line)
            if year_match and not edu['year']:
                edu['year'] = year_match.group()
                # Remove year from line for cleaner parsing
                line = line.replace(year_match.group(), '').strip()

            # Parse degree and institution
            # Pattern: "Degree, Institution Year | Location"
            if ',' in line and not edu['degree']:
                parts = line.split(',', 1)
                potential_degree = parts[0].strip()
                potential_institution = parts[1].strip()

                # Clean up institution (remove year/location markers)
                potential_institution = re.sub(r'\s*\d{1,2}/\d{4}.*', '', potential_institution)
                potential_institution = re.sub(r'\s*\|\s*.*', '', potential_institution)

                # Check if institution contains university/college keywords
                if any(word in potential_institution.lower() for word in ['university', 'college', 'institute', 'school']):
                    edu['degree'] = potential_degree
                    edu['institution'] = potential_institution
                else:
                    # Fallback: assume whole line is degree if no institution found
                    edu['degree'] = potential_degree
                    if potential_institution:
                        edu['institution'] = potential_institution

        # If still no degree but we have content, use first line
        if not edu['degree'] and lines:
            edu['degree'] = lines[0].strip()

        return edu

    def _extract_projects(self) -> List[Dict]:
        """Extract projects with improved splitting logic"""
        proj_section = self._extract_section_content('projects')

        if not proj_section:
            return []

        # Split projects by identifying project boundaries
        projects_text = proj_section.strip()
        project_blocks = self._split_projects_into_blocks(projects_text)

        projects = []
        for block in project_blocks:
            proj_data = self._parse_project_block(block)
            if proj_data['name'] or proj_data['description']:
                projects.append(proj_data)

        return projects

    def _split_projects_into_blocks(self, projects_text: str) -> List[str]:
        """Split projects text into individual project blocks"""
        lines = [line.strip() for line in projects_text.split('\n') if line.strip()]
        blocks = []

        # Find project title indices - precise pattern matching
        title_indices = []
        seen_titles = set()  # Track seen titles to avoid duplicates

        for i, line in enumerate(lines):
            line_lower = line.lower().strip()

            # Skip tech lines
            if line_lower.startswith(('tech:', '• tech:', 'technologies:', '• technologies:', 'tools:', '• tools:')):
                continue

            # Skip description bullet points (start with action verbs or are continuations)
            if line.startswith('•'):
                clean_line = line[1:].strip().lower()
                if (clean_line.startswith(('developed', 'created', 'produced', 'built', 'designed', 'constructed',
                                        'assembled', 'utilized', 'organized', 'strengthened', 'performed',
                                        'completed', 'integrated', 'deployed', 'trained', 'enhanced',
                                        'refined', 'retrieval', 'embeddings'))) or \
                   ('and' in clean_line and len(clean_line.split()) > 10):  # Continuation lines
                    continue

            # Project titles:
            # 1. Lines with colons (like "Shell.ai: Multi-Output Fuel Blend Property Prediction")
            if ':' in line and len(line.split(':')[0].strip()) > 3:
                # Use the full title after the colon for uniqueness, but normalize for comparison
                full_title = line.strip().lower()
                normalized_title = full_title.replace('multioutput', 'multi-output').replace(' ', '').replace(':', '')
                if normalized_title not in seen_titles:
                    title_indices.append(i)
                    seen_titles.add(normalized_title)
            # 2. Standalone project titles (no colon, title case or technical titles, reasonable length)
            elif (not ':' in line and
                  3 <= len(line.split()) <= 8 and
                  not line_lower.startswith(('developed', 'created', 'built', 'using', 'with')) and
                  not line.islower() and  # Not all lowercase
                  any(keyword in line_lower for keyword in ['system', 'pipeline', 'prediction', 'recommendation',
                                                           'model', 'application', 'blend', 'churn', 'travel',
                                                           'hybrid', 'rag', 'customer'])):
                normalized_title = line.lower().replace(' ', '')
                if normalized_title not in seen_titles:
                    title_indices.append(i)
                    seen_titles.add(normalized_title)
            # 3. Short bullet points that look like project names
            elif line.startswith('•') and len(line) < 60 and not clean_line.startswith(('developed', 'created')):
                # Additional check: should contain project-like keywords
                if any(keyword in clean_line for keyword in ['system', 'pipeline', 'prediction', 'recommendation',
                                                           'model', 'application', 'blend', 'churn']):
                    if clean_line not in seen_titles:
                        title_indices.append(i)
                        seen_titles.add(clean_line)

        # Remove duplicates and sort
        title_indices = sorted(list(set(title_indices)))

        # If no titles found, return whole text as one block
        if not title_indices:
            return [projects_text] if projects_text else []

        # Create blocks
        for i, start_idx in enumerate(title_indices):
            end_idx = title_indices[i + 1] if i + 1 < len(title_indices) else len(lines)
            block_lines = lines[start_idx:end_idx]
            blocks.append('\n'.join(block_lines))

        return blocks

    def _parse_project_block(self, block: str) -> Dict:
        """Parse a single project block with improved extraction"""
        lines = block.strip().split('\n')
        if not lines:
            return self._create_empty_project()

        proj = self._create_empty_project()

        # Find the actual project name (first meaningful line that's not tech)
        for i, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue

            # Skip tech lines
            if line.lower().startswith(('tech:', 'technologies:', 'tech stack:', 'tools:', '• tech:')):
                continue

            # This should be the project name - handle both bullet and non-bullet titles
            clean_name = re.sub(r'[•\-*]\s*', '', line).strip()
            if clean_name and len(clean_name) > 5:  # Avoid very short names
                proj['name'] = clean_name
                break

        # Process all lines for tech and bullets
        bullet_points = []

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Check for tech stack (case-insensitive, with or without bullet)
            if line.lower().startswith(('tech:', 'technologies:', 'tech stack:', 'tools:')) or \
               line.lower().startswith(('• tech:', '• technologies:', '• tech stack:', '• tools:')):
                tech_part = line.split(':', 1)[1] if ':' in line else line
                # Clean up bullet markers
                tech_part = re.sub(r'[•\-*]\s*', '', tech_part)
                proj['tech'] = [tech.strip() for tech in tech_part.split(',') if tech.strip()]
                continue

            # Check for bullet points (but not tech lines)
            if line.startswith(('•', '-', '*')):
                clean_bullet = line[1:].strip()
                # Skip if it's the project title
                if clean_bullet and proj['name'] and not clean_bullet.startswith(proj['name'][:20]):
                    bullet_points.append(clean_bullet)
            elif len(line) > 10 and not line.lower().startswith(('tech:', 'technologies:', 'tech stack:', 'tools:')):
                # Use as bullet point if it's not the title
                if proj['name'] and not line.startswith(proj['name'][:20]):
                    bullet_points.append(line)

        # Set bullet points
        proj['points'] = bullet_points

        return proj

    def _create_empty_project(self) -> Dict:
        """Create empty project dictionary"""
        return {
            'name': '',
            'tech': [],
            'points': []
        }

    def _extract_tech_from_description(self, description: str) -> List[str]:
        """Extract technology keywords from project description"""
        tech_found = []
        for tech in self.TECH_KEYWORDS:
            if tech in description.lower():
                tech_found.append(tech.title())
        return tech_found

    def _extract_certifications(self) -> List[str]:
        """Extract certifications with improved splitting for concatenated entries"""
        cert_section = self._extract_section_content('certifications')

        if not cert_section:
            return []

        certs = []
        lines = cert_section.split('\n')

        for line in lines:
            line = line.strip()
            if not line or len(line) < 10:  # Skip very short lines
                continue

            # Check if line contains multiple certifications (common in DOCX)
            # Split on common separators: "•", major keywords, or long lines with multiple certs
            if '•' in line:
                # Split on bullet points
                parts = line.split('•')
                for part in parts:
                    part = part.strip()
                    if part and len(part) > 5:
                        certs.append(part)
            elif len(line) > 100:  # Very long line likely contains multiple certs
                # Try to split on common certification keywords
                import re
                # Split on patterns like "Machine Learning", "Deep Learning", etc.
                split_patterns = [
                    r'(?<=\w)\s+(?=Machine Learning)',
                    r'(?<=\w)\s+(?=Deep Learning)',
                    r'(?<=\w)\s+(?=Large Language Models)',
                    r'(?<=\w)\s+(?=TensorFlow)',
                    r'(?<=\w)\s+(?=CNNs|RNNs)',
                    r'(?<=\w)\s+(?=Classification|Regression|EDA)',
                    r'(?<=\w)\s+(?=Transformers|RAG|Agents)',
                    r'(?<=\w)\s+(?=LangChain)',
                ]

                temp_line = line
                for pattern in split_patterns:
                    temp_line = re.sub(pattern, '\n', temp_line)

                if '\n' in temp_line:
                    split_certs = temp_line.split('\n')
                    for cert in split_certs:
                        cert = cert.strip()
                        if cert and len(cert) > 5:
                            certs.append(cert)
                else:
                    # Fallback: keep as single cert
                    certs.append(line)
            else:
                # Single certification
                certs.append(line)

        # Remove duplicates and clean up
        unique_certs = []
        seen = set()
        for cert in certs:
            cert_lower = cert.lower().strip()
            if cert_lower not in seen and len(cert) > 5:
                unique_certs.append(cert)
                seen.add(cert_lower)

        return unique_certs

    def _extract_achievements(self) -> List[str]:
        """Extract achievements"""
        ach_section = self._extract_section_content('achievements')

        if not ach_section:
            return []

        return [line.strip() for line in ach_section.split('\n') if line.strip()]

    def _extract_section_content(self, section_name: str) -> str:
        """Extract content of a specific section with improved header detection"""
        pattern = self.SECTION_PATTERNS.get(section_name)
        if not pattern:
            return ""

        lines = self.lines
        section_start = -1

        # Find the best section header (prioritize standalone headers)
        for i, line in enumerate(lines):
            line_stripped = line.strip()

            # Skip empty lines
            if not line_stripped:
                continue

            # Check if this line matches the section pattern
            if re.search(pattern, line_stripped, re.IGNORECASE):
                # Prioritize headers that are standalone or at line start
                if (line_stripped.lower() == section_name or
                    line_stripped.lower().startswith(section_name) or
                    len(line_stripped.split()) <= 3):  # Short headers like "EXPERIENCE"
                    section_start = i
                    break
                elif section_start == -1:  # Keep as fallback if no better match
                    section_start = i

        if section_start == -1:
            return ""

        # Extract content until next section header
        content_lines = []
        for j in range(section_start + 1, len(lines)):
            next_line = lines[j].strip()

            # Stop if we hit another section header
            if next_line:
                is_section_header = False

                # Check if this line is a clear section header
                line_upper = next_line.upper()
                if (len(next_line.split()) <= 4 and  # Short lines
                    any(keyword in line_upper for keyword in ['EXPERIENCE', 'EDUCATION', 'SKILLS', 'PROJECTS', 'CERTIFICATIONS', 'ACHIEVEMENTS', 'AWARDS', 'PROFESSIONAL SUMMARY', 'SUMMARY', 'OBJECTIVE'])):
                    is_section_header = True
                elif next_line.isupper() and len(next_line) > 5:  # ALL CAPS lines that are substantial
                    is_section_header = True
                elif re.match(r'^[A-Z\s]+$', next_line) and len(next_line) > 5:  # All caps with spaces
                    is_section_header = True

                if is_section_header:
                    break

            content_lines.append(lines[j])

        return '\n'.join(content_lines).strip()


def parse_resume_rule_based(text: str) -> Dict:
    """
    Parse resume text using rule-based approach
    """
    parser = RuleBasedParser(text)
    return parser.parse()