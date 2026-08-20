"""Streamlit dashboard for LangSmith observability & benchmarking of the incident agent."""
import os
import uuid
from datetime import datetime, timedelta

import streamlit as st
from langsmith import Client
from langchain_core.tracers.context import collect_runs

from config.settings import settings
from data.generate_docs import main as generate_mock_docs
from graph.graph_builder import compiled_guarded_graph
from services.memory_service import mem0_service

st.set_page_config(page_title="Incident Agent | LangSmith Console", layout="wide")

if not settings.KB_FILE_PATH.exists():
    generate_mock_docs()

with st.sidebar:
    st.header("🛠️ LangSmith Runtime Settings")
    tracing_enabled = st.toggle(
        "Enable LangSmith Tracing",
        value=os.environ.get("LANGCHAIN_TRACING_V2", settings.LANGCHAIN_TRACING_V2).lower() == "true",
        key="tracing_enabled",
    )
    project_name = st.text_input(
        "LangSmith Project",
        value=os.environ.get("LANGCHAIN_PROJECT", settings.LANGCHAIN_PROJECT),
        key="project_name",
    ).strip() or settings.LANGCHAIN_PROJECT

    # LangChain's tracer reads these env vars at call time, so update them live.
    os.environ["LANGCHAIN_TRACING_V2"] = "true" if tracing_enabled else "false"
    os.environ["LANGCHAIN_PROJECT"] = project_name

    st.caption(f"Tracing: {'🟢 ON' if tracing_enabled else '🔴 OFF'} · Project: `{project_name}`")


def get_client() -> Client:
    return Client(api_key=settings.LANGCHAIN_API_KEY) if settings.LANGCHAIN_API_KEY else Client()


def log_feedback(run_id: str, score: float, label: str) -> bool:
    """Logs a human feedback score against a LangSmith run id. Returns True on success."""
    try:
        get_client().create_feedback(run_id=run_id, key="user_score", score=score)
        st.session_state.setdefault("feedback_by_run", {})[run_id] = label
        return True
    except Exception as e:
        st.error(f"Failed to log feedback: {e}")
        return False


def build_initial_state(query: str, user_name: str, department: str) -> dict:
    user_id = user_name.lower().replace(" ", "_")
    return {
        "user_name": user_name,
        "user_id": user_id,
        "department": department,
        "raw_query": query,
        "sanitized_query": "",
        "user_preferences": mem0_service.get_user_memories(user_id),
        "guardrail_passed": True,
        "guardrail_violation_reason": "",
        "intent": "Unclassified",
        "sub_category": "",
        "retrieved_docs": [],
        "telemetry_data": {},
        "code_analysis_data": {},
        "billing_data": {},
        "solution": "",
        "confidence_score": 0,
        "is_cached_response": False,
        "retry_count": 0,
        "human_approved": False,
        "human_feedback": "",
        "visited_nodes": ["START"],
        "execution_logs": ["Streamlit session initiated"],
    }


def execute_query(query: str, user_name: str, department: str, tags: list[str]) -> tuple[dict, str | None]:
    """Runs the graph while capturing the root LangSmith run id via the tracing callback."""
    initial_state = build_initial_state(query, user_name, department)
    thread_id = str(uuid.uuid4())[:8]
    run_config = {
        "configurable": {"thread_id": thread_id},
        "tags": tags,
        "metadata": {"user_id": initial_state["user_id"], "department": department},
    }
    with collect_runs() as cb:
        final_state = compiled_guarded_graph.invoke(initial_state, config=run_config)
        run_id = str(cb.traced_runs[0].id) if cb.traced_runs else None
    return final_state, run_id


st.title("🔎 LangSmith & Streamlit Activity Console")

# ---------------------------------------------------------------------------
# Task 1: LangSmith Configuration Panel
# ---------------------------------------------------------------------------
with st.expander("⚙️ Task 1 — LangSmith Configuration Panel", expanded=True):
    col1, col2, col3 = st.columns(3)
    col1.metric("Tracing Enabled", os.environ["LANGCHAIN_TRACING_V2"])
    col2.metric("Project", os.environ["LANGCHAIN_PROJECT"])
    col3.metric("API Key Configured", "Yes" if settings.LANGCHAIN_API_KEY else "No")

    if st.button("Test LangSmith Connection"):
        try:
            client = get_client()
            list(client.list_runs(project_name=project_name, limit=1))
            st.success(f"Connected to project '{project_name}' successfully.")
        except Exception as e:
            st.error(f"Connection failed: {e}")

# ---------------------------------------------------------------------------
# Task 2: Query Execution & Run ID Display
# ---------------------------------------------------------------------------
st.header("▶️ Task 2 — Query Execution & Run ID Display")
with st.form("query_form"):
    q_col1, q_col2 = st.columns(2)
    user_name = q_col1.text_input("User name", value="Neeraj")
    department = q_col2.text_input("Department", value="Infrastructure")
    query = st.text_area(
        "Incident description",
        value="Production EC2 instance CPU utilization is continuously above 95%.",
    )
    submitted = st.form_submit_button("Run Agent")

if submitted:
    with st.spinner("Executing LangGraph pipeline..."):
        final_state, run_id = execute_query(query, user_name, department, tags=["streamlit_console"])
    st.session_state["last_final_state"] = final_state
    st.session_state["last_run_id"] = run_id

if "last_final_state" in st.session_state:
    final_state = st.session_state["last_final_state"]
    run_id = st.session_state.get("last_run_id")
    feedback_by_run = st.session_state.setdefault("feedback_by_run", {})
    recorded_feedback = feedback_by_run.get(run_id)

    feedback_badge = ""
    if recorded_feedback == "positive":
        feedback_badge = " · Feedback: 👍 Correct"
    elif recorded_feedback == "negative":
        feedback_badge = " · Feedback: 👎 Incorrect"

    st.success(
        f"Run ID: `{run_id}`{feedback_badge}" if run_id else "Run ID unavailable (tracing may be disabled)."
    )
    st.write("**Guardrail Passed:**", final_state.get("guardrail_passed"))
    st.write("**Confidence Score:**", final_state.get("confidence_score"))
    st.write("**Path Executed:**", " ➔ ".join(final_state.get("visited_nodes", [])))
    st.text_area("Solution", value=final_state.get("solution", ""), height=180, disabled=True)

    # -----------------------------------------------------------------------
    # Task 3: Simple Human Feedback Buttons
    # -----------------------------------------------------------------------
    st.subheader("👍👎 Task 3 — Human Feedback")
    fb_col1, fb_col2, fb_col3 = st.columns([1, 1, 4])
    feedback_disabled = not run_id

    if fb_col1.button("👍 Correct", disabled=feedback_disabled):
        log_feedback(run_id, score=1.0, label="positive")

    if fb_col2.button("👎 Incorrect", disabled=feedback_disabled):
        log_feedback(run_id, score=0.0, label="negative")

    recorded_feedback = feedback_by_run.get(run_id)
    if recorded_feedback:
        fb_col3.info(f"Feedback recorded: {recorded_feedback}")
    if feedback_disabled:
        st.caption("Feedback disabled — no run id was captured for this execution.")

# ---------------------------------------------------------------------------
# Task 4: 3-Query Benchmark Test Runner
# ---------------------------------------------------------------------------
st.header("🧪 Task 4 — 3-Query Benchmark Test Runner")
BENCHMARK_QUERIES = [
    {"raw_query": "Production EC2 instance CPU utilization is continuously above 95%.", "user_name": "Neeraj", "department": "Infrastructure"},
    {"raw_query": "Please assist user admin@company.com at IP 192.168.1.50 with server outage.", "user_name": "Alice", "department": "DevOps"},
    {"raw_query": "AWS bill increased unexpectedly by 40% this month.", "user_name": "FinanceUser", "department": "Finance"},
]

if st.button("Run 3-Query Benchmark"):
    results = []
    progress = st.progress(0.0)
    for idx, case in enumerate(BENCHMARK_QUERIES):
        final_state, run_id = execute_query(
            case["raw_query"], case["user_name"], case["department"], tags=["streamlit_benchmark"]
        )
        results.append(
            {
                "Query": case["raw_query"][:60] + ("..." if len(case["raw_query"]) > 60 else ""),
                "Guardrail Passed": final_state.get("guardrail_passed"),
                "Confidence": final_state.get("confidence_score"),
                "Run ID": run_id,
            }
        )
        progress.progress((idx + 1) / len(BENCHMARK_QUERIES))
    st.session_state["benchmark_results"] = results

if "benchmark_results" in st.session_state:
    st.table(st.session_state["benchmark_results"])

# ---------------------------------------------------------------------------
# Task 5: Recent Runs & Error Log Viewer
# ---------------------------------------------------------------------------
st.header("📜 Task 5 — Recent Runs & Error Log Viewer")
run_limit = st.slider("Number of recent runs to fetch", min_value=5, max_value=50, value=15)

if st.button("Refresh Recent Runs"):
    try:
        client = get_client()
        runs = list(
            client.list_runs(
                project_name=project_name,
                limit=run_limit,
                start_time=datetime.utcnow() - timedelta(days=7),
            )
        )
        st.session_state["recent_runs"] = runs
    except Exception as e:
        st.error(f"Failed to fetch runs: {e}")

if "recent_runs" in st.session_state:
    runs = st.session_state["recent_runs"]
    feedback_by_run = st.session_state.get("feedback_by_run", {})
    run_rows = [
        {
            "Name": r.name,
            "Status": r.status,
            "Start Time": str(r.start_time),
            "Latency (s)": round((r.end_time - r.start_time).total_seconds(), 2) if r.end_time and r.start_time else None,
            "Feedback": feedback_by_run.get(str(r.id), ""),
            "Error": r.error or "",
        }
        for r in runs
    ]
    st.dataframe(run_rows, use_container_width=True)

    error_rows = [row for row in run_rows if row["Error"]]
    st.subheader("Error Log")
    if error_rows:
        st.dataframe(error_rows, use_container_width=True)
    else:
        st.caption("No errors found in the fetched run window.")
