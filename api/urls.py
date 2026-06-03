from django.urls import path
from .views import RegisterView, LoginView, ProfileDetailView

urlpatterns = [
    path('auth/register/', RegisterView.as_view(), name='register'),
    path('auth/login/', LoginView.as_view(), name='login'),
    path('profiles/<int:user_id>/', ProfileDetailView.as_view(), name='profile-detail'),
]