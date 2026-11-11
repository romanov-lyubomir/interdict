"""Italian verb conjugation for the verb pages and the search.

conjugate(infinitive) returns every tense in the same shape as
data/italian/conjugations.json: {tense: {person: [forms]}}, with "lui" for
lui/lei/Lei and both genders of a participle that agrees ("andato", "andata").
The 21 verbs of that file are taken from it as they are. Other verbs are built
from the rules of their group, with the irregular parts listed below; verbs
such as "riprendere" or "ottenere" borrow the irregular parts of their base.
"""

import json
import os

ROOT = os.path.dirname(os.path.abspath(__file__))
PERSONS = ["io", "tu", "lui", "noi", "voi", "loro"]
IMPERATIVE_PERSONS = ["tu", "lui", "noi", "voi", "loro"]
REFLEXIVE = {"io": "mi", "tu": "ti", "lui": "si", "noi": "ci", "voi": "vi", "loro": "si"}

# The tenses in the order of the Verb tenses sheet, with their style tag
TENSES = [
    ("presente", "ip"), ("imperfetto", "im"), ("passato_prossimo", "pp"), ("trapassato_prossimo", "tp"),
    ("passato_remoto", "pr"), ("trapassato_remoto", "tr"), ("futuro_semplice", "fs"), ("futuro_anteriore", "fa"),
    ("condizionale_presente", "cop"), ("condizionale_passato", "cpa"),
    ("congiuntivo_presente", "csp"), ("congiuntivo_passato", "csa"),
    ("congiuntivo_imperfetto", "csi"), ("congiuntivo_trapassato", "cst"),
    ("imperativo", "imv"), ("imperativo_negativo", "imv"),
]

# Verbs in -ire without -isc-; every other verb in -ire takes it
NO_ISC = {
    "dormire", "partire", "sentire", "aprire", "offrire", "seguire", "servire", "vestire", "coprire",
    "scoprire", "soffrire", "fuggire", "bollire", "cucire", "divertire", "mentire", "morire", "salire",
    "venire", "uscire", "avvertire", "consentire", "convertire", "investire", "pentire", "riempire",
    "inseguire", "proseguire", "conseguire", "ricoprire", "riaprire", "ripartire", "risentire",
}

# Verbs that take essere in the compound tenses (reflexive verbs always do)
ESSERE = {
    "andare", "venire", "arrivare", "partire", "tornare", "ritornare", "uscire", "riuscire", "entrare",
    "essere", "stare", "rimanere", "restare", "diventare", "divenire", "nascere", "morire", "cadere",
    "accadere", "piacere", "dispiacere", "sembrare", "parere", "apparire", "succedere", "bastare",
    "costare", "durare", "crescere", "scendere", "salire", "fuggire", "avvenire", "mancare", "dimagrire",
    "invecchiare", "guarire", "sparire", "svanire", "esistere", "piovere", "nevicare", "capitare",
    "risultare", "scappare", "calare", "aumentare", "diminuire", "scivolare", "ritornare", "ripartire",
    "risalire", "intervenire", "sopravvivere", "dipendere", "sorgere", "ringiovanire", "fiorire",
    "fuggire", "dimagrire",
}
# Verbs whose irregular base takes essere while they take avere
AVERE = {"prevenire"}

# Irregular parts: "pres" (six forms), "pr" (passato remoto io, lui, loro;
# the other three are regular), "pp" (participle), "fut" (stem of the future
# and conditional), "imperf" (stem of the imperfetto, also giving the gerund
# and the congiuntivo imperfetto), "gerund" (when only the gerund is odd), "base" (a regular-looking infinitive for
# verbs in -rre), "imv_tu" (imperative with tu)
IRREGULAR = {
    "bere": {"base": "bevere", "pres": ["bevo", "bevi", "beve", "beviamo", "bevete", "bevono"], "fut": "berr",
             "pr": ["bevvi", "bevve", "bevvero"], "pp": "bevuto"},
    "rimanere": {"pres": ["rimango", "rimani", "rimane", "rimaniamo", "rimanete", "rimangono"], "fut": "rimarr",
                 "pr": ["rimasi", "rimase", "rimasero"], "pp": "rimasto"},
    "tenere": {"pres": ["tengo", "tieni", "tiene", "teniamo", "tenete", "tengono"], "fut": "terr",
               "pr": ["tenni", "tenne", "tennero"], "pp": "tenuto"},
    "scegliere": {"pres": ["scelgo", "scegli", "sceglie", "scegliamo", "scegliete", "scelgono"],
                  "pr": ["scelsi", "scelse", "scelsero"], "pp": "scelto"},
    "togliere": {"pres": ["tolgo", "togli", "toglie", "togliamo", "togliete", "tolgono"],
                 "pr": ["tolsi", "tolse", "tolsero"], "pp": "tolto"},
    "cogliere": {"pres": ["colgo", "cogli", "coglie", "cogliamo", "cogliete", "colgono"],
                 "pr": ["colsi", "colse", "colsero"], "pp": "colto"},
    "salire": {"pres": ["salgo", "sali", "sale", "saliamo", "salite", "salgono"]},
    "morire": {"pres": ["muoio", "muori", "muore", "moriamo", "morite", "muoiono"], "pp": "morto"},
    "piacere": {"pres": ["piaccio", "piaci", "piace", "piacciamo", "piacete", "piacciono"],
                "pr": ["piacqui", "piacque", "piacquero"], "pp": "piaciuto"},
    "sedere": {"pres": ["siedo", "siedi", "siede", "sediamo", "sedete", "siedono"], "pp": "seduto"},
    "porre": {"base": "ponere", "pres": ["pongo", "poni", "pone", "poniamo", "ponete", "pongono"],
              "fut": "porr", "pr": ["posi", "pose", "posero"], "pp": "posto"},
    "durre": {"base": "ducere", "pres": ["duco", "duci", "duce", "duciamo", "ducete", "ducono"],
              "fut": "durr", "pr": ["dussi", "dusse", "dussero"], "pp": "dotto"},
    "nascere": {"pr": ["nacqui", "nacque", "nacquero"], "pp": "nato"},
    "vivere": {"pr": ["vissi", "visse", "vissero"], "pp": "vissuto", "fut": "vivr"},
    "conoscere": {"pr": ["conobbi", "conobbe", "conobbero"], "pp": "conosciuto"},
    "crescere": {"pr": ["crebbi", "crebbe", "crebbero"], "pp": "cresciuto"},
    "prendere": {"pr": ["presi", "prese", "presero"], "pp": "preso"},
    "leggere": {"pr": ["lessi", "lesse", "lessero"], "pp": "letto"},
    "mettere": {"pr": ["misi", "mise", "misero"], "pp": "messo"},
    "scrivere": {"pr": ["scrissi", "scrisse", "scrissero"], "pp": "scritto"},
    "chiedere": {"pr": ["chiesi", "chiese", "chiesero"], "pp": "chiesto"},
    "rispondere": {"pr": ["risposi", "rispose", "risposero"], "pp": "risposto"},
    "nascondere": {"pr": ["nascosi", "nascose", "nascosero"], "pp": "nascosto"},
    "chiudere": {"pr": ["chiusi", "chiuse", "chiusero"], "pp": "chiuso"},
    "decidere": {"pr": ["decisi", "decise", "decisero"], "pp": "deciso"},
    "dividere": {"pr": ["divisi", "divise", "divisero"], "pp": "diviso"},
    "uccidere": {"pr": ["uccisi", "uccise", "uccisero"], "pp": "ucciso"},
    "ridere": {"pr": ["risi", "rise", "risero"], "pp": "riso"},
    "correre": {"pr": ["corsi", "corse", "corsero"], "pp": "corso"},
    "perdere": {"pr": ["persi", "perse", "persero"], "pp": "perso"},
    "vincere": {"pr": ["vinsi", "vinse", "vinsero"], "pp": "vinto"},
    "spendere": {"pr": ["spesi", "spese", "spesero"], "pp": "speso"},
    "scendere": {"pr": ["scesi", "scese", "scesero"], "pp": "sceso"},
    "accendere": {"pr": ["accesi", "accese", "accesero"], "pp": "acceso"},
    "rendere": {"pr": ["resi", "rese", "resero"], "pp": "reso"},
    "piangere": {"pr": ["piansi", "pianse", "piansero"], "pp": "pianto"},
    "dipingere": {"pr": ["dipinsi", "dipinse", "dipinsero"], "pp": "dipinto"},
    "spingere": {"pr": ["spinsi", "spinse", "spinsero"], "pp": "spinto"},
    "fingere": {"pr": ["finsi", "finse", "finsero"], "pp": "finto"},
    "giungere": {"pr": ["giunsi", "giunse", "giunsero"], "pp": "giunto"},
    "distinguere": {"pr": ["distinsi", "distinse", "distinsero"], "pp": "distinto"},
    "cuocere": {"pres": ["cuocio", "cuoci", "cuoce", "cuociamo", "cuocete", "cuociono"],
                "pr": ["cossi", "cosse", "cossero"], "pp": "cotto"},
    "muovere": {"pr": ["mossi", "mosse", "mossero"], "pp": "mosso"},
    "succedere": {"pr": ["successi", "successe", "successero"], "pp": "successo"},
    "discutere": {"pr": ["discussi", "discusse", "discussero"], "pp": "discusso"},
    "esprimere": {"pr": ["espressi", "espresse", "espressero"], "pp": "espresso"},
    "cadere": {"pr": ["caddi", "cadde", "caddero"], "pp": "caduto", "fut": "cadr"},
    "accorgere": {"pr": ["accorsi", "accorse", "accorsero"], "pp": "accorto"},
    "spegnere": {"pres": ["spengo", "spegni", "spegne", "spegniamo", "spegnete", "spengono"],
                 "pr": ["spensi", "spense", "spensero"], "pp": "spento"},
    "rompere": {"pr": ["ruppi", "ruppe", "ruppero"], "pp": "rotto"},
    "assumere": {"pr": ["assunsi", "assunse", "assunsero"], "pp": "assunto"},
    "proteggere": {"pr": ["protessi", "protesse", "protessero"], "pp": "protetto"},
    "dirigere": {"pr": ["diressi", "diresse", "diressero"], "pp": "diretto"},
    "alludere": {"pr": ["allusi", "alluse", "allusero"], "pp": "alluso"},
    "deludere": {"pr": ["delusi", "deluse", "delusero"], "pp": "deluso"},
    "illudere": {"pr": ["illusi", "illuse", "illusero"], "pp": "illuso"},
    "concludere": {"pr": ["conclusi", "concluse", "conclusero"], "pp": "concluso"},
    "diffondere": {"pr": ["diffusi", "diffuse", "diffusero"], "pp": "diffuso"},
    "distruggere": {"pr": ["distrussi", "distrusse", "distrussero"], "pp": "distrutto"},
    "esigere": {"pp": "esatto"},
    "presumere": {"pr": ["presunsi", "presunse", "presunsero"], "pp": "presunto"},
    "tendere": {"pr": ["tesi", "tese", "tesero"], "pp": "teso"},
    "scindere": {"pr": ["scissi", "scisse", "scissero"], "pp": "scisso"},
    "risolvere": {"pr": ["risolsi", "risolse", "risolsero"], "pp": "risolto"},
    "volgere": {"pr": ["volsi", "volse", "volsero"], "pp": "volto"},
    "tacere": {"pres": ["taccio", "taci", "tace", "tacciamo", "tacete", "tacciono"],
               "pr": ["tacqui", "tacque", "tacquero"], "pp": "taciuto"},
    "aprire": {"pp": "aperto"},
    "offrire": {"pp": "offerto"},
    "coprire": {"pp": "coperto"},
    "soffrire": {"pp": "sofferto"},
    "apparire": {"pres": ["appaio", "appari", "appare", "appariamo", "apparite", "appaiono"],
                 "pr": ["apparvi", "apparve", "apparvero"], "pp": "apparso"},
    "parere": {"pres": ["paio", "pari", "pare", "paiamo", "parete", "paiono"], "fut": "parr",
               "pr": ["parvi", "parve", "parvero"], "pp": "parso"},
    "valere": {"pres": ["valgo", "vali", "vale", "valiamo", "valete", "valgono"], "fut": "varr",
               "pr": ["valsi", "valse", "valsero"], "pp": "valso"},
    "trarre": {"base": "traere", "pres": ["traggo", "trai", "trae", "traiamo", "traete", "traggono"],
               "fut": "trarr", "pr": ["trassi", "trasse", "trassero"], "pp": "tratto"},
    "cucire": {"pres": ["cucio", "cuci", "cuce", "cuciamo", "cucite", "cuciono"]},
    "godere": {"fut": "godr"},
    "assistere": {"pp": "assistito"},
    "insistere": {"pp": "insistito"},
    "esistere": {"pp": "esistito"},
    "difendere": {"pr": ["difesi", "difese", "difesero"], "pp": "difeso"},
    "offendere": {"pr": ["offesi", "offese", "offesero"], "pp": "offeso"},
    "dipendere": {"pr": ["dipesi", "dipese", "dipesero"], "pp": "dipeso"},
    "sospendere": {"pr": ["sospesi", "sospese", "sospesero"], "pp": "sospeso"},
    "sciogliere": {"pres": ["sciolgo", "sciogli", "scioglie", "sciogliamo", "sciogliete", "sciolgono"],
                   "pr": ["sciolsi", "sciolse", "sciolsero"], "pp": "sciolto"},
    "stringere": {"pr": ["strinsi", "strinse", "strinsero"], "pp": "stretto"},
    "pungere": {"pr": ["punsi", "punse", "punsero"], "pp": "punto"},
    "spargere": {"pr": ["sparsi", "sparse", "sparsero"], "pp": "sparso"},
    "sorgere": {"pr": ["sorsi", "sorse", "sorsero"], "pp": "sorto"},
    "mordere": {"pr": ["morsi", "morse", "morsero"], "pp": "morso"},
    "radere": {"pr": ["rasi", "rase", "rasero"], "pp": "raso"},
    "invadere": {"pr": ["invasi", "invase", "invasero"], "pp": "invaso"},
    "persuadere": {"pr": ["persuasi", "persuase", "persuasero"], "pp": "persuaso"},
    "includere": {"pr": ["inclusi", "incluse", "inclusero"], "pp": "incluso"},
    "confondere": {"pr": ["confusi", "confuse", "confusero"], "pp": "confuso"},
    "correggere": {"pr": ["corressi", "corresse", "corressero"], "pp": "corretto"},
    "friggere": {"pr": ["frissi", "frisse", "frissero"], "pp": "fritto"},
    "immergere": {"pr": ["immersi", "immerse", "immersero"], "pp": "immerso"},
    "riempire": {"pres": ["riempio", "riempi", "riempie", "riempiamo", "riempite", "riempiono"], "gerund": "riempiendo"},
    "sconfiggere": {"pr": ["sconfissi", "sconfisse", "sconfissero"], "pp": "sconfitto"},
}

# Prefixes under which a verb keeps the irregular parts of its base, and the
# bases that allow it (so "costare" doesn't borrow from "stare")
PREFIXES = ["o", "i", "ri", "s", "so", "sor", "per", "pro", "com", "con", "de", "di", "dis", "ap", "at", "ac", "ot", "man",
            "tra", "sop", "sotto", "inter", "ab", "ad", "e", "es", "im", "in", "op", "pre", "sup", "sor", "sod",
            "sod", "tras", "trat", "intro", "re", "rac", "rad", "ag", "ar", "ap", "av", "contrad", "pro"]
PREFIXABLE = {"venire", "tenere", "prendere", "mettere", "scrivere", "porre", "durre", "fare", "dire", "muovere",
              "cogliere", "togliere", "vedere", "scendere", "chiudere", "correre", "rendere", "ridere", "uscire",
              "cadere", "vivere", "scoprire", "coprire", "aprire", "giungere", "conoscere", "chiedere", "spingere",
              "accendere", "rompere", "dividere", "sedere", "tenere", "venire", "stare", "leggere",
              "piacere", "assumere", "tendere", "piangere", "scindere", "volgere", "valere", "tacere",
              "vincere", "salire", "trarre", "tenere"}
PREFIXED_STARE = {"sottostare", "soprastare"}


def load_table():
    path = os.path.join(ROOT, "data", "italian", "conjugations.json")
    with open(path, encoding="utf-8") as table_file:
        return json.load(table_file)


TABLE = load_table()


def split_reflexive(infinitive):
    # "svegliarsi" → ("svegliare", True); "porsi" → ("porre", True)
    if infinitive.endswith("rsi"):
        base = infinitive[:-3] + "re"
        if infinitive.endswith(("orsi", "ursi")):
            base = infinitive[:-3] + "rre"
        return base, True
    return infinitive, False


def borrowed(verb):
    # The irregular base a prefixed verb conjugates like, and the prefix
    for base in sorted(set(IRREGULAR) | set(TABLE) | {"durre"}, key=len, reverse=True):
        if verb != base and verb.endswith(base):
            prefix = verb[: -len(base)]
            if base == "durre" and prefix:
                return base, prefix
            if base in PREFIXABLE and (prefix in PREFIXES or len(prefix) >= 2) and verb not in ("costare",):
                if base == "stare" and verb not in PREFIXED_STARE:
                    continue
                if base == "dire" and verb not in ("contraddire", "predire", "disdire", "maledire", "benedire"):
                    continue
                if base == "fare" and not verb.endswith("sfare") and verb not in ("rifare", "disfare"):
                    continue
                if base == "vedere" and prefix not in ("pre", "ri", "intra", "prov"):
                    continue
                return base, prefix
    return None, ""


def join(stem, ending, group):
    # Spelling that keeps the sound of the stem in verbs in -are
    if group == "are":
        if stem.endswith(("ci", "gi")) and ending[:1] in ("e", "i"):
            return stem[:-1] + ending
        if stem.endswith("i") and ending.startswith("i"):
            return stem + ending[1:]
        if stem.endswith(("c", "g")) and ending[:1] in ("e", "i"):
            return stem + "h" + ending
    if group != "are" and stem.endswith("i") and ending.startswith("i") and not stem.endswith(("gli", "gni")):
        return stem + ending[1:]
    return stem + ending


def six(stem, endings, group):
    return {person: [join(stem, ending, group)] for person, ending in zip(PERSONS, endings)}


def regular(verb):
    """The simple tenses of a verb that follows its group, with irregular parts."""
    base, prefix = borrowed(verb) if verb not in TABLE and verb not in IRREGULAR else (None, "")
    if base in TABLE:
        return {tense: {person: [prefix + form for form in forms] for person, forms in persons.items()}
                for tense, persons in TABLE[base].items()}, base
    parts = dict(IRREGULAR.get(base or verb, {}))
    if base:
        parts = {key: ([prefix + item for item in value] if isinstance(value, list) else prefix + value)
                 for key, value in parts.items()}
    # Verbs in -rre conjugate like their old infinitive in -ere ("porre" like "ponere")
    infinitive = parts.get("base", verb)
    group = infinitive[-3:]
    stem = infinitive[:-3]
    isc = group == "ire" and verb not in NO_ISC and (base or verb) not in NO_ISC
    vowel = {"are": "a", "ere": "e", "ire": "i"}[group]

    tenses = {}
    if "pres" in parts:
        tenses["presente"] = {person: [form] for person, form in zip(PERSONS, parts["pres"])}
    elif group == "are":
        tenses["presente"] = six(stem, ["o", "i", "a", "iamo", "ate", "ano"], group)
    elif isc:
        tenses["presente"] = six(stem, ["isco", "isci", "isce", "iamo", "ite", "iscono"], group)
    else:
        tenses["presente"] = six(stem, ["o", "i", "e", "iamo", "ete" if group == "ere" else "ite", "ono"], group)

    imperf = parts.get("imperf", stem + vowel)
    tenses["imperfetto"] = {person: [imperf + ending] for person, ending in
                            zip(PERSONS, ["vo", "vi", "va", "vamo", "vate", "vano"])}

    remote = {"are": ["ai", "asti", "ò", "ammo", "aste", "arono"],
              "ere": ["ei", "esti", "é", "emmo", "este", "erono"],
              "ire": ["ii", "isti", "ì", "immo", "iste", "irono"]}[group]
    tenses["passato_remoto"] = six(stem, remote, group)
    if "pr" in parts:
        io, lui, loro = parts["pr"]
        tenses["passato_remoto"].update({"io": [io], "lui": [lui], "loro": [loro]})

    future = parts.get("fut", join(stem, "er", group) if group in ("are", "ere") else stem + "ir")
    tenses["futuro_semplice"] = {person: [future + ending] for person, ending in
                                 zip(PERSONS, ["ò", "ai", "à", "emo", "ete", "anno"])}
    tenses["condizionale_presente"] = {person: [future + ending] for person, ending in
                                       zip(PERSONS, ["ei", "esti", "ebbe", "emmo", "este", "ebbero"])}

    present = [tenses["presente"][person][0] for person in PERSONS]
    if group == "are" and "pres" not in parts:
        subjunctive = [join(stem, ending, group) for ending in ["i", "i", "i", "iamo", "iate", "ino"]]
    else:
        root = present[0][:-1]
        noi = present[3]
        subjunctive = [root + "a", root + "a", root + "a", noi, noi[:-2] + "te", root + "ano"]
    tenses["congiuntivo_presente"] = {person: [form] for person, form in zip(PERSONS, subjunctive)}

    tenses["congiuntivo_imperfetto"] = {person: [imperf + ending] for person, ending in
                                        zip(PERSONS, ["ssi", "ssi", "sse", "ssimo", "ste", "ssero"])}

    tu = parts.get("imv_tu", join(stem, "a", group) if group == "are" else present[1])
    tenses["imperativo"] = {"tu": [tu], "lui": [subjunctive[2]], "noi": [present[3]],
                            "voi": [present[4]], "loro": [subjunctive[5]]}

    gerund_stem = imperf[:-1] if "imperf" in parts else stem
    tenses["gerundio"] = {"-": [parts.get("gerund") or
                                gerund_stem + ("ando" if group == "are" and "imperf" not in parts else "endo")]}
    tenses["participio_passato"] = {"-": [parts.get("pp", stem + {"are": "ato", "ere": "uto", "ire": "ito"}[group])]}
    return tenses, base


def compound(tenses, participle, essere, reflexive):
    """The compound tenses, from the auxiliary's simple tenses."""
    auxiliary = TABLE["essere" if essere else "avere"]
    stem = participle[:-1]
    result = {}
    for name, aux_tense in [("passato_prossimo", "presente"), ("trapassato_prossimo", "imperfetto"),
                            ("trapassato_remoto", "passato_remoto"), ("futuro_anteriore", "futuro_semplice"),
                            ("condizionale_passato", "condizionale_presente"),
                            ("congiuntivo_passato", "congiuntivo_presente"),
                            ("congiuntivo_trapassato", "congiuntivo_imperfetto")]:
        result[name] = {}
        for person in PERSONS:
            aux = auxiliary[aux_tense][person][0]
            if essere:
                endings = ["o", "a"] if person in ("io", "tu", "lui") else ["i", "e"]
                forms = [f"{aux} {stem}{ending}" for ending in endings]
            else:
                forms = [f"{aux} {participle}"]
            if reflexive:
                forms = [f"{REFLEXIVE[person]} {form}" for form in forms]
            result[name][person] = forms
    return result


def attach(form, pronoun):
    # Pronouns joined to the end of an imperative or gerund: "svegliati"
    if form.endswith("'"):
        double = pronoun[0] if pronoun != "gli" else ""
        return form[:-1] + double + pronoun
    return form + pronoun


VERB_ENDINGS = ("are", "ere", "ire", "rre", "rsi")


# Verbs the rules would get wrong and that are too rare to list
UNSUPPORTED = {"adempiere", "esimersi", "vertere"}
# English words that look like infinitives, from the older lessons in English
NOT_ITALIAN = {"were", "here", "there", "where", "more", "care", "fire", "wire", "hire", "sure", "pure", "cure",
               "core", "share", "store", "score", "square", "compare", "prepare", "declare", "aware", "rare"}


def is_verb(word):
    # A single word that looks like an infinitive this module can conjugate
    return (word.isalpha() and word.islower() and len(word) > 3 and word.endswith(VERB_ENDINGS)
            and word not in UNSUPPORTED and word not in NOT_ITALIAN)


def conjugate(infinitive):
    infinitive = infinitive.strip().lower()
    if not is_verb(infinitive):
        raise ValueError(f"not a verb this module can conjugate: {infinitive!r}")
    verb, reflexive = split_reflexive(infinitive)
    if verb in TABLE and not reflexive:
        tenses = dict(TABLE[verb])
        tenses["imperativo_negativo"] = negative_imperative(verb, tenses, False)
        return tenses
    if verb in TABLE:
        tenses, base = {key: value for key, value in TABLE[verb].items()}, None
    else:
        tenses, base = regular(verb)
    tenses = {key: value for key, value in tenses.items()
              if key not in ("passato_prossimo", "trapassato_prossimo", "trapassato_remoto", "futuro_anteriore",
                             "condizionale_passato", "congiuntivo_passato", "congiuntivo_trapassato")}
    essere = auxiliary(infinitive) == "essere"
    participle = tenses["participio_passato"]["-"][0]
    if reflexive:
        for name in ("presente", "imperfetto", "passato_remoto", "futuro_semplice", "condizionale_presente",
                     "congiuntivo_presente", "congiuntivo_imperfetto"):
            tenses[name] = {person: [f"{REFLEXIVE[person]} {form}" for form in forms]
                            for person, forms in tenses[name].items()}
        imperative = tenses["imperativo"]
        tenses["imperativo"] = {
            "tu": [attach(form, "ti") for form in imperative["tu"]],
            "lui": [f"si {form}" for form in imperative["lui"]],
            "noi": [attach(form, "ci") for form in imperative["noi"]],
            "voi": [attach(form, "vi") for form in imperative["voi"]],
            "loro": [f"si {form}" for form in imperative["loro"]],
        }
        tenses["gerundio"] = {"-": [attach(form, "si") for form in tenses["gerundio"]["-"]]}
    tenses["imperativo_negativo"] = negative_imperative(verb, tenses, reflexive)
    tenses.update(compound(tenses, participle, essere, reflexive))
    return tenses


def negative_imperative(verb, tenses, reflexive):
    """Non + the infinitive with tu, non + the imperative with the others.
    The pronoun of a reflexive verb can go before the verb or after it."""
    affirmative = tenses.get("imperativo")
    if not affirmative:
        return {}
    present = tenses["presente"]
    if not reflexive:
        result = {"tu": [f"non {verb}"]}
        result.update({person: [f"non {form}" for form in forms]
                       for person, forms in affirmative.items() if person != "tu"})
        return result
    # "svegliare" → "svegliar"; "porre" → "por"
    stem = verb[:-2] if verb.endswith("rre") else verb[:-1]
    return {
        "tu": [f"non ti {verb}", f"non {stem}ti"],
        "lui": [f"non {form}" for form in affirmative["lui"]],
        "noi": [f"non {present['noi'][0]}", f"non {affirmative['noi'][0]}"],
        "voi": [f"non {present['voi'][0]}", f"non {affirmative['voi'][0]}"],
        "loro": [f"non {form}" for form in affirmative["loro"]],
    }


def auxiliary(infinitive):
    verb, reflexive = split_reflexive(infinitive)
    base, _ = borrowed(verb)
    if not reflexive and verb in AVERE:
        return "avere"
    return "essere" if reflexive or verb in ESSERE or (base or "") in ESSERE else "avere"


def is_irregular(infinitive):
    verb, _ = split_reflexive(infinitive)
    base, _ = borrowed(verb)
    regular_verbs = {"abitare", "parlare", "trovare", "dormire", "capire", "finire"}
    if verb in regular_verbs:
        return False
    return verb in IRREGULAR or verb in TABLE or base is not None


# The verbs the search knows, and every form of them


def find_verbs(lessons, stories, extra=()):
    """Infinitives used in the lessons and stories, plus those listed here
    and in extra (the verbs written up in verb_details.json)."""
    import re

    found = set(TABLE) | {verb for verb in IRREGULAR if verb != "durre"} | set(extra)
    for story in stories.values():
        for paragraph in story["paragraphs"]:
            for part in paragraph:
                lemma = part.get("lemma", "")
                if is_verb(lemma):
                    found.add(lemma)
    pattern = re.compile(r"\b([a-z]{3,}(?:are|ere|ire|rre|rsi))\b")
    for level_lessons in lessons.values():
        for lesson in level_lessons:
            for word, _ in lesson["vocabulary"].get("words", []):
                if is_verb(word):
                    found.add(word)
            # Hints such as "(svegliarsi)" in the exercises
            text = json.dumps(lesson, ensure_ascii=False)
            found.update(match for match in re.findall(r"\(([a-z]+(?:are|ere|ire|rre|rsi))\)", text))
    good = set()
    for verb in found:
        try:
            conjugate(verb)
            good.add(verb)
        except (ValueError, KeyError, IndexError):
            pass
    return sorted(good)


def form_index(verb_list, fold):
    """{folded form: [(verb, tense, person, form)]}, for every form of every verb."""
    index = {}
    for verb in verb_list:
        for tense, persons in conjugate(verb).items():
            for person, forms in persons.items():
                for form in forms:
                    entry = (verb, tense, person, form)
                    keys = {fold(form)}
                    # "mi sveglio" can also be looked up as "sveglio"
                    words = form.split()
                    if len(words) > 1 and words[0] in REFLEXIVE.values():
                        keys.add(fold(" ".join(words[1:])))
                    for key in keys:
                        index.setdefault(key, []).append(entry)
    return index


# Names for the pages, in Italian
TENSE_NAMES = {
    "presente": "presente", "imperfetto": "imperfetto", "passato_prossimo": "passato prossimo",
    "trapassato_prossimo": "trapassato prossimo", "passato_remoto": "passato remoto",
    "trapassato_remoto": "trapassato remoto", "futuro_semplice": "futuro semplice",
    "futuro_anteriore": "futuro anteriore", "condizionale_presente": "condizionale presente",
    "condizionale_passato": "condizionale passato", "congiuntivo_presente": "congiuntivo presente",
    "congiuntivo_passato": "congiuntivo passato", "congiuntivo_imperfetto": "congiuntivo imperfetto",
    "congiuntivo_trapassato": "congiuntivo trapassato", "imperativo": "imperativo",
    "imperativo_negativo": "imperativo negativo",
    "gerundio": "gerundio", "participio_passato": "participio passato",
}
PERSON_NAMES = {"io": "io", "tu": "tu", "lui": "lui, lei, Lei", "noi": "noi", "voi": "voi", "loro": "loro"}
IMPERATIVE_NAMES = {"tu": "tu", "lui": "Lei", "noi": "noi", "voi": "voi", "loro": "Loro"}

# The moods of the verb page, each with its tenses, as on the Verb tenses sheet
MOODS = [
    ("Indicativo", ["presente", "imperfetto", "passato_prossimo", "trapassato_prossimo", "passato_remoto",
                    "trapassato_remoto", "futuro_semplice", "futuro_anteriore"]),
    ("Condizionale", ["condizionale_presente", "condizionale_passato"]),
    ("Congiuntivo", ["congiuntivo_presente", "congiuntivo_passato", "congiuntivo_imperfetto",
                     "congiuntivo_trapassato"]),
    ("Imperativo", ["imperativo"]),
]
TAGS = dict(TENSES)


def short(forms):
    # "sono andato", "sono andata" → "sono andato/a"
    if len(forms) == 2 and forms[0][:-1] == forms[1][:-1]:
        return [f"{forms[0]}/{forms[1][-1]}"]
    return forms


def with_negative(affirmative, negative):
    # One cell for both: "(non) sia" when the negative only adds "non",
    # otherwise "sii / non essere"
    if negative and all(f"non {form}" in negative for form in affirmative):
        merged = [f"(non) {form}" for form in affirmative]
        return merged + [form for form in negative if form[4:] not in affirmative]
    return affirmative + negative


def page(infinitive):
    """What the verb page shows: the moods with their tenses, person by person."""
    table = conjugate(infinitive)
    moods = []
    for mood, tenses in MOODS:
        cards = []
        for tense in tenses:
            names = IMPERATIVE_NAMES if tense.startswith("imperativo") else PERSON_NAMES
            forms = table.get(tense, {})
            if tense == "imperativo":
                negative = table.get("imperativo_negativo", {})
                rows = [(person, names[person], with_negative(forms[person], negative.get(person, [])))
                        for person in names if person in forms]
            else:
                rows = [(person, names[person], short(forms[person])) for person in names if person in forms]
            cards.append({"tense": tense, "tag": TAGS[tense], "name": TENSE_NAMES[tense], "rows": rows})
        moods.append({"name": mood, "tenses": cards})
    return {
        "infinitive": infinitive,
        "auxiliary": auxiliary(infinitive),
        "irregular": is_irregular(infinitive),
        "reflexive": split_reflexive(infinitive)[1],
        "gerund": table["gerundio"]["-"],
        "participle": table["participio_passato"]["-"],
        "moods": moods,
    }


def search(index, verb_list, query, fold, limit):
    """Verbs for a query, each verb once: the infinitive itself, infinitives that
    start with it, then verbs that have it as one of their forms."""
    folded = " ".join(fold(query).split())
    typed = " ".join(query.lower().split())
    if len(folded) < 3:
        return []
    found = {}

    def add(verb, form=None, tense=None, person=None):
        if verb not in found and len(found) < limit:
            found[verb] = {"infinitive": verb, "form": form, "tense": tense, "person": person}

    for verb in verb_list:
        if fold(verb) == folded:
            add(verb)
    for verb in verb_list:
        if fold(verb).startswith(folded):
            add(verb)
    # A form written exactly as typed, accents included, comes first
    matches = index.get(folded, [])
    exact = [entry for entry in matches if typed in (entry[3], entry[3].split(" ", 1)[-1])]
    for verb, tense, person, form in exact + matches:
        add(verb, form, tense, person)
    return list(found.values())


def describe(match):
    # "mi sono svegliata · passato prossimo, io" for a form, nothing for the infinitive
    if not match["form"]:
        return ""
    if match["tense"] in ("gerundio", "participio_passato"):
        return f"{match['form']} · {TENSE_NAMES[match['tense']]}"
    names = IMPERATIVE_NAMES if match["tense"].startswith("imperativo") else PERSON_NAMES
    return f"{match['form']} · {TENSE_NAMES[match['tense']]}, {names[match['person']]}"
