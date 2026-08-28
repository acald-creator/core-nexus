"""CORS middleware with 204 preflight responses."""
from starlette.datastructures import Headers
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import Response


class NexusCORSMiddleware(CORSMiddleware):
    """Starlette CORS with HTTP 204 on preflight (Gateway Req 15.3)."""

    def preflight_response(self, request_headers: Headers) -> Response:
        response = super().preflight_response(request_headers)
        headers = dict(response.headers)
        # Parent may set Content-Length for a body we discard on 204.
        headers.pop("content-length", None)
        headers.pop("Content-Length", None)
        return Response(status_code=204, headers=headers)
