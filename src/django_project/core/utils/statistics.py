from collections.abc import Iterator, Sequence

from django.core.cache import cache
from django.db.models import Count
from request.models import Request

from ..models import ReversableModelMixin


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


def most_viewed_instances(
    qs: Iterator[ReversableModelMixin],
    limit: int = 10,
) -> Sequence[ReversableModelMixin]:
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
