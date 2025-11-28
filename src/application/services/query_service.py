"""Query service for RAG-based question answering."""

import time

from src.domain.entities import QueryRequest, QueryResponse
from src.domain.interfaces import EmbeddingService, LLMClient, VectorStore


class QueryService:
    """Handles RAG queries against loaded books."""

    def __init__(
        self,
        vector_store: VectorStore,
        embedder: EmbeddingService,
        llm_client: LLMClient,
    ):
        """
        Args:
            vector_store: Vector storage for retrieval.
            embedder: Embedding service for query.
            llm_client: LLM for generation.
        """
        self.vector_store = vector_store
        self.embedder = embedder
        self.llm_client = llm_client

    async def query(self, request: QueryRequest) -> QueryResponse:
        """
        Process a RAG query.

        Args:
            request: Query request with question and session.

        Returns:
            Response with answer and sources.
        """
        start_time = time.perf_counter()

        # Embed the query
        query_embedding = self.embedder.embed_query(request.query)

        # Retrieve relevant chunks
        chunks = await self.vector_store.search(
            query_embedding=query_embedding,
            collection_id=request.session_id,
            top_k=request.top_k,
        )

        # Build context from chunks
        context = [chunk.content for chunk in chunks]

        # Generate answer with conversation history
        answer = await self.llm_client.generate(
            prompt=request.query,
            context=context,
            conversation_history=request.conversation_history,
        )

        elapsed_ms = (time.perf_counter() - start_time) * 1000

        return QueryResponse(
            answer=answer,
            sources=chunks,
            latency_ms=elapsed_ms,
        )
