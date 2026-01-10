"""Query service for RAG-based question answering."""

from __future__ import annotations

import logging
import time
from typing import TYPE_CHECKING

from src.llm import OllamaLLMClient
from src.models import Chunk, QueryRequest, QueryResponse, QuerySource
from src.vectorstore import ChromaVectorStore

if TYPE_CHECKING:
    from src.mcp import MCPManager

logger = logging.getLogger(__name__)


class QueryService:
    """Handles RAG queries against loaded books and/or external MCP sources."""

    def __init__(
        self,
        vector_store: ChromaVectorStore,
        embedder,  # OllamaEmbedder or SentenceTransformerEmbedder
        llm_client: OllamaLLMClient,
        neighbor_window: int = 1,
        mcp_manager: MCPManager | None = None,
    ):
        """
        Args:
            vector_store: Vector storage for retrieval.
            embedder: Embedding service for query.
            llm_client: LLM for generation.
            neighbor_window: Number of neighboring chunks to include (±N).
            mcp_manager: Optional MCP manager for external knowledge sources.
        """
        self.vector_store = vector_store
        self.embedder = embedder
        self.llm_client = llm_client
        self.neighbor_window = neighbor_window
        self.mcp_manager = mcp_manager

    async def query(self, request: QueryRequest) -> QueryResponse:
        """
        Process a RAG query with source routing.

        Routes queries to books, MCP sources, or all based on request.source.

        Args:
            request: Query request with question, session, and source selection.

        Returns:
            Response with answer and sources.
        """
        start_time = time.perf_counter()

        # Collect context from selected sources
        book_chunks: list[Chunk] = []
        mcp_context: list[str] = []

        # Determine which sources to query
        book_sources = (QuerySource.BOOKS, QuerySource.BOTH, QuerySource.ALL)
        compliance_sources = (QuerySource.COMPLIANCE, QuerySource.BOTH, QuerySource.ALL)
        query_books = request.source in book_sources
        query_compliance = request.source in compliance_sources
        query_mslearn = request.source in (QuerySource.MSLEARN, QuerySource.ALL)

        # Query books if requested
        if query_books:
            book_chunks = await self._retrieve_book_chunks(request)

        # Query MCP sources if requested
        if query_compliance:
            compliance_ctx = await self._retrieve_mcp_context("compliance", request)
            mcp_context.extend(compliance_ctx)

        if query_mslearn:
            mslearn_ctx = await self._retrieve_mcp_context("mslearn", request)
            mcp_context.extend(mslearn_ctx)

        # Build combined context for LLM
        enhanced_chunks = self._build_enhanced_chunks(book_chunks)
        combined_context = self._combine_context(enhanced_chunks, mcp_context)

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

    async def _retrieve_mcp_context(
        self, source: str, request: QueryRequest
    ) -> list[str]:
        """Retrieve context from an MCP source.

        Args:
            source: MCP source name (e.g., "compliance", "mslearn")
            request: Query request with query and top_k

        Returns:
            List of formatted context strings from the MCP source.
            Fails gracefully if the source is not configured or unavailable.
        """
        if not self.mcp_manager:
            logger.debug("MCP source '%s' requested but MCP manager not configured", source)
            return []

        try:
            context = await self.mcp_manager.search_context(
                source=source,
                query=request.query,
                top_k=request.top_k,
            )
            logger.debug("Retrieved %d results from MCP source '%s'", len(context), source)
            return context

        except Exception as e:
            logger.warning("Failed to retrieve context from MCP source '%s': %s", source, e)
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
