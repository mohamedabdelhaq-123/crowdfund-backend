from django.db import models

# Create your models here.

class Donation(models.Model):
  amount = models.FloatField()
  project = models.ForeignKey("projects.Project",on_delete=models.PROTECT)
  user = models.ForeignKey("authentication.User",on_delete=models.PROTECT)
  created_at = models.DateTimeField(auto_now_add=True)