from .models import Tag
from rest_framework import viewsets
from .serializer import TagSerializer

# Create your views here.
class TagViewSet(viewsets.ModelViewSet):
  queryset = Tag.objects.all()
  serializer_class = TagSerializer