import sys
import warnings
if not sys.warnoptions:
    warnings.simplefilter("ignore")
    os.environ["PYTHONWARNINGS"] = "ignore"

import os
from pathlib import Path
import lancedb
from langchain_community.document_loaders import DirectoryLoader
from langchain_community.document_loaders import TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import LanceDB
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def create_vector_store():
    # Initialize OpenAI embeddings
    embeddings = OpenAIEmbeddings(
        openai_api_key=os.getenv('OPENAI_API_KEY'),
        # model="text-embedding-3-small"  
    )
    
    # Initialize LanceDB
    db = lancedb.connect("data/vector_store")
    
    # Load documents from the data directory
    loader = DirectoryLoader(
        "data",
        glob="**/*.md",
        loader_cls=TextLoader,
        show_progress=True
    )
    documents = loader.load()
    
    # Split documents into chunks
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        length_function=len,
        is_separator_regex=False,
    )
    chunks = text_splitter.split_documents(documents)
    
    # Create vector store
    vector_store = LanceDB.from_documents(
        documents=chunks,
        embedding=embeddings,
        connection=db,
        table_name="voy_docs"
    )
    
    print(f"Created vector store with {len(chunks)} chunks")
    return vector_store

if __name__ == "__main__":
    if not os.getenv('OPENAI_API_KEY'):
        print("Please set OPENAI_API_KEY in your .env file")
        exit(1)
    
    vector_store = create_vector_store()
    print("Vector store created successfully!") 