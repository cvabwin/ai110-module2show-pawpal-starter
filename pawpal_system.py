"""Backend models and scheduling logic for PawPal+."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from enum import Enum
from math import sqrt
from typing import Mapping, Optional, Sequence
from uuid import uuid4


DEFAULT_AVAILABLE_MINUTES = 120
MAX_TASK_DURATION_MINUTES = 240


class Priority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass
class CareTask:
    title: str
    duration_minutes: int
    priority: Priority | str = Priority.MEDIUM
    scheduled_date: Optional[date] = None
    completed_minutes: int = 0
    id: str = field(default_factory=lambda: uuid4().hex)

    def __post_init__(self) -> None:
        self.title = self._validate_title(self.title)
        self.duration_minutes = self._validate_duration(self.duration_minutes)
        self.priority = self._validate_priority(self.priority)
        self.completed_minutes = self._validate_completed_minutes(
            self.completed_minutes, self.duration_minutes
        )
        if not isinstance(self.id, str) or not self.id.strip():
            raise ValueError("Task ID must not be blank")
        self.scheduled_date = self._validate_scheduled_date(self.scheduled_date)

    @staticmethod
    def _validate_title(title: object) -> str:
        if not isinstance(title, str) or not title.strip():
            raise ValueError("Task title must not be blank")
        return title.strip()

    @staticmethod
    def _validate_duration(duration_minutes: object) -> int:
        if isinstance(duration_minutes, bool) or not isinstance(
            duration_minutes, int
        ):
            raise TypeError("Task duration must be an integer number of minutes")
        if not 1 <= duration_minutes <= MAX_TASK_DURATION_MINUTES:
            raise ValueError(
                f"Task duration must be between 1 and "
                f"{MAX_TASK_DURATION_MINUTES} minutes"
            )
        return duration_minutes

    @staticmethod
    def _validate_priority(priority: object) -> Priority:
        try:
            if isinstance(priority, str):
                return Priority(priority.lower())
            if isinstance(priority, Priority):
                return priority
        except ValueError as error:
            raise ValueError("Priority must be low, medium, or high") from error
        raise ValueError("Priority must be low, medium, or high")

    @staticmethod
    def _validate_completed_minutes(minutes: object, duration: int) -> int:
        if isinstance(minutes, bool) or not isinstance(minutes, int):
            raise TypeError("Completed minutes must be an integer")
        if not 0 <= minutes <= duration:
            raise ValueError("Completed minutes must be between 0 and task duration")
        return minutes

    @staticmethod
    def _validate_scheduled_date(value: object) -> Optional[date]:
        if value is not None and not isinstance(value, date):
            raise TypeError("scheduled_date must be a date or None")
        return value

    @property
    def is_complete(self) -> bool:
        return self.completed_minutes == self.duration_minutes

    def update_details(self, updates: Mapping[str, object]) -> None:
        allowed_fields = {"title", "duration_minutes", "priority", "scheduled_date"}
        unexpected_fields = set(updates) - allowed_fields
        if unexpected_fields:
            names = ", ".join(sorted(unexpected_fields))
            raise ValueError(f"Cannot update task field(s): {names}")

        new_title = self.title
        new_duration = self.duration_minutes
        new_priority = self.priority
        new_scheduled_date = self.scheduled_date

        if "title" in updates:
            new_title = self._validate_title(updates["title"])
        if "duration_minutes" in updates:
            new_duration = self._validate_duration(updates["duration_minutes"])
        if "priority" in updates:
            new_priority = self._validate_priority(updates["priority"])
        if "scheduled_date" in updates:
            new_scheduled_date = self._validate_scheduled_date(
                updates["scheduled_date"]
            )

        if self.completed_minutes > new_duration:
            raise ValueError("New duration cannot be less than completed minutes")

        self.title = new_title
        self.duration_minutes = new_duration
        self.priority = new_priority
        self.scheduled_date = new_scheduled_date

    def mark_complete(self) -> None:
        self.completed_minutes = self.duration_minutes

    def record_progress(self, minutes: int) -> None:
        if isinstance(minutes, bool) or not isinstance(minutes, int):
            raise TypeError("Progress must be an integer number of minutes")
        if minutes <= 0:
            raise ValueError("Progress must be greater than zero")
        if minutes > self.get_remaining_minutes():
            raise ValueError("Progress cannot exceed the task's remaining duration")
        self.completed_minutes += minutes

    def get_remaining_minutes(self) -> int:
        return self.duration_minutes - self.completed_minutes


@dataclass
class Pet:
    name: str
    species: str
    breed: Optional[str] = None
    date_of_birth: Optional[date] = None
    weight: Optional[float] = None
    allergies: list[str] = field(default_factory=list)
    medical_conditions: list[str] = field(default_factory=list)
    care_tasks: list[CareTask] = field(default_factory=list)
    id: str = field(default_factory=lambda: uuid4().hex)

    def __post_init__(self) -> None:
        self.name = self._validate_text(self.name, "Pet name")
        self.species = self._validate_text(self.species, "Species").lower()
        if self.breed is not None:
            self.breed = self._validate_text(self.breed, "Breed")
        if self.date_of_birth is not None and not isinstance(
            self.date_of_birth, date
        ):
            raise TypeError("date_of_birth must be a date or None")
        if self.weight is not None:
            if isinstance(self.weight, bool) or not isinstance(
                self.weight, (int, float)
            ):
                raise TypeError("Weight must be a number or None")
            if self.weight <= 0:
                raise ValueError("Weight must be greater than zero")
            self.weight = float(self.weight)
        self.allergies = self._validate_text_list(self.allergies, "Allergies")
        self.medical_conditions = self._validate_text_list(
            self.medical_conditions, "Medical conditions"
        )
        if any(not isinstance(task, CareTask) for task in self.care_tasks):
            raise TypeError("care_tasks must contain CareTask objects")
        if any(task.id == "" for task in self.care_tasks):
            raise ValueError("Task IDs must not be blank")

    @staticmethod
    def _validate_text(value: str, label: str) -> str:
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{label} must not be blank")
        return value.strip()

    @classmethod
    def _validate_text_list(cls, values: Sequence[str], label: str) -> list[str]:
        if isinstance(values, (str, bytes)):
            raise TypeError(f"{label} must be a list of text values")
        return [cls._validate_text(value, label) for value in values]

    def add_task(self, task: CareTask) -> None:
        if not isinstance(task, CareTask):
            raise TypeError("task must be a CareTask")
        if any(existing.id == task.id for existing in self.care_tasks):
            raise ValueError(f"Task ID already exists for this pet: {task.id}")
        self.care_tasks.append(task)

    def edit_task(self, task_id: str, updates: Mapping[str, object]) -> None:
        self._get_task(task_id).update_details(updates)

    def remove_task(self, task_id: str) -> None:
        task = self._get_task(task_id)
        self.care_tasks.remove(task)

    def get_tasks_for_day(self, task_date: date) -> list[CareTask]:
        if not isinstance(task_date, date):
            raise TypeError("task_date must be a date")
        return [
            task
            for task in self.care_tasks
            if not task.is_complete
            and (task.scheduled_date is None or task.scheduled_date == task_date)
        ]

    def _get_task(self, task_id: str) -> CareTask:
        for task in self.care_tasks:
            if task.id == task_id:
                return task
        raise KeyError(f"No task found with ID: {task_id}")


@dataclass
class Owner:
    name: str
    pets: list[Pet] = field(default_factory=list)
    preferences: dict[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not isinstance(self.name, str) or not self.name.strip():
            raise ValueError("Owner name must not be blank")
        self.name = self.name.strip()
        if any(not isinstance(pet, Pet) for pet in self.pets):
            raise TypeError("pets must contain Pet objects")

    def add_pet(self, pet: Pet) -> None:
        if not isinstance(pet, Pet):
            raise TypeError("pet must be a Pet")
        if any(existing.id == pet.id for existing in self.pets):
            raise ValueError(f"Pet ID already exists for this owner: {pet.id}")
        self.pets.append(pet)

    def remove_pet(self, pet_id: str) -> None:
        pet = self.get_pet(pet_id)
        self.pets.remove(pet)

    def get_pet(self, pet_id: str) -> Pet:
        for pet in self.pets:
            if pet.id == pet_id:
                return pet
        raise KeyError(f"No pet found with ID: {pet_id}")


@dataclass
class ScheduledItem:
    task: CareTask
    planned_minutes: int
    reason: str

    def __post_init__(self) -> None:
        if not isinstance(self.task, CareTask):
            raise TypeError("task must be a CareTask")
        if isinstance(self.planned_minutes, bool) or not isinstance(
            self.planned_minutes, int
        ):
            raise TypeError("Planned minutes must be an integer")
        if not 1 <= self.planned_minutes <= self.task.get_remaining_minutes():
            raise ValueError("Planned minutes must fit the task's remaining duration")
        if not isinstance(self.reason, str) or not self.reason.strip():
            raise ValueError("A scheduling reason is required")
        self.reason = self.reason.strip()

    def get_remaining_task_minutes(self) -> int:
        return self.task.get_remaining_minutes() - self.planned_minutes

    def get_explanation(self) -> str:
        return self.reason


@dataclass
class DailyPlan:
    date: date = field(default_factory=date.today)
    available_minutes: int = DEFAULT_AVAILABLE_MINUTES
    candidate_tasks: list[CareTask] = field(default_factory=list, repr=False)
    scheduled_items: list[ScheduledItem] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not isinstance(self.date, date):
            raise TypeError("date must be a date")
        if isinstance(self.available_minutes, bool) or not isinstance(
            self.available_minutes, int
        ):
            raise TypeError("Available time must be an integer number of minutes")
        if self.available_minutes <= 0:
            raise ValueError("Available time must be greater than zero")
        if any(not isinstance(task, CareTask) for task in self.candidate_tasks):
            raise TypeError("candidate_tasks must contain CareTask objects")
        if any(not isinstance(item, ScheduledItem) for item in self.scheduled_items):
            raise TypeError("scheduled_items must contain ScheduledItem objects")
        if self.total_planned_minutes > self.available_minutes:
            raise ValueError("Scheduled items cannot exceed available time")

    @property
    def total_planned_minutes(self) -> int:
        return sum(item.planned_minutes for item in self.scheduled_items)

    def add_item(self, item: ScheduledItem) -> None:
        if not isinstance(item, ScheduledItem):
            raise TypeError("item must be a ScheduledItem")
        if self.get_remaining_time() < item.planned_minutes:
            raise ValueError("Scheduled items cannot exceed available time")
        if any(existing.task.id == item.task.id for existing in self.scheduled_items):
            raise ValueError("A task can only appear once in a daily plan")
        self.scheduled_items.append(item)

    def get_remaining_time(self) -> int:
        return self.available_minutes - self.total_planned_minutes

    def get_unscheduled_tasks(self) -> list[CareTask]:
        planned_by_task = {
            item.task.id: item.planned_minutes for item in self.scheduled_items
        }
        return [
            task
            for task in self.candidate_tasks
            if task.get_remaining_minutes() > planned_by_task.get(task.id, 0)
        ]


class Scheduler:
    priority_weights = {
        Priority.HIGH: 3.0,
        Priority.MEDIUM: 2.0,
        Priority.LOW: 1.0,
    }
    preference_bonus = 1.1

    def generate_plan(
        self,
        pet: Pet,
        task_date: date,
        available_minutes: Optional[int] = None,
        preferences: Optional[Mapping[str, object]] = None,
    ) -> DailyPlan:
        if not isinstance(pet, Pet):
            raise TypeError("pet must be a Pet")
        if not isinstance(task_date, date):
            raise TypeError("task_date must be a date")
        budget = (
            DEFAULT_AVAILABLE_MINUTES
            if available_minutes is None
            else available_minutes
        )
        if isinstance(budget, bool) or not isinstance(budget, int):
            raise TypeError("Available time must be an integer number of minutes")
        if budget <= 0:
            raise ValueError("Available time must be greater than zero")

        task_preferences = {} if preferences is None else preferences
        candidates = pet.get_tasks_for_day(task_date)
        plan = DailyPlan(
            date=task_date,
            available_minutes=budget,
            candidate_tasks=candidates.copy(),
        )

        ranked_tasks = sorted(
            enumerate(candidates),
            key=lambda entry: (
                -self.score_task(entry[1], task_preferences),
                entry[0],
            ),
        )

        for _, task in ranked_tasks:
            remaining = plan.get_remaining_time()
            if remaining == 0:
                break
            planned_minutes = min(task.get_remaining_minutes(), remaining)
            plan.add_item(
                ScheduledItem(
                    task=task,
                    planned_minutes=planned_minutes,
                    reason=self.explain_decision(
                        task, planned_minutes, task_preferences
                    ),
                )
            )

        return plan

    def score_task(
        self, task: CareTask, preferences: Optional[Mapping[str, object]] = None
    ) -> float:
        if not isinstance(task, CareTask):
            raise TypeError("task must be a CareTask")
        score = self.priority_weights[task.priority] / sqrt(task.duration_minutes)
        if preferences is not None and self._matches_preference(task, preferences):
            score *= self.preference_bonus
        return score

    def explain_decision(
        self,
        task: CareTask,
        planned_minutes: int,
        preferences: Optional[Mapping[str, object]] = None,
    ) -> str:
        if not isinstance(task, CareTask):
            raise TypeError("task must be a CareTask")
        if not 1 <= planned_minutes <= task.get_remaining_minutes():
            raise ValueError("Planned minutes must fit the task's remaining duration")

        explanation = (
            f"Selected with {task.priority.value} priority; "
            f"{planned_minutes} of {task.get_remaining_minutes()} remaining "
            f"minutes fit the available daily time."
        )
        if preferences is not None and self._matches_preference(task, preferences):
            explanation += " It also matches an owner preference."
        return explanation

    @staticmethod
    def _matches_preference(
        task: CareTask, preferences: Mapping[str, object]
    ) -> bool:
        supported_keys = {"preferred_task_titles", "preferred_priorities"}
        unsupported = set(preferences) - supported_keys
        if unsupported:
            names = ", ".join(sorted(unsupported))
            raise ValueError(f"Unsupported preference(s): {names}")

        preferred_titles = preferences.get("preferred_task_titles", ())
        preferred_priorities = preferences.get("preferred_priorities", ())
        for key, values in (
            ("preferred_task_titles", preferred_titles),
            ("preferred_priorities", preferred_priorities),
        ):
            if isinstance(values, (str, bytes)) or not isinstance(values, Sequence):
                raise TypeError(f"{key} must be a sequence of strings")

        normalized_titles = {
            title.strip().casefold()
            for title in preferred_titles
            if isinstance(title, str) and title.strip()
        }
        if any(
            not isinstance(title, str) or not title.strip()
            for title in preferred_titles
        ):
            raise ValueError("Preferred task titles must be non-blank strings")
        normalized_priorities = {
            Priority(priority.lower() if isinstance(priority, str) else priority)
            for priority in preferred_priorities
        }

        return (
            task.title.casefold() in normalized_titles
            or task.priority in normalized_priorities
        )
