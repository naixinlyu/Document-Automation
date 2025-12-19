# Document Automation System (Passport + G-28 → Auto-Fill Web Form)

A local web app that lets you upload a passport and a G-28 form (PDF/JPG/PNG), automatically extracts structured fields, and uses browser automation to populate the test form:

https://mendrika-alma.github.io/form-submission/

Per assignment requirement: this project does NOT submit the form and does NOT digitally sign it.

---

## What it does

1) Upload Passport + G-28 (PDF / JPEG / PNG)  
2) Extract key fields using **Google Gemini** (LLM-based document understanding)  
3) Open the provided web form and fill fields using **Selenium (Chrome)**  
4) Save a screenshot to `uploads/form_filled.png`

---

## Tech stack

- Backend: FastAPI (`main.py`)
- Extraction: Google Gemini via `google-generativeai` (`document_processor.py`)
- PDF → image: `pdf2image` (requires Poppler)
- Form automation: Selenium + Chrome + `webdriver-manager` (`form_filler.py`)
- Frontend: `static/index.html` served by FastAPI (UI for uploads + actions)

---

## Requirements

- Python 3.9+
- Google Gemini API Key
- Google Chrome installed
- Poppler (only needed when uploading PDFs)

### Install Poppler

**macOS (Homebrew)**
```bash
brew install poppler
```

**Ubuntu/Debian**
```bash
sudo apt-get update && sudo apt-get install -y poppler-utils
```

**Windows**
Install Poppler and add Poppler's `bin/` folder to your PATH (common approach: download a Windows Poppler build and set PATH).

---

## Quick start

### 1) Create venv (recommended)
```bash
python -m venv venv
# macOS / Linux:
source venv/bin/activate
# Windows:
venv\Scripts\activate
```

### 2) Install dependencies
```bash
pip install -r requirements.txt
```

### 3) Ensure folders exist
```bash
mkdir -p uploads static
# keep uploads tracked even though uploads/* is gitignored
# create an empty file:
#   uploads/.gitkeep
```

### 4) Run the server
```bash
python main.py
```

Open:
- http://localhost:8000

---

## Usage

1) Open http://localhost:8000  
2) Enter your **Gemini API key** in the UI 
3) Upload Passport  
4) Upload G-28  
5) Click **Fill Form** to run Selenium automation  
6) Check `uploads/form_filled.png`

Sample file included:
- `Example_G-28.pdf`

---

## Demo (screen recording)

- `demo/screen recording.mp4`

---

## Notes / Tips

- PDF uploads are converted using `pdf2image` (Poppler required).
- Selenium runs in **headless** mode by default.  
  If you want a visible browser window for recording, remove/comment the `--headless=new` option in `form_filler.py`.

---

## Project structure

```
.
├── main.py
├── document_processor.py
├── form_filler.py
├── requirements.txt
├── Example_G-28.pdf
├── static/
│   └── index.html
├── demo/
│   └── screen recording.mp4
└── uploads/
    └── .gitkeep
```

---

## Security

- Do not commit API keys.
- `.env` is gitignored by default if you choose to use it.

---

## License

MIT
