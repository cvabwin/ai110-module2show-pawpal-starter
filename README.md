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

Run the terminal demo with `python main.py` and the web app with `streamlit run app.py`.

### Suggested workflow

1. Read the scenario carefully and identify requirements and edge cases.
2. Draft a UML diagram (classes, attributes, methods, relationships).
3. Convert UML into Python class stubs (no logic yet).
4. Implement scheduling logic in small increments.
5. Add tests to verify key behaviors.
6. Connect your logic to the Streamlit UI in `app.py`.
7. Refine UML so it matches what you actually built.

## Implementation Summary

The backend logic lives in `pawpal_system.py`. `Owner` manages multiple pets and provides all of their tasks to `Scheduler`. Each `Pet` owns its own `CareTask` objects. Tasks track duration, priority, frequency, scheduled date, split eligibility, and completion progress. The scheduler filters tasks for the selected date, ranks them by priority first and then start time (using owner preferences to break ties within a priority), and creates a `DailyPlan` containing explained `ScheduledItem`s without exceeding the available-time limit. The default daily budget is 120 minutes; recurring tasks track completion separately for each occurrence.

`main.py` provides a small terminal demo with two pets and three tasks. The Streamlit interface in `app.py` is connected to the backend and uses `Scheduler` for sorting, filtering, conflict warnings, recurring completion, and plan generation.

## ✨ Features

- **Priority-first, then time ranking.** `Scheduler.rank_key` sorts tasks by priority (high, then medium, then low), then owner-preferred tasks, then start time with untimed tasks last, then shorter duration, and finally input order. A high-priority task is never displaced by a lower-priority one, however short.
- **Owner preferences as a tie-breaker.** Within a priority level, a task whose title (case-insensitive) matches `preferred_task_titles`, or whose priority is listed in `preferred_priorities`, is planned first. Preferences never override priority or the time budget. An unsupported preference key raises an error.
- **Greedy time-budgeted planning.** `generate_plan` ranks the eligible tasks with `rank_key` (for every pet, or only one pet when `pet_id` is given) and fills the day from the top until the budget (default 120 minutes) is used up. A splittable task that doesn't fully fit is partially planned with the time left. A non-splittable task that doesn't fit is skipped, and later tasks can still use the remaining time.
- **Date eligibility rules.** A one-time task is due only on its date, or on any day until it is done if it has no date. A daily task is due on and after its start date. A weekly task is due on the same weekday as its start date, on or after it. A task that is already complete for a date is left out.
- **Per-occurrence progress.** Recurring tasks track completed minutes separately for each date, so finishing Monday's walk does not hide Tuesday's. Partial progress is accepted and cannot exceed the remaining minutes.
- **Explained decisions.** Every scheduled item carries a reason with its priority, the minutes planned out of the minutes remaining, and whether an owner preference applied. Tasks that still have work left after the plan are listed as unscheduled.
- **Sorting by start time.** `sort_by_time` orders tasks by their "HH:MM" start time using a stable sort, with untimed tasks last. It returns a new list and does not change the original.
- **Filtering.** `filter_tasks` selects tasks by pet name (case-insensitive) and by completion status, and its result can be sorted afterwards. Recurring tasks always count as open, because an active recurring task always has future work.
- **Conflict detection and resolution.** `find_conflicts` groups timed, incomplete tasks by date and start time in a single pass and reports any group of two or more, labelled "same pet" or "different pets". A conflict can be resolved by confirming the tasks can be done at the same time (`can_overlap`) or by deleting one of them. With a plan date, it compares the tasks due that day, so recurring tasks are included. Only exact start times are compared, not durations.
- **Recurring task rollover.** Completing a daily task creates the next occurrence one day later, and a weekly task seven days later (using `timedelta`, so month, year and leap-day boundaries are handled). The finished occurrence is retired as a completed record, so exactly one active task remains in the series.
- **Validation and safe updates.** Tasks, pets and owners validate their fields on creation. `update_details` checks everything before applying anything, so a failed update changes nothing. A task belongs to one pet and a pet to one owner, and duplicate IDs are rejected.

## 🖥️ Sample Output

Terminal output from running `python main.py`. The plan is ordered by priority first, then by start time within each priority, and conflicts are reported at the end:

```
Today's Schedule (October 20, 2026): priority first, then start time
╭─────┬─────────┬─────────────────┬─────────┬────────────┬───────────╮
│   # │ Start   │ Task            │ Pet     │ Priority   │ Planned   │
├─────┼─────────┼─────────────────┼─────────┼────────────┼───────────┤
│   1 │ 07:30   │ 🦮 Morning walk │ Mochi   │ 🔴 High    │ 30 min    │
│   2 │ 08:00   │ 🍽️ Breakfast    │ Mochi   │ 🔴 High    │ 10 min    │
│   3 │ 08:00   │ 🍽️ Feeding      │ Biscuit │ 🔴 High    │ 10 min    │
│   4 │ 17:00   │ 💊 Vet call     │ Mochi   │ 🟡 Medium  │ 10 min    │
│   5 │ 17:00   │ 🎓 Training     │ Mochi   │ 🟡 Medium  │ 15 min    │
│   6 │ --:--   │ ✂️ Grooming     │ Biscuit │ 🟢 Low     │ 20 min    │
╰─────┴─────────┴─────────────────┴─────────┴────────────┴───────────╯
⏱️  95/120 minutes planned

All tasks sorted by time
╭─────────┬─────────────────┬─────────┬────────────┬──────────┬───────────┬──────────╮
│ Start   │ Task            │ Pet     │ Priority   │ Length   │ Repeats   │ Status   │
├─────────┼─────────────────┼─────────┼────────────┼──────────┼───────────┼──────────┤
│ 07:30   │ 🦮 Morning walk │ Mochi   │ 🔴 High    │ 30 min   │ Daily     │ ⏳ Open  │
│ 08:00   │ 🍽️ Breakfast    │ Mochi   │ 🔴 High    │ 10 min   │ Once      │ ⏳ Open  │
│ 08:00   │ 🍽️ Feeding      │ Biscuit │ 🔴 High    │ 10 min   │ Once      │ ⏳ Open  │
│ 17:00   │ 🎓 Training     │ Mochi   │ 🟡 Medium  │ 15 min   │ Once      │ ⏳ Open  │
│ 17:00   │ 💊 Vet call     │ Mochi   │ 🟡 Medium  │ 10 min   │ Once      │ ⏳ Open  │
│ --:--   │ ✂️ Grooming     │ Biscuit │ 🟢 Low     │ 20 min   │ Once      │ ⏳ Open  │
╰─────────┴─────────────────┴─────────┴────────────┴──────────┴───────────┴──────────╯

Mochi's tasks
╭─────────┬─────────────────┬───────┬────────────┬──────────┬───────────┬──────────╮
│ Start   │ Task            │ Pet   │ Priority   │ Length   │ Repeats   │ Status   │
├─────────┼─────────────────┼───────┼────────────┼──────────┼───────────┼──────────┤
│ 17:00   │ 🎓 Training     │ Mochi │ 🟡 Medium  │ 15 min   │ Once      │ ⏳ Open  │
│ 07:30   │ 🦮 Morning walk │ Mochi │ 🔴 High    │ 30 min   │ Daily     │ ⏳ Open  │
│ 17:00   │ 💊 Vet call     │ Mochi │ 🟡 Medium  │ 10 min   │ Once      │ ⏳ Open  │
│ 08:00   │ 🍽️ Breakfast    │ Mochi │ 🔴 High    │ 10 min   │ Once      │ ⏳ Open  │
╰─────────┴─────────────────┴───────┴────────────┴──────────┴───────────┴──────────╯

Conflict warnings
⚠️  Conflict (same pet) at 2026-10-20 17:00: Mochi: Training, Mochi: Vet call
⚠️  Conflict (different pets) at 2026-10-20 08:00: Mochi: Breakfast, Biscuit: Feeding

Completed 'Morning walk' for 2026-10-20; next occurrence scheduled for 2026-10-21 (expected 2026-10-21)

Completed tasks
╭─────────┬─────────────────┬───────┬────────────┬──────────┬───────────┬──────────╮
│ Start   │ Task            │ Pet   │ Priority   │ Length   │ Repeats   │ Status   │
├─────────┼─────────────────┼───────┼────────────┼──────────┼───────────┼──────────┤
│ 07:30   │ 🦮 Morning walk │ Mochi │ 🔴 High    │ 30 min   │ Once      │ ✅ Done  │
╰─────────┴─────────────────┴───────┴────────────┴──────────┴───────────┴──────────╯

Incomplete Mochi tasks, by time
╭─────────┬─────────────────┬───────┬────────────┬──────────┬───────────┬──────────╮
│ Start   │ Task            │ Pet   │ Priority   │ Length   │ Repeats   │ Status   │
├─────────┼─────────────────┼───────┼────────────┼──────────┼───────────┼──────────┤
│ 07:30   │ 🦮 Morning walk │ Mochi │ 🔴 High    │ 30 min   │ Daily     │ ⏳ Open  │
│ 08:00   │ 🍽️ Breakfast    │ Mochi │ 🔴 High    │ 10 min   │ Once      │ ⏳ Open  │
│ 17:00   │ 🎓 Training     │ Mochi │ 🟡 Medium  │ 15 min   │ Once      │ ⏳ Open  │
│ 17:00   │ 💊 Vet call     │ Mochi │ 🟡 Medium  │ 10 min   │ Once      │ ⏳ Open  │
╰─────────┴─────────────────┴───────┴────────────┴──────────┴───────────┴──────────╯
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
# Test covers sorting, recurrence, and conflict detection. Confidence Level: 5 stars
python -m pytest
platform win32 -- Python 3.13.16, pytest-9.1.1, pluggy-1.7.0
rootdir: C:\Users\cvabw\OneDrive\_Codepath\AI 110\Unit5\ai110-module2show-pawpal-starter
plugins: anyio-4.15.1
collected 31 items                                                                        

test_pawpal_system.py .........                                                     [ 29%]
tests\test_pawpal.py ......................                                         [100%]

=================================== 31 passed in 0.26s ===================================
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

### Conflict detection: `Scheduler.find_conflicts(owner, task_date=None)`
Returns `Conflict` objects (start time, date, and the clashing `(pet name, task)` pairs). `Scheduler.detect_conflicts(owner, task_date=None)` wraps it and returns one warning string per conflict. It raises `TypeError` only if `owner` is not an `Owner` or `task_date` is not a date.
- **Without `task_date`:** it groups incomplete, timed tasks by `(scheduled_date, start_time)` in one pass.
- **With `task_date`:** it checks only the tasks due on that day, so a daily or weekly task is compared on its effective date. For example, a daily task at 09:00 and a one-time task at 09:00 on the same day are flagged. The app uses this form for the daily schedule.
- Any group of two or more is a conflict, labelled "same pet" or "different pets", for example `Conflict (same pet) at 2026-10-20 17:00: Mochi: Training, Mochi: Vet call`. An empty list means no conflicts.
- **Allowing overlaps:** every task has a `can_overlap` flag. `Scheduler.allow_simultaneous(conflict)` sets it on all the tasks in a conflict, and a group is no longer reported when all of its tasks allow overlap. If a new task joins that slot, the conflict returns.
- **Resolving in the app:** each conflict shows the question "Can these be done at the same time?" with a **Yes, same time** button and a **Delete** button for each task. Delete asks for confirmation before removing anything. For example, a dog and a cat can both eat at 08:00.
- **Limitation:** only exact start times are compared, not durations. A task at 09:00 for 60 minutes and another at 09:30 are not flagged.

### Recurring tasks: `Scheduler.complete_task(owner, task_id, occurrence_date=None)`
- A one-time task is marked complete and the method returns `None`. Completing one that is already complete raises `ValueError`.
- Completing a **daily** task creates the next occurrence due `occurrence_date + timedelta(days=1)`. A **weekly** task uses `timedelta(days=7)`.
- `occurrence_date` defaults to today, but never to a date before the task's start date. A date that is not a date, or a date when the task is not due (or is already complete), is rejected.
- The new task copies the title, duration, priority, splittable flag, frequency and start time, and is added to the same pet. It is added before the original is changed, so a failure leaves the original task untouched.
- The finished occurrence becomes a completed one-time record, so the new task is the only active copy of the series. Progress recorded on other dates is kept in its `completed_by_date`.
- Weekly tasks need a `scheduled_date` as an anchor.

## 🎯 Priority-First Scheduling and CLI Formatting

### Priority-first, then time
`Scheduler.generate_plan` ranks tasks with `Scheduler.rank_key`, which sorts by priority first and then by start time. Within a priority level, owner-preferred tasks go first, untimed tasks go last, and shorter tasks win a remaining tie. The example below has a low-priority task at 06:00, yet the high-priority tasks are planned first, ordered by time among themselves:

```
╭─────┬─────────┬───────────────────────┬───────┬────────────┬───────────╮
│   # │ Start   │ Task                  │ Pet   │ Priority   │ Planned   │
├─────┼─────────┼───────────────────────┼───────┼────────────┼───────────┤
│   1 │ 15:00   │ 🦮 Afternoon walk     │ Mochi │ 🔴 High    │ 30 min    │
│   2 │ 20:00   │ 💊 Evening medication │ Mochi │ 🔴 High    │ 5 min     │
│   3 │ --:--   │ ✂️ Brush teeth        │ Mochi │ 🔴 High    │ 5 min     │
│   4 │ 12:00   │ 🎾 Midday play        │ Mochi │ 🟡 Medium  │ 15 min    │
│   5 │ 06:00   │ ✂️ Early grooming     │ Mochi │ 🟢 Low     │ 20 min    │
╰─────┴─────────┴───────────────────────┴───────┴────────────┴───────────╯
⏱️  75/120 minutes planned
```

The 06:00 grooming (low) comes last even though it starts earliest, the three high-priority tasks come first (timed ones by start time, the untimed one last), and the medium-priority play sits between them.

### Formatting features
The terminal formatting lives in `cli_format.py` and is used by `main.py`. The library used is [`tabulate`](https://pypi.org/project/tabulate/), with `wcwidth` so emoji columns line up.

| Feature | Function | How it works |
|---|---|---|
| Structured tables | `tasks_table()`, `plan_table()` | `tabulate` with the `rounded_outline` style; the plan table is numbered and ends with a minutes-used footer |
| Color-coded priority | `priority_label()` | Red (high), yellow (medium) and green (low) ANSI colors, shown only on a real terminal and switched off when output is piped or `NO_COLOR` is set |
| Priority emojis | `priority_label()` | 🔴 high, 🟡 medium, 🟢 low |
| Task-type emojis | `task_emoji()` | Picks an emoji from keywords in the title, such as 🦮 walk, 🍽️ feeding, 💊 vet or medication, ✂️ grooming, 🎓 training, 🎾 play, and 🐾 by default |
| Status indicators | `status_label()` | ✅ Done and ⏳ Open |
| Conflict messages | `conflict_lines()` | ⚠️ for each conflict, or ✅ "No scheduling conflicts" |

The Streamlit app has its own formatting: colored priority badges, Material icons, metric cards, and success and warning boxes.

## 📸 Demo Walkthrough

Run the app with `streamlit run app.py`, then follow these steps:

1. **Add a pet.** In the sidebar, type a name (for example "Mochi"), choose Dog, Cat or Other, and press **Add pet**. The pet appears under "Your pets" with its task count, and the overview row at the top shows your totals.
2. **Pick the active pet.** Select a pet in the sidebar list. The Tasks tab always works on the selected pet.
3. **Add care tasks.** On the **Tasks** tab, fill in the "Add a task" card: a title, a duration in minutes, a priority (low, medium or high), a frequency (once, daily or weekly), a start date, and an optional start time. Leave "Allow this task to be split" on if the task can be done in pieces, and turn on "Can be done at the same time as other tasks" for tasks that may overlap with others (such as feeding a dog and a cat together), so they won't be flagged as a conflict. Press **Add task**.
4. **Read the task cards.** The selected pet's open tasks are listed in start-time order, with untimed tasks last. Each card shows a colored priority badge, the duration, and when the task repeats.
5. **Check for conflicts.** If two tasks share the same date and start time, a warning lists them (for example, Mochi's breakfast and Biscuit's feeding at 08:00) and asks "Can these be done at the same time?". Press **Yes, same time** to allow it, or press a task's **Delete** button and confirm with **Yes, delete** (or **Cancel**). When there are no clashes, a green "No scheduling conflicts" message appears.
6. **Filter and review all tasks.** In the "All tasks" section, choose a pet and a status (All, Open or Done). The table shows the matching tasks sorted by start time.
7. **Mark a task done.** Press **Done** on a card. A one-time task moves to the "Completed" list. A daily or weekly task creates its next occurrence one day or seven days later, so it keeps repeating.
8. **Build a daily schedule.** Open the **Daily schedule** tab, choose who to plan for (the selected pet, or **All pets**), a plan date and how many minutes you have, and press **Generate**. To see another pet's schedule, select that pet in the sidebar and press **Generate** again.
9. **Read the plan.** The heading names the pet (or all pets) the plan is for. You see the planned, available and left-over minutes with a progress bar, then one card per scheduled task with the reason it was chosen. Tasks that did not fit are listed under "Still needs time", and any overlapping start times that day are flagged with a warning.

**Screenshot or video** *(optional)*: add a screenshot here, for example `![PawPal+ app](diagrams/app-video.gif)`.
