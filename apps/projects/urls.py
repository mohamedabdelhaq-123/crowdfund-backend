from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    CategoryViewSet,
    CommentReportCreateView,
    HomepageView,
    ProjectCommentCollectionView,
    ProjectCommentDetailView,
    ProjectSearchView,
    SimilarProjectsView,
    TagViewSet,
    ProjectViewSet,
)

router = DefaultRouter()
router.register(r"categories", CategoryViewSet)
router.register(r"tags",TagViewSet)
router.register(r"",ProjectViewSet)
urlpatterns = [
    path("", include(router.urls)),
    path("home/", HomepageView.as_view(), name="homepage"),
    path("search/", ProjectSearchView.as_view(), name="project-search"),
    path("<int:pk>/similar/", SimilarProjectsView.as_view(), name="similar-projects"),
    path("<int:project_id>/comments/", ProjectCommentCollectionView.as_view(), name="project-comments"),
    path("comments/<int:pk>/", ProjectCommentDetailView.as_view(), name="project-comment-detail"),
    path("comments/<int:pk>/report/", CommentReportCreateView.as_view(), name="comment-report"),
]
