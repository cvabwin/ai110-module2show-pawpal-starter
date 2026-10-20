from datetime import date

import streamlit as st

from pawpal_system import CareTask, Frequency, Owner, Pet, Scheduler


st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

if "owner" not in st.session_state:
    st.session_state.owner = Owner(name="Jordan")

owner: Owner = st.session_state.owner
scheduler = Scheduler()

st.title("🐾 PawPal+")
st.caption(f"Care planning for {owner.name} and their pets")

st.subheader("Add a Pet")
with st.form("add_pet_form", clear_on_submit=True):
    pet_name = st.text_input("Pet name")
    species = st.selectbox("Species", ["dog", "cat", "other"])
    add_pet_submitted = st.form_submit_button("Add pet")

if add_pet_submitted:
    try:
        pet = Pet(name=pet_name, species=species)
        owner.add_pet(pet)
        st.session_state.selected_pet_id = pet.id
        st.session_state.pop("generated_plan", None)
        st.success(f"Added {pet.name}.")
    except ValueError as error:
        st.error(str(error))

if not owner.pets:
    st.info("Add a pet to start building a care plan.")
    st.stop()

pet_ids = [pet.id for pet in owner.pets]
selected_pet_id = st.selectbox(
    "Select a pet",
    pet_ids,
    index=(
        pet_ids.index(st.session_state.selected_pet_id)
        if st.session_state.get("selected_pet_id") in pet_ids
        else 0
    ),
    format_func=lambda pet_id: next(
        f"{pet.name} ({pet.species})" for pet in owner.pets if pet.id == pet_id
    ),
)
selected_pet = owner.get_pet(selected_pet_id)
st.session_state.selected_pet_id = selected_pet.id

st.subheader(f"Add a Task for {selected_pet.name}")
with st.form("add_task_form", clear_on_submit=True):
    task_title = st.text_input("Task title")
    duration_minutes = st.number_input(
        "Duration (minutes)", min_value=1, max_value=240, value=20
    )
    priority = st.selectbox("Priority", ["low", "medium", "high"], index=2)
    frequency_value = st.selectbox(
        "Frequency",
        [frequency.value for frequency in Frequency],
        format_func=lambda value: value.capitalize(),
    )
    scheduled_date = st.date_input("Start or scheduled date", value=date.today())
    is_splittable = st.checkbox("Allow this task to be split", value=True)
    add_task_submitted = st.form_submit_button("Add task")

if add_task_submitted:
    try:
        selected_pet.add_task(
            CareTask(
                title=task_title,
                duration_minutes=int(duration_minutes),
                priority=priority,
                frequency=frequency_value,
                scheduled_date=scheduled_date,
                is_splittable=is_splittable,
            )
        )
        st.session_state.pop("generated_plan", None)
        st.success(f"Added {task_title.strip()} for {selected_pet.name}.")
    except (TypeError, ValueError) as error:
        st.error(str(error))

st.subheader("Pets and Care Tasks")
for pet in owner.pets:
    with st.expander(f"{pet.name} ({pet.species})", expanded=pet.id == selected_pet.id):
        if pet.care_tasks:
            st.table(
                [
                    {
                        "Task": task.title,
                        "Duration (min)": task.duration_minutes,
                        "Priority": task.priority.value,
                        "Frequency": task.frequency.value,
                        "Scheduled date": (
                            task.scheduled_date.isoformat()
                            if task.scheduled_date
                            else "Any eligible day"
                        ),
                        "Status": (
                            "Complete"
                            if task.is_complete
                            or task.is_complete_for_date(date.today())
                            else "In progress"
                        ),
                    }
                    for task in pet.care_tasks
                ]
            )
        else:
            st.info("No care tasks added for this pet yet.")

st.subheader("Build Today's Schedule")
available_minutes = st.number_input(
    "Available time today (minutes)",
    min_value=1,
    max_value=1440,
    value=120,
    step=5,
)
plan_date = st.date_input("Plan date", value=date.today())

if st.button("Generate schedule"):
    st.session_state.generated_plan = scheduler.generate_plan(
        owner=owner,
        task_date=plan_date,
        available_minutes=int(available_minutes),
    )

plan = st.session_state.get("generated_plan")
if plan is not None:
    st.markdown(f"### Schedule for {plan.date:%B %d, %Y}")
    if plan.scheduled_items:
        for item in plan.scheduled_items:
            task_pet = next(
                pet for pet in owner.pets if pet.id == item.task.pet_id
            )
            st.markdown(
                f"- **{item.task.title}** for {task_pet.name} — "
                f"{item.planned_minutes} min ({item.task.priority.value} priority)"
            )
            st.caption(item.get_explanation())
    else:
        st.info("No eligible tasks are scheduled for this date.")
    st.caption(
        f"Planned {plan.total_planned_minutes} of "
        f"{plan.available_minutes} available minutes."
    )
    unscheduled = plan.get_unscheduled_tasks()
    if unscheduled:
        st.markdown("**Still needs time or completion:**")
        for task in unscheduled:
            pet = next(pet for pet in owner.pets if pet.id == task.pet_id)
            st.write(f"- {task.title} ({pet.name})")
