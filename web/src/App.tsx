import { useState, useCallback } from 'react';
import NoteList from './components/NoteList';
import NoteEditor from './components/NoteEditor';
import Sidebar from './components/Sidebar';
import Settings from './components/Settings';
import CalendarView from './components/CalendarView';
import { db, now, findNoteByTitle } from './db';
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

type AppView = View | 'settings' | 'calendar';

function makeNewNote(): Note {
  const t = now();
  return { title: '', content: '', is_deleted: false, created_at: t, updated_at: t };
}

export default function App() {
  const [view, setView] = useState<AppView>('list');
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

  function handleTagClick(tag: { id?: number }) {
    mergeFilters({ tagId: tag.id, categoryId: undefined, folderId: undefined });
    setView('list');
    setCurrentNote(null);
  }

  async function handleWikilinkClick(title: string, id?: number) {
    let found: Note | undefined;
    if (id) {
      const byId = await db.notes.get(id);
      if (byId && !byId.is_deleted) found = byId;
    }
    if (!found) found = await findNoteByTitle(title);
    if (found) {
      setCurrentNote(found);
      setView('editor');
    }
  }

  const sidebar = (
    <div className="hidden md:flex md:flex-col md:w-72 lg:w-80 border-r border-gray-200 bg-white shrink-0">
      <Sidebar filters={filters} onFiltersChange={mergeFilters} onClose={() => {}} />
    </div>
  );

  // ── Paramètres ───────────────────────────────────────────────────────────
  if (view === 'settings') {
    return (
      <div className="flex h-screen-safe overflow-hidden">
        {sidebar}
        <div className="flex flex-col flex-1 min-w-0">
          <Settings onBack={() => setView('list')} />
        </div>
      </div>
    );
  }

  // ── Calendrier ───────────────────────────────────────────────────────────
  if (view === 'calendar') {
    return (
      <div className="flex h-screen-safe overflow-hidden">
        {sidebar}
        <div className="flex flex-col flex-1 min-w-0">
          <CalendarView
            onSelectNote={note => { setCurrentNote(note); setView('editor'); }}
            onBack={() => setView('list')}
          />
        </div>
      </div>
    );
  }

  // ── Vue principale (liste + éditeur) ────────────────────────────────────
  return (
    <div className="flex h-screen-safe overflow-hidden">
      {/* Desktop sidebar */}
      <div className="hidden md:flex md:flex-col md:w-72 lg:w-80 border-r border-gray-200 bg-white shrink-0">
        <Sidebar filters={filters} onFiltersChange={mergeFilters} onClose={() => {}} />
      </div>

      {/* Sidebar mobile overlay */}
      {view === 'sidebar' && (
        <div className="fixed inset-0 z-50 md:hidden">
          <div className="absolute inset-0 bg-black/30" onClick={() => setView('list')} />
          <div className="absolute inset-y-0 right-0 w-80 max-w-full bg-white shadow-xl">
            <Sidebar filters={filters} onFiltersChange={mergeFilters} onClose={() => setView('list')} />
          </div>
        </div>
      )}

      {/* Liste des notes */}
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
          onOpenSettings={() => setView('settings')}
          onOpenCalendar={() => setView('calendar')}
          filters={filters}
          onSearchChange={s => mergeFilters({ search: s })}
        />
      </div>

      {/* Éditeur */}
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
            onTagClick={handleTagClick}
            onWikilinkClick={handleWikilinkClick}
          />
        ) : (
          <div className="hidden md:flex flex-1 items-center justify-center text-gray-300">
            <div className="text-center">
              <img src="/icon.svg" alt="Noteor" className="w-20 h-20 mx-auto mb-4 opacity-30" />
              <p className="text-sm">Sélectionnez une note ou créez-en une</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
