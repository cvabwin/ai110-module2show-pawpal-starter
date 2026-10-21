from datetime import date

import streamlit as st

from pawpal_system import CareTask, Frequency, Owner, Pet, Scheduler


st.set_page_config(
    page_title="PawPal+",
    page_icon=":material/pets:",
    layout="wide",
)

PRIORITY_COLORS = {"high": "red", "medium": "orange", "low": "green"}
SPECIES_ICONS = {"dog": ":material/pets:", "cat": ":material/cruelty_free:"}

if "owner" not in st.session_state:
    st.session_state.owner = Owner(name="Jordan")

owner: Owner = st.session_state.owner
scheduler = Scheduler()


def priority_badge(priority: str) -> str:
    return f":{PRIORITY_COLORS[priority]}-badge[{priority.capitalize()}]"


def find_pet(pet_id: str) -> Pet:
    return owner.get_pet(pet_id)


def describe_when(task: CareTask) -> str:
    parts = [task.frequency.value.capitalize()]
    if task.start_time:
        parts.append(f"at {task.start_time}")
    if task.scheduled_date:
        parts.append(f"from {task.scheduled_date:%b %d}")
    return " · ".join(parts)


# --- Sidebar: pets ------------------------------------------------------------

with st.sidebar:
    st.title("PawPal+", icon=":material/pets:")
    st.caption(f"Care planning for {owner.name}")

    st.subheader("Add a pet", icon=":material/add_circle:")
    with st.form("add_pet_form", clear_on_submit=True, border=False):
        pet_name = st.text_input("Pet name", placeholder="Mochi")
        species = st.segmented_control(
            "Species", ["dog", "cat", "other"], default="dog", format_func=str.capitalize
        )
        add_pet_submitted = st.form_submit_button(
            "Add pet", icon=":material/add:", width="stretch"
        )

    if add_pet_submitted:
        try:
            new_pet = Pet(name=pet_name, species=species or "other")
            owner.add_pet(new_pet)
            st.session_state.selected_pet_id = new_pet.id
            st.session_state.pop("generated_plan", None)
            st.toast(f"Added {new_pet.name}", icon=":material/check_circle:")
        except ValueError as error:
            st.error(str(error))

    selected_pet = None
    if owner.pets:
        st.subheader("Your pets", icon=":material/favorite:")
        pet_ids = [pet.id for pet in owner.pets]
        selected_pet_id = st.radio(
            "Select a pet",
            pet_ids,
            index=(
                pet_ids.index(st.session_state.selected_pet_id)
                if st.session_state.get("selected_pet_id") in pet_ids
                else 0
            ),
            format_func=lambda pet_id: (
                f"{find_pet(pet_id).name} · {len(find_pet(pet_id).care_tasks)} tasks"
            ),
            label_visibility="collapsed",
        )
        selected_pet = find_pet(selected_pet_id)
        st.session_state.selected_pet_id = selected_pet.id

# --- Header ---------------------------------------------------------------------

st.title("Today with your pets", icon=":material/pets:")

if selected_pet is None:
    st.info(
        "Add your first pet in the sidebar to start building a care plan.",
        title="Welcome to PawPal+",
        icon=":material/waving_hand:",
    )
    st.stop()

today = date.today()
all_tasks = owner.get_all_tasks()
due_today = [task for task in all_tasks if task.is_scheduled_for_date(today)]

metric_cols = st.columns(3)
metric_cols[0].metric("Pets", len(owner.pets), border=True)
metric_cols[1].metric("Care tasks", len(all_tasks), border=True)
metric_cols[2].metric("Due today", len(due_today), border=True)

tasks_tab, schedule_tab = st.tabs(
    [":material/checklist: Tasks", ":material/calendar_month: Daily schedule"]
)

# --- Tasks tab ------------------------------------------------------------------

with tasks_tab:
    with st.container(border=True):
        st.subheader(f"Add a task for {selected_pet.name}", icon=":material/add_task:")
        with st.form("add_task_form", clear_on_submit=True, border=False):
            title_col, duration_col = st.columns([3, 1])
            task_title = title_col.text_input("Task title", placeholder="Morning walk")
            duration_minutes = duration_col.number_input(
                "Duration (min)", min_value=1, max_value=240, value=20
            )

            priority_col, frequency_col, date_col, time_col = st.columns(4)
            priority = priority_col.segmented_control(
                "Priority",
                ["low", "medium", "high"],
                default="medium",
                format_func=str.capitalize,
            )
            frequency_value = frequency_col.segmented_control(
                "Frequency",
                [frequency.value for frequency in Frequency],
                default=Frequency.ONCE.value,
                format_func=str.capitalize,
            )
            scheduled_date = date_col.date_input("Start date", value=today)
            start_time = time_col.time_input(
                "Start time (optional)", value=None, step=300
            )

            split_col, submit_col = st.columns([3, 1], vertical_alignment="bottom")
            with split_col:
                is_splittable = st.toggle("Allow this task to be split", value=True)
                can_overlap = st.toggle(
                    "Can be done at the same time as other tasks", value=False
                )
            add_task_submitted = submit_col.form_submit_button(
                "Add task",
                icon=":material/add:",
                type="primary",
                width="stretch",
            )

    if add_task_submitted:
        try:
            selected_pet.add_task(
                CareTask(
                    title=task_title,
                    duration_minutes=int(duration_minutes),
                    priority=priority or "medium",
                    frequency=frequency_value or Frequency.ONCE.value,
                    scheduled_date=scheduled_date,
                    is_splittable=is_splittable,
                    can_overlap=can_overlap,
                    start_time=start_time.strftime("%H:%M") if start_time else None,
                )
            )
            st.session_state.pop("generated_plan", None)
            st.toast(
                f"Added {task_title.strip()} for {selected_pet.name}",
                icon=":material/check_circle:",
            )
            st.rerun()
        except (TypeError, ValueError) as error:
            st.error(str(error), icon=":material/error:")

    conflicts = scheduler.find_conflicts(owner)
    for conflict_index, conflict in enumerate(conflicts):
        with st.container(border=True):
            st.warning(
                conflict.message,
                title="Scheduling conflict",
                icon=":material/warning:",
            )
            slot_key = f"{conflict.slot_date}_{conflict.start_time}_{conflict_index}"
            pending = next(
                (
                    (pet_name, task)
                    for pet_name, task in conflict.entries
                    if task.id == st.session_state.get("pending_delete")
                ),
                None,
            )
            if pending is not None:
                pending_pet, pending_task = pending
                st.markdown(
                    f"**Delete {pending_task.title} ({pending_pet})?** "
                    "This removes the task."
                )
                confirm_row = st.container(horizontal=True)
                if confirm_row.button(
                    "Yes, delete",
                    key=f"confirm_{slot_key}",
                    icon=":material/delete:",
                    type="primary",
                ):
                    owner.get_pet(pending_task.pet_id).remove_task(pending_task.id)
                    st.session_state.pop("pending_delete", None)
                    st.session_state.pop("generated_plan", None)
                    st.toast(f"Deleted {pending_task.title}", icon=":material/delete:")
                    st.rerun()
                if confirm_row.button(
                    "Cancel", key=f"cancel_{slot_key}", icon=":material/close:"
                ):
                    st.session_state.pop("pending_delete", None)
                    st.rerun()
                continue

            st.markdown("**Can these be done at the same time?**")
            action_row = st.container(horizontal=True)
            if action_row.button(
                "Yes, same time",
                key=f"allow_{slot_key}",
                icon=":material/group:",
                type="primary",
            ):
                scheduler.allow_simultaneous(conflict)
                st.session_state.pop("generated_plan", None)
                st.toast(
                    f"Allowed overlapping tasks at {conflict.start_time}",
                    icon=":material/check_circle:",
                )
                st.rerun()
            for pet_name, task in conflict.entries:
                if action_row.button(
                    f"Delete {task.title} ({pet_name})",
                    key=f"delete_{slot_key}_{task.id}",
                    icon=":material/delete:",
                ):
                    st.session_state.pending_delete = task.id
                    st.rerun()
    if not conflicts and all_tasks:
        st.success(
            "No tasks share a start time, or overlaps are allowed.",
            title="No scheduling conflicts",
            icon=":material/check_circle:",
        )

    st.subheader(f"{selected_pet.name}'s tasks", icon=":material/pets:")
    open_tasks = [task for task in selected_pet.care_tasks if not task.is_complete]
    done_tasks = [task for task in selected_pet.care_tasks if task.is_complete]

    if not selected_pet.care_tasks:
        st.caption("No care tasks yet. Add one above.")

    for task in scheduler.sort_by_time(open_tasks):
        with st.container(border=True):
            info_col, action_col = st.columns([5, 1], vertical_alignment="center")
            with info_col:
                st.markdown(
                    f"**{task.title}** &nbsp; {priority_badge(task.priority.value)}"
                )
                st.caption(
                    f":material/timer: {task.duration_minutes} min · "
                    f"{describe_when(task)}"
                    + ("" if task.is_splittable else " · not splittable")
                )
            if action_col.button(
                "Done",
                key=f"done_{task.id}",
                icon=":material/check:",
                width="stretch",
            ):
                try:
                    scheduler.complete_task(
                        owner,
                        task.id,
                        task.scheduled_date
                        if task.frequency is not Frequency.ONCE
                        else None,
                    )
                    st.session_state.pop("generated_plan", None)
                    st.toast(f"Completed {task.title}", icon=":material/celebration:")
                    st.rerun()
                except (KeyError, ValueError) as error:
                    st.error(str(error))

    if done_tasks:
        with st.expander(f"Completed ({len(done_tasks)})", icon=":material/task_alt:"):
            for task in done_tasks:
                st.markdown(f"~~{task.title}~~ · {task.duration_minutes} min")

    st.subheader("All tasks", icon=":material/filter_list:")
    filter_cols = st.columns(2)
    pet_filter = filter_cols[0].selectbox(
        "Pet", ["All pets"] + [pet.name for pet in owner.pets]
    )
    status_filter = filter_cols[1].segmented_control(
        "Status", ["All", "Open", "Done"], default="All"
    )
    completed_filter = {"Open": False, "Done": True}.get(status_filter)
    matching = scheduler.filter_tasks(
        owner,
        pet_name=None if pet_filter == "All pets" else pet_filter,
        completed=completed_filter,
    )
    if matching:
        st.table(
            [
                {
                    "Start": task.start_time or "Any time",
                    "Task": task.title,
                    "Pet": find_pet(task.pet_id).name,
                    "Priority": task.priority.value.capitalize(),
                    "Minutes": task.duration_minutes,
                    "Repeats": task.frequency.value.capitalize(),
                    "Status": "Done" if task.is_complete else "Open",
                }
                for task in scheduler.sort_by_time(matching)
            ]
        )
        st.caption(f"{len(matching)} task(s), sorted by start time.")
    else:
        st.warning(
            "Try a different pet or status.",
            title="No tasks match these filters",
            icon=":material/search_off:",
        )

# --- Schedule tab ---------------------------------------------------------------

with schedule_tab:
    with st.container(border=True):
        scope = st.segmented_control(
            "Plan for",
            [selected_pet.id, "all"],
            default=selected_pet.id,
            format_func=lambda value: (
                "All pets" if value == "all" else selected_pet.name
            ),
        )
        plan_cols = st.columns([2, 2, 1], vertical_alignment="bottom")
        plan_date = plan_cols[0].date_input("Plan date", value=today)
        available_minutes = plan_cols[1].number_input(
            "Available time (minutes)", min_value=1, max_value=1440, value=120, step=5
        )
        if plan_cols[2].button(
            "Generate",
            icon=":material/auto_awesome:",
            type="primary",
            width="stretch",
        ):
            plan_pet_id = None if scope == "all" else selected_pet.id
            st.session_state.generated_plan = scheduler.generate_plan(
                owner=owner,
                task_date=plan_date,
                available_minutes=int(available_minutes),
                pet_id=plan_pet_id,
            )
            st.session_state.generated_plan_label = (
                "all pets" if plan_pet_id is None else selected_pet.name
            )

    plan = st.session_state.get("generated_plan")
    if plan is None:
        st.caption("Pick a date and your available time, then generate a schedule.")
    else:
        st.subheader(
            f"Schedule for {st.session_state.get('generated_plan_label', 'all pets')}"
            f" · {plan.date:%A, %B %d}",
            icon=":material/event:",
        )

        used = plan.total_planned_minutes
        plan_metrics = st.columns(3)
        plan_metrics[0].metric("Planned", f"{used} min", border=True)
        plan_metrics[1].metric("Available", f"{plan.available_minutes} min", border=True)
        plan_metrics[2].metric("Left over", f"{plan.get_remaining_time()} min", border=True)
        st.progress(
            min(used / plan.available_minutes, 1.0),
            text=f"{used} of {plan.available_minutes} minutes used",
        )

        plan_conflicts = scheduler.detect_conflicts(owner, plan.date)
        if plan_conflicts:
            st.warning(
                "\n".join(f"- {message}" for message in plan_conflicts),
                title="Heads up: overlapping start times",
                icon=":material/warning:",
            )

        if plan.scheduled_items:
            for item in plan.scheduled_items:
                task_pet = find_pet(item.task.pet_id)
                with st.container(border=True):
                    st.markdown(
                        f"**{item.task.title}** for {task_pet.name} &nbsp; "
                        f"{priority_badge(item.task.priority.value)} "
                        f":gray-badge[{item.planned_minutes} min]"
                    )
                    st.caption(item.get_explanation())
        else:
            st.info(
                "No eligible tasks are scheduled for this date.",
                icon=":material/event_busy:",
            )

        unscheduled = plan.get_unscheduled_tasks()
        if unscheduled:
            with st.expander(
                f"Still needs time ({len(unscheduled)})", icon=":material/pending:"
            ):
                for task in unscheduled:
                    st.markdown(f"- {task.title} ({find_pet(task.pet_id).name})")
