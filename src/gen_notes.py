from typing import Any, Callable, List, TYPE_CHECKING, Optional
import json
import sys

if "unittest" in sys.modules:
    TESTING = True
else:
    from aqt import mw

    TESTING = False

if TYPE_CHECKING:
    from anki.notes import Note


def populate_note(
    note: "Note",
    seq: int,
    title: str,
    tags: List[str],
    question: str,
    answer: str,
    chapter: str,
    extra: str,
    deck_id: int,
) -> None:

    note.note_type()["did"] = deck_id  # type: ignore
    note.tags = tags
    note["سؤال"] = question
    note["جواب"] = answer
    note["باب"] = chapter
    note["إضافي"] = extra
    note["عنوان"] = title
    note["رقم السؤال"] = str(seq)
    note["كل الأسئلة"] = f'<img src="_{title}.js">'


def parse_questions(
    lines: List[str],
    qa_marker: str,
    question_marker: bool,
    chapter_marker: Optional[str],
    extra_marker: Optional[str],
) -> List:
    """
    Parse question pairs. If _question_marker_ is true, treat the _qa_marker_ as a
    separator between the question and the answer, otherwise treat it as a marker for the answer lines.
    """

    def is_chapter_line(i):
        return (
            i < len(lines)
            and bool(chapter_marker)
            and lines[i].startswith(chapter_marker)
        )

    def is_question_line(i):
        if i >= len(lines):
            return False
        res = (
            (qa_marker in lines[i]) if question_marker else (qa_marker not in lines[i])
        )
        res &= not is_chapter_line(i)

        return res

    def is_answer_line(i):
        if i >= len(lines):
            return False
        res = (
            (qa_marker in lines[i])
            if not question_marker
            else (qa_marker not in lines[i])
        )
        res &= (
            not is_chapter_line(i) and not is_question_line(i) and not is_extra_line(i)
        )

        return res

    def is_extra_line(i):
        if i >= len(lines):
            return False
        res = bool(extra_marker) and lines[i].startswith(extra_marker)
        res &= not is_chapter_line(i) and qa_marker not in lines[i]

        return res

    ret = []
    cur_question = []
    cur_answer = []
    cur_chapter = []
    cur_extra = []

    i = 0
    while i < len(lines):
        if is_chapter_line(i):
            cur_chapter = []
            while is_chapter_line(i):
                cur_chapter.append(lines[i][len(chapter_marker) :].strip())
                i += 1
        while is_question_line(i):
            cur_question.append(lines[i])
            i += 1
        while is_answer_line(i):
            cur_answer.append(lines[i])
            i += 1
        while is_extra_line(i):
            cur_extra.append(lines[i][len(extra_marker) :].strip())
            i += 1
        ret.append(
            {
                "question": "<br>".join(cur_question),
                "answer": "<br>".join(cur_answer),
                "chapter": "<br>".join(cur_chapter),
                "extra": "<br>".join(cur_extra),
            }
        )
        cur_question = []
        cur_answer = []
        cur_extra = []

    return ret


def cleanse_text(string: str) -> List[str]:
    def _normalize_blank_lines(text_lines):
        # remove consecutive lone newlines
        new_text = []
        last_line = ""
        for i in text_lines:
            if last_line.strip() or i.strip():
                new_text.append(i)
            last_line = i
        # remove lone newlines at beginning and end
        for i in (0, -1):
            if not new_text[i].strip():
                del new_text[i]
        return new_text

    text = string.splitlines()
    text = [i.strip() for i in text]
    text = _normalize_blank_lines(text)
    # entirely remove all blank lines
    text = [i for i in text if i.strip()]

    return text


def write_question_set_to_file(question_set, title):
    current = 1

    def format_line(line, previous_line):
        nonlocal current
        question = line["question"]
        answer = line["answer"]
        chapter = line["chapter"]
        s = f"<div><div>{question}</div><div>{answer}</div></div>"
        prev_chapter = previous_line["chapter"]
        if chapter != prev_chapter:
            s = f"<div>{chapter}</div>" + s
        current += 1
        return s

    lines = []

    for current_line, line in enumerate(question_set):
        lines.append(format_line(line, question_set[current_line - 1]))

    # save question set to media folder
    text = "".join(lines)
    js = f"var ARQText = {json.dumps(text, ensure_ascii=False)};"
    fname = f"_{title}.js"
    mw.col.media.trash_files([fname])
    mw.col.media.write_data(fname, js.encode())


def add_notes(
    col: Any,
    note_constructor: Callable,
    title: str,
    tags: List[str],
    text: List[str],
    deck_id: int,
    separator: str = "?",
    question_marker: bool = True,
    chapter_marker: Optional[str] = None,
    extra_marker: Optional[str] = None,
):

    added = 0
    model = col.models.by_name("ARQ 1.0")
    lines = parse_questions(
        text, separator, question_marker, chapter_marker, extra_marker
    )
    for line in lines:
        question = line["question"]
        answer = line["answer"]
        chapter = line["chapter"]
        extra = line["extra"]
        n = note_constructor(col, model)
        populate_note(
            n, added + 1, title, tags, question, answer, chapter, extra, deck_id
        )
        col.add_note(n, deck_id)
        added += 1

    if not TESTING:
        write_question_set_to_file(lines, title)

    return added
