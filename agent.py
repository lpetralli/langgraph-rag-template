from langchain.agents import create_agent
from langchain_openai import ChatOpenAI
from prompt import SYSTEM_PROMPT
from tools import buscar_info
from runtime_context import RAGContext


llm = ChatOpenAI(
    model="gpt-4.1",
    temperature=0,
    streaming=False,
)


agente_rag = create_agent(
    model=llm,
    tools=[buscar_info],
    system_prompt=SYSTEM_PROMPT,
    name="agente_rag",
    context_schema=RAGContext,
)