from fastapi import FastAPI, APIRouter, HTTPException
from pydantic import BaseModel
from pymongo import MongoClient
from bson import ObjectId

# Initialize FastAPI and APIRouter
app = FastAPI()
router = APIRouter()

# Initialize MongoDB client to use the `expense` database
client = MongoClient("mongodb://localhost:27017")
db = client.expense

# Define Pydantic models
class User(BaseModel):
    username: str
    email: str
    full_name: str

class CustomerDetails(BaseModel):
    userid: str
    password: str

class SubCategory(BaseModel):
    sub_category: str
    amount_spent: int

class Category(BaseModel):
    category: str
    total_budget: int
    sub_categories: list[SubCategory]

class Month(BaseModel):
    month: str
    monthly_budget: int
    amount_spent: int
    categories: list[Category]

class Expense(BaseModel):
    months: list[Month]

# Helper function to convert ObjectId to string
def convert_object_id(data):
    if isinstance(data, list):
        for item in data:
            if '_id' in item:
                item['_id'] = str(item['_id'])
    elif '_id' in data:
        data['_id'] = str(data['_id'])
    return data

# API Endpoint for user registration
from datetime import datetime

# ... (previous imports and setup remain the same)

@router.post("/register")
async def register_user(user: User, customer_details: CustomerDetails):
    try:
        # Check if user already exists
        if db.customer_details.find_one({"userid": customer_details.userid}):
            raise HTTPException(status_code=400, detail="User already exists")
        
        # Insert user into customer_details collection
        db.customer_details.insert_one(customer_details.dict())

        # Initialize expense document with all months and default categories
        current_year = datetime.now().year
        months = ['January', 'February', 'March', 'April', 'May', 'June', 
                  'July', 'August', 'September', 'October', 'November', 'December']
        
        default_categories = [
            {
                "category": "Food",
                "total_budget": 600,
                "sub_categories": []
            },
            {
                "category": "Transportation",
                "total_budget": 300,
                "sub_categories": []
            }
        ]

        expense_data = {
            "_id": customer_details.userid,
            "months": [
                {
                    "month": f"{month}",
                    "monthly_budget": 900,  # Sum of default category budgets
                    "amount_spent": 0,
                    "categories": default_categories
                } for month in months
            ]
        }

        db.expenses.insert_one(expense_data)

        return {"message": "User registered successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# New endpoint to modify budget
@router.put("/expenses/{user_id}/modify-budget")
async def modify_budget(user_id: str, month: str, category: str, new_budget: int):
    try:
        expense = db.expenses.find_one({"_id": user_id})
        if not expense:
            raise HTTPException(status_code=404, detail="Expense not found.")

        for m in expense["months"]:
            if m["month"] == month:
                for c in m["categories"]:
                    if c["category"] == category:
                        old_budget = c["total_budget"]
                        c["total_budget"] = new_budget
                        
                        # Update monthly budget
                        m["monthly_budget"] += (new_budget - old_budget)
                        
                        db.expenses.update_one({"_id": user_id}, {"$set": {"months": expense["months"]}})
                        return {"message": f"Budget for {category} updated successfully. Monthly budget adjusted."}
                
                raise HTTPException(status_code=404, detail="Category not found.")
        
        raise HTTPException(status_code=404, detail="Month not found.")
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# ... (rest of the code remains the same)

# API Endpoint for user authentication
@router.post("/login")
async def login_user(customer_details: CustomerDetails):
    try:
        user = db.customer_details.find_one({"userid": customer_details.userid, "password": customer_details.password})
        if user:
            return {"message": "Login successful"}
        else:
            raise HTTPException(status_code=401, detail="Invalid credentials")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Create new user with initial expense data
@router.post("/expenses/{user_id}")
async def create_expense(user_id: str, expense: Expense):
    try:
        db.expenses.insert_one({"_id": user_id, **expense.dict()})
        return {"message": "Expense created successfully."}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Read entire expense for a user
@router.get("/expenses/{user_id}")
async def read_expense(user_id: str):
    try:
        expense = db.expenses.find_one({"_id": user_id})
        if expense:
            return convert_object_id(expense)
        else:
            raise HTTPException(status_code=404, detail="Expense not found.")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Read expense for a specific month for a user
@router.get("/expenses/{user_id}/month/{month}")
async def read_month_expense(user_id: str, month: str):
    try:
        expense = db.expenses.find_one({"_id": user_id})
        if expense:
            for m in expense["months"]:
                if m["month"] == month:
                    return m
            raise HTTPException(status_code=404, detail="Month not found.")
        else:
            raise HTTPException(status_code=404, detail="Expense not found.")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Update user expense
@router.put("/expenses/{user_id}")
async def update_expense(user_id: str, expense: Expense):
    try:
        db.expenses.update_one({"_id": user_id}, {"$set": expense.dict()})
        return {"message": "Expense updated successfully."}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# Update subcategory
@router.put("/expenses/{user_id}/month/{month}/category/{category}/subcategory/{sub_category}")
async def update_subcategory(user_id: str, month: str, category: str, sub_category: str, amount_spent: int):
    try:
        expense = db.expenses.find_one({"_id": user_id})
        if expense:
            for m in expense["months"]:
                if m["month"] == month:
                    for c in m["categories"]:
                        if c["category"] == category:
                            for sc in c["sub_categories"]:
                                if sc["sub_category"] == sub_category:
                                    sc["amount_spent"] = amount_spent
                                    db.expenses.update_one({"_id": user_id}, {"$set": {"months": expense["months"]}})
                                    return {"message": "Subcategory updated successfully."}
            raise HTTPException(status_code=404, detail="Month, category, or subcategory not found.")
        else:
            raise HTTPException(status_code=404, detail="Expense not found.")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

from fastapi import FastAPI, APIRouter, HTTPException
from pydantic import BaseModel
from pymongo import MongoClient
from bson import ObjectId


# Add this function to calculate total spent
def calculate_total_spent(categories):
    return sum(
        subcategory['amount_spent']
        for category in categories
        for subcategory in category.get('sub_categories', [])
    )

# Modify your add_subcategory route
@router.post("/expenses/{user_id}/month/{month}/category/{category}")
async def add_subcategory(user_id: str, month: str, category: str, subcategory: SubCategory):
    try:
        expense = db.expenses.find_one({"_id": user_id})
        if not expense:
            raise HTTPException(status_code=404, detail="Expense not found.")

        for m in expense["months"]:
            if m["month"] == month:
                for c in m["categories"]:
                    if c["category"] == category:
                        current_spent = sum(sub['amount_spent'] for sub in c["sub_categories"])
                        remaining_budget = c["total_budget"] - current_spent
                        if subcategory.amount_spent > remaining_budget:
                            raise HTTPException(status_code=400, detail=f"Expense exceeds remaining budget. Remaining budget: ${remaining_budget}")
                        
                        c["sub_categories"].append(subcategory.dict())
                        m["amount_spent"] = calculate_total_spent(m["categories"])
                        db.expenses.update_one({"_id": user_id}, {"$set": {"months": expense["months"]}})
                        return {"message": "Subcategory added successfully and total amount updated."}
                
                raise HTTPException(status_code=404, detail="Category not found.")
        
        raise HTTPException(status_code=404, detail="Month not found.")
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    
# Similarly, update the delete_subcategory route
@router.delete("/expenses/{user_id}/month/{month}/category/{category}/subcategory/{sub_category}")
async def delete_subcategory(user_id: str, month: str, category: str, sub_category: str):
    try:
        expense = db.expenses.find_one({"_id": user_id})
        if expense:
            for m in expense["months"]:
                if m["month"] == month:
                    for c in m["categories"]:
                        if c["category"] == category:
                            c["sub_categories"] = [sc for sc in c["sub_categories"] if sc["sub_category"] != sub_category]
                            
                            # Recalculate the total amount spent for the month
                            m["amount_spent"] = calculate_total_spent(m["categories"])
                            
                            db.expenses.update_one({"_id": user_id}, {"$set": {"months": expense["months"]}})
                            return {"message": "Subcategory deleted successfully and total amount updated."}
            raise HTTPException(status_code=404, detail="Month, category, or subcategory not found.")
        else:
            raise HTTPException(status_code=404, detail="Expense not found.")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Update the add_category route to initialize amount_spent
@router.post("/expenses/{user_id}/month/{month}")
async def add_category(user_id: str, month: str, category: Category):
    try:
        expense = db.expenses.find_one({"_id": user_id})
        if expense:
            for m in expense["months"]:
                if m["month"] == month:
                    m["categories"].append(category.dict())
                    # Recalculate the total amount spent for the month
                    m["amount_spent"] = calculate_total_spent(m["categories"])
                    db.expenses.update_one({"_id": user_id}, {"$set": {"months": expense["months"]}})
                    return {"message": "Category added successfully and total amount updated."}
            raise HTTPException(status_code=404, detail="Month not found.")
        else:
            raise HTTPException(status_code=404, detail="Expense not found.")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Update the delete_category route
@router.delete("/expenses/{user_id}/month/{month}/category/{category}")
async def delete_category(user_id: str, month: str, category: str):
    try:
        expense = db.expenses.find_one({"_id": user_id})
        if expense:
            for m in expense["months"]:
                if m["month"] == month:
                    m["categories"] = [c for c in m["categories"] if c["category"] != category]
                    # Recalculate the total amount spent for the month
                    m["amount_spent"] = calculate_total_spent(m["categories"])
                    db.expenses.update_one({"_id": user_id}, {"$set": {"months": expense["months"]}})
                    return {"message": "Category deleted successfully and total amount updated."}
            raise HTTPException(status_code=404, detail="Month or category not found.")
        else:
            raise HTTPException(status_code=404, detail="Expense not found.")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    
@router.get("/leaderboard")
async def leaderboard(month: str):
    try:
        users = db.customer_details.find({})
        leaderboard = []
        for user in users:
            userid = user["userid"]
            expenses = db.expenses.find_one({"_id": userid})
            if expenses:
                for m in expenses["months"]:
                    if m["month"] == month:
                        total_savings = m["monthly_budget"] - m["amount_spent"]
                        leaderboard.append({"userid": userid, "total_savings": total_savings})
                        break
        leaderboard = sorted(leaderboard, key=lambda x: x["total_savings"], reverse=True)
        return leaderboard
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

app.include_router(router)
