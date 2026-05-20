import React from 'react';
import SearchPanel from '../components/SearchPanel';
import { SectionHeader, Card } from '../components/UI';

export default function SearchPage() {
  return (
    <div className="fade-in">
      <SectionHeader
        title="Face Search"
        subtitle="Upload a query image to find similar faces using cosine similarity on ArcFace embeddings"
      />
      <Card>
        <SearchPanel />
      </Card>
    </div>
  );
}
