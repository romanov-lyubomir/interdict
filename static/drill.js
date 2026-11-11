// Sends drill answers in the background and swaps in the next question
// without reloading the page.
//
// The page passes showQuestion(question), which fills in a new question,
// audioUrl, the recording for the question shown on load, and optionally
// onResult(result), called after each checked answer.

// Played on a wrong answer; resolved next to this script so it works under any static path
const INCORRECT_SOUND_URL = new URL("sounds/incorrect.mp3", document.currentScript.src).href;

function setupDrill({ showQuestion, audioUrl, onResult }) {
    const incorrectSound = new Audio(INCORRECT_SOUND_URL);
    const form = document.getElementById("drillForm");
    const input = document.getElementById("inputField");
    const progress = document.querySelector("progress");
    const counter = document.getElementById("questionCounter");
    const feedback = document.getElementById("feedback");
    const verdict = document.getElementById("verdict");
    const answerLine = document.getElementById("answerLine");
    const answer = document.getElementById("answer");
    const message = document.getElementById("message");

    let audio = audioUrl ? new Audio(audioUrl) : null;
    let busy = false;

    const clearFeedback = () => {
        feedback.hidden = true;
        message.hidden = true;
    };

    const showMessage = (text) => {
        feedback.hidden = false;
        verdict.hidden = true;
        answerLine.hidden = true;
        message.textContent = text;
        message.hidden = false;
    };

    const showResult = (result) => {
        feedback.hidden = false;
        message.hidden = true;
        verdict.hidden = false;
        verdict.textContent = result.correct ? "Correct!" : "Wrong!";
        verdict.style.color = result.correct ? "green" : "red";
        answerLine.hidden = false;
        answerLine.classList.toggle("wrong", !result.correct);
        answer.textContent = result.answer;
        answer.className = "correct-answer " + (result.gender || "");
        if (onResult) {
            onResult(result);
        }
    };

    // Calls done() once the recording has finished, or soon if it can't play
    const playAudio = (url, done) => {
        if (!url) {
            setTimeout(done, 1500);
            return;
        }
        const sound = audio && audio.src.endsWith(url) ? audio : new Audio(url);
        let finished = false;
        const finish = () => {
            if (!finished) {
                finished = true;
                done();
            }
        };
        sound.addEventListener("ended", finish, { once: true });
        sound.addEventListener("error", () => setTimeout(finish, 1500), { once: true });
        sound.currentTime = 0;
        sound.play().catch(() => setTimeout(finish, 1500));
    };

    const nextQuestion = (question) => {
        if (!question) {
            window.location.reload();
            return;
        }
        showQuestion(question);
        audio = question.audio_url ? new Audio(question.audio_url) : null;
        clearFeedback();
        input.value = "";
        input.disabled = false;
        input.focus();
        busy = false;
    };

    form.addEventListener("submit", async (event) => {
        event.preventDefault();
        if (busy) {
            return;
        }
        busy = true;

        let result;
        try {
            const response = await fetch(form.action, {
                method: "POST",
                body: new FormData(form),
                headers: { Accept: "application/json" },
            });
            if (!response.ok) {
                throw new Error(response.statusText);
            }
            result = await response.json();
        } catch (error) {
            // Most likely an expired session, so start over with a fresh page
            window.location.reload();
            return;
        }

        if (result.redirect) {
            window.location.href = result.redirect;
            return;
        }
        if (result.message) {
            showMessage(result.message);
            input.focus();
            busy = false;
            return;
        }
        if (!("correct" in result)) {
            nextQuestion(result.next);
            return;
        }

        showResult(result);
        if (result.correct) {
            progress.value = result.done;
            input.disabled = true;
            playAudio(result.audio_url, () => {
                if (result.finished) {
                    window.location.href = result.finished;
                    return;
                }
                counter.textContent = `${result.done + 1} / ${result.total}`;
                nextQuestion(result.next);
            });
        } else {
            // The same question stays, so the user can type it again.
            // The error sound plays first, then the recording of the right answer.
            let played = false;
            const playAnswer = () => {
                if (!played) {
                    played = true;
                    if (result.audio_url) {
                        playAudio(result.audio_url, () => {});
                    }
                }
            };
            incorrectSound.addEventListener("ended", playAnswer, { once: true });
            incorrectSound.addEventListener("error", playAnswer, { once: true });
            incorrectSound.currentTime = 0;
            incorrectSound.play().catch(playAnswer);
            input.value = "";
            input.focus();
            busy = false;
        }
    });
}
