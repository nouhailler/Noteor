import { useState, useRef, useEffect } from 'react';
import { Mic, Square, Play, Pause, Trash2 } from 'lucide-react';
import type { Attachment } from '../types';

interface RecorderProps {
  onSave: (blob: Blob, filename: string) => void;
}

export function AudioRecorderButton({ onSave }: RecorderProps) {
  const [recording, setRecording] = useState(false);
  const [seconds, setSeconds] = useState(0);
  const mediaRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => () => { timerRef.current && clearInterval(timerRef.current); }, []);

  async function start() {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    const mimeType = MediaRecorder.isTypeSupported('audio/webm;codecs=opus')
      ? 'audio/webm;codecs=opus'
      : MediaRecorder.isTypeSupported('audio/mp4')
        ? 'audio/mp4'
        : '';
    const mr = new MediaRecorder(stream, mimeType ? { mimeType } : undefined);
    chunksRef.current = [];
    mr.ondataavailable = e => { if (e.data.size > 0) chunksRef.current.push(e.data); };
    mr.onstop = () => {
      stream.getTracks().forEach(t => t.stop());
      const ext = mimeType.includes('mp4') ? 'm4a' : 'webm';
      const blob = new Blob(chunksRef.current, { type: mimeType || 'audio/webm' });
      const filename = `audio_${new Date().toISOString().replace(/[:.]/g, '-')}.${ext}`;
      onSave(blob, filename);
    };
    mr.start();
    mediaRef.current = mr;
    setSeconds(0);
    setRecording(true);
    timerRef.current = setInterval(() => setSeconds(s => s + 1), 1000);
  }

  function stop() {
    mediaRef.current?.stop();
    timerRef.current && clearInterval(timerRef.current);
    setRecording(false);
  }

  const fmt = (s: number) => `${Math.floor(s / 60).toString().padStart(2, '0')}:${(s % 60).toString().padStart(2, '0')}`;

  if (recording) {
    return (
      <button
        onClick={stop}
        className="flex items-center gap-2 px-3 py-2 rounded-lg bg-red-100 text-red-700 active:bg-red-200"
      >
        <span className="w-2 h-2 rounded-full bg-red-500 animate-pulse" />
        <Square size={16} />
        <span className="text-sm font-mono">{fmt(seconds)}</span>
      </button>
    );
  }

  return (
    <button
      onClick={start}
      className="flex items-center gap-1.5 px-3 py-2 rounded-lg bg-gray-100 text-gray-700 active:bg-gray-200"
    >
      <Mic size={16} />
      <span className="text-sm">Audio</span>
    </button>
  );
}

interface PlayerProps {
  attachment: Attachment;
  onDelete: () => void;
}

export function AudioPlayer({ attachment, onDelete }: PlayerProps) {
  const [playing, setPlaying] = useState(false);
  const [url, setUrl] = useState<string | null>(null);
  const audioRef = useRef<HTMLAudioElement | null>(null);

  useEffect(() => {
    const objUrl = URL.createObjectURL(attachment.data);
    setUrl(objUrl);
    return () => URL.revokeObjectURL(objUrl);
  }, [attachment.data]);

  function toggle() {
    if (!audioRef.current) return;
    if (playing) { audioRef.current.pause(); setPlaying(false); }
    else { audioRef.current.play(); setPlaying(true); }
  }

  return (
    <div className="flex items-center gap-2 px-3 py-2 bg-indigo-50 rounded-lg border border-indigo-100">
      {url && (
        <audio
          ref={audioRef}
          src={url}
          onEnded={() => setPlaying(false)}
          className="hidden"
        />
      )}
      <button onClick={toggle} className="text-indigo-600 active:opacity-70">
        {playing ? <Pause size={18} /> : <Play size={18} />}
      </button>
      <span className="text-xs text-gray-500 truncate flex-1">{attachment.filename}</span>
      <button onClick={onDelete} className="text-gray-400 active:text-red-500">
        <Trash2 size={16} />
      </button>
    </div>
  );
}
