"""
Management Command: seed_strategies_fr
=======================================
CBC Lesson Plan Generator — French Strategy Seeder
---------------------------------------------------
Seeds 3 strategies × 3 steps for every Lesson where language='fr'.
All step content is written in French.

Mirrors seed_strategies_per_lesson_skip.py exactly in structure.
SKIP-EXISTING: never overwrites already-seeded steps.

Strategies:
  1. Méthode de Discussion (Discussion Method)    — FREE
  2. Travail Collaboratif en Groupe (Group Work)  — FREE
  3. Apprentissage par Projets (Project-Based)    — PREMIUM

Usage:
  python manage.py seed_strategies_fr
  python manage.py seed_strategies_fr --clear
  python manage.py seed_strategies_fr --lesson_id 5
"""

from django.core.management.base import BaseCommand
from lessons.models import Lesson, TeachingStrategy, LessonStrategyStep


# ─────────────────────────────────────────────────────────────────────────────
# STRATEGIES
# ─────────────────────────────────────────────────────────────────────────────

STRATEGIES = [
    {
        "name": "Méthode de Discussion",
        "description": (
            "L'enseignant anime une discussion structurée en classe, activant "
            "les connaissances préalables et guidant les apprenants à construire "
            "la compréhension à travers le questionnement et l'interaction entre pairs."
        ),
        "is_premium_only": False,
        "is_active": True,
    },
    {
        "name": "Travail Collaboratif en Groupe",
        "description": (
            "Les apprenants travaillent en petits groupes pour investiguer, "
            "résoudre des problèmes et présenter leurs résultats. L'enseignant "
            "circule en tant que facilitateur, promouvant le travail d'équipe "
            "et les compétences de communication."
        ),
        "is_premium_only": False,
        "is_active": True,
    },
    {
        "name": "Apprentissage par Projets",
        "description": (
            "Stratégie premium. Les apprenants conçoivent et construisent des "
            "solutions réelles liées à la compétence de l'unité. L'enseignant "
            "encadre et évalue à travers l'observation et des sessions de "
            "rétroaction structurées."
        ),
        "is_premium_only": True,
        "is_active": True,
    },
]

EXPECTED_STEPS_PER_LESSON = len(STRATEGIES) * 3


# ─────────────────────────────────────────────────────────────────────────────
# DETERMINISTIC VARIANT SELECTOR
# ─────────────────────────────────────────────────────────────────────────────

def pick_variant(lesson_id, step_order, variants):
    index = (lesson_id * 7 + step_order * 3) % len(variants)
    return variants[index]


# ═════════════════════════════════════════════════════════════════════════════
# LESSON-LEVEL CONTENT GENERATORS
# ═════════════════════════════════════════════════════════════════════════════

LESSON_DESCRIPTION_VARIANTS = [
    "Cette leçon explore {title} à travers des exercices pratiques et des applications du monde réel.",
    "Les apprenants étudient {title} en utilisant l'investigation collaborative et la découverte guidée.",
    "Cette leçon développe la compréhension de {title} à travers des activités pratiques et l'interaction entre pairs.",
    "À travers la résolution de problèmes et la discussion, les apprenants maîtrisent les concepts clés de {title}.",
]

INSTRUCTIONAL_OBJ_VARIANTS = [
    "À la fin de cette leçon, les apprenants seront capables d'analyser et d'appliquer les concepts de {title} en atteignant une précision d'au moins 80% à travers des exercices guidés.",
    "À la fin de cette leçon, les apprenants auront démontré avec succès leur compréhension de {title} en résolvant correctement au moins 3 problèmes.",
    "Après cette leçon, les apprenants seront capables d'expliquer correctement {title} et de l'appliquer dans des situations réelles avec un raisonnement clair.",
    "À l'issue de cette leçon, les apprenants maîtriseront {title} comme en témoigne la réussite des tâches d'évaluation formative.",
]

CROSS_CUTTING_VARIANTS = [
    {
        "issues": "Éducation à la Paix et aux Valeurs, Culture de la Standardisation",
        "integration": "Éducation à la paix: Développée à travers l'interaction respectueuse entre pairs et la résolution collaborative de problèmes. Standardisation: Renforcée par l'utilisation précise de la terminologie et de la notation lors du travail sur {title}."
    },
    {
        "issues": "Éducation Inclusive, Éducation Financière",
        "integration": "Éducation inclusive: Tous les apprenants participent à travers des tâches différenciées et l'entraide. Éducation financière: Les concepts de {title} appliqués aux scénarios de budgétisation et de prise de décision financière."
    },
    {
        "issues": "Égalité des Genres, Environnement et Développement Durable",
        "integration": "Égalité des genres: La participation équitable est encouragée à travers des groupes mixtes et une attribution équilibrée des rôles. Durabilité: La leçon sur {title} est liée à la résolution des problèmes environnementaux et à la gestion des ressources."
    },
    {
        "issues": "Culture de la Standardisation, Éducation à la Sexualité Complète",
        "integration": "Standardisation: Soulignée par l'utilisation précise des conventions scientifiques/mathématiques dans {title}. Éducation à la sexualité complète: Intégrée à travers des discussions sur l'analyse des données de santé et la prise de décisions responsables."
    },
]

COMPETENCE_INTEGRATION_VARIANTS = {
    "intro": [
        "La communication est développée lorsque les apprenants articulent leurs connaissances préalables et posent des questions de clarification sur {title}. La pensée critique commence à travers l'analyse des objectifs de la leçon.",
        "Les apprenants s'exercent à la communication en partageant des idées initiales sur {title}. La pensée critique est activée à travers le questionnement et la connexion avec les leçons précédentes.",
        "La compétence de communication émerge à travers les discussions en binômes sur {title}. La pensée critique est engagée à travers l'identification des problèmes et la compréhension des objectifs.",
        "À travers un questionnement structuré sur {title}, les apprenants développent des compétences de communication. La pensée critique est favorisée par l'analyse des relations entre les concepts.",
    ],
    "development": [
        "La pensée critique s'approfondit lorsque les apprenants analysent les concepts de {title} et justifient leur raisonnement. La compétence de communication grandit à travers l'explication des solutions aux pairs. La collaboration est pratiquée à travers la résolution de problèmes en groupe.",
        "Les compétences de résolution de problèmes sont renforcées en travaillant méthodiquement sur {title}. La coopération se développe à travers les tâches de groupe. L'apprentissage tout au long de la vie est favorisé par l'investigation autonome.",
        "Les apprenants renforcent la pensée critique en évaluant différentes approches de {title}. La compétence de collaboration se développe à travers l'enquête collaborative. Les compétences de recherche sont pratiquées à travers la collecte d'informations.",
        "La créativité est encouragée à travers l'exploration de solutions multiples pour {title}. La collaboration se renforce à travers les retours des pairs. L'apprentissage autonome est promu à travers des exercices guidés.",
    ],
    "conclusion": [
        "L'auto-régulation est pratiquée lorsque les apprenants réfléchissent à leur compréhension de {title}. La compétence de communication est renforcée à travers le résumé des points clés d'apprentissage.",
        "L'apprentissage tout au long de la vie est favorisé par l'auto-évaluation de la maîtrise de {title}. La communication est renforcée en articulant les questions restantes et les connaissances acquises.",
        "Les apprenants développent l'auto-régulation en évaluant leurs progrès sur {title}. La pensée critique est consolidée à travers la réflexion sur les stratégies d'apprentissage utilisées.",
        "L'apprentissage autonome est promu lorsque les apprenants identifient les domaines d'étude complémentaire de {title}. La communication est pratiquée à travers l'enseignement entre pairs et l'explication.",
    ],
}


def generate_lesson_description(lesson):
    variant = pick_variant(lesson.id, 0, LESSON_DESCRIPTION_VARIANTS)
    return variant.format(title=lesson.title)


def generate_instructional_objective(lesson):
    variant = pick_variant(lesson.id, 0, INSTRUCTIONAL_OBJ_VARIANTS)
    return variant.format(title=lesson.title)


def generate_cross_cutting_issues(lesson):
    variant = pick_variant(lesson.id, 0, CROSS_CUTTING_VARIANTS)
    issues = variant["issues"]
    integration = variant["integration"].format(title=lesson.title)
    return f"{issues}\n\nIntégration: {integration}"


def generate_competence_integration(lesson, step_type):
    variants = COMPETENCE_INTEGRATION_VARIANTS.get(step_type, COMPETENCE_INTEGRATION_VARIANTS["intro"])
    variant = pick_variant(lesson.id, {"intro": 1, "development": 2, "conclusion": 3}.get(step_type, 1), variants)
    return variant.format(title=lesson.title)


# ─────────────────────────────────────────────────────────────────────────────
# VARIANT POOLS — FRENCH
# ─────────────────────────────────────────────────────────────────────────────

DISCUSSION_INTRO_TEACHER = [
    "Accueillir les apprenants et introduire le sujet: {title}. Poser des questions ouvertes pour activer les connaissances préalables sur {unit_title}. Énoncer l'objectif de la leçon aligné sur: {competence}.",
    "Commencer la leçon en révisant ce que les apprenants savent déjà sur {unit_title}. Relier les connaissances préalables à l'objectif d'aujourd'hui sur {title}. Indiquer clairement comment cette leçon contribue à: {competence}.",
    "Afficher un visuel ou poser une situation réelle liée à {title}. Demander aux apprenants ce qu'ils observent et comment cela se connecte à {unit_title}. Introduire l'objectif de la leçon lié à: {competence}.",
    "Commencer par une activité de réflexion-duo-partage sur {title}. Permettre aux apprenants de discuter de leurs idées initiales avant de partager avec la classe. Présenter comment cette leçon s'inscrit dans: {competence}.",
]

DISCUSSION_INTRO_LEARNER = [
    "Écouter attentivement et répondre aux questions de l'enseignant. Partager ce qu'ils savent déjà sur {title} et relier les idées des leçons précédentes.",
    "S'engager avec le visuel ou la situation présentée. Discuter des idées initiales avec un partenaire avant de contribuer à la discussion de classe sur {title}.",
    "Réfléchir aux leçons précédentes liées à {unit_title}. Poser des questions de clarification et se préparer à construire une nouvelle compréhension de {title}.",
    "Participer à l'activité de réflexion-duo-partage. Partager les observations et les connaissances préalables liées à {title} avec les pairs et l'enseignant.",
]

DISCUSSION_DEV_TEACHER = [
    "Animer une discussion structurée en classe entière et en binômes sur les concepts clés de {title}. Utiliser des questions de sondage pour approfondir la compréhension de {competence}. Écrire les points clés au tableau et guider les apprenants vers des conclusions.",
    "Présenter 2-3 questions directrices liées à {title}. Encourager les apprenants à discuter des réponses en petits groupes avant de partager avec la classe. Synthétiser les contributions et corriger les misconceptions liées à {competence}.",
    "Utiliser le questionnement socratique pour explorer {title} en profondeur. Mettre au défi les apprenants de justifier leur raisonnement et de s'appuyer sur les idées des autres. Documenter les insights clés au tableau et les relier à {competence}.",
    "Diviser la classe en équipes de débat sur une question ouverte ou controversée de {title}. Modérer le débat et s'assurer que tous les points de vue sont entendus. Résumer comment le débat approfondit la compréhension de {competence}.",
]

DISCUSSION_DEV_LEARNER = [
    "Participer activement à la discussion en partageant des idées, posant des questions et s'appuyant sur les contributions des pairs. Prendre des notes sur les concepts clés de {title} et les relier à des applications réelles.",
    "Travailler en binômes ou petits groupes pour discuter des questions directrices sur {title}. Écouter les perspectives des autres et affiner leur propre compréhension avant de présenter à la classe.",
    "S'engager dans le dialogue socratique en répondant aux questions et en questionnant les hypothèses. Collaborer avec les pairs pour co-construire une compréhension plus approfondie de {title}.",
    "Participer au débat en recherchant et défendant une position sur {title}. Écouter respectueusement les points de vue opposés et ajuster sa pensée en fonction des preuves.",
]

DISCUSSION_CONC_TEACHER = [
    "Résumer les points clés de la discussion sur {title}. Renforcer la compétence de l'unité: {competence}. Assigner une brève tâche de réflexion ou des devoirs.",
    "Demander aux apprenants de partager un nouvel apprentissage qu'ils ont acquis sur {title}. Relier ces connaissances à {competence}. Fournir une brève tâche de devoirs pour consolider l'apprentissage.",
    "Afficher les principales conclusions atteintes lors de la discussion sur {title}. Clarifier les misconceptions restantes et souligner comment cela renforce {competence}. Définir les attentes pour la prochaine leçon.",
    "Animer une activité de ticket de sortie où les apprenants écrivent le concept le plus important qu'ils ont appris sur {title}. Examiner les réponses et renforcer {competence}.",
]

DISCUSSION_CONC_LEARNER = [
    "Réfléchir à ce qui a été appris sur {title}. Poser les questions restantes et noter le résumé de l'enseignant. Enregistrer les devoirs ou les activités de suivi dans les cahiers d'exercices.",
    "Partager un apprentissage clé de la leçon sur {title} avec la classe. Noter les devoirs et préparer des questions pour la prochaine leçon.",
    "Revoir le résumé fourni par l'enseignant sur {title}. Demander des clarifications sur les points confus et s'assurer de la compréhension de {competence}.",
    "Compléter le ticket de sortie en écrivant leur point d'apprentissage principal sur {title}. Le remettre à l'enseignant et noter les activités de suivi assignées.",
]

GROUP_INTRO_TEACHER = [
    "Définir le contexte de {title} en expliquant brièvement les objectifs de l'activité. Diviser les apprenants en groupes de 4-5 et distribuer des fiches de travail alignées sur {competence}. Clarifier les rôles: animateur, secrétaire, présentateur, gardien du temps.",
    "Introduire le défi de groupe lié à {title}. Former des groupes équilibrés et attribuer à chacun une tâche ou une question spécifique alignée sur {competence}. Expliquer le livrable attendu et le calendrier.",
    "Afficher les résultats d'apprentissage de {title} et expliquer comment le travail de groupe aidera à atteindre {competence}. Organiser les apprenants en groupes hétérogènes et distribuer des ressources ou des études de cas.",
    "Présenter une situation-problème liée à {title}. Répartir les apprenants en équipes collaboratives et décrire le processus d'investigation lié à {competence}.",
]

GROUP_INTRO_LEARNER = [
    "Rejoindre les groupes assignés et lire les instructions de la tâche. Clarifier les questions sur l'activité de {title}. S'entendre sur les rôles au sein du groupe.",
    "Former les groupes et revoir le défi ou la question assignée sur {title}. Discuter des idées initiales et attribuer les rôles: leader, secrétaire, gardien du temps, présentateur.",
    "Rejoindre le groupe assigné et revoir les résultats d'apprentissage de {title}. Lire la fiche de travail et clarifier les attentes avec l'enseignant si nécessaire.",
    "S'organiser en équipes et examiner la situation-problème liée à {title}. Brainstormer des solutions initiales et déléguer les tâches entre les membres du groupe.",
]

GROUP_DEV_TEACHER = [
    "Se déplacer entre les groupes pour surveiller les progrès et fournir des conseils ciblés sur {title}. Poser des questions de sondage pour approfondir les discussions de groupe. S'assurer que tous les groupes restent concentrés sur l'atteinte de {competence}. Noter les observations pour les retours lors de la conclusion.",
    "Circuler parmi les groupes et écouter les discussions sur {title}. Fournir des indices ou des ressources lorsque les groupes sont bloqués. Encourager les apprenants plus silencieux à contribuer et maintenir les groupes sur la voie de {competence}.",
    "Agir comme facilitateur en visitant chaque groupe et en posant des questions de responsabilité sur {title}. Rediriger les groupes qui s'éloignent du sujet et assurer une participation équitable vers {competence}.",
    "Observer la dynamique de groupe et intervenir lorsque la collaboration se détériore. Modéliser des techniques de résolution de problèmes lorsque les groupes font face à des défis avec {title}. Renforcer la gestion du temps et l'orientation vers {competence}.",
]

GROUP_DEV_LEARNER = [
    "Collaborer pour investiguer, résoudre des tâches et discuter des concepts liés à {title}. Le secrétaire documente les résultats tandis que l'animateur maintient le groupe sur la tâche. Préparer une brève présentation de groupe des résultats clés à partager avec la classe.",
    "Travailler ensemble pour analyser les informations et résoudre le problème assigné sur {title}. Discuter de différentes perspectives et trouver un consensus. Préparer des supports visuels ou un bref rapport pour présenter les résultats.",
    "S'engager dans l'investigation collaborative sur {title}. Diviser les sous-tâches entre les membres du groupe et synthétiser les résultats. S'exercer à présenter les conclusions du groupe avant la présentation finale.",
    "Investiguer la situation-problème liée à {title} en utilisant les ressources fournies. Tester des hypothèses et affiner les solutions de manière collaborative. Documenter le processus de résolution de problèmes pour la présentation.",
]

GROUP_CONC_TEACHER = [
    "Inviter 1-2 groupes à présenter leurs résultats sur {title}. Offrir des retours constructifs et corriger les misconceptions. Consolider l'apprentissage en réaffirmant la compétence clé: {competence}.",
    "Animer une visite de galerie où les groupes affichent leur travail sur {title}. Conduire une discussion en classe entière sur les thèmes communs et les différences. Résumer comment le travail de groupe a renforcé {competence}.",
    "Demander à chaque groupe de partager un insight clé sur {title} en 30 secondes. Identifier les bons exemples et les domaines d'amélioration. Relier toutes les présentations à la compétence de l'unité: {competence}.",
    "Sélectionner 2-3 groupes pour présenter et inviter les retours des pairs sur leur travail sur {title}. Souligner l'excellence de la collaboration et renforcer comment l'activité a construit {competence}.",
]

GROUP_CONC_LEARNER = [
    "Les présentateurs du groupe partagent les résultats clés sur {title}. Les autres apprenants écoutent, prennent des notes et posent des questions de suivi. Réfléchir individuellement à ce que l'activité de groupe a ajouté à leur compréhension.",
    "Participer à la visite de galerie en consultant le travail des autres groupes sur {title}. Poser des questions et comparer les approches. Écrire une brève réflexion sur ce qu'ils ont appris de leurs pairs.",
    "Écouter les présentations des pairs sur {title} et identifier les similitudes et différences. Fournir des retours respectueux lorsqu'invité par l'enseignant. Résumer l'apprentissage personnel dans leurs cahiers.",
    "Présenter les résultats du groupe sur {title} si sélectionné. Écouter attentivement les retours des pairs et affiner la compréhension en fonction de la discussion de classe.",
]

PROJECT_INTRO_TEACHER = [
    "Introduire le cahier des charges du projet pour {title}. Expliquer la question directrice alignée sur {competence} et le contexte réel de {unit_title}. Décrire les livrables, les jalons et les critères de réussite. Constituer les équipes de projet et distribuer les ressources.",
    "Présenter un problème réel lié à {title} nécessitant une solution de projet. Relier le défi à {competence} et expliquer comment les apprenants démontreront leur maîtrise. Former des équipes et fournir l'accès aux outils, gabarits ou ressources de recherche.",
    "Lancer le projet en montrant un exemple de solution lié à {title}. Discuter de ce qui le rend efficace et comment il démontre {competence}. Constituer les équipes et clarifier le calendrier et les points de contrôle du projet.",
    "Engager les apprenants avec une présentation multimédia du thème du projet sur {title}. Expliquer le public authentique qui bénéficiera de leur travail. Organiser les équipes et distribuer la rubrique de projet alignée sur {competence}.",
]

PROJECT_INTRO_LEARNER = [
    "Réviser le cahier des charges du projet pour {title} et poser des questions de clarification. Comprendre le livrable attendu et son lien avec {competence}. Former des équipes, attribuer des rôles et commencer la planification initiale du projet.",
    "Lire l'énoncé du problème réel lié à {title}. Discuter avec les coéquipiers comment aborder le défi et les compétences nécessaires. Réviser la rubrique de projet et les critères de réussite liés à {competence}.",
    "Examiner l'exemple de solution pour {title} et identifier les caractéristiques clés. Proposer des idées initiales avec leur équipe et esquisser un plan de projet.",
    "Regarder la présentation multimédia du thème du projet sur {title}. Discuter avec les coéquipiers qui est le public authentique et ce dont il a besoin. Commencer à définir les rôles et à ébaucher un calendrier de projet.",
]

PROJECT_DEV_TEACHER = [
    "Accompagner les équipes individuelles pendant qu'elles conçoivent et construisent leur solution pour {title}. Fournir des retours formatifs sur les progrès et rediriger les équipes qui s'écartent de l'objectif de compétence: {competence}. Modéliser des techniques de résolution de problèmes et susciter une investigation plus profonde.",
    "Mener des entretiens de suivi avec chaque équipe pour évaluer les progrès sur {title}. Poser des questions de sondage qui poussent les apprenants à affiner leur travail vers {competence}. Fournir un enseignement juste-à-temps sur les compétences techniques ou les connaissances de contenu.",
    "Animer des sessions de critique entre pairs où les équipes partagent leur travail en cours sur {title}. Guider les apprenants à donner des retours constructifs alignés sur la rubrique de projet. S'assurer que toutes les équipes sont sur la voie de démontrer {competence}.",
    "Observer les équipes pendant qu'elles recherchent, prototypent et testent des solutions pour {title}. Intervenir lorsque les équipes font face à des obstacles en posant des questions directrices plutôt qu'en fournissant des réponses. Surveiller l'alignement avec {competence} et ajuster le soutien selon les besoins.",
]

PROJECT_DEV_LEARNER = [
    "Rechercher, concevoir et développer leur solution de projet liée à {title}. Collaborer au sein des équipes, prendre des décisions, tester des idées et affiner la solution pour répondre aux exigences de {competence}. Documenter les progrès dans un carnet de projet.",
    "S'engager dans des cycles itératifs de construction, test et révision de leur solution pour {title}. Rechercher des retours de l'enseignant et des pairs lors des suivis. S'assurer que le projet démontre la maîtrise de {competence}.",
    "Participer à la critique entre pairs en présentant le travail en cours sur {title}. Écouter les retours et les utiliser pour améliorer le projet. Continuer à aligner le travail sur la rubrique et {competence}.",
    "Mener des recherches et collecter des données pour informer leur projet sur {title}. Prototyper plusieurs solutions et sélectionner l'approche la plus efficace. Collaborer étroitement pour respecter les jalons et atteindre {competence}.",
]

PROJECT_CONC_TEACHER = [
    "Animer les présentations ou démonstrations de projet sur {title}. Évaluer chaque équipe à l'aide d'une rubrique alignée sur {competence}. Fournir des retours structurés et souligner les meilleures pratiques observées. Relier les résultats du projet à la compétence de l'unité.",
    "Organiser une exposition de projets où les équipes présentent leurs solutions pour {title}. Inviter l'auto-évaluation et l'évaluation par les pairs à l'aide de la rubrique de projet. Résumer les réussites communes et les domaines de croissance pour démontrer {competence}.",
    "Conduire les présentations finales où les équipes présentent leurs solutions à un public authentique. Utiliser une rubrique pour évaluer à la fois le produit et la présentation liés à {title}. Célébrer les réalisations et renforcer comment le projet a construit {competence}.",
    "Organiser une séance de réflexion où les équipes discutent de ce qu'elles ont appris sur {title}. Utiliser la rubrique pour fournir des retours individuels et d'équipe. Souligner comment le processus de projet a développé {competence}.",
]

PROJECT_CONC_LEARNER = [
    "Présenter ou démontrer leur projet terminé sur {title} à la classe. Répondre aux questions de l'enseignant et des pairs. Réfléchir à l'expérience du projet et écrire une brève auto-évaluation sur la façon dont ils ont atteint {competence}.",
    "Présenter leur solution de projet pour {title} à l'exposition. S'engager avec les pairs qui examinent leur travail et expliquer les décisions de conception. Compléter une auto-évaluation à l'aide de la rubrique de projet alignée sur {competence}.",
    "Livrer une présentation finale de leur solution pour {title} au public authentique. Répondre aux questions et défendre les choix de conception. Réfléchir par écrit à la façon dont le projet les a aidés à développer {competence}.",
    "Participer à la séance de réflexion en partageant les leçons apprises sur {title}. Revoir les retours des pairs et de l'enseignant sur leur projet. Documenter la croissance personnelle dans l'atteinte de {competence} dans leur carnet de projet.",
]


# ─────────────────────────────────────────────────────────────────────────────
# STEP GENERATOR
# ─────────────────────────────────────────────────────────────────────────────

def generate_steps(lesson, strategy, total_duration=40):
    title      = lesson.title
    unit       = lesson.unit
    competence = getattr(unit, "key_unit_competence", f"comprendre {title}")
    unit_title = getattr(unit, "title", title)
    lesson_id  = lesson.id

    intro_dur = round(total_duration * 0.20)
    dev_dur   = round(total_duration * 0.60)
    conc_dur  = total_duration - intro_dur - dev_dur

    def fmt(template):
        return template.format(title=title, unit_title=unit_title, competence=competence)

    if strategy.name == "Méthode de Discussion":
        return [
            {
                "order": 1, "title": "Introduction", "duration": intro_dur,
                "teacher": fmt(pick_variant(lesson_id, 1, DISCUSSION_INTRO_TEACHER)),
                "learner": fmt(pick_variant(lesson_id, 1, DISCUSSION_INTRO_LEARNER)),
                "competence": "Communication et Pensée Critique",
                "competence_integration": generate_competence_integration(lesson, "intro"),
                "lesson_description": generate_lesson_description(lesson),
                "instructional_objective": generate_instructional_objective(lesson),
                "cross_cutting_issues": generate_cross_cutting_issues(lesson),
            },
            {
                "order": 2, "title": "Développement de la Leçon", "duration": dev_dur,
                "teacher": fmt(pick_variant(lesson_id, 2, DISCUSSION_DEV_TEACHER)),
                "learner": fmt(pick_variant(lesson_id, 2, DISCUSSION_DEV_LEARNER)),
                "competence": "Pensée Critique, Communication et Apprentissage Tout au Long de la Vie",
                "competence_integration": generate_competence_integration(lesson, "development"),
            },
            {
                "order": 3, "title": "Conclusion", "duration": conc_dur,
                "teacher": fmt(pick_variant(lesson_id, 3, DISCUSSION_CONC_TEACHER)),
                "learner": fmt(pick_variant(lesson_id, 3, DISCUSSION_CONC_LEARNER)),
                "competence": "Auto-Régulation et Communication",
                "competence_integration": generate_competence_integration(lesson, "conclusion"),
            },
        ]

    elif strategy.name == "Travail Collaboratif en Groupe":
        return [
            {
                "order": 1, "title": "Introduction", "duration": intro_dur,
                "teacher": fmt(pick_variant(lesson_id, 1, GROUP_INTRO_TEACHER)),
                "learner": fmt(pick_variant(lesson_id, 1, GROUP_INTRO_LEARNER)),
                "competence": "Coopération et Communication",
                "competence_integration": generate_competence_integration(lesson, "intro"),
                "lesson_description": generate_lesson_description(lesson),
                "instructional_objective": generate_instructional_objective(lesson),
                "cross_cutting_issues": generate_cross_cutting_issues(lesson),
            },
            {
                "order": 2, "title": "Développement de la Leçon", "duration": dev_dur,
                "teacher": fmt(pick_variant(lesson_id, 2, GROUP_DEV_TEACHER)),
                "learner": fmt(pick_variant(lesson_id, 2, GROUP_DEV_LEARNER)),
                "competence": "Travail d'Équipe, Résolution de Problèmes et Pensée Critique",
                "competence_integration": generate_competence_integration(lesson, "development"),
            },
            {
                "order": 3, "title": "Conclusion", "duration": conc_dur,
                "teacher": fmt(pick_variant(lesson_id, 3, GROUP_CONC_TEACHER)),
                "learner": fmt(pick_variant(lesson_id, 3, GROUP_CONC_LEARNER)),
                "competence": "Communication, Apprentissage Tout au Long de la Vie et Auto-Régulation",
                "competence_integration": generate_competence_integration(lesson, "conclusion"),
            },
        ]

    elif strategy.name == "Apprentissage par Projets":
        return [
            {
                "order": 1, "title": "Introduction", "duration": intro_dur,
                "teacher": fmt(pick_variant(lesson_id, 1, PROJECT_INTRO_TEACHER)),
                "learner": fmt(pick_variant(lesson_id, 1, PROJECT_INTRO_LEARNER)),
                "competence": "Pensée Critique, Communication et Créativité",
                "competence_integration": generate_competence_integration(lesson, "intro"),
                "lesson_description": generate_lesson_description(lesson),
                "instructional_objective": generate_instructional_objective(lesson),
                "cross_cutting_issues": generate_cross_cutting_issues(lesson),
            },
            {
                "order": 2, "title": "Développement de la Leçon", "duration": dev_dur,
                "teacher": fmt(pick_variant(lesson_id, 2, PROJECT_DEV_TEACHER)),
                "learner": fmt(pick_variant(lesson_id, 2, PROJECT_DEV_LEARNER)),
                "competence": "Résolution de Problèmes, Recherche, Créativité et Collaboration",
                "competence_integration": generate_competence_integration(lesson, "development"),
            },
            {
                "order": 3, "title": "Conclusion", "duration": conc_dur,
                "teacher": fmt(pick_variant(lesson_id, 3, PROJECT_CONC_TEACHER)),
                "learner": fmt(pick_variant(lesson_id, 3, PROJECT_CONC_LEARNER)),
                "competence": "Communication, Auto-Régulation et Pensée Critique",
                "competence_integration": generate_competence_integration(lesson, "conclusion"),
            },
        ]

    else:
        return [
            {"order": 1, "title": "Introduction", "duration": intro_dur,
             "teacher": f"Introduire {title} et énoncer les objectifs de la leçon.", "learner": f"Écouter et répondre aux questions d'introduction sur {title}.", "competence": "Communication"},
            {"order": 2, "title": "Développement de la Leçon", "duration": dev_dur,
             "teacher": f"Guider les apprenants à travers les activités clés de {title}.", "learner": f"Participer aux activités guidées et aux discussions sur {title}.", "competence": "Pensée Critique"},
            {"order": 3, "title": "Conclusion", "duration": conc_dur,
             "teacher": f"Résumer les points clés et renforcer: {competence}.", "learner": f"Poser des questions et réfléchir à l'apprentissage sur {title}.", "competence": "Auto-Régulation"},
        ]


# ─────────────────────────────────────────────────────────────────────────────
# MANAGEMENT COMMAND
# ─────────────────────────────────────────────────────────────────────────────

class Command(BaseCommand):
    help = "Seed French teaching strategies and lesson steps. Skips existing steps."

    def add_arguments(self, parser):
        parser.add_argument("--clear", action="store_true", default=False)
        parser.add_argument("--lesson_id", type=int, default=None)
        parser.add_argument("--duration", type=int, default=40)

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING(
            "\n🇫🇷 French Strategy Seeder — SKIP-EXISTING MODE\n"
            "────────────────────────────────────────────────\n"
        ))

        if options["clear"]:
            fr_lesson_ids = Lesson.objects.filter(language='fr').values_list('id', flat=True)
            deleted, _ = LessonStrategyStep.objects.filter(lesson_id__in=fr_lesson_ids).delete()
            self.stdout.write(self.style.WARNING(f"  ⚠️  Cleared {deleted} existing fr steps.\n"))

        strategy_objects = {}
        for s_def in STRATEGIES:
            strategy, created = TeachingStrategy.objects.get_or_create(
                name=s_def["name"],
                defaults={"description": s_def["description"],
                          "is_premium_only": s_def["is_premium_only"],
                          "is_active": s_def["is_active"]},
            )
            strategy_objects[s_def["name"]] = strategy
            status = "✅ Créé" if created else "⏩ Existe"
            tier   = "PREMIUM" if s_def["is_premium_only"] else "GRATUIT"
            self.stdout.write(f"  {status} stratégie [{tier}]: {strategy.name}")

        self.stdout.write("")

        lessons_qs = Lesson.objects.filter(language='fr').select_related("unit__subject__class_field")
        if options["lesson_id"]:
            lessons_qs = lessons_qs.filter(id=options["lesson_id"])

        total_lessons = lessons_qs.count()
        if total_lessons == 0:
            self.stdout.write(self.style.ERROR(
                "  ❌ Aucune leçon en français trouvée. Exécutez bulk_upload_units --language fr d'abord."
            ))
            return

        self.stdout.write(self.style.SUCCESS(
            f"  📚 Traitement de {total_lessons} leçon(s) en français...\n"
        ))

        duration       = options["duration"]
        created_count  = 0
        skipped_count  = 0
        lesson_count   = 0
        strategy_list  = list(strategy_objects.values())

        existing_keys = set(
            LessonStrategyStep.objects.filter(
                lesson__language='fr'
            ).values_list("lesson_id", "strategy_id", "step_order")
        )

        for lesson in lessons_qs.order_by("unit__number", "number"):
            lesson_count += 1
            lesson_label = f"Unité {lesson.unit.number} | Leçon {lesson.number}: {lesson.title}"

            lesson_step_keys = {(lesson.id, s.id, o) for s in strategy_list for o in (1, 2, 3)}
            if lesson_step_keys.issubset(existing_keys):
                skipped_count += 1
                self.stdout.write(f"  ⏩ [{lesson_count}/{total_lessons}] IGNORÉ: {lesson_label}")
                continue

            self.stdout.write(f"  📖 [{lesson_count}/{total_lessons}] {lesson_label}")
            steps_created = 0

            for strategy in strategy_list:
                for step in generate_steps(lesson, strategy, total_duration=duration):
                    key = (lesson.id, strategy.id, step["order"])
                    if key in existing_keys:
                        continue
                    LessonStrategyStep.objects.create(
                        lesson=lesson, strategy=strategy,
                        step_order=step["order"], step_title=step["title"],
                        duration_minutes=step["duration"],
                        teacher_activity=step["teacher"], learner_activity=step["learner"],
                        generic_competence=step["competence"],
                        competence_integration=step.get("competence_integration"),
                        lesson_description=step.get("lesson_description"),
                        instructional_objective=step.get("instructional_objective"),
                        cross_cutting_issues=step.get("cross_cutting_issues"),
                    )
                    existing_keys.add(key)
                    created_count += 1
                    steps_created += 1

            self.stdout.write(f"       └─ {steps_created} nouvelles étapes créées ✓")

        self.stdout.write(self.style.SUCCESS(
            f"\n{'─'*55}\n"
            f"  ✅ Ensemencement terminé [FRANÇAIS].\n"
            f"     Leçons traitées    : {lesson_count}\n"
            f"     Leçons ignorées    : {skipped_count}\n"
            f"     Étapes créées      : {created_count}\n"
            f"{'─'*55}\n"
        ))