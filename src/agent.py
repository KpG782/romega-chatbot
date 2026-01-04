"""
Google ADK Agent for Romega Solutions
Integrates RAG pipeline with Google ADK for intelligent responses
"""

import os
from dotenv import load_dotenv
from rag_pipeline import RomegaRAGPipeline
from google import genai
from google.genai import types

class RomegaChatbotAgent:
    def __init__(self):
        """Initialize the Romega chatbot with RAG capabilities"""
        
        # Load environment variables
        load_dotenv()
        
        # Load API key from environment
        self.api_key = os.getenv('GOOGLE_API_KEY')
        if not self.api_key:
            raise ValueError("GOOGLE_API_KEY not found in environment variables. Please check your .env file")
        
        # Configure Google AI client
        self.client = genai.Client(api_key=self.api_key)
        
        # Initialize RAG pipeline
        print("🔧 Initializing RAG pipeline...")
        self.rag = RomegaRAGPipeline()
        self.rag.setup_pipeline()
        
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
        
        print("✅ Romega Chatbot Agent ready!")
    
    def query_with_rag(self, user_message: str) -> str:
        """
        Process a user query using RAG pipeline
        1. Retrieve relevant context from knowledge base
        2. Generate response using Gemini with context
        """
        
        # Step 1: Retrieve relevant context
        print(f"\n💬 User: {user_message}")
        relevant_chunks = self.rag.retrieve(user_message, top_k=3)
        
        # Step 2: Prepare context for the agent
        context = "\n\n".join([
            f"[Context {i+1}]: {chunk['content']}" 
            for i, chunk in enumerate(relevant_chunks)
        ])
        
        # Step 3: Create enhanced prompt with context
        enhanced_prompt = f"""
Context from Romega Solutions knowledge base:
{context}

User question: {user_message}

Please answer the user's question using the provided context. If the context doesn't contain enough information, acknowledge this and suggest contacting Romega Solutions directly.
"""
        
        # Step 4: Get response from Gemini
        print("🤖 Agent: Generating response...")
        
        try:
            # Combine system instruction with enhanced prompt
            full_prompt = f"""{self.system_instruction}

{enhanced_prompt}"""
            
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=full_prompt
            )
            return response.text
        except Exception as e:
            return f"Error generating response: {str(e)}"
    
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