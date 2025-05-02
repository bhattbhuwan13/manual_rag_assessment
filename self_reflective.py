from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from langchain.chat_models import ChatOpenAI
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import FAISS
from langchain.text_splitter import RecursiveCharacterTextSplitter
import os

# Initialize embedding model
embeddings = OpenAIEmbeddings()

# Function to create vector store from documents
def create_vector_store(documents_path):
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    with open(documents_path, 'r') as f:
        data = f.read()
    texts = text_splitter.split_text(data)
    vector_store = FAISS.from_texts(texts, embeddings)
    return vector_store

# Create vector store from medical FAQs
vector_store = create_vector_store("medical_faqs.txt")

# Initialize LLM
llm = ChatOpenAI(temperature=0, model="gpt-4")

# Self-reflection node to verify response against retrieved context
reflection_template = """
You are a medical information verifier. Your task is to:
1. Compare the generated response with the retrieved context
2. Identify any statements in the response that are unsupported by the context
3. Flag potential hallucinations or factual errors

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

# Main RAG function with self-reflection
def self_reflective_rag(query, top_k=3):
    # 1. Retrieve relevant documents
    docs = vector_store.similarity_search(query, k=top_k)
    context = "\n\n".join([doc.page_content for doc in docs])
    
    # 2. Generate initial response
    generation_template = f"""
    You are a medical assistant answering questions based strictly on the provided context.
    Only answer what is supported by the context. If the context doesn't contain relevant information,
    state that you don't have enough information to provide a reliable answer.
    
    Context: {context}
    
    Question: {query}
    
    Answer:
    """
    
    initial_response = llm.predict(generation_template)
    
    # 3. Self-reflection for hallucination detection
    verification = reflection_chain.run(context=context, response=initial_response)
    
    # 4. Revision based on verification results
    if "hallucination" in verification.lower() or "unsupported" in verification.lower():
        revision_template = f"""
        Original Response: {initial_response}
        
        Verification Results: {verification}
        
        Please revise the response to remove any unsupported claims or hallucinations,
        using only information from the context. If you cannot provide a complete answer
        with the available context, clearly state the limitations.
        
        Context: {context}
        
        Revised Answer:
        """
        
        final_response = llm.predict(revision_template)
        return final_response
    
    return initial_response
