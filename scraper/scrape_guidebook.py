#!/usr/bin/env python3
"""
Scraper for https://hcit.guidebook.jp/kakomon/
Fetches 医療情報技師 past exam questions (2016-2022, excluding 2020).
"""

import re
import json
import time
import requests
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

CATEGORY_MAP = {
    "j": "情報処理技術系",
    "m": "医学・医療系",
    "s": "医療情報システム系",
}

PAGES = [
    "2016-j-q1","2016-j-q2","2016-j-q3","2016-j-q4","2016-j-q5",
    "2016-m-q1","2016-m-q2","2016-m-q3","2016-m-q4","2016-m-q5",
    "2016-s-q1","2016-s-q2","2016-s-q3","2016-s-q4","2016-s-q5","2016-s-q6",
    "2017-j-q1","2017-j-q2","2017-j-q3","2017-j-q4","2017-j-q5",
    "2017-m-q1","2017-m-q2","2017-m-q3","2017-m-q4","2017-m-q5",
    "2017-s-q1","2017-s-q2","2017-s-q3","2017-s-q4","2017-s-q5","2017-s-q6",
    "2018-j-q1","2018-j-q2","2018-j-q3","2018-j-q4","2018-j-q5",
    "2018-m-q1","2018-m-q2","2018-m-q3","2018-m-q4","2018-m-q5",
    "2018-s-q1","2018-s-q2","2018-s-q3","2018-s-q4","2018-s-q5","2018-s-q6",
    "2019-j-q1","2019-j-q2","2019-j-q3","2019-j-q4","2019-j-q5",
    "2019-m-q1","2019-m-q2","2019-m-q3","2019-m-q4","2019-m-q5",
    "2019-s-q1","2019-s-q2","2019-s-q3","2019-s-q4","2019-s-q5","2019-s-q6",
    "2021-j-q1","2021-j-q2","2021-j-q3","2021-j-q4","2021-j-q5",
    "2021-m-q1","2021-m-q2","2021-m-q3","2021-m-q4","2021-m-q5",
    "2021-s-q1","2021-s-q2","2021-s-q3","2021-s-q4","2021-s-q5","2021-s-q6",
    "2022-j-q1","2022-j-q2","2022-j-q3","2022-j-q4","2022-j-q5",
    "2022-m-q1","2022-m-q2","2022-m-q3","2022-m-q4","2022-m-q5",
    "2022-s-q1","2022-s-q2","2022-s-q3","2022-s-q4","2022-s-q5","2022-s-q6",
]

# Lines to skip (noise)
NOISE_RE = re.compile(
    r'^(医療情報技師|診療録|医療情報技師の館|https?://|&nbsp;|を参照する|'
    r'医療情報技師試験対策wiki|\(別画面で開きます\)|【参考文献|^\s*$)'
)


def parse_answers(s):
    """Parse '解答:3' or '正答:1、3' or '解答:3 ,4' -> list of ints."""
    s = re.sub(r'^(解答|正答)[：:]', '', s).strip()
    parts = re.split(r'[、,\s・]+', s)
    result = []
    for p in parts:
        p = p.strip().rstrip('。')
        if p.isdigit():
            result.append(int(p))
    return result


def parse_page(slug, html):
    year, cat_code, _ = slug.split("-", 2)
    category = CATEGORY_MAP.get(cat_code, cat_code)

    soup = BeautifulSoup(html, "html.parser")
    content = soup.find("div", class_="entry-content") or soup.find("article") or soup

    for tag in content.find_all(["script", "style", "nav", "header", "footer"]):
        tag.decompose()

    lines = []
    for elem in content.descendants:
        if isinstance(elem, str):
            # Split on newlines embedded in text nodes
            for part in elem.split("\n"):
                t = part.strip()
                if t:
                    lines.append(t)

    questions = []
    current_q = None
    # states: choices, explanation, memo, done
    state = None

    # Question start: 問N: / 問N： / 問NN 削除問題:
    Q_RE = re.compile(r'^問(\d+)(?:[^\d：:][^：:]*)?[：:](.+)')
    ANS_RE = re.compile(r'^(解答|正答)[：:]')

    for line in lines:
        if NOISE_RE.match(line):
            continue

        # New question?
        m = Q_RE.match(line)
        if m:
            if current_q:
                questions.append(current_q)
            q_num = int(m.group(1))
            q_text = m.group(2).strip()
            current_q = {
                "year": year,
                "category": category,
                "question_number": q_num,
                "question_text": q_text,
                "choices": [],
                "correct_answers": [],
                "explanation_parts": [],
            }
            state = "choices"
            continue

        if current_q is None:
            continue

        # Answer line?
        if ANS_RE.match(line):
            current_q["correct_answers"] = parse_answers(line)
            state = "done"
            continue

        # Explanation/memo section header?
        if line in ("解説", "メモ"):
            state = "explanation"
            continue

        if state == "choices":
            # Accept up to 5 choices; stop if we hit what looks like explanation
            if len(current_q["choices"]) < 5:
                current_q["choices"].append(line)

        elif state == "explanation":
            current_q["explanation_parts"].append(line)

        # In "done" state, skip everything until next question

    if current_q:
        questions.append(current_q)

    # Convert to output format
    result = []
    for q in questions:
        choices = q["choices"]
        while len(choices) < 5:
            choices.append("")

        answers = q["correct_answers"]
        correct_answer = answers[0] if answers else 0

        # Build explanation string
        explanation = " ".join(q["explanation_parts"])
        if len(answers) > 1:
            ans_str = "、".join(str(a) for a in answers)
            prefix = f"正答は{ans_str}。"
            explanation = prefix + ("　" + explanation if explanation else "")

        result.append({
            "year": q["year"],
            "category": q["category"],
            "question_number": q["question_number"],
            "question_text": q["question_text"],
            "choice1": choices[0],
            "choice2": choices[1],
            "choice3": choices[2],
            "choice4": choices[3],
            "choice5": choices[4],
            "correct_answer": correct_answer,
            "correct_answers": answers,
            "explanation": explanation,
        })

    return result


def scrape_all():
    all_questions = []
    session = requests.Session()
    session.headers.update(HEADERS)

    for idx, slug in enumerate(PAGES):
        url = f"https://hcit.guidebook.jp/{slug}/"
        print(f"[{idx+1}/{len(PAGES)}] {slug} ...", end=" ", flush=True)

        for attempt in range(3):
            try:
                resp = session.get(url, timeout=20)
                if resp.status_code == 200:
                    qs = parse_page(slug, resp.text)
                    all_questions.extend(qs)
                    print(f"OK ({len(qs)} questions)")
                    break
                else:
                    print(f"HTTP {resp.status_code}", end=" ")
                    if attempt < 2:
                        time.sleep(3)
            except Exception as e:
                print(f"Error: {e}", end=" ")
                if attempt < 2:
                    time.sleep(3)
        else:
            print("FAILED")

        time.sleep(1.0)

    return all_questions


if __name__ == "__main__":
    print(f"Scraping {len(PAGES)} pages...")
    questions = scrape_all()
    print(f"\nTotal: {len(questions)} questions")

    # Filter out questions with no correct answer (likely parse errors)
    valid = [q for q in questions if q["correct_answer"] > 0]
    invalid = len(questions) - len(valid)
    if invalid:
        print(f"Skipped {invalid} questions with no detected answer")

    out_path = "/home/user/question/scraper/questions_guidebook.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(valid, f, ensure_ascii=False, indent=2)
    print(f"Saved {len(valid)} questions to {out_path}")
