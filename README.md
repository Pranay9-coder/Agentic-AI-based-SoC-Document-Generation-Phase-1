# TransformX AI

> A comprehensive document transformation platform that converts between multiple document formats using AI-powered processing.

[![Python](https://img.shields.io/badge/Python-3.9+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.0-000000?style=for-the-badge&logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
[![React](https://img.shields.io/badge/React-18-61DAFB?style=for-the-badge&logo=react&logoColor=black)](https://reactjs.org/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.0-3178C6?style=for-the-badge&logo=typescript&logoColor=white)](https://www.typescriptlang.org/)

## ✨ Features

| Module | Description |
|--------|-------------|
| **PDF → DITA Map** | Convert PDF documents to DITA format with automatic topic segmentation |
| **DOCX → DITA Map** | Transform Word documents to DITA Map format with image-to-SVG conversion |
| **.REGS → PDF** | Convert regulatory register files to formatted PDF documentation |
| **Image → SVG** | Convert raster images to scalable vector graphics |

## 🏗️ Architecture

![archdiag](https://github.com/AdityaKale22420263/Testing/blob/main/hosting/diagram-export-12-3-2025-2_02_13-AM.png?raw=true)

---

## 📋 Prerequisites

Ensure you have the following installed on your system:

- **Python 3.9+** → [Download](https://www.python.org/downloads/)
- **Node.js 18.x+** → [Download](https://nodejs.org/)
- **Git** → [Download](https://git-scm.com/downloads)

### Optional

- **Gemini API Key** (for AI-powered features) → [Get API Key](https://makersuite.google.com/app/apikey)

---

## 🚀 Installation & Setup

### Step 1: Clone the Repository

```bash
git clone https://github.com/Adiverse07/TransformX-AI.git
cd TransformX-AI
```

### Step 2: Backend Setup

#### 2.1 Navigate to Backend Directory

```bash
cd backend
```

#### 2.2 Create Virtual Environment

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

**macOS/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

> ✅ You should see `(venv)` prefix in your terminal

#### 2.3 Install Python Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

#### 2.4 Configure Environment Variables

Create a `.env` file in the `backend` directory:

```bash
# Windows
copy .env.example .env

# macOS/Linux
cp .env.example .env
```

Edit the `.env` file with your configuration:

```env
# Flask Configuration
SECRET_KEY=your-secret-key-here-change-in-production
FLASK_ENV=development
FLASK_DEBUG=True

# Server Configuration
FLASK_HOST=0.0.0.0
FLASK_PORT=5000

# Optional: Gemini API Key (for AI features)
GEMINI_API_KEY=your_gemini_api_key_here

# CORS Origins - IMPORTANT: Set to "*" to allow all origins
CORS_ORIGINS=*

# File Upload Configuration
MAX_CONTENT_LENGTH=52428800  # 50MB in bytes
UPLOAD_FOLDER=uploads
OUTPUT_FOLDER=outputs
```

> ⚠️ **Important:** Set `CORS_ORIGINS=*` to avoid CORS issues

#### 2.5 Start the Backend Server

```bash
python app.py
```

✅ Backend is now running at `http://localhost:5000`

Keep this terminal window open.

---

### Step 3: Frontend Setup

Open a **new terminal window** (keep backend running).

#### 3.1 Navigate to Project Root

```bash
cd TransformX-AI
```

#### 3.2 Install Node.js Dependencies

```bash
npm install
```

This will install all required packages from `package.json`.

#### 3.3 Configure Frontend Environment

Create a `.env` file in the project root:

```bash
# Windows
copy .env.example .env

# macOS/Linux
cp .env.example .env
```

Edit the `.env` file:

```env
VITE_API_URL=http://localhost:5000
```

#### 3.4 Start the Frontend Development Server

```bash
npm run dev
```

✅ Frontend is now running at `http://localhost:5173`

---

### Step 4: Access the Application

Open your browser and navigate to:

```
http://localhost:5173
```

You should see the TransformX AI homepage! 🎉

---

## 📖 Usage

### 1. PDF/DOCX to DITA Map

1. Click on "PDF → DITA Map" or "DocX → DITA Map" card
2. Upload your PDF or DOCX file (max 50MB)
3. Optionally enter a document title
4. Click "Convert to DITA"
5. Wait for processing (progress indicator will show)
6. Download the generated DITA package (ZIP file containing topics, media, and DITAMAP)

**Output Structure:**
```
output/
├── topics/
│   ├── topic1.dita
│   ├── topic2.dita
│   └── ...
├── media/
│   ├── image1.png
│   ├── image2.png
│   └── ...
└── document.ditamap
```

### 2. .REGS to PDF

1. Click on ".REGS → PDF" card
2. Upload your .regs or .xml file
3. Click "Convert to PDF"
4. Download the generated PDF with register documentation

### 3. Image to SVG

1. Click on "Image → SVG" card
2. Upload a raster image (PNG, JPG, JPEG)
3. Click "Convert to SVG"
4. Download the scalable vector graphic

### 4. View Conversion History

1. Click on "Upload History" in the navigation menu
2. View all past conversions with details
3. Re-download previous conversions

## 📁 Project Structure

```
TransformX-AI/
│
├── backend/                      # Python Flask backend
│   ├── extractors/              # Document content extractors
│   │   ├── docx_extractor.py   # DOCX parsing
│   │   └── pdf_extractor.py    # PDF parsing
│   │
│   ├── pipeline/                # Processing pipeline
│   │   ├── segmenter.py        # Content segmentation
│   │   └── enrich.py           # AI enrichment
│   │
│   ├── writers/                 # Output generators
│   │   ├── dita_writer.py      # DITA XML generation
│   │   └── pdf_writer.py       # PDF generation
│   │
│   ├── services/                # Business logic layer
│   │   ├── dita_converter.py
│   │   ├── regs_pdf_converter.py
│   │   └── image_to_svg_converter.py
│   │
│   ├── routes/                  # API endpoints
│   │   ├── conversion.py
│   │   ├── regs_conversion.py
│   │   ├── image_conversion.py
│   │   └── history.py
│   │
│   ├── utils/                   # Helper utilities
│   │   ├── gemini_client.py
│   │   └── helpers.py
│   │
│   ├── uploads/                 # Temporary uploads
│   ├── outputs/                 # Generated files
│   ├── app.py                   # Flask application
│   ├── requirements.txt         # Python dependencies
│   └── .env                     # Environment configuration
│
└── src/                          # React TypeScript frontend
    ├── modules/                 # Feature modules
    │   ├── DocxToDita.tsx
    │   ├── PdfToDita.tsx
    │   ├── RegsToPdf.tsx
    │   └── ImageToSvg.tsx
    │
    ├── pages/                   # Route pages
    │   ├── Home.tsx
    │   ├── History.tsx
    │   └── About.tsx
    │
    ├── lib/                     # Utilities
    ├── App.tsx                  # Main app component
    └── main.tsx                 # Entry point
```

---

## 🔌 API Endpoints

### DITA Conversion
- `POST /api/convert` - Convert PDF/DOCX to DITA
- `GET /api/convert/download/<session_id>` - Download DITA package
- `DELETE /api/convert/cleanup/<session_id>` - Clean up session files

### REGS Conversion
- `POST /api/regs/convert` - Convert .regs to PDF
- `GET /api/regs/download/<filename>` - Download PDF

### Image Conversion
- `POST /api/convert/image-to-svg` - Convert image to SVG
- `GET /api/convert/image-to-svg/download/<filename>` - Download SVG

### History
- `GET /api/history` - Get conversion history
- `POST /api/history` - Add to history
- `DELETE /api/history/<id>` - Delete history entry

---

## ⚠️ Troubleshooting

### Issue: Module not found errors

**Solution:** Ensure you've installed all dependencies:

```bash
# Backend
cd backend
pip install -r requirements.txt

# Frontend
cd ..
npm install
```

### Issue: CORS errors when making API requests

**Solution:** Update CORS configuration in `backend/app.py`:

```python
# Configure CORS
CORS(app, resources={
    r"/api/*": {
        "origins": "*",  # Change this line to allow all origins
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
})
```

Restart the backend server after making changes.

---

## 🛠️ Technologies Used

### Backend
![Python](https://skillicons.dev/icons?i=python)
![Flask](https://skillicons.dev/icons?i=flask)

**Core Libraries:**
- Flask 3.0 - Web framework
- Python-docx - DOCX processing
- PyMuPDF - PDF processing
- lxml - XML/DITA generation
- ReportLab - PDF generation
- Google Generative AI - AI-powered enhancements
- OpenCV - Image processing

### Frontend
![React](https://skillicons.dev/icons?i=react)
![TypeScript](https://skillicons.dev/icons?i=typescript)
![Vite](https://skillicons.dev/icons?i=vite)
![TailwindCSS](https://skillicons.dev/icons?i=tailwind)

**Core Libraries:**
- React 18 - UI framework
- TypeScript - Type safety
- Vite - Build tool
- Tailwind CSS - Styling
- React Router - Navigation

---

## 💻 System Requirements

### Minimum
- **OS**: Windows 10, macOS 10.15+, or Linux (Ubuntu 20.04+)
- **RAM**: 4GB
- **Storage**: 500MB free space
- **Python**: 3.9+
- **Node.js**: 18.x+

### Recommended
- **RAM**: 8GB or more
- **Storage**: 2GB free space
- **CPU**: Multi-core processor for faster conversions

---

[⭐ Star this repo](https://github.com/Adiverse07/TransformX-AI) • [🐛 Report Bug](https://github.com/Adiverse07/TransformX-AI/issues) • [💡 Request Feature](https://github.com/Adiverse07/TransformX-AI/issues)

</div>