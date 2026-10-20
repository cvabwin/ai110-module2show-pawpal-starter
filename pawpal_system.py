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


class Frequency(str, Enum):
    ONCE = "once"
    DAILY = "daily"
    WEEKLY = "weekly"


@dataclass
class CareTask:
    title: str
    duration_minutes: int
    priority: Priority | str = Priority.MEDIUM
    scheduled_date: Optional[date] = None
    completed_minutes: int = 0
    id: str = field(default_factory=lambda: uuid4().hex)
    is_splittable: bool = True
    pet_id: Optional[str] = field(default=None, repr=False)
    frequency: Frequency | str = Frequency.ONCE
    completed_by_date: dict[date, int] = field(default_factory=dict, repr=False)

    def __post_init__(self) -> None:
        """Validate and normalize task fields after initialization."""
        self.title = self._validate_title(self.title)
        self.duration_minutes = self._validate_duration(self.duration_minutes)
        self.priority = self._validate_priority(self.priority)
        self.frequency = self._validate_frequency(self.frequency)
        self.completed_minutes = self._validate_completed_minutes(
            self.completed_minutes, self.duration_minutes
        )
        if not isinstance(self.id, str) or not self.id.strip():
            raise ValueError("Task ID must not be blank")
        self.scheduled_date = self._validate_scheduled_date(self.scheduled_date)
        if not isinstance(self.is_splittable, bool):
            raise TypeError("is_splittable must be a bool")
        self.pet_id = self._validate_optional_id(self.pet_id, "Pet ID")
        self.completed_by_date = self._validate_occurrence_progress(
            self.completed_by_date, self.duration_minutes
        )
        if self.frequency is Frequency.WEEKLY and self.scheduled_date is None:
            raise ValueError("Weekly tasks require a scheduled date as an anchor")

    @staticmethod
    def _validate_title(title: object) -> str:
        """Return a trimmed non-empty task title."""
        if not isinstance(title, str) or not title.strip():
            raise ValueError("Task title must not be blank")
        return title.strip()

    @staticmethod
    def _validate_duration(duration_minutes: object) -> int:
        """Validate the task duration is within the supported range."""
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
        """Normalize a priority value or raise a validation error."""
        try:
            if isinstance(priority, str):
                return Priority(priority.lower())
            if isinstance(priority, Priority):
                return priority
        except ValueError as error:
            raise ValueError("Priority must be low, medium, or high") from error
        raise ValueError("Priority must be low, medium, or high")

    @staticmethod
    def _validate_frequency(frequency: object) -> Frequency:
        """Normalize a task frequency or raise a validation error."""
        try:
            if isinstance(frequency, str):
                return Frequency(frequency.lower())
            if isinstance(frequency, Frequency):
                return frequency
        except ValueError as error:
            raise ValueError("Frequency must be once, daily, or weekly") from error
        raise ValueError("Frequency must be once, daily, or weekly")

    @staticmethod
    def _validate_completed_minutes(minutes: object, duration: int) -> int:
        """Validate completed minutes against the task duration."""
        if isinstance(minutes, bool) or not isinstance(minutes, int):
            raise TypeError("Completed minutes must be an integer")
        if not 0 <= minutes <= duration:
            raise ValueError("Completed minutes must be between 0 and task duration")
        return minutes

    @staticmethod
    def _validate_scheduled_date(value: object) -> Optional[date]:
        """Validate an optional scheduled date."""
        if value is not None and not isinstance(value, date):
            raise TypeError("scheduled_date must be a date or None")
        return value

    @staticmethod
    def _validate_optional_id(value: object, label: str) -> Optional[str]:
        """Validate an optional non-empty identifier."""
        if value is not None and (not isinstance(value, str) or not value.strip()):
            raise ValueError(f"{label} must be a non-blank string or None")
        return value

    @classmethod
    def _validate_occurrence_progress(
        cls, progress: Mapping[date, int], duration: int
    ) -> dict[date, int]:
        """Validate recorded progress for recurring task dates."""
        if not isinstance(progress, Mapping):
            raise TypeError("completed_by_date must be a mapping of dates to minutes")
        validated: dict[date, int] = {}
        for occurrence_date, minutes in progress.items():
            if not isinstance(occurrence_date, date):
                raise TypeError("Occurrence progress keys must be dates")
            validated[occurrence_date] = cls._validate_completed_minutes(
                minutes, duration
            )
        return validated

    @property
    def is_complete(self) -> bool:
        """Return whether a one-time task is complete."""
        return (
            self.frequency is Frequency.ONCE
            and self.completed_minutes == self.duration_minutes
        )

    def is_complete_for_date(self, occurrence_date: date) -> bool:
        """Return whether the task occurrence on a date is complete."""
        return self.get_remaining_minutes(occurrence_date) == 0

    def is_scheduled_for_date(self, occurrence_date: date) -> bool:
        """Check whether an incomplete task occurrence belongs on a date."""
        if not isinstance(occurrence_date, date):
            raise TypeError("occurrence_date must be a date")
        if self.is_complete_for_date(occurrence_date):
            return False
        if self.frequency is Frequency.ONCE:
            return self.scheduled_date is None or self.scheduled_date == occurrence_date
        if self.frequency is Frequency.DAILY:
            return self.scheduled_date is None or occurrence_date >= self.scheduled_date
        return (
            occurrence_date >= self.scheduled_date
            and occurrence_date.weekday() == self.scheduled_date.weekday()
        )

    def update_details(self, updates: Mapping[str, object]) -> None:
        """Validate and apply supported task field updates."""
        allowed_fields = {
            "title",
            "duration_minutes",
            "priority",
            "scheduled_date",
            "is_splittable",
            "frequency",
        }
        unexpected_fields = set(updates) - allowed_fields
        if unexpected_fields:
            names = ", ".join(sorted(unexpected_fields))
            raise ValueError(f"Cannot update task field(s): {names}")

        new_title = self.title
        new_duration = self.duration_minutes
        new_priority = self.priority
        new_scheduled_date = self.scheduled_date
        new_is_splittable = self.is_splittable
        new_frequency = self.frequency

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
        if "is_splittable" in updates:
            new_is_splittable = updates["is_splittable"]
            if not isinstance(new_is_splittable, bool):
                raise TypeError("is_splittable must be a bool")
        if "frequency" in updates:
            new_frequency = self._validate_frequency(updates["frequency"])

        if self.completed_minutes > new_duration or any(
            minutes > new_duration for minutes in self.completed_by_date.values()
        ):
            raise ValueError("New duration cannot be less than completed minutes")
        if new_frequency is Frequency.WEEKLY and new_scheduled_date is None:
            raise ValueError("Weekly tasks require a scheduled date as an anchor")

        self.title = new_title
        self.duration_minutes = new_duration
        self.priority = new_priority
        self.scheduled_date = new_scheduled_date
        self.is_splittable = new_is_splittable
        self.frequency = new_frequency

    def mark_complete(self, occurrence_date: Optional[date] = None) -> None:
        """Mark a one-time task or dated recurring occurrence complete."""
        if self.frequency is Frequency.ONCE:
            self.completed_minutes = self.duration_minutes
            return
        self._require_occurrence_date(occurrence_date)
        self.completed_by_date[occurrence_date] = self.duration_minutes

    def record_progress(
        self, minutes: int, occurrence_date: Optional[date] = None
    ) -> None:
        """Record completed minutes for a task or dated occurrence."""
        if isinstance(minutes, bool) or not isinstance(minutes, int):
            raise TypeError("Progress must be an integer number of minutes")
        if minutes <= 0:
            raise ValueError("Progress must be greater than zero")
        remaining = self.get_remaining_minutes(occurrence_date)
        if minutes > remaining:
            raise ValueError("Progress cannot exceed the task's remaining duration")
        if self.frequency is Frequency.ONCE:
            self.completed_minutes += minutes
        else:
            self.completed_by_date[occurrence_date] = (
                self.completed_by_date.get(occurrence_date, 0) + minutes
            )

    def get_remaining_minutes(self, occurrence_date: Optional[date] = None) -> int:
        """Return remaining minutes for a task or dated occurrence."""
        if self.frequency is Frequency.ONCE:
            completed = self.completed_minutes
        else:
            self._require_occurrence_date(occurrence_date)
            completed = self.completed_by_date.get(occurrence_date, 0)
        return self.duration_minutes - completed

    @staticmethod
    def _require_occurrence_date(occurrence_date: Optional[date]) -> None:
        """Require a date when accessing recurring task progress."""
        if not isinstance(occurrence_date, date):
            raise ValueError("A date is required to track recurring task progress")


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
    owner: Optional[Owner] = field(
        default=None, init=False, repr=False, compare=False
    )

    def __post_init__(self) -> None:
        """Validate pet details and establish task ownership."""
        self.name = self._validate_text(self.name, "Pet name")
        self.species = self._validate_text(self.species, "Species").lower()
        if not isinstance(self.id, str) or not self.id.strip():
            raise ValueError("Pet ID must not be blank")
        if self.owner is not None and not isinstance(self.owner, Owner):
            raise TypeError("owner must be an Owner or None")
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
        task_ids = [task.id for task in self.care_tasks]
        if len(task_ids) != len(set(task_ids)):
            raise ValueError("A pet cannot contain duplicate task IDs")
        for task in self.care_tasks:
            if task.pet_id not in (None, self.id):
                raise ValueError("A care task can belong to only one pet")
        for task in self.care_tasks:
            task.pet_id = self.id

    @staticmethod
    def _validate_text(value: str, label: str) -> str:
        """Return trimmed non-empty text for a labeled field."""
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{label} must not be blank")
        return value.strip()

    @classmethod
    def _validate_text_list(cls, values: Sequence[str], label: str) -> list[str]:
        """Validate and normalize a sequence of text values."""
        if isinstance(values, (str, bytes)):
            raise TypeError(f"{label} must be a list of text values")
        return [cls._validate_text(value, label) for value in values]

    def add_task(self, task: CareTask) -> None:
        """Add a task while enforcing exclusive pet ownership."""
        if not isinstance(task, CareTask):
            raise TypeError("task must be a CareTask")
        if any(existing.id == task.id for existing in self.care_tasks):
            raise ValueError(f"Task ID already exists for this pet: {task.id}")
        if task.pet_id not in (None, self.id):
            raise ValueError("A care task can belong to only one pet")
        task.pet_id = self.id
        self.care_tasks.append(task)

    def edit_task(self, task_id: str, updates: Mapping[str, object]) -> None:
        """Update a task belonging to this pet."""
        self._get_task(task_id).update_details(updates)

    def remove_task(self, task_id: str) -> None:
        """Remove a task and release its pet ownership."""
        task = self._get_task(task_id)
        self.care_tasks.remove(task)
        task.pet_id = None

    def get_tasks_for_day(self, task_date: date) -> list[CareTask]:
        """Return incomplete tasks scheduled for the given date."""
        if not isinstance(task_date, date):
            raise TypeError("task_date must be a date")
        return [
            task
            for task in self.care_tasks
            if task.is_scheduled_for_date(task_date)
        ]

    def _get_task(self, task_id: str) -> CareTask:
        """Find a pet task by ID or raise a key error."""
        for task in self.care_tasks:
            if task.id == task_id:
                return task
        raise KeyError(f"No task found with ID: {task_id}")


@dataclass
class Owner:
    name: str
    pets: list[Pet] = field(default_factory=list)
    preferences: dict[str, object] = field(default_factory=dict)
    id: str = field(default_factory=lambda: uuid4().hex)

    def __post_init__(self) -> None:
        """Validate owner details and establish pet ownership."""
        if not isinstance(self.name, str) or not self.name.strip():
            raise ValueError("Owner name must not be blank")
        self.name = self.name.strip()
        if not isinstance(self.id, str) or not self.id.strip():
            raise ValueError("Owner ID must not be blank")
        if any(not isinstance(pet, Pet) for pet in self.pets):
            raise TypeError("pets must contain Pet objects")
        pet_ids = [pet.id for pet in self.pets]
        if len(pet_ids) != len(set(pet_ids)):
            raise ValueError("An owner cannot contain duplicate pet IDs")
        for pet in self.pets:
            if pet.owner is not None and pet.owner is not self:
                raise ValueError("A pet can belong to only one owner")
        for pet in self.pets:
            pet.owner = self

    def add_pet(self, pet: Pet) -> None:
        """Add a pet while enforcing exclusive owner ownership."""
        if not isinstance(pet, Pet):
            raise TypeError("pet must be a Pet")
        if any(existing.id == pet.id for existing in self.pets):
            raise ValueError(f"Pet ID already exists for this owner: {pet.id}")
        if pet.owner is not None and pet.owner is not self:
            raise ValueError("A pet can belong to only one owner")
        pet.owner = self
        self.pets.append(pet)

    def remove_pet(self, pet_id: str) -> None:
        """Remove a pet and release its owner association."""
        pet = self.get_pet(pet_id)
        self.pets.remove(pet)
        pet.owner = None

    def get_pet(self, pet_id: str) -> Pet:
        """Find an owned pet by ID or raise a key error."""
        for pet in self.pets:
            if pet.id == pet_id:
                return pet
        raise KeyError(f"No pet found with ID: {pet_id}")

    def get_all_tasks(self) -> list[CareTask]:
        """Return all pet tasks in owner pet order and each pet's task order."""
        tasks = [task for pet in self.pets for task in pet.care_tasks]
        task_ids = [task.id for task in tasks]
        if len(task_ids) != len(set(task_ids)):
            raise ValueError("Task IDs must be unique across all pets")
        return tasks


@dataclass
class ScheduledItem:
    task: CareTask
    planned_minutes: int
    reason: str
    task_date: Optional[date] = None
    remaining_minutes_before_plan: int = field(init=False)

    def __post_init__(self) -> None:
        """Validate the scheduled item and capture its remaining-time snapshot."""
        if not isinstance(self.task, CareTask):
            raise TypeError("task must be a CareTask")
        if isinstance(self.planned_minutes, bool) or not isinstance(
            self.planned_minutes, int
        ):
            raise TypeError("Planned minutes must be an integer")
        if self.task_date is not None and not isinstance(self.task_date, date):
            raise TypeError("task_date must be a date or None")
        if self.task.frequency is not Frequency.ONCE and self.task_date is None:
            raise ValueError("Recurring scheduled items require a task date")
        if not 1 <= self.planned_minutes <= self.task.get_remaining_minutes(
            self.task_date
        ):
            raise ValueError("Planned minutes must fit the task's remaining duration")
        if not isinstance(self.reason, str) or not self.reason.strip():
            raise ValueError("A scheduling reason is required")
        self.reason = self.reason.strip()
        self.remaining_minutes_before_plan = self.task.get_remaining_minutes(
            self.task_date
        )

    def get_remaining_task_minutes(self) -> int:
        """Return task minutes left after this plan's allocation."""
        return max(0, self.remaining_minutes_before_plan - self.planned_minutes)

    def get_explanation(self) -> str:
        """Return the explanation for including this scheduled item."""
        return self.reason


@dataclass
class DailyPlan:
    date: date = field(default_factory=date.today)
    available_minutes: int = DEFAULT_AVAILABLE_MINUTES
    owner_id: Optional[str] = None
    candidate_tasks: list[CareTask] = field(default_factory=list, repr=False)
    scheduled_items: list[ScheduledItem] = field(default_factory=list)

    def __post_init__(self) -> None:
        """Validate plan dates, candidate tasks, and time limits."""
        if not isinstance(self.date, date):
            raise TypeError("date must be a date")
        if self.owner_id is not None and (
            not isinstance(self.owner_id, str) or not self.owner_id.strip()
        ):
            raise ValueError("owner_id must be a non-blank string or None")
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
        candidate_ids = [task.id for task in self.candidate_tasks]
        if len(candidate_ids) != len(set(candidate_ids)):
            raise ValueError("A daily plan cannot contain duplicate candidate tasks")
        if any(task.pet_id is None for task in self.candidate_tasks):
            raise ValueError("Candidate tasks must belong to a pet")
        if any(item.task.id not in candidate_ids for item in self.scheduled_items):
            raise ValueError("Scheduled items must refer to candidate tasks")
        if any(
            item.task_date != self.date for item in self.scheduled_items
        ):
            raise ValueError("Scheduled item dates must match the plan date")
        if self.total_planned_minutes > self.available_minutes:
            raise ValueError("Scheduled items cannot exceed available time")

    @property
    def total_planned_minutes(self) -> int:
        """Return the total minutes allocated in this plan."""
        return sum(item.planned_minutes for item in self.scheduled_items)

    def add_item(self, item: ScheduledItem) -> None:
        """Add a valid candidate item without exceeding the time budget."""
        if not isinstance(item, ScheduledItem):
            raise TypeError("item must be a ScheduledItem")
        if item.task.id not in {task.id for task in self.candidate_tasks}:
            raise ValueError("Scheduled item task must be a candidate for this plan")
        if item.task_date != self.date:
            raise ValueError("Scheduled item date must match the plan date")
        if self.get_remaining_time() < item.planned_minutes:
            raise ValueError("Scheduled items cannot exceed available time")
        if any(existing.task.id == item.task.id for existing in self.scheduled_items):
            raise ValueError("A task can only appear once in a daily plan")
        self.scheduled_items.append(item)

    def get_remaining_time(self) -> int:
        """Return unallocated minutes in the daily plan."""
        return self.available_minutes - self.total_planned_minutes

    def get_unscheduled_tasks(self) -> list[CareTask]:
        """Return candidate tasks with work remaining after this plan."""
        scheduled_by_task = {
            item.task.id: item for item in self.scheduled_items
        }
        return [
            task
            for task in self.candidate_tasks
            if (
                scheduled_by_task[task.id].get_remaining_task_minutes() > 0
                if task.id in scheduled_by_task
                else (
                    task.get_remaining_minutes(self.date) > 0
                    if task.frequency is not Frequency.ONCE
                    else task.get_remaining_minutes() > 0
                )
            )
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
        owner: Owner,
        task_date: date,
        available_minutes: Optional[int] = None,
        preferences: Optional[Mapping[str, object]] = None,
    ) -> DailyPlan:
        """Build an owner-wide daily plan using eligible tasks and priorities."""
        if not isinstance(owner, Owner):
            raise TypeError("owner must be an Owner")
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

        task_preferences = owner.preferences if preferences is None else preferences
        all_tasks = owner.get_all_tasks()
        candidates = [
            task for task in all_tasks if task.is_scheduled_for_date(task_date)
        ]
        plan = DailyPlan(
            date=task_date,
            available_minutes=budget,
            owner_id=owner.id,
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
            task_remaining = task.get_remaining_minutes(task_date)
            if task_remaining > remaining and not task.is_splittable:
                continue
            planned_minutes = min(task_remaining, remaining)
            plan.add_item(
                ScheduledItem(
                    task=task,
                    planned_minutes=planned_minutes,
                    reason=self.explain_decision(
                        task, planned_minutes, task_preferences, task_date
                    ),
                    task_date=task_date,
                )
            )
            if task.frequency is Frequency.ONCE and task.scheduled_date is None:
                task.scheduled_date = task_date

        return plan

    def score_task(
        self, task: CareTask, preferences: Optional[Mapping[str, object]] = None
    ) -> float:
        """Score a task by priority, duration, and matching preferences."""
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
        task_date: Optional[date] = None,
    ) -> str:
        """Explain why a task receives its planned time allocation."""
        if not isinstance(task, CareTask):
            raise TypeError("task must be a CareTask")
        task_remaining = task.get_remaining_minutes(task_date)
        if not 1 <= planned_minutes <= task_remaining:
            raise ValueError("Planned minutes must fit the task's remaining duration")

        explanation = (
            f"Selected with {task.priority.value} priority; "
            f"{planned_minutes} of {task_remaining} remaining "
            f"minutes fit the available daily time."
        )
        if preferences is not None and self._matches_preference(task, preferences):
            explanation += " It also matches an owner preference."
        return explanation

    @staticmethod
    def _matches_preference(
        task: CareTask, preferences: Mapping[str, object]
    ) -> bool:
        """Check whether a task matches any supported owner preference."""
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
