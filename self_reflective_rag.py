import os
import lancedb
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.vectorstores import LanceDB
from langchain.chains import RetrievalQA, LLMChain
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
    
    # Create the QA chain
    qa_chain = RetrievalQA.from_chain_type(
        llm,
        retriever=vector_store.as_retriever(
            search_kwargs={"k": 3}  # Retrieve top 3 most relevant documents
        ),
        return_source_documents=True
    )
    
    # Self-reflection prompt template
    reflection_template = """
    You are a Voy help center information verifier. Your task is to:
    1. Compare the generated response with the retrieved context
    2. Identify any statements in the response that are unsupported by the context
    3. Flag potential hallucinations or factual errors
    4. Suggest improvements to make the answer more accurate and helpful

    Retrieved Context:
    {context}

    Generated Response:
    {response}

    Verification Results:
    """
    
    reflection_prompt = PromptTemplate(
        input_variables=["context", "response"],
        template=reflection_template
    )
    
    reflection_chain = LLMChain(llm=llm, prompt=reflection_prompt)
    
    return qa_chain, reflection_chain, vector_store, llm

def self_reflective_rag(query, qa_chain, reflection_chain, vector_store, llm):
    # Get initial response and context
    result = qa_chain({"query": query})
    initial_response = result["result"]
    context = "\n\n".join([doc.page_content for doc in result["source_documents"]])
    
    # Self-reflection for hallucination detection
    verification = reflection_chain.run(context=context, response=initial_response)
    
    # Revision based on verification results
    if "hallucination" in verification.lower() or "unsupported" in verification.lower():
        revision_template = """
        Original Response: {initial_response}
        
        Verification Results: {verification}
        
        Please revise the response to remove any unsupported claims or hallucinations,
        using only information from the context. If you cannot provide a complete answer
        with the available context, clearly state the limitations.
        
        Context: {context}
        
        Revised Answer:
        """
        
        revision_prompt = PromptTemplate(
            input_variables=["initial_response", "verification", "context"],
            template=revision_template
        )
        
        revision_chain = LLMChain(llm=llm, prompt=revision_prompt)
        final_response = revision_chain.run(
            initial_response=initial_response,
            verification=verification,
            context=context
        )
        return final_response, result["source_documents"]
    
    return initial_response, result["source_documents"]

def main():
    if not os.getenv('OPENAI_API_KEY'):
        print("Please set OPENAI_API_KEY in your .env file")
        exit(1)
    
    qa_chain, reflection_chain, vector_store, llm = setup_rag_pipeline()
    
    print("Welcome to Voy Help Center Assistant with Self-Reflection!")
    print("Type 'exit' to quit.")
    
    while True:
        question = input("\nWhat would you like to know about Voy? ")
        
        if question.lower() == 'exit':
            break
            
        try:
            response, sources = self_reflective_rag(question, qa_chain, reflection_chain, vector_store, llm)
            print("\nAnswer:", response)
            print("\nSources:")
            for doc in sources:
                print(f"- {doc.metadata['source']}")
        except Exception as e:
            print(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    main() 