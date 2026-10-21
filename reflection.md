# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**
1. **Manage pets and care tasks** — Create or select a pet, then add, edit, or remove that pet’s tasks, including duration and priority.
2. **Generate a daily plan** — Set the available time and get an ordered plan that balances priority and duration, allows tasks to be split, and explains what was scheduled or deferred.
3. **Track weekly care** — Review the week’s tasks and check off completed items so they aren’t scheduled again.

- Briefly describe your initial UML design.

The initial UML design separates owner and pet information, individual care tasks, the daily plan, and scheduling logic. An owner can have multiple pets, each with its own care tasks. The scheduler reads tasks from the owner and uses the selected date, available time, priorities, and preferences to build an owner-wide daily plan. Scheduled items record each task's allocated time and the reason for it. A weekly checklist can be assembled from task dates and completion status, so the initial design does not require a separate weekly-plan class.

The classes and their responsibilities are:

- **Owner** — Stores the owner’s name, pets, and scheduling preferences. It can add, remove, and look up pets, and return all tasks across its pets.
- **Pet** — Stores a pet’s identity and profile information, along with that pet’s care tasks. It can add, edit, remove, and retrieve tasks for a date.
- **CareTask** — Stores the task title, duration, priority, frequency, optional scheduled date, and completion progress. It validates and updates task details, records progress for one-time or recurring occurrences, and reports remaining time.
- **DailyPlan** — Stores the date, available minutes, candidate tasks, and scheduled items. It adds items without exceeding the time limit and reports remaining time and tasks that still need work.
- **ScheduledItem** — Connects a care task to the portion scheduled in the plan. It stores the planned minutes and an explanation, and reports any remaining task time.
- **Scheduler** — Reads all tasks through the owner, then scores and orders eligible tasks using priority, duration, preferences, and stable input-order tie-breaking; it creates a plan that may include partial tasks when time is limited.
- **Priority** — An enumeration restricting task priority to low, medium, or high.

**b. Design changes**

The design evolved to link each plan to an owner, enforce exclusive pet/task ownership, and require incomplete one-time tasks to be explicitly rescheduled. I also added task frequency, a splittable-task flag, and progress snapshots so recurring and partial plans behave predictably.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

The scheduler considers four constraints: the owner's available time for the day, task priority, task duration, and owner preferences. It also respects whether a task can be split and whether it is due on the chosen date (one-time, daily, or weekly). Eligible tasks are ranked by priority first, then owner preference, then start time, then shorter duration, and filled in that order until the time runs out.

I treated available time as a hard limit, because a plan that exceeds the owner's day is useless. Priority came next, since missing a medication matters more than missing enrichment. Start time and duration are softer factors that only break ties within a priority. Preferences work the same way, so they can nudge the order but never push out an important task.

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
Tradeoff: readability and speed vs. coupling.
Gain: no repeated get_pet lookups, one grouping pass, and warning text built straight from the stored pairs.
Cost: detect_conflicts now reads owner.pets and pet.care_tasks directly instead of going through owner.get_all_tasks() and get_pet. That ties it to how Owner and Pet store their data. If those internals change, this method has to change too.
Cost: each slot keeps a copy of the pet name and task title, not the task object. A warning can't link back to the task, so a UI couldn't offer a "fix this" action without another lookup.

- Why is that tradeoff reasonable for this scenario?
This is this fine for a small app with one detection method. The coupling would matter more if several features needed the same traversal.

---

## 3. AI Collaboration

**a. How you used AI**

I used AI to clarify requirements and edge cases, draft the UML and backend classes, review the scheduler for gaps, and create tests and a terminal demo. Asking for concrete edge cases and then checking the implementation against them was most helpful.

**b. Judgment and verification**

AI initially described a pet-specific plan, but the multi-pet requirement meant that plan needed to cover an owner's tasks across pets. I changed the design so `Scheduler` calls `Owner.get_all_tasks()` and the plan identifies its owner. I also kept the scope as a daily scheduler rather than expanding it into a full weekly planner. I verified the choices with tests for multi-pet scheduling, task completion, rescheduling, recurring occurrences, and time limits; all 31 tests passed. Running `python main.py` also confirmed the sample terminal schedule.

---

## 4. Testing and Verification

**a. What you tested**

I tested task validation and completion, adding tasks to a pet, multi-pet scheduling, the available-time limit, partial and non-splittable tasks, and owner preferences. I also tested the later features: sorting tasks by start time (including untimed tasks and an empty list), conflict detection (same pet, different pets, different times, completed tasks, no tasks), and recurring tasks (a daily task creating the next day's task, weekly after seven days, a year-end rollover, and an unknown task ID). The suite has 31 tests, and all pass.

These tests matter because the scheduler is mostly rules that interact: dates, priorities, progress and time limits. A small mistake in one place can silently produce a wrong plan, so I wanted each rule pinned down by a test that fails loudly.

**b. Confidence**

I am fairly confident in the core behaviors, because the tests cover the happy paths and the main edge cases and a code review helped find real bugs. I am less confident about unusual combinations, such as changing a task's frequency after it has progress, or conflicts between tasks that overlap but start at different times.

With more time I would test:
- overlapping durations in conflict detection (for example, 09:00 for 60 minutes versus a task at 09:30);
- changing a task from one-time to recurring or back;
- completing a recurring task on a day it isn't due;
- passing a `datetime` where a `date` is expected;
- planning the same day twice, since planning pins an undated one-time task to that day.

---

## 5. Reflection

**a. What went well**

I am most satisfied with how the backend and the app fit together. The scheduling logic lives in one place, `Scheduler`, and the Streamlit app only calls it for sorting, filtering, conflict warnings, completing recurring tasks, and building the plan. Because the logic was separate from the interface, I could test it directly and then redesign the screen without touching the rules.

**b. What you would improve**

I would change two more things. First, conflict detection should compare durations, not just exact start times, so a 09:00 task that runs 60 minutes clashes with one at 09:30. Second, planning currently pins an undated one-time task to the plan date, so a preview plan can permanently bind it to that day; I would make planning leave tasks unchanged and let the user schedule explicitly. I already fixed an earlier weakness: the original scoring favored short tasks, so a low-priority 1-minute task could outrank a high-priority 16-minute one, and I changed the ranking to priority first, then time.

**c. Key takeaway**

Designing the data and rules first made everything after it easier, but AI-generated code still needs independent review. A code review of the finished scheduler found real bugs, including lost progress when a recurring task was completed and a completion order that could leave a task half-changed. I learned to treat AI output as a draft, to ask for concrete edge cases, and to turn each one into a test so that I can trust the code instead of assuming it works.
