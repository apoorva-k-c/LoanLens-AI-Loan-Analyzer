
import re
import streamlit as st
from pypdf import PdfReader
from ai_analyzer import explain_loan_with_groq


# --------------------------------------------------
# PAGE CONFIGURATION
# --------------------------------------------------

st.set_page_config(
    page_title="LoanLens | Loan Transparency Analyzer",
    page_icon="💳",
    layout="wide"
)


# --------------------------------------------------
# CUSTOM CSS
# --------------------------------------------------

st.markdown("""
<style>
.stApp {
    background: #0b1120;
    color: #f1f5f9;
}
section[data-testid="stSidebar"] {
    background: #111827;
}
h1, h2, h3, h4 {
    color: #e2e8f0;
}
div[data-testid="stMetric"] {
    background: #172235;
    border: 1px solid #334155;
    padding: 18px;
    border-radius: 12px;
}
.stButton > button {
    background: #2563eb;
    color: white;
    border-radius: 8px;
    border: none;
    padding: 10px 18px;
    font-weight: bold;
}
.stButton > button:hover {
    background: #1d4ed8;
    color: white;
}
div[data-testid="stFileUploader"] {
    background: #172235;
    padding: 15px;
    border-radius: 12px;
}
</style>
""", unsafe_allow_html=True)


# --------------------------------------------------
# HEADER
# --------------------------------------------------

st.title("💳 LoanLens")
st.caption("AI-Powered Loan Transparency Analyzer")

st.markdown(
    "Understand loan costs, compare offers and identify "
    "important conditions before accepting a loan."
)


# --------------------------------------------------
# EMI CALCULATOR
# --------------------------------------------------

def calculate_emi(principal, annual_rate, months):

    if months <= 0:
        return 0.0

    monthly_rate = annual_rate / (12 * 100)

    if monthly_rate == 0:
        return principal / months

    factor = (1 + monthly_rate) ** months

    return principal * monthly_rate * factor / (factor - 1)


def display_emi(principal, annual_rate, months, processing_fee):

    emi = calculate_emi(principal, annual_rate, months)

    total_payment = emi * months
    total_interest = total_payment - principal
    total_cost = total_payment + processing_fee

    return emi, total_interest, total_cost


# --------------------------------------------------
# PDF EXTRACTION
# --------------------------------------------------

def extract_pdf(uploaded_file):

    uploaded_file.seek(0)
    reader = PdfReader(uploaded_file)

    if reader.is_encrypted:
        try:
            reader.decrypt("")
        except Exception as exc:
            raise ValueError(
                "This PDF is password-protected. "
                "Upload an unlocked PDF."
            ) from exc

    page_texts = []
    full_text_parts = []

    for page_number, page in enumerate(reader.pages, start=1):

        page_text = page.extract_text() or ""

        page_texts.append({
            "page": page_number,
            "text": page_text
        })

        full_text_parts.append(
            f"[PAGE {page_number}]\n{page_text}"
        )

    evidence_text = "\n\n".join(full_text_parts)

    full_text = "\n\n".join(
        item["text"] for item in page_texts
    )

    return full_text, evidence_text, page_texts


# --------------------------------------------------
# LOAN DETAIL EXTRACTION
# --------------------------------------------------

def extract_loan_details(page_texts):

    patterns = {

        "Loan Amount": (
            r"(?:loan amount|principal amount|sanctioned amount)"
            r"\s*[:\-]?\s*((?:rs\.?|inr|₹)\s*)?([\d,]+(?:\.\d+)?)"
        ),

        "Interest Rate": (
            r"(?:annual interest rate|interest rate|rate of interest)"
            r"\s*[:\-]?\s*(\d+(?:\.\d+)?\s*%?)"
        ),

        "Processing Fee": (
            r"processing fee\s*[:\-]?\s*"
            r"((?:rs\.?|inr|₹)\s*)?([\d,]+(?:\.\d+)?\s*%?)"
        ),

        "Late Payment Fee": (
            r"(?:late payment fee|late fee)"
            r"\s*[:\-]?\s*"
            r"((?:rs\.?|inr|₹)\s*)?([\d,]+(?:\.\d+)?\s*%?)"
        ),

        "Loan Tenure": (
            r"(?:loan tenure|loan term|tenure|duration)"
            r"\s*[:\-]?\s*(\d+\s*(?:months?|years?))"
        ),

        "Prepayment Charges": (
            r"(?:prepayment charges|prepayment penalty|"
            r"foreclosure charges|foreclosure penalty)"
            r"\s*[:\-]?\s*([^.\n;]+)"
        )
    }

    results = {}
    result_pages = {}

    for field, pattern in patterns.items():

        found = False

        for page in page_texts:

            match = re.search(
                pattern,
                page["text"],
                re.IGNORECASE
            )

            if match:

                # Use only the value portion, not the field label.
                value = match.group(1) if field == "Loan Tenure" else None

                if field in ("Loan Amount", "Processing Fee",
                             "Late Payment Fee"):
                    currency = match.group(1) or ""
                    amount = match.group(2)
                    value = f"{currency.strip()} {amount}".strip()

                elif field == "Interest Rate":
                    value = match.group(1).strip()

                elif field == "Prepayment Charges":
                    value = match.group(1).strip()

                results[field] = value
                result_pages[field] = page["page"]
                found = True
                break

        if not found:
            results[field] = "Not found in supplied text"
            result_pages[field] = None

    return results, result_pages


# --------------------------------------------------
# CHARGE-RELATED CLAUSES
# --------------------------------------------------

def find_charge_clauses(page_texts):

    charge_patterns = [
        ("Processing Fee", r"processing fee"),
        ("Late Payment Fee", r"late payment fee|late fee"),
        ("Prepayment Charge", r"prepayment"),
        ("Foreclosure Charge", r"foreclosure"),
        ("Penalty", r"penalty"),
        ("Additional Charge", r"additional charge"),
        ("Bounce / Dishonour Charge", r"bounce charge|dishonour charge"),
        ("Documentation Fee", r"documentation fee"),
        ("Insurance Fee", r"insurance fee"),
        ("Legal Fee", r"legal fee"),
        ("Collection Charge", r"collection charge"),
        ("Default", r"default|overdue")
    ]

    flagged_lines = []
    seen = set()

    for page in page_texts:

        for line in page["text"].splitlines():

            clean_line = line.strip()

            if not clean_line:
                continue

            for charge_name, pattern in charge_patterns:

                if re.search(pattern, clean_line, re.IGNORECASE):

                    key = (page["page"], clean_line)

                    if key not in seen:

                        flagged_lines.append({
                            "charge": charge_name,
                            "text": clean_line,
                            "page": page["page"]
                        })

                        seen.add(key)

                    break

    return flagged_lines


# --------------------------------------------------
# AI REPORT DISPLAY
# --------------------------------------------------

def render_ai_report(report):

    if not report:
        st.warning("The AI returned an empty report.")
        return

    # Streamlit renders Markdown headings, tables and lists.
    st.markdown(report)


# --------------------------------------------------
# MAIN TABS
# --------------------------------------------------

tab1, tab2, tab3 = st.tabs([
    "📊 EMI Calculator",
    "⚖️ Compare Loans",
    "📄 PDF Analyzer"
])


# ==================================================
# TAB 1 - EMI CALCULATOR
# ==================================================

with tab1:

    st.header("Loan EMI Calculator")

    col1, col2 = st.columns(2)

    with col1:

        principal = st.number_input(
            "Loan Amount (₹)",
            min_value=1000.0,
            value=100000.0,
            step=5000.0
        )

        annual_rate = st.number_input(
            "Annual Interest Rate (%)",
            min_value=0.0,
            value=12.0,
            step=0.5
        )

    with col2:

        months = st.number_input(
            "Loan Duration (Months)",
            min_value=1,
            value=24
        )

        processing_fee = st.number_input(
            "Processing Fee (₹)",
            min_value=0.0,
            value=2000.0,
            step=500.0
        )

    if st.button("Calculate EMI", key="calculate_emi"):

        emi, interest, total_cost = display_emi(
            principal,
            annual_rate,
            months,
            processing_fee
        )

        st.subheader("Your Loan Results")

        c1, c2, c3 = st.columns(3)

        c1.metric("Monthly EMI", f"₹{emi:,.2f}")
        c2.metric("Total Interest", f"₹{interest:,.2f}")
        c3.metric("Total Cost", f"₹{total_cost:,.2f}")

        st.info(
            f"Total repayment including processing fee: "
            f"₹{total_cost:,.2f}"
        )

        st.caption(
            "Estimate assumes a standard monthly reducing-balance loan. "
            "Other contractual charges are not included unless entered."
        )


# ==================================================
# TAB 2 - COMPARE LOANS
# ==================================================

with tab2:

    st.header("Compare Two Loan Offers")

    col1, col2 = st.columns(2)

    with col1:

        st.subheader("Offer A")

        amount_a = st.number_input(
            "Loan Amount A (₹)",
            min_value=1000.0,
            value=100000.0,
            key="amount_a"
        )

        rate_a = st.number_input(
            "Interest Rate A (%)",
            min_value=0.0,
            value=10.0,
            key="rate_a"
        )

        months_a = st.number_input(
            "Duration A (Months)",
            min_value=1,
            value=24,
            key="months_a"
        )

        fee_a = st.number_input(
            "Processing Fee A (₹)",
            min_value=0.0,
            value=1500.0,
            key="fee_a"
        )

    with col2:

        st.subheader("Offer B")

        amount_b = st.number_input(
            "Loan Amount B (₹)",
            min_value=1000.0,
            value=100000.0,
            key="amount_b"
        )

        rate_b = st.number_input(
            "Interest Rate B (%)",
            min_value=0.0,
            value=11.0,
            key="rate_b"
        )

        months_b = st.number_input(
            "Duration B (Months)",
            min_value=1,
            value=24,
            key="months_b"
        )

        fee_b = st.number_input(
            "Processing Fee B (₹)",
            min_value=0.0,
            value=1000.0,
            key="fee_b"
        )

    if st.button("Compare Loan Offers"):

        emi_a, interest_a, cost_a = display_emi(
            amount_a, rate_a, months_a, fee_a
        )

        emi_b, interest_b, cost_b = display_emi(
            amount_b, rate_b, months_b, fee_b
        )

        st.subheader("Comparison Results")

        comparison1, comparison2 = st.columns(2)

        with comparison1:

            st.markdown("### Offer A")
            st.metric("Monthly EMI", f"₹{emi_a:,.2f}")
            st.metric("Total Interest", f"₹{interest_a:,.2f}")
            st.metric("Total Cost", f"₹{cost_a:,.2f}")

        with comparison2:

            st.markdown("### Offer B")
            st.metric("Monthly EMI", f"₹{emi_b:,.2f}")
            st.metric("Total Interest", f"₹{interest_b:,.2f}")
            st.metric("Total Cost", f"₹{cost_b:,.2f}")

        if cost_a < cost_b:

            st.success(
                f"Offer A is cheaper by ₹{cost_b - cost_a:,.2f}."
            )

        elif cost_b < cost_a:

            st.success(
                f"Offer B is cheaper by ₹{cost_a - cost_b:,.2f}."
            )

        else:

            st.info("Both offers have the same estimated total cost.")

        st.caption(
            "Comparison assumes standard monthly reducing-balance EMI. "
            "Only entered processing fees are included."
        )


# ==================================================
# TAB 3 - PDF ANALYZER
# ==================================================

with tab3:

    st.header("AI Loan Agreement Analyzer")

    st.write(
        "Upload your loan agreement PDF to extract loan details, "
        "identify charges and receive an AI explanation."
    )

    uploaded_file = st.file_uploader(
        "Upload Loan Agreement PDF",
        type=["pdf"],
        key="loan_pdf"
    )

    if uploaded_file is not None:

        if st.button("Analyze Loan Agreement", key="analyze_pdf"):

            try:

                with st.spinner("Extracting PDF text..."):

                    full_text, evidence_text, page_texts = extract_pdf(
                        uploaded_file
                    )

                if not full_text.strip():

                    st.error(
                        "No readable text was found. This PDF may be "
                        "scanned or image-based. OCR is required for "
                        "scanned documents."
                    )

                else:

                    results, result_pages = extract_loan_details(
                        page_texts
                    )

                    flagged_lines = find_charge_clauses(page_texts)

                    st.success("PDF text extracted successfully!")

                    # EXTRACTED LOAN INFORMATION

                    st.subheader("Extracted Loan Information")

                    for field, value in results.items():

                        page_number = result_pages[field]

                        st.markdown(f"**{field}:** {value}")

                        if page_number:
                            st.caption(
                                f"📌 Source: PDF Page {page_number}"
                            )

                    # CHARGE TABLE

                    st.divider()
                    st.subheader("Charge Identification")

                    if flagged_lines:

                        charge_rows = [
                            {
                                "Charge Type": item["charge"],
                                "Clause Found": item["text"],
                                "PDF Page": item["page"]
                            }
                            for item in flagged_lines
                        ]

                        st.dataframe(
                            charge_rows,
                            use_container_width=True,
                            hide_index=True
                        )

                        st.caption(
                            "These are keyword-matched clauses. "
                            "Review the original PDF to confirm their "
                            "meaning and applicability."
                        )

                    else:

                        st.info(
                            "No matching charge-related clauses were found "
                            "in the extracted text. This does not guarantee "
                            "that no other charges exist."
                        )

                    # PAGE EVIDENCE

                    st.divider()
                    st.subheader("📌 PDF Page Evidence")

                    st.caption(
                        "Review the original extracted text from each page."
                    )

                    with st.expander(
                        "View page-by-page extracted evidence"
                    ):

                        for page in page_texts:

                            st.markdown(
                                f"**PDF Page {page['page']}**"
                            )

                            st.text(
                                page["text"] or "No text extracted."
                            )

                            st.divider()

                    with st.expander(
                        "View complete extracted PDF text"
                    ):

                        st.text(full_text)

                    # GROQ AI ANALYSIS

                    st.divider()
                    st.subheader("🤖 AI Loan Agreement Explanation")

                    with st.spinner(
                        "Groq AI is analyzing your loan agreement..."
                    ):

                        ai_result = explain_loan_with_groq(
                            evidence_text
                        )

                    render_ai_report(ai_result)

                    st.caption(
                        "AI explanations are informational and may contain "
                        "errors. They are not legal or financial advice. "
                        "Verify every finding against the original agreement."
                    )

            except Exception as error:

                st.error(f"Analysis failed: {error}")

    else:

        st.info("Please upload a PDF loan agreement to begin.")


# --------------------------------------------------
# FOOTER
# --------------------------------------------------

st.divider()

st.caption(
    "LoanLens | AI-Powered Loan Transparency Analyzer | "
    "Always verify financial terms with the original agreement."
)


