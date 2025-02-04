from django.urls import path
from .views import (
    PostListView, PostCreateView, PostDetailView,
    ImageListView, ImageUploadView, ImageDeleteView,
    GenerateAIContentView, RegenerateSectionView, ChatView,
    PromptsPostView,
)

urlpatterns = [
    # Post endpoints
    path('', PostListView.as_view(), name='post-list'),
    path('create/', PostCreateView.as_view(), name='post-create'),
    path('<int:pk>/', PostDetailView.as_view(), name='post-detail'),

    # Image endpoints
    path('<int:post_id>/images/', ImageListView.as_view(), name='image-list'),
    path('<int:post_id>/images/upload/', ImageUploadView.as_view(), name='image-upload'),
    path('<int:post_id>/images/<int:image_id>/delete/', ImageDeleteView.as_view(), name='image-delete'),

    path('<int:pk>/generate-ai-content/', GenerateAIContentView.as_view(), name='generate-ai-content'),
    path('<int:pk>/regenerate-content/', RegenerateSectionView.as_view(), name='regenerate-content'),
    path('<int:pk>/chat/', ChatView.as_view(), name='chat'),

    path('<int:pk>/prompts/', PromptsPostView.as_view(), name='prompts'),

]
