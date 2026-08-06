import os
from typing import List, Dict

_chroma_client = None

# File-based ChromaDB for local dev. Swap to InsForge pgvector for deploy.
# Dependencies (chromadb + sentence-transformers) are OPTIONAL and commented
# out in requirements.txt. Module-level imports are lazy below to avoid
# crashing the server when these are not installed.


def get_or_create_collection(meeting_id: str):
    global _chroma_client
    if _chroma_client is None:
        try:
            import chromadb
            from chromadb.utils import embedding_functions
            _chroma_client = chromadb.PersistentClient(path="data/chroma")
            get_or_create_collection._ef = embedding_functions.SentenceTransformerEmbeddingFunction(  # type: ignore[attr-defined]
                model_name="all-MiniLM-L6-v2"
            )
        except Exception as exc:
            raise RuntimeError(
                "RAG feature requires chromadb + sentence-transformers. "
                "These are OPTIONAL and deferred per README; uncomment them in "
                "requirements.txt then re-install. For now, ask questions using "
                "the inline Groq path (Chainlit: any sentence ending with '?'). "
                f"Underlying error: {exc}"
            ) from exc
    return _chroma_client.get_or_create_collection(
        name=f"meeting_{meeting_id}",
        embedding_function=get_or_create_collection._ef,  # type: ignore[attr-defined]
    )


def index_transcript(meeting_id: str, transcript: str, chunk_size: int = 200) -> None:
    """Split transcript into chunks and store embeddings."""
    collection = get_or_create_collection(meeting_id)

    # Simple chunking by sentences
    sentences = [s.strip() for s in transcript.split(".") if len(s.strip()) > 10]
    chunks = []
    current = ""
    for s in sentences:
        if len(current) + len(s) < chunk_size:
            current += s + ". "
        else:
            chunks.append(current.strip())
            current = s + ". "
    if current:
        chunks.append(current.strip())

    if not chunks:
        chunks = [transcript[:500]]

    collection.add(
        documents=chunks,
        ids=[f"{meeting_id}_chunk_{i}" for i in range(len(chunks))],
        metadatas=[{"source": "transcript", "index": i} for i in range(len(chunks))]
    )


def query_transcript(meeting_id: str, question: str, n_results: int = 3) -> List[Dict]:
    """Retrieve relevant chunks and format for LLM."""
    collection = get_or_create_collection(meeting_id)
    results = collection.query(query_texts=[question], n_results=n_results)

    docs = results.get("documents", [[]])[0]
    metas = results.get("metadatas", [[]])[0]

    context_blocks = []
    for doc, meta in zip(docs, metas):
        context_blocks.append(f"[Excerpt {meta.get('index', '?')}]: {doc}")

    return context_blocks


def answer_question(meeting_id: str, question: str, groq_client) -> str:
    """RAG pipeline: retrieve chunks → Groq generates grounded answer."""
    context = query_transcript(meeting_id, question)
    if not context:
        return "No meeting context found. Upload a transcript first."

    context_str = "\n".join(context)
    prompt = f"""You are a helpful meeting assistant. Answer the user's question using ONLY the provided transcript excerpts.
If the answer is not in the excerpts, say "I don't see that in the meeting transcript."

Transcript Excerpts:
{context_str}

User Question: {question}

Answer concisely with the relevant quote:"""

    try:
        resp = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "Answer strictly from the provided context."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.1,
            max_tokens=300,
        )
        return resp.choices[0].message.content
    except Exception as e:
        return f"[Q&A error: {e}]"
