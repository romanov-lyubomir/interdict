// For learners of Greek without a Greek keyboard: in the answer boxes, a
// Latin letter is written as the Greek letter on the same key of a Greek
// keyboard (a → α, u → θ, j → ξ, c → ψ, v → ω, w → ς, á → ά…). Only loaded while
// learning Greek (base.html).
//
// It works in the boxes where a Greek answer is expected: the drills
// (#inputField), the free writing of a lesson, and the lesson exercises that
// show the Greek letter keys. Exercises that ask for a reading in Latin
// letters show no keys, so they are left alone, and so are the search box,
// the login forms and everything else.

const GREEK_KEYS = {
    a: "α", b: "β", g: "γ", d: "δ", e: "ε", z: "ζ", h: "η", u: "θ",
    i: "ι", k: "κ", l: "λ", m: "μ", n: "ν", j: "ξ", o: "ο", p: "π",
    r: "ρ", s: "σ", w: "ς", t: "τ", y: "υ", f: "φ", x: "χ", c: "ψ", v: "ω",
    A: "Α", B: "Β", G: "Γ", D: "Δ", E: "Ε", Z: "Ζ", H: "Η", U: "Θ",
    I: "Ι", K: "Κ", L: "Λ", M: "Μ", N: "Ν", J: "Ξ", O: "Ο", P: "Π",
    R: "Ρ", S: "Σ", W: "Σ", T: "Τ", Y: "Υ", F: "Φ", X: "Χ", C: "Ψ", V: "Ω",
    // The vowels with an accent, for keyboards that have them (no Latin
    // letter is left for ή and ώ: they come from the letter keys)
    á: "ά", é: "έ", ó: "ό", í: "ί", ý: "ύ",
    Á: "Ά", É: "Έ", Ó: "Ό", Í: "Ί", Ý: "Ύ",
};

const wantsGreek = (field) => {
    if (!field.matches("input[type=text], textarea") || field.disabled || field.readOnly) return false;
    if (field.matches("#inputField, .free-text")) return true;
    const exercise = field.closest(".exercise");
    return Boolean(exercise && exercise.querySelector(".accents"));
};

// The text with every Latin letter turned Greek, and each accent joined to
// its letter (NFC: ί is one character, not ι followed by a separate accent)
const toGreek = (text) => [...text.normalize("NFC")]
    .map((letter) => GREEK_KEYS[letter] || letter).join("").normalize("NFC");

// A plain key press: the Greek letter is written instead of the Latin one
document.addEventListener("beforeinput", (event) => {
    const field = event.target;
    if (event.inputType !== "insertText" || !event.data || !wantsGreek(field)) return;
    const greek = toGreek(event.data);
    if (greek === event.data) return;
    event.preventDefault();
    field.setRangeText(greek, field.selectionStart, field.selectionEnd, "end");
    field.dispatchEvent(new Event("input", { bubbles: true }));
}, true);

// Letters that don't come from a plain key press: an accent typed with a
// dead key on Windows (´ then i gives í through the input method, which the
// handler above never sees), pasted text, autocorrect. Once the letter is
// in, the whole box is turned Greek, keeping the cursor where it was
const fixField = (field) => {
    const greek = toGreek(field.value);
    if (greek === field.value) return;
    const caret = toGreek(field.value.slice(0, field.selectionEnd)).length;
    field.value = greek;
    field.setSelectionRange(caret, caret);
    field.dispatchEvent(new Event("input", { bubbles: true }));
};

document.addEventListener("input", (event) => {
    if (!event.isComposing && wantsGreek(event.target)) fixField(event.target);
}, true);

document.addEventListener("compositionend", (event) => {
    if (wantsGreek(event.target)) setTimeout(() => fixField(event.target));
}, true);
