from rest_framework import viewsets
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import Category, Project
from .serializers import CategorySerializer, ProjectCardSerializer
from rest_framework import generics, filters


class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer


class HomepageView(APIView):
    def get(self, request):
        latest_projects = Project.objects.order_by("-created_at")[:5]

        featured_projects = Project.objects.filter(is_featured=True)[:5]

        top_rated_projects = Project.objects.order_by("-avg_rate")[:5]

        categories = Category.objects.all()

        return Response(
            {
                "latest": ProjectCardSerializer(latest_projects, many=True).data,
                "featured": ProjectCardSerializer(featured_projects, many=True).data,
                "top_rated": ProjectCardSerializer(top_rated_projects, many=True).data,
                "categories": CategorySerializer(categories, many=True).data,
            }
        )


class ProjectSearchView(generics.ListAPIView):
    queryset = Project.objects.filter(status="pending")
    serializer_class = ProjectCardSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ["title", "details", "category__name", "tags__name"]


class SimilarProjectsView(generics.ListAPIView):
    serializer_class = ProjectCardSerializer

    def get_queryset(self):
        project_id = self.kwargs.get("pk")
        try:
            current_project = Project.objects.get(id=project_id)
            return (
                Project.objects.filter(
                    tags__in=current_project.tags.all(), status="pending"
                )
                .exclude(id=project_id)
                .distinct()[:4]
            )
        except Project.DoesNotExist:
            return Project.objects.none()
