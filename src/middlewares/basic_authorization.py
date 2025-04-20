import os
import typing
import blacksheep

async def check_authorization(request: blacksheep.Request,
    next_handler : typing.Callable[..., typing.Awaitable[blacksheep.Response]]) -> blacksheep.Response:
    token = request.headers.get_first(b"Authorization") or b""
    if token.startswith(b"Bearer "):
        token = token[7:]
    
    if token.decode("ascii") != os.environ.get("PASSWORD"):
        raise blacksheep.HTTPException(401, "Unauthorized")
    
    return await next_handler(request)
