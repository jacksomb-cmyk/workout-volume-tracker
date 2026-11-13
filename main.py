"""
Workout Tonnage & Progression Tracker
CISC 106 Final Project
Allows lifters to track workout volume (sets x reps x weight) and evaluates
weekly training tonnage against optimal recovery and progression thresholds.
"""

from dataclasses import dataclass, field
from bakery import assert_equal
from drafter import (
    route,
    start_server,
    set_site_information,
    Page,
    Header,
    Text,
    Button,
    TextBox,
    SelectBox,
    CheckBox,
    HorizontalRule,
    BulletedList,
    NumberedList,
)

# Global Constants 
MAX_OPTIMAL_TONNAGE = 15000.0
MIN_OPTIMAL_TONNAGE = 5000.0


@dataclass
class WorkoutEntry:
    """Represents a single logged exercise entry."""
    exercise_name: str
    body_part: str  # "Upper" or "Lower"
    sets: int
    reps: int
    weight: float
    completed: bool


@dataclass
class State:
    """Stores persistent application state across routes."""
    current_page: str
    user_name: str
    weekly_frequency: int
    workouts: list[WorkoutEntry]


def calculate_entry_volume(entry: WorkoutEntry) -> float:
    """Calculates total tonnage (sets * reps * weight) for a single entry."""
    return float(entry.sets * entry.reps * entry.weight)


def compute_volume_breakdown(workouts: list[WorkoutEntry]) -> tuple[float, float, float]:
    """
    Iterates over logged workouts to compute total, upper-body, and
    lower-body training tonnage.
    """
    total_tonnage = 0.0
    upper_tonnage = 0.0
    lower_tonnage = 0.0

    for entry in workouts:
        session_volume = calculate_entry_volume(entry)
        total_tonnage += session_volume

        if entry.body_part == "Upper":
            upper_tonnage += session_volume
        else:
            lower_tonnage += session_volume

    return total_tonnage, upper_tonnage, lower_tonnage


def parse_positive_int(raw_value: str, fallback: int) -> int:
    """Safely converts a string input into a non-negative integer."""
    cleaned = raw_value.strip()
    if cleaned.isdigit():
        return int(cleaned)
    return fallback


def parse_positive_float(raw_value: str, fallback: float) -> float:
    """Safely converts a string input into a non-negative float."""
    cleaned = raw_value.strip()
    parts = cleaned.split(".")
    if len(parts) == 1 and parts[0].isdigit():
        return float(cleaned)
    if len(parts) == 2 and parts[0].isdigit() and parts[1].isdigit():
        return float(cleaned)
    return fallback


def build_navigation_bar() -> list:
    """Returns standard navigation buttons shared across pages."""
    return [
        HorizontalRule(),
        Button("Home Dashboard", index),
        Button("Profile Setup", setup_user_page),
        Button("Log Workout", add_workout_page),
        Button("Volume Summary", view_summary_page),
        Button("Progression Feedback", feedback_page),
    ]



@route
def index(state: State) -> Page:
    """Route 1 (Page 1): Home dashboard showing quick stats and navigation."""
    state.current_page = "home"
    total_vol, _, _ = compute_volume_breakdown(state.workouts)
    estimated_weekly = total_vol * state.weekly_frequency

    if state.user_name.strip() == "":
        greeting = "Welcome, Lifter! Please complete your Profile Setup first."
        setup_notice = Text(
            "Tip: Set your name and weekly training days before logging workouts."
        )
    else:
        greeting = f"Welcome back, {state.user_name}!"
        setup_notice = Text(
            f"Target Weekly Frequency: {state.weekly_frequency} sessions/week"
        )

    content = [
        Header("Workout Tonnage & Progression Tracker"),
        Text(greeting),
        setup_notice,
        HorizontalRule(),
        Header("Quick Stats Snapshot", 3),
        BulletedList([
            f"Logged Exercises: {len(state.workouts)}",
            f"Single-Rotation Tonnage: {total_vol:,.1f} lbs",
            f"Estimated Weekly Tonnage: {estimated_weekly:,.1f} lbs",
        ]),
    ] + build_navigation_bar()

    return Page(state, content)


@route
def setup_user_page(state: State) -> Page:
    """Route 2 (Page 2): Form page to configure user name and weekly frequency."""
    state.current_page = "setup"

    content = [
        Header("User Profile Setup"),
        Text("Enter your name and how many days per week you train."),
        Text("Your Name:"),
        TextBox("name", state.user_name),
        Text("Weekly Training Frequency (days/week):"),
        SelectBox("freq", ["1", "2", "3", "4", "5", "6"], str(state.weekly_frequency)),
        Button("Save Profile", update_user_state),
    ] + build_navigation_bar()

    return Page(state, content)


@route
def update_user_state(state: State, name: str, freq: str) -> Page:
    """Route 3 (Action Route): Saves profile inputs into State and returns home."""
    state.user_name = name.strip()
    state.weekly_frequency = parse_positive_int(freq, 3)
    return index(state)


@route
def add_workout_page(state: State) -> Page:
    """Route 4 (Page 3): Form page to log a new exercise entry."""
    state.current_page = "add_workout"

    if state.user_name.strip() == "":
        warning = Text(
            "Notice: Your profile name is currently blank. You can still log "
            "exercises or visit Profile Setup first."
        )
    else:
        warning = Text(f"Logging workout entry for {state.user_name}:")

    content = [
        Header("Log New Exercise"),
        warning,
        Text("Exercise Name (e.g., Bench Press, Squat):"),
        TextBox("name", "Bench Press"),
        Text("Target Body Area:"),
        SelectBox("body_part", ["Upper", "Lower"], "Upper"),
        Text("Number of Sets:"),
        TextBox("sets", "3"),
        Text("Reps per Set:"),
        TextBox("reps", "10"),
        Text("Load / Weight (lbs):"),
        TextBox("weight", "135"),
        CheckBox("completed", True),
        Text("Check box above if all sets were completed in full."),
        Button("Submit Workout", submit_workout),
    ] + build_navigation_bar()

    return Page(state, content)


@route
def submit_workout(
    state: State,
    name: str,
    body_part: str,
    sets: str,
    reps: str,
    weight: str,
    completed: bool,
) -> Page:
    """Route 5 (Action Route): Appends a validated WorkoutEntry to State."""
    clean_name = name.strip() if name.strip() != "" else "Unnamed Exercise"
    parsed_sets = parse_positive_int(sets, 1)
    parsed_reps = parse_positive_int(reps, 1)
    parsed_weight = parse_positive_float(weight, 0.0)

    new_entry = WorkoutEntry(
        exercise_name=clean_name,
        body_part=body_part,
        sets=parsed_sets,
        reps=parsed_reps,
        weight=parsed_weight,
        completed=completed,
    )
    state.workouts.append(new_entry)
    return view_summary_page(state)


@route
def view_summary_page(state: State) -> Page:
    """Route 6 (Page 4): Lists all logged exercises and combined tonnage."""
    state.current_page = "summary"
    total_vol, upper_vol, lower_vol = compute_volume_breakdown(state.workouts)

    workout_descriptions = []
    for entry in state.workouts:
        vol = calculate_entry_volume(entry)
        status_label = "Completed" if entry.completed else "Incomplete"
        workout_descriptions.append(
            f"{entry.exercise_name} ({entry.body_part}) — "
            f"{entry.sets}x{entry.reps} @ {entry.weight} lbs = "
            f"{vol:,.1f} lbs [{status_label}]"
        )

    if len(workout_descriptions) == 0:
        workout_section = [Text("No workouts logged yet. Add one to see stats!")]
    else:
        workout_section = [NumberedList(workout_descriptions)]

    content = [
        Header("Volume Summary"),
        Text(f"Total Combined Tonnage: {total_vol:,.1f} lbs"),
        BulletedList([
            f"Upper Body Tonnage: {upper_vol:,.1f} lbs",
            f"Lower Body Tonnage: {lower_vol:,.1f} lbs",
        ]),
        HorizontalRule(),
        Header("Logged Exercises", 3),
    ] + workout_section + build_navigation_bar()

    return Page(state, content)


@route
def feedback_page(state: State) -> Page:
    """Route 7 (Page 5): Evaluates weekly tonnage and gives progression advice."""
    state.current_page = "feedback"
    total_vol, upper_vol, lower_vol = compute_volume_breakdown(state.workouts)
    weekly_tonnage = total_vol * state.weekly_frequency

    if len(state.workouts) == 0:
        status_title = "No Data Available"
        recommendation = (
            "Log at least one workout entry so we can evaluate your weekly "
            "volume and recovery range."
        )
    elif weekly_tonnage > MAX_OPTIMAL_TONNAGE:
        status_title = "Above Optimal Range (Overtraining Risk)"
        recommendation = (
            f"Your estimated weekly tonnage ({weekly_tonnage:,.1f} lbs) exceeds "
            f"{MAX_OPTIMAL_TONNAGE:,.0f} lbs. Consider reducing sets or load "
            "next session to ensure proper recovery."
        )
    elif weekly_tonnage < MIN_OPTIMAL_TONNAGE:
        status_title = "Below Optimal Range (Room to Progress)"
        recommendation = (
            f"Your estimated weekly tonnage ({weekly_tonnage:,.1f} lbs) is under "
            f"{MIN_OPTIMAL_TONNAGE:,.0f} lbs. Gradually add 1-2 sets or increase "
            "load by 5 lbs to stimulate progression."
        )
    else:
        status_title = "Within Optimal Range"
        recommendation = (
            f"Your estimated weekly tonnage ({weekly_tonnage:,.1f} lbs) sits right "
            "in the ideal 5,000 - 15,000 lbs progression zone. Maintain your "
            "current routine and focus on clean form."
        )

    content = [
        Header("Progression & Recovery Feedback"),
        Text(f"Weekly Frequency: {state.weekly_frequency}x per week"),
        Text(f"Estimated Weekly Tonnage: {weekly_tonnage:,.1f} lbs"),
        Text(f"Upper vs. Lower Split: {upper_vol:,.1f} lbs / {lower_vol:,.1f} lbs"),
        HorizontalRule(),
        Header(status_title, 3),
        Text(recommendation),
    ] + build_navigation_bar()

    return Page(state, content)







# Helper Function Unit Tests
sample_entry = WorkoutEntry("Squat", "Lower", 3, 10, 135.0, True)
assert_equal(calculate_entry_volume(sample_entry), 4050.0)
assert_equal(
    compute_volume_breakdown([
        sample_entry,
        WorkoutEntry("Bench", "Upper", 3, 10, 100.0, True),
    ]),
    (7050.0, 3000.0, 4050.0),
)
assert_equal(parse_positive_int("4", 1), 4)
assert_equal(parse_positive_int("abc", 1), 1)
assert_equal(parse_positive_float("135.5", 0.0), 135.5)

# Route Unit Tests (All 7 Routes Tested)
test_state = State("home", "", 3, [])
assert_equal(isinstance(index(test_state), Page), True)
assert_equal(test_state.current_page, "home")

assert_equal(isinstance(setup_user_page(test_state), Page), True)
assert_equal(test_state.current_page, "setup")

assert_equal(isinstance(update_user_state(test_state, "Jackson", "4"), Page), True)
assert_equal(test_state.user_name, "Jackson")
assert_equal(test_state.weekly_frequency, 4)

assert_equal(isinstance(add_workout_page(test_state), Page), True)
assert_equal(test_state.current_page, "add_workout")

assert_equal(
    isinstance(
        submit_workout(test_state, "Deadlift", "Lower", "3", "5", "225", True),
        Page,
    ),
    True,
)
assert_equal(len(test_state.workouts), 1)
assert_equal(test_state.workouts[0].exercise_name, "Deadlift")

assert_equal(isinstance(view_summary_page(test_state), Page), True)
assert_equal(test_state.current_page, "summary")

assert_equal(isinstance(feedback_page(test_state), Page), True)
assert_equal(test_state.current_page, "feedback")

# Launch Server
if __name__ == "__main__":
    start_server(State("home", "", 3, []))
