import os
from llama_index.llms.monsterapi import MonsterLLM
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, ServiceContext

os.environ["MONSTER_API_KEY"] = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ1c2VybmFtZSI6IjRhNDhhNmNmN2U5N2I3MGYyMDM4ZDI2YTZiZWU4YmM3IiwiY3JlYXRlZF9hdCI6IjIwMjQtMDItMTdUMjI6MTM6MDUuMTM5MDIzIn0.tq_fsyfO3sYaF59ITAkinFvlzeHhvgfYynWL3VAot-0"

"""##Basic Usage Pattern
Step 1: Set the model

Step 2: Initiate LLM and Embedding Model

Step 3: Load the document

Step 4: Create embedding store and create index

Step 5: LLM Output with RAG
"""
class ZephyrRAG:
    def __init__(self, model, temperature, context_window, embed_model, data_path):
        self.model = model
        self.temperature = temperature
        self.context_window = context_window
        self.embed_model = embed_model
        self.data_path = data_path
        self.llm = None
        self.service_context = None
        self.documents = None
        self.query_engine = None

    def load_model(self):
        print("Loading model")
        self.llm = MonsterLLM(model=self.model, temperature=self.temperature, context_window=self.context_window)
        self.service_context = ServiceContext.from_defaults(
            chunk_size=1024, llm=self.llm, embed_model=self.embed_model
        )

    def load_data(self):
        print("Loading data")
        self.documents = SimpleDirectoryReader(self.data_path).load_data()

    def create_index(self):
        index = VectorStoreIndex.from_documents(
            self.documents, service_context=self.service_context
        )
        self.query_engine = index.as_query_engine()

    def query(self, text):
        response = self.query_engine.query(text)
        return response

    def run(self):
        self.load_model()
        self.load_data()
        self.create_index()

# Example usage
zephyr_rag = ZephyrRAG(
    model="zephyr-7b-beta",
    temperature=0.75,
    context_window=1024,
    embed_model="local:BAAI/bge-small-en-v1.5",
    data_path="./data"
)
zephyr_rag.run()
response = zephyr_rag.query("What does malignant mean?")
print(response)
