'use client'

import React, { useRef, useEffect, useCallback } from 'react'

const VISUALIZER_BARS = 19
const MIN_HEIGHT = 6
const MAX_HEIGHT = 34

interface AudioVisualizerProps {
  /** Live analyser node from the microphone audio context */
  analyserRef: React.RefObject<AnalyserNode | null>
  /** Whether the mic is actively capturing */
  active: boolean
  /** Whether the bot is speaking (different color scheme) */
  speaking?: boolean
  /** Callback to report current RMS amplitude back to parent */
  onRmsUpdate?: (rms: number) => void
}

export function AudioVisualizer({
  analyserRef,
  active,
  speaking = false,
  onRmsUpdate,
}: AudioVisualizerProps) {
  const barsRef = useRef<(HTMLSpanElement | null)[]>([])
  const animFrameRef = useRef<number | null>(null)
  // Smoothed level values (kept outside React state for performance)
  const smoothedLevels = useRef<number[]>(Array(VISUALIZER_BARS).fill(0.04))
  // Reusable typed arrays to avoid GC pressure in the animation loop
  const timeDataRef = useRef<Uint8Array | null>(null)
  const freqDataRef = useRef<Uint8Array | null>(null)
  const floatDataRef = useRef<Float32Array | null>(null)
  // Frame counter for throttling React state updates
  const frameCountRef = useRef(0)

  const animate = useCallback(() => {
    const analyser = analyserRef.current
    if (!analyser) {
      // No analyser — decay all bars to idle
      for (let i = 0; i < VISUALIZER_BARS; i++) {
        smoothedLevels.current[i] += (0.04 - smoothedLevels.current[i]) * 0.15
        const bar = barsRef.current[i]
        if (bar) {
          const h = MIN_HEIGHT + smoothedLevels.current[i] * (MAX_HEIGHT - MIN_HEIGHT)
          bar.style.height = `${h}px`
          bar.style.opacity = speaking ? '0.75' : '0.25'
        }
      }
      animFrameRef.current = requestAnimationFrame(animate)
      return
    }

    const fftBins = analyser.frequencyBinCount
    const timeLen = analyser.fftSize

    // Reuse typed arrays across frames to avoid GC pressure.
    // NOTE: time-domain length = fftSize, frequency length = fftBins.
    if (!floatDataRef.current || floatDataRef.current.length !== timeLen) {
      floatDataRef.current = new Float32Array(timeLen)
    }
    if (!timeDataRef.current || timeDataRef.current.length !== timeLen) {
      timeDataRef.current = new Uint8Array(timeLen)
    }
    if (!freqDataRef.current || freqDataRef.current.length !== fftBins) {
      freqDataRef.current = new Uint8Array(fftBins)
    }
    const floatData = floatDataRef.current!
    const timeData = timeDataRef.current!
    const freqData = freqDataRef.current!

    // Prefer float time-domain data (most precise, no quantization),
    // fall back to byte data if unavailable.
    let gotFloat = false
    try {
      if (typeof analyser.getFloatTimeDomainData === 'function') {
        analyser.getFloatTimeDomainData(floatData)
        gotFloat = true
      }
    } catch {
      gotFloat = false
    }
    if (!gotFloat) {
      analyser.getByteTimeDomainData(timeData)
      for (let i = 0; i < timeLen; i++) {
        floatData[i] = (timeData[i] - 128) / 128
      }
    }
    analyser.getByteFrequencyData(freqData)

    // ---- Actual microphone level: RMS -> dB ----
    // RMS of the raw waveform: sqrt(mean(x^2))
    let sumSquares = 0
    for (let i = 0; i < timeLen; i++) {
      const v = floatData[i]
      sumSquares += v * v
    }
    const rms = Math.sqrt(sumSquares / timeLen)
    // Convert to decibels (dBFS): 20 * log10(rms), silence floor at -60dB
    const MIN_DB = -60
    const MAX_DB = -12
    const db = rms > 0.00001 ? 20 * Math.log10(rms) : MIN_DB
    const clampedDb = Math.max(MIN_DB, Math.min(MAX_DB, db))
    const normalizedVolume = (clampedDb - MIN_DB) / (MAX_DB - MIN_DB)

    // Throttle React state updates to every 3 frames (~50ms at 60fps)
    frameCountRef.current++
    if (onRmsUpdate && frameCountRef.current % 3 === 0) {
      onRmsUpdate(normalizedVolume)
    }

    // Update each bar directly via DOM refs.
    // Bars are driven by the ACTUAL mic level (normalizedVolume from RMS dB):
    // louder voice -> higher bars, silence -> idle low bars.
    const isSilent = normalizedVolume < 0.06
    for (let i = 0; i < VISUALIZER_BARS; i++) {
      const centerRatio =
        Math.abs(i - (VISUALIZER_BARS - 1) / 2) / ((VISUALIZER_BARS - 1) / 2)
      const arch = 1 - Math.pow(centerRatio, 1.5) * 0.4

      let target = 0.04
      if (!isSilent) {
        // Spread bars across the voice band (first ~75% of spectrum)
        // so each bar shows real spectral energy, not the same low bins.
        const freqIdx = Math.min(
          freqData.length - 1,
          Math.floor(((i + 0.5) / VISUALIZER_BARS) * freqData.length * 0.75)
        )
        const freqNorm = freqData[freqIdx] / 255

        // Global loudness dominates; per-band spectrum adds organic variation.
        const bandBoost = 0.85 + freqNorm * 0.3
        target = Math.min(1, normalizedVolume * bandBoost * 1.25 * arch)
        if (target < 0.04) target = 0.04
      }

      // Spring smoothing
      const prev = smoothedLevels.current[i]
      const attackFactor = target > prev ? 0.36 : 0.2
      const next = prev + (target - prev) * attackFactor
      smoothedLevels.current[i] = next

      const bar = barsRef.current[i]
      if (bar) {
        const h = MIN_HEIGHT + next * (MAX_HEIGHT - MIN_HEIGHT)
        bar.style.height = `${h}px`
        bar.style.opacity = String(
          Math.max(0.5, Math.min(1, 0.45 + next * 0.8))
        )
      }
    }

    animFrameRef.current = requestAnimationFrame(animate)
  }, [analyserRef, speaking, onRmsUpdate])

  // Start/stop the animation loop based on `active` or `speaking`
  useEffect(() => {
    if (active || speaking) {
      // Start the loop
      animFrameRef.current = requestAnimationFrame(animate)
    } else {
      // Stop the loop and reset bars to idle
      if (animFrameRef.current) {
        cancelAnimationFrame(animFrameRef.current)
        animFrameRef.current = null
      }
      // Decay to idle smoothly with a final short animation burst
      let decayFrames = 0
      const decayMax = 20 // ~333ms at 60fps
      const decay = () => {
        let allIdle = true
        for (let i = 0; i < VISUALIZER_BARS; i++) {
          smoothedLevels.current[i] += (0.04 - smoothedLevels.current[i]) * 0.2
          if (Math.abs(smoothedLevels.current[i] - 0.04) > 0.005) allIdle = false
          const bar = barsRef.current[i]
          if (bar) {
            const h = MIN_HEIGHT + smoothedLevels.current[i] * (MAX_HEIGHT - MIN_HEIGHT)
            bar.style.height = `${h}px`
            bar.style.opacity = '0.25'
            bar.style.transform = 'scale(0.85)'
          }
        }
        decayFrames++
        if (!allIdle && decayFrames < decayMax) {
          requestAnimationFrame(decay)
        }
      }
      requestAnimationFrame(decay)
    }

    return () => {
      if (animFrameRef.current) {
        cancelAnimationFrame(animFrameRef.current)
        animFrameRef.current = null
      }
    }
  }, [active, speaking, animate])

  return (
    <div
      className={`pebble-visualizer-dock ${active ? 'dock-listening' : ''} ${
        speaking ? 'dock-speaking' : ''
      }`}
      aria-label="Real-time acoustic pebble visualizer"
    >
      <div className="pebbles-row">
        {Array.from({ length: VISUALIZER_BARS }, (_, idx) => (
          <span
            key={idx}
            ref={(el) => {
              barsRef.current[idx] = el
            }}
            className="pebble-unit"
            style={{
              height: `${MIN_HEIGHT}px`,
              transform: `scale(${active || speaking ? 1 : 0.85})`,
              opacity: 0.25,
            }}
          />
        ))}
      </div>
    </div>
  )
}
