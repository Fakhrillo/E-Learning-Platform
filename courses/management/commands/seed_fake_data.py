import os
import random
import string

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils.text import slugify

from courses.models import Content, Course, File, Image, Module, Subject, Text, Video


WORDS = [
    "adaptive",
    "canvas",
    "design",
    "studio",
    "signal",
    "focus",
    "craft",
    "future",
    "rhythm",
    "systems",
    "clarity",
    "vector",
    "insight",
    "method",
    "story",
    "studio",
    "motion",
    "atlas",
    "horizon",
    "atlas",
    "pattern",
    "practice",
]

SENTENCES = [
    "Learn by building projects that mirror real-world constraints.",
    "Focus on clarity, iteration, and measurable outcomes.",
    "Explore frameworks that scale from prototype to production.",
    "Develop habits that make learning durable and transferable.",
    "Pair theory with exercises that make ideas stick.",
    "Work through guided milestones with practical examples.",
]


def make_title(words=WORDS):
    count = random.randint(2, 4)
    return " ".join(random.sample(words, count)).title()


def make_paragraph():
    return " ".join(random.choice(SENTENCES) for _ in range(random.randint(2, 4)))


def unique_slug(model, base):
    base_slug = slugify(base) or "item"
    slug = base_slug
    counter = 2
    while model.objects.filter(slug=slug).exists():
        slug = f"{base_slug}-{counter}"
        counter += 1
    return slug


def random_suffix(length=5):
    return "".join(random.choices(string.ascii_lowercase + string.digits, k=length))


class Command(BaseCommand):
    help = "Populate the database with fake subjects, courses, modules, and content items."

    def add_arguments(self, parser):
        parser.add_argument("--min", type=int, default=20, help="Minimum number of courses.")
        parser.add_argument("--max", type=int, default=50, help="Maximum number of courses.")
        parser.add_argument("--count", type=int, default=None, help="Exact number of courses to create.")
        parser.add_argument("--owner", type=str, default=None, help="Username to own the courses.")

    @transaction.atomic
    def handle(self, *args, **options):
        min_count = options["min"]
        max_count = options["max"]
        count = options["count"] or random.randint(min_count, max_count)

        if count <= 0:
            self.stdout.write(self.style.ERROR("Count must be greater than 0."))
            return

        User = get_user_model()
        owner = None
        if options["owner"]:
            owner = User.objects.filter(username=options["owner"]).first()
            if not owner:
                self.stdout.write(self.style.ERROR("Owner username not found."))
                return
        else:
            owner = User.objects.first()

        if owner is None:
            owner = User.objects.create_user(
                username="seed_admin",
                email="seed_admin@example.com",
                password="seedpass123",
            )
            self.stdout.write(self.style.WARNING("Created default user: seed_admin / seedpass123"))

        os.makedirs(settings.MEDIA_ROOT, exist_ok=True)

        subjects = []
        for _ in range(6):
            title = make_title()
            subject = Subject.objects.create(title=title, slug=unique_slug(Subject, title))
            subjects.append(subject)

        created_courses = 0
        for _ in range(count):
            title = make_title()
            course = Course.objects.create(
                owner=owner,
                subject=random.choice(subjects),
                title=title,
                slug=unique_slug(Course, f"{title}-{random_suffix()}"),
                overview=make_paragraph(),
            )

            module_count = random.randint(2, 5)
            for _ in range(module_count):
                module = Module.objects.create(
                    course=course,
                    title=make_title(),
                    description=make_paragraph(),
                )

                content_count = random.randint(2, 6)
                for _ in range(content_count):
                    kind = random.choice(["text", "video", "image", "file"])
                    if kind == "text":
                        item = Text.objects.create(
                            owner=owner,
                            title=make_title(),
                            content=make_paragraph(),
                        )
                    elif kind == "video":
                        item = Video.objects.create(
                            owner=owner,
                            title=make_title(),
                            url=f"https://example.com/video/{random_suffix()}",
                        )
                    elif kind == "image":
                        item = Image.objects.create(
                            owner=owner,
                            title=make_title(),
                            file=SimpleUploadedFile(
                                f"image-{random_suffix()}.jpg",
                                b"fake image content",
                                content_type="image/jpeg",
                            ),
                        )
                    else:
                        item = File.objects.create(
                            owner=owner,
                            title=make_title(),
                            file=SimpleUploadedFile(
                                f"file-{random_suffix()}.pdf",
                                b"fake file content",
                                content_type="application/pdf",
                            ),
                        )

                    Content.objects.create(module=module, item=item)

            created_courses += 1

        self.stdout.write(self.style.SUCCESS(f"Created {created_courses} courses."))
