"""Query service for RAG-based question answering."""

import time

from src.domain.entities import Chunk, QueryRequest, QueryResponse
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

        # Calculate Top K based on percentage if provided
        if request.retrieval_percentage is not None:
            collection_size = await self.vector_store.get_collection_size(request.session_id)
            if collection_size == 0:
                top_k = 5  # Default if no collection
            else:
                # Calculate percentage-based Top K with min of 5 and max of 100
                calculated_top_k = int(collection_size * (request.retrieval_percentage / 100))
                top_k = max(5, min(100, calculated_top_k))
        else:
            top_k = request.top_k

        # Embed the query
        query_embedding = self.embedder.embed_query(request.query)

        # Retrieve relevant chunks
        chunks = await self.vector_store.search(
            query_embedding=query_embedding,
            collection_id=request.session_id,
            top_k=top_k,
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

        # Build enhanced chunks with parent content for hierarchical chunking
        # Replace chunk content with parent_content for richer context while preserving metadata
        enhanced_chunks = []
        for chunk in chunks_with_neighbors:
            # Create a new chunk with parent content but same metadata
            enhanced_chunk = Chunk(
                id=chunk.id,
                book_id=chunk.book_id,
                content=chunk.parent_content if chunk.parent_content else chunk.content,
                page_number=chunk.page_number,
                chapter=chunk.chapter,
                embedding=chunk.embedding,
                has_code=chunk.has_code,
                code_language=chunk.code_language,
                sequence_number=chunk.sequence_number,
                parent_chunk_id=chunk.parent_chunk_id,
                parent_content=chunk.parent_content,
            )
            enhanced_chunks.append(enhanced_chunk)

        # Generate answer with conversation history
        # Pass Chunk objects directly to preserve metadata for source attribution
        answer = await self.llm_client.generate(
            prompt=request.query,
            context=enhanced_chunks,
            conversation_history=request.conversation_history,
            model=request.model,
        )

        elapsed_ms = (time.perf_counter() - start_time) * 1000

        return QueryResponse(
            answer=answer,
            sources=chunks,
            latency_ms=elapsed_ms,
        )
