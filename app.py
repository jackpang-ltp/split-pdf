import streamlit as st
import pdfplumber
from PyPDF2 import PdfReader, PdfWriter
import io
import zipfile
import os

def split_pdf_logic(uploaded_file):
    input_pdf = io.BytesIO(uploaded_file.read())
    
    subject_ranges = []
    current_subject = None
    start_page = 0

    with pdfplumber.open(input_pdf) as pdf:
        total_pages = len(pdf.pages)
        for i, page in enumerate(pdf.pages):
            text = page.extract_text()
            
            # --- FIX STARTS HERE ---
            # Check if text exists on the page at all
            if text and text.strip():
                lines = text.split('\n')
                # Check the first few lines in case the header isn't exactly the first line
                first_line = lines[0].strip()
                
                if first_line.startswith("S1 ") and first_line != current_subject:
                    if current_subject:
                        subject_ranges.append((current_subject, start_page, i))
                    current_subject = first_line
                    start_page = i
            # --- FIX ENDS HERE ---
        
        # Add the final subject
        if current_subject:
            subject_ranges.append((current_subject, start_page, total_pages))

    # Splitting and Zipping logic remains the same...
    reader = PdfReader(input_pdf)
    zip_buffer = io.BytesIO()
    
    with zipfile.ZipFile(zip_buffer, "w") as zipf:
        for name, start, end in subject_ranges:
            writer = PdfWriter()
            # Clean filename for OS compatibility
            safe_name = "".join([c for c in name if c.isalnum() or c in (' ', '_')]).strip()
            
            for page_num in range(start, end):
                writer.add_page(reader.pages[page_num])
            
            pdf_output = io.BytesIO()
            writer.write(pdf_output)
            zipf.writestr(f"{safe_name}.pdf", pdf_output.getvalue())

    return zip_buffer.getvalue()

# Streamlit UI
st.title("PDF Subject Splitter")
st.write("Upload the 'S1 All Subjects Analysis Report' to split it by subject header.")

uploaded_file = st.file_uploader("Choose a PDF file", type="pdf")

if uploaded_file is not None:
    if st.button("Process and Split"):
        with st.spinner("Analyzing and splitting PDF..."):
            zip_data = split_pdf_logic(uploaded_file)
            
            st.success("Successfully split the PDF!")
            st.download_button(
                label="Download All PDFs (.zip)",
                data=zip_data,
                file_name="Split_Subject_Reports.zip",
                mime="application/zip"
            )
