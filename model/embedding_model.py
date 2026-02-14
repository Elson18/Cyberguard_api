from langchain_community.embeddings import HuggingFaceEmbeddings

class LocalEmbedder:
    def __init__(self):
        self.embeddings_client = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        )

    def embed_documents(self, texts):
        return self.embeddings_client.embed_documents(texts)

    def embed_query(self, query):
        return self.embeddings_client.embed_query(query)