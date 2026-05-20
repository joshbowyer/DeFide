package com.tristinbaker.defide.ui.divineoffice

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
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
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.text.font.FontStyle
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import com.tristinbaker.defide.R
import com.tristinbaker.defide.data.model.DivineOffice
import com.tristinbaker.defide.data.model.DivineOfficePsalm
import java.time.format.DateTimeFormatter

// ─────────────────────────────────────────────────────────────────────────────
//  Static text for Compline Examination of Conscience
// ─────────────────────────────────────────────────────────────────────────────
private const val EXAMINATION_OF_CONSCIENCE = """I confess to almighty God
and to you, my brothers and sisters,
that I have greatly sinned,
in my thoughts and in my words,
in what I have done and in what I have failed to do,
through my fault,
through my fault,
through my most grievous fault;
therefore I ask blessed Mary ever-Virgin,
all the Angels and Saints,
and you, my brothers and sisters,
to pray for me to the Lord our God.

May almighty God have mercy on us,
forgive us our sins,
and bring us to everlasting life.

Amen."""

// ─────────────────────────────────────────────────────────────────────────────
//  Screen
// ─────────────────────────────────────────────────────────────────────────────
@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun DivineOfficeReaderScreen(
    viewModel: DivineOfficeViewModel,
    onBack: () -> Unit,
) {
    val office by viewModel.selectedOffice.collectAsState()
    val psalms by viewModel.selectedPsalms.collectAsState()
    val selectedDate by viewModel.selectedDate.collectAsState()

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

// ─────────────────────────────────────────────────────────────────────────────
//  OfficeContentCard — delegates to per-office renderers
// ─────────────────────────────────────────────────────────────────────────────
@Composable
fun OfficeContentCard(
    office: DivineOffice,
    psalms: List<DivineOfficePsalm>,
) {
    when (office.officeType) {
        "Laudes"   -> LaudesContent(office, psalms)
        "Vespers"  -> VespersContent(office, psalms)
        "Matins"   -> MatinsContent(office, psalms)
        "Compline", "Completorium" -> CompletoriumContent(office, psalms)
        else        -> DefaultOfficeContent(office, psalms)
    }
}

// ─────────────────────────────────────────────────────────────────────────────
//  LAUDES
//  Canonical order:
//    1. Invitatorium (if first hour today — we always show it)
//    2. Hymn
//    3. Antiphon + Psalm(s) — one antiphon per psalm from ant1-ant3
//    4. Scripture Reading (lectio1)
//    5. Short Responsory (responsory1)
//    6. Canticle (Benedictus) — antiphon repeated
//    7. Prayers & Intercessions (preces)
//    8. Our Father
//    9. Collect (oratio)
//   10. Conclusion / Blessing (conclusio)
// ─────────────────────────────────────────────────────────────────────────────
@Composable
private fun LaudesContent(office: DivineOffice, psalms: List<DivineOfficePsalm>) {
    OfficeCard {
        // 1. Invitatorium
        maybeShowField("Invitatorium", office.invitatorium)

        // 2. Hymn
        maybeShowField("Hymn", office.hymn)

        // 3. Antiphon + Psalm(s)
        LaudesAntiphonPsalmPairs(office, psalms)

        // 4. Scripture Reading
        maybeShowField("Scripture Reading", office.lectio1)

        // 5. Short Responsory
        maybeShowField("Short Responsory", office.responsory1)

        // 6. Canticle (Benedictus) — antiphon from Laudes ant1
        CanticleSection(
            title = "Canticle (Benedictus)",
            antiphon = office.ant1,
        )

        // 7. Prayers & Intercessions
        maybeShowField("Prayers and Intercessions", office.preces)

        // 8. Collect
        maybeShowField("Collect", office.oratio, highlighted = true)

        // 9. Conclusion
        maybeShowField("Conclusion", office.conclusio)
    }
}

// ─────────────────────────────────────────────────────────────────────────────
//  VESPERS
//  Canonical order:
//    1. Hymn
//    2. Antiphon + Psalm(s) — antVespers1-3 preferred, then ant1-ant3
//    3. Scripture Reading (lectio1)
//    4. Short Responsory (responsory1)
//    5. Canticle (Magnificat) — antiphon repeated
//    6. Prayers & Intercessions (preces)
//    7. Our Father
//    8. Collect (oratio)
//    9. Conclusion / Blessing (conclusio)
// ─────────────────────────────────────────────────────────────────────────────
@Composable
private fun VespersContent(office: DivineOffice, psalms: List<DivineOfficePsalm>) {
    OfficeCard {
        // 1. Hymn
        maybeShowField("Hymn", office.hymn)

        // 2. Antiphon + Psalm(s) — prefer Vespera antiphons
        VespersAntiphonPsalmPairs(office, psalms)

        // 3. Scripture Reading
        maybeShowField("Scripture Reading", office.lectio1)

        // 4. Short Responsory
        maybeShowField("Short Responsory", office.responsory1)

        // 5. Canticle (Magnificat) — antiphon from Vespers antVespers1 or ant1
        CanticleSection(
            title = "Canticle (Magnificat)",
            antiphon = office.antVespera1 ?: office.ant1,
        )

        // 6. Prayers & Intercessions
        maybeShowField("Prayers and Intercessions", office.preces)

        // 7. Collect
        maybeShowField("Collect", office.oratio, highlighted = true)

        // 8. Conclusion
        maybeShowField("Conclusion", office.conclusio)
    }
}

// ─────────────────────────────────────────────────────────────────────────────
//  MATINS / Office of Readings
//  Canonical order:
//    1. Invitatorium
//    2. Hymn
//    3. Antiphon + Psalm 1 (antiphon repeated before and after)
//    4. First Reading (lectio1)
//    5. Responsory (responsory1)
//    6. Antiphon + Psalm 2 (antiphon repeated)
//    7. Second Reading (lectio2)
//    8. Responsory (responsory2)
//    9. Third Reading (lectio3)
//   10. Responsory (responsory3)
//   11. Te Deum (ferial only — omit when lectio3 is feast reading)
//   12. Collect (oratio)
// ─────────────────────────────────────────────────────────────────────────────
@Composable
private fun MatinsContent(office: DivineOffice, psalms: List<DivineOfficePsalm>) {
    OfficeCard {
        // 1. Invitatorium
        maybeShowField("Invitatorium", office.invitatorium)

        // 2. Hymn
        maybeShowField("Hymn", office.hymn)

        // 3. Antiphon + Psalm 1
        PsalmAntiphonPair(
            antiphon = office.ant1,
            psalms = psalms.filter { it.officeType == "Matins" }.take(1),
        )

        // 4. First Reading
        maybeShowField("First Reading", office.lectio1)

        // 5. Responsory 1
        maybeShowField("Responsory", office.responsory1)

        // 6. Antiphon + Psalm 2
        PsalmAntiphonPair(
            antiphon = office.ant2,
            psalms = psalms.filter { it.officeType == "Matins" }.drop(1).take(1),
        )

        // 7. Second Reading
        maybeShowField("Second Reading", office.lectio2)

        // 8. Responsory 2
        maybeShowField("Responsory 2", office.responsory2)

        // 9. Antiphon + Psalm 3 (if lectio3 is present)
        if (!office.lectio3.isNullOrBlank()) {
            PsalmAntiphonPair(
                antiphon = office.ant3,
                psalms = psalms.filter { it.officeType == "Matins" }.drop(2).take(1),
            )
        }

        // 10. Third Reading
        maybeShowField("Third Reading", office.lectio3)

        // 11. Responsory 3
        maybeShowField("Responsory 3", office.responsory3)

        // 12. Collect
        maybeShowField("Collect", office.oratio, highlighted = true)
    }
}

// ─────────────────────────────────────────────────────────────────────────────
//  COMPLETINE / Completorium
//  Canonical order:
//    1. Examination of Conscience (static Latin text)
//    2. Hymn
//    3. Antiphon + Psalm (matins_antiphon for ferial; ant1 for sancti)
//    4. Scripture Reading (lectio1)
//    5. Short Responsory (responsory1)
//    6. Canticle (Nunc Dimittis) — antiphon repeated
//    7. Collect (oratio)
//    8. Final Blessing (static)
//    9. Antiphon to Mary / Regina Caeli
// ─────────────────────────────────────────────────────────────────────────────
@Composable
private fun CompletoriumContent(office: DivineOffice, psalms: List<DivineOfficePsalm>) {
    OfficeCard {
        // 1. Examination of Conscience
        StaticTextSection(
            label = "Examination of Conscience",
            text = EXAMINATION_OF_CONSCIENCE,
        )

        // 2. Hymn
        maybeShowField("Hymn", office.hymn)

        // 3. Antiphon + Psalm
        // Ferial Completorium: antiphon in matinsAntiphon; sancti: in ant1
        val complineAntiphon = office.matinsAntiphon ?: office.ant1
        PsalmAntiphonPair(
            antiphon = complineAntiphon,
            psalms = psalms.filter { it.officeType in listOf("Compline", "Completorium") },
        )

        // 4. Scripture Reading
        maybeShowField("Scripture Reading", office.lectio1)

        // 5. Short Responsory
        maybeShowField("Short Responsory", office.responsory1)

        // 6. Canticle (Nunc Dimittis) — antiphon repeated
        CanticleSection(
            title = "Canticle (Nunc Dimittis)",
            antiphon = complineAntiphon,
        )

        // 7. Collect
        maybeShowField("Collect", office.oratio, highlighted = true)

        // 8. Final Blessing (static text)
        StaticTextSection(
            label = "Blessing",
            text = "The Lord grant us a quiet night and a perfect end.\n\nAmen.",
        )

        // 9. Antiphon to Mary (Regina Caeli — during Easter season)
        ReginaCaeliSection()
    }
}

// ─────────────────────────────────────────────────────────────────────────────
//  Default fallback for unknown office types
// ─────────────────────────────────────────────────────────────────────────────
@Composable
private fun DefaultOfficeContent(office: DivineOffice, psalms: List<DivineOfficePsalm>) {
    OfficeCard {
        maybeShowField("Invitatorium", office.invitatorium)
        maybeShowField("Hymn", office.hymn)

        // Show all ant1-ant9
        listOfNotNull(
            office.ant1, office.ant2, office.ant3,
            office.ant4, office.ant5, office.ant6,
            office.ant7, office.ant8, office.ant9,
        ).forEach { ant ->
            maybeShowField("Antiphon", ant)
        }

        maybeShowField("First Reading", office.lectio1)
        maybeShowField("Second Reading", office.lectio2)
        maybeShowField("Third Reading", office.lectio3)
        maybeShowField("Responsory 1", office.responsory1)
        maybeShowField("Responsory 2", office.responsory2)
        maybeShowField("Responsory 3", office.responsory3)
        maybeShowField("Versicle", office.versus)
        maybeShowField("Preces", office.preces)
        maybeShowField("Collect", office.oratio, highlighted = true)
        maybeShowField("Conclusion", office.conclusio)
    }
}

// ─────────────────────────────────────────────────────────────────────────────
//  LAUDES antiphon + psalm pairs
//  Uses ant1, ant2, ant3 from the office row (already have the psalm text in psalms)
//  Antiphon shown before AND after the Gloria Patri
// ─────────────────────────────────────────────────────────────────────────────
@Composable
private fun LaudesAntiphonPsalmPairs(office: DivineOffice, psalms: List<DivineOfficePsalm>) {
    val antiphonList = listOfNotNull(office.ant1, office.ant2, office.ant3)
    val psalmBlocks = psalms.filter { it.officeType == "Laudes" }

    if (antiphonList.isEmpty() && psalmBlocks.isEmpty()) return

    antiphonList.forEachIndexed { index, ant ->
        val block = psalmBlocks.getOrNull(index)
        AntiphonPsalmSection(antiphon = ant, block = block, index = index + 1)
    }

    // If we have psalm blocks but no antiphons, show bare psalm text
    if (antiphonList.isEmpty()) {
        psalmBlocks.forEachIndexed { index, block ->
            val versesText = block.parseBlocks().versesText
            if (versesText.isNotBlank()) {
                PsalmTextSection(versesText = versesText, index = index + 1)
            }
        }
    }
}

// ─────────────────────────────────────────────────────────────────────────────
//  VESPERS antiphon + psalm pairs
//  Uses antVespers1-3 preferred, falls back to ant1-ant3
// ─────────────────────────────────────────────────────────────────────────────
@Composable
private fun VespersAntiphonPsalmPairs(office: DivineOffice, psalms: List<DivineOfficePsalm>) {
    // Prefer Vespers-specific antiphons
    val antiphonList = listOfNotNull(
        office.antVespera1, office.antVespera2, office.antVespera3,
    ).ifEmpty {
        listOfNotNull(office.ant1, office.ant2, office.ant3)
    }
    val psalmBlocks = psalms.filter { it.officeType == "Vespers" }

    if (antiphonList.isEmpty() && psalmBlocks.isEmpty()) return

    antiphonList.forEachIndexed { index, ant ->
        val block = psalmBlocks.getOrNull(index)
        AntiphonPsalmSection(antiphon = ant, block = block, index = index + 1)
    }

    if (antiphonList.isEmpty()) {
        psalmBlocks.forEachIndexed { index, block ->
            val versesText = block.parseBlocks().versesText
            if (versesText.isNotBlank()) {
                PsalmTextSection(versesText = versesText, index = index + 1)
            }
        }
    }
}

// ─────────────────────────────────────────────────────────────────────────────
//  Antiphon + Psalm section (with Gloria Patri in the middle)
//  Shows: [Ant] Gloria Patri [Ant]
// ─────────────────────────────────────────────────────────────────────────────
@Composable
private fun AntiphonPsalmSection(
    antiphon: String?,
    block: DivineOfficePsalm?,
    index: Int,
) {
    if (antiphon.isNullOrBlank() && (block == null || block.parseBlocks().versesText.isBlank())) return

    SectionHeader("Psalm $index")
    Spacer(modifier = Modifier.height(4.dp))

    // Antiphon BEFORE
    if (!antiphon.isNullOrBlank()) {
        SectionSubtext(antiphon)
        Spacer(modifier = Modifier.height(4.dp))
    }

    // Psalm verses
    if (block != null) {
        val formattedVerses = block.parseBlocks().versesText.formatVerses()
        formattedVerses.forEach { verse ->
            Text(
                text = verse,
                style = MaterialTheme.typography.bodyMedium,
                color = MaterialTheme.colorScheme.onSurface,
            )
        }
        Spacer(modifier = Modifier.height(8.dp))
    }

    // Gloria Patri
    GloriaPatri()
    Spacer(modifier = Modifier.height(4.dp))

    // Antiphon AFTER (repeat)
    if (!antiphon.isNullOrBlank()) {
        SectionSubtext(antiphon)
    }

    Spacer(modifier = Modifier.height(12.dp))
}

// ─────────────────────────────────────────────────────────────────────────────
//  Psalm-only section (no antiphon)
// ─────────────────────────────────────────────────────────────────────────────
@Composable
private fun PsalmTextSection(versesText: String, index: Int) {
    SectionHeader("Psalm $index")
    Spacer(modifier = Modifier.height(4.dp))

    versesText.formatVerses().forEach { verse ->
        Text(
            text = verse,
            style = MaterialTheme.typography.bodyMedium,
            color = MaterialTheme.colorScheme.onSurface,
        )
    }

    Spacer(modifier = Modifier.height(8.dp))
    GloriaPatri()
    Spacer(modifier = Modifier.height(12.dp))
}

// ─────────────────────────────────────────────────────────────────────────────
//  Psalm + Antiphon pair for Matins (single antiphon before/after each psalm)
// ─────────────────────────────────────────────────────────────────────────────
@Composable
private fun PsalmAntiphonPair(
    antiphon: String?,
    psalms: List<DivineOfficePsalm>,
) {
    if (antiphon.isNullOrBlank() && psalms.isEmpty()) return

    psalms.forEach { block ->
        val versesText = block.parseBlocks().versesText

        if (!antiphon.isNullOrBlank()) {
            SectionSubtext(antiphon)
            Spacer(modifier = Modifier.height(4.dp))
        }

        if (versesText.isNotBlank()) {
            versesText.formatVerses().forEach { verse ->
                Text(
                    text = verse,
                    style = MaterialTheme.typography.bodyMedium,
                    color = MaterialTheme.colorScheme.onSurface,
                )
            }
            Spacer(modifier = Modifier.height(8.dp))
            GloriaPatri()
            Spacer(modifier = Modifier.height(4.dp))
        }

        if (!antiphon.isNullOrBlank()) {
            SectionSubtext(antiphon)
        }

        Spacer(modifier = Modifier.height(12.dp))
    }

    // If no psalm blocks but we have an antiphon, just show the antiphon
    if (psalms.isEmpty() && !antiphon.isNullOrBlank()) {
        SectionSubtext(antiphon)
        Spacer(modifier = Modifier.height(12.dp))
    }
}

// ─────────────────────────────────────────────────────────────────────────────
//  Canticle section (Benedictus, Magnificat, Nunc Dimittis)
//  Shows: [Antiphon] Gloria Patri [Antiphon]
// ─────────────────────────────────────────────────────────────────────────────
@Composable
private fun CanticleSection(title: String, antiphon: String?) {
    SectionHeader(title)
    Spacer(modifier = Modifier.height(4.dp))

    if (!antiphon.isNullOrBlank()) {
        SectionSubtext(antiphon)
        Spacer(modifier = Modifier.height(4.dp))
    }

    // The canticle text itself is shown via the canticle antiphon and Gloria Patri.
    // In the current data model, canticles don't have separate text columns —
    // the Gloria Patri bookends the antiphon in the canonical layout.
    GloriaPatri()
    Spacer(modifier = Modifier.height(4.dp))

    if (!antiphon.isNullOrBlank()) {
        SectionSubtext(antiphon)
    }

    Spacer(modifier = Modifier.height(12.dp))
}

// ─────────────────────────────────────────────────────────────────────────────
//  Regina Caeli (Antiphon to Mary — shown during Easter season)
// ─────────────────────────────────────────────────────────────────────────────
@Composable
private fun ReginaCaeliSection() {
    SectionHeader("Antiphon to Mary (Regina Caeli)")
    Spacer(modifier = Modifier.height(4.dp))

    val english = listOf(
        "Queen of Heaven, be joyful,",
        "Alleluia.",
        "He who was worthy to bear you.",
        "Alleluia.",
        "He has risen, as he promised.",
        "Alleluia.",
        "Pray for us to God.",
        "Alleluia.",
    ).joinToString("\n")

    val latin = listOf(
        "Regína cæli, lætáre, allelúia:",
        "quía quem meruísti portáre, allelúia,",
        "resurréxit sicut dixit, allelúia;",
        "ora pro nóbis Deum, allelúja.",
    ).joinToString("\n")

    Text(
        text = english,
        style = MaterialTheme.typography.bodyMedium,
        color = MaterialTheme.colorScheme.onSurfaceVariant,
    )
    Spacer(modifier = Modifier.height(8.dp))
    Text(
        text = latin,
        style = MaterialTheme.typography.bodyMedium,
        fontStyle = FontStyle.Italic,
        color = MaterialTheme.colorScheme.onSurfaceVariant.copy(alpha = 0.75f),
    )
    Spacer(modifier = Modifier.height(12.dp))
}

// ─────────────────────────────────────────────────────────────────────────────
//  Gloria Patri
// ─────────────────────────────────────────────────────────────────────────────
@Composable
private fun GloriaPatri() {
    Text(
        text = "Glory be to the Father and to the Son and to the Holy Spirit,\nas it was in the beginning, is now, and ever shall be, world without end. Amen.",
        style = MaterialTheme.typography.bodySmall,
        fontStyle = FontStyle.Italic,
        color = MaterialTheme.colorScheme.onSurfaceVariant.copy(alpha = 0.7f),
    )
}

// ─────────────────────────────────────────────────────────────────────────────
//  Office card wrapper
// ─────────────────────────────────────────────────────────────────────────────
@Composable
private fun OfficeCard(content: @Composable () -> Unit) {
    Card(
        modifier = Modifier.fillMaxWidth(),
        colors = CardDefaults.cardColors(
            containerColor = MaterialTheme.colorScheme.surfaceVariant,
        ),
    ) {
        Column(modifier = Modifier.padding(16.dp)) {
            content()
        }
    }
}

// ─────────────────────────────────────────────────────────────────────────────
//  Section header (bold label, primary color)
// ─────────────────────────────────────────────────────────────────────────────
@Composable
private fun SectionHeader(label: String) {
    Text(
        text = label,
        style = MaterialTheme.typography.labelLarge,
        fontWeight = FontWeight.Bold,
        color = MaterialTheme.colorScheme.primary,
    )
}

// ─────────────────────────────────────────────────────────────────────────────
//  Section subtext (antiphon text, italic)
// ─────────────────────────────────────────────────────────────────────────────
@Composable
private fun SectionSubtext(text: String) {
    Text(
        text = text,
        style = MaterialTheme.typography.bodyMedium,
        fontStyle = FontStyle.Italic,
        color = MaterialTheme.colorScheme.onSurfaceVariant,
    )
}

// ─────────────────────────────────────────────────────────────────────────────
//  Static text section (no DB lookup)
// ─────────────────────────────────────────────────────────────────────────────
@Composable
private fun StaticTextSection(label: String, text: String) {
    SectionHeader(label)
    Spacer(modifier = Modifier.height(4.dp))
    Text(
        text = text,
        style = MaterialTheme.typography.bodyMedium,
        color = MaterialTheme.colorScheme.onSurfaceVariant,
    )
    Spacer(modifier = Modifier.height(12.dp))
}

// ─────────────────────────────────────────────────────────────────────────────
//  maybeShowField — skip rubric noise, skip cross-references
// ─────────────────────────────────────────────────────────────────────────────
@Composable
private fun maybeShowField(
    label: String,
    value: String?,
    highlighted: Boolean = false,
) {
    val clean = value.sanitizeOfficeField() ?: return
    OfficeField(label = label, value = clean, highlighted = highlighted)
}

/** Strip rubrica noise and cross-references from Divinum Officium data. */
private fun String?.sanitizeOfficeField(): String? {
    if (this == null || isBlank()) return null
    val t = trim()
    // Skip pure rubric notes
    if (t == "(rubrica)" || t == "(rubrica tridentina)") return null
    if (t.startsWith("(rubrica") && t.endsWith(")")) return null
    // Skip cross-references: @Sancti/01-06:Responsory2
    if (t.startsWith("@")) return null
    return t
}

/** Parse verses from psalm_text blocks and strip the "ps:vs:" prefix. */
private fun String.formatVerses(): List<String> {
    return this.lines()
        .map { it.trim() }
        .filter { it.isNotBlank() }
        .mapNotNull { line ->
            val parts = line.split(":", limit = 3)
            if (parts.size >= 3) parts[2].trim() else line
        }
}

// ─────────────────────────────────────────────────────────────────────────────
//  OfficeField — one labelled content block
// ─────────────────────────────────────────────────────────────────────────────
@Composable
private fun OfficeField(
    label: String,
    value: String,
    highlighted: Boolean = false,
) {
    Column(modifier = Modifier.padding(vertical = 6.dp)) {
        Row(verticalAlignment = Alignment.CenterVertically) {
            Text(
                text = label,
                style = MaterialTheme.typography.labelLarge,
                fontWeight = FontWeight.Bold,
                color = if (highlighted) MaterialTheme.colorScheme.primary
                        else MaterialTheme.colorScheme.onSurfaceVariant,
            )
        }
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
