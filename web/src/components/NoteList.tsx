import { useState, useEffect } from 'react';
import { Search, Plus, SlidersHorizontal, Mic, Image, Video, Trash2, RotateCcw } from 'lucide-react';
import { db, getNotes, restoreNote, permanentlyDeleteNote } from '../db';
import { useLiveQuery } from 'dexie-react-hooks';
import type { Note, FilterType, DateFilter } from '../types';

interface Props {
  selectedNoteId: number | null;
  onSelectNote: (note: Note) => void;
  onNewNote: () => void;
  onOpenSidebar: () => void;
  filters: {
    search: string;
    categoryId?: number;
    folderId?: number;
    tagId?: number;
    typeFilter: FilterType;
    dateFilter: DateFilter;
    deleted: boolean;
  };
  onSearchChange: (s: string) => void;
}

export default function NoteList({
  selectedNoteId,
  onSelectNote,
  onNewNote,
  onOpenSidebar,
  filters,
  onSearchChange,
}: Props) {
  const notes = useLiveQuery(
    () => getNotes({
      search: filters.search,
      categoryId: filters.categoryId,
      folderId: filters.folderId,
      tagId: filters.tagId,
      typeFilter: filters.typeFilter,
      dateFilter: filters.dateFilter,
      deleted: filters.deleted,
    }),
    [filters]
  ) ?? [];

  const [attachmentCounts, setAttachmentCounts] = useState<Record<number, { audio: number; image: number; video: number }>>({});
  const [categories, setCategories] = useState<Record<number, string>>({});

  useEffect(() => {
    db.categories.toArray().then(cats => {
      setCategories(Object.fromEntries(cats.map(c => [c.id!, c.color])));
    });
  }, []);

  useEffect(() => {
    if (!notes.length) return;
    const ids = notes.map(n => n.id!).filter(Boolean);
    db.attachments.where('note_id').anyOf(ids).toArray().then(attachments => {
      const counts: Record<number, { audio: number; image: number; video: number }> = {};
      for (const a of attachments) {
        if (!counts[a.note_id]) counts[a.note_id] = { audio: 0, image: 0, video: 0 };
        counts[a.note_id][a.type]++;
      }
      setAttachmentCounts(counts);
    });
  }, [notes]);

  function formatDate(dateStr: string) {
    const d = new Date(dateStr.replace(' ', 'T'));
    const today = new Date();
    if (d.toDateString() === today.toDateString()) {
      return d.toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' });
    }
    return d.toLocaleDateString('fr-FR', { day: '2-digit', month: 'short' });
  }

  async function handleRestore(e: React.MouseEvent, id: number) {
    e.stopPropagation();
    await restoreNote(id);
  }

  async function handlePermanentDelete(e: React.MouseEvent, id: number) {
    e.stopPropagation();
    if (confirm('Supprimer définitivement cette note ?')) await permanentlyDeleteNote(id);
  }

  return (
    <div className="flex flex-col h-full bg-white">
      {/* Header */}
      <div className="flex items-center gap-2 px-4 pt-4 pb-2 border-b border-gray-100">
        <h1 className="text-lg font-bold text-indigo-600 flex-1">
          {filters.deleted ? 'Corbeille' : 'Noteor'}
        </h1>
        <button
          onClick={onOpenSidebar}
          className="p-2 rounded-lg text-gray-500 active:bg-gray-100 relative"
          aria-label="Filtres"
        >
          <SlidersHorizontal size={20} />
          {(filters.categoryId || filters.folderId || filters.tagId || filters.typeFilter !== 'all' || filters.dateFilter !== 'all') && (
            <span className="absolute top-1.5 right-1.5 w-2 h-2 bg-indigo-500 rounded-full" />
          )}
        </button>
        {!filters.deleted && (
          <button
            onClick={onNewNote}
            className="p-2 rounded-lg bg-indigo-600 text-white active:bg-indigo-700"
            aria-label="Nouvelle note"
          >
            <Plus size={20} />
          </button>
        )}
      </div>

      {/* Search */}
      <div className="px-4 py-2">
        <div className="flex items-center gap-2 bg-gray-100 rounded-xl px-3 py-2">
          <Search size={16} className="text-gray-400 shrink-0" />
          <input
            type="text"
            placeholder="Rechercher..."
            value={filters.search}
            onChange={e => onSearchChange(e.target.value)}
            className="flex-1 bg-transparent text-sm outline-none placeholder-gray-400"
          />
        </div>
      </div>

      {/* Notes list */}
      <div className="flex-1 overflow-y-auto">
        {notes.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-gray-400 gap-2 px-8">
            <p className="text-sm text-center">
              {filters.deleted ? 'La corbeille est vide.' : 'Aucune note. Appuyez sur + pour créer.'}
            </p>
          </div>
        ) : (
          <ul className="divide-y divide-gray-50">
            {notes.map(note => {
              const counts = attachmentCounts[note.id!] ?? { audio: 0, image: 0, video: 0 };
              const catColor = note.category_id ? categories[note.category_id] : undefined;
              return (
                <li
                  key={note.id}
                  onClick={() => onSelectNote(note)}
                  className={`flex items-stretch cursor-pointer active:bg-gray-50 transition-colors ${
                    selectedNoteId === note.id ? 'bg-indigo-50' : ''
                  }`}
                >
                  {catColor && (
                    <div className="w-1 shrink-0 rounded-l" style={{ backgroundColor: catColor }} />
                  )}
                  <div className="flex-1 px-4 py-3 min-w-0">
                    <div className="flex items-start justify-between gap-2">
                      <span className={`text-sm font-medium truncate ${selectedNoteId === note.id ? 'text-indigo-700' : 'text-gray-900'}`}>
                        {note.title || 'Sans titre'}
                      </span>
                      <span className="text-xs text-gray-400 shrink-0">{formatDate(note.updated_at)}</span>
                    </div>
                    <div className="flex items-center gap-2 mt-0.5">
                      <p className="text-xs text-gray-400 truncate flex-1">
                        {note.content.slice(0, 80).replace(/[#*`]/g, '') || '...'}
                      </p>
                      <div className="flex items-center gap-1 shrink-0">
                        {counts.audio > 0 && <Mic size={12} className="text-indigo-400" />}
                        {counts.image > 0 && <Image size={12} className="text-green-400" />}
                        {counts.video > 0 && <Video size={12} className="text-orange-400" />}
                      </div>
                    </div>
                  </div>
                  {filters.deleted && (
                    <div className="flex items-center gap-1 pr-3">
                      <button onClick={e => handleRestore(e, note.id!)} className="p-2 text-green-500 active:opacity-70">
                        <RotateCcw size={16} />
                      </button>
                      <button onClick={e => handlePermanentDelete(e, note.id!)} className="p-2 text-red-500 active:opacity-70">
                        <Trash2 size={16} />
                      </button>
                    </div>
                  )}
                </li>
              );
            })}
          </ul>
        )}
      </div>
    </div>
  );
}
