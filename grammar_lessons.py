"""Interactive lessons, grouped by level.

Each lesson is a JSON file named after its number, in
data/<language>/lessons/<level>/, for example data/italian/lessons/a1/01.json.
It has a title, a translation of the title, the topics it covers, and these
sections, always shown in this order:

    grammar     {"explain": [...]}
    use         {"exercises": [...]}, practice of the grammar
    vocabulary  {"words": [[word, translation], ...], "exercises": [...]}
    reading     {"text": [paragraph, {"h": title} or a picture, ...], "exercises": [...]}
    listening   {"transcript": [[speaker, line], ...], "exercises": [...]}
    writing     {"exercises": [...]}

An entry of "explain" is a paragraph, a heading {"h": "..."}, or
{"table": {"head": [...], "rows": [...]}}.
A table can also have "groups": [[label, number of columns], ...], which puts a
labelled brace above those columns, and a "title" shown in a row across it. The
"head" is optional. A cell can be a list of lines, or {"text": ..., "rows": n}
to span n rows, with null in its place in the rows it covers ("cols": n spans
columns).
{"grid": [table, ...]} puts small tables side by side when there is room; a
table with "wide": true takes a whole row. A table's "note" is a short
explanation shown under it, or a list of points.
A picture is {"img": path under static/images, "caption": ..., "credit": ...,
"source": url}; it can go among the explanation blocks or the reading, and a
vocabulary section can have "images": [picture, ...] shown above its words.
With "bulleted": true each line of a list cell starts with a >. With "nowrap": true
the cells stay on one line; with "compact": true
they are tighter, for tables with many columns.
**Double asterisks** underline only the letters or small word a rule is about,
such as an ending or a changing article. *Single ones* mark foreign words in italics.
{tag:form} marks a finite verb form with its tense, and a blank can carry one too:
[[sono#ip]]. The tags are ip, im, pp, tp, pr, tr, fs, fa (indicative), cop, cpa
(conditional), imv (imperative), csp, csa, csi and cst (subjunctive). An exercise has a type, a prompt and:

    gap     "questions": ["Io [[sono|ero]] qui."], the blanks with accepted answers
    choice  "questions": [{"q": "...", "options": ["*right", "wrong"]}]
    match   "pairs": [[left, right], ...]
    write   "questions": [{"q": "...", "a": [accepted answers]}]
            with "open": true the questions are personal and have no "a":
            the learner just writes, nothing is checked

The questions (and the rows of a match) are shown in a random order every
time the page opens, and so are the options of a choice question. When the
order matters, keep it:
    "ordered": true on the exercise     its questions stay in order, for a
                                        dialogue, a table or a story told in
                                        order
    "ordered": true on a choice question  its options stay in order, for
                                        options such as "The first / The
                                        second / Both"
Options that are only Vero / Falso (True / False) or only numbers always stay
in order. The order of the exercises themselves never changes. Saved answers
are kept by the original position of each question and option, so shuffling
doesn't affect them (see LessonProgress in main.py).
"""

import json
import os
import re

from stories import LEVELS, ROOT

SECTIONS = [
    ("grammar", "Grammar"),
    ("use", "Use of {language}"),
    ("vocabulary", "Vocabulary"),
    ("reading", "Reading"),
    ("listening", "Listening"),
    ("writing", "Writing"),
]
# An optional last part with more exercises to practise and learn about the
# country (a workbook). Its "blocks" are, in order:
#   {"h": "A  Studiare in Italia"}            a heading
#   {"text": ["paragraph", …]}                 a short text
#   {"picture": "what the picture shows"}      a frame waiting for a picture
#   {"checklist": ["So …", …]}                 things to tick off (not graded)
#   an exercise, as in the other parts, which can also have
#     "pictures": ["A: …", "B: …"]             frames shown above it
#   {"type": "free", "prompt": …, "cues": […], "model": "…"}
#                                              free writing with a model answer
PRACTICE = ("practice", "Workbook")
# An optional part about real life in the country (customs, practical tips,
# traps for tourists), shown before the workbook: a short text and its
# exercises, like the reading: {"text": [...], "exercises": [...]}
ITALY = ("italy", "Italy up close")
# The optional parts, in the order they come after the others
OPTIONAL_SECTIONS = [ITALY, PRACTICE]
# The words of the lesson page itself, in the language of the lessons, so a
# lesson is all in that language. Languages without their own use English.
UI = {
    "english": {
        "sections": dict(SECTIONS + OPTIONAL_SECTIONS),
        "picture": "Picture",
        "show_model": "Show an example",
        "lesson": "Lesson",
        "all_lessons": "All lessons",
        "check": "Check",
        "reveal": "Reveal",
        "start_over": "Clear",
        "exercise": "Exercise",
        "exercise_list": "Exercises",
        "previous_exercise": "Previous exercise",
        "next_exercise": "Next exercise",
        "start_over_confirm": "Clear your answers to this exercise?",
        "score": "{right} of {total} correct",
        "parts": "Parts of this lesson",
        "accents": "Letters with accents",
        "answer": "Answer",
        "meaning_of": "Meaning of",
        "word": "{language}",
        "meaning": "English",
        "audio_note": "The audio is coming soon. For now, read the transcript.",
    },
    "italian": {
        "sections": {
            "grammar": "Grammatica",
            "use": "Esercizi",
            "vocabulary": "Lessico",
            "reading": "Lettura",
            "listening": "Ascolto",
            "writing": "Scrittura",
            "italy": "L'Italia da vicino",
            "practice": "Eserciziario",
        },
        "picture": "Immagine",
        "show_model": "Mostra un esempio",
        "lesson": "Lezione",
        "all_lessons": "Tutte le lezioni",
        "check": "Controlla",
        "reveal": "Mostra le risposte",
        "start_over": "Ricomincia",
        "exercise": "Esercizio",
        "exercise_list": "Esercizi",
        "previous_exercise": "Esercizio precedente",
        "next_exercise": "Esercizio successivo",
        "start_over_confirm": "Cancellare le tue risposte a questo esercizio?",
        "score": "{right} su {total} giuste",
        "parts": "Parti della lezione",
        "accents": "Lettere con l'accento",
        "answer": "Risposta",
        "meaning_of": "Significato di",
        "word": "Parola",
        "meaning": "Significato",
        "audio_note": "L'audio arriverà presto. Per ora leggi il testo del dialogo.",
    },
}


def ui_for(language, interface=None):
    # The labels of a lesson page about `language`, written in `interface`
    # (the language itself unless the lesson says otherwise, see
    # "interface" in lesson_ui)
    interface = interface or language
    labels = dict(UI["english"])
    labels.update(UI.get(interface, {}))
    labels["sections"] = {key: label.format(language=language.capitalize()) for key, label in labels["sections"].items()}
    labels["word"] = labels["word"].format(language=language.capitalize())
    return labels


def lesson_ui(language, lesson):
    """The labels of one lesson's page.

    A lesson is written in the language it teaches, except where it says
    "interface": "english" (the first lessons, for complete beginners): then
    its page, explanations and instructions are in English. "titles" can
    rename its parts, such as {"grammar": "Meet Italian"}.
    """
    labels = ui_for(language, lesson.get("interface"))
    labels["sections"] = dict(labels["sections"], **lesson.get("titles", {}))
    return labels


GAP = re.compile(r"\[\[([^\[\]]+)\]\]")


class LessonError(ValueError):
    pass


def parse_gap_line(line, path):
    # Splits a line into plain text and blanks
    parts = []
    position = 0
    for match in GAP.finditer(line):
        parts.append({"text": line[position:match.start()]})
        answers, _, tense = match.group(1).partition("#")
        accepted = [answer.strip() for answer in answers.split("|")]
        parts.append({"accepted": accepted, "width": max(map(len, accepted)) + 3, "tense": tense})
        position = match.end()
    parts.append({"text": line[position:]})
    if len(parts) == 1:
        raise LessonError(f"{path}: no blank in {line!r}")
    return parts


# Options that read best in their usual order, so they are never shuffled
FIXED_OPTIONS = [{"vero", "falso"}, {"true", "false"}]
NUMBER = re.compile(r"\d[\d.,]*%?")


def keeps_option_order(texts):
    plain = {text.strip().casefold() for text in texts}
    return plain in FIXED_OPTIONS or all(NUMBER.fullmatch(text.strip()) for text in texts)


def prepare_choice(question, path):
    options = [
        {"text": option.lstrip("*"), "correct": option.startswith("*")}
        for option in question["options"]
    ]
    if sum(option["correct"] for option in options) != 1:
        raise LessonError(f"{path}: needs exactly one right option: {question['q']!r}")
    ordered = question.get("ordered") or keeps_option_order([option["text"] for option in options])
    return {"q": question["q"], "options": options, "ordered": bool(ordered)}


def prepare_exercise(exercise, path):
    kind = exercise["type"]
    if kind == "gap":
        exercise["questions"] = [parse_gap_line(line, path) for line in exercise["questions"]]
        # Every blank keeps its position in the exercise as written, so its
        # saved answer still finds it when the lines are shuffled
        blanks = [part for line in exercise["questions"] for part in line if "accepted" in part]
        for index, part in enumerate(blanks):
            part["index"] = index
    elif kind == "choice":
        exercise["questions"] = [prepare_choice(question, path) for question in exercise["questions"]]
    elif kind == "match":
        # Sorted, so the answers don't appear in the same order as the words
        exercise["options"] = sorted({right for _, right in exercise["pairs"]})
    elif kind == "write":
        if exercise.get("open"):
            if any(question.get("a") for question in exercise["questions"]):
                raise LessonError(f"{path}: an open writing question has answers")
        elif not all(question.get("a") for question in exercise["questions"]):
            raise LessonError(f"{path}: a writing question has no answer")
    elif kind == "free":
        if not exercise.get("model"):
            raise LessonError(f"{path}: a free writing task has no model answer")
    else:
        raise LessonError(f"{path}: unknown exercise type {kind!r}")
    return exercise


# Sections whose exercises all work on the same text (or word list), which
# stays beside them
SHARED_REFERENCE = {"vocabulary", "reading", "listening", "italy"}


def exercise_pages(key, section):
    """The exercises of a section as pages, one card each, and what they refer to.

    Returns (references, pages). A reference is a list of blocks shown beside
    the card (the reading text, the transcript, or the texts and pictures of a
    workbook part). Each page is {"id", "exercise" or "checklist", "ref" (the
    position of its reference, or None), "heading", "heading_find"}.

    The ids are the ones the exercises always had ("use-2", "practice-14"):
    saved progress is kept by them, so they must not change (see
    LessonProgress in main.py).
    """
    if key != "practice":
        shared = key in SHARED_REFERENCE
        pages = [
            {"id": f"{key}-{index}", "exercise": exercise, "ref": 0 if shared else None}
            for index, exercise in enumerate(section.get("exercises", []), 1)
        ]
        return ([[]] if shared and pages else []), pages

    # In the workbook a heading starts a part; its texts and pictures go
    # beside the exercises that follow them in that part
    references, pages = [], []
    heading, heading_find, blocks, ref = None, None, [], None
    for index, block in enumerate(section["blocks"], 1):
        if "type" in block or "checklist" in block:
            page = {"id": f"practice-{index}", "ref": ref, "heading": heading, "heading_find": heading_find}
            page["exercise" if "type" in block else "checklist"] = block if "type" in block else block["checklist"]
            pages.append(page)
            heading_find = None  # the search finds the heading on the part's first card
        elif "h" in block:
            heading, heading_find, blocks, ref = block["h"], f"practice-{index}", [], None
        else:
            blocks = blocks + [block]
            references.append(blocks)
            ref = len(references) - 1
    return references, pages


def load_lesson(path):
    with open(path, encoding="utf-8") as lesson_file:
        lesson = json.load(lesson_file)
    lesson["number"] = int(os.path.splitext(os.path.basename(path))[0])
    if lesson.get("interface") not in (None, "english"):
        raise LessonError(f"{path}: unknown interface {lesson['interface']!r}")
    for key, _ in SECTIONS[1:]:
        if not lesson[key]["exercises"]:
            raise LessonError(f"{path}: {key} has no exercises")
        lesson[key]["exercises"] = [
            prepare_exercise(exercise, path) for exercise in lesson[key]["exercises"]
        ]
    if "italy" in lesson:
        if not lesson["italy"].get("text") or not lesson["italy"].get("exercises"):
            raise LessonError(f"{path}: italy needs a text and exercises")
        lesson["italy"]["exercises"] = [
            prepare_exercise(exercise, path) for exercise in lesson["italy"]["exercises"]
        ]
    if "practice" in lesson:
        lesson["practice"]["blocks"] = [
            prepare_exercise(block, path) if "type" in block else block
            for block in lesson["practice"]["blocks"]
        ]
    return lesson


def load_lessons(language):
    # Returns {level: [lessons in order]} for the levels that have lessons
    result = {}
    for level in LEVELS:
        folder = os.path.join(ROOT, "data", language, "lessons", level.lower())
        if os.path.isdir(folder):
            result[level] = sorted(
                (
                    load_lesson(os.path.join(folder, name))
                    for name in os.listdir(folder)
                    if name.endswith(".json")
                ),
                key=lambda lesson: lesson["number"],
            )
    return result
