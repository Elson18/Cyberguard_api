import sys
import os


sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


from flask import Flask, request, jsonify
from config import Config
from vector_stores.chromadb_store import LocalChromaDb
from chat_response import generate_response_mistral

text_file = ""

chromadb_initalization_azure = LocalChromaDb()

config = Config()
app = Flask(__name__)


@app.route("/azure/chatbot/store/chromadb", methods=["POST"])
def store_document_azure():

    try:
        file_path = config.FILE_PATH
        message = chromadb_initalization_azure.store_the_chunk(file_path)
        return jsonify ({"message":message})
    
    except Exception as e:
        return jsonify ({"Error": str(e)})

@app.route("/azure/chatbot/response", methods=["POST"])
def chat_response_azure():

    try:
        data = request.json
        query = data.get("query" , None)

        response = chromadb_initalization_azure.response_query(query,k=3)

        return jsonify ({"ChatBot": response})

    except Exception as e:
        return jsonify ({"Error": str(e)})
    
@app.route("/chatbot/llm/response/chromadb", methods = ["POST"])
def chatbot_llm_response():

    try:
        data = request.json
        query = data.get("query", None)

        generate_llm_response = generate_response_mistral(query)

        return jsonify ({"ChatBot": generate_llm_response})
    except Exception as e:
        return jsonify ({"Error": str(e)})


if __name__ == "__main__":

    app.run(debug=True)
