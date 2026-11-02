import re
import unicodedata

from unidecode import unidecode

GREEK = re.compile("[Ͱ-Ͽἀ-῿]")


def fold_accents(text):
    """Removes accents so answers can be typed without them.

    Latin text is transliterated ("ü" -> "u", "ß" -> "ss"). Greek text stays
    Greek and only loses its accents, so ο and ω or η and ι aren't confused.
    """
    if not GREEK.search(text):
        return unidecode(text)
    text = unicodedata.normalize("NFD", text)
    text = "".join(char for char in text if not unicodedata.combining(char))
    return text.replace("ς", "σ")


def has_only_allowed_symbols(*args, allowed_symbols="_0123456789"):
    for arg in args:
        for letter in arg:
            if not "a" <= letter <= "z" and not "A" <= letter <= "Z" and not letter in allowed_symbols:
                return False
    return True


def empty(*args):
    for arg in args:
        if not arg.strip():
            return True
    return False

def differ_by_single_char(s1, s2):
    def remove_char_at_index(s, i):
        return s[:i] + s[i+1:]

    def swap_char_at_index(s, i):
        return s[:i] + s[i+1] + s[i] + s[i+2:]
    
    if s1 == s2:
        return False
    if len(s1) < len(s2):
        s1, s2 = s2, s1
    if len(s1) - len(s2) > 1:
        return False
    elif s1[:len(s2)] == s2:
        return True
    diff = 0
    for i in range(len(s2)):
        if s1[i] != s2[i]:
            diff += 1
    if diff == 1:
        return True
    for i in range(len(s1)):
        if remove_char_at_index(s1, i) == s2:
            return True
    for i in range(len(s1) -1 ):
        if swap_char_at_index(s1, i) == s2:
            return True
    return False

def is_valid_email(email):
    if not email:
        return False
    if email[0] == "." or email[-1] == ".":
        return False
    if email[0] == "@" or email[-1] == "@":
        return False
    if email.count("@") != 1:
        return False
    if not "." in email:
        return False
    # Check if the email has two dots next to each other
    for i in range(len(email) - 1):
        if email[i] == "." and email[i + 1] == ".":
            return False
    local_part, domain = email.split("@")
    if not local_part or "." not in domain or domain.startswith(".") or domain.endswith("."):
        return False
    if not has_only_allowed_symbols(email, allowed_symbols="_0123456789.@+-"):
        return False
    return True
