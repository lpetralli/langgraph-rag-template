import os
from typing import Any, Optional

from dotenv import load_dotenv
from langchain.tools import ToolRuntime, tool
from openai import OpenAI
from supabase import create_client

from runtime_context import RAGContext

load_dotenv()

_supabase = None
_openai = None


def _get_supabase():
    global _supabase
    if _supabase is None:
        url = os.environ["SUPABASE_URL"]
        key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY") or os.environ["SUPABASE_ANON_KEY"]
        _supabase = create_client(url, key)
    return _supabase


def _get_openai():
    global _openai
    if _openai is None:
        _openai = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    return _openai


def _embed(text: str) -> list[float]:
    client = _get_openai()
    r = client.embeddings.create(model="text-embedding-3-small", input=text)
    return r.data[0].embedding


def _to_pgvector(v: list[float]) -> str:
    # Formato compatible con pgvector vía PostgREST/RPC
    return "[" + ",".join(f"{x:.8f}" for x in v) + "]"


@tool
def buscar_info(
    query: str,
    runtime: ToolRuntime[RAGContext],
) -> list[dict[str, Any]]:
    """
    Siempre que la pregunta esté relacionada con el contenido de una materia,
    se debe buscar primero con esta herramienta y luego responder basándose solo
    en la información obtenida de la tool. Realiza una búsqueda de chunks similares
    en Supabase usando pgvector (RPC match_documents).
    Devuelve una lista limpia: [{context, metadata, similarity}, ...], solo resultados con similarity > 0.5.
    """
    sb = _get_supabase()
    q_emb = _to_pgvector(_embed(query))


    runtime_filter: dict[str, Any] = {}
    ctx = getattr(runtime, "context", None)
    file_id = getattr(ctx, "file_id", None) if ctx is not None else None
    if file_id:
        runtime_filter["file_id"] = file_id


    payload = {
        "query_embedding": q_emb,
        "match_count": 5,
        "filter": runtime_filter,
    }

    res = sb.rpc("match_documents", payload).execute()
    rows = res.data or []


    cleaned = []
    for r in rows:
        similarity = r.get("similarity")
        if similarity is not None and similarity > 0.2:
            cleaned.append(
                {
                    "context": r.get("context") or r.get("content"),
                    "metadata": r.get("metadata"),
                    "similarity": similarity,
                }
            )
    return cleaned
