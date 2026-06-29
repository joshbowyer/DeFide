package com.tristinbaker.defide.ui.catechism

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.tristinbaker.defide.data.model.CompendiumCatechism
import com.tristinbaker.defide.data.repository.CompendiumCatechismRepository
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import javax.inject.Inject

@HiltViewModel
class CompendiumCatechismViewModel @Inject constructor(
    private val repository: CompendiumCatechismRepository,
) : ViewModel() {

    private val _groups = MutableStateFlow<Map<String, List<CompendiumCatechism>>>(emptyMap())
    val groups: StateFlow<Map<String, List<CompendiumCatechism>>> = _groups.asStateFlow()

    private val _currentQuestion = MutableStateFlow<CompendiumCatechism?>(null)
    val currentQuestion: StateFlow<CompendiumCatechism?> = _currentQuestion.asStateFlow()

    private val _isLoading = MutableStateFlow(false)
    val isLoading: StateFlow<Boolean> = _isLoading.asStateFlow()

    init {
        loadAll()
    }

    private fun loadAll() {
        viewModelScope.launch {
            _isLoading.value = true
            val groupList = repository.getDistinctGroups()
            val grouped = mutableMapOf<String, List<CompendiumCatechism>>()
            for (group in groupList) {
                grouped[group] = repository.getByGroup(group)
            }
            _groups.value = grouped
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
