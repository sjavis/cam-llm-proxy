#!/usr/bin/env python3

import os
from typing import Any

import httpx
from fastapi import FastAPI, Request, Response

app = FastAPI()

UPSTREAM = os.environ.get(
    "UPSTREAM_URL",
    "https://llm.hpc.cam.ac.uk",
).rstrip("/")

API_KEY = os.environ.get("CAMLLM_API_KEY")


def strip_thinking(value: Any) -> Any:
    """Remove Anthropic thinking blocks recursively."""

    if isinstance(value, list):
        result = []

        for item in value:
            # Anthropic content block
            if (
                isinstance(item, dict)
                and item.get("type") == "thinking"
            ):
                continue

            result.append(strip_thinking(item))

        return result

    if isinstance(value, dict):
        return {
            key: strip_thinking(val)
            for key, val in value.items()
        }

    return value


@app.api_route(
    "/{path:path}",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
)
async def proxy(path: str, request: Request):
    body = await request.body()

    headers = dict(request.headers)

    # Don't forward hop-by-hop headers.
    headers.pop("host", None)
    headers.pop("content-length", None)

    # Use the Cambridge API key for the upstream request.
    if API_KEY:
        headers["authorization"] = f"Bearer {API_KEY}"

    # Only modify JSON POST requests to /v1/messages.
    if (
        request.method == "POST"
        and path.rstrip("/") == "v1/messages"
        and body
    ):
        content_type = request.headers.get("content-type", "")

        if "application/json" in content_type:
            import json

            data = json.loads(body)

            original = data.get("messages")

            if original is not None:
                data["messages"] = strip_thinking(original)

            body = json.dumps(data).encode()

            headers["content-type"] = "application/json"

    async with httpx.AsyncClient(timeout=None) as client:
        upstream = await client.request(
            request.method,
            f"{UPSTREAM}/{path}",
            headers=headers,
            content=body,
            params=request.query_params,
        )

    excluded = {
        "content-encoding",
        "transfer-encoding",
        "connection",
        "content-length",
    }

    response_headers = {
        k: v
        for k, v in upstream.headers.items()
        if k.lower() not in excluded
    }

    return Response(
        content=upstream.content,
        status_code=upstream.status_code,
        headers=response_headers,
        media_type=upstream.headers.get("content-type"),
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host="127.0.0.1",
        port=18787,
    )
