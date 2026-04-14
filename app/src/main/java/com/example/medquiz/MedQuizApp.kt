package com.example.medquiz

import android.app.Application
import com.example.medquiz.data.AppDatabase
import com.example.medquiz.repository.QuestionRepository
import com.example.medquiz.util.JsonImporter
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch

class MedQuizApp : Application() {

    val database by lazy { AppDatabase.getDatabase(this) }
    val repository by lazy {
        QuestionRepository(database.questionDao(), database.studyRecordDao())
    }

    override fun onCreate() {
        super.onCreate()
        // 初回起動時にassetsの問題データを自動ロード
        CoroutineScope(Dispatchers.IO).launch {
            try {
                val count = database.questionDao().getTotalCountOnce()
                if (count == 0) {
                    val json = assets.open("questions.json")
                        .bufferedReader().readText()
                    val questions = JsonImporter.parseJson(json)
                    repository.insertQuestions(questions)
                }
            } catch (e: Exception) {
                e.printStackTrace()
            }
        }
    }
}
