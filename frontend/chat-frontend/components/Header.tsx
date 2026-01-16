'use client';

import { useTheme } from '@/contexts/ThemeContext';
import { useSidebar } from '@/contexts/SidebarContext';
import Link from 'next/link';
import { usePathname } from 'next/navigation';

export default function Header() {
  const { theme, toggleTheme } = useTheme();
  const { isCollapsed } = useSidebar();
  const pathname = usePathname();

  const handleClick = () => {
    toggleTheme();
  };

  return (
    <header className={`fixed top-0 right-0 bg-white dark:bg-black border-b border-gray-200 dark:border-zinc-800 transition-all duration-300 z-20 ${
      isCollapsed ? 'left-0 w-full' : 'left-64 w-[calc(100%-16rem)]'
    }`}>
      <div className="px-8 py-5 flex items-center justify-between">
        <div>
          <Link href="/">
            <h1 className="text-3xl font-medium text-gray-900 dark:text-gray-100 tracking-tight cursor-pointer hover:text-gray-700 dark:hover:text-gray-300 transition-colors">
              UnCovered
            </h1>
          </Link>
          <p className="text-gray-500 dark:text-gray-400 text-sm mt-0.5 font-light">
            UnCovered Files Reader Powered by AI
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={handleClick}
            className="p-2.5 rounded-full bg-gray-100 dark:bg-zinc-900 hover:bg-gray-200 dark:hover:bg-zinc-800 transition-all border border-gray-200 dark:border-zinc-800"
            aria-label="Toggle theme"
          >
            {theme === 'dark' ? (
              <svg className="w-5 h-5 text-yellow-400" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M10 2a1 1 0 011 1v1a1 1 0 11-2 0V3a1 1 0 011-1zm4 8a4 4 0 11-8 0 4 4 0 018 0zm-.464 4.95l.707.707a1 1 0 001.414-1.414l-.707-.707a1 1 0 00-1.414 1.414zm2.12-10.607a1 1 0 010 1.414l-.706.707a1 1 0 11-1.414-1.414l.707-.707a1 1 0 011.414 0zM17 11a1 1 0 100-2h-1a1 1 0 100 2h1zm-7 4a1 1 0 011 1v1a1 1 0 11-2 0v-1a1 1 0 011-1zM5.05 6.464A1 1 0 106.465 5.05l-.708-.707a1 1 0 00-1.414 1.414l.707.707zm1.414 8.486l-.707.707a1 1 0 01-1.414-1.414l.707-.707a1 1 0 011.414 1.414zM4 11a1 1 0 100-2H3a1 1 0 000 2h1z" clipRule="evenodd" />
              </svg>
            ) : (
              <svg className="w-5 h-5 text-gray-600" fill="currentColor" viewBox="0 0 20 20">
                <path d="M17.293 13.293A8 8 0 016.707 2.707a8.001 8.001 0 1010.586 10.586z" />
              </svg>
            )}
          </button>
        </div>
      </div>
    </header>
  );
}
