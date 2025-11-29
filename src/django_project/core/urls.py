from django.urls import path

from . import views

app_name = "core"
urlpatterns = [
    path(
        "",
        views.home,
        name="home",
    ),
    path(
        "url-shortener/",
        views.URLShortenerView.as_view(),
        name="url_shortener",
    ),
    path(
        "file-hosting/",
        views.FileHostingView.as_view(),
        name="file_hosting",
    ),
    path(
        f"s/<slug:alias>",
        views.URLShortenerURLView.as_view(),
        name="url_shortener_url",
    ),
    path(
        f"s/<slug:alias>/delete/",
        views.url_shortener_url_delete,
        name="url_shortener_url_delete",
    ),
    path(
        f"f/<str:alias_filename>",
        views.file_redirect,
        name="file_redirect",
    ),
    path(
        f"f/<str:alias_filename>/delete/",
        views.file_delete,
        name="file_delete",
    ),
    path(
        f"register/",
        views.RegisterView.as_view(),
        name="register",
    ),
    path(
        f"login/",
        views.LoginView.as_view(),
        name="login",
    ),

    path(
        f"about-user/",
        views.about_user,
        name="about_user",
    ),
]
