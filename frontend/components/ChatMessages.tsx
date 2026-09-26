'use client'

import React, { useEffect, useRef } from 'react'
import { Volume2, Trash2, Bot, User, Sparkles, MessageSquare } from 'lucide-react'

export interface ChatMessage {
  id: string
  role: 'user' | 'assistant'
  text: string
  intent?: string
  confidence?: number
  lowConfidence?: boolean
  sentiment?: {
    label: 'Positive' | 'Neutral' | 'Negative'
    score: number
    confidence: number
  }
}

interface ChatMessagesProps {
  messages: ChatMessage[]
  onClear: () => void
  onReplayVoice: (text: string) => void
  onSelectPrompt?: (prompt: string) => void
}

const STARTER_PROMPTS = [
  'What is machine learning?',
  'Explain backpropagation',
  'Tell me a joke',
  'Remind me to study at 6 pm',
]

export function ChatMessages({
  messages,
  onClear,
  onReplayVoice,
  onSelectPrompt,
}: ChatMessagesProps) {
  const scrollRef = useRef<HTMLDivElement>(null)

  // Auto-scroll on new message
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight
    }
  }, [messages])

  return (
    <div className="conversation-panel" aria-label="Conversation history">
      <div className="conversation-header">
        <div className="conv-title">
          <Sparkles size={14} className="sparkle-icon" />
          <span>Interactive Chat</span>
          {messages.length > 0 && (
            <span className="msg-counter">{messages.length}</span>
          )}
        </div>
        {messages.length > 0 && (
          <button
            onClick={onClear}
            className="clear-conv-btn"
            title="Clear chat history"
            aria-label="Clear chat history"
          >
            <Trash2 size={13} />
            <span>Clear</span>
          </button>
        )}
      </div>

      <div className="conversation-scroll" ref={scrollRef}>
        {messages.length === 0 ? (
          <div className="chat-empty-state">
            <div className="empty-icon-ring">
              <MessageSquare size={24} />
            </div>
            <h4>Welcome to TARA</h4>
            <p>Speak with your microphone or type a query. Ask about AI, Deep Learning, science, campus life, or anything you’re curious about.</p>
            {onSelectPrompt && (
              <div className="starter-prompts-grid">
                {STARTER_PROMPTS.map((prompt) => (
                  <button
                    key={prompt}
                    className="starter-chip"
                    onClick={() => onSelectPrompt(prompt)}
                  >
                    {prompt}
                  </button>
                ))}
              </div>
            )}
          </div>
        ) : (
          messages.map((msg) => (
            <div key={msg.id} className={`chat-bubble-row role-${msg.role}`}>
              <div className="bubble-avatar">
                {msg.role === 'user' ? <User size={13} /> : <Bot size={13} />}
              </div>

              <div className="bubble-content">
                <div className="bubble-text">
                  <p>{msg.text}</p>
                </div>

                {msg.role === 'assistant' && (
                  <div className="bubble-meta">
                    {msg.sentiment && (
                      <span
                        className={`sentiment-tag tag-${msg.sentiment.label.toLowerCase()}`}
                        title={`Sentiment: ${msg.sentiment.label}`}
                      >
                        {msg.sentiment.label}
                      </span>
                    )}

                    {msg.intent && msg.confidence !== undefined && (
                      <span
                        className="intent-tag"
                        title="TensorFlow Transformer Intent Classification"
                      >
                        {msg.intent} · {(msg.confidence * 100).toFixed(0)}%
                      </span>
                    )}

                    {msg.lowConfidence && (
                      <span className="low-conf-note">(low confidence)</span>
                    )}

                    <button
                      onClick={() => onReplayVoice(msg.text)}
                      className="replay-voice-btn"
                      title="Replay Voice (TTS)"
                      aria-label="Speak response"
                    >
                      <Volume2 size={13} />
                    </button>
                  </div>
                )}
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  )
}
