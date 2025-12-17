from django.contrib import admin
from courses.models import Subject, Course, Module
from django_daisy.mixins import NavTabMixin


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ['id', 'title', 'slug']
    list_display_link = list_display
    prepopulated = {'slug': ('title',)}


class ModuleInline(admin.StackedInline, NavTabMixin):
    model = Module
    extra = 1

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ['id', 'title', 'subject', 'created', 'modified']
    list_display_link = list_display
    list_filter = ['created', 'modified', 'subject']
    search_fields = ['title', 'overview']
    prepopulated = {'slug': ('title',)}
    inlines = [ModuleInline]
