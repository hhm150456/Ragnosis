import { ShieldCheck, Home, Search, BookOpen, BarChart3, Info, Menu, X } from 'lucide-react';

export type PageId = 'dashboard' | 'evidence' | 'sources' | 'evaluation' | 'about';

interface SidebarProps {
  activePage: PageId;
  onNavigate: (page: PageId) => void;
  mobileOpen: boolean;
  onCloseMobile: () => void;
}

const NAV_ITEMS: { id: PageId; label: string; icon: typeof Home; primary?: boolean }[] = [
  { id: 'dashboard', label: 'Dashboard', icon: Home },
  { id: 'evidence', label: 'Evidence Checker', icon: Search, primary: true },
  { id: 'sources', label: 'Sources', icon: BookOpen },
  { id: 'evaluation', label: 'Evaluation', icon: BarChart3 },
  { id: 'about', label: 'About', icon: Info },
];

export function Sidebar({ activePage, onNavigate, mobileOpen, onCloseMobile }: SidebarProps) {
  return (
    <>
      {/* Mobile overlay */}
      {mobileOpen && (
        <div
          className="fixed inset-0 z-30 bg-black/60 backdrop-blur-sm lg:hidden"
          onClick={onCloseMobile}
        />
      )}

      <aside
        className={`fixed inset-y-0 left-0 z-40 flex w-72 flex-col border-r border-slate-700/50 bg-slate-900/95 transition-transform duration-300 lg:translate-x-0 ${
          mobileOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        {/* Brand */}
        <div className="flex items-center justify-between gap-3 px-5 py-5">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-sky-500/10 border border-sky-500/20">
              <ShieldCheck className="h-5 w-5 text-sky-400" />
            </div>
            <div>
              <div className="text-sm font-semibold tracking-wide text-white">
                CLINGUARD
              </div>
              <div className="text-[10px] text-slate-400 leading-tight">
                Evidence-Grounded
                <br />
                Clinical Retrieval
              </div>
            </div>
          </div>
          <button
            onClick={onCloseMobile}
            className="lg:hidden text-slate-400 hover:text-white"
            aria-label="Close menu"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        <div className="mx-5 border-t border-slate-700/40" />

        {/* Nav */}
        <nav className="mt-4 flex-1 space-y-1 px-3">
          {NAV_ITEMS.map((item) => {
            const Icon = item.icon;
            const active = activePage === item.id;
            return (
              <button
                key={item.id}
                onClick={() => onNavigate(item.id)}
                className={`flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-sm transition-colors ${
                  active
                    ? 'bg-sky-500/10 text-sky-300 border border-sky-500/20'
                    : 'text-slate-300 hover:bg-slate-800/60 hover:text-white border border-transparent'
                }`}
              >
                <Icon className={`h-4 w-4 ${active ? 'text-sky-400' : 'text-slate-400'}`} />
                <span className="font-medium">{item.label}</span>
                {item.primary && !active && (
                  <span className="ml-auto rounded bg-sky-500/10 px-1.5 py-0.5 text-[9px] font-semibold uppercase text-sky-400">
                    Core
                  </span>
                )}
              </button>
            );
          })}
        </nav>

        {/* Safety mode */}
        <div className="m-3 rounded-lg border border-emerald-500/20 bg-emerald-500/5 px-4 py-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <ShieldCheck className="h-4 w-4 text-emerald-400" />
              <span className="text-xs font-medium text-slate-200">Clinical Safety Mode</span>
            </div>
            <span className="flex items-center gap-1.5 text-[10px] font-semibold text-emerald-400">
              <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-emerald-400" />
              ACTIVE
            </span>
          </div>
        </div>
      </aside>
    </>
  );
}

export function MobileMenuButton({ onClick }: { onClick: () => void }) {
  return (
    <button
      onClick={onClick}
      className="lg:hidden inline-flex items-center gap-2 rounded-lg border border-slate-700 bg-slate-800/60 px-3 py-2 text-sm text-slate-300 hover:text-white"
      aria-label="Open menu"
    >
      <Menu className="h-4 w-4" />
    </button>
  );
}
