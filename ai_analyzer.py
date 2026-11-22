
import streamlit as st
from groq import Groq, RateLimitError, APIConnectionError, APIStatusError

MODEL_NAME = "openai/gpt-oss-120b"


def explain_loan_with_groq(extracted_text):
    """Analyze loan agreement text using Groq AI."""

    api_key = st.secrets.get("GROQ_API_KEY")

    if not api_key:
        raise RuntimeError(
            "GROQ_API_KEY is missing from .streamlit/secrets.toml"
        )

    if not extracted_text or not extracted_text.strip():
        return "No PDF text was provided for AI analysis."

    evidence_text = extracted_text[:30000]

    # IMPORTANT: Keep this prompt INSIDE the function.
    prompt = f"""
You are LoanLens, a highly accurate loan agreement analysis assistant.

Analyze the supplied loan agreement.

STRICT RULES:
1. Use only information explicitly supported by the document.
2. Never invent financial amounts, fees or conditions.
3. Separate confirmed facts from missing information.
4. Do not assume a fee applies to every missed payment.
5. Do not assume a processing fee is payable upfront.
6. Do not assume a fee is refundable or non-refundable.
7. Do not assume an interest rate is fixed or variable.
8. Do not assume a repayment frequency unless stated.
9. Explain clauses in simple language without changing their meaning.
10. Highlight potential risks without presenting assumptions as facts.
11. State "Not specified in the supplied document" for missing details.
12. Use page references only from [PAGE N] markers.
13. Never invent page references.
14. Do not provide definitive legal or financial advice.

REPORT FORMAT:

## 1. Loan Overview
Create a table containing loan amount, interest rate, tenure,
repayment details, PDF page and confirmation status.

## 2. Charges and Fees
Create a table containing charge, exact stated amount or condition,
PDF page and status.

## 3. Important Loan Conditions
Show the original clause and explain it in simple language.

## 4. Potential Borrower Risks
Identify risks supported by the actual document.
Explain why missing information needs clarification.

## 5. Missing Information
List important details that are not specified in the document.

## 6. Overall Assessment
Provide a balanced assessment and questions the borrower
should ask the lender before accepting the agreement.

DOCUMENT TEXT:

{evidence_text}
"""

    try:
        client = Groq(api_key=api_key)

        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a precise financial document analyst. "
                        "Never fabricate information."
                    )
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.2,
            max_completion_tokens=2000
        )

        result = response.choices[0].message.content

        if not result:
            return "The AI returned an empty response. Please try again."

        return result

    except RateLimitError as error:
        raise RuntimeError(
            "Groq rate limit or quota exceeded. Check your Groq account limits."
        ) from error

    except APIConnectionError as error:
        raise RuntimeError(
            "Could not connect to Groq. Check your internet connection."
        ) from error

    except APIStatusError as error:
        raise RuntimeError(
            f"Groq API error {error.status_code}. "
            "Check your model and API account."
        ) from error

    except Exception as error:
        raise RuntimeError(
            f"Groq analysis failed: {error}"
        ) from error
