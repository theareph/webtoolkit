from django.http import HttpRequest
from ipware import get_client_ip


class RealIPMiddleware:
    TRUSTED_PROXIES = {
        "127.0.0.1",
        "::1",
    }

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request: HttpRequest):
        if request.META["REMOTE_ADDR"] in self.TRUSTED_PROXIES:
            ip, _ = get_client_ip(request)
            request.META["REMOTE_ADDR_DEFAULT"] = request.META["REMOTE_ADDR"]
            request.META["REMOTE_ADDR"] = ip
        response = self.get_response(request)
        return response
