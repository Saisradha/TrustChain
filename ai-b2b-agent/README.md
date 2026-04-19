# B2B Multi-Agent Transaction System

Autonomous agents that negotiate, verify, monitor, and enforce B2B transactions
without manual intervention. Built on Anthropic Claude.

---

## What it does

```
Buyer sends RFQ
      │
      ▼
[Verification Agent]  ── KYB check, GSTIN validation, trust scoring
      │
      ▼
[Negotiation Agent]   ── Multi-round offer/counter-offer (up to 5 rounds)
      │
      ▼
[Contract Agent]      ── Generates full B2B purchase agreement
      │
      ▼
[Monitor Agent]       ── SLA & delivery health check
      │
      ▼ (if breach)
[Enforcement Agent]   ── Penalty calculation + breach notice
```

---

## Setup (5 minutes)

### 1. Prerequisites
- Python 3.9 or higher
- An Anthropic API key (get one at https://console.anthropic.com)

Check your Python version:
```bash
python --version
```

### 2. Create a virtual environment
```bash
# In VS Code terminal (Ctrl+` to open)

# Navigate to the project folder
cd b2b_agent_system

# Create virtual environment
python -m venv venv

# Activate it
# On Windows:
venv\Scripts\activate
# On Mac/Linux:
source venv/bin/activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Set your Anthropic API key
```bash
# On Windows (Command Prompt):
set ANTHROPIC_API_KEY=sk-ant-your-key-here

# On Windows (PowerShell):
$env:ANTHROPIC_API_KEY="sk-ant-your-key-here"

# On Mac/Linux:
export ANTHROPIC_API_KEY=sk-ant-your-key-here
```

Or create a `.env` file in the project root:
```
ANTHROPIC_API_KEY=sk-ant-your-key-here
```
Then add `python-dotenv` to requirements.txt and add this to the top of main.py:
```python
from dotenv import load_dotenv; load_dotenv()
```

### 5. Run
```bash
python main.py
```

---

## Expected output

```
============================================================
  B2B MULTI-AGENT TRANSACTION SYSTEM
============================================================

[Verification Agent]
  Company    : Acme Manufacturing Ltd
  Trust Score: 78/100  ✅ PASS
  Risk Level : low
  GSTIN Valid: True
  Decision   : PROCEED

[Negotiation Agent]
  Buyer wants : ₹4200/unit, 30d delivery, net_60
  Our floor   : ₹4000/unit

  Round 1: COUNTER
    Offer     : ₹4320/unit, 25d, net_45
    Rationale : Offering 10% discount from list price ...

  Round 2: COUNTER
    Offer     : ₹4250/unit, 25d, net_45
    ...

  ✅ Deal accepted!

[Contract Agent]
  Contract ID : CONTRACT-20250418143022
  Total Value : ₹2,125,000
  Saved to    : contracts/CONTRACT-20250418143022.txt
  Status      : ✅ Draft complete

[Monitor Agent]
  Health Score    : 85/100  ✅
  Delivery Status : on_track
  Payment Status  : on_track
  Breach Detected : ✅ No

============================================================
  FINAL TRANSACTION RESULT
============================================================
  Status      : success
  Transaction : TXN-2025-0418-001
  Stage       : closed
  Price/unit  : ₹4250
  Quantity    : 500
  Delivery    : 25 days
  Payment     : net_45
============================================================
```

---

## File structure

```
b2b_agent_system/
├── main.py                        # Entry point — run this
├── orchestrator.py                # Routes between all agents
├── requirements.txt
├── README.md
├── agents/
│   ├── verification_agent.py      # KYB + trust scoring
│   ├── negotiation_agent.py       # Multi-round deal negotiation
│   ├── contract_agent.py          # Contract generation
│   ├── monitor_agent.py           # SLA health monitoring
│   └── enforcement_agent.py      # Breach detection + penalties
├── utils/
│   ├── context_store.py           # Shared in-memory state
│   └── logger.py                  # Logging utility
└── contracts/                     # Auto-created — contracts saved here
```

---

## Customise for your business

### Change seller policy (in main.py)
```python
seller_policy = {
    "floor_price_per_unit": 4000,      # Your minimum acceptable price
    "list_price_per_unit": 4800,       # Your standard list price
    "max_discount_pct": 10,            # Maximum discount you'll give
    "min_delivery_days": 21,           # Fastest you can deliver
    "accepted_payment_terms": ["net_30", "net_45", "net_60"],
    "max_negotiation_rounds": 5        # Rounds before escalating
}
```

### Change the buyer RFQ (in main.py)
Edit the `rfq` dict to simulate different buyer scenarios.

### Production integrations to add
| Agent | What to integrate |
|---|---|
| Verification | Companies House API, GSTIN API, Experian B2B |
| Contract | DocuSign API, DigiLocker |
| Monitor | Your ERP / TMS / WMS API |
| Enforcement | Razorpay/Stripe Escrow, Email (SendGrid), WhatsApp Business API |

---

## Troubleshooting

**`ModuleNotFoundError: anthropic`**
→ Make sure your venv is activated and you ran `pip install -r requirements.txt`

**`AuthenticationError`**
→ Your API key is missing or wrong. Double-check `ANTHROPIC_API_KEY` is set.

**`JSONDecodeError`**
→ Rare — Claude occasionally returns unexpected text. Re-run; it's non-deterministic.
