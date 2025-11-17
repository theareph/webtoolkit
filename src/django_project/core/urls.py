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
        f"s/<slug:alias>/",
        views.url_shortener_redirect,
        name="url_shortener_redirect",
    ),
    path(
        f"register/",
        views.RegisterView.as_view(),
        name="register",
    ),

]
