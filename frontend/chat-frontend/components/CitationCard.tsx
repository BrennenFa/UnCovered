import { Source } from '@/types/chat';

interface CitationCardProps {
  source: Source;
  index: number;
}

export default function CitationCard({ source, index }: CitationCardProps) {
  const hasValidUrl = source.url && source.url !== "N/A";

  return (
    <div className="bg-white dark:bg-zinc-900 border border-gray-200 dark:border-zinc-800 rounded-xl p-4 hover:shadow-md transition-all">
      <div className="flex items-start gap-3">
        <div className="flex-shrink-0 w-6 h-6 bg-gradient-to-r from-blue-500 to-blue-600 text-white rounded-full flex items-center justify-center text-xs font-medium">
          {index}
        </div>
        <div className="flex-1">
          <div className="flex gap-2 mb-2 items-center flex-wrap">
            {hasValidUrl ? (
              <a
                href={source.url}
                target="_blank"
                rel="noopener noreferrer"
                className="text-xs font-mono bg-gray-100 dark:bg-zinc-800 text-blue-600 dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-300 px-2 py-1 rounded-md transition-colors underline"
              >
                {source.document_id}
              </a>
            ) : (
              <span className="text-xs font-mono bg-gray-100 dark:bg-zinc-800 text-gray-700 dark:text-gray-300 px-2 py-1 rounded-md">
                {source.document_id}
              </span>
            )}
            <span className="text-xs text-gray-500 dark:text-gray-400 font-light">
              Page {source.page}
            </span>
          </div>
          <p className="text-sm text-gray-600 dark:text-gray-400 font-light leading-relaxed">
            {source.source}
          </p>
        </div>
      </div>
    </div>
  );
}
