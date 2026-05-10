export interface Note {
  id?: number;
  title: string;
  content: string;
  category_id?: number;
  folder_id?: number;
  created_at: string;
  updated_at: string;
  is_deleted: boolean;
  deleted_at?: string;
}

export interface Category {
  id?: number;
  name: string;
  parent_id?: number;
  color: string;
  sort_order: number;
}

export interface Folder {
  id?: number;
  name: string;
  parent_id?: number;
  created_at: string;
}

export interface Tag {
  id?: number;
  name: string;
  color: string;
}

export interface NoteTag {
  note_id: number;
  tag_id: number;
}

export interface Attachment {
  id?: number;
  note_id: number;
  type: 'image' | 'audio' | 'video';
  filename: string;
  data: Blob;
  thumbnail?: string;
  duration?: number;
  created_at: string;
}

export type FilterType = 'all' | 'audio' | 'image' | 'video';
export type DateFilter = 'all' | 'today' | '7d' | '30d' | 'year';
export type View = 'list' | 'editor' | 'sidebar';
