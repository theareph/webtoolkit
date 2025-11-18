import os
import typing as t

from django.conf import settings
from django.contrib.auth import get_user_model, login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpRequest, HttpResponseNotFound
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views import View

from . import models
from .utils import url_shortener as url_shortener_utils

User = get_user_model()


def get_common_context() -> dict[str, t.Any]:
    data = {
        "enable_registration": getattr(settings, "ENABLE_REGISTRATION", False),
        "file_hosting_max_size": getattr(
            settings, "FILE_HOSTING_MAX_SIZE", 1024 * 1024
        ),
    }
    data["file_hosting_max_size_mb"] = data["file_hosting_max_size"] / 1024 / 1024
    return data


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
        return render(
            request,
            "core/url_shortener.html",
            get_common_context(),
        )

    def post(self, request: HttpRequest):
        errors: list[str] = []
        url = request.POST.get("url")
        if not url or not url_shortener_utils.is_http_url(url):
            errors.append("Invalid URL")
            return render(
                request,
                "core/url_shortener.html",
                get_common_context() | {"errors": errors},
            )

        created = models.ShortenedURL.create(
            url,
            request.user,
        )
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


class FileHostingView(LoginRequiredMixin, View):
    def get(self, request):
        return render(
            request,
            "core/file_hosting.html",
            get_common_context(),
        )

    def post(self, request: HttpRequest):
        errors = []
        common_context = get_common_context()
        try:
            content_length = int(request.META.get("CONTENT_LENGTH"))
        except:
            errors.append("Bad Request!")
            return render(
                request,
                "core/file_hosting.html",
                get_common_context() | {"errors": errors},
            )
        if "file" not in request.FILES:
            errors.append("Bad Request!")
            return render(
                request,
                "core/file_hosting.html",
                get_common_context() | {"errors": errors},
            )



        if content_length > common_context["file_hosting_max_size"]:
            errors.append(f"File too large (size: {content_length / 1024 / 1024} MB)")
            return render(
                request,
                "core/file_hosting.html",
                get_common_context() | {"errors": errors},
            )
        created = models.UploadedFile.create(request.FILES["file"], request.user)
        file_url = request.build_absolute_uri(
            reverse(
                "core:file_redirect",
                kwargs={"alias_filename": f"{created.alias}{created.ext}"},
            )
        )

        return render(
            request,
            "core/file_hosting.html",
            get_common_context()
            | {
                "errors": errors,
                "file_url": file_url,
            },
        )


def file_redirect(request: HttpRequest, alias_filename: str):
    alias, ext = os.path.splitext(alias_filename)
    file_obj = get_object_or_404(
        models.UploadedFile,
        alias=alias,
        ext=ext,
    )

    return redirect(request.build_absolute_uri(file_obj.file.url))
