const OPENROUTER_BASE = 'https://openrouter.ai/api/v1';

export interface OpenRouterModel {
  id: string;
  name: string;
  description?: string;
  architecture?: {
    input_modalities?: string[];
    output_modalities?: string[];
  };
  context_length?: number;
  pricing?: { prompt: string; completion: string };
}

export async function fetchFreeModels(apiKey: string): Promise<OpenRouterModel[]> {
  const res = await fetch(`${OPENROUTER_BASE}/models`, {
    headers: { Authorization: `Bearer ${apiKey}` },
  });
  if (!res.ok) throw new Error(`Erreur API : ${res.status} ${res.statusText}`);
  const data = await res.json() as { data: OpenRouterModel[] };
  return data.data
    .filter(m => m.id.endsWith(':free'))
    .sort((a, b) => a.name.localeCompare(b.name));
}

export async function transcribeAudio(
  audioBlob: Blob,
  model: string,
  apiKey: string
): Promise<string> {
  const base64 = await blobToBase64(audioBlob);
  const format = audioBlob.type.includes('mp4') ? 'mp4' : 'webm';

  const res = await fetch(`${OPENROUTER_BASE}/chat/completions`, {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${apiKey}`,
      'Content-Type': 'application/json',
      'HTTP-Referer': window.location.origin,
      'X-Title': 'Noteor',
    },
    body: JSON.stringify({
      model,
      messages: [
        {
          role: 'user',
          content: [
            {
              type: 'input_audio',
              input_audio: { data: base64, format },
            },
            {
              type: 'text',
              text: 'Transcris cet enregistrement audio mot pour mot, sans ajouter de commentaire ni de mise en forme. Retourne uniquement le texte parlé.',
            },
          ],
        },
      ],
    }),
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({})) as { error?: { message?: string } };
    throw new Error(err?.error?.message ?? `Erreur ${res.status}`);
  }

  const data = await res.json() as { choices: { message: { content: string } }[] };
  return data.choices?.[0]?.message?.content?.trim() ?? '';
}

function blobToBase64(blob: Blob): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => {
      const result = reader.result as string;
      resolve(result.split(',')[1]);
    };
    reader.onerror = reject;
    reader.readAsDataURL(blob);
  });
}

// Persistance dans localStorage
const STORAGE_KEY = 'noteor_settings';

interface Settings {
  openrouterKey: string;
  selectedModel: string;
}

export function loadSettings(): Settings {
  try {
    return JSON.parse(localStorage.getItem(STORAGE_KEY) ?? '{}') as Settings;
  } catch {
    return { openrouterKey: '', selectedModel: '' };
  }
}

export function saveSettings(settings: Partial<Settings>): void {
  const current = loadSettings();
  localStorage.setItem(STORAGE_KEY, JSON.stringify({ ...current, ...settings }));
}
