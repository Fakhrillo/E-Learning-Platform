from django.db.models import Count
from django.shortcuts import get_object_or_404
from django.views.generic.base import TemplateResponseMixin, View
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, DeleteView, UpdateView
from django.views.generic.list import ListView

from courses.models import Course, Subject

from .mixins import OwnerCourseMixin, OwnerCourseEditMixin
from courses.services import course_list_queryset, get_cached_courses, get_cached_subjects

from students.forms import CourseEnrollForm


class ManageCourseListView(OwnerCourseMixin, ListView):
    template_name = "courses/manage/course/list.html"
    permission_required = "courses.view_course"

    def get_queryset(self):
        return course_list_queryset().filter(owner=self.request.user)


class CourseCreateView(OwnerCourseEditMixin, CreateView):
    permission_required = "courses.add_course"


class CourseUpdateView(OwnerCourseEditMixin, UpdateView):
    permission_required = "courses.change_course"


class CourseDeleteView(OwnerCourseMixin, DeleteView):
    template_name = "courses/manage/course/delete.html"
    permission_required = "courses.delete_course"

class CourseListView(TemplateResponseMixin, View):
    model = Course
    template_name = "courses/manage/course/list.html"

    def get(self, request, subject=None):
        subjects = get_cached_subjects()
        selected_subject = None

        if subject:
            selected_subject = get_object_or_404(Subject, slug=subject)
            courses = get_cached_courses(subject_id=selected_subject.id)
        else:
            courses = get_cached_courses()

        return self.render_to_response({
            "subjects": subjects,
            "subject": selected_subject,
            "courses": courses
        })
    
class CourseDetailView(DetailView):
    model = Course
    template_name = "courses/manage/course/detail.html"

    def get_queryset(self):
        return (
            Course.objects.select_related("subject", "owner")
            .annotate(total_modules=Count("modules", distinct=True))
            .prefetch_related("modules")
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        modules = list(self.object.modules.all())

        context["enroll_form"] = CourseEnrollForm(initial={"course": self.object})
        context["subjects"] = get_cached_subjects()
        context["current_subject"] = self.object.subject
        context["modules"] = modules
        context["first_module"] = modules[0] if modules else None
        context["is_owner"] = user.is_authenticated and self.object.owner_id == user.id
        context["is_enrolled"] = user.is_authenticated and self.object.students.filter(id=user.id).exists()
        return context
    
