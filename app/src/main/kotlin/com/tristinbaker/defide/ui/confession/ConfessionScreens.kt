package com.tristinbaker.defide.ui.confession

import androidx.compose.foundation.ExperimentalFoundationApi
import androidx.compose.foundation.combinedClickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material.icons.filled.Add
import androidx.compose.material.icons.filled.Delete
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.Button
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.FloatingActionButton
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.material3.TopAppBar
import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import com.tristinbaker.defide.R
import com.tristinbaker.defide.data.db.user.entity.ConfessionNoteEntity
import com.tristinbaker.defide.data.db.user.entity.ConfessionRecordEntity
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun ConfessionScreen(
    onBack: () -> Unit,
    viewModel: ConfessionViewModel = hiltViewModel(),
) {
    val notes by viewModel.notes.collectAsState()
    val records by viewModel.records.collectAsState()

    var showAddDialog by remember { mutableStateOf(false) }
    var showConfirmDialog by remember { mutableStateOf(false) }
    var pendingDeleteRecord by remember { mutableStateOf<ConfessionRecordEntity?>(null) }
    var noteText by remember { mutableStateOf("") }

    if (showAddDialog) {
        AlertDialog(
            onDismissRequest = { showAddDialog = false; noteText = "" },
            title = { Text(stringResource(R.string.confession_add_label)) },
            text = {
                OutlinedTextField(
                    value = noteText,
                    onValueChange = { noteText = it },
                    placeholder = { Text(stringResource(R.string.confession_add_hint)) },
                    modifier = Modifier.fillMaxWidth(),
                    maxLines = 4,
                )
            },
            confirmButton = {
                Button(
                    onClick = {
                        viewModel.addNote(noteText)
                        noteText = ""
                        showAddDialog = false
                    },
                    enabled = noteText.isNotBlank(),
                ) { Text(stringResource(R.string.confession_add_label)) }
            },
            dismissButton = {
                TextButton(onClick = { showAddDialog = false; noteText = "" }) {
                    Text(stringResource(R.string.action_cancel))
                }
            },
        )
    }

    if (showConfirmDialog) {
        AlertDialog(
            onDismissRequest = { showConfirmDialog = false },
            title = { Text(stringResource(R.string.confession_confirm_title)) },
            text = { Text(stringResource(R.string.confession_confirm_text)) },
            confirmButton = {
                Button(onClick = {
                    viewModel.recordConfession()
                    showConfirmDialog = false
                }) { Text(stringResource(R.string.confession_confirm)) }
            },
            dismissButton = {
                TextButton(onClick = { showConfirmDialog = false }) {
                    Text(stringResource(R.string.action_cancel))
                }
            },
        )
    }

    pendingDeleteRecord?.let { record ->
        AlertDialog(
            onDismissRequest = { pendingDeleteRecord = null },
            title = { Text(stringResource(R.string.confession_delete_record_title)) },
            text = { Text(stringResource(R.string.confession_delete_record_text)) },
            confirmButton = {
                Button(
                    onClick = {
                        viewModel.deleteRecord(record)
                        pendingDeleteRecord = null
                    },
                    colors = androidx.compose.material3.ButtonDefaults.buttonColors(
                        containerColor = MaterialTheme.colorScheme.error,
                    ),
                ) { Text(stringResource(R.string.action_delete)) }
            },
            dismissButton = {
                TextButton(onClick = { pendingDeleteRecord = null }) {
                    Text(stringResource(R.string.action_cancel))
                }
            },
        )
    }

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text(stringResource(R.string.confession_title)) },
                navigationIcon = {
                    IconButton(onClick = onBack) {
                        Icon(Icons.AutoMirrored.Filled.ArrowBack, contentDescription = "Back")
                    }
                },
            )
        },
        floatingActionButton = {
            FloatingActionButton(onClick = { showAddDialog = true }) {
                Icon(Icons.Default.Add, contentDescription = stringResource(R.string.confession_add_label))
            }
        },
    ) { padding ->
        LazyColumn(
            modifier = Modifier.fillMaxSize().padding(padding),
            contentPadding = PaddingValues(bottom = 80.dp),
        ) {
            item {
                OutlinedButton(
                    onClick = { showConfirmDialog = true },
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(horizontal = 16.dp, vertical = 12.dp),
                ) {
                    Text(stringResource(R.string.confession_mark_confessed))
                }
                HorizontalDivider()
            }

            item {
                Text(
                    text = stringResource(R.string.confession_notes_title),
                    style = MaterialTheme.typography.labelLarge,
                    color = MaterialTheme.colorScheme.primary,
                    modifier = Modifier.padding(horizontal = 16.dp, vertical = 10.dp),
                )
            }

            if (notes.isEmpty()) {
                item {
                    Box(modifier = Modifier.fillMaxWidth().padding(horizontal = 16.dp, vertical = 8.dp)) {
                        Text(
                            stringResource(R.string.confession_no_notes),
                            style = MaterialTheme.typography.bodyMedium,
                            color = MaterialTheme.colorScheme.onSurfaceVariant,
                        )
                    }
                }
            } else {
                items(notes, key = { it.id }) { note ->
                    NoteRow(note = note, onDelete = { viewModel.deleteNote(note) })
                    HorizontalDivider()
                }
            }

            item {
                Spacer(Modifier.height(16.dp))
                HorizontalDivider()
                Text(
                    text = stringResource(R.string.confession_history_title),
                    style = MaterialTheme.typography.labelLarge,
                    color = MaterialTheme.colorScheme.primary,
                    modifier = Modifier.padding(horizontal = 16.dp, vertical = 10.dp),
                )
            }

            if (records.isEmpty()) {
                item {
                    Box(modifier = Modifier.fillMaxWidth().padding(horizontal = 16.dp, vertical = 8.dp)) {
                        Text(
                            stringResource(R.string.confession_no_records),
                            style = MaterialTheme.typography.bodyMedium,
                            color = MaterialTheme.colorScheme.onSurfaceVariant,
                        )
                    }
                }
            } else {
                items(records, key = { it.id }) { record ->
                    val dateStr = SimpleDateFormat("MMMM d, yyyy", Locale.getDefault())
                        .format(Date(record.madeAt))
                    @OptIn(ExperimentalFoundationApi::class)
                    Text(
                        text = stringResource(R.string.confession_last_on, dateStr),
                        style = MaterialTheme.typography.bodyMedium,
                        modifier = Modifier
                            .fillMaxWidth()
                            .combinedClickable(
                                onClick = {},
                                onLongClick = { pendingDeleteRecord = record },
                            )
                            .padding(horizontal = 16.dp, vertical = 12.dp),
                    )
                    HorizontalDivider()
                }
            }
        }
    }
}

@Composable
private fun NoteRow(note: ConfessionNoteEntity, onDelete: () -> Unit) {
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .padding(horizontal = 16.dp, vertical = 10.dp),
        verticalAlignment = Alignment.CenterVertically,
    ) {
        Column(modifier = Modifier.weight(1f)) {
            Text(note.text, style = MaterialTheme.typography.bodyMedium)
            val dateStr = SimpleDateFormat("MMM d", Locale.getDefault()).format(Date(note.createdAt))
            Text(
                dateStr,
                style = MaterialTheme.typography.bodySmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
            )
        }
        IconButton(onClick = onDelete) {
            Icon(
                Icons.Default.Delete,
                contentDescription = "Delete",
                tint = MaterialTheme.colorScheme.onSurfaceVariant,
            )
        }
    }
}
