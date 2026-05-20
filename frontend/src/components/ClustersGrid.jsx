import React, { useState } from 'react';
import { Badge, Button, Spinner, EmptyState, Thumb, Card } from './UI';
import { labelCluster } from '../utils/api';

function ClusterCard({ cluster, onLabelled }) {
  const [editing, setEditing] = useState(false);
  const [label, setLabel] = useState(cluster.person_label || '');
  const [saving, setSaving] = useState(false);

  const handleSave = async () => {
    setSaving(true);
    try {
      const res = await labelCluster(cluster.id, label);
      onLabelled(cluster.id, res.data.person_label);
      setEditing(false);
    } finally {
      setSaving(false);
    }
  };

  const isNoise = cluster.label === -1;
  const displayName = cluster.person_label || (isNoise ? 'Unclassified' : `Person ${cluster.label}`);

  return (
    <Card style={{ display: 'flex', flexDirection: 'column', gap: '0.9rem' }}>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', justifyContent: 'space-between' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          {cluster.representative_thumbnail ? (
            <Thumb src={cluster.representative_thumbnail} size={36}
              style={{ borderRadius: '50%', border: '2px solid var(--cyan)' }} />
          ) : (
            <div style={{
              width: 36, height: 36, borderRadius: '50%',
              background: 'var(--bg-elevated)', border: '2px solid var(--bg-border)',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              fontSize: '1rem',
            }}>👤</div>
          )}
          <div>
            <div style={{ fontFamily: 'var(--font-display)', fontWeight: 700, fontSize: '0.9rem' }}>
              {displayName}
            </div>
            <div style={{ fontSize: '0.65rem', color: 'var(--text-muted)' }}>
              {cluster.face_count} face{cluster.face_count !== 1 ? 's' : ''}
            </div>
          </div>
        </div>
        <Badge color={isNoise ? 'amber' : 'cyan'}>
          {isNoise ? 'NOISE' : `CLUSTER ${cluster.label}`}
        </Badge>
      </div>

      {/* Face thumbnails grid */}
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.35rem' }}>
        {cluster.faces.slice(0, 12).map(f => (
          <div key={f.face_id} title={f.image_filename} style={{ position: 'relative' }}>
            <Thumb src={f.thumbnail_url || f.image_url} size={44} />
          </div>
        ))}
        {cluster.face_count > 12 && (
          <div style={{
            width: 44, height: 44, borderRadius: 'var(--radius-sm)',
            background: 'var(--bg-elevated)', border: '1px solid var(--bg-border)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            fontSize: '0.65rem', color: 'var(--text-muted)',
          }}>
            +{cluster.face_count - 12}
          </div>
        )}
      </div>

      {/* Images list */}
      <div style={{ fontSize: '0.67rem', color: 'var(--text-muted)', lineHeight: 1.7 }}>
        {[...new Set(cluster.faces.map(f => f.image_filename))].slice(0, 4).join(', ')}
        {cluster.faces.length > 4 && ' …'}
      </div>

      {/* Label editor */}
      {!isNoise && (
        editing ? (
          <div style={{ display: 'flex', gap: '0.4rem', alignItems: 'center' }}>
            <input
              value={label}
              onChange={e => setLabel(e.target.value)}
              placeholder="Enter person name…"
              style={{
                flex: 1, background: 'var(--bg-elevated)',
                border: '1px solid var(--cyan)',
                borderRadius: 'var(--radius-sm)',
                padding: '0.35rem 0.6rem',
                color: 'var(--text-primary)',
                fontFamily: 'var(--font-mono)', fontSize: '0.75rem',
                outline: 'none',
              }}
              onKeyDown={e => e.key === 'Enter' && handleSave()}
              autoFocus
            />
            <Button size="sm" variant="primary" onClick={handleSave} disabled={saving || !label.trim()}>
              {saving ? <Spinner size={12} color="#000" /> : '✓'}
            </Button>
            <Button size="sm" variant="subtle" onClick={() => setEditing(false)}>✕</Button>
          </div>
        ) : (
          <Button size="sm" variant="ghost" onClick={() => setEditing(true)}>
            ✎ {cluster.person_label ? 'Edit name' : 'Add name'}
          </Button>
        )
      )}
    </Card>
  );
}

export default function ClustersGrid({ clusters, loading, onRecluster, reclustering, onLabelled }) {
  if (loading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', padding: '3rem' }}>
        <Spinner size={32} />
      </div>
    );
  }

  if (!clusters || clusters.length === 0) {
    return (
      <EmptyState
        icon="◈"
        title="No clusters yet"
        description="Upload and process images first. Then click 'Re-cluster' to group faces by identity."
      />
    );
  }

  const real   = clusters.filter(c => c.label !== -1);
  const noise  = clusters.filter(c => c.label === -1);

  return (
    <div>
      {real.length > 0 && (
        <>
          <div style={{ fontSize: '0.68rem', color: 'var(--text-muted)', letterSpacing: '0.1em', marginBottom: '0.75rem' }}>
            IDENTIFIED PERSONS — {real.length} cluster{real.length !== 1 ? 's' : ''}
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(260px, 1fr))', gap: '1rem', marginBottom: '1.5rem' }}>
            {real.map(c => <ClusterCard key={c.id} cluster={c} onLabelled={onLabelled} />)}
          </div>
        </>
      )}

      {noise.length > 0 && (
        <>
          <div style={{ fontSize: '0.68rem', color: 'var(--text-muted)', letterSpacing: '0.1em', marginBottom: '0.75rem' }}>
            UNCLASSIFIED NOISE — {noise[0].face_count} face{noise[0].face_count !== 1 ? 's' : ''}
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(260px, 1fr))', gap: '1rem' }}>
            {noise.map(c => <ClusterCard key={c.id} cluster={c} onLabelled={onLabelled} />)}
          </div>
        </>
      )}
    </div>
  );
}
