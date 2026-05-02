from flask import Request
from fastapi.testclient import TestClient

from app.api import app

client = TestClient(app)


def handler(request: Request):
    response = client.request(
        method=request.method,
        url=request.full_path if request.query_string else request.path,
        headers={k: v for k, v in request.headers.items() if k.lower() != "host"},
        data=request.get_data(),
    )
    excluded_headers = {"content-encoding", "transfer-encoding", "connection"}
    headers = [(name, value) for name, value in response.headers.items() if name.lower() not in excluded_headers]
    return response.content, response.status_code, headers
