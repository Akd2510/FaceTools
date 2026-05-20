import React, { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { searchByFile } from '../utils/api';
import { Button, Spinner, Thumb, Badge, EmptyState } from './UI';

function SimilarityBar({ value }) {
  const pct = Math.max(0, Math.min(1, value)) * 100;
  const color = value > 0.8 ? 'var(--green)' : value > 0.5 ? 'var(--cyan)' : 'var(--amber)';
  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 3 }}>
        <span style={{ fontSize: '0.65rem', color: 'var(--text-muted)' }}>cosine similarity</span>
        <span style={{ fontSize: '0.72rem', fontWeight: 700, color }}>{(value * 100).toFixed(1)}%</span>
      </div>
      <div style={{ height: 4, background: 'var(--bg-elevated)', borderRadius: 2 }}>
        <div style={{ height: '100%', width: `${pct}%`, background: color, borderRadius: 2, transition: 'width 0.4s ease' }} />
      </div>
    </div>
  );
}

function ResultCard({ result, rank }) {
  return (
    <div style={{
      display: 'flex', gap: '0.9rem', alignItems: 'flex-start',
      background: 'var(--bg-surface)', border: '1px solid var(--bg-border)',
      borderRadius: 'var(--radius-md)', padding: '0.9rem',
      transition: 'border-color 0.15s',
    }}
      onMouseEnter={e => e.currentTarget.style.borderColor = 'var(--cyan-dim)'}
      onMouseLeave={e => e.currentTarget.style.borderColor = 'var(--bg-border)'}
    >
      <div style={{ position: 'relative', flexShrink: 0 }}>
        <Thumb src={result.thumbnail_url || result.image_url} size={72} />
        <div style={{
          position: 'absolute', top: -6, left: -6,
          width: 20, height: 20, borderRadius: '50%',
          background: 'var(--bg-base)', border: '1px solid var(--bg-border)',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          fontSize: '0.6rem', fontWeight: 700, color: 'var(--cyan)',
        }}>#{rank}</div>
      </div>

      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', marginBottom: '0.4rem', flexWrap: 'wrap' }}>
          <span style={{ fontSize: '0.78rem', fontWeight: 700, color: 'var(--text-primary)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', maxWidth: 160 }}>
            {result.image_filename}
          </span>
          {result.cluster != null && result.cluster >= 0 && (
            <Badge color="cyan">cluster {result.cluster}</Badge>
          )}
        </div>

        <SimilarityBar value={result.similarity} />

        <div style={{ fontSize: '0.65rem', color: 'var(--text-muted)', marginTop: '0.4rem' }}>
          bbox ({Math.round(result.bbox.x)}, {Math.round(result.bbox.y)}) · {Math.round(result.bbox.w)}×{Math.round(result.bbox.h)}px
        </div>

        {result.image_url && (
          <a href={result.image_url} target="_blank" rel="noreferrer"
            style={{ fontSize: '0.65rem', color: 'var(--cyan-dim)', textDecoration: 'none', marginTop: '0.25rem', display: 'block' }}>
            View full image →
          </a>
        )}
      </div>
    </div>
  );
}

export default function SearchPanel() {
  const [queryFile, setQueryFile]   = useState(null);
  const [preview, setPreview]       = useState(null);
  const [searching, setSearching]   = useState(false);
  const [results, setResults]       = useState(null);
  const [error, setError]           = useState(null);
  const [topK, setTopK]             = useState(10);

  const onDrop = useCallback((accepted) => {
    if (!accepted.length) return;
    const f = accepted[0];
    setQueryFile(f);
    setPreview(URL.createObjectURL(f));
    setResults(null);
    setError(null);
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { 'image/*': ['.jpg', '.jpeg', '.png', '.webp'] },
    multiple: false,
  });

  const handleSearch = async () => {
  if (!queryFile) return;

  setSearching(true);
  setError(null);

  try {
    const res = await searchByFile(queryFile, topK);

    // 🔥 Transform backend response → UI-friendly format
    const formatted = res.data.results.flatMap(img =>
      img.faces.map(face => ({
        face_id: face.id,
        image_filename: img.filename,
        image_url: img.processed_image_url,
        thumbnail_url: face.face_thumbnail_url,
        similarity: face.confidence ?? 0.9,
        bbox: {
          x: face.bbox_x,
          y: face.bbox_y,
          w: face.bbox_w,
          h: face.bbox_h
        },
        cluster: face.cluster_label
      }))
    );

    setResults(formatted);

  } catch (err) {
    setError(err.response?.data?.error || 'Search failed');
  } finally {
    setSearching(false);
  }
};
  const handleClear = () => {
    setQueryFile(null);
    setPreview(null);
    setResults(null);
    setError(null);
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      {/* Query section */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.25rem', alignItems: 'start' }}>
        {/* Drop zone */}
        <div>
          <div style={{ fontSize: '0.68rem', color: 'var(--text-muted)', letterSpacing: '0.1em', marginBottom: '0.5rem' }}>QUERY IMAGE</div>
          <div
            {...getRootProps()}
            style={{
              border: `2px dashed ${isDragActive ? 'var(--cyan)' : 'var(--bg-border)'}`,
              borderRadius: 'var(--radius-lg)',
              background: isDragActive ? 'var(--cyan-glow)' : 'var(--bg-surface)',
              padding: '1.5rem',
              textAlign: 'center', cursor: 'pointer',
              transition: 'var(--transition)',
              minHeight: 120, display: 'flex', alignItems: 'center', justifyContent: 'center',
            }}
          >
            <input {...getInputProps()} />
            {preview ? (
              <img src={preview} alt="query" style={{ maxHeight: 160, maxWidth: '100%', borderRadius: 'var(--radius-sm)', objectFit: 'contain' }} />
            ) : (
              <div>
                <div style={{ fontSize: '1.8rem', opacity: 0.4, marginBottom: '0.4rem' }}>⊙</div>
                <p style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', fontFamily: 'var(--font-display)', fontWeight: 600 }}>
                  Drop a query face image
                </p>
                <p style={{ fontSize: '0.65rem', color: 'var(--text-muted)', marginTop: '0.2rem' }}>or click to browse</p>
              </div>
            )}
          </div>
        </div>

        {/* Options */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem', paddingTop: '1.6rem' }}>
          <div>
            <label style={{ fontSize: '0.68rem', color: 'var(--text-muted)', letterSpacing: '0.1em', display: 'block', marginBottom: '0.4rem' }}>
              TOP-K RESULTS
            </label>
            <select
              value={topK}
              onChange={e => setTopK(Number(e.target.value))}
              style={{
                background: 'var(--bg-elevated)', border: '1px solid var(--bg-border)',
                borderRadius: 'var(--radius-sm)', color: 'var(--text-primary)',
                fontFamily: 'var(--font-mono)', fontSize: '0.78rem',
                padding: '0.45rem 0.75rem', width: '100%', outline: 'none',
              }}
            >
              {[5, 10, 20, 50].map(n => <option key={n} value={n}>{n} results</option>)}
            </select>
          </div>

          <Button variant="primary" size="lg" onClick={handleSearch} disabled={!queryFile || searching}>
            {searching ? <><Spinner size={16} color="#000" /> Searching…</> : '⊙ Search Similar Faces'}
          </Button>

          {queryFile && (
            <Button variant="subtle" onClick={handleClear}>Clear</Button>
          )}

          {error && (
            <div style={{
              padding: '0.75rem', borderRadius: 'var(--radius-sm)',
              background: 'rgba(255,68,68,0.08)', border: '1px solid rgba(255,68,68,0.3)',
              fontSize: '0.75rem', color: 'var(--red)',
            }}>
              ⚠ {error}
            </div>
          )}
        </div>
      </div>

      {/* Results */}
      {results !== null && (
        <div>
          <div style={{ fontSize: '0.68rem', color: 'var(--text-muted)', letterSpacing: '0.1em', marginBottom: '0.75rem' }}>
            RESULTS — {results.length} similar face{results.length !== 1 ? 's' : ''} found
          </div>

          {results.length === 0 ? (
            <EmptyState icon="⊙" title="No similar faces found" description="Try uploading more images or lowering the similarity threshold." />
          ) : (
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: '0.75rem' }}>
              {results.map((r, i) => (
                <ResultCard key={r.face_id} result={r} rank={i + 1} />
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
