from rest_framework import viewsets
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import generics, filters, status
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAuthenticatedOrReadOnly
from django.shortcuts import get_object_or_404
from django.db.models import Avg

from .models import Category, Comment, CommentReport, Project, ProjectRating, ProjectReport, Tag,Image
from .serializers import CategorySerializer, CommentSerializer, ProjectRatingSerializer, ProjectSerializer, TagSerializer,ImageSerializer


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer


class TagViewSet(viewsets.ModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer


class ProjectViewSet(viewsets.ModelViewSet):
    queryset = Project.objects.all().prefetch_related('tags')
    serializer_class = ProjectSerializer
    parser_classes = (MultiPartParser, FormParser)

class ProjectImageListView(generics.ListCreateAPIView):
    serializer_class = ImageSerializer

    def get_queryset(self):
        return Image.objects.filter(project_id=self.kwargs['project_id'])

    def create(self, request, *args, **kwargs):
 
        files = request.FILES.getlist('image') 
        project = generics.get_object_or_404(Project, id=self.kwargs['project_id'])
        
        instances = [Image(path=f,project=project) for f in files]
        Image.objects.bulk_create(instances)
        
        return Response({"detail": "Images uploaded."}, status=status.HTTP_201_CREATED)

class ProjectImageDetailView(APIView):

    def delete(self, request,project_id, pk, format=None):
        image = get_object_or_404(Image,project=project_id,id=pk)
        image.path.delete()
        image.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    


    
class HomepageView(APIView):
    def get(self, request):
        latest_projects = Project.objects.order_by("-created_at")[:5]

        featured_projects = Project.objects.filter(is_featured=True)[:5]

        top_rated_projects = (
            Project.objects.annotate(avg_rating=Avg("ratings__stars"))
            .filter(avg_rating__isnull=False)
            .order_by("-avg_rating", "-created_at")[:5]
        )

        categories = Category.objects.all()

        return Response(
            {
                "latest": ProjectSerializer(latest_projects, many=True, context={"request": request}).data,
                "featured": ProjectSerializer(featured_projects, many=True, context={"request": request}).data,
                "top_rated": ProjectSerializer(top_rated_projects, many=True, context={"request": request}).data,
                "categories": CategorySerializer(categories, many=True).data,
            }
        )


class ProjectSearchView(generics.ListAPIView):
    queryset = Project.objects.filter(status="pending")
    serializer_class = ProjectSerializer
    permission_classes = [AllowAny]
    filter_backends = [filters.SearchFilter]
    search_fields = ["title", "details", "category__name", "tags__name"]


class SimilarProjectsView(generics.ListAPIView):
    serializer_class = ProjectSerializer
    permission_classes = [AllowAny]

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



class ProjectCommentCollectionView(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get(self, request, project_id):
        get_object_or_404(Project, id=project_id)
        comments = Comment.objects.filter(project_id=project_id).order_by("-created_at")
        serializer = CommentSerializer(comments, many=True, context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request, project_id):
        get_object_or_404(Project, id=project_id)
        serializer = CommentSerializer(data=request.data, context={"request": request, "project_id": project_id})
        serializer.is_valid(raise_exception=True)
        serializer.save(user=request.user, project_id=project_id)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class ProjectCommentDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, pk):
        comment = get_object_or_404(Comment, pk=pk, user=request.user)
        serializer = CommentSerializer(comment, data=request.data, partial=True, context={"request": request, "project_id": comment.project_id})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)


    def delete(self, request, pk):
        comment = get_object_or_404(Comment, pk=pk, user=request.user)
        comment.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class CommentReportCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        comment = get_object_or_404(Comment, pk=pk)
        report = CommentReport.objects.filter(comment=comment, user=request.user).first()
        if report:
            report.delete()
            return Response({"detail": "comment unflagged"}, status=status.HTTP_200_OK)

        CommentReport.objects.create(comment=comment, user=request.user)
        return Response({"detail": "comment flagged as inappropriate"}, status=status.HTTP_201_CREATED)


class ProjectReportCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        project = get_object_or_404(Project, pk=pk)
        report = ProjectReport.objects.filter(project=project, user=request.user).first()
        if report:
            report.delete()
            return Response({"detail": "project unflagged"}, status=status.HTTP_200_OK)

        ProjectReport.objects.create(project=project, user=request.user)
        return Response({"detail": "project flagged as inappropriate"}, status=status.HTTP_201_CREATED)


class ProjectRatingCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        project = get_object_or_404(Project, pk=pk)
        rating = ProjectRating.objects.filter(project=project, user=request.user).first()

        if rating:
            serializer = ProjectRatingSerializer(rating, data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)

        serializer = ProjectRatingSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(project=project, user=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
