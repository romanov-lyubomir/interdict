"""Builds data/<language>/conjugations.json for the conjugation drill.

Run from the project folder:  python scripts/build_conjugations.py

Each JSON file looks like {verb: {form: {person: [accepted answers]}}}.
The first answer is the one shown as the correct answer. Forms without a
person (gerund, participle) use the person "-".
To add a verb, add it to the tables below and run the script again.
"""

import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def alts(value):
    # "a|b" -> ["a", "b"]
    return [v.strip() for v in value.split("|")]


def table(persons, values):
    # values is a list of strings or a space-free "a, b, c" string
    if isinstance(values, str):
        values = [v.strip() for v in values.split(",")]
    assert len(values) == len(persons), (persons, values)
    return {p: alts(v) for p, v in zip(persons, values) if v}


def compound(aux_forms, participles):
    # aux_forms: {person: [aux]}, participles: {person: [participle, ...]}
    result = {}
    for person, aux_list in aux_forms.items():
        result[person] = [
            f"{aux} {participle}"
            for aux in aux_list
            for participle in participles[person]
        ]
    return result


# ---------------------------------------------------------------- Italian

IT_PERSONS = ["io", "tu", "lui", "noi", "voi", "loro"]
IT_IMPERATIVE_PERSONS = ["tu", "lui", "noi", "voi", "loro"]
IT_ESSERE_VERBS = {"andare", "essere", "stare", "uscire", "venire"}

IT_ENDINGS = {
    "are": {
        "presente": "o, i, a, iamo, ate, ano",
        "imperfetto": "avo, avi, ava, avamo, avate, avano",
        "passato_remoto": "ai, asti, ò, ammo, aste, arono",
        "congiuntivo_presente": "i, i, i, iamo, iate, ino",
        "congiuntivo_imperfetto": "assi, assi, asse, assimo, aste, assero",
        "imperativo": "a, i, iamo, ate, ino",
        "gerundio": "ando",
        "participio_passato": "ato",
    },
    "ere": {
        "presente": "o, i, e, iamo, ete, ono",
        "imperfetto": "evo, evi, eva, evamo, evate, evano",
        "passato_remoto": "ei, esti, é, emmo, este, erono",
        "congiuntivo_presente": "a, a, a, iamo, iate, ano",
        "congiuntivo_imperfetto": "essi, essi, esse, essimo, este, essero",
        "imperativo": "i, a, iamo, ete, ano",
        "gerundio": "endo",
        "participio_passato": "uto",
    },
    "ire": {
        "presente": "o, i, e, iamo, ite, ono",
        "imperfetto": "ivo, ivi, iva, ivamo, ivate, ivano",
        "passato_remoto": "ii, isti, ì, immo, iste, irono",
        "congiuntivo_presente": "a, a, a, iamo, iate, ano",
        "congiuntivo_imperfetto": "issi, issi, isse, issimo, iste, issero",
        "imperativo": "i, a, iamo, ite, ano",
        "gerundio": "endo",
        "participio_passato": "ito",
    },
}
IT_FUTURE_ENDINGS = "ò, ai, à, emo, ete, anno"
IT_CONDITIONAL_ENDINGS = "ei, esti, ebbe, emmo, este, ebbero"

# Only what differs from the regular pattern is listed.
# "future_stem" is used for both futuro semplice and condizionale presente.
IT_VERBS = {
    "abitare": {},
    "andare": {
        "presente": "vado, vai, va, andiamo, andate, vanno",
        "congiuntivo_presente": "vada, vada, vada, andiamo, andiate, vadano",
        "imperativo": "va'|vai|va, vada, andiamo, andate, vadano",
        "future_stem": "andr",
    },
    "avere": {
        "presente": "ho, hai, ha, abbiamo, avete, hanno",
        "passato_remoto": "ebbi, avesti, ebbe, avemmo, aveste, ebbero",
        "congiuntivo_presente": "abbia, abbia, abbia, abbiamo, abbiate, abbiano",
        "imperativo": "abbi, abbia, abbiamo, abbiate, abbiano",
        "future_stem": "avr",
    },
    "capire": {
        "presente": "capisco, capisci, capisce, capiamo, capite, capiscono",
        "congiuntivo_presente": "capisca, capisca, capisca, capiamo, capiate, capiscano",
        "imperativo": "capisci, capisca, capiamo, capite, capiscano",
    },
    "dare": {
        "presente": "do, dai, dà, diamo, date, danno",
        "passato_remoto": "diedi|detti, desti, diede|dette, demmo, deste, diedero|dettero",
        "congiuntivo_presente": "dia, dia, dia, diamo, diate, diano",
        "congiuntivo_imperfetto": "dessi, dessi, desse, dessimo, deste, dessero",
        "imperativo": "da'|dai|dà, dia, diamo, date, diano",
        "future_stem": "dar",
    },
    "dire": {
        "presente": "dico, dici, dice, diciamo, dite, dicono",
        "imperfetto": "dicevo, dicevi, diceva, dicevamo, dicevate, dicevano",
        "passato_remoto": "dissi, dicesti, disse, dicemmo, diceste, dissero",
        "congiuntivo_presente": "dica, dica, dica, diciamo, diciate, dicano",
        "congiuntivo_imperfetto": "dicessi, dicessi, dicesse, dicessimo, diceste, dicessero",
        "imperativo": "di'|dì, dica, diciamo, dite, dicano",
        "gerundio": "dicendo",
        "participio_passato": "detto",
        "future_stem": "dir",
    },
    "dormire": {},
    "dovere": {
        "presente": "devo|debbo, devi, deve, dobbiamo, dovete, devono|debbono",
        "passato_remoto": "dovetti|dovei, dovesti, dovette|dové, dovemmo, doveste, dovettero|doverono",
        "congiuntivo_presente": "debba|deva, debba|deva, debba|deva, dobbiamo, dobbiate, debbano|devano",
        "imperativo": None,
        "future_stem": "dovr",
    },
    "essere": {
        "presente": "sono, sei, è, siamo, siete, sono",
        "imperfetto": "ero, eri, era, eravamo, eravate, erano",
        "passato_remoto": "fui, fosti, fu, fummo, foste, furono",
        "congiuntivo_presente": "sia, sia, sia, siamo, siate, siano",
        "congiuntivo_imperfetto": "fossi, fossi, fosse, fossimo, foste, fossero",
        "imperativo": "sii, sia, siamo, siate, siano",
        "gerundio": "essendo",
        "participio_passato": "stato",
        "future_stem": "sar",
    },
    "fare": {
        "presente": "faccio, fai, fa, facciamo, fate, fanno",
        "imperfetto": "facevo, facevi, faceva, facevamo, facevate, facevano",
        "passato_remoto": "feci, facesti, fece, facemmo, faceste, fecero",
        "congiuntivo_presente": "faccia, faccia, faccia, facciamo, facciate, facciano",
        "congiuntivo_imperfetto": "facessi, facessi, facesse, facessimo, faceste, facessero",
        "imperativo": "fa'|fai|fa, faccia, facciamo, fate, facciano",
        "gerundio": "facendo",
        "participio_passato": "fatto",
        "future_stem": "far",
    },
    "finire": {
        "presente": "finisco, finisci, finisce, finiamo, finite, finiscono",
        "congiuntivo_presente": "finisca, finisca, finisca, finiamo, finiate, finiscano",
        "imperativo": "finisci, finisca, finiamo, finite, finiscano",
    },
    "leggere": {
        "passato_remoto": "lessi, leggesti, lesse, leggemmo, leggeste, lessero",
        "participio_passato": "letto",
    },
    "parlare": {},
    "potere": {
        "presente": "posso, puoi, può, possiamo, potete, possono",
        "passato_remoto": "potei|potetti, potesti, poté|potette, potemmo, poteste, poterono|potettero",
        "congiuntivo_presente": "possa, possa, possa, possiamo, possiate, possano",
        "imperativo": None,
        "future_stem": "potr",
    },
    "sapere": {
        "presente": "so, sai, sa, sappiamo, sapete, sanno",
        "passato_remoto": "seppi, sapesti, seppe, sapemmo, sapeste, seppero",
        "congiuntivo_presente": "sappia, sappia, sappia, sappiamo, sappiate, sappiano",
        "imperativo": "sappi, sappia, sappiamo, sappiate, sappiano",
        "future_stem": "sapr",
    },
    "stare": {
        "presente": "sto, stai, sta, stiamo, state, stanno",
        "passato_remoto": "stetti, stesti, stette, stemmo, steste, stettero",
        "congiuntivo_presente": "stia, stia, stia, stiamo, stiate, stiano",
        "congiuntivo_imperfetto": "stessi, stessi, stesse, stessimo, steste, stessero",
        "imperativo": "sta'|stai|sta, stia, stiamo, state, stiano",
        "future_stem": "star",
    },
    "trovare": {},
    "uscire": {
        "presente": "esco, esci, esce, usciamo, uscite, escono",
        "congiuntivo_presente": "esca, esca, esca, usciamo, usciate, escano",
        "imperativo": "esci, esca, usciamo, uscite, escano",
    },
    "vedere": {
        "passato_remoto": "vidi, vedesti, vide, vedemmo, vedeste, videro",
        "participio_passato": "visto|veduto",
        "future_stem": "vedr",
    },
    "venire": {
        "presente": "vengo, vieni, viene, veniamo, venite, vengono",
        "passato_remoto": "venni, venisti, venne, venimmo, veniste, vennero",
        "congiuntivo_presente": "venga, venga, venga, veniamo, veniate, vengano",
        "imperativo": "vieni, venga, veniamo, venite, vengano",
        "participio_passato": "venuto",
        "future_stem": "verr",
    },
    "volere": {
        "presente": "voglio, vuoi, vuole, vogliamo, volete, vogliono",
        "passato_remoto": "volli, volesti, volle, volemmo, voleste, vollero",
        "congiuntivo_presente": "voglia, voglia, voglia, vogliamo, vogliate, vogliano",
        "imperativo": None,
        "future_stem": "vorr",
    },
}


def italian_verb(verb, irregular):
    group = verb[-3:]
    stem = verb[:-3]
    endings = IT_ENDINGS[group]
    forms = {}

    def simple(form, persons=IT_PERSONS):
        if form in irregular:
            return irregular[form]
        return [stem + e.strip() for e in endings[form].split(",")]

    for form in [
        "presente",
        "imperfetto",
        "passato_remoto",
        "congiuntivo_presente",
        "congiuntivo_imperfetto",
    ]:
        forms[form] = table(IT_PERSONS, simple(form))

    imperative = simple("imperativo")
    if imperative is not None:
        forms["imperativo"] = table(IT_IMPERATIVE_PERSONS, imperative)

    future_stem = irregular.get(
        "future_stem", stem + ("ir" if group == "ire" else "er")
    )
    forms["futuro_semplice"] = table(
        IT_PERSONS, [future_stem + e.strip() for e in IT_FUTURE_ENDINGS.split(",")]
    )
    forms["condizionale_presente"] = table(
        IT_PERSONS,
        [future_stem + e.strip() for e in IT_CONDITIONAL_ENDINGS.split(",")],
    )

    gerund = irregular.get("gerundio", stem + endings["gerundio"])
    participle = irregular.get("participio_passato", stem + endings["participio_passato"])
    forms["gerundio"] = {"-": alts(gerund)}
    forms["participio_passato"] = {"-": alts(participle)}
    return forms


def italian_participles(participle_options, with_essere):
    # With essere the participle agrees with the subject (andato/andata)
    result = {}
    for person in IT_PERSONS:
        options = []
        for participle in participle_options:
            if not with_essere:
                options.append(participle)
                continue
            base = participle[:-1]
            if person in ("io", "tu", "lui"):
                options += [base + "o", base + "a"]
            else:
                options += [base + "i", base + "e"]
        result[person] = options
    return result


def build_italian():
    simple_forms = {verb: italian_verb(verb, irr) for verb, irr in IT_VERBS.items()}
    result = {}
    for verb, forms in simple_forms.items():
        aux = simple_forms["essere" if verb in IT_ESSERE_VERBS else "avere"]
        participles = italian_participles(
            forms["participio_passato"]["-"], verb in IT_ESSERE_VERBS
        )
        forms["passato_prossimo"] = compound(aux["presente"], participles)
        forms["trapassato_prossimo"] = compound(aux["imperfetto"], participles)
        forms["trapassato_remoto"] = compound(aux["passato_remoto"], participles)
        forms["futuro_anteriore"] = compound(aux["futuro_semplice"], participles)
        forms["congiuntivo_passato"] = compound(aux["congiuntivo_presente"], participles)
        forms["congiuntivo_trapassato"] = compound(aux["congiuntivo_imperfetto"], participles)
        forms["condizionale_passato"] = compound(aux["condizionale_presente"], participles)
        result[verb] = forms
    return result


# ---------------------------------------------------------------- Spanish

ES_PERSONS = ["yo", "tu", "vos", "el", "nosotros", "vosotros", "ellos"]
ES_IMPERATIVE_PERSONS = ["tu", "vos", "el", "nosotros", "vosotros", "ellos"]

# Voseo: the present indicative and the affirmative imperative have their own
# forms; in the present subjunctive both "seas" and "seás" are accepted.
ES_VERBS = {
    "ser": {
        "presente": "soy, eres, sos, es, somos, sois, son",
        "preterito_imperfecto": "era, eras, eras, era, éramos, erais, eran",
        "preterito_indefinido": "fui, fuiste, fuiste, fue, fuimos, fuisteis, fueron",
        "futuro": "seré, serás, serás, será, seremos, seréis, serán",
        "condicional": "sería, serías, serías, sería, seríamos, seríais, serían",
        "subjuntivo_presente": "sea, seas, seas|seás, sea, seamos, seáis, sean",
        "subjuntivo_imperfecto": "fuera|fuese, fueras|fueses, fueras|fueses, fuera|fuese, fuéramos|fuésemos, fuerais|fueseis, fueran|fuesen",
        "subjuntivo_futuro": "fuere, fueres, fueres, fuere, fuéremos, fuereis, fueren",
        "imperativo_afirmativo": "sé, sé, sea, seamos, sed, sean",
        "gerundio": "siendo",
        "participio": "sido",
    },
    "estar": {
        "presente": "estoy, estás, estás, está, estamos, estáis, están",
        "preterito_imperfecto": "estaba, estabas, estabas, estaba, estábamos, estabais, estaban",
        "preterito_indefinido": "estuve, estuviste, estuviste, estuvo, estuvimos, estuvisteis, estuvieron",
        "futuro": "estaré, estarás, estarás, estará, estaremos, estaréis, estarán",
        "condicional": "estaría, estarías, estarías, estaría, estaríamos, estaríais, estarían",
        "subjuntivo_presente": "esté, estés, estés, esté, estemos, estéis, estén",
        "subjuntivo_imperfecto": "estuviera|estuviese, estuvieras|estuvieses, estuvieras|estuvieses, estuviera|estuviese, estuviéramos|estuviésemos, estuvierais|estuvieseis, estuvieran|estuviesen",
        "subjuntivo_futuro": "estuviere, estuvieres, estuvieres, estuviere, estuviéremos, estuviereis, estuvieren",
        "imperativo_afirmativo": "está, está, esté, estemos, estad, estén",
        "gerundio": "estando",
        "participio": "estado",
    },
    # The imperative of haber is practically never used, so it is left out
    "haber": {
        "presente": "he, has, has, ha|hay, hemos, habéis, han",
        "preterito_imperfecto": "había, habías, habías, había, habíamos, habíais, habían",
        "preterito_indefinido": "hube, hubiste, hubiste, hubo, hubimos, hubisteis, hubieron",
        "futuro": "habré, habrás, habrás, habrá, habremos, habréis, habrán",
        "condicional": "habría, habrías, habrías, habría, habríamos, habríais, habrían",
        "subjuntivo_presente": "haya, hayas, hayas|hayás, haya, hayamos, hayáis, hayan",
        "subjuntivo_imperfecto": "hubiera|hubiese, hubieras|hubieses, hubieras|hubieses, hubiera|hubiese, hubiéramos|hubiésemos, hubierais|hubieseis, hubieran|hubiesen",
        "subjuntivo_futuro": "hubiere, hubieres, hubieres, hubiere, hubiéremos, hubiereis, hubieren",
        "imperativo_afirmativo": None,
        "gerundio": "habiendo",
        "participio": "habido",
    },
}


def build_spanish():
    simple = {
        verb: {
            form: table(ES_PERSONS, values)
            for form, values in data.items()
            if form not in ("imperativo_afirmativo", "gerundio", "participio")
        }
        for verb, data in ES_VERBS.items()
    }
    haber = simple["haber"]
    result = {}
    for verb, data in ES_VERBS.items():
        forms = simple[verb]
        participle = {p: [data["participio"]] for p in ES_PERSONS}
        # "hay" is only the impersonal present, not an auxiliary
        aux = {form: {p: [a for a in v if a != "hay"] for p, v in haber[form].items()} for form in haber}
        forms["preterito_perfecto"] = compound(aux["presente"], participle)
        forms["preterito_pluscuamperfecto"] = compound(aux["preterito_imperfecto"], participle)
        forms["preterito_anterior"] = compound(aux["preterito_indefinido"], participle)
        forms["futuro_perfecto"] = compound(aux["futuro"], participle)
        forms["condicional_perfecto"] = compound(aux["condicional"], participle)
        forms["subjuntivo_perfecto"] = compound(aux["subjuntivo_presente"], participle)
        forms["subjuntivo_pluscuamperfecto"] = compound(aux["subjuntivo_imperfecto"], participle)
        forms["subjuntivo_futuro_perfecto"] = compound(aux["subjuntivo_futuro"], participle)
        if data["imperativo_afirmativo"]:
            forms["imperativo_afirmativo"] = table(
                ES_IMPERATIVE_PERSONS, data["imperativo_afirmativo"]
            )
            # Negative imperative = "no" + present subjunctive.
            # The answer is accepted with or without the "no".
            subjunctive = forms["subjuntivo_presente"]
            forms["imperativo_negativo"] = {
                p: ["no " + s for s in subjunctive[p]] + subjunctive[p]
                for p in ES_IMPERATIVE_PERSONS
            }
        forms["gerundio"] = {"-": [data["gerundio"]]}
        forms["participio"] = {"-": [data["participio"]]}
        result[verb] = forms
    return result


# ---------------------------------------------------------------- German

DE_PERSONS = ["ich", "du", "er", "wir", "ihr", "sie"]
DE_IMPERATIVE_PERSONS = ["du", "ihr", "sie"]

DE_WERDEN = {
    "praesens": "werde, wirst, wird, werden, werdet, werden",
    "konjunktiv_eins": "werde, werdest, werde, werden, werdet, werden",
    "konjunktiv_zwei": "würde, würdest, würde, würden, würdet, würden",
}

DE_VERBS = {
    "sein": {
        "auxiliary": "sein",
        "praesens": "bin, bist, ist, sind, seid, sind",
        "praeteritum": "war, warst, war, waren, wart, waren",
        "konjunktiv_eins_praesens": "sei, seiest|seist, sei, seien, seiet, seien",
        "konjunktiv_zwei_praeteritum": "wäre, wärest|wärst, wäre, wären, wäret|wärt, wären",
        "imperativ": "sei, seid, seien|seien Sie",
        "partizip_eins": "seiend",
        "partizip_zwei": "gewesen",
    },
    "haben": {
        "auxiliary": "haben",
        "praesens": "habe, hast, hat, haben, habt, haben",
        "praeteritum": "hatte, hattest, hatte, hatten, hattet, hatten",
        "konjunktiv_eins_praesens": "habe, habest, habe, haben, habet, haben",
        "konjunktiv_zwei_praeteritum": "hätte, hättest, hätte, hätten, hättet, hätten",
        "imperativ": "hab|habe, habt, haben|haben Sie",
        "partizip_eins": "habend",
        "partizip_zwei": "gehabt",
    },
}


def build_german():
    werden = {name: table(DE_PERSONS, values) for name, values in DE_WERDEN.items()}
    simple = {
        verb: {
            form: table(DE_PERSONS, data[form])
            for form in (
                "praesens",
                "praeteritum",
                "konjunktiv_eins_praesens",
                "konjunktiv_zwei_praeteritum",
            )
        }
        for verb, data in DE_VERBS.items()
    }

    def with_suffix(aux_forms, suffix):
        return {p: [f"{a} {suffix}" for a in v] for p, v in aux_forms.items()}

    result = {}
    for verb, data in DE_VERBS.items():
        forms = simple[verb]
        aux = simple[data["auxiliary"]]
        participle = data["partizip_zwei"]
        infinitive = verb
        perfect_infinitive = f"{participle} {data['auxiliary']}"
        forms["perfekt"] = with_suffix(aux["praesens"], participle)
        forms["plusquamperfekt"] = with_suffix(aux["praeteritum"], participle)
        forms["futur_eins"] = with_suffix(werden["praesens"], infinitive)
        forms["futur_zwei"] = with_suffix(werden["praesens"], perfect_infinitive)
        forms["konjunktiv_eins_perfekt"] = with_suffix(aux["konjunktiv_eins_praesens"], participle)
        forms["konjunktiv_eins_futur_eins"] = with_suffix(werden["konjunktiv_eins"], infinitive)
        forms["konjunktiv_eins_futur_zwei"] = with_suffix(werden["konjunktiv_eins"], perfect_infinitive)
        forms["konjunktiv_zwei_plusquamperfekt"] = with_suffix(aux["konjunktiv_zwei_praeteritum"], participle)
        forms["konjunktiv_zwei_futur_eins"] = with_suffix(werden["konjunktiv_zwei"], infinitive)
        forms["konjunktiv_zwei_futur_zwei"] = with_suffix(werden["konjunktiv_zwei"], perfect_infinitive)
        forms["imperativ"] = table(DE_IMPERATIVE_PERSONS, data["imperativ"])
        forms["partizip_eins"] = {"-": [data["partizip_eins"]]}
        forms["partizip_zwei"] = {"-": [participle]}
        result[verb] = forms
    return result


GR_PERSONS = ["ego", "esy", "aftos", "emeis", "eseis", "aftoi"]
GR_IMPERATIVE_PERSONS = ["esy", "eseis"]
GR_ECHO = "έχω, έχεις, έχει, έχουμε, έχετε, έχουν"
GR_EICHA = "είχα, είχες, είχε, είχαμε, είχατε, είχαν"

# present, imperfect, aorist, dependent (subjunctive) stem forms,
# infinitive (απαρέμφατο) and imperative. Verbs without an aorist or an
# imperative leave them out.
GR_VERBS = {
    "γράφω": {
        "present": "γράφω, γράφεις, γράφει, γράφουμε, γράφετε, γράφουν",
        "imperfect": "έγραφα, έγραφες, έγραφε, γράφαμε, γράφατε, έγραφαν",
        "aorist": "έγραψα, έγραψες, έγραψε, γράψαμε, γράψατε, έγραψαν",
        "dependent": "γράψω, γράψεις, γράψει, γράψουμε, γράψετε, γράψουν",
        "infinitive": "γράψει",
        "imperative": "γράψε, γράψτε",
    },
    "διαβάζω": {
        "present": "διαβάζω, διαβάζεις, διαβάζει, διαβάζουμε, διαβάζετε, διαβάζουν",
        "imperfect": "διάβαζα, διάβαζες, διάβαζε, διαβάζαμε, διαβάζατε, διάβαζαν",
        "aorist": "διάβασα, διάβασες, διάβασε, διαβάσαμε, διαβάσατε, διάβασαν",
        "dependent": "διαβάσω, διαβάσεις, διαβάσει, διαβάσουμε, διαβάσετε, διαβάσουν",
        "infinitive": "διαβάσει",
        "imperative": "διάβασε, διαβάστε",
    },
    "δουλεύω": {
        "present": "δουλεύω, δουλεύεις, δουλεύει, δουλεύουμε, δουλεύετε, δουλεύουν",
        "imperfect": "δούλευα, δούλευες, δούλευε, δουλεύαμε, δουλεύατε, δούλευαν",
        "aorist": "δούλεψα, δούλεψες, δούλεψε, δουλέψαμε, δουλέψατε, δούλεψαν",
        "dependent": "δουλέψω, δουλέψεις, δουλέψει, δουλέψουμε, δουλέψετε, δουλέψουν",
        "infinitive": "δουλέψει",
        "imperative": "δούλεψε, δουλέψτε",
    },
    "μένω": {
        "present": "μένω, μένεις, μένει, μένουμε, μένετε, μένουν",
        "imperfect": "έμενα, έμενες, έμενε, μέναμε, μένατε, έμεναν",
        "aorist": "έμεινα, έμεινες, έμεινε, μείναμε, μείνατε, έμειναν",
        "dependent": "μείνω, μείνεις, μείνει, μείνουμε, μείνετε, μείνουν",
        "infinitive": "μείνει",
        "imperative": "μείνε, μείνετε",
    },
    "κάνω": {
        "present": "κάνω, κάνεις, κάνει, κάνουμε, κάνετε, κάνουν",
        "imperfect": "έκανα, έκανες, έκανε, κάναμε, κάνατε, έκαναν",
        "aorist": "έκανα, έκανες, έκανε, κάναμε, κάνατε, έκαναν",
        "dependent": "κάνω, κάνεις, κάνει, κάνουμε, κάνετε, κάνουν",
        "infinitive": "κάνει",
        "imperative": "κάνε, κάντε",
    },
    "θέλω": {
        "present": "θέλω, θέλεις, θέλει, θέλουμε, θέλετε, θέλουν",
        "imperfect": "ήθελα, ήθελες, ήθελε, θέλαμε, θέλατε, ήθελαν",
        "aorist": "θέλησα, θέλησες, θέλησε, θελήσαμε, θελήσατε, θέλησαν",
        "dependent": "θελήσω, θελήσεις, θελήσει, θελήσουμε, θελήσετε, θελήσουν",
        "infinitive": "θελήσει",
    },
    "βλέπω": {
        "present": "βλέπω, βλέπεις, βλέπει, βλέπουμε, βλέπετε, βλέπουν",
        "imperfect": "έβλεπα, έβλεπες, έβλεπε, βλέπαμε, βλέπατε, έβλεπαν",
        "aorist": "είδα, είδες, είδε, είδαμε, είδατε, είδαν",
        "dependent": "δω, δεις, δει, δούμε, δείτε, δουν",
        "infinitive": "δει",
        "imperative": "δες, δείτε",
    },
    "λέω": {
        "present": "λέω, λες, λέει, λέμε, λέτε, λένε",
        "imperfect": "έλεγα, έλεγες, έλεγε, λέγαμε, λέγατε, έλεγαν",
        "aorist": "είπα, είπες, είπε, είπαμε, είπατε, είπαν",
        "dependent": "πω, πεις, πει, πούμε, πείτε, πουν",
        "infinitive": "πει",
        "imperative": "πες, πείτε",
    },
    "τρώω": {
        "present": "τρώω, τρως, τρώει, τρώμε, τρώτε, τρώνε",
        "imperfect": "έτρωγα, έτρωγες, έτρωγε, τρώγαμε, τρώγατε, έτρωγαν",
        "aorist": "έφαγα, έφαγες, έφαγε, φάγαμε, φάγατε, έφαγαν",
        "dependent": "φάω, φας, φάει, φάμε, φάτε, φάνε",
        "infinitive": "φάει",
        "imperative": "φάε, φάτε",
    },
    "πηγαίνω": {
        "present": "πηγαίνω|πάω, πηγαίνεις|πας, πηγαίνει|πάει, πηγαίνουμε|πάμε, πηγαίνετε|πάτε, πηγαίνουν|πάνε",
        "imperfect": "πήγαινα, πήγαινες, πήγαινε, πηγαίναμε, πηγαίνατε, πήγαιναν",
        "aorist": "πήγα, πήγες, πήγε, πήγαμε, πήγατε, πήγαν",
        "dependent": "πάω, πας, πάει, πάμε, πάτε, πάνε",
        "infinitive": "πάει",
        "imperative": "πήγαινε, πηγαίνετε",
    },
    "μιλάω": {
        "present": "μιλάω|μιλώ, μιλάς, μιλάει|μιλά, μιλάμε|μιλούμε, μιλάτε, μιλάνε|μιλούν",
        "imperfect": "μιλούσα, μιλούσες, μιλούσε, μιλούσαμε, μιλούσατε, μιλούσαν",
        "aorist": "μίλησα, μίλησες, μίλησε, μιλήσαμε, μιλήσατε, μίλησαν",
        "dependent": "μιλήσω, μιλήσεις, μιλήσει, μιλήσουμε, μιλήσετε, μιλήσουν",
        "infinitive": "μιλήσει",
        "imperative": "μίλησε, μιλήστε",
    },
    "αγαπάω": {
        "present": "αγαπάω|αγαπώ, αγαπάς, αγαπάει|αγαπά, αγαπάμε|αγαπούμε, αγαπάτε, αγαπάνε|αγαπούν",
        "imperfect": "αγαπούσα, αγαπούσες, αγαπούσε, αγαπούσαμε, αγαπούσατε, αγαπούσαν",
        "aorist": "αγάπησα, αγάπησες, αγάπησε, αγαπήσαμε, αγαπήσατε, αγάπησαν",
        "dependent": "αγαπήσω, αγαπήσεις, αγαπήσει, αγαπήσουμε, αγαπήσετε, αγαπήσουν",
        "infinitive": "αγαπήσει",
        "imperative": "αγάπησε, αγαπήστε",
    },
    "μπορώ": {
        "present": "μπορώ, μπορείς, μπορεί, μπορούμε, μπορείτε, μπορούν",
        "imperfect": "μπορούσα, μπορούσες, μπορούσε, μπορούσαμε, μπορούσατε, μπορούσαν",
        "aorist": "μπόρεσα, μπόρεσες, μπόρεσε, μπορέσαμε, μπορέσατε, μπόρεσαν",
        "dependent": "μπορέσω, μπορέσεις, μπορέσει, μπορέσουμε, μπορέσετε, μπορέσουν",
        "infinitive": "μπορέσει",
    },
    "έρχομαι": {
        "present": "έρχομαι, έρχεσαι, έρχεται, ερχόμαστε, έρχεστε, έρχονται",
        "imperfect": "ερχόμουν|ερχόμουνα, ερχόσουν|ερχόσουνα, ερχόταν|ερχότανε, ερχόμασταν|ερχόμαστε, ερχόσασταν|ερχόσαστε, έρχονταν|έρχονταν",
        "aorist": "ήρθα, ήρθες, ήρθε, ήρθαμε, ήρθατε, ήρθαν",
        "dependent": "έρθω, έρθεις, έρθει, έρθουμε, έρθετε, έρθουν",
        "infinitive": "έρθει",
        "imperative": "έλα, ελάτε",
    },
    # έχω and είμαι have no aorist: their futures and subjunctive use the present
    "έχω": {
        "present": GR_ECHO,
        "imperfect": GR_EICHA,
        "dependent": GR_ECHO,
        "imperative": "έχε, έχετε",
    },
    "είμαι": {
        "present": "είμαι, είσαι, είναι, είμαστε, είστε|είσαστε, είναι",
        "imperfect": "ήμουν|ήμουνα, ήσουν|ήσουνα, ήταν|ήτανε, ήμασταν|ήμαστε, ήσασταν|ήσαστε, ήταν|ήτανε",
        "dependent": "είμαι, είσαι, είναι, είμαστε, είστε|είσαστε, είναι",
    },
}


def with_prefix(prefix, forms):
    return {person: [f"{prefix} {form}" for form in options] for person, options in forms.items()}


def with_greek_infinitive(aux_forms, infinitive):
    return {person: [f"{aux} {infinitive}" for aux in options] for person, options in aux_forms.items()}


def build_greek():
    result = {}
    for verb, data in GR_VERBS.items():
        present = table(GR_PERSONS, data["present"])
        dependent = table(GR_PERSONS, data["dependent"])
        forms = {
            "enestotas": present,
            "paratatikos": table(GR_PERSONS, data["imperfect"]),
            "mellontas_exakolouthitikos": with_prefix("θα", present),
            "mellontas_stigmiaios": with_prefix("θα", dependent),
            "ypotaktiki": with_prefix("να", dependent),
        }
        if "aorist" in data:
            forms["aoristos"] = table(GR_PERSONS, data["aorist"])
        if "infinitive" in data:
            forms["parakeimenos"] = with_greek_infinitive(table(GR_PERSONS, GR_ECHO), data["infinitive"])
            forms["ypersyntelikos"] = with_greek_infinitive(table(GR_PERSONS, GR_EICHA), data["infinitive"])
        if "imperative" in data:
            forms["prostaktiki"] = table(GR_IMPERATIVE_PERSONS, data["imperative"])
        result[verb] = forms
    return result


def main():
    for language, build in (
        ("italian", build_italian),
        ("spanish", build_spanish),
        ("german", build_german),
        ("greek", build_greek),
    ):
        path = os.path.join(ROOT, "data", language, "conjugations.json")
        with open(path, "w", encoding="utf-8") as json_file:
            json.dump(build(), json_file, ensure_ascii=False, indent=1)
        print("wrote", path)


if __name__ == "__main__":
    main()
