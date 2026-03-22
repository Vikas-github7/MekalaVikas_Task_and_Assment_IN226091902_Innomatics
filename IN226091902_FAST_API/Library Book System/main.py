from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Optional
import math

app = FastAPI()

# -------------------------------------------------------------------
#  Initial Data Setup
# -------------------------------------------------------------------

books = [
    {"id": 1, "title": "The Great Gatsby", "author": "F. Scott Fitzgerald", "genre": "Fiction", "is_available": True},
    {"id": 2, "title": "A Brief History of Time", "author": "Stephen Hawking", "genre": "Science", "is_available": True},
    {"id": 3, "title": "1984", "author": "George Orwell", "genre": "Fiction", "is_available": False},
    {"id": 4, "title": "Sapiens", "author": "Yuval Noah Harari", "genre": "History", "is_available": True},
    {"id": 5, "title": "Clean Code", "author": "Robert C. Martin", "genre": "Tech", "is_available": True},
    {"id": 6, "title": "Dune", "author": "Frank Herbert", "genre": "Fiction", "is_available": False}
]

borrow_records = []
record_counter = 1
queue = []

# -------------------------------------------------------------------
#  Helper Functions & Pydantic Models
# -------------------------------------------------------------------

# Q7 
def find_book(book_id: int):
    for book in books:
        if book["id"] == book_id:
            return book
    return None

def calculate_due_date(borrow_days: int, member_type: str = "regular"):
    max_days = 60 if member_type.lower() == "premium" else 30
    actual_days = min(borrow_days, max_days)
    return f"Return by: Day {15 + actual_days}"

def filter_books_logic(genre: Optional[str], author: Optional[str], is_available: Optional[bool]):
    filtered = books
    if genre is not None:
        filtered = [b for b in filtered if b["genre"].lower() == genre.lower()]
    if author is not None:
        filtered = [b for b in filtered if author.lower() in b["author"].lower()]
    if is_available is not None:
        filtered = [b for b in filtered if b["is_available"] == is_available]
    return filtered

class BorrowRequest(BaseModel):
    member_name: str = Field(..., min_length=2)
    book_id: int = Field(..., gt=0)
    borrow_days: int = Field(..., gt=0, le=60) 
    member_id: str = Field(..., min_length=4)
    member_type: str = Field(default="regular")

class NewBook(BaseModel):
    title: str = Field(..., min_length=2)
    author: str = Field(..., min_length=2)
    genre: str = Field(..., min_length=2)
    is_available: bool = Field(default=True)

# -------------------------------------------------------------------
# ROUTES 
# -------------------------------------------------------------------

# Q1: Home Route
@app.get("/")
def read_root():
    return {"message": "Welcome to City Public Library"}

# -------------------------------------------------------------------
# FIXED GET ROUTES (Must be above variable routes like /books/{book_id})
# -------------------------------------------------------------------

# Q5: Books Summary
@app.get("/books/summary")
def get_books_summary():
    total = len(books)
    available = sum(1 for b in books if b["is_available"])
    borrowed = total - available
    genres = {}
    for b in books:
        genres[b["genre"]] = genres.get(b["genre"], 0) + 1
    return {
        "total_books": total, 
        "available_count": available, 
        "borrowed_count": borrowed, 
        "genre_breakdown": genres
    }

# Q10: Filter Books
@app.get("/books/filter")
def filter_books(genre: Optional[str] = None, author: Optional[str] = None, is_available: Optional[bool] = None):
    results = filter_books_logic(genre, author, is_available)
    return {"total_found": len(results), "books": results}

# Q16: Search Books
@app.get("/books/search")
def search_books(keyword: str = Query(...)):
    results = [b for b in books if keyword.lower() in b["title"].lower() or keyword.lower() in b["author"].lower()]
    if not results:
        return {"message": "No books found matching your keyword.", "total_found": 0, "books": []}
    return {"total_found": len(results), "books": results}

# Q17: Sort Books
@app.get("/books/sort")
def sort_books(sort_by: str = Query("title"), order: str = Query("asc")):
    valid_sorts = ["title", "author", "genre"]
    if sort_by not in valid_sorts:
        raise HTTPException(status_code=400, detail=f"Invalid sort_by. Allowed: {valid_sorts}")
    if order not in ["asc", "desc"]:
        raise HTTPException(status_code=400, detail="Invalid order. Allowed: asc, desc")

    sorted_books = sorted(books, key=lambda x: x[sort_by], reverse=(order == "desc"))
    return {"sort_by": sort_by, "order": order, "books": sorted_books}

# Q18: Paginate Books
@app.get("/books/page")
def paginate_books(page: int = Query(1, ge=1), limit: int = Query(3, ge=1, le=10)):
    total = len(books)
    total_pages = math.ceil(total / limit)
    start = (page - 1) * limit
    sliced = books[start:start+limit]
    return {"total": total, "total_pages": total_pages, "page": page, "limit": limit, "books": sliced}

# Q20: Combined Browse Endpoint
@app.get("/books/browse")
def browse_books(
    keyword: Optional[str] = None,
    sort_by: str = Query("title"),
    order: str = Query("asc"),
    page: int = Query(1, ge=1),
    limit: int = Query(3, ge=1)
):
    results = books
    if keyword:
        results = [b for b in results if keyword.lower() in b["title"].lower() or keyword.lower() in b["author"].lower()]

    valid_sorts = ["title", "author", "genre"]
    if sort_by not in valid_sorts:
        raise HTTPException(status_code=400, detail="Invalid sort_by")
    results = sorted(results, key=lambda x: x[sort_by], reverse=(order == "desc"))

    total = len(results)
    total_pages = math.ceil(total / limit) if total > 0 else 0
    start = (page - 1) * limit
    paginated_results = results[start:start+limit]

    return {
        "keyword_used": keyword,
        "sort_settings": {"sort_by": sort_by, "order": order},
        "pagination": {"page": page, "limit": limit, "total_found": total, "total_pages": total_pages},
        "results": paginated_results
    }

# Q19: Search and Paginate Borrow Records
@app.get("/borrow-records/search")
def search_records(member_name: str = Query(...)):
    results = [r for r in borrow_records if member_name.lower() in r["member_name"].lower()]
    return {"total_found": len(results), "records": results}

@app.get("/borrow-records/page")
def paginate_records(page: int = Query(1, ge=1), limit: int = Query(3, ge=1)):
    total = len(borrow_records)
    total_pages = math.ceil(total / limit)
    start = (page - 1) * limit
    sliced = borrow_records[start:start+limit]
    return {"total": total, "total_pages": total_pages, "page": page, "limit": limit, "records": sliced}

# -------------------------------------------------------------------
# BASE GET ROUTES
# -------------------------------------------------------------------

# Q2: Get All Books
@app.get("/books")
def get_books():
    available = sum(1 for b in books if b["is_available"])
    return {"total": len(books), "available_count": available, "books": books}

# Q4: Get All Borrow Records
@app.get("/borrow-records")
def get_borrow_records():
    return {"total": len(borrow_records), "records": borrow_records}

# Q14b: View Queue
@app.get("/queue")
def get_queue():
    return {"total_in_queue": len(queue), "queue": queue}

# -------------------------------------------------------------------
# VARIABLE / ID ROUTES
# -------------------------------------------------------------------

# Q3: Get Book By ID
@app.get("/books/{book_id}")
def get_book_by_id(book_id: int):
    book = find_book(book_id)
    if book is None:
        return {"error": "Book not found"}
    return book

# -------------------------------------------------------------------
# POST / PUT / DELETE ROUTES
# -------------------------------------------------------------------

# Q11: Add a Book
@app.post("/books", status_code=201)
def add_book(new_book: NewBook):
    if any(b["title"].lower() == new_book.title.lower() for b in books):
        raise HTTPException(status_code=400, detail="Book with this title already exists")
    new_id = max((b["id"] for b in books), default=0) + 1
    book_dict = new_book.model_dump()
    book_dict["id"] = new_id
    books.append(book_dict)
    return book_dict

# Q12: Update a Book
@app.put("/books/{book_id}")
def update_book(book_id: int, genre: Optional[str] = None, is_available: Optional[bool] = None):
    book = find_book(book_id)
    if book is None:
        raise HTTPException(status_code=404, detail="Book not found")
    if genre is not None:
        book["genre"] = genre
    if is_available is not None:
        book["is_available"] = is_available
    return book

# Q13: Delete a Book
@app.delete("/books/{book_id}")
def delete_book(book_id: int):
    book = find_book(book_id)
    if book is None:
        raise HTTPException(status_code=404, detail="Book not found")
    books.remove(book)
    return {"message": "Success", "deleted_title": book["title"]}

# Q8 & Q9: Borrow a Book
@app.post("/borrow")
def borrow_book(request: BorrowRequest):
    global record_counter
    book = find_book(request.book_id)
    
    if book is None:
        raise HTTPException(status_code=404, detail="Book not found")
    if not book["is_available"]:
        raise HTTPException(status_code=400, detail="Book is already borrowed")

    book["is_available"] = False
    due_date_msg = calculate_due_date(request.borrow_days, request.member_type)

    record = {
        "record_id": record_counter,
        "member_name": request.member_name,
        "member_id": request.member_id,
        "book_id": request.book_id,
        "member_type": request.member_type,
        "due_date": due_date_msg
    }
    borrow_records.append(record)
    record_counter += 1
    return {"status": "confirmed", "record": record}

# Q14a: Add to Queue
@app.post("/queue/add")
def add_to_queue(member_name: str, book_id: int):
    book = find_book(book_id)
    if book is None:
        raise HTTPException(status_code=404, detail="Book not found")
    if book["is_available"]:
        raise HTTPException(status_code=400, detail="Book is currently available, borrow it directly")

    queue_item = {"member_name": member_name, "book_id": book_id}
    queue.append(queue_item)
    return {"message": "Added to waitlist", "queue_position": len(queue), "entry": queue_item}

# Q15: Return a Book
@app.post("/return/{book_id}")
def return_book(book_id: int):
    global record_counter
    book = find_book(book_id)
    
    if book is None:
        raise HTTPException(status_code=404, detail="Book not found")

    book["is_available"] = True

    for i, q_item in enumerate(queue): 
        if q_item["book_id"] == book_id:
            book["is_available"] = False
            due_date_msg = calculate_due_date(15, "regular") 
            
            record = {
                "record_id": record_counter,
                "member_name": q_item["member_name"],
                "book_id": book_id,
                "member_type": "regular",
                "due_date": due_date_msg
            }
            borrow_records.append(record)
            record_counter += 1
            queue.pop(i)
            return {"message": "returned and re-assigned", "new_borrow_record": record}

    return {"message": "returned and available"}