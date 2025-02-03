from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from .models import Post, Image
from .utils import generate_linkedin_hiring_post, generate_linkedin_post_components
from .serializers import PostSerializer, PostCreateSerializer, ImageSerializer

# Post Views
class PostListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        posts = Post.objects.filter(user=request.user)
        serializer = PostSerializer(posts, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class PostDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, pk, user):
        try:
            return Post.objects.get(pk=pk, user=user)
        except Post.DoesNotExist:
            return None

    def get(self, request, pk):
        post = self.get_object(pk, request.user)
        if not post:
            return Response({"error": "Post not found or you do not have permission to view it."}, status=status.HTTP_404_NOT_FOUND)
        serializer = PostSerializer(post)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, pk):
        post = self.get_object(pk, request.user)
        if not post:
            return Response({"error": "Post not found or you do not have permission to update it."}, status=status.HTTP_404_NOT_FOUND)
        serializer = PostSerializer(post, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        post = self.get_object(pk, request.user)
        if not post:
            return Response({"error": "Post not found or you do not have permission to delete it."}, status=status.HTTP_404_NOT_FOUND)
        post.delete()
        return Response({"message": "Post deleted successfully."}, status=status.HTTP_204_NO_CONTENT)


class PostCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = PostCreateSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# Image Views
class ImageListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, post_id):
        try:
            post = Post.objects.get(id=post_id, user=request.user)
        except Post.DoesNotExist:
            return Response({"error": "Post not found or you do not have permission to view its images."}, status=status.HTTP_404_NOT_FOUND)

        images = post.images.all()
        serializer = ImageSerializer(images, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class ImageUploadView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, post_id):
        try:
            post = Post.objects.get(id=post_id, user=request.user)
        except Post.DoesNotExist:
            return Response({"error": "Post not found or you do not have permission to upload images."}, status=status.HTTP_404_NOT_FOUND)

        serializer = ImageSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(post=post)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ImageDeleteView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, post_id, image_id):
        try:
            post = Post.objects.get(id=post_id, user=request.user)
        except Post.DoesNotExist:
            return Response({"error": "Post not found or you do not have permission to delete its images."}, status=status.HTTP_404_NOT_FOUND)

        try:
            image = Image.objects.get(id=image_id, post=post)
            image.delete()
            return Response({"message": "Image deleted successfully."}, status=status.HTTP_204_NO_CONTENT)
        except Image.DoesNotExist:
            return Response({"error": "Image not found."}, status=status.HTTP_404_NOT_FOUND)


class GenerateAIContentView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            # Fetch the post for the authenticated user
            post = Post.objects.get(id=pk, user=request.user)
            tone = request.data.get("tone", "numbered list")
        except Post.DoesNotExist:
            return Response({"error": "Post not found or you do not have permission to access it."}, status=status.HTTP_404_NOT_FOUND)

        post_content = post.user_content
        if post_content == {} or post_content is None:
            return Response({"error": "Post Details is empty."}, status=status.HTTP_400_BAD_REQUEST)
        
        # Generate AI content using user content and title
        # result: str = str(generate_linkedin_hiring_post(details=post_content))

        result = generate_linkedin_post_components(post_content, tone)
        print(result)
        print(type(result))
        if result is None:
            return Response({"error": "Failed to generate AI content."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        

        # Update the post with the generated content
        post.ai_generated_content = result
        post.save()

        return Response({
            "message": "AI content generated successfully.",
            "ai_content": result
        }, status=status.HTTP_200_OK)
    