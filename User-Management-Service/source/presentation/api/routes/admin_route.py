from collections.abc import Callable, Coroutine
from fastapi import Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.routing import APIRoute
from fastapi.responses import JSONResponse
from source.application.exceptions import UserNotFoundError


class AdminRoute(APIRoute):
    def get_route_handler(
        self,
    ) -> Callable[[Request], Coroutine[object, object, Response]]:
        original = super().get_route_handler()

        async def handler(request: Request) -> Response:
            try:
                return await original(request)
            except RequestValidationError as error:
                code = "invalid_request"
                if any(
                    item.get("type") == "literal_error"
                    and item.get("loc") == ("body", "role")
                    for item in error.errors()
                ):
                    code = "invalid_role"
                return JSONResponse(status_code=422, content={"error": code})
            except UserNotFoundError:
                return JSONResponse(
                    status_code=404, content={"error": "user_not_found"}
                )

        return handler
