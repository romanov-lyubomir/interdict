"""Graded reading stories with a translation for every word.

Each story is a text file in data/<language>/stories/ that looks like this:

    title: Der neue Job
    translation: The new job
    level: A1

    Ich{I} lade{~herunterladen: download} die{the} Datei{file} herunter{~herunterladen: download}.

Every word is followed by its translation in this context in braces,
optionally with its base form first: {base form: translation}.
A leading ~ marks one part of a word split up in the sentence, like a
German separable verb. All parts with the same base form in one sentence
belong together and show the same translation. Paragraphs are separated
by blank lines.
"""

import os
import re

ROOT = os.path.dirname(os.path.abspath(__file__))
LEVELS = ["A1", "A2", "B1", "B2", "C1", "C2"]

WORD = re.compile(r"([\w'’-]+)\{([^{}]*)\}")
SENTENCE_END = re.compile(r"[.!?…;:]")


class StoryError(ValueError):
    pass


def parse_gloss(gloss):
    split = gloss.startswith("~")
    if split:
        gloss = gloss[1:]
    lemma, sep, meaning = gloss.partition(":")
    if not sep:
        lemma, meaning = "", gloss
    return lemma.strip(), meaning.strip(), split


def end_sentence(path, groups):
    lonely = [lemma for lemma, (_, size) in groups["open"].items() if size < 2]
    if lonely:
        raise StoryError(f"{path}: split words with only one part: {lonely}")
    groups["open"] = {}


def parse_paragraph(text, path, groups):
    # Splits a paragraph into plain text and translated words
    parts = []
    position = 0
    for match in WORD.finditer(text):
        parts.append({"text": text[position:match.start()]})
        if SENTENCE_END.search(parts[-1]["text"]):
            end_sentence(path, groups)
        lemma, meaning, split = parse_gloss(match.group(2))
        if not meaning:
            raise StoryError(f"{path}: no translation for {match.group(1)!r}")
        word = {"word": match.group(1), "lemma": lemma, "meaning": meaning}
        if split:
            if not lemma:
                raise StoryError(f"{path}: split word {match.group(1)!r} needs a base form")
            # Parts with the same base form in one sentence belong together
            if lemma not in groups["open"]:
                groups["count"] += 1
                groups["open"][lemma] = [groups["count"], 0]
            groups["open"][lemma][1] += 1
            word["group"] = groups["open"][lemma][0]
        parts.append(word)
        position = match.end()
    parts.append({"text": text[position:]})
    end_sentence(path, groups)

    leftover = "".join(part.get("text", "") for part in parts)
    untranslated = re.findall(r"[^\W\d_]+", leftover)
    if untranslated:
        raise StoryError(f"{path}: words without a translation: {untranslated[:5]}")
    return [part for part in parts if part.get("word") or part["text"]]


def word_count(paragraphs):
    # Counts words as a reader sees them, so "l'acqua" is one word
    text = " ".join(
        "".join(part.get("word", part.get("text")) for part in paragraph)
        for paragraph in paragraphs
    )
    return len(text.split())


def load_story(path):
    with open(path, encoding="utf-8") as story_file:
        header, _, body = story_file.read().partition("\n\n")
    meta = {}
    for line in header.splitlines():
        key, _, value = line.partition(":")
        meta[key.strip()] = value.strip()
    if meta.get("level") not in LEVELS or not meta.get("title"):
        raise StoryError(f"{path}: needs a title and a level from {LEVELS}")

    groups = {"count": 0, "open": {}}
    paragraphs = [
        parse_paragraph(" ".join(block.split()), path, groups)
        for block in body.split("\n\n")
        if block.strip()
    ]
    return {
        "slug": os.path.splitext(os.path.basename(path))[0],
        "title": meta["title"],
        "translation": meta.get("translation", ""),
        "level": meta["level"],
        "paragraphs": paragraphs,
        "words": word_count(paragraphs),
    }


def load_stories(language):
    folder = os.path.join(ROOT, "data", language, "stories")
    if not os.path.isdir(folder):
        return {}
    stories = [
        load_story(os.path.join(folder, name))
        for name in sorted(os.listdir(folder))
        if name.endswith(".txt")
    ]
    stories.sort(key=lambda story: (LEVELS.index(story["level"]), story["slug"]))
    return {story["slug"]: story for story in stories}


def by_level(stories):
    return [
        (level, [story for story in stories.values() if story["level"] == level])
        for level in LEVELS
    ]
