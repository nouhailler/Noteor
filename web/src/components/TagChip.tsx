import { X } from 'lucide-react';
import type { Tag } from '../types';

interface Props {
  tag: Tag;
  onRemove?: () => void;
  onClick?: () => void;
}

export default function TagChip({ tag, onRemove, onClick }: Props) {
  return (
    <span
      className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium text-white"
      style={{ backgroundColor: tag.color }}
    >
      <button
        onClick={onClick}
        className={onClick ? 'hover:opacity-80 active:opacity-60' : 'cursor-default'}
        aria-label={`Filtrer par tag ${tag.name}`}
      >
        {tag.name}
      </button>
      {onRemove && (
        <button
          onClick={e => { e.stopPropagation(); onRemove(); }}
          className="ml-0.5 hover:opacity-70 active:opacity-50"
          aria-label={`Supprimer le tag ${tag.name}`}
        >
          <X size={11} strokeWidth={2.5} />
        </button>
      )}
    </span>
  );
}
