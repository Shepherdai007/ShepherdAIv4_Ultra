import os
import json
from flask import Flask, request, jsonify, send_from_directory
from openai import OpenAI
from tavily import TavilyClient
from dotenv import load_dotenv

# Load keys from .env
load_dotenv()

app = Flask(__name__, static_folder='static')

# Initialize Clients
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
tavily = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))

def web_search(query):
    """Function to perform a real-time web search via Tavily."""
    try:
        # We search for the top 5 most relevant results
        search_result = tavily.search(query=query, search_depth="advanced", max_results=5)
        return search_result['results']
    except Exception as e:
        print(f"Tavily Error: {e}")
        return []

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/chat', methods=['POST'])
def chat():
    try:
        user_message = request.form.get('message')
        selected_model = request.form.get('model', 'gpt-4o')
        
        # Mapping models from your UI
        model_mapping = {
            "gpt-3": "gpt-3.5-turbo",
            "gpt-4": "gpt-4o",
            "gpt-5": "o1-preview" # Using O1-preview for the 'GPT-5' experience
        }
        target_model = model_mapping.get(selected_model, "gpt-4o")

        # 1. Check if the user is asking for something that needs a web search
        # (This is a simple logic, we can make it more 'Ultra' with function calling later)
        search_keywords = ["search", "who is", "latest", "news", "what happened", "weather", "price"]
        needs_search = any(word in user_message.lower() for word in search_keywords)

        context = ""
        if needs_search:
            print(f"Searching web for: {user_message}")
            results = web_search(user_message)
            context = "\n\nWeb Search Results:\n" + json.dumps(results)

        # 2. Call OpenAI with the search context included
        response = client.chat.completions.create(
            model=target_model,
            messages=[
                {
                    "role": "system", 
                    "content": f"You are ShepherdAI v4 Ultra. You have access to real-time web data via Tavily. {context}"
                },
                {"role": "user", "content": user_message}
            ],
            temperature=0.7
        )

        ai_reply = response.choices[0].message.content

        return jsonify({
            "status": "success",
            "reply": ai_reply,
            "model_used": target_model
        })

    except Exception as e:
        print(f"Server Error: {e}")
        return jsonify({"status": "error", "reply": "Connection lost, King. Check your API keys."}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)