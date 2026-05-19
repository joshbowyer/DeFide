package com.tristinbaker.defide.ui.divineoffice

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.tristinbaker.defide.data.model.DivineOffice
import com.tristinbaker.defide.data.model.DivineOfficeCalendar
import com.tristinbaker.defide.data.model.DivineOfficePsalm
import com.tristinbaker.defide.data.repository.DivineOfficeRepository
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import java.time.LocalDate
import javax.inject.Inject

/**
 * Groups offices available for a date into the canonical canonical offices of the day.
 *
 * Matins  – office_type = NULL (reading sections with lectio + responsory, no antiphons)
 * Laudes  – office_type = "Laudes"
 * Vespera – office_type = "Vespera"
 * (Prime / Terce / Sext / None / Completorium may be present as NULL entries with
 *  suitable titles — grouped under Matins for now as the current data is sparse.)
 */
data class DayOffices(
    val calendarEntry: DivineOfficeCalendar?,
    val matins: List<DivineOffice> = emptyList(),
    val laudes: List<DivineOffice> = emptyList(),
    val vespera: List<DivineOffice> = emptyList(),
    val completorium: List<DivineOffice> = emptyList(),
    val hasData: Boolean = false,
)

@HiltViewModel
class DivineOfficeViewModel @Inject constructor(
    private val repository: DivineOfficeRepository,
) : ViewModel() {

    // ── Shared state ──────────────────────────────────────────────────────────

    private val _selectedDate = MutableStateFlow(LocalDate.now())
    val selectedDate: StateFlow<LocalDate> = _selectedDate.asStateFlow()

    private val _dayOffices = MutableStateFlow(DayOffices(calendarEntry = null))
    val dayOffices: StateFlow<DayOffices> = _dayOffices.asStateFlow()

    private val _isLoading = MutableStateFlow(false)
    val isLoading: StateFlow<Boolean> = _isLoading.asStateFlow()

    // ── Office reader state ───────────────────────────────────────────────────

    /** The office selected by the user to read. */
    private val _selectedOffice = MutableStateFlow<DivineOffice?>(null)
    val selectedOffice: StateFlow<DivineOffice?> = _selectedOffice.asStateFlow()

    /** The psalms for the selected office (based on day-of-week + office type). */
    private val _selectedPsalms = MutableStateFlow<List<DivineOfficePsalm>>(emptyList())
    val selectedPsalms: StateFlow<List<DivineOfficePsalm>> = _selectedPsalms.asStateFlow()

    // ── Init ─────────────────────────────────────────────────────────────────

    init {
        loadForDate(_selectedDate.value)
    }

    // ── Date navigation ──────────────────────────────────────────────────────

    fun goToPreviousDay() = setDate(_selectedDate.value.minusDays(1))

    fun goToNextDay() = setDate(_selectedDate.value.plusDays(1))

    fun setDate(date: LocalDate) {
        _selectedDate.value = date
        _selectedOffice.value = null
        _selectedPsalms.value = emptyList()
        loadForDate(date)
    }

    fun showDatePicker(): Boolean = true  // caller opens system date picker; then calls setDate

    // ── Office selection ──────────────────────────────────────────────────────

    /**
     * dayOfWeek: 0=Sunday … 6=Saturday (Java LocalDate convention).
     * Psalmi major.txt: Day0 = Sunday, Day1 = Monday … Day6 = Saturday.
     * They match perfectly — no conversion needed.
     */
    private val dayOfWeek: Int get() = _selectedDate.value.dayOfWeek.value % 7

    fun selectOffice(office: DivineOffice) {
        _selectedOffice.value = office
        viewModelScope.launch {
            // officeType from DB: "Laudes", "Vespers", "Matins", "Completorium"
            // Psalm rows use "Compline" instead of "Completorium"
            val rawOt = office.officeType?.takeIf { it.isNotBlank() } ?: "Laudes"
            val ot = if (rawOt == "Completorium") "Compline" else rawOt

            // Load psalms from the ferial row keyed by day-of-week + office type.
            // The antiphons are already merged into office.ferialAntiphons by the DAO.
            _selectedPsalms.value = repository.getFerialPsalms(dayOfWeek, ot)
        }
    }

    fun clearSelection() {
        _selectedOffice.value = null
        _selectedPsalms.value = emptyList()
    }

    // ── Data loading ─────────────────────────────────────────────────────────

    private fun loadForDate(date: LocalDate) {
        viewModelScope.launch {
            _isLoading.value = true

            val mmDd = "%02d-%02d".format(date.monthValue, date.dayOfMonth)
            val calendarEntry = repository.getCalendarEntry(mmDd)
            val allOffices = repository.getAllOfficesForDate(date)

            val matins = allOffices.filter {
                it.officeType == null || it.officeType == "Matins"
            }
            val laudes = allOffices.filter { it.officeType == "Laudes" }
            val vespera = allOffices.filter {
                it.officeType == "Vespers" || it.officeType == "Vespera"
            }
            val completorium = allOffices.filter {
                it.officeType == "Completorium" || it.officeType == "Compline"
            }

            // If no offices found in sancti/tempora for this date, show whatever we have
            // (empty screens for pure-ferial days without sancti entries will be addressed
            // in a future enhancement that maps tempora ferial files by liturgical week)
            val hasAnyOffice = laudes.isNotEmpty() || vespera.isNotEmpty() || matins.isNotEmpty() || completorium.isNotEmpty()

            _dayOffices.value = DayOffices(
                calendarEntry = calendarEntry,
                matins = matins,
                laudes = laudes,
                vespera = vespera,
                completorium = completorium,
                hasData = allOffices.isNotEmpty(),
            )
            _isLoading.value = false
        }
    }
}
