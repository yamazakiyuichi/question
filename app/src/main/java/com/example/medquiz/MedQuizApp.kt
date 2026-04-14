package com.example.medquiz

import android.app.Application
import com.example.medquiz.data.AppDatabase
import com.example.medquiz.repository.QuestionRepository

class MedQuizApp : Application() {

    val database by lazy { AppDatabase.getDatabase(this) }
    val repository by lazy {
        QuestionRepository(database.questionDao(), database.studyRecordDao())
    }
}
