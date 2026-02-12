from lessons.models import LessonStrategyStep


def build_strategy_steps(lesson, strategy, profile):
    """
    Fetch steps for a given lesson and strategy.
    Enforce premium restrictions already handled in view.
    Returns list of step dictionaries.
    """

    # If no lesson, return default fallback
    if not lesson:
        return _default_steps()

    # Fetch DB steps
    strategy_steps = lesson.strategy_steps.filter(
        strategy=strategy
    ).order_by("step_order")

    # If steps exist → build from DB
    if strategy_steps.exists():
        steps = []
        for idx, step in enumerate(strategy_steps, start=1):
            steps.append({
                "order": idx,
                "title": step.step_title or f"Step {idx}",
                "duration_minutes": step.duration_minutes or 5,
                "teacher_activity": step.teacher_activity or "",
                "learner_activity": step.learner_activity or ""
            })
        return steps

    # If no DB steps → fallback
    return _default_steps()


def _default_steps():
    """
    Generic 3-step fallback template.
    """
    return [
        {
            "order": 1,
            "title": "Introduction",
            "duration_minutes": 10,
            "teacher_activity": "Introduce the lesson objectives",
            "learner_activity": "Listen and respond to questions"
        },
        {
            "order": 2,
            "title": "Development",
            "duration_minutes": 25,
            "teacher_activity": "Explain and demonstrate key concepts",
            "learner_activity": "Participate in guided practice"
        },
        {
            "order": 3,
            "title": "Conclusion",
            "duration_minutes": 5,
            "teacher_activity": "Summarize key points",
            "learner_activity": "Reflect and ask questions"
        }
    ]
