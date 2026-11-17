"""Contêiner de dependências (LLM e grafo) com cache."""

from functools import lru_cache

from app.config import get_settings
from app.graph.flg_graph import FLGGraph
from app.llm.base import LLMProvider, ProviderFactory


@lru_cache
def get_llm() -> LLMProvider:
    return ProviderFactory.create(get_settings())


@lru_cache
def get_graph() -> FLGGraph:
    return FLGGraph(get_llm())
