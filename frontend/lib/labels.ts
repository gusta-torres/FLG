import type {
  Arquetipo,
  Canal,
  FormatoConteudo,
  ModeloNegocio,
  NivelFunil,
  ProporcaoAtribuicao,
} from "./types";

export const BUSINESS_MODEL_LABELS: Record<ModeloNegocio, string> = {
  b2b_servicos_executivos: "B2B / Consultoria / Serviços Executivos",
  software_saas_b2b: "Software / SaaS B2B",
  conhecimento_educacao: "Produtos de Conhecimento / Educação",
  produtos_fisicos_d2c: "Produtos Físicos / D2C / Consumo",
  midia_conteudo: "Empresa de Mídia e Conteúdo",
};

export const ARCHETYPE_LABELS: Record<Arquetipo, string> = {
  nerd_rico_analitico: "O Nerd Rico / Analítico",
  vendedor_gente_boa: "O Vendedor Gente Boa / Conectado",
  professor_low_profile: "O Professor / Especialista Low Profile",
  construtor_em_publico: "O Construtor em Público / Autêntico",
  lider_disciplinado: "O Líder Disciplinado / Provocador",
};

export const CHANNEL_LABELS: Record<Canal, string> = {
  linkedin: "LinkedIn",
  youtube: "YouTube",
  instagram: "Instagram",
  tiktok: "TikTok",
  newsletter: "Newsletter",
  podcast: "Podcast",
};

export const FUNNEL_LABELS: Record<NivelFunil, string> = {
  topo: "Topo de Funil",
  meio: "Meio de Funil",
  fundo: "Fundo de Funil",
};

export const FUNNEL_ORDER: NivelFunil[] = ["topo", "meio", "fundo"];

export const FUNNEL_ACCENTS: Record<NivelFunil, string> = {
  topo: "text-sky-300 border-sky-400/30 bg-sky-400/10",
  meio: "text-brand-300 border-brand-400/30 bg-brand-400/10",
  fundo: "text-amber-300 border-amber-400/30 bg-amber-400/10",
};

export const ATTRIBUTION_LABELS: Record<ProporcaoAtribuicao, string> = {
  "70_assunto_industria": "70% · Assunto/Indústria",
  "20_autoridade_tecnica": "20% · Autoridade Técnica",
  "8_humanizacao": "8% · Humanização",
  "2_comercial_direto": "2% · Comercial Direto",
};

export const FORMAT_LABELS: Record<FormatoConteudo, string> = {
  carrossel: "Carrossel",
  reels_shorts: "Reels / Shorts",
  artigo_linkedin: "Artigo LinkedIn",
  foto_texto: "Foto / Texto",
  video_longo: "Vídeo Longo",
  stories: "Stories",
  newsletter_edicao: "Edição de Newsletter",
  podcast_episodio: "Episódio de Podcast",
};

export const DAY_LABELS = [
  "Dia 1",
  "Dia 2",
  "Dia 3",
  "Dia 4",
  "Dia 5",
  "Dia 6",
  "Dia 7",
];
