"""
Test PDF reading functionality
"""

import os
import glob
import fitz  # PyMuPDF

def test_pdf_reading(data_folder="data"):
    """Test reading PDF files from data folder"""
    
    # Get all PDF files in the data folder
    pdf_files = glob.glob(os.path.join(data_folder, "*.pdf"))
    
    if not pdf_files:
        print(f"❌ No PDF files found in {data_folder} folder")
        print("📝 Please add your PDF books to the data folder")
        print("📂 Current files in data folder:")
        for file in glob.glob(os.path.join(data_folder, "*")):
            print(f"  - {os.path.basename(file)}")
        return None, []
    
    print(f"📂 Found {len(pdf_files)} PDF files:")
    for file_path in pdf_files:
        print(f"  - {os.path.basename(file_path)}")
    
    all_text = ""
    processed_files = []
    
    # Read and extract text from all PDF files
    for file_path in pdf_files:
        try:
            with fitz.open(file_path) as doc:
                text_content = ""
                for page_num in range(len(doc)):
                    page = doc.load_page(page_num)
                    text_content += page.get_text()
                
                if text_content.strip():
                    all_text += "\n\n" + text_content
                    processed_files.append(os.path.basename(file_path))
                    print(f"✅ Loaded: {os.path.basename(file_path)} ({len(text_content)} characters, {len(doc)} pages)")
                else:
                    print(f"⚠️  Empty PDF: {os.path.basename(file_path)}")
        except Exception as e:
            print(f"❌ Error reading {file_path}: {e}")
    
    if not all_text.strip():
        print("❌ No content found in any PDF files")
        return None, []
    
    print(f"\n📄 Total extracted text length: {len(all_text)} characters")
    return all_text, processed_files

if __name__ == "__main__":
    print("🔍 Testing PDF reading functionality...")
    text, files = test_pdf_reading()
    
    if text:
        print(f"\n📋 First 500 characters of extracted text:")
        print(text[:500] + "..." if len(text) > 500 else text)
        print(f"\n✅ PDF reading test completed!")
    else:
        print("\n📝 Add PDF files to the data folder to test")
