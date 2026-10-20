# PawPal+ (Module 2 Project)

You are building **PawPal+**, a Streamlit app that helps a pet owner plan care tasks for their pet.

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority, owner preferences)
- Produce a daily plan and explain why it chose that plan

Your job is to design the system first (UML), then implement the logic in Python, then connect it to the Streamlit UI.

## What you will build

Your final app should:

- Let a user enter basic owner + pet info
- Let a user add/edit tasks (duration + priority at minimum)
- Generate a daily schedule/plan based on constraints and priorities
- Display the plan clearly (and ideally explain the reasoning)
- Include tests for the most important scheduling behaviors

## Getting started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Suggested workflow

1. Read the scenario carefully and identify requirements and edge cases.
2. Draft a UML diagram (classes, attributes, methods, relationships).
3. Convert UML into Python class stubs (no logic yet).
4. Implement scheduling logic in small increments.
5. Add tests to verify key behaviors.
6. Connect your logic to the Streamlit UI in `app.py`.
7. Refine UML so it matches what you actually built.

## Implementation Summary

The backend logic lives in `pawpal_system.py`. `Owner` manages multiple pets and provides all of their tasks to `Scheduler`. Each `Pet` owns its own `CareTask` objects. Tasks track duration, priority, frequency, scheduled date, split eligibility, and completion progress. The scheduler filters tasks for the selected date, ranks them by priority and duration (using owner preferences as a soft bonus), and creates a `DailyPlan` containing explained `ScheduledItem`s without exceeding the available-time limit. The default daily budget is 120 minutes; recurring tasks track completion separately for each occurrence.

`main.py` provides a small terminal demo with two pets and three tasks. The Streamlit interface in `app.py` is still the starter UI and has not yet been connected to the backend.

## 🖥️ Sample Output
Terminal ouput from running main.py:
```
Today's Schedule (October 20, 2026)
- Biscuit: Feeding (10 min, high priority)
- Mochi: Morning walk (30 min, high priority)
- Mochi: Training (15 min, medium priority)
Total: 55/120 minutes
```

Paste a sample of your app's CLI or Streamlit output here so a reader can see what a generated plan looks like:

```
# e.g.:
# Daily plan for Biscuit (Golden Retriever):
#   08:00 — Morning walk (30 min) [priority: high]
#   09:00 — Feeding (10 min) [priority: high]
#   ...
```

## 🧪 Testing PawPal+

```bash
# Run the full test suite:
pytest

# Run with coverage:
pytest --cov
```

Sample test output:

```
# Paste your pytest output here
```

## 📐 Smarter Scheduling

All four features live on `Scheduler` in `pawpal_system.py`, and `main.py` demos each one.

| Feature            | Method                         | Notes                                |
|--------------------|--------------------------------|--------------------------------------|
| Sorting            | `Scheduler.sort_by_time()`     | By "HH:MM" start time                |
| Filtering          | `Scheduler.filter_tasks()`     | By pet name and/or completion status |
| Conflict detection | `Scheduler.detect_conflicts()` | Same date and start time             |
| Recurring tasks    | `Scheduler.complete_task()`    | Daily (+1 day) and weekly (+7 days)  |

### Sorting: `Scheduler.sort_by_time(tasks)`
Sorts tasks by their optional `start_time` ("HH:MM", 24-hour). Zero-padded times sort correctly as plain text, so the key is a lambda, `(start_time is None, start_time or "")`. Tasks without a start time go last. It returns a new list and leaves the input unchanged.

### Filtering: `Scheduler.filter_tasks(owner, pet_name=None, completed=None)`
- `pet_name` keeps only that pet's tasks (case-insensitive).
- `completed=True` keeps finished tasks, `completed=False` keeps open ones, and `None` ignores status.
- The filters combine, and the result can be passed to `sort_by_time()`, for example "Mochi's open tasks, in time order".

### Conflict detection: `Scheduler.detect_conflicts(owner)`
A lightweight check that returns warning strings and never raises.
- It groups incomplete, timed tasks by `(scheduled_date, start_time)` in one pass.
- Any group of two or more produces a warning labelled "same pet" or "different pets", for example `Conflict (same pet) at 2026-10-20 17:00: Mochi: Training, Mochi: Vet call`.
- An empty list means no conflicts.
- **Limitation:** only exact start times are compared, not durations, and a recurring task is checked only on its anchor date.

### Recurring tasks: `Scheduler.complete_task(owner, task_id, occurrence_date=None)`
- A one-time task is simply marked complete.
- Completing a **daily** task creates the next occurrence due `occurrence_date + timedelta(days=1)`. A **weekly** task uses `timedelta(days=7)`.
- `occurrence_date` defaults to today. The new task copies the title, duration, priority, splittable flag, frequency and start time, and is added to the same pet.
- The finished occurrence becomes a completed one-time record, so the new task is the only active copy of the series.
- Weekly tasks need a `scheduled_date` as an anchor.

## 📸 Demo Walkthrough

Describe your app in numbered steps so a reader can follow along without watching a video:

1. <!-- Describe this step -->
2. <!-- Describe this step -->
3. <!-- Describe this step -->
4. <!-- Describe this step -->
5. <!-- Add more steps as needed -->

**Screenshot or video** *(optional)*: <!-- Insert a screenshot or link to a demo video here -->
