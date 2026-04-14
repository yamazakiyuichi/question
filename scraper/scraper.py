#!/usr/bin/env python3
"""
医療情報技師試験 過去問スクレイパー
https://iryoujyouhou.wiki.fc2.com の過去問を取得してJSON形式に変換します。

使い方:
    pip install requests beautifulsoup4
    python scraper.py

出力: questions.json (Androidアプリにインポート可能)
"""

import json
import re
import time
import sys
from urllib.parse import urljoin, unquote

try:
    import requests
    from bs4 import BeautifulSoup
except ImportError:
    print("必要なライブラリをインストールしてください:")
    print("  pip install requests beautifulsoup4")
    sys.exit(1)

BASE_URL = "https://iryoujyouhou.wiki.fc2.com"
INDEX_URL = f"{BASE_URL}/wiki/%E9%81%8E%E5%8E%BB%E5%95%8F%E9%A1%8C%EF%BD%A5%E8%A7%A3%E8%AA%AC%E3%83%BB%E8%A7%A3%E7%AD%94%E4%B8%80%E8%A6%A7"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept-Language": "ja,en;q=0.9",
}

session = requests.Session()
session.headers.update(HEADERS)


def fetch_page(url: str) -> BeautifulSoup | None:
    """ページを取得してBeautifulSoupオブジェクトを返す"""
    try:
        resp = session.get(url, timeout=15)
        resp.raise_for_status()
        resp.encoding = resp.apparent_encoding
        return BeautifulSoup(resp.text, "html.parser")
    except Exception as e:
        print(f"  [ERROR] {url}: {e}")
        return None


def get_question_links(index_soup: BeautifulSoup) -> list[dict]:
    """インデックスページから問題集リンクを取得"""
    links = []
    content = index_soup.find("div", id="wikibody") or index_soup.find("div", class_="wiki-body")
    if not content:
        content = index_soup

    for a in content.find_all("a", href=True):
        href = a["href"]
        text = a.get_text(strip=True)
        # 年度別ページへのリンクを抽出
        if "/wiki/" in href and ("年度" in text or re.search(r"\d{4}", text)):
            full_url = href if href.startswith("http") else urljoin(BASE_URL, href)
            links.append({"url": full_url, "text": text})

    return links


def parse_questions_from_page(soup: BeautifulSoup, year: str, category: str) -> list[dict]:
    """
    ページから問題を解析する。
    FC2 Wikiの構造に合わせてパースします。
    実際のページ構造に合わせてこの関数を調整してください。
    """
    questions = []
    content = soup.find("div", id="wikibody") or soup.find("div", class_="wiki-body")
    if not content:
        return questions

    text = content.get_text("\n")
    lines = [line.strip() for line in text.split("\n") if line.strip()]

    # 問題ブロックを解析
    # 典型的なパターン: "問1" または "第1問" で始まる
    i = 0
    q_num = 0
    while i < len(lines):
        line = lines[i]

        # 問題番号の検出
        m = re.match(r"(?:問|第)\s*(\d+)\s*(?:問)?[.．]?\s*(.*)", line)
        if m:
            q_num = int(m.group(1))
            q_text_start = m.group(2).strip()

            # 問題文を収集
            q_text_lines = [q_text_start] if q_text_start else []
            i += 1
            while i < len(lines) and not re.match(r"[①②③④⑤１２３４５ア-オa-e][\s.．]", lines[i]):
                if re.match(r"(?:問|第)\s*\d+", lines[i]):
                    break
                q_text_lines.append(lines[i])
                i += 1
            q_text = " ".join(q_text_lines).strip()

            # 選択肢を収集
            choices = []
            while i < len(lines) and len(choices) < 5:
                cl = lines[i]
                # 選択肢パターン: ①〜⑤ または 1.〜5.
                cm = re.match(r"[①②③④⑤１２３４５ア-オa-e][\s.．]?\s*(.*)", cl)
                if cm:
                    choices.append(cm.group(1).strip())
                    i += 1
                elif re.match(r"(?:問|第)\s*\d+", cl):
                    break
                else:
                    break

            # 正解と解説を探す
            correct_answer = 0
            explanation = ""
            while i < len(lines):
                cl = lines[i]
                # 正解パターン
                am = re.search(r"(?:正解|答え?)[：:]\s*([①②③④⑤１２３４５1-5])", cl)
                if am:
                    ans_char = am.group(1)
                    char_map = {"①": 1, "②": 2, "③": 3, "④": 4, "⑤": 5,
                                "１": 1, "２": 2, "３": 3, "４": 4, "５": 5}
                    correct_answer = char_map.get(ans_char, int(ans_char) if ans_char.isdigit() else 0)
                    i += 1
                    continue
                # 解説パターン
                if re.match(r"(?:解説|解答)[：:]?", cl):
                    exp_lines = []
                    i += 1
                    while i < len(lines) and not re.match(r"(?:問|第)\s*\d+", lines[i]):
                        exp_lines.append(lines[i])
                        i += 1
                    explanation = " ".join(exp_lines).strip()
                    break
                # 次の問題が来たら終了
                if re.match(r"(?:問|第)\s*\d+", cl):
                    break
                i += 1

            if q_text and len(choices) >= 2:
                questions.append({
                    "year": year,
                    "category": category,
                    "question_number": q_num,
                    "question_text": q_text,
                    "choice1": choices[0] if len(choices) > 0 else "",
                    "choice2": choices[1] if len(choices) > 1 else "",
                    "choice3": choices[2] if len(choices) > 2 else "",
                    "choice4": choices[3] if len(choices) > 3 else "",
                    "choice5": choices[4] if len(choices) > 4 else "",
                    "correct_answer": correct_answer,
                    "explanation": explanation
                })
        else:
            i += 1

    return questions


def scrape_all() -> list[dict]:
    """全過去問を収集"""
    print("インデックスページを取得中...")
    index_soup = fetch_page(INDEX_URL)
    if not index_soup:
        print("インデックスページの取得に失敗しました。")
        return []

    links = get_question_links(index_soup)
    print(f"{len(links)} 件のページリンクを発見")

    if not links:
        print("リンクが見つかりませんでした。")
        print("ページ構造を手動で確認し、scraper.pyのget_question_links()を調整してください。")
        # デバッグ用: インデックスページのリンクを表示
        for a in index_soup.find_all("a", href=True)[:30]:
            print(f"  {a['href']}: {a.get_text(strip=True)[:50]}")
        return []

    all_questions = []

    for item in links:
        url = item["url"]
        text = item["text"]
        print(f"取得中: {text} ({url})")

        # 年度を抽出
        year_m = re.search(r"(\d{4})", text)
        year = year_m.group(1) if year_m else "不明"

        # カテゴリを推定
        category = "医療情報技師"
        for cat_keyword in ["医療情報基礎", "情報処理技術", "医学医療系", "保健医療情報学"]:
            if cat_keyword in text:
                category = cat_keyword
                break

        soup = fetch_page(url)
        if soup:
            questions = parse_questions_from_page(soup, year, category)
            print(f"  → {len(questions)} 問取得")
            all_questions.extend(questions)

        time.sleep(1.5)  # サーバー負荷軽減

    return all_questions


def main():
    print("=== 医療情報技師試験 過去問スクレイパー ===\n")
    questions = scrape_all()

    if not questions:
        print("\n問題を取得できませんでした。")
        print("ヒント: サイトの構造が変わっている場合は scraper.py の")
        print("parse_questions_from_page() 関数を実際のHTML構造に合わせて調整してください。")
        return

    output_file = "questions.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(questions, f, ensure_ascii=False, indent=2)

    print(f"\n完了! {len(questions)} 問を {output_file} に保存しました。")
    print("このファイルをAndroidアプリの「問題をインポート」からインポートしてください。")


if __name__ == "__main__":
    main()
