"""
FaceVision Serializers
"""
from rest_framework import serializers
from .models import UploadedImage, DetectedFace, FaceCluster


class DetectedFaceSerializer(serializers.ModelSerializer):
    face_thumbnail_url = serializers.SerializerMethodField()
    cluster_label = serializers.SerializerMethodField()

    class Meta:
        model = DetectedFace
        fields = [
            'id', 'bbox_x', 'bbox_y', 'bbox_w', 'bbox_h',
            'confidence', 'face_thumbnail_url', 'cluster_label',
            'detected_at',
        ]

    def get_face_thumbnail_url(self, obj):
        request = self.context.get('request')
        if obj.face_thumbnail and request:
            return request.build_absolute_uri(obj.face_thumbnail.url)
        return None

    def get_cluster_label(self, obj):
        if obj.cluster:
            return obj.cluster.label
        return -1


class UploadedImageSerializer(serializers.ModelSerializer):
    original_image_url = serializers.SerializerMethodField()
    processed_image_url = serializers.SerializerMethodField()
    faces = DetectedFaceSerializer(many=True, read_only=True)
    extracted_features = serializers.SerializerMethodField()

    class Meta:
        model = UploadedImage
        fields = [
            'id', 'filename', 'status', 'error_message',
            'face_count', 'original_image_url', 'processed_image_url',
            'faces', 'extracted_features', 'uploaded_at', 'processed_at',
        ]

    def get_original_image_url(self, obj):
        request = self.context.get('request')
        if obj.original_image and request:
            return request.build_absolute_uri(obj.original_image.url)
        return None

    def get_processed_image_url(self, obj):
        request = self.context.get('request')
        if obj.processed_image and request:
            return request.build_absolute_uri(obj.processed_image.url)
        return None

    def get_extracted_features(self, obj):
        """Summarise features per face for dashboard table."""
        features = []
        for face in obj.faces.all():
            features.append({
                'face_id': str(face.id),
                'bbox': {
                    'x': face.bbox_x, 'y': face.bbox_y,
                    'w': face.bbox_w, 'h': face.bbox_h,
                },
                'confidence': round(face.confidence, 4),
                'has_landmarks': bool(face.landmarks_json),
                'landmark_count': len(face.get_landmarks()),
                'has_embedding': bool(face.embedding_json),
                'embedding_dim': 512 if face.embedding_json else 0,
                'cluster': face.cluster.label if face.cluster else -1,
            })
        return features


class FaceClusterSerializer(serializers.ModelSerializer):
    face_count = serializers.SerializerMethodField()
    faces = serializers.SerializerMethodField()
    representative_thumbnail = serializers.SerializerMethodField()

    class Meta:
        model = FaceCluster
        fields = [
            'id', 'label', 'person_label',
            'face_count', 'faces', 'representative_thumbnail',
            'created_at', 'updated_at',
        ]

    def get_face_count(self, obj):
        return obj.faces.count()

    def get_faces(self, obj):
        request = self.context.get('request')
        faces = obj.faces.select_related('image').all()[:20]  # cap for performance
        result = []
        for face in faces:
            thumb_url = None
            if face.face_thumbnail and request:
                thumb_url = request.build_absolute_uri(face.face_thumbnail.url)
            orig_url = None
            if face.image.processed_image and request:
                orig_url = request.build_absolute_uri(face.image.processed_image.url)
            elif face.image.original_image and request:
                orig_url = request.build_absolute_uri(face.image.original_image.url)
            result.append({
                'face_id': str(face.id),
                'image_id': str(face.image_id),
                'image_filename': face.image.filename,
                'thumbnail_url': thumb_url,
                'image_url': orig_url,
                'confidence': round(face.confidence, 4),
            })
        return result

    def get_representative_thumbnail(self, obj):
        """Return the highest-confidence face thumbnail in the cluster."""
        request = self.context.get('request')
        face = obj.faces.filter(face_thumbnail__isnull=False).order_by('-confidence').first()
        if face and request:
            return request.build_absolute_uri(face.face_thumbnail.url)
        return None


class SearchResultSerializer(serializers.Serializer):
    face_id = serializers.UUIDField()
    image_id = serializers.UUIDField()
    image_filename = serializers.CharField()
    similarity = serializers.FloatField()
    thumbnail_url = serializers.CharField(allow_null=True)
    image_url = serializers.CharField(allow_null=True)
    bbox = serializers.DictField()
    cluster = serializers.IntegerField(allow_null=True)
