from fastapi import FastAPI
from fastapi.responses import FileResponse
from fpdf import FPDF
import os

app = FastAPI()
OUTPUT_PDF = "tailored_resume.pdf"

@app.get("/download")
def download_resume():
    if os.path.exists(OUTPUT_PDF):
        return FileResponse(path=OUTPUT_PDF, filename="tailored_resume.pdf", media_type='application/pdf')
    return {"error": "No resume found to download."}

def save_resume_to_pdf(text: str):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    
    for line in text.split('\n'):
        pdf.multi_cell(0, 10, line)
    
    pdf.output(OUTPUT_PDF)





# from fpdf import FPDF

# def save_resume_to_pdf(text: str):
#     pdf = FPDF()
#     pdf.set_auto_page_break(auto=True, margin=15)
#     pdf.add_page()
#     pdf.set_font("Arial", size=12)
    
#     for line in text.split('\n'):
#         pdf.multi_cell(0, 10, line)
    
#     pdf.output("tailored_resume.pdf")
