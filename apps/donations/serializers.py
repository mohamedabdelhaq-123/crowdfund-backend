from rest_framework import serializers

from .models import Donation

class DonationSerializer(serializers.ModelSerializer):
  user_fullname = serializers.SerializerMethodField()
  project_name = serializers.ReadOnlyField(source="project.title")

  class Meta:
    model = Donation
    fields = "__all__"
    read_only_fields = ["id", "created_at"]

  def get_user_fullname(self, obj):
    return f"{obj.user.first_name} {obj.user.last_name}"