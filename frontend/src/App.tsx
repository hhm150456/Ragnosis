import { useState } from 'react';
import { Sidebar, type PageId } from '@/components/Sidebar';
import { TopBar } from '@/components/TopBar';
import { Dashboard } from '@/pages/Dashboard';
import { EvidenceChecker } from '@/pages/EvidenceChecker';
import { Sources } from '@/pages/Sources';
import { Evaluation } from '@/pages/Evaluation';
import { About } from '@/pages/About';

const PAGE_TITLES: Record<PageId, string> = {
  dashboard: 'Dashboard',
  evidence: 'Evidence Checker',
  sources: 'Sources',
  evaluation: 'Evaluation',
  about: 'About',
};

function App() {
  const [page, setPage] = useState<PageId>('dashboard');
  const [mobileOpen, setMobileOpen] = useState(false);
  const [pendingQuery, setPendingQuery] = useState<string | undefined>();

  const navigate = (next: PageId) => {
    setPage(next);
    setMobileOpen(false);
    if (next !== 'evidence') setPendingQuery(undefined);
  };

  const handleHeroSubmit = (query: string) => {
    setPendingQuery(query);
    setPage('evidence');
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100">
      <Sidebar
        activePage={page}
        onNavigate={navigate}
        mobileOpen={mobileOpen}
        onCloseMobile={() => setMobileOpen(false)}
      />

      <div className="lg:pl-72">
        <TopBar title={PAGE_TITLES[page]} onOpenMobileMenu={() => setMobileOpen(true)} />

        <main className="mx-auto max-w-5xl px-4 py-6 lg:px-8 lg:py-10">
          {page === 'dashboard' && <Dashboard onNavigate={handleHeroSubmit} />}
          {page === 'evidence' && (
            <EvidenceChecker
              initialQuery={pendingQuery}
              onClearInitial={() => setPendingQuery(undefined)}
            />
          )}
          {page === 'sources' && <Sources />}
          {page === 'evaluation' && <Evaluation />}
          {page === 'about' && <About />}
        </main>
      </div>
    </div>
  );
}

export default App;
