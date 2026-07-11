/**
 * 多语言文案 — 云集智能音乐创意台官网
 *
 * 新增语言：在 locales 对象加一个键（如 'fr': {...}），
 * 并在 config.js 的 i18n.available 里登记即可。
 */

const locales = {
  'zh-CN': {
    nav: { home: '首页', features: '功能', how: '使用教程', download: '下载' },
    hero: {
      badge: '本地优先 · 隐私安全',
      title: '用 AI 创作属于你的音乐',
      subtitle: '文本生成音乐、智能翻唱、LoRA 风格训练——全部在你的显卡上完成，数据不出本机。',
      ctaPrimary: '免费下载',
      ctaSecondary: '登录创作',
      stats: ['文本生成音乐', '翻唱 / 风格迁移', 'LoRA 训练'],
    },
    features: {
      title: '核心功能',
      subtitle: '从灵感到成片，一站式 AI 音乐工作流',
      items: [
        { icon: '🎵', title: '文本生成音乐', desc: '输入风格、歌词与情绪，秒级生成完整歌曲，支持多语言歌词与元信息。' },
        { icon: '🔁', title: '智能翻唱', desc: '上传参考音频，保留旋律迁移风格；可调噪声强度控制还原度。' },
        { icon: '🎓', title: 'LoRA 风格训练', desc: '用少量样本训练专属风格模型，简易 / 标准双模式适配不同水平。' },
        { icon: '🖥️', title: '本地运行', desc: '模型与推理全在本地显卡，无需上传素材，隐私零泄露。' },
        { icon: '⚡', title: '极速推理', desc: 'Turbo 模型 8 步出片，配合缓存机制秒开即用。' },
        { icon: '🌐', title: '多语言支持', desc: '界面含简繁英日韩，歌词生成覆盖主流语种。' },
      ],
    },
    how: {
      title: '三步开始创作',
      subtitle: '无需音乐基础，人人都是创作者',
      steps: [
        { n: '1', title: '下载并启动', desc: '选择对应系统版本，启动后自动打开创作界面。' },
        { n: '2', title: '描述你的音乐', desc: '填写风格、歌词与参数，或上传参考音频做翻唱。' },
        { n: '3', title: '生成与训练', desc: '一键生成试听，满意后可训练专属 LoRA 风格。' },
      ],
    },
    download: {
      title: '下载客户端',
      subtitle: '支持 Windows / macOS / Linux',
      windows: 'Windows 版',
      mac: 'macOS 版',
      linux: 'Linux 版',
      note: '首次启动会自动下载所需模型权重（数 GB），请确保网络通畅。',
    },
    login: {
      title: '扫码登录',
      subtitle: '使用微信扫一扫，安全登录云集账号',
      scanHint: '请使用微信扫描二维码',
      loggingIn: '登录中，请稍候…',
      loginSuccess: '登录成功，正在跳转…',
      loginFailed: '登录失败，请重试',
      switchAccount: '切换账号',
      logout: '退出登录',
      welcome: '你好，',
    },
    footer: { privacy: '隐私政策', terms: '服务条款', contact: '联系我们' },
    common: { language: '语言' },
  },

  'zh-TW': {
    nav: { home: '首頁', features: '功能', how: '使用教學', download: '下載' },
    hero: {
      badge: '本地優先 · 隱私安全',
      title: '用 AI 創作屬於你的音樂',
      subtitle: '文字生成音樂、智慧翻唱、LoRA 風格訓練——全部在你的顯卡上完成，資料不出本機。',
      ctaPrimary: '免費下載',
      ctaSecondary: '登入創作',
      stats: ['文字生成音樂', '翻唱 / 風格遷移', 'LoRA 訓練'],
    },
    features: {
      title: '核心功能',
      subtitle: '從靈感到成片，一站式 AI 音樂工作流',
      items: [
        { icon: '🎵', title: '文字生成音樂', desc: '輸入風格、歌詞與情緒，秒級生成完整歌曲，支援多語言歌詞與元資訊。' },
        { icon: '🔁', title: '智慧翻唱', desc: '上傳參考音訊，保留旋律遷移風格；可調噪聲強度控制還原度。' },
        { icon: '🎓', title: 'LoRA 風格訓練', desc: '用少量樣本訓練專屬風格模型，簡易 / 標準雙模式適配不同水平。' },
        { icon: '🖥️', title: '本地執行', desc: '模型與推理全在本地顯卡，無需上傳素材，隱私零洩露。' },
        { icon: '⚡', title: '極速推理', desc: 'Turbo 模型 8 步出片，配合快取機制秒開即用。' },
        { icon: '🌐', title: '多語言支援', desc: '介面含簡繁英日韓，歌詞生成涵蓋主流語種。' },
      ],
    },
    how: {
      title: '三步開始創作',
      subtitle: '無需音樂基礎，人人都是創作者',
      steps: [
        { n: '1', title: '下載並啟動', desc: '選擇對應系統版本，啟動後自動開啟創作介面。' },
        { n: '2', title: '描述你的音樂', desc: '填寫風格、歌詞與參數，或上傳參考音訊做翻唱。' },
        { n: '3', title: '生成與訓練', desc: '一鍵生成試聽，滿意後可訓練專屬 LoRA 風格。' },
      ],
    },
    download: {
      title: '下載客戶端',
      subtitle: '支援 Windows / macOS / Linux',
      windows: 'Windows 版',
      mac: 'macOS 版',
      linux: 'Linux 版',
      note: '首次啟動會自動下載所需模型權重（數 GB），請確保網路暢通。',
    },
    login: {
      title: '掃碼登入',
      subtitle: '使用微信掃一掃，安全登入雲集帳號',
      scanHint: '請使用微信掃描二維碼',
      loggingIn: '登入中，請稍候…',
      loginSuccess: '登入成功，正在跳轉…',
      loginFailed: '登入失敗，請重試',
      switchAccount: '切換帳號',
      logout: '登出',
      welcome: '你好，',
    },
    footer: { privacy: '隱私政策', terms: '服務條款', contact: '聯絡我們' },
    common: { language: '語言' },
  },

  en: {
    nav: { home: 'Home', features: 'Features', how: 'How it works', download: 'Download' },
    hero: {
      badge: 'Local-first · Private',
      title: 'Create Music with AI, Your Way',
      subtitle: 'Text-to-music, smart cover, and LoRA style training — all on your own GPU, nothing leaves your machine.',
      ctaPrimary: 'Download Free',
      ctaSecondary: 'Sign in to Create',
      stats: ['Text-to-Music', 'Cover / Style Transfer', 'LoRA Training'],
    },
    features: {
      title: 'Core Features',
      subtitle: 'From idea to master, an end-to-end AI music workflow',
      items: [
        { icon: '🎵', title: 'Text-to-Music', desc: 'Describe style, lyrics and mood to generate a full song in seconds, with multilingual lyrics and metadata.' },
        { icon: '🔁', title: 'Smart Cover', desc: 'Upload reference audio to keep the melody while transferring style; tune noise strength for fidelity.' },
        { icon: '🎓', title: 'LoRA Style Training', desc: 'Train a personal style model from a few samples, with Simple / Standard modes for every level.' },
        { icon: '🖥️', title: 'Runs Locally', desc: 'Models and inference stay on your local GPU — no uploads, zero privacy leaks.' },
        { icon: '⚡', title: 'Blazing Fast', desc: 'Turbo model renders in 8 steps, with caching for instant startup.' },
        { icon: '🌐', title: 'Multilingual', desc: 'UI in Simplified/Traditional Chinese, English, Japanese, Korean; lyrics in major languages.' },
      ],
    },
    how: {
      title: 'Start in 3 Steps',
      subtitle: 'No music background needed — everyone is a creator',
      steps: [
        { n: '1', title: 'Download & Launch', desc: 'Pick your OS, launch, and the studio opens automatically.' },
        { n: '2', title: 'Describe Your Music', desc: 'Fill in style, lyrics and params, or upload audio for a cover.' },
        { n: '3', title: 'Generate & Train', desc: 'Generate and preview in one click; train your own LoRA when happy.' },
      ],
    },
    download: {
      title: 'Download the App',
      subtitle: 'Windows / macOS / Linux',
      windows: 'Windows',
      mac: 'macOS',
      linux: 'Linux',
      note: 'On first launch the required model weights (several GB) are downloaded automatically — keep your network connected.',
    },
    login: {
      title: 'Scan to Sign In',
      subtitle: 'Use WeChat to scan and securely sign in to your Yunji account',
      scanHint: 'Please scan the QR code with WeChat',
      loggingIn: 'Signing in, please wait…',
      loginSuccess: 'Signed in, redirecting…',
      loginFailed: 'Sign in failed, please retry',
      switchAccount: 'Switch account',
      logout: 'Sign out',
      welcome: 'Hi, ',
    },
    footer: { privacy: 'Privacy', terms: 'Terms', contact: 'Contact' },
    common: { language: 'Language' },
  },

  ja: {
    nav: { home: 'ホーム', features: '機能', how: '使い方', download: 'ダウンロード' },
    hero: {
      badge: 'ローカル優先 · プライベート',
      title: 'AI で、あなたの音楽を作ろう',
      subtitle: 'テキストから音楽、スマートカバー、LoRA スタイル学習——すべてあなたの GPU 上で完結し、データは外に出ません。',
      ctaPrimary: '無料ダウンロード',
      ctaSecondary: 'ログインして作成',
      stats: ['テキスト→音楽', 'カバー / スタイル変換', 'LoRA 学習'],
    },
    features: {
      title: '主要機能',
      subtitle: 'アイデアから完成まで、一貫した AI 音楽ワークフロー',
      items: [
        { icon: '🎵', title: 'テキスト→音楽', desc: 'スタイル・歌詞・雰囲気を入力するだけで、数秒で完成曲を生成。多言語歌詞とメタデータに対応。' },
        { icon: '🔁', title: 'スマートカバー', desc: '参照音声をアップロードしメロディを保持したままスタイルを移転。ノイズ強度で再現度を調整。' },
        { icon: '🎓', title: 'LoRA スタイル学習', desc: '少数サンプルで専用スタイルを学習。簡易／標準モードでレベルに合わせて選択。' },
        { icon: '🖥️', title: 'ローカル実行', desc: 'モデルと推論はすべてローカル GPU 上。アップロード不要でプライバシー零漏洩。' },
        { icon: '⚡', title: '超高速推論', desc: 'Turbo モデルは 8 ステップで出力。キャッシュで即時起動。' },
        { icon: '🌐', title: '多言語対応', desc: 'UI は簡繁中・英・日・韓、歌詞は主要言語に対応。' },
      ],
    },
    how: {
      title: '3 ステップで開始',
      subtitle: '音楽の知識は不要、誰もがクリエイター',
      steps: [
        { n: '1', title: 'ダウンロードと起動', desc: 'OS を選んで起動すると、スタジオが自動的に開きます。' },
        { n: '2', title: '音楽を記述', desc: 'スタイル・歌詞・パラメータを入力、またはカバー用に音声をアップロード。' },
        { n: '3', title: '生成と学習', desc: 'ワンクリックで生成・試聴。気に入ったら専用 LoRA を学習。' },
      ],
    },
    download: {
      title: 'アプリをダウンロード',
      subtitle: 'Windows / macOS / Linux 対応',
      windows: 'Windows 版',
      mac: 'macOS 版',
      linux: 'Linux 版',
      note: '初回起動時に必要なモデル重み（数 GB）を自動ダウンロードします。通信環境をご確認ください。',
    },
    login: {
      title: 'スキャンしてログイン',
      subtitle: 'WeChat でスキャンし、雲集アカウントに安全にログイン',
      scanHint: 'WeChat で QR コードをスキャンしてください',
      loggingIn: 'ログイン中、少々お待ちください…',
      loginSuccess: 'ログイン成功、遷移中…',
      loginFailed: 'ログイン失敗、再試行してください',
      switchAccount: 'アカウント切替',
      logout: 'ログアウト',
      welcome: 'こんにちは、',
    },
    footer: { privacy: 'プライバシー', terms: '利用規約', contact: 'お問い合わせ' },
    common: { language: '言語' },
  },

  ko: {
    nav: { home: '홈', features: '기능', how: '사용 방법', download: '다운로드' },
    hero: {
      badge: '로컬 우선 · 개인정보 보호',
      title: 'AI 로 당신의 음악을 만들어요',
      subtitle: '텍스트 음악 생성, 스마트 커버, LoRA 스타일 학습 — 모두 당신의 GPU 에서 완료되고 데이터는 외부로 나가지 않습니다.',
      ctaPrimary: '무료 다운로드',
      ctaSecondary: '로그인하여 만들기',
      stats: ['텍스트→음악', '커버 / 스타일 전송', 'LoRA 학습'],
    },
    features: {
      title: '핵심 기능',
      subtitle: '영감부터 완성까지, 올인원 AI 음악 워크플로우',
      items: [
        { icon: '🎵', title: '텍스트→음악', desc: '스타일·가사·분위기를 입력하면 몇 초 만에 완성곡 생성. 다국어 가사와 메타데이터 지원.' },
        { icon: '🔁', title: '스마트 커버', desc: '참조 오디오를 업로드해 멜로디를 유지한 채 스타일 전송. 노이즈 강도로 재현도 조절.' },
        { icon: '🎓', title: 'LoRA 스타일 학습', desc: '소수 샘플로 전용 스타일 모델 학습. 간편/표준 모드로 수준에 맞춰 선택.' },
        { icon: '🖥️', title: '로컬 실행', desc: '모델과 추론은 모두 로컬 GPU 에서. 업로드 없이 개인정보 완벽 보호.' },
        { icon: '⚡', title: '초고속 추론', desc: 'Turbo 모델은 8 스텝 출력. 캐시로 즉시 시작.' },
        { icon: '🌐', title: '다국어 지원', desc: 'UI 는 간체/번체 중국어·영어·일본어·한국어, 가사는 주요 언어 지원.' },
      ],
    },
    how: {
      title: '3 단계로 시작',
      subtitle: '음악 지식 없이도 누구나 크리에이터',
      steps: [
        { n: '1', title: '다운로드 및 실행', desc: 'OS 를 선택해 실행하면 스튜디오가 자동으로 열립니다.' },
        { n: '2', title: '음악 설명하기', desc: '스타일·가사·파라미터를 입력하거나 커버용 오디오 업로드.' },
        { n: '3', title: '생성 및 학습', desc: '원클릭으로 생성·미리듣기. 마음에 들면 전용 LoRA 학습.' },
      ],
    },
    download: {
      title: '앱 다운로드',
      subtitle: 'Windows / macOS / Linux 지원',
      windows: 'Windows 버전',
      mac: 'macOS 버전',
      linux: 'Linux 버전',
      note: '첫 실행 시 필요한 모델 가중치(수 GB)를 자동 다운로드하니 네트워크 연결을 유지하세요.',
    },
    login: {
      title: '스캔하여 로그인',
      subtitle: 'WeChat 으로 스캔해 윈지 계정에 안전하게 로그인',
      scanHint: 'WeChat 으로 QR 코드를 스캔해 주세요',
      loggingIn: '로그인 중, 잠시만 기다려 주세요…',
      loginSuccess: '로그인 성공, 이동 중…',
      loginFailed: '로그인 실패, 다시 시도해 주세요',
      switchAccount: '계정 전환',
      logout: '로그아웃',
      welcome: '안녕하세요, ',
    },
    footer: { privacy: '개인정보', terms: '이용약관', contact: '문의하기' },
    common: { language: '언어' },
  },
};

if (typeof module !== 'undefined' && module.exports) module.exports = locales;
if (typeof window !== 'undefined') window.__I18N__ = locales;
