from rest_framework import serializers
from django.db.models import Avg

from .models import Category, Comment, Project, ProjectRating, Tag


class TagSerializer(serializers.ModelSerializer):
  class Meta:
    model = Tag
    fields = "__all__"


class CategorySerializer(serializers.ModelSerializer):
  class Meta:
    model = Category
    fields = "__all__"


class ProjectSerializer(serializers.ModelSerializer):
  category = serializers.ReadOnlyField(source="category.name")
  user_fullname = serializers.SerializerMethodField()
  calculate_average_rating = serializers.SerializerMethodField()

  class Meta:
    model = Project
    fields = "__all__"
    read_only_fields = ["user"]

  def get_user_fullname(self, obj):
    return f"{obj.user.first_name} {obj.user.last_name}"

  def get_calculate_average_rating(self, obj):
    average = obj.ratings.aggregate(average=Avg("stars"))["average"]
    return round(average, 2) if average is not None else 0


class ProjectRatingSerializer(serializers.ModelSerializer):
  class Meta:
    model = ProjectRating
    fields = ["id", "project", "user", "stars", "created_at"]
    read_only_fields = ["id", "project", "user", "created_at"]


class CommentSerializer(serializers.ModelSerializer):
  user_fullname = serializers.SerializerMethodField(read_only=True) # calls the get_user_fullname method using

  class Meta:
    model = Comment
    fields = ["id", "project", "user", "user_fullname", "content", "created_at"]
    read_only_fields = ["id", "project", "user", "created_at", "user_fullname"]

  def get_user_fullname(self, obj):
    return f"{obj.user.first_name} {obj.user.last_name}"
