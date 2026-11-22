# LoanLens – AI-Powered Loan Agreement Analyzer

**Making loan agreements easier to understand through AI-powered analysis.**

LoanLens is an AI-powered loan transparency application designed to help borrowers understand loan agreements, calculate EMIs, compare loan offers, and identify important charges and conditions in loan documents.

The application combines financial calculations, PDF text extraction, and AI-based analysis to make complex loan information easier to understand.

## 🚀 Key Features

### 1. EMI Calculator
- Calculate monthly loan instalments (EMI).
- Calculate total interest payable.
- Calculate total repayment amount.
- Include processing fees in loan cost calculations.

### 2. Loan Comparison
- Compare two different loan offers.
- Evaluate EMI and total repayment costs.
- Identify which loan offer is more economical.
- Understand the cost difference between offers.

### 3. AI-Powered PDF Loan Analyzer
- Upload loan agreement PDF documents.
- Extract important loan information.
- Identify loan amount, interest rate and tenure.
- Detect important charges and clauses.
- Highlight missing loan information.
- Generate an AI-powered explanation of loan terms.

### 4. Loan Transparency
- Present complex financial information in a simpler format.
- Help borrowers understand important loan conditions.
- Support more informed financial decisions.

## 🛠️ Technologies Used

| Technology | Purpose |
|---|---|
| Python | Core programming language |
| Streamlit | Web application interface |
| Groq API | AI-powered loan explanation |
| GPT-OSS-120B | AI model used through Groq |
| PyPDF | PDF text extraction |
| Git & GitHub | Version control and project hosting |

## ⚙️ Project Structure

```text
LoanLens-AI-Loan-Analyzer/
│
├── app.py
├── ai_analyzer.py
├── loan_calculator.py
├── requirements.txt
├── README.md
└── .gitignore
```

## 💻 Installation and Setup

### Step 1: Clone the repository

```bash
git clone https://github.com/apoorva-k-c/LoanLens-AI-Loan-Analyzer.git
```

### Step 2: Open the project folder

```bash
cd LoanLens-AI-Loan-Analyzer
```

### Step 3: Install dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Configure the Groq API key

Create a file named `.streamlit/secrets.toml` and add:

```toml
GROQ_API_KEY = "your_groq_api_key"
```

Obtain your API key from [Groq Console](https://console.groq.com/keys).

**Important:** Never upload your API key or `secrets.toml` file to GitHub.

### Step 5: Run the application

```bash
python -m streamlit run app.py
```

Open the local application at:

```text
http://localhost:8501
```

## 🎯 Project Objective

LoanLens aims to improve loan transparency by helping borrowers understand financial commitments before making borrowing decisions.

It combines traditional financial calculations with AI-powered document analysis to make loan information more accessible and understandable.

## 🔮 Future Enhancements

- Support for additional loan document formats.
- Enhanced financial risk analysis.
- More advanced loan comparison features.
- Improved document analysis and visualization.
- Online deployment for wider accessibility.

## 👩‍💻 Developer

**Apoorva K C**

GitHub: [apoorva-k-c](https://github.com/apoorva-k-c)

Project: [LoanLens – AI Loan Analyzer](https://github.com/apoorva-k-c/LoanLens-AI-Loan-Analyzer)

---

**LoanLens – Understand Your Loan. Make Informed Decisions.**
