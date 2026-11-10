"""Interactive lessons, grouped by level.

Each lesson is a JSON file named after its number, in
data/<language>/lessons/<level>/, for example data/italian/lessons/a1/01.json.
It has a title, a translation of the title, the topics it covers, and these
sections, always shown in this order:

    grammar     {"explain": [...]}
    use         {"exercises": [...]}, practice of the grammar
    vocabulary  {"words": [[word, translation], ...], "exercises": [...]}
    reading     {"text": [paragraph or {"h": title}, ...], "exercises": [...]}
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
With "bulleted": true each line of a list cell starts with a >. With "nowrap": true
the cells stay on one line.
**Double asterisks** underline only the letters or small word a rule is about,
such as an ending or a changing article. *Single ones* mark foreign words in italics.
{tag:form} marks a finite verb form with its tense, and a blank can carry one too:
[[sono#ip]]. The tags are ip, im, pp, tp, pr, tr, fs, fa (indicative), cop, cpa
(conditional), imv (imperative), csp, csa, csi and cst (subjunctive). An exercise has a type, a prompt and:

    gap     "questions": ["Io [[sono|ero]] qui."], the blanks with accepted answers
    choice  "questions": [{"q": "...", "options": ["*right", "wrong"]}]
    match   "pairs": [[left, right], ...]
    write   "questions": [{"q": "...", "a": [accepted answers]}]
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
# The words of the lesson page itself, in the language of the lessons, so a
# lesson is all in that language. Languages without their own use English.
UI = {
    "english": {
        "sections": dict(SECTIONS),
        "lesson": "Lesson",
        "all_lessons": "All lessons",
        "check": "Check",
        "reveal": "Reveal",
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
        },
        "lesson": "Lezione",
        "all_lessons": "Tutte le lezioni",
        "check": "Controlla",
        "reveal": "Mostra le risposte",
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


def ui_for(language):
    labels = dict(UI["english"])
    labels.update(UI.get(language, {}))
    labels["sections"] = {key: label.format(language=language.capitalize()) for key, label in labels["sections"].items()}
    labels["word"] = labels["word"].format(language=language.capitalize())
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


def prepare_choice(question, path):
    options = [
        {"text": option.lstrip("*"), "correct": option.startswith("*")}
        for option in question["options"]
    ]
    if sum(option["correct"] for option in options) != 1:
        raise LessonError(f"{path}: needs exactly one right option: {question['q']!r}")
    return {"q": question["q"], "options": options}


def prepare_exercise(exercise, path):
    kind = exercise["type"]
    if kind == "gap":
        exercise["questions"] = [parse_gap_line(line, path) for line in exercise["questions"]]
    elif kind == "choice":
        exercise["questions"] = [prepare_choice(question, path) for question in exercise["questions"]]
    elif kind == "match":
        # Sorted, so the answers don't appear in the same order as the words
        exercise["options"] = sorted({right for _, right in exercise["pairs"]})
    elif kind == "write":
        if not all(question["a"] for question in exercise["questions"]):
            raise LessonError(f"{path}: a writing question has no answer")
    else:
        raise LessonError(f"{path}: unknown exercise type {kind!r}")
    return exercise


def load_lesson(path):
    with open(path, encoding="utf-8") as lesson_file:
        lesson = json.load(lesson_file)
    lesson["number"] = int(os.path.splitext(os.path.basename(path))[0])
    for key, _ in SECTIONS[1:]:
        if not lesson[key]["exercises"]:
            raise LessonError(f"{path}: {key} has no exercises")
        lesson[key]["exercises"] = [
            prepare_exercise(exercise, path) for exercise in lesson[key]["exercises"]
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
