"""
Management Command: seed_strategies_per_lesson (VARIANT POOL EDITION)
======================================================================
CBC Lesson Plan Generator – Professional Strategy Seeder with Unique Content
-----------------------------------------------------------------------------
Seeds 3 strategies per lesson with DETERMINISTIC VARIANT POOL.
Each lesson gets unique phrasing while maintaining professional quality.

Strategies:
  1. Discussion Method         (FREE)
  2. Group Collaborative Work  (FREE)
  3. Project-Based Learning    (PREMIUM)

Each lesson gets 3 steps per strategy:
  - Introduction  (20% duration)
  - Development   (60% duration)
  - Conclusion    (20% duration)

VARIANT POOL SYSTEM:
  - 3-5 sentence variants per step type
  - Deterministic selection based on lesson_id (same lesson = same variant always)
  - Every lesson across 250+ lessons reads uniquely
  - Zero AI cost, instant generation

Step content is generated from:
  - lesson.title
  - unit.key_unit_competence
  - unit.title
  - strategy pedagogical pattern
  - deterministic variant selection

Usage:
  python manage.py seed_strategies_per_lesson
  python manage.py seed_strategies_per_lesson --clear   # wipe and reseed
  python manage.py seed_strategies_per_lesson --lesson_id 5  # single lesson
"""

from django.core.management.base import BaseCommand
from lessons.models import (
    Lesson,
    TeachingStrategy,
    LessonStrategyStep,
)


# ─────────────────────────────────────────────────────────────────────────────
# STRATEGY DEFINITIONS
# 3 strategies: 2 free, 1 premium
# ─────────────────────────────────────────────────────────────────────────────

STRATEGIES = [
    {
        "name": "Discussion Method",
        "description": (
            "Teacher facilitates structured classroom discussion, activating "
            "prior knowledge and guiding learners to construct understanding "
            "through questioning and peer interaction."
        ),
        "is_premium_only": False,
        "is_active": True,
    },
    {
        "name": "Group Collaborative Work",
        "description": (
            "Learners work in small groups to investigate, solve problems, "
            "and present findings. Teacher circulates as a facilitator, "
            "promoting teamwork and communication competences."
        ),
        "is_premium_only": False,
        "is_active": True,
    },
    {
        "name": "Project-Based Learning",
        "description": (
            "Premium strategy. Learners design and build real-world solutions "
            "tied to the unit competence. Teacher coaches and evaluates through "
            "observation and structured feedback sessions."
        ),
        "is_premium_only": True,
        "is_active": True,
    },
]


# ─────────────────────────────────────────────────────────────────────────────
# DETERMINISTIC VARIANT SELECTOR
# Uses lesson_id as seed to pick consistent variant per lesson
# ─────────────────────────────────────────────────────────────────────────────

def pick_variant(lesson_id, step_order, variants):
    """
    Deterministically select one variant from a list.
    Same lesson_id + step_order = same variant always.
    Different lessons get different variants.
    """
    index = (lesson_id * 7 + step_order * 3) % len(variants)
    return variants[index]


# ─────────────────────────────────────────────────────────────────────────────
# VARIANT POOLS — Multiple professional phrasings per step type
# ─────────────────────────────────────────────────────────────────────────────

# ══════════════════════════════════════════════════════════════════════════════
# DISCUSSION METHOD VARIANTS
# ══════════════════════════════════════════════════════════════════════════════

DISCUSSION_INTRO_TEACHER = [
    (
        "Welcome learners and introduce the topic: {title}. "
        "Pose open-ended questions to activate prior knowledge about {unit_title}. "
        "State the lesson objective aligned to: {competence}."
    ),
    (
        "Begin the lesson by reviewing what learners already know about {unit_title}. "
        "Connect prior knowledge to today's focus on {title}. "
        "Clearly state how this lesson contributes to: {competence}."
    ),
    (
        "Display a visual or pose a real-world scenario related to {title}. "
        "Ask learners what they observe and how it connects to {unit_title}. "
        "Introduce the lesson objective tied to: {competence}."
    ),
    (
        "Start with a think-pair-share prompt about {title}. "
        "Allow learners to discuss their initial ideas before sharing with the class. "
        "Outline how this lesson builds toward: {competence}."
    ),
]

DISCUSSION_INTRO_LEARNER = [
    (
        "Listen attentively and respond to the teacher's questions. "
        "Share what they already know about {title} and connect ideas "
        "from previous lessons."
    ),
    (
        "Engage with the visual or scenario presented. "
        "Discuss initial thoughts with a partner before contributing to the class discussion about {title}."
    ),
    (
        "Reflect on prior lessons related to {unit_title}. "
        "Ask clarifying questions and prepare to build new understanding about {title}."
    ),
    (
        "Participate in the think-pair-share activity. "
        "Share observations and prior knowledge related to {title} with peers and the teacher."
    ),
]

DISCUSSION_DEV_TEACHER = [
    (
        "Facilitate a structured whole-class and pair discussion on key concepts "
        "of {title}. Use probing questions to deepen understanding of {competence}. "
        "Write key points on the board and guide learners to draw conclusions."
    ),
    (
        "Present 2-3 guiding questions related to {title}. "
        "Encourage learners to discuss answers in small groups before sharing with the class. "
        "Synthesize contributions and correct misconceptions related to {competence}."
    ),
    (
        "Use a Socratic questioning approach to explore {title} in depth. "
        "Challenge learners to justify their reasoning and build on each other's ideas. "
        "Document key insights on the board and relate them to {competence}."
    ),
    (
        "Divide the class into debate teams on a controversial or open-ended question about {title}. "
        "Moderate the debate and ensure all sides are heard. "
        "Summarize how the debate deepens understanding of {competence}."
    ),
]

DISCUSSION_DEV_LEARNER = [
    (
        "Participate actively in the discussion by sharing ideas, asking questions, "
        "and building on peers' contributions. Take notes on key concepts of {title} "
        "and relate them to real-life applications."
    ),
    (
        "Work in pairs or small groups to discuss the guiding questions on {title}. "
        "Listen to others' perspectives and refine their own understanding before presenting to the class."
    ),
    (
        "Engage in Socratic dialogue by answering questions and challenging assumptions. "
        "Collaborate with peers to co-construct deeper understanding of {title}."
    ),
    (
        "Participate in the debate by researching and defending a position on {title}. "
        "Listen respectfully to opposing views and adjust thinking based on evidence."
    ),
]

DISCUSSION_CONC_TEACHER = [
    (
        "Summarise the key points from the discussion on {title}. "
        "Reinforce the unit competence: {competence}. "
        "Assign a short reflection task or homework."
    ),
    (
        "Ask learners to share one new insight they gained about {title}. "
        "Connect these insights back to {competence}. "
        "Provide a brief homework task to consolidate learning."
    ),
    (
        "Display the main conclusions reached during the discussion on {title}. "
        "Clarify any remaining misconceptions and emphasize how this builds {competence}. "
        "Set expectations for the next lesson."
    ),
    (
        "Facilitate a quick exit ticket activity where learners write down the most important "
        "concept they learned about {title}. Review responses and reinforce {competence}."
    ),
]

DISCUSSION_CONC_LEARNER = [
    (
        "Reflect on what was learned about {title}. "
        "Ask any remaining questions and note the teacher's summary. "
        "Record homework or follow-up tasks in their exercise books."
    ),
    (
        "Share one key takeaway from the lesson on {title} with the class. "
        "Write down homework and prepare questions for the next lesson."
    ),
    (
        "Review the summary provided by the teacher on {title}. "
        "Ask for clarification on any confusing points and ensure understanding of {competence}."
    ),
    (
        "Complete the exit ticket by writing their main learning point about {title}. "
        "Submit it to the teacher and note any follow-up activities assigned."
    ),
]


# ══════════════════════════════════════════════════════════════════════════════
# GROUP COLLABORATIVE WORK VARIANTS
# ══════════════════════════════════════════════════════════════════════════════

GROUP_INTRO_TEACHER = [
    (
        "Set the context for {title} by briefly explaining the activity objectives. "
        "Divide learners into groups of 4–5 and distribute task sheets "
        "aligned to {competence}. "
        "Clarify roles: facilitator, recorder, presenter, timekeeper."
    ),
    (
        "Introduce the group challenge related to {title}. "
        "Form balanced groups and assign each a specific task or question aligned to {competence}. "
        "Explain the expected deliverable and timeline."
    ),
    (
        "Display the learning outcomes for {title} and explain how group work will help achieve {competence}. "
        "Organize learners into heterogeneous groups and distribute resources or case studies."
    ),
    (
        "Present a problem scenario related to {title}. "
        "Assign learners to collaborative teams and outline the investigation process tied to {competence}."
    ),
]

GROUP_INTRO_LEARNER = [
    (
        "Move into assigned groups and read the task instructions. "
        "Clarify any questions about the activity on {title}. "
        "Agree on roles within the group."
    ),
    (
        "Form groups and review the challenge or question assigned on {title}. "
        "Discuss initial ideas and assign roles: leader, note-taker, timekeeper, presenter."
    ),
    (
        "Join their assigned group and review the learning outcomes for {title}. "
        "Read the task sheet and clarify expectations with the teacher if needed."
    ),
    (
        "Organize into teams and examine the problem scenario related to {title}. "
        "Brainstorm initial solutions and delegate tasks among group members."
    ),
]

GROUP_DEV_TEACHER = [
    (
        "Move between groups to monitor progress and provide targeted guidance "
        "on {title}. Ask probing questions to deepen group discussions. "
        "Ensure all groups stay focused on achieving {competence}. "
        "Note observations for feedback during conclusion."
    ),
    (
        "Circulate among groups and listen to discussions on {title}. "
        "Provide hints or resources when groups are stuck. "
        "Encourage quieter learners to contribute and keep groups on task toward {competence}."
    ),
    (
        "Act as a facilitator by visiting each group and asking accountability questions about {title}. "
        "Redirect groups that drift off-topic and ensure equitable participation toward {competence}."
    ),
    (
        "Observe group dynamics and intervene when collaboration breaks down. "
        "Model problem-solving techniques when groups face challenges with {title}. "
        "Reinforce time management and focus on achieving {competence}."
    ),
]

GROUP_DEV_LEARNER = [
    (
        "Collaborate to investigate, solve tasks, and discuss concepts related "
        "to {title}. The recorder documents findings while the facilitator "
        "keeps the group on task. Prepare a short group presentation of key "
        "findings to share with the class."
    ),
    (
        "Work together to analyze information and solve the assigned problem on {title}. "
        "Discuss different perspectives and reach consensus. "
        "Prepare visual aids or a brief report to present findings."
    ),
    (
        "Engage in collaborative inquiry about {title}. "
        "Divide subtasks among group members and synthesize findings. "
        "Practice presenting the group's conclusions before the final presentation."
    ),
    (
        "Investigate the problem scenario related to {title} using provided resources. "
        "Test hypotheses and refine solutions collaboratively. "
        "Document the problem-solving process for presentation."
    ),
]

GROUP_CONC_TEACHER = [
    (
        "Invite 1–2 groups to present their findings on {title}. "
        "Offer constructive feedback and correct any misconceptions. "
        "Consolidate learning by restating the key competence: {competence}."
    ),
    (
        "Facilitate a gallery walk where groups display their work on {title}. "
        "Lead a whole-class discussion on common themes and differences. "
        "Summarize how group work reinforced {competence}."
    ),
    (
        "Ask each group to share one key insight about {title} in 30 seconds. "
        "Identify strong examples and areas for improvement. "
        "Connect all presentations back to the unit competence: {competence}."
    ),
    (
        "Select 2-3 groups to present and invite peer feedback on their work on {title}. "
        "Highlight excellent collaboration and reinforce how the activity built {competence}."
    ),
]

GROUP_CONC_LEARNER = [
    (
        "Group presenters share key findings on {title}. "
        "Other learners listen, take notes, and ask follow-up questions. "
        "Reflect individually on what the group activity added to their "
        "understanding."
    ),
    (
        "Participate in the gallery walk by viewing other groups' work on {title}. "
        "Ask questions and compare approaches. "
        "Write a brief reflection on what they learned from peers."
    ),
    (
        "Listen to peer presentations on {title} and identify similarities and differences. "
        "Provide respectful feedback when prompted by the teacher. "
        "Summarize personal learning in their notebooks."
    ),
    (
        "Present group findings on {title} if selected. "
        "Listen attentively to peer feedback and refine understanding based on class discussion."
    ),
]


# ══════════════════════════════════════════════════════════════════════════════
# PROJECT-BASED LEARNING VARIANTS (PREMIUM)
# ══════════════════════════════════════════════════════════════════════════════

PROJECT_INTRO_TEACHER = [
    (
        "Introduce the project brief for {title}. "
        "Explain the driving question aligned to {competence} and the "
        "real-world context of {unit_title}. "
        "Outline deliverables, milestones, and success criteria. "
        "Assign project teams and distribute resource materials."
    ),
    (
        "Present a real-world problem related to {title} that requires a project solution. "
        "Connect the challenge to {competence} and explain how learners will demonstrate mastery. "
        "Form project teams and provide access to tools, templates, or research materials."
    ),
    (
        "Launch the project by showing an exemplar solution related to {title}. "
        "Discuss what makes it effective and how it demonstrates {competence}. "
        "Assign teams and clarify the project timeline and checkpoints."
    ),
    (
        "Engage learners with a multimedia introduction to the project theme on {title}. "
        "Explain the authentic audience who will benefit from their work. "
        "Organize teams and distribute the project rubric aligned to {competence}."
    ),
]

PROJECT_INTRO_LEARNER = [
    (
        "Review the project brief for {title} and ask clarifying questions. "
        "Understand the expected deliverable and how it connects to {competence}. "
        "Form teams, assign roles, and begin initial project planning."
    ),
    (
        "Read the real-world problem statement related to {title}. "
        "Discuss with teammates how to approach the challenge and what skills are needed. "
        "Review the project rubric and success criteria tied to {competence}."
    ),
    (
        "Examine the exemplar solution for {title} and identify key features. "
        "Brainstorm initial ideas with their team and outline a project plan."
    ),
    (
        "Watch the multimedia introduction to the project theme on {title}. "
        "Discuss with teammates who the authentic audience is and what they need. "
        "Begin defining roles and drafting a project timeline."
    ),
]

PROJECT_DEV_TEACHER = [
    (
        "Coach individual teams as they design and build their solution for {title}. "
        "Provide formative feedback on progress and redirect teams that deviate "
        "from the competence goal: {competence}. "
        "Model problem-solving techniques and prompt deeper inquiry."
    ),
    (
        "Conduct check-in conferences with each team to assess progress on {title}. "
        "Ask probing questions that push learners to refine their work toward {competence}. "
        "Provide just-in-time instruction on technical skills or content knowledge."
    ),
    (
        "Facilitate peer critique sessions where teams share work-in-progress on {title}. "
        "Guide learners to give constructive feedback aligned to the project rubric. "
        "Ensure all teams are on track to demonstrate {competence}."
    ),
    (
        "Observe teams as they research, prototype, and test solutions for {title}. "
        "Intervene when teams face obstacles by asking guiding questions rather than providing answers. "
        "Monitor alignment with {competence} and adjust support as needed."
    ),
]

PROJECT_DEV_LEARNER = [
    (
        "Research, design, and develop their project solution related to {title}. "
        "Collaborate within teams, make decisions, test ideas, and refine the "
        "solution to meet the requirements of {competence}. "
        "Document progress in a project logbook."
    ),
    (
        "Engage in iterative cycles of building, testing, and revising their solution for {title}. "
        "Seek feedback from the teacher and peers during check-ins. "
        "Ensure the project demonstrates mastery of {competence}."
    ),
    (
        "Participate in peer critique by presenting work-in-progress on {title}. "
        "Listen to feedback and use it to improve the project. "
        "Continuously align work with the rubric and {competence}."
    ),
    (
        "Conduct research and gather data to inform their project on {title}. "
        "Prototype multiple solutions and select the most effective approach. "
        "Collaborate closely to meet milestones and achieve {competence}."
    ),
]

PROJECT_CONC_TEACHER = [
    (
        "Facilitate project presentations or demonstrations on {title}. "
        "Evaluate each team using a rubric aligned to {competence}. "
        "Provide structured feedback and highlight best practices observed. "
        "Connect the project outcomes back to the unit competence."
    ),
    (
        "Host a project exhibition where teams showcase their solutions for {title}. "
        "Invite peer and self-assessment using the project rubric. "
        "Summarize common successes and growth areas in demonstrating {competence}."
    ),
    (
        "Conduct final presentations where teams pitch their solutions to an authentic audience. "
        "Use a rubric to assess both the product and the presentation related to {title}. "
        "Celebrate achievements and reinforce how the project built {competence}."
    ),
    (
        "Organize a reflection session where teams discuss what they learned about {title}. "
        "Use the rubric to provide individual and team feedback. "
        "Highlight how the project process developed {competence}."
    ),
]

PROJECT_CONC_LEARNER = [
    (
        "Present or demonstrate their completed project on {title} to the class. "
        "Respond to questions from the teacher and peers. "
        "Reflect on the project experience and write a brief self-assessment "
        "on how well they achieved {competence}."
    ),
    (
        "Showcase their project solution for {title} at the exhibition. "
        "Engage with peers reviewing their work and explain design decisions. "
        "Complete a self-assessment using the project rubric aligned to {competence}."
    ),
    (
        "Deliver a final pitch presentation on their solution for {title} to the authentic audience. "
        "Answer questions and defend design choices. "
        "Reflect in writing on how the project helped them develop {competence}."
    ),
    (
        "Participate in the reflection session by sharing lessons learned about {title}. "
        "Review peer and teacher feedback on their project. "
        "Document personal growth in achieving {competence} in their project logbook."
    ),
]


# ─────────────────────────────────────────────────────────────────────────────
# STEP TEMPLATE ENGINE WITH VARIANT POOL
# Generates 3 steps per (lesson, strategy) using competence + lesson title + variants
# Duration split: 20% / 60% / 20%
# ─────────────────────────────────────────────────────────────────────────────

def generate_steps(lesson, strategy, total_duration=40):
    """
    Returns a list of 3 step dicts for (lesson × strategy).
    Content is driven by lesson.title, unit.key_unit_competence, and VARIANT POOL.
    Duration is split proportionally: 20/60/20.
    Uses deterministic selection so same lesson = same variant always.
    """

    title = lesson.title
    unit = lesson.unit
    competence = getattr(unit, "key_unit_competence", f"understand {title}")
    unit_title = getattr(unit, "title", title)
    strategy_name = strategy.name
    lesson_id = lesson.id

    # Duration calculation (20 / 60 / 20 percent)
    intro_dur = round(total_duration * 0.20)
    dev_dur = round(total_duration * 0.60)
    conc_dur = total_duration - intro_dur - dev_dur  # absorb rounding remainder

    # Format helper
    def fmt(template):
        return template.format(
            title=title,
            unit_title=unit_title,
            competence=competence
        )

    # ── DISCUSSION METHOD ─────────────────────────────────────────────────────
    if strategy_name == "Discussion Method":
        return [
            {
                "order": 1,
                "title": "Introduction",
                "duration": intro_dur,
                "teacher": fmt(pick_variant(lesson_id, 1, DISCUSSION_INTRO_TEACHER)),
                "learner": fmt(pick_variant(lesson_id, 1, DISCUSSION_INTRO_LEARNER)),
                "competence": "Communication and Critical Thinking",
            },
            {
                "order": 2,
                "title": "Development",
                "duration": dev_dur,
                "teacher": fmt(pick_variant(lesson_id, 2, DISCUSSION_DEV_TEACHER)),
                "learner": fmt(pick_variant(lesson_id, 2, DISCUSSION_DEV_LEARNER)),
                "competence": "Critical Thinking, Communication, and Lifelong Learning",
            },
            {
                "order": 3,
                "title": "Conclusion",
                "duration": conc_dur,
                "teacher": fmt(pick_variant(lesson_id, 3, DISCUSSION_CONC_TEACHER)),
                "learner": fmt(pick_variant(lesson_id, 3, DISCUSSION_CONC_LEARNER)),
                "competence": "Self-Regulation and Communication",
            },
        ]

    # ── GROUP COLLABORATIVE WORK ──────────────────────────────────────────────
    elif strategy_name == "Group Collaborative Work":
        return [
            {
                "order": 1,
                "title": "Introduction",
                "duration": intro_dur,
                "teacher": fmt(pick_variant(lesson_id, 1, GROUP_INTRO_TEACHER)),
                "learner": fmt(pick_variant(lesson_id, 1, GROUP_INTRO_LEARNER)),
                "competence": "Cooperation and Communication",
            },
            {
                "order": 2,
                "title": "Development",
                "duration": dev_dur,
                "teacher": fmt(pick_variant(lesson_id, 2, GROUP_DEV_TEACHER)),
                "learner": fmt(pick_variant(lesson_id, 2, GROUP_DEV_LEARNER)),
                "competence": "Teamwork, Problem-Solving, and Critical Thinking",
            },
            {
                "order": 3,
                "title": "Conclusion",
                "duration": conc_dur,
                "teacher": fmt(pick_variant(lesson_id, 3, GROUP_CONC_TEACHER)),
                "learner": fmt(pick_variant(lesson_id, 3, GROUP_CONC_LEARNER)),
                "competence": "Communication, Lifelong Learning, and Self-Regulation",
            },
        ]

    # ── PROJECT-BASED LEARNING (PREMIUM) ─────────────────────────────────────
    elif strategy_name == "Project-Based Learning":
        return [
            {
                "order": 1,
                "title": "Introduction",
                "duration": intro_dur,
                "teacher": fmt(pick_variant(lesson_id, 1, PROJECT_INTRO_TEACHER)),
                "learner": fmt(pick_variant(lesson_id, 1, PROJECT_INTRO_LEARNER)),
                "competence": "Critical Thinking, Communication, and Creativity",
            },
            {
                "order": 2,
                "title": "Development",
                "duration": dev_dur,
                "teacher": fmt(pick_variant(lesson_id, 2, PROJECT_DEV_TEACHER)),
                "learner": fmt(pick_variant(lesson_id, 2, PROJECT_DEV_LEARNER)),
                "competence": "Problem-Solving, Research, Creativity, and Collaboration",
            },
            {
                "order": 3,
                "title": "Conclusion",
                "duration": conc_dur,
                "teacher": fmt(pick_variant(lesson_id, 3, PROJECT_CONC_TEACHER)),
                "learner": fmt(pick_variant(lesson_id, 3, PROJECT_CONC_LEARNER)),
                "competence": "Communication, Self-Regulation, and Critical Thinking",
            },
        ]

    # ── FALLBACK (should never trigger)
    else:
        return [
            {
                "order": 1,
                "title": "Introduction",
                "duration": intro_dur,
                "teacher": f"Introduce {title} and state lesson objectives.",
                "learner": f"Listen and respond to introductory questions about {title}.",
                "competence": "Communication",
            },
            {
                "order": 2,
                "title": "Development",
                "duration": dev_dur,
                "teacher": f"Guide learners through key activities on {title}.",
                "learner": f"Participate in guided activities and discussions on {title}.",
                "competence": "Critical Thinking",
            },
            {
                "order": 3,
                "title": "Conclusion",
                "duration": conc_dur,
                "teacher": f"Summarise key points and reinforce: {competence}.",
                "learner": f"Ask questions and reflect on learning about {title}.",
                "competence": "Self-Regulation",
            },
        ]


# ─────────────────────────────────────────────────────────────────────────────
# MANAGEMENT COMMAND
# ─────────────────────────────────────────────────────────────────────────────

class Command(BaseCommand):
    help = (
        "Seed professional teaching strategies and lesson steps with VARIANT POOL. "
        "Each lesson gets unique phrasing driven by key_unit_competence and deterministic selection."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--clear",
            action="store_true",
            default=False,
            help="Delete all existing LessonStrategyStep records before reseeding.",
        )
        parser.add_argument(
            "--lesson_id",
            type=int,
            default=None,
            help="Seed steps for a single lesson ID only.",
        )
        parser.add_argument(
            "--duration",
            type=int,
            default=40,
            help="Default lesson duration in minutes (default: 40).",
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING(
            "\n🔥 CBC Strategy Seeder — VARIANT POOL EDITION\n"
            "─────────────────────────────────────────────────────\n"
            "Each lesson gets unique content via deterministic variant selection.\n"
        ))

        # ── Optional: clear all existing steps
        if options["clear"]:
            deleted, _ = LessonStrategyStep.objects.all().delete()
            self.stdout.write(self.style.WARNING(
                f"  ⚠️  Cleared {deleted} existing LessonStrategyStep records.\n"
            ))

        # ── Upsert strategies
        strategy_objects = {}
        for s_def in STRATEGIES:
            strategy, created = TeachingStrategy.objects.update_or_create(
                name=s_def["name"],
                defaults={
                    "description": s_def["description"],
                    "is_premium_only": s_def["is_premium_only"],
                    "is_active": s_def["is_active"],
                },
            )
            strategy_objects[s_def["name"]] = strategy
            status = "✅ Created" if created else "🔄 Updated"
            tier = "PREMIUM" if s_def["is_premium_only"] else "FREE"
            self.stdout.write(f"  {status} strategy [{tier}]: {strategy.name}")

        self.stdout.write("")

        # ── Fetch lessons
        lessons_qs = Lesson.objects.select_related("unit__subject__class_field")
        if options["lesson_id"]:
            lessons_qs = lessons_qs.filter(id=options["lesson_id"])
            if not lessons_qs.exists():
                self.stdout.write(self.style.ERROR(
                    f"  ❌ No lesson found with id={options['lesson_id']}"
                ))
                return

        total_lessons = lessons_qs.count()
        if total_lessons == 0:
            self.stdout.write(self.style.ERROR(
                "  ❌ No lessons found in database. "
                "Run bulk_upload_units or seed_full_computer first."
            ))
            return

        self.stdout.write(self.style.SUCCESS(
            f"  📚 Seeding steps for {total_lessons} lesson(s) × "
            f"{len(STRATEGIES)} strategies × 3 steps each...\n"
        ))

        duration = options["duration"]
        created_count = 0
        skipped_count = 0
        lesson_count = 0

        # ── Main loop: lesson × strategy
        for lesson in lessons_qs.order_by("unit__number", "number"):
            lesson_count += 1
            lesson_label = (
                f"Unit {lesson.unit.number} | Lesson {lesson.number}: {lesson.title}"
            )
            self.stdout.write(f"  📖 [{lesson_count}/{total_lessons}] {lesson_label}")

            for strategy in strategy_objects.values():
                steps = generate_steps(lesson, strategy, total_duration=duration)

                for step in steps:
                    _, step_created = LessonStrategyStep.objects.update_or_create(
                        lesson=lesson,
                        strategy=strategy,
                        step_order=step["order"],
                        defaults={
                            "step_title": step["title"],
                            "duration_minutes": step["duration"],
                            "teacher_activity": step["teacher"],
                            "learner_activity": step["learner"],
                            "generic_competence": step["competence"],
                        },
                    )
                    if step_created:
                        created_count += 1
                    else:
                        skipped_count += 1

            self.stdout.write(
                f"       └─ 3 strategies × 3 steps seeded (unique per lesson) ✓"
            )

        # ── Summary
        self.stdout.write(self.style.SUCCESS(
            f"\n{'─' * 60}\n"
            f"  ✅ Seeding complete (VARIANT POOL MODE).\n"
            f"     Lessons processed : {lesson_count}\n"
            f"     Steps created     : {created_count}\n"
            f"     Steps updated     : {skipped_count}\n"
            f"     Total steps in DB : {created_count + skipped_count}\n"
            f"     Unique variants   : 4 per step type × 9 steps = 36 variations\n"
            f"{'─' * 60}\n"
        ))
