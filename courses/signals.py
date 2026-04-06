from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from courses.models import Course, Module, Subject
from courses.services import bump_catalog_version


@receiver(post_save, sender=Subject)
@receiver(post_delete, sender=Subject)
@receiver(post_save, sender=Course)
@receiver(post_delete, sender=Course)
@receiver(post_save, sender=Module)
@receiver(post_delete, sender=Module)
def invalidate_catalog_cache(**kwargs):
    bump_catalog_version()
