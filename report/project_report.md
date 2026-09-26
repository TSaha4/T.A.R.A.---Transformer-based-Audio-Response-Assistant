# TARA — Transformer-based Audio & Response Assistant
**Course Assessment Project Report**  
*Speech and Language Processing Lab Assessment*

---

## 1. Title & Abstract
**Project Title**: TARA — Transformer-based Audio & Response Assistant  
**Abstract**:  
TARA is a complete voice-first interactive assistant combining speech processing, natural language understanding, and deep learning. The system accepts spoken voice input in Indian-accented English (`en-IN`), converts speech to text using the browser Web Speech API, processes the query through a Deep Learning Multi-Head Self-Attention Transformer Classifier in TensorFlow/Keras, selects an appropriate response from a verified knowledge pool covering 19 distinct intent classes, visibly displays both the recognized speech and chatbot response, and articulates the reply using SpeechSynthesis (TTS). An acoustic pebble audio visualizer underneath the companion robot tracks real microphone RMS amplitude. Pluggable session persistence allows seamless tracking and contextual follow-up handling.

---

## 2. Objective
- Develop, implement, and deploy an online voice-enabled chatbot using speech recognition and deep learning.
- Accept speech input from the user via the microphone and convert it to text in real-time.
- Classify intents using a deep Transformer neural network across 19 diverse intent categories with high accuracy.
- Support multi-turn contextual inquiries and follow-ups.
- Clearly display both the recognized user speech and the generated chatbot response in the interactive UI.
- Provide real-time acoustic feedback via an audio visualizer and animated companion states.
- Prepare the application for online deployment over public HTTPS.

---

## 3. Problem Statement
Users require immediate, natural assistance regarding computer science concepts, machine learning principles, general trivia, tasks, reminders, and daily productivity. Traditional rule-based chatbots often fail to understand colloquial phrasing or handle open-ended variations. TARA addresses this by providing a unified voice and text interface powered by a custom Multi-Head Self-Attention Transformer deep learning model trained on the `tara_dataset`.

---

## 4. System Architecture

```text
       [ User Spoken Voice ]
                 │
                 ▼
     ┌───────────────────────┐
     │   Web Speech API      │  (en-IN Speech Recognition)
     │   getUserMedia / RMS  │  (Web Audio AnalyserNode → Pebble Visualizer)
     └───────────┬───────────┘
                 │ (Recognized Transcript)
                 ▼
     ┌───────────────────────┐
     │  Chat UI Presentation │  (Displays "You: <Recognized Speech>")
     └───────────┬───────────┘
                 │ HTTP POST /predict {"message": "...", "session_id": "..."}
                 ▼
     ┌───────────────────────┐
     │    FastAPI Backend    │
     │ 1. Text Sanitization  │
     │ 2. Context Resolution │  (Pluggable BaseConversationRepository)
     │ 3. Tokenizer (4000)   │
     │ 4. Pad Sequence (24)  │
     │ 5. Transformer Model  │  (Token & Pos Embed + Self-Attention)
     │ 6. Softmax Prediction │
     └───────────┬───────────┘
                 │ JSON Response { intent, confidence, response, sentiment }
                 ▼
     ┌───────────────────────┐
     │ Frontend Presentation │  (Displays "TARA: <Chatbot Response>")
     │   & Voice Synthesis   │  (SpeechSynthesisUtterance TTS)
     └───────────────────────┘
```

---

## 5. Deep Learning Model Architecture

The core intent classification engine is a custom Multi-Head Self-Attention Transformer neural network built in TensorFlow 2.18 / Keras (`tara_transformer.keras`):

1. **Input Layer**: Accepts integer sequences padded to length $L = 24$.
2. **Token & Position Embedding Layer**:
   - Vocabulary size: $V = 4000$.
   - Embedding dimension: $D = 64$.
   - Sums token embedding vectors with learned positional embedding vectors.
3. **Transformer Encoder Block**:
   - Multi-Head Attention with $4$ heads and key dimension $64$.
   - Layer Normalization + Residual Dropout ($p = 0.15$).
   - Feed-Forward Network: Dense ($128$ units, ReLU) $\rightarrow$ Dense ($64$ units).
   - Second Layer Normalization + Residual Dropout ($p = 0.15$).
4. **Global Average Pooling 1D**: Condenses sequence output into fixed-length latent representation.
5. **Dropout Layer**: Dropout probability $p = 0.20$ to prevent overfitting.
6. **Dense Hidden Layer**: $64$ units with Rectified Linear Unit ($\text{ReLU}$) activation.
7. **Output Dense Layer**: $19$ units with $\text{Softmax}$ activation:
   $$\hat{y}_i = \frac{e^{z_i}}{\sum_{j=1}^{19} e^{z_j}}$$

---

## 6. Experimental Results & Metrics

Evaluation was conducted against the official held-out test split `data/tara_dataset/tara_test.jsonl` (1,259 test samples):

| Metric | Measured Value |
|---|---|
| **Test Accuracy** | **99.52%** |
| **Macro Precision** | **99.57%** |
| **Macro Recall** | **99.46%** |
| **Macro F1-Score** | **99.50%** |
| **Weighted F1-Score** | **99.52%** |
| **Intent Classes** | 19 distinct classes |
| **Total Dataset Size** | 12,557 utterances |
| **Sequence Length** | 24 tokens |
| **Confidence Threshold** | 0.42 |

---

## 7. Acoustic Pebble Audio Visualizer

Underneath the desk companion robot, a real acoustic visualizer reacts dynamically to the user's voice input:
- The browser opens an audio stream via `navigator.mediaDevices.getUserMedia({ audio: true })`.
- An `AnalyserNode` with FFT size 256 captures 128 time-domain bins.
- Root-Mean-Square (RMS) amplitude is computed every frame.
- Spring-damped height scaling renders 19 organic pill bars that bounce in authentic correlation with vocal loudness.

---

## 8. Pluggable Conversation Persistence

TARA implements a clean repository pattern (`BaseConversationRepository`) supporting both in-memory caching and persistent SQLite storage. Each exchange is tagged with an optional `session_id`, enabling the backend to resolve follow-up inquiries (e.g. asking *"what are its types"* after inquiring about *"machine learning"*).

---

## 9. Conclusion
TARA satisfies all objectives of the Speech and Language Processing laboratory assessment:
1. Low-latency voice capture via Web Speech API (`en-IN`).
2. Deep learning classification with TensorFlow/Keras Transformer across 19 intents with 99.52% accuracy.
3. Transparent dual-turn presentation of recognized user speech and synthesized response.
4. Real-time acoustic visualizer with tactile responsive feedback.
5. Production-grade containerization and cloud-ready FastAPI backend.
