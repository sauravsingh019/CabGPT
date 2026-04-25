# 🚕 CabGPT – Agentic AI Cab Booking & Pricing Assistant

A production-style AI agent demo built for AI/ML internship interviews.  
Uses **Gemini API** for NLP extraction, **Streamlit** for UI, and a modular
multi-step agentic pipeline — all in a single Python file.

---

## 🏗️ Agentic Pipeline

```
User Input
   ↓
Agent 1 · NLP Extraction    ← Gemini 1.5 Flash (LLM)
   ↓
Tool 2  · Distance Estimator ← Python dict lookup
   ↓
Tool 3  · Pricing Engine     ← Rule-based fare calculation
   ↓
Agent 4 · Decision Agent     ← Business logic (Mini/Sedan/SUV)
   ↓
Agent 5 · Response Builder   ← Streamlit UI renderer
```

---

## ⚡ Quick Start

### 1. Clone / download the project
```bash
cd cab_assistant
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Set your Gemini API Key
Get a free key at https://makersuite.google.com/app/apikey

**Option A – environment variable (recommended)**
```bash
export GEMINI_API_KEY="your_key_here"    # Linux / macOS
set GEMINI_API_KEY=your_key_here         # Windows CMD
$env:GEMINI_API_KEY="your_key_here"      # Windows PowerShell
```

**Option B – enter in the app sidebar**  
Just paste your key in the sidebar text box when the app opens.

### 4. Run the app
```bash
streamlit run app.py
```

Then open http://localhost:8501 in your browser.

---

## 💬 Sample Requests
- "Book a cab from Meerut to Delhi tomorrow at 9 AM"
- "I need a ride from Noida to Gurgaon at 6 PM today"
- "Get me a cab from Delhi to Agra on 2025-08-10 at 7 AM"

---

## 📐 Pricing Rules
| Cab Type | Rate     | Best For        |
|----------|----------|-----------------|
| Mini     | ₹10/km   | < 5 km          |
| Sedan    | ₹15/km   | 5–15 km         |
| SUV      | ₹20/km   | 15+ km          |

- Base fare: ₹50 flat
- Peak hours (8–11 AM, 5–9 PM): 1.2× multiplier

---

## 🗂️ Project Structure
```
cab_assistant/
├── app.py            # Full app (single file)
├── requirements.txt
└── README.md
```

---

## 🎯 Why This Is Agentic AI
Unlike a simple chatbot, this system:
1. **Decomposes** the user's request into sub-tasks
2. **Calls tools** (distance lookup, pricing engine) autonomously
3. **Makes decisions** (cab type selection) based on tool outputs
4. **Handles errors** at each step with clear feedback
5. **Renders results** with full transparency into the reasoning chain
