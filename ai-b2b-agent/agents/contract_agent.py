"""
Contract Agent
==============
Takes the agreed deal and generates a formal B2B purchase contract.
Saves it as a .txt file (simulates PDF/DocuSign in production).
"""

import json
from datetime import datetime
from utils.logger import setup_logger
from utils.llm_client import get_anthropic_client

logger = setup_logger("contract_agent")

client = get_anthropic_client()

SYSTEM_PROMPT = """You are a B2B Contract Drafting Agent for an SME.

Given a finalised deal and the parties involved, produce a complete,
professional B2B Purchase Agreement.

The contract must include:
1. Header with contract ID, date, parties
2. Recitals / background
3. Definitions
4. Product / service description
5. Price and payment terms
6. Delivery schedule and conditions
7. Inspection and acceptance
8. Warranties and representations
9. Penalty and SLA breach clause (auto-calculated late penalty)
10. Confidentiality clause
11. Dispute resolution (arbitration first)
12. Governing law
13. Signature block

Make it legally solid but in plain English. Use formal contract language.
Return ONLY the contract text — no JSON wrapper, no commentary.
"""


class ContractAgent:
    async def run(self, deal: dict, rfq: dict) -> dict:
        logger.info("Drafting contract")

        contract_id = f"CONTRACT-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        buyer_info = rfq["buyer"]
        total = deal.get("total_value", deal.get("price_per_unit", 0) * deal.get("quantity", 1))

        user_message = f"""
Draft a B2B Purchase Agreement for the following deal:

CONTRACT ID   : {contract_id}
DATE          : {datetime.utcnow().strftime('%B %d, %Y')}

SELLER:
  Name        : ABC Industrial Supplies Pvt. Ltd.
  Registration: U74999MH2018PTC310852
  Address     : Plot 14, MIDC Industrial Area, Pune, Maharashtra - 411019
  GSTIN       : 27AABCA1234Z1ZM

BUYER:
  Name        : {buyer_info.get('company')}
  Registration: {buyer_info.get('registration_number')}
  GSTIN       : {buyer_info.get('gstin')}
  Email       : {buyer_info.get('email')}

DEAL TERMS:
  Product     : {deal.get('product')}
  Quantity    : {deal.get('quantity')} units
  Unit Price  : ₹{deal.get('price_per_unit')}
  Total Value : ₹{total:,}
  Currency    : {deal.get('currency', 'INR')}
  Delivery    : {deal.get('delivery_days')} days from contract signing
  Payment     : {deal.get('payment_terms')}

PENALTY CLAUSE: 0.5% of total contract value per day of delay beyond delivery date,
capped at 10% of total value.

Please draft the complete contract now.
"""

        if client is None:
          contract_text = f"""B2B PURCHASE AGREEMENT
    Contract ID: {contract_id}
    Date: {datetime.utcnow().strftime('%B %d, %Y')}

    Seller: ABC Industrial Supplies Pvt. Ltd.
    Buyer: {buyer_info.get('company')}

    Product: {deal.get('product')}
    Quantity: {deal.get('quantity')} units
    Unit Price: Rs.{deal.get('price_per_unit')}
    Total Value: Rs.{total:,}
    Delivery: {deal.get('delivery_days')} days from signing
    Payment Terms: {deal.get('payment_terms')}

    Penalty Clause:
    0.5% of total contract value per day of delivery delay, capped at 10%.

    Confidentiality:
    Both parties will keep all commercial and technical details confidential.

    Dispute Resolution:
    Any dispute will first be attempted via arbitration.

    Governing Law:
    Laws of India.

    Signatures:
    Authorized Signatory (Seller) ____________________
    Authorized Signatory (Buyer) _____________________
    """
        else:
          response = client.messages.create(
            model="claude-opus-4-5",
            max_tokens=2500,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_message}]
          )

          contract_text = response.content[0].text.strip()

        # Save contract to file
        filename = f"contracts/{contract_id}.txt"
        import os
        os.makedirs("contracts", exist_ok=True)
        with open(filename, "w", encoding="utf-8") as f:
            f.write(contract_text)

        contract_hash = str(abs(hash(contract_text)))[:16]

        print(f"\n[Contract Agent]")
        print(f"  Contract ID : {contract_id}")
        print(f"  Total Value : ₹{total:,}")
        print(f"  Saved to    : {filename}")
        print(f"  Hash        : {contract_hash}")
        print(f"  Status      : ✅ Draft complete (awaiting e-signature in production)")

        return {
            "contract_id": contract_id,
            "filename": filename,
            "hash": contract_hash,
            "total_value": total,
            "status": "draft_generated",
            "created_at": datetime.utcnow().isoformat()
        }
