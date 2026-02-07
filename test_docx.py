from app.services.parser import extract_text_from_file
from app.services.rule_based_parser import parse_resume_rule_based

# Parse the DOCX file
docx_path = r'c:\Users\pc\Desktop\resume_creator\outputs\optimized_Pratik_Singh_Resume_Mu (1) copy.docx'
text = extract_text_from_file(docx_path)
parsed_data = parse_resume_rule_based(text)

print('=== DOCX FILE PARSING RESULTS ===')
print(f'Summary: "{parsed_data["summary"]}"')
print(f'Skills count: {len(parsed_data["skills"])}')
print(f'Experience count: {len(parsed_data["experience"])}')
print(f'Education count: {len(parsed_data["education"])}')
print(f'Projects count: {len(parsed_data["projects"])}')
print(f'Certifications count: {len(parsed_data["certifications"])}')
print(f'Achievements count: {len(parsed_data["achievements"])}')
print()

# Check specific sections
print('SUMMARY CONTENT:')
print(repr(parsed_data['summary']))
print()

print('EXPERIENCE:')
for exp in parsed_data['experience']:
    print(f'  Title: "{exp["title"]}"')
    print(f'  Company: "{exp["company"]}"')
    print(f'  Duration: "{exp["duration"]}"')
print()

print('PROJECTS:')
for proj in parsed_data['projects']:
    print(f'  Name: "{proj["name"]}"')
    print(f'  Tech: {proj["tech"]}')
    print(f'  Points: {len(proj["points"])} items')