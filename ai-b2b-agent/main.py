"""
B2B Multi-Agent Transaction System
====================================
Run: python main.py
"""

import asyncio
from orchestrator import Orchestrator
from utils.logger import setup_logger

logger = setup_logger("main")


async def demo():
    """Run a full demo transaction end-to-end."""

    print("\n" + "="*60)
    print("  B2B MULTI-AGENT TRANSACTION SYSTEM")
    print("="*60 + "\n")

    orchestrator = Orchestrator()

    # ── Sample RFQ (Request for Quotation) ────────────────────────
    rfq = {
        "transaction_id": "TXN-2025-0418-001",
        "type": "purchase_order",
        "buyer": {
            "company": "Acme Manufacturing Ltd",
            "registration_number": "U74999MH2010PTC123456",
            "gstin": "27AAPFU0939F1ZV",
            "email": "procurement@acme.com",
            "country": "India"
        },
        "rfq": {
            "product": "Industrial Hydraulic Valves",
            "sku": "HV-500-SERIES",
            "quantity": 500,
            "target_price_per_unit": 4200,   # buyer wants ₹4200/unit
            "currency": "INR",
            "delivery_days": 30,
            "payment_terms": "net_60"
        }
    }

    # ── Seller policy (your SME's limits) ─────────────────────────
    seller_policy = {
        "floor_price_per_unit": 4000,         # never go below this
        "list_price_per_unit": 4800,
        "max_discount_pct": 10,               # max 10% off list
        "min_delivery_days": 21,
        "accepted_payment_terms": ["net_30", "net_45", "net_60"],
        "max_negotiation_rounds": 5
    }

    result = await orchestrator.run_transaction(rfq, seller_policy)

    print("\n" + "="*60)
    print("  FINAL TRANSACTION RESULT")
    print("="*60)
    print(f"  Status      : {result['status']}")
    print(f"  Transaction : {result['transaction_id']}")
    print(f"  Stage       : {result['final_stage']}")
    if "deal" in result:
        d = result["deal"]
        print(f"  Price/unit  : ₹{d.get('price_per_unit', 'N/A')}")
        print(f"  Quantity    : {d.get('quantity', 'N/A')}")
        print(f"  Delivery    : {d.get('delivery_days', 'N/A')} days")
        print(f"  Payment     : {d.get('payment_terms', 'N/A')}")
    print("="*60 + "\n")

    return result


if __name__ == "__main__":
    asyncio.run(demo())
