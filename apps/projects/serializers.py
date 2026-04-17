from rest_framework import serializers
from django.db.models import Avg
import cloudinary
from .models import Category, Comment, CommentReport, Project, ProjectRating, ProjectReport, Tag


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
  uploaded_image_url = serializers.SerializerMethodField()
  calculate_average_rating = serializers.SerializerMethodField()
  is_reported_by_me = serializers.SerializerMethodField()
 
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
      "is_reported_by_me",
      "category_name",
      "user_fullname",
      'user',
      'category',
      "image",
      "uploaded_image_url",
      "calculate_average_rating",
      "created_at",
    ]
    extra_kwargs = {         
            "category": {"write_only": True},
            "image": {"write_only": True},
            "user": {"write_only": True},
            "created_at": {"read_only": True},
        }
    

  def get_user_fullname(self, obj):
    return f"{obj.user.first_name} {obj.user.last_name}"

  def get_calculate_average_rating(self, obj):
    average = obj.ratings.aggregate(average=Avg("stars"))["average"]
    return round(average, 2) if average is not None else 0

  def get_uploaded_image_url(self, obj):
    return cloudinary.CloudinaryImage(obj.image.name).build_url(secure=True) 

  def get_is_reported_by_me(self, obj):
    request = self.context.get("request")
    if not request or not request.user or not request.user.is_authenticated:
      return False
    return ProjectReport.objects.filter(project_id=obj.id, user_id=request.user.id).exists()
  





class ProjectRatingSerializer(serializers.ModelSerializer):
  class Meta:
    model = ProjectRating
    fields = ["id", "project", "user", "stars", "created_at"]
    read_only_fields = ["id", "project", "user", "created_at"]


class CommentSerializer(serializers.ModelSerializer):
  user_fullname = serializers.SerializerMethodField(read_only=True) # calls the get_user_fullname method using
  is_reported_by_me = serializers.SerializerMethodField(read_only=True)

  class Meta:
    model = Comment
    fields = ["id", "project", "user", "user_fullname", "content", "is_reported_by_me", "created_at"]
    read_only_fields = ["id", "project", "user", "created_at", "user_fullname", "is_reported_by_me"]

  def get_user_fullname(self, obj):
    return f"{obj.user.first_name} {obj.user.last_name}"

  def get_is_reported_by_me(self, obj):
    request = self.context.get("request")
    if not request or not request.user or not request.user.is_authenticated:
      return False
    return CommentReport.objects.filter(comment_id=obj.id, user_id=request.user.id).exists()
