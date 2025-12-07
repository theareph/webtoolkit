import typing as t
from collections.abc import Iterator, Sequence

from django.core.cache import cache
from django.db.models import Count, QuerySet
from request.models import Request
from django.urls import resolve
import os
from django.urls.exceptions import Resolver404

from ..models import ReversableModelMixin, ShortenedURL, UploadedFile, StatisticsModelMixin

class Instance(t.TypedDict):
    instance: StatisticsModelMixin
    view_count: int

def get_all_request_counts() -> dict[str, int]:
    """
    A bit costly :(

    Caching this for a day.
    """
    request_counts = cache.get("all_request_counts")
    if request_counts:
        return request_counts

    request_counts = dict(
        Request.objects.values("path")
        .annotate(count=Count("id"))
        .values_list("path", "count")
    )
    cache.set(
        "all_request_counts",
        request_counts,
        3600 * 24,
    )
    return request_counts


def most_viewed_instances_no_post_save_signal(
    qs: Iterator[ReversableModelMixin],
    limit: int = 10,
) -> Sequence[dict[str, ReversableModelMixin | int]]:
    request_counts = get_all_request_counts()
    model_counts = []
    for instance in qs:
        view_count = request_counts.get(instance.view_path, 0)
        if view_count > 0:
            model_counts.append(
                {
                    "instance": instance,
                    "view_count": view_count,
                }
            )
    return sorted(
        model_counts,
        key=lambda x: x["view_count"],
        reverse=True,
    )[:limit]


def resolve_url_path_to_db_instance(url_path: str,) -> StatisticsModelMixin | None:
    try:
        match = resolve(url_path)
        if match.view_name == "core:url_shortener_url":
            return ShortenedURL.objects.filter(alias=match.kwargs["alias"]).first()
        if match.view_name == "core:file_redirect":
            alias, ext = os.path.splitext(match.kwargs["alias_filename"])
            return UploadedFile.objects.filter(alias=alias, ext=ext,).first()
    except Resolver404:
        return None
def most_viewed_instances(qs: QuerySet[StatisticsModelMixin], limit: int = 10) -> Iterator[Instance]:
    instances = qs.annotate(
        request_count=Count('requests')
    ).order_by('-request_count')[:limit]
    for instance in instances:
        yield {"instance": instance, "view_count": instance.request_count}