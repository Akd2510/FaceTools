"""
FaceVision API Views
"""
import logging
import threading

from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.pagination import PageNumberPagination

from .models import UploadedImage, DetectedFace, FaceCluster
from .serializers import (
    UploadedImageSerializer, FaceClusterSerializer, SearchResultSerializer
)

logger = logging.getLogger(__name__)


def _run_pipeline_async(image_id: str):
    """Run the processing pipeline in a background thread."""
    from .pipeline import process_image
    from django.db import connection

    try:
        img = UploadedImage.objects.get(id=image_id)
        img.status = UploadedImage.Status.PROCESSING
        img.save(update_fields=['status'])
        process_image(img)
    except Exception as exc:
        logger.exception("Pipeline failed for image %s: %s", image_id, exc)
        try:
            img = UploadedImage.objects.get(id=image_id)
            img.status = UploadedImage.Status.FAILED
            img.error_message = str(exc)
            img.save(update_fields=['status', 'error_message'])
        except Exception:
            pass
    finally:
        connection.close()


# ---------------------------------------------------------------------------
# Image Upload & List
# ---------------------------------------------------------------------------

class ImageListUploadView(APIView):
    """
    GET  /api/images/          – list all uploaded images (paginated)
    POST /api/images/upload/   – upload one or more images
    """
    parser_classes = [MultiPartParser, FormParser]

    def get(self, request):
        qs = UploadedImage.objects.prefetch_related('faces').all()
        paginator = PageNumberPagination()
        paginator.page_size = 20
        page = paginator.paginate_queryset(qs, request)
        serializer = UploadedImageSerializer(page, many=True, context={'request': request})
        return paginator.get_paginated_response(serializer.data)

    def post(self, request):
        files = request.FILES.getlist('images')
        if not files:
            return Response(
                {'error': 'No images provided. Send files under the "images" key.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        created = []
        for f in files:
            img = UploadedImage.objects.create(
                original_image=f,
                filename=f.name,
                status=UploadedImage.Status.PENDING,
            )
            # Kick off processing in background thread
            t = threading.Thread(target=_run_pipeline_async, args=(str(img.id),), daemon=True)
            t.start()
            created.append(img)

        serializer = UploadedImageSerializer(created, many=True, context={'request': request})
        return Response(serializer.data, status=status.HTTP_202_ACCEPTED)


class ImageDetailView(APIView):
    """GET /api/images/<id>/ – retrieve a single image and its faces."""

    def get(self, request, pk):
        img = get_object_or_404(UploadedImage, pk=pk)
        serializer = UploadedImageSerializer(img, context={'request': request})
        return Response(serializer.data)

    def delete(self, request, pk):
        img = get_object_or_404(UploadedImage, pk=pk)
        img.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# ---------------------------------------------------------------------------
# Cluster Views
# ---------------------------------------------------------------------------

class ClusterListView(APIView):
    """GET /api/clusters/ – list all face clusters."""

    def get(self, request):
        clusters = FaceCluster.objects.prefetch_related('faces__image').all()
        serializer = FaceClusterSerializer(clusters, many=True, context={'request': request})
        return Response(serializer.data)


class ClusterDetailView(APIView):
    """GET /api/clusters/<id>/ – detail view for one cluster."""

    def get(self, request, pk):
        cluster = get_object_or_404(FaceCluster, pk=pk)
        serializer = FaceClusterSerializer(cluster, context={'request': request})
        return Response(serializer.data)

    def patch(self, request, pk):
        """Allow labelling a cluster with a person name."""
        cluster = get_object_or_404(FaceCluster, pk=pk)
        label = request.data.get('person_label', '').strip()
        if not label:
            return Response({'error': 'person_label is required'}, status=400)
        cluster.person_label = label
        cluster.save(update_fields=['person_label', 'updated_at'])
        serializer = FaceClusterSerializer(cluster, context={'request': request})
        return Response(serializer.data)


class ReclusterView(APIView):
    """POST /api/clusters/recluster/ – re-run DBSCAN over all embeddings."""

    def post(self, request):
        from .pipeline import _recluster_all
        try:
            _recluster_all()
            count = FaceCluster.objects.count()
            return Response({'message': f'Reclustered. Found {count} clusters.'})
        except Exception as exc:
            logger.exception("Recluster failed: %s", exc)
            return Response({'error': str(exc)}, status=500)


# ---------------------------------------------------------------------------
# Search View
# ---------------------------------------------------------------------------

class FaceSearchView(APIView):
    """
    POST /api/search/
    Body: multipart with field "query_image" (file) or "image_id" (UUID)
    Returns: ranked list of similar faces with similarity scores
    """
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def post(self, request):
        from .pipeline import search_similar_faces

        query_bytes = None

        # Option A – uploaded file
        query_file = request.FILES.get('query_image')
        if query_file:
            query_bytes = query_file.read()

        # Option B – reference an already-uploaded image by id
        image_id = request.data.get('image_id')
        if not query_bytes and image_id:
            try:
                img = UploadedImage.objects.get(id=image_id)
                img.original_image.open()
                query_bytes = img.original_image.read()
            except UploadedImage.DoesNotExist:
                return Response({'error': 'Image not found'}, status=404)

        if not query_bytes:
            return Response(
                {'error': 'Provide query_image (file) or image_id'},
                status=400
            )

        try:
            top_k = int(request.data.get('top_k', 10))
            results = search_similar_faces(query_bytes, top_k=top_k)
        except ValueError as exc:
            return Response({'error': str(exc)}, status=400)
        except Exception as exc:
            logger.exception("Search error: %s", exc)
            return Response({'error': 'Internal search error'}, status=500)

        data = []
        for face, sim in results:
            thumb_url = None
            image_url = None
            if face.face_thumbnail:
                thumb_url = request.build_absolute_uri(face.face_thumbnail.url)
            if face.image.processed_image:
                image_url = request.build_absolute_uri(face.image.processed_image.url)
            elif face.image.original_image:
                image_url = request.build_absolute_uri(face.image.original_image.url)

            data.append({
                'face_id': str(face.id),
                'image_id': str(face.image_id),
                'image_filename': face.image.filename,
                'similarity': round(sim, 4),
                'thumbnail_url': thumb_url,
                'image_url': image_url,
                'bbox': {
                    'x': face.bbox_x, 'y': face.bbox_y,
                    'w': face.bbox_w, 'h': face.bbox_h,
                },
                'cluster': face.cluster.label if face.cluster else None,
            })

        return Response({'results': data, 'count': len(data)})


# ---------------------------------------------------------------------------
# Stats / Health
# ---------------------------------------------------------------------------

class StatsView(APIView):
    """GET /api/stats/ – summary statistics for the dashboard."""

    def get(self, request):
        total_images = UploadedImage.objects.count()
        processed = UploadedImage.objects.filter(status='done').count()
        failed = UploadedImage.objects.filter(status='failed').count()
        pending = UploadedImage.objects.filter(status__in=['pending', 'processing']).count()
        total_faces = DetectedFace.objects.count()
        total_clusters = FaceCluster.objects.count()

        return Response({
            'total_images': total_images,
            'processed': processed,
            'failed': failed,
            'pending': pending,
            'total_faces': total_faces,
            'total_clusters': total_clusters,
        })


class HealthView(APIView):
    """GET /api/health/ – liveness probe."""

    def get(self, request):
        return Response({'status': 'ok'})
