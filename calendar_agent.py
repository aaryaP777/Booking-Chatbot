from langgraph.graph import StateGraph, END
from langchain_groq import ChatGroq
from langchain.schema import SystemMessage, HumanMessage
from typing import TypedDict
import json
import os
from google_calendar import authenticate_google, is_time_slot_free, create_event, get_events
from dotenv import load_dotenv
load_dotenv()

llm = ChatGroq(
    temperature=0,
    model_name="llama3-70b-8192",
    groq_api_key=os.getenv("GROQ_API_KEY")
)

# Define the shared state type
class AgentState(TypedDict, total=False):
    user_input: str
    date: str
    time: str
    duration: str
    available: bool
    start: str
    end: str
    event_link: str
    status: str
    suggested_start: str
    suggested_end: str

# Define nodes

def parse_intent(state: AgentState):
    user_input = state["user_input"]

    messages = [
        SystemMessage(content="Extract intent to schedule a meeting. Reply ONLY in JSON. Keys: 'date', 'time', 'duration'."),
        HumanMessage(content=user_input)
    ]

    response = llm.invoke(messages)
    
    # print("LLM raw output: ", response.content)
    
    try:
        extracted = json.loads(response.content)  # simple JSON parsing for now
        print("Intent parsed:", extracted)
        return {
            "user_input": user_input,
            "date": extracted.get("date"),
            "time": extracted.get("time"),
            "duration": extracted.get("duration") or "30m"
        }
    except Exception as e:
        print("Parsing error:", e)
        return {"user_input": user_input}

def check_availability(state: AgentState):
    print("Checking availability...")
    
    service = authenticate_google()
    available, start, end, suggested = is_time_slot_free(
        service,
        state.get("date", ""),
        state.get("time", ""),
        state.get("duration", "30m")
    )
    
    if available:
        print(f"Slot is free: {start} to {end}")
        return {
            **state,
            "available": True,
            "start": start.isoformat(),
            "end": end.isoformat()
        }
    else:
        if suggested:
            print(f"Suggested: {suggested[0]} to {suggested[1]}")
            return {
                **state,
                "available": False,
                "suggested_start": suggested[0].isoformat(),
                "suggested_end": suggested[1].isoformat()
            }
        else:
            return {**state, "available": False}

def confirm_booking(state: AgentState):
    print(f"Should i book a meeting on {state['date']} at {state['time']} for {state['duration']}?")
    print("Auto-confirming for now.")
    return state

def book_slot(state: AgentState):
    print("Booking the slot...")

    service = authenticate_google()

    start_override = state.get("start_override")
    end_override = state.get("end_override")

    if start_override and end_override:
        start = start_override
        end = end_override
    else:
        # your usual logic to compute time from state['date'] and state['time']
        ...

    # check again before booking
    events = get_events(service, start, end)
    if len(events) > 0:
        return {**state, "available": False, "status": "conflict"}

    link = create_event(service, "AI Booking", start, end)

    return {
        **state,
        "start": start,
        "end": end,
        "event_link": link,
        "available": True,
        "status": "booked"
    }


# Build graph
workflow = StateGraph(AgentState)

workflow.add_node("parse_intent", parse_intent)
workflow.add_node("check_availability", check_availability)
workflow.add_node("confirm_booking", confirm_booking)
workflow.add_node("book_slot", book_slot)

# Define transitions
workflow.set_entry_point("parse_intent")
workflow.add_edge("parse_intent", "check_availability")
workflow.add_edge("check_availability", "confirm_booking")
workflow.add_edge("confirm_booking", "book_slot")
workflow.add_edge("book_slot", END)

app = workflow.compile()

if __name__ == "__main__":
    result = app.invoke({"user_input": "Can I book a slot tomorrow afternoon?"})
    print("Final result:", result)
