import React, { useState, useEffect } from 'react';
import ClustersGrid from '../components/ClustersGrid';
import { SectionHeader, Button, Spinner } from '../components/UI';
import { fetchClusters, triggerRecluster } from '../utils/api';

export default function ClustersPage() {
  const [clusters, setClusters]       = useState([]);
  const [loading, setLoading]         = useState(true);
  const [reclustering, setReclustering] = useState(false);
  const [message, setMessage]         = useState(null);

  const load = async () => {
    setLoading(true);
    try {
      const res = await fetchClusters();
      setClusters(res.data);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  const handleRecluster = async () => {
    setReclustering(true);
    setMessage(null);
    try {
      const res = await triggerRecluster();
      setMessage(res.data.message);
      await load();
    } catch (e) {
      setMessage('Recluster failed: ' + (e.response?.data?.error || e.message));
    } finally {
      setReclustering(false);
    }
  };

  const handleLabelled = (clusterId, newLabel) => {
    setClusters(prev => prev.map(c =>
      c.id === clusterId ? { ...c, person_label: newLabel } : c
    ));
  };

  return (
    <div className="fade-in">
      <SectionHeader
        title="Face Clusters"
        subtitle="Faces grouped by identity using DBSCAN on 512-dim ArcFace embeddings"
        actions={
          <Button variant="ghost" onClick={handleRecluster} disabled={reclustering}>
            {reclustering ? <><Spinner size={14} /> Clustering…</> : '◈ Re-cluster All'}
          </Button>
        }
      />

      {message && (
        <div style={{
          padding: '0.7rem 1rem', marginBottom: '1rem',
          borderRadius: 'var(--radius-sm)',
          background: 'rgba(0,229,255,0.07)', border: '1px solid rgba(0,229,255,0.25)',
          fontSize: '0.75rem', color: 'var(--cyan)',
        }}>
          {message}
        </div>
      )}

      <ClustersGrid
        clusters={clusters}
        loading={loading}
        reclustering={reclustering}
        onLabelled={handleLabelled}
      />
    </div>
  );
}
