from pawpal_system import CareTask, Pet


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
