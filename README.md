🚀 TrustChain – Autonomous AI B2B Operations Platform

An intelligent multi-agent system that automates B2B deal workflows — from negotiation to enforcement — reducing manual effort, risk, and inefficiencies.

📌 Overview

TrustChain is an AI-powered platform designed for SMEs (Small & Medium Enterprises) to streamline and automate business transactions.

It leverages multiple AI agents to handle:

Deal intake
Negotiation
Trust verification
Contract generation
Enforcement & monitoring

👉 The goal: Zero-friction, secure, and autonomous B2B operations

⚡ Key Features
🤖 Multi-Agent System
🧠 Negotiation Agent – Handles deal discussions
🔍 Verification Agent – Validates parties & trust signals
📄 Contract Agent – Generates smart agreements
⚖️ Enforcement Agent – Ensures compliance
📊 Monitoring Agent – Tracks live deal status
🔐 Trust & Risk Management
Detects suspicious behavior
Verifies counterparties
Maintains audit logs
📈 Real-Time Dashboard
Built with Streamlit
View active deals, alerts, and analytics
🧾 Automated Workflows
End-to-end deal lifecycle automation
Reduces manual intervention
🏗️ Tech Stack
Layer	Technology Used
Frontend	Streamlit
Backend	FastAPI + Uvicorn
AI Engine	Anthropic API
Database	SQLite
Language	Python
Config	python-dotenv
📂 Project Structure
ai-b2b-agent/
│
├── agents/              # AI agents (negotiation, verification, etc.)
├── utils/               # Helper utilities
├── templates/           # HTML templates
├── contracts/           # Generated contracts
│
├── app.py               # Streamlit dashboard
├── main.py              # Backend entry point
├── orchestrator.py      # Agent coordination logic
│
├── requirements.txt
├── README.md
└── .gitignore
⚙️ Installation & Setup
1️⃣ Clone the repository
git clone https://github.com/Saisradha/TrustChain.git
cd TrustChain
2️⃣ Create virtual environment
python -m venv venv
source venv/bin/activate   # Linux/Mac
venv\Scripts\activate      # Windows
3️⃣ Install dependencies
pip install -r requirements.txt
4️⃣ Set environment variables

Create a .env file:

ANTHROPIC_API_KEY=your_api_key_here
▶️ Run the Project
Run backend (FastAPI)
uvicorn main:app --reload
Run frontend (Streamlit)
streamlit run app.py
🧠 How It Works
User submits a deal
Orchestrator activates AI agents
Agents:
Negotiate terms
Verify trust
Generate contract
System monitors execution in real-time
🎯 Use Cases
🏢 SME B2B transactions
📦 Supplier negotiations
🤝 Contract automation
🔐 Fraud detection & trust scoring
🚀 Future Enhancements
Blockchain-based contract validation
Multi-language negotiation support
Advanced ML risk scoring
Real-time alerts & notifications
👩‍💻 Author

Sradha

Passionate about AI, automation & real-world problem solving
Building impactful tech for business and society
