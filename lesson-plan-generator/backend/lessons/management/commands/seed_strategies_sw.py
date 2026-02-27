"""
Management Command: seed_strategies_sw
=======================================
CBC Lesson Plan Generator — Kiswahili Strategy Seeder
------------------------------------------------------
Seeds 3 strategies × 3 steps for every Lesson where language='sw'.
All step content is written in Kiswahili.

Mirrors seed_strategies_per_lesson_skip.py exactly in structure.
SKIP-EXISTING: never overwrites already-seeded steps.

Strategies:
  1. Mbinu ya Majadiliano (Discussion Method)     — FREE
  2. Kazi ya Vikundi (Group Collaborative Work)   — FREE
  3. Kujifunza kwa Miradi (Project-Based)         — PREMIUM

Usage:
  python manage.py seed_strategies_sw
  python manage.py seed_strategies_sw --clear
  python manage.py seed_strategies_sw --lesson_id 5
"""

from django.core.management.base import BaseCommand
from lessons.models import Lesson, TeachingStrategy, LessonStrategyStep


# ─────────────────────────────────────────────────────────────────────────────
# STRATEGIES
# ─────────────────────────────────────────────────────────────────────────────

STRATEGIES = [
    {
        "name": "Mbinu ya Majadiliano",
        "description": (
            "Mwalimu anaongoza majadiliano ya darasa yaliyopangwa, "
            "akiamsha maarifa ya awali na kuwaongoza wanafunzi kujenga "
            "uelewa kupitia maswali na mwingiliano wa wenzao."
        ),
        "is_premium_only": False,
        "is_active": True,
    },
    {
        "name": "Kazi ya Vikundi",
        "description": (
            "Wanafunzi wanafanya kazi katika vikundi vidogo kuchunguza, "
            "kutatua matatizo, na kuwasilisha matokeo. Mwalimu anazunguka "
            "kama mshauri, akikuza ushirikiano na uwezo wa mawasiliano."
        ),
        "is_premium_only": False,
        "is_active": True,
    },
    {
        "name": "Kujifunza kwa Miradi",
        "description": (
            "Mbinu ya malipo. Wanafunzi wanabuni na kujenga suluhu halisi "
            "zinazohusiana na uwezo wa kitengo. Mwalimu anafundisha na "
            "kutathmini kupitia uchunguzi na vikao vya maoni yaliyopangwa."
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
    "Somo hili linachunguza {title} kupitia mazoezi ya vitendo na matumizi ya ulimwengu wa kweli.",
    "Wanafunzi wanachunguza {title} wakitumia uchunguzi wa ushirikiano na ugunduzi ulioongozwa.",
    "Somo hili linakuza uelewa wa {title} kupitia shughuli za vitendo na mwingiliano na wenzao.",
    "Kupitia kutatua matatizo na majadiliano, wanafunzi wanajua dhana kuu za {title}.",
]

INSTRUCTIONAL_OBJ_VARIANTS = [
    "Mwishoni mwa somo hili, wanafunzi wataweza kuchambua na kutumia dhana za {title} wakifikia usahihi wa chini ya 80% kupitia mazoezi yaliyoongozwa.",
    "Mwishoni mwa somo hili, wanafunzi watakuwa wameonyesha kwa mafanikio uelewa wa {title} kwa kutatua angalau matatizo 3 kwa usahihi.",
    "Baada ya somo hili, wanafunzi wataweza kueleza kwa usahihi {title} na kuitumia katika hali za ulimwengu wa kweli kwa hoja wazi.",
    "Baada ya kukamilika, wanafunzi watajua {title} kama inavyoonyeshwa na kukamilika kwa usahihi kwa kazi za tathmini ya muundo.",
]

CROSS_CUTTING_VARIANTS = [
    {
        "issues": "Elimu ya Amani na Maadili, Utamaduni wa Viwango",
        "integration": "Elimu ya amani: Inakuzwa kupitia mwingiliano wa heshima na wenzao na kutatua matatizo kwa ushirikiano. Viwango: Inaimarishwa kwa kutumia istilahi sahihi na uwakilishi thabiti unapofanya kazi na {title}."
    },
    {
        "issues": "Elimu Jumuishi, Ujuzi wa Fedha",
        "integration": "Elimu jumuishi: Wanafunzi wote wanashiriki kupitia kazi tofauti na msaada wa wenzao. Ujuzi wa fedha: Dhana za {title} zinatumika katika hali za kupanga bajeti na kufanya maamuzi ya fedha."
    },
    {
        "issues": "Usawa wa Kijinsia, Mazingira na Uendelevu",
        "integration": "Usawa wa kijinsia: Ushiriki sawa unakusudiwa kupitia vikundi vya jinsia mchanganyiko na ugawaji wa majukumu wa usawa. Uendelevu: Somo la {title} linahusishwa na kutatua matatizo ya mazingira na usimamizi wa rasilimali."
    },
    {
        "issues": "Utamaduni wa Viwango, Elimu Kamili ya Ujinsia",
        "integration": "Viwango: Inasisitizwa kupitia matumizi sahihi ya mikataba ya kisayansi/kihesabu katika {title}. Elimu kamili ya ujinsia: Imejumuishwa kupitia majadiliano ya uchambuzi wa data ya afya na kufanya maamuzi ya uwajibikaji."
    },
]

COMPETENCE_INTEGRATION_VARIANTS = {
    "intro": [
        "Mawasiliano yanakuzwa wanafunzi wanapoeleza maarifa ya awali na kuuliza maswali ya ufafanuzi kuhusu {title}. Fikira makini inaanza kupitia uchambuzi wa malengo ya somo.",
        "Wanafunzi wanafanya mazoezi ya mawasiliano kwa kushiriki mawazo ya awali kuhusu {title}. Fikira makini inaamshwa kupitia maswali na kuunganisha na masomo ya awali.",
        "Uwezo wa mawasiliano unaonekana kupitia majadiliano ya wenza kuhusu {title}. Fikira makini inashughulikiwa kupitia utambuzi wa tatizo na uelewa wa lengo.",
        "Kupitia maswali yaliyopangwa kuhusu {title}, wanafunzi wanakuza ustadi wa mawasiliano. Fikira makini inakuzwa kupitia uchambuzi wa mahusiano kati ya dhana.",
    ],
    "development": [
        "Fikira makini inakua wanafunzi wanapochambua dhana za {title} na kuhalalisha hoja zao. Uwezo wa mawasiliano unakua kupitia kuelezea suluhisho kwa wenzao. Ushirikiano unafanyiwa mazoezi kupitia kutatua matatizo kwa vikundi.",
        "Ujuzi wa kutatua matatizo unaimarishwa kwa kufanya kazi kupitia {title} kwa utaratibu. Ushirikiano unakua kupitia kazi za vikundi. Kujifunza maisha yote kunakuzwa kupitia uchunguzi binafsi.",
        "Wanafunzi wanajenga fikira makini kwa kutathmini mbinu tofauti za {title}. Uwezo wa ushirikiano unakua kupitia uchunguzi wa pamoja. Ujuzi wa utafiti unafanyiwa mazoezi kupitia ukusanyaji wa habari.",
        "Ubunifu unakusudiwa kupitia kuchunguza suluhisho nyingi za {title}. Ushirikiano unaimarishwa kupitia maoni ya wenzao. Kujifunza binafsi kunakuzwa kupitia mazoezi yaliyoongozwa.",
    ],
    "conclusion": [
        "Kujidhibiti kunafanyiwa mazoezi wanafunzi wanapofikiri tena juu ya uelewa wao wa {title}. Uwezo wa mawasiliano unaimarishwa kupitia kufupisha pointi kuu za kujifunza.",
        "Kujifunza maisha yote kunakuzwa kupitia tathmini ya kibinafsi ya ustadi wa {title}. Mawasiliano yanaimarishwa kwa kueleza maswali yaliyobaki na maarifa yaliyopatikana.",
        "Wanafunzi wanakuza kujidhibiti kwa kutathmini maendeleo yao ya {title}. Fikira makini inachanganywa kupitia kutafakari juu ya mikakati ya kujifunza iliyotumika.",
        "Kujifunza binafsi kunakuzwa wanafunzi wanapotambua maeneo ya masomo zaidi ya {title}. Mawasiliano yanafanyiwa mazoezi kupitia kufundisha wenzao na kueleza.",
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
    return f"{issues}\n\nUjumuishaji: {integration}"


def generate_competence_integration(lesson, step_type):
    variants = COMPETENCE_INTEGRATION_VARIANTS.get(step_type, COMPETENCE_INTEGRATION_VARIANTS["intro"])
    variant = pick_variant(lesson.id, {"intro": 1, "development": 2, "conclusion": 3}.get(step_type, 1), variants)
    return variant.format(title=lesson.title)


# ─────────────────────────────────────────────────────────────────────────────
# VARIANT POOLS — KISWAHILI
# ─────────────────────────────────────────────────────────────────────────────

DISCUSSION_INTRO_TEACHER = [
    "Karibisha wanafunzi na utangulize mada: {title}. Uliza maswali wazi ili kuamsha maarifa ya awali kuhusu {unit_title}. Taja lengo la somo linalohusiana na: {competence}.",
    "Anza somo kwa kupitia kile wanafunzi wanachokijua tayari kuhusu {unit_title}. Unganisha maarifa ya awali na lengo la leo la {title}. Eleza wazi jinsi somo hili linavyochangia: {competence}.",
    "Onyesha picha au uliza hali ya ulimwengu wa kweli inayohusiana na {title}. Waulize wanafunzi wanaona nini na inavyounganika na {unit_title}. Tambulisha lengo la somo linalohusiana na: {competence}.",
    "Anza na swali la fikiri-joza-shiriki kuhusu {title}. Ruhusu wanafunzi kujadili mawazo yao ya awali kabla ya kushiriki na darasa. Eleza jinsi somo hili linavyojenga kuelekea: {competence}.",
]

DISCUSSION_INTRO_LEARNER = [
    "Sikiliza kwa makini na ujibu maswali ya mwalimu. Shiriki unachojua tayari kuhusu {title} na unganisha mawazo kutoka masomo ya awali.",
    "Shiriki na picha au hali iliyowasilishwa. Jadili mawazo ya awali na mwenzako kabla ya kuchangia katika majadiliano ya darasa kuhusu {title}.",
    "Fikiria juu ya masomo ya awali yanayohusiana na {unit_title}. Uliza maswali ya ufafanuzi na ujiandae kujenga uelewa mpya wa {title}.",
    "Shiriki katika shughuli ya fikiri-joza-shiriki. Shiriki uchunguzi na maarifa ya awali yanayohusiana na {title} na wenzako na mwalimu.",
]

DISCUSSION_DEV_TEACHER = [
    "Ongoza majadiliano yaliyopangwa ya darasa nzima na jozi kuhusu dhana kuu za {title}. Tumia maswali ya kuchunguza ili kukuza uelewa wa {competence}. Andika pointi kuu ubaoni na uwaongoze wanafunzi kufika kwenye hitimisho.",
    "Wasilisha maswali 2-3 ya mwongozo yanayohusiana na {title}. Wahimize wanafunzi kujadili majibu katika vikundi vidogo kabla ya kushiriki na darasa. Fupisha michango na urekebishe dhana potofu zinazohusiana na {competence}.",
    "Tumia mbinu ya Socratic kuchunguza {title} kwa undani. Changamoto wanafunzi kuhalalisha hoja zao na kujenga juu ya mawazo ya wenzao. Rekodi maarifa muhimu ubaoni na uyaunganishe na {competence}.",
    "Gawanya darasa katika timu za mjadala kuhusu swali wazi la {title}. Simamia mjadala na uhakikishe pande zote zinasikiwa. Fupisha jinsi mjadala unavyokua uelewa wa {competence}.",
]

DISCUSSION_DEV_LEARNER = [
    "Shiriki kikamilifu katika majadiliano kwa kushiriki mawazo, kuuliza maswali, na kujenga juu ya michango ya wenzao. Chukua maelezo kuhusu dhana kuu za {title} na uzihusishe na matumizi ya ulimwengu wa kweli.",
    "Fanya kazi kwa jozi au vikundi vidogo kujadili maswali ya mwongozo kuhusu {title}. Sikiliza mitazamo ya wengine na uboreshe uelewa wako kabla ya kuwasilisha darasani.",
    "Shiriki katika mazungumzo ya Socratic kwa kujibu maswali na kupinga dhana. Shirikiana na wenzao kujenga pamoja uelewa wa kina zaidi wa {title}.",
    "Shiriki katika mjadala kwa kutafiti na kutetea msimamo kuhusu {title}. Sikiliza kwa heshima mitazamo inayopingana na ubadilishe fikira kulingana na ushahidi.",
]

DISCUSSION_CONC_TEACHER = [
    "Fupisha pointi kuu kutoka majadiliano kuhusu {title}. Imarisha uwezo wa kitengo: {competence}. Panga kazi fupi ya kutafakari au ya nyumbani.",
    "Waulize wanafunzi kushiriki ufahamu mpya mmoja walioupata kuhusu {title}. Unganisha maarifa haya na {competence}. Toa kazi fupi ya nyumbani kuimarisha kujifunza.",
    "Onyesha hitimisho kuu lililofikiwa wakati wa majadiliano kuhusu {title}. Fafanua dhana potofu zilizobaki na sisitiza jinsi inavyojenga {competence}. Weka matarajio ya somo lijalo.",
    "Ongoza shughuli ya kadi ya kutoka ambapo wanafunzi wanaandika dhana muhimu zaidi waliojifunza kuhusu {title}. Pitia majibu na uimarisha {competence}.",
]

DISCUSSION_CONC_LEARNER = [
    "Fikiria kuhusu ulichojifunza kuhusu {title}. Uliza maswali yaliyobaki na uandike muhtasari wa mwalimu. Rekodi kazi ya nyumbani au shughuli za ufuatiliaji katika vitabu vya mazoezi.",
    "Shiriki jambo moja kuu ulilolichukua kutoka somo kuhusu {title} na darasa. Andika kazi ya nyumbani na ujiandae kwa maswali ya somo lijalo.",
    "Pitia muhtasari uliotolewa na mwalimu kuhusu {title}. Omba ufafanuzi wa pointi zozote za kuchanganya na uhakikishe uelewa wa {competence}.",
    "Kamilisha kadi ya kutoka kwa kuandika pointi yako kuu ya kujifunza kuhusu {title}. Iwasilishe kwa mwalimu na uandike shughuli zozote za ufuatiliaji zilizopewa.",
]

GROUP_INTRO_TEACHER = [
    "Weka muktadha wa {title} kwa kueleza kwa ufupi malengo ya shughuli. Gawanya wanafunzi katika vikundi vya 4-5 na usambaze karatasi za kazi zinazohusiana na {competence}. Fafanua majukumu: msimamizi, mwandishi, mwasilishaji, mlinzi wa muda.",
    "Tambulisha changamoto ya kikundi inayohusiana na {title}. Unda vikundi vyenye usawa na umpe kila kimoja kazi au swali maalum linalolingana na {competence}. Eleza matokeo yanayotarajiwa na ratiba ya wakati.",
    "Onyesha matokeo ya kujifunza ya {title} na eleza jinsi kazi ya kikundi itakavyosaidia kufikia {competence}. Panga wanafunzi katika vikundi tofauti na usambaze rasilimali au tafiti.",
    "Wasilisha hali ya tatizo inayohusiana na {title}. Wapange wanafunzi katika timu za ushirikiano na eleza mchakato wa uchunguzi unaohusiana na {competence}.",
]

GROUP_INTRO_LEARNER = [
    "Nenda kwenye vikundi vilivyopewa na soma maelekezo ya kazi. Fafanua maswali yoyote kuhusu shughuli ya {title}. Kubali majukumu ndani ya kikundi.",
    "Unda vikundi na upitie changamoto au swali lililowekwa kuhusu {title}. Jadili mawazo ya awali na ugawanye majukumu: kiongozi, mwandishi wa maelezo, mlinzi wa muda, mwasilishaji.",
    "Jiunge na kikundi kilichopewa na upitie matokeo ya kujifunza ya {title}. Soma karatasi ya kazi na fafanua matarajio na mwalimu ikiwa inahitajika.",
    "Panga timu na uchunguze hali ya tatizo inayohusiana na {title}. Fikiria suluhisho za awali na ugawanye kazi kati ya wanakikundi.",
]

GROUP_DEV_TEACHER = [
    "Zunguka kati ya vikundi kufuatilia maendeleo na kutoa mwongozo maalum kuhusu {title}. Uliza maswali ya kuchunguza ili kukuza majadiliano ya vikundi. Hakikisha vikundi vyote vinalenga kufikia {competence}. Angalia uchunguzi kwa maoni wakati wa hitimisho.",
    "Zunguka kati ya vikundi na usikilize majadiliano kuhusu {title}. Toa vidokezo au rasilimali vikundi vinapokwama. Wahimize wanafunzi wanaokaa kimya kushiriki na uweke vikundi kwenye njia ya {competence}.",
    "Fanya kama mshauri kwa kutembelea kila kikundi na kuuliza maswali ya uwajibikaji kuhusu {title}. Elekeza vikundi vinavyopotoka na uhakikishe ushiriki sawa kuelekea {competence}.",
    "Angalia mwenendo wa vikundi na uingilie kati wakati ushirikiano unaporomoka. Onesha mbinu za kutatua matatizo vikundi vinapokutana na changamoto za {title}. Imarisha usimamizi wa muda na lengo la kufikia {competence}.",
]

GROUP_DEV_LEARNER = [
    "Shirikiana kuchunguza, kutatua kazi, na kujadili dhana zinazohusiana na {title}. Mwandishi anarekodi matokeo wakati msimamizi anaweka kikundi kwenye kazi. Andaa uwasilishaji mfupi wa kikundi wa matokeo muhimu ya kushiriki na darasa.",
    "Fanya kazi pamoja kuchambua habari na kutatua tatizo lililowekwa kuhusu {title}. Jadili mitazamo tofauti na fikia makubaliano. Andaa vifaa vya kuona au ripoti fupi ili kuwasilisha matokeo.",
    "Shiriki katika uchunguzi wa ushirikiano kuhusu {title}. Gawanya kazi ndogo kati ya wanakikundi na fupisha matokeo. Fanya mazoezi ya kuwasilisha hitimisho la kikundi kabla ya uwasilishaji wa mwisho.",
    "Chunguza hali ya tatizo inayohusiana na {title} ukitumia rasilimali zilizotolewa. Jaribu nadharia na uboreshe suluhisho kwa pamoja. Rekodi mchakato wa kutatua matatizo kwa uwasilishaji.",
]

GROUP_CONC_TEACHER = [
    "Alika vikundi 1-2 kuwasilisha matokeo yao kuhusu {title}. Toa maoni ya ujenzi na urekebishe dhana potofu. Fupisha kujifunza kwa kusema tena uwezo muhimu: {competence}.",
    "Ongoza safari ya matunzio ambapo vikundi vinaonyesha kazi yao kuhusu {title}. Ongoza majadiliano ya darasa nzima kuhusu mada za kawaida na tofauti. Fupisha jinsi kazi ya kikundi ilivyoimarisha {competence}.",
    "Waulize kila kikundi kushiriki ufahamu mmoja muhimu kuhusu {title} katika sekunde 30. Tambua mifano mizuri na maeneo ya uboreshaji. Unganisha uwasilishaji wote na uwezo wa kitengo: {competence}.",
    "Chagua vikundi 2-3 kuwasilisha na ualike maoni ya wenzao kuhusu kazi yao ya {title}. Angazia ushirikiano bora na uimarisha jinsi shughuli ilvyojenga {competence}.",
]

GROUP_CONC_LEARNER = [
    "Wasilishaji wa kikundi wanashiriki matokeo muhimu kuhusu {title}. Wanafunzi wengine wanasikiliza, wanachukua maelezo, na wanauliza maswali ya ufuatiliaji. Fikiria kibinafsi juu ya kile kazi ya kikundi kiliongeza kwa uelewa wako.",
    "Shiriki katika safari ya matunzio kwa kuangalia kazi ya vikundi vingine kuhusu {title}. Uliza maswali na ulinganishe mbinu. Andika tafakuri fupi kuhusu ulichojifunza kutoka kwa wenzako.",
    "Sikiliza uwasilishaji wa wenzao kuhusu {title} na utambue mfanano na tofauti. Toa maoni ya heshima ukiombwa na mwalimu. Fupisha kujifunza binafsi katika daftari lako.",
    "Wasilisha matokeo ya kikundi kuhusu {title} ikiwa umechaguliwa. Sikiliza kwa makini maoni ya wenzao na uboreshe uelewa kulingana na majadiliano ya darasa.",
]

PROJECT_INTRO_TEACHER = [
    "Tambulisha muhtasari wa mradi wa {title}. Eleza swali la msingi linalolingana na {competence} na muktadha wa ulimwengu wa kweli wa {unit_title}. Eleza matokeo yanayotarajiwa, alama za njia, na vigezo vya mafanikio. Wapange timu za mradi na usambaze nyenzo za rasilimali.",
    "Wasilisha tatizo la ulimwengu wa kweli linalohusu {title} ambalo linahitaji suluhu ya mradi. Unganisha changamoto na {competence} na eleza jinsi wanafunzi watathibitisha ustadi. Unda timu na toa ufikiaji wa zana, violezo, au nyenzo za utafiti.",
    "Anzisha mradi kwa kuonyesha mfano wa suluhu inayohusiana na {title}. Jadili kinachofanya iwe na ufanisi na jinsi inavyoonyesha {competence}. Panga timu na fafanua ratiba ya mradi na alama za ukaguzi.",
    "Washirikishe wanafunzi na utambulisho wa media nyingi wa mada ya mradi wa {title}. Eleza hadhira halisi ambao watanufaika na kazi yao. Panga timu na usambaze rubrika ya mradi inayolingana na {competence}.",
]

PROJECT_INTRO_LEARNER = [
    "Pitia muhtasari wa mradi wa {title} na uulize maswali ya ufafanuzi. Elewa matokeo yanayotarajiwa na jinsi yanavyohusiana na {competence}. Unda timu, gawanya majukumu, na uanze kupanga mradi wa awali.",
    "Soma taarifa ya tatizo la ulimwengu wa kweli inayohusiana na {title}. Jadili na wanatimu jinsi ya kukabiliana na changamoto na ujuzi unaohitajika. Pitia rubrika ya mradi na vigezo vya mafanikio vinavyohusiana na {competence}.",
    "Chunguza mfano wa suluhu ya {title} na utambue vipengele muhimu. Fikiria mawazo ya awali na timu yako na eleza mpango wa mradi.",
    "Tazama utambulisho wa media nyingi wa mada ya mradi wa {title}. Jadili na wanatimu ni nani hadhira halisi na wanachohitaji. Anza kufafanua majukumu na kuandaa ratiba ya mradi.",
]

PROJECT_DEV_TEACHER = [
    "Fundisha timu za mtu mmoja mmoja zinapobuni na kujenga suluhu yao ya {title}. Toa maoni ya muundo kuhusu maendeleo na elekeza timu zinazopotoka kutoka lengo la uwezo: {competence}. Onesha mbinu za kutatua matatizo na uchochee uchunguzi wa kina zaidi.",
    "Fanya mikutano ya kukagua na kila timu ili kutathmini maendeleo ya {title}. Uliza maswali ya kuchunguza yanayosukuma wanafunzi kuboresha kazi yao kuelekea {competence}. Toa mafunzo ya wakati mwafaka kuhusu ujuzi wa kiufundi au maarifa ya maudhui.",
    "Ongoza vikao vya uhakiki wa wenzao ambapo timu zinashiriki kazi inayoendelea ya {title}. Waongoze wanafunzi kutoa maoni ya ujenzi yanayolingana na rubrika ya mradi. Hakikisha timu zote ziko kwenye njia ya kuonyesha {competence}.",
    "Angalia timu zinatafuta, kubuni, na kujaribu suluhu za {title}. Ingilia kati timu zinapokutana na vizuizi kwa kuuliza maswali ya mwongozo badala ya kutoa majibu. Fuatilia ulingano na {competence} na urekebishe msaada inavyohitajika.",
]

PROJECT_DEV_LEARNER = [
    "Tafuta, buni, na tengeneza suluhu ya mradi inayohusiana na {title}. Shirikiana ndani ya timu, fanya maamuzi, jaribu mawazo, na uboreshe suluhu ili kukidhi mahitaji ya {competence}. Rekodi maendeleo katika daftari la mradi.",
    "Shiriki katika mizunguko ya mzunguko ya kujenga, kujaribu, na kurekebisha suluhu yako ya {title}. Tafuta maoni kutoka kwa mwalimu na wenzao wakati wa ukaguzi. Hakikisha mradi unaonyesha ustadi wa {competence}.",
    "Shiriki katika uhakiki wa wenzao kwa kuwasilisha kazi inayoendelea kuhusu {title}. Sikiliza maoni na uyatumie kuboresha mradi. Endelea kuunga mkono kazi na rubrika na {competence}.",
    "Fanya utafiti na ukusanye data ili kufahamisha mradi wako kuhusu {title}. Buni suluhu nyingi na uchague mbinu inayofaa zaidi. Shirikiana kwa karibu ili kukidhi alama za njia na kufikia {competence}.",
]

PROJECT_CONC_TEACHER = [
    "Ongoza uwasilishaji wa mradi au maonyesho kuhusu {title}. Tathmini kila timu ukitumia rubrika inayolingana na {competence}. Toa maoni yaliyopangwa na uangalize mbinu bora zilizoonekana. Unganisha matokeo ya mradi na uwezo wa kitengo.",
    "Andaa maonyesho ya mradi ambapo timu zinaonyesha suluhu zao za {title}. Alika tathmini ya wenzao na binafsi ukitumia rubrika ya mradi. Fupisha mafanikio ya kawaida na maeneo ya ukuaji wa kuonyesha {competence}.",
    "Fanya uwasilishaji wa mwisho ambapo timu zinawasilisha suluhu zao kwa hadhira halisi. Tumia rubrika kutathmini bidhaa na uwasilishaji unaohusiana na {title}. Sherehekea mafanikio na uimarisha jinsi mradi ulivyojenga {competence}.",
    "Panga kikao cha tafakuri ambapo timu zinajadili walichojifunza kuhusu {title}. Tumia rubrika kutoa maoni ya mtu mmoja mmoja na kikundi. Angazia jinsi mchakato wa mradi ulivyokua {competence}.",
]

PROJECT_CONC_LEARNER = [
    "Wasilisha au uonyeshe mradi wako uliokamilika kuhusu {title} kwa darasa. Jibu maswali kutoka kwa mwalimu na wenzao. Fikiria uzoefu wa mradi na uandike tathmini fupi ya kibinafsi kuhusu jinsi ulivyofikia {competence}.",
    "Onyesha suluhu ya mradi wako ya {title} katika maonyesho. Shiriki na wenzao wanaopitia kazi yako na ueleze maamuzi ya muundo. Kamilisha tathmini ya kibinafsi ukitumia rubrika ya mradi inayolingana na {competence}.",
    "Toa uwasilishaji wa mwisho wa suluhu yako ya {title} kwa hadhira halisi. Jibu maswali na utetee maamuzi ya muundo. Fikiria kwa maandishi jinsi mradi ulikukuza {competence}.",
    "Shiriki katika kikao cha tafakuri kwa kushiriki masomo yaliyojifunzwa kuhusu {title}. Pitia maoni ya wenzao na mwalimu kuhusu mradi wako. Rekodi ukuaji wa kibinafsi katika kufikia {competence} katika daftari lako la mradi.",
]


# ─────────────────────────────────────────────────────────────────────────────
# STEP GENERATOR
# ─────────────────────────────────────────────────────────────────────────────

def generate_steps(lesson, strategy, total_duration=40):
    title      = lesson.title
    unit       = lesson.unit
    competence = getattr(unit, "key_unit_competence", f"kuelewa {title}")
    unit_title = getattr(unit, "title", title)
    lesson_id  = lesson.id

    intro_dur = round(total_duration * 0.20)
    dev_dur   = round(total_duration * 0.60)
    conc_dur  = total_duration - intro_dur - dev_dur

    def fmt(template):
        return template.format(title=title, unit_title=unit_title, competence=competence)

    if strategy.name == "Mbinu ya Majadiliano":
        return [
            {
                "order": 1, "title": "Utangulizi", "duration": intro_dur,
                "teacher": fmt(pick_variant(lesson_id, 1, DISCUSSION_INTRO_TEACHER)),
                "learner": fmt(pick_variant(lesson_id, 1, DISCUSSION_INTRO_LEARNER)),
                "competence": "Mawasiliano na Fikira Makini",
                "competence_integration": generate_competence_integration(lesson, "intro"),
                "lesson_description": generate_lesson_description(lesson),
                "instructional_objective": generate_instructional_objective(lesson),
                "cross_cutting_issues": generate_cross_cutting_issues(lesson),
            },
            {
                "order": 2, "title": "Somo Lenyewe", "duration": dev_dur,
                "teacher": fmt(pick_variant(lesson_id, 2, DISCUSSION_DEV_TEACHER)),
                "learner": fmt(pick_variant(lesson_id, 2, DISCUSSION_DEV_LEARNER)),
                "competence": "Fikira Makini, Mawasiliano na Kujifunza Maisha Yote",
                "competence_integration": generate_competence_integration(lesson, "development"),
            },
            {
                "order": 3, "title": "Hitimisho", "duration": conc_dur,
                "teacher": fmt(pick_variant(lesson_id, 3, DISCUSSION_CONC_TEACHER)),
                "learner": fmt(pick_variant(lesson_id, 3, DISCUSSION_CONC_LEARNER)),
                "competence": "Kujidhibiti na Mawasiliano",
                "competence_integration": generate_competence_integration(lesson, "conclusion"),
            },
        ]

    elif strategy.name == "Kazi ya Vikundi":
        return [
            {
                "order": 1, "title": "Utangulizi", "duration": intro_dur,
                "teacher": fmt(pick_variant(lesson_id, 1, GROUP_INTRO_TEACHER)),
                "learner": fmt(pick_variant(lesson_id, 1, GROUP_INTRO_LEARNER)),
                "competence": "Ushirikiano na Mawasiliano",
                "competence_integration": generate_competence_integration(lesson, "intro"),
                "lesson_description": generate_lesson_description(lesson),
                "instructional_objective": generate_instructional_objective(lesson),
                "cross_cutting_issues": generate_cross_cutting_issues(lesson),
            },
            {
                "order": 2, "title": "Somo Lenyewe", "duration": dev_dur,
                "teacher": fmt(pick_variant(lesson_id, 2, GROUP_DEV_TEACHER)),
                "learner": fmt(pick_variant(lesson_id, 2, GROUP_DEV_LEARNER)),
                "competence": "Kazi ya Timu, Kutatua Matatizo na Fikira Makini",
                "competence_integration": generate_competence_integration(lesson, "development"),
            },
            {
                "order": 3, "title": "Hitimisho", "duration": conc_dur,
                "teacher": fmt(pick_variant(lesson_id, 3, GROUP_CONC_TEACHER)),
                "learner": fmt(pick_variant(lesson_id, 3, GROUP_CONC_LEARNER)),
                "competence": "Mawasiliano, Kujifunza Maisha Yote na Kujidhibiti",
                "competence_integration": generate_competence_integration(lesson, "conclusion"),
            },
        ]

    elif strategy.name == "Kujifunza kwa Miradi":
        return [
            {
                "order": 1, "title": "Utangulizi", "duration": intro_dur,
                "teacher": fmt(pick_variant(lesson_id, 1, PROJECT_INTRO_TEACHER)),
                "learner": fmt(pick_variant(lesson_id, 1, PROJECT_INTRO_LEARNER)),
                "competence": "Fikira Makini, Mawasiliano na Ubunifu",
                "competence_integration": generate_competence_integration(lesson, "intro"),
                "lesson_description": generate_lesson_description(lesson),
                "instructional_objective": generate_instructional_objective(lesson),
                "cross_cutting_issues": generate_cross_cutting_issues(lesson),
            },
            {
                "order": 2, "title": "Somo Lenyewe", "duration": dev_dur,
                "teacher": fmt(pick_variant(lesson_id, 2, PROJECT_DEV_TEACHER)),
                "learner": fmt(pick_variant(lesson_id, 2, PROJECT_DEV_LEARNER)),
                "competence": "Kutatua Matatizo, Utafiti, Ubunifu na Ushirikiano",
                "competence_integration": generate_competence_integration(lesson, "development"),
            },
            {
                "order": 3, "title": "Hitimisho", "duration": conc_dur,
                "teacher": fmt(pick_variant(lesson_id, 3, PROJECT_CONC_TEACHER)),
                "learner": fmt(pick_variant(lesson_id, 3, PROJECT_CONC_LEARNER)),
                "competence": "Mawasiliano, Kujidhibiti na Fikira Makini",
                "competence_integration": generate_competence_integration(lesson, "conclusion"),
            },
        ]

    else:
        return [
            {"order": 1, "title": "Utangulizi", "duration": intro_dur,
             "teacher": f"Tambulisha {title} na utaje malengo ya somo.", "learner": f"Sikiliza na ujibu maswali kuhusu {title}.", "competence": "Mawasiliano"},
            {"order": 2, "title": "Somo Lenyewe", "duration": dev_dur,
             "teacher": f"Waongoze wanafunzi kupitia shughuli kuu za {title}.", "learner": f"Shiriki katika shughuli na majadiliano ya {title}.", "competence": "Fikira Makini"},
            {"order": 3, "title": "Hitimisho", "duration": conc_dur,
             "teacher": f"Fupisha pointi kuu na uimarisha: {competence}.", "learner": f"Uliza maswali na utafakari juu ya kujifunza kuhusu {title}.", "competence": "Kujidhibiti"},
        ]


# ─────────────────────────────────────────────────────────────────────────────
# MANAGEMENT COMMAND
# ─────────────────────────────────────────────────────────────────────────────

class Command(BaseCommand):
    help = "Seed Kiswahili teaching strategies and lesson steps. Skips existing steps."

    def add_arguments(self, parser):
        parser.add_argument("--clear", action="store_true", default=False)
        parser.add_argument("--lesson_id", type=int, default=None)
        parser.add_argument("--duration", type=int, default=40)

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING(
            "\n🇹🇿 Kiswahili Strategy Seeder — SKIP-EXISTING MODE\n"
            "────────────────────────────────────────────────────\n"
        ))

        if options["clear"]:
            sw_lesson_ids = Lesson.objects.filter(language='sw').values_list('id', flat=True)
            deleted, _ = LessonStrategyStep.objects.filter(lesson_id__in=sw_lesson_ids).delete()
            self.stdout.write(self.style.WARNING(f"  ⚠️  Cleared {deleted} existing sw steps.\n"))

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

        lessons_qs = Lesson.objects.filter(language='sw').select_related("unit__subject__class_field")
        if options["lesson_id"]:
            lessons_qs = lessons_qs.filter(id=options["lesson_id"])

        total_lessons = lessons_qs.count()
        if total_lessons == 0:
            self.stdout.write(self.style.ERROR(
                "  ❌ No Kiswahili lessons found. Run bulk_upload_units --language sw first."
            ))
            return

        self.stdout.write(self.style.SUCCESS(
            f"  📚 Processing {total_lessons} Kiswahili lesson(s)...\n"
        ))

        duration       = options["duration"]
        created_count  = 0
        skipped_count  = 0
        lesson_count   = 0
        strategy_list  = list(strategy_objects.values())

        existing_keys = set(
            LessonStrategyStep.objects.filter(
                lesson__language='sw'
            ).values_list("lesson_id", "strategy_id", "step_order")
        )

        for lesson in lessons_qs.order_by("unit__number", "number"):
            lesson_count += 1
            lesson_label = f"Unit {lesson.unit.number} | Somo {lesson.number}: {lesson.title}"

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

            self.stdout.write(f"       └─ {steps_created} hatua mpya zimeundwa ✓")

        self.stdout.write(self.style.SUCCESS(
            f"\n{'─'*55}\n"
            f"  ✅ Upandaji mbegu umekamilika [KISWAHILI].\n"
            f"     Masomo yaliyoshughulikiwa : {lesson_count}\n"
            f"     Masomo yaliyorukwa        : {skipped_count}\n"
            f"     Hatua zilizoundwa         : {created_count}\n"
            f"{'─'*55}\n"
        ))