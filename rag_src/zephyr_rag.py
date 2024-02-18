import os
from llama_index.llms.monsterapi import MonsterLLM
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, ServiceContext

os.environ[
    "MONSTER_API_KEY"
] = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ1c2VybmFtZSI6IjRhNDhhNmNmN2U5N2I3MGYyMDM4ZDI2YTZiZWU4YmM3IiwiY3JlYXRlZF9hdCI6IjIwMjQtMDItMTdUMjI6MTM6MDUuMTM5MDIzIn0.tq_fsyfO3sYaF59ITAkinFvlzeHhvgfYynWL3VAot-0"

"""##Basic Usage Pattern
Step 1: Set the model

Step 2: Initiate LLM and Embedding Model

Step 3: Load the document

Step 4: Create embedding store and create index

Step 5: LLM Output with RAG
"""


class ZephyrRAG:
    def __init__(
        self,
        model,
        temperature=0.75,
        context_window=1024,
        embed_model="local:BAAI/bge-small-en-v1.5",
        init_data_path=None,
    ):
        self.model = model
        self.temperature = temperature
        self.context_window = context_window
        self.embed_model = embed_model
        self.init_data_path = init_data_path
        self.llm = None
        self.service_context = None
        self.query_engine = None
        self.index = None

    def load_model(self):
        print("Loading model")
        self.llm = MonsterLLM(
            model=self.model,
            temperature=self.temperature,
            context_window=self.context_window,
        )
        self.service_context = ServiceContext.from_defaults(
            chunk_size=1024, llm=self.llm, embed_model=self.embed_model
        )

    def load_data(self, data_to_index):
        print("Loading data")
        documents = SimpleDirectoryReader(data_to_index).load_data()
        return documents

    def create_index(self, documents):
        index = VectorStoreIndex.from_documents(
            documents, service_context=self.service_context
        )
        self.query_engine = index.as_query_engine()
        self.index = index

    def update_index(self, documents):
        for d in documents:
            self.index.insert(d)

    def add_documents_to_index(self, data_to_index):
        documents = self.load_data(data_to_index=data_to_index)
        if self.index is not None:
            self.update_index(documents=documents)
            print("Updated documents")
        else:
            self.create_index(documents=documents)

    def query(self, text):
        if self.query_engine is not None:
            response = self.query_engine.query(text)
        else:
            response = self.llm.complete(text)
        return response

    def start_rag(self):
        self.load_model()
        if self.init_data_path is not None:
            print("No documents to load from")
            documents = self.load_data(data_to_index=self.init_data_path)
            self.create_index(documents=documents)


# Example usage
zephyr_rag = ZephyrRAG(model="zephyr-7b-beta")

zephyr_rag.start_rag()

response = zephyr_rag.query("what is cancer and its treatments")
print(response)

print("After adding RAG")
zephyr_rag.add_documents_to_index(data_to_index="./data")
response = zephyr_rag.query("what is cancer and its treatments")
print(response)
