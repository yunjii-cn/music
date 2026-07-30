import React, { useState, useEffect, useRef, useCallback, useMemo } from 'react';
import { Sparkles, ChevronDown, ChevronUp, Settings2, Trash2, Music2, Sliders, Dices, Hash, RefreshCw, Plus, Upload, Play, Pause, Loader2, Bookmark, Save, X, FolderOpen, FolderPlus, History, Undo2, Redo2, FileText, Pencil } from 'lucide-react';
import { GenerationParams, Song } from '../types';
import { useAuth } from '../context/AuthContext';
import { useI18n } from '../context/I18nContext';
import { generateApi, presetsApi, Preset, projectsApi, Project, ProjectSnapshot, ProjectChangelog } from '../services/api';
import { MAIN_STYLES, SUB_STYLES, getStyleMeta } from '../data/genres';
import { EditableSlider } from './EditableSlider';
import { useUndoRedo } from '../hooks/useUndoRedo';

function HelpTip({ text }: { text: string }) {
  const [show, setShow] = useState(false);
  return (
    <span className="inline-flex items-center ml-0.5">
      <span
        className="relative inline-flex items-center cursor-help"
        onMouseEnter={() => setShow(true)}
        onMouseLeave={() => setShow(false)}
      >
        <svg className="w-3 h-3 text-zinc-400 dark:text-zinc-500" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5">
          <circle cx="8" cy="8" r="6.5" />
          <path d="M6.5 6a1.5 1.5 0 1 1 2 1.4V8.5" strokeLinecap="round" />
          <circle cx="8" cy="10.8" r="0.5" fill="currentColor" stroke="none" />
        </svg>
        {show && (
          <span className="absolute left-full top-1/2 -translate-y-1/2 ml-1.5 px-2 py-1 text-[10px] leading-tight text-white bg-zinc-800 dark:bg-zinc-700 rounded-md whitespace-normal w-max max-w-[200px] pointer-events-none z-50 shadow-lg">
            {text}
            <span className="absolute top-1/2 -translate-y-1/2 right-full border-4 border-transparent border-r-zinc-800 dark:border-r-zinc-700" />
          </span>
        )}
      </span>
    </span>
  );
}

interface ReferenceTrack {
  id: string;
  filename: string;
  storage_key: string;
  duration: number | null;
  file_size_bytes: number | null;
  tags: string[] | null;
  created_at: string;
  audio_url: string;
}

interface CreatePanelProps {
  onGenerate: (params: GenerationParams) => void;
  isGenerating: boolean;
  initialData?: { song: Song, timestamp: number } | null;
  createdSongs?: Song[];
  pendingAudioSelection?: { target: 'reference' | 'source'; url: string; title?: string } | null;
  onAudioSelectionApplied?: () => void;
}

const KEY_SIGNATURES = [
  '',
  'C major', 'C minor',
  'C# major', 'C# minor',
  'Db major', 'Db minor',
  'D major', 'D minor',
  'D# major', 'D# minor',
  'Eb major', 'Eb minor',
  'E major', 'E minor',
  'F major', 'F minor',
  'F# major', 'F# minor',
  'Gb major', 'Gb minor',
  'G major', 'G minor',
  'G# major', 'G# minor',
  'Ab major', 'Ab minor',
  'A major', 'A minor',
  'A# major', 'A# minor',
  'Bb major', 'Bb minor',
  'B major', 'B minor'
];

const TIME_SIGNATURES = ['', '2/4', '3/4', '4/4', '6/8'];

const VOCAL_LANGUAGE_KEYS = [
  { value: 'unknown', key: 'autoInstrumental' as const },
  { value: 'ar', key: 'vocalArabic' as const },
  { value: 'az', key: 'vocalAzerbaijani' as const },
  { value: 'bg', key: 'vocalBulgarian' as const },
  { value: 'bn', key: 'vocalBengali' as const },
  { value: 'ca', key: 'vocalCatalan' as const },
  { value: 'cs', key: 'vocalCzech' as const },
  { value: 'da', key: 'vocalDanish' as const },
  { value: 'de', key: 'vocalGerman' as const },
  { value: 'el', key: 'vocalGreek' as const },
  { value: 'en', key: 'vocalEnglish' as const },
  { value: 'es', key: 'vocalSpanish' as const },
  { value: 'fa', key: 'vocalPersian' as const },
  { value: 'fi', key: 'vocalFinnish' as const },
  { value: 'fr', key: 'vocalFrench' as const },
  { value: 'he', key: 'vocalHebrew' as const },
  { value: 'hi', key: 'vocalHindi' as const },
  { value: 'hr', key: 'vocalCroatian' as const },
  { value: 'ht', key: 'vocalHaitianCreole' as const },
  { value: 'hu', key: 'vocalHungarian' as const },
  { value: 'id', key: 'vocalIndonesian' as const },
  { value: 'is', key: 'vocalIcelandic' as const },
  { value: 'it', key: 'vocalItalian' as const },
  { value: 'ja', key: 'vocalJapanese' as const },
  { value: 'ko', key: 'vocalKorean' as const },
  { value: 'la', key: 'vocalLatin' as const },
  { value: 'lt', key: 'vocalLithuanian' as const },
  { value: 'ms', key: 'vocalMalay' as const },
  { value: 'ne', key: 'vocalNepali' as const },
  { value: 'nl', key: 'vocalDutch' as const },
  { value: 'no', key: 'vocalNorwegian' as const },
  { value: 'pa', key: 'vocalPunjabi' as const },
  { value: 'pl', key: 'vocalPolish' as const },
  { value: 'pt', key: 'vocalPortuguese' as const },
  { value: 'ro', key: 'vocalRomanian' as const },
  { value: 'ru', key: 'vocalRussian' as const },
  { value: 'sa', key: 'vocalSanskrit' as const },
  { value: 'sk', key: 'vocalSlovak' as const },
  { value: 'sr', key: 'vocalSerbian' as const },
  { value: 'sv', key: 'vocalSwedish' as const },
  { value: 'sw', key: 'vocalSwahili' as const },
  { value: 'ta', key: 'vocalTamil' as const },
  { value: 'te', key: 'vocalTelugu' as const },
  { value: 'th', key: 'vocalThai' as const },
  { value: 'tl', key: 'vocalTagalog' as const },
  { value: 'tr', key: 'vocalTurkish' as const },
  { value: 'uk', key: 'vocalUkrainian' as const },
  { value: 'ur', key: 'vocalUrdu' as const },
  { value: 'vi', key: 'vocalVietnamese' as const },
  { value: 'yue', key: 'vocalCantonese' as const },
  { value: 'zh', key: 'vocalChineseMandarin' as const },
];

export const CreatePanel: React.FC<CreatePanelProps> = ({
  onGenerate,
  isGenerating,
  initialData,
  createdSongs = [],
  pendingAudioSelection,
  onAudioSelectionApplied,
}) => {
  const { isAuthenticated, token, user } = useAuth();
  const { t } = useI18n();

  // Randomly select 6 music tags from MAIN_STYLES
  const [musicTags, setMusicTags] = useState<string[]>(() => {
    const shuffled = [...MAIN_STYLES].sort(() => Math.random() - 0.5);
    return shuffled.slice(0, 6);
  });

  // Function to refresh music tags
  const refreshMusicTags = useCallback(() => {
    const shuffled = [...MAIN_STYLES].sort(() => Math.random() - 0.5);
    setMusicTags(shuffled.slice(0, 6));
  }, []);

  // Mode
  const [customMode, setCustomMode] = useState(() => {
    const stored = localStorage.getItem('ace-customMode');
    return stored !== null ? stored === 'true' : true;
  });

  // Simple Mode
  const [songDescription, setSongDescription] = useState(() => {
    return localStorage.getItem('ace-songDescription') || '';
  });

  // Custom Mode
  const [lyrics, setLyrics] = useState(() => {
    return localStorage.getItem('ace-lyrics') || '';
  });
  const [style, setStyle] = useState(() => {
    return localStorage.getItem('ace-style') || '';
  });
  const [title, setTitle] = useState(() => {
    return localStorage.getItem('ace-title') || '';
  });

  // Common
  const [instrumental, setInstrumental] = useState(() => {
    const stored = localStorage.getItem('ace-instrumental');
    return stored !== null ? stored === 'true' : false;
  });
  const [vocalLanguage, setVocalLanguage] = useState(() => {
    return localStorage.getItem('ace-vocalLanguage') || 'en';
  });
  const [vocalGender, setVocalGender] = useState<'male' | 'female' | ''>(() => {
    const stored = localStorage.getItem('ace-vocalGender');
    return stored as 'male' | 'female' | '' || '';
  });

  // Music Parameters
  const [bpm, setBpm] = useState(() => {
    const stored = localStorage.getItem('ace-bpm');
    return stored ? Number(stored) : 0;
  });
  const [keyScale, setKeyScale] = useState(() => {
    return localStorage.getItem('ace-keyScale') || '';
  });
  const [timeSignature, setTimeSignature] = useState(() => {
    return localStorage.getItem('ace-timeSignature') || '';
  });

  // Advanced Settings
  const [showAdvanced, setShowAdvanced] = useState(() => {
    const stored = localStorage.getItem('ace-showAdvanced');
    return stored !== null ? stored === 'true' : false;
  });
  const [duration, setDuration] = useState(() => {
    const stored = localStorage.getItem('ace-duration');
    return stored ? Number(stored) : -1;
  });
  const [batchSize, setBatchSize] = useState(() => {
    const stored = localStorage.getItem('ace-batchSize');
    return stored ? Number(stored) : 1;
  });
  const [bulkCount, setBulkCount] = useState(() => {
    const stored = localStorage.getItem('ace-bulkCount');
    return stored ? Number(stored) : 1;
  });
  const [guidanceScale, setGuidanceScale] = useState(() => {
    const stored = localStorage.getItem('ace-guidanceScale');
    return stored ? Number(stored) : 9.0;
  });
  const [randomSeed, setRandomSeed] = useState(() => {
    const stored = localStorage.getItem('ace-randomSeed');
    return stored !== null ? stored === 'true' : true;
  });
  const [seed, setSeed] = useState(() => {
    const stored = localStorage.getItem('ace-seed');
    return stored ? Number(stored) : -1;
  });
  const [thinking, setThinking] = useState(() => {
    const stored = localStorage.getItem('ace-thinking');
    return stored !== null ? stored === 'true' : false; // Default false for GPU compatibility
  });
  const [audioFormat, setAudioFormat] = useState<'mp3' | 'flac'>(() => {
    const stored = localStorage.getItem('ace-audioFormat');
    return (stored as 'mp3' | 'flac') || 'mp3';
  });
  const [inferenceSteps, setInferenceSteps] = useState(() => {
    const stored = localStorage.getItem('ace-inferenceSteps');
    return stored ? Number(stored) : 12;
  });
  const [inferMethod, setInferMethod] = useState<'ode' | 'sde'>(() => {
    const stored = localStorage.getItem('ace-inferMethod');
    return (stored as 'ode' | 'sde') || 'ode';
  });
  const [lmBackend, setLmBackend] = useState<'pt' | 'vllm'>(() => {
    const stored = localStorage.getItem('ace-lmBackend');
    return (stored as 'pt' | 'vllm') || 'pt';
  });
  const [lmModel, setLmModel] = useState(() => {
    return localStorage.getItem('ace-lmModel') || 'acestep-5Hz-lm-0.6B';
  });
  const [shift, setShift] = useState(() => {
    const stored = localStorage.getItem('ace-shift');
    return stored ? Number(stored) : 3.0;
  });

  // LM Parameters (under Expert)
  const [showLmParams, setShowLmParams] = useState(() => {
    const stored = localStorage.getItem('ace-showLmParams');
    return stored !== null ? stored === 'true' : false;
  });
  const [lmTemperature, setLmTemperature] = useState(() => {
    const stored = localStorage.getItem('ace-lmTemperature');
    return stored ? Number(stored) : 0.8;
  });
  const [lmCfgScale, setLmCfgScale] = useState(() => {
    const stored = localStorage.getItem('ace-lmCfgScale');
    return stored ? Number(stored) : 2.2;
  });
  const [lmTopK, setLmTopK] = useState(() => {
    const stored = localStorage.getItem('ace-lmTopK');
    return stored ? Number(stored) : 0;
  });
  const [lmTopP, setLmTopP] = useState(() => {
    const stored = localStorage.getItem('ace-lmTopP');
    return stored ? Number(stored) : 0.92;
  });
  const [lmNegativePrompt, setLmNegativePrompt] = useState(() => {
    return localStorage.getItem('ace-lmNegativePrompt') || 'NO USER INPUT';
  });

  // Expert Parameters (now in Advanced section)
  const [referenceAudioUrl, setReferenceAudioUrl] = useState('');
  const [sourceAudioUrl, setSourceAudioUrl] = useState('');
  const [referenceAudioTitle, setReferenceAudioTitle] = useState('');
  const [sourceAudioTitle, setSourceAudioTitle] = useState('');
  const [audioCodes, setAudioCodes] = useState('');
  const [repaintingStart, setRepaintingStart] = useState(() => { const v = localStorage.getItem('ace-repaintingStart'); return v !== null ? parseFloat(v) : 0; });
  const [repaintingEnd, setRepaintingEnd] = useState(() => { const v = localStorage.getItem('ace-repaintingEnd'); return v !== null ? parseFloat(v) : -1; });
  const [instruction, setInstruction] = useState('Fill the audio semantic mask based on the given conditions:');
  const [audioCoverStrength, setAudioCoverStrength] = useState(() => { const v = localStorage.getItem('ace-audioCoverStrength'); return v !== null ? parseFloat(v) : 1.0; });
  const [coverNoiseStrength, setCoverNoiseStrength] = useState(() => { const v = localStorage.getItem('ace-coverNoiseStrength'); return v !== null ? parseFloat(v) : 0.3; });
  const [taskType, setTaskType] = useState(() => localStorage.getItem('ace-taskType') || 'text2music');
  const [useAdg, setUseAdg] = useState(() => localStorage.getItem('ace-useAdg') !== 'false');
  const [cfgIntervalStart, setCfgIntervalStart] = useState(() => { const v = localStorage.getItem('ace-cfgIntervalStart'); return v !== null ? parseFloat(v) : 0.0; });
  const [cfgIntervalEnd, setCfgIntervalEnd] = useState(() => { const v = localStorage.getItem('ace-cfgIntervalEnd'); return v !== null ? parseFloat(v) : 1.0; });
  const [customTimesteps, setCustomTimesteps] = useState(() => localStorage.getItem('ace-customTimesteps') || '');
  const [useCotMetas, setUseCotMetas] = useState(() => localStorage.getItem('ace-useCotMetas') !== 'false');
  const [useCotCaption, setUseCotCaption] = useState(() => localStorage.getItem('ace-useCotCaption') !== 'false');
  const [useCotLanguage, setUseCotLanguage] = useState(() => localStorage.getItem('ace-useCotLanguage') !== 'false');
  const [autogen, setAutogen] = useState(() => localStorage.getItem('ace-autogen') === 'true');
  const [constrainedDecodingDebug, setConstrainedDecodingDebug] = useState(() => localStorage.getItem('ace-constrainedDecodingDebug') === 'true');
  const [allowLmBatch, setAllowLmBatch] = useState(() => localStorage.getItem('ace-allowLmBatch') !== 'false');
  const [getScores, setGetScores] = useState(() => localStorage.getItem('ace-getScores') === 'true');
  const [getLrc, setGetLrc] = useState(() => localStorage.getItem('ace-getLrc') === 'true');
  const [scoreScale, setScoreScale] = useState(() => { const v = localStorage.getItem('ace-scoreScale'); return v !== null ? parseFloat(v) : 0.5; });
  const [lmBatchChunkSize, setLmBatchChunkSize] = useState(() => { const v = localStorage.getItem('ace-lmBatchChunkSize'); return v !== null ? parseInt(v, 10) : 8; });
  const [trackName, setTrackName] = useState('');
  const [completeTrackClasses, setCompleteTrackClasses] = useState('');
  const [isFormatCaption, setIsFormatCaption] = useState(() => localStorage.getItem('ace-isFormatCaption') === 'true');
  const [maxDurationWithLm, setMaxDurationWithLm] = useState(() => { const v = localStorage.getItem('ace-maxDurationWithLm'); return v !== null ? parseInt(v, 10) : 240; });
  const [maxDurationWithoutLm, setMaxDurationWithoutLm] = useState(() => { const v = localStorage.getItem('ace-maxDurationWithoutLm'); return v !== null ? parseInt(v, 10) : 240; });

  // LoRA Parameters
  const [showLoraPanel, setShowLoraPanel] = useState(() => {
    return localStorage.getItem('ace-loraEnabled') === 'true';
  });
  const [loraPath, setLoraPath] = useState(() => {
    return localStorage.getItem('ace-loraPath') || '';
  });
  const [loraLoaded, setLoraLoaded] = useState(false);
  const [loraAdapterInMemory, setLoraAdapterInMemory] = useState(false);
  const [loraScale, setLoraScale] = useState(() => {
    const saved = localStorage.getItem('ace-loraScale');
    return saved ? parseFloat(saved) : 1.0;
  });
  const [loraError, setLoraError] = useState<string | null>(null);
  const [isLoraLoading, setIsLoraLoading] = useState(false);
  const [availableLoraPaths, setAvailableLoraPaths] = useState<Array<{
    path: string;
    type: string;
    format: string;
    display_name: string;
    is_final?: boolean;
    priority?: number;
    metadata?: Record<string, any>;
    adapter_config?: Record<string, any> | null;
    training_hints?: {
      trigger_word?: string;
      tag_position?: string;
      model_variant?: string;
      recommended_shift?: number;
      recommended_steps?: number;
      dataset_name?: string;
      genre_ratio?: number;
      dataset_file?: string;
    };
  }>>([]);
  const [showLoraMenu, setShowLoraMenu] = useState(false);
  const [showCustomLoraInput, setShowCustomLoraInput] = useState(false);
  const [showAllLoraPaths, setShowAllLoraPaths] = useState(false);
  const [showLoraHints, setShowLoraHints] = useState(false);
  const loraMenuRef = useRef<HTMLDivElement>(null);

  const currentLoraHints = useMemo(() => {
    if (!loraPath || !availableLoraPaths.length) return null;
    const match = availableLoraPaths.find(p => p.path === loraPath);
    return match?.training_hints || null;
  }, [loraPath, availableLoraPaths]);

  const effectiveStyleForLora = useMemo(() => {
    if (!loraLoaded || !currentLoraHints?.trigger_word) return null;
    const tag = currentLoraHints.trigger_word;
    const pos = currentLoraHints.tag_position || 'prepend';
    return { tag, pos };
  }, [loraLoaded, currentLoraHints]);

  // Model selection
  const [selectedModel, setSelectedModel] = useState<string>(() => {
    return localStorage.getItem('ace-model') || 'acestep-v15-turbo';
  });
  const [showModelMenu, setShowModelMenu] = useState(false);
  const modelMenuRef = useRef<HTMLDivElement>(null);
  const projectDropdownRef = useRef<HTMLDivElement>(null);
  const previousModelRef = useRef<string>(selectedModel);
  
  // Available models fetched from backend
  const [fetchedModels, setFetchedModels] = useState<{ 
    name: string; 
    is_active: boolean; 
    is_preloaded: boolean; 
    is_installed: boolean;
    integrity_status?: 'complete' | 'incomplete' | 'missing';
    integrity_details?: {
      files_found: string[];
      files_missing: string[];
      total_size_mb: number;
      expected_size_mb: number;
      size_ok: boolean;
    };
  }[]>([]);

  // Presets state
  const [presets, setPresets] = useState<Preset[]>([]);
  const [showProjectDropdown, setShowProjectDropdown] = useState(false);
  const [showPresetMenu, setShowPresetMenu] = useState(false);
  const [selectedPresetId, setSelectedPresetId] = useState<string | null>(null);
  const [showSavePresetModal, setShowSavePresetModal] = useState(false);
  const [presetName, setPresetName] = useState('');
  const [presetDescription, setPresetDescription] = useState('');
  const [presetCategory, setPresetCategory] = useState('custom');
  const [presetLoading, setPresetLoading] = useState(false);

  // Projects state
  const [projects, setProjects] = useState<Project[]>([]);
  const [activeProject, setActiveProject] = useState<Project | null>(null);
  const [snapshots, setSnapshots] = useState<ProjectSnapshot[]>([]);
  const [showSaveProjectModal, setShowSaveProjectModal] = useState(false);
  const [projectName, setProjectName] = useState('');
  const [projectDescription, setProjectDescription] = useState('');
  const [projectLoading, setProjectLoading] = useState(false);
  const [showSnapshots, setShowSnapshots] = useState(false);
  const autoSaveTimerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  // Undo/Redo state
  const [canUndo, setCanUndo] = useState(false);
  const [canRedo, setCanRedo] = useState(false);
  const [undoAction, setUndoAction] = useState<string | null>(null);
  const [redoAction, setRedoAction] = useState<string | null>(null);

  // Changelog state
  const [changelogs, setChangelogs] = useState<ProjectChangelog[]>([]);
  const [showChangelog, setShowChangelog] = useState(false);
  const [changelogTotal, setChangelogTotal] = useState(0);

  // Project rename state
  const [showRenameModal, setShowRenameModal] = useState(false);
  const [renameValue, setRenameValue] = useState('');

  // Fallback model list when backend is unavailable
  const availableModels = useMemo(() => {
    return [
      { id: 'acestep-v15-base', name: 'acestep-v15-base' },
      { id: 'acestep-v15-sft', name: 'acestep-v15-sft' },
      { id: 'acestep-v15-turbo', name: 'acestep-v15-turbo' },
      { id: 'acestep-v15-turbo-shift1', name: 'acestep-v15-turbo-shift1' },
      { id: 'acestep-v15-turbo-shift3', name: 'acestep-v15-turbo-shift3' },
      { id: 'acestep-v15-turbo-continuous', name: 'acestep-v15-turbo-continuous' },
      { id: 'acestep-v15-xl-turbo', name: 'acestep-v15-xl-turbo' },
      { id: 'acestep-v15-xl-sft', name: 'acestep-v15-xl-sft' },
      { id: 'acestep-v15-xl-base', name: 'acestep-v15-xl-base' },
    ];
  }, []);

  const getModelDisplayName = (modelId: string): string => {
    const mapping: Record<string, string> = {
      'acestep-v15-base': '1.5B',
      'acestep-v15-sft': '1.5S',
      'acestep-v15-turbo-shift1': '1.5TS1',
      'acestep-v15-turbo-shift3': '1.5TS3',
      'acestep-v15-turbo-continuous': '1.5TC',
      'acestep-v15-turbo': '1.5T',
      'acestep-v15-xl-turbo': 'XL-T',
      'acestep-v15-xl-sft': 'XL-S',
      'acestep-v15-xl-base': 'XL-B',
    };
    return mapping[modelId] || modelId;
  };

  const isTurboModel = (modelId: string): boolean => {
    return modelId.includes('turbo');
  };

  const isXlModel = (modelId: string): boolean => {
    return modelId.startsWith('acestep-v15-xl');
  };

  // Genre selection state (cascading)
  const [selectedMainGenre, setSelectedMainGenre] = useState<string>('');
  const [selectedSubGenre, setSelectedSubGenre] = useState<string>('');

  // Filter sub-genres based on selected main genre
  const filteredSubGenres = useMemo(() => {
    if (!selectedMainGenre) return [];
    const mainLower = selectedMainGenre.toLowerCase().trim();
    return SUB_STYLES.filter(style => 
      style.toLowerCase().includes(mainLower)
    );
  }, [selectedMainGenre]);

  const [isUploadingReference, setIsUploadingReference] = useState(false);
  const [isUploadingSource, setIsUploadingSource] = useState(false);
  const [isTranscribingReference, setIsTranscribingReference] = useState(false);
  const transcribeAbortRef = useRef<AbortController | null>(null);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [isFormattingStyle, setIsFormattingStyle] = useState(false);
  const [isFormattingLyrics, setIsFormattingLyrics] = useState(false);
  const [isDraggingFile, setIsDraggingFile] = useState(false);
  const [dragKind, setDragKind] = useState<'file' | 'audio' | null>(null);
  const referenceInputRef = useRef<HTMLInputElement>(null);
  const sourceInputRef = useRef<HTMLInputElement>(null);
  const audioSectionRef = useRef<HTMLDivElement>(null);
  // 翻唱/音频转音频缺少源音频时，点击「创建」后高亮引导用户上传「内容参考」
  const [sourceHintActive, setSourceHintActive] = useState(false);
  const dragDepthRef = useRef(0);
  const [showAudioModal, setShowAudioModal] = useState(false);
  const [audioModalTarget, setAudioModalTarget] = useState<'reference' | 'source'>('reference');
  const [tempAudioUrl, setTempAudioUrl] = useState('');
  const [audioTab, setAudioTab] = useState<'reference' | 'source'>('reference');
  const referenceAudioRef = useRef<HTMLAudioElement>(null);
  const sourceAudioRef = useRef<HTMLAudioElement>(null);
  const [referencePlaying, setReferencePlaying] = useState(false);
  const [sourcePlaying, setSourcePlaying] = useState(false);
  const [referenceTime, setReferenceTime] = useState(0);
  const [sourceTime, setSourceTime] = useState(0);
  const [referenceDuration, setReferenceDuration] = useState(0);
  const [sourceDuration, setSourceDuration] = useState(0);

  // Reference tracks modal state
  const [referenceTracks, setReferenceTracks] = useState<ReferenceTrack[]>([]);
  const [isLoadingTracks, setIsLoadingTracks] = useState(false);
  const [playingTrackId, setPlayingTrackId] = useState<string | null>(null);
  const [playingTrackSource, setPlayingTrackSource] = useState<'uploads' | 'created' | null>(null);
  const modalAudioRef = useRef<HTMLAudioElement>(null);
  const [modalTrackTime, setModalTrackTime] = useState(0);
  const [modalTrackDuration, setModalTrackDuration] = useState(0);
  const [libraryTab, setLibraryTab] = useState<'uploads' | 'created'>('uploads');

  const createdTrackOptions = useMemo(() => {
    return createdSongs
      .filter(song => !song.isGenerating)
      .filter(song => (user ? song.userId === user.id : true))
      .filter(song => Boolean(song.audioUrl))
      .map(song => ({
        id: song.id,
        title: song.title || 'Untitled',
        audio_url: song.audioUrl!,
        duration: song.duration,
      }));
  }, [createdSongs, user]);

  const getAudioLabel = (url: string) => {
    try {
      const parsed = new URL(url);
      const name = decodeURIComponent(parsed.pathname.split('/').pop() || parsed.hostname);
      return name.replace(/\.[^/.]+$/, '') || name;
    } catch {
      const parts = url.split('/');
      const name = decodeURIComponent(parts[parts.length - 1] || url);
      return name.replace(/\.[^/.]+$/, '') || name;
    }
  };

  // Resize Logic
  const [lyricsHeight, setLyricsHeight] = useState(() => {
    const saved = localStorage.getItem('acestep_lyrics_height');
    return saved ? parseInt(saved, 10) : 144;
  });
  const [styleHeight, setStyleHeight] = useState(() => {
    const saved = localStorage.getItem('acestep_style_height');
    return saved ? parseInt(saved, 10) : 80;
  });
  const [isResizing, setIsResizing] = useState(false);
  const [resizingTarget, setResizingTarget] = useState<'lyrics' | 'style'>('lyrics');
  const lyricsRef = useRef<HTMLDivElement>(null);
  const styleRef = useRef<HTMLDivElement>(null);
  const lyricsTextareaRef = useRef<HTMLTextAreaElement>(null);
  const styleTextareaRef = useRef<HTMLTextAreaElement>(null);
  const [lyricsExpanded, setLyricsExpanded] = useState(false);
  const [styleExpanded, setStyleExpanded] = useState(false);
  const MAX_HEIGHT = 1000;
  const MIN_LYRICS_HEIGHT = 96;
  const MIN_STYLE_HEIGHT = 80;


  // Close model menu when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (modelMenuRef.current && !modelMenuRef.current.contains(event.target as Node)) {
        setShowModelMenu(false);
      }
    };

    if (showModelMenu) {
      document.addEventListener('mousedown', handleClickOutside);
      return () => document.removeEventListener('mousedown', handleClickOutside);
    }
  }, [showModelMenu]);

  useEffect(() => {
    if (showLoraMenu) {
      const handleClickOutside = (e: MouseEvent) => {
        if (loraMenuRef.current && !loraMenuRef.current.contains(e.target as Node)) {
          setShowLoraMenu(false);
        }
      };
      document.addEventListener('mousedown', handleClickOutside);
      return () => document.removeEventListener('mousedown', handleClickOutside);
    }
  }, [showLoraMenu]);

  useEffect(() => {
    if (showProjectDropdown) {
      const handleClickOutside = (e: MouseEvent) => {
        if (projectDropdownRef.current && !projectDropdownRef.current.contains(e.target as Node)) {
          setShowProjectDropdown(false);
        }
      };
      document.addEventListener('mousedown', handleClickOutside);
      return () => document.removeEventListener('mousedown', handleClickOutside);
    }
  }, [showProjectDropdown]);

  useEffect(() => {
    if (token) {
      presetsApi.getPresets(token).then(result => {
        setPresets(result.presets);
      }).catch(() => {});
      projectsApi.getProjects(token).then(result => {
        setProjects(result.projects);
        const active = result.projects.find((p: Project) => p.is_active);
        if (active) {
          setActiveProject(active);
        } else if (result.default_project) {
          setActiveProject(result.default_project);
          projectsApi.updateProject(result.default_project.id, {
            params: getCurrentParamsRef.current(),
            changelog_label: 'init',
          }, token).then(updateResult => {
            setActiveProject(updateResult.project);
            setProjects(prev => prev.map(p => p.id === updateResult.project.id ? updateResult.project : p));
          }).catch(() => {});
        }
      }).catch(() => {});
    }
  }, [token]);

  const getCurrentParams = useCallback(() => {
    return {
      customMode,
      songDescription,
      lyrics,
      style,
      title,
      instrumental,
      vocalLanguage,
      vocalGender,
      bpm,
      keyScale,
      timeSignature,
      duration,
      inferenceSteps,
      guidanceScale,
      batchSize,
      randomSeed,
      seed,
      thinking,
      audioFormat,
      inferMethod,
      lmBackend,
      lmModel,
      shift,
      lmTemperature,
      lmCfgScale,
      lmTopK,
      lmTopP,
      lmNegativePrompt,
      taskType,
      audioCoverStrength,
      coverNoiseStrength,
      useAdg,
      cfgIntervalStart,
      cfgIntervalEnd,
      customTimesteps,
      useCotMetas,
      useCotCaption,
      useCotLanguage,
      autogen,
      allowLmBatch,
      getScores,
      getLrc,
      scoreScale,
      lmBatchChunkSize,
      isFormatCaption,
      ditModel: selectedModel,
      loraEnabled: loraLoaded,
      loraPath,
      loraScale,
    };
  }, [customMode, songDescription, lyrics, style, title, instrumental, vocalLanguage, vocalGender, bpm, keyScale, timeSignature, duration, inferenceSteps, guidanceScale, batchSize, randomSeed, seed, thinking, audioFormat, inferMethod, lmBackend, lmModel, shift, lmTemperature, lmCfgScale, lmTopK, lmTopP, lmNegativePrompt, taskType, audioCoverStrength, coverNoiseStrength, useAdg, cfgIntervalStart, cfgIntervalEnd, customTimesteps, useCotMetas, useCotCaption, useCotLanguage, autogen, allowLmBatch, getScores, getLrc, scoreScale, lmBatchChunkSize, isFormatCaption, selectedModel, loraLoaded, loraPath, loraScale]);

  const getCurrentParamsRef = useRef(getCurrentParams);
  getCurrentParamsRef.current = getCurrentParams;

  const presetCheckParams = useCallback(() => {
    return {
      customMode,
      songDescription,
      lyrics,
      style,
      title,
      instrumental,
      vocalLanguage,
      vocalGender,
      bpm,
      keyScale,
      timeSignature,
      duration,
      inferenceSteps,
      guidanceScale,
      batchSize,
      randomSeed,
      seed,
      thinking,
      audioFormat,
      inferMethod,
      lmBackend,
      lmModel,
      shift,
      lmTemperature,
      lmCfgScale,
      lmTopK,
      lmTopP,
      lmNegativePrompt,
      taskType,
      audioCoverStrength,
      coverNoiseStrength,
      useAdg,
      cfgIntervalStart,
      cfgIntervalEnd,
      customTimesteps,
      useCotMetas,
      useCotCaption,
      useCotLanguage,
      autogen,
      allowLmBatch,
      getScores,
      getLrc,
      scoreScale,
      lmBatchChunkSize,
      isFormatCaption,
      ditModel: selectedModel,
    };
  }, [customMode, songDescription, lyrics, style, title, instrumental, vocalLanguage, vocalGender, bpm, keyScale, timeSignature, duration, inferenceSteps, guidanceScale, batchSize, randomSeed, seed, thinking, audioFormat, inferMethod, lmBackend, lmModel, shift, lmTemperature, lmCfgScale, lmTopK, lmTopP, lmNegativePrompt, taskType, audioCoverStrength, coverNoiseStrength, useAdg, cfgIntervalStart, cfgIntervalEnd, customTimesteps, useCotMetas, useCotCaption, useCotLanguage, autogen, allowLmBatch, getScores, getLrc, scoreScale, lmBatchChunkSize, isFormatCaption, selectedModel]);

  useEffect(() => {
    if (!selectedPresetId || presets.length === 0) return;
    const selectedPreset = presets.find(p => p.id === selectedPresetId);
    if (!selectedPreset) { setSelectedPresetId(null); return; }
    const current = presetCheckParams();
    const presetParams = selectedPreset.params;
    const presetKeys = Object.keys(presetParams);
    const changed = presetKeys.some(key => {
      if (key === 'loraEnabled' || key === 'loraPath' || key === 'loraScale') return false;
      return JSON.stringify(current[key as keyof typeof current]) !== JSON.stringify(presetParams[key]);
    });
    if (changed) setSelectedPresetId(null);
  }, [presetCheckParams, selectedPresetId, presets]);

  const refreshUndoRedoState = useCallback(async () => {
    if (!activeProject?.id || !token) {
      setCanUndo(false);
      setCanRedo(false);
      setUndoAction(null);
      setRedoAction(null);
      return;
    }
    try {
      const result = await projectsApi.getChangelogs(activeProject.id, token, { limit: 1, offset: 0 });
      setCanUndo(result.total > 0);
      setUndoAction(result.changelogs.length > 0 ? result.changelogs[0].action : null);
    } catch {
      setCanUndo(false);
      setUndoAction(null);
    }
  }, [activeProject?.id, token]);

  const applyPreset = useCallback((preset: Preset) => {
    isApplyingProjectRef.current = true;
    const p = preset.params;
    if (p.customMode !== undefined) { setCustomMode(p.customMode); localStorage.setItem('ace-customMode', String(p.customMode)); }
    if (p.instrumental !== undefined) { setInstrumental(p.instrumental); localStorage.setItem('ace-instrumental', String(p.instrumental)); }
    if (p.vocalLanguage !== undefined) { setVocalLanguage(p.vocalLanguage); localStorage.setItem('ace-vocalLanguage', p.vocalLanguage); }
    if (p.vocalGender !== undefined) { setVocalGender(p.vocalGender); localStorage.setItem('ace-vocalGender', p.vocalGender); }
    if (p.bpm !== undefined) { setBpm(p.bpm); localStorage.setItem('ace-bpm', String(p.bpm)); }
    if (p.duration !== undefined) { setDuration(p.duration); localStorage.setItem('ace-duration', String(p.duration)); }
    if (p.inferenceSteps !== undefined) { setInferenceSteps(p.inferenceSteps); localStorage.setItem('ace-inferenceSteps', String(p.inferenceSteps)); }
    if (p.guidanceScale !== undefined) { setGuidanceScale(p.guidanceScale); localStorage.setItem('ace-guidanceScale', String(p.guidanceScale)); }
    if (p.randomSeed !== undefined) { setRandomSeed(p.randomSeed); localStorage.setItem('ace-randomSeed', String(p.randomSeed)); }
    if (p.audioFormat !== undefined) { setAudioFormat(p.audioFormat); localStorage.setItem('ace-audioFormat', p.audioFormat); }
    if (p.inferMethod !== undefined) { setInferMethod(p.inferMethod); localStorage.setItem('ace-inferMethod', p.inferMethod); }
    if (p.shift !== undefined) { setShift(p.shift); localStorage.setItem('ace-shift', String(p.shift)); }
    if (p.useAdg !== undefined) { setUseAdg(p.useAdg); localStorage.setItem('ace-useAdg', String(p.useAdg)); }
    if (p.taskType !== undefined) { setTaskType(p.taskType); localStorage.setItem('ace-taskType', p.taskType); }
    if (p.audioCoverStrength !== undefined) { setAudioCoverStrength(p.audioCoverStrength); localStorage.setItem('ace-audioCoverStrength', String(p.audioCoverStrength)); }
    if (p.coverNoiseStrength !== undefined) { setCoverNoiseStrength(p.coverNoiseStrength); localStorage.setItem('ace-coverNoiseStrength', String(p.coverNoiseStrength)); }
    if (p.ditModel !== undefined) { setSelectedModel(p.ditModel); localStorage.setItem('ace-model', p.ditModel); }
    if (p.lmModel !== undefined) { setLmModel(p.lmModel); localStorage.setItem('ace-lmModel', p.lmModel); }
    if (p.lmBackend !== undefined) { setLmBackend(p.lmBackend); localStorage.setItem('ace-lmBackend', p.lmBackend); }
    if (p.lmTemperature !== undefined) { setLmTemperature(p.lmTemperature); localStorage.setItem('ace-lmTemperature', String(p.lmTemperature)); }
    if (p.lmCfgScale !== undefined) { setLmCfgScale(p.lmCfgScale); localStorage.setItem('ace-lmCfgScale', String(p.lmCfgScale)); }
    if (p.lmTopK !== undefined) { setLmTopK(p.lmTopK); localStorage.setItem('ace-lmTopK', String(p.lmTopK)); }
    if (p.lmTopP !== undefined) { setLmTopP(p.lmTopP); localStorage.setItem('ace-lmTopP', String(p.lmTopP)); }
    if (p.lmNegativePrompt !== undefined) { setLmNegativePrompt(p.lmNegativePrompt); localStorage.setItem('ace-lmNegativePrompt', p.lmNegativePrompt); }
    if (p.cfgIntervalStart !== undefined) { setCfgIntervalStart(p.cfgIntervalStart); localStorage.setItem('ace-cfgIntervalStart', String(p.cfgIntervalStart)); }
    if (p.cfgIntervalEnd !== undefined) { setCfgIntervalEnd(p.cfgIntervalEnd); localStorage.setItem('ace-cfgIntervalEnd', String(p.cfgIntervalEnd)); }
    if (p.customTimesteps !== undefined) { setCustomTimesteps(p.customTimesteps); localStorage.setItem('ace-customTimesteps', p.customTimesteps); }
    if (p.useCotMetas !== undefined) { setUseCotMetas(p.useCotMetas); localStorage.setItem('ace-useCotMetas', String(p.useCotMetas)); }
    if (p.useCotCaption !== undefined) { setUseCotCaption(p.useCotCaption); localStorage.setItem('ace-useCotCaption', String(p.useCotCaption)); }
    if (p.useCotLanguage !== undefined) { setUseCotLanguage(p.useCotLanguage); localStorage.setItem('ace-useCotLanguage', String(p.useCotLanguage)); }
    if (p.autogen !== undefined) { setAutogen(p.autogen); localStorage.setItem('ace-autogen', String(p.autogen)); }
    if (p.allowLmBatch !== undefined) { setAllowLmBatch(p.allowLmBatch); localStorage.setItem('ace-allowLmBatch', String(p.allowLmBatch)); }
    if (p.getScores !== undefined) { setGetScores(p.getScores); localStorage.setItem('ace-getScores', String(p.getScores)); }
    if (p.getLrc !== undefined) { setGetLrc(p.getLrc); localStorage.setItem('ace-getLrc', String(p.getLrc)); }
    if (p.scoreScale !== undefined) { setScoreScale(p.scoreScale); localStorage.setItem('ace-scoreScale', String(p.scoreScale)); }
    if (p.lmBatchChunkSize !== undefined) { setLmBatchChunkSize(p.lmBatchChunkSize); localStorage.setItem('ace-lmBatchChunkSize', String(p.lmBatchChunkSize)); }
    if (p.isFormatCaption !== undefined) { setIsFormatCaption(p.isFormatCaption); localStorage.setItem('ace-isFormatCaption', String(p.isFormatCaption)); }
    if (p.loraEnabled === true) {
      setShowLoraPanel(true);
      localStorage.setItem('ace-loraEnabled', 'true');
      if (loraAdapterInMemory) {
        setLoraLoaded(true);
        generateApi.toggleLora({ use_lora: true }, token || '').catch(() => {});
      } else if (loraPath.trim()) {
        setIsLoraLoading(true);
        generateApi.loadLora({ lora_path: loraPath }, token || '').then(() => {
          setLoraAdapterInMemory(true);
          return generateApi.toggleLora({ use_lora: true }, token || '');
        }).then(() => {
          setLoraLoaded(true);
        }).catch((err) => {
          const message = err instanceof Error ? err.message : 'LoRA load failed';
          setLoraError(message);
        }).finally(() => {
          setIsLoraLoading(false);
        });
      }
    } else if (p.loraEnabled === false) {
      setLoraLoaded(false);
      setShowLoraPanel(false);
      localStorage.setItem('ace-loraEnabled', 'false');
      if (loraAdapterInMemory) {
        generateApi.toggleLora({ use_lora: false }, token || '').catch(() => {});
      }
    }
    if (p.loraScale !== undefined) { setLoraScale(p.loraScale); localStorage.setItem('ace-loraScale', String(p.loraScale)); }
    setSelectedPresetId(preset.id);
    setShowPresetMenu(false);

    setTimeout(() => { isApplyingProjectRef.current = false; }, 100);

    setTimeout(() => {
      if (activeProject?.id && token) {
        projectsApi.updateProject(activeProject.id, {
          params: getCurrentParamsRef.current(),
          changelog_label: `preset:${preset.name}`,
        }, token).then(result => {
          setActiveProject(result.project);
          refreshUndoRedoState();
        }).catch(() => {});
      }
    }, 100);
  }, [activeProject?.id, token, refreshUndoRedoState, loraAdapterInMemory, loraPath]);

  const isApplyingProjectRef = useRef(false);

  const applyProject = useCallback((project: Project) => {
    isApplyingProjectRef.current = true;
    const p = project.params;
    if (p.customMode !== undefined) { setCustomMode(p.customMode); localStorage.setItem('ace-customMode', String(p.customMode)); }
    if (p.songDescription !== undefined) { setSongDescription(p.songDescription); localStorage.setItem('ace-songDescription', p.songDescription); }
    if (p.lyrics !== undefined) { setLyrics(p.lyrics); localStorage.setItem('ace-lyrics', p.lyrics); }
    if (p.style !== undefined) { setStyle(p.style); localStorage.setItem('ace-style', p.style); }
    if (p.title !== undefined) { setTitle(p.title); localStorage.setItem('ace-title', p.title); }
    if (p.instrumental !== undefined) { setInstrumental(p.instrumental); localStorage.setItem('ace-instrumental', String(p.instrumental)); }
    if (p.vocalLanguage !== undefined) { setVocalLanguage(p.vocalLanguage); localStorage.setItem('ace-vocalLanguage', p.vocalLanguage); }
    if (p.vocalGender !== undefined) { setVocalGender(p.vocalGender); localStorage.setItem('ace-vocalGender', p.vocalGender); }
    if (p.bpm !== undefined) { setBpm(p.bpm); localStorage.setItem('ace-bpm', String(p.bpm)); }
    if (p.keyScale !== undefined) { setKeyScale(p.keyScale); localStorage.setItem('ace-keyScale', p.keyScale); }
    if (p.timeSignature !== undefined) { setTimeSignature(p.timeSignature); localStorage.setItem('ace-timeSignature', p.timeSignature); }
    if (p.duration !== undefined) { setDuration(p.duration); localStorage.setItem('ace-duration', String(p.duration)); }
    if (p.inferenceSteps !== undefined) { setInferenceSteps(p.inferenceSteps); localStorage.setItem('ace-inferenceSteps', String(p.inferenceSteps)); }
    if (p.guidanceScale !== undefined) { setGuidanceScale(p.guidanceScale); localStorage.setItem('ace-guidanceScale', String(p.guidanceScale)); }
    if (p.batchSize !== undefined) { setBatchSize(p.batchSize); localStorage.setItem('ace-batchSize', String(p.batchSize)); }
    if (p.randomSeed !== undefined) { setRandomSeed(p.randomSeed); localStorage.setItem('ace-randomSeed', String(p.randomSeed)); }
    if (p.seed !== undefined) { setSeed(p.seed); localStorage.setItem('ace-seed', String(p.seed)); }
    if (p.thinking !== undefined) { setThinking(p.thinking); localStorage.setItem('ace-thinking', String(p.thinking)); }
    if (p.audioFormat !== undefined) { setAudioFormat(p.audioFormat); localStorage.setItem('ace-audioFormat', p.audioFormat); }
    if (p.inferMethod !== undefined) { setInferMethod(p.inferMethod); localStorage.setItem('ace-inferMethod', p.inferMethod); }
    if (p.lmBackend !== undefined) { setLmBackend(p.lmBackend); localStorage.setItem('ace-lmBackend', p.lmBackend); }
    if (p.lmModel !== undefined) { setLmModel(p.lmModel); localStorage.setItem('ace-lmModel', p.lmModel); }
    if (p.shift !== undefined) { setShift(p.shift); localStorage.setItem('ace-shift', String(p.shift)); }
    if (p.lmTemperature !== undefined) { setLmTemperature(p.lmTemperature); localStorage.setItem('ace-lmTemperature', String(p.lmTemperature)); }
    if (p.lmCfgScale !== undefined) { setLmCfgScale(p.lmCfgScale); localStorage.setItem('ace-lmCfgScale', String(p.lmCfgScale)); }
    if (p.lmTopK !== undefined) { setLmTopK(p.lmTopK); localStorage.setItem('ace-lmTopK', String(p.lmTopK)); }
    if (p.lmTopP !== undefined) { setLmTopP(p.lmTopP); localStorage.setItem('ace-lmTopP', String(p.lmTopP)); }
    if (p.lmNegativePrompt !== undefined) { setLmNegativePrompt(p.lmNegativePrompt); localStorage.setItem('ace-lmNegativePrompt', p.lmNegativePrompt); }
    if (p.taskType !== undefined) { setTaskType(p.taskType); localStorage.setItem('ace-taskType', p.taskType); }
    if (p.audioCoverStrength !== undefined) { setAudioCoverStrength(p.audioCoverStrength); localStorage.setItem('ace-audioCoverStrength', String(p.audioCoverStrength)); }
    if (p.coverNoiseStrength !== undefined) { setCoverNoiseStrength(p.coverNoiseStrength); localStorage.setItem('ace-coverNoiseStrength', String(p.coverNoiseStrength)); }
    if (p.useAdg !== undefined) { setUseAdg(p.useAdg); localStorage.setItem('ace-useAdg', String(p.useAdg)); }
    if (p.cfgIntervalStart !== undefined) { setCfgIntervalStart(p.cfgIntervalStart); localStorage.setItem('ace-cfgIntervalStart', String(p.cfgIntervalStart)); }
    if (p.cfgIntervalEnd !== undefined) { setCfgIntervalEnd(p.cfgIntervalEnd); localStorage.setItem('ace-cfgIntervalEnd', String(p.cfgIntervalEnd)); }
    if (p.customTimesteps !== undefined) { setCustomTimesteps(p.customTimesteps); localStorage.setItem('ace-customTimesteps', p.customTimesteps); }
    if (p.useCotMetas !== undefined) { setUseCotMetas(p.useCotMetas); localStorage.setItem('ace-useCotMetas', String(p.useCotMetas)); }
    if (p.useCotCaption !== undefined) { setUseCotCaption(p.useCotCaption); localStorage.setItem('ace-useCotCaption', String(p.useCotCaption)); }
    if (p.useCotLanguage !== undefined) { setUseCotLanguage(p.useCotLanguage); localStorage.setItem('ace-useCotLanguage', String(p.useCotLanguage)); }
    if (p.autogen !== undefined) { setAutogen(p.autogen); localStorage.setItem('ace-autogen', String(p.autogen)); }
    if (p.allowLmBatch !== undefined) { setAllowLmBatch(p.allowLmBatch); localStorage.setItem('ace-allowLmBatch', String(p.allowLmBatch)); }
    if (p.getScores !== undefined) { setGetScores(p.getScores); localStorage.setItem('ace-getScores', String(p.getScores)); }
    if (p.getLrc !== undefined) { setGetLrc(p.getLrc); localStorage.setItem('ace-getLrc', String(p.getLrc)); }
    if (p.scoreScale !== undefined) { setScoreScale(p.scoreScale); localStorage.setItem('ace-scoreScale', String(p.scoreScale)); }
    if (p.lmBatchChunkSize !== undefined) { setLmBatchChunkSize(p.lmBatchChunkSize); localStorage.setItem('ace-lmBatchChunkSize', String(p.lmBatchChunkSize)); }
    if (p.isFormatCaption !== undefined) { setIsFormatCaption(p.isFormatCaption); localStorage.setItem('ace-isFormatCaption', String(p.isFormatCaption)); }
    if (p.ditModel !== undefined) { setSelectedModel(p.ditModel); localStorage.setItem('ace-model', p.ditModel); }
    if (p.loraPath !== undefined) { setLoraPath(p.loraPath); localStorage.setItem('ace-loraPath', p.loraPath); }
    if (p.loraScale !== undefined) { setLoraScale(p.loraScale); localStorage.setItem('ace-loraScale', String(p.loraScale)); }
    if (p.loraEnabled !== undefined) { setShowLoraPanel(p.loraEnabled); localStorage.setItem('ace-loraEnabled', String(p.loraEnabled)); }
    setShowPresetMenu(false);
    setTimeout(() => { isApplyingProjectRef.current = false; }, 0);
  }, []);

  const handleUndo = useCallback(async () => {
    if (!activeProject?.id || !token || !canUndo) return;
    try {
      const result = await projectsApi.undoProject(activeProject.id, token);
      applyProject(result.project);
      setActiveProject(result.project);
      await refreshUndoRedoState();
    } catch (error) {
      console.error('Undo failed:', error);
    }
  }, [activeProject?.id, token, canUndo, applyProject, refreshUndoRedoState]);

  const redoStackRef = useRef<{ params: Record<string, any>; action: string }[]>([]);

  const handleRedo = useCallback(async () => {
    if (!activeProject?.id || !token || redoStackRef.current.length === 0) return;
    const redoItem = redoStackRef.current.pop()!;
    try {
      const result = await projectsApi.updateProject(activeProject.id, {
        params: redoItem.params,
        changelog_label: 'redo',
      }, token);
      applyProject(result.project);
      setActiveProject(result.project);
      setCanRedo(redoStackRef.current.length > 0);
      setRedoAction(redoStackRef.current.length > 0 ? redoStackRef.current[redoStackRef.current.length - 1].action : null);
      await refreshUndoRedoState();
    } catch (error) {
      console.error('Redo failed:', error);
      redoStackRef.current.push(redoItem);
    }
  }, [activeProject?.id, token, applyProject, refreshUndoRedoState]);

  const saveProjectParams = useCallback(async (label?: string) => {
    if (!activeProject?.id || !token) return;
    try {
      const result = await projectsApi.updateProject(activeProject.id, {
        params: getCurrentParamsRef.current(),
        changelog_label: label,
      }, token);
      setActiveProject(result.project);
      redoStackRef.current = [];
      setCanRedo(false);
      setRedoAction(null);
      await refreshUndoRedoState();
    } catch (error) {
      console.error('Save project params failed:', error);
    }
  }, [activeProject?.id, token, refreshUndoRedoState]);

  const saveProjectParamsRef = useRef(saveProjectParams);
  saveProjectParamsRef.current = saveProjectParams;

  useEffect(() => {
    refreshUndoRedoState();
  }, [refreshUndoRedoState]);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key === 'z' && !e.shiftKey) {
        e.preventDefault();
        handleUndo();
      }
      if ((e.ctrlKey || e.metaKey) && (e.key === 'y' || (e.key === 'z' && e.shiftKey))) {
        e.preventDefault();
        handleRedo();
      }
    };
    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [handleUndo, handleRedo]);

  useEffect(() => {
    if (activeProject && token && activeProject.auto_save_enabled) {
      if (autoSaveTimerRef.current) clearInterval(autoSaveTimerRef.current);
      const intervalMs = (activeProject.auto_save_interval || 60) * 1000;
      autoSaveTimerRef.current = setInterval(async () => {
        try {
          await saveProjectParamsRef.current('auto-save');
        } catch {}
      }, intervalMs);
      return () => {
        if (autoSaveTimerRef.current) clearInterval(autoSaveTimerRef.current);
      };
    } else {
      if (autoSaveTimerRef.current) {
        clearInterval(autoSaveTimerRef.current);
        autoSaveTimerRef.current = null;
      }
    }
  }, [activeProject?.id, activeProject?.auto_save_enabled, activeProject?.auto_save_interval, token]);

  useEffect(() => {
    const fetchLoraPaths = async () => {
      try {
        const result = await generateApi.discoverLoraPaths();
        if (result?.paths) {
          setAvailableLoraPaths(result.paths);
          if (!loraPath && result.paths.length > 0) {
            const finalPath = result.paths.find((p: any) => p.is_final);
            setLoraPath(finalPath ? finalPath.path : result.paths[0].path);
          }
        }
      } catch {}
    };
    fetchLoraPaths();
    const interval = setInterval(fetchLoraPaths, 30000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    if (loraPath) {
      localStorage.setItem('ace-loraPath', loraPath);
    }
  }, [loraPath]);

  useEffect(() => {
    localStorage.setItem('ace-loraScale', loraScale.toString());
  }, [loraScale]);

  useEffect(() => {
    let failCount = 0;
    let timerId: ReturnType<typeof setTimeout>;
    let isSyncing = false;
    
    const syncLoraStatus = async () => {
      if (isGenerating || isSyncing) {
        if (!timerId) {
          timerId = setTimeout(syncLoraStatus, 5000);
        }
        return;
      }
      
      isSyncing = true;
      try {
        const status = await generateApi.getLoraStatus(token || '');
        failCount = 0;
        if (status?.lora_loaded) {
          setLoraAdapterInMemory(true);
          if (status.use_lora) {
            setLoraLoaded(true);
          } else {
            setLoraLoaded(false);
          }
          if (status.lora_scale !== undefined) {
            setLoraScale(status.lora_scale);
          }
        } else {
          setLoraLoaded(false);
          setLoraAdapterInMemory(false);
        }
      } catch {
        failCount++;
      } finally {
        isSyncing = false;
      }
      
      const delay = failCount > 3 ? 60000 : 15000;
      timerId = setTimeout(syncLoraStatus, delay);
    };
    
    syncLoraStatus();
    return () => {
      if (timerId) clearTimeout(timerId);
    };
  }, [token, isGenerating]);

  // Track model changes for reference (no auto-unload)
  useEffect(() => {
    previousModelRef.current = selectedModel;
  }, [selectedModel]);

  // LoRA API handlers
  const handleLoraToggle = async () => {
    if (!token) {
      setLoraError('Please sign in to use LoRA');
      return;
    }

    if (loraLoaded) {
      setIsLoraLoading(true);
      setLoraError(null);
      try {
        await generateApi.toggleLora({ use_lora: false }, token);
        setLoraLoaded(false);
        localStorage.setItem('ace-loraEnabled', 'false');
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Failed to disable LoRA';
        setLoraError(message);
        console.error('Toggle off error:', err);
        setLoraLoaded(false);
        localStorage.setItem('ace-loraEnabled', 'false');
      } finally {
        setIsLoraLoading(false);
      }
    } else {
      if (loraAdapterInMemory) {
        setIsLoraLoading(true);
        setLoraError(null);
        try {
          await generateApi.toggleLora({ use_lora: true }, token);
          setLoraLoaded(true);
          localStorage.setItem('ace-loraEnabled', 'true');
        } catch (err) {
          const message = err instanceof Error ? err.message : 'Failed to enable LoRA';
          setLoraError(message);
          console.error('Toggle on error:', err);
        } finally {
          setIsLoraLoading(false);
        }
      } else {
        if (!loraPath.trim()) {
          setLoraError('Please enter a LoRA path');
          setShowLoraPanel(true);
          localStorage.setItem('ace-loraEnabled', 'true');
          return;
        }
        setIsLoraLoading(true);
        setLoraError(null);
        try {
          const result = await generateApi.loadLora({ lora_path: loraPath }, token);
          setLoraAdapterInMemory(true);
          await generateApi.toggleLora({ use_lora: true }, token);
          setLoraLoaded(true);
          setShowLoraPanel(true);
          localStorage.setItem('ace-loraEnabled', 'true');
          console.log('LoRA loaded:', result?.message);
        } catch (err) {
          const message = err instanceof Error ? err.message : 'LoRA load failed';
          setLoraError(message);
          console.error('LoRA error:', err);
        } finally {
          setIsLoraLoading(false);
        }
      }
    }
  };

  const handleLoraScaleChange = async (newScale: number) => {
    setLoraScale(newScale);
    
    if (!token || !loraLoaded) return;

    try {
      await generateApi.setLoraScale({ scale: newScale }, token);
    } catch (err) {
      console.error('Failed to set LoRA scale:', err);
    }
  };

  // Reuse Effect - must be after all state declarations
  useEffect(() => {
    if (initialData) {
      setCustomMode(true);
      setLyrics(initialData.song.lyrics);
      setStyle(initialData.song.style);
      setTitle(initialData.song.title);
      setInstrumental(initialData.song.lyrics.length === 0);
    }
  }, [initialData]);

  useEffect(() => {
    if (!pendingAudioSelection) return;
    applyAudioTargetUrl(
      pendingAudioSelection.target,
      pendingAudioSelection.url,
      pendingAudioSelection.title
    );
    onAudioSelectionApplied?.();
  }, [pendingAudioSelection, onAudioSelectionApplied]);

  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      if (!isResizing) return;

      const ref = resizingTarget === 'lyrics' ? lyricsRef : styleRef;
      const minHeight = resizingTarget === 'lyrics' ? MIN_LYRICS_HEIGHT : MIN_STYLE_HEIGHT;

      if (ref.current) {
        const rect = ref.current.getBoundingClientRect();
        const newHeight = e.clientY - rect.top;
        if (newHeight > minHeight && newHeight < MAX_HEIGHT) {
          if (resizingTarget === 'lyrics') {
            setLyricsHeight(newHeight);
            localStorage.setItem('acestep_lyrics_height', String(newHeight));
          } else {
            setStyleHeight(newHeight);
            localStorage.setItem('acestep_style_height', String(newHeight));
          }
        }
      }
    };

    const handleMouseUp = () => {
      setIsResizing(false);
      document.body.style.cursor = 'default';
      document.body.style.userSelect = 'auto';
    };

    if (isResizing) {
      window.addEventListener('mousemove', handleMouseMove);
      window.addEventListener('mouseup', handleMouseUp);
      document.body.style.cursor = 'ns-resize';
      document.body.style.userSelect = 'none';
    }

    return () => {
      window.removeEventListener('mousemove', handleMouseMove);
      window.removeEventListener('mouseup', handleMouseUp);
      document.body.style.cursor = 'default';
      document.body.style.userSelect = 'auto';
    };
  }, [isResizing]);

  const refreshModels = useCallback(async () => {
    try {
      const modelsRes = await fetch('/api/generate/models');
      if (modelsRes.ok) {
        const data = await modelsRes.json();
        console.log('[CreatePanel] API response:', data);
        const models = data.data?.models || data.models || [];
        console.log('[CreatePanel] models:', models);
        if (models.length > 0) {
          setFetchedModels(models);
          // Always sync to the backend's active model
          const active = models.find((m: any) => m.is_active);
          if (active) {
            setSelectedModel(active.name);
            localStorage.setItem('ace-model', active.name);
          }
        }
      }
    } catch (err) {
      console.error('[CreatePanel] Error fetching models:', err);
    }
  }, []);

  useEffect(() => {
    const loadModelsAndLimits = async () => {
      await refreshModels();

      // Fetch limits
      try {
        const response = await fetch('/api/generate/limits');
        if (!response.ok) return;
        const data = await response.json();
        if (typeof data.max_duration_with_lm === 'number') {
          setMaxDurationWithLm(data.max_duration_with_lm);
        }
        if (typeof data.max_duration_without_lm === 'number') {
          setMaxDurationWithoutLm(data.max_duration_without_lm);
        }
      } catch {
        // ignore limits fetch failures
      }
    };

    loadModelsAndLimits();
  }, []);

  // Re-fetch models after generation completes to update active model
  const prevIsGeneratingRef = useRef(isGenerating);
  useEffect(() => {
    if (prevIsGeneratingRef.current && !isGenerating) {
      void refreshModels();
    }
    prevIsGeneratingRef.current = isGenerating;
  }, [isGenerating, refreshModels]);

  const activeMaxDuration = thinking ? maxDurationWithLm : maxDurationWithoutLm;

  useEffect(() => {
    if (duration > activeMaxDuration) {
      setDuration(activeMaxDuration);
    }
  }, [duration, activeMaxDuration]);

  useEffect(() => {
    const getDragKind = (e: DragEvent): 'file' | 'audio' | null => {
      if (!e.dataTransfer) return null;
      const types = Array.from(e.dataTransfer.types);
      if (types.includes('Files')) return 'file';
      if (types.includes('application/x-ace-audio')) return 'audio';
      return null;
    };

    const handleDragEnter = (e: DragEvent) => {
      const kind = getDragKind(e);
      if (!kind) return;
      dragDepthRef.current += 1;
      setIsDraggingFile(true);
      setDragKind(kind);
      e.preventDefault();
    };

    const handleDragOver = (e: DragEvent) => {
      const kind = getDragKind(e);
      if (!kind) return;
      setDragKind(kind);
      e.preventDefault();
    };

    const handleDragLeave = (e: DragEvent) => {
      const kind = getDragKind(e);
      if (!kind) return;
      dragDepthRef.current = Math.max(0, dragDepthRef.current - 1);
      if (dragDepthRef.current === 0) {
        setIsDraggingFile(false);
        setDragKind(null);
      }
    };

    const handleDrop = (e: DragEvent) => {
      const kind = getDragKind(e);
      if (!kind) return;
      e.preventDefault();
      dragDepthRef.current = 0;
      setIsDraggingFile(false);
      setDragKind(null);
    };

    window.addEventListener('dragenter', handleDragEnter);
    window.addEventListener('dragover', handleDragOver);
    window.addEventListener('dragleave', handleDragLeave);
    window.addEventListener('drop', handleDrop);

    return () => {
      window.removeEventListener('dragenter', handleDragEnter);
      window.removeEventListener('dragover', handleDragOver);
      window.removeEventListener('dragleave', handleDragLeave);
      window.removeEventListener('drop', handleDrop);
    };
  }, []);

  const startResizing = (e: React.MouseEvent, target: 'lyrics' | 'style') => {
    e.preventDefault();
    setResizingTarget(target);
    setIsResizing(true);
  };

  const calcContentHeight = (textarea: HTMLTextAreaElement, minHeight: number): number => {
    textarea.style.height = 'auto';
    const scrollH = textarea.scrollHeight;
    textarea.style.height = '';
    const lineHeight = parseInt(getComputedStyle(textarea).lineHeight) || 20;
    return Math.min(Math.max(scrollH + lineHeight, minHeight), MAX_HEIGHT);
  };

  const toggleLyricsExpand = () => {
    if (lyricsExpanded) {
      const saved = localStorage.getItem('acestep_lyrics_height');
      setLyricsHeight(saved ? parseInt(saved, 10) : 144);
      setLyricsExpanded(false);
    } else {
      if (lyricsTextareaRef.current) {
        setLyricsHeight(calcContentHeight(lyricsTextareaRef.current, MIN_LYRICS_HEIGHT));
      }
      setLyricsExpanded(true);
    }
  };

  const toggleStyleExpand = () => {
    if (styleExpanded) {
      const saved = localStorage.getItem('acestep_style_height');
      setStyleHeight(saved ? parseInt(saved, 10) : 80);
      setStyleExpanded(false);
    } else {
      if (styleTextareaRef.current) {
        setStyleHeight(calcContentHeight(styleTextareaRef.current, MIN_STYLE_HEIGHT));
      }
      setStyleExpanded(true);
    }
  };

  const uploadAudio = async (file: File, target: 'reference' | 'source') => {
    if (!token) {
      setUploadError('Please sign in to upload audio.');
      return;
    }
    setUploadError(null);
    const setUploading = target === 'reference' ? setIsUploadingReference : setIsUploadingSource;
    const setUrl = target === 'reference' ? setReferenceAudioUrl : setSourceAudioUrl;
    setUploading(true);
    try {
      const result = await generateApi.uploadAudio(file, token);
      setUrl(result.url);
      setShowAudioModal(false);
      setTempAudioUrl('');
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Upload failed';
      setUploadError(message);
    } finally {
      setUploading(false);
    }
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>, target: 'reference' | 'source') => {
    const file = e.target.files?.[0];
    if (file) {
      void uploadReferenceTrack(file, target);
    }
    e.target.value = '';
  };

  // Format handler - uses LLM to enhance style/lyrics and auto-fill parameters
  const handleFormat = async (target: 'style' | 'lyrics') => {
    if (!token || !style.trim()) return;
    if (target === 'style') {
      setIsFormattingStyle(true);
    } else {
      setIsFormattingLyrics(true);
    }
    try {
      const result = await generateApi.formatInput({
        caption: style,
        lyrics: lyrics,
        bpm: bpm > 0 ? bpm : undefined,
        duration: duration > 0 ? duration : undefined,
        keyScale: keyScale || undefined,
        timeSignature: timeSignature || undefined,
        temperature: lmTemperature,
        topK: lmTopK > 0 ? lmTopK : undefined,
        topP: lmTopP,
        lmModel: lmModel || 'acestep-5Hz-lm-0.6B',
        lmBackend: lmBackend || 'pt',
      }, token);

      if (result.caption || result.lyrics || result.bpm || result.duration) {
        // Update fields with LLM-generated values
        if (target === 'style' && result.caption) setStyle(result.caption);
        if (target === 'lyrics' && result.lyrics) setLyrics(result.lyrics);
        if (result.bpm && result.bpm > 0) setBpm(result.bpm);
        if (result.duration && result.duration > 0) setDuration(result.duration);
        if (result.key_scale) setKeyScale(result.key_scale);
        if (result.time_signature) {
          const ts = String(result.time_signature);
          setTimeSignature(ts.includes('/') ? ts : `${ts}/4`);
        }
        if (result.vocal_language) setVocalLanguage(result.vocal_language);
        if (target === 'style') setIsFormatCaption(true);
      } else {
        console.error('Format failed:', result.error || result.status_message);
        alert(result.error || result.status_message || 'Format failed. Make sure the LLM is initialized.');
      }
    } catch (err) {
      console.error('Format error:', err);
      alert('Format failed. The LLM may not be available.');
    } finally {
      if (target === 'style') {
        setIsFormattingStyle(false);
      } else {
        setIsFormattingLyrics(false);
      }
    }
  };

  const openAudioModal = (target: 'reference' | 'source', tab: 'uploads' | 'created' = 'uploads') => {
    setAudioModalTarget(target);
    setTempAudioUrl('');
    setLibraryTab(tab);
    setShowAudioModal(true);
    void fetchReferenceTracks();
  };

  const fetchReferenceTracks = useCallback(async () => {
    if (!token) return;
    setIsLoadingTracks(true);
    try {
      const response = await fetch('/api/reference-tracks', {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (response.ok) {
        const data = await response.json();
        setReferenceTracks(data.tracks || []);
      }
    } catch (err) {
      console.error('Failed to fetch reference tracks:', err);
    } finally {
      setIsLoadingTracks(false);
    }
  }, [token]);

  const uploadReferenceTrack = async (file: File, target?: 'reference' | 'source') => {
    if (!token) {
      setUploadError('Please sign in to upload audio.');
      return;
    }
    setUploadError(null);
    setIsUploadingReference(true);
    try {
      const formData = new FormData();
      formData.append('audio', file);

      const response = await fetch('/api/reference-tracks', {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` },
        body: formData
      });

      if (!response.ok) {
        const err = await response.json();
        throw new Error(err.error || 'Upload failed');
      }

      const data = await response.json();
      setReferenceTracks(prev => [data.track, ...prev]);

      // Also set as current reference/source
      const selectedTarget = target ?? audioModalTarget;
      applyAudioTargetUrl(selectedTarget, data.track.audio_url, data.track.filename);
      if (data.whisper_available && data.track?.id) {
        void transcribeReferenceTrack(data.track.id).then(() => undefined);
      } else {
        setShowAudioModal(false);
      }
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Upload failed';
      setUploadError(message);
    } finally {
      setIsUploadingReference(false);
    }
  };

  const transcribeReferenceTrack = async (trackId: string) => {
    if (!token) return;
    setIsTranscribingReference(true);
    const controller = new AbortController();
    transcribeAbortRef.current = controller;
    try {
      const response = await fetch(`/api/reference-tracks/${trackId}/transcribe`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` },
        signal: controller.signal,
      });
      if (!response.ok) {
        throw new Error('Failed to transcribe');
      }
      const data = await response.json();
      if (data.lyrics) {
        setLyrics(prev => prev || data.lyrics);
      }
    } catch (err) {
      if (controller.signal.aborted) return;
      console.error('Transcription failed:', err);
    } finally {
      if (transcribeAbortRef.current === controller) {
        transcribeAbortRef.current = null;
      }
      setIsTranscribingReference(false);
    }
  };

  const cancelTranscription = () => {
    if (transcribeAbortRef.current) {
      transcribeAbortRef.current.abort();
      transcribeAbortRef.current = null;
    }
    setIsTranscribingReference(false);
  };

  const deleteReferenceTrack = async (trackId: string) => {
    if (!token) return;
    try {
      const response = await fetch(`/api/reference-tracks/${trackId}`, {
        method: 'DELETE',
        headers: { Authorization: `Bearer ${token}` }
      });
      if (response.ok) {
        setReferenceTracks(prev => prev.filter(t => t.id !== trackId));
        if (playingTrackId === trackId && playingTrackSource === 'uploads') {
          setPlayingTrackId(null);
          setPlayingTrackSource(null);
          if (modalAudioRef.current) {
            modalAudioRef.current.pause();
          }
        }
      }
    } catch (err) {
      console.error('Failed to delete track:', err);
    }
  };

  const useReferenceTrack = (track: { audio_url: string; title?: string }) => {
    applyAudioTargetUrl(audioModalTarget, track.audio_url, track.title);
    setShowAudioModal(false);
    setPlayingTrackId(null);
    setPlayingTrackSource(null);
  };

  const toggleModalTrack = (track: { id: string; audio_url: string; source: 'uploads' | 'created' }) => {
    if (playingTrackId === track.id) {
      if (modalAudioRef.current) {
        modalAudioRef.current.pause();
      }
      setPlayingTrackId(null);
      setPlayingTrackSource(null);
    } else {
      setPlayingTrackId(track.id);
      setPlayingTrackSource(track.source);
      if (modalAudioRef.current) {
        modalAudioRef.current.src = track.audio_url;
        modalAudioRef.current.play().catch(() => undefined);
      }
    }
  };

  const applyAudioUrl = () => {
    if (!tempAudioUrl.trim()) return;
    applyAudioTargetUrl(audioModalTarget, tempAudioUrl.trim());
    setShowAudioModal(false);
    setTempAudioUrl('');
  };

  const applyAudioTargetUrl = (target: 'reference' | 'source', url: string, title?: string) => {
    const derivedTitle = title ? title.replace(/\.[^/.]+$/, '') : getAudioLabel(url);
    if (target === 'reference') {
      setReferenceAudioUrl(url);
      setReferenceAudioTitle(derivedTitle);
      setReferenceTime(0);
      setReferenceDuration(0);
    } else {
      setSourceAudioUrl(url);
      setSourceAudioTitle(derivedTitle);
      setSourceTime(0);
      setSourceDuration(0);
      if (taskType === 'text2music') {
        setTaskType('cover');
      }
    }
  };

  const formatTime = (time: number) => {
    if (!Number.isFinite(time) || time <= 0) return '0:00';
    const minutes = Math.floor(time / 60);
    const seconds = Math.floor(time % 60);
    return `${minutes}:${String(seconds).padStart(2, '0')}`;
  };

  const toggleAudio = (target: 'reference' | 'source') => {
    const audio = target === 'reference' ? referenceAudioRef.current : sourceAudioRef.current;
    if (!audio) return;
    if (audio.paused) {
      audio.play().catch(() => undefined);
    } else {
      audio.pause();
    }
  };

  const handleDrop = (e: React.DragEvent<HTMLDivElement>, target: 'reference' | 'source') => {
    e.preventDefault();
    const file = e.dataTransfer.files?.[0];
    if (file) {
      void uploadReferenceTrack(file, target);
      return;
    }
    const payload = e.dataTransfer.getData('application/x-ace-audio');
    if (payload) {
      try {
        const data = JSON.parse(payload);
        if (data?.url) {
          applyAudioTargetUrl(target, data.url, data.title);
        }
      } catch {
        // ignore
      }
    }
  };

  const handleDragOver = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
  };

  const handleWorkspaceDrop = (e: React.DragEvent<HTMLDivElement>) => {
    if (e.dataTransfer.files?.length || e.dataTransfer.types.includes('application/x-ace-audio')) {
      handleDrop(e, audioTab);
    }
  };

  const handleWorkspaceDragOver = (e: React.DragEvent<HTMLDivElement>) => {
    if (e.dataTransfer.types.includes('Files') || e.dataTransfer.types.includes('application/x-ace-audio')) {
      e.preventDefault();
    }
  };

  const handleGenerate = () => {
    // cover / audio2audio require a source audio (or audio codes).
    // 点击「创建」时立即拦截并引导：切到「内容参考」标签、滚动定位、高亮闪烁，避免让用户进入生成流程后等待很久才报错。
    if ((taskType === 'cover' || taskType === 'audio2audio') && !sourceAudioUrl.trim() && !audioCodes.trim()) {
      setCustomMode(true);          // 音频区仅在自定义模式显示，确保引导可见
      setAudioTab('source');        // 自动切到「内容参考」标签（源音频槽）
      setSourceHintActive(true);    // 触发高亮闪烁
      // 滚动到音频区并聚焦上传入口
      requestAnimationFrame(() => {
        audioSectionRef.current?.scrollIntoView({ behavior: 'smooth', block: 'center' });
      });
      window.setTimeout(() => setSourceHintActive(false), 2600);
      return;
    }
    let baseStyle = style;
    if (effectiveStyleForLora && !baseStyle.includes(effectiveStyleForLora.tag)) {
      const { tag, pos } = effectiveStyleForLora;
      if (pos === 'prepend') baseStyle = `${tag}, ${baseStyle}`;
      else if (pos === 'replace') baseStyle = tag;
      else baseStyle = `${baseStyle}, ${tag}`;
    }
    const styleWithGender = (() => {
      if (!vocalGender) return baseStyle;
      const genderHint = vocalGender === 'male' ? 'Male vocals' : 'Female vocals';
      const trimmed = baseStyle.trim();
      return trimmed ? `${trimmed}\n${genderHint}` : genderHint;
    })();

    // Bulk generation: loop bulkCount times
    for (let i = 0; i < bulkCount; i++) {
      // Seed handling: first job uses user's seed, rest get random seeds
      let jobSeed = -1;
      if (!randomSeed && i === 0) {
        jobSeed = seed;
      } else if (!randomSeed && i > 0) {
        // Subsequent jobs get random seeds for variety
        jobSeed = Math.floor(Math.random() * 4294967295);
      }

      onGenerate({
        customMode,
        songDescription: customMode ? undefined : songDescription,
        prompt: lyrics,
        lyrics,
        style: styleWithGender,
        title: bulkCount > 1 ? `${title} (${i + 1})` : title,
        ditModel: selectedModel,
        instrumental,
        vocalLanguage,
        bpm,
        keyScale,
        timeSignature,
        duration,
        inferenceSteps,
        guidanceScale,
        batchSize,
        randomSeed: randomSeed || i > 0, // Force random for subsequent bulk jobs
        seed: jobSeed,
        thinking,
        audioFormat,
        inferMethod,
        lmBackend,
        lmModel,
        shift,
        lmTemperature,
        lmCfgScale,
        lmTopK,
        lmTopP,
        lmNegativePrompt,
        referenceAudioUrl: referenceAudioUrl.trim() || undefined,
        sourceAudioUrl: sourceAudioUrl.trim() || undefined,
        referenceAudioTitle: referenceAudioTitle.trim() || undefined,
        sourceAudioTitle: sourceAudioTitle.trim() || undefined,
        audioCodes: audioCodes.trim() || undefined,
        repaintingStart,
        repaintingEnd,
        instruction,
        audioCoverStrength,
        coverNoiseStrength,
        taskType,
        useAdg,
        cfgIntervalStart,
        cfgIntervalEnd,
        customTimesteps: customTimesteps.trim() || undefined,
        useCotMetas,
        useCotCaption,
        useCotLanguage,
        autogen,
        constrainedDecodingDebug,
        allowLmBatch,
        getScores,
        getLrc,
        scoreScale,
        lmBatchChunkSize,
        trackName: trackName.trim() || undefined,
        completeTrackClasses: (() => {
          const parsed = completeTrackClasses
            .split(',')
            .map((item) => item.trim())
            .filter(Boolean);
          return parsed.length ? parsed : undefined;
        })(),
        isFormatCaption,
        loraLoaded,
      });
    }

    // Reset bulk count after generation
    if (bulkCount > 1) {
      setBulkCount(1);
    }
  };

  return (
    <div
      className="relative flex flex-col h-full bg-zinc-50 dark:bg-suno-panel w-full overflow-y-auto custom-scrollbar transition-colors duration-300"
      onDrop={handleWorkspaceDrop}
      onDragOver={handleWorkspaceDragOver}
    >
      {isDraggingFile && (
        <div className="absolute inset-0 z-[90] pointer-events-none">
          <div className="absolute inset-0 bg-white/70 dark:bg-black/50 backdrop-blur-sm" />
          <div className="absolute inset-0 flex items-center justify-center">
            <div className="flex flex-col items-center gap-2 rounded-2xl border border-zinc-200 dark:border-white/10 bg-white/90 dark:bg-zinc-900/90 px-6 py-5 shadow-xl">
              {dragKind !== 'audio' && (
                <div className="w-12 h-12 rounded-full bg-gradient-to-br from-pink-500 to-purple-600 text-white flex items-center justify-center shadow-lg">
                  <Upload size={22} />
                </div>
              )}
              <div className="text-sm font-semibold text-zinc-900 dark:text-white">
                {dragKind === 'audio' ? t('dropToUseAudio') : t('dropToUpload')}
              </div>
              <div className="text-[11px] text-zinc-500 dark:text-zinc-400">
                {dragKind === 'audio'
                  ? (audioTab === 'reference' ? t('usingAsReference') : t('usingAsCover'))
                  : (audioTab === 'reference' ? t('uploadingAsReference') : t('uploadingAsCover'))}
              </div>
            </div>
          </div>
        </div>
      )}
      <div className="p-4 pt-14 md:pt-4 pb-24 lg:pb-32 space-y-5">
        <input
          ref={referenceInputRef}
          type="file"
          accept="audio/*"
          onChange={(e) => handleFileSelect(e, 'reference')}
          className="hidden"
        />
        <input
          ref={sourceInputRef}
          type="file"
          accept="audio/*"
          onChange={(e) => handleFileSelect(e, 'source')}
          className="hidden"
        />
        <audio
          ref={referenceAudioRef}
          src={referenceAudioUrl || undefined}
          onPlay={() => setReferencePlaying(true)}
          onPause={() => setReferencePlaying(false)}
          onEnded={() => setReferencePlaying(false)}
          onTimeUpdate={(e) => setReferenceTime(e.currentTarget.currentTime)}
          onLoadedMetadata={(e) => setReferenceDuration(e.currentTarget.duration || 0)}
        />
        <audio
          ref={sourceAudioRef}
          src={sourceAudioUrl || undefined}
          onPlay={() => setSourcePlaying(true)}
          onPause={() => setSourcePlaying(false)}
          onEnded={() => setSourcePlaying(false)}
          onTimeUpdate={(e) => setSourceTime(e.currentTarget.currentTime)}
          onLoadedMetadata={(e) => setSourceDuration(e.currentTarget.duration || 0)}
        />

        {/* Header - Mode Toggle & Model Selection */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse"></div>
            <span className="text-xs font-medium text-zinc-500 dark:text-zinc-400">ACE-Step v1.5</span>
          </div>

          <div className="flex items-center gap-2">
            {/* Mode Toggle */}
            <div className="flex items-center bg-zinc-200 dark:bg-black/40 rounded-lg p-1 border border-zinc-300 dark:border-white/5">
              <button
                onClick={() => { setCustomMode(false); localStorage.setItem('ace-customMode', 'false'); }}
                className={`px-3 py-1.5 rounded-md text-xs font-semibold transition-all ${!customMode ? 'bg-white dark:bg-zinc-800 text-black dark:text-white shadow-sm' : 'text-zinc-500 hover:text-zinc-900 dark:hover:text-zinc-300'}`}
              >
                {t('simple')}
              </button>
              <button
                onClick={() => { setCustomMode(true); localStorage.setItem('ace-customMode', 'true'); }}
                className={`px-3 py-1.5 rounded-md text-xs font-semibold transition-all ${customMode ? 'bg-white dark:bg-zinc-800 text-black dark:text-white shadow-sm' : 'text-zinc-500 hover:text-zinc-900 dark:hover:text-zinc-300'}`}
              >
                {t('custom')}
              </button>
            </div>

            {/* Model Selection */}
            <div className="relative" ref={modelMenuRef}>
              <button
                onClick={() => setShowModelMenu(!showModelMenu)}
                className="bg-zinc-200 dark:bg-black/40 border border-zinc-300 dark:border-white/5 rounded-md px-2 py-1 text-[11px] font-medium text-zinc-900 dark:text-white hover:bg-zinc-300 dark:hover:bg-black/50 transition-colors flex items-center gap-1"
                disabled={availableModels.length === 0}
              >
                {availableModels.length === 0 ? '...' : getModelDisplayName(selectedModel)}
                <ChevronDown size={10} className="text-zinc-600 dark:text-zinc-400" />
              </button>
              
              {/* Floating Model Menu */}
              {showModelMenu && availableModels.length > 0 && (
                <div className="absolute top-full right-0 mt-1 w-80 bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-700 rounded-xl shadow-2xl z-50 overflow-hidden">
                  <div className="max-h-96 overflow-y-auto custom-scrollbar">
                    {availableModels.map(model => {
                      const fetchedModel = fetchedModels.find(m => m.name === model.id);
                      const isAvailable = fetchedModel?.is_installed ?? false;
                      const integrityStatus = fetchedModel?.integrity_status ?? (isAvailable ? 'complete' : 'missing');
                      const integrityDetails = fetchedModel?.integrity_details;
                      console.log(`[CreatePanel] Model ${model.id}:`, { fetchedModel, isAvailable, integrityStatus });
                      
                      const descriptions: Record<string, string> = {
                        'acestep-v15-base': '基础模型，适合从零开始创作，生成风格多样的音乐。',
                        'acestep-v15-sft': 'SFT微调模型，更适合风格延续和参考创作，旋律还原度较高。',
                        'acestep-v15-turbo': 'Turbo快速模型，生成速度快，适合快速迭代和测试想法。',
                        'acestep-v15-turbo-shift1': 'Turbo Shift 1模型，平衡速度与质量，是日常创作的首选。',
                        'acestep-v15-turbo-shift3': 'Turbo Shift 3模型，质量更好的快速模型，推荐用于正式创作。',
                        'acestep-v15-turbo-continuous': 'Turbo Continuous模型，适合长音频生成，稳定性极佳。',
                        'acestep-v15-xl-turbo': 'XL Turbo 4B模型，最高音质，8步快速推理，需要≥12GB VRAM。',
                        'acestep-v15-xl-sft': 'XL SFT 4B模型，最高品质，50步精细推理，需要≥12GB VRAM。',
                        'acestep-v15-xl-base': 'XL Base 4B模型，最高多样性，支持extract/lego/complete高级任务，需要≥12GB VRAM。',
                      };
                      const modelDescription = descriptions[model.id] || '';
                      
                      return (
                        <button
                          key={model.id}
                          onClick={() => {
                            if (!isAvailable) return;
                            setSelectedModel(model.id);
                            localStorage.setItem('ace-model', model.id);
                            // Auto-adjust parameters for non-turbo models
                            if (!isTurboModel(model.id)) {
                              setInferenceSteps(20);
                              setUseAdg(true);
                            }
                            setShowModelMenu(false);
                          }}
                          className={`w-full px-4 py-3 text-left transition-colors border-b border-zinc-100 dark:border-zinc-800 last:border-b-0 ${
                            selectedModel === model.id ? 'bg-zinc-50 dark:bg-zinc-800/50' : ''
                          } ${
                            isAvailable 
                              ? 'hover:bg-zinc-100 dark:hover:bg-zinc-800 cursor-pointer' 
                              : 'opacity-50 cursor-not-allowed'
                          }`}
                        >
                          <div className="flex items-center justify-between mb-1">
                            <div className="flex items-center gap-2">
                              <span className="text-sm font-semibold text-zinc-900 dark:text-white">
                                {getModelDisplayName(model.id)}
                              </span>
                              {isAvailable ? (
                                <span className={`px-1.5 py-0.5 rounded text-[9px] font-bold ${selectedModel === model.id ? 'bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-400' : 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400'}`}>
                                  {selectedModel === model.id ? '● 激活中' : '● 可用'}
                                </span>
                              ) : integrityStatus === 'incomplete' ? (
                                <span className="px-1.5 py-0.5 rounded text-[9px] font-bold bg-orange-100 dark:bg-orange-900/30 text-orange-700 dark:text-orange-400" title={integrityDetails?.files_missing?.length ? `缺少文件: ${integrityDetails.files_missing.join(', ')}` : '模型不完整，建议重新下载'}>
                                  ● 不完整
                                </span>
                              ) : (
                                <span className="px-1.5 py-0.5 rounded text-[9px] font-bold bg-yellow-100 dark:bg-yellow-900/30 text-yellow-700 dark:text-yellow-400">
                                  ● 未加载
                                </span>
                              )}
                            </div>
                            {selectedModel === model.id && (
                              <div className="w-4 h-4 rounded-full bg-pink-500 flex items-center justify-center">
                                <svg className="w-3 h-3 text-white" fill="currentColor" viewBox="0 0 20 20">
                                  <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                                </svg>
                              </div>
                            )}
                          </div>
                          <p className="text-xs text-zinc-500 dark:text-zinc-400 mb-1">{model.id}</p>
                          {modelDescription && (
                            <p className="text-xs text-zinc-400 dark:text-zinc-500 line-clamp-2">{modelDescription}</p>
                          )}
                          {integrityStatus === 'incomplete' && integrityDetails && (
                            <p className="text-xs text-orange-500 dark:text-orange-400 mt-1">
                              ⚠ 模型不完整{integrityDetails.files_missing?.length > 0 ? `，缺少: ${integrityDetails.files_missing.join(', ')}` : ''}，请重新下载
                            </p>
                          )}
                        </button>
                      );
                    })}
                  </div>
                </div>
              )}
            </div>

          </div>
        </div>

        {/* Project & Presets Panel */}
        <div className="bg-white dark:bg-suno-card rounded-xl border border-zinc-200 dark:border-white/5 overflow-hidden">
          <div className="px-3 py-2.5 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <FolderOpen size={12} className="text-blue-500" />
              {activeProject && (
                <button
                  onClick={() => setShowProjectDropdown(!showProjectDropdown)}
                  className="flex items-center gap-1.5 hover:bg-zinc-100 dark:hover:bg-white/5 rounded px-1.5 py-0.5 transition-colors"
                >
                  <span className="text-xs font-medium text-zinc-900 dark:text-white truncate max-w-[120px]">{activeProject.name}</span>
                  {activeProject.is_default && <span className="text-[9px] text-yellow-500">●</span>}
                  <ChevronDown size={10} className="text-zinc-400" />
                </button>
              )}
            </div>
            <div className="flex items-center gap-1">
              {activeProject && (
                <>
                  <button
                    onClick={() => handleUndo()}
                    disabled={!canUndo}
                    className={`p-1 rounded transition-colors ${canUndo ? 'text-zinc-500 hover:text-blue-600 hover:bg-blue-50 dark:hover:bg-blue-900/20' : 'text-zinc-300 dark:text-zinc-600 cursor-not-allowed'}`}
                    title={canUndo ? `撤销: ${undoAction}` : '无可撤销操作 (Ctrl+Z)'}
                  >
                    <Undo2 size={12} />
                  </button>
                  <button
                    onClick={() => handleRedo()}
                    disabled={!canRedo}
                    className={`p-1 rounded transition-colors ${canRedo ? 'text-zinc-500 hover:text-blue-600 hover:bg-blue-50 dark:hover:bg-blue-900/20' : 'text-zinc-300 dark:text-zinc-600 cursor-not-allowed'}`}
                    title={canRedo ? `重做: ${redoAction}` : '无可重做操作 (Ctrl+Y)'}
                  >
                    <Redo2 size={12} />
                  </button>
                  <button
                    onClick={async () => {
                      if (!token || !activeProject) return;
                      try {
                        const result = await projectsApi.getChangelogs(activeProject.id, token, { limit: 50, offset: 0 });
                        setChangelogs(result.changelogs);
                        setChangelogTotal(result.total);
                        setShowChangelog(true);
                      } catch {}
                    }}
                    className="p-1 text-zinc-400 hover:text-green-500 rounded transition-colors"
                    title={t('history')}
                  >
                    <History size={12} />
                  </button>
                  <button
                    onClick={async () => { try { await saveProjectParams(); } catch {} }}
                    className="p-1 text-zinc-400 hover:text-blue-500 rounded transition-colors"
                    title={t('saveProject')}
                  >
                    <Save size={12} />
                  </button>
                </>
              )}
              <button
                onClick={() => {
                  setProjectName('');
                  setProjectDescription('');
                  setShowSaveProjectModal(true);
                }}
                className="p-1 text-zinc-400 hover:text-blue-500 rounded transition-colors"
                title={t('newProject')}
              >
                <FolderPlus size={12} />
              </button>
            </div>
          </div>

          {/* Project Dropdown */}
          {showProjectDropdown && (
            <div className="border-t border-zinc-100 dark:border-white/5 max-h-48 overflow-y-auto custom-scrollbar" ref={projectDropdownRef}>
              {projects.map(project => (
                <div
                  key={project.id}
                  className={`flex items-center px-3 py-2 hover:bg-zinc-50 dark:hover:bg-zinc-800/50 transition-colors border-b border-zinc-50 dark:border-zinc-800/50 group ${project.is_default ? 'bg-yellow-50/50 dark:bg-yellow-900/10' : ''}`}
                >
                  <button
                    onClick={async () => {
                      if (!token) return;
                      try {
                        if (project.id !== activeProject?.id) {
                          const result = await projectsApi.activateProject(project.id, token);
                          setActiveProject(result.project);
                          applyProject(result.project);
                          setProjects(prev => prev.map(p => ({ ...p, is_active: p.id === result.project.id })));
                          await refreshUndoRedoState();
                        } else {
                          applyProject(project);
                        }
                      } catch {}
                      setShowProjectDropdown(false);
                    }}
                    className="flex-1 text-left flex items-center gap-2 min-w-0"
                  >
                    <FolderOpen size={12} className={project.is_active ? 'text-blue-500 flex-shrink-0' : 'text-zinc-400 dark:text-zinc-500 flex-shrink-0'} />
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-1.5">
                        {project.is_default && <span className="text-[9px] text-yellow-500">●</span>}
                        <p className="text-xs font-medium text-zinc-900 dark:text-white truncate">{project.name}</p>
                        {project.is_active && (
                          <span className="px-1.5 py-0.5 text-[8px] font-bold bg-blue-100 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400 rounded">{t('active')}</span>
                        )}
                      </div>
                    </div>
                  </button>
                  <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-all">
                    {project.is_default && (
                      <button
                        onClick={async (e) => {
                          e.stopPropagation();
                          setRenameValue(project.name);
                          setShowRenameModal(true);
                        }}
                        className="p-1 text-zinc-400 hover:text-yellow-500 transition-colors"
                        title="命名项目"
                      >
                        <Pencil size={12} />
                      </button>
                    )}
                    {!project.is_default && (
                      <button
                        onClick={async (e) => {
                          e.stopPropagation();
                          if (!token) return;
                          try {
                            await projectsApi.deleteProject(project.id, token);
                            setProjects(prev => prev.filter(p => p.id !== project.id));
                            if (project.id === activeProject?.id) {
                              const projectsResult = await projectsApi.getProjects(token);
                              setProjects(projectsResult.projects);
                              const newActive = projectsResult.projects.find((p: Project) => p.is_active) || projectsResult.default_project;
                              if (newActive) {
                                setActiveProject(newActive);
                                applyProject(newActive);
                              }
                            }
                          } catch {}
                        }}
                        className="p-1 text-zinc-400 hover:text-red-500 transition-colors"
                        title={t('delete')}
                      >
                        <Trash2 size={12} />
                      </button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* Presets - Collapsible Dropdown */}
          <div className="border-t border-zinc-100 dark:border-white/5">
            <button
              onClick={() => setShowPresetMenu(!showPresetMenu)}
              className="w-full px-3 py-2 flex items-center justify-between hover:bg-zinc-50 dark:hover:bg-white/5 transition-colors"
            >
              <div className="flex items-center gap-1.5">
                <Bookmark size={12} className="text-pink-500" />
                <span className="text-[11px] font-bold tracking-wide text-zinc-500 dark:text-zinc-400">{t('presets')}</span>
                {selectedPresetId && (() => {
                  const sp = presets.find(p => p.id === selectedPresetId);
                  return sp ? (
                    <span className="px-1.5 py-0.5 text-[8px] font-bold bg-pink-100 dark:bg-pink-900/30 text-pink-600 dark:text-pink-400 rounded">{sp.name}</span>
                  ) : null;
                })()}
              </div>
              {showPresetMenu ? <ChevronUp size={12} className="text-zinc-400" /> : <ChevronDown size={12} className="text-zinc-400" />}
            </button>

            {showPresetMenu && (
              <div className="border-t border-zinc-100 dark:border-white/5">
                <div className="px-3 py-1.5 border-b border-zinc-100 dark:border-zinc-800 flex items-center justify-between">
                  <span className="text-[10px] text-zinc-400 dark:text-zinc-500">{t('presetHint')}</span>
                  <button
                    onClick={() => {
                      setPresetName('');
                      setPresetDescription('');
                      setPresetCategory(taskType || 'custom');
                      setShowSavePresetModal(true);
                    }}
                    className="flex items-center gap-1 px-2 py-1 text-[10px] font-medium bg-pink-600 text-white rounded-md hover:bg-pink-700 transition-colors"
                  >
                    <Save size={10} />
                    {t('savePreset')}
                  </button>
                </div>
                <div className="max-h-52 overflow-y-auto custom-scrollbar">
                  {presets.length === 0 ? (
                    <div className="px-3 py-6 text-center text-xs text-zinc-400 dark:text-zinc-500">
                      {t('noPresets')}
                    </div>
                  ) : (
                    (() => {
                      const builtinPresets = presets.filter(p => p.is_builtin);
                      const customPresets = presets.filter(p => !p.is_builtin);
                      const categoryLabels: Record<string, string> = {
                        text2music: t('textToMusic'),
                        cover: t('coverTask'),
                        audio2audio: t('audio2audio'),
                        instrumental: t('instrumental'),
                        long: t('longAudio'),
                        custom: t('custom'),
                      };
                      const categoryOrder = ['text2music', 'cover', 'audio2audio', 'instrumental', 'long', 'custom'];
                      const groupedBuiltin = categoryOrder.reduce((acc, cat) => {
                        const items = builtinPresets.filter(p => p.category === cat);
                        if (items.length > 0) acc.push({ category: cat, label: categoryLabels[cat] || cat, items });
                        return acc;
                      }, [] as { category: string; label: string; items: Preset[] }[]);

                      return (
                        <>
                          {groupedBuiltin.map(group => (
                            <div key={group.category}>
                              <div className="px-3 py-1.5 bg-zinc-50 dark:bg-zinc-800/50 border-b border-zinc-100 dark:border-zinc-800">
                                <span className="text-[10px] font-semibold text-zinc-400 dark:text-zinc-500 tracking-wider">{group.label}</span>
                              </div>
                              {group.items.map(preset => (
                                <button
                                  key={preset.id}
                                  onClick={() => { applyPreset(preset); setShowPresetMenu(false); }}
                                  className={`w-full text-left px-3 py-2.5 transition-colors border-b border-zinc-50 dark:border-zinc-800/50 ${
                                    selectedPresetId === preset.id
                                      ? 'bg-pink-50 dark:bg-pink-900/20 border-l-2 border-l-pink-500'
                                      : 'hover:bg-zinc-50 dark:hover:bg-zinc-800/50'
                                  }`}
                                >
                                  <div className="flex items-center gap-2">
                                    <Bookmark size={12} className={selectedPresetId === preset.id ? 'text-pink-600 dark:text-pink-400 fill-pink-600 dark:fill-pink-400' : 'text-pink-500'} />
                                    <div className="flex-1 min-w-0">
                                      <p className={`text-xs font-medium truncate ${selectedPresetId === preset.id ? 'text-pink-700 dark:text-pink-300' : 'text-zinc-900 dark:text-white'}`}>{preset.name}</p>
                                      {preset.description && (
                                        <p className="text-[10px] text-zinc-400 dark:text-zinc-500 line-clamp-2">{preset.description}</p>
                                      )}
                                    </div>
                                    {selectedPresetId === preset.id && (
                                      <span className="text-[8px] font-bold px-1.5 py-0.5 bg-pink-600 text-white rounded-full flex-shrink-0">✓</span>
                                    )}
                                  </div>
                                </button>
                              ))}
                            </div>
                          ))}
                          {customPresets.length > 0 && (
                            <div>
                              <div className="px-3 py-1.5 bg-zinc-50 dark:bg-zinc-800/50 border-b border-zinc-100 dark:border-zinc-800">
                                <span className="text-[10px] font-semibold text-zinc-400 dark:text-zinc-500 tracking-wider">{t('customPresets')}</span>
                              </div>
                              {customPresets.map(preset => (
                                <div
                                  key={preset.id}
                                  className={`flex items-center px-3 py-2.5 transition-colors border-b border-zinc-50 dark:border-zinc-800/50 group ${
                                    selectedPresetId === preset.id
                                      ? 'bg-blue-50 dark:bg-blue-900/20 border-l-2 border-l-blue-500'
                                      : 'hover:bg-zinc-50 dark:hover:bg-zinc-800/50'
                                  }`}
                                >
                                  <button
                                    onClick={() => { applyPreset(preset); setShowPresetMenu(false); }}
                                    className="flex-1 text-left flex items-center gap-2 min-w-0"
                                  >
                                    <Bookmark size={12} className={selectedPresetId === preset.id ? 'text-blue-600 dark:text-blue-400 fill-blue-600 dark:fill-blue-400' : 'text-blue-500 flex-shrink-0'} />
                                    <div className="flex-1 min-w-0">
                                      <p className={`text-xs font-medium truncate ${selectedPresetId === preset.id ? 'text-blue-700 dark:text-blue-300' : 'text-zinc-900 dark:text-white'}`}>{preset.name}</p>
                                      {preset.description && (
                                        <p className="text-[10px] text-zinc-400 dark:text-zinc-500 line-clamp-2">{preset.description}</p>
                                      )}
                                    </div>
                                    {selectedPresetId === preset.id && (
                                      <span className="text-[8px] font-bold px-1.5 py-0.5 bg-blue-600 text-white rounded-full flex-shrink-0">✓</span>
                                    )}
                                  </button>
                                  <button
                                    onClick={async (e) => {
                                      e.stopPropagation();
                                      if (!token) return;
                                      try {
                                        await presetsApi.deletePreset(preset.id, token);
                                        setPresets(prev => prev.filter(p => p.id !== preset.id));
                                        if (selectedPresetId === preset.id) setSelectedPresetId(null);
                                      } catch {}
                                    }}
                                    className="opacity-0 group-hover:opacity-100 p-1 text-zinc-400 hover:text-red-500 transition-all"
                                    title={t('delete')}
                                  >
                                    <Trash2 size={12} />
                                  </button>
                                </div>
                              ))}
                            </div>
                          )}
                        </>
                      );
                    })()
                  )}
                </div>
              </div>
            )}
          </div>
        </div>

        {/* SIMPLE MODE */}
        {!customMode && (
          <div className="space-y-5">
            {/* Song Description */}
            <div className="bg-white dark:bg-suno-card rounded-xl border border-zinc-200 dark:border-white/5 overflow-hidden">
              <div className="px-3 py-2.5 text-xs font-bold uppercase tracking-wide text-zinc-500 dark:text-zinc-400 border-b border-zinc-100 dark:border-white/5 bg-zinc-50 dark:bg-white/5">
                {t('describeYourSong')}
              </div>
              <textarea
                value={songDescription}
                onChange={(e) => { setSongDescription(e.target.value); localStorage.setItem('ace-songDescription', e.target.value); }}
                placeholder={t('songDescriptionPlaceholder')}
                className="w-full h-32 bg-transparent p-3 text-sm text-zinc-900 dark:text-white placeholder-zinc-400 dark:placeholder-zinc-600 focus:outline-none resize-none"
              />
            </div>

            {/* Vocal Language (Simple) */}
            <div className="bg-white dark:bg-suno-card rounded-xl border border-zinc-200 dark:border-white/5 overflow-hidden">
              <div className="px-3 py-2.5 text-xs font-bold uppercase tracking-wide text-zinc-500 dark:text-zinc-400 border-b border-zinc-100 dark:border-white/5 bg-zinc-50 dark:bg-white/5">
                {t('vocalLanguage')}
              </div>
              <div className="flex flex-wrap items-center gap-2 p-3">
                <select
                  value={vocalLanguage}
                  onChange={(e) => { setVocalLanguage(e.target.value); localStorage.setItem('ace-vocalLanguage', e.target.value); }}
                  className="flex-1 min-w-[180px] bg-transparent text-sm text-zinc-900 dark:text-white focus:outline-none"
                >
                  {VOCAL_LANGUAGE_KEYS.map(lang => (
                    <option key={lang.value} value={lang.value}>{lang.key}</option>
                  ))}
                </select>
                <div className="flex items-center gap-2">
                  <button
                    type="button"
                    onClick={() => { const newVal = vocalGender === 'male' ? '' : 'male'; setVocalGender(newVal); localStorage.setItem('ace-vocalGender', newVal); }}
                    className={`px-3 py-1.5 rounded-full text-xs font-semibold border transition-colors ${vocalGender === 'male' ? 'bg-pink-600 text-white border-pink-600' : 'border-zinc-200 dark:border-white/10 text-zinc-600 dark:text-zinc-300 hover:border-zinc-300 dark:hover:border-white/20'}`}
                  >
                    {t('male')}
                  </button>
                  <button
                    type="button"
                    onClick={() => { const newVal = vocalGender === 'female' ? '' : 'female'; setVocalGender(newVal); localStorage.setItem('ace-vocalGender', newVal); }}
                    className={`px-3 py-1.5 rounded-full text-xs font-semibold border transition-colors ${vocalGender === 'female' ? 'bg-pink-600 text-white border-pink-600' : 'border-zinc-200 dark:border-white/10 text-zinc-600 dark:text-zinc-300 hover:border-zinc-300 dark:hover:border-white/20'}`}
                  >
                    {t('female')}
                  </button>
                </div>
              </div>
            </div>

            {/* Quick Settings (Simple Mode) */}
            <div className="bg-white dark:bg-suno-card rounded-xl border border-zinc-200 dark:border-white/5 p-4 space-y-4">
              <h3 className="text-xs font-bold text-zinc-500 dark:text-zinc-400 uppercase tracking-wide flex items-center gap-2">
                <Sliders size={14} />
                {t('quickSettings')}
              </h3>

              {/* Duration */}
              <EditableSlider
                label={t('duration')}
                value={duration}
                min={-1}
                max={600}
                step={5}
                onChange={(val) => { setDuration(val); localStorage.setItem('ace-duration', val.toString()); }}
                formatDisplay={(val) => val === -1 ? t('auto') : `${val}${t('seconds')}`}
                title={''}
                autoLabel={t('auto')}
              />

              {/* BPM */}
              <EditableSlider
                label="BPM"
                value={bpm}
                min={0}
                max={300}
                step={5}
                onChange={(val) => { setBpm(val); localStorage.setItem('ace-bpm', val.toString()); }}
                formatDisplay={(val) => val === 0 ? t('auto') : val.toString()}
                autoLabel={t('auto')}
              />

              {/* Key & Time Signature */}
              <div className="grid grid-cols-2 gap-3">
                <div className="space-y-1.5">
                  <label className="text-xs font-medium text-zinc-600 dark:text-zinc-400">{t('key')}</label>
                  <select
                    value={keyScale}
                    onChange={(val) => { setKeyScale(val); localStorage.setItem('ace-keyScale', val); }}
                    className="w-full bg-zinc-50 dark:bg-black/20 border border-zinc-200 dark:border-white/10 rounded-xl px-2 py-1.5 text-xs text-zinc-900 dark:text-white focus:outline-none focus:border-pink-500 dark:focus:border-pink-500 transition-colors cursor-pointer [&>option]:bg-white [&>option]:dark:bg-zinc-800 [&>option]:text-zinc-900 [&>option]:dark:text-white"
                  >
                    <option value="">{t('auto')}</option>
                    {KEY_SIGNATURES.filter(k => k).map(key => (
                      <option key={key} value={key}>{key}</option>
                    ))}
                  </select>
                </div>
                <div className="space-y-1.5">
                  <label className="text-xs font-medium text-zinc-600 dark:text-zinc-400">{t('time')}</label>
                  <select
                    value={timeSignature}
                    onChange={(val) => { setTimeSignature(val); localStorage.setItem('ace-timeSignature', val); }}
                    className="w-full bg-zinc-50 dark:bg-black/20 border border-zinc-200 dark:border-white/10 rounded-xl px-2 py-1.5 text-xs text-zinc-900 dark:text-white focus:outline-none focus:border-pink-500 dark:focus:border-pink-500 transition-colors cursor-pointer [&>option]:bg-white [&>option]:dark:bg-zinc-800 [&>option]:text-zinc-900 [&>option]:dark:text-white"
                  >
                    <option value="">{t('auto')}</option>
                    {TIME_SIGNATURES.filter(t => t).map(time => (
                      <option key={time} value={time}>{time}</option>
                    ))}
                  </select>
                </div>
              </div>

              {/* Variations */}
              <EditableSlider
                label={t('variations')}
                value={batchSize}
                min={1}
                max={8}
                step={1}
                onChange={(val) => { setBatchSize(val); localStorage.setItem('ace-batchSize', val.toString()); }}
              />
              <div style={{display: 'none'}}>
                <input
                  type="range"
                  min="1"
                  max="8"
                  step="1"
                  value={batchSize}
                  onChange={(val) => { setBatchSize(val); localStorage.setItem('ace-batchSize', val.toString()); }}
                  className="w-full h-2 bg-zinc-200 dark:bg-zinc-700 rounded-lg appearance-none cursor-pointer accent-pink-500"
                />
                <p className="text-[10px] text-zinc-500">{t('numberOfVariations')}</p>
              </div>
            </div>
          </div>
        )}

        {/* CUSTOM MODE */}
        {customMode && (
          <div className="space-y-5">
            {/* Audio Section */}
            <div
              ref={audioSectionRef}
              onDrop={(e) => handleDrop(e, audioTab)}
              onDragOver={handleDragOver}
              className={`bg-white dark:bg-[#1a1a1f] rounded-xl border overflow-hidden transition-all duration-300 ${
                sourceHintActive
                  ? 'border-amber-400 ring-2 ring-amber-400/60 shadow-lg shadow-amber-400/20 animate-pulse'
                  : 'border-zinc-200 dark:border-white/5'
              }`}
            >
              {/* Header with Audio label and tabs */}
              <div className="px-3 py-2.5 border-b border-zinc-100 dark:border-white/5 bg-zinc-50 dark:bg-white/[0.02]">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-zinc-500 dark:text-zinc-400 uppercase tracking-wide">{t('audio')}</span>
                  <div className="flex items-center gap-1 bg-zinc-200/50 dark:bg-black/30 rounded-lg p-0.5">
                    <button
                      type="button"
                      onClick={() => setAudioTab('reference')}
                      className={`px-2.5 py-1 rounded-md text-[11px] font-medium transition-all ${
                        audioTab === 'reference'
                          ? 'bg-white dark:bg-zinc-700 text-zinc-900 dark:text-white shadow-sm'
                          : 'text-zinc-500 dark:text-zinc-400 hover:text-zinc-700 dark:hover:text-zinc-200'
                      }`}
                    >
                      {t('reference')}
                    </button>
                    <button
                      type="button"
                      onClick={() => setAudioTab('source')}
                      className={`px-2.5 py-1 rounded-md text-[11px] font-medium transition-all ${
                        audioTab === 'source'
                          ? 'bg-white dark:bg-zinc-700 text-zinc-900 dark:text-white shadow-sm'
                          : 'text-zinc-500 dark:text-zinc-400 hover:text-zinc-700 dark:hover:text-zinc-200'
                      }`}
                    >
                      {t('cover')}
                    </button>
                  </div>
                </div>
              </div>

              {/* Cover / audio2audio guidance: tell the user to upload source audio */}
              {(taskType === 'cover' || taskType === 'audio2audio') && !sourceAudioUrl.trim() && !audioCodes.trim() && (
                <div className={`px-3 py-2.5 border-b flex items-start gap-2 transition-colors ${
                  sourceHintActive
                    ? 'bg-amber-100 dark:bg-amber-500/20 border-amber-300 dark:border-amber-500/40'
                    : 'bg-amber-50 dark:bg-amber-500/10 border-amber-200 dark:border-amber-500/20'
                }`}>
                  <svg className="w-4 h-4 text-amber-500 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
                  <div className="flex-1 min-w-0">
                    <p className="text-[11px] leading-relaxed text-amber-700 dark:text-amber-300">
                      <span className="font-bold">翻唱模式需要「{t('cover')}」（内容参考）源音频。</span> 请上传您想要翻唱的原曲后再点击创建；未上传源音频无法生成。
                    </p>
                    <button
                      type="button"
                      onClick={() => { setAudioTab('source'); sourceInputRef.current?.click(); }}
                      className="mt-1.5 inline-flex items-center gap-1 rounded-md bg-amber-500 hover:bg-amber-600 text-white px-2.5 py-1 text-[11px] font-semibold transition-colors"
                    >
                      <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1M12 12V4m0 0L8 8m4-4l4 4" /></svg>
                      立即上传内容参考
                    </button>
                  </div>
                </div>
              )}

              {/* Audio Content */}
              <div className="p-3 space-y-2">
                {/* Reference Audio Player */}
                {audioTab === 'reference' && referenceAudioUrl && (
                  <div className="flex items-center gap-3 p-2 rounded-lg bg-zinc-50 dark:bg-white/[0.03] border border-zinc-100 dark:border-white/5">
                    <button
                      type="button"
                      onClick={() => toggleAudio('reference')}
                      className="relative flex-shrink-0 w-10 h-10 rounded-full bg-gradient-to-br from-pink-500 to-purple-600 text-white flex items-center justify-center shadow-lg shadow-pink-500/20 hover:scale-105 transition-transform"
                    >
                      {referencePlaying ? (
                        <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24"><path d="M6 4h4v16H6V4zm8 0h4v16h-4V4z"/></svg>
                      ) : (
                        <svg className="w-4 h-4 ml-0.5" fill="currentColor" viewBox="0 0 24 24"><path d="M8 5v14l11-7z"/></svg>
                      )}
                      <span className="absolute -bottom-1 -right-1 text-[8px] font-bold bg-zinc-900 text-white px-1 py-0.5 rounded">
                        {formatTime(referenceDuration)}
                      </span>
                    </button>
                    <div className="flex-1 min-w-0">
                      <div className="text-xs font-medium text-zinc-800 dark:text-zinc-200 truncate mb-1.5">
                        {referenceAudioTitle || getAudioLabel(referenceAudioUrl)}
                      </div>
                      <div className="flex items-center gap-2">
                        <span className="text-[10px] text-zinc-400 tabular-nums">{formatTime(referenceTime)}</span>
                        <div
                          className="flex-1 h-1.5 rounded-full bg-zinc-200 dark:bg-white/10 cursor-pointer group/seek"
                          onClick={(e) => {
                            if (referenceAudioRef.current && referenceDuration > 0) {
                              const rect = e.currentTarget.getBoundingClientRect();
                              const percent = (e.clientX - rect.left) / rect.width;
                              referenceAudioRef.current.currentTime = percent * referenceDuration;
                            }
                          }}
                        >
                          <div
                            className="h-full bg-gradient-to-r from-pink-500 to-purple-500 rounded-full transition-all relative"
                            style={{ width: referenceDuration ? `${Math.min(100, (referenceTime / referenceDuration) * 100)}%` : '0%' }}
                          >
                            <div className="absolute right-0 top-1/2 -translate-y-1/2 w-2.5 h-2.5 rounded-full bg-white shadow-md opacity-0 group-hover/seek:opacity-100 transition-opacity" />
                          </div>
                        </div>
                        <span className="text-[10px] text-zinc-400 tabular-nums">{formatTime(referenceDuration)}</span>
                      </div>
                    </div>
                    <button
                      type="button"
                      onClick={() => { setReferenceAudioUrl(''); setReferenceAudioTitle(''); setReferencePlaying(false); setReferenceTime(0); setReferenceDuration(0); }}
                      className="p-1.5 rounded-full hover:bg-zinc-200 dark:hover:bg-white/10 text-zinc-400 hover:text-zinc-600 dark:hover:text-white transition-colors"
                    >
                      <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12"/></svg>
                    </button>
                  </div>
                )}

                {/* Source/Cover Audio Player */}
                {audioTab === 'source' && sourceAudioUrl && (
                  <div className="flex items-center gap-3 p-2 rounded-lg bg-zinc-50 dark:bg-white/[0.03] border border-zinc-100 dark:border-white/5">
                    <button
                      type="button"
                      onClick={() => toggleAudio('source')}
                      className="relative flex-shrink-0 w-10 h-10 rounded-full bg-gradient-to-br from-emerald-500 to-teal-600 text-white flex items-center justify-center shadow-lg shadow-emerald-500/20 hover:scale-105 transition-transform"
                    >
                      {sourcePlaying ? (
                        <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24"><path d="M6 4h4v16H6V4zm8 0h4v16h-4V4z"/></svg>
                      ) : (
                        <svg className="w-4 h-4 ml-0.5" fill="currentColor" viewBox="0 0 24 24"><path d="M8 5v14l11-7z"/></svg>
                      )}
                      <span className="absolute -bottom-1 -right-1 text-[8px] font-bold bg-zinc-900 text-white px-1 py-0.5 rounded">
                        {formatTime(sourceDuration)}
                      </span>
                    </button>
                    <div className="flex-1 min-w-0">
                      <div className="text-xs font-medium text-zinc-800 dark:text-zinc-200 truncate mb-1.5">
                        {sourceAudioTitle || getAudioLabel(sourceAudioUrl)}
                      </div>
                      <div className="flex items-center gap-2">
                        <span className="text-[10px] text-zinc-400 tabular-nums">{formatTime(sourceTime)}</span>
                        <div
                          className="flex-1 h-1.5 rounded-full bg-zinc-200 dark:bg-white/10 cursor-pointer group/seek"
                          onClick={(e) => {
                            if (sourceAudioRef.current && sourceDuration > 0) {
                              const rect = e.currentTarget.getBoundingClientRect();
                              const percent = (e.clientX - rect.left) / rect.width;
                              sourceAudioRef.current.currentTime = percent * sourceDuration;
                            }
                          }}
                        >
                          <div
                            className="h-full bg-gradient-to-r from-emerald-500 to-teal-500 rounded-full transition-all relative"
                            style={{ width: sourceDuration ? `${Math.min(100, (sourceTime / sourceDuration) * 100)}%` : '0%' }}
                          >
                            <div className="absolute right-0 top-1/2 -translate-y-1/2 w-2.5 h-2.5 rounded-full bg-white shadow-md opacity-0 group-hover/seek:opacity-100 transition-opacity" />
                          </div>
                        </div>
                        <span className="text-[10px] text-zinc-400 tabular-nums">{formatTime(sourceDuration)}</span>
                      </div>
                    </div>
                    <button
                      type="button"
                      onClick={() => { setSourceAudioUrl(''); setSourceAudioTitle(''); setSourcePlaying(false); setSourceTime(0); setSourceDuration(0); if (taskType === 'cover') setTaskType('text2music'); }}
                      className="p-1.5 rounded-full hover:bg-zinc-200 dark:hover:bg-white/10 text-zinc-400 hover:text-zinc-600 dark:hover:text-white transition-colors"
                    >
                      <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12"/></svg>
                    </button>
                  </div>
                )}

                {/* Action buttons */}
                <div className="flex gap-2">
                  <button
                    type="button"
                    onClick={() => openAudioModal(audioTab, 'uploads')}
                    className="flex-1 flex items-center justify-center gap-1.5 rounded-lg bg-zinc-100 dark:bg-white/5 hover:bg-zinc-200 dark:hover:bg-white/10 text-zinc-700 dark:text-zinc-300 px-3 py-2 text-xs font-medium transition-colors border border-zinc-200 dark:border-white/5"
                  >
                    <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19V6l12-3v13M9 19c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zm12-3c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zM9 10l12-3"/>
                    </svg>
                    {t('fromLibrary')}
                  </button>
                  <button
                    type="button"
                    onClick={() => {
                      const input = audioTab === 'reference' ? referenceInputRef.current : sourceInputRef.current;
                      input?.click();
                    }}
                    className="flex-1 flex items-center justify-center gap-1.5 rounded-lg bg-zinc-100 dark:bg-white/5 hover:bg-zinc-200 dark:hover:bg-white/10 text-zinc-700 dark:text-zinc-300 px-3 py-2 text-xs font-medium transition-colors border border-zinc-200 dark:border-white/5"
                  >
                    <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12"/>
                    </svg>
                    {t('upload')}
                  </button>
                </div>
              </div>
            </div>

            {/* Lyrics Input */}
            <div
              ref={lyricsRef}
              className="bg-white dark:bg-suno-card rounded-xl border border-zinc-200 dark:border-white/5 overflow-hidden transition-colors group focus-within:border-zinc-400 dark:focus-within:border-white/20 relative flex flex-col"
              style={{ height: 'auto' }}
            >
              <div className="flex items-center justify-between px-3 py-2.5 bg-zinc-50 dark:bg-white/5 border-b border-zinc-100 dark:border-white/5 flex-shrink-0">
                <div className="flex items-center">
                  <span className="text-xs font-bold text-zinc-500 dark:text-zinc-400 uppercase tracking-wide">{t('lyrics')}<HelpTip text={t('leaveLyricsEmpty')} /></span>
                </div>
                <div className="flex items-center gap-2">
                  <button
                    onClick={toggleLyricsExpand}
                    className={`p-1.5 hover:bg-zinc-200 dark:hover:bg-white/10 rounded text-zinc-500 hover:text-black dark:hover:text-white transition-colors ${lyricsExpanded ? 'text-pink-500 hover:text-pink-600' : ''}`}
                    title={lyricsExpanded ? t('collapse') : t('expand')}
                  >
                    {lyricsExpanded ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
                  </button>
                  <button
                    onClick={() => { setInstrumental(!instrumental); localStorage.setItem('ace-instrumental', (!instrumental).toString()); }}
                    className={`px-2.5 py-1 rounded-full text-[10px] font-semibold border transition-colors ${
                      instrumental
                        ? 'bg-pink-600 text-white border-pink-500'
                        : 'bg-white dark:bg-suno-card border-zinc-200 dark:border-white/10 text-zinc-600 dark:text-zinc-200 hover:bg-zinc-100 dark:hover:bg-white/10'
                    }`}
                  >
                    {instrumental ? t('instrumental') : t('vocal')}
                  </button>
                  <button
                    className={`p-1.5 hover:bg-zinc-200 dark:hover:bg-white/10 rounded transition-colors ${isFormattingLyrics ? 'text-pink-500' : 'text-zinc-500 hover:text-black dark:hover:text-white'}`}
                    title="AI Format - Enhance style & auto-fill parameters"
                    onClick={() => handleFormat('lyrics')}
                    disabled={isFormattingLyrics || !style.trim()}
                  >
                    {isFormattingLyrics ? <Loader2 size={14} className="animate-spin" /> : <Sparkles size={14} />}
                  </button>
                  <button
                    className="p-1.5 hover:bg-zinc-200 dark:hover:bg-white/10 rounded text-zinc-500 hover:text-black dark:hover:text-white transition-colors"
                    onClick={() => setLyrics('')}
                  >
                    <Trash2 size={14} />
                  </button>
                </div>
              </div>
              <textarea
                ref={lyricsTextareaRef}
                disabled={instrumental}
                value={lyrics}
                onChange={(e) => { setLyrics(e.target.value); localStorage.setItem('ace-lyrics', e.target.value); }}
                placeholder={instrumental ? t('instrumental') + ' mode' : t('lyricsPlaceholder')}
                className={`w-full bg-transparent p-3 text-sm text-zinc-900 dark:text-white placeholder-zinc-400 dark:placeholder-zinc-600 focus:outline-none resize-none font-mono leading-relaxed ${instrumental ? 'opacity-30 cursor-not-allowed' : ''}`}
                style={{ height: `${lyricsHeight}px`, maxHeight: `${MAX_HEIGHT}px` }}
              />
              <div
                onMouseDown={(e) => startResizing(e, 'lyrics')}
                className="h-3 w-full cursor-ns-resize flex items-center justify-center hover:bg-zinc-100 dark:hover:bg-white/5 transition-colors absolute bottom-0 left-0 z-10"
              >
                <div className="w-8 h-1 rounded-full bg-zinc-300 dark:bg-zinc-700"></div>
              </div>
            </div>

            {/* Style Input */}
            <div
              ref={styleRef}
              className="bg-white dark:bg-suno-card rounded-xl border border-zinc-200 dark:border-white/5 overflow-hidden transition-colors group focus-within:border-zinc-400 dark:focus-within:border-white/20 relative flex flex-col"
            >
              <div className="flex items-center justify-between px-3 py-2.5 bg-zinc-50 dark:bg-white/5 border-b border-zinc-100 dark:border-white/5 flex-shrink-0">
                <div className="flex items-center">
                  <span className="text-xs font-bold text-zinc-500 dark:text-zinc-400 uppercase tracking-wide">{t('styleOfMusic')}<HelpTip text={t('genreMoodInstruments')} /></span>
                </div>
                <div className="flex items-center gap-1">
                  <button
                    onClick={toggleStyleExpand}
                    className={`p-1.5 hover:bg-zinc-200 dark:hover:bg-white/10 rounded text-zinc-500 hover:text-black dark:hover:text-white transition-colors ${styleExpanded ? 'text-pink-500 hover:text-pink-600' : ''}`}
                    title={styleExpanded ? t('collapse') : t('expand')}
                  >
                    {styleExpanded ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
                  </button>
                  <button
                    className="p-1.5 hover:bg-zinc-200 dark:hover:bg-white/10 rounded transition-colors text-zinc-500 hover:text-black dark:hover:text-white"
                    title={t('refreshGenres')}
                    onClick={refreshMusicTags}
                  >
                    <Dices size={14} />
                  </button>
                  <button
                    className="p-1.5 hover:bg-zinc-200 dark:hover:bg-white/10 rounded text-zinc-500 hover:text-black dark:hover:text-white transition-colors"
                    onClick={() => setStyle('')}
                  >
                    <Trash2 size={14} />
                  </button>
                </div>
                <button
                  className={`p-1.5 hover:bg-zinc-200 dark:hover:bg-white/10 rounded transition-colors ${isFormattingStyle ? 'text-pink-500' : 'text-zinc-500 hover:text-black dark:hover:text-white'}`}
                  title="AI Format - Enhance style & auto-fill parameters"
                  onClick={() => handleFormat('style')}
                  disabled={isFormattingStyle || !style.trim()}
                >
                  {isFormattingStyle ? <Loader2 size={14} className="animate-spin" /> : <Sparkles size={14} />}
                </button>
              </div>
              <textarea
                ref={styleTextareaRef}
                value={style}
                onChange={(e) => { setStyle(e.target.value); localStorage.setItem('ace-style', e.target.value); }}
                placeholder={t('stylePlaceholder')}
                className="w-full bg-transparent p-3 text-sm text-zinc-900 dark:text-white placeholder-zinc-400 dark:placeholder-zinc-600 focus:outline-none resize-none overflow-y-auto"
                style={{ height: `${styleHeight}px`, maxHeight: `${MAX_HEIGHT}px` }}
              />
              <div
                onMouseDown={(e) => startResizing(e, 'style')}
                className="h-3 w-full cursor-ns-resize flex items-center justify-center hover:bg-zinc-100 dark:hover:bg-white/5 transition-colors flex-shrink-0"
              >
                <div className="w-8 h-1 rounded-full bg-zinc-300 dark:bg-zinc-700"></div>
              </div>
              <div className="px-3 pb-3 space-y-3">
                {/* Cascading Genre Selector */}
                <div className="space-y-2">
                  {/* First Level: Main Genre */}
                  <div className="flex gap-2">
                    <select
                      value={selectedMainGenre}
                      onChange={(e) => {
                        setSelectedMainGenre(e.target.value);
                        setSelectedSubGenre(''); // Reset sub genre when main changes
                        if (e.target.value) {
                          setStyle(prev => prev ? `${prev}, ${e.target.value}` : e.target.value);
                        }
                      }}
                      className="flex-1 bg-zinc-50 dark:bg-black/20 border border-zinc-200 dark:border-white/10 rounded-xl px-2 py-1.5 text-xs text-zinc-900 dark:text-white focus:outline-none focus:border-pink-500 dark:focus:border-pink-500 transition-colors cursor-pointer [&>option]:bg-white [&>option]:dark:bg-zinc-800 [&>option]:text-zinc-900 [&>option]:dark:text-white"
                    >
                      <option value="">{t('mainGenre')}</option>
                      {MAIN_STYLES.map(genre => {
                        const meta = getStyleMeta(genre);
                        return (
                          <option key={genre} value={genre}>
                            {meta ? `${genre} · ${meta.zh}` : genre}
                          </option>
                        );
                      })}
                    </select>
                    {selectedMainGenre && (
                      <button
                        onClick={() => {
                          setSelectedMainGenre('');
                          setSelectedSubGenre('');
                        }}
                        className="px-2 py-1.5 text-xs text-zinc-500 hover:text-zinc-900 dark:hover:text-white transition-colors"
                        title={t('cancel')}
                      >
                        ✕
                      </button>
                    )}
                  </div>
                  
                  {/* Second Level: Sub Genre (only show when main genre is selected) */}
                  {selectedMainGenre && filteredSubGenres.length > 0 && (
                    <div className="flex gap-2 pl-4 border-l-2 border-zinc-200 dark:border-white/10">
                      <select
                        value={selectedSubGenre}
                        onChange={(e) => {
                          setSelectedSubGenre(e.target.value);
                          if (e.target.value) {
                            setStyle(prev => prev ? `${prev}, ${e.target.value}` : e.target.value);
                          }
                        }}
                        className="flex-1 bg-zinc-50 dark:bg-black/20 border border-zinc-200 dark:border-white/10 rounded-xl px-2 py-1.5 text-xs text-zinc-900 dark:text-white focus:outline-none focus:border-pink-500 dark:focus:border-pink-500 transition-colors cursor-pointer [&>option]:bg-white [&>option]:dark:bg-zinc-800 [&>option]:text-zinc-900 [&>option]:dark:text-white"
                      >
                        <option value="">{t('subGenre')} ({filteredSubGenres.length})</option>
                        {filteredSubGenres.map(genre => {
                          const meta = getStyleMeta(genre);
                          return (
                            <option key={genre} value={genre}>
                              {meta ? `${genre} · ${meta.zh}` : genre}
                            </option>
                          );
                        })}
                      </select>
                      {selectedSubGenre && (
                        <button
                          onClick={() => setSelectedSubGenre('')}
                          className="px-2 py-1.5 text-xs text-zinc-500 hover:text-zinc-900 dark:hover:text-white transition-colors"
                          title={t('cancel')}
                        >
                          ✕
                        </button>
                      )}
                    </div>
                  )}
                </div>
                {/* Quick Tags */}
                <div className="flex flex-wrap gap-2">
                  {musicTags.map(tag => {
                    const meta = getStyleMeta(tag);
                    return (
                      <button
                        key={tag}
                        onClick={() => setStyle(prev => prev ? `${prev}, ${tag}` : tag)}
                        className="text-[10px] font-medium bg-zinc-100 dark:bg-white/5 hover:bg-zinc-200 dark:hover:bg-white/10 text-zinc-600 dark:text-zinc-400 hover:text-black dark:hover:text-white px-2.5 py-1 rounded-full transition-colors border border-zinc-200 dark:border-white/5"
                        title={meta?.desc || ''}
                      >
                        {meta ? `${tag} · ${meta.zh}` : tag}
                      </button>
                    );
                  })}
                </div>
              </div>
            </div>

            {/* Title Input */}
            <div className="bg-white dark:bg-suno-card rounded-xl border border-zinc-200 dark:border-white/5 overflow-hidden">
              <div className="px-3 py-2.5 text-xs font-bold uppercase tracking-wide text-zinc-500 dark:text-zinc-400 border-b border-zinc-100 dark:border-white/5 bg-zinc-50 dark:bg-white/5">
                {t('title')}
              </div>
              <input
                type="text"
                value={title}
                onChange={(e) => { setTitle(e.target.value); localStorage.setItem('ace-title', e.target.value); }}
                placeholder={t('nameSong')}
                className="w-full bg-transparent p-3 text-sm text-zinc-900 dark:text-white placeholder-zinc-400 dark:placeholder-zinc-600 focus:outline-none"
              />
            </div>
          </div>
        )}

        {/* COMMON SETTINGS */}
        <div className="space-y-4">
          {/* Instrumental Toggle (Simple Mode) */}
          {!customMode && (
            <div className="flex items-center justify-between px-1 py-2">
              <div className="flex items-center gap-2">
                <Music2 size={14} className="text-zinc-500" />
                <span className="text-sm font-medium text-zinc-700 dark:text-zinc-300">{t('instrumental')}</span>
              </div>
              <button
                onClick={() => { setInstrumental(!instrumental); localStorage.setItem('ace-instrumental', (!instrumental).toString()); }}
                className={`w-11 h-6 rounded-full flex items-center transition-colors duration-200 px-1 border border-zinc-200 dark:border-white/5 ${instrumental ? 'bg-pink-600' : 'bg-zinc-300 dark:bg-black/40'}`}
              >
                <div className={`w-4 h-4 rounded-full bg-white transform transition-transform duration-200 shadow-sm ${instrumental ? 'translate-x-5' : 'translate-x-0'}`} />
              </button>
            </div>
          )}

          {/* Vocal Language (Custom mode) */}
          {customMode && !instrumental && (
            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-1.5">
                <label className="text-xs font-bold text-zinc-500 dark:text-zinc-400 uppercase tracking-wide px-1">
                  {t('vocalLanguage')}
                </label>
                <select
                  value={vocalLanguage}
                  onChange={(e) => { setVocalLanguage(e.target.value); localStorage.setItem('ace-vocalLanguage', e.target.value); }}
                  className="w-full bg-white dark:bg-suno-card border border-zinc-200 dark:border-white/5 rounded-xl px-3 py-2 text-sm text-zinc-900 dark:text-white focus:outline-none focus:border-pink-500 dark:focus:border-pink-500 transition-colors cursor-pointer [&>option]:bg-white [&>option]:dark:bg-zinc-800 [&>option]:text-zinc-900 [&>option]:dark:text-white"
                >
                  {VOCAL_LANGUAGE_KEYS.map(lang => (
                    <option key={lang.value} value={lang.value}>{t(lang.key)}</option>
                  ))}
                </select>
              </div>
              <div className="space-y-1.5">
                <label className="text-xs font-bold text-zinc-500 dark:text-zinc-400 uppercase tracking-wide px-1">
                  {t('vocalGender')}
                </label>
                <div className="flex items-center gap-2">
                  <button
                    type="button"
                    onClick={() => { const newVal = vocalGender === 'male' ? '' : 'male'; setVocalGender(newVal); localStorage.setItem('ace-vocalGender', newVal); }}
                    className={`flex-1 px-3 py-2 rounded-lg text-xs font-semibold border transition-colors ${vocalGender === 'male' ? 'bg-pink-600 text-white border-pink-600' : 'border-zinc-200 dark:border-white/10 text-zinc-600 dark:text-zinc-300 hover:border-zinc-300 dark:hover:border-white/20'}`}
                  >
                    {t('male')}
                  </button>
                  <button
                    type="button"
                    onClick={() => { const newVal = vocalGender === 'female' ? '' : 'female'; setVocalGender(newVal); localStorage.setItem('ace-vocalGender', newVal); }}
                    className={`flex-1 px-3 py-2 rounded-lg text-xs font-semibold border transition-colors ${vocalGender === 'female' ? 'bg-pink-600 text-white border-pink-600' : 'border-zinc-200 dark:border-white/10 text-zinc-600 dark:text-zinc-300 hover:border-zinc-300 dark:hover:border-white/20'}`}
                  >
                    {t('female')}
                  </button>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* LORA CONTROL PANEL */}
        {customMode && (
          <>
            <div className="flex items-center justify-between px-4 py-3 bg-white dark:bg-suno-card rounded-xl border border-zinc-200 dark:border-white/5">
              <div className="flex items-center gap-2">
                <button
                  type="button"
                  role="switch"
                  aria-checked={loraLoaded}
                  onClick={handleLoraToggle}
                  disabled={isLoraLoading}
                  className={`relative w-9 h-5 rounded-full transition-colors duration-200 focus:outline-none disabled:opacity-40 disabled:cursor-not-allowed ${
                    loraLoaded ? 'bg-pink-600' : 'bg-zinc-300 dark:bg-zinc-700'
                  }`}
                >
                  <span
                    className={`absolute top-0.5 left-0.5 w-4 h-4 rounded-full bg-white shadow transition-transform duration-200 ${
                      loraLoaded ? 'translate-x-4' : 'translate-x-0'
                    }`}
                  />
                </button>
                <span className={`text-sm font-medium ${loraLoaded ? 'text-pink-600 dark:text-pink-400' : 'text-zinc-700 dark:text-zinc-300'}`}>
                  LoRA
                </span>
                {isLoraLoading && <span className="text-[10px] text-zinc-400">...</span>}
              </div>
              <button
                onClick={() => {
                  const next = !showLoraPanel;
                  setShowLoraPanel(next);
                  localStorage.setItem('ace-loraEnabled', next.toString());
                }}
                className="p-1 hover:bg-zinc-100 dark:hover:bg-white/5 rounded transition-colors"
              >
                <ChevronDown size={16} className={`text-zinc-500 transition-transform ${showLoraPanel ? 'rotate-180' : ''}`} />
              </button>
            </div>

            {showLoraPanel && (
              <div className="bg-white dark:bg-suno-card rounded-xl border border-zinc-200 dark:border-white/5 p-4 space-y-4">
                {/* LoRA Selector */}
                <div className="space-y-2">
                  <label className="text-xs font-medium text-zinc-600 dark:text-zinc-400">{t('loraPath')}</label>
                  <div className="relative" ref={loraMenuRef}>
                    <button
                      onClick={() => setShowLoraMenu(!showLoraMenu)}
                      className="w-full bg-zinc-50 dark:bg-black/20 border border-zinc-200 dark:border-white/10 rounded-lg px-3 py-2 text-xs text-zinc-900 dark:text-white hover:bg-zinc-100 dark:hover:bg-black/30 transition-colors flex items-center justify-between"
                    >
                      <span className="truncate">
                        {loraPath || t('selectLora') || '选择 LoRA'}
                      </span>
                      <ChevronDown size={14} className={`text-zinc-500 transition-transform flex-shrink-0 ml-2 ${showLoraMenu ? 'rotate-180' : ''}`} />
                    </button>
                    
                    {showLoraMenu && (
                      <div className="absolute z-50 mt-1 w-full bg-white dark:bg-zinc-800 border border-zinc-200 dark:border-white/10 rounded-lg shadow-2xl max-h-80 overflow-y-auto">
                        <button
                          type="button"
                          onClick={() => {
                            setShowLoraMenu(false);
                            setShowCustomLoraInput(true);
                          }}
                          className="w-full text-left px-3 py-2 text-xs border-b border-zinc-100 dark:border-white/5 text-zinc-700 dark:text-zinc-300 hover:bg-zinc-50 dark:hover:bg-white/5"
                        >
                          ✏️ {t('customPath') || '自定义路径'}
                        </button>
                        
                        {(() => {
                          const visiblePaths = showAllLoraPaths
                            ? availableLoraPaths
                            : availableLoraPaths.filter(p => p.is_final);
                          const hasNonFinal = availableLoraPaths.some(p => !p.is_final);
                          
                          return (
                            <>
                              {visiblePaths.length > 0 ? (
                                visiblePaths.map((item, index) => {
                                  const adapterCfg = item.adapter_config || {};
                                  const metaKeys = item.metadata ? Object.keys(item.metadata) : [];
                                  const loraRank = adapterCfg.r || adapterCfg.rank;
                                  const loraAlpha = adapterCfg.lora_alpha || adapterCfg.alpha;
                                  const targetModules = adapterCfg.target_modules;
                                  const modulesStr = Array.isArray(targetModules)
                                    ? targetModules.join(', ')
                                    : typeof targetModules === 'string' ? targetModules : '';
                                  
                                  return (
                                    <button
                                      key={index}
                                      type="button"
                                      onClick={() => {
                                        setLoraPath(item.path);
                                        setShowLoraMenu(false);
                                        setShowCustomLoraInput(false);
                                      }}
                                      className={`w-full text-left px-3 py-2 text-xs border-b border-zinc-100 dark:border-white/5 last:border-0 ${
                                        loraPath === item.path
                                          ? 'bg-pink-50 dark:bg-pink-900/20 text-pink-700 dark:text-pink-300'
                                          : 'text-zinc-700 dark:text-zinc-300 hover:bg-zinc-50 dark:hover:bg-white/5'
                                      }`}
                                    >
                                      <div className="flex items-center justify-between">
                                        <span className="truncate font-medium">
                                          {item.is_final && <span className="text-green-500 mr-1">✓</span>}
                                          {item.display_name}
                                        </span>
                                        <span className="text-[10px] text-zinc-400 dark:text-zinc-500 ml-2 flex-shrink-0">
                                          {item.type}
                                          {item.is_final ? ' · final' : ''}
                                        </span>
                                      </div>
                                      <div className="text-[10px] text-zinc-400 dark:text-zinc-500 truncate mt-0.5">{item.path}</div>
                                      {(loraRank || loraAlpha || modulesStr || metaKeys.length > 0) && (
                                        <div className="text-[10px] text-zinc-400 dark:text-zinc-500 mt-0.5 flex flex-wrap gap-x-2">
                                          {loraRank && <span>r={loraRank}</span>}
                                          {loraAlpha && <span>α={loraAlpha}</span>}
                                          {modulesStr && <span className="truncate max-w-[120px]">{modulesStr}</span>}
                                          {metaKeys.length > 0 && <span>{metaKeys.length} meta</span>}
                                        </div>
                                      )}
                                    </button>
                                  );
                                })
                              ) : (
                                <div className="px-3 py-3 text-xs text-zinc-500 dark:text-zinc-400">
                                  {t('noLoraFound') || '未发现 LoRA 适配器'}
                                </div>
                              )}
                              {hasNonFinal && (
                                <button
                                  type="button"
                                  onClick={() => setShowAllLoraPaths(!showAllLoraPaths)}
                                  className="w-full text-left px-3 py-2 text-[10px] text-zinc-400 dark:text-zinc-500 hover:text-zinc-600 dark:hover:text-zinc-300 border-t border-zinc-100 dark:border-white/5"
                                >
                                  {showAllLoraPaths
                                    ? (t('showFinalOnly') || '仅显示训练完成的')
                                    : (t('showAllPaths') || `显示全部 (${availableLoraPaths.filter(p => !p.is_final).length} 个中间检查点)`)}
                                </button>
                              )}
                            </>
                          );
                        })()}
                      </div>
                    )}
                  </div>
                  
                  {showCustomLoraInput && (
                    <div className="flex gap-2">
                      <input
                        type="text"
                        value={loraPath}
                        onChange={(e) => setLoraPath(e.target.value)}
                        placeholder={t('loraPathPlaceholder') || 'LoRA 路径'}
                        className="flex-1 bg-zinc-50 dark:bg-black/20 border border-zinc-200 dark:border-white/10 rounded-lg px-3 py-2 text-xs text-zinc-900 dark:text-white placeholder-zinc-400 dark:placeholder-zinc-600 focus:outline-none focus:border-pink-500 dark:focus:border-pink-500 transition-colors"
                      />
                      <button
                        onClick={() => setShowCustomLoraInput(false)}
                        className="px-2 py-1 text-xs text-zinc-500 hover:text-zinc-700 dark:hover:text-zinc-300"
                      >
                        ✕
                      </button>
                    </div>
                  )}
                </div>

                {/* LoRA Load/Unload + Trigger Word */}
                <div className="space-y-2 border-t border-zinc-100 dark:border-white/5 pt-3">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <div className={`w-2 h-2 rounded-full ${
                        loraAdapterInMemory ? 'bg-green-500 animate-pulse' : 'bg-red-500'
                      }`}></div>
                      <span className={`text-xs font-medium ${
                        loraAdapterInMemory ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'
                      }`}>
                        {loraAdapterInMemory ? (loraLoaded ? t('loraLoaded') : t('loraDisabled') || '已禁用') : t('loraUnloaded')}
                      </span>
                    </div>
                    <button
                      onClick={async () => {
                        if (!token) { setLoraError('Please sign in'); return; }
                        if (loraAdapterInMemory) {
                          setIsLoraLoading(true);
                          setLoraError(null);
                          try {
                            await generateApi.unloadLora(token);
                            setLoraLoaded(false);
                            setLoraAdapterInMemory(false);
                            localStorage.setItem('ace-loraEnabled', 'false');
                          } catch (err) {
                            setLoraError(err instanceof Error ? err.message : 'Failed to unload LoRA');
                          } finally {
                            setIsLoraLoading(false);
                          }
                        } else {
                          if (!loraPath.trim()) { setLoraError('Please enter a LoRA path'); return; }
                          setIsLoraLoading(true);
                          setLoraError(null);
                          try {
                            const result = await generateApi.loadLora({ lora_path: loraPath }, token);
                            setLoraAdapterInMemory(true);
                            await generateApi.toggleLora({ use_lora: true }, token);
                            setLoraLoaded(true);
                            localStorage.setItem('ace-loraEnabled', 'true');
                            console.log('LoRA loaded:', result?.message);
                          } catch (err) {
                            setLoraError(err instanceof Error ? err.message : 'LoRA load failed');
                          } finally {
                            setIsLoraLoading(false);
                          }
                        }
                      }}
                      disabled={isLoraLoading || (!loraAdapterInMemory && !loraPath.trim())}
                      className={`px-4 py-2 rounded-lg text-xs font-semibold transition-all disabled:opacity-40 disabled:cursor-not-allowed ${
                        loraAdapterInMemory
                          ? 'bg-gradient-to-r from-green-500 to-emerald-600 text-white shadow-lg shadow-green-500/20 hover:from-green-600 hover:to-emerald-700'
                          : 'bg-zinc-100 dark:bg-zinc-800 text-zinc-600 dark:text-zinc-400 hover:bg-zinc-200 dark:hover:bg-zinc-700'
                      }`}
                    >
                      {isLoraLoading ? '...' : (loraAdapterInMemory ? t('loraUnload') : t('loraLoad'))}
                    </button>
                  </div>
                  {currentLoraHints?.trigger_word && loraPath && (
                    <div className="flex items-center gap-1.5">
                      <span className="text-[10px] text-zinc-500 dark:text-zinc-400">{t('triggerWordLabel') || '触发词'}:</span>
                      <code className="px-1.5 py-0.5 bg-pink-50 dark:bg-pink-900/30 rounded text-[10px] font-mono text-pink-700 dark:text-pink-300 border border-pink-200 dark:border-pink-800/40">
                        {currentLoraHints.trigger_word}
                      </code>
                      <span className="text-[10px] text-zinc-400 dark:text-zinc-500">
                        {t('autoInsertTrigger') || '已自动生效'}
                      </span>
                    </div>
                  )}
                  {loraError && (
                    <div className="text-xs text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-900/20 px-2 py-1 rounded">
                      {loraError}
                    </div>
                  )}
                </div>

                {/* LoRA Scale Slider */}
                <div className={!loraLoaded ? 'opacity-40 pointer-events-none' : ''}>
                  <EditableSlider
                    label={t('loraScale')}
                    value={loraScale}
                    min={0}
                    max={2}
                    step={0.05}
                    onChange={handleLoraScaleChange}
                    formatDisplay={(val) => val.toFixed(2)}
                    helpText={t('loraScaleDescription')}
                  />
                </div>

                {/* Training Hints - Collapsible */}
                {currentLoraHints && loraLoaded && (
                  <div className="border-t border-zinc-100 dark:border-white/5 pt-2">
                    <button
                      type="button"
                      onClick={() => setShowLoraHints(!showLoraHints)}
                      className="flex items-center gap-1 text-[10px] text-zinc-400 dark:text-zinc-500 hover:text-zinc-600 dark:hover:text-zinc-300 transition-colors"
                    >
                      <svg
                        className={`w-3 h-3 transition-transform ${showLoraHints ? 'rotate-90' : ''}`}
                        fill="currentColor"
                        viewBox="0 0 20 20"
                      >
                        <path fillRule="evenodd" d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z" clipRule="evenodd" />
                      </svg>
                      {t('loraHintsTitle') || '训练提示'}
                    </button>
                    {showLoraHints && (
                      <div className="mt-2 p-2.5 rounded-lg bg-zinc-50 dark:bg-white/5 border border-zinc-100 dark:border-white/5 space-y-1.5">
                        {currentLoraHints.trigger_word && (
                          <div className="text-[10px] text-zinc-500 dark:text-zinc-400">
                            {t('triggerWordLabel') || '触发词'}: <code className="px-1 py-0.5 bg-zinc-100 dark:bg-white/10 rounded font-mono">{currentLoraHints.trigger_word}</code>
                            <span className="ml-1">
                              ({currentLoraHints.tag_position === 'prepend' ? (t('tagPrepend') || '前置') : currentLoraHints.tag_position === 'replace' ? (t('tagReplace') || '替换') : (t('tagAppend') || '后置')})
                            </span>
                          </div>
                        )}
                        <div className="flex flex-wrap gap-x-3 gap-y-1 text-[10px] text-zinc-500 dark:text-zinc-400">
                          {currentLoraHints.model_variant && (
                            <span>{t('modelVariant') || '模型'}: <strong>{currentLoraHints.model_variant}</strong></span>
                          )}
                          {currentLoraHints.recommended_shift != null && (
                            <span>Shift: <strong>{currentLoraHints.recommended_shift}</strong></span>
                          )}
                          {currentLoraHints.recommended_steps != null && (
                            <span>Steps: <strong>{currentLoraHints.recommended_steps}</strong></span>
                          )}
                          {currentLoraHints.dataset_name && (
                            <span>{t('datasetName') || '数据集'}: {currentLoraHints.dataset_name}</span>
                          )}
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </div>
            )}
          </>
        )}

        {/* MUSIC PARAMETERS */}
        <div className="bg-white dark:bg-suno-card rounded-xl border border-zinc-200 dark:border-white/5 p-4 space-y-4">
          <h3 className="text-xs font-bold text-zinc-500 dark:text-zinc-400 uppercase tracking-wide flex items-center gap-2">
            <Sliders size={14} />
            {t('musicParameters')}
          </h3>

          {/* BPM */}
          <EditableSlider
            label={t('bpm')}
            value={bpm}
            min={0}
            max={300}
            step={5}
            onChange={setBpm}
            formatDisplay={(val) => val === 0 ? t('auto') : val.toString()}
            autoLabel={t('auto')}
          />

          {/* Key & Time Signature */}
          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-1.5">
              <label className="text-xs font-medium text-zinc-600 dark:text-zinc-400">Key</label>
              <select
                value={keyScale}
                onChange={(e) => { setKeyScale(e.target.value); localStorage.setItem('ace-keyScale', e.target.value); }}
                className="w-full bg-zinc-50 dark:bg-black/20 border border-zinc-200 dark:border-white/10 rounded-xl px-2 py-1.5 text-xs text-zinc-900 dark:text-white focus:outline-none focus:border-pink-500 dark:focus:border-pink-500 transition-colors cursor-pointer [&>option]:bg-white [&>option]:dark:bg-zinc-800 [&>option]:text-zinc-900 [&>option]:dark:text-white"
              >
                <option value="">{t('auto')}</option>
                {KEY_SIGNATURES.filter(k => k).map(key => (
                  <option key={key} value={key}>{key}</option>
                ))}
              </select>
            </div>
            <div className="space-y-1.5">
              <label className="text-xs font-medium text-zinc-600 dark:text-zinc-400">Time</label>
              <select
                value={timeSignature}
                onChange={(e) => { setTimeSignature(e.target.value); localStorage.setItem('ace-timeSignature', e.target.value); }}
                className="w-full bg-zinc-50 dark:bg-black/20 border border-zinc-200 dark:border-white/10 rounded-xl px-2 py-1.5 text-xs text-zinc-900 dark:text-white focus:outline-none focus:border-pink-500 dark:focus:border-pink-500 transition-colors cursor-pointer [&>option]:bg-white [&>option]:dark:bg-zinc-800 [&>option]:text-zinc-900 [&>option]:dark:text-white"
              >
                <option value="">{t('auto')}</option>
                {TIME_SIGNATURES.filter(t => t).map(time => (
                  <option key={time} value={time}>{time}</option>
                ))}
              </select>
            </div>
          </div>
        </div>

        {/* ADVANCED SETTINGS */}
        <button
          onClick={() => { setShowAdvanced(!showAdvanced); localStorage.setItem('ace-showAdvanced', (!showAdvanced).toString()); }}
          className="w-full flex items-center justify-between px-4 py-3 bg-white dark:bg-suno-card rounded-xl border border-zinc-200 dark:border-white/5 text-sm font-medium text-zinc-700 dark:text-zinc-300 hover:bg-zinc-50 dark:hover:bg-white/5 transition-colors"
        >
          <div className="flex items-center gap-2">
            <Settings2 size={16} className="text-zinc-500" />
            <span>{t('advancedSettings')}</span>
          </div>
          <ChevronDown size={16} className={`text-zinc-500 transition-transform ${showAdvanced ? 'rotate-180' : ''}`} />
        </button>

        {showAdvanced && (
          <div className="bg-white dark:bg-suno-card rounded-xl border border-zinc-200 dark:border-white/5 p-4 space-y-4">

            {/* Duration */}
            <EditableSlider
              label={t('duration')}
              value={duration}
              min={-1}
              max={600}
              step={5}
              onChange={setDuration}
              formatDisplay={(val) => val === -1 ? t('auto') : `${val}${t('seconds')}`}
              autoLabel={t('auto')}
              helpText={`${t('auto')} - 10 ${t('min')}`}
            />

            {/* Batch Size */}
            <EditableSlider
              label={t('batchSize')}
              value={batchSize}
              min={1}
              max={8}
              step={1}
              onChange={setBatchSize}
              helpText={t('numberOfVariations')}
              title="Creates multiple variations in a single run. More variations = longer total time."
            />

            {/* Bulk Generate */}
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <label className="text-xs font-medium text-zinc-600 dark:text-zinc-400">{t('bulkGenerate')}</label>
                <span className="text-xs font-mono text-zinc-900 dark:text-white bg-zinc-100 dark:bg-black/20 px-2 py-0.5 rounded">
                  {bulkCount} {t(bulkCount === 1 ? 'job' : 'jobs')}
                </span>
              </div>
              <div className="flex items-center gap-1">
                {[1, 2, 3, 5, 10].map((count) => (
                  <button
                    key={count}
                    onClick={() => { setBulkCount(count); localStorage.setItem('ace-bulkCount', String(count)); }}
                    className={`flex-1 py-2 rounded-lg text-xs font-bold transition-all ${
                      bulkCount === count
                        ? 'bg-gradient-to-r from-orange-500 to-pink-600 text-white shadow-md'
                        : 'bg-zinc-100 dark:bg-zinc-800 text-zinc-600 dark:text-zinc-400 hover:bg-zinc-200 dark:hover:bg-zinc-700'
                    }`}
                  >
                    {count}
                  </button>
                ))}
              </div>
              <p className="text-[10px] text-zinc-500">{t('queueMultipleJobs')}</p>
            </div>

            {/* Inference Steps */}
            <EditableSlider
              label={t('inferenceSteps')}
              value={inferenceSteps}
              min={4}
              max={200}
              step={1}
              onChange={(val) => { setInferenceSteps(val); localStorage.setItem('ace-inferenceSteps', val.toString()); }}
              helpText={t('moreStepsBetterQuality')}
              title="More steps usually improves quality but slows generation."
            />

            {/* Guidance Scale */}
            <EditableSlider
              label={t('guidanceScale')}
              value={guidanceScale}
              min={1}
              max={15}
              step={0.5}
              onChange={(val) => { setGuidanceScale(val); localStorage.setItem('ace-guidanceScale', val.toString()); }}
              formatDisplay={(val) => val.toFixed(1)}
              helpText={t('howCloselyFollowPrompt')}
              title="How strongly the model follows the prompt. Higher = stricter, lower = freer."
            />

            {/* Audio Format & Inference Method */}
            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-1.5">
                <label className="text-xs font-medium text-zinc-600 dark:text-zinc-400">{t('audioFormat')}</label>
                <select
                  value={audioFormat}
                  onChange={(e) => { setAudioFormat(e.target.value as 'mp3' | 'flac'); localStorage.setItem('ace-audioFormat', e.target.value); }}
                  className="w-full bg-zinc-50 dark:bg-black/20 border border-zinc-200 dark:border-white/10 rounded-xl px-2 py-1.5 text-xs text-zinc-900 dark:text-white focus:outline-none focus:border-pink-500 dark:focus:border-pink-500 transition-colors cursor-pointer [&>option]:bg-white [&>option]:dark:bg-zinc-800 [&>option]:text-zinc-900 [&>option]:dark:text-white"
                >
                  <option value="mp3">{t('mp3Smaller')}</option>
                  <option value="flac">{t('flacLossless')}</option>
                </select>
              </div>
              <div className="space-y-1.5">
                <label className="text-xs font-medium text-zinc-600 dark:text-zinc-400" title="Deterministic is more repeatable; stochastic adds randomness.">{t('inferMethod')}</label>
                <select
                  value={inferMethod}
                  onChange={(e) => { setInferMethod(e.target.value as 'ode' | 'sde'); localStorage.setItem('ace-inferMethod', e.target.value); }}
                  className="w-full bg-zinc-50 dark:bg-black/20 border border-zinc-200 dark:border-white/10 rounded-xl px-2 py-1.5 text-xs text-zinc-900 dark:text-white focus:outline-none focus:border-pink-500 dark:focus:border-pink-500 transition-colors cursor-pointer [&>option]:bg-white [&>option]:dark:bg-zinc-800 [&>option]:text-zinc-900 [&>option]:dark:text-white"
                >
                  <option value="ode">{t('odeDeterministic')}</option>
                  <option value="sde">{t('sdeStochastic')}</option>
                </select>
              </div>
            </div>

            {/* LM Backend */}
            <div className="space-y-1.5">
              <label className="text-xs font-medium text-zinc-600 dark:text-zinc-400">{t('lmBackendLabel')}</label>
              <select
                value={lmBackend}
                onChange={(e) => { setLmBackend(e.target.value as 'pt' | 'vllm'); localStorage.setItem('ace-lmBackend', e.target.value); }}
                className="w-full bg-zinc-50 dark:bg-black/20 border border-zinc-200 dark:border-white/10 rounded-xl px-2 py-1.5 text-xs text-zinc-900 dark:text-white focus:outline-none focus:border-pink-500 dark:focus:border-pink-500 transition-colors cursor-pointer [&>option]:bg-white [&>option]:dark:bg-zinc-800 [&>option]:text-zinc-900 [&>option]:dark:text-white"
              >
                <option value="pt">{t('lmBackendPt')}</option>
                <option value="vllm">{t('lmBackendVllm')}</option>
              </select>
              <p className="text-[10px] text-zinc-500">{t('lmBackendHint')}</p>
            </div>

            {/* LM Model */}
            <div className="space-y-1.5">
              <label className="text-xs font-medium text-zinc-600 dark:text-zinc-400">{t('lmModelLabel')}</label>
              <select
                value={lmModel}
                onChange={(e) => { const v = e.target.value; setLmModel(v); localStorage.setItem('ace-lmModel', v); }}
                className="w-full bg-zinc-50 dark:bg-black/20 border border-zinc-200 dark:border-white/10 rounded-xl px-2 py-1.5 text-xs text-zinc-900 dark:text-white focus:outline-none focus:border-pink-500 dark:focus:border-pink-500 transition-colors cursor-pointer [&>option]:bg-white [&>option]:dark:bg-zinc-800 [&>option]:text-zinc-900 [&>option]:dark:text-white"
              >
                <option value="acestep-5Hz-lm-0.6B">{t('lmModel06B')} - ⚡ 最快速度</option>
                <option value="acestep-5Hz-lm-1.7B">{t('lmModel17B')} - 🎵 推荐之选</option>
                <option value="acestep-5Hz-lm-4B">{t('lmModel4B')} - 🌟 最高质量</option>
              </select>
              <div className="space-y-1">
                <p className="text-[10px] text-zinc-500">
                  {lmModel === 'acestep-5Hz-lm-0.6B' ? t('lmModel06BDesc') :
                   lmModel === 'acestep-5Hz-lm-1.7B' ? t('lmModel17BDesc') :
                   t('lmModel4BDesc')}
                </p>
                <p className="text-[10px] text-zinc-400">{t('lmModelHint')}</p>
              </div>
            </div>

            {/* Seed */}
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Dices size={14} className="text-zinc-500" />
                  <span className="text-xs font-medium text-zinc-600 dark:text-zinc-400" title="Fixing the seed makes results repeatable. Random is recommended for variety.">{t('seed')}</span>
                </div>
                <button
                  onClick={() => { setRandomSeed(!randomSeed); localStorage.setItem('ace-randomSeed', (!randomSeed).toString()); }}
                  className={`w-10 h-5 rounded-full flex items-center transition-colors duration-200 px-0.5 border border-zinc-200 dark:border-white/5 ${randomSeed ? 'bg-pink-600' : 'bg-zinc-300 dark:bg-black/40'}`}
                >
                  <div className={`w-4 h-4 rounded-full bg-white transform transition-transform duration-200 shadow-sm ${randomSeed ? 'translate-x-5' : 'translate-x-0'}`} />
                </button>
              </div>
              <div className="flex items-center gap-2">
                <Hash size={14} className="text-zinc-500" />
                <input
                  type="number"
                  value={seed}
                  onChange={(e) => setSeed(Number(e.target.value))}
                  placeholder={t('enterFixedSeed')}
                  disabled={randomSeed}
                  className={`flex-1 bg-zinc-50 dark:bg-black/20 border border-zinc-200 dark:border-white/10 rounded-lg px-3 py-1.5 text-xs text-zinc-900 dark:text-white focus:outline-none ${randomSeed ? 'opacity-40 cursor-not-allowed' : ''}`}
                />
              </div>
              <p className="text-[10px] text-zinc-500">{randomSeed ? t('randomSeedRecommended') : t('fixedSeedReproducible')}</p>
            </div>

            {/* Thinking Toggle */}
            <div className="flex items-center justify-between py-2 border-t border-zinc-100 dark:border-white/5">
              <span className="text-xs font-medium text-zinc-600 dark:text-zinc-400">{t('thinkingCot')}<HelpTip text={t('thinkingCotHint')} /></span>
              <button
                onClick={() => { const newVal = !thinking; setThinking(newVal); localStorage.setItem('ace-thinking', newVal.toString()); }}
                className={`w-10 h-5 rounded-full flex items-center transition-colors duration-200 px-0.5 border border-zinc-200 dark:border-white/5 ${thinking ? 'bg-pink-600' : 'bg-zinc-300 dark:bg-black/40'} cursor-pointer`}
              >
                <div className={`w-4 h-4 rounded-full bg-white transform transition-transform duration-200 shadow-sm ${thinking ? 'translate-x-5' : 'translate-x-0'}`} />
              </button>
            </div>

            {/* Shift */}
            <EditableSlider
              label={t('shift')}
              value={shift}
              min={1}
              max={5}
              step={0.1}
              onChange={(val) => { setShift(val); localStorage.setItem('ace-shift', val.toString()); }}
              formatDisplay={(val) => val.toFixed(1)}
              helpText={t('timestepShiftForBase')}
              title="Adjusts the diffusion schedule. Only affects base model."
            />

            {/* Divider */}
            <div className="border-t border-zinc-200 dark:border-white/10 pt-4">
              <p className="text-[10px] text-zinc-500 uppercase tracking-wide font-bold mb-3">{t('expertControls')}</p>
            </div>

            {uploadError && (
              <div className="text-[11px] text-rose-500">{uploadError}</div>
            )}

            {/* LM Parameters */}
            <button
              onClick={() => { setShowLmParams(!showLmParams); localStorage.setItem('ace-showLmParams', (!showLmParams).toString()); }}
              className="w-full flex items-center justify-between px-4 py-3 bg-white/60 dark:bg-black/20 rounded-xl border border-zinc-200/70 dark:border-white/10 text-sm font-medium text-zinc-700 dark:text-zinc-300 hover:bg-zinc-50 dark:hover:bg-white/5 transition-colors"
            >
              <div className="flex items-center gap-2">
                <Music2 size={16} className="text-zinc-500" />
                <div className="flex flex-col items-start">
                  <span title="Controls the 5Hz lyric/caption model sampling behavior.">{t('lmParameters')}</span>
                  <span className="text-[11px] text-zinc-400 dark:text-zinc-500 font-normal">{t('controlLyricGeneration')}</span>
                </div>
              </div>
              <ChevronDown size={16} className={`text-zinc-500 transition-transform ${showLmParams ? 'rotate-180' : ''}`} />
            </button>

            {showLmParams && (
              <div className="bg-white dark:bg-suno-card rounded-xl border border-zinc-200 dark:border-white/5 p-4 space-y-4">
                {/* LM Temperature */}
                <EditableSlider
                  label={t('lmTemperature')}
                  value={lmTemperature}
                  min={0}
                  max={2}
                  step={0.05}
                  onChange={(val) => { setLmTemperature(val); localStorage.setItem('ace-lmTemperature', val.toString()); }}
                  formatDisplay={(val) => val.toFixed(2)}
                  helpText={t('higherMoreRandom')}
                  title="Higher temperature = more random word choices."
                />

                {/* LM CFG Scale */}
                <EditableSlider
                  label={t('lmCfgScale')}
                  value={lmCfgScale}
                  min={1}
                  max={3}
                  step={0.1}
                  onChange={(val) => { setLmCfgScale(val); localStorage.setItem('ace-lmCfgScale', val.toString()); }}
                  formatDisplay={(val) => val.toFixed(1)}
                  helpText={t('noCfgScale')}
                  title="How strongly the lyric model follows the prompt."
                />

                {/* LM Top-K & Top-P */}
                <div className="grid grid-cols-2 gap-3">
                  <EditableSlider
                    label={t('topK')}
                    value={lmTopK}
                    min={0}
                    max={100}
                    step={1}
                    onChange={(val) => { setLmTopK(val); localStorage.setItem('ace-lmTopK', val.toString()); }}
                    title="Restricts choices to the K most likely tokens. 0 disables."
                  />
                  <EditableSlider
                    label={t('topP')}
                    value={lmTopP}
                    min={0}
                    max={1}
                    step={0.01}
                    onChange={(val) => { setLmTopP(val); localStorage.setItem('ace-lmTopP', val.toString()); }}
                    formatDisplay={(val) => val.toFixed(2)}
                    title="Samples from the smallest set whose total probability is P."
                  />
                </div>

                {/* LM Negative Prompt */}
                <div className="space-y-1.5">
                  <label className="text-xs font-medium text-zinc-600 dark:text-zinc-400" title="Words or ideas to steer the lyric model away from.">{t('lmNegativePrompt')}</label>
                  <textarea
                    value={lmNegativePrompt}
                    onChange={(e) => { setLmNegativePrompt(e.target.value); localStorage.setItem('ace-lmNegativePrompt', e.target.value); }}
                    placeholder={t('thingsToAvoid')}
                    className="w-full h-16 bg-zinc-50 dark:bg-black/20 border border-zinc-200 dark:border-white/10 rounded-lg p-2 text-xs text-zinc-900 dark:text-white focus:outline-none resize-none"
                  />
                  <p className="text-[10px] text-zinc-500">{t('useWhenCfgScaleGreater')}</p>
                </div>
              </div>
            )}

            <div className="space-y-1">
              <h4 className="text-xs font-bold text-zinc-500 dark:text-zinc-400 uppercase tracking-wide" title="Controls how much the output follows the input audio.">{t('transform')}</h4>
              <p className="text-[11px] text-zinc-400 dark:text-zinc-500">{t('controlSourceAudio')}</p>
            </div>
            <div className="space-y-1.5">
              <label className="text-xs font-medium text-zinc-600 dark:text-zinc-400" title="Advanced: precomputed audio codes for conditioning.">{t('audioCodes')}</label>
              <textarea
                value={audioCodes}
                onChange={(e) => setAudioCodes(e.target.value)}
                placeholder={t('optionalAudioCodes')}
                className="w-full h-16 bg-zinc-50 dark:bg-black/20 border border-zinc-200 dark:border-white/10 rounded-lg p-2 text-xs text-zinc-900 dark:text-white focus:outline-none resize-none"
              />
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-1.5">
                <label className="text-xs font-medium text-zinc-600 dark:text-zinc-400" title="Choose text-to-music or audio-based modes.">{t('taskType')}</label>
                <select
                  value={taskType}
                   onChange={(e) => { const v = e.target.value; setTaskType(v); localStorage.setItem('ace-taskType', v); if (v === 'cover' || v === 'audio2audio') setAudioTab('source'); }}
                  className="w-full bg-zinc-50 dark:bg-black/20 border border-zinc-200 dark:border-white/10 rounded-xl px-2 py-1.5 text-xs text-zinc-900 dark:text-white focus:outline-none focus:border-pink-500 dark:focus:border-pink-500 transition-colors cursor-pointer [&>option]:bg-white [&>option]:dark:bg-zinc-800 [&>option]:text-zinc-900 [&>option]:dark:text-white"
                >
                  <option value="text2music">{t('textToMusic')}</option>
                  <option value="audio2audio">{t('audio2audio')}</option>
                  <option value="cover">{t('coverTask')}</option>
                  <option value="repaint">{t('repaintTask')}</option>
                </select>
              </div>
              <div className="space-y-1.5">
                <label className="text-xs font-medium text-zinc-600 dark:text-zinc-400" title="How strongly the source audio shapes the result.">{t('audioCoverStrength')}</label>
                <input
                  type="number"
                  step="0.05"
                  min="0"
                  max="1"
                  value={audioCoverStrength}
                  onChange={(e) => { const v = Number(e.target.value); setAudioCoverStrength(v); localStorage.setItem('ace-audioCoverStrength', String(v)); }}
                  className="w-full bg-zinc-50 dark:bg-black/20 border border-zinc-200 dark:border-white/10 rounded-lg px-3 py-2 text-xs text-zinc-900 dark:text-white focus:outline-none"
                />
              </div>
              <div className="space-y-1.5">
                <label className="text-xs font-medium text-zinc-600 dark:text-zinc-400" title="Noise level during cover mixing (0=more noise/more creative, 1=more faithful to source).">Cover Noise Str.</label>
                <input
                  type="number"
                  step="0.05"
                  min="0"
                  max="1"
                  value={coverNoiseStrength}
                  onChange={(e) => { const v = Number(e.target.value); setCoverNoiseStrength(v); localStorage.setItem('ace-coverNoiseStrength', String(v)); }}
                  className="w-full bg-zinc-50 dark:bg-black/20 border border-zinc-200 dark:border-white/10 rounded-lg px-3 py-2 text-xs text-zinc-900 dark:text-white focus:outline-none"
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-1.5">
                <label className="text-xs font-medium text-zinc-600 dark:text-zinc-400" title="Start time for the region to repaint (seconds).">{t('repaintingStart')}</label>
                <input
                  type="number"
                  step="0.1"
                  value={repaintingStart}
                  onChange={(e) => { const v = Number(e.target.value); setRepaintingStart(v); localStorage.setItem('ace-repaintingStart', String(v)); }}
                  className="w-full bg-zinc-50 dark:bg-black/20 border border-zinc-200 dark:border-white/10 rounded-lg px-3 py-2 text-xs text-zinc-900 dark:text-white focus:outline-none"
                />
              </div>
              <div className="space-y-1.5">
                <label className="text-xs font-medium text-zinc-600 dark:text-zinc-400" title="End time for the region to repaint (seconds).">{t('repaintingEnd')}</label>
                <input
                  type="number"
                  step="0.1"
                  value={repaintingEnd}
                  onChange={(e) => { const v = Number(e.target.value); setRepaintingEnd(v); localStorage.setItem('ace-repaintingEnd', String(v)); }}
                  className="w-full bg-zinc-50 dark:bg-black/20 border border-zinc-200 dark:border-white/10 rounded-lg px-3 py-2 text-xs text-zinc-900 dark:text-white focus:outline-none"
                />
              </div>
            </div>

            <div className="space-y-1.5">
              <label className="text-xs font-medium text-zinc-600 dark:text-zinc-400" title="Additional directives to guide generation.">{t('instruction')}</label>
              <textarea
                value={instruction}
                onChange={(e) => setInstruction(e.target.value)}
                className="w-full h-16 bg-zinc-50 dark:bg-black/20 border border-zinc-200 dark:border-white/10 rounded-lg p-2 text-xs text-zinc-900 dark:text-white focus:outline-none resize-none"
              />
            </div>

            <div className="space-y-1">
              <h4 className="text-xs font-bold text-zinc-500 dark:text-zinc-400 uppercase tracking-wide">{t('guidance')}</h4>
              <p className="text-[11px] text-zinc-400 dark:text-zinc-500">{t('advancedCfgScheduling')}</p>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-1.5">
                <label className="text-xs font-medium text-zinc-600 dark:text-zinc-400" title="Fraction of the diffusion process to start applying guidance.">{t('cfgIntervalStart')}</label>
                <input
                  type="number"
                  step="0.05"
                  min="0"
                  max="1"
                  value={cfgIntervalStart}
                  onChange={(e) => { const v = Number(e.target.value); setCfgIntervalStart(v); localStorage.setItem('ace-cfgIntervalStart', String(v)); }}
                  className="w-full bg-zinc-50 dark:bg-black/20 border border-zinc-200 dark:border-white/10 rounded-lg px-3 py-2 text-xs text-zinc-900 dark:text-white focus:outline-none"
                />
              </div>
              <div className="space-y-1.5">
                <label className="text-xs font-medium text-zinc-600 dark:text-zinc-400" title="Fraction of the diffusion process to stop applying guidance.">{t('cfgIntervalEnd')}</label>
                <input
                  type="number"
                  step="0.05"
                  min="0"
                  max="1"
                  value={cfgIntervalEnd}
                  onChange={(e) => { const v = Number(e.target.value); setCfgIntervalEnd(v); localStorage.setItem('ace-cfgIntervalEnd', String(v)); }}
                  className="w-full bg-zinc-50 dark:bg-black/20 border border-zinc-200 dark:border-white/10 rounded-lg px-3 py-2 text-xs text-zinc-900 dark:text-white focus:outline-none"
                />
              </div>
            </div>

            <div className="space-y-1.5">
              <label className="text-xs font-medium text-zinc-600 dark:text-zinc-400" title="Override the default timestep schedule (advanced).">{t('customTimesteps')}</label>
              <input
                type="text"
                value={customTimesteps}
                onChange={(e) => { setCustomTimesteps(e.target.value); localStorage.setItem('ace-customTimesteps', e.target.value); }}
                placeholder={t('timestepsPlaceholder')}
                className="w-full bg-zinc-50 dark:bg-black/20 border border-zinc-200 dark:border-white/10 rounded-lg px-3 py-2 text-xs text-zinc-900 dark:text-white focus:outline-none"
              />
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-1.5">
                <label className="text-xs font-medium text-zinc-600 dark:text-zinc-400" title="Scales score-based guidance (advanced).">{t('scoreScale')}</label>
                <input
                  type="number"
                  step="0.05"
                  value={scoreScale}
                  onChange={(e) => { const v = Number(e.target.value); setScoreScale(v); localStorage.setItem('ace-scoreScale', String(v)); }}
                  className="w-full bg-zinc-50 dark:bg-black/20 border border-zinc-200 dark:border-white/10 rounded-lg px-3 py-2 text-xs text-zinc-900 dark:text-white focus:outline-none"
                />
              </div>
              <div className="space-y-1.5">
                <label className="text-xs font-medium text-zinc-600 dark:text-zinc-400" title="Bigger chunks can be faster but use more memory.">{t('lmBatchChunkSize')}</label>
                <input
                  type="number"
                  min="1"
                  value={lmBatchChunkSize}
                  onChange={(e) => { const v = Number(e.target.value); setLmBatchChunkSize(v); localStorage.setItem('ace-lmBatchChunkSize', String(v)); }}
                  className="w-full bg-zinc-50 dark:bg-black/20 border border-zinc-200 dark:border-white/10 rounded-lg px-3 py-2 text-xs text-zinc-900 dark:text-white focus:outline-none"
                />
              </div>
            </div>

            <div className="space-y-1.5">
              <label className="text-xs font-medium text-zinc-600 dark:text-zinc-400">{t('trackName')}</label>
              <input
                type="text"
                value={trackName}
                onChange={(e) => setTrackName(e.target.value)}
                placeholder={t('optionalTrackName')}
                className="w-full bg-zinc-50 dark:bg-black/20 border border-zinc-200 dark:border-white/10 rounded-lg px-3 py-2 text-xs text-zinc-900 dark:text-white focus:outline-none"
              />
            </div>

            <div className="space-y-1.5">
              <label className="text-xs font-medium text-zinc-600 dark:text-zinc-400">{t('completeTrackClasses')}</label>
              <input
                type="text"
                value={completeTrackClasses}
                onChange={(e) => setCompleteTrackClasses(e.target.value)}
                placeholder={t('trackClassesPlaceholder')}
                className="w-full bg-zinc-50 dark:bg-black/20 border border-zinc-200 dark:border-white/10 rounded-lg px-3 py-2 text-xs text-zinc-900 dark:text-white focus:outline-none"
              />
            </div>

            <div className="grid grid-cols-2 gap-3">
              <label
                className="flex items-center gap-2 text-xs font-medium text-zinc-600 dark:text-zinc-400"
              >
                <input type="checkbox" checked={useAdg} onChange={() => { const v = !useAdg; setUseAdg(v); localStorage.setItem('ace-useAdg', String(v)); }} />
                {t('useAdg')}<HelpTip text={t('useAdgHint')} />
              </label>
              <label className="flex items-center gap-2 text-xs font-medium text-zinc-600 dark:text-zinc-400">
                <input type="checkbox" checked={allowLmBatch} onChange={() => { const v = !allowLmBatch; setAllowLmBatch(v); localStorage.setItem('ace-allowLmBatch', String(v)); }} />
                {t('allowLmBatch')}<HelpTip text={t('allowLmBatchHint')} />
              </label>
              <label className="flex items-center gap-2 text-xs font-medium text-zinc-600 dark:text-zinc-400">
                <input type="checkbox" checked={useCotMetas} onChange={() => { const v = !useCotMetas; setUseCotMetas(v); localStorage.setItem('ace-useCotMetas', String(v)); }} />
                {t('useCotMetas')}<HelpTip text={t('useCotMetasHint')} />
              </label>
              <label className="flex items-center gap-2 text-xs font-medium text-zinc-600 dark:text-zinc-400">
                <input type="checkbox" checked={useCotCaption} onChange={() => { const v = !useCotCaption; setUseCotCaption(v); localStorage.setItem('ace-useCotCaption', String(v)); }} />
                {t('useCotCaption')}<HelpTip text={t('useCotCaptionHint')} />
              </label>
              <label className="flex items-center gap-2 text-xs font-medium text-zinc-600 dark:text-zinc-400">
                <input type="checkbox" checked={useCotLanguage} onChange={() => { const v = !useCotLanguage; setUseCotLanguage(v); localStorage.setItem('ace-useCotLanguage', String(v)); }} />
                {t('useCotLanguage')}<HelpTip text={t('useCotLanguageHint')} />
              </label>
              <label className="flex items-center gap-2 text-xs font-medium text-zinc-600 dark:text-zinc-400">
                <input type="checkbox" checked={autogen} onChange={() => { const v = !autogen; setAutogen(v); localStorage.setItem('ace-autogen', String(v)); }} />
                {t('autogen')}<HelpTip text={t('autogenHint')} />
              </label>
              <label className="flex items-center gap-2 text-xs font-medium text-zinc-600 dark:text-zinc-400">
                <input type="checkbox" checked={constrainedDecodingDebug} onChange={() => { const v = !constrainedDecodingDebug; setConstrainedDecodingDebug(v); localStorage.setItem('ace-constrainedDecodingDebug', String(v)); }} />
                {t('constrainedDecodingDebug')}<HelpTip text={t('constrainedDecodingDebugHint')} />
              </label>
              <label className="flex items-center gap-2 text-xs font-medium text-zinc-600 dark:text-zinc-400">
                <input type="checkbox" checked={isFormatCaption} onChange={() => { const v = !isFormatCaption; setIsFormatCaption(v); localStorage.setItem('ace-isFormatCaption', String(v)); }} />
                {t('formatCaption')}<HelpTip text={t('formatCaptionHint')} />
              </label>
              <label className="flex items-center gap-2 text-xs font-medium text-zinc-600 dark:text-zinc-400">
                <input type="checkbox" checked={getScores} onChange={() => { const v = !getScores; setGetScores(v); localStorage.setItem('ace-getScores', String(v)); }} />
                {t('getScores')}<HelpTip text={t('getScoresHint')} />
              </label>
              <label className="flex items-center gap-2 text-xs font-medium text-zinc-600 dark:text-zinc-400">
                <input type="checkbox" checked={getLrc} onChange={() => { const v = !getLrc; setGetLrc(v); localStorage.setItem('ace-getLrc', String(v)); }} />
                {t('getLrcLyrics')}<HelpTip text={t('getLrcHint')} />
              </label>
            </div>
          </div>
        )}
      </div>

      {showAudioModal && (
        <div className="fixed inset-0 z-[120] flex items-center justify-center">
          <div
            className="absolute inset-0 bg-black/60 backdrop-blur-sm"
            onClick={() => { setShowAudioModal(false); setPlayingTrackId(null); setPlayingTrackSource(null); }}
          />
          <div className="relative w-[92%] max-w-lg rounded-2xl bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-white/10 shadow-2xl overflow-hidden">
            {/* Header */}
            <div className="p-5 pb-4">
              <div className="flex items-start justify-between">
                <div>
                  <h3 className="text-xl font-semibold text-zinc-900 dark:text-white">
                    {audioModalTarget === 'reference' ? t('referenceModalTitle') : t('coverModalTitle')}
                  </h3>
                  <p className="text-sm text-zinc-500 dark:text-zinc-400 mt-1">
                    {audioModalTarget === 'reference'
                      ? t('referenceModalDescription')
                      : t('coverModalDescription')}
                  </p>
                </div>
                <button
                  onClick={() => { setShowAudioModal(false); setPlayingTrackId(null); setPlayingTrackSource(null); }}
                  className="p-1.5 rounded-lg hover:bg-zinc-100 dark:hover:bg-white/10 text-zinc-400 hover:text-zinc-900 dark:hover:text-white transition-colors"
                >
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12"/>
                  </svg>
                </button>
              </div>

              {/* Upload Button */}
              <button
                type="button"
                onClick={() => {
                  const input = document.createElement('input');
                  input.type = 'file';
                  input.accept = '.mp3,.wav,.flac,.m4a,.mp4,audio/*';
                  input.onchange = (e) => {
                    const file = (e.target as HTMLInputElement).files?.[0];
                    if (file) void uploadReferenceTrack(file);
                  };
                  input.click();
                }}
                disabled={isUploadingReference || isTranscribingReference}
                className="mt-4 w-full flex items-center justify-center gap-2 rounded-xl border border-dashed border-zinc-300 dark:border-white/20 bg-zinc-50 dark:bg-white/5 px-4 py-3 text-sm font-medium text-zinc-700 dark:text-zinc-200 hover:bg-zinc-100 dark:hover:bg-white/10 hover:border-zinc-400 dark:hover:border-white/30 transition-all"
              >
                {isUploadingReference ? (
                  <>
                    <RefreshCw size={16} className="animate-spin" />
                    {t('uploadingAudio')}
                  </>
                ) : isTranscribingReference ? (
                  <>
                    <RefreshCw size={16} className="animate-spin" />
                    {t('transcribing')}
                  </>
                ) : (
                  <>
                    <Upload size={16} />
                    {t('uploadAudio')}
                    <span className="text-xs text-zinc-400 ml-1">{t('audioFormats')}</span>
                  </>
                )}
              </button>

              {uploadError && (
                <div className="mt-2 text-xs text-rose-500">{uploadError}</div>
              )}
              {isTranscribingReference && (
                <div className="mt-2 flex items-center justify-between text-xs text-zinc-400">
                  <span>{t('transcribingWithWhisper')}</span>
                  <button
                    type="button"
                    onClick={cancelTranscription}
                    className="text-zinc-600 dark:text-zinc-300 hover:text-zinc-900 dark:hover:text-white"
                  >
                    {t('cancel')}
                  </button>
                </div>
              )}
            </div>

            {/* Library Section */}
            <div className="border-t border-zinc-100 dark:border-white/5">
              <div className="px-5 py-3 flex items-center gap-2">
                <div className="flex items-center gap-1 bg-zinc-200/60 dark:bg-white/10 rounded-full p-0.5">
                  <button
                    type="button"
                    onClick={() => setLibraryTab('uploads')}
                    className={`px-3 py-1 rounded-full text-xs font-semibold transition-colors ${
                      libraryTab === 'uploads'
                        ? 'bg-zinc-900 dark:bg-white text-white dark:text-zinc-900'
                        : 'text-zinc-500 dark:text-zinc-400 hover:text-zinc-700 dark:hover:text-zinc-200'
                    }`}
                  >
                    {t('uploaded')}
                  </button>
                  <button
                    type="button"
                    onClick={() => setLibraryTab('created')}
                    className={`px-3 py-1 rounded-full text-xs font-semibold transition-colors ${
                      libraryTab === 'created'
                        ? 'bg-zinc-900 dark:bg-white text-white dark:text-zinc-900'
                        : 'text-zinc-500 dark:text-zinc-400 hover:text-zinc-700 dark:hover:text-zinc-200'
                    }`}
                  >
                    {t('createdTab')}
                  </button>
                </div>
              </div>

              {/* Track List */}
              <div className="max-h-[280px] overflow-y-auto">
                {libraryTab === 'uploads' ? (
                  isLoadingTracks ? (
                    <div className="px-5 py-8 text-center">
                      <RefreshCw size={20} className="animate-spin mx-auto text-zinc-400" />
                      <p className="text-xs text-zinc-400 mt-2">{t('loadingTracks')}</p>
                    </div>
                  ) : referenceTracks.length === 0 ? (
                    <div className="px-5 py-8 text-center">
                      <Music2 size={24} className="mx-auto text-zinc-300 dark:text-zinc-600" />
                      <p className="text-sm text-zinc-400 mt-2">{t('noTracksYet')}</p>
                      <p className="text-xs text-zinc-400 mt-1">{t('uploadAudioFilesAsReferences')}</p>
                    </div>
                  ) : (
                    <div className="divide-y divide-zinc-100 dark:divide-white/5">
                      {referenceTracks.map((track) => (
                        <div
                          key={track.id}
                          className="px-5 py-3 flex items-center gap-3 hover:bg-zinc-50 dark:hover:bg-white/[0.02] transition-colors group"
                        >
                          {/* Play Button */}
                          <button
                            type="button"
                            onClick={() => toggleModalTrack({ id: track.id, audio_url: track.audio_url, source: 'uploads' })}
                            className="flex-shrink-0 w-9 h-9 rounded-full bg-zinc-100 dark:bg-white/10 text-zinc-600 dark:text-zinc-300 flex items-center justify-center hover:bg-zinc-200 dark:hover:bg-white/20 transition-colors"
                          >
                            {playingTrackId === track.id && playingTrackSource === 'uploads' ? (
                              <Pause size={14} fill="currentColor" />
                            ) : (
                              <Play size={14} fill="currentColor" className="ml-0.5" />
                            )}
                          </button>

                          {/* Track Info */}
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center gap-2">
                              <span className="text-sm font-medium text-zinc-800 dark:text-zinc-200 truncate">
                                {track.filename.replace(/\.[^/.]+$/, '')}
                              </span>
                              {track.tags && track.tags.length > 0 && (
                                <div className="flex gap-1">
                                  {track.tags.slice(0, 2).map((tag, i) => (
                                    <span key={i} className="px-1.5 py-0.5 rounded text-[10px] font-medium bg-zinc-200 dark:bg-white/10 text-zinc-600 dark:text-zinc-400">
                                      {tag}
                                    </span>
                                  ))}
                                </div>
                              )}
                            </div>
                            {/* Progress bar with seek - show when this track is playing */}
                            {playingTrackId === track.id && playingTrackSource === 'uploads' ? (
                              <div className="flex items-center gap-2 mt-1.5">
                                <span className="text-[10px] text-zinc-400 tabular-nums w-8">
                                  {formatTime(modalTrackTime)}
                                </span>
                                <div
                                  className="flex-1 h-1.5 rounded-full bg-zinc-200 dark:bg-white/10 cursor-pointer group/seek"
                                  onClick={(e) => {
                                    if (modalAudioRef.current && modalTrackDuration > 0) {
                                      const rect = e.currentTarget.getBoundingClientRect();
                                      const percent = (e.clientX - rect.left) / rect.width;
                                      modalAudioRef.current.currentTime = percent * modalTrackDuration;
                                    }
                                  }}
                                >
                                  <div
                                    className="h-full bg-gradient-to-r from-pink-500 to-purple-500 rounded-full relative"
                                    style={{ width: modalTrackDuration > 0 ? `${(modalTrackTime / modalTrackDuration) * 100}%` : '0%' }}
                                  >
                                    <div className="absolute right-0 top-1/2 -translate-y-1/2 w-2.5 h-2.5 rounded-full bg-white shadow-md opacity-0 group-hover/seek:opacity-100 transition-opacity" />
                                  </div>
                                </div>
                                <span className="text-[10px] text-zinc-400 tabular-nums w-8 text-right">
                                  {formatTime(modalTrackDuration)}
                                </span>
                              </div>
                            ) : (
                              <div className="text-xs text-zinc-400 mt-0.5">
                                {track.duration ? formatTime(track.duration) : '--:--'}
                              </div>
                            )}
                          </div>

                          {/* Actions */}
                          <div className="flex items-center gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                            <button
                              type="button"
                              onClick={() => useReferenceTrack({ audio_url: track.audio_url, title: track.filename })}
                              className="px-3 py-1.5 rounded-lg bg-zinc-900 dark:bg-white text-white dark:text-zinc-900 text-xs font-semibold hover:bg-zinc-800 dark:hover:bg-zinc-100 transition-colors"
                            >
                              {t('useTrack')}
                            </button>
                            <button
                              type="button"
                              onClick={() => void deleteReferenceTrack(track.id)}
                              className="p-1.5 rounded-lg hover:bg-zinc-200 dark:hover:bg-white/10 text-zinc-400 hover:text-rose-500 transition-colors"
                            >
                              <Trash2 size={14} />
                            </button>
                          </div>
                        </div>
                      ))}
                    </div>
                  )
                ) : createdTrackOptions.length === 0 ? (
                  <div className="px-5 py-8 text-center">
                    <Music2 size={24} className="mx-auto text-zinc-300 dark:text-zinc-600" />
                    <p className="text-sm text-zinc-400 mt-2">{t('noCreatedSongsYet')}</p>
                    <p className="text-xs text-zinc-400 mt-1">{t('generateSongsToReuse')}</p>
                  </div>
                ) : (
                  <div className="divide-y divide-zinc-100 dark:divide-white/5">
                    {createdTrackOptions.map((track) => (
                      <div
                        key={track.id}
                        className="px-5 py-3 flex items-center gap-3 hover:bg-zinc-50 dark:hover:bg-white/[0.02] transition-colors group"
                      >
                        <button
                          type="button"
                          onClick={() => toggleModalTrack({ id: track.id, audio_url: track.audio_url, source: 'created' })}
                          className="flex-shrink-0 w-9 h-9 rounded-full bg-zinc-100 dark:bg-white/10 text-zinc-600 dark:text-zinc-300 flex items-center justify-center hover:bg-zinc-200 dark:hover:bg-white/20 transition-colors"
                        >
                          {playingTrackId === track.id && playingTrackSource === 'created' ? (
                            <Pause size={14} fill="currentColor" />
                          ) : (
                            <Play size={14} fill="currentColor" className="ml-0.5" />
                          )}
                        </button>

                        <div className="flex-1 min-w-0">
                          <div className="text-sm font-medium text-zinc-800 dark:text-zinc-200 truncate">
                            {track.title}
                          </div>
                          {playingTrackId === track.id && playingTrackSource === 'created' ? (
                            <div className="flex items-center gap-2 mt-1.5">
                              <span className="text-[10px] text-zinc-400 tabular-nums w-8">
                                {formatTime(modalTrackTime)}
                              </span>
                              <div
                                className="flex-1 h-1.5 rounded-full bg-zinc-200 dark:bg-white/10 cursor-pointer group/seek"
                                onClick={(e) => {
                                  if (modalAudioRef.current && modalTrackDuration > 0) {
                                    const rect = e.currentTarget.getBoundingClientRect();
                                    const percent = (e.clientX - rect.left) / rect.width;
                                    modalAudioRef.current.currentTime = percent * modalTrackDuration;
                                  }
                                }}
                              >
                                <div
                                  className="h-full bg-gradient-to-r from-pink-500 to-purple-500 rounded-full relative"
                                  style={{ width: modalTrackDuration > 0 ? `${(modalTrackTime / modalTrackDuration) * 100}%` : '0%' }}
                                >
                                  <div className="absolute right-0 top-1/2 -translate-y-1/2 w-2.5 h-2.5 rounded-full bg-white shadow-md opacity-0 group-hover/seek:opacity-100 transition-opacity" />
                                </div>
                              </div>
                              <span className="text-[10px] text-zinc-400 tabular-nums w-8 text-right">
                                {formatTime(modalTrackDuration)}
                              </span>
                            </div>
                          ) : (
                            <div className="text-xs text-zinc-400 mt-0.5">
                              {track.duration || '--:--'}
                            </div>
                          )}
                        </div>

                        <div className="flex items-center gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                          <button
                            type="button"
                            onClick={() => useReferenceTrack({ audio_url: track.audio_url, title: track.title })}
                            className="px-3 py-1.5 rounded-lg bg-zinc-900 dark:bg-white text-white dark:text-zinc-900 text-xs font-semibold hover:bg-zinc-800 dark:hover:bg-zinc-100 transition-colors"
                          >
                            {t('useTrack')}
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>

            {/* Hidden audio element for modal playback */}
            <audio
              ref={modalAudioRef}
              onTimeUpdate={() => {
                if (modalAudioRef.current) {
                  setModalTrackTime(modalAudioRef.current.currentTime);
                }
              }}
              onLoadedMetadata={() => {
                if (modalAudioRef.current) {
                  setModalTrackDuration(modalAudioRef.current.duration);
                  // Update track duration in database if not set
                  const track = referenceTracks.find(t => t.id === playingTrackId);
                  if (playingTrackSource === 'uploads' && track && !track.duration && token) {
                    fetch(`/api/reference-tracks/${track.id}`, {
                      method: 'PATCH',
                      headers: {
                        'Content-Type': 'application/json',
                        Authorization: `Bearer ${token}`
                      },
                      body: JSON.stringify({ duration: Math.round(modalAudioRef.current.duration) })
                    }).then(() => {
                      setReferenceTracks(prev => prev.map(t =>
                        t.id === track.id ? { ...t, duration: Math.round(modalAudioRef.current?.duration || 0) } : t
                      ));
                    }).catch(() => undefined);
                  }
                }
              }}
              onEnded={() => setPlayingTrackId(null)}
            />
          </div>
        </div>
      )}

      {/* Footer Create Button */}
      <div className="p-4 mt-auto sticky bottom-0 bg-zinc-50/95 dark:bg-suno-panel/95 backdrop-blur-sm z-10 border-t border-zinc-200 dark:border-white/5 space-y-3">
        <button
          onClick={handleGenerate}
          className="w-full h-12 rounded-xl font-bold text-base flex items-center justify-center gap-2 transition-all transform active:scale-[0.98] bg-gradient-to-r from-orange-500 to-pink-600 text-white shadow-lg hover:brightness-110 disabled:opacity-60 disabled:cursor-not-allowed"
          disabled={isGenerating || !isAuthenticated}
          title={(taskType === 'cover' || taskType === 'audio2audio') && !sourceAudioUrl.trim() && !audioCodes.trim() ? `翻唱 / 音频转音频模式：点击后将引导您在「${t('cover')}」（内容参考）上传源音频` : undefined}
        >
          <Sparkles size={18} />
          <span>
            {isGenerating 
              ? t('generating')
              : bulkCount > 1
                ? `${t('createButton')} ${bulkCount} ${t('jobs')} (${bulkCount * batchSize} ${t('variations')})`
                : `${t('createButton')}${batchSize > 1 ? ` (${batchSize} ${t('variations')})` : ''}`
            }
          </span>
        </button>
      </div>

      {/* Save Preset Modal */}
      {showSavePresetModal && (
        <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/50 backdrop-blur-sm" onClick={() => setShowSavePresetModal(false)}>
          <div className="bg-white dark:bg-zinc-900 rounded-2xl shadow-2xl border border-zinc-200 dark:border-zinc-700 w-full max-w-md mx-4 overflow-hidden" onClick={e => e.stopPropagation()}>
            <div className="px-5 py-4 border-b border-zinc-100 dark:border-zinc-800 flex items-center justify-between">
              <h3 className="text-sm font-bold text-zinc-900 dark:text-white">{t('savePreset')}</h3>
              <button onClick={() => setShowSavePresetModal(false)} className="text-zinc-400 hover:text-zinc-600 dark:hover:text-zinc-300 transition-colors">
                <X size={16} />
              </button>
            </div>
            <div className="px-5 py-4 space-y-4">
              <div className="space-y-1.5">
                <label className="text-xs font-medium text-zinc-600 dark:text-zinc-400">{t('presetName')}</label>
                <input
                  type="text"
                  value={presetName}
                  onChange={e => setPresetName(e.target.value)}
                  placeholder={t('presetNamePlaceholder')}
                  className="w-full bg-zinc-50 dark:bg-black/20 border border-zinc-200 dark:border-white/10 rounded-lg px-3 py-2 text-sm text-zinc-900 dark:text-white focus:outline-none focus:border-pink-500"
                  autoFocus
                />
              </div>
              <div className="space-y-1.5">
                <label className="text-xs font-medium text-zinc-600 dark:text-zinc-400">{t('presetDescription')}</label>
                <textarea
                  value={presetDescription}
                  onChange={e => setPresetDescription(e.target.value)}
                  placeholder={t('presetDescriptionPlaceholder')}
                  className="w-full bg-zinc-50 dark:bg-black/20 border border-zinc-200 dark:border-white/10 rounded-lg px-3 py-2 text-sm text-zinc-900 dark:text-white focus:outline-none focus:border-pink-500 resize-none h-20"
                />
              </div>
              <div className="space-y-1.5">
                <label className="text-xs font-medium text-zinc-600 dark:text-zinc-400">{t('presetCategory')}</label>
                <select
                  value={presetCategory}
                  onChange={e => setPresetCategory(e.target.value)}
                  className="w-full bg-zinc-50 dark:bg-black/20 border border-zinc-200 dark:border-white/10 rounded-lg px-3 py-2 text-sm text-zinc-900 dark:text-white focus:outline-none"
                >
                  <option value="text2music">{t('textToMusic')}</option>
                  <option value="cover">{t('coverTask')}</option>
                  <option value="audio2audio">{t('audio2audio')}</option>
                  <option value="instrumental">{t('instrumental')}</option>
                  <option value="long">{t('longAudio')}</option>
                  <option value="custom">{t('custom')}</option>
                </select>
              </div>
            </div>
            <div className="px-5 py-3 border-t border-zinc-100 dark:border-zinc-800 flex items-center justify-end gap-2">
              <button
                onClick={() => setShowSavePresetModal(false)}
                className="px-4 py-2 text-xs font-medium text-zinc-600 dark:text-zinc-400 hover:text-zinc-900 dark:hover:text-white transition-colors"
              >
                {t('cancel')}
              </button>
              <button
                onClick={async () => {
                  if (!presetName.trim() || !token) return;
                  setPresetLoading(true);
                  try {
                    const result = await presetsApi.createPreset({
                      name: presetName.trim(),
                      description: presetDescription.trim() || undefined,
                      category: presetCategory,
                      params: getCurrentParams(),
                    }, token);
                    setPresets(prev => [...prev, result.preset]);
                    setShowSavePresetModal(false);
                    setPresetName('');
                    setPresetDescription('');
                  } catch (err) {
                    console.error('Failed to save preset:', err);
                  } finally {
                    setPresetLoading(false);
                  }
                }}
                disabled={!presetName.trim() || presetLoading}
                className="px-4 py-2 text-xs font-medium bg-pink-600 text-white rounded-lg hover:bg-pink-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-1"
              >
                {presetLoading ? <Loader2 size={12} className="animate-spin" /> : <Save size={12} />}
                {t('save')}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Save Project Modal */}
      {showSaveProjectModal && (
        <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/50 backdrop-blur-sm" onClick={() => setShowSaveProjectModal(false)}>
          <div className="bg-white dark:bg-zinc-900 rounded-2xl shadow-2xl border border-zinc-200 dark:border-zinc-700 w-full max-w-md mx-4 overflow-hidden" onClick={e => e.stopPropagation()}>
            <div className="px-5 py-4 border-b border-zinc-100 dark:border-zinc-800 flex items-center justify-between">
              <h3 className="text-sm font-bold text-zinc-900 dark:text-white">{t('newProject')}</h3>
              <button onClick={() => setShowSaveProjectModal(false)} className="text-zinc-400 hover:text-zinc-600 dark:hover:text-zinc-300 transition-colors">
                <X size={16} />
              </button>
            </div>
            <div className="px-5 py-4 space-y-4">
              <div className="space-y-1.5">
                <label className="text-xs font-medium text-zinc-600 dark:text-zinc-400">{t('projectName')}</label>
                <input
                  type="text"
                  value={projectName}
                  onChange={e => setProjectName(e.target.value)}
                  placeholder={t('projectNamePlaceholder')}
                  className="w-full bg-zinc-50 dark:bg-black/20 border border-zinc-200 dark:border-white/10 rounded-lg px-3 py-2 text-sm text-zinc-900 dark:text-white focus:outline-none focus:border-blue-500"
                  autoFocus
                />
              </div>
              <div className="space-y-1.5">
                <label className="text-xs font-medium text-zinc-600 dark:text-zinc-400">{t('presetDescription')}</label>
                <textarea
                  value={projectDescription}
                  onChange={e => setProjectDescription(e.target.value)}
                  placeholder={t('presetDescriptionPlaceholder')}
                  className="w-full bg-zinc-50 dark:bg-black/20 border border-zinc-200 dark:border-white/10 rounded-lg px-3 py-2 text-sm text-zinc-900 dark:text-white focus:outline-none focus:border-blue-500 resize-none h-20"
                />
              </div>
              {activeProject?.is_default && (
                <div className="bg-yellow-50 dark:bg-yellow-900/20 rounded-lg px-3 py-2">
                  <p className="text-[10px] text-yellow-600 dark:text-yellow-400">将当前默认项目的参数保存到新项目中，默认项目会自动重置</p>
                </div>
              )}
              {!activeProject?.is_default && (
                <div className="bg-blue-50 dark:bg-blue-900/20 rounded-lg px-3 py-2">
                  <p className="text-[10px] text-blue-600 dark:text-blue-400">{t('projectSaveHint')}</p>
                </div>
              )}
            </div>
            <div className="px-5 py-3 border-t border-zinc-100 dark:border-zinc-800 flex items-center justify-end gap-2">
              <button
                onClick={() => setShowSaveProjectModal(false)}
                className="px-4 py-2 text-xs font-medium text-zinc-600 dark:text-zinc-400 hover:text-zinc-900 dark:hover:text-white transition-colors"
              >
                {t('cancel')}
              </button>
              <button
                onClick={async () => {
                  if (!projectName.trim() || !token) return;
                  setProjectLoading(true);
                  try {
                    const result = await projectsApi.createProject({
                      name: projectName.trim(),
                      description: projectDescription.trim() || undefined,
                      params: getCurrentParams(),
                      from_default: activeProject?.is_default ? true : undefined,
                    }, token);
                    setActiveProject(result.project);
                    if (token) {
                      const projectsResult = await projectsApi.getProjects(token);
                      setProjects(projectsResult.projects);
                    }
                    setShowSaveProjectModal(false);
                    setProjectName('');
                    setProjectDescription('');
                    await refreshUndoRedoState();
                  } catch (err) {
                    console.error('Failed to create project:', err);
                  } finally {
                    setProjectLoading(false);
                  }
                }}
                disabled={!projectName.trim() || projectLoading}
                className="px-4 py-2 text-xs font-medium bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-1"
              >
                {projectLoading ? <Loader2 size={12} className="animate-spin" /> : <FolderPlus size={12} />}
                {t('create')}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Snapshots History Modal */}
      {showSnapshots && activeProject && (
        <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/50 backdrop-blur-sm" onClick={() => setShowSnapshots(false)}>
          <div className="bg-white dark:bg-zinc-900 rounded-2xl shadow-2xl border border-zinc-200 dark:border-zinc-700 w-full max-w-lg mx-4 overflow-hidden" onClick={e => e.stopPropagation()}>
            <div className="px-5 py-4 border-b border-zinc-100 dark:border-zinc-800 flex items-center justify-between">
              <div>
                <h3 className="text-sm font-bold text-zinc-900 dark:text-white">{t('history')} - {activeProject.name}</h3>
                <p className="text-[10px] text-zinc-400 dark:text-zinc-500 mt-0.5">{t('snapshotHint')}</p>
              </div>
              <button onClick={() => setShowSnapshots(false)} className="text-zinc-400 hover:text-zinc-600 dark:hover:text-zinc-300 transition-colors">
                <X size={16} />
              </button>
            </div>
            <div className="max-h-96 overflow-y-auto custom-scrollbar">
              {snapshots.length === 0 ? (
                <div className="px-5 py-8 text-center text-xs text-zinc-400 dark:text-zinc-500">
                  {t('noSnapshots')}
                </div>
              ) : (
                snapshots.map(snapshot => (
                  <div
                    key={snapshot.id}
                    className="flex items-center px-5 py-3 hover:bg-zinc-50 dark:hover:bg-zinc-800/50 transition-colors border-b border-zinc-50 dark:border-zinc-800/50 group"
                  >
                    <button
                      onClick={async () => {
                        if (!token) return;
                        try {
                          const result = await projectsApi.restoreSnapshot(activeProject.id, snapshot.id, token);
                          applyProject(result.project);
                          setActiveProject(result.project);
                          setShowSnapshots(false);
                        } catch {}
                      }}
                      className="flex-1 text-left flex items-center gap-3 min-w-0"
                    >
                      <div className={`w-2 h-2 rounded-full flex-shrink-0 ${snapshot.is_auto ? 'bg-green-400' : 'bg-blue-400'}`} />
                      <div className="flex-1 min-w-0">
                        <p className="text-xs font-medium text-zinc-900 dark:text-white truncate">
                          {snapshot.label || (snapshot.is_auto ? t('autoSave') : t('manualSave'))}
                        </p>
                        <p className="text-[10px] text-zinc-400 dark:text-zinc-500">
                          {snapshot.created_at ? new Date(snapshot.created_at).toLocaleString() : ''}
                        </p>
                      </div>
                    </button>
                    <button
                      onClick={async (e) => {
                        e.stopPropagation();
                        if (!token) return;
                        try {
                          await projectsApi.deleteSnapshot(activeProject.id, snapshot.id, token);
                          setSnapshots(prev => prev.filter(s => s.id !== snapshot.id));
                        } catch {}
                      }}
                      className="opacity-0 group-hover:opacity-100 p-1 text-zinc-400 hover:text-red-500 transition-all"
                      title={t('delete')}
                    >
                      <Trash2 size={12} />
                    </button>
                  </div>
                ))
              )}
            </div>
            <div className="px-5 py-3 border-t border-zinc-100 dark:border-zinc-800 flex items-center justify-between">
              <button
                onClick={async () => {
                  if (!token || !activeProject) return;
                  try {
                    const result = await projectsApi.createSnapshot(activeProject.id, {
                      label: t('manualSave'),
                      params: getCurrentParams(),
                      is_auto: false,
                    }, token);
                    setSnapshots(prev => [result.snapshot, ...prev]);
                  } catch {}
                }}
                className="px-3 py-1.5 text-[10px] font-medium bg-green-600 text-white rounded-md hover:bg-green-700 transition-colors flex items-center gap-1"
              >
                <Save size={10} />
                {t('manualSave')}
              </button>
              <button
                onClick={() => setShowSnapshots(false)}
                className="px-4 py-2 text-xs font-medium text-zinc-600 dark:text-zinc-400 hover:text-zinc-900 dark:hover:text-white transition-colors"
              >
                {t('close')}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Changelog Modal */}
      {showChangelog && activeProject && (
        <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/50 backdrop-blur-sm" onClick={() => setShowChangelog(false)}>
          <div className="bg-white dark:bg-zinc-900 rounded-2xl shadow-2xl border border-zinc-200 dark:border-zinc-700 w-full max-w-lg mx-4 overflow-hidden" onClick={e => e.stopPropagation()}>
            <div className="px-5 py-4 border-b border-zinc-100 dark:border-zinc-800 flex items-center justify-between">
              <div>
                <h3 className="text-sm font-bold text-zinc-900 dark:text-white">修改日志 - {activeProject.name}</h3>
                <p className="text-[10px] text-zinc-400 dark:text-zinc-500 mt-0.5">共 {changelogTotal} 条记录，类似 Git 提交历史</p>
              </div>
              <button onClick={() => setShowChangelog(false)} className="text-zinc-400 hover:text-zinc-600 dark:hover:text-zinc-300 transition-colors">
                <X size={16} />
              </button>
            </div>
            <div className="max-h-96 overflow-y-auto custom-scrollbar">
              {changelogs.length === 0 ? (
                <div className="px-5 py-8 text-center text-xs text-zinc-400 dark:text-zinc-500">
                  暂无修改记录
                </div>
              ) : (
                changelogs.map((log, index) => (
                  <div
                    key={log.id}
                    className="px-5 py-3 hover:bg-zinc-50 dark:hover:bg-zinc-800/50 transition-colors border-b border-zinc-50 dark:border-zinc-800/50"
                  >
                    <div className="flex items-start gap-3">
                      <div className="flex flex-col items-center mt-1">
                        <div className="w-3 h-3 rounded-full bg-blue-500 border-2 border-blue-200 dark:border-blue-800 flex-shrink-0" />
                        {index < changelogs.length - 1 && (
                          <div className="w-0.5 h-full min-h-[20px] bg-zinc-200 dark:bg-zinc-700 mt-1" />
                        )}
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2">
                          <p className="text-xs font-medium text-zinc-900 dark:text-white truncate">{log.action}</p>
                          {log.label && (
                            <span className={`px-1.5 py-0.5 text-[8px] font-bold rounded ${
                              log.label === 'auto-save' ? 'bg-green-100 dark:bg-green-900/30 text-green-600 dark:text-green-400' :
                              log.label === 'redo' ? 'bg-purple-100 dark:bg-purple-900/30 text-purple-600 dark:text-purple-400' :
                              log.label === 'restore' ? 'bg-orange-100 dark:bg-orange-900/30 text-orange-600 dark:text-orange-400' :
                              'bg-zinc-100 dark:bg-zinc-800 text-zinc-600 dark:text-zinc-400'
                            }`}>
                              {log.label}
                            </span>
                          )}
                        </div>
                        <p className="text-[10px] text-zinc-400 dark:text-zinc-500 mt-0.5">
                          {log.created_at ? new Date(log.created_at).toLocaleString() : ''}
                        </p>
                        <div className="mt-1 space-y-0.5">
                          {Object.entries(log.changes).slice(0, 5).map(([key, change]) => (
                            <p key={key} className="text-[10px] text-zinc-500 dark:text-zinc-400 font-mono">
                              <span className="text-red-400">- {key}: {JSON.stringify((change as { old: unknown; new: unknown }).old)}</span>
                              <span className="mx-1">→</span>
                              <span className="text-green-400">{JSON.stringify((change as { old: unknown; new: unknown }).new)}</span>
                            </p>
                          ))}
                          {Object.keys(log.changes).length > 5 && (
                            <p className="text-[10px] text-zinc-400">...还有 {Object.keys(log.changes).length - 5} 个参数变更</p>
                          )}
                        </div>
                      </div>
                      <button
                        onClick={async () => {
                          if (!token) return;
                          try {
                            const result = await projectsApi.updateProject(activeProject.id, {
                              params: log.snapshot_params,
                              changelog_label: 'restore',
                            }, token);
                            applyProject(result.project);
                            setActiveProject(result.project);
                            setShowChangelog(false);
                            await refreshUndoRedoState();
                          } catch {}
                        }}
                        className="px-2 py-1 text-[10px] font-medium bg-zinc-100 dark:bg-zinc-800 text-zinc-600 dark:text-zinc-300 rounded hover:bg-zinc-200 dark:hover:bg-zinc-700 transition-colors flex-shrink-0"
                      >
                        恢复
                      </button>
                    </div>
                  </div>
                ))
              )}
            </div>
            <div className="px-5 py-3 border-t border-zinc-100 dark:border-zinc-800 flex items-center justify-end">
              <button
                onClick={() => setShowChangelog(false)}
                className="px-4 py-2 text-xs font-medium text-zinc-600 dark:text-zinc-400 hover:text-zinc-900 dark:hover:text-white transition-colors"
              >
                {t('close')}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Rename Project Modal */}
      {showRenameModal && activeProject && (
        <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/50 backdrop-blur-sm" onClick={() => setShowRenameModal(false)}>
          <div className="bg-white dark:bg-zinc-900 rounded-2xl shadow-2xl border border-zinc-200 dark:border-zinc-700 w-full max-w-sm mx-4 overflow-hidden" onClick={e => e.stopPropagation()}>
            <div className="px-5 py-4 border-b border-zinc-100 dark:border-zinc-800 flex items-center justify-between">
              <h3 className="text-sm font-bold text-zinc-900 dark:text-white">命名项目</h3>
              <button onClick={() => setShowRenameModal(false)} className="text-zinc-400 hover:text-zinc-600 dark:hover:text-zinc-300 transition-colors">
                <X size={16} />
              </button>
            </div>
            <div className="px-5 py-4 space-y-3">
              <div className="space-y-1.5">
                <label className="text-xs font-medium text-zinc-600 dark:text-zinc-400">{t('projectName')}</label>
                <input
                  type="text"
                  value={renameValue}
                  onChange={e => setRenameValue(e.target.value)}
                  placeholder="输入项目名称"
                  className="w-full bg-zinc-50 dark:bg-black/20 border border-zinc-200 dark:border-white/10 rounded-lg px-3 py-2 text-sm text-zinc-900 dark:text-white focus:outline-none focus:border-blue-500"
                  autoFocus
                />
              </div>
              <div className="bg-yellow-50 dark:bg-yellow-900/20 rounded-lg px-3 py-2">
                <p className="text-[10px] text-yellow-600 dark:text-yellow-400">命名后，默认项目将变为正式项目，系统会自动创建新的默认项目</p>
              </div>
            </div>
            <div className="px-5 py-3 border-t border-zinc-100 dark:border-zinc-800 flex items-center justify-end gap-2">
              <button
                onClick={() => setShowRenameModal(false)}
                className="px-4 py-2 text-xs font-medium text-zinc-600 dark:text-zinc-400 hover:text-zinc-900 dark:hover:text-white transition-colors"
              >
                {t('cancel')}
              </button>
              <button
                onClick={async () => {
                  if (!renameValue.trim() || !token || !activeProject) return;
                  try {
                    const result = await projectsApi.renameProject(activeProject.id, renameValue.trim(), token);
                    setActiveProject(result.project);
                    if (token) {
                      const projectsResult = await projectsApi.getProjects(token);
                      setProjects(projectsResult.projects);
                    }
                    setShowRenameModal(false);
                  } catch (err) {
                    console.error('Failed to rename project:', err);
                  }
                }}
                disabled={!renameValue.trim()}
                className="px-4 py-2 text-xs font-medium bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-1"
              >
                <Pencil size={12} />
                确认命名
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
