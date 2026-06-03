from rest_framework import status, generics, permissions, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.decorators import action
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404
from .models import Profile, Post, Comment, Like
from .serializers import RegisterSerializer, ProfileSerializer, PostSerializer, CommentSerializer

# --- AUTHENTICATION VIEWS ---
class RegisterView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            from rest_framework.authtoken.models import Token
            user = serializer.save()
            token, created = Token.objects.get_or_create(user=user)
            return Response({"user": RegisterSerializer(user).data, "token": token.key}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class LoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        from django.contrib.auth import authenticate
        from rest_framework.authtoken.models import Token
        username = request.data.get('username')
        password = request.data.get('password')
        user = authenticate(username=username, password=password)
        if user is not None:
            token, created = Token.objects.get_or_create(user=user)
            return Response({"token": token.key}, status=status.HTTP_200_OK)
        return Response({"error": "Invalid Credentials"}, status=status.HTTP_400_BAD_REQUEST)


# --- USER PROFILE VIEWS ---
class ProfileDetailView(generics.RetrieveUpdateAPIView):
    queryset = Profile.objects.all()
    serializer_class = ProfileSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    lookup_field = 'user_id'


# --- POSTS AND NEWS FEED VIEWSET ---
class PostViewSet(viewsets.ModelViewSet):
    queryset = Post.objects.all()
    serializer_class = PostSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def perform_create(self, serializer):
        # Automatically saves the logged-in user as the author of the post
        serializer.save(author=self.request.user)

    # GET /api/posts/feed/ -> Fetches posts from users the current logged-in user follows
    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def feed(self, stream):
        user = self.request.user
        # Get the profiles of users the current user is following
        following_profiles = user.profile.following.all()
        # Extract the underlying User objects from those profiles
        followed_users = [profile.user for profile in following_profiles]
        
        # Pull posts authored by followed users or the current user themselves
        posts = Post.objects.filter(author__in=followed_users).order_by('-created_at')
        serializer = self.get_serializer(posts, many=True)
        return Response(serializer.data)

    # POST /api/posts/{post_id}/like/ & DELETE /api/posts/{post_id}/like/
    @action(detail=True, methods=['post', 'delete'], permission_classes=[permissions.IsAuthenticated])
    def like(self, request, pk=None):
        post = self.get_object()
        if request.method == 'POST':
            like, created = Like.objects.get_or_create(user=request.user, post=post)
            if created:
                return Response({"message": "Post liked successfully"}, status=status.HTTP_201_CREATED)
            return Response({"message": "You already liked this post"}, status=status.HTTP_400_BAD_REQUEST)
        
        elif request.method == 'DELETE':
            like = Like.objects.filter(user=request.user, post=post)
            if like.exists():
                like.delete()
                return Response({"message": "Like removed successfully"}, status=status.HTTP_200_OK)
            return Response({"message": "You have not liked this post yet"}, status=status.HTTP_400_BAD_REQUEST)


# --- COMMENT VIEWS ---
class CommentListCreateView(generics.ListCreateAPIView):
    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        return Comment.objects.filter(post_id=self.kwargs['post_id'])

    def perform_create(self, serializer):
        post = get_object_or_404(Post, id=self.kwargs['post_id'])
        serializer.save(author=self.request.user, post=post)

class CommentDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    lookup_field = 'id'


# --- FOLLOW & UNFOLLOW VIEWS ---
class FollowUserView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, user_id):
        user_to_follow = get_object_or_404(User, id=user_id)
        if user_to_follow == request.user:
            return Response({"error": "You cannot follow yourself"}, status=status.HTTP_400_BAD_REQUEST)
        
        current_user_profile = request.user.profile
        target_profile = user_to_follow.profile
        
        # Add target profile to current user's "following" list
        current_user_profile.followers.add(target_profile) 
        return Response({"message": f"Successfully followed {user_to_follow.username}"}, status=status.HTTP_200_OK)

    def delete(self, request, user_id):
        user_to_unfollow = get_object_or_404(User, id=user_id)
        current_user_profile = request.user.profile
        target_profile = user_to_unfollow.profile
        
        if target_profile in current_user_profile.followers.all():
            current_user_profile.followers.remove(target_profile)
            return Response({"message": f"Successfully unfollowed {user_to_unfollow.username}"}, status=status.HTTP_200_OK)
        return Response({"error": "You are not following this user"}, status=status.HTTP_400_BAD_REQUEST)


# --- SEARCH VIEW ---
class UserSearchView(generics.ListAPIView):
    serializer_class = ProfileSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        query = self.request.query_params.get('query', '')
        if query:
            return Profile.objects.filter(user__username__icontains=query)
        return Profile.objects.none()