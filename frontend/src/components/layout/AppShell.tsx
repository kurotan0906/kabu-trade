import { Outlet } from 'react-router-dom';
import { Header } from './Header';

export const AppShell = () => (
  <div className="min-h-screen bg-slate-50 text-slate-900 font-sans">
    <Header />
    <main className="mx-auto max-w-6xl px-4 md:px-6 py-6">
      <Outlet />
    </main>
  </div>
);
