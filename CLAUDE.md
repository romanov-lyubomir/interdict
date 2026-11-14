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
Tuscany, told with comparatives) and B2/1 (Giovanni Falcone, the
maxiprocesso and Capaci, and how Italians answered: Libera, Addiopizzo and
its stickers for travellers; told with the *passato remoto*).

- Tie each text to the lesson's topic and write it with the grammar the
  learner already has at that point (A2/3 comes before the imperative, so it
  uses *dovete* + infinitive and *è meglio*; A2/6 uses the imperative).
- Describe what scammers do, not who they are.
- On the mafia: respectful, never romantic, and never "Italy = mafia"; show
  the Italians who fight it. Only checked facts. The famous photo of Falcone
  and Borsellino laughing is by Tony Gentile and under copyright: keep the
  picture frame unless the user gets permission.
- Add the new words to the glossary, like any lesson text.

The options of a match exercise are a drop-down list, which can't show
markup: the page shows them through `visible_text` (`grammar_lessons.py`),
while each option's value stays the text as written, so checking and saved
answers are unchanged.

## Georgian

Georgian (`georgian`, flag `ge`) has its alphabet lessons
(`data/georgian/lessons/a1/01–05.json`, marked `"alphabet": true`), the
first A1 lessons (06–08: greetings and *to be*, the family and numbers, the
café), all with an English interface, and, since 2026-11-14, the other parts
of the site: vocabulary (4 topics, no audio, the shared pictures where they
fit), 4 stories (A1–A2 only, at the user's choice: write higher levels only
when asked), the conjugation drill (16 verbs, present, future and aorist, by
subject person; the aorist shows the ergative მან / მათ, see
`FORM_PERSON_LABELS` in `conjugation.py`) and a cheat sheet of the main
screeves with short articles. Only the search is still off (`"features"` in
`LANGUAGES`, `FEATURES`, `FEATURE_ENDPOINTS`, `hide_missing_features`).

- The lessons use two blocks made for a new alphabet (`explain.html`,
  `static/letters.js`): `{"letters": [...]}`, tiles that show a letter's
  sound and an example word when tapped, with a "hide the sounds" self-test,
  and `{"flash": [[word, reading, meaning], …]}`, words to read that show how
  they are read when tapped. Neither is saved.
- `"keys"` on a lesson or an exercise replaces the Italian accent buttons
  above gap and writing exercises (the Georgian letters learnt so far);
  `"keys": ""` shows none.
- Readings in Latin letters mark the tight (ejective) sounds with an
  apostrophe (*k'at'a*); answers are also accepted without it.
- A lesson can leave out parts other than the explanation (`load_lesson` in
  `grammar_lessons.py`): the Georgian ones have no listening.
- The scratchpad script that wrote them is not kept; edit the JSON directly.
- Georgian script setting: in the settings (Settings for guests, Profile and
  settings for signed-in users) a learner picks Georgian letters or Latin
  letters (`get_script`, `User.script`, `session["script"]` in `main.py`).
  Latin hides the alphabet lessons and transliterates everything else when
  the page is made (`grammar_lessons.latin_lessons`, `to_latin`); the other
  lessons are then shown counted from 1 (`"shown"`), but keep their real
  numbers in links and saved progress. Answers are also accepted without the
  apostrophes. Every other page and JSON answer is transliterated when it is
  sent (`georgian_in_latin` in `main.py`), and the drills accept Latin answers
  (`latin_answers`); only what is wrapped in `<!--keep-script-->…
  <!--/keep-script-->` stays in Georgian (the sample in the setting). So write Georgian lessons only in Georgian letters, and write
  every Georgian word in an English sentence in *italics* (in Latin letters
  *is* would otherwise read as English).
- In Georgian letters the drills show buttons with the 33 letters under the
  answer box (`templates/letter_keys.html`), like the keys of the lessons.
- Georgian letters use Droid Sans Georgian (`static/fonts/`, Apache 2.0:
  keep `droid-sans-georgian-LICENSE.txt` with it). Its `@font-face` in
  `base.html` covers only the Georgian letters (`unicode-range`); everything
  else, digits and punctuation included, stays Bahnschrift, as the user
  asked. Don't give `[lang="ka"]` a font of its own.

## Greek

Greek (`greek`) has new A1 lessons in `data/greek/lessons/a1/` that replace
the old alphabet page (`templates/lessons/greek/the_alphabet.html`, no longer
listed). So far 01–05 teach reading (`"alphabet": true`, English interface,
the same `letters` and `flash` blocks as Georgian with `"lang": "el"`); the
plan for the rest of A1 is in the assistant's memory (greek-a1-plan).

- Readings in Latin letters use *dh* for δ, *th* for θ, *gh* (or *y* before
  e and i) for γ and *ch* for χ, with the accent on the stressed vowel.
- Blanks also accept a word without its accent mark (`[[σπίτι|σπιτι]]`),
  and Latin readings are accepted with or without the accent.
- `"keys"` holds the Greek letters learnt so far, with the accented vowels.
- New words go in `data/greek/glossary_1.txt`; for a word written without
  its accent (signs in capitals) add `word > accented word = meaning`.
