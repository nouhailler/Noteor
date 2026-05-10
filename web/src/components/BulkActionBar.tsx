import { useState } from 'react';
import { Folder, Tag as TagIcon, Download, Trash2, X, Check, Plus } from 'lucide-react';
import { useLiveQuery } from 'dexie-react-hooks';
import {
  getCategories, getFolders, getAllTags,
  moveNotesBulk, tagNotesBulk, deleteNotesBulk, exportSelectedNotes,
} from '../db';

type Panel = null | 'move' | 'tag';

interface Props {
  selectedIds: number[];
  onDone: () => void;
}

export default function BulkActionBar({ selectedIds, onDone }: Props) {
  const [panel, setPanel] = useState<Panel>(null);
  const count = selectedIds.length;

  // ── Move panel ────────────────────────────────────────────────────────────
  if (panel === 'move') {
    return (
      <MovePanel
        selectedIds={selectedIds}
        onClose={() => setPanel(null)}
        onDone={onDone}
      />
    );
  }

  // ── Tag panel ─────────────────────────────────────────────────────────────
  if (panel === 'tag') {
    return (
      <TagPanel
        selectedIds={selectedIds}
        onClose={() => setPanel(null)}
        onDone={onDone}
      />
    );
  }

  // ── Barre principale ──────────────────────────────────────────────────────
  async function handleExport() {
    const data = await exportSelectedNotes(selectedIds);
    const json = JSON.stringify(data, null, 2);
    const blob = new Blob([json], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `noteor-selection-${new Date().toISOString().slice(0, 10)}.json`;
    a.click();
    URL.revokeObjectURL(url);
    onDone();
  }

  async function handleDelete() {
    if (!confirm(`Mettre ${count} note${count > 1 ? 's' : ''} à la corbeille ?`)) return;
    await deleteNotesBulk(selectedIds);
    onDone();
  }

  return (
    <div className="border-t border-gray-200 bg-white px-3 py-2 safe-bottom">
      <div className="flex items-center justify-around gap-1">
        <ActionBtn icon={<Folder size={18} />} label="Déplacer" onClick={() => setPanel('move')} />
        <ActionBtn icon={<TagIcon size={18} />} label="Taguer" onClick={() => setPanel('tag')} />
        <ActionBtn icon={<Download size={18} />} label="Exporter" onClick={handleExport} />
        <ActionBtn icon={<Trash2 size={18} />} label="Supprimer" onClick={handleDelete} danger />
      </div>
    </div>
  );
}

// ── Bouton action ─────────────────────────────────────────────────────────────

function ActionBtn({
  icon, label, onClick, danger = false,
}: { icon: React.ReactNode; label: string; onClick: () => void; danger?: boolean }) {
  return (
    <button
      onClick={onClick}
      className={`flex flex-col items-center gap-0.5 px-3 py-2 rounded-xl active:opacity-70 transition-opacity min-w-[64px]
        ${danger ? 'text-red-500' : 'text-indigo-600'}`}
    >
      {icon}
      <span className="text-[10px] font-medium">{label}</span>
    </button>
  );
}

// ── Panneau Déplacer ──────────────────────────────────────────────────────────

function MovePanel({
  selectedIds, onClose, onDone,
}: { selectedIds: number[]; onClose: () => void; onDone: () => void }) {
  const categories = useLiveQuery(getCategories) ?? [];
  const folders = useLiveQuery(getFolders) ?? [];

  const [folderId, setFolderId] = useState<number | null | undefined>(undefined);   // undefined = unchanged
  const [categoryId, setCategoryId] = useState<number | null | undefined>(undefined);

  async function apply() {
    const opts: { folderId?: number | null; categoryId?: number | null } = {};
    if (folderId !== undefined) opts.folderId = folderId;
    if (categoryId !== undefined) opts.categoryId = categoryId;
    if (Object.keys(opts).length === 0) { onClose(); return; }
    await moveNotesBulk(selectedIds, opts);
    onDone();
  }

  return (
    <Sheet title="Déplacer les notes" onClose={onClose} onApply={apply} applyLabel="Appliquer">
      {/* Dossiers */}
      <SectionTitle>Dossier</SectionTitle>
      <RadioRow
        label="Aucun dossier"
        selected={folderId === null}
        onSelect={() => setFolderId(null)}
      />
      {folders.map(f => (
        <RadioRow
          key={f.id}
          label={f.name}
          selected={folderId === f.id}
          onSelect={() => setFolderId(f.id!)}
          icon={<Folder size={14} className="text-gray-400" />}
        />
      ))}
      {folders.length === 0 && (
        <p className="text-xs text-gray-400 pl-1 pb-2">Aucun dossier créé</p>
      )}

      {/* Catégories */}
      <SectionTitle className="mt-4">Catégorie</SectionTitle>
      <RadioRow
        label="Aucune catégorie"
        selected={categoryId === null}
        onSelect={() => setCategoryId(null)}
      />
      {categories.map(c => (
        <RadioRow
          key={c.id}
          label={c.name}
          selected={categoryId === c.id}
          onSelect={() => setCategoryId(c.id!)}
          icon={<span className="w-3 h-3 rounded-full shrink-0" style={{ backgroundColor: c.color }} />}
        />
      ))}
      {categories.length === 0 && (
        <p className="text-xs text-gray-400 pl-1 pb-2">Aucune catégorie créée</p>
      )}
    </Sheet>
  );
}

// ── Panneau Taguer ────────────────────────────────────────────────────────────

function TagPanel({
  selectedIds, onClose, onDone,
}: { selectedIds: number[]; onClose: () => void; onDone: () => void }) {
  const allTags = useLiveQuery(getAllTags) ?? [];
  const [pickedTags, setPickedTags] = useState<Set<string>>(new Set());
  const [newTag, setNewTag] = useState('');

  function toggleTag(name: string) {
    setPickedTags(prev => {
      const next = new Set(prev);
      next.has(name) ? next.delete(name) : next.add(name);
      return next;
    });
  }

  async function apply() {
    const toAdd = new Set(pickedTags);
    if (newTag.trim()) toAdd.add(newTag.trim());
    for (const name of toAdd) await tagNotesBulk(selectedIds, name);
    onDone();
  }

  return (
    <Sheet title="Ajouter un tag" onClose={onClose} onApply={apply} applyLabel="Appliquer">
      {/* Tags existants */}
      {allTags.length > 0 && (
        <div className="flex flex-wrap gap-2 mb-4">
          {allTags.map(tag => {
            const picked = pickedTags.has(tag.name);
            return (
              <button
                key={tag.id}
                onClick={() => toggleTag(tag.name)}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium text-white transition-all
                  ${picked ? 'ring-2 ring-offset-2 ring-current scale-105' : 'opacity-70'}`}
                style={{ backgroundColor: tag.color }}
              >
                {picked && <Check size={11} strokeWidth={3} />}
                {tag.name}
              </button>
            );
          })}
        </div>
      )}

      {/* Nouveau tag */}
      <div className="flex items-center gap-2">
        <Plus size={16} className="text-gray-400 shrink-0" />
        <input
          type="text"
          placeholder="Nouveau tag..."
          value={newTag}
          onChange={e => setNewTag(e.target.value)}
          onKeyDown={e => { if (e.key === 'Enter') apply(); }}
          className="flex-1 text-sm border border-gray-200 rounded-xl px-3 py-2 outline-none focus:border-indigo-400"
        />
      </div>
      {allTags.length === 0 && !newTag && (
        <p className="text-xs text-gray-400 mt-2">Aucun tag existant. Saisis un nom ci-dessus.</p>
      )}
    </Sheet>
  );
}

// ── Helpers UI ────────────────────────────────────────────────────────────────

function Sheet({
  title, children, onClose, onApply, applyLabel,
}: {
  title: string;
  children: React.ReactNode;
  onClose: () => void;
  onApply: () => void;
  applyLabel: string;
}) {
  return (
    <div className="border-t border-gray-200 bg-white safe-bottom">
      {/* Handle + header */}
      <div className="flex items-center gap-2 px-4 py-3 border-b border-gray-100">
        <button onClick={onClose} className="p-1 text-gray-400 active:text-gray-700">
          <X size={18} />
        </button>
        <span className="flex-1 text-sm font-semibold text-gray-800">{title}</span>
        <button
          onClick={onApply}
          className="px-3 py-1.5 bg-indigo-600 text-white text-xs font-medium rounded-lg active:bg-indigo-700"
        >
          {applyLabel}
        </button>
      </div>
      {/* Content */}
      <div className="px-4 py-3 max-h-60 overflow-y-auto">
        {children}
      </div>
    </div>
  );
}

function SectionTitle({ children, className = '' }: { children: React.ReactNode; className?: string }) {
  return (
    <p className={`text-[10px] font-bold text-indigo-500 uppercase tracking-wider mb-1.5 ${className}`}>
      {children}
    </p>
  );
}

function RadioRow({
  label, selected, onSelect, icon,
}: { label: string; selected: boolean; onSelect: () => void; icon?: React.ReactNode }) {
  return (
    <button
      onClick={onSelect}
      className={`flex items-center gap-2.5 w-full px-2 py-2 rounded-lg text-sm text-left transition-colors mb-0.5
        ${selected ? 'bg-indigo-50 text-indigo-700' : 'text-gray-700 active:bg-gray-50'}`}
    >
      <div className={`w-4 h-4 rounded-full border-2 flex items-center justify-center shrink-0 transition-colors
        ${selected ? 'border-indigo-600 bg-indigo-600' : 'border-gray-300'}`}>
        {selected && <div className="w-1.5 h-1.5 bg-white rounded-full" />}
      </div>
      {icon}
      <span className="flex-1 truncate">{label}</span>
      {selected && <Check size={14} className="text-indigo-600 shrink-0" />}
    </button>
  );
}
