from xml.parsers.expat import model

from django.db import models
from django.conf import settings

from apps.authentication.models import User


class Category(models.Model):
    name = models.CharField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name if self.name else f"Category {self.id}"


class Tag(models.Model):
    name = models.CharField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name if self.name else f"Tag {self.id}"




class Project(models.Model):
    title = models.CharField(max_length=255)
    start_date = models.DateField()
    end_date = models.DateField()
    details = models.TextField()
    target = models.FloatField()
    current_money = models.FloatField(default=0, blank=True)
    is_featured = models.BooleanField(default=False)
    class Status(models.TextChoices):
        BANNED = "banned", "Banned"
        PENDING = "pending", "Pending"
        FINISHED = "finished", "Finished"
        CANCELED = "canceled", "Canceled"
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    category =models.ForeignKey(Category,on_delete=models.PROTECT)
    user= models.ForeignKey(User, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)
