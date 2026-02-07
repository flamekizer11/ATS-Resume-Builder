import pdfplumber
import docx
import os
import re

def extract_text_from_file(file_path: str) -> str:
    """
    Extract text from PDF or DOCX file

    Args:
        file_path: Path to the file

    Returns:
        Extracted text as string
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    file_extension = file_path.lower().split('.')[-1]

    if file_extension == 'pdf':
        text = extract_text_from_pdf(file_path)
    elif file_extension in ['docx', 'doc']:
        text = extract_text_from_docx(file_path)
    else:
        raise ValueError(f"Unsupported file type: {file_extension}")

    # Apply light, safe post-processing
    text = post_process_text(text)

    return text

def extract_text_from_pdf(file_path: str) -> str:
    """
    Extract text from PDF file using pdfplumber
    """
    with pdfplumber.open(file_path) as pdf:
        text = ""
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
        return text.strip()

def extract_text_from_docx(file_path: str) -> str:
    """
    Extract text from DOCX file using python-docx
    """
    doc = docx.Document(file_path)
    text = ""
    for paragraph in doc.paragraphs:
        text += paragraph.text + "\n"
    return text.strip()

def post_process_text(text: str) -> str:
    """
    Apply sophisticated post-processing to preserve layout semantics

    CRITICAL POINTS:
    1. Header de-duplication guard: Skip duplicate section headers
    2. Bullet + header firewall: Never attach bullets to section headers
    3. Section-aware bullet scope: Bullets only valid in EXPERIENCE/KEY PROJECTS
    4. Project title detector: Convert bullet-prefixed titles to plain titles
    5. Summary protection: Disable aggressive merging in PROFESSIONAL SUMMARY
    """
    lines = text.split('\n')
    processed_lines = []

    # Section detection patterns (case-insensitive)
    section_patterns = [
        r'^(professional\s+summary|summary|objective|profile|about\s+me)$',
        r'^(work\s+experience|experience|employment|work\s+history|professional\s+experience)$',
        r'^(education|academic|qualifications|educational\s+background)$',
        r'^(skills|technical\s+skills|core\s+competencies|expertise|competencies)$',
        r'^(projects|personal\s+projects|key\s+projects)$',
        r'^(certifications?|licenses?|credentials)$',
        r'^(achievements?|awards?|honors?|accomplishments)$',
        r'^(languages?|technical\s+proficiencies)$',
        r'^(interests?|hobbies)$',
        r'^(references?|contact\s+information)$'
    ]

    # Bullet markers to detect
    bullet_markers = [r'•', r'-', r'–', r'▪', r'○', r'●', r'■', r'♦']

    # Sections where bullets are allowed
    bullet_allowed_sections = ['EXPERIENCE', 'KEY PROJECTS', 'PROJECTS']

    i = 0
    current_section = None
    last_non_empty_line = None
    last_line_was_bullet = False

    while i < len(lines):
        line = lines[i].strip()

        # Skip empty lines at the start
        if not line:
            i += 1
            continue

        # HEADER DE-DUPLICATION GUARD
        # Check if this is a duplicate section header
        is_duplicate_header = False
        for pattern in section_patterns:
            if re.match(pattern, line.lower()):
                if last_non_empty_line and last_non_empty_line.upper() == line.upper():
                    is_duplicate_header = True
                break

        if is_duplicate_header:
            i += 1
            continue

        # DETECT CURRENT SECTION
        section_detected = False
        for pattern in section_patterns:
            if re.match(pattern, line.lower()):
                current_section = line.upper()
                section_detected = True
                break

        # Also check for all-caps lines (common section headers)
        if not section_detected and re.match(r'^[A-Z\s]{3,}$', line) and len(line) > 3:
            current_section = line.upper()
            section_detected = True

        if section_detected:
            # Add blank line before section headers (except first)
            if processed_lines:
                processed_lines.append('')
            processed_lines.append(current_section)
            last_non_empty_line = current_section
            i += 1
            continue

        # MID-SENTENCE BULLET SPLIT PROTECTION
        # To check if this line starts with bullet and should merge with next line
        if any(line.startswith(marker) or re.match(rf'^\s*{re.escape(marker)}\s', line) for marker in bullet_markers):
            next_line_check = lines[i + 1].strip() if i + 1 < len(lines) else ""
            if next_line_check and not re.search(r'[.!?;]$', line) and next_line_check[0].islower():
                # Merge bullet line with next line before processing
                line = line + " " + next_line_check
                i += 1  # Skip the next line since we merged it

        # BULLET + HEADER FIREWALL & SECTION-AWARE BULLET SCOPE
        # Check if this line contains ONLY a bullet symbol
        is_standalone_bullet = False
        for marker in bullet_markers:
            if re.match(rf'^\s*{re.escape(marker)}\s*$', line):
                is_standalone_bullet = True
                break

        if is_standalone_bullet:
            # Only process bullets if we're in an allowed section
            if current_section and any(allowed in current_section for allowed in bullet_allowed_sections):
                # Find the next non-empty line and check if it's a valid target
                bullet_marker = line.strip()
                j = i + 1
                valid_target_found = False
                while j < len(lines):
                    next_line = lines[j].strip()
                    if next_line:
                        # SO that we never attach to section headers or ALL CAPS lines
                        is_header_target = (
                            next_line.isupper() or
                            any(re.match(pattern, next_line.lower()) for pattern in section_patterns)
                        )

                        if not is_header_target:
                            # PROJECT TITLE DETECTION
                            # A line is a project title if:
                            # - No verbs (developed, created, built, using, with)
                            # - Title case
                            # - Reasonable length
                            # - Appears after "Tech:" line or blank line
                            has_verbs = any(word in next_line.lower() for word in [
                                'developed', 'created', 'built', 'using', 'with', 'performed',
                                'completed', 'integrated', 'deployed', 'designed', 'produced'
                            ])
                            is_title_case = next_line.istitle()
                            reasonable_length = 3 <= len(next_line.split()) <= 12

                            # Check context: after Tech: or blank line or section header
                            prev_was_tech = False
                            prev_was_blank = False
                            prev_was_section = False
                            if processed_lines:
                                last_processed = processed_lines[-1]
                                prev_was_tech = last_processed.startswith('Tech:')
                                prev_was_blank = last_processed == ''
                                prev_was_section = any(re.match(pattern, last_processed.upper()) for pattern in section_patterns)

                            is_project_title = (
                                not has_verbs and
                                is_title_case and
                                reasonable_length and
                                (prev_was_tech or prev_was_blank or prev_was_section)
                            )

                            if is_project_title:
                                # Convert to plain title (remove bullet)
                                processed_lines.append(next_line)
                            else:
                                # Normal bullet attachment
                                merged_bullet = f"{bullet_marker} {next_line}"
                                processed_lines.append(merged_bullet)
                            valid_target_found = True
                            i = j + 1  # Skip the line we just processed
                            break
                        else:
                            # Invalid target, stop looking
                            break
                    j += 1

                # TRAILING ORPHAN BULLETS 
                # If no valid target found, discard the bullet entirely
                if not valid_target_found:
                    pass  # Discard the bullet
                i += 1  # Always advance past the bullet
            else:
                # Not in bullet-allowed section, skip the bullet
                i += 1
            continue

        # PRE-BULLET SENTENCE MERGING 
        # To check if we should merge with next line BEFORE processing bullets
        should_merge = False
        next_line = lines[i + 1].strip() if i + 1 < len(lines) else ""

        if next_line:
            # Conditions for merging (applied before bullet processing):
            ends_with_sentence = re.search(r'[.!?;]$', line)
            next_starts_lowercase = next_line[0].islower() if next_line else False
            continuation_words = ['and', 'or', 'but', 'the', 'a', 'an', 'in', 'on', 'at', 'to', 'for', 'with', 'by', 'from']
            next_is_continuation = next_line.lower().split()[0] in continuation_words if next_line else False

            # Don't merge if next line is a section header
            next_is_section = any(re.match(pattern, next_line.lower()) for pattern in section_patterns)

            # Special handling for CERTIFICATIONS section
            if current_section and 'CERTIFICATION' in current_section:
                should_merge = not ends_with_sentence or ',' in line
            else:
                should_merge = (not ends_with_sentence and
                              (next_starts_lowercase or next_is_continuation) and
                              not next_is_section)

        if should_merge:
            # Merge with next line
            merged_line = line + " " + next_line
            processed_lines.append(merged_line)
            last_non_empty_line = merged_line
            last_line_was_bullet = False  # Reset bullet tracking after merge
            i += 2
            continue

        # PROJECT TITLE DETECTION 
        # Check if this line is a project title that should not get a bullet
        is_project_title = False
        if (current_section and 'PROJECTS' in current_section and
            not any(word in line.lower() for word in [
                'developed', 'created', 'built', 'using', 'with', 'performed',
                'completed', 'integrated', 'deployed', 'designed', 'produced',
                'built', 'using', 'with', 'performed', 'completed', 'integrated',
                'deployed', 'designed', 'produced', 'analyzed', 'managed', 'led'
            ]) and
            line.istitle() and
            3 <= len(line.split()) <= 12):
            # Check context: after Tech: or blank line or section header
            prev_was_tech = False
            prev_was_blank = False
            prev_was_section = False
            if processed_lines:
                last_processed = processed_lines[-1]
                prev_was_tech = last_processed.startswith('Tech:')
                prev_was_blank = last_processed == ''
                prev_was_section = any(re.match(pattern, last_processed.upper()) for pattern in section_patterns)

            is_project_title = prev_was_tech or prev_was_blank or prev_was_section

        # BULLET INHERITANCE FOR CONTINUATION LINES
        # If the last processed line was a bullet and this line is a continuation, prefix with bullet
        if (not is_project_title and
            processed_lines and processed_lines[-1].startswith('• ') and
            current_section and any(allowed in current_section for allowed in bullet_allowed_sections) and
            not line.isupper() and  # Not a section header
            not any(re.match(pattern, line.lower()) for pattern in section_patterns) and  # Not a section header
            not line.startswith('• ') and  # Not already a bullet
            not any(line.startswith(marker) for marker in bullet_markers)):  # Not a bullet
            line = f"• {line}"

        # Check if current line starts with bullet 
        is_bullet_line = False
        for marker in bullet_markers:
            if line.startswith(marker) or re.match(rf'^\s*{re.escape(marker)}\s', line):
                is_bullet_line = True
                # Only normalize if in allowed section
                if current_section and any(allowed in current_section for allowed in bullet_allowed_sections):
                    line = re.sub(rf'^\s*{re.escape(marker)}\s*', '• ', line)

                    # TECH: LINES ARE NEVER BULLETS
                    # Strip bullet marker from Tech: lines
                    if line.startswith('• Tech:'):
                        line = line[2:]  # Remove the "• " prefix
                        is_bullet_line = False  # Mark as not a bullet
                else:
                    # Remove bullet marker entirely
                    line = re.sub(rf'^\s*{re.escape(marker)}\s*', '', line)
                    is_bullet_line = False
                break

        # Update bullet tracking
        last_line_was_bullet = is_bullet_line

        # ANCHOR DATES AND LOCATIONS
        date_location_pattern = r'^\d{1,2}/\d{4}\s*[-–]\s*\d{1,2}/\d{4}.*\|.*$|^\d{1,2}/\d{4}\s*[-–]\s*present.*\|.*$'
        if re.match(date_location_pattern, line, re.IGNORECASE):
            processed_lines.append(line)
            last_non_empty_line = line
            i += 1
            continue

        # ENFORCE SECTION BOUNDARIES
        role_pattern = r'^[^,]+,\s*[^,]+\s*\d{1,2}/\d{4}'
        if re.match(role_pattern, line):
            if processed_lines and processed_lines[-1]:
                processed_lines.append('')
            processed_lines.append(line)
            last_non_empty_line = line
            i += 1
            continue

        # Default: add the line as-is
        processed_lines.append(line)
        last_non_empty_line = line
        i += 1

    # Final cleanup: remove excessive blank lines
    final_lines = []
    prev_blank = False
    for line in processed_lines:
        is_blank = not line.strip()
        if is_blank and prev_blank:
            continue  # Skip consecutive blanks
        final_lines.append(line)
        prev_blank = is_blank

    return '\n'.join(final_lines)