'use client'

/**
 * TARA Text-to-Speech voice selection.
 *
 * Why this file exists
 * --------------------
 * `window.speechSynthesis.getVoices()` is populated ASYNCHRONOUSLY by the
 * browser. On page load it returns an empty array and only fills in later,
 * firing a `voiceschanged` event. Calling it synchronously therefore yields
 * `[]`, the voice filter matches nothing, `utterance.voice` is left unset, and
 * the browser silently falls back to its own default system voice — which on
 * this machine is a deep/male voice (Microsoft David / Ravi). That was the
 * cause of TARA losing its cute, feminine, slightly robotic voice.
 *
 * This module makes voice selection deterministic and waits until the real
 * voice list is available.
 *
 * No external TTS service or dependency is used — this only picks from the
 * voices the browser / Web Speech API already exposes.
 */

/**
 * Ordered preference list, highest priority first, matched case-insensitively
 * against the full voice name. These are all feminine English voices that read
 * as a cute, slightly robotic AI companion.
 *
 * 'google uk english female' and 'microsoft zira' / 'zira' were verified to be
 * present on the target system and are the previously working TARA voices.
 */
const TARA_VOICE_PREFERENCES: readonly string[] = [
  // Previously working TARA voices (verified present on this system)
  'google uk english female',
  'microsoft zira',
  'zira',
  'samantha',
  'aria',
  'natural',
  // Other well-known feminine English voices
  'jenny',
  'heera',
  'victoria',
  'karen',
  'moira',
  'tessa',
  'fiona',
  'hazel',
  'susan',
  'vicki',
  'serena',
  'catherine',
  'carla',
  'linda',
  'zuzana',
  'paulina',
  // Generic feminine markers, checked last
  'female',
  'woman',
]

/**
 * Voices that must never be chosen, because TARA is a feminine companion.
 *
 * These use word-boundary matching on purpose: `\bmale\b` matches
 * "Google UK English Male" but correctly does NOT match
 * "Google UK English Female" (where "male" is glued to "fe").
 */
const MALE_VOICE_PATTERN =
  /\b(male|man|men|boy|david|mark|ravi|daniel|alex|fred|george|guy|thomas|james|richard|brian|ryan|christopher|diego|juan|luca|maged|xander|arnold|grandpa|oliver|arthur|jorge|ricardo)\b/i

function isMaleVoice(voice: SpeechSynthesisVoice): boolean {
  return MALE_VOICE_PATTERN.test(voice.name)
}

function isEnglish(voice: SpeechSynthesisVoice): boolean {
  return voice.lang.toLowerCase().startsWith('en')
}

/**
 * Deterministically choose TARA's voice from the available voices.
 *
 * Order of resolution:
 *  1. First entry of TARA_VOICE_PREFERENCES present (exact match, then substring).
 *  2. Any non-male English voice, preferring en-IN (TARA's recognition locale),
 *     then local/offline voices, then alphabetical for stability.
 *  3. Any English voice at all, so speech still works.
 *
 * Returns `null` only when there are no English voices whatsoever.
 */
export function selectTaraVoice(
  voices: readonly SpeechSynthesisVoice[]
): SpeechSynthesisVoice | null {
  const english = voices.filter(isEnglish)
  if (english.length === 0) return null

  // 1. Explicit, ordered preference list.
  for (const preference of TARA_VOICE_PREFERENCES) {
    const exact = english.find((v) => v.name.toLowerCase() === preference)
    if (exact && !isMaleVoice(exact)) return exact

    const partial = english.find(
      (v) => v.name.toLowerCase().includes(preference) && !isMaleVoice(v)
    )
    if (partial) return partial
  }

  // 2. Deterministic feminine-preferring fallback: never the browser default.
  const nonMale = english.filter((v) => !isMaleVoice(v))
  if (nonMale.length > 0) {
    return [...nonMale].sort((a, b) => {
      // en-IN first (matches TARA's `recognition.lang = 'en-IN'`).
      const aIn = a.lang.toLowerCase() === 'en-in' ? 0 : 1
      const bIn = b.lang.toLowerCase() === 'en-in' ? 0 : 1
      if (aIn !== bIn) return aIn - bIn
      // Then local/offline voices (no network dependency).
      if (a.localService !== b.localService) return a.localService ? -1 : 1
      return a.name.localeCompare(b.name)
    })[0]
  }

  // 3. Last resort: only male voices are installed. Speech still works, but be
  //    explicit about it rather than silently using a random default.
  console.warn(
    '[TARA TTS] No feminine English voice found; available voices:',
    english.map((v) => `${v.name} (${v.lang})`)
  )
  return [...english].sort((a, b) => a.name.localeCompare(b.name))[0]
}

let voicesPromise: Promise<SpeechSynthesisVoice[]> | null = null
let cachedVoice: SpeechSynthesisVoice | null = null
let listeningForVoices = false

/**
 * Invalidate cached voice state after `voiceschanged`.
 *
 * Both the selected voice AND the cached voice list are dropped, so a late
 * voice load (which is the normal case on Chrome) is picked up on the next
 * `speakText` call instead of staying stuck on the initial empty array.
 */
export function resetTaraVoiceCache(): void {
  cachedVoice = null
  voicesPromise = null
}

/**
 * Resolve once the browser has actually populated its voice list.
 *
 * Handles all three loading paths:
 *  - voices already available (fast path, no delay),
 *  - the `voiceschanged` event,
 *  - a short polling fallback for browsers that never fire the event.
 */
export function loadVoices(): Promise<SpeechSynthesisVoice[]> {
  if (typeof window === 'undefined' || !('speechSynthesis' in window)) {
    return Promise.resolve([])
  }
  if (voicesPromise) return voicesPromise

  // Register the permanent re-check listener exactly once.
  if (!listeningForVoices) {
    listeningForVoices = true
    window.speechSynthesis.addEventListener('voiceschanged', resetTaraVoiceCache)
  }

  voicesPromise = new Promise<SpeechSynthesisVoice[]>((resolve) => {
    const synth = window.speechSynthesis

    const immediate = synth.getVoices()
    if (immediate.length > 0) {
      resolve(immediate)
      return
    }

    let settled = false
    let poll: ReturnType<typeof setInterval> | undefined
    let timeout: ReturnType<typeof setTimeout> | undefined

    const finish = () => {
      if (settled) return
      settled = true
      synth.removeEventListener('voiceschanged', finish)
      if (poll !== undefined) clearInterval(poll)
      if (timeout !== undefined) clearTimeout(timeout)
      // Final read after the event, so we capture the completed list.
      resolve(synth.getVoices())
    }

    synth.addEventListener('voiceschanged', finish)

    // Polling fallback — some builds populate voices without firing the event.
    poll = setInterval(() => {
      if (synth.getVoices().length > 0) finish()
    }, 250)

    // Never block speech indefinitely on a machine with no voices installed.
    timeout = setTimeout(finish, 3000)
  })

  return voicesPromise
}

/**
 * Get TARA's voice, waiting for the browser voice list if necessary.
 * The result is cached, so repeat calls are cheap and synchronous-ish.
 */
export async function getTaraVoice(): Promise<SpeechSynthesisVoice | null> {
  if (cachedVoice) return cachedVoice
  const voices = await loadVoices()
  cachedVoice = selectTaraVoice(voices)
  return cachedVoice
}

/**
 * Guard token so a speech request cancelled while waiting for the voice list
 * does not start speaking late.
 */
let speakToken = 0

export function nextSpeakToken(): number {
  speakToken += 1
  return speakToken
}

export function isSpeakTokenCurrent(token: number): boolean {
  return token === speakToken
}

/** Cancel any in-flight or currently active TARA speech. */
export function cancelSpeech(): void {
  nextSpeakToken()
  if (typeof window !== 'undefined' && 'speechSynthesis' in window) {
    window.speechSynthesis.cancel()
  }
}
