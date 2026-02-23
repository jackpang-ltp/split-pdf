import streamlit as st
import pdfplumber
from PyPDF2 import PdfReader, PdfWriter
import io
import zipfile

def split_pdf_logic(uploaded_file):
    # 1. Read the file into memory once
    file_bytes = uploaded_file.read()
    
    # 2. First Pass: Detect Headers
    subject_ranges = []
    current_subject = None
    start_page = 0

    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        total_pages = len(pdf.pages)
        for i, page in enumerate(pdf.pages):
            text = page.extract_text()
            if text:
                # Look at the first 3 lines to find the "S1" header
                lines = [line.strip() for line in text.split('\n') if line.strip()]
                if lines:
                    header_candidate = lines[0]
                    if header_candidate.startswith("S1 ") and header_candidate != current_subject:
                        if current_subject:
                            subject_ranges.append((current_subject, start_page, i))
                        current_subject = header_candidate
                        start_page = i
        
        # Add the final subject
        if current_subject:
            subject_ranges.append((current_subject, start_page, total_pages))

    # 3. Second Pass: Split and Zip
    # We use a fresh BytesIO object for the reader
    reader = PdfReader(io.BytesIO(file_bytes))
    zip_buffer = io.BytesIO()
    
    if not subject_ranges:
        return None # Return None if no headers were found

    with zipfile.ZipFile(zip_buffer, "w") as zipf:
        for name, start, end in subject_ranges:
            writer = PdfWriter()
            # Clean filename
            safe_name = "".join([c for c in name if c.isalnum() or c in (' ', '_')]).strip()
            
            for page_num in range(start, end):
                writer.add_page(reader.pages[page_num])
            
            pdf_output = io.BytesIO()
            writer.write(pdf_output)
            zipf.writestr(f"{safe_name}.pdf", pdf_output.getvalue())

    zip_buffer.seek(0)
    return zip_buffer.getvalue()

# --- Streamlit UI ---
st.set_page_config(page_title="PDF Subject Splitter", page_icon="📄")
st.title("📄 PDF Subject Splitter")
st.info("Upload the 'S1 All Subjects Analysis Report' to split it by subject header automatically.")

uploaded_file = st.file_uploader("Upload S1 Analysis PDF", type="pdf")

if uploaded_file is not None:
    if st.button("Process & Generate ZIP"):
        with st.spinner("Processing pages..."):
            zip_data = split_pdf_logic(uploaded_file)
            
            if zip_data:
                st.success(f"Split completed! Found {zip_data.count(b'.pdf')} subjects.")
                st.download_button(
                    label="Download Results (ZIP)",
                    data=zip_data,
                    file_name="S1_Split_Reports.zip",
                    mime="application/zip"
                )
            else:
                st.error("No headers starting with 'S1 ' were detected. Please check the PDF format.")
