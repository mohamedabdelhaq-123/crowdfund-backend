from django.contrib import admin

from apps.projects.models import Category, Comment, CommentReport, Image, Project, ProjectRating, ProjectReport, Tag

# Register your models here.
admin.site.register(Category)
admin.site.register(Tag)
admin.site.register(Project)
admin.site.register(Image)
admin.site.register(ProjectRating)
admin.site.register(Comment)
admin.site.register(CommentReport)
admin.site.register(ProjectReport)  