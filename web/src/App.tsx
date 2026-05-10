import { useState, useCallback } from 'react';
import NoteList from './components/NoteList';
import NoteEditor from './components/NoteEditor';
import Sidebar from './components/Sidebar';
import { now } from './db';
import type { Note, FilterType, DateFilter, View } from './types';

interface Filters {
  search: string;
  categoryId?: number;
  folderId?: number;
  tagId?: number;
  typeFilter: FilterType;
  dateFilter: DateFilter;
  deleted: boolean;
}

const DEFAULT_FILTERS: Filters = {
  search: '',
  typeFilter: 'all',
  dateFilter: 'all',
  deleted: false,
};

function makeNewNote(): Note {
  const t = now();
  return { title: '', content: '', is_deleted: false, created_at: t, updated_at: t };
}

export default function App() {
  const [view, setView] = useState<View>('list');
  const [currentNote, setCurrentNote] = useState<Note | null>(null);
  const [filters, setFilters] = useState<Filters>(DEFAULT_FILTERS);

  function mergeFilters(partial: Partial<Filters>) {
    setFilters(f => ({ ...f, ...partial }));
  }

  function openNote(note: Note) {
    setCurrentNote(note);
    setView('editor');
  }

  function openNewNote() {
    setCurrentNote(makeNewNote());
    setView('editor');
  }

  const handleSaved = useCallback((note: Note) => {
    setCurrentNote(note);
  }, []);

  function handleBack() {
    setView('list');
    setCurrentNote(null);
  }

  // Desktop: 3-column layout
  // Mobile: single panel with view state
  return (
    <div className="flex h-screen-safe overflow-hidden">
      {/* Desktop sidebar — always visible on md+ */}
      <div className={`
        hidden md:flex md:flex-col md:w-72 lg:w-80 border-r border-gray-200 bg-white shrink-0
      `}>
        <Sidebar
          filters={filters}
          onFiltersChange={mergeFilters}
          onClose={() => {}}
        />
      </div>

      {/* Mobile sidebar — overlay */}
      {view === 'sidebar' && (
        <div className="fixed inset-0 z-50 md:hidden">
          <div className="absolute inset-0 bg-black/30" onClick={() => setView('list')} />
          <div className="absolute inset-y-0 right-0 w-80 max-w-full bg-white shadow-xl">
            <Sidebar
              filters={filters}
              onFiltersChange={mergeFilters}
              onClose={() => setView('list')}
            />
          </div>
        </div>
      )}

      {/* Note list — visible on list view (mobile) or always (desktop) */}
      <div className={`
        flex-col w-full md:flex md:w-80 lg:w-96 border-r border-gray-200 shrink-0
        ${view === 'list' || view === 'sidebar' ? 'flex' : 'hidden'}
        md:flex
      `}>
        <NoteList
          selectedNoteId={currentNote?.id ?? null}
          onSelectNote={openNote}
          onNewNote={openNewNote}
          onOpenSidebar={() => setView('sidebar')}
          filters={filters}
          onSearchChange={s => mergeFilters({ search: s })}
        />
      </div>

      {/* Editor — full screen on mobile, right panel on desktop */}
      <div className={`
        flex-col flex-1 min-w-0
        ${view === 'editor' ? 'flex' : 'hidden'}
        md:flex
      `}>
        {currentNote ? (
          <NoteEditor
            key={currentNote.id ?? 'new'}
            note={currentNote}
            onBack={handleBack}
            onSaved={handleSaved}
          />
        ) : (
          <div className="hidden md:flex flex-1 items-center justify-center text-gray-300">
            <div className="text-center">
              <p className="text-5xl mb-3">📝</p>
              <p className="text-sm">Sélectionnez une note ou créez-en une</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
