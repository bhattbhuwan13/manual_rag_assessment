# Voy FAQ Bot

A Retrieval-Augmented Generation (RAG) system for Voy's help center, built using LangChain, LanceDB, and OpenAI's GPT models.

## Example Outputs

### When the system knows the answer

![Knows the answer](knows_answer.png)
*The RAG system provides a confident, supported answer with sources.*

### When the system does not know the answer

![No answer](no_answer.png)
*The RAG system declines to answer questions that can't be answered using the knowledge base (vector store) and suggests contacting a human.*

## Project Structure

The project consists of four main components:

1. **Data Collection** (`crawl_voy_zendesk.py`)
2. **Vector Store Creation** (`create_vector_store.py`)
3. **RAG Pipeline with Self-Reflection** (`self_reflective_rag.py`)
4. **Evaluation System** (`evaluator.py`)

## Components

### 1. Data Collection (`crawl_voy_zendesk.py`)

This script crawls Voy's Zendesk help center to collect FAQ content.

**Key Features:**
- Uses Firecrawl to extract content from Zendesk
- Saves content in markdown format.   
Note: The file didn't successfully run so I had to use the firecrawl UI to crawl 30 pages from voy.

**Design Decisions:**
- Structured storage in `data/` directory
- I have prioritised tools that allow me to experiment fast or are open source. Hence, I have used LanceDB as vector store and OpenAI for LLM.
- I have put more focus in evaulation than any other stuff.

### 2. Vector Store Creation (`create_vector_store.py`)

Creates a vector store from the crawled content using LanceDB and OpenAI embeddings.

**Key Features:**
- Implements document chunking(1000 chars) with overlap (200). Didn't think much about it. 
- Stores vectors in LanceDB for efficient retrieval

**Design Decisions:**
- Chunk size of 1000 characters with 200 character overlap
- LanceDB chosen for its efficient vector storage and retrieval
- OpenAI embeddings for high-quality semantic search

### 3. RAG Pipeline with Self-Reflection (`self_reflective_rag.py`)

Implements a RAG system with self-reflection to ensure accurate responses.

**Key Features:**
- Uses GPT-3.5 Turbo for response generation
- Implements self-reflection for hallucination detection
- Provides source attribution for answers

**Design Decisions:**
- Three-step verification process:
  1. Initial response generation
  2. [Self-reflection verification](https://www.semanticscholar.org/paper/A-Self-Reflective-Retrieval-Augmented-Generation-to-Hu-Washburn/1281ec0c63825715cd666c447662bbf7f6992fc3) - Eliminates hallucinations
  3. Response revision if needed  (Currently the relevancy of the documents is only determined using the title of the document, this can be improved)
- Temperature set to 0 for consistent responses
- Retrieves top 3 most relevant documents for context (again, this can be improved)

### 4. Evaluation System (`evaluator.py`)

Evaluates the RAG system's performance across multiple dimensions.

**Key Features:**
- Hallucination detection
- Consistency evaluation
- Semantic similarity measurement

**Design Decisions:**
- Uses GPT-4 for evaluation (chose a better model than gpt-3.5-turbo as a judge)
- Implements comprehensive metrics:
  - Hallucination rate
  - Consistency across variations
  - Semantic similarity scoring

## Usage

1. **Setup Environment:**
```bash
pip install -r requirements.txt
```

2. **Set Environment Variables:**
```bash
export OPENAI_API_KEY=your_api_key_here
```
or, create a .env file with credentials. 

3. **Run the Pipeline:**
```bash
# 1. Crawl Zendesk
python crawl_voy_zendesk.py DO NOT TRY

# 2. Create Vector Store
python create_vector_store.py

# 3. Start RAG System
python self_reflective_rag.py

# 4. Run Evaluation (optional)
python evaluator.py
```

## Design Decisions

### 1. Model Selection
- **GPT-3.5 Turbo** for response generation (cost-effective, good performance)
- **GPT-4** for evaluation (better analysis capabilities)

### 2. Vector Store
- **LanceDB** chosen for:
  - Efficient vector storage
  - Fast similarity search
  - Local storage capability
  - Easy integration with LangChain

### 3. Document Processing
- **Chunking Strategy:**
  - 1000 character chunks
  - 200 character overlap
  - Preserves context across chunks

### 4. Self-Reflection
- **Three-Step Verification:**
  1. Initial response generation
  2. Context verification
  3. Response revision if needed
- **Prompt Engineering:**
  - Clear instructions for verification
  - Structured output format
  - Explicit handling of uncertainty

### 5. Evaluation Metrics
- **Comprehensive Assessment:**
  - Hallucination detection
  - Consistency across variations
  - Source attribution

## Future Improvements
Let's discuss in the next call.