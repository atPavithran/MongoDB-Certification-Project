import streamlit as st
import requests
import pandas as pd
from datetime import datetime

BASE_URL = "http://127.0.0.1:8000"

def main():
    st.title("Gamified Expense Tracker")

    page = st.sidebar.selectbox("Choose a page", ["Login", "Register", "Dashboard", "Leaderboard"])

    if page == "Login":
        login_page()
    elif page == "Register":
        register_page()
    elif page == "Dashboard":
        dashboard_page()

    elif page == "Leaderboard":
        leaderboard_page()

def login_page():
    st.header("Login")
    userid = st.text_input("User ID")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        response = requests.post(f"{BASE_URL}/login", json={"userid": userid, "password": password})
        if response.status_code == 200:
            st.success("Login successful!")
            st.session_state.user_id = userid
        else:
            st.error("Invalid credentials")

def register_page():
    st.header("Register")
    username = st.text_input("Username")
    email = st.text_input("Email")
    full_name = st.text_input("Full Name")
    userid = st.text_input("User ID")
    password = st.text_input("Password", type="password")
    if st.button("Register"):
        user_data = {"username": username, "email": email, "full_name": full_name}
        customer_details = {"userid": userid, "password": password}
        response = requests.post(f"{BASE_URL}/register", json={"user": user_data, "customer_details": customer_details})
        if response.status_code == 200:
            st.success("Registration successful!")
        else:
            st.error("Registration failed")
def add_category(user_id, month, new_category, total_budget):
    category_data = {
        "category": new_category,
        "total_budget": total_budget,
        "sub_categories": []
    }
    response = requests.post(f"{BASE_URL}/expenses/{user_id}/month/{month}", json=category_data)
    if response.status_code == 200:
        st.success("Expense added successfully!")
    else:
        st.error("Failed to add category")

def add_subcategory(user_id, month, category, new_subcategory, amount_spent):
    subcategory_data = {
        "sub_category": new_subcategory,
        "amount_spent": amount_spent
    }
    response = requests.post(f"{BASE_URL}/expenses/{user_id}/month/{month}/category/{category}", json=subcategory_data)
    if response.status_code == 200:
        st.success("Expense added successfully!")
    elif response.status_code == 400:
        st.error("Failed to add Expense: Budget exceeded")
    else:
        st.error("Failed to add Expense")

def modify_budget(user_id, month, category, new_budget):
    response = requests.put(f"{BASE_URL}/expenses/{user_id}/modify-budget", 
                            params={"month": month, "category": category, "new_budget": new_budget})
    if response.status_code == 200:
        st.success("Budget modified successfully!")
        return True
    else:
        st.error("Failed to modify budget")
        return False

def get_previous_month(current_month):
    months = ['January', 'February', 'March', 'April', 'May', 'June', 
              'July', 'August', 'September', 'October', 'November', 'December']
    current_index = months.index(current_month)
    previous_index = (current_index - 1) % 12
    return months[previous_index]

def display_expenses(expenses, user_id):
    months = expenses.get("months", [])
    if not months:
        st.write("No expenses found for the user.")
        return

    current_month = datetime.now().strftime("%B")
    selected_month = st.selectbox("Select Month", [month['month'] for month in months], 
                                  index=[month['month'] for month in months].index(current_month) 
                                  if current_month in [month['month'] for month in months] else 0)

    # Analysis section
    st.subheader("Monthly Spending Analysis")
    current_month_data = next((month for month in months if month['month'] == selected_month), None)
    previous_month = get_previous_month(selected_month)
    previous_month_data = next((month for month in months if month['month'] == previous_month), None)

    if current_month_data and previous_month_data:
        current_spent = current_month_data.get('amount_spent', 0)
        previous_spent = previous_month_data.get('amount_spent', 0)
        difference = previous_spent - current_spent

        col1, col2 = st.columns(2)
        with col1:
            st.metric(label=f"{selected_month} Spending", value=f"${current_spent:,.2f}")
        with col2:
            st.metric(label=f"{previous_month} Spending", value=f"${previous_spent:,.2f}", delta=f"${difference:,.2f}")

        if difference > 0:
            st.success(f"🎉 Congratulations! You've saved ${difference:,.2f} compared to last month.")
        elif difference < 0:
            st.error(f"💡 You've spent ${-difference:,.2f} more than last month. Try to cut back on expenses!")
        else:
            st.info("Your spending is consistent with last month.")

    # Original display_expenses content
    for month in months:
        if month['month'] == selected_month:
            st.write(f"Monthly Budget: ${month.get('monthly_budget', 'N/A')}")
            st.write(f"Amount Spent: ${month.get('amount_spent', 'N/A')}")
            
            categories = month.get("categories", [])
            if not categories:
                st.write("No categories found for this month.")
                continue

            selected_category = st.selectbox("Select Category", [category['category'] for category in categories])

            for category in categories:
                if category['category'] == selected_category:
                    total_budget = category.get('total_budget', 0)
                    st.write(f"Total Budget: ${total_budget}")
                    
                    new_budget = st.number_input(f"Modify budget for {selected_category}", 
                                                 value=float(total_budget), 
                                                 min_value=0.0, 
                                                 format="%.2f")
                    if st.button("Update Budget", key=f"update_budget_{selected_category}"):
                        if modify_budget(user_id, selected_month, selected_category, int(new_budget)):
                            st.experimental_rerun()
                    
                    subcategories = category.get("sub_categories", [])
                    current_spent = sum(sub['amount_spent'] for sub in subcategories)
                    st.write(f"Current Spent: ${current_spent}")
                    st.write(f"Remaining Budget: ${max(total_budget - current_spent, 0)}")

                    if not subcategories:
                        st.write("No Expense found for this category.")
                    else:
                        for subcategory in subcategories:
                            col1, col2, col3 = st.columns([3, 1, 1])
                            with col1:
                                st.write(f"Expense: {subcategory.get('sub_category', 'Unknown')}")
                            with col2:
                                st.write(f"Amount: ${subcategory.get('amount_spent', 'N/A')}")
                            with col3:
                                if st.button("Delete", key=f"del_sub_{subcategory.get('sub_category', '')}_{selected_month}_{selected_category}"):
                                    delete_subcategory(user_id, selected_month, selected_category, subcategory.get('sub_category', ''))

                    if st.button("Delete Category", key=f"del_cat_{selected_category}_{selected_month}"):
                        delete_category(user_id, selected_month, selected_category)
                    
                    if current_spent < total_budget:
                        new_subcategory = st.text_input(f"New Expense for {selected_category}")
                        amount_spent = st.number_input(f"Amount Spent for {new_subcategory}", min_value=0.0, max_value=float(total_budget - current_spent), format="%.2f")
                        if st.button("Add Expense", key=f"add_sub_{selected_category}_{selected_month}"):
                            add_subcategory(user_id, selected_month, selected_category, new_subcategory, amount_spent)
                    else:
                        st.warning("Category budget is fully spent. Cannot add more expenses.")

            new_category = st.text_input(f"New Category for {selected_month}")
            new_category_budget = st.number_input(f"Budget for {new_category}", min_value=0.0, format="%.2f")
            if st.button("Add Category", key=f"add_cat_{selected_month}"):
                add_category(user_id, selected_month, new_category, new_category_budget)

def dashboard_page():
    if "user_id" not in st.session_state:
        st.warning("Please login first")
        return

    st.header("Dashboard")
    user_id = st.session_state.user_id
    response = requests.get(f"{BASE_URL}/expenses/{user_id}")
    if response.status_code == 200:
        expenses = response.json()
        display_expenses(expenses, user_id)
    else:
        st.error("Failed to fetch expenses")


def delete_category(user_id, month, category):
    response = requests.delete(f"{BASE_URL}/expenses/{user_id}/month/{month}/category/{category}")
    if response.status_code == 200:
        st.success("Category deleted successfully!")
    else:
        st.error("Failed to delete category")

def delete_subcategory(user_id, month, category, sub_category):
    response = requests.delete(f"{BASE_URL}/expenses/{user_id}/month/{month}/category/{category}/subcategory/{sub_category}")
    if response.status_code == 200:
        st.success("Subcategory deleted successfully!")
    else:
        st.error("Failed to delete subcategory")



def leaderboard_page():
    st.header("Leaderboard")
    months = ['January', 'February', 'March', 'April', 'May', 'June', 
              'July', 'August', 'September', 'October', 'November', 'December']
    selected_month = st.selectbox("Select Month", months)
    
    response = requests.get(f"{BASE_URL}/leaderboard", params={"month": selected_month})
    if response.status_code == 200:
        leaderboard_data = response.json()
        display_leaderboard(leaderboard_data)
    else:
        st.warning(f"Leaderboard data for {selected_month} is not available.")


def display_leaderboard(leaderboard_data):
    st.subheader("Top Savers")

    df = pd.DataFrame(leaderboard_data)
    df['Rank'] = range(1, len(df) + 1)
    df = df[['Rank', 'userid', 'total_savings']]
    df.columns = ['Rank', 'User ID', 'Total Savings ($)']

    df['Total Savings ($)'] = df['Total Savings ($)'].apply(lambda x: f"${x:,.2f}")

   

    st.table(df)

    if len(df) >= 3:
        st.markdown("🥇 **First Place**")
        st.info(f"Congratulations to {df.iloc[0]['User ID']} for saving {df.iloc[0]['Total Savings ($)']}!")
        
        st.markdown("🥈 **Second Place**")
        st.success(f"Great job, {df.iloc[1]['User ID']}! You saved {df.iloc[1]['Total Savings ($)']}.")
        
        st.markdown("🥉 **Third Place**")
        st.warning(f"Well done, {df.iloc[2]['User ID']}! You saved {df.iloc[2]['Total Savings ($)']}.")

    st.markdown("---")
    st.markdown("Keep saving and climb the ranks! 💪💰")

if __name__ == "__main__":
    main()
