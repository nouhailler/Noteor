import { useState } from 'react';
import { X, Folder, Tag as TagIcon, LayoutGrid, Trash2, ChevronRight, Plus, HelpCircle } from 'lucide-react';
import { useLiveQuery } from 'dexie-react-hooks';
import { getCategories, getFolders, getAllTags, saveCategory, saveFolder, deleteCategory, deleteFolder } from '../db';
import HelpModal from './HelpModal';
import type { FilterType, DateFilter } from '../types';

const HELP_SECTIONS = [
  {
    title: 'Filtres rapides',
    items: [
      { label: 'Type de contenu', description: 'Afficher uniquement les notes avec audio, images, ou toutes les notes.' },
      { label: 'Période', description: 'Filtrer par date de dernière modification : aujourd\'hui, 7 j, 30 j, cette année.' },
    ],
  },
  {
    title: 'Organisation',
    items: [
      { label: 'Catégories', description: 'Filtrer les notes par catégorie colorée. Bouton + pour créer, × au survol pour supprimer.' },
      { label: 'Dossiers', description: 'Filtrer les notes par dossier. Bouton + pour créer, × au survol pour supprimer.' },
      { label: 'Tags', description: 'Cliquer sur un tag pour filtrer les notes qui le portent.' },
    ],
  },
  {
    title: 'Corbeille',
    items: [
      { label: 'Accéder à la corbeille', description: 'Bouton Corbeille en haut du panneau.' },
      { label: 'Restaurer une note', description: 'Icône ↩ sur une note dans la corbeille.' },
      { label: 'Supprimer définitivement', description: 'Icône 🗑 sur une note dans la corbeille — irréversible.' },
    ],
  },
  {
    title: 'Réinitialiser',
    items: [
      { label: 'Effacer les filtres', description: 'Lien "Effacer tous les filtres" en haut du panneau quand des filtres sont actifs.' },
    ],
  },
];

interface Props {
  filters: {
    categoryId?: number;
    folderId?: number;
    tagId?: number;
    typeFilter: FilterType;
    dateFilter: DateFilter;
    deleted: boolean;
  };
  onFiltersChange: (f: Partial<Props['filters']>) => void;
  onClose: () => void;
}

export default function Sidebar({ filters, onFiltersChange, onClose }: Props) {
  const categories = useLiveQuery(getCategories) ?? [];
  const folders = useLiveQuery(getFolders) ?? [];
  const tags = useLiveQuery(getAllTags) ?? [];

  const [newCatName, setNewCatName] = useState('');
  const [addingCat, setAddingCat] = useState(false);
  const [newFolderName, setNewFolderName] = useState('');
  const [addingFolder, setAddingFolder] = useState(false);
  const [showHelp, setShowHelp] = useState(false);

  async function handleAddCategory() {
    if (!newCatName.trim()) return;
    const colors = ['#4F46E5', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6', '#EC4899'];
    await saveCategory({ name: newCatName.trim(), color: colors[categories.length % colors.length], sort_order: categories.length });
    setNewCatName('');
    setAddingCat(false);
  }

  async function handleAddFolder() {
    if (!newFolderName.trim()) return;
    await saveFolder({ name: newFolderName.trim(), created_at: '' });
    setNewFolderName('');
    setAddingFolder(false);
  }

  const TYPE_OPTIONS: { value: FilterType; label: string }[] = [
    { value: 'all', label: 'Tous les types' },
    { value: 'audio', label: 'Avec audio' },
    { value: 'image', label: 'Avec images' },
    { value: 'video', label: 'Avec vidéos' },
  ];

  const DATE_OPTIONS: { value: DateFilter; label: string }[] = [
    { value: 'all', label: 'Toutes les dates' },
    { value: 'today', label: "Aujourd'hui" },
    { value: '7d', label: '7 derniers jours' },
    { value: '30d', label: '30 derniers jours' },
    { value: 'year', label: 'Cette année' },
  ];

  return (
    <div className="flex flex-col h-full bg-white">
      {/* Header */}
      <div className="flex items-center px-4 pt-4 pb-3 border-b border-gray-100">
        <span className="font-semibold text-gray-800 flex-1">Filtres &amp; Organisation</span>
        <button onClick={() => setShowHelp(true)} className="p-1.5 text-gray-400 active:text-gray-600" aria-label="Aide">
          <HelpCircle size={18} />
        </button>
        <button onClick={onClose} className="p-1.5 text-gray-400 active:text-gray-700">
          <X size={20} />
        </button>
      </div>

      <div className="flex-1 overflow-y-auto pb-safe-bottom">
        {/* Active filters reset */}
        {(filters.categoryId || filters.folderId || filters.tagId || filters.typeFilter !== 'all' || filters.dateFilter !== 'all' || filters.deleted) && (
          <div className="px-4 py-3 border-b border-gray-100">
            <button
              onClick={() => onFiltersChange({ categoryId: undefined, folderId: undefined, tagId: undefined, typeFilter: 'all', dateFilter: 'all', deleted: false })}
              className="text-xs text-indigo-600 font-medium"
            >
              Effacer tous les filtres
            </button>
          </div>
        )}

        {/* Corbeille */}
        <div className="px-4 pt-4 pb-2">
          <button
            onClick={() => { onFiltersChange({ deleted: !filters.deleted, categoryId: undefined, folderId: undefined, tagId: undefined }); onClose(); }}
            className={`flex items-center gap-2 w-full px-3 py-2 rounded-lg text-sm ${filters.deleted ? 'bg-red-50 text-red-600' : 'text-gray-600 active:bg-gray-50'}`}
          >
            <Trash2 size={16} />
            Corbeille
          </button>
        </div>

        <Section title="Type" icon={<LayoutGrid size={14} />}>
          <div className="flex flex-col gap-1">
            {TYPE_OPTIONS.map(o => (
              <button
                key={o.value}
                onClick={() => { onFiltersChange({ typeFilter: o.value }); onClose(); }}
                className={`text-left px-3 py-2 rounded-lg text-sm ${filters.typeFilter === o.value ? 'bg-indigo-50 text-indigo-700 font-medium' : 'text-gray-600 active:bg-gray-50'}`}
              >
                {o.label}
              </button>
            ))}
          </div>
        </Section>

        <Section title="Date" icon={<ChevronRight size={14} />}>
          <div className="flex flex-col gap-1">
            {DATE_OPTIONS.map(o => (
              <button
                key={o.value}
                onClick={() => { onFiltersChange({ dateFilter: o.value }); onClose(); }}
                className={`text-left px-3 py-2 rounded-lg text-sm ${filters.dateFilter === o.value ? 'bg-indigo-50 text-indigo-700 font-medium' : 'text-gray-600 active:bg-gray-50'}`}
              >
                {o.label}
              </button>
            ))}
          </div>
        </Section>

        <Section
          title="Catégories"
          icon={<LayoutGrid size={14} />}
          action={<button onClick={() => setAddingCat(true)} className="text-indigo-600 active:opacity-70"><Plus size={16} /></button>}
        >
          {addingCat && (
            <div className="flex gap-1 mb-2">
              <input
                autoFocus
                type="text"
                placeholder="Nom..."
                value={newCatName}
                onChange={e => setNewCatName(e.target.value)}
                onKeyDown={e => { if (e.key === 'Enter') handleAddCategory(); if (e.key === 'Escape') setAddingCat(false); }}
                className="flex-1 text-sm border border-gray-200 rounded-lg px-2 py-1 outline-none focus:border-indigo-400"
              />
              <button onClick={handleAddCategory} className="px-2 py-1 bg-indigo-600 text-white text-xs rounded-lg">OK</button>
            </div>
          )}
          {categories.length === 0 && !addingCat && (
            <p className="text-xs text-gray-400 px-1">Aucune catégorie</p>
          )}
          {categories.map(cat => (
            <div key={cat.id} className="flex items-center gap-2 group">
              <button
                onClick={() => { onFiltersChange({ categoryId: filters.categoryId === cat.id ? undefined : cat.id, folderId: undefined }); onClose(); }}
                className={`flex-1 flex items-center gap-2 px-3 py-2 rounded-lg text-sm text-left ${filters.categoryId === cat.id ? 'bg-indigo-50 text-indigo-700 font-medium' : 'text-gray-600 active:bg-gray-50'}`}
              >
                <span className="w-2.5 h-2.5 rounded-full shrink-0" style={{ backgroundColor: cat.color }} />
                {cat.name}
              </button>
              <button onClick={() => deleteCategory(cat.id!)} className="opacity-0 group-hover:opacity-100 p-1 text-gray-300 active:text-red-500">
                <X size={12} />
              </button>
            </div>
          ))}
        </Section>

        <Section
          title="Dossiers"
          icon={<Folder size={14} />}
          action={<button onClick={() => setAddingFolder(true)} className="text-indigo-600 active:opacity-70"><Plus size={16} /></button>}
        >
          {addingFolder && (
            <div className="flex gap-1 mb-2">
              <input
                autoFocus
                type="text"
                placeholder="Nom..."
                value={newFolderName}
                onChange={e => setNewFolderName(e.target.value)}
                onKeyDown={e => { if (e.key === 'Enter') handleAddFolder(); if (e.key === 'Escape') setAddingFolder(false); }}
                className="flex-1 text-sm border border-gray-200 rounded-lg px-2 py-1 outline-none focus:border-indigo-400"
              />
              <button onClick={handleAddFolder} className="px-2 py-1 bg-indigo-600 text-white text-xs rounded-lg">OK</button>
            </div>
          )}
          {folders.length === 0 && !addingFolder && (
            <p className="text-xs text-gray-400 px-1">Aucun dossier</p>
          )}
          {folders.map(folder => (
            <div key={folder.id} className="flex items-center gap-2 group">
              <button
                onClick={() => { onFiltersChange({ folderId: filters.folderId === folder.id ? undefined : folder.id, categoryId: undefined }); onClose(); }}
                className={`flex-1 flex items-center gap-2 px-3 py-2 rounded-lg text-sm text-left ${filters.folderId === folder.id ? 'bg-indigo-50 text-indigo-700 font-medium' : 'text-gray-600 active:bg-gray-50'}`}
              >
                <Folder size={14} className="text-gray-400" />
                {folder.name}
              </button>
              <button onClick={() => deleteFolder(folder.id!)} className="opacity-0 group-hover:opacity-100 p-1 text-gray-300 active:text-red-500">
                <X size={12} />
              </button>
            </div>
          ))}
        </Section>

        <Section title="Tags" icon={<TagIcon size={14} />}>
          {tags.length === 0 && <p className="text-xs text-gray-400 px-1">Aucun tag</p>}
          <div className="flex flex-wrap gap-2 px-1">
            {tags.map(tag => (
              <button
                key={tag.id}
                onClick={() => { onFiltersChange({ tagId: filters.tagId === tag.id ? undefined : tag.id }); onClose(); }}
                className={`px-2.5 py-1 rounded-full text-xs font-medium text-white transition-opacity ${filters.tagId === tag.id ? 'ring-2 ring-offset-1 ring-current' : 'opacity-80 active:opacity-60'}`}
                style={{ backgroundColor: tag.color }}
              >
                {tag.name}
              </button>
            ))}
          </div>
        </Section>
      </div>

      {showHelp && (
        <HelpModal
          title="Aide — Filtres &amp; Organisation"
          sections={HELP_SECTIONS}
          onClose={() => setShowHelp(false)}
        />
      )}
    </div>
  );
}

function Section({ title, icon, children, action }: { title: string; icon: React.ReactNode; children: React.ReactNode; action?: React.ReactNode }) {
  return (
    <div className="px-4 pt-4 pb-2 border-t border-gray-50">
      <div className="flex items-center gap-1.5 mb-2">
        <span className="text-gray-400">{icon}</span>
        <span className="text-xs font-semibold text-gray-500 uppercase tracking-wide">{title}</span>
        {action && <div className="ml-auto">{action}</div>}
      </div>
      {children}
    </div>
  );
}
