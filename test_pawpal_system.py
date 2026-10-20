from datetime import date, timedelta

import pytest

from pawpal_system import (
    CareTask,
    DailyPlan,
    Frequency,
    Owner,
    Pet,
    Priority,
    ScheduledItem,
    Scheduler,
)


def test_task_and_pet_cannot_have_multiple_owners() -> None:
    task = CareTask("Feed", 10)
    first_pet = Pet("Mochi", "dog")
    second_pet = Pet("Biscuit", "dog")
    first_pet.add_task(task)

    with pytest.raises(ValueError, match="only one pet"):
        second_pet.add_task(task)

    first_owner = Owner("Jordan")
    second_owner = Owner("Alex")
    first_owner.add_pet(first_pet)
    with pytest.raises(ValueError, match="only one owner"):
        second_owner.add_pet(first_pet)

    first_owner.remove_pet(first_pet.id)
    second_owner.add_pet(first_pet)
    assert first_pet.owner is second_owner


def test_daily_plan_accepts_only_its_candidate_tasks() -> None:
    first_task = CareTask("Feed", 10)
    other_task = CareTask("Walk", 20)
    pet = Pet("Mochi", "dog", care_tasks=[first_task])
    owner = Owner("Jordan", pets=[pet])
    plan = DailyPlan(
        date=date(2026, 10, 20),
        available_minutes=20,
        owner_id=owner.id,
        candidate_tasks=[first_task],
    )

    with pytest.raises(ValueError, match="candidate"):
        plan.add_item(ScheduledItem(other_task, 10, "test"))


def test_partial_task_requires_explicit_rescheduling() -> None:
    today = date(2026, 10, 20)
    tomorrow = today + timedelta(days=1)
    task = CareTask("Walk", 25)
    pet = Pet("Mochi", "dog", care_tasks=[task])
    owner = Owner("Jordan", pets=[pet])
    scheduler = Scheduler()

    first_plan = scheduler.generate_plan(owner, today, available_minutes=10)
    assert first_plan.scheduled_items[0].planned_minutes == 10
    assert task.scheduled_date == today
    task.record_progress(10)

    next_day_plan = scheduler.generate_plan(owner, tomorrow, available_minutes=30)
    assert next_day_plan.scheduled_items == []

    pet.edit_task(task.id, {"scheduled_date": tomorrow})
    rescheduled_plan = scheduler.generate_plan(owner, tomorrow, available_minutes=30)
    assert rescheduled_plan.scheduled_items[0].planned_minutes == 15


def test_progress_does_not_double_count_against_plan_snapshot() -> None:
    task = CareTask("Groom", 30)
    pet = Pet("Mochi", "dog", care_tasks=[task])
    owner = Owner("Jordan", pets=[pet])
    plan = Scheduler().generate_plan(
        owner, date(2026, 10, 20), available_minutes=10
    )
    item = plan.scheduled_items[0]

    task.record_progress(item.planned_minutes)

    assert item.get_remaining_task_minutes() == 20
    assert plan.get_unscheduled_tasks() == [task]


def test_nonsplittable_task_is_skipped_for_task_that_fits() -> None:
    pet = Pet(
        "Mochi",
        "dog",
        care_tasks=[
            CareTask("Long medication routine", 30, Priority.HIGH, is_splittable=False),
            CareTask("Quick meal", 10, Priority.LOW),
        ],
    )
    owner = Owner("Jordan", pets=[pet])

    plan = Scheduler().generate_plan(
        owner, date(2026, 10, 20), available_minutes=10
    )

    assert [(item.task.title, item.planned_minutes) for item in plan.scheduled_items] == [
        ("Quick meal", 10)
    ]


def test_owner_preferences_are_used_automatically() -> None:
    pet = Pet(
        "Mochi",
        "dog",
        care_tasks=[
            CareTask("Long walk", 10, Priority.HIGH),
            CareTask("Preferred meal", 4, Priority.MEDIUM),
        ],
    )
    owner = Owner(
        "Jordan",
        pets=[pet],
        preferences={"preferred_priorities": ["medium"]},
    )

    plan = Scheduler().generate_plan(
        owner, date(2026, 10, 20), available_minutes=4
    )

    assert plan.scheduled_items[0].task.title == "Preferred meal"
    assert "owner preference" in plan.scheduled_items[0].reason


def test_owner_returns_tasks_across_all_pets_and_scheduler_uses_them() -> None:
    walk = CareTask("Walk", 20, Priority.HIGH)
    feeding = CareTask("Feeding", 10, Priority.MEDIUM)
    mochi = Pet("Mochi", "dog", care_tasks=[walk])
    biscuit = Pet("Biscuit", "dog", care_tasks=[feeding])
    owner = Owner("Jordan", pets=[mochi, biscuit])

    assert owner.get_all_tasks() == [walk, feeding]
    plan = Scheduler().generate_plan(
        owner, date(2026, 10, 20), available_minutes=30
    )

    assert {item.task.id for item in plan.scheduled_items} == {
        walk.id,
        feeding.id,
    }
    assert plan.owner_id == owner.id


def test_recurring_tasks_track_completion_per_occurrence() -> None:
    first_day = date(2026, 10, 20)
    next_day = first_day + timedelta(days=1)
    daily_task = CareTask(
        "Medication",
        5,
        frequency=Frequency.DAILY,
        scheduled_date=first_day,
    )
    weekly_task = CareTask(
        "Grooming",
        15,
        frequency=Frequency.WEEKLY,
        scheduled_date=first_day,
    )
    pet = Pet("Mochi", "dog", care_tasks=[daily_task, weekly_task])
    owner = Owner("Jordan", pets=[pet])
    scheduler = Scheduler()

    first_plan = scheduler.generate_plan(owner, first_day, available_minutes=20)
    assert {item.task.id for item in first_plan.scheduled_items} == {
        daily_task.id,
        weekly_task.id,
    }
    daily_task.mark_complete(first_day)
    weekly_task.record_progress(5, first_day)

    next_day_plan = scheduler.generate_plan(owner, next_day, available_minutes=20)
    assert [item.task.id for item in next_day_plan.scheduled_items] == [
        daily_task.id
    ]
    assert next_day_plan.scheduled_items[0].planned_minutes == 5
    assert weekly_task.get_remaining_minutes(first_day) == 10
    assert daily_task.get_remaining_minutes(next_day) == 5


def test_weekly_task_requires_anchor_date() -> None:
    with pytest.raises(ValueError, match="anchor"):
        CareTask("Grooming", 15, frequency="weekly")
