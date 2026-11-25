from langgraph.graph import END, START, StateGraph

from app.ask_user import collect_answer
from app.check_node import check_resume
from app.email_node import write_email
from app.gap_node import analyze_gap
from app.resume_node import write_resume
from app.state import AgentState
from app.utils.email_extractor import extract_emails

MAX_ATTEMPTS = 3


def gap_step(state: AgentState):
    return {"report": analyze_gap(state["resume"], state["jd"])}


def ask_step(state: AgentState):
    # The web app passes answers in, so no input box is needed there.
    if state.get("answers") is not None:
        return {}
    return {"answers": collect_answer(state["report"].questions_for_user)}


def write_step(state: AgentState):
    check = state.get("check")
    feedback = check.unsupported_claims if check else None
    new_resume = write_resume(
        state["resume"], state["jd"], state["report"], state["answers"], feedback
    )
    return {"new_resume": new_resume, "attempts": state.get("attempts", 0) + 1}


def check_step(state: AgentState):
    return {
        "check": check_resume(state["resume"], state["new_resume"], state["answers"])
    }


def resolve_email_step(state: AgentState):
    # Only extract. If there is no single email, the UI asks the user.
    emails = extract_emails(state["jd"])
    to_email = state.get("to_email") or (emails[0] if len(emails) == 1 else "")
    return {"emails": emails, "to_email": to_email}


def email_step(state: AgentState):
    return {"email_draft": write_email(state["new_resume"], state["jd"])}


def route_start(state: AgentState):
    # If the gap report already exists (web flow), skip the gap node.
    return "ask" if state.get("report") else "gap"


def route_after_check(state: AgentState):
    if state["check"].is_safe:
        return "resolve_email"
    if state["attempts"] >= MAX_ATTEMPTS:
        return END  # unsafe resume: never email it
    return "write"


def build_graph():
    g = StateGraph(AgentState)
    g.add_node("gap", gap_step)
    g.add_node("ask", ask_step)
    g.add_node("write", write_step)
    g.add_node("check", check_step)
    g.add_node("resolve_email", resolve_email_step)
    g.add_node("email", email_step)

    g.add_conditional_edges(START, route_start, {"gap": "gap", "ask": "ask"})
    g.add_edge("gap", "ask")
    g.add_edge("ask", "write")
    g.add_edge("write", "check")
    g.add_conditional_edges(
        "check",
        route_after_check,
        {"write": "write", "resolve_email": "resolve_email", END: END},
    )
    g.add_edge("resolve_email", "email")
    g.add_edge("email", END)

    return g.compile()