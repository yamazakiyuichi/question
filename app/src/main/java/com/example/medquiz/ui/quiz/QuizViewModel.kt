package com.example.medquiz.ui.quiz

import androidx.lifecycle.*
import com.example.medquiz.data.Question
import com.example.medquiz.repository.QuestionRepository
import kotlinx.coroutines.launch

data class QuizState(
    val question: Question,
    val index: Int,
    val total: Int,
    val selectedAnswer: Int = 0,   // 0=未選択
    val isAnswered: Boolean = false
)

class QuizViewModel(private val repository: QuestionRepository) : ViewModel() {

    private val questions = mutableListOf<Question>()
    private var currentIndex = 0

    private val _state = MutableLiveData<QuizState?>()
    val state: LiveData<QuizState?> = _state

    private val _quizFinished = MutableLiveData<Pair<Int, Int>?>() // correct, total
    val quizFinished: LiveData<Pair<Int, Int>?> = _quizFinished

    private var correctCount = 0

    fun loadQuestions(year: String, category: String, mode: String) = viewModelScope.launch {
        val list = when (mode) {
            "wrong" -> repository.getWrongQuestions().let { flow ->
                val result = mutableListOf<Question>()
                flow.collect { result.addAll(it) }
                result
            }
            else -> {
                val result = mutableListOf<Question>()
                repository.getFilteredQuestions(year, category).collect { result.addAll(it) }
                result
            }
        }
        questions.clear()
        questions.addAll(list.shuffled())
        currentIndex = 0
        correctCount = 0
        if (questions.isNotEmpty()) {
            _state.value = QuizState(questions[0], 0, questions.size)
        } else {
            _state.value = null
        }
    }

    fun selectAnswer(answer: Int) {
        val current = _state.value ?: return
        if (current.isAnswered) return

        val isCorrect = answer == current.question.correctAnswer
        if (isCorrect) correctCount++

        viewModelScope.launch {
            repository.recordAnswer(current.question.id, answer, isCorrect)
        }

        _state.value = current.copy(selectedAnswer = answer, isAnswered = true)
    }

    fun next() {
        currentIndex++
        if (currentIndex >= questions.size) {
            _quizFinished.value = Pair(correctCount, questions.size)
        } else {
            _state.value = QuizState(questions[currentIndex], currentIndex, questions.size)
        }
    }
}

class QuizViewModelFactory(private val repository: QuestionRepository) : ViewModelProvider.Factory {
    override fun <T : ViewModel> create(modelClass: Class<T>): T {
        if (modelClass.isAssignableFrom(QuizViewModel::class.java)) {
            @Suppress("UNCHECKED_CAST")
            return QuizViewModel(repository) as T
        }
        throw IllegalArgumentException("Unknown ViewModel class")
    }
}
