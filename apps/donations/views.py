from django.shortcuts import render
from apps.donations.models import Donation
from apps.donations.serializers import DonationSerializer
from rest_framework import viewsets
# Create your views here.

class DonationViewSet(viewsets.ModelViewSet):
  queryset = Donation.objects.all()
  serializer_class = DonationSerializer