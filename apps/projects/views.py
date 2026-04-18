from rest_framework import viewsets
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import generics, filters, status
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404
from django.db.models import Avg,Value
from django.db.models.functions import Coalesce
from .models import Category, Comment, CommentReport, Project, ProjectRating, ProjectReport, Tag,Image
from .serializers import CategorySerializer, CommentSerializer, ProjectRatingSerializer, ProjectSerializer, TagSerializer,ImageSerializer


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticatedOrReadOnly]


class TagViewSet(viewsets.ModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]


class ProjectViewSet(viewsets.ModelViewSet):
    serializer_class = ProjectSerializer
    parser_classes = (MultiPartParser, FormParser)
    def get_queryset(self):
        queryset = Project.objects.all()
        if self.action in ['list', 'retrieve']:
            return queryset.annotate(
                avg_rate=Coalesce(Avg('ratings__stars'), Value(0.0))
            ).select_related('user').prefetch_related('tags', 'image_set')
        return queryset
    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            permission_classes = [AllowAny]
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]
    def get_object(self):
        obj = super().get_object()
        if(self.action not in ['retrieve']):
            if obj.user != self.request.user:
                raise PermissionDenied("You do not have permission to edit this project.")
        return obj

    def perform_update(self, serializer):
        serializer.save(user=self.request.user)
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
    
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        
  
        if (instance.current_money / instance.target) > 0.25:
            raise PermissionDenied("You cant cancel a project that has reached more than 25% of th target")
        if(instance.status != 'pending'):
            raise PermissionDenied(f"You cant cancel this project because it is {instance.status}")

        instance.status = 'canceled'
        instance.save()
        serializer = self.get_serializer(instance)
        return Response({"detail": serializer.data}, status=200)


        
    


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
    permission_classes = [AllowAny]
    def get(self, request):
        # Base queryset with rating annotation and performance optimizations
        base_queryset = Project.objects.annotate(
            avg_rate=Coalesce(Avg('ratings__stars'), Value(0.0))
        ).select_related('user').prefetch_related('image_set')

        latest_projects = base_queryset.order_by("-created_at")[:5]
        featured_projects = base_queryset.filter(is_featured=True)[:5]

        # Filter only projects that have at least one rating for the "Top Rated" section
        top_rated_projects = (
            base_queryset.filter(ratings__isnull=False)
            .distinct()
            .order_by("-avg_rate", "-created_at")[:5]
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
    serializer_class = ProjectSerializer
    permission_classes = [AllowAny]
    filter_backends = [filters.SearchFilter]
    search_fields = ["title", "details", "category__name", "tags__name"]

    def get_queryset(self):
        return Project.objects.filter(status="pending").annotate(
            avg_rate=Coalesce(Avg('ratings__stars'), Value(0.0))
        ).select_related('user').prefetch_related('image_set')


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
                .annotate(avg_rate=Coalesce(Avg('ratings__stars'), Value(0.0)))
                .select_related('user')
                .prefetch_related('image_set')
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
