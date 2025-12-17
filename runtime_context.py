from typing import Optional

from pydantic import BaseModel


class RAGContext(BaseModel):
    """
    Runtime context (inyectado al invocar el agente) para controlar filtros en RAG.

    Por ahora soporta solo scoping por `file_id`, que se usa para filtrar
    en el RPC `match_documents` (pgvector) vía `filter={"file_id": file_id}`.
    """

    file_id: Optional[str] = None
