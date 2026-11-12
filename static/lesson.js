// Checks and reveals the answers of the exercises in a lesson.
//
// An answer is a text box or list marked .field, or a group of radio buttons
// marked .choice. Each one sits inside .answer, which shows its tick or cross.
//
// The server shows the questions and options in a random order. Each answer
// carries its position as written in the lesson (data-index) and each option
// its own (data-option); saving and restoring only ever use those, never the
// order on the page, so a shuffle can't put a saved answer in the wrong place.

const normalise = (text) => text
    .trim()
    .replace(/[’`´]/g, "'")
    .replace(/\s+/g, " ")
    .replace(/[.!?]+$/, "")
    .toLowerCase();

const lessonRoot = document.querySelector(".lesson");

// The score line, in the language of the lesson, such as "{right} of {total} correct"
const scoreText = lessonRoot.dataset.score;

// Saved answers of a signed-in user. Each exercise is saved by its id on the
// page (such as "practice-3") and its answers by their order, as
// {shape, fields: [{value, state}], scored}. The page gets every saved
// version of an exercise, newest first, and uses the one whose shape matches.
// Guests have no data-progress-url, so nothing is saved for them.
//
// NOTE FOR WHOEVER CHANGES THE LESSONS (people and AI assistants alike):
// after a real change to an exercise, clear that lesson's saved progress
// (see "Saved exercise progress" in CLAUDE.md and LessonProgress in main.py).
// "shape" (the kind of each answer and how many options it has) is checked
// before anything is put back, so saved data that clearly belongs to another
// exercise is ignored, but a change that keeps the shape (new questions with
// the same number of options, for example) can't be noticed here.
//
// Saved progress must never be lost because of a bug: data of another shape
// is only skipped, never overwritten (the server keeps each shape apart), and
// whenever the saved data can't be read or put back, nothing is saved over
// it. Keep it that way when changing this file.
let progressUrl = lessonRoot.dataset.progressUrl;
const savedProgress = (() => {
    const element = document.getElementById("lessonProgress");
    try {
        return element ? JSON.parse(element.textContent) : {};
    } catch (error) {
        // The saved answers couldn't be read: saving now would replace them
        // with empty ones, so nothing is saved on this page
        console.error("Saved lesson progress could not be read; saving is off.", error);
        progressUrl = null;
        return {};
    }
})();

// The saved versions of one exercise (newest first)
const savedVersions = (id) => (Array.isArray(savedProgress[id]) ? savedProgress[id] : []);

// Exercises whose saved answers must not be saved over
const doNotSave = new Set();

const pendingSaves = new Map();

const sendProgress = (id, state, keepalive = false) => fetch(progressUrl, {
    method: "POST",
    headers: { "Content-Type": "application/json", "X-CSRFToken": lessonRoot.dataset.csrf },
    body: JSON.stringify({ exercise: id, state }),
    keepalive,
}).catch(() => {
    // Offline or signed out: the answers just aren't remembered this time
});

// Waits for a pause in typing, so every letter isn't a request
const saveProgress = (id, getState) => {
    if (!progressUrl || !id || doNotSave.has(id)) return;
    clearTimeout(pendingSaves.get(id)?.timer);
    const timer = setTimeout(() => {
        pendingSaves.delete(id);
        sendProgress(id, getState());
    }, 800);
    pendingSaves.set(id, { timer, getState });
};

// The "clear" button: forgets the waiting save and deletes the saved answers
// of this version of the exercise (other shapes are kept, see main.py)
const clearProgress = (id, shape) => {
    clearTimeout(pendingSaves.get(id)?.timer);
    pendingSaves.delete(id);
    doNotSave.delete(id);
    if (!progressUrl || !id) return;
    fetch(`${progressUrl}/clear`, {
        method: "POST",
        headers: { "Content-Type": "application/json", "X-CSRFToken": lessonRoot.dataset.csrf },
        body: JSON.stringify({ exercise: id, shape }),
    }).catch(() => {
        // Offline: the old answers come back on the next visit
    });
};

// Asks first, but only when there is something to lose
const confirmClear = (hasAnswers) => !hasAnswers || window.confirm(lessonRoot.dataset.clearConfirm);

// Sends what is still waiting when the page is closed or left
window.addEventListener("pagehide", () => {
    pendingSaves.forEach(({ timer, getState }, id) => {
        clearTimeout(timer);
        sendProgress(id, getState(), true);
    });
    pendingSaves.clear();
});

const isChoice = (field) => field.classList.contains("choice");

const isEmpty = (field) => (isChoice(field)
    ? !field.querySelector("input:checked")
    : !field.value.trim());

const isCorrect = (field) => {
    if (isChoice(field)) {
        const picked = field.querySelector("input:checked");
        return Boolean(picked && picked.dataset.correct);
    }
    return JSON.parse(field.dataset.accepted).some((answer) => normalise(answer) === normalise(field.value));
};

const fillIn = (field) => {
    if (isChoice(field)) {
        field.querySelector("input[data-correct]").checked = true;
    } else {
        field.value = JSON.parse(field.dataset.accepted)[0];
    }
};

// The answer as saved: the text, or the position as written of the picked
// option (-1 for none)
const valueOf = (field) => {
    if (isChoice(field)) {
        const picked = field.querySelector("input:checked");
        return picked ? Number(picked.dataset.option) : -1;
    }
    return field.value;
};

const setValue = (field, value) => {
    if (isChoice(field)) {
        const radio = field.querySelector(`input[data-option="${value}"]`);
        if (radio) radio.checked = true;
    } else if (typeof value === "string") {
        field.value = value;
    }
};

// What kind of answer each field is: "text", "list:5" (a list with 5
// entries) or "choice:3" (3 options). Saved data with another shape is from
// an exercise that has changed, so it is not used
const shapeOf = (fields) => fields.map((field) => {
    if (isChoice(field)) return `choice:${field.querySelectorAll("input").length}`;
    if (field.tagName === "SELECT") return `list:${field.options.length}`;
    return "text";
}).join(",");

const STATES = [null, "correct", "wrong", "revealed"];

// A saved answer fits a field if its value is of the right kind, and only
// fields that can be checked have a state
const fits = (field, saved, checkable) => {
    if (!saved || typeof saved !== "object" || !STATES.includes(saved.state ?? null)) return false;
    if (saved.state && !checkable) return false;
    if (isChoice(field)) {
        return Number.isInteger(saved.value) && saved.value >= -1
            && saved.value < field.querySelectorAll("input").length;
    }
    if (typeof saved.value !== "string") return false;
    return field.tagName !== "SELECT" || [...field.options].some((option) => option.value === saved.value);
};

const unlock = (field) => {
    delete field.closest(".answer").dataset.state;
    delete field.dataset.locked;
    if (field.dataset.tense) {
        field.classList.remove(`t-${field.dataset.tense}`);
    }
    if (isChoice(field)) {
        field.querySelectorAll("input").forEach((radio) => {
            radio.disabled = false;
            radio.checked = false;
        });
    } else {
        field.disabled = false;
        field.value = "";
    }
};

const lock = (field, state) => {
    field.closest(".answer").dataset.state = state;
    field.dataset.locked = "true";
    if (field.dataset.tense) {
        field.classList.add(`t-${field.dataset.tense}`);
    }
    if (isChoice(field)) {
        field.querySelectorAll("input").forEach((radio) => { radio.disabled = true; });
    } else {
        field.disabled = true;
    }
};

function setupExercise(exercise) {
    // In the order the lesson was written, not the shuffled order on the page
    const fields = [...exercise.querySelectorAll(".field, .choice")]
        .sort((a, b) => Number(a.dataset.index) - Number(b.dataset.index));
    const checkButton = exercise.querySelector(".check");
    const revealButton = exercise.querySelector(".reveal");
    const status = exercise.querySelector(".ex-status");
    const id = exercise.dataset.find;
    let lastInput = null;
    let scored = false;

    const open = () => fields.filter((field) => !field.dataset.locked);

    const showScore = () => {
        const right = fields.filter((field) => field.closest(".answer").dataset.state === "correct").length;
        status.textContent = scoreText.replace("{right}", right).replace("{total}", fields.length);
    };

    const shape = `${exercise.dataset.type}|${shapeOf(fields)}`;
    const currentState = () => ({
        shape,
        fields: fields.map((field) => ({
            value: valueOf(field),
            state: field.closest(".answer").dataset.state || null,
        })),
        scored,
    });
    const save = () => saveProgress(id, currentState);

    const finishIfDone = () => {
        if (!open().length) {
            checkButton.disabled = true;
            revealButton.disabled = true;
        }
    };

    // Open questions (personal answers) have no buttons: nothing to check
    if (checkButton) checkButton.addEventListener("click", () => {
        open().forEach((field) => {
            if (isEmpty(field)) {
                delete field.closest(".answer").dataset.state;
            } else if (isCorrect(field)) {
                lock(field, "correct");
            } else {
                field.closest(".answer").dataset.state = "wrong";
            }
        });
        scored = true;
        showScore();
        finishIfDone();
        save();
    });

    if (revealButton) revealButton.addEventListener("click", () => {
        open().forEach((field) => {
            fillIn(field);
            lock(field, "revealed");
        });
        status.textContent = "";
        scored = false;
        finishIfDone();
        save();
    });

    exercise.querySelector(".clear").addEventListener("click", () => {
        const hasAnswers = fields.some((field) => !isEmpty(field) || field.dataset.locked);
        if (!confirmClear(hasAnswers)) return;
        fields.forEach(unlock);
        scored = false;
        if (status) status.textContent = "";
        if (checkButton) {
            checkButton.disabled = false;
            revealButton.disabled = false;
        }
        clearProgress(id, shape);
    });

    // A changed answer loses its cross until it is checked again
    exercise.addEventListener("input", (event) => {
        const answer = event.target.closest(".answer");
        if (answer) {
            delete answer.dataset.state;
        }
        save();
    });
    // Radio buttons and lists send "change" (and also "input" in most browsers)
    exercise.addEventListener("change", save);

    exercise.addEventListener("focusin", (event) => {
        if (event.target.matches("input[type=text].field")) {
            lastInput = event.target;
        }
    });

    // The letters with accents, for keyboards that don't have them
    exercise.querySelectorAll(".accent").forEach((key) => {
        key.addEventListener("mousedown", (event) => event.preventDefault());
        key.addEventListener("click", () => {
            const input = lastInput && !lastInput.disabled
                ? lastInput
                // The first open box as shown on the page
                : [...exercise.querySelectorAll("input[type=text].field")].find((field) => !field.dataset.locked);
            if (input) {
                input.setRangeText(key.textContent, input.selectionStart, input.selectionEnd, "end");
                input.focus();
                input.dispatchEvent(new Event("input", { bubbles: true }));
            }
        });
    });

    // Opens the exercise the way it was left. Saved versions of another
    // shape belong to another version of the exercise: they are skipped but
    // stay saved. A version of the same shape whose answers don't fit means
    // something is wrong, so this exercise isn't saved over it
    const saved = savedVersions(id).find((version) => version && version.shape === shape);
    const usable = saved && Array.isArray(saved.fields)
        && saved.fields.length === fields.length
        && fields.every((field, index) => fits(field, saved.fields[index], Boolean(checkButton)));
    if (saved && !usable) {
        console.error(`Saved answers of ${id} don't fit the exercise; they are kept and not saved over.`);
        doNotSave.add(id);
    }
    if (usable) try {
        fields.forEach((field, index) => {
            const { value, state } = saved.fields[index] || {};
            setValue(field, value);
            if (state === "correct" || state === "revealed") {
                lock(field, state);
            } else if (state === "wrong") {
                field.closest(".answer").dataset.state = "wrong";
            }
        });
        scored = Boolean(saved.scored);
        if (scored && status) showScore();
        if (checkButton) finishIfDone();
    } catch (error) {
        console.error(`Saved answers of ${id} could not be put back; they are kept and not saved over.`, error);
        doNotSave.add(id);
    }
}

// The free writing tasks only keep their text
function setupFreeExercise(exercise) {
    const id = exercise.dataset.find;
    const text = exercise.querySelector(".free-text");
    const saved = savedVersions(id).find((version) => version && version.shape === "free");
    if (saved && typeof saved.text === "string") {
        text.value = saved.text;
    } else if (saved) {
        doNotSave.add(id);
    }
    text.addEventListener("input", () => saveProgress(id, () => ({ shape: "free", text: text.value })));
    exercise.querySelector(".clear").addEventListener("click", () => {
        // Back to the text the task starts with, if it has one
        if (!confirmClear(text.value !== text.defaultValue)) return;
        text.value = text.defaultValue;
        exercise.querySelector(".model").hidden = true;
        clearProgress(id, "free");
    });
}

document.querySelectorAll(".exercise").forEach(setupExercise);
document.querySelectorAll(".free-exercise").forEach(setupFreeExercise);
