"""
Romega Solutions Chatbot Agent
Integrates RAG pipeline with Google Gemini for intelligent responses
"""

import os
import logging
import time
from typing import Optional
from dotenv import load_dotenv
from rag_pipeline import RomegaRAGPipeline
from google import genai
from google.genai import types

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class RomegaChatbotAgent:
    def __init__(self, max_retries: int = 3, retry_delay: float = 1.0):
        """Initialize the Romega chatbot with RAG capabilities"""
        logger.info("Initializing Romega Chatbot Agent...")
        
        # Load environment variables
        load_dotenv()
        
        # Load API key from environment
        self.api_key = os.getenv('GOOGLE_API_KEY')
        if not self.api_key:
            logger.error("GOOGLE_API_KEY not found in environment variables")
            raise ValueError("GOOGLE_API_KEY not found in environment variables. Please check your .env file")
        
        # Configure retry parameters
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        
        try:
            # Configure Google AI client
            self.client = genai.Client(api_key=self.api_key)
            logger.info("Google AI client configured successfully")
        except Exception as e:
            logger.error(f"Failed to configure Google AI client: {e}", exc_info=True)
            raise
        
        # Initialize RAG pipeline
        try:
            logger.info("🔧 Initializing RAG pipeline...")
            self.rag = RomegaRAGPipeline()
            self.rag.setup_pipeline()
            logger.info("RAG pipeline initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize RAG pipeline: {e}", exc_info=True)
            raise
        
        # System instruction for the agent
        self.system_instruction = """
You are a helpful AI assistant for Romega Solutions, a US-based holding company specializing in recruitment and business support services.

Your role is to:
1. Answer questions about Romega Solutions' services (RPO, BPO, Strategic HR, Quality Hire, etc.)
2. Provide information about pricing, timelines, and processes
3. Help schedule consultations and provide contact information
4. Maintain a professional, friendly, and helpful tone

Key facts to remember:
- Romega is founded by Robbie Galoso
- We're 60-70% faster than traditional recruitment methods
- We have 95%+ retention rates
- Our fees are 15% lower than competitors
- We specialize in Philippine-based talent leading global innovation

When you don't know something specific, be honest and encourage users to schedule a consultation or contact us directly at info@romega-solutions.com or through our website www.romega-solutions.com.

Always base your answers on the provided context from the knowledge base.
"""
        
        # Configure the model
        self.model_name = 'gemini-2.0-flash-exp'
        
        logger.info("✅ Romega Chatbot Agent ready!")
    
    def _generate_with_retry(self, prompt: str) -> Optional[str]:
        """Generate response with retry logic"""
        for attempt in range(self.max_retries):
            try:
                logger.debug(f"Attempt {attempt + 1}/{self.max_retries} to generate response")
                
                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=prompt
                )
                
                if response and response.text:
                    logger.debug("Successfully generated response")
                    return response.text
                else:
                    logger.warning(f"Empty response received on attempt {attempt + 1}")
                    
            except Exception as e:
                logger.warning(f"Attempt {attempt + 1} failed: {e}")
                
                if attempt < self.max_retries - 1:
                    # Exponential backoff
                    sleep_time = self.retry_delay * (2 ** attempt)
                    logger.info(f"Retrying in {sleep_time:.1f} seconds...")
                    time.sleep(sleep_time)
                else:
                    logger.error(f"All {self.max_retries} attempts failed", exc_info=True)
                    return None
        
        return None
    
    def query_with_rag(self, user_message: str) -> str:
        """
        Process a user query using RAG pipeline
        1. Retrieve relevant context from knowledge base
        2. Generate response using Gemini with context
        """
        logger.info(f"Processing query: {user_message[:50]}...")
        
        try:
            # Step 1: Retrieve relevant context
            logger.debug("Retrieving relevant context from knowledge base")
            relevant_chunks = self.rag.retrieve(user_message, top_k=3)
            
            if not relevant_chunks:
                logger.warning("No relevant context found")
                return "I apologize, but I couldn't find relevant information to answer your question. Please contact us at info@romega-solutions.com for assistance."
            
            # Step 2: Prepare context for the agent
            context = "\n\n".join([
                f"[Context {i+1}]: {chunk['content']}" 
                for i, chunk in enumerate(relevant_chunks)
            ])
            
            # Step 3: Create enhanced prompt with context
            enhanced_prompt = f"""{self.system_instruction}

Context from Romega Solutions knowledge base:
{context}

User question: {user_message}

Please answer the user's question using the provided context. If the context doesn't contain enough information, acknowledge this and suggest contacting Romega Solutions directly.
"""
            
            # Step 4: Get response from Gemini with retry logic
            logger.debug("Generating response with Gemini")
            response_text = self._generate_with_retry(enhanced_prompt)
            
            if response_text:
                logger.info("Successfully generated response")
                return response_text
            else:
                logger.error("Failed to generate response after all retries")
                return "I apologize, but I'm having trouble generating a response right now. Please try again in a moment or contact us at info@romega-solutions.com."
                
        except Exception as e:
            logger.error(f"Error in query_with_rag: {e}", exc_info=True)
            return "I apologize, but an error occurred while processing your question. Please contact us at info@romega-solutions.com for assistance."
    
    def run_interactive(self):
        """Run the chatbot in interactive mode"""
        print("\n" + "="*60)
        print("🤖 Romega Solutions Chatbot")
        print("="*60)
        print("Type your questions or 'quit' to exit\n")
        
        while True:
            user_input = input("You: ").strip()
            
            if user_input.lower() in ['quit', 'exit', 'bye']:
                print("\n👋 Thank you for chatting with Romega Solutions!")
                break
            
            if not user_input:
                continue
            
            # Get response using RAG
            response = self.query_with_rag(user_input)
            print(f"\n🤖 Assistant: {response}\n")
            print("-" * 60 + "\n")


def main():
    """Main entry point"""
    
    try:
        # Create the chatbot agent
        chatbot = RomegaChatbotAgent()
        
        # Run in interactive mode
        chatbot.run_interactive()
        
    except ValueError as e:
        print(f"\n❌ Configuration Error: {e}")
        print("\nMake sure you have:")
        print("1. Created a .env file in the project root")
        print("2. Added your Google API key: GOOGLE_API_KEY=your_key_here")
        print("3. Get your key from: https://aistudio.google.com/app/apikey")
    except FileNotFoundError as e:
        print(f"\n❌ File Error: {e}")
        print("\nMake sure you have:")
        print("1. Created the knowledge_base folder")
        print("2. Saved romega_kb.json in knowledge_base/")
    except Exception as e:
        print(f"\n❌ Unexpected Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()