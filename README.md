# QA Agent - Autonomous Test Case & Selenium Script Generator

An intelligent QA agent that generates test cases and Selenium scripts from project documentation.

## Features

- **Document Ingestion**: Upload MD, TXT, JSON, PDF, DOCX, and HTML files
- **Knowledge Base**: Uses ChromaDB vector database with sentence-transformers embeddings
- **Test Case Generation**: RAG pipeline with Groq LLM (LLaMA 3.3 70B)
- **Selenium Script Generation**: Generates executable Python Selenium scripts

## Project Structure
```
qa-agent/
├── backend/
│   ├── __init__.py
│   ├── main.py              # FastAPI application
│   ├── ingestion.py         # Document parsing
│   ├── vector_store.py      # ChromaDB operations
│   ├── test_generator.py    # Test case generation
│   └── script_generator.py  # Selenium script generation
├── frontend/
│   └── app.py               # Streamlit UI
├── documents/               # Support documents
│   ├── product_specs.md
│   ├── ui_ux_guide.txt
│   └── api_endpoints.json
├── target/
│   └── checkout.html        # HTML file to test
├── .env                     # API keys
├── requirements.txt
└── README.md
```

## Setup Instructions

### Prerequisites
- Python 3.9 or higher
- Groq API key (free at https://console.groq.com)

### Installation

1. Clone the repository:
```bash
git clone <your-repo-url>
cd qa-agent
```

2. Create virtual environment:
```bash
python -m venv venv
```

3. Activate virtual environment:
- Windows: `venv\Scripts\activate`
- Mac/Linux: `source venv/bin/activate`

4. Install dependencies:
```bash
pip install -r requirements.txt
```

5. Create `.env` file with your Groq API key:
```
GROQ_API_KEY=your_api_key_here
```

## Running the Application

### Start Backend (Terminal 1):
```bash
uvicorn backend.main:app --reload
```

### Start Frontend (Terminal 2):
```bash
streamlit run frontend/app.py
```

### Access the Application:
Open http://localhost:8501 in your browser.

## Usage

### Phase 1: Upload & Build Knowledge Base
1. Upload support documents (MD, TXT, JSON, PDF)
2. Upload the HTML file to test
3. Click "Build Knowledge Base"

### Phase 2: Generate Test Cases
1. Choose "Custom Query" or "Generate All Test Cases"
2. Click "Generate Test Cases"
3. Select a test case for script generation

### Phase 3: Generate Selenium Scripts
1. View the selected test case
2. Click "Generate Selenium Script"
3. Download the generated script

## Support Documents

### product_specs.md
Contains product rules including:
- Discount codes (SAVE15, WELCOME10, FREESHIP)
- Shipping options (Standard: Free, Express: $10)
- Cart and payment rules

### ui_ux_guide.txt
Contains UI/UX guidelines including:
- Form validation rules
- Button styles and colors
- Error message formatting

### api_endpoints.json
Contains API specifications for:
- Apply coupon endpoint
- Submit order endpoint
- Cart total endpoint

## Technologies Used

- **Backend**: FastAPI, Python
- **Frontend**: Streamlit
- **Vector Database**: ChromaDB
- **Embeddings**: Sentence-Transformers (all-MiniLM-L6-v2)
- **LLM**: Groq (LLaMA 3.3 70B Versatile)
- **Testing**: Selenium WebDriver

## Author

ANKITA TIWARY