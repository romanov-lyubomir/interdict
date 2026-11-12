// Shows the exercises of a lesson part one at a time, each in its own card,
// with numbered circles and arrows to move between them. The text a card
// refers to (data-ref) is shown beside it. The card on screen is remembered
// in this browser, so the part opens where it was left.
//
// A circle is marked "started" once something is answered and "done" once
// every answer is right or shown. That only reads the page; the answers
// themselves are saved by lesson.js.
//
// The arrows go on past the last exercise of a part to the first exercise of
// the next part that has exercises, and back from the first one to the last
// exercise of the part before.

const areas = [...document.querySelectorAll(".ex-area")];

// The tab of a lesson part shows how far it has got: "done" once every
// exercise is answered right (answers that were only revealed don't count)
// and every open question or writing task has an answer; "started" once
// anything is answered. The tick lists of the workbook don't count.
const answeredField = (field) => {
    if (field.matches(".choice")) return Boolean(field.querySelector("input:checked"));
    return Boolean(field.value.trim()) && field.value !== field.defaultValue;
};

const cardProgress = (card) => {
    const exercise = card.querySelector(".exercise, .free-exercise");
    if (!exercise) return null;
    const fields = [...exercise.querySelectorAll(".field, .choice, .free-text")];
    const started = fields.some((field) => answeredField(field) || field.closest(".answer")?.dataset.state);
    const complete = exercise.querySelector(".check")
        ? fields.every((field) => field.closest(".answer").dataset.state === "correct")
        : fields.every(answeredField);
    return { started, complete };
};

const markTab = (area) => {
    const panel = area.closest('[role="tabpanel"]');
    const tab = panel && document.querySelector(`[role="tab"][aria-controls="${panel.id}"]`);
    if (!tab) return;
    const parts = [...area.querySelectorAll(".ex-card")].map(cardProgress).filter(Boolean);
    if (parts.length && parts.every((part) => part.complete)) tab.dataset.progress = "done";
    else if (parts.some((part) => part.started)) tab.dataset.progress = "started";
    else delete tab.dataset.progress;
};
const pagers = new Map();

// Opens another part of the lesson on one of its exercises
const openPart = (area, index) => {
    const panel = area.closest('[role="tabpanel"]');
    const tab = panel && document.querySelector(`[role="tab"][aria-controls="${panel.id}"]`);
    if (tab) tab.click();
    pagers.get(area).show(index);
    area.scrollIntoView({ block: "start" });
};

function setupPager(area) {
    const cards = [...area.querySelectorAll(".ex-card")];
    const groups = [...area.querySelectorAll(".ref-group")];
    const dots = [...area.querySelectorAll(".pager-dot")];
    const [back, forward] = area.querySelectorAll(".pager-step");
    const main = area.querySelector(".ex-main");
    const storageKey = `exercise-${area.dataset.key}`;
    let current = 0;

    // The part before or after this one (only parts with exercises have an area)
    const neighbour = (direction) => areas[areas.indexOf(area) + direction];

    const step = (direction) => {
        const next = current + direction;
        if (next >= 0 && next < cards.length) {
            show(next, true);
            return;
        }
        const other = neighbour(direction);
        if (other) openPart(other, direction > 0 ? 0 : pagers.get(other).count - 1);
    };

    // The exercise stays in view beside a long text only if all of it fits
    // on the screen; otherwise its bottom (and the circles) couldn't be reached
    const fitSticky = () => {
        main.classList.remove("stick");
        main.classList.toggle("stick", main.offsetHeight <= window.innerHeight - 96);
    };

    const show = (index, scroll = false) => {
        current = Math.max(0, Math.min(index, cards.length - 1));
        const card = cards[current];
        cards.forEach((other) => { other.hidden = other !== card; });
        groups.forEach((group) => { group.hidden = group.dataset.ref !== card.dataset.ref; });
        area.classList.toggle("has-ref", card.dataset.ref !== undefined);
        dots.forEach((dot, position) => {
            if (position === current) dot.setAttribute("aria-current", "step");
            else dot.removeAttribute("aria-current");
        });
        if (back) {
            back.disabled = current === 0 && !neighbour(-1);
            forward.disabled = current === cards.length - 1 && !neighbour(1);
        }
        fitSticky();
        try {
            localStorage.setItem(storageKey, String(current));
        } catch (error) {
            // Without storage the part just opens on its first exercise
        }
        // Bring the top of the new card into view when it is out of sight (on
        // a phone the text above it can be long)
        const top = card.getBoundingClientRect().top;
        if (scroll && (top < 60 || top > window.innerHeight - 80)) {
            card.scrollIntoView({ block: "start" });
        }
    };

    const mark = (card, dot) => {
        if (!dot) return;
        const fields = [...card.querySelectorAll(".field, .choice, .free-text, .checklist input")];
        const answered = fields.some((field) => {
            if (field.matches(".choice")) return Boolean(field.querySelector("input:checked"));
            if (field.type === "checkbox") return field.checked;
            return field.value.trim() && field.value !== field.defaultValue;
        });
        const checkable = card.querySelector(".check");
        dot.classList.toggle("done", Boolean(checkable) && fields.every((field) => field.dataset.locked));
        dot.classList.toggle("started", answered && !dot.classList.contains("done"));
    };
    const markAll = () => cards.forEach((card, position) => mark(card, dots[position]));

    dots.forEach((dot, position) => dot.addEventListener("click", () => show(position, true)));
    if (back) {
        back.addEventListener("click", () => step(-1));
        forward.addEventListener("click", () => step(1));
    }

    // Any answer, check, reveal or start-over changes how its circle looks.
    // These listeners sit above the exercise, so they run after lesson.js
    cards.forEach((card, position) => {
        const update = () => {
            mark(card, dots[position]);
            markTab(area);
            fitSticky();
        };
        card.addEventListener("input", update);
        card.addEventListener("change", update);
        card.addEventListener("click", update);
    });

    // A link from the search asks for the card that holds what it found
    area.addEventListener("show-card", (event) => {
        const card = event.target.closest(".ex-card");
        if (card) show(cards.indexOf(card));
    });

    let saved = 0;
    try {
        saved = Number(localStorage.getItem(storageKey)) || 0;
    } catch (error) {
        // Nothing saved
    }
    show(saved);
    markAll();
    markTab(area);
    pagers.set(area, { show, count: cards.length });
    window.addEventListener("resize", fitSticky);
    // A tab opened later lays the card out only once it is shown
    document.querySelectorAll(".tab").forEach((tab) => tab.addEventListener("click", fitSticky));
}

areas.forEach(setupPager);
