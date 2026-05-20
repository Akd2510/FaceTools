import React from 'react';
import { useNavigate } from 'react-router-dom';
import UploadZone from '../components/UploadZone';
import { SectionHeader, Card } from '../components/UI';

export default function UploadPage() {
  const navigate = useNavigate();

  const handleUploaded = (newImages) => {
    setTimeout(() => navigate('/'), 1200);
  };

  return (
    <div className="fade-in">
      <SectionHeader
        title="Upload Images"
        subtitle="Drop one or many images — the pipeline runs automatically in the background"
      />

      <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '1.5rem', alignItems: 'start' }}>
        <Card>
          <UploadZone onUploaded={handleUploaded} />
        </Card>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          <Card>
            <div style={{ fontSize: '0.68rem', color: 'var(--text-muted)', letterSpacing: '0.1em', marginBottom: '0.9rem' }}>
              PIPELINE STAGES
            </div>
            {[
              { step: '01', title: 'BlazeFace Detection', desc: 'MediaPipe FaceMesh locates all faces and returns 468 landmarks per face.' },
              { step: '02', title: 'Face Alignment',     desc: 'Affine warp to 112×112 canonical pose using 5 landmark reference points.' },
              { step: '03', title: 'ArcFace Embedding',  desc: 'InsightFace generates a 512-dim L2-normalised identity vector.' },
              { step: '04', title: 'DBSCAN Clustering',  desc: 'Cosine-distance DBSCAN groups all faces by identity across all images.' },
            ].map(({ step, title, desc }) => (
              <div key={step} style={{ display: 'flex', gap: '0.9rem', marginBottom: '1rem', alignItems: 'flex-start' }}>
                <div style={{
                  width: 28, height: 28, borderRadius: '50%', flexShrink: 0,
                  background: 'var(--cyan-glow)', border: '1px solid var(--cyan)',
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  fontSize: '0.6rem', fontWeight: 700, color: 'var(--cyan)',
                }}>{step}</div>
                <div>
                  <div style={{ fontSize: '0.78rem', fontWeight: 700, color: 'var(--text-primary)' }}>{title}</div>
                  <div style={{ fontSize: '0.68rem', color: 'var(--text-muted)', marginTop: '0.15rem', lineHeight: 1.5 }}>{desc}</div>
                </div>
              </div>
            ))}
          </Card>

          <Card>
            <div style={{ fontSize: '0.68rem', color: 'var(--text-muted)', letterSpacing: '0.1em', marginBottom: '0.6rem' }}>TIPS</div>
            <ul style={{ listStyle: 'none', fontSize: '0.72rem', color: 'var(--text-secondary)', lineHeight: 2 }}>
              <li>• Images up to 50 MB are supported</li>
              <li>• Multiple faces per image are handled</li>
              <li>• Processing is async — check Dashboard</li>
              <li>• Re-run clustering after bulk upload</li>
            </ul>
          </Card>
        </div>
      </div>
    </div>
  );
}
