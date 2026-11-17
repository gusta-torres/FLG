import os

# Os testes não devem depender do .env do desenvolvedor (ex: provedor real).
# Variáveis de ambiente têm precedência sobre o arquivo .env no pydantic-settings.
os.environ["LLM_PROVIDER"] = "mock"
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"
