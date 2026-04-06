from django.shortcuts import render
from django.contrib.auth import authenticate, login
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count
from django.urls import reverse_lazy
from django.views.generic.edit import CreateView, FormView
from django.views.generic.list import ListView
from django.views.generic.detail import DetailView
from students.forms import CourseEnrollForm
from courses.models import Content, Course
from courses.services import attach_content_items
# Create your views here.

class StudentRegistrationView(CreateView):
    template_name = "students/student/registration.html"
    form_class = UserCreationForm
    success_url = reverse_lazy("student_course_list")

    def form_valid(self, form):
        result = super().form_valid(form)
        cd = form.cleaned_data
        user = authenticate(username=cd['username'], password=cd['password1'])
        login(self.request, user)
        return result
    

class StudentEnrollCourseView(LoginRequiredMixin, FormView):
    course = None
    form_class = CourseEnrollForm

    def form_valid(self, form):
        self.course = form.cleaned_data['course']
        self.course.students.add(self.request.user)
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('student_course_detail', args=[self.course.id])
    

class StudentCourseListView(LoginRequiredMixin, ListView):
    model = Course
    template_name = "students/course/list.html"

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .filter(students__in=[self.request.user])
            .select_related("subject", "owner")
            .annotate(total_modules=Count("modules", distinct=True))
        )
    

class StudentCourseDetailView(LoginRequiredMixin, DetailView):
    model = Course
    template_name = "students/course/detail.html"

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .filter(students__in=[self.request.user])
            .select_related("subject", "owner")
            .annotate(total_modules=Count("modules", distinct=True))
            .prefetch_related("modules")
        )
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        course = self.object
        modules = list(course.modules.all())
        module = None

        if "module_id" in self.kwargs:
            module_id = int(self.kwargs["module_id"])
            module = next((item for item in modules if item.id == module_id), None)
        if module is None:
            module = modules[0] if modules else None

        module_contents = []
        if module is not None:
            module_contents = attach_content_items(
                Content.objects.filter(module=module).select_related("content_type")
            )

        context["modules"] = modules
        context["module"] = module
        context["module_contents"] = module_contents
        return context
    
