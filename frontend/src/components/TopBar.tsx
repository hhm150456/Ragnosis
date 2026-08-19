import { ShieldCheck } from 'lucide-react';
import { MobileMenuButton } from './Sidebar';

interface TopBarProps {
  title: string;
  onOpenMobileMenu: () => void;
}

export function TopBar({ title, onOpenMobileMenu }: TopBarProps) {
  return (
    <header className="sticky top-0 z-20 flex items-center justify-between border-b border-slate-700/50 bg-slate-900/80 px-4 py-3 backdrop-blur-md lg:px-8">
      <div className="flex items-center gap-3">
        <MobileMenuButton onClick={onOpenMobileMenu} />
        <h1 className="text-sm font-semibold text-white lg:text-base">{title}</h1>
      </div>
      <div className="flex items-center gap-2 rounded-full border border-emerald-500/20 bg-emerald-500/5 px-3 py-1.5">
        <ShieldCheck className="h-3.5 w-3.5 text-emerald-400" />
        <span className="text-xs font-medium text-emerald-300">
          Evidence Safety: <span className="font-semibold">ACTIVE</span>
        </span>
      </div>
    </header>
  );
}
