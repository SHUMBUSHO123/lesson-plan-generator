"""
Management Command: seed_strategies_rw
=======================================
CBC Lesson Plan Generator — Kinyarwanda Strategy Seeder
--------------------------------------------------------
Seeds 3 strategies × 3 steps for every Lesson where language='rw'.
All step content (teacher activities, learner activities, competences,
objectives, descriptions) is written in Kinyarwanda.

Mirrors seed_strategies_per_lesson_skip.py exactly in structure.
SKIP-EXISTING: never overwrites already-seeded steps.

Strategies:
  1. Uburyo bw'Iganiro (Discussion Method)        — FREE
  2. Akazi k'Amatsinda (Group Collaborative Work) — FREE
  3. Kwiga Binyuze mu Bikorwa (Project-Based)     — PREMIUM

Usage:
  python manage.py seed_strategies_rw
  python manage.py seed_strategies_rw --clear
  python manage.py seed_strategies_rw --lesson_id 5
"""

from django.core.management.base import BaseCommand
from lessons.models import Lesson, TeachingStrategy, LessonStrategyStep


# ─────────────────────────────────────────────────────────────────────────────
# STRATEGIES
# ─────────────────────────────────────────────────────────────────────────────

STRATEGIES = [
    {
        "name": "Uburyo bw'Iganiro",
        "description": (
            "Umwarimu ayobora ikiganiro ry'ishuri ryubahiriza amategeko, "
            "akangura ubumenyi bw'ibanze kandi agaragaza abanyeshuri inzira "
            "yo kubaka ubumenyi binyuze mu bibazo no gutumanahana n'inshuti."
        ),
        "is_premium_only": False,
        "is_active": True,
    },
    {
        "name": "Akazi k'Amatsinda",
        "description": (
            "Abanyeshuri bakorana mu matsinda make bagenzura, bakemura ibibazo, "
            "kandi bagaragaza ibyo babonye. Umwarimu azenguruka nk'umuyobozi, "
            "ashyigikira akazi k'amatsinda no gutumanaho."
        ),
        "is_premium_only": False,
        "is_active": True,
    },
    {
        "name": "Kwiga Binyuze mu Bikorwa",
        "description": (
            "Uburyo bw'abishyura. Abanyeshuri bategura kandi bubaka ibisubizo "
            "bya none bijyanye n'ubushobozi bw'inturuka. Umwarimu atoza kandi "
            "asuzuma binyuze no kugenzura no gutanga ibitekerezo bifatika."
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
    "Iri somo risesengura {title} binyuze mu bikorwa bifatika no gukoresha mu bihe bya none.",
    "Abanyeshuri basesengura {title} bakoresheje ubushakashatsi bwo gukorana no kuvumbura binyuze mu yobora.",
    "Iri somo ryorohereza gusobanukirwa {title} binyuze mu bikorwa byimuriwe no gutumanahana n'inshuti.",
    "Binyuze mu gukemura ibibazo no kuganira, abanyeshuri bamenya neza ibintu by'ingenzi bya {title}.",
]

INSTRUCTIONAL_OBJ_VARIANTS = [
    "Burigihe  cy'isomo, abanyeshuri bazashobora gusesengura no gukoresha ibitekerezo bya {title} bagera nibura kuri 80% y'ibisobanuro binyuze mu bikorwa byoborwa.",
    "Buri gihe cy'isomo, abanyeshuri bazagerageza neza kwerekana ko basobanukiwe {title} bagikemura nibura ibibazo 3 neza.",
    "Nyuma y'iri somo, abanyeshuri bazasobanura neza {title} kandi babikoresha mu bihe bya none bashingiwe ku mpamvu zikwiye.",
    "Nyuma yo gusoza, abanyeshuri bazamenya neza {title} bigaragazwa no gusoza neza ibikorwa by'isuzuma.",
]

CROSS_CUTTING_VARIANTS = [
    {
        "issues": "Uburezi bw'Amahoro n'Indangagaciro, Umuco wo Gukurikiza Amahame",
        "integration": "Uburezi bw'amahoro: Burashamizwa binyuze mu gutumanahana n'icyubahiro no gukemura ibibazo byo gukorana. Gukurikiza amahame: Bikomezwa hakoreshejwe amagambo y'ibisobanuro no kwerekana neza iyo bakorana na {title}."
    },
    {
        "issues": "Uburezi Budaheza Umuntu, Ubukungu bwo mu Rugo",
        "integration": "Uburezi budaheza umuntu: Abanyeshuri bose bafata uruhare binyuze mu bikorwa bitandukanye no gufashanya. Ubukungu bwo mu rugo: Ibitekerezo bya {title} bikoreshereza gutegura ingengo y'imari no gufata ibyemezo by'ubukungu."
    },
    {
        "issues": "Uburinganire bw'Ibitsina, Ibidukikije n'Iterambere Rirambye",
        "integration": "Uburinganire bw'ibitsina: Kwitabira bingana bishyigikiwe binyuze mu matsinda ahuje ibitsina n'ibigenerwa neza. Iterambere rirambye: Isomo rya {title} rihurizwa no gukemura ibibazo by'ibidukikije no gucunga amikoro."
    },
    {
        "issues": "Umuco wo Gukurikiza Amahame, Uburezi Bujyanye n'Ubuzima",
        "integration": "Gukurikiza amahame: Byibutswa binyuze mu gukoresha neza amahame ya siyansi/imibare muri {title}. Uburezi bujyanye n'ubuzima: Buhurizwa binyuze mu biganiro ku isesengura ry'amakuru y'ubuzima no gufata ibyemezo by'ubutwari."
    },
]

COMPETENCE_INTEGRATION_VARIANTS = {
    "intro": [
        "Gutumanahana gushyirwaho ubushobozi bwo kuvuga ibitekerezo binyuze mu bibazo by'umwarimu bijyanye na {title}. Gutekereza neza biratangirwa binyuze mu gusesengura intego z'isomo.",
        "Abanyeshuri banoza gutumanahana basangira ibitekerezo bya mbere bya {title}. Gutekereza neza birakangurwa binyuze mu bibazo no guhuza amasomo ashize.",
        "Ubushobozi bwo gutumanahana bugaragara binyuze mu biganiro by'inshuti bya {title}. Gutekereza neza birakangurwa binyuze no kumenya ibibazo no gusobanukirwa intego.",
        "Binyuze mu bibazo bifatika bya {title}, abanyeshuri banoza ubushobozi bwo gutumanahana. Gutekereza neza birashamizwa binyuze mu gusesengura imishyikirano hagati y'ibitekerezo.",
    ],
    "development": [
        "Gutekereza neza birashamira iyo abanyeshuri basesengura ibitekerezo bya {title} kandi basobanura impamvu z'ibyemezo byabo. Ubushobozi bwo gutumanahana bugenda bukomera binyuze no gusobanurira inshuti ibisubizo. Gukorana bikorerwa mu gukemura ibibazo mu matsinda.",
        "Ubushobozi bwo gukemura ibibazo bushyirwaho neza hakoreshejwe {title} gukurikirana. Ubufatanye bugenda bukura binyuze mu bikorwa by'amatsinda. Kwiga ubwawe bishyigikiwe binyuze mu bushakashatsi bwigenga.",
        "Abanyeshuri bashyiraho gutekereza neza basesengura inzira zitandukanye za {title}. Ubushobozi bwo gukorana bukomera binyuze mu gutumanahana n'inshuti. Ubushakashatsi bukorerwa binyuze mu gukusanya amakuru.",
        "Uburemyi buryozwa binyuze mu gushakisha ibisubizo bitandukanye bya {title}. Gukorana gukomera binyuze mu gutumanahana n'inshuti. Kwiga ubwawe birashamizwa binyuze mu bikorwa byoborwa.",
    ],
    "conclusion": [
        "Kwigenzura bikorerwa iyo abanyeshuri basubiramo ibyo bashoboye gusobanukirwa bya {title}. Ubushobozi bwo gutumanahana bukomezwa binyuze no gusobanura ingingo z'ibanze z'inyigisho.",
        "Kwiga ubuzima bwose birashamizwa binyuze mu kwisuzuma ubumenyi bwa {title}. Gutumanahana gukomera binyuze no kuvuga ibibazo bisigaye n'ibyo basanze.",
        "Abanyeshuri bashyiraho kwigenzura basuzuma iterambere ryabo bya {title}. Gutekereza neza bihurizwa binyuze mu gutekereza ku miyoboro y'inyigisho yakoreshejwe.",
        "Kwiga ubwawe birashamizwa abanyeshuri bemera ibice bisigaye by'inyigisho ya {title}. Gutumanahana bikorerwa binyuze no kwigisha inshuti no gusobanura.",
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
    return f"{issues}\n\nUburyo buzagerwaho: {integration}"


def generate_competence_integration(lesson, step_type):
    variants = COMPETENCE_INTEGRATION_VARIANTS.get(step_type, COMPETENCE_INTEGRATION_VARIANTS["intro"])
    variant = pick_variant(lesson.id, {"intro": 1, "development": 2, "conclusion": 3}.get(step_type, 1), variants)
    return variant.format(title=lesson.title)


# ─────────────────────────────────────────────────────────────────────────────
# VARIANT POOLS — KINYARWANDA
# ─────────────────────────────────────────────────────────────────────────────

# ══════════════════════════════════════════════════════════════════════════════
# UBURYO BW'IGANIRO (Discussion Method)
# ══════════════════════════════════════════════════════════════════════════════

DISCUSSION_INTRO_TEACHER = [
    "Akira abanyeshuri kandi atangaze inyigisho: {title}. Baza ibibazo bifunguye kugira ngo ukangure ubumenyi bw'ibanze bwa {unit_title}. Vuga intego y'isomo ijyanye na: {competence}.",
    "Tangira isomo usubira ku byo abanyeshuri basanzwe bazi bya {unit_title}. Huza ubumenyi bw'ibanze n'inyigisho ya none ya {title}. Sobanura neza uko iri somo rifasha kugera kuri: {competence}.",
    "Erekana ishusho cyangwa pose ikibazo cya none gijyanye na {title}. Baza abanyeshuri icyo babona n'uko bihuza na {unit_title}. Tangaza intego y'isomo ijyanye na: {competence}.",
    "Tangira n'ikibazo cy'iganiro-inshuti bya {title}. Rekera abanyeshuri igihe cyo kuganira ibitekerezo byabo mbere yo kongera mu ishuri. Erekana uko iri somo rushaka gukubita: {competence}.",
]

DISCUSSION_INTRO_LEARNER = [
    "Umviriza neza kandi subiza ibibazo by'umwarimu. Sangira ibyo usanzwe uzi bya {title} kandi huza ibitekerezo uva ku masomo ashize.",
    "Fata uruhare mu ishusho cyangwa ikibazo gitanzwe. Ganira ibitekerezo bya mbere n'inshuti mbere yo gutanga mu ganiro rya {title} mu ishuri.",
    "Tekereza ku masomo ashize ajyanye na {unit_title}. Baza ibibazo by'isobanuro kandi witegure kubaka ubumenyi bushya bwa {title}.",
    "Fata uruhare mu kibazo cy'iganiro-inshuti. Sangira ibisobanuro n'ubumenyi bw'ibanze bujyanye na {title} n'inshuti n'umwarimu.",
]

DISCUSSION_DEV_TEACHER = [
    "Ayobora iganiro ryuzuye rya {title}. Koresheza ibibazo by'isobanuro kuzamura gusobanukirwa kwa {competence}. Andika ingingo z'ingenzi ku mbaho kandi yobore abanyeshuri kugera ku byo basanze.",
    "Tanga ibibazo 2-3 bijyanye na {title}. Shishikariza abanyeshuri kuganira ibisubizo mu matsinda make mbere yo kongera mu ishuri. Huza imirimo kandi ukosore ibitekerezo bidakwiye bijyanye na {competence}.",
    "Koresheza ibibazo byo kugerageza kumenya {title} neza. Shishikariza abanyeshuri gusobanura impamvu z'ibyemezo byabo no kubaka ku bitekerezo by'inshuti. Andika ibitekerezo by'ingenzi ku mbaho ujyanye na {competence}.",
    "Banya ishuri mu matsinda abili ajyanye n'ikibazo gifunguye cya {title}. Tanga iganiro kandi ubwisanze ko impande zose zumvikana. Sobanura uko iganiro ryorohereza gusobanukirwa kwa {competence}.",
]

DISCUSSION_DEV_LEARNER = [
    "Fata uruhare mu iganiro asangira ibitekerezo, abaza ibibazo, kandi akubaka ku bitekerezo by'inshuti. Andika ingingo z'ingenzi za {title} kandi ubijyanye n'ibikoresho bya none.",
    "Korana mu matsinda make guganira ibibazo bijyanye na {title}. Umviriza ibitekerezo by'abandi kandi nonosorera ubwenge bwawe mbere yo gutanga mu ishuri.",
    "Fata uruhare mu biganiro by'isobanuro usubiza ibibazo kandi upinga imyumvire. Korana n'inshuti kugira ngo mugire ubumenyi bunini bwa {title}.",
    "Fata uruhare mu iganiro ugenzura kandi ugaragaza umwanya wa {title}. Umviriza n'icyubahiro ibitekerezo bitandukanye kandi uhindura ibyiyumvo hashingiwe ku bimenyetso.",
]

DISCUSSION_CONC_TEACHER = [
    "Sobanura ingingo z'ingenzi z'iganiro rya {title}. Komeza ubushobozi bw'inturuka: {competence}. Ha akazi gato k'isubiramwo cyangwa k'imuhira.",
    "Baza abanyeshuri kongera kimwe gishya basanze bya {title}. Huza ibyo basanze na {competence}. Tanga akazi gato k'imuhira kuzamura inyigisho.",
    "Erekana ibisobanuro by'ingenzi byagezweho mu iganiro rya {title}. Sobanura ibitekerezo bidakwiye bisigaye kandi komeza uko ibi bushaka gukubita {competence}. Shyira imbere integuza y'isomo rikurikira.",
    "Ayobora ibikorwa byo gusohoka aho abanyeshuri bandika ibintu by'ingenzi by'inyigisho basanze bya {title}. Subiramo ibisubizo kandi ukomeze {competence}.",
]

DISCUSSION_CONC_LEARNER = [
    "Subiramo ibyo wize bya {title}. Baza ibibazo bisigaye kandi andika incamake y'umwarimu. Andika akazi k'imuhira cyangwa ibikorwa by'ikurikizaho mu bitabo by'imyitozo.",
    "Sangira kimwe gishya wasanze mu isomo rya {title} n'ishuri. Andika akazi k'imuhira kandi witegure ibibazo by'isomo rikurikira.",
    "Subiramo incamake y'umwarimu bya {title}. Baza kugira ngo usobanuke ibibazo bigora kandi ubwisanze gusobanukirwa kwa {competence}.",
    "Soza ikibazo cyo gusohoka wandika ingingo y'ingenzi wasomye bya {title}. Bita ku mwarimu kandi andike ibikorwa by'ikurikizaho byashyizwe.",
]

# ══════════════════════════════════════════════════════════════════════════════
# AKAZI K'AMATSINDA (Group Collaborative Work)
# ══════════════════════════════════════════════════════════════════════════════

GROUP_INTRO_TEACHER = [
    "Shyira mu ntebe {title} usobanura intego z'ibikorwa. Banya abanyeshuri mu matsinda ya 4-5 kandi usangize imikorere ijyanye na {competence}. Sobanura imirimo: umuyobozi, umuandishi, umutangamagambo, umurinzi w'igihe.",
    "Tangaza ikibazo cy'itsinda gijyanye na {title}. Shyira matsinda yuzuye kandi ha buri tsinda ikibazo runaka cya {competence}. Sobanura icyo biteganyijwe gutanga n'igihe.",
    "Erekana ibyavuye mu nyigisho ya {title} kandi sobanura uko akazi k'amatsinda kazafasha kugera kuri {competence}. Shyira abanyeshuri mu matsinda ahuje kandi usangize ibikoresho cyangwa ibyigwa.",
    "Tanga ikibazo cy'ikigereranyo gijyanye na {title}. Ha abanyeshuri amatsinda yo gukora hamwe kandi sobanura inzira y'ubushakashatsi ijyanye na {competence}.",
]

GROUP_INTRO_LEARNER = [
    "Injira mu matsinda yashyizwe kandi usome amabwiriza y'ibikorwa. Sobanura ibibazo bijyanye n'ibikorwa bya {title}. Emera imirimo mu tsinda.",
    "Shyira matsinda kandi subiramo ikibazo cyashyizwe bya {title}. Ganira ibitekerezo bya mbere kandi shyira imirimo: umuyobozi, umuandishi, umurinzi w'igihe, umutangamagambo.",
    "Injira mu tsinda ryashyizwe kandi subiramo ibyavuye mu nyigisho ya {title}. Soma amabwiriza y'ibikorwa kandi sobanura integuza n'umwarimu niba bikenewe.",
    "Shyira mu matsinda kandi usuzume ikibazo cy'ikigereranyo gijyanye na {title}. Tanga ibisubizo bya mbere no kwirinda ibyo kugabanya imirimo hagati y'abagize itsinda.",
]

GROUP_DEV_TEACHER = [
    "Zunguruka mu matsinda kugira ngo ugenzure iterambere kandi utange ubuyobozi bufatika bya {title}. Baza ibibazo by'isobanuro kuzamura ibiganiro by'amatsinda. Bwisanze ko amatsinda yose aguma ashaka kugera kuri {competence}. Andika ibisobanuro mu kwiyumvisha kugira ngo utange ibitekerezo mu gusozwa.",
    "Zunguruka mu matsinda kandi umvirize ibiganiro bya {title}. Tanga ubufasha cyangwa ibikoresho iyo matsinda agoye. Shishikariza abanyeshuri bacecetse gutanga kandi ugume amatsinda ashaka kugera kuri {competence}.",
    "Korana nk'umuyobozi ugendagenda buri tsinda ubaza ibibazo by'uburiganire bya {title}. Subiza matsinda apotoka ku nzira kandi ubwisanze ko bose bafata uruhare mu kugera kuri {competence}.",
    "Genzura imikobere y'amatsinda kandi injira iyo gukorana bigora. Erekana inzira zo gukemura ibibazo iyo matsinda asanga ingorane za {title}. Komeza gucunga igihe no gutekereza ku kugera kuri {competence}.",
]

GROUP_DEV_LEARNER = [
    "Korana ugenzura, ukemura ibikorwa, no kuganira ibitekerezo bijyanye na {title}. Umuandishi yandika ibyo basanze naho umuyobozi aguma itsinda ku bikorwa. Tegura gutangaza ku makuru y'ingenzi yo kongera n'ishuri.",
    "Korana usesengura amakuru kandi ukemure ikibazo cyashyizwe bya {title}. Ganira ibitekerezo bitandukanye kandi ugere ku bwumvikane mbere yo gutangaza mu ishuri.",
    "Fata uruhare mu bushakashatsi bwo gukorana bya {title}. Gabanya imirimo hagati y'abagize itsinda kandi huza ibyo basanze. Subiramo kugaragaza ibisobanuro by'itsinda mbere yo gutangaza.",
    "Genzura ikibazo cy'ikigereranyo gijyanye na {title} ukoresheje ibikoresho bitanzwe. Gerageza inzere kandi nonosorera ibisubizo byo gukorana. Andika inzira yo gukemura ibibazo kugira ngo ugatangaze.",
]

GROUP_CONC_TEACHER = [
    "Shishikariza amatsinda 1-2 gutangaza ibyo yasanze bya {title}. Tanga ibitekerezo bifatika kandi ukosore ibitekerezo bidakwiye. Huza inyigisho usubira ku bushobozi bw'inturuka: {competence}.",
    "Ayobora inzira y'ingendo y'ingurube aho amatsinda yerekana akazi kabo bya {title}. Yobora iganiro ry'ishuri ryose ku ngingo rusange n'itandukaniro. Sobanura uko akazi k'amatsinda korohereje {competence}.",
    "Baza buri tsinda kongera kimwe gishya basanzwe bya {title} mu masegonda 30. Menya urugero rwiza n'ibice bikeneye kunozwa. Huza ibiganiro byose bijyanye n'ubushobozi bw'inturuka: {competence}.",
    "Hitamo amatsinda 2-3 gutangaza kandi ushishikarize ibitekerezo by'inshuti ku akazi kabo bya {title}. Menya gukorana kwiza kandi ukomeze uko ibikorwa bushaka gukubita {competence}.",
]

GROUP_CONC_LEARNER = [
    "Abahagarara batangaza ibyo amatsinda yasanze bya {title}. Abanyeshuri bandi bumviriza, bafata inyandiko, kandi babaza ibibazo by'ikurikizaho. Tekereza wenyine ku byo akazi k'itsinda kongeye ku gusobanukirwa kwawe.",
    "Fata uruhare mu ngendo y'ingurube ureba akazi k'amatsinda abyita bya {title}. Baza ibibazo kandi ugereranye inzira. Andika gutekereza gugufi ku byo wize uva ku banshuti.",
    "Umviriza ibiganiro by'inshuti bya {title} kandi menya amafanane n'itandukaniro. Tanga ibitekerezo by'icyubahiro niba bishyizwe impuguke n'umwarimu. Sobanura inyigisho y'umuntu mu bitabo byawe.",
    "Tangaza ibyo itsinda ryasanze bya {title} niba wahisemo. Umviriza neza ibitekerezo by'inshuti kandi nonosorera gusobanukirwa hashingiwe ku ganiro ry'ishuri.",
]

# ══════════════════════════════════════════════════════════════════════════════
# KWIGA BINYUZE MU BIKORWA (Project-Based Learning) — PREMIUM
# ══════════════════════════════════════════════════════════════════════════════

PROJECT_INTRO_TEACHER = [
    "Tangaza impapuro y'umushinga wa {title}. Sobanura ikibazo cy'ubuyobozi gijyanye na {competence} n'intego ya none ya {unit_title}. Sobanura ibyo biteganyijwe gutanga, intambwe z'ingenzi, n'ibipimo by'ikizere. Ha amatsinda y'umushinga kandi usangize ibikoresho.",
    "Tanga ikibazo cya none gijyanye na {title} gisaba igisubizo cy'umushinga. Huza ikibazo na {competence} kandi sobanura uko abanyeshuri bagaragaza ubunararibonye. Shyira amatsinda kandi utange uburenganzira ku bikoresho, imbumbatiro, cyangwa ibikoresho by'ubushakashatsi.",
    "Tangaza umushinga werekana urugero rw'igisubizo gijyanye na {title}. Ganira icyo cyatuma ari nziza kandi uko igaragaza {competence}. Ha amatsinda kandi sobanura neza igihe cy'umushinga n'amasegonda y'igenzura.",
    "Shishikariza abanyeshuri binyuze mu tangaza ya multimedia y'inyigisho ya {title}. Sobanura abakira b'ukuri bazageraho akazi kabo. Shyira amatsinda kandi usangize rubango rw'umushinga ijyanye na {competence}.",
]

PROJECT_INTRO_LEARNER = [
    "Subiramo impapuro y'umushinga wa {title} kandi ubaze ibibazo by'isobanuro. Sobanukirwa icyo biteganyijwe gutanga n'uko bihuza na {competence}. Shyira amatsinda, ha imirimo, kandi utangire gutegura umushinga.",
    "Soma ikibazo cya none cy'ikigereranyo gijyanye na {title}. Ganira n'abagize itsinda uko wogereza ikibazo n'ubushobozi bukenewe. Subiramo rubango rw'umushinga n'ibipimo by'ikizere bijyanye na {competence}.",
    "Genzura urugero rw'igisubizo cya {title} kandi menya ibiranga by'ingenzi. Tanga ibitekerezo bya mbere n'itsinda kandi erekana gahunda y'umushinga.",
    "Reba tangaza ya multimedia y'inyigisho ya {title}. Ganira n'abagize itsinda uzi nde abakira b'ukuri ari na cyo bakeneye. Tangira gusobanura imirimo no gutegura igihe cy'umushinga.",
]

PROJECT_DEV_TEACHER = [
    "Toza amatsinda buri kimwe ngo ateguye kandi ubake igisubizo cya {title}. Tanga ibitekerezo by'isuzuma ku iterambere kandi subiza amatsinda apotoka ku ntego: {competence}. Erekana inzira zo gukemura ibibazo kandi shishikariza ubushakashatsi bunini.",
    "Genzura buri tsinda usuzuma iterambere bya {title}. Baza ibibazo bisenga abanyeshuri kuzamura akazi kabo ngo bagere kuri {competence}. Tanga inyigisho zihuye n'igihe ku bumenyi bwa tekiniki cyangwa ibikubiyemo.",
    "Ayobora ibibazo by'inshuti aho amatsinda asangira akazi k'iterambere bya {title}. Yobora abanyeshuri gutanga ibitekerezo bifatika bijyanye na rubango rw'umushinga. Bwisanze ko amatsinda yose agumya kwerekana {competence}.",
    "Genzura amatsinda agerageza, ubake, kandi gerageza ibisubizo bya {title}. Injira iyo matsinda asanga ingorane ubaza ibibazo by'ubuyobozi aho gutanga ibisubizo. Genzura guhuzwa na {competence} kandi uhindure ubufasha nk'uko bikenewe.",
]

PROJECT_DEV_LEARNER = [
    "Genzura, tegura, kandi ubake igisubizo cy'umushinga gijyanye na {title}. Korana mu matsinda, fata ibyemezo, gerageza ibitekerezo, kandi nonosorera igisubizo kugira ngo bihuje n'ibisabwa bya {competence}. Andika iterambere mu gitabo cy'igihe cy'umushinga.",
    "Fata uruhare mu inzira z'iterambere zo kubaka, kugenzura, no kunonosora igisubizo cya {title}. Shakira ibitekerezo by'umwarimu n'inshuti mu biganiro. Bwisanze ko umushinga ugaragaza ubunararibonye bwa {competence}.",
    "Fata uruhare mu biganiro by'inshuti werekana akazi k'iterambere bya {title}. Umviriza ibitekerezo kandi ubikoreshe kuzamura umushinga. Gumya guhuza akazi na rubango na {competence}.",
    "Genzura ubushakashatsi kandi ukusanye amakuru kugira ngo amakuru umushinga wawe bya {title}. Ubake ibisubizo bitandukanye kandi hitamo inzira nziza. Korana neza kugira ngo ugere ku ntambwe kandi kugera kuri {competence}.",
]

PROJECT_CONC_TEACHER = [
    "Ayobora ibiganiro by'umushinga cyangwa kwerekana bya {title}. Suzuma buri tsinda ukoresheje rubango ijyanye na {competence}. Tanga ibitekerezo bifatika kandi menya ibikorwa bwiza byabonwe. Huza ibyavuye mu mushinga bijyanye n'ubushobozi bw'inturuka.",
    "Ikaze ibiganiro aho amatsinda yerekana ibisubizo byabo bya {title}. Shishikariza kwisuzuma n'inshuti ukoresheje rubango rw'umushinga. Sobanura inzira z'ikizere rusange n'ibice by'iterambere mu kwerekana {competence}.",
    "Shyira aho ibiganiro by'imperuka aho amatsinda atangaza ibisubizo byabo ku bakira b'ukuri. Koresheza rubango usuzuma ibicuruzwa n'ibiganiro gijyanye na {title}. Inanira ibyagezweho kandi ukomeze uko inzira y'umushinga yashyizeho {competence}.",
    "Shyira aho ibibazo by'isubiramo aho amatsinda aganira ibyo yize bya {title}. Koresheza rubango gutanga ibitekerezo by'umuntu n'itsinda. Menya uko inzira y'umushinga yashyizeho {competence}.",
]

PROJECT_CONC_LEARNER = [
    "Tangaza cyangwa werekane umushinga wawe warangiye bya {title} mu ishuri. Subiza ibibazo by'umwarimu n'inshuti. Tekereza ku bikorwa by'umushinga kandi wandike kwisuzuma gugufi ku byo wagezweho neza bya {competence}.",
    "Erekana igisubizo cy'umushinga wawe bya {title} mu biganiro. Ganira n'inshuti zisuzumye akazi kawe kandi sobanura ibyemezo by'imiterere. Soza kwisuzuma ukoresheje rubango rw'umushinga ijyanye na {competence}.",
    "Tanga iganiro ry'imperuka ry'igisubizo cyawe bya {title} ku bakira b'ukuri. Subiza ibibazo kandi garagaza inzira z'imiterere. Tekereza mu nyandiko uko umushinga wakugezaho {competence}.",
    "Fata uruhare mu bibazo by'isubiramo usangira inyigisho zasomwe bya {title}. Subiramo ibitekerezo by'inshuti n'umwarimu ku mushinga wawe. Andika iterambere ry'umuntu ryo kugera kuri {competence} mu gitabo cy'igihe cy'umushinga.",
]


# ─────────────────────────────────────────────────────────────────────────────
# STEP GENERATOR
# ─────────────────────────────────────────────────────────────────────────────

def generate_steps(lesson, strategy, total_duration=40):
    title      = lesson.title
    unit       = lesson.unit
    competence = getattr(unit, "key_unit_competence", f"gusobanukirwa {title}")
    unit_title = getattr(unit, "title", title)
    lesson_id  = lesson.id

    intro_dur = round(total_duration * 0.20)
    dev_dur   = round(total_duration * 0.60)
    conc_dur  = total_duration - intro_dur - dev_dur

    def fmt(template):
        return template.format(title=title, unit_title=unit_title, competence=competence)

    if strategy.name == "Uburyo bw'Iganiro":
        return [
            {
                "order": 1, "title": "Intangiriro", "duration": intro_dur,
                "teacher": fmt(pick_variant(lesson_id, 1, DISCUSSION_INTRO_TEACHER)),
                "learner": fmt(pick_variant(lesson_id, 1, DISCUSSION_INTRO_LEARNER)),
                "competence": "Gutumanahana no Gutekereza neza",
                "competence_integration": generate_competence_integration(lesson, "intro"),
                "lesson_description": generate_lesson_description(lesson),
                "instructional_objective": generate_instructional_objective(lesson),
                "cross_cutting_issues": generate_cross_cutting_issues(lesson),
            },
            {
                "order": 2, "title": "Iterambere ry'Isomo", "duration": dev_dur,
                "teacher": fmt(pick_variant(lesson_id, 2, DISCUSSION_DEV_TEACHER)),
                "learner": fmt(pick_variant(lesson_id, 2, DISCUSSION_DEV_LEARNER)),
                "competence": "Gutekereza neza, Gutumanahana no Kwiga Ubuzima Bwose",
                "competence_integration": generate_competence_integration(lesson, "development"),
            },
            {
                "order": 3, "title": "Umusozo w'Isomo", "duration": conc_dur,
                "teacher": fmt(pick_variant(lesson_id, 3, DISCUSSION_CONC_TEACHER)),
                "learner": fmt(pick_variant(lesson_id, 3, DISCUSSION_CONC_LEARNER)),
                "competence": "Kwigenzura no Gutumanahana",
                "competence_integration": generate_competence_integration(lesson, "conclusion"),
            },
        ]

    elif strategy.name == "Akazi k'Amatsinda":
        return [
            {
                "order": 1, "title": "Intangiriro", "duration": intro_dur,
                "teacher": fmt(pick_variant(lesson_id, 1, GROUP_INTRO_TEACHER)),
                "learner": fmt(pick_variant(lesson_id, 1, GROUP_INTRO_LEARNER)),
                "competence": "Gukorana no Gutumanahana",
                "competence_integration": generate_competence_integration(lesson, "intro"),
                "lesson_description": generate_lesson_description(lesson),
                "instructional_objective": generate_instructional_objective(lesson),
                "cross_cutting_issues": generate_cross_cutting_issues(lesson),
            },
            {
                "order": 2, "title": "Iterambere ry'Isomo", "duration": dev_dur,
                "teacher": fmt(pick_variant(lesson_id, 2, GROUP_DEV_TEACHER)),
                "learner": fmt(pick_variant(lesson_id, 2, GROUP_DEV_LEARNER)),
                "competence": "Akazi k'Amatsinda, Gukemura Ibibazo no Gutekereza neza",
                "competence_integration": generate_competence_integration(lesson, "development"),
            },
            {
                "order": 3, "title": "Umusozo w'Isomo", "duration": conc_dur,
                "teacher": fmt(pick_variant(lesson_id, 3, GROUP_CONC_TEACHER)),
                "learner": fmt(pick_variant(lesson_id, 3, GROUP_CONC_LEARNER)),
                "competence": "Gutumanahana, Kwiga Ubuzima Bwose no Kwigenzura",
                "competence_integration": generate_competence_integration(lesson, "conclusion"),
            },
        ]

    elif strategy.name == "Kwiga Binyuze mu Bikorwa":
        return [
            {
                "order": 1, "title": "Intangiriro", "duration": intro_dur,
                "teacher": fmt(pick_variant(lesson_id, 1, PROJECT_INTRO_TEACHER)),
                "learner": fmt(pick_variant(lesson_id, 1, PROJECT_INTRO_LEARNER)),
                "competence": "Gutekereza neza, Gutumanahana no Uburemyi",
                "competence_integration": generate_competence_integration(lesson, "intro"),
                "lesson_description": generate_lesson_description(lesson),
                "instructional_objective": generate_instructional_objective(lesson),
                "cross_cutting_issues": generate_cross_cutting_issues(lesson),
            },
            {
                "order": 2, "title": "Iterambere ry'Isomo", "duration": dev_dur,
                "teacher": fmt(pick_variant(lesson_id, 2, PROJECT_DEV_TEACHER)),
                "learner": fmt(pick_variant(lesson_id, 2, PROJECT_DEV_LEARNER)),
                "competence": "Gukemura Ibibazo, Ubushakashatsi, Uburemyi no Gukorana",
                "competence_integration": generate_competence_integration(lesson, "development"),
            },
            {
                "order": 3, "title": "Umusozo w'Isomo", "duration": conc_dur,
                "teacher": fmt(pick_variant(lesson_id, 3, PROJECT_CONC_TEACHER)),
                "learner": fmt(pick_variant(lesson_id, 3, PROJECT_CONC_LEARNER)),
                "competence": "Gutumanahana, Kwigenzura no Gutekereza neza",
                "competence_integration": generate_competence_integration(lesson, "conclusion"),
            },
        ]

    else:
        return [
            {"order": 1, "title": "Intangiriro", "duration": intro_dur,
             "teacher": f"Tangaza {title} kandi uvuge intego z'isomo.", "learner": f"Umviriza kandi subiza ibibazo bya {title}.", "competence": "Gutumanahana"},
            {"order": 2, "title": "Iterambere ry'Isomo", "duration": dev_dur,
             "teacher": f"Yobora abanyeshuri mu bikorwa by'ingenzi bya {title}.", "learner": f"Fata uruhare mu bikorwa no kuganira bya {title}.", "competence": "Gutekereza neza"},
            {"order": 3, "title": "Umusozo w'Isomo", "duration": conc_dur,
             "teacher": f"Sobanura ingingo z'ingenzi kandi ukomeze: {competence}.", "learner": f"Baza ibibazo kandi subiramo inyigisho bya {title}.", "competence": "Kwigenzura"},
        ]


# ─────────────────────────────────────────────────────────────────────────────
# MANAGEMENT COMMAND
# ─────────────────────────────────────────────────────────────────────────────

class Command(BaseCommand):
    help = "Seed Kinyarwanda teaching strategies and lesson steps. Skips existing steps."

    def add_arguments(self, parser):
        parser.add_argument("--clear", action="store_true", default=False,
                            help="Delete all existing steps for rw lessons before reseeding.")
        parser.add_argument("--lesson_id", type=int, default=None,
                            help="Seed steps for a single lesson ID only.")
        parser.add_argument("--duration", type=int, default=40,
                            help="Default lesson duration in minutes (default: 40).")

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING(
            "\n🇷🇼 Kinyarwanda Strategy Seeder — SKIP-EXISTING MODE\n"
            "────────────────────────────────────────────────────\n"
        ))

        if options["clear"]:
            rw_lesson_ids = Lesson.objects.filter(language='rw').values_list('id', flat=True)
            deleted, _ = LessonStrategyStep.objects.filter(lesson_id__in=rw_lesson_ids).delete()
            self.stdout.write(self.style.WARNING(f"  ⚠️  Cleared {deleted} existing rw steps.\n"))

        strategy_objects = {}
        for s_def in STRATEGIES:
            strategy, created = TeachingStrategy.objects.get_or_create(
                name=s_def["name"],
                defaults={"description": s_def["description"],
                          "is_premium_only": s_def["is_premium_only"],
                          "is_active": s_def["is_active"]},
            )
            strategy_objects[s_def["name"]] = strategy
            status = "✅ Created" if created else "⏩ Exists"
            tier   = "PREMIUM" if s_def["is_premium_only"] else "FREE"
            self.stdout.write(f"  {status} strategy [{tier}]: {strategy.name}")

        self.stdout.write("")

        lessons_qs = Lesson.objects.filter(language='rw').select_related("unit__subject__class_field")
        if options["lesson_id"]:
            lessons_qs = lessons_qs.filter(id=options["lesson_id"])

        total_lessons = lessons_qs.count()
        if total_lessons == 0:
            self.stdout.write(self.style.ERROR(
                "  ❌ No Kinyarwanda lessons found. Run bulk_upload_units --language rw first."
            ))
            return

        self.stdout.write(self.style.SUCCESS(
            f"  📚 Processing {total_lessons} Kinyarwanda lesson(s)...\n"
        ))

        duration       = options["duration"]
        created_count  = 0
        skipped_count  = 0
        lesson_count   = 0
        strategy_list  = list(strategy_objects.values())

        existing_keys = set(
            LessonStrategyStep.objects.filter(
                lesson__language='rw'
            ).values_list("lesson_id", "strategy_id", "step_order")
        )

        for lesson in lessons_qs.order_by("unit__number", "number"):
            lesson_count += 1
            lesson_label = f"Unit {lesson.unit.number} | Isomo {lesson.number}: {lesson.title}"

            lesson_step_keys = {(lesson.id, s.id, o) for s in strategy_list for o in (1, 2, 3)}
            if lesson_step_keys.issubset(existing_keys):
                skipped_count += 1
                self.stdout.write(f"  ⏩ [{lesson_count}/{total_lessons}] SKIP: {lesson_label}")
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

            self.stdout.write(f"       └─ {steps_created} inyandiko nshya zashinzwe ✓")

        self.stdout.write(self.style.SUCCESS(
            f"\n{'─'*55}\n"
            f"  ✅ Gutera imbuto byarangiye [KINYARWANDA].\n"
            f"     Amasomo yakoweho    : {lesson_count}\n"
            f"     Amasomo yasibye     : {skipped_count}\n"
            f"     Intambwe zashinzwe  : {created_count}\n"
            f"{'─'*55}\n"
        ))