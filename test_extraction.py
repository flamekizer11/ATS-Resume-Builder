#!/usr/bin/env python3
"""
Test script to extract text from resume files in uploads folder
"""

import os
import sys
from app.services.parser import extract_text_from_file

def test_text_extraction():
    """Test text extraction from files in uploads folder"""

    # Get uploads directory
    uploads_dir = "uploads"

    if not os.path.exists(uploads_dir):
        print(f"❌ Uploads directory '{uploads_dir}' not found!")
        return

    # List files in uploads
    files = [f for f in os.listdir(uploads_dir) if f.lower().endswith(('.pdf', '.docx', '.doc'))]

    if not files:
        print(f"❌ No PDF/DOCX files found in '{uploads_dir}' folder!")
        print("Please place a resume file in the uploads folder first.")
        return

    print(f"📁 Found {len(files)} file(s) in uploads folder:")
    for i, file in enumerate(files, 1):
        print(f"  {i}. {file}")

    # If multiple files, ask which one
    if len(files) > 1:
        try:
            choice = int(input("\nEnter the number of the file to test (1-{}): ".format(len(files))))
            if choice < 1 or choice > len(files):
                print("❌ Invalid choice!")
                return
            selected_file = files[choice - 1]
        except ValueError:
            print("❌ Invalid input!")
            return
    else:
        selected_file = files[0]
        print(f"\n📄 Testing with: {selected_file}")

    # Extract text
    file_path = os.path.join(uploads_dir, selected_file)

    try:
        print(f"\n🔄 Extracting text from: {selected_file}")
        print("=" * 60)

        extracted_text = extract_text_from_file(file_path)

        print("✅ Text extraction successful!")
        print(f"📊 Total characters: {len(extracted_text)}")
        print(f"📊 Total lines: {len(extracted_text.splitlines())}")
        print("\n" + "=" * 60)
        print("EXTRACTED TEXT:")
        print("=" * 60)
        print(extracted_text)
        print("=" * 60)

        # Save to file for inspection
        output_file = f"extracted_text_{selected_file.rsplit('.', 1)[0]}.txt"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(extracted_text)
        print(f"\n💾 Extracted text also saved to: {output_file}")

    except Exception as e:
        print(f"❌ Text extraction failed: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🧪 Resume Text Extraction Test")
    print("=" * 40)
    test_text_extraction()