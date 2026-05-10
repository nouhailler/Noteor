import { useState, useEffect, useRef } from 'react';
import { Search, Plus, SlidersHorizontal, Mic, Image, Video, Trash2, RotateCcw, Settings, HelpCircle, CalendarDays, X, CheckSquare } from 'lucide-react';
import { db, getNotes, restoreNote, permanentlyDeleteNote } from '../db';
import { useLiveQuery } from 'dexie-react-hooks';
import HelpModal from './HelpModal';
import BulkActionBar from './BulkActionBar';
import type { Note, FilterType, DateFilter } from '../types';

const HELP_SECTIONS = [
  {
    title: 'Navigation',
    items: [
      { label: 'Ouvrir une note', description: 'Appuyer sur une note dans la liste pour l\'ouvrir dans l\'éditeur.' },
      { label: 'Nouvelle note', description: 'Bouton + en haut à droite pour créer une note vide.' },
    ],
  },
  {
    title: 'Recherche',
    items: [
      { label: 'Recherche en temps réel', description: 'Saisir dans la barre de recherche pour filtrer par titre et contenu simultanément.' },
    ],
  },
  {
    title: 'Sélection multiple',
    items: [
      { label: 'Appui long (mobile)', description: 'Maintenir le doigt sur une note pendant 0,5 s pour entrer en mode sélection.' },
      { label: 'Clic long (desktop)', description: 'Maintenir le clic gauche pendant 0,5 s sur une note pour entrer en mode sélection.' },
      { label: 'Actions groupées', description: 'En mode sélection : déplacer, taguer, exporter ou supprimer les notes cochées.' },
    ],
  },
  {
    title: 'Barre d\'outils',
    items: [
      { label: 'Filtres (⊞)', description: 'Ouvrir le panneau de filtres : type de contenu, date, catégorie, dossier, tag.' },
      { label: 'Paramètres (⚙)', description: 'Configurer la clé OpenRouter pour l\'IA, exporter ou importer vos notes.' },
    ],
  },
  {
    title: 'Indicateurs',
    items: [
      { label: '🎤  Audio', description: 'La note contient au moins un enregistrement audio.' },
      { label: '🖼  Image', description: 'La note contient au moins une image.' },
      { label: 'Bande couleur', description: 'Indique la catégorie attribuée à la note.' },
    ],
  },
];

interface Props {
  selectedNoteId: number | null;
  onSelectNote: (note: Note) => void;
  onNewNote: () => void;
  onOpenSidebar: () => void;
  onOpenSettings: () => void;
  onOpenCalendar: () => void;
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
  onOpenSettings,
  onOpenCalendar,
  filters,
  onSearchChange,
}: Props) {
  const [showHelp, setShowHelp] = useState(false);
  const [selectionMode, setSelectionMode] = useState(false);
  const [selectedIds, setSelectedIds] = useState<Set<number>>(new Set());
  const longPressTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const longPressFired = useRef(false);

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

  function exitSelection() {
    setSelectionMode(false);
    setSelectedIds(new Set());
  }

  function toggleSelect(id: number) {
    setSelectedIds(prev => {
      const next = new Set(prev);
      next.has(id) ? next.delete(id) : next.add(id);
      return next;
    });
  }

  function selectAll() {
    setSelectedIds(new Set(notes.map(n => n.id!).filter(Boolean)));
  }

  function startLongPress(id: number) {
    longPressFired.current = false;
    longPressTimer.current = setTimeout(() => {
      longPressFired.current = true;
      setSelectionMode(true);
      setSelectedIds(new Set([id]));
    }, 500);
  }

  function cancelLongPress() {
    if (longPressTimer.current) {
      clearTimeout(longPressTimer.current);
      longPressTimer.current = null;
    }
  }

  function handleNoteClick(note: Note) {
    if (longPressFired.current) return;
    if (selectionMode) {
      toggleSelect(note.id!);
    } else {
      onSelectNote(note);
    }
  }

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
      {selectionMode ? (
        <div className="flex items-center gap-2 px-4 pt-4 pb-2 border-b border-gray-100">
          <button onClick={exitSelection} className="p-2 rounded-lg text-gray-400 active:bg-gray-100">
            <X size={20} />
          </button>
          <span className="flex-1 text-sm font-semibold text-gray-800">
            {selectedIds.size} sélectionnée{selectedIds.size > 1 ? 's' : ''}
          </span>
          <button
            onClick={selectAll}
            className="flex items-center gap-1 px-3 py-1.5 rounded-lg text-xs font-medium text-indigo-600 active:bg-indigo-50"
          >
            <CheckSquare size={15} />
            Tout
          </button>
        </div>
      ) : (
        <div className="flex items-center gap-2 px-4 pt-4 pb-2 border-b border-gray-100">
          <h1 className="text-lg font-bold text-indigo-600 flex-1">
            {filters.deleted ? 'Corbeille' : 'Noteor'}
          </h1>
          <button
            onClick={onOpenCalendar}
            className="p-2 rounded-lg text-gray-400 active:bg-gray-100"
            aria-label="Calendrier"
          >
            <CalendarDays size={19} />
          </button>
          <button
            onClick={() => setShowHelp(true)}
            className="p-2 rounded-lg text-gray-400 active:bg-gray-100"
            aria-label="Aide"
          >
            <HelpCircle size={19} />
          </button>
          <button
            onClick={onOpenSettings}
            className="p-2 rounded-lg text-gray-400 active:bg-gray-100"
            aria-label="Paramètres"
          >
            <Settings size={19} />
          </button>
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
      )}

      {/* Search */}
      {!selectionMode && (
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
      )}

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
              const isSelected = selectedIds.has(note.id!);
              return (
                <li
                  key={note.id}
                  onClick={() => handleNoteClick(note)}
                  onMouseDown={() => startLongPress(note.id!)}
                  onMouseUp={cancelLongPress}
                  onMouseLeave={cancelLongPress}
                  onTouchStart={() => startLongPress(note.id!)}
                  onTouchEnd={cancelLongPress}
                  onTouchMove={cancelLongPress}
                  className={`flex items-stretch cursor-pointer active:bg-gray-50 transition-colors ${
                    isSelected ? 'bg-indigo-50' : selectedNoteId === note.id && !selectionMode ? 'bg-indigo-50' : ''
                  }`}
                >
                  {/* Selection checkbox */}
                  {selectionMode && (
                    <div className="flex items-center pl-3 pr-1">
                      <div className={`w-5 h-5 rounded-full border-2 flex items-center justify-center shrink-0 transition-colors
                        ${isSelected ? 'border-indigo-600 bg-indigo-600' : 'border-gray-300'}`}>
                        {isSelected && <div className="w-2 h-2 bg-white rounded-full" />}
                      </div>
                    </div>
                  )}
                  {catColor && (
                    <div className="w-1 shrink-0 rounded-l" style={{ backgroundColor: catColor }} />
                  )}
                  <div className="flex-1 px-4 py-3 min-w-0">
                    <div className="flex items-start justify-between gap-2">
                      <span className={`text-sm font-medium truncate ${
                        isSelected || (selectedNoteId === note.id && !selectionMode) ? 'text-indigo-700' : 'text-gray-900'
                      }`}>
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
                  {filters.deleted && !selectionMode && (
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

      {/* Bulk action bar */}
      {selectionMode && selectedIds.size > 0 && (
        <BulkActionBar selectedIds={[...selectedIds]} onDone={exitSelection} />
      )}

      {showHelp && (
        <HelpModal
          title="Aide — Liste des notes"
          sections={HELP_SECTIONS}
          onClose={() => setShowHelp(false)}
        />
      )}
    </div>
  );
}
