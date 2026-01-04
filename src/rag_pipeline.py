"""
RAG Pipeline for Romega Solutions Chatbot
Handles: Extract -> Chunk -> Embed -> Vectorize -> Retrieve
"""

import json
import logging
import os
from typing import List, Dict, Any
from sentence_transformers import SentenceTransformer
import chromadb
from chromadb.config import Settings

# Configure logging
logger = logging.getLogger(__name__)

class RomegaRAGPipeline:
    def __init__(self, kb_path: str = None, persist_directory: str = "./chroma_db"):
        """Initialize the RAG pipeline with knowledge base path and persistence"""
        logger.info("Initializing RAG Pipeline...")
        
        if kb_path is None:
            # Try multiple paths to find the knowledge base
            possible_paths = [
                "knowledge_base/romega_kb.json",  # Docker/production
                "../knowledge_base/romega_kb.json",  # Local development
                os.path.join(os.path.dirname(os.path.dirname(__file__)), "knowledge_base", "romega_kb.json")
            ]
            for path in possible_paths:
                if os.path.exists(path):
                    kb_path = path
                    logger.info("Found knowledge base at: %s", kb_path)
                    break
            if kb_path is None:
                logger.error("Knowledge base not found in any expected location")
                raise FileNotFoundError("Could not find romega_kb.json in any expected location")
        
        self.kb_path = kb_path
        self.persist_directory = persist_directory
        
        # Create persist directory if it doesn't exist
        os.makedirs(self.persist_directory, exist_ok=True)
        logger.info("Using persistent storage at: %s", self.persist_directory)
        
        # Initialize embedding model
        logger.info("Loading embedding model: all-MiniLM-L6-v2")
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        
        # Initialize ChromaDB with persistence
        self.chroma_client = chromadb.PersistentClient(
            path=self.persist_directory,
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        logger.info("ChromaDB initialized with persistence")
        
        # Create or get collection
        self.collection = self.chroma_client.get_or_create_collection(
            name="romega_knowledge_base",
            metadata={"description": "Romega Solutions company knowledge"}
        )
        logger.info("Collection loaded: %d existing vectors", self.collection.count())
        
        self.knowledge_base = None
        self.chunks = []
    
    def load_knowledge_base(self) -> Dict[str, Any]:
        """Step 1: EXTRACT - Load the JSON knowledge base"""
        logger.info("📥 Loading knowledge base...")
        try:
            with open(self.kb_path, 'r', encoding='utf-8') as f:
                self.knowledge_base = json.load(f)
            logger.info(f"✅ Loaded {len(self.knowledge_base)} main sections")
            return self.knowledge_base
        except Exception as e:
            logger.error(f"Failed to load knowledge base: {e}", exc_info=True)
            raise
    
    def chunk_data(self) -> List[Dict[str, Any]]:
        """
        Step 2: CHUNK - Break knowledge base into semantic chunks
        This is the HARDEST part according to your friend Jam
        """
        print("✂️  Chunking data...")
        chunks = []
        
        # Chunk company info
        if 'company' in self.knowledge_base:
            company = self.knowledge_base['company']
            chunks.append({
                'id': 'company_overview',
                'category': 'company',
                'content': f"Company: {company['name']}. {company['description']}. Mission: {company['mission']}. Vision: {company['vision']}.",
                'metadata': {'type': 'overview', 'section': 'company'}
            })
        
        # Chunk services (CRITICAL - this is your main content)
        if 'services' in self.knowledge_base:
            for service_key, service in self.knowledge_base['services'].items():
                # Main service description
                chunks.append({
                    'id': f'service_{service_key}_main',
                    'category': 'services',
                    'content': f"{service['name']}: {service['description']}. Details: {' '.join(service.get('details', []))}",
                    'metadata': {'type': 'service', 'service_name': service_key}
                })
                
                # Service process/benefits as separate chunks
                if 'process' in service:
                    chunks.append({
                        'id': f'service_{service_key}_process',
                        'category': 'services',
                        'content': f"{service['name']} process: {' -> '.join(service['process'])}",
                        'metadata': {'type': 'process', 'service_name': service_key}
                    })
        
        # Chunk pricing info
        if 'pricing' in self.knowledge_base:
            pricing = self.knowledge_base['pricing']
            for pricing_type, info in pricing.items():
                content = f"Pricing - {pricing_type}: "
                if isinstance(info, dict):
                    content += ". ".join([f"{k}: {v}" for k, v in info.items() if isinstance(v, str)])
                chunks.append({
                    'id': f'pricing_{pricing_type}',
                    'category': 'pricing',
                    'content': content,
                    'metadata': {'type': 'pricing', 'pricing_type': pricing_type}
                })
        
        # Chunk FAQ
        if 'faq' in self.knowledge_base:
            for idx, qa in enumerate(self.knowledge_base['faq']['common_questions']):
                chunks.append({
                    'id': f'faq_{idx}',
                    'category': 'faq',
                    'content': f"Q: {qa['question']} A: {qa['answer']}",
                    'metadata': {'type': 'faq', 'category': qa.get('category', 'general')}
                })
        
        # Chunk team info
        if 'team' in self.knowledge_base:
            team = self.knowledge_base['team']
            if 'leadership' in team:
                for role, person in team['leadership'].items():
                    chunks.append({
                        'id': f'team_{role}',
                        'category': 'team',
                        'content': f"{person['name']}, {person['title']}: {person.get('background', '')}",
                        'metadata': {'type': 'leadership'}
                    })
        
        # Chunk contact info
        if 'contact' in self.knowledge_base:
            contact = self.knowledge_base['contact']
            contact_info = []
            for section, details in contact.items():
                if isinstance(details, dict):
                    contact_info.extend([f"{k}: {v}" for k, v in details.items() if isinstance(v, str)])
            chunks.append({
                'id': 'contact_info',
                'category': 'contact',
                'content': f"Contact information: {'. '.join(contact_info)}",
                'metadata': {'type': 'contact'}
            })
        
        self.chunks = chunks
        print(f"✅ Created {len(chunks)} chunks")
        return chunks
    
    def embed_and_vectorize(self, force_rebuild: bool = False):
        """
        Step 3 & 4: EMBED and VECTORIZE
        Convert chunks to embeddings and store in vector database
        """
        # Check if collection already has vectors (from persistence)
        existing_count = self.collection.count()
        if existing_count > 0 and not force_rebuild:
            logger.info(f"📦 Using {existing_count} existing vectors from persistent storage")
            return
        
        logger.info("🧠 Embedding and vectorizing chunks...")
        
        if not self.chunks:
            logger.error("No chunks found to embed")
            raise ValueError("No chunks found. Run chunk_data() first.")
        
        try:
            # Extract content for embedding
            texts = [chunk['content'] for chunk in self.chunks]
            
            # Generate embeddings
            logger.info(f"Generating embeddings for {len(texts)} chunks...")
            embeddings = self.embedding_model.encode(texts, show_progress_bar=True)
            
            # Prepare data for ChromaDB
            ids = [chunk['id'] for chunk in self.chunks]
            metadatas = [chunk['metadata'] for chunk in self.chunks]
            
            # Clear existing if force rebuild
            if force_rebuild and existing_count > 0:
                logger.warning(f"Force rebuild: Clearing {existing_count} existing vectors")
                # Delete collection and recreate
                self.chroma_client.delete_collection(name="romega_knowledge_base")
                self.collection = self.chroma_client.create_collection(
                    name="romega_knowledge_base",
                    metadata={"description": "Romega Solutions company knowledge"}
                )
            
            # Store in vector database
            self.collection.add(
                embeddings=embeddings.tolist(),
                documents=texts,
                metadatas=metadatas,
                ids=ids
            )
            
            logger.info(f"✅ Stored {len(self.chunks)} embeddings in vector database")
        except Exception as e:
            logger.error(f"Failed to embed and vectorize: {e}", exc_info=True)
            raise
    
    def retrieve(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """
        Step 5: RETRIEVE - Find most relevant chunks for a query
        """
        logger.debug(f"🔍 Retrieving top {top_k} results for: '{query}'")
        
        try:
            # Embed the query
            query_embedding = self.embedding_model.encode([query])[0]
            
            # Search vector database
            results = self.collection.query(
                query_embeddings=[query_embedding.tolist()],
                n_results=top_k
            )
            
            # Format results
            retrieved_chunks = []
            for i in range(len(results['ids'][0])):
                retrieved_chunks.append({
                    'id': results['ids'][0][i],
                    'content': results['documents'][0][i],
                    'metadata': results['metadatas'][0][i],
                    'distance': results['distances'][0][i] if 'distances' in results else None
                })
            
            logger.debug(f"Retrieved {len(retrieved_chunks)} relevant chunks")
            return retrieved_chunks
        except Exception as e:
            logger.error(f"Failed to retrieve results for query '{query}': {e}", exc_info=True)
            raise
    
    def setup_pipeline(self, force_rebuild: bool = False):
        """Run the complete pipeline: Extract -> Chunk -> Embed -> Vectorize"""
        logger.info("\n🚀 Starting RAG Pipeline Setup...\n")
        
        # Check if we already have vectors from persistence
        existing_count = self.collection.count()
        if existing_count > 0 and not force_rebuild:
            logger.info(f"✅ Using {existing_count} existing vectors from persistent storage")
            logger.info("\n✅ RAG Pipeline ready!\n")
            return
        
        try:
            # Extract
            self.load_knowledge_base()
            
            # Chunk
            self.chunk_data()
            
            # Embed & Vectorize
            self.embed_and_vectorize(force_rebuild=force_rebuild)
            
            logger.info("\n✅ RAG Pipeline setup complete!\n")
        except Exception as e:
            logger.error(f"Pipeline setup failed: {e}", exc_info=True)
            raise
    
    def test_retrieval(self):
        """Test the retrieval with sample queries"""
        test_queries = [
            "What services does Romega offer?",
            "How much does it cost?",
            "How fast can you fill positions?",
            "Who is the founder?",
            "How can I contact Romega?"
        ]
        
        print("\n🧪 Testing retrieval with sample queries:\n")
        for query in test_queries:
            print(f"\n❓ Query: {query}")
            results = self.retrieve(query, top_k=2)
            for idx, result in enumerate(results, 1):
                print(f"  {idx}. {result['content'][:100]}...")


# Example usage
if __name__ == "__main__":
    # Initialize pipeline
    rag = RomegaRAGPipeline()
    
    # Setup the full pipeline
    rag.setup_pipeline()
    
    # Test retrieval
    rag.test_retrieval()