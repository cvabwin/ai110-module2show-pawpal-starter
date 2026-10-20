from datetime import date, timedelta

from pawpal_system import CareTask, Owner, Pet, Scheduler


def show(label: str, tasks: list[CareTask], owner: Owner) -> None:
    print(f"\n{label}")
    for task in tasks:
        print(
            f"- {task.start_time or '--:--'} {owner.get_pet(task.pet_id).name}: "
            f"{task.title} [{task.frequency.value}, "
            f"{'done' if task.is_complete else 'open'}]"
        )


def main() -> None:
    today = date.today()
    owner = Owner(name="Jordan")
    scheduler = Scheduler()

    mochi = Pet(name="Mochi", species="dog")
    biscuit = Pet(name="Biscuit", species="cat")
    owner.add_pet(mochi)
    owner.add_pet(biscuit)

    # Tasks are deliberately added out of time order.
    mochi.add_task(CareTask("Training", 15, "medium", today, start_time="17:00"))
    mochi.add_task(
        CareTask(
            "Morning walk", 30, "high", today,
            frequency="daily", start_time="07:30",
        )
    )
    biscuit.add_task(CareTask("Feeding", 10, "high", today, start_time="08:00"))
    biscuit.add_task(CareTask("Grooming", 20, "low"))
    # Deliberate conflicts: same pet at 17:00, and across pets at 08:00.
    mochi.add_task(CareTask("Vet call", 10, "medium", today, start_time="17:00"))
    mochi.add_task(CareTask("Breakfast", 10, "high", today, start_time="08:00"))

    plan = scheduler.generate_plan(owner, today)
    print(f"Today's Schedule ({today:%B %d, %Y})")
    for item in plan.scheduled_items:
        print(
            f"- {owner.get_pet(item.task.pet_id).name}: {item.task.title} "
            f"({item.planned_minutes} min, {item.task.priority.value} priority)"
        )
    print(f"Total: {plan.total_planned_minutes}/{plan.available_minutes} minutes")

    show("All tasks sorted by time", scheduler.sort_by_time(owner.get_all_tasks()), owner)
    show("Mochi's tasks", scheduler.filter_tasks(owner, pet_name="Mochi"), owner)

    print("\nConflict warnings")
    for warning in scheduler.detect_conflicts(owner):
        print(f"! {warning}")

    walk = next(t for t in mochi.care_tasks if t.title == "Morning walk")
    next_walk = scheduler.complete_task(owner, walk.id, today)
    print(
        f"\nCompleted '{walk.title}' for {today}; next occurrence scheduled "
        f"for {next_walk.scheduled_date} (expected {today + timedelta(days=1)})"
    )
    show("Completed tasks", scheduler.filter_tasks(owner, completed=True), owner)
    show(
        "Incomplete Mochi tasks, by time",
        scheduler.sort_by_time(
            scheduler.filter_tasks(owner, pet_name="Mochi", completed=False)
        ),
        owner,
    )


if __name__ == "__main__":
    main()
