"""Terminal formatting helpers for the PawPal+ demo: color, emojis, and tables."""

from __future__ import annotations

import os
import sys
from typing import Iterable

from tabulate import tabulate

from pawpal_system import CareTask, DailyPlan, Owner, Priority

ANSI_RESET = "\033[0m"
PRIORITY_COLORS = {
    Priority.HIGH: "\033[91m",
    Priority.MEDIUM: "\033[93m",
    Priority.LOW: "\033[92m",
}
PRIORITY_ICONS = {Priority.HIGH: "🔴", Priority.MEDIUM: "🟡", Priority.LOW: "🟢"}

# The first keyword found in a task title picks its emoji.
TASK_EMOJIS = (
    (("walk", "run", "exercise"), "🦮"),
    (("feed", "meal", "breakfast", "dinner"), "🍽️"),
    (("groom", "brush", "bath"), "✂️"),
    (("vet", "med", "pill", "dose"), "💊"),
    (("train", "practice"), "🎓"),
    (("play", "toy", "enrich"), "🎾"),
)
DEFAULT_TASK_EMOJI = "🐾"


def use_color() -> bool:
    """Color only real terminals, and respect the NO_COLOR convention."""
    return sys.stdout.isatty() and "NO_COLOR" not in os.environ


def task_emoji(task: CareTask) -> str:
    """Pick an emoji for a task from keywords in its title."""
    title = task.title.casefold()
    for keywords, emoji in TASK_EMOJIS:
        if any(keyword in title for keyword in keywords):
            return emoji
    return DEFAULT_TASK_EMOJI


def priority_label(priority: Priority) -> str:
    """Return the priority with an emoji, wrapped in an ANSI color on a terminal."""
    label = f"{PRIORITY_ICONS[priority]} {priority.value.capitalize()}"
    if use_color():
        return f"{PRIORITY_COLORS[priority]}{label}{ANSI_RESET}"
    return label


def status_label(task: CareTask) -> str:
    """Return a status indicator for a task."""
    return "✅ Done" if task.is_complete else "⏳ Open"


def tasks_table(owner: Owner, tasks: Iterable[CareTask]) -> str:
    """Render tasks as a table with start time, pet, priority and status."""
    rows = [
        [
            task.start_time or "--:--",
            f"{task_emoji(task)} {task.title}",
            owner.get_pet(task.pet_id).name,
            priority_label(task.priority),
            f"{task.duration_minutes} min",
            task.frequency.value.capitalize(),
            status_label(task),
        ]
        for task in tasks
    ]
    headers = ["Start", "Task", "Pet", "Priority", "Length", "Repeats", "Status"]
    return tabulate(rows, headers=headers, tablefmt="rounded_outline")


def plan_table(owner: Owner, plan: DailyPlan) -> str:
    """Render a daily plan in planned order, with a time-budget footer."""
    rows = [
        [
            index,
            item.task.start_time or "--:--",
            f"{task_emoji(item.task)} {item.task.title}",
            owner.get_pet(item.task.pet_id).name,
            priority_label(item.task.priority),
            f"{item.planned_minutes} min",
        ]
        for index, item in enumerate(plan.scheduled_items, start=1)
    ]
    headers = ["#", "Start", "Task", "Pet", "Priority", "Planned"]
    table = tabulate(rows, headers=headers, tablefmt="rounded_outline")
    return (
        f"{table}\n"
        f"⏱️  {plan.total_planned_minutes}/{plan.available_minutes} minutes planned"
    )


def conflict_lines(warnings: Iterable[str]) -> str:
    """Return conflict warnings, or a success line when there are none."""
    warnings = list(warnings)
    if not warnings:
        return "✅ No scheduling conflicts"
    return "\n".join(f"⚠️  {warning}" for warning in warnings)
