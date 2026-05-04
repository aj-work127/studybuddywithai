import os
import PyPDF2
import json
from datetime import datetime, timedelta
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain_community.vectorstores import FAISS

# Define where our vector database will live
FAISS_PATH = "data/faiss_index"

def process_and_store_document(uploaded_file, api_key):
    """Extracts text from a PDF, chunks it, and stores it in FAISS."""
    try:
        pdf_reader = PyPDF2.PdfReader(uploaded_file)
        raw_text = ""
        for page in pdf_reader.pages:
            raw_text += page.extract_text() or ""
            
        if not raw_text.strip():
            return False, "Error: The PDF appears to be empty."
    except Exception as e:
        return False, f"Error reading PDF: {e}"

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        length_function=len
    )
    chunks = text_splitter.split_text(raw_text)

    try:
        os.environ["GOOGLE_API_KEY"] = api_key
        # 🟢 UPDATED EMBEDDING MODEL
        embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")
        vectorstore = FAISS.from_texts(texts=chunks, embedding=embeddings)
        vectorstore.save_local(FAISS_PATH)
        return True, f"Success! Document converted into {len(chunks)} memory chunks."
    except Exception as e:
        return False, f"Error creating embeddings: {e}"

def ask_document(question, api_key):
    """Searches the document memory and asks Gemini to answer the question."""
    try:
        os.environ["GOOGLE_API_KEY"] = api_key
        # 🟢 UPDATED EMBEDDING MODEL
        embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")
        
        if not os.path.exists(FAISS_PATH):
            return "No document has been processed yet. Please upload and process a PDF first."
            
        vectorstore = FAISS.load_local(FAISS_PATH, embeddings, allow_dangerous_deserialization=True)
        retriever = vectorstore.as_retriever(search_kwargs={"k": 3})
        
        relevant_docs = retriever.invoke(question)
        context_text = "\n\n".join([doc.page_content for doc in relevant_docs])
        
        # 🟢 UPDATED CHAT MODEL
        llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.3)
        
        prompt = f"""
        You are a helpful, encouraging Study Buddy. 
        Use ONLY the following pieces of retrieved context from the student's textbook to answer their question. 
        If the answer is not in the context, politely say that you don't know based on the uploaded document. 
        Keep the answer concise, educational, and easy to understand.
        
        Context:
        {context_text}
        
        Student's Question: {question}
        
        Answer:
        """
        
        response = llm.invoke(prompt)
        return response.content
        
    except Exception as e:
        return f"Error generating answer: {e}"

def generate_flashcards(api_key, num_cards=5):
    """Retrieves key concepts from the document and generates flashcards."""
    try:
        os.environ["GOOGLE_API_KEY"] = api_key
        # 🟢 UPDATED EMBEDDING MODEL
        embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")
        
        if not os.path.exists(FAISS_PATH):
            return False, "No document found. Please process a PDF first."
            
        vectorstore = FAISS.load_local(FAISS_PATH, embeddings, allow_dangerous_deserialization=True)
        
        retriever = vectorstore.as_retriever(search_kwargs={"k": 10})
        relevant_docs = retriever.invoke("What are the most important key concepts, definitions, and main ideas?")
        context_text = "\n\n".join([doc.page_content for doc in relevant_docs])
        
        # 🟢 UPDATED CHAT MODEL
        llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.7)
        
        prompt = f"""
        You are an expert tutor. Based ONLY on the provided context, generate {num_cards} flashcards covering the most important concepts.
        Return the output STRICTLY as a valid JSON array of objects, exactly like this:
        [
            {{"front": "Question or term here", "back": "Answer or definition here"}}
        ]
        Do not include markdown blocks like ```json or any other text.
        
        Context:
        {context_text}
        """
        
        response = llm.invoke(prompt)
        
        clean_text = response.content.strip()
        if clean_text.startswith("```json"):
            clean_text = clean_text[7:-3]
        elif clean_text.startswith("```"):
            clean_text = clean_text[3:-3]
            
        cards = json.loads(clean_text)
        return True, cards
        
    except Exception as e:
        return False, f"Error generating flashcards: {e}"

def generate_quiz(api_key, num_questions=5):
    """Retrieves context and generates a multiple-choice quiz."""
    try:
        os.environ["GOOGLE_API_KEY"] = api_key
        # 🟢 UPDATED EMBEDDING MODEL
        embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")
        
        if not os.path.exists(FAISS_PATH):
            return False, "No document found. Please process a PDF first."
            
        vectorstore = FAISS.load_local(FAISS_PATH, embeddings, allow_dangerous_deserialization=True)
        
        retriever = vectorstore.as_retriever(search_kwargs={"k": 8})
        relevant_docs = retriever.invoke("What are the key facts, dates, definitions, and concepts?")
        context_text = "\n\n".join([doc.page_content for doc in relevant_docs])
        
        # 🟢 UPDATED CHAT MODEL
        llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.7)
        
        prompt = f"""
        You are an expert professor. Based ONLY on the provided context, create a {num_questions}-question multiple-choice quiz.
        Return the output STRICTLY as a valid JSON array of objects. 
        Do not include markdown blocks like ```json.
        
        Format exactly like this:
        [
            {{
                "question": "The question text here?",
                "options": ["Option A", "Option B", "Option C", "Option D"],
                "answer": "The exact string of the correct option",
                "explanation": "A short explanation of why this is correct."
            }}
        ]
        
        Context:
        {context_text}
        """
        
        response = llm.invoke(prompt)
        
        clean_text = response.content.strip()
        if clean_text.startswith("```json"):
            clean_text = clean_text[7:-3]
        elif clean_text.startswith("```"):
            clean_text = clean_text[3:-3]
            
        quiz_data = json.loads(clean_text)
        return True, quiz_data
        
    except Exception as e:
        return False, f"Error generating quiz: {e}"