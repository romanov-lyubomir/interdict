import json
import os
import random

import functions

ROOT = os.path.dirname(os.path.abspath(__file__))

# (key, label, audio id). The audio id is the number of the recording in
# static/audio/<language>/sentences/<form>/<verb>/<id>.mp3
PERSONS = {
    "italian": [
        ("io", "io", 1),
        ("tu", "tu", 2),
        ("lui", "lui/lei", 3),
        ("noi", "noi", 4),
        ("voi", "voi", 5),
        ("loro", "loro", 6),
    ],
    "spanish": [
        ("yo", "yo", 1),
        ("tu", "tú", 2),
        ("vos", "vos", None),
        ("el", "él/ella/usted", 3),
        ("nosotros", "nosotros/nosotras", 4),
        ("vosotros", "vosotros/vosotras", 5),
        ("ellos", "ellos/ellas/ustedes", 6),
    ],
    "german": [
        ("ich", "ich", 1),
        ("du", "du", 2),
        ("er", "er/sie/es", 3),
        ("wir", "wir", 4),
        ("ihr", "ihr", 5),
        ("sie", "sie/Sie", 6),
    ],
    "greek": [
        ("ego", "εγώ", 1),
        ("esy", "εσύ", 2),
        ("aftos", "αυτός/αυτή/αυτό", 3),
        ("emeis", "εμείς", 4),
        ("eseis", "εσείς", 5),
        ("aftoi", "αυτοί/αυτές/αυτά", 6),
    ],
}

# In the imperative the 3rd person is the polite form
IMPERATIVE_LABELS = {
    "italian": {"lui": "Lei", "loro": "Loro"},
    "spanish": {"el": "usted", "nosotros": "nosotros", "vosotros": "vosotros", "ellos": "ustedes"},
    "german": {"sie": "Sie"},
    "greek": {},
}
IMPERATIVE_FORMS = {"imperativo", "imperativo_afirmativo", "imperativo_negativo", "imperativ", "prostaktiki"}

# Groups of forms shown as checkboxes: (group label, [(form key, label)])
FORM_GROUPS = {
    "italian": [
        ("Indicativo", [
            ("presente", "Presente"),
            ("imperfetto", "Imperfetto"),
            ("passato_prossimo", "Passato prossimo"),
            ("passato_remoto", "Passato remoto"),
            ("trapassato_prossimo", "Trapassato prossimo"),
            ("trapassato_remoto", "Trapassato remoto"),
            ("futuro_semplice", "Futuro semplice"),
            ("futuro_anteriore", "Futuro anteriore"),
        ]),
        ("Congiuntivo", [
            ("congiuntivo_presente", "Presente"),
            ("congiuntivo_passato", "Passato"),
            ("congiuntivo_imperfetto", "Imperfetto"),
            ("congiuntivo_trapassato", "Trapassato"),
        ]),
        ("Condizionale", [
            ("condizionale_presente", "Presente"),
            ("condizionale_passato", "Passato"),
        ]),
        ("Imperativo", [
            ("imperativo", "Imperativo"),
        ]),
        ("Forme indefinite", [
            ("gerundio", "Gerundio"),
            ("participio_passato", "Participio passato"),
        ]),
    ],
    "spanish": [
        ("Indicativo", [
            ("presente", "Presente"),
            ("preterito_imperfecto", "Pretérito imperfecto"),
            ("preterito_indefinido", "Pretérito indefinido"),
            ("preterito_perfecto", "Pretérito perfecto"),
            ("preterito_pluscuamperfecto", "Pretérito pluscuamperfecto"),
            ("preterito_anterior", "Pretérito anterior"),
            ("futuro", "Futuro simple"),
            ("futuro_perfecto", "Futuro perfecto"),
            ("condicional", "Condicional simple"),
            ("condicional_perfecto", "Condicional perfecto"),
        ]),
        ("Subjuntivo", [
            ("subjuntivo_presente", "Presente"),
            ("subjuntivo_imperfecto", "Pretérito imperfecto"),
            ("subjuntivo_perfecto", "Pretérito perfecto"),
            ("subjuntivo_pluscuamperfecto", "Pretérito pluscuamperfecto"),
            ("subjuntivo_futuro", "Futuro simple"),
            ("subjuntivo_futuro_perfecto", "Futuro perfecto"),
        ]),
        ("Imperativo", [
            ("imperativo_afirmativo", "Afirmativo"),
            ("imperativo_negativo", "Negativo"),
        ]),
        ("Formas no personales", [
            ("gerundio", "Gerundio"),
            ("participio", "Participio"),
        ]),
    ],
    "german": [
        ("Indikativ", [
            ("praesens", "Präsens"),
            ("praeteritum", "Präteritum"),
            ("perfekt", "Perfekt"),
            ("plusquamperfekt", "Plusquamperfekt"),
            ("futur_eins", "Futur I"),
            ("futur_zwei", "Futur II"),
        ]),
        ("Konjunktiv I", [
            ("konjunktiv_eins_praesens", "Präsens"),
            ("konjunktiv_eins_perfekt", "Perfekt"),
            ("konjunktiv_eins_futur_eins", "Futur I"),
            ("konjunktiv_eins_futur_zwei", "Futur II"),
        ]),
        ("Konjunktiv II", [
            ("konjunktiv_zwei_praeteritum", "Präteritum"),
            ("konjunktiv_zwei_plusquamperfekt", "Plusquamperfekt"),
            ("konjunktiv_zwei_futur_eins", "Futur I (würde)"),
            ("konjunktiv_zwei_futur_zwei", "Futur II (würde)"),
        ]),
        ("Imperativ", [
            ("imperativ", "Imperativ"),
        ]),
        ("Partizipien", [
            ("partizip_eins", "Partizip I"),
            ("partizip_zwei", "Partizip II"),
        ]),
    ],
    "greek": [
        ("Οριστική", [
            ("enestotas", "Ενεστώτας"),
            ("paratatikos", "Παρατατικός"),
            ("aoristos", "Αόριστος"),
            ("parakeimenos", "Παρακείμενος"),
            ("ypersyntelikos", "Υπερσυντέλικος"),
            ("mellontas_exakolouthitikos", "Εξακολουθητικός μέλλοντας"),
            ("mellontas_stigmiaios", "Στιγμιαίος μέλλοντας"),
        ]),
        ("Υποτακτική", [
            ("ypotaktiki", "Υποτακτική"),
        ]),
        ("Προστακτική", [
            ("prostaktiki", "Προστακτική"),
        ]),
    ],
}

# Groups whose forms are named on their own in the drill ("Gerundio",
# "Imperativo"), the rest get the group name too ("Congiuntivo – Passato")
STANDALONE_GROUPS = {"Forme indefinite", "Formas no personales", "Imperativ", "Partizipien"}

# Extra checkboxes for Spanish: which second persons to practise
PRONOUN_OPTIONS = {
    "spanish": [
        ("tu", "Tuteo (tú)"),
        ("vos", "Voseo (vos)"),
        ("vosotros", "Vosotros"),
    ],
}

DEFAULT_FORMS = {
    "italian": ["presente"],
    "spanish": ["presente"],
    "german": ["praesens"],
    "greek": ["enestotas"],
}
DEFAULT_PRONOUNS = {"spanish": ["tu", "vosotros"]}


def load_conjugations(language):
    path = os.path.join(ROOT, "data", language, "conjugations.json")
    with open(path, encoding="utf-8") as json_file:
        return json.load(json_file)


CONJUGATIONS = {language: load_conjugations(language) for language in PERSONS}

FORM_LABELS = {}
for _language, _groups in FORM_GROUPS.items():
    FORM_LABELS[_language] = {}
    for _group, _forms in _groups:
        for _key, _label in _forms:
            if _group in STANDALONE_GROUPS or _group == _label:
                FORM_LABELS[_language][_key] = _label
            else:
                FORM_LABELS[_language][_key] = f"{_group} – {_label}"


def all_forms(language):
    return [key for _, forms in FORM_GROUPS[language] for key, _ in forms]


def clean_settings(language, forms, pronouns):
    # Keeps only known values, in the order they appear on the page
    forms = [f for f in all_forms(language) if f in forms]
    options = [key for key, _ in PRONOUN_OPTIONS.get(language, [])]
    pronouns = [p for p in options if p in pronouns]
    return forms, pronouns


def allowed_persons(language, pronouns):
    # Spanish: tú, vos and vosotros only appear when their box is ticked
    options = {key for key, _ in PRONOUN_OPTIONS.get(language, [])}
    return [key for key, _, _ in PERSONS[language] if key not in options or key in pronouns]


def person_label(language, form, person):
    if person == "-":
        return None
    if form in IMPERATIVE_FORMS and person in IMPERATIVE_LABELS[language]:
        return IMPERATIVE_LABELS[language][person]
    return next(label for key, label, _ in PERSONS[language] if key == person)


def audio_path(language, form, verb, person):
    audio_id = next((a for key, _, a in PERSONS[language] if key == person), None)
    if audio_id is None:
        return None
    path = f"audio/{language}/sentences/{form}/{verb}/{audio_id}.mp3"
    return path if os.path.exists(os.path.join(ROOT, "static", path)) else None


def pick_question(language, forms, pronouns, previous=None):
    # Picks a form first so every ticked form comes up equally often
    persons = allowed_persons(language, pronouns)
    verbs = CONJUGATIONS[language]
    candidates = {}
    for form in forms:
        options = [
            (verb, person)
            for verb, table in verbs.items()
            if form in table
            for person in table[form]
            if person == "-" or person in persons
        ]
        if options:
            candidates[form] = options
    if not candidates:
        return None
    for _ in range(5):
        form = random.choice(list(candidates))
        verb, person = random.choice(candidates[form])
        question = {"language": language, "verb": verb, "form": form, "person": person}
        if question != previous:
            break
    return question


def answers(question):
    table = CONJUGATIONS[question["language"]].get(question["verb"], {})
    return table.get(question["form"], {}).get(question["person"])


def normalize(text):
    return " ".join(functions.fold_accents(text).lower().split())


def check(user_input, accepted):
    """Returns (is_correct, missed_one_letter, answer to show)."""
    typed = normalize(user_input)
    for answer in accepted:
        if typed == normalize(answer):
            return True, False, answer
    for answer in accepted:
        if functions.differ_by_single_char(typed, normalize(answer)):
            return False, True, answer
    return False, False, accepted[0]
