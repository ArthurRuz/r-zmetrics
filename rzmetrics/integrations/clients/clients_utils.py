import functools
import requests



def handle_api_errors(default_return=None):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)

            except requests.HTTPError as e:
                response = getattr(e, "response", None)
                status_code = getattr(response, "status_code", None)

                if status_code == 404:
                    return default_return if default_return is not None else {"error": "not_found"}
                if status_code == 403:
                    return default_return if default_return is not None else {"error": "forbidden"}
                if status_code is not None and status_code >= 500:
                    return default_return if default_return is not None else {"error": "server_error"}

                raise

            except requests.ConnectionError:
                return default_return if default_return is not None else {"error": "connection_failed"}

            except requests.Timeout:
                return default_return if default_return is not None else {"error": "timeout"}

            except requests.RequestException:
                return default_return if default_return is not None else {"error": "request_failed"}

        return wrapper
    return decorator