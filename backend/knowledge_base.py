"""Local Knowledge & Dialogue Response Module for TARA.

Architecture:
Transformer DL Classifier
      │
      ├── (High confidence & Known intent) ──> Intent Response Handler
      └── (Low confidence OR UNKNOWN OR General query) ──> Built-in Local Knowledge Engine
"""

from __future__ import annotations

import logging
import re

logger = logging.getLogger("tara.knowledge_base")

# Built-in general knowledge bank for common open-ended and educational queries
KNOWLEDGE_BANK: dict[str, str] = {
    "what is machine learning": (
        "Machine Learning is a branch of artificial intelligence where algorithms learn patterns directly from data "
        "rather than following hardcoded rules. It powers technologies like recommendation engines, speech recognition, and computer vision."
    ),
    "explain backpropagation": (
        "Backpropagation is the fundamental training algorithm for artificial neural networks. It calculates the gradient "
        "of the loss function with respect to each weight using the chain rule of calculus, flowing errors backward from output to input to update parameters."
    ),
    "why are neural networks useful": (
        "Neural networks excel at modeling complex, non-linear relationships in unstructured data such as audio, images, and text. "
        "Their layered representation allows them to automatically extract hierarchical features without manual feature engineering."
    ),
    "what is deep learning": (
        "Deep Learning is a subset of machine learning based on multi-layered artificial neural networks. "
        "By stacking multiple processing layers, deep architectures can learn rich representations of data, enabling breakthroughs in generative AI and language understanding."
    ),
    "what is an attention mechanism": (
        "The Attention mechanism allows neural networks to focus dynamically on the most relevant parts of an input sequence. "
        "It forms the core foundation of Transformer architectures, replacing recurrence with self-attention across tokens."
    ),
    "what is a transformer": (
        "A Transformer is a deep learning architecture introduced in 'Attention Is All You Need' (2017). "
        "It processes entire sequences in parallel using multi-head self-attention and positional embeddings, powering modern models like BERT, GPT, and TARA."
    ),
    "what is python": (
        "Python is a versatile, high-level programming language known for its clean syntax and readability. "
        "It is the dominant language in data science and AI thanks to rich ecosystems like TensorFlow, PyTorch, and NumPy."
    ),
    "what is a black hole": (
        "A black hole is a region of spacetime where gravity is so intense that nothing—not even light—can escape its event horizon. "
        "They typically form when massive stars collapse at the end of their life cycles."
    ),
    "why is the sky blue": (
        "The sky appears blue due to Rayleigh scattering. Earth's atmosphere scatters shorter blue wavelengths of sunlight much more strongly "
        "than longer red wavelengths in all directions."
    ),
    "who painted the mona lisa": (
        "The Mona Lisa was painted by Leonardo da Vinci, likely between 1503 and 1519. "
        "It is one of the most famous paintings in the world and is currently housed in the Louvre Museum in Paris."
    ),
    "what is the capital of india": (
        "New Delhi is the capital of India."
    ),
    "what is the capital of france": (
        "Paris is the capital of France."
    ),
    "what is the largest planet": (
        "Jupiter is the largest planet in our solar system, with a mass more than twice that of all other planets combined."
    ),
    "how many bones in the human body": (
        "An adult human body has 206 bones."
    ),
    "what is the speed of light": (
        "The speed of light in a vacuum is approximately 299,792 kilometers per second (about 186,282 miles per second)."
    ),
    "what can you do": (
        "I'm TARA, your voice-enabled AI companion powered by a Deep Learning Transformer model. "
        "I can understand speech and text, explain Machine Learning, Deep Learning, and science concepts, "
        "answer academic and general knowledge questions, tell jokes, and chat with you in real-time."
    ),
    "tell me a joke": (
        "Why do programmers prefer dark mode? Because light attracts bugs!"
    ),
}

# Follow-up topics mappings
FOLLOW_UP_MAP: dict[str, dict[str, str]] = {
    "machine learning": {
        "types": (
            "The primary types of Machine Learning are: Supervised Learning (learning from labeled data), "
            "Unsupervised Learning (finding hidden patterns in unlabeled data), Semi-Supervised Learning, and Reinforcement Learning (learning through rewards and penalties)."
        ),
        "examples": (
            "Common examples of machine learning include email spam filtering, Netflix recommendations, voice assistants, and medical diagnostic imaging."
        ),
    },
    "deep learning": {
        "types": (
            "Common types of deep learning architectures include Convolutional Neural Networks (CNNs) for vision, "
            "Recurrent Neural Networks and LSTMs for sequences, and Transformer models for natural language and multi-modal tasks."
        ),
        "examples": (
            "Examples of deep learning include autonomous vehicle perception, ChatGPT, speech-to-text synthesis, and protein structure prediction."
        ),
    },
    "neural networks": {
        "types": (
            "Key types of neural networks include Feedforward Neural Networks (FNNs), Convolutional Neural Networks (CNNs), "
            "Recurrent Neural Networks (RNNs/LSTMs), and Transformer-based networks with self-attention."
        ),
    },
    "backpropagation": {
        "types": (
            "Variants of backpropagation include standard gradient descent, Stochastic Gradient Descent (SGD), Mini-batch Gradient Descent, and adaptive optimizers like Adam and RMSprop."
        ),
    },
}


def answer_general_query(query: str, last_topic: str | None = None) -> str:
    """Handle open-ended and follow-up questions using the built-in knowledge bank."""
    cleaned = (query or "").lower().strip()
    cleaned = re.sub(r"[^a-z0-9'\s]", " ", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()

    # 1. Check for contextual follow-up (e.g. "what are its types", "tell me its types")
    if any(m in cleaned for m in ["its types", "their types", "what are the types", "what types"]):
        if last_topic:
            topic_lower = last_topic.lower()
            for key, val_dict in FOLLOW_UP_MAP.items():
                if key in topic_lower:
                    if "types" in val_dict:
                        return val_dict["types"]
        return (
            "Depending on the subject you're asking about, the main types typically include supervised, "
            "unsupervised, and reinforcement paradigms in machine learning, or feedforward and recurrent structures in neural networks."
        )

    # 2. Direct knowledge lookup
    for key, answer in KNOWLEDGE_BANK.items():
        if key in cleaned or cleaned in key:
            return answer

    # 3. Keyword fuzzy matches for AI/ML/CS
    if "backprop" in cleaned:
        return KNOWLEDGE_BANK["explain backpropagation"]
    if "machine learning" in cleaned or "what is ml" in cleaned:
        return KNOWLEDGE_BANK["what is machine learning"]
    if "deep learning" in cleaned:
        return KNOWLEDGE_BANK["what is deep learning"]
    if "neural net" in cleaned:
        return KNOWLEDGE_BANK["why are neural networks useful"]
    if "transformer" in cleaned or "attention" in cleaned:
        return KNOWLEDGE_BANK["what is a transformer"]
    if "black hole" in cleaned:
        return KNOWLEDGE_BANK["what is a black hole"]
    if "sky blue" in cleaned:
        return KNOWLEDGE_BANK["why is the sky blue"]
    if "mona lisa" in cleaned:
        return KNOWLEDGE_BANK["who painted the mona lisa"]
    if "capital of india" in cleaned:
        return KNOWLEDGE_BANK["what is the capital of india"]
    if "capital of france" in cleaned:
        return KNOWLEDGE_BANK["what is the capital of france"]
    if "largest planet" in cleaned:
        return KNOWLEDGE_BANK["what is the largest planet"]
    if "speed of light" in cleaned:
        return KNOWLEDGE_BANK["what is the speed of light"]
    if "bones" in cleaned and "body" in cleaned:
        return KNOWLEDGE_BANK["how many bones in the human body"]
    if "joke" in cleaned or "funny" in cleaned:
        return KNOWLEDGE_BANK["tell me a joke"]
    if any(k in cleaned for k in ["what can you do", "what are your abilities", "what are ur abilities", "your abilities", "ur abilities", "your features", "your capabilities", "what do you do", "how can you help"]):
        return KNOWLEDGE_BANK["what can you do"]

    # 4. Polite conversational fallback
    return (
        "That's an interesting question! I may not have the answer in my built-in knowledge, "
        "but I can help with topics like machine learning, neural networks, programming concepts, "
        "and general science. Try asking me something specific!"
    )

