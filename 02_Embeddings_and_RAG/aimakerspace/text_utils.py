import os
from typing import List, Dict, Any, Tuple
import PyPDF2
from datetime import datetime


class TextFileLoader:
    def __init__(self, path: str, encoding: str = "utf-8"):
        self.documents = []
        self.metadata = []
        self.path = path
        self.encoding = encoding

    def load(self):
        if os.path.isdir(self.path):
            self.load_directory()
        elif os.path.isfile(self.path):
            if self.path.endswith(".txt"):
                self.load_file()
            elif self.path.endswith(".pdf"):
                self.load_pdf()
            else:
                raise ValueError(
                    "Unsupported file type. Only .txt and .pdf files are supported."
                )
        else:
            raise ValueError(
                "Provided path is neither a valid directory nor a supported file."
            )

    def load_file(self):
        with open(self.path, "r", encoding=self.encoding) as f:
            content = f.read()
            self.documents.append(content)
            self.metadata.append({
                "source": self.path,
                "file_type": "txt",
                "file_size": os.path.getsize(self.path),
                "created_at": datetime.now().isoformat()
            })

    def load_pdf(self):
        try:
            with open(self.path, "rb") as file:
                pdf_reader = PyPDF2.PdfReader(file)
                content = ""
                for page_num, page in enumerate(pdf_reader.pages):
                    content += page.extract_text() + "\n"
                
                self.documents.append(content)
                self.metadata.append({
                    "source": self.path,
                    "file_type": "pdf",
                    "file_size": os.path.getsize(self.path),
                    "page_count": len(pdf_reader.pages),
                    "created_at": datetime.now().isoformat()
                })
        except Exception as e:
            raise ValueError(f"Error reading PDF file: {str(e)}")

    def load_directory(self):
        for root, _, files in os.walk(self.path):
            for file in files:
                file_path = os.path.join(root, file)
                if file.endswith(".txt"):
                    with open(file_path, "r", encoding=self.encoding) as f:
                        content = f.read()
                        self.documents.append(content)
                        self.metadata.append({
                            "source": file_path,
                            "file_type": "txt",
                            "file_size": os.path.getsize(file_path),
                            "created_at": datetime.now().isoformat()
                        })
                elif file.endswith(".pdf"):
                    try:
                        with open(file_path, "rb") as pdf_file:
                            pdf_reader = PyPDF2.PdfReader(pdf_file)
                            content = ""
                            for page in pdf_reader.pages:
                                content += page.extract_text() + "\n"
                            
                            self.documents.append(content)
                            self.metadata.append({
                                "source": file_path,
                                "file_type": "pdf",
                                "file_size": os.path.getsize(file_path),
                                "page_count": len(pdf_reader.pages),
                                "created_at": datetime.now().isoformat()
                            })
                    except Exception as e:
                        print(f"Warning: Could not process PDF {file_path}: {str(e)}")

    def load_documents(self):
        self.load()
        return self.documents
    
    def load_documents_with_metadata(self) -> Tuple[List[str], List[Dict[str, Any]]]:
        """Load documents and return both content and metadata"""
        self.load()
        return self.documents, self.metadata


class CharacterTextSplitter:
    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
    ):
        assert (
            chunk_size > chunk_overlap
        ), "Chunk size must be greater than chunk overlap"

        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def split(self, text: str) -> List[str]:
        chunks = []
        for i in range(0, len(text), self.chunk_size - self.chunk_overlap):
            chunks.append(text[i : i + self.chunk_size])
        return chunks

    def split_texts(self, texts: List[str]) -> List[str]:
        chunks = []
        for text in texts:
            chunks.extend(self.split(text))
        return chunks
    
    def split_texts_with_metadata(self, texts: List[str], metadata: List[Dict[str, Any]]) -> Tuple[List[str], List[Dict[str, Any]]]:
        """Split texts while preserving metadata for each chunk"""
        chunks = []
        chunk_metadata = []
        
        for text, meta in zip(texts, metadata):
            text_chunks = self.split(text)
            chunks.extend(text_chunks)
            
            # Create metadata for each chunk
            for i, chunk in enumerate(text_chunks):
                chunk_meta = meta.copy()
                chunk_meta.update({
                    "chunk_index": i,
                    "total_chunks": len(text_chunks),
                    "chunk_size": len(chunk)
                })
                chunk_metadata.append(chunk_meta)
        
        return chunks, chunk_metadata


if __name__ == "__main__":
    loader = TextFileLoader("data/KingLear.txt")
    loader.load()
    splitter = CharacterTextSplitter()
    chunks = splitter.split_texts(loader.documents)
    print(len(chunks))
    print(chunks[0])
    print("--------")
    print(chunks[1])
    print("--------")
    print(chunks[-2])
    print("--------")
    print(chunks[-1])
