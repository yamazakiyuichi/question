package com.example.medquiz.ui.home

import androidx.lifecycle.*
import com.example.medquiz.repository.QuestionRepository
import kotlinx.coroutines.launch

class HomeViewModel(private val repository: QuestionRepository) : ViewModel() {

    val totalCount = repository.getTotalCount().asLiveData()
    val studiedCount = repository.getStudiedQuestionCount().asLiveData()
    val correctCount = repository.getCorrectQuestionCount().asLiveData()
    val years = repository.getAllYears().asLiveData()
    val categories = repository.getAllCategories().asLiveData()

    private val _selectedYear = MutableLiveData("")
    private val _selectedCategory = MutableLiveData("")

    val selectedYear: LiveData<String> = _selectedYear
    val selectedCategory: LiveData<String> = _selectedCategory

    fun setYear(year: String) { _selectedYear.value = year }
    fun setCategory(category: String) { _selectedCategory.value = category }

    fun getFilteredQuestions() = repository.getFilteredQuestions(
        _selectedYear.value ?: "",
        _selectedCategory.value ?: ""
    ).asLiveData()

    fun resetProgress() = viewModelScope.launch {
        repository.resetProgress()
    }

    fun importQuestions(jsonString: String) = viewModelScope.launch {
        val questions = com.example.medquiz.util.JsonImporter.parseJson(jsonString)
        repository.deleteAllQuestions()
        repository.insertQuestions(questions)
    }
}

class HomeViewModelFactory(private val repository: QuestionRepository) : ViewModelProvider.Factory {
    override fun <T : ViewModel> create(modelClass: Class<T>): T {
        if (modelClass.isAssignableFrom(HomeViewModel::class.java)) {
            @Suppress("UNCHECKED_CAST")
            return HomeViewModel(repository) as T
        }
        throw IllegalArgumentException("Unknown ViewModel class")
    }
}
