import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
from fpdf import FPDF

# Page config
st.set_page_config(page_title="Expense Tracker", layout="wide")
st.title("My Expense Tracker")
st.markdown("Add, Track & Visualize your expenses!")

# File for saving data
DATA_FILE = "expenses.csv"

# Load data
def load_data():
    try:
        df = pd.read_csv(DATA_FILE)
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce', format='mixed')
        df = df.dropna(subset=['Date'])
        return df
    except FileNotFoundError:
        return pd.DataFrame(columns=['Date', 'Category', 'Description', 'Amount'])

df = load_data()

# Sidebar - Add Expense
with st.sidebar.form("expense_form", clear_on_submit=True):
    st.header("Add Expense")

    date = st.date_input("Date", datetime.today())
    category = st.selectbox(
        "Category",
        ["Food", "Travel", "Study", "Entertainment", "Transport", "Bills", "Others"]
    )
    description = st.text_input("Description")
    amount = st.number_input("Amount (NPR)", min_value=0.0, step=10.0)

    submitted = st.form_submit_button("Add Expense")

    if submitted and amount > 0:
        new_row = pd.DataFrame({
            'Date': [pd.to_datetime(date)],
            'Category': [category],
            'Description': [description],
            'Amount': [amount]
        })

        df = pd.concat([df, new_row], ignore_index=True)
        df.to_csv(DATA_FILE, index=False)

        st.success("Expense added successfully!")
        st.rerun()

# Main Area
st.subheader("All Expenses")

if not df.empty:

    # Filters
  
    col1, col2 = st.columns(2)

    with col1:
        min_date = st.date_input("From", df['Date'].min(), key="min_date")

    with col2:
        max_date = st.date_input("To", df['Date'].max(), key="max_date")

    mask = (df['Date'].dt.date >= min_date) & (df['Date'].dt.date <= max_date)
    filtered_df = df.loc[mask].copy()

    # Table & Metrics
    st.dataframe(
        filtered_df.sort_values(by='Date', ascending=False),
        use_container_width=True
    )
    
    st.subheader("Edit Expense")

if not df.empty:
    selected_id = st.selectbox(
        "Select row to edit",
        df.index.tolist()
    )

    selected_row = df.loc[selected_id]

    with st.form("edit_form"):
        new_date = st.date_input("Date", selected_row["Date"])
        new_category = st.selectbox(
            "Category",
            ["Food", "Travel", "Study", "Entertainment", "Transport", "Bills", "Others"],
            index=["Food", "Travel", "Study", "Entertainment", "Transport", "Bills", "Others"].index(selected_row["Category"])
        )
        new_description = st.text_input("Description", selected_row["Description"])
        new_amount = st.number_input("Amount", value=float(selected_row["Amount"]))

        update = st.form_submit_button("Update")

        if update:
            df.at[selected_id, "Date"] = new_date
            df.at[selected_id, "Category"] = new_category
            df.at[selected_id, "Description"] = new_description
            df.at[selected_id, "Amount"] = new_amount

            df.to_csv(DATA_FILE, index=False)
            st.success("Expense updated successfully!")
            st.rerun()
            
    st.subheader("Delete Expense")

if not df.empty:
    delete_id = st.selectbox(
        "Select row to delete",
        df.index.tolist(),
        key="delete_select"
    )

    if st.button("Delete Expense"):
        df = df.drop(delete_id)

        df.to_csv(DATA_FILE, index=False)
        st.success("Expense deleted successfully!")
        st.rerun()

    total = filtered_df['Amount'].sum()
    st.metric("Total Expenses", f"NPR {total:,.2f}")

    st.markdown("Expense Dashboard")

    filtered_df['Month'] = filtered_df['Date'].dt.strftime('%b %Y')
    filtered_df['Day'] = filtered_df['Date'].dt.date
    filtered_df = filtered_df.sort_values('Date')

    # Row 1
    col1, col2 = st.columns(2)

    # Monthly Trend
    with col1:
        st.subheader("Monthly Spending")
        # Create Month column properly
        filtered_df['Month'] = filtered_df['Date'].dt.to_period('M').astype(str)
        
        # Group by month and sum amount
        monthly = filtered_df.groupby('Month')['Amount'].sum().reset_index()
        monthly = monthly.sort_values('Month')   # Sort chronologically
        
        # BAR CHART 
        fig_month = px.bar(
            monthly, 
            x='Month', 
            y='Amount',
            title="Monthly Expenses",
            labels={'Amount': 'Amount (NPR)', 'Month': 'Month'},
            color_discrete_sequence=['#00cc96'],   # Nice green color
            text_auto=True   # Shows value on top of each bar
        )
        
        # Improve layout
        fig_month.update_layout(
            xaxis_title="Month",
            yaxis_title="Total Amount (NPR)",
            plot_bgcolor="rgba(0,0,0,0)",
            bargap=0.2,
            height=450
        )
        
        st.plotly_chart(fig_month, use_container_width=True)

    # Category Pie
    with col2:
        st.subheader("Category Distribution")
        category_total = filtered_df.groupby('Category')['Amount'].sum().reset_index()

        fig_cat = px.pie(
            category_total, 
            names='Category', 
            values='Amount',
            title="Category-wise Breakdown",
            hole=0.4,                    # Donut chart (modern look)
            color_discrete_sequence=px.colors.qualitative.Set3
        )
        st.plotly_chart(fig_cat, use_container_width=True)

    # Row 2
    col3, col4 = st.columns(2)

    # Category Bar
    with col3:
        st.subheader("Category Comparison")
        fig_bar = px.bar(
            category_total,
            x='Category',
            y='Amount',
            text_auto=True
        )
        st.plotly_chart(fig_bar, use_container_width=True)

    # Daily Trend
    with col4:
        st.subheader("Daily Spending")
        daily = filtered_df.groupby('Day')['Amount'].sum().reset_index()

        fig_area = px.area(
            daily,
            x='Day',
            y='Amount'
        )
        st.plotly_chart(fig_area, use_container_width=True)

   
    # EXPORT SECTION

    st.subheader("Export Reports")
    col1, col2 = st.columns(2)

    # CSV Export
    csv = filtered_df.to_csv(index=False).encode('utf-8')
    col1.download_button(
        "Download CSV",
        data=csv,
        file_name=f"expenses_{datetime.today().strftime('%Y-%m-%d')}.csv",
        mime="text/csv",
        key="csv_download"
    )

    def create_pdf(df):
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=10)

        for index, row in df.iterrows():
             desc = row.get('Description', '')
             line = f"{row['Date']} | {row['Category']} | {row['Amount']} | {desc}"
             pdf.cell(200, 10, txt=line, ln=True)

        output = pdf.output(dest='S')

        if isinstance(output, str):
            return output.encode('latin1')
        else:
            return bytes(output)       


    # Create PDF
    pdf_bytes = create_pdf(filtered_df)

    # Download button
    col2.download_button(
        "Download PDF",
        data=pdf_bytes,
        file_name=f"expense_report_{datetime.today().strftime('%Y-%m-%d')}.pdf",
        mime="application/pdf",
        key="pdf_download"
)

else:
    st.info("No expenses found. Add from the sidebar")