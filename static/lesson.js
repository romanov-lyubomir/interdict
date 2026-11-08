// Checks and reveals the answers of the exercises in a lesson.
//
// An answer is a text box or list marked .field, or a group of radio buttons
// marked .choice. Each one sits inside .answer, which shows its tick or cross.

const normalise = (text) => text
    .trim()
    .replace(/[’`´]/g, "'")
    .replace(/\s+/g, " ")
    .replace(/[.!?]+$/, "")
    .toLowerCase();

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
    const fields = [...exercise.querySelectorAll(".field, .choice")];
    const checkButton = exercise.querySelector(".check");
    const revealButton = exercise.querySelector(".reveal");
    const status = exercise.querySelector(".ex-status");
    let lastInput = null;

    const open = () => fields.filter((field) => !field.dataset.locked);

    const finishIfDone = () => {
        if (!open().length) {
            checkButton.disabled = true;
            revealButton.disabled = true;
        }
    };

    checkButton.addEventListener("click", () => {
        open().forEach((field) => {
            if (isEmpty(field)) {
                delete field.closest(".answer").dataset.state;
            } else if (isCorrect(field)) {
                lock(field, "correct");
            } else {
                field.closest(".answer").dataset.state = "wrong";
            }
        });
        const right = fields.filter((field) => field.closest(".answer").dataset.state === "correct").length;
        status.textContent = `${right} of ${fields.length} correct`;
        finishIfDone();
    });

    revealButton.addEventListener("click", () => {
        open().forEach((field) => {
            fillIn(field);
            lock(field, "revealed");
        });
        status.textContent = "";
        finishIfDone();
    });

    // A changed answer loses its cross until it is checked again
    exercise.addEventListener("input", (event) => {
        const answer = event.target.closest(".answer");
        if (answer) {
            delete answer.dataset.state;
        }
    });

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
                : open().find((field) => field.matches("input[type=text]"));
            if (input) {
                input.setRangeText(key.textContent, input.selectionStart, input.selectionEnd, "end");
                input.focus();
                input.dispatchEvent(new Event("input", { bubbles: true }));
            }
        });
    });
}

document.querySelectorAll(".exercise").forEach(setupExercise);
