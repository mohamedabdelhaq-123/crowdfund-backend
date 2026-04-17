from rest_framework import serializers
from django.db.models import Avg
import cloudinary
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
  category_name = serializers.ReadOnlyField(source="category.name")
  user_fullname = serializers.SerializerMethodField()
  # uploaded_image_url = serializers.SerializerMethodField()
  calculate_average_rating = serializers.SerializerMethodField()
  tags_names = serializers.SerializerMethodField()
  class Meta:
    model = Project
    fields = [
      "id",
      "title",
      "start_date",
      "end_date",
      "details",
      "target",
      "current_money",
      "is_featured",
      "avg_rate",
      "status",
      "category_name",
      "user_fullname",
      'user',
      'category',
      "image",
      "tags",
      "calculate_average_rating",
      "created_at",
    ]
    extra_kwargs = {         
            "category": {"write_only": True},
            "user": {"write_only": True},
            "created_at": {"read_only": True},
            "tags":{"write_only":True}
      }
    

  def get_user_fullname(self, obj):
    return f"{obj.user.first_name} {obj.user.last_name}"

  def get_calculate_average_rating(self, obj):
    average = obj.ratings.aggregate(average=Avg("stars"))["average"]
    return round(average, 2) if average is not None else 0

  def get_uploaded_image_url(self, obj):
    return cloudinary.CloudinaryImage(obj.image.name).build_url(secure=True) 
  def get_tags_names(self,obj):
      return obj.tags.all()
  





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
