"""English meanings for the words of a lesson, shown in a balloon on hover.

There is no dictionary of the whole language, so the glossary is put
together from what the site already knows:
- the hand-written lists in data/<language>/glossary_*.txt;
- the words of the stories, with the meaning they were saved with;
- the built-in topic words (without their article);
- for Italian, every form of every verb on the verb pages.
A word can have more than one entry (letto: "il letto, bed" and "leggere,
to read"); the page picks the one that fits the sentence and shows only that.
"""
import json
import os
import re

WORD = re.compile(r"[^\W\d_]+", re.UNICODE)
ARTICLES = {
    "italian": ("il ", "lo ", "la ", "l'", "i ", "gli ", "le "),
    "spanish": ("el ", "la ", "los ", "las "),
    "german": ("der ", "die ", "das "),
    "greek": ("ο ", "η ", "το ", "οι ", "τα "),
}
# Words that end some verb forms but are not the verb ("non svegliarti" is fine,
# but a form is never just a pronoun)
VERB_PRONOUNS = {"mi", "ti", "si", "ci", "vi", "non", "lo", "la", "li", "le", "ne", "se", "me", "te", "ce", "ve"}


COMMON_VERBS = ["essere", "avere", "fare", "andare", "stare", "dire", "potere", "volere", "dovere",
                "venire", "dare", "sapere", "vedere", "prendere", "mettere"]


def add(glossary, word, lemma, meaning, verb_tags=None):
    word = word.casefold()
    entry = {"w": lemma, "m": meaning}
    if verb_tags is not None:
        # A verb form: the tense tags it appears under ("pp", "ip", …,
        # "participio_passato", "inf")
        entry["t"] = verb_tags
    entries = glossary.setdefault(word, [])
    if all(item["w"].casefold() != lemma.casefold() for item in entries):
        entries.append(entry)


def read_base(lang, data_dir):
    """The hand-written glossary_*.txt files: "word = meaning" or
    "word > base form = meaning"."""
    entries = []
    folder = os.path.join(data_dir, lang)
    if not os.path.isdir(folder):
        return entries
    for name in sorted(os.listdir(folder)):
        if not (name.startswith("glossary_") and name.endswith(".txt")):
            continue
        with open(os.path.join(folder, name), encoding="utf-8") as file:
            for line in file:
                line = line.strip()
                if not line or line.startswith("#") or " = " not in line:
                    continue
                left, meaning = line.split(" = ", 1)
                word, _, lemma = (part.strip() for part in left.partition(" > "))
                entries.append((word, lemma or word, meaning.strip()))
    return entries


def build(lang, stories, vocabulary, verb_list=(), verb_details=None, conjugate=None, data_dir="data", tags=None):
    glossary = {}
    # The hand-written words first, then what the stories and topics know
    base = read_base(lang, data_dir)
    for word, lemma, meaning in base:
        add(glossary, word, lemma, meaning)
    hand_written = {(word.casefold(), lemma) for word, lemma, _ in base}
    # Story words first: their meanings were written for real sentences
    for story in stories.values():
        for part in story.get("vocabulary", {}).values():
            lemma = part.get("saved") or part.get("word")
            meaning = part.get("saved_meaning") or part.get("meaning")
            if part.get("word") and meaning and " " not in part["word"]:
                add(glossary, part["word"], lemma, meaning)
    for words in vocabulary.values():
        for word in words:
            foreign = word["foreign"]
            bare = foreign
            for article in ARTICLES.get(lang, ()):
                if foreign.casefold().startswith(article):
                    bare = foreign[len(article):]
                    break
            if " " not in bare:
                add(glossary, bare, foreign, word["english"])
    tags = tags or {}
    if conjugate and verb_details:
        for verb in verb_list:
            meaning = verb_details.get(verb, {}).get("meaning")
            if not meaning:
                continue
            # Which tenses each word of the verb belongs to, so the balloon
            # can tell "ho capito" (capire) from "io capito" (capitare)
            seen = {verb.casefold(): {"inf"}}
            for tense, persons in conjugate(verb).items():
                tag = tags.get(tense, tense)
                for forms in persons.values():
                    for form in forms:
                        # Only the verb itself: in "si è svegliato" the
                        # pronoun and the auxiliary belong to other words
                        part = form.split()[-1].casefold()
                        if part not in VERB_PRONOUNS:
                            seen.setdefault(part, set()).add(tag)
            # Every participle also in -a, -i, -e: "ti ho aspettata", "le ho comprate"
            for part, part_tags in list(seen.items()):
                if "participio_passato" in part_tags and part.endswith("o"):
                    for ending in "aie":
                        seen.setdefault(part[:-1] + ending, set()).update(part_tags)
            for part, part_tags in seen.items():
                add(glossary, part, verb, meaning, sorted(part_tags))
        # A story gives a verb form the meaning it had in its sentence ("ho":
        # "I am", from "ho fame"); the infinitive says more, so it replaces it
        known = set(verb_list)
        for word, entries in glossary.items():
            if any(entry["w"] in known for entry in entries):
                entries[:] = [entry for entry in entries
                              if entry["w"].casefold() != word or entry["w"] in known
                              or (word, entry["w"]) in hand_written]
            # When two verbs share a form ("stato": essere and stare), the
            # more common verb comes first and is the one shown
            entries.sort(key=lambda entry: COMMON_VERBS.index(entry["w"])
                         if "t" in entry and entry["w"] in COMMON_VERBS else len(COMMON_VERBS))
    return glossary


def for_lesson(glossary, lesson):
    """Only the entries for the words the lesson uses, to keep the page small."""
    # Without the ** of highlighted endings, so "alzat**o**" counts as "alzato"
    text = json.dumps(lesson, ensure_ascii=False).replace("**", "")
    # Leave out the markup inside {tag:...} and [tag:...]
    text = re.sub(r"[\[{](\w+):", " ", text)
    used = {word.casefold() for word in WORD.findall(text)}
    return {word: glossary[word] for word in used if word in glossary}
