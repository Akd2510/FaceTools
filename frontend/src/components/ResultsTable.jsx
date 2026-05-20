import React, { useState } from 'react';
import { Thumb, StatusBadge, Badge, Button, EmptyState, Spinner } from './UI';
import { deleteImage } from '../utils/api';

function FeaturesCell({ features }) {
  if (!features || features.length === 0) {
    return <span style={{ color: 'var(--text-muted)', fontSize: '0.72rem' }}>No faces</span>;
  }
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
      {features.map((f, i) => (
        <div key={f.face_id} style={{
          background: 'var(--bg-elevated)',
          border: '1px solid var(--bg-border)',
          borderRadius: 'var(--radius-sm)',
          padding: '0.35rem 0.6rem',
          fontSize: '0.68rem',
          lineHeight: 1.6,
        }}>
          <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
            <Badge color="cyan">Face {i + 1}</Badge>
            <Badge color={f.confidence > 0.8 ? 'green' : 'amber'}>
              conf {(f.confidence * 100).toFixed(0)}%
            </Badge>
            {f.has_landmarks && <Badge color="muted">{f.landmark_count} landmarks</Badge>}
            {f.has_embedding && <Badge color="muted">{f.embedding_dim}‑dim emb</Badge>}
            {f.cluster >= 0 && <Badge color="cyan">cluster {f.cluster}</Badge>}
          </div>
          <div style={{ color: 'var(--text-muted)', marginTop: '0.2rem' }}>
            bbox ({Math.round(f.bbox.x)}, {Math.round(f.bbox.y)}) {Math.round(f.bbox.w)}×{Math.round(f.bbox.h)}px
          </div>
        </div>
      ))}
    </div>
  );
}

function ImageRow({ img, onDeleted }) {
  const [deleting, setDeleting] = useState(false);
  const [expanded, setExpanded] = useState(false);

  const handleDelete = async () => {
    if (!window.confirm('Delete this image and all detected faces?')) return;
    setDeleting(true);
    try {
      await deleteImage(img.id);
      onDeleted(img.id);
    } catch {
      setDeleting(false);
    }
  };

  const isLoading = img.status === 'pending' || img.status === 'processing';

  return (
    <>
      <tr style={{ borderBottom: '1px solid var(--bg-border)', transition: 'background 0.15s' }}
        onMouseEnter={e => e.currentTarget.style.background = 'rgba(255,255,255,0.02)'}
        onMouseLeave={e => e.currentTarget.style.background = 'transparent'}
      >
        {/* Original */}
        <td style={TD}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            <Thumb src={img.original_image_url} alt={img.filename} size={52} />
            <div>
              <div style={{ fontSize: '0.78rem', fontWeight: 700, color: 'var(--text-primary)', maxWidth: 160, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                {img.filename}
              </div>
              <div style={{ fontSize: '0.65rem', color: 'var(--text-muted)', marginTop: '0.15rem' }}>
                {new Date(img.uploaded_at).toLocaleString()}
              </div>
            </div>
          </div>
        </td>

        {/* Status */}
        <td style={TD}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <StatusBadge status={img.status} />
            {isLoading && <Spinner size={14} />}
          </div>
          {img.error_message && (
            <div style={{ fontSize: '0.65rem', color: 'var(--red)', marginTop: '0.3rem', maxWidth: 180 }}>
              {img.error_message}
            </div>
          )}
        </td>

        {/* Processed */}
        <td style={TD}>
          {img.processed_image_url ? (
            <a href={img.processed_image_url} target="_blank" rel="noreferrer">
              <Thumb src={img.processed_image_url} alt="processed" size={52}
                style={{ cursor: 'pointer', transition: 'opacity 0.15s' }} />
            </a>
          ) : isLoading ? (
            <div style={{ width: 52, height: 52, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <Spinner size={20} />
            </div>
          ) : (
            <span style={{ color: 'var(--text-muted)', fontSize: '0.72rem' }}>—</span>
          )}
        </td>

        {/* Faces */}
        <td style={TD}>
          <Badge color={img.face_count > 0 ? 'cyan' : 'muted'}>
            {img.face_count} {img.face_count === 1 ? 'face' : 'faces'}
          </Badge>
        </td>

        {/* Features toggle */}
        <td style={TD}>
          {img.extracted_features?.length > 0 ? (
            <Button size="sm" variant="ghost" onClick={() => setExpanded(v => !v)}>
              {expanded ? '▲ Hide' : '▼ Show'}
            </Button>
          ) : (
            <span style={{ color: 'var(--text-muted)', fontSize: '0.72rem' }}>—</span>
          )}
        </td>

        {/* Actions */}
        <td style={TD}>
          <Button size="sm" variant="danger" onClick={handleDelete} disabled={deleting}>
            {deleting ? <Spinner size={12} color="var(--red)" /> : '✕'}
          </Button>
        </td>
      </tr>

      {/* Expanded features row */}
      {expanded && (
        <tr style={{ background: 'var(--bg-elevated)' }}>
          <td colSpan={6} style={{ padding: '0.75rem 1rem' }}>
            <FeaturesCell features={img.extracted_features} />
          </td>
        </tr>
      )}
    </>
  );
}

const TD = {
  padding: '0.75rem 1rem',
  verticalAlign: 'middle',
  fontSize: '0.78rem',
};

const TH = {
  ...TD,
  color: 'var(--text-muted)',
  fontWeight: 700,
  letterSpacing: '0.08em',
  fontSize: '0.65rem',
  borderBottom: '1px solid var(--bg-border)',
  background: 'var(--bg-elevated)',
  textAlign: 'left',
};

export default function ResultsTable({ images, loading, onDeleted, onLoadMore, hasMore }) {
  if (loading && images.length === 0) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', padding: '3rem' }}>
        <Spinner size={32} />
      </div>
    );
  }

  if (!loading && images.length === 0) {
    return (
      <EmptyState
        icon="🖼"
        title="No images yet"
        description="Upload images using the Upload tab to begin face detection and analysis."
      />
    );
  }

  return (
    <div>
      <div style={{ overflowX: 'auto', borderRadius: 'var(--radius-lg)', border: '1px solid var(--bg-border)' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse' }}>
          <thead>
            <tr>
              <th style={TH}>ORIGINAL IMAGE</th>
              <th style={TH}>STATUS</th>
              <th style={TH}>PROCESSED</th>
              <th style={TH}>FACES</th>
              <th style={TH}>FEATURES</th>
              <th style={TH}></th>
            </tr>
          </thead>
          <tbody>
            {images.map(img => (
              <ImageRow key={img.id} img={img} onDeleted={onDeleted} />
            ))}
          </tbody>
        </table>
      </div>

      {hasMore && (
        <div style={{ display: 'flex', justifyContent: 'center', marginTop: '1rem' }}>
          <Button variant="ghost" onClick={onLoadMore} disabled={loading}>
            {loading ? <Spinner size={14} /> : 'Load more'}
          </Button>
        </div>
      )}
    </div>
  );
}
