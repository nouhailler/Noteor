import { useEffect } from 'react';
import { X } from 'lucide-react';

export interface HelpItem {
  label: string;
  description: string;
}

export interface HelpSection {
  title: string;
  items: HelpItem[];
}

interface Props {
  title: string;
  sections: HelpSection[];
  onClose: () => void;
}

export default function HelpModal({ title, sections, onClose }: Props) {
  // Fermer avec Escape
  useEffect(() => {
    const handler = (e: KeyboardEvent) => { if (e.key === 'Escape') onClose(); };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, [onClose]);

  return (
    <div className="fixed inset-0 z-50 flex items-end md:items-center justify-center">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/40 backdrop-blur-sm"
        onClick={onClose}
      />

      {/* Panel — bottom sheet on mobile, centered dialog on desktop */}
      <div className="relative w-full md:w-[480px] md:max-w-full bg-white rounded-t-2xl md:rounded-2xl shadow-2xl max-h-[80dvh] flex flex-col">
        {/* Handle (mobile) */}
        <div className="flex justify-center pt-3 pb-1 md:hidden">
          <div className="w-10 h-1 rounded-full bg-gray-200" />
        </div>

        {/* Header */}
        <div className="flex items-center gap-3 px-5 py-3 border-b border-gray-100">
          <span className="flex-1 text-base font-semibold text-gray-800">{title}</span>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-gray-400 active:bg-gray-100"
            aria-label="Fermer l'aide"
          >
            <X size={18} />
          </button>
        </div>

        {/* Content */}
        <div className="overflow-y-auto px-5 py-4 space-y-5">
          {sections.map((section, i) => (
            <section key={i}>
              <h3 className="text-xs font-bold text-indigo-600 uppercase tracking-wider mb-2.5">
                {section.title}
              </h3>
              <ul className="space-y-3">
                {section.items.map((item, j) => (
                  <li key={j} className="flex gap-3">
                    <div className="min-w-0">
                      <span className="block text-sm font-medium text-gray-800">{item.label}</span>
                      <span className="block text-xs text-gray-500 leading-relaxed mt-0.5">{item.description}</span>
                    </div>
                  </li>
                ))}
              </ul>
            </section>
          ))}

          {/* Footer */}
          <p className="text-xs text-gray-300 text-center pt-2">
            Appuyez en dehors ou sur Échap pour fermer
          </p>
        </div>
      </div>
    </div>
  );
}
