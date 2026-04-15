from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CategoryViewSet, HomepageView, ProjectSearchView, SimilarProjectsView, TagViewSet,ProjectViewSet

router = DefaultRouter()
router.register(r"categories", CategoryViewSet)
router.register(r"tags",TagViewSet)
router.register(r"",ProjectViewSet)
urlpatterns = [
    path("", include(router.urls)),
    path("home/", HomepageView.as_view(), name="homepage"),
    path("search/", ProjectSearchView.as_view(), name="project-search"),
    path("<int:pk>/similar/", SimilarProjectsView.as_view(), name="similar-projects"),
]
