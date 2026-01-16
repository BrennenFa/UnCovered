'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useSidebar } from '@/contexts/SidebarContext';

export default function Sidebar() {
  const pathname = usePathname();
  const { isCollapsed, toggleSidebar } = useSidebar();

  return (
    <>
      <aside
        className={`fixed left-0 top-0 h-screen bg-white dark:bg-black border-r border-gray-200 dark:border-zinc-800 transition-all duration-300 z-10 ${
          isCollapsed ? 'w-0' : 'w-64'
        }`}
      >
        <nav className={`flex flex-col gap-2 p-4 ${isCollapsed ? 'hidden' : 'block'}`}>
          <Link
            href="/"
            className={`px-4 py-3 text-sm font-medium rounded-lg transition-colors ${
              pathname === '/'
                ? 'text-blue-600 dark:text-blue-400'
                : 'text-gray-600 dark:text-gray-400'
            } hover:bg-gray-100 dark:hover:bg-zinc-900`}
          >
            Chat
          </Link>
          <Link
            href="/sources"
            className={`px-4 py-3 text-sm font-medium rounded-lg transition-colors ${
              pathname === '/sources'
                ? 'text-blue-600 dark:text-blue-400'
                : 'text-gray-600 dark:text-gray-400'
            } hover:bg-gray-100 dark:hover:bg-zinc-900`}
          >
            Sources
          </Link>
        </nav>
      </aside>

      <button
        onClick={toggleSidebar}
        className={`fixed top-6 bg-white dark:bg-black border border-gray-200 dark:border-zinc-800 p-2 rounded-r-lg hover:bg-gray-100 dark:hover:bg-zinc-900 transition-all duration-300 z-50 ${
          isCollapsed ? 'left-0' : 'left-64'
        }`}
        aria-label={isCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
      >
        <svg
          className={`w-4 h-4 text-gray-600 dark:text-gray-400 transition-transform duration-300 ${
            isCollapsed ? 'rotate-0' : 'rotate-180'
          }`}
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
        </svg>
      </button>
    </>
  );
}
