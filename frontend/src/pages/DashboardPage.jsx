import React, { useState, useEffect, useCallback } from 'react';
import StatsBar from '../components/StatsBar';
import ResultsTable from '../components/ResultsTable';
import { SectionHeader, Button, Spinner } from '../components/UI';
import { fetchImages } from '../utils/api';

export default function DashboardPage() {
  const [images, setImages]       = useState([]);
  const [loading, setLoading]     = useState(true);
  const [page, setPage]           = useState(1);
  const [hasMore, setHasMore]     = useState(false);
  const [autoRefresh, setAutoRefresh] = useState(true);

  const loadImages = useCallback(async (pg = 1, append = false) => {
    setLoading(true);
    try {
      const res = await fetchImages(pg);
      const data = res.data;
      setImages(prev => append ? [...prev, ...data.results] : data.results);
      setHasMore(!!data.next);
      setPage(pg);
    } catch (e) {
      console.error('Failed to load images', e);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { loadImages(1); }, [loadImages]);

  // Auto-refresh every 5s when any image is still processing
  useEffect(() => {
    if (!autoRefresh) return;
    const hasPending = images.some(i => i.status === 'pending' || i.status === 'processing');
    if (!hasPending) return;
    const id = setTimeout(() => loadImages(1), 5000);
    return () => clearTimeout(id);
  }, [images, autoRefresh, loadImages]);

  const handleDeleted = (id) => {
    setImages(prev => prev.filter(i => i.id !== id));
  };

  const handleLoadMore = () => loadImages(page + 1, true);

  return (
    <div className="fade-in">
      <SectionHeader
        title="Dashboard"
        subtitle="Uploaded images · face detections · clustering overview"
        actions={
          <>
            <Button
              size="sm"
              variant={autoRefresh ? 'ghost' : 'subtle'}
              onClick={() => setAutoRefresh(v => !v)}
            >
              {autoRefresh ? '⟳ Auto-refresh ON' : '⟳ Auto-refresh OFF'}
            </Button>
            <Button size="sm" variant="ghost" onClick={() => loadImages(1)} disabled={loading}>
              {loading ? <Spinner size={12} /> : '↺ Refresh'}
            </Button>
          </>
        }
      />

      <StatsBar />

      <ResultsTable
        images={images}
        loading={loading}
        onDeleted={handleDeleted}
        onLoadMore={handleLoadMore}
        hasMore={hasMore}
      />
    </div>
  );
}
