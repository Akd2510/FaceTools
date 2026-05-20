from django.urls import path
from . import views

urlpatterns = [
    # Images
    path('images/', views.ImageListUploadView.as_view(), name='image-list'),
    path('images/upload/', views.ImageListUploadView.as_view(), name='image-upload'),
    path('images/<uuid:pk>/', views.ImageDetailView.as_view(), name='image-detail'),

    # Clusters
    path('clusters/', views.ClusterListView.as_view(), name='cluster-list'),
    path('clusters/recluster/', views.ReclusterView.as_view(), name='recluster'),
    path('clusters/<uuid:pk>/', views.ClusterDetailView.as_view(), name='cluster-detail'),

    # Search
    path('search/', views.FaceSearchView.as_view(), name='face-search'),

    # Utilities
    path('stats/', views.StatsView.as_view(), name='stats'),
    path('health/', views.HealthView.as_view(), name='health'),
]
