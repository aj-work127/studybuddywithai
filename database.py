import sqlite3
import os

DB_PATH = "data/study_buddy.db"

def init_db():
    # Ensure the data directory exists
    os.makedirs("data", exist_ok=True)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 1. Create Tables
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Users (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Documents (
            doc_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            filename TEXT,
            upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES Users(user_id)
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Flashcards (
            card_id INTEGER PRIMARY KEY AUTOINCREMENT,
            topic TEXT,
            front_text TEXT,
            back_text TEXT,
            next_review_date DATE
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS QuizScores (
            score_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            topic TEXT,
            score INTEGER,
            total_questions INTEGER,
            date_taken TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES Users(user_id)
        )
    ''')

    # 2. Inject Mock Data (Only if the tables are empty)
    cursor.execute("SELECT COUNT(*) FROM Users")
    if cursor.fetchone()[0] == 0:
        print("Initializing mock data...")
        
        # Add a default user
        cursor.execute("INSERT INTO Users (username) VALUES ('test_student')")
        
        # Mock Flashcards (AI, Cybersec, DAA)
        mock_flashcards = [
            ("Artificial Intelligence", "What is the difference between supervised and unsupervised learning?", "Supervised learning uses labeled data to train algorithms, while unsupervised learning uses unlabeled data to find hidden patterns.", "2024-05-01"),
            ("Cybersecurity", "What does CIA stand for in the CIA Triad?", "Confidentiality, Integrity, and Availability.", "2024-05-01"),
            ("Cybersecurity", "What is a SQL Injection (SQLi)?", "A code injection technique that might destroy your database by inserting malicious SQL statements into entry fields for execution.", "2024-05-02"),
            ("DAA", "What is the Time Complexity of Merge Sort?", "O(n log n) in the best, average, and worst cases.", "2024-05-01"),
            ("DAA", "Explain the core concept of Dynamic Programming.", "It is a method for solving complex problems by breaking them down into simpler overlapping subproblems and storing the results of subproblems to avoid redundant computations.", "2024-05-03")
        ]
        cursor.executemany('''
            INSERT INTO Flashcards (topic, front_text, back_text, next_review_date) 
            VALUES (?, ?, ?, ?)
        ''', mock_flashcards)

        conn.commit()
    
    conn.close()

if __name__ == "__main__":
    init_db()
    print("Database initialized successfully at", DB_PATH)