from django.core.paginator import Page, Paginator
from django.db.models import Model
from ..models import ShortenedURL, UploadedFile


def get_paginated_items(
    query,
    page: int | None = None,
    page_size: int = 10,
) -> Page[Model] | None:
    page = page or 1
    if page < 0:
        return None
    p = Paginator(
        query,
        page_size,
    )
    if page > p.num_pages:
        return None
    return p.page(page)

def get_latest_uploaded_files(is_public=True, count=10):
    return UploadedFile.objects.filter(is_public=is_public,).order_by("-inserted_at")[:count]

def get_latest_shortened_urls(is_public=True, count=10):
    return ShortenedURL.objects.filter(is_public=is_public,).order_by("-inserted_at")[:count]