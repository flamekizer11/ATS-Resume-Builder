#!/usr/bin/env python3
"""
Test script to parse extracted resume text and generate a new DOCX resume
Uses the main pipeline components: parser → structured data → generator
"""

import os
import sys
from pathlib import Path

# Add app directory to path for imports
sys.path.append(str(Path(__file__).parent / 'app'))

from app.services.rule_based_parser import RuleBasedParser
from app.services.generator import generate_ats_resume


def main():
    """Main function to test resume parsing and generation"""

    print("🧪 Resume Parsing & Generation Test")
    print("=" * 50)

    # Input file (extracted text)
    input_file = "extracted_text_Pratik_Singh_Resume_Mu.txt"

    # Check if input file exists
    if not os.path.exists(input_file):
        print(f"❌ Input file not found: {input_file}")
        print("Please run test_extraction.py first to extract text from a resume.")
        return

    print(f"📖 Input file: {input_file}")

    # Step 1: Read the extracted text
    print("\n1️⃣ Reading extracted text...")
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            text = f.read()
        print(f"✅ Read {len(text)} characters")
    except Exception as e:
        print(f"❌ Error reading file: {e}")
        return

    # Step 2: Parse the text into structured data
    print("\n2️⃣ Parsing text into structured resume data...")
    try:
        parser = RuleBasedParser(text)
        resume_data = parser.parse()
        print("✅ Parsing completed successfully")
    except Exception as e:
        print(f"❌ Error parsing text: {e}")
        return

    # Step 3: Display key extracted information
    print("\n3️⃣ Extracted Information Summary:")
    personal = resume_data.get('personal', {})
    print(f"   👤 Name: {personal.get('name', 'Not found')}")
    print(f"   📧 Email: {personal.get('email', 'Not found')}")
    print(f"   📱 Phone: {personal.get('phone', 'Not found')}")
    print(f"   📍 Location: {personal.get('location', 'Not found')}")

    summary = resume_data.get('summary', '')
    print(f"   📝 Summary: {summary[:80]}{'...' if len(summary) > 80 else ''}")

    skills = resume_data.get('skills', [])
    print(f"   🛠️ Skills: {len(skills)} skills extracted")

    experience = resume_data.get('experience', [])
    print(f"   💼 Experience: {len(experience)} positions")

    education = resume_data.get('education', [])
    print(f"   🎓 Education: {len(education)} entries")

    projects = resume_data.get('projects', [])
    print(f"   🚀 Projects: {len(projects)} projects")

    # Step 4: Generate the new DOCX resume
    print("\n4️⃣ Generating new DOCX resume...")
    output_dir = "outputs"
    os.makedirs(output_dir, exist_ok=True)

    output_file = os.path.join(output_dir, "generated_resume.docx")

    try:
        generate_ats_resume(resume_data, output_file)
        print("✅ DOCX generation completed")
    except Exception as e:
        print(f"❌ Error generating DOCX: {e}")
        return

    # Step 5: Verify output
    if os.path.exists(output_file):
        file_size = os.path.getsize(output_file)
        print(f"\n✅ Success! Generated resume: {output_file}")
        print(f"   📊 File size: {file_size} bytes")
        print(f"   📂 Location: {os.path.abspath(output_file)}")
    else:
        print("❌ Output file was not created")

    print("\n🎉 Test completed!")


if __name__ == "__main__":
    main()