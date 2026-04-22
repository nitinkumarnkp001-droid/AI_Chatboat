from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
import os

from groq import Groq
from database import collection

load_dotenv()

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

# Groq setup
client = Groq(api_key=os.getenv("GROQ_API_KEY"))
MODEL_NAME = "llama-3.1-8b-instant"


# Chatbot function
def get_bot_response(user_input):
    try:
        prompt = f"""
        You are a helpful customer support chatbot.
        Answer clearly and briefly.

        User: {user_input}
        """

        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[{"role": "user", "content": prompt}]
        )

        return response.choices[0].message.content.strip()

    except Exception as e:
        print("Groq Error:", e)
        return "Sorry, something went wrong."


# Home route
@app.get("/", response_class=HTMLResponse)
async def home():
    with open("templates/index.html", "r") as f:
        return f.read()


# Chat API
@app.post("/chat")
async def chat(request: Request):
    data = await request.json()
    user_input = data.get("message")

    bot_response = get_bot_response(user_input)

    # Save in MongoDB
    collection.insert_one({
        "user_input": user_input,
        "bot_response": bot_response
    })

    return {"response": bot_response}


# Chat history
@app.get("/history")
async def history():
    logs = list(collection.find({}, {"_id": 0}))

    return logs

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)