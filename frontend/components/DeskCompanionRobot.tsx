'use client'

import React, { useEffect, useState, useRef } from 'react'

export type RobotState = 'idle' | 'listening' | 'thinking' | 'speaking' | 'success' | 'error'

interface DeskCompanionRobotProps {
  state: RobotState
  pointer: { x: number; y: number }
  audioLevel?: number // Real-time 0.0 - 1.0 audio RMS for ear glow reactivity
}

export function DeskCompanionRobot({ state, pointer, audioLevel = 0.05 }: DeskCompanionRobotProps) {
  // Blinking system: natural organic intervals (2 - 4.5s) with double blinks
  const [blinkPhase, setBlinkPhase] = useState<'open' | 'blink'>('open')
  const blinkTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const prevStateRef = useRef<RobotState>(state)

  // Natural organic blinking loop
  useEffect(() => {
    const scheduleNextBlink = () => {
      const delay = 2200 + Math.random() * 2600 // 2.2s - 4.8s
      blinkTimerRef.current = setTimeout(() => {
        setBlinkPhase('blink')

        setTimeout(() => {
          setBlinkPhase('open')
          // 22% chance of a quick organic double-blink
          if (Math.random() < 0.22) {
            setTimeout(() => {
              setBlinkPhase('blink')
              setTimeout(() => {
                setBlinkPhase('open')
                scheduleNextBlink()
              }, 110)
            }, 90)
          } else {
            scheduleNextBlink()
          }
        }, 130)
      }, delay)
    }

    scheduleNextBlink()
    return () => {
      if (blinkTimerRef.current) clearTimeout(blinkTimerRef.current)
    }
  }, [])

  // Sharp-turn blink: trigger natural blink when turning to 'listening'
  useEffect(() => {
    if (state === 'listening' && prevStateRef.current !== 'listening') {
      const turnTimer = setTimeout(() => {
        setBlinkPhase('blink')
        setTimeout(() => setBlinkPhase('open'), 120)
      }, 140)
      prevStateRef.current = state
      return () => clearTimeout(turnTimer)
    }
    prevStateRef.current = state
  }, [state])

  // Restrained, smooth eye mouse tracking (max ±6px X, ±4px Y)
  const eyeX = Math.max(-6, Math.min(6, pointer.x / 60))
  const eyeY = Math.max(-4, Math.min(4, pointer.y / 80))

  // Face rotation toward user/cursor (small restrained 3D tilt)
  const faceRotateY = state === 'listening' ? -4 : Math.max(-5, Math.min(5, pointer.x / 140))
  const faceRotateX = state === 'listening' ? 2 : Math.max(-3, Math.min(3, -pointer.y / 160))

  // Ear illumination reactivity from real microphone volume
  const earGlowOpacity = state === 'listening' 
    ? Math.min(1, 0.4 + audioLevel * 1.5) 
    : state === 'speaking' 
    ? 0.7 
    : 0.2

  return (
    <div
      className={`desk-robot-face-scene state-${state}`}
      style={
        {
          '--eye-x': `${eyeX}px`,
          '--eye-y': `${eyeY}px`,
          '--face-rot-x': `${faceRotateX}deg`,
          '--face-rot-y': `${faceRotateY}deg`,
          '--ear-glow': earGlowOpacity,
        } as React.CSSProperties
      }
      aria-label={`TARA Robot Companion Face in ${state} state`}
    >
      {/* Soft Contact Drop Shadow */}
      <div className="face-contact-shadow" />

      {/* Robot Face Pod (3D Floating Head Unit) */}
      <div className="robot-face-pod">
        {/* Subtle Crown Antenna / Sensor Notch */}
        <div className="face-crown-sensor">
          <span className="crown-stem" />
          <span className="crown-orb" />
        </div>

        {/* Left Audio Ear Sensor */}
        <div className="face-ear ear-left">
          <span className="ear-core" />
          <span className="ear-pulse-ring" />
        </div>

        {/* Right Audio Ear Sensor */}
        <div className="face-ear ear-right">
          <span className="ear-core" />
          <span className="ear-pulse-ring" />
        </div>

        {/* Main 3D Ceramic/Matte Shell */}
        <div className="face-chassis">
          {/* Glass Specular Reflection Highlight */}
          <div className="face-glass-specular" />

          {/* OLED Curved Visor Screen */}
          <div className="face-visor-screen">
            {/* Expressive OLED Digital Eyes */}
            <div className={`face-eyes-group blink-${blinkPhase}`}>
              {/* Left Eye */}
              <div className="oled-eye eye-left">
                <div className="eye-iris-ring">
                  <div className="eye-pupil" />
                  <div className="eye-specular-dot" />
                </div>
              </div>

              {/* Right Eye */}
              <div className="oled-eye eye-right">
                <div className="eye-iris-ring">
                  <div className="eye-pupil" />
                  <div className="eye-specular-dot" />
                </div>
              </div>
            </div>

            {/* Temporary Acoustic Waveform Mouth (ONLY active during speaking) */}
            {state === 'speaking' && (
              <div className="speaker-waveform-mouth" aria-hidden="true">
                <span className="wave-bar wb-1" />
                <span className="wave-bar wb-2" />
                <span className="wave-bar wb-3" />
                <span className="wave-bar wb-4" />
                <span className="wave-bar wb-5" />
              </div>
            )}

            {/* Cheerful Blush / Cheek Glow during speaking & success */}
            <div className="face-cheek cheek-left" />
            <div className="face-cheek cheek-right" />
          </div>
        </div>

        {/* Desk Base Floating Ring */}
        <div className="face-bottom-cushion" />
      </div>
    </div>
  )
}
