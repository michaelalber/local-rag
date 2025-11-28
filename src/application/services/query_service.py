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
        neighbor_window: int = 1,
    ):
        """
        Args:
            vector_store: Vector storage for retrieval.
            embedder: Embedding service for query.
            llm_client: LLM for generation.
            neighbor_window: Number of neighboring chunks to include (±N).
        """
        self.vector_store = vector_store
        self.embedder = embedder
        self.llm_client = llm_client
        self.neighbor_window = neighbor_window

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

        # Fetch neighboring chunks for contextual retrieval
        if self.neighbor_window > 0:
            chunks_with_neighbors = await self.vector_store.get_neighbor_chunks(
                chunks=chunks,
                collection_id=request.session_id,
                window=self.neighbor_window,
            )
        else:
            chunks_with_neighbors = chunks

        # Build context from chunks using parent content for hierarchical chunking
        # Use parent_content if available (hierarchical chunking), otherwise use content (backward compat)
        # Group chunks by book to maintain coherent context
        context = []
        current_book_id = None
        book_chunks = []

        for chunk in chunks_with_neighbors:
            if current_book_id != chunk.book_id:
                # New book - add previous book's context if exists
                if book_chunks:
                    combined = "\n\n".join(book_chunks)
                    context.append(combined)
                    book_chunks = []
                current_book_id = chunk.book_id

            # Add chunk content (prefer parent_content for richer context)
            chunk_text = chunk.parent_content if chunk.parent_content else chunk.content
            book_chunks.append(chunk_text)

        # Don't forget the last book
        if book_chunks:
            combined = "\n\n".join(book_chunks)
            context.append(combined)

        # Generate answer with conversation history
        answer = await self.llm_client.generate(
            prompt=request.query,
            context=context,
            conversation_history=request.conversation_history,
            model=request.model,
        )

        elapsed_ms = (time.perf_counter() - start_time) * 1000

        return QueryResponse(
            answer=answer,
            sources=chunks,
            latency_ms=elapsed_ms,
        )
