from django.core.cache import cache
from django.db.models import Count, OuterRef, Subquery

from courses.models import Content, Course, File, Image, Module, Subject, Text, Video


CATALOG_VERSION_KEY = "catalog:version"


def _catalog_version():
    version = cache.get(CATALOG_VERSION_KEY)
    if version is None:
        version = 1
        cache.set(CATALOG_VERSION_KEY, version, None)
    return version


def bump_catalog_version():
    cache.set(CATALOG_VERSION_KEY, _catalog_version() + 1, None)


def course_list_queryset():
    first_module = Module.objects.filter(course=OuterRef("pk")).order_by("order").values("id")[:1]
    return (
        Course.objects.select_related("subject", "owner")
        .annotate(
            total_modules=Count("modules", distinct=True),
            first_module_id=Subquery(first_module),
        )
    )


def get_cached_subjects():
    key = f"catalog:subjects:v{_catalog_version()}"
    return cache.get_or_set(
        key,
        lambda: list(Subject.objects.annotate(total_courses=Count("courses")).order_by("title")),
        60 * 15,
    )


def get_cached_courses(subject_id=None):
    subject_key = subject_id if subject_id is not None else "all"
    key = f"catalog:courses:{subject_key}:v{_catalog_version()}"
    queryset = course_list_queryset()
    if subject_id is not None:
        queryset = queryset.filter(subject_id=subject_id)
    return cache.get_or_set(key, lambda: list(queryset), 60 * 15)


def attach_content_items(contents):
    content_list = list(contents)
    object_ids_by_model = {
        "text": [],
        "file": [],
        "image": [],
        "video": [],
    }

    for content in content_list:
        object_ids_by_model[content.content_type.model].append(content.object_id)

    item_maps = {
        "text": Text.objects.in_bulk(object_ids_by_model["text"]),
        "file": File.objects.in_bulk(object_ids_by_model["file"]),
        "image": Image.objects.in_bulk(object_ids_by_model["image"]),
        "video": Video.objects.in_bulk(object_ids_by_model["video"]),
    }

    for content in content_list:
        content.prefetched_item = item_maps[content.content_type.model].get(content.object_id)

    return content_list
