import streamlit as st
import pdfplumber
from PyPDF2 import PdfReader, PdfWriter
import io
import zipfile

def split_pdf_universal(uploaded_file):
    file_bytes = uploaded_file.read()
    subject_ranges = []
    current_header = None
    start_page = 0

    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        total_pages = len(pdf.pages)
        
        for i, page in enumerate(pdf.pages):
            text = page.extract_text()
            if text:
                # Get the first non-empty line as the header
                lines = [line.strip() for line in text.split('\n') if line.strip()]
                if lines:
                    detected_header = lines[0]
                    
                    # Logic: If the header changes, we've found a new section
                    if current_header is None:
                        current_header = detected_header
                    elif detected_header != current_header:
                        # Before switching, check if this new header looks like a title 
                        # (often titles repeat, so we only split if it's a significant change)
                        subject_ranges.append((current_header, start_page, i))
                        current_header = detected_header
                        start_page = i
        
        # Add the final section
        if current_header:
            subject_ranges.append((current_header, start_page, total_pages))

    # Splitting and Zipping
    reader = PdfReader(io.BytesIO(file_bytes))
    zip_buffer = io.BytesIO()
    
    with zipfile.ZipFile(zip_buffer, "w") as zipf:
        for name, start, end in subject_ranges:
            writer = PdfWriter()
            # Clean filename: remove symbols that Windows/Mac don't like
            safe_name = "".join([c for c in name if c.isalnum() or c in (' ', '_')]).strip()
            # Truncate long names to prevent OS errors
            safe_name = safe_name[:50] 
            
            for page_num in range(start, end):
                writer.add_page(reader.pages[page_num])
            
            pdf_output = io.BytesIO()
            writer.write(pdf_output)
            zipf.writestr(f"{safe_name}.pdf", pdf_output.getvalue())

    zip_buffer.seek(0)
    return zip_buffer.getvalue(), len(subject_ranges)

# --- Streamlit UI ---
st.set_page_config(page_title="Universal PDF Splitter", page_icon="✂️")
st.title("✂️ Universal PDF Section Splitter")
st.write("Upload any PDF where sections are defined by a title on the first line of the page.")

uploaded_file = st.file_uploader("Upload PDF file", type="pdf")

if uploaded_file is not None:
    if st.button("Analyze & Split"):
        with st.spinner("Detecting sections and splitting..."):
            zip_data, count = split_pdf_universal(uploaded_file)
            
            if count > 1:
                st.success(f"Successfully identified and split {count} sections!")
                st.download_button(
                    label=f"Download {count} PDFs (ZIP)",
                    data=zip_data,
                    file_name="Split_Documents.zip",
                    mime="application/zip"
                )
            else:
                st.warning("Only one section detected. Ensure your PDF has distinct headers on the first line of new sections.")
