import csv
import json
import os
import random
import re
import secrets
from functools import wraps

from flask import (
    Flask,
    abort,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from flask_compress import Compress
from flask_login import LoginManager, UserMixin, current_user, login_user, logout_user
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect
from markupsafe import Markup, escape
from sqlalchemy.exc import IntegrityError
from werkzeug.security import check_password_hash, generate_password_hash

import conjugation
import functions
import grammar_lessons
import stories

app = Flask(__name__)


def load_secret_key():
    # In production set the SECRET_KEY environment variable.
    # Locally a random key is generated once and kept in instance/secret_key.
    if os.environ.get("SECRET_KEY"):
        return os.environ["SECRET_KEY"]
    os.makedirs(app.instance_path, exist_ok=True)
    key_path = os.path.join(app.instance_path, "secret_key")
    if not os.path.exists(key_path):
        with open(key_path, "w") as key_file:
            key_file.write(secrets.token_hex(32))
    with open(key_path) as key_file:
        return key_file.read().strip()


app.config["SECRET_KEY"] = load_secret_key()
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get(
    "DATABASE_URL", "sqlite:///users.db"
)
# The CSRF token stays valid for the whole session, so a drill left open
# for a long time doesn't fail on the next answer.
app.config["WTF_CSRF_TIME_LIMIT"] = None
# Only send the session cookie when it changes. Otherwise a slow response
# (like an audio file still loading) can bring back an older cookie and undo
# the drill's progress.
app.config["SESSION_REFRESH_EACH_REQUEST"] = False

Compress(app)
CSRFProtect(app)
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)

MIN_PASSWORD_LENGTH = 8
MAX_LIST_NAME_LENGTH = 100
DATA_DIR = os.path.join(app.root_path, "data")

TOPICS = ["foods", "drinks", "fruits", "transport"]

LANGUAGES = {
    "italian": {
        "lessons": [],
        "cities": ["rome", "venice", "milan"],
        "flag": "it",
        "native": "Italiano",
    },
    "spanish": {
        "lessons": ["the_alphabet"],
        "cities": ["malaga"],
        "flag": "es",
        "native": "Español",
    },
    "german": {
        "lessons": ["the_alphabet"],
        "cities": ["berlin", "frankfurt", "munich", "leipzig"],
        "flag": "de",
        "native": "Deutsch",
    },
    "greek": {
        "lessons": ["the_alphabet"],
        "cities": ["thessaloniki"],
        "flag": "gr",
        "native": "Ελληνικά",
    },
}

# Pages the language switcher may send the user back to
LANGUAGE_SWITCH_TARGETS = {
    "index",
    "vocabulary_topics",
    "conjugation_drill",
    "stories_list",
    "cheat_sheets",
    "lessons",
    "profile",
}


def read_csv(path):
    with open(path, encoding="utf-8-sig", newline="") as csv_file:
        return list(csv.DictReader(csv_file))


# The article at the start of a word decides the colour it is shown in
ARTICLE_GENDERS = {
    "german": {"der": "masculine", "die": "feminine", "das": "neuter"},
    "spanish": {"el": "masculine", "los": "masculine", "la": "feminine", "las": "feminine"},
    "italian": {
        "il": "masculine",
        "lo": "masculine",
        "i": "masculine",
        "gli": "masculine",
        "la": "feminine",
        "le": "feminine",
    },
    "greek": {"ο": "masculine", "η": "feminine", "το": "neuter", "τα": "neuter"},
}


def word_gender(lang, foreign):
    article = foreign.split(" ", 1)[0]
    return ARTICLE_GENDERS.get(lang, {}).get(article) if " " in foreign else None


def load_vocabulary(lang, topic):
    words = []
    for row in read_csv(os.path.join(DATA_DIR, lang, "vocabulary", f"{topic}.csv")):
        foreign, english, word_id, image = list(row.values())[:4]
        words.append(
            {
                "foreign": foreign,
                "english": english,
                "id": word_id,
                "image": None if image in ("", "None") else image,
                "gender": word_gender(lang, foreign),
            }
        )
    return words


# All drill data is read once at startup instead of on every request.
VOCABULARY = {
    lang: {topic: load_vocabulary(lang, topic) for topic in TOPICS}
    for lang in LANGUAGES
}
STORIES = {lang: stories.load_stories(lang) for lang in LANGUAGES}
LESSONS = {lang: grammar_lessons.load_lessons(lang) for lang in LANGUAGES}
HOME_PAGE_LESSONS = 4


def load_cheat_sheet(lang):
    path = os.path.join(DATA_DIR, lang, "cheat_sheet.json")
    if not os.path.exists(path):
        return None
    with open(path, encoding="utf-8") as sheet_file:
        return json.load(sheet_file)


CHEAT_SHEETS = {lang: load_cheat_sheet(lang) for lang in LANGUAGES}


# Further sheets on one grammar topic each, shown as their own tabs
def load_extra_sheets(lang):
    path = os.path.join(DATA_DIR, lang, "extra_sheets.json")
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8") as sheets_file:
        return json.load(sheets_file)


EXTRA_SHEETS = {lang: load_extra_sheets(lang) for lang in LANGUAGES}

with open(os.path.join(DATA_DIR, "moods_across_languages.json"), encoding="utf-8") as across_file:
    MOODS_ACROSS_LANGUAGES = json.load(across_file)


def load_tense_articles(lang):
    path = os.path.join(DATA_DIR, lang, "tense_articles.json")
    if not os.path.exists(path):
        return {}
    with open(path, encoding="utf-8") as articles_file:
        return json.load(articles_file)


TENSE_ARTICLES = {lang: load_tense_articles(lang) for lang in LANGUAGES}


class User(UserMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    username = db.Column(db.String(100), unique=True, nullable=False)
    language = db.Column(db.String(10), nullable=False)
    word_lists = db.relationship("WordList", cascade="all, delete-orphan")


class WordList(db.Model):
    # A list holds words of one language, so it only shows up while learning it
    __tablename__ = "word_lists"
    __table_args__ = (db.UniqueConstraint("user_id", "language", "name"),)
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    language = db.Column(db.String(10), nullable=False)
    name = db.Column(db.String(MAX_LIST_NAME_LENGTH), nullable=False)
    entries = db.relationship(
        "WordListEntry", cascade="all, delete-orphan", order_by="WordListEntry.id"
    )


class WordListEntry(db.Model):
    __tablename__ = "word_list_entries"
    __table_args__ = (db.UniqueConstraint("list_id", "word_key"),)
    id = db.Column(db.Integer, primary_key=True)
    list_id = db.Column(db.Integer, db.ForeignKey("word_lists.id"), nullable=False, index=True)
    word_key = db.Column(db.String(255), nullable=False)
    word = db.Column(db.String(100), nullable=False)
    lemma = db.Column(db.String(100), nullable=False)
    meaning = db.Column(db.String(255), nullable=False)


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


with app.app_context():
    db.create_all()


def get_lang():
    if current_user.is_authenticated:
        return current_user.language
    return session.get("language")


def safe_next():
    # The page to return to after logging in or signing up. Only paths on
    # this site are accepted, so the link can't send people elsewhere
    target = request.values.get("next", "")
    # Browsers ignore tabs and newlines and read \ as /, which could turn
    # "/\t/evil.com" or "/\evil.com" into a link to another site
    if any(char in target for char in "\\\t\r\n") or not target.startswith("/") or target.startswith("//"):
        return None
    return target


def not_logged_in(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.is_authenticated:
            return redirect(url_for("index"))
        return f(*args, **kwargs)

    return decorated_function


def logged_in(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for("index"))
        return f(*args, **kwargs)

    return decorated_function


# Allows access when logged in or when a guest has picked a language
def language_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if get_lang() not in LANGUAGES:
            session.pop("language", None)
            return redirect(url_for("index"))
        return f(*args, **kwargs)

    return decorated_function


@app.context_processor
def inject_language():
    return dict(user_language=get_lang(), languages=LANGUAGES)


def load_reviewed(lang):
    # The lessons already brought up to date, as {level: {numbers}}
    path = os.path.join(DATA_DIR, lang, "lessons", "reviewed.json")
    if not os.path.exists(path):
        return {}
    with open(path, encoding="utf-8") as reviewed_file:
        data = json.load(reviewed_file)
    return {level: set(numbers) for level, numbers in data.items() if not level.startswith("_")}


REVIEWED_LESSONS = {lang: load_reviewed(lang) for lang in LANGUAGES}
LOCAL_HOSTS = {"localhost", "127.0.0.1", "::1", "[::1]"}


@app.context_processor
def inject_reviewed():
    # A temporary mark on the lessons already updated. It only shows on a
    # local development server, never on the deployed site
    def is_reviewed(level, number):
        if request.host.rsplit(":", 1)[0] not in LOCAL_HOSTS:
            return False
        return number in REVIEWED_LESSONS.get(get_lang(), {}).get(level.upper(), set())

    return dict(is_reviewed=is_reviewed)


@app.template_filter("format")
def format(string_to_format):
    return string_to_format.replace("_", " ").capitalize()


TENSE_MARK = re.compile(r"\{(\w+):([^{}]+)\}")
# A tense named in the text, [tag:name], boxed as on the Verb tenses sheet
TENSE_NAME = re.compile(r"\[(\w+):([^\[\]]+)\]")


@app.template_filter("plain")
def plain(text):
    # The text without its tense marks
    return TENSE_NAME.sub(r"\2", TENSE_MARK.sub(r"\2", text))


@app.template_filter("rich")
def rich(text):
    # Turns {tag:form} into a verb in its tense's style, [tag:name] into a
    # boxed tense name, **text** into highlighted text and *text* into italics
    tensed = TENSE_MARK.sub(r'<span class="t-\1">\2</span>', str(escape(text)))
    tensed = TENSE_NAME.sub(r'<span class="tense-name tn-\1"><span class="t-\1">\2</span></span>', tensed)
    underlined = re.sub(r"\*\*(.+?)\*\*", r"<u>\1</u>", tensed)
    return Markup(re.sub(r"\*(.+?)\*", r"<i>\1</i>", underlined))


def check_answer(user_input, answer):
    # Returns (is_correct, missed_one_letter)
    typed, expected = functions.fold_accents(user_input), functions.fold_accents(answer)
    is_correct = typed == expected
    return is_correct, not is_correct and functions.differ_by_single_char(typed, expected)


def drill_row(drill, row_count, **expected):
    # Returns the row saved in the session if it belongs to this drill
    if not isinstance(drill, dict):
        return None
    if any(drill.get(key) != value for key, value in expected.items()):
        return None
    row = drill.get("row")
    if not isinstance(row, int) or not 0 <= row < row_count:
        return None
    return row


def hash_password(password):
    # Keeps the hash short enough for the existing 100-character column
    return generate_password_hash(password, method="pbkdf2:sha256", salt_length=8)


def home_page_lessons(lang):
    new_lessons = [
        (lesson["title"], url_for("lesson", level="a1", number=lesson["number"]))
        for lesson in LESSONS[lang].get("A1", [])[:HOME_PAGE_LESSONS]
    ]
    return new_lessons or [
        (format(topic), url_for("lesson_for_topic", topic=topic))
        for topic in LANGUAGES[lang]["lessons"]
    ]


@app.route("/")
def index():
    lang = get_lang()
    if lang not in LANGUAGES:
        return render_template("index.html", current_user=current_user)
    config = LANGUAGES[lang]
    return render_template(
        "index.html",
        current_user=current_user,
        topics=TOPICS,
        lessons_list=home_page_lessons(lang),
        story_count=len(STORIES[lang]),
        story_levels=stories.LEVELS,
        random_city=random.choice(config["cities"]),
        word_lists=user_word_lists(),
    )


@app.route("/vocabulary_topics")
@language_required
def vocabulary_topics():
    return render_template(
        "vocabulary_topics.html",
        word_lists=user_word_lists(),
        max_list_name_length=MAX_LIST_NAME_LENGTH,
        current_user=current_user,
    )


@app.route("/cheat_sheets")
@language_required
def cheat_sheets():
    return render_template(
        "cheat_sheets.html",
        sheet=CHEAT_SHEETS.get(get_lang()),
        extra_sheets=EXTRA_SHEETS.get(get_lang(), []),
        across=MOODS_ACROSS_LANGUAGES,
        current_user=current_user,
    )


@app.route("/cheat_sheets/<slug>")
@language_required
def tense_article(slug):
    article = TENSE_ARTICLES.get(get_lang(), {}).get(slug)
    if article is None:
        abort(404)
    return render_template("tense_article.html", article=article, current_user=current_user)


@app.route("/lessons")
@language_required
def lessons():
    lang = get_lang()
    return render_template(
        "lessons.html",
        levels=stories.LEVELS,
        lessons_by_level=LESSONS[lang],
        older=LANGUAGES[lang]["lessons"],
        current_user=current_user,
    )


@app.route("/lessons/<level>/<int:number>")
@language_required
def lesson(level, number):
    level = level.upper()
    level_lessons = LESSONS[get_lang()].get(level, [])
    position = next(
        (index for index, item in enumerate(level_lessons) if item["number"] == number), None
    )
    if position is None:
        abort(404)
    return render_template(
        "lesson.html",
        lesson=level_lessons[position],
        level=level,
        ui=grammar_lessons.ui_for(get_lang()),
        lesson_sections=[
            (key, grammar_lessons.ui_for(get_lang())["sections"][key])
            for key, _ in grammar_lessons.SECTIONS
        ],
        previous=level_lessons[position - 1] if position else None,
        following=level_lessons[position + 1] if position + 1 < len(level_lessons) else None,
        current_user=current_user,
    )


@app.route("/lesson_for_topic/<topic>")
@language_required
def lesson_for_topic(topic):
    lang = get_lang()
    if topic not in LANGUAGES[lang]["lessons"]:
        abort(404)
    return render_template(f"lessons/{lang}/{topic}.html", current_user=current_user)


@app.route("/stories")
@language_required
def stories_list():
    return render_template(
        "stories.html",
        levels=stories.by_level(STORIES[get_lang()]),
        current_user=current_user,
    )


@app.route("/stories/<slug>")
@language_required
def story(slug):
    lang_stories = STORIES[get_lang()]
    if slug not in lang_stories:
        abort(404)
    lists_for_page = [
        {
            "id": word_list.id,
            "name": word_list.name,
            "keys": [entry.word_key for entry in word_list.entries],
        }
        for word_list in user_word_lists()
    ]
    return render_template(
        "story.html",
        story=lang_stories[slug],
        word_lists=lists_for_page,
        max_list_name_length=MAX_LIST_NAME_LENGTH,
        current_user=current_user,
    )


def user_word_lists():
    if not current_user.is_authenticated:
        return []
    return (
        WordList.query.filter_by(user_id=current_user.id, language=get_lang())
        .order_by(WordList.id)
        .all()
    )


def owned_word_list(list_id):
    return WordList.query.filter_by(id=list_id, user_id=current_user.id).first_or_404()


def new_word_list(raw_name):
    # Returns (word_list, error). The caller commits the new list.
    name = " ".join(raw_name.split())
    if not name:
        return None, "The name needs at least one character."
    if len(name) > MAX_LIST_NAME_LENGTH:
        return None, f"The name can have at most {MAX_LIST_NAME_LENGTH} characters."
    if any(word_list.name.casefold() == name.casefold() for word_list in user_word_lists()):
        return None, "You already have a list with that name."
    word_list = WordList(user_id=current_user.id, language=get_lang(), name=name)
    db.session.add(word_list)
    return word_list, None


@app.route("/word_lists", methods=["POST"])
@logged_in
def create_word_list():
    _, error = new_word_list(request.form.get("name", ""))
    if error:
        flash(error)
        return redirect(url_for("vocabulary_topics"))
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        flash("You already have a list with that name.")
    return redirect(url_for("vocabulary_topics"))


@app.route("/word_lists/<int:list_id>")
@logged_in
def word_list(list_id):
    return render_template(
        "word_list.html", word_list=owned_word_list(list_id), current_user=current_user
    )


@app.route("/word_lists/<int:list_id>/delete", methods=["POST"])
@logged_in
def delete_word_list(list_id):
    db.session.delete(owned_word_list(list_id))
    db.session.commit()
    return redirect(url_for("vocabulary_topics"))


@app.route("/word_lists/<int:list_id>/remove/<int:entry_id>", methods=["POST"])
@logged_in
def remove_list_word(list_id, entry_id):
    target = owned_word_list(list_id)
    entry = next((entry for entry in target.entries if entry.id == entry_id), None)
    if entry is None:
        abort(404)
    target.entries.remove(entry)
    db.session.commit()
    return redirect(url_for("word_list", list_id=list_id))


@app.route("/word_lists/add_word", methods=["POST"])
@logged_in
def add_word_to_list():
    # Adds a word from a story to an existing list or to a new one (when "name" is sent)
    lang = get_lang()
    story_data = STORIES[lang].get(request.form.get("story"))
    key = request.form.get("key")
    part = story_data["vocabulary"].get(key) if story_data else None
    if part is None:
        return jsonify(error="That word could not be found."), 404

    if "name" in request.form:
        target, error = new_word_list(request.form["name"])
        if error:
            return jsonify(error=error), 400
    else:
        target = WordList.query.filter_by(
            id=request.form.get("list_id", type=int),
            user_id=current_user.id,
            language=lang,
        ).first()
        if target is None:
            return jsonify(error="That list no longer exists."), 404

    if all(entry.word_key != key for entry in target.entries):
        has_other_base_form = part["lemma"].casefold() != part["saved"].casefold()
        target.entries.append(
            WordListEntry(
                word_key=key,
                word=part["saved"],
                lemma=part["lemma"] if has_other_base_form else "",
                meaning=part["saved_meaning"],
            )
        )
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify(error="That list has just changed. Please try again."), 409
    return jsonify(id=target.id, name=target.name)


QUIZ_LENGTHS = [5, 10, 20, 50, 100, 200]
DEFAULT_QUIZ_LENGTH = 10


def clean_quiz_length(value):
    try:
        value = int(value)
    except (TypeError, ValueError):
        return DEFAULT_QUIZ_LENGTH
    return value if value in QUIZ_LENGTHS else DEFAULT_QUIZ_LENGTH


def start_quiz(kind, length, topic=None, title=None):
    session["quiz"] = {
        "kind": kind,
        "lang": get_lang(),
        "topic": topic,
        "title": title,
        "total": length,
        "done": 0,
        "first_try": 0,
        # Whether the current question has already been answered wrongly
        "missed": False,
    }


def current_quiz(kind, topic=None):
    # Returns the quiz saved in the session if it belongs to this drill
    quiz = session.get("quiz")
    if not isinstance(quiz, dict):
        return None
    if (quiz.get("kind"), quiz.get("lang"), quiz.get("topic")) != (kind, get_lang(), topic):
        return None
    if not all(isinstance(quiz.get(key), int) for key in ("total", "done", "first_try")):
        return None
    return quiz


def quiz_finished(quiz):
    return quiz["done"] >= quiz["total"]


def record_answer(quiz, is_correct):
    # A question counts as correct only if the first answer to it was right
    if not is_correct:
        quiz["missed"] = True
    else:
        quiz["done"] += 1
        if not quiz.get("missed"):
            quiz["first_try"] += 1
        quiz["missed"] = False
    session["quiz"] = quiz
    result = dict(done=quiz["done"], total=quiz["total"])
    if quiz_finished(quiz):
        result["finished"] = url_for("quiz_report")
    return result


def setup_url(quiz):
    if quiz["kind"] == "conjugation":
        return url_for("conjugation_drill")
    if quiz["kind"] == "word_list":
        return url_for("word_list_quiz", list_id=quiz["topic"])
    return url_for("vocabulary_for_topic", topic=quiz["topic"])


@app.route("/quiz_report")
@language_required
def quiz_report():
    quiz = session.get("quiz")
    if isinstance(quiz, dict):
        quiz = current_quiz(quiz.get("kind"), quiz.get("topic"))
    if not quiz or not quiz_finished(quiz):
        return redirect(url_for("index"))
    return render_template(
        "quiz_report.html",
        quiz=quiz,
        percent=round(100 * quiz["first_try"] / quiz["total"]),
        new_quiz_url=setup_url(quiz),
        current_user=current_user,
    )


def get_conjugation_settings(lang):
    saved = session.get("conjugation", {}).get(lang, {})
    return conjugation.clean_settings(
        lang,
        saved.get("forms", conjugation.DEFAULT_FORMS[lang]),
        saved.get("pronouns", conjugation.DEFAULT_PRONOUNS.get(lang, [])),
    )


@app.route("/conjugation_drill", methods=["GET", "POST"])
@language_required
def conjugation_drill():
    lang = get_lang()
    if request.method == "POST":
        forms, pronouns = conjugation.clean_settings(
            lang, request.form.getlist("forms"), request.form.getlist("pronouns")
        )
        if not forms:
            flash("Choose at least one verb form.")
            return redirect(url_for("conjugation_drill"))
        length = clean_quiz_length(request.form.get("length"))
        settings = dict(session.get("conjugation", {}))
        settings[lang] = {"forms": forms, "pronouns": pronouns, "length": length}
        session["conjugation"] = settings
        # Remember the choice after the browser is closed
        session.permanent = True
        session.pop("conjugation_question", None)
        start_quiz("conjugation", length)
        return redirect(url_for("conjugation_practice"))

    forms, pronouns = get_conjugation_settings(lang)
    saved = session.get("conjugation", {}).get(lang, {})
    return render_template(
        "conjugation_drill.html",
        groups=conjugation.FORM_GROUPS[lang],
        pronoun_options=conjugation.PRONOUN_OPTIONS.get(lang, []),
        selected_forms=forms,
        selected_pronouns=pronouns,
        quiz_lengths=QUIZ_LENGTHS,
        selected_length=clean_quiz_length(saved.get("length")),
        current_user=current_user,
    )


# Old links from the home screen of the installed app
@app.route("/conjugation_drill_tenses")
def conjugation_drill_tenses():
    return redirect(url_for("conjugation_drill"))


def leave_drill(target):
    # Sends the browser elsewhere, as JSON for answers and as a redirect otherwise
    if request.method == "POST":
        return jsonify(redirect=target)
    return redirect(target)


@app.route("/conjugation_drill/practice", methods=["GET", "POST"])
@language_required
def conjugation_practice():
    # GET renders the page, POST checks an answer and returns JSON
    lang = get_lang()
    forms, pronouns = get_conjugation_settings(lang)
    quiz = current_quiz("conjugation")
    if not forms or quiz is None:
        return leave_drill(url_for("conjugation_drill"))
    if quiz_finished(quiz):
        return leave_drill(url_for("quiz_report"))

    # Only the question is kept in the session cookie, never the answer
    question = session.get("conjugation_question")
    accepted = None
    if (
        isinstance(question, dict)
        and question.get("language") == lang
        and question.get("form") in forms
    ):
        accepted = conjugation.answers(question)

    if request.method == "POST":
        user_input = request.form.get("user_input", "")
        if not accepted:
            # The question expired, so just show a new one
            return jsonify(next=next_conjugation_question(lang, forms, pronouns, question))
        verb_is_correct, missed_one_letter, answer = conjugation.check(
            user_input, accepted
        )
        if missed_one_letter:
            record_answer(quiz, False)
            return jsonify(message="You missed one letter.")
        result = dict(
            correct=verb_is_correct,
            answer=answer,
            audio_url=conjugation_question_args(question)["audio_url"],
            **record_answer(quiz, verb_is_correct),
        )
        if verb_is_correct and "finished" not in result:
            result["next"] = next_conjugation_question(lang, forms, pronouns, question)
        return jsonify(result)

    # A reload keeps the current question, so it can't be skipped
    if not accepted:
        question = conjugation.pick_question(lang, forms, pronouns, previous=question)
        if question is None:
            flash("There is nothing to practise with these settings.")
            return redirect(url_for("conjugation_drill"))
        session["conjugation_question"] = question
    return render_template(
        "conjugation_practice.html",
        **conjugation_question_args(question),
        quiz=quiz,
        current_user=current_user,
    )


def next_conjugation_question(lang, forms, pronouns, previous):
    question = conjugation.pick_question(lang, forms, pronouns, previous=previous)
    if question is None:
        return None
    session["conjugation_question"] = question
    return conjugation_question_args(question)


def conjugation_question_args(question):
    lang, form = question["language"], question["form"]
    audio = conjugation.audio_path(lang, form, question["verb"], question["person"])
    return dict(
        verb=question["verb"],
        form_label=conjugation.FORM_LABELS[lang][form],
        pronoun=conjugation.person_label(lang, form, question["person"]),
        audio_url=url_for("static", filename=audio) if audio else None,
    )


def pick_word(lang, topic, words, previous=None):
    # Short lists would otherwise ask the same word twice in a row very often
    row = random.choice([row for row in range(len(words)) if row != previous] or [previous])
    session["word_drill"] = {"lang": lang, "topic": topic, "row": row}
    return words[row]


def word_question_args(lang, topic, word):
    image = word["image"]
    return dict(
        english=word["english"],
        image_url=(
            url_for("static", filename=f"images/vocabulary/{topic}/{image}")
            if image
            else None
        ),
        audio_url=(
            url_for("static", filename=f"audio/{lang}/vocabulary/{word['id']}.mp3")
            if word["id"]
            else None
        ),
    )


def check_word(user_input, word):
    # Returns (is_correct, missed_one_letter)
    accepted = word.get("accepted")
    if accepted is None:
        return check_answer(user_input, word["foreign"])
    # List words keep the capital they had in the sentence, so capitals don't count
    results = [check_answer(user_input.casefold(), answer.casefold()) for answer in accepted]
    is_correct = any(correct for correct, _ in results)
    return is_correct, not is_correct and any(missed for _, missed in results)


def word_setup_page(kind, topic, title, hint, practice_url, back_url, quiz_title=None):
    # The start page of a vocabulary quiz
    if request.method == "POST":
        length = clean_quiz_length(request.form.get("length"))
        session["vocabulary_length"] = length
        session.permanent = True
        session.pop("word_drill", None)
        start_quiz(kind, length, topic, quiz_title)
        return redirect(practice_url)

    return render_template(
        "vocabulary_setup.html",
        title=title,
        hint=hint,
        back_url=back_url,
        quiz_lengths=QUIZ_LENGTHS,
        selected_length=clean_quiz_length(session.get("vocabulary_length")),
        current_user=current_user,
    )


def word_practice_page(kind, topic, words, setup_page):
    # GET renders the page, POST checks an answer and returns JSON
    lang = get_lang()
    quiz = current_quiz(kind, topic)
    if quiz is None:
        return leave_drill(setup_page)
    if quiz_finished(quiz):
        return leave_drill(url_for("quiz_report"))

    # Only the row number is kept in the session cookie, never the answer
    row = drill_row(session.get("word_drill"), len(words), lang=lang, topic=topic)
    if request.method == "POST":
        if row is None:
            # The question expired, so just show a new one
            return jsonify(next=word_question_args(lang, topic, pick_word(lang, topic, words)))
        word = words[row]
        word_is_correct, missed_one_letter = check_word(request.form.get("user_input", ""), word)
        if missed_one_letter:
            record_answer(quiz, False)
            return jsonify(message="You missed one letter.")
        result = dict(
            correct=word_is_correct,
            answer=word["foreign"],
            gender=word["gender"],
            audio_url=word_question_args(lang, topic, word)["audio_url"],
            **record_answer(quiz, word_is_correct),
        )
        if word_is_correct and "finished" not in result:
            result["next"] = word_question_args(lang, topic, pick_word(lang, topic, words, row))
        return jsonify(result)

    # A reload keeps the current word, so it can't be skipped
    word = words[row] if row is not None else pick_word(lang, topic, words)
    return render_template(
        "vocabulary_for_topic.html",
        **word_question_args(lang, topic, word),
        quiz=quiz,
        current_user=current_user,
    )


@app.route("/vocabulary_for_topic/<topic>", methods=["GET", "POST"])
@language_required
def vocabulary_for_topic(topic):
    if topic not in TOPICS:
        flash("Unknown topic: " + topic)
        return redirect(url_for("vocabulary_topics"))
    return word_setup_page(
        "vocabulary",
        topic,
        format(topic),
        f"Translate each word into {get_lang().capitalize()}, together with its definite article.",
        url_for("vocabulary_practice", topic=topic),
        url_for("vocabulary_topics"),
    )


@app.route("/vocabulary_for_topic/<topic>/practice", methods=["GET", "POST"])
@language_required
def vocabulary_practice(topic):
    if topic not in TOPICS:
        return leave_drill(url_for("vocabulary_topics"))
    return word_practice_page(
        "vocabulary",
        topic,
        VOCABULARY[get_lang()][topic],
        url_for("vocabulary_for_topic", topic=topic),
    )


def practice_list(list_id):
    # A list can only be practised while its language is the one being learned
    return WordList.query.filter_by(
        id=list_id, user_id=current_user.id, language=get_lang()
    ).first()


def list_quiz_words(word_list):
    # Words with the same translation, like "il" and "la", are all accepted
    same_meaning = {}
    for entry in word_list.entries:
        same_meaning.setdefault(entry.meaning.casefold(), []).append(entry.word)
    return [
        {
            "foreign": entry.word,
            "english": entry.meaning,
            "id": None,
            "image": None,
            "gender": word_gender(word_list.language, entry.word),
            "accepted": same_meaning[entry.meaning.casefold()],
        }
        for entry in word_list.entries
    ]


@app.route("/word_lists/<int:list_id>/quiz", methods=["GET", "POST"])
@logged_in
def word_list_quiz(list_id):
    target = practice_list(list_id)
    if target is None:
        return redirect(url_for("vocabulary_topics"))
    if not target.entries:
        flash("Add some words to this list before starting a quiz.")
        return redirect(url_for("word_list", list_id=list_id))
    return word_setup_page(
        "word_list",
        list_id,
        target.name,
        f"Translate each word into {get_lang().capitalize()}. Give every noun with its definite article.",
        url_for("word_list_practice", list_id=list_id),
        url_for("word_list", list_id=list_id),
        target.name,
    )


@app.route("/word_lists/<int:list_id>/quiz/practice", methods=["GET", "POST"])
@logged_in
def word_list_practice(list_id):
    target = practice_list(list_id)
    if target is None:
        return leave_drill(url_for("vocabulary_topics"))
    if not target.entries:
        return leave_drill(url_for("word_list", list_id=list_id))
    return word_practice_page(
        "word_list",
        list_id,
        list_quiz_words(target),
        url_for("word_list_quiz", list_id=list_id),
    )


@app.route("/register", methods=["GET", "POST"])
@not_logged_in
def register():
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        language = request.form.get("language")

        if functions.empty(email, username, password):
            flash("Don't leave fields empty!")
            return redirect(url_for("register", next=safe_next()))

        if not functions.is_valid_email(email):
            flash("Please enter a valid email address.")
            return redirect(url_for("register", next=safe_next()))

        if not functions.has_only_allowed_symbols(username):
            flash("Usernames can only contain letters, numbers and _.")
            return redirect(url_for("register", next=safe_next()))

        if len(password) < MIN_PASSWORD_LENGTH:
            flash(f"Your password must be at least {MIN_PASSWORD_LENGTH} characters.")
            return redirect(url_for("register", next=safe_next()))

        if language not in LANGUAGES:
            flash("Please choose a language.")
            return redirect(url_for("register", next=safe_next()))

        if User.query.filter_by(email=email).first():
            flash("You've already signed up with that email, log in instead!")
            return redirect(url_for("register", next=safe_next()))

        if User.query.filter_by(username=username).first():
            flash("That username is taken, please choose another one.")
            return redirect(url_for("register", next=safe_next()))

        new_user = User(
            email=email,
            username=username,
            password=hash_password(password),
            language=language,
        )
        db.session.add(new_user)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            flash("That email or username is already taken.")
            return redirect(url_for("register", next=safe_next()))
        login_user(new_user, remember=True)
        return redirect(safe_next() or url_for("index"))

    return render_template("register.html", current_user=current_user)


@app.route("/create_session_profile/<language>")
def create_session_profile(language):
    if language in LANGUAGES:
        session["language"] = language
    return redirect(url_for("index"))


@app.route("/set_language", methods=["POST"])
def set_language():
    # The language switcher in the navigation bar
    language = request.form.get("language")
    if language in LANGUAGES:
        if current_user.is_authenticated:
            current_user.language = language
            db.session.commit()
        else:
            session["language"] = language
    target = request.form.get("next")
    return redirect(url_for(target if target in LANGUAGE_SWITCH_TARGETS else "index"))


@app.route("/login", methods=["GET", "POST"])
@not_logged_in
def login():
    if request.method == "POST":
        email_or_username = request.form.get("email", "").strip()
        password = request.form.get("password", "")

        user = (
            User.query.filter_by(email=email_or_username).first()
            or User.query.filter_by(username=email_or_username).first()
        )

        if not user:
            flash("Profile not found!")
            return redirect(url_for("login", next=safe_next()))
        if not check_password_hash(user.password, password):
            flash("Password incorrect, please try again.")
            return redirect(url_for("login", next=safe_next()))
        login_user(user, remember=True)
        return redirect(safe_next() or url_for("index"))
    return render_template("login.html", current_user=current_user)


@app.route("/profile")
@logged_in
def profile():
    return render_template("profile.html", current_user=current_user)


@app.route("/logout")
def logout():
    logout_user()
    session.pop("language", None)
    return redirect(url_for("index"))


@app.route("/delete_profile", methods=["POST"])
@logged_in
def delete_profile():
    db.session.delete(current_user)
    db.session.commit()
    logout_user()
    return redirect(url_for("index"))


@app.route("/change_password", methods=["POST"])
@logged_in
def change_password():
    old_password = request.form.get("old_password", "")
    new_password = request.form.get("new_password", "")
    if not check_password_hash(current_user.password, old_password):
        flash("Old password is incorrect!")
        return redirect(url_for("profile"))
    if len(new_password) < MIN_PASSWORD_LENGTH:
        flash(f"Your password must be at least {MIN_PASSWORD_LENGTH} characters.")
        return redirect(url_for("profile"))
    current_user.password = hash_password(new_password)
    db.session.commit()
    flash("Password changed!")
    return redirect(url_for("profile"))


@app.route("/change_username", methods=["POST"])
@logged_in
def change_username():
    password = request.form.get("password", "")
    new_username = request.form.get("new_username", "").strip()
    if not check_password_hash(current_user.password, password):
        flash("Password incorrect, please try again.")
        return redirect(url_for("profile"))
    if not new_username or not functions.has_only_allowed_symbols(new_username):
        flash("Usernames can only contain letters, numbers and _.")
        return redirect(url_for("profile"))
    if User.query.filter(
        User.username == new_username, User.id != current_user.id
    ).first():
        flash("That username is taken, please choose another one.")
        return redirect(url_for("profile"))
    current_user.username = new_username
    db.session.commit()
    flash("Username changed!")
    return redirect(url_for("profile"))


@app.route("/change_language", methods=["POST"])
@logged_in
def change_language():
    new_language = request.form.get("new_language")
    if new_language not in LANGUAGES:
        flash("Language not changed!")
        return redirect(url_for("profile"))
    current_user.language = new_language
    db.session.commit()
    flash("Language changed!")
    return redirect(url_for("profile"))


@app.errorhandler(404)
def error_404(e):
    return render_template("error_404.html"), 404


@app.route("/service-worker.js")
def sw():
    return app.send_static_file("service-worker.js")


@app.route("/robots.txt")
def robots_txt():
    return app.send_static_file("robots.txt")


if __name__ == "__main__":
    app.run(host="127.0.0.1", debug=True)
