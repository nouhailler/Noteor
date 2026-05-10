import { useState, useMemo, useEffect } from 'react';
import { ChevronLeft, ChevronRight, CalendarDays, HelpCircle, Calendar, CalendarRange } from 'lucide-react';
import { useLiveQuery } from 'dexie-react-hooks';
import { db } from '../db';
import HelpModal from './HelpModal';
import type { Note } from '../types';

const HELP_SECTIONS = [
  {
    title: 'Navigation',
    items: [
      { label: '‹ / ›', description: 'Passer au mois ou à la semaine précédent(e) / suivant(e).' },
      { label: 'Aujourd\'hui', description: 'Revenir à la période contenant la date du jour.' },
      { label: 'Mois / Semaine', description: 'Basculer entre la vue mensuelle et la vue hebdomadaire.' },
    ],
  },
  {
    title: 'Notes',
    items: [
      { label: 'Ouvrir une note', description: 'Cliquer sur une note dans le calendrier pour l\'ouvrir dans l\'éditeur.' },
      { label: 'Date affichée', description: 'Les notes apparaissent à leur date de dernière modification.' },
      { label: '+N autres', description: 'Si plus de 3 notes le même jour (vue mensuelle), les suivantes sont masquées.' },
    ],
  },
  {
    title: 'Re-datation',
    items: [
      { label: 'Glisser-déposer (desktop)', description: 'Faire glisser une note vers un autre jour pour changer sa date de modification.' },
      { label: 'Icône crayon (mobile)', description: 'Appuyer sur ✎ sur une note pour choisir une nouvelle date via le sélecteur.' },
    ],
  },
];

const DAY_LABELS = ['Lun', 'Mar', 'Mer', 'Jeu', 'Ven', 'Sam', 'Dim'];

function toStr(d: Date): string {
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
}

function todayStr(): string { return toStr(new Date()); }

interface Props {
  onSelectNote: (note: Note) => void;
  onBack: () => void;
}

export default function CalendarView({ onSelectNote, onBack }: Props) {
  const [mode, setMode] = useState<'month' | 'week'>('month');
  const [refDate, setRefDate] = useState(new Date());
  const [dragId, setDragId] = useState<number | null>(null);
  const [dropDate, setDropDate] = useState<string | null>(null);
  const [reschedule, setReschedule] = useState<{ note: Note; date: string } | null>(null);
  const [showHelp, setShowHelp] = useState(false);
  const [catColors, setCatColors] = useState<Record<number, string>>({});

  const notes = useLiveQuery(() => db.notes.filter(n => !n.is_deleted).toArray()) ?? [];

  useEffect(() => {
    db.categories.toArray().then(cats =>
      setCatColors(Object.fromEntries(cats.map(c => [c.id!, c.color])))
    );
  }, []);

  const byDate = useMemo(() => {
    const map: Record<string, Note[]> = {};
    for (const n of notes) {
      const d = n.updated_at.slice(0, 10);
      if (!map[d]) map[d] = [];
      map[d].push(n);
    }
    return map;
  }, [notes]);

  // ── Grilles ──────────────────────────────────────────────────────────────

  const monthGrid = useMemo(() => {
    const year = refDate.getFullYear();
    const month = refDate.getMonth();
    const firstDay = new Date(year, month, 1);
    // Décalage pour commencer lundi (0=lun … 6=dim)
    const offset = (firstDay.getDay() + 6) % 7;
    const start = new Date(firstDay);
    start.setDate(start.getDate() - offset);
    const days: Date[] = [];
    const cur = new Date(start);
    // 6 semaines max
    while (days.length < 42) {
      days.push(new Date(cur));
      cur.setDate(cur.getDate() + 1);
    }
    return days;
  }, [refDate]);

  const weekDays = useMemo(() => {
    const dow = (refDate.getDay() + 6) % 7;
    const monday = new Date(refDate);
    monday.setDate(monday.getDate() - dow);
    return Array.from({ length: 7 }, (_, i) => {
      const d = new Date(monday);
      d.setDate(d.getDate() + i);
      return d;
    });
  }, [refDate]);

  // ── Navigation ────────────────────────────────────────────────────────────

  function prev() {
    const d = new Date(refDate);
    if (mode === 'month') d.setMonth(d.getMonth() - 1);
    else d.setDate(d.getDate() - 7);
    setRefDate(d);
  }

  function next() {
    const d = new Date(refDate);
    if (mode === 'month') d.setMonth(d.getMonth() + 1);
    else d.setDate(d.getDate() + 7);
    setRefDate(d);
  }

  function gotoToday() { setRefDate(new Date()); }

  // ── Re-datation ───────────────────────────────────────────────────────────

  async function redate(noteId: number, newDate: string) {
    const note = await db.notes.get(noteId);
    if (!note) return;
    const time = note.updated_at.slice(11) || '12:00:00';
    await db.notes.update(noteId, { updated_at: `${newDate} ${time}` });
  }

  async function commitReschedule() {
    if (!reschedule) return;
    await redate(reschedule.note.id!, reschedule.date);
    setReschedule(null);
  }

  // ── Titre période ──────────────────────────────────────────────────────────

  const periodLabel = mode === 'month'
    ? refDate.toLocaleDateString('fr-FR', { month: 'long', year: 'numeric' })
    : `${weekDays[0].toLocaleDateString('fr-FR', { day: 'numeric', month: 'short' })} – ${weekDays[6].toLocaleDateString('fr-FR', { day: 'numeric', month: 'short', year: 'numeric' })}`;

  // ── Composant note-chip ───────────────────────────────────────────────────

  function NoteChip({ note, compact = false }: { note: Note; compact?: boolean }) {
    const color = note.category_id ? catColors[note.category_id] : '#6366F1';
    return (
      <div
        draggable
        onDragStart={e => { e.dataTransfer.setData('noteId', String(note.id)); setDragId(note.id!); }}
        onDragEnd={() => setDragId(null)}
        onClick={e => { e.stopPropagation(); onSelectNote(note); }}
        className={`flex items-center gap-1 rounded cursor-pointer select-none group
          ${dragId === note.id ? 'opacity-40' : ''}
          ${compact ? 'px-1 py-0.5' : 'px-1.5 py-1'}
        `}
        style={{ backgroundColor: `${color}22`, borderLeft: `3px solid ${color}` }}
        title={note.title || 'Sans titre'}
      >
        <span className={`flex-1 text-gray-800 font-medium truncate ${compact ? 'text-[10px]' : 'text-xs'}`}>
          {note.title || 'Sans titre'}
        </span>
        {/* Re-dater (mobile) */}
        <button
          onClick={e => {
            e.stopPropagation();
            setReschedule({ note, date: note.updated_at.slice(0, 10) });
          }}
          className="shrink-0 opacity-0 group-hover:opacity-100 text-gray-400 hover:text-indigo-500 transition-opacity"
          title="Changer la date"
          aria-label="Changer la date"
        >
          <CalendarDays size={compact ? 10 : 12} />
        </button>
      </div>
    );
  }

  // ── Cellule jour (partagée mois/semaine) ──────────────────────────────────

  function DayCell({ day, showMonth = false, compact = false }: { day: Date; showMonth?: boolean; compact?: boolean }) {
    const ds = toStr(day);
    const dayNotes = byDate[ds] ?? [];
    const isToday = ds === todayStr();
    const isCurrentMonth = day.getMonth() === refDate.getMonth();
    const isOver = dropDate === ds;

    return (
      <div
        key={ds}
        className={`flex flex-col border-gray-100 transition-colors
          ${compact ? 'min-h-[80px] p-1' : 'min-h-[120px] p-2'}
          ${!isCurrentMonth && showMonth ? 'bg-gray-50/60' : 'bg-white'}
          ${isOver ? 'bg-indigo-50 ring-2 ring-inset ring-indigo-300' : ''}
        `}
        onDragOver={e => { e.preventDefault(); setDropDate(ds); }}
        onDragLeave={e => { if (!e.currentTarget.contains(e.relatedTarget as Node)) setDropDate(null); }}
        onDrop={e => {
          e.preventDefault();
          const id = Number(e.dataTransfer.getData('noteId'));
          if (id) redate(id, ds);
          setDropDate(null);
          setDragId(null);
        }}
      >
        {/* Numéro du jour */}
        <div className="flex items-center mb-1">
          <span className={`text-xs font-semibold flex items-center justify-center w-5 h-5 rounded-full
            ${isToday ? 'bg-indigo-600 text-white' : (!isCurrentMonth && showMonth) ? 'text-gray-300' : 'text-gray-600'}
          `}>
            {day.getDate()}
          </span>
          {compact && dayNotes.length > 0 && (
            <span className="ml-1 text-[10px] text-gray-400">{dayNotes.length}</span>
          )}
        </div>

        {/* Notes */}
        <div className="flex flex-col gap-0.5 overflow-hidden flex-1">
          {dayNotes.slice(0, compact ? 2 : 3).map(n => (
            <NoteChip key={n.id} note={n} compact={compact} />
          ))}
          {dayNotes.length > (compact ? 2 : 3) && (
            <span className="text-[10px] text-gray-400 pl-1">
              +{dayNotes.length - (compact ? 2 : 3)} autres
            </span>
          )}
        </div>
      </div>
    );
  }

  // ── Render ────────────────────────────────────────────────────────────────

  return (
    <div className="flex flex-col h-full bg-white">
      {/* Header */}
      <div className="flex items-center gap-1.5 px-4 pt-4 pb-3 border-b border-gray-100">
        <button onClick={onBack} className="p-1.5 text-gray-400 active:text-gray-700 md:hidden">
          <ChevronLeft size={20} />
        </button>

        <button onClick={prev} className="p-1.5 rounded-lg text-gray-500 active:bg-gray-100" aria-label="Précédent">
          <ChevronLeft size={18} />
        </button>
        <button onClick={next} className="p-1.5 rounded-lg text-gray-500 active:bg-gray-100" aria-label="Suivant">
          <ChevronRight size={18} />
        </button>
        <button onClick={gotoToday} className="px-2 py-1 text-xs rounded-lg border border-gray-200 text-gray-600 active:bg-gray-50">
          Aujourd'hui
        </button>

        <span className="flex-1 text-center text-sm font-semibold text-gray-800 capitalize truncate">
          {periodLabel}
        </span>

        {/* Mode toggle */}
        <div className="flex rounded-lg border border-gray-200 overflow-hidden shrink-0">
          <button
            onClick={() => setMode('month')}
            className={`p-1.5 transition-colors ${mode === 'month' ? 'bg-indigo-600 text-white' : 'text-gray-500 active:bg-gray-50'}`}
            title="Vue mensuelle"
          >
            <Calendar size={16} />
          </button>
          <button
            onClick={() => setMode('week')}
            className={`p-1.5 transition-colors ${mode === 'week' ? 'bg-indigo-600 text-white' : 'text-gray-500 active:bg-gray-50'}`}
            title="Vue hebdomadaire"
          >
            <CalendarRange size={16} />
          </button>
        </div>

        <button onClick={() => setShowHelp(true)} className="p-1.5 text-gray-400 active:text-gray-600" aria-label="Aide">
          <HelpCircle size={19} />
        </button>
      </div>

      {/* Grille */}
      <div className="flex-1 overflow-auto">
        {mode === 'month' ? (
          <div className="flex flex-col h-full min-h-[500px]">
            {/* En-têtes jours */}
            <div className="grid grid-cols-7 border-b border-gray-100">
              {DAY_LABELS.map(l => (
                <div key={l} className="py-1.5 text-center text-xs font-semibold text-gray-400 uppercase tracking-wide">
                  {l}
                </div>
              ))}
            </div>
            {/* Cellules */}
            <div className="grid grid-cols-7 divide-x divide-y divide-gray-100 flex-1">
              {monthGrid.map(day => (
                <DayCell key={toStr(day)} day={day} showMonth compact />
              ))}
            </div>
          </div>
        ) : (
          <div className="flex flex-col h-full min-h-[500px]">
            {/* En-têtes jours (semaine) */}
            <div className="grid grid-cols-7 border-b border-gray-100">
              {weekDays.map(day => {
                const isToday = toStr(day) === todayStr();
                return (
                  <div key={toStr(day)} className="py-2 text-center">
                    <div className="text-xs text-gray-400 uppercase">
                      {day.toLocaleDateString('fr-FR', { weekday: 'short' })}
                    </div>
                    <div className={`mx-auto mt-0.5 w-7 h-7 flex items-center justify-center rounded-full text-sm font-semibold
                      ${isToday ? 'bg-indigo-600 text-white' : 'text-gray-800'}`}>
                      {day.getDate()}
                    </div>
                  </div>
                );
              })}
            </div>
            {/* Colonnes */}
            <div className="grid grid-cols-7 divide-x divide-gray-100 flex-1">
              {weekDays.map(day => (
                <DayCell key={toStr(day)} day={day} />
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Modale re-datation (mobile) */}
      {reschedule && (
        <div className="fixed inset-0 z-50 flex items-end md:items-center justify-center">
          <div className="absolute inset-0 bg-black/40" onClick={() => setReschedule(null)} />
          <div className="relative w-full md:w-80 bg-white rounded-t-2xl md:rounded-2xl shadow-2xl p-5">
            <div className="w-10 h-1 bg-gray-200 rounded-full mx-auto mb-4 md:hidden" />
            <h3 className="text-sm font-semibold text-gray-800 mb-1 truncate">
              {reschedule.note.title || 'Sans titre'}
            </h3>
            <p className="text-xs text-gray-500 mb-4">Choisir une nouvelle date</p>
            <input
              type="date"
              value={reschedule.date}
              onChange={e => setReschedule(r => r ? { ...r, date: e.target.value } : r)}
              className="w-full px-3 py-2.5 border border-gray-200 rounded-xl text-sm outline-none focus:border-indigo-400 mb-4"
            />
            <div className="flex gap-2">
              <button
                onClick={() => setReschedule(null)}
                className="flex-1 px-4 py-2 border border-gray-200 rounded-xl text-sm text-gray-600 active:bg-gray-50"
              >
                Annuler
              </button>
              <button
                onClick={commitReschedule}
                className="flex-1 px-4 py-2 bg-indigo-600 text-white rounded-xl text-sm active:bg-indigo-700"
              >
                Confirmer
              </button>
            </div>
          </div>
        </div>
      )}

      {showHelp && (
        <HelpModal
          title="Aide — Calendrier"
          sections={HELP_SECTIONS}
          onClose={() => setShowHelp(false)}
        />
      )}
    </div>
  );
}
