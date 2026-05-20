import React, { useCallback, useState } from 'react';
import { useDropzone } from 'react-dropzone';
import { uploadImages } from '../utils/api';
import { Button, Spinner, Badge } from './UI';

const ACCEPT = { 'image/*': ['.jpg', '.jpeg', '.png', '.webp', '.bmp'] };
const MAX_SIZE = 50 * 1024 * 1024; // 50MB

function FileItem({ file, status, progress, error }) {
  const colors = { queued: 'muted', uploading: 'cyan', done: 'green', error: 'red' };
  return (
    <div style={{
      display: 'flex', alignItems: 'center', gap: '0.75rem',
      padding: '0.6rem 0.9rem',
      background: 'var(--bg-elevated)',
      border: '1px solid var(--bg-border)',
      borderRadius: 'var(--radius-sm)',
      fontSize: '0.75rem',
    }}>
      <span style={{ flex: 1, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', color: 'var(--text-secondary)' }}>
        {file.name}
      </span>
      <span style={{ color: 'var(--text-muted)', flexShrink: 0 }}>
        {(file.size / 1024).toFixed(0)} KB
      </span>
      {status === 'uploading' && progress != null && (
        <span style={{ color: 'var(--cyan)', flexShrink: 0 }}>{progress}%</span>
      )}
      <Badge color={colors[status] || 'muted'}>{status.toUpperCase()}</Badge>
      {error && <span style={{ color: 'var(--red)', fontSize: '0.65rem', maxWidth: 140, overflow: 'hidden', textOverflow: 'ellipsis' }}>{error}</span>}
    </div>
  );
}

export default function UploadZone({ onUploaded }) {
  const [files, setFiles] = useState([]);
  const [uploading, setUploading] = useState(false);

  const onDrop = useCallback((accepted, rejected) => {
    const newFiles = accepted.map(f => ({ file: f, status: 'queued', progress: null, error: null }));
    const errFiles = rejected.map(({ file, errors }) => ({
      file, status: 'error', progress: null,
      error: errors.map(e => e.message).join(', '),
    }));
    setFiles(prev => [...prev, ...newFiles, ...errFiles]);
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop, accept: ACCEPT, maxSize: MAX_SIZE, multiple: true,
  });

  const handleUpload = async () => {
    const queued = files.filter(f => f.status === 'queued');
    if (!queued.length) return;
    setUploading(true);

    // Mark all queued as uploading
    setFiles(prev => prev.map(f => f.status === 'queued' ? { ...f, status: 'uploading' } : f));

    try {
      const response = await uploadImages(
        queued.map(f => f.file),
        (pct) => {
          setFiles(prev => prev.map(f =>
            f.status === 'uploading' ? { ...f, progress: pct } : f
          ));
        }
      );
      setFiles(prev => prev.map(f =>
        f.status === 'uploading' ? { ...f, status: 'done', progress: 100 } : f
      ));
      if (onUploaded) onUploaded(response.data);
    } catch (err) {
      const msg = err.response?.data?.error || 'Upload failed';
      setFiles(prev => prev.map(f =>
        f.status === 'uploading' ? { ...f, status: 'error', error: msg } : f
      ));
    } finally {
      setUploading(false);
    }
  };

  const clearDone = () => setFiles(prev => prev.filter(f => f.status !== 'done'));
  const clearAll  = () => setFiles([]);
  const queued    = files.filter(f => f.status === 'queued').length;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
      {/* Drop zone */}
      <div
        {...getRootProps()}
        style={{
          border: `2px dashed ${isDragActive ? 'var(--cyan)' : 'var(--bg-border)'}`,
          borderRadius: 'var(--radius-lg)',
          background: isDragActive ? 'var(--cyan-glow)' : 'var(--bg-surface)',
          padding: '3rem 2rem',
          textAlign: 'center',
          cursor: 'pointer',
          transition: 'var(--transition)',
        }}
      >
        <input {...getInputProps()} />
        <div style={{ fontSize: '2.5rem', marginBottom: '0.75rem', opacity: isDragActive ? 1 : 0.4 }}>
          {isDragActive ? '⬇' : '↑'}
        </div>
        <p style={{ fontFamily: 'var(--font-display)', fontWeight: 700, fontSize: '1rem', color: isDragActive ? 'var(--cyan)' : 'var(--text-secondary)' }}>
          {isDragActive ? 'Release to add files' : 'Drop images here or click to browse'}
        </p>
        <p style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginTop: '0.4rem' }}>
          JPG · PNG · WEBP · BMP · up to 50 MB each · multiple files supported
        </p>
      </div>

      {/* File list */}
      {files.length > 0 && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.25rem' }}>
            <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)', letterSpacing: '0.06em' }}>
              {files.length} FILE{files.length !== 1 ? 'S' : ''}
            </span>
            <div style={{ display: 'flex', gap: '0.4rem' }}>
              <Button size="sm" variant="subtle" onClick={clearDone}>Clear done</Button>
              <Button size="sm" variant="subtle" onClick={clearAll}>Clear all</Button>
            </div>
          </div>
          <div style={{ maxHeight: 280, overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '0.35rem' }}>
            {files.map((f, i) => (
              <FileItem key={i} file={f.file} status={f.status} progress={f.progress} error={f.error} />
            ))}
          </div>
        </div>
      )}

      {/* Upload button */}
      {queued > 0 && (
        <Button variant="primary" size="lg" onClick={handleUpload} disabled={uploading}>
          {uploading
            ? <><Spinner size={16} color="#000" /> Uploading…</>
            : `Upload ${queued} image${queued !== 1 ? 's' : ''}`
          }
        </Button>
      )}
    </div>
  );
}
