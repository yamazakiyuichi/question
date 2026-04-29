import csv
import json
import re
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urljoin, urlparse

import requests
from bs4 import BeautifulSoup


START_URL = (
    "https://iryoujyouhou.wiki.fc2.com/wiki/"
    "%E9%81%8E%E5%8E%BB%E5%95%8F%E9%A1%8C%EF%BD%A5%E8%A7%A3%E8%AA%AC%EF%BD%A5"
    "%E8%A7%A3%E7%AD%94%E4%B8%80%E8%A6%A7"
)
OUT_DIR = Path("data") / "iryoujyouhou"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    ),
    "Accept-Language": "ja,en-US;q=0.9,en;q=0.8",
}

QUESTION_LINK_RE = re.compile(r"^問\s*([0-9０-９]{1,2})$")
CHOICE_RE = re.compile(r"^([1-5１-５])[\)\）]\s*(.*)$")
NAV_LINES = {"次の問題→", "←前の問題", "↑問題一覧", "ページトップ"}
THREAD_LOCAL = threading.local()


def z2h(text: str) -> str:
    return text.translate(str.maketrans("０１２３４５６７８９", "0123456789"))


def wiki_path(url: str) -> str:
    parsed = urlparse(url)
    path = unquote(parsed.path)
    if "/wiki/" in path:
        return path.split("/wiki/", 1)[1]
    return path.strip("/")


def path_meta(url: str) -> dict[str, str]:
    parts = wiki_path(url).split(">")
    meta = {
        "wiki_path": ">".join(parts),
        "year": parts[0] if len(parts) > 0 else "",
        "category": parts[1] if len(parts) > 1 else "",
        "page_type": parts[2] if len(parts) > 2 else "",
        "question_no": parts[3] if len(parts) > 3 else "",
    }
    return meta


def fetch(
    session: requests.Session,
    url: str,
    retries: int = 2,
    timeout: tuple[int, int] = (5, 20),
) -> tuple[str, int, str]:
    last_error = ""
    for attempt in range(1, retries + 1):
        try:
            response = session.get(url, timeout=timeout)
            response.raise_for_status()
            return response.text, response.status_code, response.url
        except Exception as exc:
            last_error = repr(exc)
            time.sleep(0.6 * attempt)
    raise RuntimeError(last_error)


def soup_main(html: str) -> tuple[BeautifulSoup, Any]:
    soup = BeautifulSoup(html, "html.parser")
    return soup, soup.select_one("#main") or soup.body or soup


def clean_lines(main: Any) -> tuple[list[str], str]:
    lines = [line.strip() for line in main.get_text("\n", strip=True).splitlines()]
    updated = ""
    cleaned: list[str] = []
    for line in lines:
        if line.startswith("最終更新:"):
            updated = line.replace("最終更新:", "", 1).strip()
            continue
        if line in NAV_LINES:
            continue
        cleaned.append(line)
    return cleaned, updated


def split_marker_line(line: str) -> tuple[str, str]:
    normalized = line.strip().replace("【", "")
    match = re.match(r"^(解答|解説|補足)】?\s*(.*)$", normalized)
    if not match:
        return "", line
    return match.group(1), match.group(2).strip()


def parse_question_fields(lines: list[str]) -> dict[str, Any]:
    try:
        answer_block_idx = lines.index("解答解説")
    except ValueError:
        answer_block_idx = len(lines)

    question_block = lines[:answer_block_idx]
    answer_block = lines[answer_block_idx + 1 :] if answer_block_idx < len(lines) else []

    first_choice_idx = next(
        (idx for idx, line in enumerate(question_block) if CHOICE_RE.match(line)),
        len(question_block),
    )
    question_text = "\n".join(question_block[:first_choice_idx]).strip()

    choices: list[dict[str, str]] = []
    for line in question_block[first_choice_idx:]:
        match = CHOICE_RE.match(line)
        if match:
            choices.append(
                {
                    "no": z2h(match.group(1)),
                    "text": match.group(2).strip(),
                    "raw": line,
                }
            )

    answer = ""
    explanation_lines: list[str] = []
    supplement_lines: list[str] = []
    section = ""
    for line in answer_block:
        marker, rest = split_marker_line(line)
        if marker == "解答":
            section = "answer"
            if rest and not answer:
                answer = z2h(rest).strip()
            continue
        if marker == "解説":
            section = "explanation"
            if rest:
                explanation_lines.append(rest)
            continue
        if marker == "補足":
            section = "supplement"
            if rest:
                supplement_lines.append(rest)
            continue
        if not section and not answer:
            answer = z2h(line).strip()
            section = "answer"
            continue
        if section == "answer" and not answer:
            answer = z2h(line).strip()
            continue
        if section == "answer" and answer:
            explanation_lines.append(line)
            continue
        if section == "explanation":
            explanation_lines.append(line)
        elif section == "supplement":
            supplement_lines.append(line)

    return {
        "question_text": question_text,
        "choices": choices,
        "answer": answer,
        "explanation": "\n".join(explanation_lines).strip(),
        "supplement": "\n".join(supplement_lines).strip(),
        "body_text": "\n".join(lines).strip(),
    }


def parse_index(html: str) -> list[dict[str, str]]:
    _, main = soup_main(html)
    rows: list[dict[str, str]] = []
    for a in main.find_all("a", href=True):
        label = a.get_text(" ", strip=True)
        if label not in {"問題と解説", "解答一覧"}:
            continue
        url = urljoin(START_URL, a["href"])
        meta = path_meta(url)
        rows.append({"label": label, "url": url, **meta})
    return rows


def parse_answer_page(html: str, url: str) -> tuple[list[dict[str, str]], str]:
    _, main = soup_main(html)
    _, updated = clean_lines(main)
    meta = path_meta(url)
    answers_by_key: dict[tuple[str, str, str], dict[str, str]] = {}

    def add_answer(q_label: str, q_no_raw: str, answer: str) -> None:
        q_match = re.search(r"([0-9０-９]{1,2})", q_label) or re.search(
            r"([0-9０-９]{1,2})", q_no_raw
        )
        if not q_match:
            return
        q_no = f"{int(z2h(q_match.group(1))):02d}"
        answer = z2h(answer).strip()
        if not answer or answer == "正解":
            return
        key = (meta["year"], meta["category"], q_no)
        row = answers_by_key.get(key)
        if row is None:
            answers_by_key[key] = {
                "year": meta["year"],
                "category": meta["category"],
                "question_no": q_no,
                "answer": answer,
                "answer_page_url": url,
                "answer_page_updated": updated,
            }
            return
        existing_answers = {part.strip() for part in row["answer"].split(" / ")}
        if answer not in existing_answers:
            row["answer"] = f"{row['answer']} / {answer}"

    for table in main.find_all("table"):
        for tr in table.find_all("tr"):
            cells = [cell.get_text(" ", strip=True) for cell in tr.find_all(["th", "td"])]
            if len(cells) >= 3 and len(cells) % 3 == 0 and re.search(r"[0-9０-９]", cells[1]):
                for i in range(0, len(cells), 3):
                    chunk = cells[i : i + 3]
                    if len(chunk) == 3:
                        add_answer(chunk[0], chunk[1], chunk[2])
            elif len(cells) >= 2 and len(cells) % 2 == 0:
                for i in range(0, len(cells), 2):
                    chunk = cells[i : i + 2]
                    if len(chunk) == 2:
                        add_answer(chunk[0], "", chunk[1])
    return list(answers_by_key.values()), updated


def parse_question_list(html: str, url: str) -> tuple[list[dict[str, str]], str]:
    _, main = soup_main(html)
    _, updated = clean_lines(main)
    meta = path_meta(url)
    questions: list[dict[str, str]] = []
    for a in main.find_all("a", href=True):
        label = a.get_text(" ", strip=True)
        match = QUESTION_LINK_RE.match(label)
        if not match:
            continue
        q_no = f"{int(z2h(match.group(1))):02d}"
        questions.append(
            {
                "year": meta["year"],
                "category": meta["category"],
                "question_no": q_no,
                "label": label,
                "url": urljoin(url, a["href"]),
                "question_list_url": url,
                "question_list_updated": updated,
            }
        )
    return questions, updated


def split_question_page(html: str, url: str) -> dict[str, Any]:
    soup, main = soup_main(html)
    lines, updated = clean_lines(main)
    title = soup.title.get_text(" ", strip=True) if soup.title else ""
    meta = path_meta(url)

    if lines and lines[0] == meta["wiki_path"]:
        lines = lines[1:]

    question_label = lines[0] if lines and re.match(r"^問\s*[0-9０-９]+", lines[0]) else ""
    if question_label:
        lines = lines[1:]

    fields = parse_question_fields(lines)

    image_urls = []
    for img in main.find_all("img"):
        src = img.get("src")
        if src:
            image_urls.append(
                {
                    "src": urljoin(url, src),
                    "alt": img.get("alt", ""),
                }
            )

    return {
        "year": meta["year"],
        "category": meta["category"],
        "question_no": f"{int(meta['question_no']):02d}" if meta["question_no"].isdigit() else meta["question_no"],
        "url": url,
        "wiki_path": meta["wiki_path"],
        "title": title,
        "question_label": question_label,
        "question_text": fields["question_text"],
        "choices": fields["choices"],
        "answer": fields["answer"],
        "explanation": fields["explanation"],
        "supplement": fields["supplement"],
        "body_text": fields["body_text"],
        "source_last_updated": updated,
        "image_urls": image_urls,
    }


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def thread_session() -> requests.Session:
    session = getattr(THREAD_LOCAL, "session", None)
    if session is None:
        session = requests.Session()
        session.headers.update(HEADERS)
        THREAD_LOCAL.session = session
    return session


def is_missing_record(record: dict[str, Any]) -> bool:
    body_text = record.get("body_text", "")
    return (not body_text.strip()) or ("ページ名「" in body_text and "見つかりませんでした" in body_text)


def dedupe_records(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    deduped: dict[str, dict[str, Any]] = {}
    for record in records:
        url = record.get("url", "")
        if url:
            deduped[url] = record
    return list(deduped.values())


def normalize_answer_for_compare(value: str) -> str:
    value = z2h(str(value)).strip()
    value = (
        value.replace("，", ",")
        .replace("、", ",")
        .replace("と", ",")
        .replace("　", "")
        .replace(" ", "")
        .replace(".", ",")
    )
    if re.fullmatch(r"[1-5]+", value) and len(value) > 1:
        value = ",".join(value)
    return value


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    session = requests.Session()
    session.headers.update(HEADERS)

    index_path = OUT_DIR / "index_links.csv"
    if index_path.exists() and (OUT_DIR / "source_index.html").exists():
        index_links = read_csv(index_path)
        print(f"loaded index links: {len(index_links)}", flush=True)
    else:
        index_html, _, _ = fetch(session, START_URL)
        (OUT_DIR / "source_index.html").write_text(index_html, encoding="utf-8")
        index_links = parse_index(index_html)
        write_csv(
            index_path,
            index_links,
            ["year", "category", "page_type", "label", "wiki_path", "url"],
        )

    answer_page_urls = [row["url"] for row in index_links if row["page_type"] == "解答一覧"]
    question_list_urls = [row["url"] for row in index_links if row["page_type"] == "問題と解説"]

    failures: list[dict[str, str]] = []
    answers_path = OUT_DIR / "answers.csv"
    question_links_path = OUT_DIR / "question_links.csv"
    answer_entries: list[dict[str, str]] = read_csv(answers_path) if answers_path.exists() else []
    question_link_rows: list[dict[str, str]] = (
        read_csv(question_links_path) if question_links_path.exists() else []
    )

    if answer_entries:
        print(f"loaded answers: {len(answer_entries)}", flush=True)
    else:
        for n, url in enumerate(answer_page_urls, 1):
            try:
                html, _, _ = fetch(session, url)
                entries, _ = parse_answer_page(html, url)
                answer_entries.extend(entries)
            except Exception as exc:
                failures.append({"stage": "answer_page", "url": url, "error": repr(exc)})
            if n % 20 == 0:
                print(f"answer pages: {n}/{len(answer_page_urls)}", flush=True)
        write_csv(
            answers_path,
            answer_entries,
            ["year", "category", "question_no", "answer", "answer_page_updated", "answer_page_url"],
        )

    if question_link_rows:
        print(f"loaded question links: {len(question_link_rows)}", flush=True)
    else:
        for n, url in enumerate(question_list_urls, 1):
            try:
                html, _, _ = fetch(session, url)
                links, _ = parse_question_list(html, url)
                question_link_rows.extend(links)
            except Exception as exc:
                failures.append({"stage": "question_list", "url": url, "error": repr(exc)})
            if n % 20 == 0:
                print(f"question list pages: {n}/{len(question_list_urls)}", flush=True)
        write_csv(
            question_links_path,
            question_link_rows,
            [
                "year",
                "category",
                "question_no",
                "label",
                "question_list_updated",
                "question_list_url",
                "url",
            ],
        )

    question_urls: dict[tuple[str, str, str], str] = {}
    for row in question_link_rows:
        expected_q_no = row["question_no"]
        actual_q_no = path_meta(row["url"]).get("question_no", "")
        if actual_q_no.isdigit():
            actual_q_no = f"{int(actual_q_no):02d}"
        url = row["url"]
        if actual_q_no and actual_q_no != expected_q_no:
            url = f"{row['question_list_url']}%3E{expected_q_no}"
        question_urls[(row["year"], row["category"], expected_q_no)] = url

    list_url_by_group = {
        (path_meta(url)["year"], path_meta(url)["category"]): url for url in question_list_urls
    }
    for row in answer_entries:
        key = (row["year"], row["category"], row["question_no"])
        if key in question_urls:
            continue
        list_url = list_url_by_group.get((row["year"], row["category"]))
        if list_url:
            question_urls[key] = f"{list_url}%3E{row['question_no']}"

    question_pages_jsonl_path = OUT_DIR / "question_pages.jsonl"
    questions_jsonl_path = OUT_DIR / "questions.jsonl"
    existing_records: list[dict[str, Any]] = []
    existing_urls: set[str] = set()
    load_jsonl_path = question_pages_jsonl_path if question_pages_jsonl_path.exists() else questions_jsonl_path
    if load_jsonl_path.exists():
        with load_jsonl_path.open("r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    record = json.loads(line)
                    if record.get("body_text"):
                        fields = parse_question_fields(record["body_text"].splitlines())
                        record.update(fields)
                    record["is_missing"] = is_missing_record(record)
                    existing_records.append(record)
                    existing_urls.add(record.get("url", ""))
                except json.JSONDecodeError:
                    continue
        existing_records = dedupe_records(existing_records)
        existing_urls = {record.get("url", "") for record in existing_records}
        print(f"loaded question records: {len(existing_records)}", flush=True)
    fetched_at = datetime.now(timezone.utc).isoformat()

    def fetch_question(item: tuple[tuple[str, str, str], str]) -> tuple[dict[str, Any] | None, dict[str, str] | None]:
        key, url = item
        local_session = thread_session()
        try:
            html, _, final_url = fetch(local_session, url, retries=2, timeout=(5, 15))
            record = split_question_page(html, final_url)
            record["fetched_at_utc"] = fetched_at
            record["is_missing"] = is_missing_record(record)
            if not record["question_no"]:
                record["question_no"] = key[2]
            return record, None
        except Exception as exc:
            return None, {"stage": "question_page", "url": url, "error": repr(exc)}

    items = [(key, url) for key, url in sorted(question_urls.items()) if url not in existing_urls]
    print(f"question pages queued: {len(items)}", flush=True)
    question_records: list[dict[str, Any]] = list(existing_records)
    with ThreadPoolExecutor(max_workers=16) as executor:
        futures = [executor.submit(fetch_question, item) for item in items]
        with question_pages_jsonl_path.open("a", encoding="utf-8") as jsonl:
            for n, future in enumerate(as_completed(futures), 1):
                record, failure = future.result()
                if record:
                    question_records.append(record)
                    jsonl.write(json.dumps(record, ensure_ascii=False) + "\n")
                if failure:
                    failures.append(failure)
                if n % 100 == 0 or n == len(futures):
                    print(f"question pages: {n}/{len(futures)}", flush=True)

    question_records = dedupe_records(question_records)
    question_records.sort(key=lambda r: (r["year"], r["category"], r["question_no"], r["url"]))
    valid_question_records = [
        record for record in question_records if not record.get("is_missing") and record.get("question_text")
    ]
    answer_lookup = {
        (row["year"], row["category"], row["question_no"]): row["answer"]
        for row in answer_entries
        if row.get("answer")
    }
    for record in valid_question_records:
        key = (record["year"], record["category"], record["question_no"])
        listed_answer = answer_lookup.get(key, "")
        record["answer_list_value"] = listed_answer
        if not record.get("answer") and listed_answer:
            record["answer"] = listed_answer
            record["answer_source"] = "answer_list"
        elif record.get("answer"):
            record["answer_source"] = "question_page"
        else:
            record["answer_source"] = ""
    answer_mismatches = [
        {
            "year": record["year"],
            "category": record["category"],
            "question_no": record["question_no"],
            "question_page_answer": record.get("answer", ""),
            "answer_list_value": record.get("answer_list_value", ""),
            "url": record.get("url", ""),
        }
        for record in valid_question_records
        if record.get("answer")
        and record.get("answer_list_value")
        and normalize_answer_for_compare(record["answer"])
        != normalize_answer_for_compare(record["answer_list_value"])
    ]
    with question_pages_jsonl_path.open("w", encoding="utf-8") as f:
        for record in question_records:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    with questions_jsonl_path.open("w", encoding="utf-8") as f:
        for record in valid_question_records:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    question_csv_rows = []
    for record in valid_question_records:
        question_csv_rows.append(
            {
                "year": record["year"],
                "category": record["category"],
                "question_no": record["question_no"],
                "question_text": record["question_text"],
                "choices": " | ".join(choice["raw"] for choice in record["choices"]),
                "answer": record["answer"],
                "answer_source": record.get("answer_source", ""),
                "answer_list_value": record.get("answer_list_value", ""),
                "explanation": record["explanation"],
                "supplement": record["supplement"],
                "source_last_updated": record["source_last_updated"],
                "image_urls": " | ".join(image["src"] for image in record["image_urls"]),
                "url": record["url"],
            }
        )
    write_csv(
        OUT_DIR / "questions.csv",
        question_csv_rows,
        [
            "year",
            "category",
            "question_no",
            "question_text",
            "choices",
            "answer",
            "answer_source",
            "answer_list_value",
            "explanation",
            "supplement",
            "source_last_updated",
            "image_urls",
            "url",
        ],
    )

    missing_rows = [
        {
            "year": record.get("year", ""),
            "category": record.get("category", ""),
            "question_no": record.get("question_no", ""),
            "url": record.get("url", ""),
            "body_text": record.get("body_text", ""),
        }
        for record in question_records
        if record.get("is_missing") or not record.get("question_text")
    ]
    write_csv(
        OUT_DIR / "missing_question_pages.csv",
        missing_rows,
        ["year", "category", "question_no", "url", "body_text"],
    )
    write_csv(
        OUT_DIR / "answer_mismatches.csv",
        answer_mismatches,
        ["year", "category", "question_no", "question_page_answer", "answer_list_value", "url"],
    )

    write_csv(OUT_DIR / "failures.csv", failures, ["stage", "url", "error"])
    summary = {
        "source_url": START_URL,
        "fetched_at_utc": fetched_at,
        "index_link_count": len(index_links),
        "answer_entry_count": len(answer_entries),
        "question_link_count": len(question_link_rows),
        "question_page_attempt_count": len(question_records),
        "valid_question_count": len(valid_question_records),
        "missing_question_page_count": len(missing_rows),
        "answer_mismatch_count": len(answer_mismatches),
        "question_page_failures": sum(1 for row in failures if row["stage"] == "question_page"),
        "failure_count": len(failures),
        "output_dir": str(OUT_DIR),
    }
    (OUT_DIR / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
