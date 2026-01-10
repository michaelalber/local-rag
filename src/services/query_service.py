"""Query service for RAG-based question answering."""

from __future__ import annotations

import logging
import time
from typing import TYPE_CHECKING

from src.models import Chunk, QueryRequest, QueryResponse, QuerySource
from src.vectorstore import ChromaVectorStore
from src.llm import OllamaLLMClient

if TYPE_CHECKING:
    from src.mcp import AegisMCPClient

logger = logging.getLogger(__name__)


class QueryService:
    """Handles RAG queries against loaded books and/or compliance data."""

    def __init__(
        self,
        vector_store: ChromaVectorStore,
        embedder,  # OllamaEmbedder or SentenceTransformerEmbedder
        llm_client: OllamaLLMClient,
        neighbor_window: int = 1,
        aegis_client: AegisMCPClient | None = None,
    ):
        """
        Args:
            vector_store: Vector storage for retrieval.
            embedder: Embedding service for query.
            llm_client: LLM for generation.
            neighbor_window: Number of neighboring chunks to include (±N).
            aegis_client: Optional Aegis MCP client for compliance queries.
        """
        self.vector_store = vector_store
        self.embedder = embedder
        self.llm_client = llm_client
        self.neighbor_window = neighbor_window
        self.aegis_client = aegis_client

    async def query(self, request: QueryRequest) -> QueryResponse:
        """
        Process a RAG query with source routing.

        Routes queries to books, compliance data, or both based on request.source.

        Args:
            request: Query request with question, session, and source selection.

        Returns:
            Response with answer and sources.
        """
        start_time = time.perf_counter()

        # Collect context from selected sources
        book_chunks: list[Chunk] = []
        compliance_context: list[str] = []

        # Query books if requested
        if request.source in (QuerySource.BOOKS, QuerySource.BOTH):
            book_chunks = await self._retrieve_book_chunks(request)

        # Query compliance if requested
        if request.source in (QuerySource.COMPLIANCE, QuerySource.BOTH):
            compliance_context = await self._retrieve_compliance_context(request)

        # Build combined context for LLM
        enhanced_chunks = self._build_enhanced_chunks(book_chunks)
        combined_context = self._combine_context(enhanced_chunks, compliance_context)

        # Generate answer with conversation history
        answer = await self.llm_client.generate(
            prompt=request.query,
            context=combined_context,
            conversation_history=request.conversation_history,
            model=request.model,
        )

        elapsed_ms = (time.perf_counter() - start_time) * 1000

        return QueryResponse(
            answer=answer,
            sources=book_chunks,
            latency_ms=elapsed_ms,
        )

    async def _retrieve_book_chunks(self, request: QueryRequest) -> list[Chunk]:
        """Retrieve relevant chunks from book vector store."""
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
            chunks = await self.vector_store.get_neighbor_chunks(
                chunks=chunks,
                collection_id=request.session_id,
                window=self.neighbor_window,
            )

        return chunks

    async def _retrieve_compliance_context(self, request: QueryRequest) -> list[str]:
        """Retrieve compliance context from Aegis MCP.

        Returns formatted compliance results as context strings.
        Fails gracefully if Aegis is not configured or unavailable.
        """
        if not self.aegis_client:
            logger.debug("Compliance requested but Aegis client not configured")
            return []

        try:
            results = await self.aegis_client.search_compliance(
                query=request.query,
                top_k=request.top_k,
            )

            # Format compliance results as context strings
            context_strings = []
            for result in results:
                context_str = (
                    f"[Compliance Control: {result.control_id}]\n"
                    f"Framework: {result.framework}\n"
                    f"Title: {result.title}\n"
                    f"Description: {result.description}\n"
                )
                context_strings.append(context_str)

            logger.debug("Retrieved %d compliance results", len(context_strings))
            return context_strings

        except Exception as e:
            logger.warning("Failed to retrieve compliance context: %s", e)
            return []

    def _build_enhanced_chunks(self, chunks: list[Chunk]) -> list[Chunk]:
        """Build enhanced chunks with parent content for hierarchical chunking."""
        enhanced_chunks = []
        for chunk in chunks:
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
        return enhanced_chunks

    def _combine_context(
        self, book_chunks: list[Chunk], compliance_context: list[str]
    ) -> list[Chunk] | list[str]:
        """Combine book chunks and compliance context.

        If only books: return Chunk objects (preserves metadata for source attribution)
        If only compliance: return formatted strings
        If both: return strings (compliance first, then book content)
        """
        if not compliance_context:
            return book_chunks

        if not book_chunks:
            return compliance_context

        # Combine both: convert chunks to strings and prepend compliance
        combined = compliance_context.copy()
        for chunk in book_chunks:
            source_info = []
            if chunk.chapter:
                source_info.append(f"Chapter: {chunk.chapter}")
            if chunk.page_number:
                source_info.append(f"Page {chunk.page_number}")
            source_suffix = f" [{', '.join(source_info)}]" if source_info else ""
            combined.append(f"{chunk.content}{source_suffix}")

        return combined
