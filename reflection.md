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

- What constraints does your scheduler consider (for example: time, priority, preferences)?
- How did you decide which constraints mattered most?

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

AI initially described a pet-specific plan, but the multi-pet requirement meant that plan needed to cover an owner's tasks across pets. I changed the design so `Scheduler` calls `Owner.get_all_tasks()` and the plan identifies its owner. I also kept the scope as a daily scheduler rather than expanding it into a full weekly planner. I verified the choices with tests for multi-pet scheduling, task completion, rescheduling, recurring occurrences, and time limits; all 11 tests passed. Running `python main.py` also confirmed the sample terminal schedule.

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?
