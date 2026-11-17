"""Enums do domínio FLG, extraídos diretamente da especificação técnica."""

from enum import StrEnum


class Arquetipo(StrEnum):
    """Arquétipos nativos de posicionamento do fundador (Módulo 1)."""

    NERD_RICO_ANALITICO = "nerd_rico_analitico"
    VENDEDOR_GENTE_BOA = "vendedor_gente_boa"
    PROFESSOR_LOW_PROFILE = "professor_low_profile"
    CONSTRUTOR_EM_PUBLICO = "construtor_em_publico"
    LIDER_DISCIPLINADO = "lider_disciplinado"


class ModeloNegocio(StrEnum):
    """Modelo de negócio da empresa (Módulo 2)."""

    B2B_SERVICOS = "b2b_servicos_executivos"
    SOFTWARE_SAAS = "software_saas_b2b"
    CONHECIMENTO_EDUCACAO = "conhecimento_educacao"
    PRODUTOS_FISICOS_D2C = "produtos_fisicos_d2c"
    MIDIA_CONTEUDO = "midia_conteudo"


class Canal(StrEnum):
    """Canais de distribuição digital (Módulo 2)."""

    LINKEDIN = "linkedin"
    YOUTUBE = "youtube"
    INSTAGRAM = "instagram"
    TIKTOK = "tiktok"
    NEWSLETTER = "newsletter"
    PODCAST = "podcast"


class PapelCanal(StrEnum):
    """Papel do canal na alocação 70/30."""

    PRIMARIO = "primario"
    SECUNDARIO = "secundario"


class NivelFunil(StrEnum):
    """Nível do funil de vendas (Módulo 3)."""

    TOPO = "topo"
    MEIO = "meio"
    FUNDO = "fundo"


class ProporcaoAtribuicao(StrEnum):
    """Modelo 70-20-8-2 de proporção de atribuição de conteúdo (Módulo 3)."""

    ASSUNTO_INDUSTRIA = "70_assunto_industria"
    AUTORIDADE_TECNICA = "20_autoridade_tecnica"
    HUMANIZACAO = "8_humanizacao"
    COMERCIAL_DIRETO = "2_comercial_direto"


class FormatoConteudo(StrEnum):
    """Formatos nativos de conteúdo por canal."""

    CARROSSEL = "carrossel"
    REELS_SHORTS = "reels_shorts"
    ARTIGO_LINKEDIN = "artigo_linkedin"
    FOTO_TEXTO = "foto_texto"
    VIDEO_LONGO = "video_longo"
    STORIES = "stories"
    NEWSLETTER_EDICAO = "newsletter_edicao"
    PODCAST_EPISODIO = "podcast_episodio"


class DimensaoDiagnostica(StrEnum):
    """As quatro dimensões analíticas da Matriz de Diagnóstico (Módulo 1)."""

    TESE_CORE_MERCADO = "tese_core_mercado"
    REPERTORIO_TECNICO = "repertorio_tecnico_historico"
    FRONTEIRAS_ROTINA = "fronteiras_pessoais_rotina"
    PERFIL_COMUNICACIONAL = "perfil_comunicacional_nativo"


class UserRole(StrEnum):
    """Papéis de acesso ao sistema."""

    MARKETING = "marketing"
    FOUNDER = "founder"


class ContentStatus(StrEnum):
    """Ciclo de vida de um post no calendário."""

    PENDENTE = "pendente"
    APROVADO = "aprovado"
    POSTADO = "postado"
