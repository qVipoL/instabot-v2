import uvicorn
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from models import BotStartModel, BotResponseModel
from bot import run_bot
import threading
from fastapi.openapi.docs import get_swagger_ui_html, get_redoc_html
from fastapi.openapi.utils import get_openapi

DEBUG = True
VERSION = "0.0.1"
PORT = 5555

bot_threads = {}

app = FastAPI(
    debug=DEBUG,
    title="Instabot API",
    version=VERSION,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    return get_swagger_ui_html(openapi_url="/openapi.json", title="API Documentation")


@app.get("/openapi.json", include_in_schema=False)
async def get_open_api_endpoint():
    return get_openapi(
        title="API Documentation",
        version="0.0.1",
        description="This is the API documentation for my FastAPI project.",
        routes=app.routes,
    )


@app.get("/redoc", include_in_schema=False)
async def redoc_html():
    return get_redoc_html(openapi_url="/openapi.json", title="API Documentation")


@app.post("/bot/start")
async def start_bot(body: BotStartModel) -> BotResponseModel:
    if bot_threads.get(body.username):
        bot_threads[body.username].terminate()

    bot_t = threading.Thread(target=run_bot, args=(body,))
    bot_threads[body.username] = bot_t
    bot_threads[body.username].daemon = True
    bot_threads[body.username].start()

    return BotResponseModel(
        message="Bot started",
        total_bots=len(bot_threads.keys()),
    )


if __name__ == "__main__":
    print("start")
    uvicorn.run(app, host="0.0.0.0", port=PORT)
