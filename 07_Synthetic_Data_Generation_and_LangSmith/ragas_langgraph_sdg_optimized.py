"""
Optimized RAGAS Synthetic Data Generation using LangGraph Agent Graph
Professional-grade implementation with error handling, logging, and performance optimizations.
"""

import os
import uuid
import json
import logging
import asyncio
from typing import Dict, List, Any, Optional, TypedDict, Tuple
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import time
from contextlib import contextmanager

from langchain_core.documents import Document
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langgraph.graph import StateGraph, END
from langchain_community.vectorstores import Qdrant
from langchain.text_splitter import RecursiveCharacterTextSplitter
import pandas as pd
from tqdm import tqdm


class EvolutionType(Enum):
    """Types of question evolution strategies"""
    SIMPLE = "simple"
    MULTI_CONTEXT = "multi_context"
    REASONING = "reasoning"


@dataclass
class EvolvedQuestion:
    """Represents an evolved question with metadata"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    question: str = ""
    evolution_type: EvolutionType = EvolutionType.SIMPLE
    original_question: Optional[str] = None
    source_documents: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class QuestionAnswer:
    """Represents a question-answer pair"""
    question_id: str = ""
    answer: str = ""
    confidence_score: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class QuestionContext:
    """Represents context for a question"""
    question_id: str = ""
    context: str = ""
    relevance_score: float = 0.0
    source_documents: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SDGConfig:
    """Configuration for the SDG system"""
    llm_model: str = "gpt-4o-mini"
    embedding_model: str = "text-embedding-3-small"
    chunk_size: int = 1000
    chunk_overlap: int = 100
    max_documents: int = 10
    questions_per_document: int = 3
    temperature: float = 0.7
    max_retries: int = 3
    timeout_seconds: int = 300
    log_level: str = "INFO"
    export_dir: str = "synthetic_data_output"


class SyntheticDataState(TypedDict):
    """Enhanced state for the LangGraph workflow"""
    documents: List[Document]
    vectorstore: Optional[Qdrant]
    simple_questions: List[str]
    evolved_questions: List[EvolvedQuestion]
    contexts: List[QuestionContext]
    answers: List[QuestionAnswer]
    current_evolution_type: Optional[EvolutionType]
    processed_questions: List[str]
    config: SDGConfig
    stats: Dict[str, Any]


class OptimizedRagasLangGraphSDG:
    """
    Optimized RAGAS Synthetic Data Generation using LangGraph Agent Graph
    """
    
    def __init__(self, config: Optional[SDGConfig] = None):
        """
        Initialize the optimized SDG system
        
        Args:
            config: Configuration object, uses defaults if None
        """
        self.config = config or SDGConfig()
        
        # Setup logging
        self._setup_logging()
        
        # Initialize components
        self.llm = ChatOpenAI(
            model=self.config.llm_model, 
            temperature=self.config.temperature,
            timeout=self.config.timeout_seconds
        )
        self.embeddings = OpenAIEmbeddings(model=self.config.embedding_model)
        
        # Initialize prompts
        self._setup_prompts()
        
        # Build the graph
        self.graph = self._build_graph()
        
        self.logger.info(f"Initialized SDG system with config: {self.config}")
    
    def _setup_logging(self):
        """Setup logging configuration"""
        logging.basicConfig(
            level=getattr(logging, self.config.log_level.upper()),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
    
    def _setup_prompts(self):
        """Set up optimized prompts for different agents"""
        
        self.question_generation_prompt = ChatPromptTemplate.from_template("""
        You are an expert at generating diverse, high-quality questions from documents.
        
        Given the following document content, generate exactly {num_questions} simple, factual questions that can be answered from this content.
        
        Focus on:
        - Key facts and information
        - Specific details mentioned
        - Important concepts or definitions
        - Numerical data or statistics
        
        Document content:
        {content}
        
        Generate questions that are:
        - Clear and specific
        - Answerable from the provided content
        - Cover different aspects of the document
        - Vary in complexity and depth
        
        Return only the questions, one per line, without numbering or additional text.
        """)
        
        self.simple_evolution_prompt = ChatPromptTemplate.from_template("""
        You are an expert at evolving questions to make them more specific and detailed.
        
        Take the following simple question and make it more specific, detailed, or nuanced:
        Original question: {original_question}
        
        Evolution rules:
        - Add specific details or constraints
        - Make the question more precise
        - Include additional context if helpful
        - Keep the core intent but enhance clarity
        - Maintain the same level of complexity
        
        Return only the evolved question.
        """)
        
        self.multi_context_evolution_prompt = ChatPromptTemplate.from_template("""
        You are an expert at creating questions that require information from multiple sources or contexts.
        
        Take the following question and evolve it to require information from multiple parts of the document or multiple concepts:
        Original question: {original_question}
        
        Evolution rules:
        - Create a question that requires combining information from different sections
        - Ask for comparisons between different concepts
        - Request synthesis of multiple pieces of information
        - Make it require reasoning across contexts
        - Maintain factual accuracy
        
        Return only the evolved question.
        """)
        
        self.reasoning_evolution_prompt = ChatPromptTemplate.from_template("""
        You are an expert at creating questions that require deep reasoning and analysis.
        
        Take the following question and evolve it to require complex reasoning, analysis, or critical thinking:
        Original question: {original_question}
        
        Evolution rules:
        - Add requirements for analysis or evaluation
        - Include "why" or "how" reasoning components
        - Ask for implications or consequences
        - Require synthesis of multiple concepts
        - Add comparative or analytical elements
        - Maintain answerability from the context
        
        Return only the evolved question.
        """)
        
        self.answer_generation_prompt = ChatPromptTemplate.from_template("""
        You are an expert at providing accurate, comprehensive answers based on the given context.
        
        Question: {question}
        Context: {context}
        
        Provide a detailed, accurate answer based solely on the provided context.
        
        Guidelines:
        - Be comprehensive but concise
        - Use specific examples from the context when available
        - If the context doesn't contain enough information, say so explicitly
        - Maintain factual accuracy
        - Structure your answer clearly
        
        Answer:
        """)
    
    def _build_graph(self) -> StateGraph:
        """Build the optimized LangGraph workflow"""
        
        workflow = StateGraph(SyntheticDataState)
        
        # Add nodes for each step
        workflow.add_node("prepare_documents", self._prepare_documents_node)
        workflow.add_node("generate_simple_questions", self._generate_simple_questions_node)
        workflow.add_node("simple_evolution", self._simple_evolution_node)
        workflow.add_node("multi_context_evolution", self._multi_context_evolution_node)
        workflow.add_node("reasoning_evolution", self._reasoning_evolution_node)
        workflow.add_node("generate_contexts", self._generate_contexts_node)
        workflow.add_node("generate_answers", self._generate_answers_node)
        
        # Define the workflow
        workflow.set_entry_point("prepare_documents")
        
        workflow.add_edge("prepare_documents", "generate_simple_questions")
        workflow.add_edge("generate_simple_questions", "simple_evolution")
        workflow.add_edge("simple_evolution", "multi_context_evolution")
        workflow.add_edge("multi_context_evolution", "reasoning_evolution")
        workflow.add_edge("reasoning_evolution", "generate_contexts")
        workflow.add_edge("generate_contexts", "generate_answers")
        workflow.add_edge("generate_answers", END)
        
        return workflow.compile()
    
    @contextmanager
    def _timer(self, operation_name: str):
        """Context manager for timing operations"""
        start_time = time.time()
        self.logger.info(f"Starting {operation_name}")
        try:
            yield
        finally:
            elapsed = time.time() - start_time
            self.logger.info(f"Completed {operation_name} in {elapsed:.2f} seconds")
    
    def _prepare_documents_node(self, state: SyntheticDataState) -> SyntheticDataState:
        """Prepare documents by chunking and creating vectorstore"""
        with self._timer("document preparation"):
            documents = state["documents"][:self.config.max_documents]  # Limit documents
            
            # Chunk the documents
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=self.config.chunk_size,
                chunk_overlap=self.config.chunk_overlap
            )
            
            chunked_docs = text_splitter.split_documents(documents)
            
            # Create vectorstore
            vectorstore = Qdrant.from_documents(
                documents=chunked_docs,
                embedding=self.embeddings,
                location=":memory:",
                collection_name="synthetic_data_generation"
            )
            
            state["vectorstore"] = vectorstore
            state["stats"] = {
                "total_documents": len(documents),
                "total_chunks": len(chunked_docs),
                "chunk_size": self.config.chunk_size
            }
            
            self.logger.info(f"Prepared {len(chunked_docs)} document chunks from {len(documents)} documents")
            
        return state
    
    def _generate_simple_questions_node(self, state: SyntheticDataState) -> SyntheticDataState:
        """Generate simple questions from documents"""
        with self._timer("simple question generation"):
            documents = state["documents"][:self.config.max_documents]
            simple_questions = []
            
            # Generate questions from each document
            for doc in tqdm(documents, desc="Generating questions"):
                content = doc.page_content[:2000]  # Limit content length
                
                try:
                    # Generate questions using LLM
                    chain = self.question_generation_prompt | self.llm
                    response = chain.invoke({
                        "content": content,
                        "num_questions": self.config.questions_per_document
                    })
                    
                    # Parse questions
                    questions = [q.strip() for q in response.content.split('\n') if q.strip()]
                    simple_questions.extend(questions[:self.config.questions_per_document])
                    
                except Exception as e:
                    self.logger.error(f"Error generating questions for document: {e}")
                    continue
            
            state["simple_questions"] = simple_questions
            self.logger.info(f"Generated {len(simple_questions)} simple questions")
            
        return state
    
    def _simple_evolution_node(self, state: SyntheticDataState) -> SyntheticDataState:
        """Apply simple evolution to questions"""
        with self._timer("simple evolution"):
            simple_questions = state["simple_questions"]
            evolved_questions = []
            
            for question in tqdm(simple_questions, desc="Simple evolution"):
                try:
                    chain = self.simple_evolution_prompt | self.llm
                    response = chain.invoke({"original_question": question})
                    
                    evolved_question = EvolvedQuestion(
                        question=response.content.strip(),
                        evolution_type=EvolutionType.SIMPLE,
                        original_question=question
                    )
                    evolved_questions.append(evolved_question)
                    
                except Exception as e:
                    self.logger.error(f"Error in simple evolution for question '{question}': {e}")
                    continue
            
            state["evolved_questions"] = evolved_questions
            self.logger.info(f"Applied simple evolution to {len(evolved_questions)} questions")
            
        return state
    
    def _multi_context_evolution_node(self, state: SyntheticDataState) -> SyntheticDataState:
        """Apply multi-context evolution to questions"""
        with self._timer("multi-context evolution"):
            simple_questions = state["simple_questions"]
            evolved_questions = state["evolved_questions"]
            
            for question in tqdm(simple_questions, desc="Multi-context evolution"):
                try:
                    chain = self.multi_context_evolution_prompt | self.llm
                    response = chain.invoke({"original_question": question})
                    
                    evolved_question = EvolvedQuestion(
                        question=response.content.strip(),
                        evolution_type=EvolutionType.MULTI_CONTEXT,
                        original_question=question
                    )
                    evolved_questions.append(evolved_question)
                    
                except Exception as e:
                    self.logger.error(f"Error in multi-context evolution for question '{question}': {e}")
                    continue
            
            state["evolved_questions"] = evolved_questions
            self.logger.info(f"Applied multi-context evolution to {len(simple_questions)} questions")
            
        return state
    
    def _reasoning_evolution_node(self, state: SyntheticDataState) -> SyntheticDataState:
        """Apply reasoning evolution to questions"""
        with self._timer("reasoning evolution"):
            simple_questions = state["simple_questions"]
            evolved_questions = state["evolved_questions"]
            
            for question in tqdm(simple_questions, desc="Reasoning evolution"):
                try:
                    chain = self.reasoning_evolution_prompt | self.llm
                    response = chain.invoke({"original_question": question})
                    
                    evolved_question = EvolvedQuestion(
                        question=response.content.strip(),
                        evolution_type=EvolutionType.REASONING,
                        original_question=question
                    )
                    evolved_questions.append(evolved_question)
                    
                except Exception as e:
                    self.logger.error(f"Error in reasoning evolution for question '{question}': {e}")
                    continue
            
            state["evolved_questions"] = evolved_questions
            self.logger.info(f"Applied reasoning evolution to {len(simple_questions)} questions")
            
        return state
    
    def _generate_contexts_node(self, state: SyntheticDataState) -> SyntheticDataState:
        """Generate relevant contexts for each evolved question"""
        with self._timer("context generation"):
            vectorstore = state["vectorstore"]
            evolved_questions = state["evolved_questions"]
            contexts = []
            
            retriever = vectorstore.as_retriever(search_kwargs={"k": 3})
            
            for evolved_q in tqdm(evolved_questions, desc="Generating contexts"):
                try:
                    # Retrieve relevant context
                    relevant_docs = retriever.invoke(evolved_q.question)
                    
                    # Combine context from multiple documents
                    context_parts = [doc.page_content for doc in relevant_docs]
                    combined_context = "\n\n".join(context_parts)
                    
                    question_context = QuestionContext(
                        question_id=evolved_q.id,
                        context=combined_context,
                        relevance_score=1.0,  # Could be enhanced with actual scoring
                        source_documents=[doc.metadata.get('source', 'unknown') for doc in relevant_docs]
                    )
                    contexts.append(question_context)
                    
                except Exception as e:
                    self.logger.error(f"Error generating context for question '{evolved_q.question}': {e}")
                    continue
            
            state["contexts"] = contexts
            self.logger.info(f"Generated contexts for {len(contexts)} questions")
            
        return state
    
    def _generate_answers_node(self, state: SyntheticDataState) -> SyntheticDataState:
        """Generate answers for each question using the retrieved context"""
        with self._timer("answer generation"):
            evolved_questions = state["evolved_questions"]
            contexts = state["contexts"]
            answers = []
            
            # Create a mapping of question_id to context
            context_map = {ctx.question_id: ctx.context for ctx in contexts}
            
            for evolved_q in tqdm(evolved_questions, desc="Generating answers"):
                try:
                    context = context_map.get(evolved_q.id, "")
                    
                    # Generate answer using LLM
                    chain = self.answer_generation_prompt | self.llm
                    response = chain.invoke({
                        "question": evolved_q.question,
                        "context": context
                    })
                    
                    question_answer = QuestionAnswer(
                        question_id=evolved_q.id,
                        answer=response.content.strip(),
                        confidence_score=1.0  # Could be enhanced with actual confidence scoring
                    )
                    answers.append(question_answer)
                    
                except Exception as e:
                    self.logger.error(f"Error generating answer for question '{evolved_q.question}': {e}")
                    continue
            
            state["answers"] = answers
            self.logger.info(f"Generated answers for {len(answers)} questions")
            
        return state
    
    def generate_synthetic_data(self, documents: List[Document]) -> Dict[str, List[Dict]]:
        """
        Generate synthetic data using the optimized LangGraph workflow
        
        Args:
            documents: List of LangChain documents to process
            
        Returns:
            Dictionary containing evolved questions, answers, and contexts
        """
        self.logger.info("Starting synthetic data generation")
        
        # Validate inputs
        if not documents:
            raise ValueError("No documents provided")
        
        # Initialize state
        initial_state = SyntheticDataState(
            documents=documents,
            vectorstore=None,
            simple_questions=[],
            evolved_questions=[],
            contexts=[],
            answers=[],
            current_evolution_type=None,
            processed_questions=[],
            config=self.config,
            stats={}
        )
        
        try:
            # Run the graph
            final_state = self.graph.invoke(initial_state)
            
            # Format output
            output = {
                "evolved_questions": [
                    {
                        "id": eq.id,
                        "question": eq.question,
                        "evolution_type": eq.evolution_type.value,
                        "original_question": eq.original_question,
                        "metadata": eq.metadata
                    }
                    for eq in final_state["evolved_questions"]
                ],
                "answers": [
                    {
                        "question_id": qa.question_id,
                        "answer": qa.answer,
                        "confidence_score": qa.confidence_score,
                        "metadata": qa.metadata
                    }
                    for qa in final_state["answers"]
                ],
                "contexts": [
                    {
                        "question_id": qc.question_id,
                        "context": qc.context,
                        "relevance_score": qc.relevance_score,
                        "source_documents": qc.source_documents,
                        "metadata": qc.metadata
                    }
                    for qc in final_state["contexts"]
                ],
                "stats": final_state.get("stats", {})
            }
            
            self.logger.info(f"Synthetic data generation completed successfully")
            self.logger.info(f"Generated {len(output['evolved_questions'])} evolved questions")
            self.logger.info(f"Generated {len(output['answers'])} answers")
            self.logger.info(f"Generated {len(output['contexts'])} contexts")
            
            return output
            
        except Exception as e:
            self.logger.error(f"Synthetic data generation failed: {e}")
            raise
    
    def export_results(self, synthetic_data: Dict[str, List[Dict]], export_dir: Optional[str] = None) -> Dict[str, str]:
        """
        Export synthetic data to various formats
        
        Args:
            synthetic_data: The generated synthetic data
            export_dir: Directory to export to, uses config default if None
            
        Returns:
            Dictionary mapping format names to file paths
        """
        export_path = Path(export_dir or self.config.export_dir)
        export_path.mkdir(exist_ok=True)
        
        timestamp = pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")
        exported_files = {}
        
        try:
            # Export to JSON
            json_file = export_path / f"langgraph_sdg_results_{timestamp}.json"
            with open(json_file, 'w') as f:
                json.dump(synthetic_data, f, indent=2)
            exported_files['json'] = str(json_file)
            
            # Export individual components to CSV
            for component in ['evolved_questions', 'answers', 'contexts']:
                if component in synthetic_data:
                    df = pd.DataFrame(synthetic_data[component])
                    csv_file = export_path / f"{component}_{timestamp}.csv"
                    df.to_csv(csv_file, index=False)
                    exported_files[component] = str(csv_file)
            
            # Export combined dataset
            combined_data = self._create_combined_dataset(synthetic_data)
            combined_df = pd.DataFrame(combined_data)
            combined_file = export_path / f"complete_dataset_{timestamp}.csv"
            combined_df.to_csv(combined_file, index=False)
            exported_files['complete_dataset'] = str(combined_file)
            
            self.logger.info(f"Exported results to {len(exported_files)} files in {export_path}")
            return exported_files
            
        except Exception as e:
            self.logger.error(f"Export failed: {e}")
            raise
    
    def _create_combined_dataset(self, synthetic_data: Dict[str, List[Dict]]) -> List[Dict]:
        """Create a combined dataset with all components"""
        combined_data = []
        
        # Create mappings for efficient lookup
        answers_map = {qa['question_id']: qa for qa in synthetic_data.get('answers', [])}
        contexts_map = {qc['question_id']: qc for qc in synthetic_data.get('contexts', [])}
        
        for question in synthetic_data.get('evolved_questions', []):
            question_id = question['id']
            
            combined_item = {
                'id': question_id,
                'evolution_type': question['evolution_type'],
                'question': question['question'],
                'original_question': question.get('original_question', ''),
                'answer': answers_map.get(question_id, {}).get('answer', 'No answer'),
                'context': contexts_map.get(question_id, {}).get('context', 'No context'),
                'confidence_score': answers_map.get(question_id, {}).get('confidence_score', 0.0),
                'relevance_score': contexts_map.get(question_id, {}).get('relevance_score', 0.0),
                'source_documents': contexts_map.get(question_id, {}).get('source_documents', [])
            }
            combined_data.append(combined_item)
        
        return combined_data


def create_optimized_config(**kwargs) -> SDGConfig:
    """
    Create an optimized configuration with sensible defaults
    
    Args:
        **kwargs: Configuration overrides
        
    Returns:
        SDGConfig instance
    """
    defaults = {
        'llm_model': 'gpt-4o-mini',
        'embedding_model': 'text-embedding-3-small',
        'chunk_size': 1000,
        'chunk_overlap': 100,
        'max_documents': 5,  # Reduced for efficiency
        'questions_per_document': 2,  # Reduced for efficiency
        'temperature': 0.7,
        'max_retries': 3,
        'timeout_seconds': 300,
        'log_level': 'INFO',
        'export_dir': 'synthetic_data_output'
    }
    
    # Override defaults with provided kwargs
    config_dict = {**defaults, **kwargs}
    return SDGConfig(**config_dict)


if __name__ == "__main__":
    # Example usage
    from langchain_core.documents import Document
    
    # Create sample documents
    sample_docs = [
        Document(page_content="Sample content...", metadata={"source": "test.pdf"})
    ]
    
    # Create optimized configuration
    config = create_optimized_config(
        max_documents=2,
        questions_per_document=1,
        log_level="DEBUG"
    )
    
    # Initialize SDG system
    sdg = OptimizedRagasLangGraphSDG(config)
    
    # Generate synthetic data
    result = sdg.generate_synthetic_data(sample_docs)
    
    # Export results
    exported_files = sdg.export_results(result)
    print(f"Exported to: {exported_files}")
