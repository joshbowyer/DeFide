package com.tristinbaker.defide.worker

import android.content.Context
import android.net.Uri
import android.provider.DocumentsContract
import androidx.hilt.work.HiltWorker
import androidx.work.CoroutineWorker
import androidx.work.WorkerParameters
import com.tristinbaker.defide.data.backup.BackupManager
import com.tristinbaker.defide.data.preferences.UserPreferencesRepository
import dagger.assisted.Assisted
import dagger.assisted.AssistedInject
import kotlinx.coroutines.flow.first
import java.time.LocalDate

@HiltWorker
class BackupWorker @AssistedInject constructor(
    @Assisted context: Context,
    @Assisted params: WorkerParameters,
    private val backupManager: BackupManager,
    private val prefsRepository: UserPreferencesRepository,
) : CoroutineWorker(context, params) {

    override suspend fun doWork(): Result {
        val folderUriStr = prefsRepository.preferences.first().autoBackupFolderUri
        if (folderUriStr.isEmpty()) return Result.success()

        val treeUri = Uri.parse(folderUriStr)
        val docUri = DocumentsContract.buildDocumentUriUsingTree(
            treeUri,
            DocumentsContract.getTreeDocumentId(treeUri),
        )
        val date = LocalDate.now().toString().replace("-", "")
        val fileUri = DocumentsContract.createDocument(
            applicationContext.contentResolver,
            docUri,
            "application/json",
            "DeFide_$date.json",
        ) ?: return Result.retry()

        return if (backupManager.exportTo(fileUri).isSuccess) Result.success() else Result.retry()
    }

    companion object {
        const val WORK_NAME = "auto_backup"
    }
}
