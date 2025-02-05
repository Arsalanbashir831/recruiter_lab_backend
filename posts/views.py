from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from .models import Post, Image, Prompt
from .utils import generate_linkedin_hiring_post, generate_linkedin_post_components, generate_section, derive_section
from .utils import DerivedSections
from .serializers import PostSerializer, PostCreateSerializer, ImageSerializer, PromptSerializer

from django.db import transaction

# Post Views
class PostListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        posts = Post.objects.filter(user=request.user)
        serializer = PostSerializer(posts, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

class PostUpdateView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request, pk):
        try:
            print(request.user)
            post = Post.objects.get(pk=pk, user=request.user)
            print(post)
            serializer = PostSerializer(post, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Post.DoesNotExist:
            return Response({"error": "Post not found or you do not have permission to update it."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
class PostDeleteView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, pk):
        try:
            post = Post.objects.get(pk=pk, user=request.user)
            post.delete()
            return Response({"message": "Post deleted successfully."}, status=status.HTTP_204_NO_CONTENT)
        except Post.DoesNotExist:
            return Response({"error": "Post not found or you do not have permission to delete it."}, status=status.HTTP_404_NOT_FOUND)
        

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
        if isinstance(result, str):
            return Response({"error": f"Failed to generate AI content. {result}" }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        

        # Update the post with the generated content
        post.ai_generated_content = result
        post.save()

        return Response({
            "message": "AI content generated successfully.",
            "ai_content": result
        }, status=status.HTTP_200_OK)
    
class RegenerateSectionView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            # Fetch the post for the authenticated user
            post = Post.objects.get(id=pk, user=request.user)
            prompt = request.data.get("prompt", "")

            if not prompt:
                return Response({"error": "Prompt is required."}, status=status.HTTP_400_BAD_REQUEST)
            section = request.data.get("section", "")
            if not section:
                return Response({"error": "Section is required."}, status=status.HTTP_400_BAD_REQUEST)
            
            sections = ["hook", "body", "call_to_action"]

            if section not in sections:
                return Response({"error": "Invalid section."}, status=status.HTTP_400_BAD_REQUEST)
            
        except Post.DoesNotExist:
            return Response({"error": "Post not found or you do not have permission to access it."}, status=status.HTTP_404_NOT_FOUND)

        post_content = post.user_content
        if post_content == {} or post_content is None:
            return Response({"error": "Post Details is empty."}, status=status.HTTP_400_BAD_REQUEST)
        
        ai_content = post.ai_generated_content
        if ai_content == {} or ai_content is None:
            return Response({"error": "AI Content is empty."}, status=status.HTTP_400_BAD_REQUEST)
        
        content = ai_content[section]
        if not content:
            return Response({"error": "AI Content is empty."}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            
            # Generate AI content using user content and title
            result = str(generate_section(content, prompt))
            if result is None:
                return Response({"error": "Failed to generate AI content." }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            with transaction.atomic(): 
            # Update the post with the generated content
                ai_content[section] = result
                post.ai_generated_content = ai_content
                post.save()

                Prompt.objects.create(prompt=prompt, post=post, response=ai_content)

        except Exception as e:
            return Response({"error": f"Failed to generate AI content. {e}" }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        return Response({
            "message": "AI content generated successfully.",
            "ai_content": result
        }, status=status.HTTP_200_OK)
    


class ChatView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            # Fetch the post for the authenticated user
            post : Post = Post.objects.get(id=pk, user=request.user)
            prompt = request.data.get("prompt", "")
        except Post.DoesNotExist:
            return Response({"error": "Post not found or you do not have permission to access it."}, status=status.HTTP_404_NOT_FOUND)
        post_ai_content = post.ai_generated_content
        if post_ai_content == {} or post_ai_content is None:
            return Response({"error": "AI Content is empty."}, status=status.HTTP_400_BAD_REQUEST)

        derived_sections: DerivedSections = derive_section(prompt)
        derived_sections = derived_sections.model_dump(mode="json")
        print(derived_sections)

        try:
            with transaction.atomic():
                post_ai_content = post.ai_generated_content
                for section in derived_sections["sections"]:
                    if section not in ["hook", "body", "call_to_action"]:
                        return Response({"error": "Invalid section."}, status=status.HTTP_400_BAD_REQUEST)
                    
                    if post_ai_content == {} or post_ai_content is None:
                        return Response({"error": "AI Content is empty."}, status=status.HTTP_400_BAD_REQUEST)
                    content = post_ai_content[section]
                    if not content:
                        return Response({"error": "AI Content is empty."}, status=status.HTTP_400_BAD_REQUEST)
                    result = str(generate_section(content, prompt))
                    if result is None:
                        return Response({"error": "Failed to generate AI content." }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                    post_ai_content[section] = result
                post.ai_generated_content = post_ai_content
                post.save()    
                Prompt.objects.create(prompt=prompt, post=post, response=post_ai_content)
        except Exception as e:
            print(e)
            return Response({"error": "Failed to generate AI content." }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        

        return Response({"message": "AI content generated successfully.", "section" : derived_sections, "ai_content": post_ai_content}, status=status.HTTP_200_OK)
    


class PromptsPostView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            # Fetch the post for the authenticated user
            post = Post.objects.get(id=pk, user=request.user)
        except Post.DoesNotExist:
            return Response({"error": "Post not found or you do not have permission to access it."}, status=status.HTTP_404_NOT_FOUND)
        
        prompts = Prompt.objects.filter(post=post)
        
        serializer = PromptSerializer(prompts, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)