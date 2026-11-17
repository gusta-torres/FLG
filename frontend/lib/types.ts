export type ModeloNegocio =
  | "b2b_servicos_executivos"
  | "software_saas_b2b"
  | "conhecimento_educacao"
  | "produtos_fisicos_d2c"
  | "midia_conteudo";

export type Arquetipo =
  | "nerd_rico_analitico"
  | "vendedor_gente_boa"
  | "professor_low_profile"
  | "construtor_em_publico"
  | "lider_disciplinado";

export type Canal = "linkedin" | "youtube" | "instagram" | "tiktok" | "newsletter" | "podcast";

export type PapelCanal = "primario" | "secundario";

export type NivelFunil = "topo" | "meio" | "fundo";

export type ProporcaoAtribuicao =
  | "70_assunto_industria"
  | "20_autoridade_tecnica"
  | "8_humanizacao"
  | "2_comercial_direto";

export type FormatoConteudo =
  | "carrossel"
  | "reels_shorts"
  | "artigo_linkedin"
  | "foto_texto"
  | "video_longo"
  | "stories"
  | "newsletter_edicao"
  | "podcast_episodio";

export type UserRole = "marketing" | "founder";
export type ContentStatus = "pendente" | "aprovado" | "postado";

export interface User {
  id: string;
  email: string;
  name: string;
  role: UserRole;
  founder_id: string | null;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export interface Founder {
  id: string;
  name: string;
  company_name: string;
  business_model: ModeloNegocio;
  email: string;
  created_at: string;
}

export interface ChannelAllocation {
  channel: Canal;
  role: PapelCanal;
  dedication_percent: number;
  native_formats: FormatoConteudo[];
}

export interface DiagnosticProfile {
  dominant_archetype: Arquetipo;
  secondary_archetype: Arquetipo | null;
  central_thesis: string;
  channel_allocation: ChannelAllocation[];
}

export interface InterviewQuestion {
  block: number;
  dimension: string;
  key: string;
  text: string;
}

export interface StartInterviewResponse {
  diagnostic_id: string;
  questions: InterviewQuestion[];
}

export interface AnswerResponse {
  status: "in_progress" | "completed";
  next_questions: InterviewQuestion[] | null;
}

export interface ContentItem {
  id: string;
  day: number;
  channel: Canal;
  funnel_level: NivelFunil;
  attribution: ProporcaoAtribuicao;
  format: FormatoConteudo;
  hook: string;
  central_idea: string;
  cta: string;
  status: ContentStatus;
  full_text: string | null;
  posted_at: string | null;
}

export interface EditorialGrid {
  id: string;
  founder_id: string;
  period_days: number;
  goal_posts: number;
  start_date: string | null;
  created_at: string;
  items: ContentItem[];
}

export interface LeaderboardEntry {
  founder_id: string;
  name: string;
  company_name: string;
  goal_posts: number;
  total_posts: number;
  posted_posts: number;
  completion_pct: number;
  streak: number;
  xp: number;
}

export interface CreateFounderPayload {
  name: string;
  company_name: string;
  business_model: ModeloNegocio;
  email: string;
  password: string;
}
