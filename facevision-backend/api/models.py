"""
FaceVision Models
-----------------
UploadedImage  - stores uploaded images and processing state
DetectedFace   - per-face records with bounding box, landmarks, embedding
FaceCluster    - groups of faces belonging to the same person
"""
import json
import uuid
from django.db import models


class UploadedImage(models.Model):
    """An image uploaded by the user."""

    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        PROCESSING = 'processing', 'Processing'
        DONE = 'done', 'Done'
        FAILED = 'failed', 'Failed'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    original_image = models.ImageField(upload_to='uploads/')
    processed_image = models.ImageField(upload_to='processed/', null=True, blank=True)
    filename = models.CharField(max_length=255)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    error_message = models.TextField(blank=True, null=True)
    face_count = models.IntegerField(default=0)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-uploaded_at']

    def __str__(self):
        return f"{self.filename} ({self.status})"


class DetectedFace(models.Model):
    """A single detected face within an uploaded image."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    image = models.ForeignKey(UploadedImage, on_delete=models.CASCADE, related_name='faces')

    # Bounding box (normalized 0-1 or pixel coords)
    bbox_x = models.FloatField()
    bbox_y = models.FloatField()
    bbox_w = models.FloatField()
    bbox_h = models.FloatField()

    # Detection confidence
    confidence = models.FloatField(default=0.0)

    # 468 MediaPipe landmarks stored as JSON list of [x,y,z] triplets
    landmarks_json = models.TextField(blank=True, null=True)

    # 512-dim ArcFace embedding stored as JSON list of floats
    embedding_json = models.TextField(blank=True, null=True)

    # Cropped aligned face thumbnail
    face_thumbnail = models.ImageField(upload_to='faces/', null=True, blank=True)

    # Cluster assignment (-1 = noise/unassigned)
    cluster = models.ForeignKey(
        'FaceCluster', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='faces'
    )

    detected_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['detected_at']

    def get_embedding(self):
        """Return embedding as numpy array."""
        import numpy as np
        if self.embedding_json:
            return np.array(json.loads(self.embedding_json), dtype=np.float32)
        return None

    def set_embedding(self, arr):
        import numpy as np
        self.embedding_json = json.dumps(arr.tolist())

    def get_landmarks(self):
        if self.landmarks_json:
            return json.loads(self.landmarks_json)
        return []

    def __str__(self):
        return f"Face in {self.image.filename} (conf={self.confidence:.2f})"


class FaceCluster(models.Model):
    """A cluster of faces that likely belong to the same person."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    label = models.IntegerField()           # DBSCAN cluster label
    person_label = models.CharField(max_length=100, blank=True, null=True)

    # Mean embedding of all faces in this cluster
    centroid_json = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['label']

    def get_centroid(self):
        import numpy as np
        if self.centroid_json:
            return np.array(json.loads(self.centroid_json), dtype=np.float32)
        return None

    def set_centroid(self, arr):
        self.centroid_json = json.dumps(arr.tolist())

    def __str__(self):
        name = self.person_label or f"Person {self.label}"
        return f"Cluster {name} ({self.faces.count()} faces)"
