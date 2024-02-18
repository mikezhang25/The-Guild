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

#Step 1
model = "zephyr-7b-beta"

#Step 2
print("Loading model")
llm = MonsterLLM(model=model, temperature=0.75, context_window=1024)
service_context = ServiceContext.from_defaults(
    chunk_size=1024, llm=llm, embed_model="local:BAAI/bge-small-en-v1.5"
)

#Step 3
print("Loading data")
documents = SimpleDirectoryReader("./data").load_data()

#Step 4
index = VectorStoreIndex.from_documents(
    documents, service_context=service_context
)
query_engine = index.as_query_engine()

#Step 5
response = query_engine.query("What does malignant mean?")
print(response)

from monsterapi import client

monster_client = client(os.environ["MONSTER_API_KEY"])
model = 'llama2-7b-chat';
input_data = {
  'prompt': 'Whats the meaning of life?',
  'top_k': 10,
  'top_p': 0.9,
  'temp': 0.9,
  'max_length': 1000,
  'beam_size': 1,
  'system_prompt': 'You are a helpful, respectful and honest assistant. Always answer as helpfully as possible, while being safe...',
  'repetition_penalty': 1.2,
};
result = monster_client.generate(model, input_data)

print(result['text'])