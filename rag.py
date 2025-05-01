import os
import lancedb
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.vectorstores import LanceDB
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def setup_rag_pipeline():
    # Initialize OpenAI embeddings
    embeddings = OpenAIEmbeddings(
        openai_api_key=os.getenv('OPENAI_API_KEY')
    )
    
    # Connect to LanceDB
    db = lancedb.connect("data/vector_store")
    
    # Load the vector store
    vector_store = LanceDB(
        connection=db,
        embedding=embeddings,
        table_name="voy_docs"
    )
    
    # Create the LLM
    llm = ChatOpenAI(
        model_name="gpt-3.5-turbo",
        temperature=0,
        openai_api_key=os.getenv('OPENAI_API_KEY')
    )
    
    # Create a custom prompt template
    template = """You are a helpful assistant for Voy's help center. Use the following pieces of context to answer the question at the end. 
    If you don't know the answer, just say that you don't know, don't try to make up an answer.
    Always provide a clear and concise answer based on the context provided.
    
    Context: {context}
    
    Question: {question}
    
    Helpful Answer:"""
    
    QA_CHAIN_PROMPT = PromptTemplate.from_template(template)
    
    # Create the QA chain
    qa_chain = RetrievalQA.from_chain_type(
        llm,
        retriever=vector_store.as_retriever(
            search_kwargs={"k": 3}  # Retrieve top 3 most relevant documents
        ),
        chain_type_kwargs={"prompt": QA_CHAIN_PROMPT},
        return_source_documents=True
    )
    
    return qa_chain

def main():
    if not os.getenv('OPENAI_API_KEY'):
        print("Please set OPENAI_API_KEY in your .env file")
        exit(1)
    
    qa_chain = setup_rag_pipeline()
    
    print("Welcome to Voy Help Center Assistant!")
    print("Type 'exit' to quit.")
    
    while True:
        question = input("\nWhat would you like to know about Voy? ")
        
        if question.lower() == 'exit':
            break
            
        try:
            result = qa_chain({"query": question})
            print("\nAnswer:", result["result"])
            print("\nSources:")
            for doc in result["source_documents"]:
                print(f"- {doc.metadata['source']}")
        except Exception as e:
            print(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    main() 