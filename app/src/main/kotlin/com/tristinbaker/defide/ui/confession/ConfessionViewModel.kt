package com.tristinbaker.defide.ui.confession

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.tristinbaker.defide.data.db.user.dao.ConfessionNoteDao
import com.tristinbaker.defide.data.db.user.dao.ConfessionRecordDao
import com.tristinbaker.defide.data.db.user.entity.ConfessionNoteEntity
import com.tristinbaker.defide.data.db.user.entity.ConfessionRecordEntity
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.stateIn
import kotlinx.coroutines.launch
import java.util.UUID
import javax.inject.Inject

@HiltViewModel
class ConfessionViewModel @Inject constructor(
    private val noteDao: ConfessionNoteDao,
    private val recordDao: ConfessionRecordDao,
) : ViewModel() {

    val notes = noteDao.getAllFlow()
        .stateIn(viewModelScope, SharingStarted.WhileSubscribed(5000), emptyList())

    val records = recordDao.getAllFlow()
        .stateIn(viewModelScope, SharingStarted.WhileSubscribed(5000), emptyList())

    fun addNote(text: String) {
        if (text.isBlank()) return
        viewModelScope.launch {
            noteDao.insert(
                ConfessionNoteEntity(
                    id = UUID.randomUUID().toString(),
                    text = text.trim(),
                    createdAt = System.currentTimeMillis(),
                )
            )
        }
    }

    fun deleteNote(note: ConfessionNoteEntity) {
        viewModelScope.launch { noteDao.delete(note) }
    }

    fun deleteRecord(record: ConfessionRecordEntity) {
        viewModelScope.launch { recordDao.delete(record) }
    }

    fun recordConfession() {
        viewModelScope.launch {
            recordDao.insert(
                ConfessionRecordEntity(
                    id = UUID.randomUUID().toString(),
                    madeAt = System.currentTimeMillis(),
                )
            )
            noteDao.deleteAll()
        }
    }
}
