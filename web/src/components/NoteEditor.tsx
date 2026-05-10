import { useState, useEffect, useRef, useCallback } from 'react';
import { ArrowLeft, Save, Bold, Italic, Code, List, Heading2, Eye, EyeOff, Image as ImageIcon, Trash2, X, Plus, Sparkles, Loader2, HelpCircle } from 'lucide-react';
import HelpModal from './HelpModal';

const HELP_SECTIONS = [
  {
    title: 'Saisie',
    items: [
      { label: 'Titre', description: 'Champ de titre en haut de l\'éditeur.' },
      { label: 'Contenu Markdown', description: 'Zone de texte principale. Utilise la syntaxe Markdown pour le formatage.' },
      { label: 'Aperçu', description: 'Bouton "Aperçu" (œil) pour basculer entre l\'édition et le rendu visuel.' },
      { label: 'Auto-sauvegarde', description: 'La note est enregistrée automatiquement 2,5 secondes après la dernière frappe.' },
    ],
  },
  {
    title: 'Tags',
    items: [
      { label: 'Filtrer par tag', description: 'Cliquer sur le nom d\'un tag pour revenir à la liste filtrée sur ce tag.' },
      { label: 'Ajouter un tag', description: 'Bouton "+ Tag" : saisir un nom puis Entrée. Le tag est créé s\'il n\'existe pas.' },
      { label: 'Supprimer un tag', description: 'Cliquer sur × à droite du tag pour le retirer de la note.' },
    ],
  },
  {
    title: 'Formatage Markdown',
    items: [
      { label: 'Gras (B)', description: '**texte** — met la sélection en gras.' },
      { label: 'Italique (I)', description: '*texte* — met la sélection en italique.' },
      { label: 'Code (◇)', description: '`texte` — formate la sélection en code inline.' },
      { label: 'Liste (≡)', description: 'Insère un élément de liste à puces (- ).' },
      { label: 'Titre (H2)', description: 'Insère un titre de niveau 2 (## ).' },
    ],
  },
  {
    title: 'Médias',
    items: [
      { label: 'Audio', description: 'Enregistre un mémo vocal via le micro. Appuyer à nouveau pour arrêter.' },
      { label: 'Photo', description: 'Importe une image depuis la galerie ou l\'appareil photo.' },
      { label: 'IA (transcription)', description: 'Visible uniquement si la note contient un audio. Envoie l\'enregistrement à OpenRouter et insère la transcription dans le texte.' },
    ],
  },
];
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { saveNote, getNoteTags, addTagToNote, removeTagFromNote, getNoteAttachments, addAttachment, deleteAttachment, now } from '../db';
import { AudioRecorderButton, AudioPlayer } from './AudioRecorder';
import TagChip from './TagChip';
import { transcribeAudio, loadSettings } from '../services/openrouter';
import type { Note, Tag, Attachment } from '../types';

interface Props {
  note: Note;
  onBack: () => void;
  onSaved: (note: Note) => void;
  onTagClick: (tag: Tag) => void;
}

export default function NoteEditor({ note, onBack, onSaved, onTagClick }: Props) {
  const [title, setTitle] = useState(note.title);
  const [content, setContent] = useState(note.content);
  const [preview, setPreview] = useState(false);
  const [tags, setTags] = useState<Tag[]>([]);
  const [tagInput, setTagInput] = useState('');
  const [showTagInput, setShowTagInput] = useState(false);
  const [attachments, setAttachments] = useState<Attachment[]>([]);
  const [dirty, setDirty] = useState(false);
  const [showHelp, setShowHelp] = useState(false);
  const [transcribing, setTranscribing] = useState(false);
  const [transcribeError, setTranscribeError] = useState('');
  const autoSaveRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const noteIdRef = useRef<number | undefined>(note.id);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    setTitle(note.title);
    setContent(note.content);
    setDirty(false);
    noteIdRef.current = note.id;
    if (note.id) {
      getNoteTags(note.id).then(setTags);
      getNoteAttachments(note.id).then(setAttachments);
    } else {
      setTags([]);
      setAttachments([]);
    }
  }, [note.id]);

  const doSave = useCallback(async (t: string, c: string) => {
    const updated: Note = { ...note, id: noteIdRef.current, title: t, content: c, updated_at: now() };
    const id = await saveNote(updated);
    noteIdRef.current = id;
    onSaved({ ...updated, id });
    setDirty(false);
  }, [note, onSaved]);

  useEffect(() => {
    if (!dirty) return;
    autoSaveRef.current && clearTimeout(autoSaveRef.current);
    autoSaveRef.current = setTimeout(() => doSave(title, content), 2500);
    return () => { autoSaveRef.current && clearTimeout(autoSaveRef.current); };
  }, [title, content, dirty, doSave]);

  function markDirty() { setDirty(true); }

  function insertMarkdown(before: string, after = '') {
    const ta = textareaRef.current;
    if (!ta) return;
    const start = ta.selectionStart;
    const end = ta.selectionEnd;
    const selected = content.slice(start, end);
    const newContent = content.slice(0, start) + before + selected + after + content.slice(end);
    setContent(newContent);
    setDirty(true);
    setTimeout(() => {
      ta.focus();
      ta.setSelectionRange(start + before.length, start + before.length + selected.length);
    }, 0);
  }

  async function handleAddTag() {
    if (!tagInput.trim() || !noteIdRef.current) return;
    await addTagToNote(noteIdRef.current, tagInput.trim());
    const updated = await getNoteTags(noteIdRef.current);
    setTags(updated);
    setTagInput('');
    setShowTagInput(false);
  }

  async function handleRemoveTag(tagId: number) {
    if (!noteIdRef.current) return;
    await removeTagFromNote(noteIdRef.current, tagId);
    setTags(prev => prev.filter(t => t.id !== tagId));
  }

  async function handleAudioSave(blob: Blob, filename: string) {
    if (!noteIdRef.current) await doSave(title, content);
    const att: Omit<Attachment, 'id'> = {
      note_id: noteIdRef.current!,
      type: 'audio',
      filename,
      data: blob,
      created_at: now(),
    };
    await addAttachment(att);
    const updated = await getNoteAttachments(noteIdRef.current!);
    setAttachments(updated);
  }

  async function handleImageImport() {
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = 'image/*';
    input.onchange = async () => {
      const file = input.files?.[0];
      if (!file) return;
      if (!noteIdRef.current) await doSave(title, content);
      const thumbnail = await createThumbnail(file);
      const att: Omit<Attachment, 'id'> = {
        note_id: noteIdRef.current!,
        type: 'image',
        filename: file.name,
        data: file,
        thumbnail,
        created_at: now(),
      };
      await addAttachment(att);
      const updated = await getNoteAttachments(noteIdRef.current!);
      setAttachments(updated);
    };
    input.click();
  }

  async function handleDeleteAttachment(id: number) {
    await deleteAttachment(id);
    setAttachments(prev => prev.filter(a => a.id !== id));
  }

  async function handleTranscribe() {
    const audioAttachments = attachments.filter(a => a.type === 'audio');
    if (!audioAttachments.length) return;

    const { openrouterKey, selectedModel } = loadSettings();
    if (!openrouterKey || !selectedModel) {
      setTranscribeError('Configure ta clé API et un modèle dans les Paramètres.');
      setTimeout(() => setTranscribeError(''), 4000);
      return;
    }

    setTranscribing(true);
    setTranscribeError('');
    try {
      const results: string[] = [];
      for (const att of audioAttachments) {
        const text = await transcribeAudio(att.data, selectedModel, openrouterKey);
        if (text) results.push(text);
      }
      if (results.length) {
        const insertion = '\n\n' + results.join('\n\n');
        setContent(prev => prev + insertion);
        setDirty(true);
      }
    } catch (e) {
      const msg = e instanceof Error ? e.message : 'Erreur de transcription';
      setTranscribeError(msg);
      setTimeout(() => setTranscribeError(''), 5000);
    } finally {
      setTranscribing(false);
    }
  }

  return (
    <div className="flex flex-col h-full bg-white">
      {/* Header */}
      <div className="flex items-center gap-2 px-4 pt-4 pb-3 border-b border-gray-100">
        <button onClick={onBack} className="p-1.5 -ml-1.5 text-gray-500 active:text-gray-700">
          <ArrowLeft size={22} />
        </button>
        <div className="flex-1" />
        {dirty && (
          <span className="text-xs text-gray-400">Modification...</span>
        )}
        <button
          onClick={() => setShowHelp(true)}
          className="p-1.5 text-gray-400 active:text-gray-600"
          aria-label="Aide"
        >
          <HelpCircle size={19} />
        </button>
        <button
          onClick={() => doSave(title, content)}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-indigo-600 text-white text-sm active:bg-indigo-700"
        >
          <Save size={14} />
          Enregistrer
        </button>
      </div>

      {/* Title */}
      <div className="px-4 pt-3 pb-2">
        <input
          type="text"
          placeholder="Titre de la note"
          value={title}
          onChange={e => { setTitle(e.target.value); markDirty(); }}
          className="w-full text-xl font-bold text-gray-900 placeholder-gray-300 outline-none bg-transparent"
        />
      </div>

      {/* Tags */}
      <div className="px-4 pb-2 flex flex-wrap items-center gap-1.5 min-h-[32px]">
        {tags.map(tag => (
          <TagChip key={tag.id} tag={tag} onRemove={() => handleRemoveTag(tag.id!)} onClick={() => onTagClick(tag)} />
        ))}
        {showTagInput ? (
          <div className="flex items-center gap-1">
            <input
              autoFocus
              type="text"
              placeholder="Nouveau tag..."
              value={tagInput}
              onChange={e => setTagInput(e.target.value)}
              onKeyDown={e => { if (e.key === 'Enter') handleAddTag(); if (e.key === 'Escape') { setShowTagInput(false); setTagInput(''); }}}
              className="text-xs border border-indigo-300 rounded-full px-2.5 py-0.5 outline-none w-28 focus:border-indigo-500"
            />
            <button onClick={handleAddTag} className="text-indigo-600 active:opacity-70"><Plus size={14} /></button>
            <button onClick={() => { setShowTagInput(false); setTagInput(''); }} className="text-gray-400 active:opacity-70"><X size={14} /></button>
          </div>
        ) : (
          <button
            onClick={() => { if (noteIdRef.current) setShowTagInput(true); else doSave(title, content).then(() => setShowTagInput(true)); }}
            className="text-xs text-gray-400 border border-dashed border-gray-300 rounded-full px-2.5 py-0.5 active:bg-gray-50"
          >
            + Tag
          </button>
        )}
      </div>

      {/* Markdown toolbar */}
      <div className="flex items-center gap-1 px-3 py-1.5 border-y border-gray-100 overflow-x-auto">
        <button onClick={() => insertMarkdown('**', '**')} className="p-1.5 rounded text-gray-600 active:bg-gray-100"><Bold size={16} /></button>
        <button onClick={() => insertMarkdown('*', '*')} className="p-1.5 rounded text-gray-600 active:bg-gray-100"><Italic size={16} /></button>
        <button onClick={() => insertMarkdown('`', '`')} className="p-1.5 rounded text-gray-600 active:bg-gray-100"><Code size={16} /></button>
        <button onClick={() => insertMarkdown('\n- ')} className="p-1.5 rounded text-gray-600 active:bg-gray-100"><List size={16} /></button>
        <button onClick={() => insertMarkdown('\n## ')} className="p-1.5 rounded text-gray-600 active:bg-gray-100"><Heading2 size={16} /></button>
        <div className="flex-1" />
        <button
          onClick={() => setPreview(p => !p)}
          className={`flex items-center gap-1 px-2.5 py-1 rounded-lg text-xs ${preview ? 'bg-indigo-100 text-indigo-700' : 'text-gray-500 active:bg-gray-100'}`}
        >
          {preview ? <EyeOff size={14} /> : <Eye size={14} />}
          {preview ? 'Éditer' : 'Aperçu'}
        </button>
      </div>

      {/* Editor / Preview */}
      <div className="flex-1 overflow-y-auto">
        {preview ? (
          <div className="px-4 py-3 prose prose-sm max-w-none">
            <ReactMarkdown remarkPlugins={[remarkGfm]}>{content || '*Aucun contenu*'}</ReactMarkdown>
          </div>
        ) : (
          <textarea
            ref={textareaRef}
            value={content}
            onChange={e => { setContent(e.target.value); markDirty(); }}
            placeholder="Commencez à écrire en Markdown..."
            className="w-full h-full px-4 py-3 text-sm text-gray-800 placeholder-gray-300 outline-none resize-none bg-transparent font-mono leading-relaxed"
          />
        )}
      </div>

      {/* Attachments */}
      {attachments.length > 0 && (
        <div className="border-t border-gray-100 px-4 py-2 flex flex-col gap-2">
          {attachments.filter(a => a.type === 'audio').map(a => (
            <AudioPlayer key={a.id} attachment={a} onDelete={() => handleDeleteAttachment(a.id!)} />
          ))}
          {attachments.filter(a => a.type === 'image').length > 0 && (
            <div className="flex gap-2 overflow-x-auto pb-1">
              {attachments.filter(a => a.type === 'image').map(a => (
                <ImageAttachment key={a.id} attachment={a} onDelete={() => handleDeleteAttachment(a.id!)} />
              ))}
            </div>
          )}
        </div>
      )}

      {/* Erreur transcription */}
      {transcribeError && (
        <div className="mx-4 mb-2 px-3 py-2 bg-red-50 border border-red-100 rounded-xl text-xs text-red-600">
          {transcribeError}
        </div>
      )}

      {/* Bottom action bar */}
      <div className="flex items-center gap-2 px-4 py-2 border-t border-gray-100 safe-bottom">
        <AudioRecorderButton onSave={handleAudioSave} />
        <button
          onClick={handleImageImport}
          className="flex items-center gap-1.5 px-3 py-2 rounded-lg bg-gray-100 text-gray-700 active:bg-gray-200"
        >
          <ImageIcon size={16} />
          <span className="text-sm">Photo</span>
        </button>

        {/* Bouton IA — visible seulement si enregistrement audio présent */}
        {attachments.some(a => a.type === 'audio') && (
          <button
            onClick={handleTranscribe}
            disabled={transcribing}
            className={`flex items-center gap-1.5 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
              transcribing
                ? 'bg-indigo-100 text-indigo-400'
                : 'bg-indigo-600 text-white active:bg-indigo-700'
            }`}
            title="Transcrire l'audio en texte via IA"
          >
            {transcribing ? <Loader2 size={16} className="animate-spin" /> : <Sparkles size={16} />}
            IA
          </button>
        )}

        <div className="flex-1" />
        <button
          onClick={async () => {
            if (confirm('Mettre cette note à la corbeille ?')) {
              await saveNote({ ...note, id: noteIdRef.current });
              onBack();
            }
          }}
          className="p-2 text-gray-400 active:text-red-500"
          aria-label="Supprimer"
        >
          <Trash2 size={18} />
        </button>
      </div>

      {showHelp && (
        <HelpModal
          title="Aide — Éditeur de note"
          sections={HELP_SECTIONS}
          onClose={() => setShowHelp(false)}
        />
      )}
    </div>
  );
}

function ImageAttachment({ attachment, onDelete }: { attachment: Attachment; onDelete: () => void }) {
  const [url, setUrl] = useState<string | null>(null);

  useEffect(() => {
    const objUrl = URL.createObjectURL(attachment.data);
    setUrl(objUrl);
    return () => URL.revokeObjectURL(objUrl);
  }, [attachment.data]);

  return (
    <div className="relative shrink-0">
      {url && (
        <img
          src={url}
          alt={attachment.filename}
          className="h-24 w-24 object-cover rounded-lg border border-gray-200"
          onClick={() => window.open(url, '_blank')}
        />
      )}
      <button
        onClick={onDelete}
        className="absolute -top-1.5 -right-1.5 w-5 h-5 rounded-full bg-gray-800 text-white flex items-center justify-center active:opacity-70"
      >
        <X size={11} strokeWidth={2.5} />
      </button>
    </div>
  );
}

async function createThumbnail(file: File): Promise<string> {
  return new Promise(resolve => {
    const img = new window.Image();
    const url = URL.createObjectURL(file);
    img.onload = () => {
      const canvas = document.createElement('canvas');
      const max = 400;
      const ratio = Math.min(max / img.width, max / img.height);
      canvas.width = img.width * ratio;
      canvas.height = img.height * ratio;
      canvas.getContext('2d')?.drawImage(img, 0, 0, canvas.width, canvas.height);
      URL.revokeObjectURL(url);
      resolve(canvas.toDataURL('image/jpeg', 0.7));
    };
    img.onerror = () => { URL.revokeObjectURL(url); resolve(''); };
    img.src = url;
  });
}
