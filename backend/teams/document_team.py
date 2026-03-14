# backend/teams/document_team.py
from unittest import result

import autogen
from typing import Dict, Any, List
from backend.agents.document.qa_agent import create_qa_agent
from backend.agents.document.insight_extractor import create_insight_extractor
from backend.tools.rag.pdf_parser import process_pdf, parse_pdf, extract_text_from_pdf
from backend.tools.rag.document_chunker import chunk_document
from backend.tools.rag.embedding_generator import generate_embeddings
from backend.database.vector_store import vector_store
from backend.utils.logger import get_logger

logger = get_logger(__name__)

def create_document_team():
    """Team for PDF upload, indexing, and Q&A."""
    qa_agent = create_qa_agent()
    insight_agent = create_insight_extractor()
    
    user_proxy = autogen.UserProxyAgent(
        name="UserProxy",
        human_input_mode="NEVER",
        max_consecutive_auto_reply=5,
        code_execution_config=False,
    )
    
    def process_document(file_path: str) -> Dict[str, Any]:
        """Upload, parse, chunk, embed, and index a PDF document."""
        logger.info(f"Processing document: {file_path}")
        
        try:
            # Step 1: Parse PDF (using combined tool)
            result = parse_pdf(file_path)
            if not result.get("success"):
                return {"status": "error", "message": result.get("error", "Unknown error")}
            
            # Step 2: Chunk the text
            chunks = []

            for page_data in result["pages"]:
                page_chunks = chunk_document(
                    page_data["text"],
                    page=page_data["page"]
                )
                chunks.extend(page_chunks)
            # Step 3: Generate embeddings
            texts = [c["text"] for c in chunks]
            embeddings = generate_embeddings(texts)
            
            if not embeddings:
                return {"status": "error", "message": "Failed to generate embeddings"}
            
            # Step 4: Store in vector DB
            vector_store.create_collection()
            vector_store.add_documents(chunks, embeddings, result["metadata"])
            
            logger.info(f"✓ Indexed {len(chunks)} chunks from {result['metadata']['pages']} pages")
            
            return {
                "status": "complete",
                "pages": result["metadata"]["pages"],
                "chunks": len(chunks),
                "message": f"Successfully indexed {len(chunks)} chunks from {result['metadata']['pages']} pages"
            }
            
        except Exception as e:
            logger.error(f"Document processing failed: {e}")
            return {"status": "error", "message": str(e)}
    
    def query_document(question: str, limit: int = 5) -> Dict[str, Any]:
        """Ask questions about uploaded documents using RAG."""
        logger.info(f"Querying documents: {question}")
        
        try:
            # Step 1: Get embedding for query
            query_embedding = generate_embeddings([question])[0]
            
            # Step 2: Search vector store
            results = vector_store.search(query_embedding, limit=limit)
            
            if not results:
                return {
                    "status": "complete",
                    "answer": "No relevant documents found for this query.",
                    "sources": []
                }
            
            # Step 3: Build context with citations
            context = "\n\n".join([
                f"[Page {r['page']}] {r['text'][:500]}..."  # Truncate for context window
                for r in results
            ])
            
            # Step 4: Generate answer using QA agent
            qa_agent.initiate_chat(
                user_proxy,
                message=f"""Answer this question using ONLY the provided context.

Question: {question}

Context (from uploaded documents):
<context>
{context}
</context>

Instructions:
1. Answer based ONLY on the context above
2. Cite page numbers like [p.5] when referencing specific info
3. If the answer isn't in the context, say "I couldn't find this in the uploaded documents"
4. Keep your answer clear and concise""",
                max_turns=3
            )
            
            answer = qa_agent.last_message().get("content", "No answer generated")
            
            logger.info(f"✓ Generated answer ({len(answer)} chars)")
            
            return {
                "status": "complete",
                "answer": answer,
                "sources": [
                    {"page": r["page"], "score": round(r["score"], 3), "snippet": r["text"][:200]}
                    for r in results
                ]
            }
            
        except Exception as e:
            logger.error(f"Document query failed: {e}")
            return {"status": "error", "message": str(e)}
    
    def extract_insights(document_path: str) -> Dict[str, Any]:
        """Extract key insights, claims, and findings from a document."""
        logger.info(f"Extracting insights from: {document_path}")
        
        try:
            # Parse document
            result = parse_pdf(document_path)
            if not result.get("success"):
                return {"status": "error", "message": result.get("error")}
            
            # Use insight extractor agent
            insight_agent.initiate_chat(
                user_proxy,
                message=f"""Extract key insights from this document:
Document Metadata:
- Title: {result['metadata'].get('title', 'N/A')}
- Pages: {result['metadata'].get('pages', 'N/A')}
Document Text (first 3000 chars):
{result['text'][:3000]}

Extract:
1. 🔑 Key Claims (3-5 bullet points)
2. 📊 Data/Statistics mentioned
3. ⚠️ Limitations or caveats
4. 💡 Actionable takeaways

Format as markdown.""",
                max_turns=3
            )
            
            insights = insight_agent.last_message().get("content", "No insights extracted")
            
            return {
                "status": "complete",
                "insights": insights,
                "metadata": result["metadata"]
            }
            
        except Exception as e:
            logger.error(f"Insight extraction failed: {e}")
            return {"status": "error", "message": str(e)}
    
    return {
        "user_proxy": user_proxy,
        "agents": [qa_agent, insight_agent],  
        "process_document": process_document,
        "query_document": query_document,
        "extract_insights": extract_insights
    }