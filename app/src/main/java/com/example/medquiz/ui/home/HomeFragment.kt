package com.example.medquiz.ui.home

import android.app.Activity
import android.content.Intent
import android.net.Uri
import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.ArrayAdapter
import android.widget.Toast
import androidx.activity.result.contract.ActivityResultContracts
import androidx.appcompat.app.AlertDialog
import androidx.core.os.bundleOf
import androidx.fragment.app.Fragment
import androidx.fragment.app.viewModels
import androidx.navigation.fragment.findNavController
import com.example.medquiz.MedQuizApp
import com.example.medquiz.R
import com.example.medquiz.databinding.FragmentHomeBinding

class HomeFragment : Fragment() {

    private var _binding: FragmentHomeBinding? = null
    private val binding get() = _binding!!

    private val viewModel: HomeViewModel by viewModels {
        HomeViewModelFactory((requireActivity().application as MedQuizApp).repository)
    }

    private val filePickerLauncher = registerForActivityResult(
        ActivityResultContracts.StartActivityForResult()
    ) { result ->
        if (result.resultCode == Activity.RESULT_OK) {
            result.data?.data?.let { uri -> importJson(uri) }
        }
    }

    override fun onCreateView(inflater: LayoutInflater, container: ViewGroup?, savedInstanceState: Bundle?): View {
        _binding = FragmentHomeBinding.inflate(inflater, container, false)
        return binding.root
    }

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)

        // 統計表示
        viewModel.totalCount.observe(viewLifecycleOwner) { total ->
            binding.textTotalCount.text = "総問題数: ${total ?: 0}問"
        }
        viewModel.studiedCount.observe(viewLifecycleOwner) { studied ->
            binding.textStudiedCount.text = "学習済み: ${studied ?: 0}問"
        }
        viewModel.correctCount.observe(viewLifecycleOwner) { correct ->
            binding.textCorrectCount.text = "正解済み: ${correct ?: 0}問"
        }

        // 年度フィルター
        val yearItems = mutableListOf("全年度")
        val yearAdapter = ArrayAdapter(requireContext(), android.R.layout.simple_spinner_item, yearItems).also {
            it.setDropDownViewResource(android.R.layout.simple_spinner_dropdown_item)
        }
        binding.spinnerYear.adapter = yearAdapter
        viewModel.years.observe(viewLifecycleOwner) { years ->
            yearItems.clear()
            yearItems.add("全年度")
            yearItems.addAll(years)
            yearAdapter.notifyDataSetChanged()
        }

        // カテゴリフィルター
        val catItems = mutableListOf("全カテゴリ")
        val catAdapter = ArrayAdapter(requireContext(), android.R.layout.simple_spinner_item, catItems).also {
            it.setDropDownViewResource(android.R.layout.simple_spinner_dropdown_item)
        }
        binding.spinnerCategory.adapter = catAdapter
        viewModel.categories.observe(viewLifecycleOwner) { cats ->
            catItems.clear()
            catItems.add("全カテゴリ")
            catItems.addAll(cats)
            catAdapter.notifyDataSetChanged()
        }

        // クイズ開始
        binding.btnStartQuiz.setOnClickListener {
            val year = if (binding.spinnerYear.selectedItemPosition == 0) ""
                       else yearItems[binding.spinnerYear.selectedItemPosition]
            val cat = if (binding.spinnerCategory.selectedItemPosition == 0) ""
                      else catItems[binding.spinnerCategory.selectedItemPosition]
            findNavController().navigate(
                R.id.action_homeFragment_to_quizFragment,
                bundleOf("year" to year, "category" to cat, "mode" to "all")
            )
        }

        // 苦手問題のみ
        binding.btnStartWrong.setOnClickListener {
            findNavController().navigate(
                R.id.action_homeFragment_to_quizFragment,
                bundleOf("year" to "", "category" to "", "mode" to "wrong")
            )
        }

        // JSONインポート
        binding.btnImport.setOnClickListener {
            val intent = Intent(Intent.ACTION_GET_CONTENT).apply {
                type = "application/json"
                addCategory(Intent.CATEGORY_OPENABLE)
            }
            filePickerLauncher.launch(intent)
        }

        // 進捗リセット
        binding.btnResetProgress.setOnClickListener {
            AlertDialog.Builder(requireContext())
                .setTitle("進捗をリセット")
                .setMessage("学習履歴を全て削除しますか？")
                .setPositiveButton("リセット") { _, _ ->
                    viewModel.resetProgress()
                    Toast.makeText(requireContext(), "進捗をリセットしました", Toast.LENGTH_SHORT).show()
                }
                .setNegativeButton("キャンセル", null)
                .show()
        }
    }

    private fun importJson(uri: Uri) {
        try {
            val inputStream = requireContext().contentResolver.openInputStream(uri)
            val json = inputStream?.bufferedReader()?.readText() ?: return
            viewModel.importQuestions(json)
            Toast.makeText(requireContext(), "問題をインポートしました", Toast.LENGTH_SHORT).show()
        } catch (e: Exception) {
            Toast.makeText(requireContext(), "インポートに失敗しました: ${e.message}", Toast.LENGTH_LONG).show()
        }
    }

    override fun onDestroyView() {
        super.onDestroyView()
        _binding = null
    }
}
