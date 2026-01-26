# TransformX AI

<div align="center">

### Intelligent Document Transformation Platform
*Convert between multiple document formats using AI-powered processing*

[![Python](https://img.shields.io/badge/Python-3.9+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.0-000000?style=for-the-badge&logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
[![React](https://img.shields.io/badge/React-18-61DAFB?style=for-the-badge&logo=react&logoColor=black)](https://reactjs.org/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.0-3178C6?style=for-the-badge&logo=typescript&logoColor=white)](https://www.typescriptlang.org/)

[Features](#-features) • [Installation](#-installation--setup) • [Usage](#-usage) • [Architecture](#-architecture) • [Documentation](#-api-endpoints)

</div>

---

## 🎯 Overview

**TransformX AI** is an enterprise-grade document transformation platform designed for technical documentation professionals. Leveraging advanced AI capabilities, it streamlines the complex process of converting technical documentation between industry-standard formats while maintaining structural integrity and semantic accuracy.

### Why TransformX AI?

<table>
<tr>
<td width="33%" align="center">
<h4>🚀 Accelerate Workflows</h4>
Automate tedious conversion tasks that traditionally require hours of manual work
</td>
<td width="33%" align="center">
<h4>🎯 Ensure Accuracy</h4>
AI-powered content enrichment maintains professional output with proper formatting
</td>
<td width="33%" align="center">
<h4>🔒 Maintain Security</h4>
Local processing ensures your sensitive documents never leave your infrastructure
</td>
</tr>
</table>

---

## ✨ Features

<table>
<thead>
<tr>
<th width="30%">Module</th>
<th width="70%">Capabilities</th>
</tr>
</thead>
<tbody>
<tr>
<td><strong>Multi-IP Documentation Generator</strong></td>
<td>
Process multiple IP documents (PDF/DOCX/Excel) simultaneously. Automatically extracts register tables from both structured tables and text content, generates DITA topics and maps, converts images to SVG format, and produces one organized PDF with chapters for each IP. Includes a built-in editor to modify and regenerate PDFs instantly. Download spec_source ZIP separately containing organized specification files.
</td>
</tr>
<tr>
<td><strong>Spec Source → PDF</strong></td>
<td>
Convert spec_source ZIP files (generated from Multi-IP Documentation) directly into formatted PDF documents. Perfect for regenerating documentation from previously processed specification sources.
</td>
</tr>
<tr>
<td><strong>PDF → DITA Map</strong></td>
<td>
Convert PDF documents to DITA format with automatic topic segmentation and intelligent content structuring.
</td>
</tr>
<tr>
<td><strong>DOCX → DITA Map</strong></td>
<td>
Transform Word documents to DITA Map format with automated image-to-SVG conversion and topic organization.
</td>
</tr>
<tr>
<td><strong>.REGS → PDF</strong></td>
<td>
Convert regulatory register files (.regs or .xml) to professionally formatted PDF documentation.
</td>
</tr>
<tr>
<td><strong>PDF/DOCX/Excel → .REGS</strong></td>
<td>
Extract register tables from PDF, Word, or Excel documents and convert them to .regs format for standardized register documentation.
</td>
</tr>
<tr>
<td><strong>Image → SVG</strong></td>
<td>
Convert raster images (PNG, JPG, JPEG) to scalable vector graphics for high-quality, resolution-independent output.
</td>
</tr>
</tbody>
</table>

---

## 🏗️ Architecture

<div align="center">

![System Architecture](https://github.com/AdityaKale22420263/Testing/blob/main/hosting/diagram-export-12-3-2025-2_02_13-AM.png?raw=true)

*Modular architecture designed for scalability and maintainability*

</div>

---

## 📋 Prerequisites

Before beginning the installation, ensure your system meets the following requirements:

### Required Software

| Component | Version | Download Link |
|-----------|---------|---------------|
| **Python** | 3.9 or higher | [Download Python](https://www.python.org/downloads/) |
| **Node.js** | 18.x or higher | [Download Node.js](https://nodejs.org/) |
| **Git** | Latest stable | [Download Git](https://git-scm.com/downloads) |

### API Configuration

<details>
<summary><strong>🔑 Gemini API Key Setup (Required)</strong></summary>

TransformX AI leverages Google's Gemini AI for advanced document processing capabilities.

**Obtaining Your API Key:**

1. Visit [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Sign in with your Google account
3. Click **"Create API Key"**
4. Copy the generated key for configuration in the `.env` file

> **Note:** Keep your API key secure and never commit it to version control.

</details>

---

## 🚀 Installation & Setup

### Option 1: Quick Start with Automated Launcher
**✅ Recommended for Windows Users**

The automated launcher provides a streamlined, one-click installation and startup experience.

#### Quick Start Guide

**1. Clone the Repository**
```bash
git clone https://github.com/Adiverse07/TransformX-AI.git
cd TransformX-AI
```

**2. Configure Environment Variables**

   Before running the launcher, ensure your Gemini API key is configured:
   - Navigate to the `backend` folder
   - If `.env` file doesn't exist
   - Add your Gemini API key to the `.env` file:
     ```env
     GEMINI_API_KEY=your_gemini_api_key_here
     ```

**3. Launch the Application**

Double-click **`RUN_PROJECT.exe`** in the project root directory.

#### What Happens Next?

The launcher automatically handles:

- ✅ System verification (Python & Node.js)
- ✅ Virtual environment creation
- ✅ Dependency installation (first run only)
- ✅ Port management and cleanup
- ✅ Server initialization (Backend: `5000`, Frontend: `8080`)
- ✅ Browser launch

> **⏱️ First Run:** Initial setup takes 3-5 minutes for dependency installation  
> **⏱️ Subsequent Runs:** Application launches in under 30 seconds

#### Application Access

Once launched, the application is accessible at:

- **Frontend Interface:** `http://localhost:8080`
- **Backend API:** `http://localhost:5000`

> **Important:** Keep both console windows open during operation

#### Stopping the Application

To terminate the servers:
- Close both console windows, **OR**
- Press `Ctrl+C` in each console window

---

### Option 2: Manual Installation
**For Advanced Users and Non-Windows Platforms**

<details>
<summary><strong>Click to expand manual installation instructions</strong></summary>

### Step 1: Repository Setup

```bash
git clone https://github.com/Adiverse07/TransformX-AI.git
cd TransformX-AI
```

### Step 2: Backend Configuration

#### 2.1 Navigate to Backend Directory

```bash
cd backend
```

#### 2.2 Create Python Virtual Environment

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

> ✅ Successful activation displays `(venv)` prefix in your terminal

#### 2.3 Install Python Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

#### 2.4 Environment Configuration

Create and configure the `.env` file:

**Windows:**
```bash
copy .env.example .env
```

**macOS/Linux:**
```bash
cp .env.example .env
```

**Required Configuration:**

```env
# Flask Configuration
SECRET_KEY=your-secret-key-here-change-in-production
FLASK_ENV=development
FLASK_DEBUG=True

# Server Configuration
FLASK_HOST=0.0.0.0
FLASK_PORT=5000

# Gemini API Configuration (Required)
GEMINI_API_KEY=your_gemini_api_key_here

# CORS Configuration
CORS_ORIGINS=*

# File Upload Limits
MAX_CONTENT_LENGTH=52428800  # 50MB
UPLOAD_FOLDER=uploads
OUTPUT_FOLDER=outputs
```

> ⚠️ **Security Note:** Update `SECRET_KEY` for production deployments

#### 2.5 Start Backend Server

```bash
python run_server.py
```

✅ **Backend Service:** Running at `http://localhost:5000`

---

### Step 3: Frontend Configuration

Open a new terminal window while keeping the backend server running.

#### 3.1 Navigate to Project Root

```bash
cd TransformX-AI
```

#### 3.2 Install Node.js Dependencies

```bash
npm install
```

#### 3.3 Configure Frontend Environment

Create and configure the frontend `.env` file:

**Windows:**
```bash
copy .env.example .env
```

**macOS/Linux:**
```bash
cp .env.example .env
```

**Configuration:**

```env
VITE_API_URL=http://localhost:5000
```

#### 3.4 Start Frontend Development Server

```bash
npm run dev
```

✅ **Frontend Service:** Running at `http://localhost:8080`

---

### Step 4: Access the Application

Navigate to `http://localhost:8080` in your web browser.

🎉 **Success!** TransformX AI is now running.

</details>

---

## 📖 Usage

### 1. Multi-IP Documentation Generator

**Comprehensive multi-document processing with integrated editing capabilities**

#### Workflow

1. Select **"Multi-IP Documentation Generator"** from the home page
2. Upload multiple IP documents (supported formats: PDF, DOCX, Excel)
3. Automated processing includes:
   - Register table extraction from structured and unstructured content
   - DITA topic and map generation
   - Image-to-SVG conversion
   - Unified PDF generation with chapter organization

4. Utilize the integrated editor for real-time modifications and regeneration
5. Download options:
   - **Combined PDF:** Single document with chapter-based organization
   - **Spec Source ZIP:** Complete specification file structure

#### Output Structure

```
Combined PDF Output:
organized_documentation.pdf
├── Chapter 1: Temp Registers (IP1)
│   ├── Register descriptions
│   ├── Tables and diagrams
│   └── Technical specifications
├── Chapter 2: Control Registers (IP2)
│   ├── Register descriptions
│   └── Technical specifications
└── Chapter N: Additional IPs

Spec Source ZIP (Separate Download):
spec_source.zip
├── IP_1_temp_registers/
│   └── spec_source/
│       ├── topics/
│       ├── media/
│       ├── images/
│       └── registers/
├── IP_2_control_registers/
│   └── spec_source/
│       ├── topics/
│       ├── media/
│       ├── images/
│       └── registers/
└── Additional IP directories...
```

---

### 2. Spec Source → PDF Conversion

**Regenerate PDFs from previously processed specification sources**

1. Select **"Spec Source → PDF"** module
2. Upload spec_source ZIP file (from Multi-IP Documentation Generator)
3. Click **"Generate PDF"**
4. Download the formatted PDF document

---

### 3. PDF/DOCX to DITA Map Conversion

#### Process Flow

1. Select **"PDF → DITA Map"** or **"DocX → DITA Map"** module
2. Upload source document (maximum file size: 50MB)
3. Optionally specify document title
4. Click **"Convert to DITA"**
5. Monitor conversion progress via progress indicator
6. Download generated DITA package (ZIP archive)

#### Output Structure

```
dita_output/
├── topics/
│   ├── topic1.dita
│   ├── topic2.dita
│   └── additional_topics.dita
├── media/
│   ├── image1.svg
│   ├── image2.svg
│   └── additional_images.svg
└── document.ditamap
```

---

### 4. .REGS to PDF Conversion

1. Select **".REGS → PDF"** module
2. Upload .regs or .xml file
3. Click **"Convert to PDF"**
4. Download professionally formatted register documentation

---

### 5. PDF/DOCX/Excel → .REGS Conversion

**Automated register table extraction and standardization**

1. Select **"Any to .REGS"** module
2. Upload source document containing register tables
3. Automated detection and extraction of register information
4. Click **"Convert to .REGS"**
5. Download standardized .regs file

---

### 6. Image to SVG Conversion

1. Select **"Image → SVG"** module
2. Upload raster image (PNG, JPG, JPEG)
3. Click **"Convert to SVG"**
4. Download scalable vector graphic

---

### 7. Conversion History Management

1. Navigate to **"Upload History"** in the main menu
2. Review all past conversions with detailed metadata
3. Re-download previous conversion outputs as needed

---

## 📁 Project Structure

```
TransformX-AI/
│
├── backend/                           # Flask Backend Service
│   ├── extractors/                    # Document Content Extraction
│   │   ├── docx_extractor.py         # DOCX parsing engine
│   │   ├── pdf_extractor.py          # PDF extraction utilities
│   │   ├── regs_base_extractor.py    # Base register extraction class
│   │   ├── regs_excel_extractor.py   # Excel register extraction
│   │   ├── regs_pdf_extractor.py     # PDF register extraction
│   │   └── regs_word_extractor.py    # Word register extraction
│   │
│   ├── pipeline/                      # AI Processing Pipeline
│   │   ├── segmenter.py              # Content segmentation
│   │   └── enrich.py                 # AI-powered enrichment
│   │
│   ├── routes/                        # API Route Handlers
│   │   ├── conversion.py             # DITA conversion endpoints
│   │   ├── regs_conversion.py        # Register conversion endpoints
│   │   ├── image_conversion.py       # Image conversion endpoints
│   │   ├── spec_source_editor.py     # Spec source editing
│   │   ├── spec_to_pdf_conversion.py # Spec to PDF conversion
│   │   ├── multi_ip_conversion.py    # Multi-IP documentation
│   │   ├── any_to_regs_conversion.py # Multi-format register conversion
│   │   └── history.py                # History management
│   │
│   ├── services/                      # Business Logic Layer
│   │   ├── dita_converter.py         # DITA conversion service
│   │   ├── regs_pdf_converter.py     # REGS to PDF service
│   │   ├── image_to_svg_converter.py # Image conversion service
│   │   ├── multi_ip_converter.py     # Multi-IP processing
│   │   └── any_to_regs_converter.py  # Multi-format conversion
│   │
│   ├── utils/                         # Utility Functions
│   │   ├── gemini_client.py          # Gemini AI integration
│   │   ├── gemini_processor.py       # AI processing utilities
│   │   ├── gemini_rate_limiter.py    # API rate limiting
│   │   ├── regs_table_detector.py    # Register table detection
│   │   ├── xml_generator.py          # XML/DITA generation
│   │   └── helpers.py                # General utilities
│   │
│   ├── writers/                       # Output Generation
│   │   ├── dita_writer.py            # DITA XML generation
│   │   └── pdf_writer.py             # PDF document generation
│   │
│   ├── uploads/                       # Temporary file storage
│   ├── outputs/                       # Generated outputs
│   ├── spec_outputs/                  # Spec source outputs
│   ├── venv/                          # Python virtual environment
│   │
│   ├── app.py                         # Flask application core
│   ├── config.py                      # Configuration management
│   ├── run_server.py                  # Server initialization
│   ├── requirements.txt               # Python dependencies
│   └── .env                           # Environment configuration
│
├── src/                               # React Frontend Application
│   ├── components/                    # Reusable UI Components
│   │   ├── layout/                    # Layout Components
│   │   │   ├── AppSidebar.tsx        # Navigation sidebar
│   │   │   ├── Layout.tsx            # Main layout wrapper
│   │   │   └── TopNav.tsx            # Top navigation bar
│   │   │
│   │   └── ui/                        # UI Components
│   │       ├── FileUpload.tsx        # File upload interface
│   │       ├── LogViewer.tsx         # Log viewing component
│   │       ├── ModuleCard.tsx        # Feature module cards
│   │       ├── SpecSourceEditor.tsx  # Spec source editor
│   │       └── ThemeToggle.tsx       # Theme switcher
│   │
│   ├── pages/                         # Application Pages
│   │   ├── modules/                   # Feature Modules
│   │   │   ├── DocxToDita.tsx        # DOCX to DITA module
│   │   │   ├── PdfToDita.tsx         # PDF to DITA module
│   │   │   ├── RegsToPdf.tsx         # REGS to PDF module
│   │   │   ├── ImageToSvg.tsx        # Image to SVG module
│   │   │   ├── SpecToPdf.tsx         # Spec to PDF module
│   │   │   ├── MultiIpDocGen.tsx     # Multi-IP documentation
│   │   │   └── AnyToRegs.tsx         # Multi-format conversion
│   │   │
│   │   ├── Home.tsx                   # Home page
│   │   ├── History.tsx                # Conversion history
│   │   ├── About.tsx                  # About page
│   │   ├── Settings.tsx               # Settings page
│   │   ├── Index.tsx                  # Landing page
│   │   └── NotFound.tsx               # 404 error page
│   │
│   ├── hooks/                         # Custom React hooks
│   ├── lib/                           # Utility libraries
│   ├── App.tsx                        # Main React application
│   ├── main.tsx                       # Application entry point
│   └── index.css                      # Global styles
│
├── public/                            # Static assets
├── node_modules/                      # Node.js dependencies
│
├── .gitignore                         # Git ignore patterns
├── package.json                       # Node.js configuration
├── package-lock.json                  # Dependency lock file
├── tsconfig.json                      # TypeScript configuration
├── vite.config.ts                     # Vite build configuration
├── tailwind.config.ts                 # Tailwind CSS configuration
├── postcss.config.js                  # PostCSS configuration
│
├── RUN_PROJECT.exe                    # Automated launcher (Windows)
└── README.md                          # Project documentation
```

---

## 🔌 API Endpoints

### Multi-IP Conversion Service
| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/multi-ip/convert` | Process multiple IP documents |
| `GET` | `/api/multi-ip/download/<session_id>` | Download generated files |
| `POST` | `/api/multi-ip/edit` | Edit and regenerate PDFs |

### Spec Source Conversion Service
| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/spec-to-pdf/convert` | Convert spec source to PDF |
| `GET` | `/api/spec-to-pdf/download/<filename>` | Download PDF output |

### DITA Conversion Service
| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/convert` | Convert PDF/DOCX to DITA |
| `GET` | `/api/convert/download/<session_id>` | Download DITA package |
| `DELETE` | `/api/convert/cleanup/<session_id>` | Clean up session files |

### REGS Conversion Service
| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/regs/convert` | Convert .regs to PDF |
| `GET` | `/api/regs/download/<filename>` | Download PDF output |
| `POST` | `/api/any-to-regs/convert` | Convert any format to .regs |
| `GET` | `/api/any-to-regs/download/<filename>` | Download .regs file |

### Image Conversion Service
| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/convert/image-to-svg` | Convert image to SVG |
| `GET` | `/api/convert/image-to-svg/download/<filename>` | Download SVG output |

### History Management Service
| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/history` | Retrieve conversion history |
| `POST` | `/api/history` | Add history entry |
| `DELETE` | `/api/history/<id>` | Delete history entry |

---

## ⚠️ Troubleshooting

<details>
<summary><strong>Module Not Found Errors</strong></summary>

Ensure all dependencies are properly installed:

**Backend:**
```bash
cd backend
pip install -r requirements.txt
```

**Frontend:**
```bash
cd ..
npm install
```

</details>

<details>
<summary><strong>CORS Configuration Issues</strong></summary>

Update CORS settings in `backend/app.py`:

```python
CORS(app, resources={
    r"/api/*": {
        "origins": "*",
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
})
```

Restart the backend server after configuration changes.

</details>

<details>
<summary><strong>Launcher Execution Issues</strong></summary>

**Troubleshooting Steps:**

1. Verify Python 3.9+ and Node.js 18+ are installed and added to system PATH
2. Execute Command Prompt with Administrator privileges
3. Navigate to project directory
4. Re-run `RUN_PROJECT.exe`
5. Review console output for specific error messages

</details>

<details>
<summary><strong>Port Conflict Resolution</strong></summary>

The launcher automatically manages ports 5000 and 8080. For manual resolution:

**Windows:**
```bash
# Identify and terminate process on port 5000
netstat -ano | findstr :5000
taskkill /PID <PID> /F

# Identify and terminate process on port 8080
netstat -ano | findstr :8080
taskkill /PID <PID> /F
```

**macOS/Linux:**
```bash
# Terminate process on port 5000
lsof -ti:5000 | xargs kill -9

# Terminate process on port 8080
lsof -ti:8080 | xargs kill -9
```

</details>

<details>
<summary><strong>Gemini API Connectivity Issues</strong></summary>

**Resolution Steps:**

1. Verify API key configuration in `backend/.env`
2. Confirm API quota availability at [Google AI Studio](https://makersuite.google.com/)
3. Ensure stable internet connectivity

</details>

---

## 🛠️ Technology Stack

### Backend Infrastructure

<div align="center">

![Python](https://skillicons.dev/icons?i=python)
![Flask](https://skillicons.dev/icons?i=flask)

</div>

**Core Dependencies:**
- **Flask 3.0** - Web application framework
- **Python-docx** - DOCX document processing
- **PyMuPDF** - PDF manipulation and extraction
- **OpenPyXL** - Excel file processing
- **lxml** - XML/DITA generation
- **ReportLab** - PDF document generation
- **Google Generative AI** - AI-powered content enhancement
- **OpenCV** - Advanced image processing
- **Pillow** - Image manipulation utilities

### Frontend Infrastructure

<div align="center">

![React](https://skillicons.dev/icons?i=react)
![TypeScript](https://skillicons.dev/icons?i=typescript)
![Vite](https://skillicons.dev/icons?i=vite)
![TailwindCSS](https://skillicons.dev/icons?i=tailwind)

</div>

**Core Dependencies:**
- **React 18** - Component-based UI framework
- **TypeScript** - Static type checking
- **Vite** - Next-generation build tool
- **Tailwind CSS** - Utility-first CSS framework
- **React Router** - Client-side routing
- **Shadcn/ui** - High-quality UI components

---

## 💻 System Requirements

### Minimum Requirements

| Component | Specification |
|-----------|--------------|
| **Operating System** | Windows 10, macOS 10.15+, or Linux (Ubuntu 20.04+) |
| **RAM** | 4GB |
| **Storage** | 1GB available space |
| **Python** | 3.9 or higher |
| **Node.js** | 18.x or higher |
| **Internet** | Required for AI features |

### Recommended Configuration

| Component | Specification |
|-----------|--------------|
| **Operating System** | Windows 11 or latest macOS/Linux distribution |
| **RAM** | 8GB or higher |
| **Storage** | 2GB available space |
| **Processor** | Multi-core processor (4+ cores recommended) |
| **Internet** | Stable broadband connection (10+ Mbps) |

---

## 📝 Platform Overview

**TransformX AI** is an enterprise-grade intelligent document transformation platform engineered to streamline complex technical documentation workflows. Designed for technical writers, documentation specialists, and engineering teams, TransformX AI delivers:

### Core Capabilities

- **Batch Processing Architecture:** Handle multiple IP documentation files simultaneously through the Multi-IP Documentation Generator
- **Real-Time Editing Interface:** Integrated editor enables instant content modification and PDF regeneration without re-uploading source materials
- **Multi-Format Support:** Seamless conversion between industry-standard formats including DITA, PDF, DOCX, .REGS, and SVG
- **Intelligent Register Extraction:** Advanced AI-powered detection and extraction of register tables from diverse document structures
- **Quality Assurance:** AI-enhanced content enrichment ensures professional output with consistent formatting and semantic structure
- **Workflow Optimization:** Automate labor-intensive conversion tasks, reducing manual processing time from hours to minutes

### Ideal Use Cases

- Semiconductor and hardware documentation teams
- Technical register specification management
- IP documentation consolidation and standardization
- Cross-format documentation migration projects

---

## 🎯 Key Advantages

<table>
<tr>
<td width="50%">

### Technical Excellence
- **🚀 Zero-Configuration Setup:** Automated launcher eliminates technical complexity
- **🤖 AI-Powered Intelligence:** Google Gemini AI integration for advanced content processing
- **📦 Enterprise Batch Processing:** Multi-document conversion with unified output generation
- **✏️ Integrated Editing Suite:** Modify and regenerate without workflow disruption

</td>
<td width="50%">

### Operational Benefits
- **🔄 Comprehensive Format Support:** PDF, DOCX, Excel, DITA, .REGS, SVG, and more
- **📊 Intelligent Detection:** Automated register table extraction from structured and unstructured content
- **💾 Audit Trail:** Complete conversion history with re-download capabilities
- **🎨 Modern User Experience:** Intuitive interface with dark mode support

</td>
</tr>
<tr>
<td colspan="2" align="center">

### Security & Privacy
**🔒 Local Processing Architecture:** All document processing occurs on your infrastructure - zero cloud upload requirement

</td>
</tr>
</table>

---

## 🤝 Contributing

We welcome contributions from the community. Please submit Pull Requests following our contribution guidelines.

---

## 📄 License

This project is proprietary software. All rights reserved.

---

## 🆘 Support & Resources

### Getting Help

- 🐛 **Bug Reports:** [Submit an Issue](https://github.com/Adiverse07/TransformX-AI/issues)
- 💡 **Feature Requests:** [Request a Feature](https://github.com/Adiverse07/TransformX-AI/issues)
- 📧 **Direct Support:** toBeUpdated

---

<div align="center">

### Project Links

**[⭐ Star Repository](https://github.com/Adiverse07/TransformX-AI)** • **[🐛 Report Issues](https://github.com/Adiverse07/TransformX-AI/issues)** • **[💡 Feature Requests](https://github.com/Adiverse07/TransformX-AI/issues)**

---

*Developed with precision by the TransformX AI Team*

**© 2025 TransformX AI. All rights reserved.**

</div>
