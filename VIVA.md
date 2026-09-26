# TARA — Viva Voce Questions & Answers
**Speech and Language Processing Lab Assessment**
**TARA — Transformer-based Audio & Response Assistant**

---

### 1. What is the end-to-end pipeline of TARA?
**Answer**:
1. User clicks the microphone and speaks an Indian-English query (`en-IN`).
2. Browser **Web Speech API** captures and converts speech into text in real-time.
3. The recognized text is displayed in the user chat bubble and sent via HTTP `POST /predict` with `session_id` to the **FastAPI** backend.
4. If the query is an elliptical follow-up (e.g. *"what are its types"*), the conversation repository resolves the context against the active session.
5. Text is cleaned, tokenized with a Keras `Tokenizer`, and padded to 24 tokens.
6. The **TensorFlow/Keras Transformer model** (`tara_transformer.keras`) performs a forward pass through Token & Position Embedding, Multi-Head Self-Attention, LayerNorm, Feed-Forward Network, Global Pooling, and Softmax layers to predict intent and confidence score across 19 classes.
7. A contextual response is selected from the predicted intent pool, or handled via the local knowledge bank for open-ended queries (e.g., machine learning concepts).
8. The JSON response is rendered in the assistant chat bubble, conversation state is persisted in the repository layer, and browser **SpeechSynthesis** speaks the answer aloud.

---

### 2. What is the exact Deep Learning architecture used?
**Answer**:
- **Input**: Integer token sequence of fixed length $24$.
- **Token & Position Embedding**: Vocabulary size $4000$, Embedding dimension $64$, combining learned token embeddings with learned position embeddings.
- **Transformer Encoder Block**:
  - **Multi-Head Self-Attention**: $4$ attention heads, key dimension $64$.
  - **Layer Normalization & Residual Dropout**: Rate $0.15$.
  - **Feed-Forward Network (FFN)**: Two Dense layers ($128$ units with ReLU $\rightarrow$ $64$ units).
  - **Second Layer Normalization & Residual Dropout**: Rate $0.15$.
- **Global Average Pooling 1D**: Condenses sequence representations into a fixed feature vector.
- **Dropout Layer**: Rate $0.20$ to prevent overfitting.
- **Dense Hidden Layer**: $64$ units with **ReLU** activation.
- **Output Dense Layer**: $19$ units with **Softmax** activation producing a probability distribution over the 19 dataset intent classes.

---

### 3. Was the speech recognizer trained on Svarah?
**Answer**:
No. Svarah (AI4Bharat) is an Indian-English ASR evaluation dataset included under `dataset/svarah/` for acoustic documentation. Live speech recognition is handled by the browser's native **Web Speech API** (`lang="en-IN"`), which provides real-time, low-latency recognition without requiring heavy server-side acoustic models.

---

### 4. What are the measured model metrics and dataset scope?
**Answer**:
- **Dataset**: `data/tara_dataset` containing 12,557 total utterances across 19 intent classes (train/val/test splits).
- **Official Test Split**: 1,259 test utterances (`tara_test.jsonl`).
- **Test Accuracy**: **99.52%**.
- **Macro Precision**: **99.57%**.
- **Macro Recall**: **99.46%**.
- **Macro F1-Score**: **99.50%**.
- **Weighted F1-Score**: **99.52%**.

---

### 5. How does the real acoustic pebble audio visualizer work?
**Answer**:
When the microphone is active:
1. `navigator.mediaDevices.getUserMedia()` streams audio to a Web Audio `AudioContext`.
2. An `AnalyserNode` captures real time-domain waveform data.
3. Root-Mean-Square (RMS) amplitude is computed in real-time ($ \text{RMS} = \sqrt{\frac{1}{N}\sum x_i^2} $).
4. Volume is normalized and applied across 19 rounded pebble bars with spring-like physics (fast attack, smooth damping).
5. When idle or stopped, all media tracks and audio contexts are explicitly closed to prevent memory leaks.

---

### 6. What happens if an unknown or out-of-domain question is asked?
**Answer**:
The model outputs a probability distribution. If the predicted tag is `UNKNOWN` or maximum confidence is below the threshold ($0.42$), or for open-ended queries (e.g. *"Tell me the quantum banana pizza price on mars"*), TARA falls back to a deterministic, local knowledge bank and helpful guidance response without relying on any external cloud LLM or internet API.

---

### 7. Why choose a Transformer over an LSTM/RNN for this architecture?
**Answer**:
- **Multi-Head Self-Attention**: Computes pairwise token interactions directly across all time-steps in parallel, avoiding the sequential bottleneck and vanishing gradient issues of recurrent networks.
- **Generalization**: Self-attention heads independently focus on syntax, intent markers, and domain keywords, yielding 99.52% test accuracy on complex natural phrasing variations.
- **Efficiency**: Full batch parallelization during training and rapid inference latency ($<15\text{ms}$) on commodity hardware.

---

### 8. How does TARA satisfy the 20-mark assessment requirements?
**Answer**:
1. **Speech Recognition**: Implemented via Web Speech API (`en-IN`).
2. **Deep Learning Chatbot Model**: Multi-Head Self-Attention Transformer neural network trained in TensorFlow/Keras.
3. **Display Recognized Speech & Response**: Distinct chat bubbles explicitly show both the user's transcript and TARA's reply.
4. **Interactive UI**: Desktop 2-column equal-height cards, companion robot with eye-tracking, and real acoustic visualizer.
5. **Deployment Ready**: Modular FastAPI + Next.js architecture configured for HTTPS cloud deployment.
