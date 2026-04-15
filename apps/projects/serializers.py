from rest_framework import serializers
from .models import Project, Tag

class TagSerializer(serializers.ModelSerializer):
  class Meta:
    model = Tag
    fields = '__all__'

class CategorySerializer(serializers.ModelSerializer):
  class Meta:
    model = Tag
    fields = '__all__'

class ProjectSerializer(serializers.ModelSerializer):
    category = serializers.ReadOnlyField(source='category.name')
    user_fullname = serializers.SerializerMethodField()
    calculate_average_rating= serializers.SerializerMethodField()
    class Meta:
        model = Project
        fields = '__all__'

    def get_user_fullname(self,obj):
      return f"{obj.user.first_name} {obj.user.last_name}"
    def get_calculate_average_rating(self, obj):
        #TODO: Implement the logic to calculate the average rating for the grade
        pass
    