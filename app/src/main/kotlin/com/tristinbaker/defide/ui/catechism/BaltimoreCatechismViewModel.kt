package com.tristinbaker.defide.ui.catechism

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.tristinbaker.defide.data.model.BaltimoreCatechism
import com.tristinbaker.defide.data.repository.BaltimoreCatechismRepository
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import javax.inject.Inject

@HiltViewModel
class BaltimoreCatechismViewModel @Inject constructor(
    private val repository: BaltimoreCatechismRepository,
) : ViewModel() {

    private val _lessons = MutableStateFlow<Map<Int, List<BaltimoreCatechism>>>(emptyMap())
    val lessons: StateFlow<Map<Int, List<BaltimoreCatechism>>> = _lessons.asStateFlow()

    private val _currentQuestion = MutableStateFlow<BaltimoreCatechism?>(null)
    val currentQuestion: StateFlow<BaltimoreCatechism?> = _currentQuestion.asStateFlow()

    private val _isLoading = MutableStateFlow(false)
    val isLoading: StateFlow<Boolean> = _isLoading.asStateFlow()

    init {
        loadAll()
    }

    private fun loadAll() {
        viewModelScope.launch {
            _isLoading.value = true
            val lessonList = repository.getDistinctLessons()
            val grouped = mutableMapOf<Int, List<BaltimoreCatechism>>()
            for (lesson in lessonList) {
                grouped[lesson] = repository.getByLesson(lesson)
            }
            _lessons.value = grouped
            _isLoading.value = false
        }
    }

    fun loadQuestion(id: Int) {
        viewModelScope.launch {
            _isLoading.value = true
            _currentQuestion.value = repository.getById(id)
            _isLoading.value = false
        }
    }
}
