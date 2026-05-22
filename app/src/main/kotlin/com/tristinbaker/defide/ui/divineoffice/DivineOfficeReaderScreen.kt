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
import com.tristinbaker.defide.data.preferences.AppRite
import com.tristinbaker.defide.data.model.DivineOfficePsalm
import java.time.format.DateTimeFormatter

// ─────────────────────────────────────────────────────────────────────────────
//  Static text for Compline
// ─────────────────────────────────────────────────────────────────────────────
private const val EXAMINATION_OF_CONSCIENCE_LATIN = """Confíteor Deo omnipoténti
et vobis, fratres et soróres,
quóniam peccávi nimis
cogitatóne, verbo et ópere:
mea culpa, mea culpa, mea máxima culpa.
Ideo precor beátam Maríam semper Vírginem,
omnes Angelos et Sanctos,
et vos, fratres et soróres,
oráre pro me ad Dóminum Deum nostrum.

Misereátur nostri omnípotens Deus,
et dimíssis peccátis nostris,
perdúcat nos ad vitam ætérnam.
Amen."""

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

private const val COMPLETORY_BLESSING = "The Lord grant us a quiet night and a perfect end.\n\nAmen."

private const val GLORIA_PATRI = """Glory be to the Father and to the Son and to the Holy Spirit,
as it was in the beginning, is now, and ever shall be, world without end. Amen."""

private const val REGINA_CAELI_LATIN = """Regína cæli, lætáre, allelúia:
quía quem meruísti portáre, allelúia,
resurréxit sicut dixit, allelúia;
ora pro nóbis Deum, allelúja."""

private const val REGINA_CAELI_ENGLISH = """Queen of Heaven, be joyful,
Alleluia.
He who was worthy to bear you,
Alleluia.
He has risen, as he promised,
Alleluia.
Pray for us to God,
Alleluia."""

private const val OUR_FATHER_LATIN = """Pater noster, qui es in cælis,
sanctificétur nomen tuum;
advéniat régnum tuum;
fiat volúntas tua, sicut in cælo et in terra.
Panem nostrum quotidiánum da nobis hódie;
et dimítte nobis débita nostra,
sicut et nos dimíttimus debitóribus nostris;
et ne nos indúcas in tentatiónem;
sed líbera nos a malo.
Amen."""

private const val OUR_FATHER = """Our Father, who art in heaven,
hallowed be thy name;
thy kingdom come;
thy will be done on earth as it is in heaven.
Give us this day our daily bread;
and forgive us our trespasses
as we forgive those who trespass against us;
and lead us not into temptation,
but deliver us from evil."""

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
    val officeLatin by viewModel.selectedOfficeLatin.collectAsState()
    val psalms by viewModel.selectedPsalms.collectAsState()
    val psalmsLatin by viewModel.selectedPsalmsLatin.collectAsState()
    val selectedDate by viewModel.selectedDate.collectAsState()
    val currentRite by viewModel.currentRite.collectAsState()

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
                        OfficeContentCard(
                            office = o,
                            psalms = psalms,
                            psalmsLatin = psalmsLatin,
                            officeLatin = officeLatin,
                            rite = currentRite,
                        )
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
    psalmsLatin: List<DivineOfficePsalm>,
    officeLatin: DivineOffice?,
    rite: AppRite,
) {
    when (office.officeType) {
        "Laudes"   -> LaudesContent(office, psalms, psalmsLatin, officeLatin, rite)
        "Vespers"  -> VespersContent(office, psalms, psalmsLatin, officeLatin, rite)
        "Matins"   -> MatinsContent(office, psalms, psalmsLatin, officeLatin, rite)
        "Compline", "Completorium" -> CompletoriumContent(office, psalms, psalmsLatin, officeLatin, rite)
        else        -> DefaultOfficeContent(office, psalms, psalmsLatin, officeLatin, rite)
    }
}

// ─────────────────────────────────────────────────────────────────────────────
//  LAUDES
//  Canonical sections (always shown):
//    1. Invitatorium
//    2. Hymn
//    3. Psalm 1 (+ Gloria Patri)
//    4. Psalm 2 (+ Gloria Patri)
//    5. Psalm 3 (+ Gloria Patri)
//    6. Scripture Reading (lectio1)
//    7. Short Responsory
//    8. Canticle Benedictus (+ Gloria Patri)
//    9. Prayers and Intercessions
//   10. Our Father
//   11. Collect
//   12. Conclusion
// ─────────────────────────────────────────────────────────────────────────────
@Composable
private fun LaudesContent(
    office: DivineOffice,
    psalms: List<DivineOfficePsalm>,
    psalmsLatin: List<DivineOfficePsalm>,
    officeLatin: DivineOffice?,
    rite: AppRite,
) {
    OfficeCard {
        // 1. Invitatorium — always Latin in Traditional mode
        val invitText = if (rite == AppRite.TRADITIONAL) officeLatin?.invitatorium ?: office.invitatorium else office.invitatorium
        InvitatoriumSection(invitText)

        // 2. Hymn — Latin in Traditional
        val hymnText = if (rite == AppRite.TRADITIONAL) officeLatin?.hymn ?: office.hymn else office.hymn
        HymnSection(hymnText)

        // 3–5. Psalms 1–3 — Latin antiphons in Traditional
        val laudPsalms = psalms.filter { it.officeType == "Laudes" }
        val getAnt = { idx: Int ->
            if (rite == AppRite.TRADITIONAL) {
                officeLatin?.let {
                    when (idx) { 0 -> it.ant1; 1 -> it.ant2; 2 -> it.ant3; else -> null }
                } ?: when (idx) { 0 -> office.ant1; 1 -> office.ant2; 2 -> office.ant3; else -> null }
            } else {
                when (idx) { 0 -> office.ant1; 1 -> office.ant2; 2 -> office.ant3; else -> null }
            }
        }
        Psalm1Section(laudPsalms.getOrNull(0), getAnt(0))
        Psalm2Section(laudPsalms.getOrNull(1), getAnt(1))
        Psalm3Section(laudPsalms.getOrNull(2), getAnt(2))

        // 6. Scripture Reading — English in Traditional
        ScriptureReadingSection(office.lectio1)

        // 7. Short Responsory — Latin in Traditional
        val respText = if (rite == AppRite.TRADITIONAL) officeLatin?.responsory1 ?: office.responsory1 else office.responsory1
        ShortResponsorySection(respText)

        // 8. Canticle Benedictus — Latin antiphon in Traditional
        val cantAnt = if (rite == AppRite.TRADITIONAL) officeLatin?.ant1 ?: office.ant1 else office.ant1
        CanticleBenedictusSection(cantAnt)

        // 9. Prayers and Intercessions — Latin in Traditional
        val precesText = if (rite == AppRite.TRADITIONAL) officeLatin?.preces ?: office.preces else office.preces
        PrayersSection(precesText)

        // 10. Our Father
        OurFatherSection(rite)

        // 11. Collect — Latin in Traditional
        val oratioText = if (rite == AppRite.TRADITIONAL) officeLatin?.oratio ?: office.oratio else office.oratio
        CollectSection(oratioText)

        // 12. Conclusion — Latin in Traditional
        val conclusioText = if (rite == AppRite.TRADITIONAL) officeLatin?.conclusio ?: office.conclusio else office.conclusio
        ConclusionSection(conclusioText)
    }
}

// ─────────────────────────────────────────────────────────────────────────────
//  VESPERS
//  Canonical sections (always shown):
//    1. Hymn
//    2. Psalm 1 (+ Gloria Patri)
//    3. Psalm 2 (+ Gloria Patri)
//    4. Psalm 3 (+ Gloria Patri)
//    5. Scripture Reading (lectio1)
//    6. Short Responsory
//    7. Canticle Magnificat (+ Gloria Patri)
//    8. Prayers and Intercessions
//    9. Our Father
//   10. Collect
//   11. Conclusion
// ─────────────────────────────────────────────────────────────────────────────
@Composable
private fun VespersContent(
    office: DivineOffice,
    psalms: List<DivineOfficePsalm>,
    psalmsLatin: List<DivineOfficePsalm>,
    officeLatin: DivineOffice?,
    rite: AppRite,
) {
    OfficeCard {
        // 1. Hymn — Latin in Traditional
        val hymnText = if (rite == AppRite.TRADITIONAL) officeLatin?.hymn ?: office.hymn else office.hymn
        HymnSection(hymnText)

        // 2–4. Psalms 1–3 — Latin antiphons in Traditional
        val vespAnt1 = if (rite == AppRite.TRADITIONAL) officeLatin?.antVespera1 ?: officeLatin?.ant1 ?: office.antVespera1 ?: office.ant1 else office.antVespera1 ?: office.ant1
        val vespAnt2 = if (rite == AppRite.TRADITIONAL) officeLatin?.antVespera2 ?: officeLatin?.ant2 ?: office.antVespera2 ?: office.ant2 else office.antVespera2 ?: office.ant2
        val vespAnt3 = if (rite == AppRite.TRADITIONAL) officeLatin?.antVespera3 ?: officeLatin?.ant3 ?: office.antVespera3 ?: office.ant3 else office.antVespera3 ?: office.ant3
        val vespPsalms = psalms.filter { it.officeType == "Vespers" }
        Psalm1Section(vespPsalms.getOrNull(0), vespAnt1)
        Psalm2Section(vespPsalms.getOrNull(1), vespAnt2)
        Psalm3Section(vespPsalms.getOrNull(2), vespAnt3)

        // 5. Scripture Reading — English in Traditional
        ScriptureReadingSection(office.lectio1)

        // 6. Short Responsory — Latin in Traditional
        val respText = if (rite == AppRite.TRADITIONAL) officeLatin?.responsory1 ?: office.responsory1 else office.responsory1
        ShortResponsorySection(respText)

        // 7. Canticle Magnificat — Latin antiphon in Traditional
        val magnAnt = if (rite == AppRite.TRADITIONAL) officeLatin?.antVespera1 ?: officeLatin?.ant1 ?: office.antVespera1 ?: office.ant1 else office.antVespera1 ?: office.ant1
        CanticleMagnificatSection(magnAnt)

        // 8. Prayers and Intercessions — Latin in Traditional
        val precesText = if (rite == AppRite.TRADITIONAL) officeLatin?.preces ?: office.preces else office.preces
        PrayersSection(precesText)

        // 9. Our Father
        OurFatherSection(rite)

        // 10. Collect — Latin in Traditional
        val oratioText = if (rite == AppRite.TRADITIONAL) officeLatin?.oratio ?: office.oratio else office.oratio
        CollectSection(oratioText)

        // 11. Conclusion — Latin in Traditional
        val conclusioText = if (rite == AppRite.TRADITIONAL) officeLatin?.conclusio ?: office.conclusio else office.conclusio
        ConclusionSection(conclusioText)
    }
}

// ─────────────────────────────────────────────────────────────────────────────
//  MATINS
//  Canonical sections (always shown):
//    1. Invitatorium
//    2. Hymn
//    3. Psalm 1 (+ Gloria Patri)
//    4. First Reading
//    5. Responsory 1
//    6. Psalm 2 (+ Gloria Patri)
//    7. Second Reading
//    8. Responsory 2
//    9. Psalm 3 (+ Gloria Patri) — only if lectio3 present
//   10. Third Reading
//   11. Responsory 3
//   12. Te Deum (omitted for feasts)
//   13. Collect
// ─────────────────────────────────────────────────────────────────────────────
@Composable
private fun MatinsContent(
    office: DivineOffice,
    psalms: List<DivineOfficePsalm>,
    psalmsLatin: List<DivineOfficePsalm>,
    officeLatin: DivineOffice?,
    rite: AppRite,
) {
    OfficeCard {
        // 1. Invitatorium — Latin in Traditional
        val invitText = if (rite == AppRite.TRADITIONAL) officeLatin?.invitatorium ?: office.invitatorium else office.invitatorium
        InvitatoriumSection(invitText)

        // 2. Hymn — Latin in Traditional
        val hymnText = if (rite == AppRite.TRADITIONAL) officeLatin?.hymn ?: office.hymn else office.hymn
        HymnSection(hymnText)

        // 3. Psalm 1
        val matinsPsalms = psalms.filter { it.officeType == "Matins" }
        val matAnt1 = if (rite == AppRite.TRADITIONAL) officeLatin?.ant1 ?: office.ant1 else office.ant1
        MatinsPsalm1Section(matinsPsalms.getOrNull(0), matAnt1)

        // 4. First Reading — English in Traditional
        FirstReadingSection(office.lectio1)

        // 5. Responsory 1 — Latin in Traditional
        val r1Text = if (rite == AppRite.TRADITIONAL) officeLatin?.responsory1 ?: office.responsory1 else office.responsory1
        Responsory1Section(r1Text)

        // 6. Psalm 2
        val matAnt2 = if (rite == AppRite.TRADITIONAL) officeLatin?.ant2 ?: office.ant2 else office.ant2
        MatinsPsalm2Section(matinsPsalms.getOrNull(1), matAnt2)

        // 7. Second Reading — English in Traditional
        SecondReadingSection(office.lectio2)

        // 8. Responsory 2 — Latin in Traditional
        val r2Text = if (rite == AppRite.TRADITIONAL) officeLatin?.responsory2 ?: office.responsory2 else office.responsory2
        Responsory2Section(r2Text)

        // 9. Psalm 3 — only if lectio3 is present (feast/commemoratio format)
        if (!office.lectio3.isNullOrBlank()) {
            MatinsPsalm3Section(matinsPsalms.getOrNull(2), office.ant3)
        }

        // 10. Third Reading — English in Traditional
        ThirdReadingSection(office.lectio3)

        // 11. Responsory 3 — Latin in Traditional
        val r3Text = if (rite == AppRite.TRADITIONAL) officeLatin?.responsory3 ?: office.responsory3 else office.responsory3
        Responsory3Section(r3Text)

        // 12. Collect — Latin in Traditional
        val oratioText = if (rite == AppRite.TRADITIONAL) officeLatin?.oratio ?: office.oratio else office.oratio
        CollectSection(oratioText)
    }
}

// ─────────────────────────────────────────────────────────────────────────────
//  COMPLETORY / Completorium
//  Canonical sections (always shown):
//    1. Examination of Conscience
//    2. Hymn
//    3. Antiphon + Psalm (+ Gloria Patri)
//    4. Scripture Reading
//    5. Short Responsory
//    6. Canticle Nunc Dimittis (+ Gloria Patri)
//    7. Collect
//    8. Final Blessing
//    9. Antiphon to Mary (Regina Caeli)
// ─────────────────────────────────────────────────────────────────────────────
@Composable
private fun CompletoriumContent(
    office: DivineOffice,
    psalms: List<DivineOfficePsalm>,
    psalmsLatin: List<DivineOfficePsalm>,
    officeLatin: DivineOffice?,
    rite: AppRite,
) {
    OfficeCard {
        // 1. Examination of Conscience — Latin in Traditional
        ExaminationOfConscienceSection(rite)

        // 2. Hymn — Latin in Traditional
        val hymnText = if (rite == AppRite.TRADITIONAL) officeLatin?.hymn ?: office.hymn else office.hymn
        HymnSection(hymnText)

        // 3. Antiphon + Psalm
        val complineAntiphon = office.matinsAntiphon ?: office.ant1
        val complinePsalms = psalms.filter { it.officeType in listOf("Compline", "Completorium") }
        ComplineAntiphonPsalmSection(complinePsalms.firstOrNull(), complineAntiphon)

        // 4. Scripture Reading
        ScriptureReadingSection(office.lectio1)

        // 5. Short Responsory
        ShortResponsorySection(office.responsory1)

        // 6. Canticle Nunc Dimittis
        CanticleNuncDimittisSection(complineAntiphon)

        // 7. Collect
        CollectSection(office.oratio)

        // 8. Final Blessing
        FinalBlessingSection()

        // 9. Antiphon to Mary
        AntiphonToMarySection(rite)
    }
}

// ─────────────────────────────────────────────────────────────────────────────
//  Default fallback for unknown office types
// ─────────────────────────────────────────────────────────────────────────────
@Composable
private fun DefaultOfficeContent(
    office: DivineOffice,
    psalms: List<DivineOfficePsalm>,
    psalmsLatin: List<DivineOfficePsalm>,
    officeLatin: DivineOffice?,
    rite: AppRite,
) {
    OfficeCard {
        val invitText = if (rite == AppRite.TRADITIONAL) officeLatin?.invitatorium ?: office.invitatorium else office.invitatorium
        InvitatoriumSection(invitText)
        val hymnText = if (rite == AppRite.TRADITIONAL) officeLatin?.hymn ?: office.hymn else office.hymn
        HymnSection(hymnText)
        listOfNotNull(
            office.ant1, office.ant2, office.ant3,
            office.ant4, office.ant5, office.ant6,
            office.ant7, office.ant8, office.ant9,
        ).forEachIndexed { index, ant ->
            OfficeField(label = "Antiphon ${index + 1}", value = ant)
        }
        FirstReadingSection(office.lectio1)
        SecondReadingSection(office.lectio2)
        ThirdReadingSection(office.lectio3)
        Responsory1Section(office.responsory1)
        Responsory2Section(office.responsory2)
        Responsory3Section(office.responsory3)
        PrayersSection(office.preces)
        CollectSection(office.oratio)
        ConclusionSection(office.conclusio)
    }
}

// ─────────────────────────────────────────────────────────────────────────────
//  Individual section composables — each always renders its header + content
//  LAUDES
// ─────────────────────────────────────────────────────────────────────────────
@Composable private fun InvitatoriumSection(value: String?) =
    OfficeField(label = "Invitatorium", value = value ?: "(empty)")

@Composable private fun HymnSection(value: String?) =
    OfficeField(label = "Hymn", value = value ?: "(empty)")

@Composable private fun Psalm1Section(psalm: DivineOfficePsalm?, antiphon: String?) {
    SectionHeader("Psalm 1")
    if (!antiphon.isNullOrBlank()) {
        val clean = antiphon.sanitizeOfficeField()
        if (!clean.isNullOrBlank()) SectionSubtext(clean)
        Spacer(modifier = Modifier.height(4.dp))
    }
    psalm?.let { PsalmVerses(it) }
    Spacer(modifier = Modifier.height(8.dp))
    GloriaPatriLine()
    if (!antiphon.isNullOrBlank()) {
        val clean = antiphon.sanitizeOfficeField()
        if (!clean.isNullOrBlank()) {
            Spacer(modifier = Modifier.height(4.dp))
            SectionSubtext(clean)
        }
    }
    SectionDivider()
}

@Composable private fun Psalm2Section(psalm: DivineOfficePsalm?, antiphon: String?) {
    SectionHeader("Psalm 2")
    if (!antiphon.isNullOrBlank()) {
        val clean = antiphon.sanitizeOfficeField()
        if (!clean.isNullOrBlank()) SectionSubtext(clean)
        Spacer(modifier = Modifier.height(4.dp))
    }
    psalm?.let { PsalmVerses(it) }
    Spacer(modifier = Modifier.height(8.dp))
    GloriaPatriLine()
    if (!antiphon.isNullOrBlank()) {
        val clean = antiphon.sanitizeOfficeField()
        if (!clean.isNullOrBlank()) {
            Spacer(modifier = Modifier.height(4.dp))
            SectionSubtext(clean)
        }
    }
    SectionDivider()
}

@Composable private fun Psalm3Section(psalm: DivineOfficePsalm?, antiphon: String?) {
    SectionHeader("Psalm 3")
    if (!antiphon.isNullOrBlank()) {
        val clean = antiphon.sanitizeOfficeField()
        if (!clean.isNullOrBlank()) SectionSubtext(clean)
        Spacer(modifier = Modifier.height(4.dp))
    }
    psalm?.let { PsalmVerses(it) }
    Spacer(modifier = Modifier.height(8.dp))
    GloriaPatriLine()
    if (!antiphon.isNullOrBlank()) {
        val clean = antiphon.sanitizeOfficeField()
        if (!clean.isNullOrBlank()) {
            Spacer(modifier = Modifier.height(4.dp))
            SectionSubtext(clean)
        }
    }
    SectionDivider()
}

@Composable private fun ScriptureReadingSection(value: String?) =
    OfficeField(label = "Scripture Reading", value = value ?: "(empty)")

@Composable private fun ShortResponsorySection(value: String?) =
    OfficeField(label = "Short Responsory", value = value ?: "(empty)")

@Composable private fun CanticleBenedictusSection(antiphon: String?) {
    SectionHeader("Canticle (Benedictus)")
    if (!antiphon.isNullOrBlank()) {
        val clean = antiphon.sanitizeOfficeField()
        if (!clean.isNullOrBlank()) SectionSubtext(clean)
        Spacer(modifier = Modifier.height(4.dp))
    }
    GloriaPatriLine()
    if (!antiphon.isNullOrBlank()) {
        val clean = antiphon.sanitizeOfficeField()
        if (!clean.isNullOrBlank()) {
            Spacer(modifier = Modifier.height(4.dp))
            SectionSubtext(clean)
        }
    }
    SectionDivider()
}

@Composable private fun PrayersSection(value: String?) =
    OfficeField(label = "Prayers and Intercessions", value = value ?: "(empty)")

@Composable private fun OurFatherSection(rite: AppRite) {
    SectionHeader("Our Father")
    Spacer(modifier = Modifier.height(4.dp))
    val fatherText = if (rite != AppRite.MODERN) OUR_FATHER_LATIN else OUR_FATHER
    Text(
        text = fatherText,
        style = MaterialTheme.typography.bodyMedium,
        color = MaterialTheme.colorScheme.onSurfaceVariant,
    )
    SectionDivider()
}

@Composable private fun CollectSection(value: String?) =
    OfficeField(label = "Collect", value = value ?: "(empty)", highlighted = true)

@Composable private fun ConclusionSection(value: String?) =
    OfficeField(label = "Conclusion", value = value ?: "(empty)")

// ─────────────────────────────────────────────────────────────────────────────
//  VESPERS canticle
// ─────────────────────────────────────────────────────────────────────────────
@Composable private fun CanticleMagnificatSection(antiphon: String?) {
    SectionHeader("Canticle (Magnificat)")
    if (!antiphon.isNullOrBlank()) {
        val clean = antiphon.sanitizeOfficeField()
        if (!clean.isNullOrBlank()) SectionSubtext(clean)
        Spacer(modifier = Modifier.height(4.dp))
    }
    GloriaPatriLine()
    if (!antiphon.isNullOrBlank()) {
        val clean = antiphon.sanitizeOfficeField()
        if (!clean.isNullOrBlank()) {
            Spacer(modifier = Modifier.height(4.dp))
            SectionSubtext(clean)
        }
    }
    SectionDivider()
}

// ─────────────────────────────────────────────────────────────────────────────
//  MATINS
// ─────────────────────────────────────────────────────────────────────────────
@Composable private fun MatinsPsalm1Section(psalm: DivineOfficePsalm?, antiphon: String?) {
    SectionHeader("Psalm 1")
    if (!antiphon.isNullOrBlank()) {
        val clean = antiphon.sanitizeOfficeField()
        if (!clean.isNullOrBlank()) SectionSubtext(clean)
        Spacer(modifier = Modifier.height(4.dp))
    }
    psalm?.let { PsalmVerses(it) }
    Spacer(modifier = Modifier.height(8.dp))
    GloriaPatriLine()
    if (!antiphon.isNullOrBlank()) {
        val clean = antiphon.sanitizeOfficeField()
        if (!clean.isNullOrBlank()) {
            Spacer(modifier = Modifier.height(4.dp))
            SectionSubtext(clean)
        }
    }
    SectionDivider()
}

@Composable private fun FirstReadingSection(value: String?) =
    OfficeField(label = "First Reading", value = value ?: "(empty)")

@Composable private fun Responsory1Section(value: String?) =
    OfficeField(label = "Responsory", value = value ?: "(empty)")

@Composable private fun MatinsPsalm2Section(psalm: DivineOfficePsalm?, antiphon: String?) {
    SectionHeader("Psalm 2")
    if (!antiphon.isNullOrBlank()) {
        val clean = antiphon.sanitizeOfficeField()
        if (!clean.isNullOrBlank()) SectionSubtext(clean)
        Spacer(modifier = Modifier.height(4.dp))
    }
    psalm?.let { PsalmVerses(it) }
    Spacer(modifier = Modifier.height(8.dp))
    GloriaPatriLine()
    if (!antiphon.isNullOrBlank()) {
        val clean = antiphon.sanitizeOfficeField()
        if (!clean.isNullOrBlank()) {
            Spacer(modifier = Modifier.height(4.dp))
            SectionSubtext(clean)
        }
    }
    SectionDivider()
}

@Composable private fun SecondReadingSection(value: String?) =
    OfficeField(label = "Second Reading", value = value ?: "(empty)")

@Composable private fun Responsory2Section(value: String?) =
    OfficeField(label = "Responsory 2", value = value ?: "(empty)")

@Composable private fun MatinsPsalm3Section(psalm: DivineOfficePsalm?, antiphon: String?) {
    SectionHeader("Psalm 3")
    if (!antiphon.isNullOrBlank()) {
        val clean = antiphon.sanitizeOfficeField()
        if (!clean.isNullOrBlank()) SectionSubtext(clean)
        Spacer(modifier = Modifier.height(4.dp))
    }
    psalm?.let { PsalmVerses(it) }
    Spacer(modifier = Modifier.height(8.dp))
    GloriaPatriLine()
    if (!antiphon.isNullOrBlank()) {
        val clean = antiphon.sanitizeOfficeField()
        if (!clean.isNullOrBlank()) {
            Spacer(modifier = Modifier.height(4.dp))
            SectionSubtext(clean)
        }
    }
    SectionDivider()
}

@Composable private fun ThirdReadingSection(value: String?) =
    OfficeField(label = "Third Reading", value = value ?: "(empty)")

@Composable private fun Responsory3Section(value: String?) =
    OfficeField(label = "Responsory 3", value = value ?: "(empty)")

// ─────────────────────────────────────────────────────────────────────────────
//  COMPLETORY
// ─────────────────────────────────────────────────────────────────────────────
@Composable private fun ExaminationOfConscienceSection(rite: AppRite) {
    SectionHeader("Examination of Conscience")
    Spacer(modifier = Modifier.height(4.dp))
    val examText = if (rite == AppRite.TRADITIONAL) EXAMINATION_OF_CONSCIENCE_LATIN else EXAMINATION_OF_CONSCIENCE
    Text(
        text = examText,
        style = MaterialTheme.typography.bodyMedium,
        color = MaterialTheme.colorScheme.onSurfaceVariant,
    )
    SectionDivider()
}

@Composable private fun ComplineAntiphonPsalmSection(psalm: DivineOfficePsalm?, antiphon: String?) {
    SectionHeader("Antiphon + Psalm")
    if (!antiphon.isNullOrBlank()) {
        val clean = antiphon.sanitizeOfficeField()
        if (!clean.isNullOrBlank()) SectionSubtext(clean)
        Spacer(modifier = Modifier.height(4.dp))
    }
    psalm?.let { PsalmVerses(it) }
    Spacer(modifier = Modifier.height(8.dp))
    GloriaPatriLine()
    if (!antiphon.isNullOrBlank()) {
        val clean = antiphon.sanitizeOfficeField()
        if (!clean.isNullOrBlank()) {
            Spacer(modifier = Modifier.height(4.dp))
            SectionSubtext(clean)
        }
    }
    SectionDivider()
}

@Composable private fun CanticleNuncDimittisSection(antiphon: String?) {
    SectionHeader("Canticle (Nunc Dimittis)")
    if (!antiphon.isNullOrBlank()) {
        val clean = antiphon.sanitizeOfficeField()
        if (!clean.isNullOrBlank()) SectionSubtext(clean)
        Spacer(modifier = Modifier.height(4.dp))
    }
    GloriaPatriLine()
    if (!antiphon.isNullOrBlank()) {
        val clean = antiphon.sanitizeOfficeField()
        if (!clean.isNullOrBlank()) {
            Spacer(modifier = Modifier.height(4.dp))
            SectionSubtext(clean)
        }
    }
    SectionDivider()
}

@Composable private fun FinalBlessingSection() {
    SectionHeader("Blessing")
    Spacer(modifier = Modifier.height(4.dp))
    Text(
        text = COMPLETORY_BLESSING,
        style = MaterialTheme.typography.bodyMedium,
        color = MaterialTheme.colorScheme.onSurfaceVariant,
    )
    SectionDivider()
}

@Composable private fun AntiphonToMarySection(rite: AppRite) {
    SectionHeader("Antiphon to Mary (Regina Caeli)")
    Spacer(modifier = Modifier.height(4.dp))
    // Traditional mode: Latin only; other modes: English first then Latin
    val showLatinOnly = rite == AppRite.TRADITIONAL
    if (!showLatinOnly) {
        Text(
            text = REGINA_CAELI_ENGLISH,
            style = MaterialTheme.typography.bodyMedium,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
        )
    }
    Spacer(modifier = Modifier.height(8.dp))
    Text(
        text = REGINA_CAELI_LATIN,
        style = MaterialTheme.typography.bodyMedium,
        fontStyle = FontStyle.Italic,
        color = MaterialTheme.colorScheme.onSurfaceVariant.copy(alpha = 0.75f),
    )
    SectionDivider()
}

// ─────────────────────────────────────────────────────────────────────────────
//  Shared helpers
// ─────────────────────────────────────────────────────────────────────────────

/** Render all verses from a psalm block, stripping the "ps:vs:" prefix. */
@Composable
private fun PsalmVerses(psalm: DivineOfficePsalm) {
    val versesText = psalm.parseBlocks().versesText
    versesText.formatVerses().forEach { verse ->
        Text(
            text = verse,
            style = MaterialTheme.typography.bodyMedium,
            color = MaterialTheme.colorScheme.onSurface,
        )
    }
}

/** Strip rubrica noise and cross-references from Divinum Officium data. */
private fun String?.sanitizeOfficeField(): String? {
    if (this == null || isBlank()) return null
    val t = trim()
    if (t == "(rubrica)" || t == "(rubrica tridentina)") return null
    if (t.startsWith("(rubrica") && t.endsWith(")")) return null
    if (t.startsWith("@")) return null
    return t
}

/** Strip the "ps:vs:" prefix from each line of a verses block. */
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
//  Section header
// ─────────────────────────────────────────────────────────────────────────────
@Composable
private fun SectionHeader(label: String) {
    Spacer(modifier = Modifier.height(8.dp))
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
//  Gloria Patri line
// ─────────────────────────────────────────────────────────────────────────────
@Composable
private fun GloriaPatriLine() {
    Text(
        text = GLORIA_PATRI,
        style = MaterialTheme.typography.bodySmall,
        fontStyle = FontStyle.Italic,
        color = MaterialTheme.colorScheme.onSurfaceVariant.copy(alpha = 0.7f),
    )
}

// ─────────────────────────────────────────────────────────────────────────────
//  Section divider
// ─────────────────────────────────────────────────────────────────────────────
@Composable
private fun SectionDivider() {
    Spacer(modifier = Modifier.height(8.dp))
    HorizontalDivider(
        color = MaterialTheme.colorScheme.outlineVariant.copy(alpha = 0.5f),
    )
}

// ─────────────────────────────────────────────────────────────────────────────
//  OfficeField — labelled content block
// ─────────────────────────────────────────────────────────────────────────────
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
        SectionDivider()
    }
}
