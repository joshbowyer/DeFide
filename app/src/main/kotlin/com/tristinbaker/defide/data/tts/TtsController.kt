package com.tristinbaker.defide.data.tts

import android.content.Context
import android.os.Bundle
import android.speech.tts.TextToSpeech
import android.speech.tts.UtteranceProgressListener
import dagger.hilt.android.qualifiers.ApplicationContext
import java.util.Locale
import javax.inject.Inject
import kotlinx.coroutines.flow.MutableSharedFlow
import kotlinx.coroutines.flow.SharedFlow
import kotlinx.coroutines.flow.asSharedFlow

sealed interface TtsEvent {
    data class SequenceCompleted(val key: String) : TtsEvent
    data class SequenceInterrupted(val key: String) : TtsEvent
}

/**
 * Thin wrapper around [TextToSpeech] for narrating Rosary content.
 * Not a singleton — each owner (e.g. RosaryViewModel) gets its own instance
 * and is responsible for calling [shutdown] when done.
 */
class TtsController @Inject constructor(
    @ApplicationContext private val context: Context,
) {
    private var tts: TextToSpeech? = null
    private var isReady = false
    // Set once the init callback reports failure; from then on speak() fails fast
    // instead of queueing forever, since Android only fires the init callback once.
    private var initFailed = false
    private var pendingSpeak: PendingSpeak? = null
    private var lastAppliedLanguageTag: String? = null

    // Utterance ids are "$key#$partIndex"; these track the LAST part's utterance id
    // for the sequence currently in flight, so onDone can tell it apart from earlier parts.
    private var currentSequenceKey: String? = null
    private var currentSequenceLastUtteranceId: String? = null

    private data class PendingSpeak(val parts: List<String>, val languageCode: String, val key: String)

    private val _events = MutableSharedFlow<TtsEvent>(extraBufferCapacity = 4)
    val events: SharedFlow<TtsEvent> = _events.asSharedFlow()

    private fun ensureEngine() {
        if (tts != null) return
        tts = TextToSpeech(context) { status ->
            isReady = status == TextToSpeech.SUCCESS
            initFailed = !isReady
            if (isReady) {
                tts?.setOnUtteranceProgressListener(object : UtteranceProgressListener() {
                    override fun onStart(utteranceId: String?) {}

                    override fun onDone(utteranceId: String?) {
                        if (utteranceId != null && utteranceId == currentSequenceLastUtteranceId) {
                            currentSequenceKey?.let { _events.tryEmit(TtsEvent.SequenceCompleted(it)) }
                        }
                    }

                    @Deprecated("Deprecated in Java")
                    override fun onError(utteranceId: String?) {
                        utteranceId?.let { _events.tryEmit(TtsEvent.SequenceInterrupted(keyOf(it))) }
                    }

                    override fun onStop(utteranceId: String?, interrupted: Boolean) {
                        utteranceId?.let { _events.tryEmit(TtsEvent.SequenceInterrupted(keyOf(it))) }
                    }
                })
                pendingSpeak?.let { speakNow(it.parts, it.languageCode, it.key) }
            } else {
                // Engine failed to bind (e.g. no default TTS engine configured on the
                // device) — report the queued request as interrupted rather than
                // leaving the caller's "isSpeaking" state stuck forever.
                pendingSpeak?.let { _events.tryEmit(TtsEvent.SequenceInterrupted(it.key)) }
            }
            pendingSpeak = null
        }
    }

    private fun keyOf(utteranceId: String): String = utteranceId.substringBeforeLast('#')

    private fun applyLanguage(languageCode: String) {
        val engine = tts ?: return
        if (lastAppliedLanguageTag == languageCode) return
        val locale = localeFor(languageCode)
        val result = engine.setLanguage(locale)
        if (result == TextToSpeech.LANG_MISSING_DATA || result == TextToSpeech.LANG_NOT_SUPPORTED) {
            // No installed voice for this language — speak with whatever voice
            // the engine already defaults to rather than blocking narration.
            engine.defaultVoice?.let { engine.voice = it }
        }
        lastAppliedLanguageTag = languageCode
    }

    /**
     * Speaks [parts] in order for content tagged [key] (e.g. a stable bead id).
     * Only the completion of the LAST part emits [TtsEvent.SequenceCompleted] with [key].
     * If the engine previously failed to initialize, fails fast with [TtsEvent.SequenceInterrupted]
     * instead of queueing — Android never fires the init callback a second time.
     */
    fun speak(parts: List<String>, languageCode: String, key: String) {
        val nonEmpty = parts.filter { it.isNotBlank() }
        if (nonEmpty.isEmpty()) return
        if (initFailed) {
            _events.tryEmit(TtsEvent.SequenceInterrupted(key))
            return
        }
        if (isReady) {
            speakNow(nonEmpty, languageCode, key)
        } else {
            pendingSpeak = PendingSpeak(nonEmpty, languageCode, key)
            ensureEngine()
        }
    }

    private fun speakNow(parts: List<String>, languageCode: String, key: String) {
        applyLanguage(languageCode)
        currentSequenceKey = key
        currentSequenceLastUtteranceId = "$key#${parts.lastIndex}"
        parts.forEachIndexed { index, text ->
            val mode = if (index == 0) TextToSpeech.QUEUE_FLUSH else TextToSpeech.QUEUE_ADD
            tts?.speak(text, mode, Bundle.EMPTY, "$key#$index")
        }
    }

    /** Stops any speech in progress; a pending onStop/onError will emit SequenceInterrupted. */
    fun stop() {
        pendingSpeak = null
        currentSequenceKey = null
        currentSequenceLastUtteranceId = null
        tts?.stop()
    }

    fun shutdown() {
        tts?.stop()
        tts?.shutdown()
        tts = null
        isReady = false
    }

    companion object {
        fun localeFor(languageCode: String): Locale = when (languageCode) {
            "en" -> Locale.US
            "es" -> Locale("es", "ES")
            "fr" -> Locale.FRENCH
            "it" -> Locale.ITALIAN
            "la" -> Locale("la")
            "lt" -> Locale("lt", "LT")
            "pt-BR" -> Locale("pt", "BR")
            "pt-PT" -> Locale("pt", "PT")
            else -> Locale.getDefault()
        }
    }
}
