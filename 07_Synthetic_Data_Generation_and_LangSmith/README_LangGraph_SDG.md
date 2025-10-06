# RAGAS Synthetic Data Generation with LangGraph Agent Graph

This implementation reproduces RAGAS Synthetic Data Generation steps using a LangGraph Agent Graph instead of the Knowledge Graph approach. It leverages the Evol-Instruct method to generate diverse, high-quality synthetic data for RAG system evaluation.

## 🎯 Features

- **LangGraph Workflow**: Uses LangGraph's stateful agent system for orchestration
- **Evol-Instruct Method**: Implements three evolution strategies for question generation
- **Multiple Evolution Types**: Handles simple, multi-context, and reasoning evolution
- **Context Retrieval**: Automatically retrieves relevant contexts for questions
- **Answer Generation**: Generates comprehensive answers based on retrieved contexts
- **Flexible Input**: Takes a list of LangChain Documents as input

## 🔄 Evolution Strategies

### 1. Simple Evolution
- Makes questions more specific and detailed
- Adds constraints or additional context
- Enhances clarity while maintaining the core intent

### 2. Multi-Context Evolution
- Creates questions requiring information from multiple sources
- Asks for comparisons between different concepts
- Requires synthesis of multiple pieces of information

### 3. Reasoning Evolution
- Generates questions requiring complex reasoning and analysis
- Includes "why" or "how" reasoning components
- Asks for implications, consequences, or analytical elements

## 📊 Output Format

The system generates three main outputs:

### 1. Evolved Questions
```python
[
    {
        "id": "unique-question-id",
        "question": "evolved question text",
        "evolution_type": "simple|multi_context|reasoning",
        "original_question": "original simple question"
    }
]
```

### 2. Answers
```python
[
    {
        "question_id": "unique-question-id",
        "answer": "comprehensive answer based on context"
    }
]
```

### 3. Contexts
```python
[
    {
        "question_id": "unique-question-id",
        "context": "retrieved relevant context from documents"
    }
]
```

## 🚀 Quick Start

### 1. Installation

Ensure you have the required dependencies installed:

```bash
pip install langchain langgraph langchain-openai langchain-community qdrant-client
```

### 2. Environment Setup

Set your API keys:

```python
import os
os.environ["OPENAI_API_KEY"] = "your-openai-api-key"
os.environ["LANGCHAIN_API_KEY"] = "your-langchain-api-key"  # Optional
```

### 3. Basic Usage

```python
from langchain_core.documents import Document
from ragas_langgraph_sdg import RagasLangGraphSDG

# Load your documents
documents = [
    Document(page_content="Your document content...", metadata={"source": "doc1.pdf"})
]

# Initialize the SDG system
sdg_system = RagasLangGraphSDG(
    llm_model="gpt-4o-mini",
    embedding_model="text-embedding-3-small",
    chunk_size=1000,
    chunk_overlap=100
)

# Generate synthetic data
synthetic_data = sdg_system.generate_synthetic_data(documents)

# Access results
questions = synthetic_data['evolved_questions']
answers = synthetic_data['answers']
contexts = synthetic_data['contexts']
```

## 🔧 Configuration

### RagasLangGraphSDG Parameters

- `llm_model` (str): OpenAI model for question/answer generation (default: "gpt-4o-mini")
- `embedding_model` (str): OpenAI embedding model for vector operations (default: "text-embedding-3-small")
- `chunk_size` (int): Size of document chunks for processing (default: 1000)
- `chunk_overlap` (int): Overlap between chunks (default: 100)

### Customization

You can customize the evolution strategies by modifying the prompts in the `_setup_prompts()` method:

```python
# Example: Custom simple evolution prompt
self.simple_evolution_prompt = ChatPromptTemplate.from_template("""
Your custom prompt here...
Original question: {original_question}
...
""")
```

## 📁 File Structure

```
├── ragas_langgraph_sdg.py          # Main SDG implementation
├── RAGAS_LangGraph_SDG_Demo.ipynb  # Demonstration notebook
├── test_sdg_system.py              # Test script
└── README_LangGraph_SDG.md         # This documentation
```

## 🧪 Testing

Run the test script to verify the implementation:

```bash
python test_sdg_system.py
```

Or use the demonstration notebook:

```bash
jupyter notebook RAGAS_LangGraph_SDG_Demo.ipynb
```

## 🔍 Architecture

### LangGraph Workflow

The system uses a stateful workflow with the following nodes:

1. **prepare_documents**: Chunks documents and creates vectorstore
2. **generate_simple_questions**: Generates initial questions from documents
3. **simple_evolution**: Applies simple evolution to questions
4. **multi_context_evolution**: Applies multi-context evolution to questions
5. **reasoning_evolution**: Applies reasoning evolution to questions
6. **generate_contexts**: Retrieves relevant contexts for each question
7. **generate_answers**: Generates answers based on contexts

### State Management

The workflow uses a `SyntheticDataState` TypedDict to manage state across nodes:

```python
class SyntheticDataState(TypedDict):
    documents: List[Document]
    vectorstore: Optional[Qdrant]
    simple_questions: List[str]
    evolved_questions: List[EvolvedQuestion]
    contexts: List[QuestionContext]
    answers: List[QuestionAnswer]
    current_evolution_type: Optional[EvolutionType]
    processed_questions: List[str]
```

## 📈 Performance Considerations

- **Chunk Size**: Larger chunks provide more context but increase processing time
- **LLM Model**: GPT-4o mini provides good quality at lower cost than GPT-4
- **Embedding Model**: text-embedding-3-small offers good performance for most use cases
- **Document Limit**: The system processes the first 3 documents by default for efficiency

## 🔄 Comparison with RAGAS Knowledge Graph

| Feature | RAGAS Knowledge Graph | LangGraph Agent Graph |
|---------|----------------------|----------------------|
| Architecture | Knowledge Graph with nodes/edges | Stateful agent workflow |
| Evolution Strategy | Graph-based transformations | Prompt-based evolution |
| Flexibility | Fixed graph structure | Customizable workflow |
| Extensibility | Limited to graph operations | Easy to add new agents/nodes |
| State Management | Graph state | TypedDict state |
| Debugging | Graph visualization | Workflow step tracking |

## 🤝 Contributing

To extend the system:

1. **Add New Evolution Types**: Create new evolution strategies in the prompt setup
2. **Add New Agents**: Implement new nodes in the LangGraph workflow
3. **Customize Prompts**: Modify prompts to fit your specific use case
4. **Add Evaluators**: Include quality evaluation for generated data

## 📄 License

This implementation is provided as an educational example of reproducing RAGAS functionality using LangGraph.

## 🙏 Acknowledgments

- RAGAS team for the original synthetic data generation approach
- LangChain team for the LangGraph framework
- OpenAI for the language models and embeddings
