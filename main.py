from datetime import date

from pawpal_system import CareTask, Owner, Pet, Scheduler


def main() -> None:
    today = date.today()
    owner = Owner(name="Jordan")

    mochi = Pet(name="Mochi", species="dog")
    biscuit = Pet(name="Biscuit", species="cat")
    owner.add_pet(mochi)
    owner.add_pet(biscuit)

    mochi.add_task(
        CareTask(
            title="Morning walk",
            duration_minutes=30,
            priority="high",
        )
    )
    mochi.add_task(
        CareTask(
            title="Training",
            duration_minutes=15,
            priority="medium",
        )
    )
    biscuit.add_task(
        CareTask(
            title="Feeding",
            duration_minutes=10,
            priority="high",
        )
    )

    plan = Scheduler().generate_plan(owner, today)
    print(f"Today's Schedule ({today:%B %d, %Y})")
    for item in plan.scheduled_items:
        pet = next(
            pet for pet in owner.pets if pet.id == item.task.pet_id
        )
        print(
            f"- {pet.name}: {item.task.title} "
            f"({item.planned_minutes} min, {item.task.priority.value} priority)"
        )
    print(f"Total: {plan.total_planned_minutes}/{plan.available_minutes} minutes")


if __name__ == "__main__":
    main()
