import sys
import os
from dotenv import load_dotenv

# Ensure the root directory is on PYTHONPATH
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
load_dotenv(os.path.abspath(os.path.join(os.path.dirname(__file__), "../.env")))

from ai_agents.master_agent.router import MasterRouter

def main():
    print("==================================================")
    print("ProjectMaster Agent CLI 🟢")
    print("The agent is ready. You can provide project descriptions or scheduling tasks.")
    print("Using Moonshot-v1-8K Brain + Local FastAPI Calculus Engine")
    print("Type 'exit' or 'quit' to close.")
    print("==================================================\n")
    
    router = MasterRouter()
    chat_history = []
    
    while True:
        try:
            user_input = input("USER: ")
            if user_input.strip().lower() in ["exit", "quit", "q"]:
                break
                
            if not user_input.strip():
                continue
                
            print("\n[ProjectMaster Agent is thinking...]")
            # Pass and update the conversation history safely
            chat_history = router.process_message(user_input, chat_history)
            
            # The last message is always the AI's final response if tools responded to it
            final_response = chat_history[-1].content
            print(f"\nAGENT:\n{final_response}\n")
            print("-" * 50)
            
        except KeyboardInterrupt:
            print("\nExiting...")
            break
        except Exception as e:
            print(f"\nError: {str(e)}")

if __name__ == "__main__":
    main()
