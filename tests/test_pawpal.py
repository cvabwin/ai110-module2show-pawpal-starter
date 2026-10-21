from datetime import date

import pytest

from pawpal_system import CareTask, Frequency, Owner, Pet, Scheduler

DAY = date(2026, 10, 20)


def make_owner(*pets: Pet) -> Owner:
    return Owner(name="Sam", pets=list(pets))


def test_mark_complete_changes_task_status() -> None:
    task = CareTask(title="Feed", duration_minutes=10)

    task.mark_complete()

    assert task.is_complete


def test_adding_task_increases_pet_task_count() -> None:
    pet = Pet(name="Mochi", species="dog")
    task = CareTask(title="Walk", duration_minutes=20)
    initial_count = len(pet.care_tasks)

    pet.add_task(task)

    assert len(pet.care_tasks) == initial_count + 1


# --- Sorting correctness -----------------------------------------------------


def test_sort_by_time_returns_chronological_order() -> None:
    late = CareTask(title="Dinner", duration_minutes=10, start_time="18:00")
    early = CareTask(title="Breakfast", duration_minutes=10, start_time="07:30")
    mid = CareTask(title="Walk", duration_minutes=10, start_time="12:15")

    result = Scheduler.sort_by_time([late, early, mid])

    assert [t.title for t in result] == ["Breakfast", "Walk", "Dinner"]


def test_sort_by_time_puts_untimed_tasks_last_and_keeps_input_unchanged() -> None:
    untimed = CareTask(title="Groom", duration_minutes=10)
    timed = CareTask(title="Feed", duration_minutes=10, start_time="09:00")
    tasks = [untimed, timed]

    result = Scheduler.sort_by_time(tasks)

    assert result == [timed, untimed]
    assert tasks == [untimed, timed]


def test_sort_by_time_treats_unpadded_hours_as_zero_padded() -> None:
    ten = CareTask(title="Ten", duration_minutes=5, start_time="10:00")
    nine = CareTask(title="Nine", duration_minutes=5, start_time="9:05")

    result = Scheduler.sort_by_time([ten, nine])

    assert [t.title for t in result] == ["Nine", "Ten"]


def test_sort_by_time_handles_empty_list() -> None:
    assert Scheduler.sort_by_time([]) == []


# --- Recurrence logic --------------------------------------------------------


def test_completing_daily_task_creates_task_for_next_day() -> None:
    pet = Pet(name="Mochi", species="dog")
    task = CareTask(
        title="Feed",
        duration_minutes=10,
        frequency=Frequency.DAILY,
        scheduled_date=DAY,
        start_time="08:00",
    )
    pet.add_task(task)
    owner = make_owner(pet)

    next_task = Scheduler().complete_task(owner, task.id, DAY)

    assert next_task is not None
    assert next_task.scheduled_date == date(2026, 10, 21)
    assert next_task.title == "Feed"
    assert next_task.frequency is Frequency.DAILY
    assert next_task.start_time == "08:00"
    assert next_task.id != task.id
    assert next_task in pet.care_tasks


def test_completing_weekly_task_creates_task_seven_days_later() -> None:
    pet = Pet(name="Mochi", species="dog")
    task = CareTask(
        title="Bath",
        duration_minutes=30,
        frequency=Frequency.WEEKLY,
        scheduled_date=DAY,
    )
    pet.add_task(task)

    next_task = Scheduler().complete_task(make_owner(pet), task.id, DAY)

    assert next_task.scheduled_date == date(2026, 10, 27)


def test_completing_one_time_task_returns_none() -> None:
    pet = Pet(name="Mochi", species="dog")
    task = CareTask(title="Vet", duration_minutes=60)
    pet.add_task(task)

    result = Scheduler().complete_task(make_owner(pet), task.id)

    assert result is None
    assert task.is_complete
    assert len(pet.care_tasks) == 1


def test_daily_recurrence_rolls_over_year_end() -> None:
    pet = Pet(name="Mochi", species="dog")
    task = CareTask(
        title="Feed",
        duration_minutes=10,
        frequency=Frequency.DAILY,
        scheduled_date=date(2026, 12, 31),
    )
    pet.add_task(task)

    next_task = Scheduler().complete_task(
        make_owner(pet), task.id, date(2026, 12, 31)
    )

    assert next_task.scheduled_date == date(2027, 1, 1)


def test_completing_unknown_task_raises_key_error() -> None:
    with pytest.raises(KeyError):
        Scheduler().complete_task(make_owner(Pet(name="Mochi", species="dog")), "nope")


# --- Conflict detection ------------------------------------------------------


def test_detect_conflicts_flags_same_pet_duplicate_time() -> None:
    pet = Pet(name="Mochi", species="dog")
    pet.add_task(
        CareTask(title="Walk", duration_minutes=20, scheduled_date=DAY, start_time="09:00")
    )
    pet.add_task(
        CareTask(title="Feed", duration_minutes=10, scheduled_date=DAY, start_time="09:00")
    )

    warnings = Scheduler().detect_conflicts(make_owner(pet))

    assert len(warnings) == 1
    assert "same pet" in warnings[0]
    assert "09:00" in warnings[0]
    assert "Walk" in warnings[0] and "Feed" in warnings[0]


def test_detect_conflicts_flags_duplicate_time_across_pets() -> None:
    mochi = Pet(name="Mochi", species="dog")
    luna = Pet(name="Luna", species="cat")
    mochi.add_task(
        CareTask(title="Walk", duration_minutes=20, scheduled_date=DAY, start_time="09:00")
    )
    luna.add_task(
        CareTask(title="Feed", duration_minutes=10, scheduled_date=DAY, start_time="09:00")
    )

    warnings = Scheduler().detect_conflicts(make_owner(mochi, luna))

    assert len(warnings) == 1
    assert "different pets" in warnings[0]


def test_detect_conflicts_ignores_different_times_dates_and_untimed() -> None:
    pet = Pet(name="Mochi", species="dog")
    pet.add_task(
        CareTask(title="A", duration_minutes=5, scheduled_date=DAY, start_time="09:00")
    )
    pet.add_task(
        CareTask(title="B", duration_minutes=5, scheduled_date=DAY, start_time="10:00")
    )
    pet.add_task(
        CareTask(
            title="C",
            duration_minutes=5,
            scheduled_date=date(2026, 10, 21),
            start_time="09:00",
        )
    )
    pet.add_task(CareTask(title="D", duration_minutes=5, scheduled_date=DAY))
    pet.add_task(CareTask(title="E", duration_minutes=5, scheduled_date=DAY))

    assert Scheduler().detect_conflicts(make_owner(pet)) == []


def test_detect_conflicts_ignores_completed_tasks() -> None:
    pet = Pet(name="Mochi", species="dog")
    done = CareTask(
        title="Walk", duration_minutes=20, scheduled_date=DAY, start_time="09:00"
    )
    done.mark_complete()
    pet.add_task(done)
    pet.add_task(
        CareTask(title="Feed", duration_minutes=10, scheduled_date=DAY, start_time="09:00")
    )

    assert Scheduler().detect_conflicts(make_owner(pet)) == []


def test_detect_conflicts_with_no_pets_or_tasks_returns_empty_list() -> None:
    assert Scheduler().detect_conflicts(make_owner()) == []
    assert Scheduler().detect_conflicts(make_owner(Pet(name="Mochi", species="dog"))) == []


# --- Regression tests for review fixes ---------------------------------------


def _daily(pet: Pet, anchor: date = DAY) -> CareTask:
    task = CareTask(
        title="Feed", duration_minutes=10, frequency=Frequency.DAILY, scheduled_date=anchor
    )
    pet.add_task(task)
    return task


def test_complete_task_preserves_progress_on_other_dates() -> None:
    pet = Pet(name="Mochi", species="dog")
    task = _daily(pet)
    task.record_progress(5, DAY)

    Scheduler().complete_task(make_owner(pet), task.id, date(2026, 10, 21))

    assert task.completed_by_date[DAY] == 5


def test_complete_task_twice_raises() -> None:
    pet = Pet(name="Mochi", species="dog")
    task = _daily(pet)
    owner = make_owner(pet)
    Scheduler().complete_task(owner, task.id, DAY)

    with pytest.raises(ValueError):
        Scheduler().complete_task(owner, task.id, DAY)


def test_complete_task_rejects_date_when_not_due() -> None:
    pet = Pet(name="Mochi", species="dog")
    task = _daily(pet, anchor=date(2026, 11, 1))

    with pytest.raises(ValueError):
        Scheduler().complete_task(make_owner(pet), task.id, DAY)
    assert task.frequency is Frequency.DAILY


def test_complete_task_default_date_never_precedes_anchor() -> None:
    pet = Pet(name="Mochi", species="dog")
    anchor = date(2999, 1, 1)
    task = _daily(pet, anchor=anchor)

    next_task = Scheduler().complete_task(make_owner(pet), task.id)

    assert next_task.scheduled_date == date(2999, 1, 2)


def test_failed_successor_leaves_original_unchanged(monkeypatch) -> None:
    pet = Pet(name="Mochi", species="dog")
    task = _daily(pet)

    def boom(self, t):
        raise ValueError("boom")

    monkeypatch.setattr(Pet, "add_task", boom)
    with pytest.raises(ValueError):
        Scheduler().complete_task(make_owner(pet), task.id, DAY)

    assert task.frequency is Frequency.DAILY
    assert not task.completed_by_date


def test_detect_conflicts_on_date_flags_recurring_vs_one_time() -> None:
    pet = Pet(name="Mochi", species="dog")
    pet.add_task(
        CareTask(
            title="Feed",
            duration_minutes=10,
            frequency=Frequency.DAILY,
            scheduled_date=date(2026, 10, 1),
            start_time="09:00",
        )
    )
    pet.add_task(
        CareTask(title="Vet", duration_minutes=30, scheduled_date=DAY, start_time="09:00")
    )
    owner = make_owner(pet)

    assert Scheduler().detect_conflicts(owner) == []
    assert len(Scheduler().detect_conflicts(owner, DAY)) == 1
