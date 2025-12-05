# RFP Management System

An intelligent Request for Proposal (RFP) management system that automates vendor proposal processing using AI-powered extraction and provides smart vendor recommendations.

##  Features

- **Natural Language RFP Creation**: Create RFPs using plain English descriptions
- **Email-Based Proposal Collection**: Automatically fetch and process vendor proposals from Gmail
- **AI-Powered Extraction**: Extract pricing, payment terms, and warranty information using Google Gemini
- **Vendor Comparison**: Side-by-side comparison of all vendor proposals
- **AI Recommendations**: Get intelligent vendor selection recommendations based on price, terms, and warranty
- **RESTful API**: Complete Django REST Framework API for all operations

##  Tech Stack

### Backend

- **Django 4.2.7**: Python web framework for building the REST API
- **Django REST Framework**: Toolkit for building Web APIs
- **SQLite**: Lightweight database for development
- **Google Gemini API**: AI model for proposal extraction and vendor recommendations
- **IMAP**: Email fetching from Gmail

### Frontend

- **React 18.2.0**: JavaScript library for building user interfaces
- **React Router**: Client-side routing
- **CSS3**: Custom styling with animations and gradients

### AI Integration

- **Google Generative AI (Gemini)**:
  - Model: `gemini-2.5-flash`
  - Used for natural language RFP extraction
  - Automated proposal data extraction from emails
  - Intelligent vendor recommendation analysis

##  Prerequisites

- Python 3.8 or higher
- Node.js 14 or higher
- npm or yarn
- Gmail account (for email integration)
- Google Gemini API key

##  Project Setup

### 1. Clone the Repository

```bash
git clone <repository-url>
cd rfp-system
```

### 2. Backend Setup

#### Install Python Dependencies

```bash
cd backend
pip install -r requirements.txt
```

#### Configure Environment Variables

Create a `.env` file in the `backend` directory:

```env
# Gemini API Configuration
GEMINI_API_KEY=your_gemini_api_key_here

# Django Settings
DEBUG=True
SECRET_KEY=your_secret_key_here
ALLOWED_HOSTS=localhost,127.0.0.1

# Email Configuration (Gmail)
EMAIL_HOST=imap.gmail.com
EMAIL_HOST_USER=your_email@gmail.com
EMAIL_HOST_PASSWORD=your_app_password_here
```

#### Run Database Migrations

```bash
python manage.py migrate
```

### 3. Frontend Setup

#### Install Node Dependencies

```bash
cd ../frontend
npm install
```

##  Running the Application

### Start Backend Server

```bash
cd backend
python manage.py runserver
```

The Django server will start at: **http://localhost:8000**

### Start Frontend Development Server

Open a new terminal:

```bash
cd frontend
npm start
```

The React app will start at: **http://localhost:3000**

##  Project Structure

```
rfp-system/
├── backend/
│   ├── backend/              # Django project settings
│   │   ├── settings.py
│   │   ├── urls.py
│   │   └── wsgi.py
│   ├── rfp/                  # Main Django app
│   │   ├── models.py         # RFP, Vendor, Proposal models
│   │   ├── views.py          # API endpoints
│   │   ├── serializers.py    # DRF serializers
│   │   ├── urls.py           # API routes
│   │   ├── utils.py          # AI extraction utilities
│   │   └── management/
│   │       └── commands/
│   │           ├── fetch_emails.py    # Email fetcher
│   │           └── seed_data.py       # Database seeder
│   ├── manage.py
│   ├── requirements.txt
│   └── .env
│
└── frontend/
    ├── src/
    │   ├── components/
    │   │   ├── ComparisonTable.js    # Vendor comparison UI
    │   │   ├── ComparisonTable.css
    │   │   ├── CreateRFP.js          # RFP creation form
    │   │   ├── CreateRFP.css
    │   │   ├── RFPDetail.js          # RFP details view
    │   │   └── RFPDetail.css
    │   ├── App.js
    │   └── index.js
    ├── package.json
    └── public/
```

##  API Endpoints

### RFPs

- `GET /api/rfp/rfps/` - List all RFPs
- `POST /api/rfp/rfps/` - Create new RFP
- `GET /api/rfp/rfps/{id}/` - Get RFP details
- `POST /api/rfp/rfps/{id}/send-rfp-emails/` - Send RFP to vendors

### Vendors

- `GET /api/rfp/vendors/` - List all vendors
- `POST /api/rfp/vendors/` - Create new vendor
- `GET /api/rfp/vendors/{id}/` - Get vendor details

### Proposals & Analysis

- `GET /api/rfp/comparison/{id}/` - Get RFP with all proposals for comparison
- `POST /api/rfp/ai-recommendation/{id}/` - Get AI recommendation for vendor selection

### RFP Creation

- `POST /api/rfp/create-from-text/` - Create RFP from natural language

##  Email Integration

### Fetch Vendor Proposals from Email

```bash
python manage.py fetch_emails
```

**Options:**

- `--create-proposals`: Automatically create proposals from emails (default: False)

The system will:

1. Connect to Gmail via IMAP
2. Search for emails with "RFP" in the subject
3. Extract proposal data using Gemini AI
4. Match vendors by email address
5. Create proposal records in the database

##  Usage Workflow

### 1. Create an RFP

- Navigate to the Create RFP page
- Enter natural language description of your requirements
- The system uses Gemini AI to extract structured data
- Review and submit the RFP

### 2. Send to Vendors

- Select vendors from the list
- Send RFP invitation emails
- Vendors receive detailed RFP information

### 3. Receive Proposals

- Vendors reply via email with their proposals
- Run `python manage.py fetch_emails --create-proposals`
- System automatically extracts and stores proposal data

### 4. Compare & Analyze

- View all proposals in a comparison table
- Lowest price is highlighted in green
- Click "Ask AI for Recommendation"
- Gemini analyzes all proposals and provides expert recommendation

``

##  Acknowledgments

- Google Gemini AI for intelligent text processing
- Django REST Framework community
- React development community
