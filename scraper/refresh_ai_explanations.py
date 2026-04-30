import difflib
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
QUESTIONS_JSON = ROOT / "scraper" / "questions_iryoujyouhou.json"
SUMMARY_JSON = ROOT / "scraper" / "iryoujyouhou_summary.json"
DOCS_INDEX = ROOT / "docs" / "index.html"


def normalize(text: str | None) -> str:
    return re.sub(r"\s+", " ", (text or "").strip())


def shorten(text: str | None, limit: int) -> str:
    value = clean_generated_text(normalize(text))
    if len(value) <= limit:
        return value
    return value[: limit - 1].rstrip() + "..."


def clean_generated_text(text: str) -> str:
    value = normalize(text)
    value = re.sub(r"^#+\s*", "", value)
    value = re.sub(r"この(?:設問|問題)は[、,\s]*", "", value)
    value = value.replace("この問題では", "ここでは")
    value = value.replace("この設問では", "ここでは")
    value = value.replace("正解は", "選ぶ根拠は")
    value = value.replace("正答は", "選ぶ根拠は")
    value = value.replace("答えは", "結論は")
    value = value.replace("について解説する。", "を確認します。")
    value = value.replace("。。", "。")
    value = value.replace("。。", "。")
    return value.strip()


def choice_text(question: dict, number: int) -> str:
    return normalize(question.get(f"choice{number}", ""))


def answer_numbers(question: dict) -> list[int]:
    answers = question.get("correct_answers") or []
    if not answers and question.get("correct_answer"):
        answers = [question.get("correct_answer")]

    normalized = []
    for answer in answers:
        if str(answer).isdigit():
            number = int(answer)
            if 1 <= number <= 5:
                normalized.append(number)
    return normalized


def infer_condition(question_text: str) -> str:
    text = normalize(question_text)
    if any(term in text for term in ("誤っている", "誤り", "正しくない", "適切でない", "不適切")):
        return "誤り・不適切な記述を選ぶ条件"
    if any(term in text for term in ("含まれない", "属さない", "必要でない", "関係がない", "でないのは", "ないのはどれか")):
        return "含まれない・該当しない項目を選ぶ条件"
    if any(term in text for term in ("正しい", "適切", "妥当", "できる", "該当する", "分類される", "含まれる", "必要な", "行うべき")):
        return "正しい内容として選ぶ条件"
    return "設問が求める条件"


def is_multiple_choice(question_text: str, answers: list[int]) -> bool:
    text = normalize(question_text)
    return len(answers) > 1 or any(term in text for term in ("２つ", "2つ", "二つ", "複数"))


def trim_reference_text(explanation: str) -> str:
    # Keep the explanation relevant to the current question. Some source comments
    # include another year's question as a reference, which should not drive AI text.
    text = explanation or ""
    cut_patterns = ("【問", "参考文献", "参考サイト", "http://", "https://")
    indexes = [text.find(pattern) for pattern in cut_patterns if text.find(pattern) != -1]
    if indexes:
        text = text[: min(indexes)]
    return text.strip()


def split_sentences(text: str) -> list[str]:
    text = normalize(trim_reference_text(text))
    if not text:
        return []
    return [part.strip() for part in re.split(r"(?<=[。！？])\s*", text) if part.strip()]


def parse_option_notes(explanation: str) -> dict[int, str]:
    text = trim_reference_text(explanation)
    if not text:
        return {}

    line_notes: dict[int, list[str]] = {}
    current: int | None = None
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        match = re.match(r"^(?:選択肢)?\s*([1-5])\s*[\)）．.、:：]\s*(.*)$", line)
        if match:
            current = int(match.group(1))
            line_notes.setdefault(current, []).append(match.group(2).strip())
        elif current is not None:
            line_notes.setdefault(current, []).append(line)

    notes = {number: clean_generated_text(" ".join(parts)) for number, parts in line_notes.items()}
    notes = {number: note for number, note in notes.items() if note}
    if notes:
        return notes

    markers = list(re.finditer(r"(?<!\d)([1-5])\s*[\)）]", normalize(text)))
    if not markers:
        return {}

    inline_notes: dict[int, str] = {}
    normalized_text = normalize(text)
    for index, marker in enumerate(markers):
        number = int(marker.group(1))
        start = marker.end()
        end = markers[index + 1].start() if index + 1 < len(markers) else len(normalized_text)
        note = clean_generated_text(normalized_text[start:end])
        if note:
            inline_notes[number] = note
    return inline_notes


def support_from_explanation(explanation: str, condition: str) -> str:
    sentences = split_sentences(explanation)
    if not sentences:
        return ""
    support = shorten(" ".join(sentences[:2]), 130)
    if "誤り" in condition or "含まれない" in condition:
        return f"根拠: 補足情報と正答肢を照らすと、正答肢が設問の求める「誤り／該当しない側」に当たります。補足要点: {support}"
    return f"根拠: 補足情報と正答肢を照らすと、正答肢が設問の求める内容に一致します。補足要点: {support}"


def generate_ai_explanation(question: dict) -> str:
    question_text = normalize(question.get("question_text", ""))
    condition = infer_condition(question_text)
    answers = answer_numbers(question)
    answer_labels = [f"{number}) {shorten(choice_text(question, number), 72)}" for number in answers]
    notes = parse_option_notes(question.get("explanation", ""))
    lines: list[str] = []

    if answer_labels:
        lines.append(f"照合結果: {condition}に合わせると、選ぶ選択肢は{ '、'.join(answer_labels) }です。")
    else:
        lines.append(f"照合結果: {condition}に合わせて、選択肢を順に照合します。")

    answer_notes = [f"{number}) {shorten(notes[number], 90)}" for number in answers if notes.get(number)]
    if answer_notes:
        lines.append(
            "根拠: 正答肢の文言と補足情報を突き合わせると、"
            + " / ".join(answer_notes)
            + " となり、設問条件に合います。"
        )
    else:
        support = support_from_explanation(question.get("explanation", ""), condition)
        if support:
            lines.append(support)
        else:
            lines.append("根拠: 正答肢の語句を設問のキーワードに戻して読むと、対象・役割・手順・数値条件がずれません。")

    wrong_numbers = [number for number in range(1, 6) if choice_text(question, number) and number not in answers]
    wrong_with_notes = [number for number in wrong_numbers if notes.get(number)]
    if wrong_with_notes:
        parts = [
            f"{number}) {shorten(choice_text(question, number), 38)}: {shorten(notes[number], 48)}"
            for number in wrong_with_notes[:4]
        ]
        if len(wrong_with_notes) > 4:
            parts.append("残りも同じ照合軸では外れます")
        lines.append(clean_generated_text("除外判断: " + " / ".join(parts) + "。"))
    else:
        examples = ", ".join(f"{number}) {shorten(choice_text(question, number), 30)}" for number in wrong_numbers[:3])
        if examples:
            lines.append(f"除外判断: {examples} などは、正答として指定された条件には合わないため選びません。")

    if is_multiple_choice(question_text, answers):
        lines.append("複数選択なので、同じ照合条件で正答数分を拾い、片方だけで判断を止めないことが重要です。")

    return "\n".join(clean_generated_text(line) for line in lines)


def replace_builtin_questions(index_html: str, questions: list[dict]) -> str:
    serialized = json.dumps(questions, ensure_ascii=False, separators=(",", ":"))
    next_html, count = re.subn(
        r"const BUILTIN_QUESTIONS = [\s\S]*?\n\n// ========== STATE",
        lambda _: f"const BUILTIN_QUESTIONS = {serialized};\n\n// ========== STATE",
        index_html,
        count=1,
    )
    if count != 1:
        raise RuntimeError("Could not replace BUILTIN_QUESTIONS in docs/index.html")
    return next_html


def similarity_stats(questions: list[dict]) -> dict[str, float | int]:
    ratios = []
    same = 0
    high = 0
    for question in questions:
        explanation = normalize(question.get("explanation", ""))
        ai_explanation = normalize(question.get("ai_explanation", ""))
        if not explanation or not ai_explanation:
            continue
        ratio = difflib.SequenceMatcher(None, explanation, ai_explanation).ratio()
        ratios.append(ratio)
        if explanation == ai_explanation:
            same += 1
        if ratio >= 0.8:
            high += 1
    return {
        "same": same,
        "high_similarity_0_8": high,
        "average_similarity": round(sum(ratios) / len(ratios), 4) if ratios else 0,
    }


def main() -> int:
    questions = json.loads(QUESTIONS_JSON.read_text(encoding="utf-8"))
    before = similarity_stats(questions)

    for question in questions:
        question["ai_explanation"] = generate_ai_explanation(question)

    after = similarity_stats(questions)
    QUESTIONS_JSON.write_text(json.dumps(questions, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    summary = json.loads(SUMMARY_JSON.read_text(encoding="utf-8"))
    initial_before = summary.get("ai_analysis_similarity_initial_before") or before
    summary.pop("ai_analysis_similarity_before", None)
    summary.update(
        {
            "ai_explanation_count": len(questions),
            "ai_analysis_rewrite_note": "全問の設問・選択肢・正答・元解説を照合し、AI解析回答を元解説のコピーではない別文に再生成。",
            "ai_analysis_similarity_initial_before": initial_before,
            "ai_analysis_similarity_after": after,
        }
    )
    SUMMARY_JSON.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    index_html = DOCS_INDEX.read_text(encoding="utf-8")
    DOCS_INDEX.write_text(replace_builtin_questions(index_html, questions), encoding="utf-8")

    print(json.dumps({"updated": len(questions), "before": before, "after": after}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
