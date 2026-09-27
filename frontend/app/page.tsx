'use client'

import React, { useState, useEffect, useRef, useCallback } from 'react'
import {
  Mic,
  MicOff,
  Send,
  VolumeX,
  Sparkles,
  HelpCircle,
  Cpu,
  Radio,
} from 'lucide-react'
import { DeskCompanionRobot, RobotState } from '../components/DeskCompanionRobot'
import { AudioVisualizer } from '../components/AudioVisualizer'
import { ChatMessages, ChatMessage } from '../components/ChatMessages'
import { predictIntent, checkBackendHealth, API_BASE_URL } from '../lib/api'
import { getTaraVoice, nextSpeakToken, isSpeakTokenCurrent, cancelSpeech } from '../lib/ttsVoice'



const EXAMPLE_QUERIES = [
  'What is machine learning?',
  'Explain backpropagation',
  'Why are neural networks useful?',
  'Tell me a joke',
  'Remind me to study at 6 pm',
  'What time is it in Tokyo?',
  'What is the weather in Mumbai?',
  'What can you do?',
]

// The `SpeechRecognitionInstance`, `SpeechRecognitionEvent` and
// `SpeechRecognitionErrorEvent` types (and the `window.SpeechRecognition` /
// `window.webkitSpeechRecognition` entry points) are declared globally in
// `frontend/types/speech-recognition.d.ts`, because TypeScript's lib.dom.d.ts
// only ships the low-level result types for the Web Speech API.

export default function Home() {
  // Application & Robot State
  const [robotState, setRobotState] = useState<RobotState>('idle')
  const [pointer, setPointer] = useState({ x: 0, y: 0 })
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [inputMessage, setInputMessage] = useState('')
  const [interimTranscript, setInterimTranscript] = useState('')
  const [isRecording, setIsRecording] = useState(false)
  const [isLoading, setIsLoading] = useState(false)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)
  const [backendReady, setBackendReady] = useState<boolean | null>(null)
  const [showExamples, setShowExamples] = useState(false)
  const [currentRms, setCurrentRms] = useState(0)
  const [sessionId] = useState(() => crypto.randomUUID ? crypto.randomUUID() : String(Date.now()))

  // Audio & Speech References
  const recognitionRef = useRef<SpeechRecognitionInstance | null>(null)
  const audioContextRef = useRef<{
    context: AudioContext
    source: MediaStreamAudioSourceNode
    analyser: AnalyserNode
    stream: MediaStream
  } | null>(null)
  const analyserNodeRef = useRef<AnalyserNode | null>(null)
  const animFrameRef = useRef<number | null>(null)
  const lastAssistantResponse = useRef<string>('')
  const currentRequestId = useRef(0)

  // 1. Initial Health Check
  useEffect(() => {
    let isMounted = true
    const checkStatus = async () => {
      try {
        const health = await checkBackendHealth()
        if (isMounted) {
          setBackendReady(health.model_ready)
        }
      } catch {
        if (isMounted) {
          setBackendReady(false)
        }
      }
    }
    checkStatus()
    const interval = setInterval(checkStatus, 15000)
    return () => {
      isMounted = false
      clearInterval(interval)
    }
  }, [])

  // 2. Mouse Tracking for Robot Eyes
  useEffect(() => {
    let animId = 0
    let targetX = 0
    let targetY = 0

    const handleMouseMove = (e: MouseEvent) => {
      targetX = e.clientX - window.innerWidth / 2
      targetY = e.clientY - window.innerHeight / 2
    }

    const animateEyes = () => {
      setPointer((prev) => ({
        x: prev.x + (targetX - prev.x) * 0.08,
        y: prev.y + (targetY - prev.y) * 0.08,
      }))
      animId = requestAnimationFrame(animateEyes)
    }

    window.addEventListener('mousemove', handleMouseMove)
    animateEyes()

    return () => {
      window.removeEventListener('mousemove', handleMouseMove)
      cancelAnimationFrame(animId)
    }
  }, [])

  // 2b. Synthesized Sound Effect for Mic Activation (Matches Ear Lighting Up Motif)
  const playMicChime = useCallback(() => {
    try {
      const AudioCtxClass =
        window.AudioContext ||
        (window as unknown as { webkitAudioContext: typeof AudioContext }).webkitAudioContext
      if (!AudioCtxClass) return

      const ctx = new AudioCtxClass()
      const now = ctx.currentTime

      // High-tech two-tone ascending sonic chime (e.g., 587.33 Hz D5 -> 880 Hz A5)
      const osc1 = ctx.createOscillator()
      const osc2 = ctx.createOscillator()
      const gainNode = ctx.createGain()

      osc1.type = 'sine'
      osc2.type = 'sine'

      // Frequency glide: D5 (587.33Hz) up to A5 (880Hz) to represent 'waking up / ears lit'
      osc1.frequency.setValueAtTime(587.33, now)
      osc1.frequency.exponentialRampToValueAtTime(880, now + 0.12)

      // Harmonics shimmer at an octave higher
      osc2.frequency.setValueAtTime(1174.66, now + 0.04)
      osc2.frequency.exponentialRampToValueAtTime(1760, now + 0.18)

      // Gentle, crisp envelope with fast attack and warm decay
      gainNode.gain.setValueAtTime(0.001, now)
      gainNode.gain.linearRampToValueAtTime(0.18, now + 0.02)
      gainNode.gain.exponentialRampToValueAtTime(0.001, now + 0.32)

      osc1.connect(gainNode)
      osc2.connect(gainNode)
      gainNode.connect(ctx.destination)

      osc1.start(now)
      osc2.start(now + 0.04)

      osc1.stop(now + 0.32)
      osc2.stop(now + 0.32)

      setTimeout(() => {
        if (ctx.state !== 'closed') {
          void ctx.close()
        }
      }, 400)
    } catch (e) {
      console.warn('Mic chime sound effect failed:', e)
    }
  }, [])

  // 3. Audio Cleanup (Prevents leaks and dangling AudioContext instances)
  const stopAudioCapture = useCallback(() => {
    if (animFrameRef.current) {
      cancelAnimationFrame(animFrameRef.current)
      animFrameRef.current = null
    }
    analyserNodeRef.current = null
    if (audioContextRef.current) {
      try {
        audioContextRef.current.source.disconnect()
        audioContextRef.current.stream.getTracks().forEach((track) => track.stop())
        if (audioContextRef.current.context.state !== 'closed') {
          audioContextRef.current.context.close()
        }
      } catch (e) {
        console.warn('Audio cleanup exception:', e)
      }
      audioContextRef.current = null
    }
    setCurrentRms(0)
  }, [])

  // 4. Start Microphone & Web Audio Analyser
  const startAudioCapture = useCallback(async (): Promise<boolean> => {
    // Tear down any previous instance first
    stopAudioCapture()

    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: { echoCancellation: true, noiseSuppression: true, autoGainControl: true },
        video: false,
      })

      const AudioCtxClass =
        window.AudioContext ||
        (window as unknown as { webkitAudioContext: typeof AudioContext }).webkitAudioContext
      const context = new AudioCtxClass()
      if (context.state === 'suspended') {
        await context.resume()
      }
      const analyser = context.createAnalyser()
      analyser.fftSize = 256
      analyser.smoothingTimeConstant = 0.65

      const source = context.createMediaStreamSource(stream)
      source.connect(analyser)

      audioContextRef.current = { context, source, analyser, stream }
      // Expose analyser to the AudioVisualizer component via ref
      analyserNodeRef.current = analyser

      return true
    } catch (err) {
      console.warn('Microphone audio capture warning:', err)
      return false
    }
  }, [stopAudioCapture])

  // 5. Text-to-Speech Engine (Cute & Friendly Companion Voice)
  // NOTE: pitch/rate/volume are the original TARA settings and are preserved
  // unchanged. Only voice *selection* was fixed (see lib/ttsVoice.ts).
  const speakText = useCallback((text: string) => {
    if (typeof window === 'undefined' || !('speechSynthesis' in window) || !text) return

    window.speechSynthesis.cancel()

    const token = nextSpeakToken()

    // Resolve TARA's voice BEFORE building the utterance.
    // `getVoices()` is empty on first paint, so this waits for the real list
    // (voiceschanged / polling) instead of silently using the deep male default.
    void getTaraVoice().then((voice) => {
      // Bail out if the user cancelled (or started something else) meanwhile.
      if (!isSpeakTokenCurrent(token)) return
      if (typeof window === 'undefined' || !('speechSynthesis' in window)) return

      const utterance = new SpeechSynthesisUtterance(text)

      if (voice) {
        utterance.voice = voice
      }

      utterance.lang = utterance.voice?.lang || 'en-IN'
      utterance.pitch = 1.18
      utterance.rate = 1.15
      utterance.volume = 0.9

      utterance.onstart = () => {
        setRobotState('speaking')
      }

      utterance.onend = () => {
        setRobotState('success')
        setTimeout(() => {
          setRobotState('idle')
        }, 700)
      }

      utterance.onerror = () => {
        setRobotState('idle')
      }

      window.speechSynthesis.speak(utterance)
    })
  }, [])

  // 6. Voice Command Interpreter
  const handleVoiceCommand = useCallback(
    (query: string): boolean => {
      const clean = query.toLowerCase().replace(/[^a-z0-9\s]/g, ' ').replace(/\s+/g, ' ').trim()

      if (['clear chat', 'clear the chat', 'reset chat', 'clean chat'].includes(clean)) {
        setMessages([])
        cancelSpeech()
        setRobotState('idle')
        return true
      }

      if (['repeat that', 'repeat', 'say that again', 'replay'].includes(clean)) {
        if (lastAssistantResponse.current) {
          speakText(lastAssistantResponse.current)
        }
        return true
      }

      if (['stop speaking', 'stop talking', 'be quiet', 'shut up', 'silence'].includes(clean)) {
        cancelSpeech()
        setRobotState('idle')
        return true
      }

      if (['show examples', 'example questions', 'show me examples'].includes(clean)) {
        setShowExamples(true)
        const guide = 'Here are a few example questions you can ask me.'
        setMessages((prev) => [
          ...prev,
          { id: String(Date.now()), role: 'assistant', text: guide },
        ])
        speakText(guide)
        return true
      }

      if (['help', 'show help', 'how to use this', 'instructions'].includes(clean)) {
        const guide = 'Tap the microphone to speak or type below. Ask about courses, exams, attendance, hostel, fees, or library.'
        setMessages((prev) => [
          ...prev,
          { id: String(Date.now()), role: 'assistant', text: guide },
        ])
        speakText(guide)
        return true
      }

      return false
    },
    [speakText]
  )

  // 7. Message Submission (to Backend Deep Learning LSTM Classifier)
  const processUserMessage = useCallback(
    async (rawText: string) => {
      const query = rawText.trim()
      if (!query || isLoading) return

      // Handle voice commands instantly
      if (handleVoiceCommand(query)) {
        setInputMessage('')
        setInterimTranscript('')
        stopAudioCapture()
        setIsRecording(false)
        return
      }

      const reqId = ++currentRequestId.current
      setInputMessage('')
      setInterimTranscript('')
      stopAudioCapture()
      setIsRecording(false)
      setErrorMessage(null)

      // Add user message to conversation list
      const userMsg: ChatMessage = {
        id: `user-${Date.now()}-${Math.random()}`,
        role: 'user',
        text: query,
      }
      setMessages((prev) => [...prev, userMsg])

      setIsLoading(true)
      setRobotState('thinking')

      try {
        const result = await predictIntent(query, sessionId)
        if (reqId !== currentRequestId.current) return

        lastAssistantResponse.current = result.response

        const assistantMsg: ChatMessage = {
          id: `asst-${Date.now()}-${Math.random()}`,
          role: 'assistant',
          text: result.response,
          intent: result.intent,
          confidence: result.confidence,
          lowConfidence: Boolean(result.below_threshold),
          sentiment: result.sentiment,
        }

        setMessages((prev) => [...prev, assistantMsg])
        setBackendReady(true)

        // Trigger TTS & companion speaking animation
        speakText(result.response)
      } catch (err) {
        console.error('Inference error:', err)
        const errorText =
          err instanceof Error && err.name === 'TimeoutError'
            ? 'TARA took too long to respond. Please check your backend connection.'
            : `Sorry, I can't reach my brain right now. Please check that the backend server is running.`

        setErrorMessage(errorText)
        setRobotState('error')

        // Display error message in chat history so the user is informed
        const errorMsg: ChatMessage = {
          id: `asst-err-${Date.now()}`,
          role: 'assistant',
          text: errorText,
        }
        setMessages((prev) => [...prev, errorMsg])
        speakText("Sorry, I can't reach my brain right now. Please check the server.")
      } finally {
        setIsLoading(false)
      }
    },
    [handleVoiceCommand, isLoading, speakText, stopAudioCapture, sessionId]
  )

  // 8. Speech Recognition Toggle
  const toggleListening = useCallback(async () => {
    // 1. Immediately terminate/interrupt any ongoing chatbot speech or in-flight processing
    cancelSpeech()
    // Invalidate any in-flight backend inference response
    currentRequestId.current += 1
    setIsLoading(false)

    if (isRecording) {
      if (recognitionRef.current) {
        recognitionRef.current.stop()
      }
      stopAudioCapture()
      setIsRecording(false)
      setRobotState('idle')
      return
    }

    // Play high-tech ear-lighting acoustic chime
    playMicChime()

    setErrorMessage(null)
    setRobotState('listening')

    const SpeechRec: SpeechRecognitionConstructor | undefined =
      window.SpeechRecognition || window.webkitSpeechRecognition

    if (!SpeechRec) {
      setErrorMessage('Speech recognition is not supported in this browser. Please use Chrome, Edge, or type your message.')
      setRobotState('error')
      return
    }

    // Initialize real-time audio visualizer capture
    void startAudioCapture()

    const recognition: SpeechRecognitionInstance = new SpeechRec()
    recognition.continuous = false
    recognition.interimResults = true
    recognition.lang = 'en-IN'

    recognition.onstart = () => {
      setIsRecording(true)
      setRobotState('listening')
      setErrorMessage(null)
    }

    recognition.onresult = (event: SpeechRecognitionEvent) => {
      let finalStr = ''
      let interimStr = ''

      for (let i = event.resultIndex; i < event.results.length; i++) {
        const transcript = event.results[i][0].transcript
        if (event.results[i].isFinal) {
          finalStr += transcript
        } else {
          interimStr += transcript
        }
      }

      setInterimTranscript(interimStr)

      if (finalStr.trim()) {
        try {
          recognition.stop()
        } catch {
          // Ignore stop error if already stopped
        }
        void processUserMessage(finalStr)
      }
    }

    recognition.onerror = (event: SpeechRecognitionErrorEvent) => {
      const err = event.error || ''
      console.warn('SpeechRecognition event status:', err)

      // 1. Normal non-fatal speech lifecycle events
      if (err === 'no-speech' || err === 'aborted') {
        stopAudioCapture()
        setIsRecording(false)
        setInterimTranscript('')
        setRobotState('idle')
        return
      }

      // 2. Clear, actionable error messages for real issues
      let msg = 'Speech recognition issue. Please try speaking again or type your question.'
      if (err === 'not-allowed' || err === 'service-not-allowed') {
        msg = 'Microphone access was blocked. Please click the lock/camera icon in your address bar and allow microphone permissions.'
      } else if (err === 'audio-capture') {
        msg = 'No microphone input detected. Please ensure your microphone is plugged in and not in exclusive use by another app.'
      } else if (err === 'network') {
        msg = 'Speech recognition service is unreachable. Please check your internet connection or type your question.'
      }

      setErrorMessage(msg)
      setRobotState('error')
      stopAudioCapture()
      setIsRecording(false)
    }

    recognition.onend = () => {
      stopAudioCapture()
      setIsRecording(false)
      setInterimTranscript('')
      setRobotState((prev) => (prev === 'listening' ? 'idle' : prev))
    }

    recognitionRef.current = recognition
    setIsRecording(true)

    try {
      recognition.start()
    } catch (startErr) {
      console.warn('Speech recognition start error:', startErr)
      setErrorMessage('Could not initialize speech recognition. Please try again.')
      setRobotState('error')
      stopAudioCapture()
      setIsRecording(false)
    }
  }, [isRecording, playMicChime, processUserMessage, startAudioCapture, stopAudioCapture])

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      stopAudioCapture()
      if (recognitionRef.current) {
        recognitionRef.current.stop()
      }
      cancelSpeech()
    }
  }, [stopAudioCapture])

  // Dynamic status headline
  const getStatusHeadline = () => {
    switch (robotState) {
      case 'listening':
        return 'Listening to your voice...'
      case 'thinking':
        return 'Evaluating with Transformer Neural Net...'
      case 'speaking':
        return 'TARA Speaking:'
      case 'success':
        return 'Glad I could help!'
      case 'error':
        return 'Connection Notice'
      default:
        return 'TARA Companion'
    }
  }

  return (
    <main className="voxbuddy-desktop-shell">
      {/* Ambient Lighting Orbs */}
      <div className="ambient-glow glow-cyan" />
      <div className="ambient-glow glow-amber" />

      {/* Top Application Header */}
      <header className="app-topbar">
        <div className="brand-logo">
          <div className="brand-icon">
            <Sparkles size={18} />
          </div>
          <div className="brand-info">
            <span className="brand-title">TARA</span>
            <span className="brand-subtitle">Transformer-based Audio & Response Assistant</span>
          </div>
        </div>

        <div className="topbar-actions">
          <div
            className={`status-chip ${
              backendReady === true
                ? 'status-online'
                : backendReady === false
                ? 'status-offline'
                : 'status-checking'
            }`}
            title={`Backend endpoint: ${API_BASE_URL}`}
          >
            <span className="status-dot" />
            <span className="status-text">
              {backendReady === true
                ? 'AI Core Online'
                : backendReady === false
                ? 'AI Core Offline'
                : 'Connecting...'}
            </span>
          </div>
        </div>
      </header>

      {/* Master 2-Column Responsive Workspace */}
      <div className="workspace-container">
        {/* ========================================================
            LEFT COLUMN: PRIMARY CHATBOT INTERFACE (~70% Width)
            ======================================================== */}
        <section className="chatbot-primary-pane" aria-label="Chatbot interface">
          {/* Scrollable Chat Area */}
          <div className="chat-viewport">
            <ChatMessages
              messages={messages}
              onClear={() => setMessages([])}
              onReplayVoice={speakText}
              onSelectPrompt={(p) => void processUserMessage(p)}
            />
          </div>

          {/* Tactile Control Bar */}
          <div className="controls-hub">
            <button
              id="mic-trigger-btn"
              className={`tactile-mic-button ${isRecording ? 'mic-active' : ''}`}
              onClick={() => void toggleListening()}
              aria-label={isRecording ? 'Stop listening' : 'Start speaking'}
            >
              <div className="mic-inner">
                {isRecording ? <MicOff size={20} /> : <Mic size={20} />}
              </div>
              <span className="mic-label">
                {isRecording ? 'Listening (Click to Stop)' : 'Speak to TARA'}
              </span>
            </button>

            {robotState === 'speaking' && (
              <button
                className="tactile-icon-button"
                onClick={() => {
                  cancelSpeech()
                  setRobotState('idle')
                }}
                title="Stop speaking"
                aria-label="Stop speech output"
              >
                <VolumeX size={16} />
                <span>Silence</span>
              </button>
            )}

            <button
              className={`tactile-icon-button ${showExamples ? 'active-toggle' : ''}`}
              onClick={() => setShowExamples((prev) => !prev)}
              title="Toggle question examples"
              aria-label="Toggle examples"
            >
              <HelpCircle size={16} />
              <span>{showExamples ? 'Hide Hints' : 'Quick Hints'}</span>
            </button>
          </div>

          {/* Collapsible Example Prompts Rack */}
          {showExamples && (
            <div className="example-chips-rack">
              <span className="chips-label">Frequently Asked Topics:</span>
              <div className="chips-grid">
                {EXAMPLE_QUERIES.map((q) => (
                  <button
                    key={q}
                    className="query-chip"
                    onClick={() => void processUserMessage(q)}
                    disabled={isLoading}
                  >
                    {q}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Text Input Composer */}
          <form
            className="tactile-composer"
            onSubmit={(e) => {
              e.preventDefault()
              void processUserMessage(inputMessage)
            }}
          >
            <input
              type="text"
              className="composer-input"
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              placeholder="Ask about AI, Deep Learning, science, campus, courses, or anything..."
              disabled={isLoading}
            />
            <button
              type="submit"
              className="composer-send-btn"
              disabled={isLoading || !inputMessage.trim()}
              aria-label="Send message"
            >
              <Send size={16} />
            </button>
          </form>

          {/* Voice Command Hints */}
          <div className="voice-commands-footer">
            <span className="v-cmd-title">Voice commands:</span>
            <code>clear chat</code>
            <code>repeat that</code>
            <code>stop speaking</code>
            <code>show examples</code>
            <code>help</code>
          </div>
        </section>

        {/* ========================================================
            RIGHT COLUMN: ROBOT FACE COMPANION POD (~30% Width)
            ======================================================== */}
        <aside className="robot-companion-pane" aria-label="Robot face companion">
          <div className="companion-pod-card">
            {/* Status Header Badge */}
            <div className={`companion-state-badge badge-${robotState}`}>
              <Cpu size={12} className="state-icon" />
              <span>{getStatusHeadline()}</span>
            </div>

            {/* Pure Face-Only Robot Character */}
            <div className="robot-face-stage">
              <DeskCompanionRobot
                state={robotState}
                pointer={pointer}
                audioLevel={currentRms}
              />
            </div>

            {/* Real-time Pebble Audio Visualizer directly underneath robot */}
            <AudioVisualizer
              analyserRef={analyserNodeRef}
              active={isRecording}
              speaking={robotState === 'speaking'}
              onRmsUpdate={setCurrentRms}
            />

            {/* Live Audio / Transcript Monitor Box */}
            <div className="robot-feedback-box">
              {interimTranscript ? (
                <div className="live-transcript">
                  <span className="transcript-tag">Hearing:</span>
                  <p className="interim-text">"{interimTranscript}..."</p>
                </div>
              ) : robotState === 'error' && errorMessage ? (
                <p className="status-error-text">{errorMessage}</p>
              ) : (
                <div className="companion-idle-hint">
                  <Radio size={14} className="radio-pulse-icon" />
                  <p>
                    {robotState === 'listening'
                      ? 'Listening to microphone...'
                      : robotState === 'thinking'
                      ? 'Transformer classifying intent...'
                      : robotState === 'speaking'
                      ? 'Streaming audio response...'
                      : 'Sitting quietly on your desk'}
                  </p>
                </div>
              )}
            </div>
          </div>
        </aside>
      </div>

      {/* App Footer */}
      <footer className="app-footer">
        <span>TARA — Transformer-based Audio & Response Assistant · TensorFlow Transformer Architecture</span>
      </footer>
    </main>
  )
}
