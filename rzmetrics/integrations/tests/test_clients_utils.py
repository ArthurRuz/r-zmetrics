import pytest
import requests

from integrations.clients.clients_utils import handle_api_errors


def test_handle_api_errors_success():
    @handle_api_errors()
    def ok():
        return {"data": 1}

    assert ok() == {"data": 1}


def test_handle_api_errors_404():
    @handle_api_errors(default_return={"error": "not_found"})
    def raise_404():
        response = requests.Response()
        response.status_code = 404
        raise requests.HTTPError(response=response)

    assert raise_404() == {"error": "not_found"}


def test_handle_api_errors_403():
    @handle_api_errors()
    def raise_403():
        response = requests.Response()
        response.status_code = 403
        raise requests.HTTPError(response=response)

    result = raise_403()
    assert result["error"] == "forbidden"


def test_handle_api_errors_500():
    @handle_api_errors()
    def raise_500():
        response = requests.Response()
        response.status_code = 503
        raise requests.HTTPError(response=response)

    result = raise_500()
    assert result["error"] == "server_error"


def test_handle_api_errors_connection_error():
    @handle_api_errors()
    def raise_connection():
        raise requests.ConnectionError()

    result = raise_connection()
    assert result["error"] == "connection_failed"


def test_handle_api_errors_timeout():
    @handle_api_errors()
    def raise_timeout():
        raise requests.Timeout()

    result = raise_timeout()
    assert result["error"] == "timeout"
