import os
import subprocess
from pathlib import Path

CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
if not os.path.exists(CHROME):
    CHROME = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"

def build_pdf():
    project_root = Path(__file__).resolve().parent.parent
    html_path = project_root / "docs" / "interview_guide.html"
    out_pdf_docs = project_root / "docs" / "FinPilot_AI_Complete_Interview_Master_Guide.pdf"
    
    static_docs = project_root / "src" / "app" / "static" / "docs"
    static_docs.mkdir(parents=True, exist_ok=True)
    out_pdf_static = static_docs / "FinPilot_AI_Complete_Interview_Master_Guide.pdf"

    cmd = [
        CHROME,
        "--headless=new",
        "--disable-gpu",
        "--no-pdf-header-footer",
        f"--print-to-pdf={out_pdf_docs}",
        html_path.as_uri()
    ]
    print("Compiling PDF Guide via Chrome Headless...")
    res = subprocess.run(cmd, capture_output=True, timeout=15)
    print("Return code:", res.returncode)
    
    if out_pdf_docs.exists():
        size = out_pdf_docs.stat().st_size
        print(f"[SUCCESS] PDF generated at: {out_pdf_docs} ({size:,} bytes)")
        
        # Copy to static docs for web serving
        with open(out_pdf_docs, "rb") as f_in, open(out_pdf_static, "wb") as f_out:
            f_out.write(f_in.read())
        print(f"[SUCCESS] PDF served statically at: {out_pdf_static}")
    else:
        print("[ERROR] PDF generation failed:", res.stderr.decode('utf-8', errors='ignore'))

if __name__ == "__main__":
    build_pdf()
