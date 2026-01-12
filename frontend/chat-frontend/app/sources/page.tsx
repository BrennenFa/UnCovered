'use client';

import Header from '@/components/Header';

const sources = [
  {
    code: 'DOJ',
    name: 'DOJ Disclosures',
    fullName: 'DOJ Disclosures, Including Disclosures Under the Epstein Files Transparency Act (H.R. 4405)',
    description: 'Department of Justice documents released under the Epstein Files Transparency Act, providing comprehensive disclosure of government records related to the investigation.',
  },
  {
    code: 'HC',
    name: 'House Committee Depositions & Testimonies',
    fullName: 'House Committee on Oversight and Reform Depositions and Testimonies',
    description: 'Congressional oversight committee depositions and testimonies from investigations conducted by the House Committee on Oversight and Reform.',
  },
  {
    code: 'EE',
    name: 'Epstein Estate Documents',
    fullName: 'Oversight Committee Releases Additional Epstein Estate Documents',
    description: 'Additional documents from the Epstein estate released by oversight committees, including financial records, correspondence, and related materials.',
  },
];

export default function SourcesPage() {
  return (
    <div className="flex min-h-screen flex-col bg-white dark:bg-black transition-colors">
      <Header />
      <main className="flex-1 max-w-6xl w-full mx-auto px-8 py-12">
        <div className="mb-12">
          <h1 className="text-4xl font-medium text-gray-900 dark:text-gray-100 tracking-tight mb-4">
            Document Sources
          </h1>
          <p className="text-lg text-gray-600 dark:text-gray-400 font-light leading-relaxed">
            UnCovered aggregates documents from multiple official sources to provide comprehensive research access.
          </p>
        </div>

        <div className="space-y-6">
          {sources.map((source) => (
            <div
              key={source.code}
              className="bg-white dark:bg-zinc-900 border border-gray-200 dark:border-zinc-800 rounded-2xl p-8 hover:shadow-lg transition-all"
            >
              <div className="flex items-start gap-4">
                <div className="flex-shrink-0 w-12 h-12 bg-gradient-to-r from-blue-500 to-blue-600 text-white rounded-xl flex items-center justify-center font-mono font-semibold text-sm">
                  {source.code}
                </div>
                <div className="flex-1">
                  <h2 className="text-2xl font-medium text-gray-900 dark:text-gray-100 mb-2">
                    {source.name}
                  </h2>
                  <p className="text-sm text-gray-500 dark:text-gray-400 font-light mb-4">
                    {source.fullName}
                  </p>
                  <p className="text-base text-gray-700 dark:text-gray-300 font-light leading-relaxed">
                    {source.description}
                  </p>
                </div>
              </div>
            </div>
          ))}
        </div>

        <div className="mt-12 p-6 bg-gray-50 dark:bg-zinc-900 border border-gray-200 dark:border-zinc-800 rounded-2xl">
          <h3 className="text-lg font-medium text-gray-900 dark:text-gray-100 mb-3">
            About These Documents
          </h3>
          <p className="text-sm text-gray-600 dark:text-gray-400 font-light leading-relaxed">
            All documents in UnCovered are from publicly available official sources. The system uses AI-powered
            search to help researchers quickly find relevant information across thousands of pages of legal documents,
            depositions, and official disclosures.
          </p>
        </div>
      </main>
    </div>
  );
}
