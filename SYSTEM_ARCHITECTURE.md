# RFP Management System - Complete Architecture Walkthrough

## 📚 Table of Contents

1. [Frontend Entry Point](#1-frontend-entry-point)
2. [Data Flow - RFP Creation](#2-data-flow---rfp-creation)
3. [Backend Processing](#3-backend-processing)
4. [Background Task - Email Parsing](#4-background-task---email-parsing)
5. [Final Output - Comparison View](#5-final-output---comparison-view)
6. [Complete Flow Diagram](#6-complete-flow-diagram)

---

## 1. Frontend Entry Point

### 🚀 How the React App Initializes

#### **File: `frontend/src/index.js`**

This is the **absolute starting point** of your React application.

```javascript
import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App";

const root = ReactDOM.createRoot(document.getElementById("root"));
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
```

**What happens:**

1. React finds the `<div id="root">` element in `public/index.html`
2. Creates a React root and renders the `<App />` component
3. `<React.StrictMode>` enables additional development checks

---

#### **File: `frontend/src/App.js`**

The main application component that sets up routing.

```javascript
import { BrowserRouter, Routes, Route } from "react-router-dom";
import CreateRFP from "./components/CreateRFP";
import RFPDetail from "./components/RFPDetail";
import ComparisonTable from "./components/ComparisonTable";

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<CreateRFP />} />
        <Route path="/rfp/:id" element={<RFPDetail />} />
        <Route path="/comparison/:id" element={<ComparisonTable />} />
      </Routes>
    </BrowserRouter>
  );
}
```

**Routing Structure:**

- **`/`** → CreateRFP component (landing page)
- **`/rfp/:id`** → RFPDetail component (shows a single RFP)
- **`/comparison/:id`** → ComparisonTable component (compare vendor proposals)

**Navigation Flow:**

1. User visits `http://localhost:3000/`
2. `BrowserRouter` takes control of URL navigation
3. `Routes` matches the current path
4. For `/`, it renders `<CreateRFP />` component

---

## 2. Data Flow - RFP Creation

### 📝 User Journey: Creating an RFP

#### **File: `frontend/src/components/CreateRFP.js`**

Let's trace what happens when a user creates an RFP:

```javascript
const [text, setText] = useState("");
const [loading, setLoading] = useState(false);
const navigate = useNavigate();
```

**Step 1: User Types in Textarea**

```javascript
<textarea
  value={text}
  onChange={(e) => setText(e.target.value)}
  placeholder="Example: We need 50 laptops with 16GB RAM..."
/>
```

- User types: "We need 50 laptops with 16GB RAM and 512GB SSD. Budget is $75,000."
- `onChange` updates the `text` state variable

---

**Step 2: User Clicks "Generate RFP" Button**

```javascript
<button type="submit" onClick={handleSubmit}>
  Generate RFP
</button>
```

This triggers the `handleSubmit` function:

```javascript
const handleSubmit = async (e) => {
  e.preventDefault(); // Prevent default form submission

  setLoading(true); // Show loading spinner
  setError(null); // Clear any previous errors

  try {
    // Make POST request to Django backend
    const response = await fetch(
      "http://localhost:8000/api/rfp/create-from-text/",
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ text }), // Send user's text
      }
    );

    const data = await response.json();

    if (response.ok) {
      // Navigate to the created RFP detail page
      navigate(`/rfp/${data.rfp.id}`);
    } else {
      setError(data.error || "Failed to create RFP");
    }
  } catch (err) {
    setError("Network error: Unable to connect to the server");
  } finally {
    setLoading(false);
  }
};
```

**What's happening:**

1. Frontend sends HTTP POST request to `http://localhost:8000/api/rfp/create-from-text/`
2. Request body: `{ "text": "We need 50 laptops..." }`
3. Waits for Django backend to process
4. If successful, navigates to `/rfp/:id` to show the created RFP
5. If error, displays error message

---

## 3. Backend Processing

### ⚙️ Django Receives the Request

#### **File: `backend/backend/urls.py`**

```python
urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/rfp/', include('rfp.urls')),  # Routes all /api/rfp/* to rfp app
]
```

#### **File: `backend/rfp/urls.py`**

```python
urlpatterns = [
    # ... other routes
    path('create-from-text/', views.create_rfp_from_text, name='create-from-text'),
]
```

The request is routed to the `create_rfp_from_text` view function.

---

### 🧠 The View Function

#### **File: `backend/rfp/views.py`**

```python
@api_view(['POST'])
def create_rfp_from_text(request) -> Response:
    """Create an RFP from natural language text."""

    # Step 1: Extract text from request body
    text = request.data.get('text')

    # Step 2: Validate input
    if not text or not text.strip():
        return Response(
            {'error': 'Text must be a non-empty string'},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        # Step 3: Call AI extraction utility
        extraction_result = extract_rfp_from_text(text)

        # Step 4: Check if extraction was successful
        if not extraction_result.get('success', False):
            return Response(
                {'error': 'Failed to extract RFP data'},
                status=status.HTTP_422_UNPROCESSABLE_ENTITY
            )

        # Step 5: Create RFP and RFPItems in database transaction
        with transaction.atomic():
            # Create RFP object
            rfp = RFP.objects.create(
                title=extraction_result.get('title', 'Untitled RFP'),
                natural_language_input=text,
                budget=_parse_budget(extraction_result.get('budget')),
                status=RFP.Status.DRAFT
            )

            # Create RFPItem objects
            items_data = extraction_result.get('items', [])
            for item_data in items_data:
                RFPItem.objects.create(
                    rfp=rfp,
                    name=item_data.get('name', 'Unnamed Item'),
                    quantity=_parse_quantity(item_data.get('quantity', 1)),
                    specifications=item_data.get('specifications', '')
                )

            # Step 6: Serialize and return the created RFP
            serializer = RFPSerializer(rfp)
            return Response(
                {
                    'message': 'RFP created successfully',
                    'rfp': serializer.data,
                },
                status=status.HTTP_201_CREATED
            )

    except Exception as e:
        return Response(
            {'error': f'Internal server error: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
```

**Key Steps:**

1. **Validate** the input text
2. **Call** `extract_rfp_from_text()` to use Gemini AI
3. **Create** database records in a transaction
4. **Serialize** the RFP object to JSON
5. **Return** the response to frontend

---

### 🤖 The AI Extraction Utility

#### **File: `backend/rfp/utils.py`**

This is where the magic happens - converting natural language to structured data!

````python
def extract_rfp_from_text(natural_language_input: str) -> Dict[str, Any]:
    """Extract structured RFP data using Gemini API."""

    # Step 1: Get API key from environment
    api_key = os.getenv('GEMINI_API_KEY')

    # Step 2: Configure Gemini API
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-2.5-flash')

    # Step 3: Create prompt for AI
    prompt = f"""
You are an RFP data extraction assistant.
Analyze the following natural language RFP description and extract structured data.

RFP Description:
{natural_language_input}

Extract and return a JSON object with this structure:
{{
    "title": "Brief descriptive title for the RFP",
    "budget": <numeric value or null>,
    "deadline": "YYYY-MM-DD format or null",
    "items": [
        {{
            "name": "Item name",
            "quantity": <numeric value>,
            "specifications": "Technical specifications"
        }}
    ]
}}

Rules:
1. Extract budget as numeric value without currency symbols
2. Convert dates to YYYY-MM-DD format
3. Create separate entries for each item
4. Return ONLY valid JSON
"""

    # Step 4: Make API call to Gemini
    response = model.generate_content(
        prompt,
        generation_config={
            'temperature': 0.1,  # Low = more consistent
            'max_output_tokens': 2048,
        }
    )

    # Step 5: Parse the JSON response
    response_text = response.text.strip()

    # Clean markdown code blocks if present
    if response_text.startswith('```json'):
        response_text = response_text[7:]
    if response_text.endswith('```'):
        response_text = response_text[:-3]

    # Step 6: Parse JSON
    extracted_data = json.loads(response_text)

    # Step 7: Validate and return
    result = {
        'success': True,
        'error': None,
        'title': extracted_data.get('title', 'Untitled RFP'),
        'budget': extracted_data.get('budget'),
        'deadline': extracted_data.get('deadline'),
        'items': extracted_data.get('items', [])
    }

    return result
````

**Example Transformation:**

**Input Text:**

```
"We need 50 laptops with 16GB RAM and 512GB SSD. Budget is $75,000."
```

**Gemini Output (JSON):**

```json
{
  "title": "Laptop Procurement",
  "budget": 75000,
  "deadline": null,
  "items": [
    {
      "name": "Laptops",
      "quantity": 50,
      "specifications": "16GB RAM, 512GB SSD"
    }
  ]
}
```

**Database Records Created:**

```sql
-- RFP table
INSERT INTO rfp (title, natural_language_input, budget, status)
VALUES ('Laptop Procurement', 'We need 50 laptops...', 75000.00, 'draft');

-- RFPItem table
INSERT INTO rfp_item (rfp_id, name, quantity, specifications)
VALUES (1, 'Laptops', 50, '16GB RAM, 512GB SSD');
```

---

## 4. Background Task - Email Parsing

### 📧 How Email Proposals are Processed

#### **File: `backend/rfp/management/commands/fetch_emails.py`**

This is a Django management command run from the terminal:

```bash
python manage.py fetch_emails --create-proposals
```

**The Complete Email Processing Flow:**

```python
class Command(BaseCommand):
    def handle(self, *args, **options):
        # Step 1: Load email credentials from .env
        email_user = os.getenv('EMAIL_HOST_USER')
        email_password = os.getenv('EMAIL_HOST_PASSWORD')

        # Step 2: Connect to Gmail via IMAP
        mail = imaplib.IMAP4_SSL('imap.gmail.com')
        mail.login(email_user, email_password)
        mail.select('inbox')

        # Step 3: Search for unseen emails
        status, messages = mail.search(None, 'UNSEEN')
        email_ids = messages[0].split()

        # Step 4: Process each email
        for email_id in email_ids:
            # Fetch email data
            status, msg_data = mail.fetch(email_id, '(RFC822)')

            # Parse email
            msg = email.message_from_bytes(msg_data[0][1])

            # Extract key information
            subject = msg.get('Subject')
            sender = msg.get('From')
            sender_email = self._extract_email_address(sender)
            body = self._get_email_body(msg)

            # Step 5: Create proposal if flag is set
            if options['create_proposals']:
                self._create_proposal_from_email(
                    sender_email=sender_email,
                    subject=subject,
                    body=body
                )
```

---

### 🔍 Proposal Creation Logic

```python
def _create_proposal_from_email(self, sender_email, subject, body):
    # Step 1: Find vendor by email
    vendor = Vendor.objects.filter(email__iexact=sender_email).first()

    if not vendor:
        print(f'Vendor not found: {sender_email}')
        return False

    # Step 2: Extract RFP ID from subject
    # Looks for patterns like "Re: RFP #123" or "RFP Invitation: Title"
    rfp_id = self._extract_rfp_id_from_subject(subject)

    # Step 3: Get RFP from database
    rfp = RFP.objects.get(id=rfp_id)

    # Step 4: Extract proposal data using Gemini AI
    extracted_data = extract_proposal_from_email(body)

    # Step 5: Create Proposal record
    proposal = Proposal.objects.create(
        rfp=rfp,
        vendor=vendor,
        price=Decimal(str(extracted_data['price'])),
        payment_terms=extracted_data.get('payment_terms'),
        warranty=extracted_data.get('warranty'),
        raw_email_content=body
    )

    return True
```

---

### 🤖 Email Proposal Extraction

#### **File: `backend/rfp/utils.py`**

```python
def extract_proposal_from_email(email_body: str) -> Dict[str, Any]:
    """Extract price, payment terms, and warranty from email."""

    # Configure Gemini
    genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
    model = genai.GenerativeModel('gemini-2.5-flash')

    # Create extraction prompt
    prompt = f"""
You are a proposal data extraction assistant.
Analyze this vendor email and extract proposal details.

Email Body:
{email_body}

Extract and return JSON:
{{
    "price": <total price as number or null>,
    "payment_terms": "Payment terms description",
    "warranty": "Warranty information"
}}

Rules:
1. Extract total price without currency symbols
2. Extract payment terms (e.g., "Net 30", "50% upfront")
3. Extract warranty (e.g., "1 year warranty")
4. Return ONLY valid JSON
"""

    # Call Gemini API
    response = model.generate_content(prompt)

    # Parse JSON response
    response_text = response.text.strip()
    extracted_data = json.loads(response_text)

    return {
        'success': True,
        'price': extracted_data.get('price'),
        'payment_terms': extracted_data.get('payment_terms'),
        'warranty': extracted_data.get('warranty')
    }
```

**Example Email Processing:**

**Vendor Email Body:**

```
Dear Customer,

Thank you for your RFP. We are pleased to submit our proposal:

Total Quote: $68,500

Payment Terms: 30% upfront, 70% upon delivery

Warranty: All items come with 2-year manufacturer warranty.

Best regards,
Dell Technologies
```

**Gemini Extraction Result:**

```json
{
  "price": 68500,
  "payment_terms": "30% upfront, 70% upon delivery",
  "warranty": "2-year manufacturer warranty"
}
```

**Database Record:**

```sql
INSERT INTO proposal (rfp_id, vendor_id, price, payment_terms, warranty)
VALUES (1, 5, 68500.00, '30% upfront, 70% upon delivery', '2-year manufacturer warranty');
```

---

## 5. Final Output - Comparison View

### 📊 Displaying Vendor Proposals

#### **File: `frontend/src/components/ComparisonTable.js`**

**Step 1: Component Loads**

```javascript
const { id } = useParams(); // Get RFP ID from URL (/comparison/2)
const [rfpData, setRfpData] = useState(null);
const [proposals, setProposals] = useState([]);
```

**Step 2: Fetch Data on Mount**

```javascript
useEffect(() => {
  const fetchData = async () => {
    // Call Django API endpoint
    const response = await fetch(
      `http://localhost:8000/api/rfp/comparison/${id}/`
    );

    const data = await response.json();

    // Set state with fetched data
    setRfpData(data.rfp); // RFP details
    setProposals(data.proposals); // Array of proposals

    // Find lowest price proposal
    const lowest = validProposals.reduce((min, proposal) => {
      return parseFloat(proposal.price) < parseFloat(min.price)
        ? proposal
        : min;
    });
    setLowestPriceId(lowest.id);
  };

  fetchData();
}, [id]);
```

---

### 🔧 Backend Comparison Endpoint

#### **File: `backend/rfp/views.py`**

```python
@api_view(['GET'])
def get_rfp_comparison(request, rfp_id) -> Response:
    """Get RFP with all proposals for comparison."""

    # Get RFP from database
    rfp = get_object_or_404(RFP, pk=rfp_id)

    # Get all proposals for this RFP
    proposals = Proposal.objects.filter(rfp=rfp).select_related('vendor')

    # Build RFP details
    rfp_data = {
        'id': rfp.id,
        'title': rfp.title,
        'budget': str(rfp.budget),
        'status': rfp.status,
        'items': [
            {
                'name': item.name,
                'quantity': item.quantity,
                'specifications': item.specifications
            }
            for item in rfp.items.all()
        ]
    }

    # Build proposals list
    proposals_data = [
        {
            'id': proposal.id,
            'vendor_name': proposal.vendor.name,
            'vendor_email': proposal.vendor.email,
            'price': str(proposal.price),
            'payment_terms': proposal.payment_terms,
            'warranty': proposal.warranty,
            'submitted_at': proposal.submitted_at.isoformat()
        }
        for proposal in proposals
    ]

    # Return combined response
    return Response({
        'rfp': rfp_data,
        'proposals': proposals_data,
        'proposal_count': len(proposals_data)
    })
```

**API Response Example:**

```json
{
  "rfp": {
    "id": 2,
    "title": "Laptop Procurement",
    "budget": "75000.00",
    "status": "sent",
    "items": [
      {
        "name": "Laptops",
        "quantity": 50,
        "specifications": "16GB RAM, 512GB SSD"
      }
    ]
  },
  "proposals": [
    {
      "id": 1,
      "vendor_name": "Dell Technologies",
      "vendor_email": "sales@dell.com",
      "price": "68500.00",
      "payment_terms": "30% upfront, 70% on delivery",
      "warranty": "2-year warranty"
    },
    {
      "id": 2,
      "vendor_name": "HP Inc.",
      "vendor_email": "enterprise@hp.com",
      "price": "72000.00",
      "payment_terms": "Net 30",
      "warranty": "1-year warranty"
    }
  ],
  "proposal_count": 2
}
```

---

### 🎨 Frontend Displays the Table

```javascript
return (
  <div className="comparison-container">
    <h2>{rfpData.title}</h2>
    <p>Budget: ${rfpData.budget}</p>

    <table className="comparison-table">
      <thead>
        <tr>
          <th>Vendor Name</th>
          <th>Total Price</th>
          <th>Payment Terms</th>
          <th>Warranty</th>
        </tr>
      </thead>
      <tbody>
        {proposals.map((proposal) => (
          <tr
            key={proposal.id}
            className={proposal.id === lowestPriceId ? "lowest-price" : ""}
          >
            <td>{proposal.vendor_name}</td>
            <td>
              {formatPrice(proposal.price)}
              {proposal.id === lowestPriceId && (
                <span className="best-price-badge">Lowest Price</span>
              )}
            </td>
            <td>{proposal.payment_terms}</td>
            <td>{proposal.warranty}</td>
          </tr>
        ))}
      </tbody>
    </table>

    <button onClick={getAiRecommendation}>🤖 Ask AI for Recommendation</button>
  </div>
);
```

**CSS Styling:**

- Lowest price row gets green highlighting
- "Lowest Price" badge appears on the cheapest proposal
- Table is responsive and styled with gradients

---

### 🤖 AI Recommendation Feature

**Step 1: User Clicks Button**

```javascript
const getAiRecommendation = async () => {
  setLoadingAi(true);

  // Call AI recommendation endpoint
  const response = await fetch(
    `http://localhost:8000/api/rfp/ai-recommendation/${id}/`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
    }
  );

  const data = await response.json();
  setAiRecommendation(data.recommendation);
  setLoadingAi(false);
};
```

**Step 2: Backend Processes Request**

#### **File: `backend/rfp/views.py`**

```python
@api_view(['POST'])
def get_ai_recommendation(request, rfp_id) -> Response:
    """Get AI recommendation for vendor selection."""

    # Get RFP and proposals
    rfp = get_object_or_404(RFP, pk=rfp_id)
    proposals = Proposal.objects.filter(rfp=rfp).select_related('vendor')

    # Configure Gemini
    genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
    model = genai.GenerativeModel('gemini-2.5-flash')

    # Build comprehensive prompt
    prompt = f"""
You are an expert procurement advisor.
Analyze the following RFP and vendor proposals.

RFP: {rfp.title}
Budget: ${rfp.budget}
Requirements: {rfp.natural_language_input}

Vendor Proposals:
"""

    for idx, proposal in enumerate(proposals, 1):
        prompt += f"""
{idx}. {proposal.vendor.name}
   - Total Price: ${proposal.price}
   - Payment Terms: {proposal.payment_terms}
   - Warranty: {proposal.warranty}
"""

    prompt += """
Provide a clear recommendation on which vendor to choose and why.
Consider price, payment terms, warranty, and overall value.
"""

    # Generate AI recommendation
    response = model.generate_content(
        prompt,
        generation_config={
            'temperature': 0.3,  # Balanced creativity
            'max_output_tokens': 1024,
        }
    )

    recommendation = response.text

    return Response({
        'recommendation': recommendation,
        'rfp_id': rfp_id,
        'proposals_analyzed': len(proposals)
    })
```

**Step 3: Frontend Displays Recommendation**

```javascript
{
  aiRecommendation && (
    <div className="ai-recommendation-box">
      <div className="ai-recommendation-header">
        <span className="ai-icon">🤖</span>
        <h4>AI Recommendation</h4>
        <button onClick={() => setAiRecommendation(null)}>✕</button>
      </div>
      <div className="ai-recommendation-content">{aiRecommendation}</div>
    </div>
  );
}
```

**Example AI Response:**

```
Based on the analysis of all proposals:

RECOMMENDED VENDOR: Dell Technologies

REASONING:
1. PRICE: Dell offers the lowest total price at $68,500, which is
   $3,500 below HP and well within the $75,000 budget.

2. PAYMENT TERMS: The 30% upfront / 70% on delivery structure is
   reasonable and helps with cash flow management.

3. WARRANTY: Dell provides a superior 2-year warranty compared to
   HP's 1-year warranty, offering better long-term value.

4. OVERALL VALUE: While not the absolute cheapest per unit, Dell
   provides the best combination of price, payment flexibility,
   and warranty coverage.

RECOMMENDATION: Select Dell Technologies for this procurement.
```

---

## 6. Complete Flow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                     USER CREATES RFP                            │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  FRONTEND: CreateRFP.js                                         │
│  ┌───────────────────────────────────────────────────┐          │
│  │ 1. User types: "We need 50 laptops..."           │          │
│  │ 2. Clicks "Generate RFP"                          │          │
│  │ 3. handleSubmit() triggered                       │          │
│  │ 4. POST /api/rfp/create-from-text/                │          │
│  │    Body: { text: "We need 50 laptops..." }        │          │
│  └───────────────────────────────────────────────────┘          │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  BACKEND: views.py → create_rfp_from_text()                     │
│  ┌───────────────────────────────────────────────────┐          │
│  │ 1. Validate input text                            │          │
│  │ 2. Call extract_rfp_from_text(text)               │          │
│  └───────────────────────────────────────────────────┘          │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  AI PROCESSING: utils.py → extract_rfp_from_text()              │
│  ┌───────────────────────────────────────────────────┐          │
│  │ 1. Configure Gemini API                           │          │
│  │ 2. Build prompt with extraction rules             │          │
│  │ 3. Call Gemini: model.generate_content()          │          │
│  │ 4. Gemini returns JSON:                           │          │
│  │    {                                              │          │
│  │      "title": "Laptop Procurement",               │          │
│  │      "budget": 75000,                             │          │
│  │      "items": [...]                               │          │
│  │    }                                              │          │
│  │ 5. Parse and validate JSON                        │          │
│  └───────────────────────────────────────────────────┘          │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  DATABASE: Create Records                                       │
│  ┌───────────────────────────────────────────────────┐          │
│  │ 1. BEGIN TRANSACTION                              │          │
│  │ 2. INSERT INTO rfp (title, budget, status...)     │          │
│  │ 3. INSERT INTO rfp_item (name, quantity...)       │          │
│  │ 4. COMMIT TRANSACTION                             │          │
│  └───────────────────────────────────────────────────┘          │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  BACKEND: Serialize and Return                                  │
│  ┌───────────────────────────────────────────────────┐          │
│  │ 1. RFPSerializer(rfp) → JSON                      │          │
│  │ 2. Response: { "rfp": {...}, "message": "..." }   │          │
│  └───────────────────────────────────────────────────┘          │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  FRONTEND: Navigate to RFP Detail                               │
│  ┌───────────────────────────────────────────────────┐          │
│  │ navigate(`/rfp/${data.rfp.id}`)                   │          │
│  │ → User sees created RFP                           │          │
│  └───────────────────────────────────────────────────┘          │
└─────────────────────────────────────────────────────────────────┘

═══════════════════════════════════════════════════════════════════

┌─────────────────────────────────────────────────────────────────┐
│              VENDOR SENDS PROPOSAL VIA EMAIL                    │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  BACKGROUND TASK: python manage.py fetch_emails                 │
│  ┌───────────────────────────────────────────────────┐          │
│  │ 1. Connect to Gmail via IMAP                      │          │
│  │ 2. Search for UNSEEN emails                       │          │
│  │ 3. For each email:                                │          │
│  │    - Parse subject, sender, body                  │          │
│  │    - Find Vendor by email                         │          │
│  │    - Extract RFP ID from subject                  │          │
│  └───────────────────────────────────────────────────┘          │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  AI PROCESSING: utils.py → extract_proposal_from_email()        │
│  ┌───────────────────────────────────────────────────┐          │
│  │ Email Body: "Total: $68,500, Terms: 30% upfront"  │          │
│  │                                                    │          │
│  │ Gemini extracts:                                  │          │
│  │ {                                                 │          │
│  │   "price": 68500,                                 │          │
│  │   "payment_terms": "30% upfront, 70% delivery",   │          │
│  │   "warranty": "2-year warranty"                   │          │
│  │ }                                                 │          │
│  └───────────────────────────────────────────────────┘          │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  DATABASE: Create Proposal                                      │
│  ┌───────────────────────────────────────────────────┐          │
│  │ INSERT INTO proposal                              │          │
│  │   (rfp_id, vendor_id, price, payment_terms,       │          │
│  │    warranty, raw_email_content)                   │          │
│  │ VALUES (1, 5, 68500, '30% upfront...', ...)       │          │
│  └───────────────────────────────────────────────────┘          │
└─────────────────────────────────────────────────────────────────┘

═══════════════════════════════════════════════════════════════════

┌─────────────────────────────────────────────────────────────────┐
│           USER VIEWS COMPARISON TABLE                           │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  FRONTEND: ComparisonTable.js                                   │
│  ┌───────────────────────────────────────────────────┐          │
│  │ 1. useParams() gets RFP ID from URL               │          │
│  │ 2. useEffect() → fetchData()                      │          │
│  │ 3. GET /api/rfp/comparison/{id}/                  │          │
│  └───────────────────────────────────────────────────┘          │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  BACKEND: views.py → get_rfp_comparison()                       │
│  ┌───────────────────────────────────────────────────┐          │
│  │ 1. Query RFP from database                        │          │
│  │ 2. Query all Proposals for this RFP               │          │
│  │ 3. Join with Vendor data                          │          │
│  │ 4. Build response:                                │          │
│  │    {                                              │          │
│  │      "rfp": {...},                                │          │
│  │      "proposals": [                               │          │
│  │        { vendor, price, terms, warranty },        │          │
│  │        { vendor, price, terms, warranty }         │          │
│  │      ]                                            │          │
│  │    }                                              │          │
│  └───────────────────────────────────────────────────┘          │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  FRONTEND: Display Table                                        │
│  ┌───────────────────────────────────────────────────┐          │
│  │ 1. Map proposals to table rows                    │          │
│  │ 2. Calculate lowest price                         │          │
│  │ 3. Highlight lowest price in green                │          │
│  │ 4. Show "Lowest Price" badge                      │          │
│  └───────────────────────────────────────────────────┘          │
└─────────────────────────────────────────────────────────────────┘

═══════════════════════════════════════════════════════════════════

┌─────────────────────────────────────────────────────────────────┐
│         USER CLICKS "ASK AI FOR RECOMMENDATION"                 │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  FRONTEND: getAiRecommendation()                                │
│  ┌───────────────────────────────────────────────────┐          │
│  │ POST /api/rfp/ai-recommendation/{id}/             │          │
│  └───────────────────────────────────────────────────┘          │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  BACKEND: views.py → get_ai_recommendation()                    │
│  ┌───────────────────────────────────────────────────┐          │
│  │ 1. Get RFP and all proposals                      │          │
│  │ 2. Build comprehensive prompt:                    │          │
│  │    "You are an expert procurement advisor..."     │          │
│  │    + RFP details                                  │          │
│  │    + All vendor proposals                         │          │
│  │ 3. Call Gemini with temperature=0.3               │          │
│  └───────────────────────────────────────────────────┘          │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  AI RESPONSE: Gemini Analyzes                                   │
│  ┌───────────────────────────────────────────────────┐          │
│  │ "RECOMMENDED: Dell Technologies                   │          │
│  │                                                    │          │
│  │  REASONING:                                       │          │
│  │  1. Lowest price: $68,500                         │          │
│  │  2. Flexible payment terms                        │          │
│  │  3. Best warranty: 2 years                        │          │
│  │  4. Overall best value                            │          │
│  │                                                    │          │
│  │  Select Dell for this procurement."               │          │
│  └───────────────────────────────────────────────────┘          │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  FRONTEND: Display Recommendation                               │
│  ┌───────────────────────────────────────────────────┐          │
│  │ Show in animated gradient box                     │          │
│  │ User can close with X button                      │          │
│  └───────────────────────────────────────────────────┘          │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🎓 Key Takeaways

### Frontend Architecture

- **React Router** handles navigation between pages
- **useState** manages component state (loading, data, errors)
- **useEffect** triggers data fetching on component mount
- **fetch API** makes HTTP requests to Django backend

### Backend Architecture

- **Django REST Framework** provides API endpoints
- **@api_view decorator** marks functions as API views
- **Django ORM** handles database queries
- **Serializers** convert models to JSON
- **transaction.atomic()** ensures data consistency

### AI Integration Points

1. **RFP Creation**: Natural language → Structured data
2. **Proposal Extraction**: Email text → Price/Terms/Warranty
3. **Vendor Recommendation**: All proposals → Expert analysis

### Database Flow

```
User Input → Gemini AI → Structured JSON → Django ORM → SQLite → Serializer → JSON Response → React State → UI
```

### Email Processing

```
Gmail Inbox → IMAP → Python → Parse → Gemini AI → Extract Data → Database → Available for Comparison
```

This architecture provides a complete end-to-end automated procurement system powered by AI! 🚀
