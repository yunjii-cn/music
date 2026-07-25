import mainStyleText from './main_style.txt?raw';
import allStyleText from './all_style.txt?raw';

export const MAIN_STYLES = mainStyleText
  .split('\n')
  .map(line => line.trim())
  .filter(line => line.length > 0);

export const ALL_STYLES = allStyleText
  .split('\n')
  .map(line => line.trim())
  .filter(line => line.length > 0);

export const GENRE_KEYS = MAIN_STYLES;

const mainStylesLower = new Set(MAIN_STYLES.map(s => s.toLowerCase().trim()));

export const SUB_STYLES = ALL_STYLES.filter(style => {
  const styleLower = style.toLowerCase().trim();
  return !mainStylesLower.has(styleLower);
});

export type MainStyle = typeof MAIN_STYLES[number];
export type AllStyle = typeof ALL_STYLES[number];
export type SubStyle = typeof SUB_STYLES[number];

export interface StyleMeta {
  zh: string;
  desc: string;
}

const STYLE_META: Record<string, StyleMeta> = {
  '16-bit': { zh: '16位芯片音乐', desc: '复古游戏机音效风格' },
  '2-step': { zh: '两步舞曲', desc: 'UK车库音乐的基础节拍' },
  'acid house': { zh: '酸性浩室', desc: '迷幻合成器驱动的浩室音乐' },
  'acid techno': { zh: '酸性科技舞曲', desc: '硬朗节拍配酸性合成器' },
  'acid trance': { zh: '酸性迷幻', desc: '酸性音色与迷幻旋律结合' },
  'acoustic chicago blues': { zh: '芝加哥原声蓝调', desc: '传统芝加哥蓝调的原声演绎' },
  'acoustic rock': { zh: '原声摇滚', desc: '以木吉他为主的摇滚风格' },
  'acoustic texas blues': { zh: '德州原声蓝调', desc: '德州蓝调的原声传统形式' },
  'african folk': { zh: '非洲民谣', desc: '非洲传统民间音乐' },
  'afrikaner folk': { zh: '布尔人民谣', desc: '南非白人传统民谣' },
  'afro house': { zh: '非洲浩室', desc: '融合非洲节奏的浩室音乐' },
  'afro trap': { zh: '非洲陷阱', desc: '非洲旋律与陷阱节拍结合' },
  'afro-cuban jazz': { zh: '非古爵士', desc: '非洲与古巴节奏融合的爵士' },
  'afro-funk': { zh: '非洲放克', desc: '非洲节奏驱动的放克音乐' },
  'afro-jazz': { zh: '非洲爵士', desc: '非洲音乐元素与爵士融合' },
  'afro-rock': { zh: '非洲摇滚', desc: '非洲节奏与摇滚乐融合' },
  'afrobeat': { zh: '非洲节拍', desc: '尼日利亚起源的融合音乐风格' },
  'afropiano': { zh: '非洲钢琴', desc: '非洲旋律与钢琴浩室融合' },
  'afroswing': { zh: '非洲摇摆', desc: '非洲节奏与摇摆流行融合' },
  'algorave': { zh: '算法狂欢', desc: '实时编程生成的电子音乐' },
  'alternative r&b': { zh: '另类R&B', desc: '实验性与非传统的R&B风格' },
  'alternative rock': { zh: '另类摇滚', desc: '非主流的摇滚音乐风格' },
  'ambient techno': { zh: '氛围科技舞曲', desc: '氛围音乐与科技舞曲融合' },
  'anti-folk': { zh: '反民谣', desc: '颠覆传统民谣的实验风格' },
  'avant-garde jazz': { zh: '先锋爵士', desc: '突破传统的实验性爵士' },
  'bachata': { zh: '巴恰塔', desc: '多米尼加浪漫吉他舞曲' },
  'bedroom pop': { zh: '卧室流行', desc: '居家DIY制作的梦幻流行' },
  'bluegrass': { zh: '蓝草音乐', desc: '美国南方原声乡村风格' },
  'blues rock': { zh: '蓝调摇滚', desc: '蓝调与摇滚的融合风格' },
  'boogie': { zh: '布吉', desc: '70年代放克驱动的舞曲' },
  'bossa nova': { zh: '巴萨诺瓦', desc: '巴西慵懒爵士风格' },
  'bubblegum bass': { zh: '泡泡糖贝斯', desc: '可爱甜美的电子贝斯风格' },
  'bubblegum dance': { zh: '泡泡糖舞曲', desc: '甜美欢快的流行舞曲' },
  'cabaret': { zh: '卡巴莱', desc: '剧场式的歌舞表演风格' },
  'cajun': { zh: '卡津', desc: '路易斯安那法裔传统音乐' },
  'cape verdean': { zh: '佛得角音乐', desc: '大西洋岛国传统音乐' },
  'caribbean': { zh: '加勒比音乐', desc: '加勒比海地区音乐总称' },
  'carnatic': { zh: '卡纳提克', desc: '印度南方古典音乐体系' },
  'celtic': { zh: '凯尔特音乐', desc: '爱尔兰苏格兰传统音乐' },
  'chanson': { zh: '香颂', desc: '法语抒情歌曲传统' },
  'chillstep': { zh: '弛放步', desc: '柔和舒缓的回响步风格' },
  'chillsynth': { zh: '弛放合成器', desc: '放松氛围的合成器音乐' },
  'classical': { zh: '古典音乐', desc: '西方古典音乐传统' },
  'cloud rap': { zh: '云说唱', desc: '梦幻氛围的说唱风格' },
  'coptic': { zh: '科普特音乐', desc: '埃及基督教会传统音乐' },
  'cumbia': { zh: '昆比亚', desc: '哥伦比亚民间舞曲' },
  'dance': { zh: '舞曲', desc: '电子舞曲总称' },
  'dancehall': { zh: '舞厅雷鬼', desc: '牙买加电子雷鬼舞曲' },
  'dancepop': { zh: '流行舞曲', desc: '旋律感强的电子流行舞曲' },
  'dembow': { zh: '登波', desc: '加勒比节奏型驱动的舞曲' },
  'dirty south': { zh: '脏南', desc: '美国南方硬核嘻哈风格' },
  'dream pop': { zh: '梦幻流行', desc: '朦胧氛围的流行摇滚' },
  'drill': { zh: '钻头说唱', desc: '暗黑节拍的嘻哈子类型' },
  'dubstep': { zh: '回响步', desc: '重低音与切分节奏的电子乐' },
  'edm': { zh: '电子舞曲', desc: '电子舞曲商业风格总称' },
  'egyptian': { zh: '埃及音乐', desc: '埃及传统与现代音乐' },
  'garage': { zh: '车库音乐', desc: 'UK车库/2-step节奏风格' },
  'gnawa': { zh: '格纳瓦', desc: '摩洛哥苏非派精神音乐' },
  'goa trance': { zh: '果阿迷幻', desc: '印度果阿起源的迷幻舞曲' },
  'grime': { zh: '格林姆', desc: '伦敦140BPM说唱电子风格' },
  'griot': { zh: '格里奥', desc: '西非口头传统叙事音乐' },
  'grunge': { zh: '垃圾摇滚', desc: '西雅图90年代另类摇滚' },
  'hip hop': { zh: '嘻哈', desc: '说唱与节拍驱动的都市音乐' },
  'house': { zh: '浩室', desc: '4/4拍电子舞曲基础风格' },
  'hyphy': { zh: '海菲', desc: '旧金山湾区高能嘻哈风格' },
  'illbient': { zh: '暗氛围', desc: '阴暗实验的嘻哈氛围融合' },
  'indie': { zh: '独立音乐', desc: '独立制作的音乐风格' },
  'jazz': { zh: '爵士', desc: '即兴演奏为核心的美国音乐' },
  'jungle': { zh: '丛林舞曲', desc: '高速碎拍与重低音电子乐' },
  'k-pop': { zh: '韩国流行', desc: '韩国流行音乐风格' },
  'kawaii future bass': { zh: '可爱未来贝斯', desc: '日系可爱风格的未来贝斯' },
  'klezmer': { zh: '克莱兹默', desc: '东欧犹太传统庆典音乐' },
  'liquid drum and bass': { zh: '液态鼓打贝斯', desc: '柔和旋律的鼓打贝斯风格' },
  'mariachi': { zh: '墨西哥街头乐队', desc: '墨西哥传统庆典音乐' },
  'math rock': { zh: '数学摇滚', desc: '复杂节拍的实验摇滚' },
  'merengue': { zh: '梅伦格', desc: '多米尼加快节奏舞曲' },
  'motown': { zh: '摩城音乐', desc: '底特律灵魂乐厂牌风格' },
  'new jack swing': { zh: '新杰克摇摆', desc: '80年代末R&B与嘻哈融合' },
  'new wave': { zh: '新浪潮', desc: '70年代末合成器驱动的摇滚' },
  'p-funk': { zh: 'P放克', desc: '乔治克林顿的迷幻放克' },
  'pacific reggae': { zh: '太平洋雷鬼', desc: '太平洋岛国风格雷鬼' },
  'polka': { zh: '波尔卡', desc: '中欧2/4拍欢快舞曲' },
  'pop': { zh: '流行', desc: '大众化的流行音乐风格' },
  'raga': { zh: '拉格', desc: '印度古典旋律体系' },
  'rap': { zh: '说唱', desc: '节奏性口语表达的音乐形式' },
  'reggae': { zh: '雷鬼', desc: '牙买加反拍节奏音乐' },
  'rock': { zh: '摇滚', desc: '吉他驱动的流行摇滚音乐' },
  'rockabilly': { zh: '乡村摇滚', desc: '50年代摇滚与乡村融合' },
  'rumba': { zh: '伦巴', desc: '古巴起源的浪漫舞曲' },
  'salsa': { zh: '萨尔萨', desc: '拉丁美洲热情舞曲' },
  'samba': { zh: '桑巴', desc: '巴西狂欢节节奏舞曲' },
  'ska': { zh: '斯卡', desc: '牙买加快节奏反拍音乐' },
  'soul': { zh: '灵魂乐', desc: '福音与R&B融合的深情音乐' },
  'southern rock': { zh: '南方摇滚', desc: '美国南方风格的摇滚乐' },
  'surf': { zh: '冲浪音乐', desc: '60年代加州冲浪文化摇滚' },
  'surf rock': { zh: '冲浪摇滚', desc: '混响吉他驱动的冲浪风格' },
  'swamp blues': { zh: '沼泽蓝调', desc: '路易斯安那慵懒蓝调风格' },
  'swing': { zh: '摇摆乐', desc: '30年代大乐队爵士舞曲' },
  'symphonic metal': { zh: '交响金属', desc: '管弦乐编排的重金属音乐' },
  'synthpop': { zh: '合成器流行', desc: '合成器驱动的流行音乐' },
  'synthwave': { zh: '合成器浪潮', desc: '80年代复古未来主义电子乐' },
  'tango': { zh: '探戈', desc: '阿根廷双人舞曲' },
  'trance': { zh: '迷幻舞曲', desc: '旋律性强的电子舞曲风格' },
  'trap': { zh: '陷阱音乐', desc: '808低音与快速踩镲的嘻哈' },
  'tuareg': { zh: '图阿雷格', desc: '撒哈拉沙漠蓝人的吉他摇滚' },
};

const MODIFIER_ZH: Record<string, string> = {
  'dreamy': '梦幻',
  'dark': '暗黑',
  'soulful': '深情',
  'symphonic': '交响',
  'psychedelic': '迷幻',
  'prog': '前卫',
  'hypnagogic': '半梦半醒',
  'liquid': '液态',
  'hard': '硬核',
  'deep': '深邃',
  'chill': '弛放',
  'melodic': '旋律',
  'atmospheric': '氛围',
  'minimal': '极简',
  'raw': '原始',
  'lo-fi': '低保真',
  'hi-fi': '高保真',
  'acoustic': '原声',
  'electric': '电子',
  'electronic': '电子',
  'classic': '经典',
  'modern': '现代',
  'experimental': '实验',
  'traditional': '传统',
  'spiritual': '灵性',
  'upbeat': '欢快',
  'downtempo': '缓拍',
  'uptempo': '快拍',
  'futuristic': '未来',
  'retro': '复古',
  'nostalgic': '怀旧',
  'epic': '史诗',
  'cinematic': '电影感',
  'ambient': '氛围',
  'ethereal': '空灵',
  'groovy': '律动',
  'funky': '放克',
  'sleazy': '慵懒',
  'smooth': '丝滑',
  'aggressive': '激进',
  'mellow': '柔和',
  'warm': '温暖',
  'cold': '冰冷',
  'dream': '梦幻',
  'heavy': '重型',
  'soft': '轻柔',
  'fast': '快速',
  'slow': '缓慢',
  'loud': '响亮',
  'quiet': '安静',
  'new': '新',
  'old': '老',
  'big': '大',
  'small': '小',
};

const EXTRA_STYLE_ZH: Record<string, StyleMeta> = {
  'acid breaks': { zh: '酸性碎拍', desc: '酸性音色的碎拍电子乐' },
  'acid jazz': { zh: '酸性爵士', desc: '爵士与放克电子融合风格' },
  'acid rock': { zh: '酸性摇滚', desc: '迷幻效果器驱动的摇滚' },
  'alt-country': { zh: '另类乡村', desc: '非传统的乡村音乐风格' },
  'alt-pop': { zh: '另类流行', desc: '实验性的流行音乐' },
  'americana': { zh: '美式民谣', desc: '美国根源音乐融合风格' },
  'american primitivism': { zh: '美国原始主义', desc: '极简原声吉他实验风格' },
  'ambient dub': { zh: '氛围回响', desc: '氛围音乐与回响融合' },
  'ambient house': { zh: '氛围浩室', desc: '柔和氛围的浩室音乐' },
  'ambient noise wall': { zh: '氛围噪音墙', desc: '密集持续的噪音氛围' },
  'ambient trance': { zh: '氛围迷幻', desc: '柔和氛围的迷幻舞曲' },
  'appalachian folk': { zh: '阿巴拉契亚民谣', desc: '美国东部山区传统音乐' },
  'barbershop': { zh: '理发店和声', desc: '四声部无伴奏和声演唱' },
  'balkan brass band': { zh: '巴尔干铜管乐队', desc: '东南欧婚礼庆典铜管乐' },
  'big band': { zh: '大乐队', desc: '大型爵士管弦乐队' },
  'boom bap': { zh: '布姆巴普', desc: '90年代经典东海岸嘻哈' },
  'breakbeat': { zh: '碎拍', desc: '切分鼓点驱动的电子舞曲' },
  'breakstep': { zh: '碎拍步', desc: '碎拍与2-step融合风格' },
  'calypso': { zh: '卡里普索', desc: '特立尼达民间叙事歌曲' },
  'chillwave': { zh: '弛放波', desc: '梦幻朦胧的合成器流行' },
  'city pop': { zh: '城市流行', desc: '70-80年代日本都市流行' },
  'crunk': { zh: '旷克', desc: '美国南方高能说唱风格' },
  'delta blues': { zh: '三角洲蓝调', desc: '密西西比三角洲原声蓝调' },
  'disco': { zh: '迪斯科', desc: '70年代流行舞曲风格' },
  'doo-wop': { zh: '嘟喔普', desc: '50年代和声演唱风格' },
  'drill and bass': { zh: '钻打贝斯', desc: '高速碎拍与低音结合' },
  'drum and bass': { zh: '鼓打贝斯', desc: '高速碎拍电子舞曲' },
  'drumstep': { zh: '鼓步', desc: '鼓打贝斯与回响步融合' },
  'electropop': { zh: '电子流行', desc: '电子合成器驱动的流行乐' },
  'flamenco': { zh: '弗拉门戈', desc: '西班牙安达卢西亚艺术音乐' },
  'folk': { zh: '民谣', desc: '民间传统音乐风格' },
  'funk': { zh: '放克', desc: '律动感强的节奏音乐' },
  'future bass': { zh: '未来贝斯', desc: '明亮合成器和弦的电子乐' },
  'g-funk': { zh: 'G放克', desc: '西海岸放克风格说唱' },
  'glitch hop': { zh: '故障嘻哈', desc: '数字故障美学的嘻哈电子' },
  'gospel': { zh: '福音音乐', desc: '基督教会音乐传统' },
  'hawaiian': { zh: '夏威夷音乐', desc: '夏威夷传统滑吉他音乐' },
  'harpischord': { zh: '大键琴', desc: '巴洛克时期键盘乐器风格' },
  'j-pop': { zh: '日本流行', desc: '日本流行音乐风格' },
  'jazzwave': { zh: '爵士浪潮', desc: '爵士与合成器浪潮融合' },
  'koto': { zh: '筝', desc: '日本传统筝乐风格' },
  'mento': { zh: '门托', desc: '牙买加传统民间音乐' },
  'metal': { zh: '金属', desc: '重型吉他驱动的摇滚' },
  'norteño': { zh: '北方音乐', desc: '墨西哥北部手风琴音乐' },
  'opera': { zh: '歌剧', desc: '西方古典声乐戏剧' },
  'piano': { zh: '钢琴', desc: '钢琴演奏风格' },
  'popcore': { zh: '流行核', desc: '流行与金属核融合风格' },
  'psybient': { zh: '迷幻氛围', desc: '迷幻与氛围电子融合' },
  'punk': { zh: '朋克', desc: '反叛简约的摇滚风格' },
  'reggaeton': { zh: '雷鬼顿', desc: '拉丁都市舞曲风格' },
  'roots reggae': { zh: '根源雷鬼', desc: '传统纯正的雷鬼音乐' },
  'saxophone': { zh: '萨克斯', desc: '萨克斯管演奏风格' },
  'sertanejo': { zh: '塞尔塔内乔', desc: '巴西乡村音乐风格' },
  'shoegaze': { zh: '盯鞋', desc: '密集吉他音墙的梦幻摇滚' },
  'sitar': { zh: '西塔尔', desc: '印度传统弦乐风格' },
  'slushwave': { zh: '泥泞波', desc: '降速处理的梦幻氛围' },
  'soulful': { zh: '深情', desc: '充满情感的演唱风格' },
  'tabla': { zh: '塔布拉', desc: '印度传统鼓乐风格' },
  'techno': { zh: '科技舞曲', desc: '底特律起源的电子舞曲' },
  'r&b': { zh: 'R&B', desc: '节奏蓝调音乐风格' },
  'country': { zh: '乡村音乐', desc: '美国南方乡村传统音乐' },
  'emo': { zh: '情绪摇滚', desc: '情感表达强烈的摇滚' },
  'liverpool': { zh: '利物浦', desc: '利物浦摇滚传统风格' },
  'tokyo': { zh: '东京', desc: '东京都市音乐风格' },
  'havana': { zh: '哈瓦那', desc: '古巴哈瓦那音乐风格' },
  'dakar': { zh: '达喀尔', desc: '塞内加尔首都音乐风格' },
  'new orleans': { zh: '新奥尔良', desc: '新奥尔良爵士传统' },
  'bengali': { zh: '孟加拉', desc: '孟加拉地区音乐风格' },
  'mandarin': { zh: '华语', desc: '华语流行音乐风格' },
  'korean': { zh: '韩语', desc: '韩语音乐风格' },
  'japanese': { zh: '日语', desc: '日语音乐风格' },
  'arabic': { zh: '阿拉伯', desc: '阿拉伯音乐风格' },
  'hindi': { zh: '印地语', desc: '印地语音乐风格' },
  'urdu': { zh: '乌尔都', desc: '乌尔都语音乐风格' },
  'portuguese': { zh: '葡萄牙语', desc: '葡萄牙语音乐风格' },
  'spanish': { zh: '西班牙语', desc: '西班牙语音乐风格' },
  'russian': { zh: '俄语', desc: '俄语音乐风格' },
  'french': { zh: '法语', desc: '法语音乐风格' },
  'accordion': { zh: '手风琴', desc: '手风琴演奏风格' },
  'piano': { zh: '钢琴', desc: '钢琴演奏风格' },
  'saxophone': { zh: '萨克斯', desc: '萨克斯管演奏风格' },
  'harpischord': { zh: '大键琴', desc: '巴洛克键盘乐器风格' },
  'koto': { zh: '筝', desc: '日本传统筝乐风格' },
  'tabla': { zh: '塔布拉', desc: '印度传统鼓乐风格' },
  'choral': { zh: '合唱', desc: '合唱团演唱风格' },
  'instrumental': { zh: '器乐', desc: '纯器乐演奏无演唱' },
  'dancecore': { zh: '舞曲核', desc: '硬核舞曲风格' },
  'dubstepcore': { zh: '回响步核', desc: '回响步与硬核融合' },
  'reggaetonwave': { zh: '雷鬼顿波', desc: '雷鬼顿与合成器波融合' },
  'cabaretwave': { zh: '卡巴莱波', desc: '卡巴莱与合成器波融合' },
  'chillwavewave': { zh: '弛放波波', desc: '双层弛放波效果' },
  'classicalwave': { zh: '古典波', desc: '古典与合成器波融合' },
  'anti-folkwave': { zh: '反民谣波', desc: '反民谣与合成器波融合' },
  'breakbeatwave': { zh: '碎拍波', desc: '碎拍与合成器波融合' },
  'rumbawave': { zh: '伦巴波', desc: '伦巴与合成器波融合' },
  'surfwave': { zh: '冲浪波', desc: '冲浪与合成器波融合' },
  'gnawawave': { zh: '格纳瓦波', desc: '格纳瓦与合成器波融合' },
  'norteñowave': { zh: '北方波', desc: '北方音乐与合成器波融合' },
  'gospelwave': { zh: '福音波', desc: '福音与合成器波融合' },
  'illbientwave': { zh: '暗氛围波', desc: '暗氛围与合成器波融合' },
  'electro-chanson': { zh: '电子香颂', desc: '电子化的法语香颂' },
  'electro-bossa nova': { zh: '电子巴萨诺瓦', desc: '电子化的巴萨诺瓦' },
  'electro-alternative r&b': { zh: '电子另类R&B', desc: '电子化的另类R&B' },
  'electro-acid house': { zh: '电子酸性浩室', desc: '电子化的酸性浩室' },
  'electro-classical': { zh: '电子古典', desc: '电子化的古典音乐' },
  'electro-jungle': { zh: '电子丛林', desc: '电子化的丛林舞曲' },
  'electro-new wave': { zh: '电子新浪潮', desc: '电子化的新浪潮' },
  'electro-techno': { zh: '电子科技舞曲', desc: '电子化的科技舞曲' },
  'hyper-house': { zh: '超浩室', desc: '加速变奏的浩室音乐' },
  'hyper-crunk': { zh: '超旷克', desc: '加速变奏的旷克风格' },
  'hyper-dance': { zh: '超舞曲', desc: '加速变奏的舞曲风格' },
  'hyper-grime': { zh: '超格林姆', desc: '加速变奏的格林姆' },
  'hyper-egyptian': { zh: '超埃及', desc: '加速变奏的埃及风格' },
  'hyper-indie': { zh: '超独立', desc: '加速变奏的独立音乐' },
  'hyper-jungle': { zh: '超丛林', desc: '加速变奏的丛林舞曲' },
  'hyper-motown': { zh: '超摩城', desc: '加速变奏的摩城风格' },
  'hyper-southern rock': { zh: '超南方摇滚', desc: '加速变奏的南方摇滚' },
  'hyper-roots reggae': { zh: '超根源雷鬼', desc: '加速变奏的根源雷鬼' },
  'hyper-afrobeat': { zh: '超非洲节拍', desc: '加速变奏的非洲节拍' },
  'hyper-acid house': { zh: '超酸性浩室', desc: '加速变奏的酸性浩室' },
  'hyper-2-step': { zh: '超两步', desc: '加速变奏的两步舞曲' },
  'hyper-blues rock': { zh: '超蓝调摇滚', desc: '加速变奏的蓝调摇滚' },
  'hyper-afrikaner folk': { zh: '超布尔人民谣', desc: '加速变奏的布尔人民谣' },
};

const ALL_KNOWN_STYLES = new Map<string, StyleMeta>();
for (const [k, v] of Object.entries(STYLE_META)) ALL_KNOWN_STYLES.set(k.toLowerCase(), v);
for (const [k, v] of Object.entries(EXTRA_STYLE_ZH)) ALL_KNOWN_STYLES.set(k.toLowerCase(), v);

function trySplitCompound(style: string): StyleMeta | undefined {
  const parts = style.split(' ').filter(p => p.length > 0);
  if (parts.length < 2) return undefined;

  for (let i = 1; i < parts.length; i++) {
    const prefix = parts.slice(0, i).join(' ');
    const suffix = parts.slice(i).join(' ');
    const prefixLower = prefix.toLowerCase();
    const suffixLower = suffix.toLowerCase();

    const prefixMeta = ALL_KNOWN_STYLES.get(prefixLower) || (MODIFIER_ZH[prefixLower] ? { zh: MODIFIER_ZH[prefixLower], desc: '' } : undefined);
    const suffixMeta = ALL_KNOWN_STYLES.get(suffixLower);

    if (prefixMeta && suffixMeta) {
      return {
        zh: `${prefixMeta.zh}${suffixMeta.zh}`,
        desc: `${prefixMeta.desc ? prefixMeta.desc + '的' : ''}${suffixMeta.desc || suffixMeta.zh}`.replace(/^的/, ''),
      };
    }
  }

  if (parts.length >= 2) {
    const firstLower = parts[0].toLowerCase();
    const restLower = parts.slice(1).join(' ').toLowerCase();
    const modZh = MODIFIER_ZH[firstLower];
    const restMeta = ALL_KNOWN_STYLES.get(restLower);
    if (modZh && restMeta) {
      return {
        zh: `${modZh}${restMeta.zh}`,
        desc: `${modZh}风格的${restMeta.desc || restMeta.zh}`,
      };
    }
    const firstMeta = ALL_KNOWN_STYLES.get(firstLower);
    const restMeta2 = ALL_KNOWN_STYLES.get(restLower);
    if (firstMeta && restMeta2) {
      return {
        zh: `${firstMeta.zh}${restMeta2.zh}`,
        desc: `${firstMeta.desc || firstMeta.zh}与${restMeta2.desc || restMeta2.zh}融合`,
      };
    }
  }

  return undefined;
}

const metaCache = new Map<string, StyleMeta | undefined>();

export function getStyleMeta(style: string): StyleMeta | undefined {
  const key = style.toLowerCase().trim();
  if (metaCache.has(key)) return metaCache.get(key);

  let result = ALL_KNOWN_STYLES.get(key);
  if (!result) {
    result = trySplitCompound(key);
  }
  metaCache.set(key, result);
  return result;
}
