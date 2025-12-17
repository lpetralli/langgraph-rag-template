## langgraph-rag-template

Plantilla mínima de **agente RAG**: combina un LLM y una tool (`buscar_info`) que recupera chunks desde **Supabase/pgvector** mediante el RPC `match_documents`, y responde **solo** en base a esa evidencia.

## Cómo funciona el agente

### Componentes

- **Agente**: `agent.py` crea `agente_rag` usando `create_agent`, pasando un LLM (`ChatOpenAI`), la tool `buscar_info`, un `system_prompt` (`prompt.py`) y el schema de contexto runtime (`context_schema=RAGContext`).
- **Prompt**: `prompt.py` define reglas estrictas obligando a usar primero la herramienta de búsqueda y evitar alucinaciones o respuestas fuera de la materia.
- **Tool de RAG**: `tools.py::buscar_info`:
  - Embebe la query con OpenAI (`text-embedding-3-small`)
  - Llama a `supabase.rpc("match_documents", ...)`
  - Devuelve una lista: `[{context, metadata, similarity}, ...]` (solo resultados con `similarity > 0.2`)
  - Implementa filtrado por runtime context según los parámetros recibidos (ver más abajo)
- **Runtime context**: `runtime_context.py::RAGContext` define los parámetros de scoping y personalización que se pueden pasar al agente *al momento de invocarlo*.

### Flujo

1. El usuario hace una pregunta.
2. El agente usa la tool `buscar_info(query, runtime=...)` para recuperar los textos relevantes desde Supabase.
3. El agente responde basándose **exclusivamente** en los `context` devueltos por la tool.

## Runtime context: scoping por materia y personalización por alumno

El runtime context permite controlar sobre qué corpus se ejecuta el RAG y pasar datos del alumno para personalización.

### Scoping por materia y archivo

- Actualmente, `RAGContext` soporta solo **`file_id`** como filtro de scoping (ver `runtime_context.py`).
- Al invocar `buscar_info`, si hay `runtime.context.file_id`, el filtro del RPC aplica: `filter={"file_id": file_id}`
- Esto permite que el agente opere solo sobre los documentos/chunks asociados a un archivo específico.
- Ejemplo de extensión: para proyectos reales deberías incluir también `materia_id` en `RAGContext` y la metadata, y modificar la lógica de la tool para filtrar por materia (por ejemplo: prioridad `materia_id` > `file_id`).

### Personalización: datos del alumno

`RAGContext` puede extenderse para incluir:
- `alumno_id`
- `alumno_nombre`
- `alumno_contexto` (dict con nivel, objetivos, carrera, dificultades, etc.)

> **Nota**: En esta plantilla, la tool de RAG **no usa** esos campos aún, solo `file_id`. Sin embargo, quedan disponibles en el runtime context para que personalices comportamientos adicionales (por ejemplo: expandir el prompt, adaptar la respuesta, ajustar el RAG, agregar pasos de perfilado, etc.).


## Probar la búsqueda en Supabase (`supabase.ipynb`)

- La notebook `supabase.ipynb` permite testear el RPC `match_documents` directamente:
  - Calcula el embedding de una query
  - Llama `supabase.rpc("match_documents", {"query_embedding": ..., "match_count": 5, "filter": {...}})`
  - Devuelve los matches (chunks) y sus metadatos
