import os
import uuid

from django.contrib.auth import get_user_model
from django.db import models

from core.utils.url_shortener import available_chars, generate_alias

User = get_user_model()


# Create your models here.
class ShortenedURL(models.Model):
    alias = models.TextField()
    url = models.TextField()
    owner = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    inserted_at = models.DateTimeField(
        auto_now_add=True,
    )
    updated_at = models.DateTimeField(
        auto_now=True,
    )
    is_public = models.BooleanField(default=False,)

    def visibility(self):
        if self.is_public:
            return "Public"
        else:
            return "Private"

    @classmethod
    def create(cls, url: str, owner: User | None = None, is_public = False):
        return cls.objects.create(
            alias=get_alias(cls),
            url=url,
            owner=owner,
            is_public=is_public,
        )

    def url_display(self) -> str:
        return self.url[:100]


def uploaded_filename(_instance, filename):
    return "/".join(["uploaded_files", uuid.uuid4().hex, filename])


class UploadedFile(models.Model):
    alias = models.TextField()
    ext = models.TextField(
        null=True,
        blank=True,
    )
    file = models.FileField(upload_to=uploaded_filename)
    owner = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    inserted_at = models.DateTimeField(
        auto_now_add=True,
    )
    updated_at = models.DateTimeField(
        auto_now=True,
    )
    is_public = models.BooleanField(default=False,)
    def visibility(self):
        if self.is_public:
            return "Public"
        else:
            return "Private"

    @classmethod
    def create(cls, file, owner, is_public=False,):
        _, ext = os.path.splitext(file.name)
        return cls.objects.create(
            alias=get_alias(cls, 8),
            ext=ext,
            file=file,
            owner=owner,
            is_public=is_public,
        )

    def alias_filename(self):
        return self.alias + self.ext

    def filename(self):
        return os.path.basename(self.file.url)

    def file_size_mb(self):
        return round(self.file.size / 1024 / 1024, 4)


def get_alias(model: type[UploadedFile] | type[ShortenedURL], start_length=3) -> str:
    current_length = start_length
    while model.objects.count() / (len(available_chars) ** current_length) >= 0.3:
        current_length += 1
    alias = generate_alias(current_length)
    while model.objects.filter(alias=alias).exists():
        alias = generate_alias(current_length)
    return alias
