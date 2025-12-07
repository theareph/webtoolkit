from django.db.models.signals import post_save
from django.dispatch import receiver
from request.models import Request

from .utils.statistics import resolve_url_path_to_db_instance


@receiver(post_save, sender=Request)
def add_request_to_m2m_field(sender, instance, created, **kwargs):
    if not created:
        return
    m = resolve_url_path_to_db_instance(instance.path)
    if not m:
        return
    m.requests.add(instance)
