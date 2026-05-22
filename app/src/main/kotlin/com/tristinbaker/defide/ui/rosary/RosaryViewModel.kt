package com.tristinbaker.defide.ui.rosary

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.tristinbaker.defide.data.model.Mystery
import com.tristinbaker.defide.data.model.MysteryBead
import com.tristinbaker.defide.data.preferences.RosaryOrder
import com.tristinbaker.defide.data.preferences.UserPreferencesRepository
import com.tristinbaker.defide.data.preferences.language
import com.tristinbaker.defide.data.repository.PrayerRepository
import com.tristinbaker.defide.data.repository.RosaryRepository
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.collectLatest
import kotlinx.coroutines.flow.distinctUntilChangedBy
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.flow.map
import kotlinx.coroutines.flow.stateIn
import kotlinx.coroutines.launch
import java.time.DayOfWeek
import java.time.LocalDate
import javax.inject.Inject

/** Returns the traditional mystery ID for a given day of the week. */
fun suggestedMysteryId(date: LocalDate = LocalDate.now()): String = when (date.dayOfWeek) {
    DayOfWeek.MONDAY, DayOfWeek.SATURDAY -> "joyful"
    DayOfWeek.TUESDAY, DayOfWeek.FRIDAY  -> "sorrowful"
    DayOfWeek.THURSDAY                   -> "luminous"
    else /* WEDNESDAY, SUNDAY */         -> "glorious"
}

@HiltViewModel
class RosaryViewModel @Inject constructor(
    private val repository: RosaryRepository,
    private val prayerRepository: PrayerRepository,
    private val prefsRepository: UserPreferencesRepository,
) : ViewModel() {

    private val _mysteries = MutableStateFlow<List<Mystery>>(emptyList())
    val mysteries: StateFlow<List<Mystery>> = _mysteries.asStateFlow()

    val todaysMysteryId: String = suggestedMysteryId()

    private val _beads = MutableStateFlow<List<MysteryBead>>(emptyList())
    val beads: StateFlow<List<MysteryBead>> = _beads.asStateFlow()

    private val _currentPosition = MutableStateFlow(0)
    val currentPosition: StateFlow<Int> = _currentPosition.asStateFlow()

    private val _prayerTexts = MutableStateFlow<Map<String, String>>(emptyMap())
    val prayerTexts: StateFlow<Map<String, String>> = _prayerTexts.asStateFlow()

    private val _prayerTitles = MutableStateFlow<Map<String, String>>(emptyMap())
    val prayerTitles: StateFlow<Map<String, String>> = _prayerTitles.asStateFlow()

    private var currentRosaryOrder: RosaryOrder = RosaryOrder.DOMINICAN

    private fun physicalBeadForDominican(stepIndex: Int): Int {
        val lastStep = _beads.value.lastIndex
        return when {
            stepIndex == 0         -> -1
            stepIndex in 1..4      -> stepIndex - 1
            stepIndex == 5         -> 4
            stepIndex == lastStep  -> 59
            else -> {
                val loopStep = stepIndex - 6
                val decade   = loopStep / 14
                val within   = loopStep % 14
                val start    = 4 + decade * 11
                when {
                    within <= 1     -> start
                    within in 2..11 -> start + (within - 1)
                    else            -> start + 11
                }
            }
        }
    }

    private fun physicalBeadForFatima(stepIndex: Int): Int {
        val lastStep = _beads.value.lastIndex
        return when {
            stepIndex == 0                    -> -1
            stepIndex == 1                    -> 59
            stepIndex == lastStep             -> 0
            stepIndex > lastStep - 4          -> lastStep - stepIndex
            else -> {
                val loopStep = stepIndex - 2
                val decade   = loopStep / 15
                val within   = loopStep % 15
                when {
                    within <= 1     -> if (decade == 0) 59 else 59 - 11 * decade
                    within in 2..11 -> (60 - 11 * decade) - within
                    else            -> 59 - 11 * (decade + 1)
                }
            }
        }
    }

    private fun physicalBeadFor(stepIndex: Int): Int = when (currentRosaryOrder) {
        RosaryOrder.FATIMA    -> physicalBeadForFatima(stepIndex)
        RosaryOrder.DOMINICAN -> physicalBeadForDominican(stepIndex)
    }

    val currentPhysicalBead: StateFlow<Int> = _currentPosition
        .map { physicalBeadFor(it) }
        .stateIn(viewModelScope, SharingStarted.WhileSubscribed(5000), -1)

    val visitedPhysBeads: StateFlow<Set<Int>> = _currentPosition
        .map { pos -> (0..pos).mapNotNull { physicalBeadFor(it).takeIf { it >= 0 } }.toSet() }
        .stateIn(viewModelScope, SharingStarted.WhileSubscribed(5000), emptySet())

    val rosaryOrder: StateFlow<RosaryOrder> = prefsRepository.preferences
        .map { it.rosaryOrder }
        .stateIn(viewModelScope, SharingStarted.WhileSubscribed(5000), RosaryOrder.DOMINICAN)

    val hapticFeedback: StateFlow<Boolean> = prefsRepository.preferences
        .map { it.rosaryHapticFeedback }
        .stateIn(viewModelScope, SharingStarted.WhileSubscribed(5000), true)

    private val _sessionId = MutableStateFlow<String?>(null)
    private var currentLanguage = "en"

    private val _completing = MutableStateFlow(false)
    val completing: StateFlow<Boolean> = _completing.asStateFlow()

    init {
        // React to appRite changes — the Rite setting controls prayer/mystery language
        viewModelScope.launch {
            prefsRepository.preferences
                .distinctUntilChangedBy { it.appRite }
                .collectLatest { prefs ->
                    currentLanguage = prefs.appRite.language
                    _mysteries.value = repository.getMysteries(currentLanguage)
                    val prayers = prayerRepository.getAll(currentLanguage)
                    _prayerTexts.value = prayers.associate { it.id to it.body }
                    _prayerTitles.value = prayers.associate { it.id to it.title }
                }
        }
        viewModelScope.launch {
            prefsRepository.preferences
                .distinctUntilChangedBy { it.rosaryOrder }
                .collect { prefs -> currentRosaryOrder = prefs.rosaryOrder }
        }
    }

    fun startSession(mysteryId: String) {
        if (_beads.value.isNotEmpty()) return
        viewModelScope.launch {
            val prefs = prefsRepository.preferences.first()
            val variant = prefs.rosaryOrder.name.lowercase()
            val beads = repository.getBeads(mysteryId, currentLanguage, variant)
            if (beads.isNotEmpty()) {
                _beads.value = beads
            } else {
                currentRosaryOrder = RosaryOrder.DOMINICAN
                _beads.value = repository.getBeads(mysteryId, currentLanguage, "dominican")
            }
            _currentPosition.value = 0
            _sessionId.value = repository.startSession(mysteryId)
        }
    }

    fun advance() {
        val next = _currentPosition.value + 1
        if (next < _beads.value.size) {
            _currentPosition.value = next
        }
    }

    fun back() {
        val prev = _currentPosition.value - 1
        if (prev >= 0) _currentPosition.value = prev
    }

    fun completeSession(onDone: () -> Unit) {
        if (_completing.value) return
        _completing.value = true
        viewModelScope.launch {
            _sessionId.value?.let { repository.completeSession(it) }
            onDone()
        }
    }
}
