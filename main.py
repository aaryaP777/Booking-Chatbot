from fastapi import FastAPI
from pydantic import BaseModel
from calendar_agent import app as calendar_app

class Message(BaseModel):
    user_input: str
 
chat_history = []
   
app = FastAPI()

@app.post("/chat")

async def chat(msg: Message):
    global chat_history
    user_input = msg.user_input.lower().strip()

    # Handle confirmation
    if user_input in ["yes", "sure", "ok", "yep"]:
        if chat_history:
            last_result = chat_history[-1]

            suggested_start = last_result.get("suggested_start")
            suggested_end = last_result.get("suggested_end")

            if suggested_start and suggested_end:
                result = calendar_app.invoke({
                    "user_input": "book fallback slot",
                    "start_override": suggested_start,
                    "end_override": suggested_end,
                    "date": last_result.get("date"),
                    "time": last_result.get("time"),
                    "duration": last_result.get("duration"),
                })
                chat_history.append(result)

                if result.get("status") == "booked":
                    return {
                        "reply": f"Meeting booked!\n {result['start']} to {result['end']}\n📎 [Event Link]({result['event_link']})"
                    }
                else:
                    return {"reply": "Sorry that slot is booked too.."}

        return {"reply": "No suggested slot to confirm."}

    # Handle general intent input
    result = calendar_app.invoke({"user_input": user_input})
    chat_history.append(result)

    # Check what to respond with
    if result.get("available"):
        return {
            "reply": f"Meeting is available!\nDo you want to book for:\n\n {result['start']} to {result['end']}?"
        }
    elif result.get("suggested_start"):
        return {
            "reply": (
                "That time is busy.\n\n"
                f"Would you like to book instead at:\n\n {result['suggested_start']} to {result['suggested_end']}?"
            )
        }
    else:
        return {
            "reply": "No slots are available for your request. Try another time."
        }
