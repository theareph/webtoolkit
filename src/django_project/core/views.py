import os
import typing as t

from django.conf import settings
from django.contrib.auth import get_user_model, login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView as DjangoLoginView
from django.http import Http404, HttpRequest
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views import View

from . import models
from .utils import url_shortener as url_shortener_utils
from .utils.common import (
    get_latest_shortened_urls,
    get_latest_uploaded_files,
    get_paginated_items,
)

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
    context = get_common_context()
    context |= {
        "latest_urls": get_latest_shortened_urls(),
        "latest_files": get_latest_uploaded_files(),
    }

    return render(
        request,
        "core/home.html",
        context,
    )


class LoginView(DjangoLoginView):
    @t.override
    def get_context_data(self, **kwargs: t.Any) -> dict[str, t.Any]:
        return get_common_context() | super().get_context_data(**kwargs)


class RegisterView(View):
    def get(self, request: HttpRequest):
        if not getattr(settings, "ENABLE_REGISTRATION", False):
            raise Http404("Registration is disabled.")
        return render(request, "core/register.html", get_common_context())

    def post(self, request: HttpRequest):
        if not getattr(settings, "ENABLE_REGISTRATION", False):
            raise Http404("Registration is disabled.")

        username = request.POST.get("username")
        password = request.POST.get("password")
        if not username or not password:
            return render(
                request,
                "core/register.html",
                get_common_context() | {"errors": ["invalid username or password."]},
            )

        if User.objects.filter(username=username).exists():
            return render(request, "core/register.html", get_common_context())
        user = User.objects.create_user(username, password=password)
        login(request, user)
        return redirect(reverse("core:home"))


class URLShortenerView(LoginRequiredMixin, View):
    def get_page(
        self,
    ):
        try:
            page = int(self.request.GET.get("page", 1))
        except:
            page = None
        return get_paginated_items(
            models.ShortenedURL.objects.filter(owner=self.request.user).order_by(
                "-inserted_at"
            ),
            page,
            page_size=3,
        )

    def get(self, request: HttpRequest):
        return render(
            request,
            "core/url_shortener.html",
            get_common_context() | {"page": self.get_page()},
        )

    def post(self, request: HttpRequest):
        errors: list[str] = []
        common_context = get_common_context() | {"page": self.get_page()}
        url = request.POST.get("url")
        if not url or not url_shortener_utils.is_http_url(url):
            errors.append("Invalid URL")
            return render(
                request,
                "core/url_shortener.html",
                common_context | {"errors": errors},
            )
        is_public = bool(request.POST.get("is_public"))

        created = models.ShortenedURL.create(
            url,
            request.user,
            is_public,
        )
        common_context["page"] = self.get_page()
        shortened_url = request.build_absolute_uri(
            reverse(
                "core:url_shortener_url",
                kwargs={
                    "alias": created.alias,
                },
            )
        )

        return render(
            request,
            "core/url_shortener.html",
            common_context | {"shortened_url": shortened_url},
        )


class URLShortenerURLView(View):
    def get(self, request, alias, *args, **kwargs):
        obj = get_object_or_404(
            models.ShortenedURL,
            alias=alias,
        )
        return redirect(obj.url)


@login_required
def url_shortener_url_delete(request, alias):
    try:
        page = int(request.GET.get("page", 1))
    except:
        page = 1
    obj = get_object_or_404(
        models.ShortenedURL,
        alias=alias,
        owner=request.user,
    )
    obj.delete()
    return redirect(reverse("core:url_shortener") + f"?page={page}")


class FileHostingView(LoginRequiredMixin, View):
    def get_page(
        self,
    ):
        try:
            page = int(self.request.GET.get("page", 1))
        except:
            page = None
        return get_paginated_items(
            models.UploadedFile.objects.filter(owner=self.request.user).order_by(
                "-inserted_at"
            ),
            page,
            page_size=3,
        )

    def get(self, request):
        return render(
            request,
            "core/file_hosting.html",
            get_common_context() | {"page": self.get_page()},
        )

    def post(self, request: HttpRequest):
        errors = []
        common_context = get_common_context() | {"page": self.get_page()}
        try:
            content_length = int(request.META.get("CONTENT_LENGTH"))
        except:
            errors.append("Bad Request!")
            return render(
                request,
                "core/file_hosting.html",
                common_context | {"errors": errors},
            )
        if "file" not in request.FILES:
            errors.append("Bad Request!")
            return render(
                request,
                "core/file_hosting.html",
                common_context | {"errors": errors},
            )

        if content_length > common_context["file_hosting_max_size"]:
            errors.append(f"File too large (size: {content_length / 1024 / 1024} MB)")
            return render(
                request,
                "core/file_hosting.html",
                common_context | {"errors": errors},
            )

        is_public = bool(request.POST.get("is_public"))
        created = models.UploadedFile.create(
            request.FILES["file"], request.user, is_public
        )

        common_context["page"] = self.get_page()
        file_url = request.build_absolute_uri(
            reverse(
                "core:file_redirect",
                kwargs={"alias_filename": f"{created.alias}{created.ext}"},
            )
        )

        return render(
            request,
            "core/file_hosting.html",
            common_context
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


@login_required
def file_delete(request: HttpRequest, alias_filename: str):
    try:
        page = int(request.GET.get("page", 1))
    except:
        page = 1
    alias, ext = os.path.splitext(alias_filename)
    file_obj = get_object_or_404(
        models.UploadedFile,
        alias=alias,
        ext=ext,
        owner=request.user,
    )
    file_obj.delete()

    return redirect(reverse("core:file_hosting") + f"?page={page}")


@login_required
def about_user(request):
    context = get_common_context() | {
        "total_uploaded_files": models.UploadedFile.objects.filter(
            owner=request.user
        ).count(),
        "total_shortened_urls": models.ShortenedURL.objects.filter(
            owner=request.user
        ).count(),
    }
    return render(
        request,
        "core/about_user.html",
        context,
    )
