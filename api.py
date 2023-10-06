import uvicorn
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from models import BotStartModel, BotResponseModel, BotStatusResponseModel
from bot import run_bot
import threading
from fastapi.openapi.docs import get_swagger_ui_html, get_redoc_html
from fastapi.openapi.utils import get_openapi
from stop_thread import stop_thread
import asyncio

DEBUG = True
VERSION = "0.0.1"
PORT = 5987

BOT_LIMIT = 40

proxies = {
    # "http://jrpiplvy:p4z8h38ud023@104.143.224.52:5913": False,
    "http://jrpiplvy:p4z8h38ud023@193.36.172.251:6334": False,
    "http://jrpiplvy:p4z8h38ud023@104.239.91.47:5771": False,
}

username_to_proxy = {}

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


@app.get("/bot/status/{username}")
async def stop_bot(username: str) -> BotStatusResponseModel:
    if bot_threads.get(username):
        is_alive = bot_threads[username].is_alive()

        return BotStatusResponseModel(bot_status="ACTIVE" if is_alive else "STOPPED")

    return BotStatusResponseModel(bot_status="STOPPED")


@app.post("/bot/start")
async def start_bot(body: BotStartModel) -> BotResponseModel:
    active_bots = sum(
        1 for thread in bot_threads.values() if thread != None and thread.is_alive()
    )

    if active_bots >= BOT_LIMIT:
        return BotResponseModel(
            message="Bot limit reached",
            total_bots=active_bots,
        )

    if bot_threads.get(body.username):
        stop_thread(bot_threads[body.username].ident)
        bot_threads[body.username] = None
        
        if username_to_proxy.get(body.username):
            proxies[username_to_proxy[body.username]] = False
            username_to_proxy[body.username] = None

    for proxy in proxies:
        if not proxies[proxy]:
            proxies[proxy] = True
            body.proxy = proxy
            break

    print("using proxy", body.proxy)
    if body.proxy:
        username_to_proxy[body.username] = body.proxy

    bot_t = threading.Thread(target=run_bot, args=(body,))
    bot_threads[body.username] = bot_t
    bot_threads[body.username].daemon = True
    bot_threads[body.username].start()

    await asyncio.sleep(5)

    return BotResponseModel(
        message="Bot started",
        total_bots=active_bots,
    )


@app.post("/bot/stop/{username}")
async def stop_bot(username: str):
    if bot_threads.get(username):
        stop_thread(bot_threads[username].ident)
        bot_threads[username] = None
        proxies[username_to_proxy[username]] = False
        username_to_proxy[username] = None

    return BotResponseModel(
        message="Bot stopped",
        total_bots=sum(
            1 for thread in bot_threads.values() if thread != None and thread.is_alive()
        ),
    )


if __name__ == "__main__":
    print("start")
    uvicorn.run(app, host="0.0.0.0", port=PORT)
