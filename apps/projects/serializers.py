from rest_framework import serializers
from django.db.models import Avg
import cloudinary
from .models import Category, Comment, Project, ProjectRating, Tag,Image


class TagSerializer(serializers.ModelSerializer):
  class Meta:
    model = Tag
    fields = "__all__"


class CategorySerializer(serializers.ModelSerializer):
  class Meta:
    model = Category
    fields = "__all__"

class ImageSerializer(serializers.ModelSerializer):
   class Meta:
    model = Category
    fields = "__all__"



class ProjectSerializer(serializers.ModelSerializer):
  category_name = serializers.ReadOnlyField(source="category.name")
  user_fullname = serializers.SerializerMethodField()
  # uploaded_image_url = serializers.SerializerMethodField()
  tags = serializers.PrimaryKeyRelatedField(many=True ,queryset=Tag.objects.all(),write_only=True)
  images  = serializers.PrimaryKeyRelatedField(many=True,queryset=Image.objects.all(),write_only=True)
  calculate_average_rating = serializers.SerializerMethodField()
  tags_names = serializers.SlugRelatedField(
    many=True, 
    read_only=True, 
    slug_field='name', 
    source='tags'
)
  images_urls = serializers.SlugRelatedField(
    many=True,
    read_only=True,
    slug_field='path',
    source='images'
  )
  class Meta:
    model = Project
    fields = [
        "id", "title", "status", "is_featured",
        "start_date", "end_date", "created_at",
        "details", "target", "current_money","images",'images_urls', "avg_rate",
        "category", "category_name", "user", "user_fullname",
        "tags", "tags_names", "calculate_average_rating",
    ]
    extra_kwargs = {         
            "category": {"write_only": True},
            "user": {"write_only": True},
            "created_at": {"read_only": True},
            "tags":{"write_only":True},
            "images":{"write_only":True}
      }

  def create(self,validated_data):
    images_data = validated_data.pop('images',[])
    tags_data = validated_data.pop('tags',[])
    project = Project.objects.create(**validated_data)
    if tags_data:
      project.tags.set(tags_data)
    if images_data:
      image_instances = [Image(path=img,project=project) for img in images_data]
      Image.objects.bulk_create(image_instances)
    return project

  def get_user_fullname(self, obj):
    return f"{obj.user.first_name} {obj.user.last_name}"

  def get_calculate_average_rating(self, obj):
    average = obj.ratings.aggregate(average=Avg("stars"))["average"]
    return round(average, 2) if average is not None else 0

  def get_uploaded_image_url(self, obj):
    return cloudinary.CloudinaryImage(obj.image.name).build_url(secure=True)   #TODO: customize the image sent to client

  





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
