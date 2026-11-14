// The blocks for learning a new alphabet (explain.html): the letter tiles
// with their card, and the words to read that show how they're read when
// tapped. Nothing here is saved: they are for looking and trying.

// A voice for the language, if the browser has one (few have Georgian)
const voiceFor = (lang) => (window.speechSynthesis
    ? speechSynthesis.getVoices().find((voice) => voice.lang.toLowerCase().startsWith(lang))
    : null);

document.querySelectorAll(".letter-explorer").forEach((explorer) => {
    const grid = explorer.querySelector(".letter-grid");
    const lang = grid.lang || "ka";
    const card = explorer.querySelector(".letter-card");
    const big = card.querySelector(".big");
    const hint = card.querySelector(".letter-hint");
    const sound = card.querySelector(".letter-sound");
    const say = card.querySelector(".letter-say");
    const word = card.querySelector(".word");
    const wordLatin = card.querySelector(".word-latin");
    const meaning = card.querySelector(".meaning");
    const listen = card.querySelector(".letter-listen");
    const quiz = explorer.querySelector(".hide-sounds input");
    let current = null;

    const show = (tile) => {
        grid.querySelectorAll(".letter-tile.current").forEach((other) => other.classList.remove("current"));
        tile.classList.add("current", "seen");
        current = tile;
        big.textContent = tile.querySelector(".glyph").textContent;
        hint.hidden = true;
        sound.textContent = tile.dataset.latin;
        say.textContent = tile.dataset.say;
        word.textContent = tile.dataset.word;
        wordLatin.textContent = tile.dataset.wordLatin ? `(${tile.dataset.wordLatin})` : "";
        meaning.textContent = tile.dataset.meaning ? `“${tile.dataset.meaning}”` : "";
        listen.hidden = !voiceFor(lang);
    };

    grid.querySelectorAll(".letter-tile").forEach((tile) => {
        tile.addEventListener("click", () => show(tile));
    });

    // Arrow keys move between the tiles
    grid.addEventListener("keydown", (event) => {
        if (!["ArrowLeft", "ArrowRight"].includes(event.key) || !event.target.matches(".letter-tile")) return;
        const tiles = [...grid.querySelectorAll(".letter-tile")];
        const next = tiles[tiles.indexOf(event.target) + (event.key === "ArrowRight" ? 1 : -1)];
        if (next) {
            next.focus();
            show(next);
        }
    });

    quiz.addEventListener("change", () => {
        explorer.classList.toggle("quiz", quiz.checked);
        // Starting a test hides every sound again
        grid.querySelectorAll(".letter-tile.seen").forEach((tile) => tile.classList.remove("seen"));
        if (current && !quiz.checked) current.classList.add("seen");
    });

    listen.addEventListener("click", () => {
        const voice = voiceFor(lang);
        if (!voice || !current) return;
        const utterance = new SpeechSynthesisUtterance(current.dataset.word || big.textContent);
        utterance.voice = voice;
        utterance.lang = voice.lang;
        speechSynthesis.speak(utterance);
    });
});

document.querySelectorAll(".flash-word").forEach((card) => {
    card.addEventListener("click", () => {
        card.setAttribute("aria-expanded", card.getAttribute("aria-expanded") === "true" ? "false" : "true");
    });
});
