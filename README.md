# TARA — Transformer-based Audio & Response Assistant

> **Speech and Language Processing Lab Project**  
> An end-to-end voice-enabled interactive assistant combining real-time Speech Recognition, Deep Learning (Transformer Multi-Head Self-Attention Intent Classification), and Text-to-Speech synthesis with a cute desk companion robot, real-time acoustic visualizer, and pluggable conversation persistence.

---

## 🌟 Key Features

1. **Voice Input & Real-Time Speech Recognition**:
   - Built with the browser Web Speech API configured for Indian English (`lang="en-IN"`).
   - Real-time display of recognized user voice queries alongside the assistant's responses.
2. **Deep Learning Intent Classifier**:
   - Neural network built with TensorFlow/Keras: `Token & Position Embedding → Multi-Head Self-Attention Transformer Block → GlobalAveragePooling1D → Dropout → Dense(ReLU) → Dense(Softmax)`.
   - Trained on the official `data/tara_dataset` across 19 intent classes with 99.52% test accuracy, confidence scoring, and local knowledge fallback.
3. **Conversational Context & State Management**:
   - Handles multi-turn queries and contextual follow-ups (e.g. asking *"what are its types"* after discussing machine learning).
   - Session ID propagation with pluggable database persistence abstraction (`BaseConversationRepository` with InMemory and SQLite support).
4. **Real Acoustic Pebble Visualizer**:
   - 19 rounded tactile pebble bars that dynamically react to real microphone volume (RMS amplitude via Web Audio API `AnalyserNode`).
   - Zero fake animation loops; spring-damped physical height modulation.
5. **Desktop & Mobile Responsive UI**:
   - Equal-height 2-column desktop layout (Left: Chatbot card, Right: Robot Companion pod).
   - Expressive face-only companion robot with natural organic blinking, user eye-tracking, and state reactions (Idle, Listening, Thinking, Speaking).
6. **Full Text Input & Voice Commands**:
   - Keyboard input with instant submission.
   - Built-in local voice commands: `clear chat`, `repeat that`, `stop speaking`, `show examples`, `help`.
7. **Text-to-Speech (TTS)**:
   - Clear, friendly synthesized voice output with replay controls.

---

## 📐 Deep Learning Architecture

```text
Input (24 integer tokens)
       │
       ▼
Token & Position Embedding (maxlen: 24, vocab: 4000, embed_dim: 64)
       │
       ▼
Transformer Block:
 ├── Multi-Head Self-Attention (4 heads, key_dim: 64)
 ├── Layer Normalization + Residual Dropout (0.15)
 ├── Feed-Forward Network (Dense 128 ReLU → Dense 64)
 └── Layer Normalization + Residual Dropout (0.15)
       │
       ▼
Global Average Pooling 1D
       │
       ▼
Dropout (0.20)
       │
       ▼
Dense Hidden Layer (64 units, ReLU)
       │
       ▼
Dense Output Layer (19 classes, Softmax)
```

### Measured Model Metrics (`backend/model/evaluation_metrics.json`):
- **Model**: TARA Transformer (`tara_transformer.keras`)
- **Dataset**: `data/tara_dataset` (12,557 utterances total across 19 intents)
- **Test Samples**: 1,259 utterances (`tara_test.jsonl`)
- **Test Accuracy**: **99.52%**
- **Macro Precision**: **99.57%**
- **Macro Recall**: **99.46%**
- **Macro F1-Score**: **99.50%**
- **Weighted F1-Score**: **99.52%**

---

## 📁 Repository Structure

```text
lab_project/
├── backend/
│   ├── app.py                 # FastAPI REST Service (Endpoints: /health, /predict, /history)
│   ├── config.py              # TARA identity and hyperparameter constants
│   ├── predict.py             # Inference pipeline: Preprocessing → Tokenizer → Transformer Model → Response
│   ├── llm_fallback.py        # Local Knowledge Bank & Contextual Follow-up Engine (DL-only, No external LLM)
│   ├── sentiment.py           # Supporting lexicon-based sentiment analysis
│   ├── evaluate_test_split.py # Evaluator against official tara_test.jsonl
│   ├── test_tara_system.py    # Verification test suite for inference pipeline
│   ├── requirements.txt       # Python dependencies (FastAPI, TensorFlow/Keras, etc.)
│   ├── db/
│   │   └── repository.py      # Pluggable repository interface (InMemory / SQLite)
│   └── model/
│       ├── tara_transformer.keras  # Trained Multi-Head Self-Attention Transformer model
│       ├── tokenizer.pkl      # Pickled Keras Tokenizer
│       ├── label2id.json      # 19 intent class label-to-id mapping
│       └── evaluation_metrics.json # Official test evaluation metrics (99.52% accuracy)
├── database/
│   └── README.md              # Database integration architecture and migration documentation
├── frontend/
│   ├── app/
│   │   ├── page.tsx           # Main Next.js interface with audio pipeline, state & session management
│   │   └── globals.css        # Responsive CSS Grid styling, visualizer, & animations
│   ├── components/
│   │   ├── DeskCompanionRobot.tsx  # Face-only companion robot unit with eye-tracking
│   │   ├── AudioVisualizer.tsx     # Real-time acoustic pebble audio visualizer
│   │   └── ChatMessages.tsx        # Conversation viewport displaying user & assistant messages
│   ├── lib/
│   │   └── api.ts             # Centralized API service connecting to backend /predict & /health
│   ├── package.json           # Node.js dependencies (Next.js 16, React 19, Lucide icons)
│   └── .env.local             # Local environment configuration (NEXT_PUBLIC_API_URL)
├── report/
│   └── project_report.md      # Detailed academic project report for TARA
├── VIVA.md                    # 2-3 minute viva demonstration walkthrough guide
└── README.md
```

---

## 🚀 Running the Project Locally

### 1. Prerequisites
- **Python**: 3.11 or 3.12
- **Node.js**: 18+ or 20+
- **Browser**: Google Chrome, Microsoft Edge, or Chromium-based browser (for Web Speech API support)

### 2. Backend Setup
```bash
# From repository root
# Create virtual environment (if not already created)
python -m venv .venv

# Activate virtual environment
# Windows (PowerShell):
.\.venv\Scripts\Activate.ps1
# macOS/Linux:
source .venv/bin/activate

# Install dependencies
pip install -r backend/requirements.txt

# (Optional) Retrain model
python backend/train.py

# Start FastAPI server
python -m uvicorn app:app --app-dir backend --host 127.0.0.1 --port 5000
```

The backend will start at `http://127.0.0.1:5000`. Test health at `http://127.0.0.1:5000/health`.

### 3. Frontend Setup
```bash
# In a second terminal window
cd frontend

# Install Node dependencies
npm install

# Start Next.js development server
npm run dev
```

Open your browser at `http://localhost:3000`.

---

## 📡 API Contract

### 1. Health Check
- **Endpoint**: `GET /health`
- **Response**:
```json
{
  "status": "ok",
  "app": "TARA",
  "model_ready": true
}
```

### 2. Intent Prediction
- **Endpoint**: `POST /predict`
- **Request Body**:
```json
{
  "message": "What is deep learning?",
  "session_id": "optional-uuid-string"
}
```
- **Response Body**:
```json
{
  "intent": "ai_concepts",
  "raw_intent": "ai_concepts",
  "confidence": 0.9998,
  "response": "Deep learning is a subset of machine learning based on artificial neural networks...",
  "below_threshold": false,
  "sentiment": {
    "label": "Neutral",
    "score": 0,
    "confidence": 0.5
  },
  "app": "TARA",
  "threshold": 0.42,
  "session_id": "optional-uuid-string"
}
```

### 3. Conversation History
- **Endpoint**: `GET /history?session_id=...`
- **Response**: List of prior user and assistant messages for that session.

---

## 🌐 Public Cloud Deployment Guide

### Backend Deployment (Render / Railway)
1. Deploy the `backend/` directory as a Web Service.
2. Set the build command: `pip install -r backend/requirements.txt`.
3. Set the start command: `uvicorn app:app --app-dir backend --host 0.0.0.0 --port $PORT`.
4. Add environment variables:
   - `CORS_ORIGINS`: `https://your-frontend.vercel.app`
5. Verify public endpoint: `https://your-backend.onrender.com/health`.

### Frontend Deployment (Vercel)
1. Import the repository into Vercel and set the Root Directory to `frontend`.
2. Add environment variable:
   - `NEXT_PUBLIC_API_URL`: `https://your-backend.onrender.com` (no trailing slash).
3. Deploy and access the public HTTPS URL.
4. Open the deployed website in Chrome/Edge, allow microphone permission, and talk to TARA!

---

## 🎤 2-Minute Viva Demonstration Flow

1. **Open the Application**: Show the dual-card desktop layout and the status badge (`AI Core Online`).
2. **Voice Demonstration**: Click **"Speak to TARA"**, allow microphone access, and say:
   > *"What is deep learning?"*
3. **Point out the requirements**:
   - **Real acoustic pebbles** bouncing in response to vocal amplitude underneath the robot.
   - **Recognized speech displayed** in the user bubble: *"What is deep learning?"*.
   - **LSTM Deep Learning Prediction**: Intent tag shows `ai_concepts · 100%`.
   - **Assistant Response**: Displayed clearly in the assistant bubble.
   - **Speech Synthesis (TTS)**: TARA speaks the response automatically.
4. **Follow-up / Context Demonstration**:
   > *"What are its types?"*
   - Show how TARA resolves the context using the active session and explains machine learning / deep learning types.
5. **Campus Query Demonstration**: Type or speak:
   > *"What courses are offered?"*
   - Show intent `courses · 100%` and the distinct campus curriculum response.
6. **Fallback Demonstration**: Say or type:
   > *"Tell me the quantum banana pizza price on mars"*
   - Show confidence score and explicit fallback response.
