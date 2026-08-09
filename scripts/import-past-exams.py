"""Import all downloaded iPAS past-exam PDFs into the static site data file.

The source PDFs are kept outside the public repository. This script creates the
browser-ready past-exams.js file and records 50 questions per exam.
"""
from __future__ import annotations

import argparse
import json
import re
import unicodedata
from pathlib import Path

from pypdf import PdfReader

QUESTION_RE = re.compile(r"(?m)^\s*([ABCD])?\s*(\d{1,2})\.\s+")
OPTION_RE = re.compile(r"\(([ABCD])\)")
PAGE_RE = re.compile(r"\d+\s*年.*?第\s*\d+\s*頁，共\s*\d+\s*頁")
CHINESE_NUMBER = {"一": 1, "二": 2, "三": 3, "四": 4, "五": 5, "六": 6, "七": 7, "八": 8, "九": 9, "十": 10}


def normalize(value: str) -> str:
    return unicodedata.normalize("NFKC", value).replace("\u3000", " ")


def chinese_number(value: str) -> str:
    if value.isdigit():
        return value
    if value == "十":
        return "10"
    if value.startswith("十"):
        return str(10 + CHINESE_NUMBER[value[1:]])
    if value.endswith("十"):
        return str(CHINESE_NUMBER[value[0]] * 10)
    if "十" in value:
        return str(CHINESE_NUMBER[value[0]] * 10 + CHINESE_NUMBER[value[2:]])
    return str(CHINESE_NUMBER[value])


def metadata(path: Path) -> dict[str, str]:
    name = normalize(path.name)
    level = "初級" if "初級" in name else "中級"
    subject_match = re.search(r"第\s*([一二三四五六七八九十\d]+)\s*科", name)
    subject_no = chinese_number(subject_match.group(1)) if subject_match else "1"
    year = re.search(r"(\d{3})年", name).group(1)
    session_match = re.search(r"第\s*([一二三四五六七八九十\d]+)\s*(次|梯次)", name)
    session_no = chinese_number(session_match.group(1)) if session_match else ""
    session_word = "梯次" if "梯次" in name else "次"

    if level == "初級" and subject_no == "1":
        subject_id, subject_name = "basic-ai", "人工智慧基礎概論"
    elif level == "初級" and subject_no == "2":
        subject_id, subject_name = "gen-ai", "生成式 AI 應用與規劃"
    elif level == "中級" and subject_no == "1":
        subject_id, subject_name = "ai-plan", "人工智慧技術應用與規劃"
    elif level == "中級" and subject_no == "2":
        subject_id, subject_name = "big-data", "大數據處理分析與應用"
    else:
        subject_id, subject_name = "ml", "機器學習技術與應用"

    key = f"{year}-{session_no}-{level}-{subject_no}"
    session = f"第 {session_no} {session_word}" if session_no else "公告試題"
    return {
        "key": key,
        "level": level,
        "year": year,
        "session": session,
        "subject_id": subject_id,
        "subject_name": subject_name,
        "title": f"{year} 年{session}｜{level}科目 {subject_no}：{subject_name}",
        "source": f"iPAS 官方公告試題｜{path.name}",
    }


def select_questions(text: str) -> list[tuple[re.Match[str], re.Match[str] | None]]:
    candidates = list(QUESTION_RE.finditer(text))
    selected: list[re.Match[str]] = []
    expected = 1
    previous_end = -1
    for candidate in candidates:
        number = int(candidate.group(2))
        if number == expected and candidate.start() >= previous_end:
            selected.append(candidate)
            previous_end = candidate.end()
            expected += 1
            if expected == 51:
                break
    if len(selected) != 50:
        raise ValueError(f"Unable to locate all 50 question starts; found {len(selected)}")
    return [(item, selected[index + 1] if index + 1 < len(selected) else None) for index, item in enumerate(selected)]


def clean_segment(segment: str) -> str:
    lines = []
    for line in segment.splitlines():
        line = line.strip()
        if not line or PAGE_RE.search(line):
            continue
        if line in {"答案 題目", "題目 答案", "一、選擇題", "二、程式題"}:
            continue
        lines.append(line)
    value = " ".join(lines)
    value = re.sub(r"\s+", " ", value)
    value = re.sub(r"\d{3} 年.*?考試日期：.*?(?:試題公告日期：.*?)?(?=\d+\.)", "", value)
    value = re.sub(r"第\s*\d+\s*頁，共\s*\d+\s*頁", "", value)
    return value.strip(" ;；")


def parse_questions(text: str, info: dict[str, str], filename: str) -> list[dict]:
    parsed = []
    for index, (start, next_start) in enumerate(select_questions(text), start=1):
        end = next_start.start() if next_start else len(text)
        segment = clean_segment(text[start.end():end])
        option_matches = list(OPTION_RE.finditer(segment))
        if len(option_matches) < 4:
            raise ValueError(f"{filename}: question {index} has only {len(option_matches)} options")
        prompt = segment[: option_matches[0].start()].strip()
        options = []
        for option_index, option_match in enumerate(option_matches[:4]):
            option_end = option_matches[option_index + 1].start() if option_index + 1 < len(option_matches) else len(segment)
            option = segment[option_match.end():option_end].strip(" ;；")
            options.append(re.sub(r"\s+", " ", option))
        answer = start.group(1) or "A"
        question_id = f"past-{info['key']}-{index:02d}"
        parsed.append({
            "id": question_id,
            "subject": info["subject_id"],
            "chapter": info["subject_name"],
            "type": "歷屆考題",
            "prompt": prompt,
            "options": options,
            "answer": "ABCD".index(answer),
            "explanation": f"依官方公告試題答案：{answer}。請以原始試卷圖表與完整題幹為準。",
            "source": info["source"],
        })
    return parsed


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-dir", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    all_questions: list[dict] = []
    exams: list[dict] = []
    for pdf in sorted(args.input_dir.glob("*.pdf")):
        info = metadata(pdf)
        text = normalize("\n".join(page.extract_text() or "" for page in PdfReader(str(pdf)).pages))
        questions = parse_questions(text, info, pdf.name)
        all_questions.extend(questions)
        exams.append({
            "id": f"past-exam-{info['key']}",
            "level": info["level"],
            "title": info["title"],
            "year": info["year"],
            "note": f"{info['session']}｜完整 50 題｜{pdf.name}",
            "sourceUrl": "https://www.ipas.org.tw/AIAP/AbilityExamBulletinList.aspx",
            "sourceFile": pdf.name,
            "questionIds": [question["id"] for question in questions],
        })
        print(f"{pdf.name}: {len(questions)} 題")

    if not exams or any(len(exam["questionIds"]) != 50 for exam in exams):
        raise ValueError("Every imported exam must contain exactly 50 questions")

    payload = "window.IPAS_PAST_QUESTIONS = " + json.dumps(all_questions, ensure_ascii=False, separators=(",", ":")) + ";\n\n"
    payload += "window.IPAS_PAST_EXAMS = " + json.dumps(exams, ensure_ascii=False, separators=(",", ":")) + ";\n\n"
    payload += "window.IPAS_DATA.questions.push(...window.IPAS_PAST_QUESTIONS);\n"
    args.output.write_text(payload, encoding="utf-8")
    print(f"Imported {len(exams)} exams / {len(all_questions)} questions -> {args.output}")


if __name__ == "__main__":
    main()
