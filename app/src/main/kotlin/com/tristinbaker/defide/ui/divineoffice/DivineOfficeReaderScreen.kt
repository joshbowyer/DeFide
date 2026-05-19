package com.tristinbaker.defide.ui.divineoffice

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.material3.TopAppBar
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import com.tristinbaker.defide.R
import com.tristinbaker.defide.data.model.DivineOffice
import com.tristinbaker.defide.data.model.DivineOfficePsalm
import java.time.format.DateTimeFormatter

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun DivineOfficeReaderScreen(
    viewModel: DivineOfficeViewModel,
    onBack: () -> Unit,
) {
    val office by viewModel.selectedOffice.collectAsState()
    val psalms by viewModel.selectedPsalms.collectAsState()
    val selectedDate by viewModel.selectedDate.collectAsState()

    LaunchedEffect(Unit) {
        // Ensure we don't navigate to this screen without a selected office.
        // If selectedOffice is null, go back.
    }

    val dateFormatter = DateTimeFormatter.ofPattern("EEEE, MMMM d, yyyy")

    Scaffold(
        topBar = {
            TopAppBar(
                title = {
                    Text(
                        text = office?.title ?: stringResource(R.string.divine_office_title),
                        maxLines = 1,
                    )
                },
                navigationIcon = {
                    IconButton(onClick = {
                        viewModel.clearSelection()
                        onBack()
                    }) {
                        Icon(Icons.AutoMirrored.Filled.ArrowBack, contentDescription = null)
                    }
                },
            )
        },
    ) { padding ->
        if (office == null) {
            Column(
                modifier = Modifier
                    .fillMaxSize()
                    .padding(padding)
                    .padding(16.dp),
                verticalArrangement = Arrangement.Center,
            ) {
                Text(
                    text = "No office selected.",
                    style = MaterialTheme.typography.bodyLarge,
                    textAlign = TextAlign.Center,
                    modifier = Modifier.fillMaxWidth(),
                )
            }
        } else {
            LazyColumn(
                modifier = Modifier
                    .fillMaxSize()
                    .padding(padding)
                    .padding(horizontal = 16.dp),
            ) {
                item {
                    Spacer(modifier = Modifier.height(8.dp))
                    // Date sub-header
                    Text(
                        text = selectedDate.format(dateFormatter),
                        style = MaterialTheme.typography.titleSmall,
                        color = MaterialTheme.colorScheme.primary,
                        modifier = Modifier.fillMaxWidth(),
                        textAlign = TextAlign.Center,
                    )
                    Spacer(modifier = Modifier.height(16.dp))
                }

                office?.let { o ->
                    item {
                        OfficeContentCard(office = o, psalms = psalms)
                        Spacer(modifier = Modifier.height(32.dp))
                    }
                }
            }
        }
    }
}

@Composable
fun OfficeContentCard(
    office: DivineOffice,
    psalms: List<DivineOfficePsalm>,
) {
    val officeType = office.officeType ?: ""

    // Antiphons: prefer the ferial-antiphon list (merged by DAO), fall back to psalm_text blocks
    val displayAntiphons = office.ferialAntiphons.ifEmpty {
        psalms.flatMap { it.parseBlocks().antiphons }.filter { it.isNotBlank() }
    }

    // Verse texts from the psalm_text JSON blocks
    val allVersesText = psalms.map { it.parseBlocks().versesText }.filter { it.isNotBlank() }
        .joinToString("\n\n")

    // For Matins: use matinsAntiphon if available.
    // Completorium handles its antiphon in its own screen branch (line 234) — skip here.
    val matinsAntiphonDisplay = when (officeType) {
        "Matins" -> office.matinsAntiphon ?: office.ferialAntiphons.firstOrNull()
        else -> null
    }

    Card(
        modifier = Modifier.fillMaxWidth(),
        colors = CardDefaults.cardColors(
            containerColor = MaterialTheme.colorScheme.surfaceVariant,
        ),
    ) {
        Column(modifier = Modifier.padding(16.dp)) {

            // Completorium has its own Invitatorium/Hymn/Antiphon handling in the
            // Completorium branch below — skip those pre-section fields to avoid duplication.
            if (officeType != "Completorium") {
                maybeShowField(label = "Invitatorium", value = office.invitatorium)
                maybeShowField(label = "Hymn", value = office.hymn)
            }

            // Antiphons — ferial antiphons merged by DAO, or fall back to psalm_text blocks
            if (displayAntiphons.isNotEmpty()) {
                Text(
                    text = "Antiphons",
                    style = MaterialTheme.typography.labelLarge,
                    fontWeight = FontWeight.Bold,
                    color = MaterialTheme.colorScheme.primary,
                )
                Spacer(modifier = Modifier.height(4.dp))
                displayAntiphons.forEachIndexed { index, ant ->
                    Text(
                        text = ant,
                        style = MaterialTheme.typography.bodyMedium,
                        color = MaterialTheme.colorScheme.onSurfaceVariant,
                    )
                    if (index < displayAntiphons.lastIndex) {
                        Spacer(modifier = Modifier.height(4.dp))
                    }
                }
                Spacer(modifier = Modifier.height(12.dp))
            }

            // Matins antiphon (loaded from matutinum.txt) — shown as its own section
            if (matinsAntiphonDisplay != null && displayAntiphons.isEmpty()) {
                Text(
                    text = "Antiphon",
                    style = MaterialTheme.typography.labelLarge,
                    fontWeight = FontWeight.Bold,
                    color = MaterialTheme.colorScheme.primary,
                )
                Spacer(modifier = Modifier.height(4.dp))
                Text(
                    text = matinsAntiphonDisplay,
                    style = MaterialTheme.typography.bodyMedium,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                )
                Spacer(modifier = Modifier.height(12.dp))
            }

            // Psalm verses — show the expanded Latin text
            if (allVersesText.isNotBlank()) {
                Text(
                    text = stringResource(R.string.office_psalms),
                    style = MaterialTheme.typography.labelLarge,
                    fontWeight = FontWeight.Bold,
                    color = MaterialTheme.colorScheme.primary,
                )
                Spacer(modifier = Modifier.height(4.dp))
                // Format verses: strip the "ps:vs:" prefix from each verse line
                val formattedVerses = allVersesText.lines().mapNotNull { line ->
                    val trimmed = line.trim()
                    if (trimmed.isBlank()) return@mapNotNull null
                    val parts = trimmed.split(":", limit = 3)
                    if (parts.size >= 3) parts[2].trim() else trimmed
                }
                formattedVerses.forEach { verse ->
                    Text(
                        text = verse,
                        style = MaterialTheme.typography.bodyMedium,
                        color = MaterialTheme.colorScheme.onSurface,
                    )
                }
                Spacer(modifier = Modifier.height(12.dp))
            }

            // Readings — use the right field per office type
            when (officeType) {
                "Laudes" -> {
                    maybeShowField(label = "Capitulum", value = office.capitulum)
                    maybeShowField(label = "Reading", value = office.lectio1)
                    maybeShowField(label = "Responsory", value = office.responsory1)
                    maybeShowField(label = "Collect", value = office.oratio, highlighted = true)
                }
                "Vespers" -> {
                    maybeShowField(label = "Capitulum", value = office.capitulum)
                    maybeShowField(label = "Reading", value = office.lectio1)
                    maybeShowField(label = "Responsory", value = office.responsory1)
                    maybeShowField(label = "Collect", value = office.oratio, highlighted = true)
                }
                "Compline", "Completorium" -> {
                    // Completorium antiphon stored in matins_antiphon field
                    maybeShowField(label = "Hymn", value = office.hymn)
                    maybeShowField(label = "Antiphon", value = office.matinsAntiphon)
                    maybeShowField(label = "Collect", value = office.oratio, highlighted = true)
                }
                else -> {
                    maybeShowField(label = "First Reading", value = office.lectio1)
                    maybeShowField(label = "Second Reading", value = office.lectio2)
                    maybeShowField(label = "Third Reading", value = office.lectio3)
                    maybeShowField(label = "Responsory 1", value = office.responsory1)
                    maybeShowField(label = "Responsory 2", value = office.responsory2)
                    maybeShowField(label = "Responsory 3", value = office.responsory3)
                    maybeShowField(label = "Collect", value = office.oratio, highlighted = true)
                }
            }

            maybeShowField(label = "Versicle", value = office.versus)
            maybeShowField(label = "Preces", value = office.preces)
            maybeShowField(label = "Conclusion", value = office.conclusio)
        }
    }
}

@Composable
private fun maybeShowField(
    label: String,
    value: String?,
    highlighted: Boolean = false,
) {
    val clean = value.sanitizeOfficeField() ?: return
    OfficeField(label = label, value = clean, highlighted = highlighted)
}

/** Strip rubrica noise and empty strings that come from the Divinum Officium data. */
private fun String?.sanitizeOfficeField(): String? {
    if (this == null || isBlank()) return null
    val trimmed = trim()
    // Skip pure rubric notes
    if (trimmed == "(rubrica)" || trimmed == "(rubrica tridentina)") return null
    // Skip rubric notes followed only by whitespace
    if (trimmed.startsWith("(rubrica") && trimmed.endsWith(")")) return null
    // Skip cross-references to other files (e.g. "@Sancti/01-06:Responsory2")
    if (trimmed.startsWith("@")) return null
    return trimmed
}

@Composable
private fun OfficeField(
    label: String,
    value: String,
    highlighted: Boolean = false,
) {
    Column(modifier = Modifier.padding(vertical = 6.dp)) {
        Text(
            text = label,
            style = MaterialTheme.typography.labelLarge,
            fontWeight = FontWeight.Bold,
            color = if (highlighted) MaterialTheme.colorScheme.primary
                    else MaterialTheme.colorScheme.onSurfaceVariant,
        )
        Spacer(modifier = Modifier.height(2.dp))
        Text(
            text = value,
            style = MaterialTheme.typography.bodyMedium,
            color = if (highlighted) MaterialTheme.colorScheme.onPrimaryContainer
                    else MaterialTheme.colorScheme.onSurface,
        )
        Spacer(modifier = Modifier.height(8.dp))
        HorizontalDivider(color = MaterialTheme.colorScheme.outlineVariant.copy(alpha = 0.5f))
    }
}
