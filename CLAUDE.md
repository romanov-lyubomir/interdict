# InterDict

## Saved exercise progress

Signed-in users have their lesson exercise answers saved in the database
(the `LessonProgress` table in `main.py`, saved and restored by
`static/lesson.js`). A saved row only knows its exercise by position on the
page (such as `practice-3` or `workbook-12`) and its answers, and the picked
options, by their position **as written in the lesson file** (not the
shuffled order on the page, see below).

**Whenever you make a real change to an exercise in a lesson file
(`data/<language>/lessons/<level>/<number>.json`), clear that lesson's saved
progress in the same piece of work**, and say in your reply that you did:

```bash
flask --app main clear-lesson-progress A2 9
```

Add `--language spanish` (etc.) for a language other than Italian, and
`--exercise use-5` to clear only one exercise (the `data-find` id on the
page). Run it once per lesson you changed. It asks before deleting (`--yes`
skips the question) and first writes a backup to
`instance/progress_backups/`, which can be put back with
`flask --app main restore-lesson-progress <backup file>`.

A real change, which needs clearing:
- adding, removing or reordering exercises, or moving one to another section;
- adding, removing or reordering questions, gaps, pairs or options;
- changing an exercise's type (for example a choice exercise becoming a gap
  exercise) or making it open or not open;
- changing which answer is correct, or what a gap or written answer accepts,
  in a way that could turn an answer saved as right into a wrong one (or the
  other way round);
- replacing a question with a different one.

Not a real change, so leave the progress alone:
- fixing the spelling or wording of a question, option or answer that keeps
  its meaning and position, such as the correct option `migliore` becoming
  `miglior` in "il ___ film dell'anno";
- adding another accepted answer to a gap without removing any;
- changing the prompt, pictures, cues, model answers or anything outside the
  answers themselves;
- adding or removing `"ordered": true` (it only changes what is shown, see
  below).

When unsure whether a change is real, ask the user instead of clearing.

### Progress must never be lost by accident

Only the clear command, run on purpose for a real change, deletes progress.
The code must never throw saved answers away on its own, because a bug while
developing (a broken template, a wrong selector) could otherwise wipe out
every user's work. Keep these rules when changing the code:

- The page checks each saved exercise against the real one before putting
  anything back (`shapeOf` and `fits` in `static/lesson.js`: exercise type,
  number of answers, kind of each answer and number of options). Data that
  doesn't match is **skipped, not deleted**.
- Rows are kept per shape (the `shape` column of `LessonProgress`). Answers
  given to an exercise of another shape go into a new row and never replace
  the old one, so when a bug is fixed, the old answers come back.
- If the saved data can't be read, or a saved version of the same shape
  doesn't fit or can't be put back, nothing is saved over it (`doNotSave` in
  `static/lesson.js`) and an error is written to the browser console.
- Nothing is ever saved from a page load alone, only after the user answers,
  checks or reveals something.

The shape check can't notice a change that keeps the same shape (new
questions with the same number of options, for example), so it does not
replace clearing after a real change.

## Shuffled questions and options

Each time a lesson page opens, the server shows the questions of every
exercise (lines of a gap exercise, rows of a match) and the options of every
choice question in a random order (the `shuffled` filter in `main.py`, used in
`templates/lesson.html`). The order of the exercises themselves never changes.

- Every answer field carries `data-index`, its position as written in the
  lesson, and every option carries `data-option`. Saving, restoring and
  clearing use only these, never the order on the page. Keep it that way: any
  new exercise type needs the same attributes.
- When the order matters, keep it with `"ordered": true` on the exercise (its
  questions stay in order: a dialogue, a conjugation table, a story or a
  biography told in order) or on a choice question (its options stay in
  order, such as "The first / The second / Both"). Options that are only
  Vero / Falso (True / False) or only numbers always keep their order
  (`keeps_option_order` in `grammar_lessons.py`).
- When you write a new exercise, decide whether it needs `"ordered": true`.
  Independent sentences don't; lines that continue each other do.
- The list of a match exercise is sorted alphabetically, not shuffled.

## One exercise per card

Each lesson part shows its exercises one at a time, each in its own card,
with numbered circles under it (`exercise_pages` in `grammar_lessons.py`,
the `.ex-area` in `templates/lesson.html`, `static/pager.js`). What the
exercises refer to stays beside the card on a wide screen and above it on a
narrow one: the word list in Lessico, the text in Lettura, the transcript
in Ascolto, and in the
Eserciziario the texts and pictures of the part (from its heading) that come
before the exercise. So in a workbook part, put a text or picture **before**
the exercises that use it.

The cards keep the exercise ids they always had (`use-2`, `practice-14`):
saved progress and search links depend on them, so never renumber them when
changing the layout.

## Lessons in English

Lessons are written in the language they teach, except where the lesson file
says `"interface": "english"` (Italian A1/1, the welcome lesson, and A1/2,
the alphabet, for complete beginners). Then the page labels, explanations,
prompts and meanings are in English (`lesson_ui` in `grammar_lessons.py`),
while the Italian examples, dialogues and Italian texts stay Italian.

- In such a lesson the word balloons only appear on Italian: words in
  *italics*, verb forms, gap lines, the left side of a match, the word list,
  and texts marked with the language (a reading or transcript is, unless the
  section says `"lang": "en"`). So write every Italian word in an English
  sentence in *italics*, and don't italicise single letters or foreign words
  that are also Italian words (the "a" of Romanian *a cânta*).
- `"titles"` renames the parts of a lesson, for example
  `{"grammar": "Meet Italian"}`.
- `**double asterisks**` underline the letters a rule is about; they are not
  bold, so don't use them for emphasis in running text.
- `{"picture": "what the picture shows"}` is a frame waiting for a picture,
  in the explanation, the reading text or the workbook.

The lesson numbers are part of the saved progress (level + number). If you
renumber lessons, move their `LessonProgress` rows too (none existed for A1
when A1/1–11 became A1/2–12 on 2026-11-12).

## L'Italia da vicino

An optional part of a lesson, in its own tab after Scrittura: a short text
about real life in Italy (customs, practical tips, traps and scams for
tourists, culture) with its exercises, shown like the reading (text on the
left). In the lesson file it is `"italy": {"text": [...], "exercises": [...]}`
(`ITALY` in `grammar_lessons.py`). The user wants one in every lesson over
time; so far A2/3 (scams with bracelets and signatures) and A2/6 (tourist
traps: gelato, people calling you in, restaurants by the monuments) and
A2/9 (smaller places: Comacchio instead of Venice, Lucca and Certaldo in
Tuscany, told with comparatives).

- Tie each text to the lesson's topic and write it with the grammar the
  learner already has at that point (A2/3 comes before the imperative, so it
  uses *dovete* + infinitive and *è meglio*; A2/6 uses the imperative).
- Describe what scammers do, not who they are.
- Add the new words to the glossary, like any lesson text.
