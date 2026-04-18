from rest_framework import serializers
from django.db.models import Avg
import cloudinary
from .models import Category, Comment, CommentReport, Project, ProjectRating, ProjectReport, Tag, Image
from rest_framework.exceptions import ValidationError
def validate_max_images(value):
    # 'value' here is the list of items sent by the user
    MAX_COUNT = 4
    if len(value) > MAX_COUNT:
        raise ValidationError(f"You cannot add more than {MAX_COUNT} images.")

def validate_max_tags(value):
    # 'value' here is the list of items sent by the user
    MAX_COUNT = 10
    if len(value) > MAX_COUNT:
        raise ValidationError(f"You cannot add more than {MAX_COUNT} tags.")



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
    model = Image
    fields = ['id','path']



class ProjectSerializer(serializers.ModelSerializer):
  category_name = serializers.ReadOnlyField(source="category.name")
  user_fullname = serializers.SerializerMethodField()
  user_profile_pic = serializers.SerializerMethodField()
  is_reported_by_me = serializers.SerializerMethodField(read_only=True)
  avg_rate=serializers.FloatField(read_only=True)
  calculate_average_rating = serializers.SerializerMethodField()
  uploaded_image_url = serializers.SerializerMethodField()
  tags = serializers.ListField(child=serializers.CharField(max_length=255),required=False,write_only=True,validators=[validate_max_tags])
  images  = serializers.ListField(child=serializers.ImageField(max_length=10000,allow_empty_file=False,use_url=False),
                                  write_only=True,required=False,validators=[validate_max_images])
  tags_names = serializers.SlugRelatedField(
    many=True, 
    read_only=True, 
    slug_field='name', 
    source='tags'
)
  images_urls = ImageSerializer(many=True,read_only=True,source='image_set')
  class Meta:
    model = Project
    fields = [
        "id", "title", "status", "is_featured",
        "start_date", "end_date", "created_at",
        "details", "target", "current_money","images",'images_urls',
        "is_reported_by_me", "category", "category_name", "user", "user_fullname", "user_profile_pic",
        "tags", "tags_names", "avg_rate", "calculate_average_rating", "uploaded_image_url",
    ]
    extra_kwargs = {         
            "category": {"write_only": True},
            "user": {"write_only": True},
            "created_at": {"read_only": True},
      }

  def create(self,validated_data):
    images_data = validated_data.pop('images',[])
    tags_data = validated_data.pop('tags',[])
    project = Project.objects.create(**validated_data)
    if tags_data:
      tag_instances = [Tag.objects.get_or_create(name=tag)[0] for tag in tags_data]
      project.tags.add(*tag_instances) 
    if images_data:
      image_instances = [Image(path=img,project=project) for img in images_data]
      Image.objects.bulk_create(image_instances)
    return project

  def update(self, instance, validated_data):
    images_data = validated_data.pop('images', None)
    tags_data = validated_data.pop('tags', None)

    for key,data in validated_data.items():
      setattr(instance, key, data)
    instance.save()
   

    if tags_data:
        tag_instances = [Tag.objects.get_or_create(name=tag)[0] for tag in tags_data]
        instance.tags.set(tag_instances)

    if images_data:
        currentImages = instance.image_set.all()
        for img in currentImages:
          img.path.delete()
        currentImages.delete()
        image_instances = [Image(path=img, project=instance) for img in images_data]
        Image.objects.bulk_create(image_instances)

    return instance

  def partial_update(self, instance, validated_data):
    images_data = validated_data.pop('images', None)
    tags_data = validated_data.pop('tags', None)

    for key,data in validated_data.items():
      setattr(instance, key, data)
    instance.save()

    if tags_data:
        tag_instances = [Tag.objects.get_or_create(name=tag)[0] for tag in tags_data]
        instance.tags.set(tag_instances)

    if images_data:
        currentImages = instance.image_set.all()
        for img in currentImages:
          img.path.delete()
        currentImages.delete()
        image_instances = [Image(path=img, project=instance) for img in images_data]
        Image.objects.bulk_create(image_instances)

    return instance

  def get_user_fullname(self, obj):
    return f"{obj.user.first_name} {obj.user.last_name}"

  def get_user_profile_pic(self, obj):
    if hasattr(obj.user, 'profile_pic') and obj.user.profile_pic:
      # If requested URL is needed, build it:
      return obj.user.profile_pic.url
    return None

  def get_is_reported_by_me(self, obj):
    request = self.context.get("request")
    if not request or not request.user or not request.user.is_authenticated:
      return False
    return ProjectReport.objects.filter(project_id=obj.id, user_id=request.user.id).exists()

  def get_calculate_average_rating(self, obj):
    return getattr(obj, 'avg_rate', 0.0)

  def get_uploaded_image_url(self, obj):
    # Try to get the first image from the set
    image = obj.image_set.first()
    if image and image.path:
        return image.path.url
    return None
  
  # def get_uploaded_image_url(self, obj):
  #  return cloudinary.CloudinaryImage(obj.image.name).build_url(secure=True) 
  





class ProjectRatingSerializer(serializers.ModelSerializer):
  class Meta:
    model = ProjectRating
    fields = ["id", "project", "user", "stars", "created_at"]
    read_only_fields = ["id", "project", "user", "created_at"]


class CommentSerializer(serializers.ModelSerializer):
  user_fullname = serializers.SerializerMethodField(read_only=True) # calls the get_user_fullname method using
  user_profile_pic = serializers.SerializerMethodField(read_only=True)
  is_reported_by_me = serializers.SerializerMethodField(read_only=True)

  class Meta:
    model = Comment
    fields = ["id", "project", "user", "user_fullname", "user_profile_pic", "parent", "content", "is_reported_by_me", "created_at"]
    read_only_fields = ["id", "project", "user", "created_at", "user_fullname", "user_profile_pic", "is_reported_by_me"]

  def validate_parent(self, parent):
    # If no parent is given, this is a top-level comment
    if parent is None:
      return parent

    # Prevent a comment from replying to itself
    if self.instance and parent.id == self.instance.id:
      raise serializers.ValidationError("Comment cannot reply to itself.")

    # Get the project ID from context or instance
    project_id = self.context.get("project_id")
    if project_id is None and self.instance:
      project_id = self.instance.project_id

    # Make sure the parent comment is in the same project
    if project_id is not None and parent.project_id != project_id:
      raise serializers.ValidationError("Parent comment must belong to the same project.")

    # Only allow replies to top-level comments (not to replies)
    if parent.parent_id is not None:
      raise serializers.ValidationError("Replies can only be added to top-level comments.")

    return parent

  def get_user_fullname(self, obj):
    return f"{obj.user.first_name} {obj.user.last_name}"

  def get_user_profile_pic(self, obj):
    if hasattr(obj.user, 'profile_pic') and obj.user.profile_pic:
      return obj.user.profile_pic.url
    return None

  def get_is_reported_by_me(self, obj):
    request = self.context.get("request")
    if not request or not request.user or not request.user.is_authenticated:
      return False
    return CommentReport.objects.filter(comment_id=obj.id, user_id=request.user.id).exists()
