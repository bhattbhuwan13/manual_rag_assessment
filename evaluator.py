import openai
import numpy as np
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
import json

class MedicalLLMEvaluator:
    def __init__(self, model_name="gpt-4", documents_path="medical_faqs.txt"):
        self.model_name = model_name
        self.vector_store = create_vector_store(documents_path)
        self.llm = ChatOpenAI(temperature=0, model=model_name)
        
    def evaluate_comprehensive(self, test_queries, ground_truth=None, experts=None):
        """
        Comprehensive evaluation using multiple strategies
        
        Args:
            test_queries: List of medical queries to evaluate
            experts: Optional list of expert evaluators (functions that rate responses)
            
        Returns:
            Evaluation results across multiple dimensions
        """
        results = {
            "hallucination_metrics": {},
            "consistency_metrics": {},
            "expert_ratings": {},
            "benchmark_metrics": {}
        }
        
        # 1. Evaluate hallucination rate with self-reflection
        hallucination_results = self.evaluate_hallucination(test_queries)
        results["hallucination_metrics"] = hallucination_results
        
        # 2. Evaluate consistency using semantically equivalent queries
        consistency_results = self.evaluate_consistency(test_queries)
        results["consistency_metrics"] = consistency_results
        
        # 3. Benchmark evaluation if ground truth is available
        if ground_truth:
            benchmark_results = self.evaluate_benchmark(test_queries, ground_truth)
            results["benchmark_metrics"] = benchmark_results
        
        # 4. Expert evaluation if provided
        if experts:
            expert_results = self.evaluate_with_experts(test_queries, experts)
            results["expert_ratings"] = expert_results
            
        return results
    
    def evaluate_hallucination(self, test_queries, sample_size=20):
        """Evaluate hallucination rate using self-reflection"""
        hallucination_count = 0
        unsupported_claims = []
        
        # Sample queries for detailed analysis
        if len(test_queries) > sample_size:
            sampled_queries = np.random.choice(test_queries, sample_size, replace=False)
        else:
            sampled_queries = test_queries
            
        for query in sampled_queries:
            # Get initial response using RAG
            docs = self.vector_store.similarity_search(query, k=3)
            context = "\n\n".join([doc.page_content for doc in docs])
            
            response = self.llm.predict(f"""
            Context: {context}
            Question: {query}
            Answer:
            """)
            
            # Use self-reflection to check for hallucinations
            verification = self.llm.predict(
                f"""
                You are a medical fact-checker. Verify if the following response is fully supported
                by the given context. Identify any claims that go beyond the context.
                
                Context: {context}
                Response: {response}
                
                List any unsupported claims or hallucinations:
            """
            )
            
            if not "no unsupported claims" in verification.lower():
                hallucination_count += 1
                unsupported_claims.append({
                    "query": query,
                    "context": context,
                    "response": response,
                    "verification": verification
                })
        
        return {
            "hallucination_rate": hallucination_count / len(sampled_queries),
            "samples": unsupported_claims
        }
    
    def evaluate_consistency(self, test_queries, variations_per_query=3):
        """Evaluate consistency across semantically equivalent query variations"""
        consistency_scores = []
        
        for query in test_queries[:10]:  # Limit to 10 queries for efficiency
            # Generate variations of the query
            variations_prompt = f"""
            Generate {variations_per_query} semantically equivalent variations of this medical question
            that ask for the same information but with different wording:
            
            Original question: {query}
            
            Output the variations as a JSON array:
            """
            
            variations_json = self.llm.predict(variations_prompt)
            
            try:
                # Extract variations from JSON response
                variations = json.loads(variations_json)
                if not isinstance(variations, list):
                    variations = [var for var in variations.values()]
            except:
                # Fallback if JSON parsing fails
                variations = [query] + [query + f" (rephrased version {i})" for i in range(variations_per_query-1)]
            
            # Get responses for all variations
            responses = []
            for var in variations:
                resp = self_reflective_rag(var)
                responses.append(resp)
            
            # Check consistency across responses
            pairwise_similarities = []
            for i in range(len(responses)):
                for j in range(i+1, len(responses)):
                    similarity = self.semantic_similarity(responses[i], responses[j])
                    pairwise_similarities.append(similarity)
            
            avg_consistency = np.mean(pairwise_similarities) if pairwise_similarities else 0
            consistency_scores.append({
                "original_query": query,
                "variations": variations,
                "consistency_score": avg_consistency
            })
        
        return {
            "average_consistency": np.mean([s["consistency_score"] for s in consistency_scores]),
            "per_query_results": consistency_scores
        }
    
    def semantic_similarity(self, text1, text2):
        """Calculate semantic similarity between two texts"""
        # Using LLM to rate similarity
        similarity_prompt = f"""
        On a scale of 0 to 1, rate how semantically similar these two medical responses are
        in terms of their clinical content and advice:
        
        Response 1: {text1}
        
        Response 2: {text2}
        
        Output a single number between 0 and 1:
        """
        
        similarity_score = self.llm.predict(similarity_prompt).strip()
        try:
            return float(similarity_score)
        except:
            return 0.5  # Default if parsing fails
    
    
    
    def extract_classification(self, response):
        """Extract classification answer from model response"""
        extraction_prompt = f"""
        Extract the core answer/classification from this medical response:
        
        {response}
        
        Output the answer class or category only:
        """
        
        extracted = self.llm.predict(extraction_prompt).strip()
        return extracted
    
    

# Example usage
evaluator = MedicalLLMEvaluator()
test_queries = [
    "What are the symptoms of COVID-19?",
    "How is diabetes treated?",
    "What medications should be avoided during pregnancy?"
    # Add more test queries
]


print(json.dumps(evaluation_results, indent=2))
