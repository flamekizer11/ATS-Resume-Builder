#!/usr/bin/env python3
"""
Test script to recreate a resume from extracted text
Tests the full pipeline: text → structured data → DOCX generation
"""

import os
import sys
from pathlib import Path

# Add app directory to path for imports
sys.path.append(str(Path(__file__).parent / 'app'))

from app.services.rule_based_parser import RuleBasedParser
from app.services.generator import generate_ats_resume


def test_resume_recreation():
    """Test recreating a resume from extracted text"""

    # Path to the extracted text file
    extracted_text_file = "extracted_text_Pratik_Singh_Resume_Mu.txt"

    if not os.path.exists(extracted_text_file):
        print(f"❌ Extracted text file not found: {extracted_text_file}")
        print("Please run test_extraction.py first to generate the extracted text.")
        return

    print("🧪 Resume Recreation Test")
    print("=" * 50)

    # Step 1: Read the extracted text
    print(f"📖 Reading extracted text from: {extracted_text_file}")
    try:
        with open(extracted_text_file, 'r', encoding='utf-8') as f:
            extracted_text = f.read()
    except Exception as e:
        print(f"❌ Error reading file: {e}")
        return

    print(f"✅ Read {len(extracted_text)} characters")

    # Step 2: Parse the text into structured data
    print("\n🔄 Parsing text into structured data...")
    try:
        parser = RuleBasedParser(extracted_text)
        structured_data = parser.parse()
    except Exception as e:
        print(f"❌ Error parsing text: {e}")
        return

    print("✅ Parsing completed")

    # Step 3: Display some key information from parsed data
    print("\n📊 Parsed Data Summary:")
    print(f"  Name: {structured_data.get('personal', {}).get('name', 'N/A')}")
    print(f"  Email: {structured_data.get('personal', {}).get('email', 'N/A')}")
    print(f"  Skills: {len(structured_data.get('skills', []))} skills found")
    print(f"  Experience: {len(structured_data.get('experience', []))} positions")
    print(f"  Education: {len(structured_data.get('education', []))} entries")
    print(f"  Projects: {len(structured_data.get('projects', []))} projects")

    # Step 4: Generate the DOCX resume
    output_dir = "outputs"
    os.makedirs(output_dir, exist_ok=True)

    output_filename = os.path.join(output_dir, "recreated_resume.docx")

    print(f"\n📝 Generating DOCX resume: {output_filename}")
    try:
        generate_ats_resume(structured_data, output_filename)
    except Exception as e:
        print(f"❌ Error generating DOCX: {e}")
        return

    print("✅ DOCX generation completed")

    # Step 5: Verify the output file
    if os.path.exists(output_filename):
        file_size = os.path.getsize(output_filename)
        print(f"✅ Output file created: {output_filename} ({file_size} bytes)")
        print("\n🎉 Resume recreation test completed successfully!")
        print(f"📂 Check the outputs folder for: recreated_resume.docx")
    else:
        print("❌ Output file was not created")


def display_parsed_data_sample(data: dict):
    """Display a sample of the parsed data for verification"""
    print("\n🔍 Sample Parsed Data:")

    # Personal info
    personal = data.get('personal', {})
    if personal:
        print(f"Personal: {personal}")

    # Summary
    summary = data.get('summary', '')
    if summary:
        print(f"Summary: {summary[:100]}...")

    # Skills (first 5)
    skills = data.get('skills', [])
    if skills:
        print(f"Skills: {skills[:5]}{'...' if len(skills) > 5 else ''}")

    # Experience (first entry)
    experience = data.get('experience', [])
    if experience:
        first_exp = experience[0]
        print(f"First Experience: {first_exp.get('title', 'N/A')} at {first_exp.get('company', 'N/A')}")


if __name__ == "__main__":
    test_resume_recreation()