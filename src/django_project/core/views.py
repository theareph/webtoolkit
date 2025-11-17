from django.http import HttpRequest, HttpResponseBadRequest, HttpResponseNotFound
from django.shortcuts import get_object_or_404, redirect, render
from django.conf import settings
from django.urls import reverse
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth import get_user_model, login

from . import models

User = get_user_model()

def get_common_context():
    return {
        "enable_registration": getattr(settings, "ENABLE_REGISTRATION", False),
    }

def home(request):
    return render(request, "core/home.html", get_common_context())


class RegisterView(View):
    def get(self, request: HttpRequest): 
        if not getattr(settings, "ENABLE_REGISTRATION", False):
            return HttpResponseNotFound()
        return render(request, "core/register.html", get_common_context())
    def post(self, request: HttpRequest): 
        if not getattr(settings, "ENABLE_REGISTRATION", False):
            return HttpResponseNotFound()

        username = request.POST.get("username")
        password = request.POST.get("password")
        if User.objects.filter(username=username).exists():
            return render(request, "core/register.html", get_common_context())
        user = User.objects.create_user(username, password=password)
        login(request, user)
        return redirect(reverse("core:home"))


class URLShortenerView(LoginRequiredMixin, View):

    def get(self, request: HttpRequest):
        return render(request, "core/url_shortener.html", get_common_context())

    def post(self, request: HttpRequest):
        url = request.POST.get("url")
        if not url:
            return HttpResponseBadRequest()
        created = models.ShortenedURL.create(url)
        shortened_url = request.build_absolute_uri(
            reverse(
                "core:url_shortener_redirect",
                kwargs={
                    "alias": created.alias,
                },
            )
        )

        return render(
            request,
            "core/url_shortener.html",
            get_common_context() | {"shortened_url": shortened_url},
        )


def url_shortener_redirect(request, alias):
    if (request.method or "").lower() != "get":
        return HttpResponseNotFound()
    obj = get_object_or_404(
        models.ShortenedURL,
        alias=alias,
    )
    return redirect(obj.url)
