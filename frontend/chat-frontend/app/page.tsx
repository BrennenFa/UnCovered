'use client';

import ChatInterface from '@/components/ChatInterface';
import Header from '@/components/Header';
import Sidebar from '@/components/Sidebar';
import { useSidebar } from '@/contexts/SidebarContext';

export default function Home() {
  const { isCollapsed } = useSidebar();

  return (
    <div className="flex min-h-screen flex-col bg-white dark:bg-black transition-colors">
      <Header />
      <Sidebar />
      <main className={`flex-1 flex flex-col max-w-6xl w-full mx-auto px-8 py-6 pt-[105px] transition-all duration-300 ${isCollapsed ? 'ml-0' : 'ml-64'}`}>
        <ChatInterface />
      </main>
    </div>
  );
}
