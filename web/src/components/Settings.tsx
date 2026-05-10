import { useState, useEffect } from 'react';
import { ArrowLeft, Key, RefreshCw, Check, AlertCircle, ExternalLink } from 'lucide-react';
import { fetchFreeModels, loadSettings, saveSettings, type OpenRouterModel } from '../services/openrouter';

interface Props {
  onBack: () => void;
}

export default function Settings({ onBack }: Props) {
  const [apiKey, setApiKey] = useState('');
  const [selectedModel, setSelectedModel] = useState('');
  const [models, setModels] = useState<OpenRouterModel[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    const s = loadSettings();
    setApiKey(s.openrouterKey ?? '');
    setSelectedModel(s.selectedModel ?? '');
  }, []);

  async function handleFetchModels() {
    if (!apiKey.trim()) { setError('Entre d\'abord ta clé API.'); return; }
    setError('');
    setLoading(true);
    try {
      const list = await fetchFreeModels(apiKey.trim());
      setModels(list);
      if (list.length === 0) setError('Aucun modèle gratuit trouvé.');
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Erreur lors de la récupération des modèles.');
    } finally {
      setLoading(false);
    }
  }

  function handleSave() {
    saveSettings({ openrouterKey: apiKey.trim(), selectedModel });
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  }

  const supportsAudio = (m: OpenRouterModel) =>
    m.architecture?.input_modalities?.includes('audio') ?? false;

  const audioModels = models.filter(supportsAudio);
  const otherModels = models.filter(m => !supportsAudio(m));

  return (
    <div className="flex flex-col h-full bg-white">
      {/* Header */}
      <div className="flex items-center gap-2 px-4 pt-4 pb-3 border-b border-gray-100">
        <button onClick={onBack} className="p-1.5 -ml-1.5 text-gray-500 active:text-gray-700">
          <ArrowLeft size={22} />
        </button>
        <h1 className="text-base font-semibold text-gray-800 flex-1">Paramètres</h1>
        <button
          onClick={handleSave}
          className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm transition-colors ${
            saved ? 'bg-green-500 text-white' : 'bg-indigo-600 text-white active:bg-indigo-700'
          }`}
        >
          {saved ? <Check size={14} /> : null}
          {saved ? 'Enregistré' : 'Enregistrer'}
        </button>
      </div>

      <div className="flex-1 overflow-y-auto px-4 py-4 space-y-6">
        {/* Section OpenRouter */}
        <section>
          <div className="flex items-center gap-2 mb-3">
            <div className="w-8 h-8 rounded-lg bg-indigo-100 flex items-center justify-center">
              <Key size={16} className="text-indigo-600" />
            </div>
            <div>
              <h2 className="text-sm font-semibold text-gray-800">OpenRouter</h2>
              <p className="text-xs text-gray-500">Transcription audio vers texte par IA</p>
            </div>
            <a
              href="https://openrouter.ai/keys"
              target="_blank"
              rel="noopener noreferrer"
              className="ml-auto text-indigo-500 active:opacity-70"
              aria-label="Obtenir une clé API"
            >
              <ExternalLink size={16} />
            </a>
          </div>

          {/* Clé API */}
          <div className="mb-3">
            <label className="block text-xs font-medium text-gray-600 mb-1.5">Clé API</label>
            <input
              type="password"
              placeholder="sk-or-..."
              value={apiKey}
              onChange={e => { setApiKey(e.target.value); setSaved(false); }}
              className="w-full px-3 py-2.5 text-sm border border-gray-200 rounded-xl outline-none focus:border-indigo-400 focus:ring-2 focus:ring-indigo-100 font-mono"
            />
          </div>

          {/* Bouton Refresh modèles */}
          <button
            onClick={handleFetchModels}
            disabled={loading}
            className="flex items-center gap-2 w-full px-4 py-2.5 rounded-xl border border-indigo-200 text-indigo-600 text-sm font-medium active:bg-indigo-50 disabled:opacity-50 transition-colors"
          >
            <RefreshCw size={16} className={loading ? 'animate-spin' : ''} />
            {loading ? 'Chargement des modèles...' : 'Actualiser les modèles gratuits'}
          </button>

          {error && (
            <div className="flex items-start gap-2 mt-3 px-3 py-2.5 bg-red-50 rounded-xl border border-red-100">
              <AlertCircle size={16} className="text-red-500 shrink-0 mt-0.5" />
              <p className="text-xs text-red-600">{error}</p>
            </div>
          )}
        </section>

        {/* Sélection du modèle */}
        {models.length > 0 && (
          <section>
            <h2 className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-3">
              Modèle pour la transcription ({models.length} gratuits)
            </h2>

            {audioModels.length > 0 && (
              <div className="mb-4">
                <p className="text-xs text-green-600 font-medium mb-2 flex items-center gap-1">
                  <span className="w-2 h-2 rounded-full bg-green-500 inline-block" />
                  Supporte l'audio
                </p>
                <ModelList
                  models={audioModels}
                  selected={selectedModel}
                  onSelect={m => { setSelectedModel(m); setSaved(false); }}
                />
              </div>
            )}

            {otherModels.length > 0 && (
              <div>
                <p className="text-xs text-gray-400 font-medium mb-2 flex items-center gap-1">
                  <span className="w-2 h-2 rounded-full bg-gray-300 inline-block" />
                  Autres modèles gratuits
                </p>
                <ModelList
                  models={otherModels}
                  selected={selectedModel}
                  onSelect={m => { setSelectedModel(m); setSaved(false); }}
                />
              </div>
            )}
          </section>
        )}

        {/* Modèle actuel (si pas encore rechargé) */}
        {models.length === 0 && selectedModel && (
          <section>
            <h2 className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">
              Modèle sélectionné
            </h2>
            <div className="px-3 py-2.5 bg-indigo-50 rounded-xl border border-indigo-100">
              <p className="text-sm text-indigo-700 font-mono">{selectedModel}</p>
            </div>
            <p className="text-xs text-gray-400 mt-1.5">Actualise les modèles pour changer de sélection.</p>
          </section>
        )}

        {/* Info */}
        <section className="bg-gray-50 rounded-xl p-4">
          <p className="text-xs text-gray-500 leading-relaxed">
            La clé API et le modèle sont stockés <strong>localement sur cet appareil</strong>.
            Utilise un modèle qui supporte l'audio (ex. Gemini Flash) pour la transcription.
            Les modèles <strong>:free</strong> sont gratuits mais peuvent avoir des limites de débit.
          </p>
        </section>
      </div>
    </div>
  );
}

function ModelList({
  models,
  selected,
  onSelect,
}: {
  models: OpenRouterModel[];
  selected: string;
  onSelect: (id: string) => void;
}) {
  return (
    <div className="space-y-1 max-h-64 overflow-y-auto rounded-xl border border-gray-100">
      {models.map(m => (
        <button
          key={m.id}
          onClick={() => onSelect(m.id)}
          className={`w-full text-left px-3 py-2.5 text-sm transition-colors ${
            selected === m.id
              ? 'bg-indigo-600 text-white'
              : 'hover:bg-gray-50 active:bg-gray-100 text-gray-700'
          }`}
        >
          <span className="font-medium block">{m.name}</span>
          <span className={`text-xs font-mono ${selected === m.id ? 'text-indigo-200' : 'text-gray-400'}`}>
            {m.id}
          </span>
        </button>
      ))}
    </div>
  );
}
