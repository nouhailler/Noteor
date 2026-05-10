import { X } from 'lucide-react';
import type { Tag } from '../types';

interface Props {
  tag: Tag;
  onRemove?: () => void;
}

export default function TagChip({ tag, onRemove }: Props) {
  return (
    <span
      className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium text-white"
      style={{ backgroundColor: tag.color }}
    >
      {tag.name}
      {onRemove && (
        <button
          onClick={onRemove}
          className="ml-0.5 hover:opacity-70 active:opacity-50"
          aria-label={`Supprimer le tag ${tag.name}`}
        >
          <X size={11} strokeWidth={2.5} />
        </button>
      )}
    </span>
  );
}
