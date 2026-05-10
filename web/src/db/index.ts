import Dexie, { type Table } from 'dexie';
import type { Note, Category, Folder, Tag, NoteTag, Attachment } from '../types';

class NoteorDB extends Dexie {
  notes!: Table<Note, number>;
  categories!: Table<Category, number>;
  folders!: Table<Folder, number>;
  tags!: Table<Tag, number>;
  note_tags!: Table<NoteTag>;
  attachments!: Table<Attachment, number>;

  constructor() {
    super('noteor');
    this.version(1).stores({
      notes: '++id, title, category_id, folder_id, updated_at, is_deleted',
      categories: '++id, name, parent_id, sort_order',
      folders: '++id, name, parent_id',
      tags: '++id, &name',
      note_tags: '[note_id+tag_id], note_id, tag_id',
      attachments: '++id, note_id, type, created_at',
    });
  }
}

export const db = new NoteorDB();

export function now(): string {
  return new Date().toISOString().slice(0, 19).replace('T', ' ');
}

// Notes
export async function getNotes(opts: {
  search?: string;
  categoryId?: number;
  folderId?: number;
  tagId?: number;
  typeFilter?: string;
  dateFilter?: string;
  deleted?: boolean;
}): Promise<Note[]> {
  const { search, categoryId, folderId, tagId, typeFilter, dateFilter, deleted = false } = opts;

  let notes = await db.notes.filter(n => n.is_deleted === deleted).toArray();

  if (search) {
    const q = search.toLowerCase();
    notes = notes.filter(n =>
      n.title.toLowerCase().includes(q) || n.content.toLowerCase().includes(q)
    );
  }
  if (categoryId !== undefined) notes = notes.filter(n => n.category_id === categoryId);
  if (folderId !== undefined) notes = notes.filter(n => n.folder_id === folderId);

  if (tagId !== undefined) {
    const taggedIds = (await db.note_tags.where('tag_id').equals(tagId).toArray()).map(r => r.note_id);
    notes = notes.filter(n => n.id !== undefined && taggedIds.includes(n.id));
  }

  if (typeFilter && typeFilter !== 'all') {
    const attachsByNote = await db.attachments.where('type').equals(typeFilter).toArray();
    const noteIds = new Set(attachsByNote.map(a => a.note_id));
    notes = notes.filter(n => n.id !== undefined && noteIds.has(n.id));
  }

  if (dateFilter && dateFilter !== 'all') {
    const now = new Date();
    let cutoff: Date;
    if (dateFilter === 'today') {
      cutoff = new Date(now.getFullYear(), now.getMonth(), now.getDate());
    } else if (dateFilter === '7d') {
      cutoff = new Date(now.getTime() - 7 * 86400000);
    } else if (dateFilter === '30d') {
      cutoff = new Date(now.getTime() - 30 * 86400000);
    } else {
      cutoff = new Date(now.getFullYear(), 0, 1);
    }
    const cutoffStr = cutoff.toISOString().slice(0, 19).replace('T', ' ');
    notes = notes.filter(n => n.updated_at >= cutoffStr);
  }

  return notes.sort((a, b) => b.updated_at.localeCompare(a.updated_at));
}

export async function saveNote(note: Note): Promise<number> {
  if (note.id) {
    await db.notes.update(note.id, { ...note, updated_at: now() });
    return note.id;
  }
  return db.notes.add({ ...note, created_at: now(), updated_at: now() });
}

export async function deleteNote(id: number): Promise<void> {
  await db.notes.update(id, { is_deleted: true, deleted_at: now() });
}

export async function restoreNote(id: number): Promise<void> {
  await db.notes.update(id, { is_deleted: false, deleted_at: undefined });
}

export async function permanentlyDeleteNote(id: number): Promise<void> {
  await db.attachments.where('note_id').equals(id).delete();
  await db.note_tags.where('note_id').equals(id).delete();
  await db.notes.delete(id);
}

// Tags
export async function getNoteTags(noteId: number): Promise<Tag[]> {
  const links = await db.note_tags.where('note_id').equals(noteId).toArray();
  if (!links.length) return [];
  return db.tags.where('id').anyOf(links.map(l => l.tag_id)).toArray();
}

export async function addTagToNote(noteId: number, tagName: string): Promise<void> {
  const name = tagName.trim().toLowerCase();
  if (!name) return;
  let tag = await db.tags.where('name').equalsIgnoreCase(name).first();
  if (!tag) {
    const colors = ['#6366F1', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6', '#EC4899', '#14B8A6'];
    const color = colors[Math.floor(Math.random() * colors.length)];
    const id = await db.tags.add({ name, color });
    tag = { id, name, color };
  }
  const exists = await db.note_tags.get([noteId, tag.id!]);
  if (!exists) await db.note_tags.add({ note_id: noteId, tag_id: tag.id! });
}

export async function removeTagFromNote(noteId: number, tagId: number): Promise<void> {
  await db.note_tags.delete([noteId, tagId]);
}

// Attachments
export async function getNoteAttachments(noteId: number): Promise<Attachment[]> {
  return db.attachments.where('note_id').equals(noteId).sortBy('created_at');
}

export async function addAttachment(attachment: Omit<Attachment, 'id'>): Promise<number> {
  return db.attachments.add(attachment as Attachment);
}

export async function deleteAttachment(id: number): Promise<void> {
  await db.attachments.delete(id);
}

// Categories
export async function getCategories(): Promise<Category[]> {
  return db.categories.orderBy('sort_order').toArray();
}

export async function saveCategory(cat: Category): Promise<number> {
  if (cat.id) { await db.categories.update(cat.id, cat); return cat.id; }
  return db.categories.add(cat);
}

export async function deleteCategory(id: number): Promise<void> {
  await db.notes.where('category_id').equals(id).modify({ category_id: undefined });
  await db.categories.where('parent_id').equals(id).modify({ parent_id: undefined });
  await db.categories.delete(id);
}

// Folders
export async function getFolders(): Promise<Folder[]> {
  return db.folders.toArray();
}

export async function saveFolder(folder: Folder): Promise<number> {
  if (folder.id) { await db.folders.update(folder.id, folder); return folder.id; }
  return db.folders.add({ ...folder, created_at: now() });
}

export async function deleteFolder(id: number): Promise<void> {
  await db.notes.where('folder_id').equals(id).modify({ folder_id: undefined });
  await db.folders.where('parent_id').equals(id).modify({ parent_id: undefined });
  await db.folders.delete(id);
}

// All tags
export async function getAllTags(): Promise<Tag[]> {
  return db.tags.toArray();
}

// ─── Export / Import ────────────────────────────────────────────────────────

export interface ExportAttachment {
  type: 'image' | 'audio' | 'video';
  filename: string;
  filepath: string;
  duration?: number;
}

export interface ExportNote {
  id: number;
  title: string;
  content: string;
  created_at: string;
  updated_at: string;
  is_deleted: boolean;
  deleted_at?: string;
  tags: { name: string; color: string }[];
  attachments: ExportAttachment[];
}

export interface ExportData {
  version: '1.0';
  app: 'Noteor';
  exported_at: string;
  notes: ExportNote[];
}

export async function exportAllNotes(): Promise<ExportData> {
  const notes = await db.notes.toArray();
  const exportedNotes: ExportNote[] = [];

  for (const note of notes) {
    if (!note.id) continue;
    const tags = await getNoteTags(note.id);
    const attachments = await db.attachments
      .where('note_id').equals(note.id).toArray();

    exportedNotes.push({
      id: note.id,
      title: note.title,
      content: note.content,
      created_at: note.created_at,
      updated_at: note.updated_at,
      is_deleted: note.is_deleted,
      deleted_at: note.deleted_at,
      tags: tags.map(t => ({ name: t.name, color: t.color })),
      attachments: attachments.map(a => ({
        type: a.type,
        filename: a.filename,
        filepath: a.filename,
        duration: a.duration,
      })),
    });
  }

  return {
    version: '1.0',
    app: 'Noteor',
    exported_at: new Date().toISOString(),
    notes: exportedNotes,
  };
}

export async function importNotes(
  data: ExportData
): Promise<{ imported: number; skipped: number; errors: number }> {
  let imported = 0;
  let skipped = 0;
  let errors = 0;

  const existingIds = new Set(
    (await db.notes.toArray()).map(n => n.id!)
  );

  for (const noteData of data.notes) {
    try {
      if (existingIds.has(noteData.id)) {
        skipped++;
        continue;
      }

      const newId = await db.notes.add({
        title: noteData.title,
        content: noteData.content,
        created_at: noteData.created_at,
        updated_at: noteData.updated_at,
        is_deleted: noteData.is_deleted ?? false,
        deleted_at: noteData.deleted_at,
      } as Note);

      for (const tagData of noteData.tags ?? []) {
        let tag = await db.tags.where('name').equalsIgnoreCase(tagData.name).first();
        if (!tag) {
          const tagId = await db.tags.add({ name: tagData.name, color: tagData.color });
          tag = { id: tagId, name: tagData.name, color: tagData.color };
        }
        const exists = await db.note_tags.get([newId, tag.id!]);
        if (!exists) await db.note_tags.add({ note_id: newId, tag_id: tag.id! });
      }

      imported++;
    } catch {
      errors++;
    }
  }

  return { imported, skipped, errors };
}
