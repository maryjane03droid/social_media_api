from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    RegisterView, LoginView, ProfileDetailView, PostViewSet,
    CommentListCreateView, CommentDetailView, FollowUserView, UserSearchView
)

# A Router handles full standard CRUD endpoints for posts automatically
# E.g., GET /api/posts/, POST /api/posts/, DELETE /api/posts/{id}/
router = DefaultRouter()
router.register(r'posts', PostViewSet, basename='post')

urlpatterns = [
    # --- Authentication Endpoints ---
    path('auth/register/', RegisterView.as_view(), name='register'),
    path('auth/login/', LoginView.as_view(), name='login'),
    
    # --- Profile Endpoints ---
    path('profiles/<int:user_id>/', ProfileDetailView.as_view(), name='profile-detail'),
    
    # --- Post Endpoints (Includes router generated CRUD + Feed + Likes) ---
    path('', include(router.urls)),
    
    # --- Comment Endpoints ---
    path('posts/<int:post_id>/comments/', CommentListCreateView.as_view(), name='comment-list-create'),
    path('comments/<int:id>/', CommentDetailView.as_view(), name='comment-detail'),
    
    # --- Follow Endpoints ---
    path('users/<int:user_id>/follow/', FollowUserView.as_view(), name='user-follow'),
    
    # --- Search Endpoints ---
    path('search/users/', UserSearchView.as_view(), name='user-search'),
]