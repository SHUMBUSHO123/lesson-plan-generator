"""
lessons/helpers.py
==================
Single-page lesson plan context builder (CBC-Complete Edition).

One call → one lesson × one strategy × exactly 3 steps = one printable page.

Exported functions:
  prepare_lesson_plan_context()   – legacy helper (unchanged)
  build_lesson_plan_context()     – SINGLE-PAGE builder (updated)

Language support:
  Pass 'language' in request_data to get fully translated fallback text.
  Supported: 'en' (default), 'rw' (Kinyarwanda), 'sw' (Kiswahili), 'fr' (French)
  DB content (from seeders) is already in the correct language — these
  fallbacks only fire when no seeded steps exist for a lesson yet.
"""

import random
from django.shortcuts import get_object_or_404
from .models import Lesson, Unit, UserProfile, TeachingStrategy, LessonStrategyStep
from datetime import date


VALID_LANGUAGES = {'en', 'rw', 'sw', 'fr'}


def _get_lang(request_data):
    """Read language from request_data. Defaults to 'en' if missing or invalid."""
    lang = request_data.get('language', 'en')
    return lang if lang in VALID_LANGUAGES else 'en'


# ─────────────────────────────────────────────────────────────────────────────
# DYNAMIC INSTRUCTIONAL OBJECTIVE TEMPLATES
# One set per language — used ONLY when no seeded step exists.
# ─────────────────────────────────────────────────────────────────────────────

OBJECTIVE_TEMPLATES = {

    'en': [
        (
            "By using concrete and semi-concrete materials, learners will be able to "
            "demonstrate understanding of {title}, achieving a minimum accuracy of 80% "
            "in both practical and written tasks."
        ),
        (
            "Given guided practice and peer discussion, learners will accurately "
            "explain, apply, and evaluate key concepts of {title}, "
            "scoring at least 4 out of 5 on formative assessment tasks."
        ),
        (
            "Learners (A) will be able to analyse and solve problems related to {title} (B), "
            "using classroom resources and teacher-guided worked examples (C), "
            "with a minimum success rate of 80% on assessed tasks (D)."
        ),
        (
            "Through collaborative inquiry and teacher-facilitated activities, "
            "learners will construct, communicate, and justify their understanding of {title}, "
            "demonstrating mastery in both written responses and oral presentations."
        ),
        (
            "By the end of this lesson, all learners — including those with special "
            "educational needs — will be able to identify, describe, and apply "
            "the core concepts of {title} using appropriately differentiated "
            "support materials and strategies."
        ),
    ],

    'rw': [
        (
            "Hakoreshejwe ibikoresho biteye amanga, abanyeshuri bazashobora "
            "kwerekana ko basobanukiwe {title}, bagera ku kwinshi kwa 80% "
            "mu bikorwa byose by'amategeko no gukorora."
        ),
        (
            "Binyuze mu gukorana no guterana ibitekerezo, abanyeshuri bazashobora "
            "gusobanura, gukoresha no gusuzuma ibintu by'ingenzi bya {title}, "
            "bagera nibura ku manota 4 kuri 5 mu isuzuma."
        ),
        (
            "Abanyeshuri (A) bazashobora gusesengura no gukemura ibibazo bijyanye na {title} (B), "
            "bakoresheje ibikoresho byo mu ishuri n'ingero ziherekejwe n'umwarimu (C), "
            "bagera ku kwinshi kwa 80% mu bikorwa byasuzumwe (D)."
        ),
        (
            "Binyuze mu bushakashatsi bwo gukorana n'ibikorwa biherekejwe n'umwarimu, "
            "abanyeshuri bazubaka, gutangaza no gusobanura ibyumvikana bya {title}, "
            "berekana ubunararibonye mu gisubizo cyanditse no gutanga ikiganiro."
        ),
        (
            "Parigihembwe cy'isomo, abanyeshuri bose — harimo n'abafite ubumuga bw'icyumweru — "
            "bazashobora kumenya, gusobanura no gukoresha ibintu by'ingenzi bya {title} "
            "bakoresheje ibikoresho bihuye n'ubushobozi bwabo."
        ),
    ],

    'sw': [
        (
            "Kwa kutumia vifaa vya kugusika na nusu-kugusika, wanafunzi wataweza "
            "kuonyesha uelewa wa {title}, wakifikia usahihi wa chini ya 80% "
            "katika kazi za vitendo na maandishi."
        ),
        (
            "Kupitia mazoezi ya kuelekeza na majadiliano ya wenzao, wanafunzi wataweza "
            "kueleza kwa usahihi, kutumia na kutathmini dhana kuu za {title}, "
            "wakipata angalau alama 4 kati ya 5 katika tathmini."
        ),
        (
            "Wanafunzi (A) wataweza kuchambua na kutatua matatizo yanayohusiana na {title} (B), "
            "wakitumia rasilimali za darasa na mifano iliyoongozwa na mwalimu (C), "
            "wakifikia kiwango cha chini cha mafanikio cha 80% (D)."
        ),
        (
            "Kupitia uchunguzi wa ushirikiano na shughuli zinazoongozwa na mwalimu, "
            "wanafunzi wataunda, kuwasiliana na kuhalalisha uelewa wao wa {title}, "
            "wakionyesha ustadi katika majibu ya maandishi na uwasilishaji wa mdomo."
        ),
        (
            "Mwishoni mwa somo hili, wanafunzi wote — wakiwemo wenye mahitaji maalum — "
            "wataweza kutambua, kuelezea na kutumia dhana kuu za {title} "
            "wakitumia vifaa na mikakati inayofaa."
        ),
    ],

    'fr': [
        (
            "En utilisant des matériaux concrets et semi-concrets, les apprenants seront "
            "capables de démontrer leur compréhension de {title}, atteignant une précision "
            "minimale de 80% dans les tâches pratiques et écrites."
        ),
        (
            "Grâce à la pratique guidée et à la discussion entre pairs, les apprenants "
            "pourront expliquer, appliquer et évaluer avec précision les concepts clés de {title}, "
            "obtenant au moins 4 sur 5 aux évaluations formatives."
        ),
        (
            "Les apprenants (A) seront capables d'analyser et de résoudre des problèmes "
            "liés à {title} (B), en utilisant les ressources de la classe et des exemples "
            "guidés par l'enseignant (C), avec un taux de réussite minimum de 80% (D)."
        ),
        (
            "À travers une enquête collaborative et des activités facilitées par l'enseignant, "
            "les apprenants construiront, communiqueront et justifieront leur compréhension "
            "de {title}, démontrant leur maîtrise dans les réponses écrites et orales."
        ),
        (
            "À la fin de cette leçon, tous les apprenants — y compris ceux ayant des besoins "
            "éducatifs spéciaux — seront capables d'identifier, de décrire et d'appliquer "
            "les concepts fondamentaux de {title} à l'aide de supports différenciés."
        ),
    ],
}


# ─────────────────────────────────────────────────────────────────────────────
# TEACHER SELF-EVALUATION OPTIONS
# ─────────────────────────────────────────────────────────────────────────────

SELF_EVALUATION_OPTIONS = {

    'en': [
        "Lesson objective fully achieved — learners demonstrated mastery.",
        "Lesson objective partially achieved — some learners need follow-up support.",
        "Lesson needs to be repeated — majority of learners did not meet the objective.",
        "Lesson pace adjusted — content will continue in the next lesson.",
    ],

    'rw': [
        "Intego y'isomo yagezweho rwose — abanyeshuri berekeje ubunararibonye.",
        "Intego y'isomo yagezweho agace — abanyeshuri bamwe bakeneye inkunga yongeyeho.",
        "Isomo rigomba gusubirwamo — abanyeshuri benshi ntibageze ku ntego.",
        "Igihe cy'isomo cyahinditswe — ibizomara mu isomo rikurikira.",
    ],

    'sw': [
        "Lengo la somo limetimizwa kikamilifu — wanafunzi wameonyesha ustadi.",
        "Lengo la somo limetimizwa kwa sehemu — wanafunzi wengine wanahitaji msaada zaidi.",
        "Somo linahitaji kurudiwa — wengi wa wanafunzi hawakufikia lengo.",
        "Kasi ya somo ilirekebishwa — maudhui yataendelea katika somo lijalo.",
    ],

    'fr': [
        "Objectif de la leçon pleinement atteint — les apprenants ont démontré leur maîtrise.",
        "Objectif partiellement atteint — certains apprenants nécessitent un soutien supplémentaire.",
        "La leçon doit être répétée — la majorité des apprenants n'a pas atteint l'objectif.",
        "Le rythme de la leçon a été ajusté — le contenu se poursuivra lors de la prochaine leçon.",
    ],
}


# ─────────────────────────────────────────────────────────────────────────────
# SPECIAL NEEDS FALLBACK
# ─────────────────────────────────────────────────────────────────────────────

SPECIAL_NEEDS_FALLBACK = {
    'en': "No specific special educational needs identified in this class.",
    'rw': "Nta makuru yihariye y'ubumenyi bwihariye y'inyigisho yavuzwe mu ishuri ryawe.",
    'sw': "Hakuna mahitaji maalum ya elimu yaliyotambuliwa katika darasa hili.",
    'fr': "Aucun besoin éducatif spécial spécifique identifié dans cette classe.",
}

# ─────────────────────────────────────────────────────────────────────────────
# LOCATION FALLBACK
# ─────────────────────────────────────────────────────────────────────────────
LOCATION_FALLBACK = {
    'en': "Inside classroom",
    'rw': "Mu ishuri",
    'sw': "Ndani ya darasa",
    'fr': "Dans la salle de classe",
}

# ─────────────────────────────────────────────────────────────────────────────
# MATERIALS FALLBACK
# ─────────────────────────────────────────────────────────────────────────────
MATERIALS_FALLBACK = {
    'en': "Textbook, Chalkboard",
    'rw': "Igitabo cy'umunyeshuri, Ikirahuri",
    'sw': "Kitabu cha kiada, Ubao wa chaki",
    'fr': "Manuel scolaire, Tableau noir",
}

# ─────────────────────────────────────────────────────────────────────────────
# REFERENCES FALLBACK
# ─────────────────────────────────────────────────────────────────────────────
REFERENCES_FALLBACK = {
    'en': "No references provided",
    'rw': "Nta myandiko yifashishijwe yatanzwe",
    'sw': "Hakuna marejeo yaliyotolewa",
    'fr': "Aucune référence fournie",
}

# ─────────────────────────────────────────────────────────────────────────────
# MATERIALS LABEL
# ─────────────────────────────────────────────────────────────────────────────
MATERIALS_LABEL = {
    'en': "Learning Materials",
    'rw': "Imfashanyigisho",
    'sw': "Vifaa vya Kujifunza",
    'fr': "Matériel Pédagogique",
}

# ─────────────────────────────────────────────────────────────────────────────
# REFERENCES LABEL
# ─────────────────────────────────────────────────────────────────────────────
REFERENCES_LABEL = {
    'en': "References",
    'rw': "Imyandiko n'ibitabo byifashishijwe",
    'sw': "Marejeo",
    'fr': "Références",
}


# ─────────────────────────────────────────────────────────────────────────────
# LOCATION TRANSLATION
# ─────────────────────────────────────────────────────────────────────────────
LOCATION_TRANSLATION = {
    'en': {
        'Inside classroom':    'Inside classroom',
        'Outside classroom':   'Outside classroom',
        'Computer laboratory': 'Computer laboratory',
        'Field work':          'Field work',
        'Library':             'Library',
    },
    'rw': {
        'Inside classroom':    'Mu ishuri',
        'Outside classroom':   "Hanze y'ishuri",
        'Computer laboratory': 'Labo ya mudasobwa',
        'Field work':          'Gukorera hanze',
        'Library':             'Bibliotheque',
    },
    'sw': {
        'Inside classroom':    'Ndani ya darasa',
        'Outside classroom':   'Nje ya darasa',
        'Computer laboratory': 'Maabara ya kompyuta',
        'Field work':          'Kazi ya shambani',
        'Library':             'Maktaba',
    },
    'fr': {
        'Inside classroom':    'Dans la salle de classe',
        'Outside classroom':   'En dehors de la salle de classe',
        'Computer laboratory': 'Laboratoire informatique',
        'Field work':          'Travail sur le terrain',
        'Library':             'Bibliothèque',
    },
}


# ─────────────────────────────────────────────────────────────────────────────
# MATERIALS ITEM TRANSLATION
# ─────────────────────────────────────────────────────────────────────────────
MATERIALS_ITEM_TRANSLATION = {
    'en': {
        'Textbook':             'Textbook',
        'Chalkboard':           'Chalkboard',
        'Projector':            'Projector',
        'Computer':             'Computer',
        'Charts':               'Charts',
        'Laboratory equipment': 'Laboratory equipment',
        'IDE software':         'IDE software',
        'Microscope':           'Microscope',
        'Specimens':            'Specimens',
        'Chemicals':            'Chemicals',
        'Safety equipment':     'Safety equipment',
        'Measuring instruments':'Measuring instruments',
    },
    'rw': {
        'Textbook':             "Igitabo cy'umunyeshuri",
        'Chalkboard':           'Ikirahuri',
        'Projector':            'Projekiteri',
        'Computer':             'Mudasobwa',
        'Charts':               'Amashusho',
        'Laboratory equipment': 'Ibikoresho bya labo',
        'IDE software':         'Porogaramu ya IDE',
        'Microscope':           'Microscope',
        'Specimens':            'Ingero',
        'Chemicals':            'Ibintu bya chimie',
        'Safety equipment':     "Ibikoresho by'umutekano",
        'Measuring instruments':'Ibikoresho byo gupima',
    },
    'sw': {
        'Textbook':             'Kitabu cha kiada',
        'Chalkboard':           'Ubao wa chaki',
        'Projector':            'Projekta',
        'Computer':             'Kompyuta',
        'Charts':               'Chati',
        'Laboratory equipment': 'Vifaa vya maabara',
        'IDE software':         'Programu ya IDE',
        'Microscope':           'Darubini',
        'Specimens':            'Sampuli',
        'Chemicals':            'Kemikali',
        'Safety equipment':     'Vifaa vya usalama',
        'Measuring instruments':'Vifaa vya kupimia',
    },
    'fr': {
        'Textbook':             'Manuel scolaire',
        'Chalkboard':           'Tableau noir',
        'Projector':            'Projecteur',
        'Computer':             'Ordinateur',
        'Charts':               'Tableaux/Graphiques',
        'Laboratory equipment': 'Équipement de laboratoire',
        'IDE software':         'Logiciel IDE',
        'Microscope':           'Microscope',
        'Specimens':            'Échantillons',
        'Chemicals':            'Produits chimiques',
        'Safety equipment':     'Équipement de sécurité',
        'Measuring instruments':'Instruments de mesure',
    },
}


def _translate_location(value, lang):
    """Translate an English location value to the target language."""
    if not value:
        return LOCATION_FALLBACK.get(lang, LOCATION_FALLBACK['en'])
    table = LOCATION_TRANSLATION.get(lang, LOCATION_TRANSLATION['en'])
    return table.get(value.strip(), value)


def _translate_materials(value, lang):
    """
    Translate a comma-separated English materials string to the target language.
    e.g. "Textbook, Chalkboard" → "Igitabo cy'umunyeshuri, Ikirahuri"
    """
    if not value:
        return MATERIALS_FALLBACK.get(lang, MATERIALS_FALLBACK['en'])
    table  = MATERIALS_ITEM_TRANSLATION.get(lang, MATERIALS_ITEM_TRANSLATION['en'])
    items  = [v.strip() for v in value.split(',') if v.strip()]
    result = [table.get(item, item) for item in items]
    return ', '.join(result)


# ─────────────────────────────────────────────────────────────────────────────
# FALLBACK STEPS TEXT
# ─────────────────────────────────────────────────────────────────────────────

FALLBACK_STEPS = {

    'en': {
        'lesson_description': "This lesson explores {title} through guided practice and collaborative learning.",
        'steps': [
            {
                'step_title':             "Introduction",
                'teacher_activity':       "Introduce the lesson objectives for {title} and activate prior knowledge through structured questioning.",
                'learner_activity':       "Listen attentively, respond to questions, and share prior knowledge.",
                'competence':             "Communication and Critical Thinking",
                'competence_integration': (
                    "Communication is developed as learners articulate prior knowledge "
                    "through teacher-led questioning. Critical thinking is activated as "
                    "learners connect new topics to existing knowledge."
                ),
            },
            {
                'step_title':             "Development",
                'teacher_activity':       "Guide learners through key concepts and activities on {title}. Facilitate peer discussion and provide formative feedback.",
                'learner_activity':       "Participate in guided activities, discuss with peers, and apply concepts to practice tasks.",
                'competence':             "Critical Thinking, Problem-Solving, and Collaboration",
                'competence_integration': (
                    "Critical thinking deepens as learners analyse and break down concepts. "
                    "Problem-solving is practised through structured application exercises. "
                    "Collaboration is fostered as learners work in pairs or groups."
                ),
            },
            {
                'step_title':             "Conclusion",
                'teacher_activity':       "Summarise key points about {title}, reinforce the unit competence, and assign a brief reflection or homework task.",
                'learner_activity':       "Reflect on learning, ask remaining questions, and record homework in exercise books.",
                'competence':             "Self-Regulation and Communication",
                'competence_integration': (
                    "Self-regulation is practised as learners reflect on what they have understood. "
                    "Communication is reinforced as learners articulate key takeaways in their own words."
                ),
            },
        ],
    },

    'rw': {
        'lesson_description': "Iri somo risesengura {title} binyuze mu gukorana n'imyitozo yoborwa.",
        'steps': [
            {
                'step_title':             "Intangiriro",
                'teacher_activity':       "Tangaza intego z'isomo rya {title} kandi ushire imbere ubumenyi bw'ibanze binyuze mu bibazo bifatika.",
                'learner_activity':       "Umviriza neza, subiza ibibazo, usangire ubumenyi bw'ibanze.",
                'competence':             "Gutumanahana no Gutekereza neza",
                'competence_integration': (
                    "Gutumanahana gushyirwaho ubushobozi bwo kuvuga ibitekerezo binyuze mu bibazo by'umwarimu. "
                    "Gutekereza neza biragaragazwa iyo abanyeshuri bashamikiye ibintu bishya ku bumenyi bafite."
                ),
            },
            {
                'step_title':             "Iterambere",
                'teacher_activity':       "Popoza abanyeshuri mu nzira z'ingenzi n'ibikorwa bya {title}. Shyiraho ibiganiro hagati y'abanyeshuri utange ibitekerezo.",
                'learner_activity':       "Fata uruhare mu bikorwa byoborwa, ganira n'inshuti, ukore imirimo y'inyigisho.",
                'competence':             "Gutekereza neza, Gukemura Ibibazo no Gukorana",
                'competence_integration': (
                    "Gutekereza neza birashamira iyo abanyeshuri basesengura ibitekerezo. "
                    "Gukemura ibibazo bikorwa binyuze mu bikorwa bifatika. "
                    "Gukorana bikomezwa iyo abanyeshuri bakorana mu matsinda."
                ),
            },
            {
                'step_title':             "Isoza",
                'teacher_activity':       "Sobanura ingingo z'ingenzi za {title}, komeza ubushobozi bw'inturuka kandi usabe akazi gato k'isubiramwo cyangwa akazi k'imuhira.",
                'learner_activity':       "Subiramo inyigisho, baza ibibazo bisigaye, andika akazi k'imuhira mu ibitabo by'imyitozo.",
                'competence':             "Kwigenzura no Gutumanahana",
                'competence_integration': (
                    "Kwigenzura bikorwa iyo abanyeshuri basuzumanya ibyo bashoboye gusobanukirwa. "
                    "Gutumanahana bikomezwa iyo abanyeshuri bavuga ibyo bize mu magambo yabo bwite."
                ),
            },
        ],
    },

    'sw': {
        'lesson_description': "Somo hili linachunguza {title} kupitia mazoezi ya kuelekeza na kujifunza kwa ushirikiano.",
        'steps': [
            {
                'step_title':             "Utangulizi",
                'teacher_activity':       "Wasilisha malengo ya somo la {title} na uamsha maarifa ya awali kupitia maswali yaliyopangwa.",
                'learner_activity':       "Sikiliza kwa makini, jibu maswali, na shiriki maarifa ya awali.",
                'competence':             "Mawasiliano na Fikira Makini",
                'competence_integration': (
                    "Mawasiliano yanakuzwa wanafunzi wanapoeleza maarifa ya awali kupitia maswali ya mwalimu. "
                    "Fikira makini inaamshwa wanafunzi wanaounganisha mada mpya na maarifa waliyonayo."
                ),
            },
            {
                'step_title':             "Maendeleo",
                'teacher_activity':       "Ongoza wanafunzi kupitia dhana kuu na shughuli za {title}. Wezesha majadiliano ya wenzao na toa maoni ya tathmini.",
                'learner_activity':       "Shiriki katika shughuli zinazoongozwa, jadili na wenzako, na tumia dhana katika kazi za mazoezi.",
                'competence':             "Fikira Makini, Kutatua Matatizo na Ushirikiano",
                'competence_integration': (
                    "Fikira makini inakua wanafunzi wanapochanganua dhana. "
                    "Kutatua matatizo kunafanyiwa mazoezi kupitia mazoezi ya vitendo. "
                    "Ushirikiano unakuzwa wanafunzi wanafanya kazi kwa jozi au makundi."
                ),
            },
            {
                'step_title':             "Hitimisho",
                'teacher_activity':       "Fupisha pointi kuu za {title}, imarisha uwezo wa kitengo, na upe kazi fupi ya kutafakari au kazi ya nyumbani.",
                'learner_activity':       "Tafakari juu ya kujifunza, uliza maswali yaliyobaki, na andika kazi ya nyumbani katika vitabu vya mazoezi.",
                'competence':             "Kujidhibiti na Mawasiliano",
                'competence_integration': (
                    "Kujidhibiti kunafanyiwa mazoezi wanafunzi wanapotafakari wanachokielewa. "
                    "Mawasiliano yanaimarishwa wanafunzi wanapoeleza mambo waliyojifunza kwa maneno yao wenyewe."
                ),
            },
        ],
    },

    'fr': {
        'lesson_description': "Cette leçon explore {title} à travers une pratique guidée et un apprentissage collaboratif.",
        'steps': [
            {
                'step_title':             "Introduction",
                'teacher_activity':       "Présenter les objectifs de la leçon sur {title} et activer les connaissances antérieures par des questions structurées.",
                'learner_activity':       "Écouter attentivement, répondre aux questions et partager les connaissances antérieures.",
                'competence':             "Communication et Pensée Critique",
                'competence_integration': (
                    "La communication est développée lorsque les apprenants articulent leurs connaissances antérieures. "
                    "La pensée critique est activée lorsque les apprenants relient les nouveaux sujets aux connaissances existantes."
                ),
            },
            {
                'step_title':             "Développement",
                'teacher_activity':       "Guider les apprenants à travers les concepts clés et les activités sur {title}. Faciliter la discussion entre pairs et fournir des retours formatifs.",
                'learner_activity':       "Participer aux activités guidées, discuter avec les pairs et appliquer les concepts aux tâches pratiques.",
                'competence':             "Pensée Critique, Résolution de Problèmes et Collaboration",
                'competence_integration': (
                    "La pensée critique s'approfondit lorsque les apprenants analysent les concepts. "
                    "La résolution de problèmes est pratiquée à travers des exercices d'application structurés. "
                    "La collaboration est encouragée lorsque les apprenants travaillent en binômes ou en groupes."
                ),
            },
            {
                'step_title':             "Conclusion",
                'teacher_activity':       "Résumer les points clés de {title}, renforcer la compétence de l'unité et assigner une brève tâche de réflexion ou des devoirs.",
                'learner_activity':       "Réfléchir sur les apprentissages, poser les questions restantes et noter les devoirs dans les cahiers d'exercices.",
                'competence':             "Auto-Régulation et Communication",
                'competence_integration': (
                    "L'auto-régulation est pratiquée lorsque les apprenants réfléchissent à ce qu'ils ont compris. "
                    "La communication est renforcée lorsque les apprenants articulent les points clés avec leurs propres mots."
                ),
            },
        ],
    },
}


# ─────────────────────────────────────────────────────────────────────────────
# LEGACY HELPER (unchanged)
# ─────────────────────────────────────────────────────────────────────────────

def prepare_lesson_plan_context(lesson_id, form_data, user=None, device_id=None):
    """
    Prepare all context needed for rendering a lesson plan table.
    Handles default location/materials and multi-select materials.
    """

    if user:
        profile = get_object_or_404(UserProfile, user=user)
    else:
        profile, _ = UserProfile.objects.get_or_create(device_id=device_id)

    if not profile.can_generate_plan():
        raise PermissionError(
            f"Free Lessons Limit Reached (Only {profile.get_current_lesson_limit()} Allowed)"
        )

    lesson = get_object_or_404(Lesson, pk=lesson_id)
    unit = lesson.unit
    subject_name = unit.subject.name if unit.subject else "N/A"

    if subject_name == "Computer Science":
        default_materials = ["Computer", "Projector", "IDE software"]
        default_location = "Computer laboratory"
    elif subject_name == "Biology":
        default_materials = ["Charts", "Microscope", "Specimens"]
        default_location = "Laboratory"
    elif subject_name == "Chemistry":
        default_materials = ["Laboratory apparatus", "Chemicals", "Safety equipment"]
        default_location = "Laboratory"
    elif subject_name == "Physics":
        default_materials = ["Laboratory equipment", "Measuring instruments"]
        default_location = "Laboratory"
    else:
        default_materials = ["Textbook", "Chalkboard"]
        default_location = "Inside classroom"

    location_plan = form_data.get("location_plan") or default_location

    if hasattr(form_data, "getlist"):
        materials_list = form_data.getlist("materials")
    else:
        materials_list = form_data.get("materials")
        if isinstance(materials_list, str):
            materials_list = [m.strip() for m in materials_list.split(",") if m.strip()]
        elif not isinstance(materials_list, list):
            materials_list = []

    lang_for_legacy = form_data.get('language', 'en') if hasattr(form_data, 'get') else 'en'
    if not lang_for_legacy or lang_for_legacy not in VALID_LANGUAGES:
        lang_for_legacy = 'en'
    raw_materials   = ", ".join(materials_list) if materials_list else ", ".join(default_materials)
    materials       = _translate_materials(raw_materials, lang_for_legacy)
    location_plan   = _translate_location(location_plan, lang_for_legacy)

    context = {
        'lesson_info': {
            'term': form_data.get('term', ''),
            'date': form_data.get('date', ''),
            'subject': subject_name,
            'class_name': unit.subject.class_field.name if unit.subject and hasattr(unit.subject, "class_field") else "",
            'location_plan': location_plan,
            'materials': materials,
            'references': form_data.get('references', ''),
            'self_evaluation': form_data.get('self_evaluation', ''),
            'class_size': form_data.get('class_size', ''),
        },
        'unit_info': {
            'unit_number': unit.number,
            'unit_title': unit.title,
            'total_lessons': getattr(unit, "total_lessons", 1),
            'key_unit_competence': getattr(unit, "key_unit_competence", f"Understand {lesson.title}"),
        },
        'lesson_number': lesson.number,
        'lesson_duration': form_data.get('duration', 40),
        'special_needs': form_data.get('special_needs', 'None'),
        'steps': lesson.strategy_steps.all().order_by('step_order'),
    }

    return context


# ─────────────────────────────────────────────────────────────────────────────
# SINGLE-PAGE LESSON PLAN CONTEXT BUILDER (CBC-Complete)
# ─────────────────────────────────────────────────────────────────────────────

def build_lesson_plan_context(request_data, profile):
    """
    Build a SINGLE-PAGE lesson plan context for one lesson × one strategy.

    Language is read from request_data['language'] (default 'en').
    All fallback text (objectives, self-evaluation, step activities)
    is returned in the selected language.
    DB content from seeders is already in the correct language — fallbacks
    only fire when no seeded steps exist for a lesson yet.
    """

    # ── 0. Language ───────────────────────────────────────────────────────────
    lang      = _get_lang(request_data)
    fallback  = FALLBACK_STEPS[lang]
    obj_tmpl  = OBJECTIVE_TEMPLATES[lang]
    eval_opts = SELF_EVALUATION_OPTIONS[lang]

    # ── 1. Resolve Lesson & Unit ──────────────────────────────────────────────
    lesson_id = request_data.get("lesson_id")

    if not lesson_id:
        raise ValueError("lesson_id is required to build a single-page lesson plan.")

    lesson = get_object_or_404(Lesson, id=lesson_id)
    unit   = lesson.unit

    # ── 2. Resolve Teaching Strategy ─────────────────────────────────────────
    strategy_input    = request_data.get("strategy")
    selected_strategy = None

    if strategy_input:
        if str(strategy_input).isdigit():
            selected_strategy = TeachingStrategy.objects.filter(
                id=strategy_input, is_active=True
            ).first()
        else:
            selected_strategy = TeachingStrategy.objects.filter(
                name__iexact=strategy_input, is_active=True
            ).first()

    if not selected_strategy:
        selected_strategy = (
            TeachingStrategy.objects
            .filter(is_active=True, is_premium_only=False)
            .order_by("id")
            .first()
        )

    if not selected_strategy:
        raise ValueError("No active teaching strategy found in the database.")

    if selected_strategy.is_premium_only and not profile.is_subscription_active():
        raise PermissionError(
            "The selected strategy is available to premium subscribers only."
        )

    # ── 3. lesson_info ────────────────────────────────────────────────────────
    subject_name = unit.subject.name if unit and unit.subject else "N/A"

    db_class_name = (
        unit.subject.class_field.name
        if unit and unit.subject and hasattr(unit.subject, "class_field")
        else None
    )
    class_name = (
        request_data.get("class")
        or db_class_name
        or "N/A"
    )

    # ── BUG FIX 1a: references — form input ALWAYS wins over DB/profile.
    # Old code: request_data.get("references") or lesson.references or profile.references or FALLBACK
    # Problem:  if lesson.references had any DB value it silently overrode
    #           the teacher's checkbox/free-text selections from the form.
    # Fix:      strip the form value; only fall back to DB/profile when the
    #           form sent nothing at all (empty string or missing key).
    form_references = (request_data.get("references") or "").strip()
    resolved_references = (
        form_references                              # 1st: what teacher typed/checked
        or getattr(lesson, "references", "") or ""   # 2nd: DB lesson default (if any)
        or getattr(profile, "references", "") or ""  # 3rd: profile default
        or REFERENCES_FALLBACK[lang]                 # 4th: language fallback
    )

    # ── BUG FIX 1b: special_needs — same priority fix.
    # The top-level context key 'special_needs' (step 6 below) already reads
    # request_data first and is correct. This lesson_info key was never used
    # by the template — keeping it consistent and correct anyway.
    form_special_needs = (request_data.get("special_needs") or "").strip()

    lesson_info = {
        "school_name":     request_data.get("school_name")    or profile.school_name   or "N/A",
        "teacher_name":    request_data.get("teacher_name")   or profile.teacher_name  or "N/A",
        "term":            request_data.get("term")            or profile.default_term  or "N/A",
        "class_size":      request_data.get("class_size")      or profile.class_size    or 0,

        # FIX 1a applied — form references always take priority
        "references":      resolved_references,

        # FIX: honour teacher's lesson title override from the form.
        # request_data["lesson_title"] is the display label saved by
        # saveInlineEdit(); falls back to DB lesson.title only if not sent.
        "lesson_title":    (request_data.get("lesson_title") or "").strip() or lesson.title,

        "class_name":      class_name,
        "level":           request_data.get("level", "N/A"),
        "subject":         subject_name,
        "date":            request_data.get("date") or str(date.today()),
        "strategy":        selected_strategy.name,
        "location_plan":   _translate_location(
                               request_data.get("location_plan"), lang
                           ),
        "materials":       _translate_materials(
                               request_data.get("materials"), lang
                           ),
        "self_evaluation": request_data.get("self_evaluation") or "",
        "language":        lang,
    }

    # ── 4. unit_info ──────────────────────────────────────────────────────────
    unit_info = {
        "unit_number":         unit.number,
        "unit_title":          request_data.get("unit_title") or unit.title,
        "key_unit_competence": getattr(unit, "key_unit_competence", f"Understand {lesson.title}"),
        "total_lessons":       unit.lessons.count() if hasattr(unit, "lessons") else 1,
        "unit_number_display": (
            request_data.get("unit_number_display") or f"Unit {unit.number}"
        ),
    }

    # ── 5. Steps — exactly 3 for one page ────────────────────────────────────
    steps                   = []
    lesson_description      = None
    instructional_objective = None
    title                   = lesson.title

    db_steps = (
        LessonStrategyStep.objects
        .filter(lesson=lesson, strategy=selected_strategy)
        .order_by("step_order")[:3]
    )

    if db_steps.exists():
        for step in db_steps:
            if step.step_order == 1:
                lesson_description = (
                    step.lesson_description
                    or fallback['lesson_description'].format(title=title)
                )
                instructional_objective = (
                    step.instructional_objective
                    or random.choice(obj_tmpl).format(title=title)
                )

            steps.append({
                "title":                  f"{step.step_order}: {step.step_title}",
                "duration_minutes":       step.duration_minutes,
                "teacher_activity":       step.teacher_activity,
                "learner_activity":       step.learner_activity,
                "competence":             step.generic_competence or "Communication",
                "competence_integration": (
                    step.competence_integration
                    or f"{step.generic_competence} is developed through active engagement in this step."
                ),
            })

    else:
        dur     = int(request_data.get("duration", 40))
        intro_d = round(dur * 0.20)
        dev_d   = round(dur * 0.60)
        conc_d  = dur - intro_d - dev_d
        durations = [intro_d, dev_d, conc_d]

        lesson_description      = fallback['lesson_description'].format(title=title)
        instructional_objective = random.choice(obj_tmpl).format(title=title)

        for i, step_tmpl in enumerate(fallback['steps']):
            steps.append({
                "title":                  f"{i + 1}: {step_tmpl['step_title']}",
                "duration_minutes":       durations[i],
                "teacher_activity":       step_tmpl['teacher_activity'].format(title=title),
                "learner_activity":       step_tmpl['learner_activity'],
                "competence":             step_tmpl['competence'],
                "competence_integration": step_tmpl['competence_integration'],
            })

    # ── 6. Page-level meta ────────────────────────────────────────────────────
    lesson_number   = request_data.get("lesson_no", lesson.number)
    lesson_duration = int(request_data.get("duration", 40))

    # BUG FIX 1b: special_needs — form value always wins.
    # Empty string from form → show language fallback (not the empty string).
    special_needs = form_special_needs or SPECIAL_NEEDS_FALLBACK[lang]

    # ── 7. Return single-page context ─────────────────────────────────────────
    return {
        "lesson_info":             lesson_info,
        "unit_info":               unit_info,
        "lesson_number":           lesson_number,
        "lesson_duration":         lesson_duration,
        "special_needs":           special_needs,
        "lesson_description":      lesson_description,
        "instructional_objective": instructional_objective,
        "steps":                   steps,
        "self_evaluation_options": eval_opts,
        "is_single_page":          True,
        "language":                lang,
        "materials_label":         MATERIALS_LABEL[lang],
        "references_label":        REFERENCES_LABEL[lang],
    }