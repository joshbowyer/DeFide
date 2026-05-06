package com.tristinbaker.defide.widget

import android.content.Context
import android.content.Intent
import androidx.glance.appwidget.GlanceAppWidgetManager
import androidx.glance.appwidget.GlanceAppWidgetReceiver
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.launch

class VotdWidgetReceiver : GlanceAppWidgetReceiver() {
    override val glanceAppWidget = VotdWidget()

    override fun onReceive(context: Context, intent: Intent) {
        super.onReceive(context, intent)
        if (intent.action == Intent.ACTION_DATE_CHANGED) {
            val pendingResult = goAsync()
            CoroutineScope(Dispatchers.IO + SupervisorJob()).launch {
                try {
                    GlanceAppWidgetManager(context)
                        .getGlanceIds(VotdWidget::class.java)
                        .forEach { VotdWidget().update(context, it) }
                } finally {
                    pendingResult.finish()
                }
            }
        }
    }
}
