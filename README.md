# 🚕 CabGPT — AI-Powered Cab Intelligence Platform
🌐 **Live Demo**: https://drive.google.com/file/d/1IZ-HWPgHX2t2bOx-I2jRSsSloQZUnmYR/view?usp=sharing
### Real-Time Fare Intelligence Across Ola, Uber & Rapido

CabGPT is an AI-powered cab fare comparison platform that combines local LLM intelligence, dynamic surge pricing, weather awareness, and route estimation to help users discover the most cost-effective ride options instantly.

Built using Flask, Python, and Ollama, CabGPT supports natural Hinglish conversations, intelligent fare recommendations, and AI-powered booking assistance—all while functioning even without premium API keys.

---

## ✨ Key Features

### ⚡ Instant Fare Comparison

Get real-time fare estimates across multiple providers without waiting for AI processing.

Supported Providers:

* Ola Mini
* Ola Auto
* Uber Go
* Uber Auto
* Rapido Bike
* Rapido Auto

---

### 🤖 AI Booking Assistant

Ask naturally in English or Hinglish:

**Example:**

> Meerut se Delhi kal subah 9 baje sabse sasta cab batao

CabGPT understands travel intent and recommends the most economical ride option.

---

### 🌦️ Smart Weather-Aware Pricing

The platform automatically considers:

* Rain conditions
* Peak traffic hours
* Dynamic surge multipliers

to provide more realistic fare estimates.

---

### 🗺️ Route Intelligence

Distance calculation supports:

#### Google Maps Mode

* Accurate road distance
* Route optimization

#### Offline Fallback Mode

* Geopy-based geodesic calculations
* No API key required

---

### 💬 AI Driver Simulation

After booking, users can chat with a simulated driver in Hinglish.

Example:

> Driver kaha tak pahucha?

> Bhai 5 minute mein pickup point pe pahunch raha hoon.

---

### 🔄 Intelligent Fallback System

If the selected LLM:

* Fails tool calling
* Hallucinates responses
* Returns incomplete results

CabGPT automatically executes the backend tool pipeline and delivers verified data.

---

## 🏗️ System Architecture

```text
Browser (HTML + CSS + JavaScript)
            │
            ▼
      Flask Backend
            │
 ┌──────────┴──────────┐
 │                     │
 ▼                     ▼
Quick Fare API      AI Chat API
(No LLM)            (Ollama LLM)
 │                     │
 └──────────┬──────────┘
            │
     Tool Execution Layer
            │
 ┌──────────┼───────────┬───────────┐
 │          │           │           │
 ▼          ▼           ▼           ▼
Geocoder   Maps      Weather     Fare Engine
```

---

## 🚀 Technology Stack

### Backend

* Python 3.10+
* Flask

### AI

* Ollama
* Llama 3.1
* Mistral
* Gemma 2
* Phi 3

### APIs

* OpenWeatherMap
* Google Maps API

### Fallback Services

* Geopy
* Nominatim

### Frontend

* HTML5
* CSS3
* JavaScript

---

## 📂 Project Structure

```text
CabGPT/
│
├── server.py
├── agent.py
├── prompts.py
├── config.py
├── requirements.txt
│
├── tools/
│   ├── geocoding.py
│   ├── maps.py
│   ├── weather.py
│   └── fare_calculator.py
│
├── templates/
│   └── index.html
│
└── static/
    ├── css/
    │   └── style.css
    │
    └── js/
        └── main.js
```

---

## ⚙️ Installation

### Clone Repository

```bash
git clone https://github.com/sauravsingh019/CabGPT.git
cd CabGPT
```

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Install Ollama

Download and install Ollama.

Pull a model:

```bash
ollama pull llama3.1
```

Alternative models:

```bash
ollama pull mistral
ollama pull gemma2
ollama pull phi3
```

---

## 🔑 Optional Configuration

Create a `.env` file:

```env
GOOGLE_MAPS_API_KEY=YOUR_KEY
OPENWEATHER_API_KEY=YOUR_KEY
```

CabGPT works without these keys using built-in fallback services.

---

## ▶️ Run Application

```bash
python server.py
```

Open:

```text
http://localhost:5000
```

---

## 🔌 API Endpoints

| Method | Endpoint         | Description              |
| ------ | ---------------- | ------------------------ |
| GET    | /                | Landing Page             |
| GET    | /api/models      | Available Ollama Models  |
| POST   | /api/quick_fare  | Instant Fare Calculation |
| POST   | /api/chat        | AI Assistant             |
| POST   | /api/driver_chat | Driver Simulation        |

---

## 💰 Fare Engine

### Base Pricing

| Service     | Base Fare | Per KM |
| ----------- | --------- | ------ |
| Ola Mini    | ₹30       | ₹12    |
| Ola Auto    | ₹25       | ₹10    |
| Uber Go     | ₹35       | ₹13    |
| Uber Auto   | ₹25       | ₹10    |
| Rapido Bike | ₹15       | ₹6     |
| Rapido Auto | ₹20       | ₹9     |

### Surge Logic

| Condition   | Multiplier |
| ----------- | ---------- |
| Normal      | 1.0×       |
| Peak Hours  | 1.3×       |
| Rain        | 1.2×       |
| Peak + Rain | 1.5×       |

---

## 🎯 Example Query

### Request

```json
{
  "query": "Meerut se Delhi kal subah 9 baje Rapido chahiye",
  "model_name": "llama3.1"
}
```

### Response

```json
{
  "provider": "Rapido Bike",
  "estimated_fare": "₹350-380",
  "weather": "Clear",
  "surge": "No"
}
```

---

## 🌟 Future Roadmap

* User Authentication
* Trip History Dashboard
* Voice-Based Booking
* Live Traffic Integration
* Fare Prediction Models
* Mobile Application
* PostgreSQL Support
* Docker Deployment

---

## 📄 License

MIT License

Feel free to use, modify, and distribute this project.

---

<div align="center">

### 🚕 Smarter Rides. Better Prices. Powered by AI.

Made with ❤️ using Flask, Python & Ollama

</div>
