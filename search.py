"""Search through the lessons and stories of one language.

The index is built once at start-up. Each entry is one place on a page, such
as a paragraph of a reading, a table of the grammar or a line of a dialogue,
and knows the "find" key of that place. The page marks the same place with
data-find="<key>", so a result can open the page right there.
"""

import re

from markupsafe import Markup, escape

import functions

TAGS = re.compile(r"\{\w+:([^{}]*)\}|\[\w+:([^\[\]]*)\]")
GAP = re.compile(r"\[\[([^\[\]#|]*)[^\[\]]*\]\]")
SNIPPET = 140


def plain(text):
    # Text as a reader sees it, without tense marks, gaps or emphasis
    text = GAP.sub(r"\1", str(text))
    text = TAGS.sub(lambda match: match.group(1) or match.group(2) or "", text)
    return " ".join(text.replace("*", "").split())


def fold(text):
    return functions.fold_accents(text).casefold()


def strings(node):
    # Every piece of text inside a block, in order
    if isinstance(node, str):
        yield node
    elif isinstance(node, list):
        for item in node:
            yield from strings(item)
    elif isinstance(node, dict):
        for key, value in node.items():
            if key not in ("img", "source", "rows_span", "wide", "nowrap", "compact", "bulleted"):
                yield from strings(value)


def entry(kind, title, where, url, find, text):
    text = plain(" ".join(strings(text)) if not isinstance(text, str) else text)
    return {"kind": kind, "title": plain(title), "where": where, "url": url, "find": find,
            "text": text, "folded": fold(text), "folded_title": fold(plain(title))}


def lesson_entries(level, lesson, url, ui):
    title = f"{level}/{lesson['number']} · {plain(lesson['title'])}"
    sections = ui["sections"]
    yield entry("lesson", title, ui["lesson"], url, "head", [lesson["title"], lesson.get("topics", "")])
    for index, block in enumerate(lesson["grammar"]["explain"]):
        if isinstance(block, dict) and "grid" in block:
            for position, item in enumerate(block["grid"]):
                yield entry("lesson", title, sections["grammar"], url, f"grammar-{index}-{position}", item)
        else:
            yield entry("lesson", title, sections["grammar"], url, f"grammar-{index}", block)
    for index, (word, meaning) in enumerate(lesson["vocabulary"].get("words", [])):
        yield entry("lesson", title, sections["vocabulary"], url, f"vocabulary-w{index}", f"{word} — {meaning}")
    for index, paragraph in enumerate(lesson["reading"].get("text", [])):
        yield entry("lesson", title, sections["reading"], url, f"reading-p{index}", paragraph)
    for index, (speaker, line) in enumerate(lesson["listening"].get("transcript", [])):
        yield entry("lesson", title, sections["listening"], url, f"listening-l{index}", f"{speaker}: {line}")
    for key in ("use", "vocabulary", "reading", "listening", "writing"):
        for index, exercise in enumerate(lesson[key]["exercises"], 1):
            yield entry("lesson", title, sections[key], url, f"{key}-{index}", raw_exercise(exercise))


def raw_exercise(exercise):
    # The prompt and the questions, as written, without the right answers of gaps
    parts = [exercise.get("prompt", "")]
    for question in exercise.get("questions", []):
        if isinstance(question, dict):
            parts.append(question.get("q", ""))
            parts += [option.get("text", "") if isinstance(option, dict) else option.lstrip("*")
                      for option in question.get("options", [])]
        elif isinstance(question, list):
            parts += [part.get("text", "") for part in question]
        else:
            parts.append(question)
    for left, right in exercise.get("pairs", []):
        parts += [left, right]
    return " ".join(str(part) for part in parts)


def story_entries(story, url):
    title = f"{story['level']} · {story['title']}"
    yield entry("story", title, "Story", url, "head", [story["title"], story.get("translation", "")])
    for index, paragraph in enumerate(story["paragraphs"]):
        text = "".join(part.get("word", part.get("text", "")) for part in paragraph)
        yield entry("story", title, "Story", url, f"p{index}", text)


def build(lessons, stories, lesson_url, story_url, ui):
    """lessons: {level: [lesson]}, stories: {slug: story}; the url functions build links."""
    index = []
    for level, level_lessons in lessons.items():
        for lesson in level_lessons:
            index += lesson_entries(level, lesson, lesson_url(level, lesson["number"]), ui)
    for story in stories.values():
        index += story_entries(story, story_url(story["slug"]))
    return [item for item in index if item["text"]]


def search(index, query):
    words = fold(query).split()
    if not words or len(" ".join(words)) < 2:
        return []
    phrase = " ".join(words)
    found = []
    for position, item in enumerate(index):
        haystack = item["folded"] + " " + item["folded_title"]
        if all(word in haystack for word in words):
            # The whole phrase first, then titles, then the order of the course
            rank = (phrase not in item["folded"], item["find"] != "head", position)
            found.append((rank, item))
    return [item for _, item in sorted(found, key=lambda pair: pair[0])]


def fold_with_positions(text):
    # The folded text, and for each of its characters the place in the original,
    # so a match found in the folded text can be marked in the original
    folded, positions = [], []
    for index, char in enumerate(text):
        piece = fold(char)
        folded.append(piece)
        positions += [index] * len(piece)
    return "".join(folded), positions


def matches(text, words):
    # Where each word appears in the text, as (start, end) in the original
    folded, positions = fold_with_positions(text)
    found = []
    for word in words:
        at = folded.find(word)
        while at >= 0:
            found.append((positions[at], positions[at + len(word) - 1] + 1))
            at = folded.find(word, at + len(word))
    return sorted(found)


def snippet(item, query):
    # A short piece of the text around the first match, with the matches marked
    text = item["text"]
    words = [word for word in fold(query).split() if word]
    found = matches(text, words)
    start = found[0][0] if found else 0
    begin = max(0, start - SNIPPET // 3)
    if begin:
        space = text.find(" ", begin)
        begin = space + 1 if 0 <= space < start else begin
    end = min(len(text), begin + SNIPPET)
    piece = text[begin:end]
    marks = [(a - begin, b - begin) for a, b in found if a >= begin and b <= end]
    html, last = [], 0
    for mark_start, mark_end in marks:
        if mark_start < last:
            continue
        html.append(escape(piece[last:mark_start]))
        html.append(Markup("<mark>") + escape(piece[mark_start:mark_end]) + Markup("</mark>"))
        last = mark_end
    html.append(escape(piece[last:]))
    prefix = "… " if begin else ""
    suffix = " …" if end < len(text) else ""
    return Markup(prefix) + Markup("").join(html) + Markup(suffix)


def result(item, query):
    separator = "&" if "?" in item["url"] else "?"
    return {
        "kind": item["kind"],
        "title": item["title"],
        "where": item["where"],
        "snippet": snippet(item, query),
        "url": f"{item['url']}{separator}find={item['find']}",
    }
