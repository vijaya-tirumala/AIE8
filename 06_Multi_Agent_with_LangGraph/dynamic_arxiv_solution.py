# Dynamic ArXiv Paper Fetching - Activity #1 Solution
# This replaces the hard-coded PDF approach with dynamic paper fetching

from langchain_community.tools.arxiv.tool import ArxivQueryRun
from langchain_core.documents import Document
from langchain_core.tools import tool
from langchain_community.vectorstores import Qdrant
from langchain_openai.embeddings import OpenAIEmbeddings
from langchain_openai.chat_models import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from langchain_community.tools.tavily_search import TavilySearchResults

# Initialize tools
arxiv_tool = ArxivQueryRun()
tavily_tool = TavilySearchResults(max_results=5)
embedding_model = OpenAIEmbeddings(model="text-embedding-3-small")

# Simple cache to avoid re-fetching same papers
paper_cache = {}

@tool
def fetch_arxiv_papers(query: str, max_papers: int = 2):
    """
    Dynamically fetch ArXiv papers based on query.
    
    Args:
        query: What to search for (e.g., "machine learning")
        max_papers: How many papers to get (default: 2)
    
    Returns:
        List of paper documents ready for RAG
    """
    # Check cache first
    cache_key = f"{query}_{max_papers}"
    if cache_key in paper_cache:
        print(f"Using cached papers for: {query}")
        return paper_cache[cache_key]
    
    try:
        # Search ArXiv
        results = arxiv_tool.run(query)
        
        # Simple parsing - extract papers
        papers = []
        lines = results.split('\n')
        
        current_paper = {}
        for line in lines:
            if line.startswith('Title:'):
                current_paper['title'] = line.replace('Title:', '').strip()
            elif line.startswith('Authors:'):
                current_paper['authors'] = line.replace('Authors:', '').strip()
            elif line.startswith('Summary:'):
                current_paper['summary'] = line.replace('Summary:', '').strip()
                if current_paper.get('title'):  # Only add if we have a title
                    papers.append(current_paper.copy())
                    current_paper = {}
        
        # Limit to max_papers
        papers = papers[:max_papers]
        
        # Convert to documents
        documents = []
        for i, paper in enumerate(papers):
            content = f"""Title: {paper['title']}
Authors: {paper['authors']}
Summary: {paper['summary']}"""
            
            doc = Document(
                page_content=content,
                metadata={
                    'title': paper['title'],
                    'authors': paper['authors'],
                    'source': f'arxiv_paper_{i+1}'
                }
            )
            documents.append(doc)
        
        # Cache the results
        paper_cache[cache_key] = documents
        
        print(f"Fetched {len(documents)} papers for: {query}")
        return documents
        
    except Exception as e:
        print(f"Error: {e}")
        return []

def create_dynamic_rag(query: str):
    """
    Create a dynamic RAG system that fetches papers and answers questions.
    
    Args:
        query: The research question
    
    Returns:
        Answer based on ArXiv papers
    """
    # Fetch papers
    papers = fetch_arxiv_papers(query, max_papers=2)
    
    if not papers:
        return "No papers found for this topic."
    
    # Create vector store
    vectorstore = Qdrant.from_documents(
        documents=papers,
        embedding=embedding_model,
        location=":memory:"
    )
    
    # Create retriever
    retriever = vectorstore.as_retriever()
    
    # Simple prompt
    prompt = ChatPromptTemplate.from_template("""
    Answer this question using the provided research papers:
    
    Papers: {context}
    
    Question: {question}
    
    Answer:
    """)
    
    # Create chain
    chain = (
        {"context": retriever | (lambda docs: "\n\n".join([doc.page_content for doc in docs])),
         "question": RunnablePassthrough()}
        | prompt
        | ChatOpenAI(model="gpt-4o-mini")
        | StrOutputParser()
    )
    
    return chain.invoke(query)

@tool
def dynamic_arxiv_retrieve_information(query: str) -> str:
    """
    Tool for agents to fetch ArXiv papers and get answers.
    This replaces the hard-coded retrieve_information tool.
    """
    try:
        answer = create_dynamic_rag(query)
        return answer
    except Exception as e:
        return f"Error: {str(e)}"

# Test the dynamic fetching
if __name__ == "__main__":
    print("Testing Dynamic ArXiv Paper Fetching...")
    print("=" * 50)
    
    # Test query
    test_query = "What are the latest developments in multi-agent systems?"
    print(f"Query: {test_query}")
    print("\nAnswer:")
    answer = create_dynamic_rag(test_query)
    print(answer)
    
    print("\n" + "=" * 50)
    print("SOLUTION COMPLETE!")
    print("=" * 50)
    print("""
    To use this in your multi-agent system:
    
    1. Replace this line:
       research_agent = create_agent(llm, [retrieve_information], prompt)
       
    2. With this:
       research_agent = create_agent(llm, [dynamic_arxiv_retrieve_information], prompt)
    
    That's it! Your system now fetches ArXiv papers dynamically.
    """)
