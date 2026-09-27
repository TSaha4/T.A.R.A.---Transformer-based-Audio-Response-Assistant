/**
 * Web Speech API (SpeechRecognition) type declarations.
 *
 * TypeScript's `lib.dom.d.ts` only declares the low-level result types
 * (`SpeechRecognitionAlternative`, `SpeechRecognitionResult`,
 * `SpeechRecognitionResultList`). It does NOT declare the `SpeechRecognition`
 * constructor, its `Window` entry points, or the `SpeechRecognition*Event`
 * types, so this file fills those gaps locally.
 *
 * No runtime code is emitted from this file — it only augments the global
 * scope for the compiler. Nothing here uses `any`.
 */

/**
 * Error codes reported by `SpeechRecognitionErrorEvent.error`.
 */
type SpeechRecognitionErrorCode =
  | 'aborted'
  | 'audio-capture'
  | 'bad-grammar'
  | 'language-not-supported'
  | 'network'
  | 'no-speech'
  | 'not-allowed'
  | 'service-not-allowed'
  | 'phonation'
  | 'language-unavailable'
  | 'no-download'
  | 'not-installed'
  | 'voice-unavailable'
  | 'aborted-silent'
  | (string & {})

/**
 * Event fired on `SpeechRecognition.onresult`.
 */
interface SpeechRecognitionEvent extends Event {
  readonly resultIndex: number
  readonly results: SpeechRecognitionResultList
}

/**
 * Event fired on `SpeechRecognition.onerror`.
 */
interface SpeechRecognitionErrorEvent extends Event {
  readonly error: SpeechRecognitionErrorCode
  readonly message: string
}

/**
 * A live `SpeechRecognition` instance (created via
 * `new SpeechRecognition()` or `new webkitSpeechRecognition()`).
 *
 * Every member below is actually used by `frontend/app/page.tsx`, except the
 * `on*` handlers that are part of the standard surface area and are declared
 * so the object can be treated as a complete recognition session.
 */
interface SpeechRecognitionInstance extends EventTarget {
  /* ---- Configuration ---- */
  lang: string
  continuous: boolean
  interimResults: boolean
  maxAlternatives: number

  /* ---- Lifecycle methods ---- */
  start(): void
  stop(): void
  abort(): void

  /* ---- Event handlers ---- */
  onstart: ((this: SpeechRecognitionInstance, ev: Event) => unknown) | null
  onaudiostart: ((this: SpeechRecognitionInstance, ev: Event) => unknown) | null
  onspeechstart: ((this: SpeechRecognitionInstance, ev: Event) => unknown) | null
  onresult: ((this: SpeechRecognitionInstance, ev: SpeechRecognitionEvent) => unknown) | null
  onnomatch: ((this: SpeechRecognitionInstance, ev: SpeechRecognitionEvent) => unknown) | null
  onerror: ((this: SpeechRecognitionInstance, ev: SpeechRecognitionErrorEvent) => unknown) | null
  onend: ((this: SpeechRecognitionInstance, ev: Event) => unknown) | null
}

/**
 * Constructor signature exposed as `window.SpeechRecognition` and
 * `window.webkitSpeechRecognition`.
 */
interface SpeechRecognitionConstructor {
  new (): SpeechRecognitionInstance
  prototype: SpeechRecognitionInstance
}

interface Window {
  /** Standard (unprefixed) constructor — Chrome/Edge. */
  SpeechRecognition?: SpeechRecognitionConstructor
  /** Legacy WebKit-prefixed constructor — Safari/older Chrome. */
  webkitSpeechRecognition?: SpeechRecognitionConstructor
}
