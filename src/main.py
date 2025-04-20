import logging
import blacksheep
import middlewares.basic_authorization

logger = logging.getLogger(__name__)
app = blacksheep.Application()

app.add_cors_policy("oldapi", allow_methods="GET,POST,OPTIONS", allow_origins="*")
app.middlewares.append(middlewares.basic_authorization.check_authorization)

@blacksheep.get("/v1/models")
@blacksheep.get("/models")
async def models(request : blacksheep.Request) -> blacksheep.Response:
    ...

@blacksheep.post("/v1/chat/completions")
@blacksheep.post("/chat/completions")
async def chat_completions(request : blacksheep.Request) -> blacksheep.Response:
    ...
