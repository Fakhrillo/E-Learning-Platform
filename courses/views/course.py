from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.views.generic.base import TemplateResponseMixin, View
from django.views.generic.detail import DetailView
from django.views.generic.list import ListView
from django.db.models import Count
from courses.models import Subject, Course
from django.shortcuts import get_object_or_404

from .mixins import OwnerCourseMixin, OwnerCourseEditMixin

from students.forms import CourseEnrollForm


class ManageCourseListView(OwnerCourseMixin, ListView):
    template_name = "courses/manage/course/list.html"
    permission_required = "courses.view_course"


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
        subjects = Subject.objects.annotate(total_courses=Count('courses'))
        courses = Course.objects.annotate(total_modules=Count('modules'))

        if subject:
            subject = get_object_or_404(Subject, slug=subject)
            courses = courses.filter(subject=subject)
        
        return self.render_to_response({
            "subjects": subjects,
            "subject": subject,
            "courses": courses
        })
    
class CourseDetailView(DetailView):
    model = Course
    template_name = "courses/manage/course/detail.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        context["enroll_form"] = CourseEnrollForm(initial={"course": self.object})
        context["subjects"] = Subject.objects.annotate(total_courses=Count("courses"))
        context["current_subject"] = self.object.subject
        context["is_owner"] = user.is_authenticated and self.object.owner_id == user.id
        context["is_enrolled"] = user.is_authenticated and self.object.students.filter(id=user.id).exists()
        return context
    
