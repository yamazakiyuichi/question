package com.example.medquiz.ui.review

import androidx.lifecycle.*
import com.example.medquiz.repository.QuestionRepository

class ReviewViewModel(repository: QuestionRepository) : ViewModel() {
    val wrongQuestions = repository.getWrongQuestions().asLiveData()
}

class ReviewViewModelFactory(private val repository: QuestionRepository) : ViewModelProvider.Factory {
    override fun <T : ViewModel> create(modelClass: Class<T>): T {
        if (modelClass.isAssignableFrom(ReviewViewModel::class.java)) {
            @Suppress("UNCHECKED_CAST")
            return ReviewViewModel(repository) as T
        }
        throw IllegalArgumentException("Unknown ViewModel class")
    }
}
