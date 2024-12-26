# app.py
import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

# Database connection
def get_database_connection():
    return create_engine('postgresql://postgre:nikhithreddY7@localhost:5432/your_database')

# Query templates based on your data structure
QUERY_TEMPLATES = {
    'top_selling_products': """
        SELECT s.sku_id, sk.name, sk.category, sk.subcategory, 
               SUM(s.quantity) as total_quantity,
               SUM(s.quantity * s.unit_price) as total_revenue
        FROM sales_data s
        JOIN skus sk ON s.sku_id = sk.sku_id
        WHERE s.date BETWEEN :start_date AND :end_date
        GROUP BY s.sku_id, sk.name, sk.category, sk.subcategory
        ORDER BY total_revenue DESC
        LIMIT 10
    """,
    'inventory_turnover': """
        SELECT sk.category, sk.subcategory,
               ABS(SUM(CASE WHEN i.transaction_type = 'SALE' THEN i.quantity ELSE 0 END)) as total_sales,
               AVG(sk.safety_stock) as avg_safety_stock
        FROM inventory_data i
        JOIN skus sk ON i.sku_id = sk.sku_id
        WHERE i.date BETWEEN :start_date AND :end_date
        GROUP BY sk.category, sk.subcategory
    """,
    'supplier_performance': """
        SELECT s.name as supplier_name, s.country,
               s.lead_time_reliability, s.quality_rating,
               COUNT(DISTINCT pt.sku_id) as products_supplied
        FROM suppliers s
        JOIN pricing_tiers pt ON s.supplier_id = pt.supplier_id
        GROUP BY s.supplier_id, s.name, s.country, s.lead_time_reliability, s.quality_rating
        ORDER BY s.quality_rating DESC
    """
}

def main():
    st.title('Supply Chain Analytics Dashboard')
    
    # Sidebar for filters
    st.sidebar.header('Filters')
    
    # Date range selector
    default_start_date = datetime(2022, 1, 1)
    default_end_date = datetime(2024, 12, 31)
    start_date = st.sidebar.date_input('Start Date', default_start_date)
    end_date = st.sidebar.date_input('End Date', default_end_date)
    
    # Analysis type selector
    analysis_type = st.sidebar.selectbox(
        'Select Analysis',
        ['Top Selling Products', 'Inventory Analysis', 'Supplier Performance']
    )
    
    try:
        engine = get_database_connection()
        
        if analysis_type == 'Top Selling Products':
            df = pd.read_sql(
                QUERY_TEMPLATES['top_selling_products'],
                engine,
                params={'start_date': start_date, 'end_date': end_date}
            )
            
            st.header('Top 10 Products by Revenue')
            
            # Revenue chart
            fig = px.bar(
                df,
                x='name',
                y='total_revenue',
                color='category',
                title='Revenue by Product'
            )
            st.plotly_chart(fig)
            
            # Detailed data table
            st.dataframe(df)
            
        elif analysis_type == 'Inventory Analysis':
            df = pd.read_sql(
                QUERY_TEMPLATES['inventory_turnover'],
                engine,
                params={'start_date': start_date, 'end_date': end_date}
            )
            
            # Calculate inventory turnover ratio
            df['inventory_turnover'] = df['total_sales'] / df['avg_safety_stock']
            
            st.header('Inventory Turnover by Category')
            
            # Turnover chart
            fig = px.treemap(
                df,
                path=['category', 'subcategory'],
                values='inventory_turnover',
                title='Inventory Turnover Ratio'
            )
            st.plotly_chart(fig)
            
            # Detailed data table
            st.dataframe(df)
            
        elif analysis_type == 'Supplier Performance':
            df = pd.read_sql(QUERY_TEMPLATES['supplier_performance'], engine)
            
            st.header('Supplier Performance Matrix')
            
            # Scatter plot of supplier performance
            fig = px.scatter(
                df,
                x='lead_time_reliability',
                y='quality_rating',
                size='products_supplied',
                color='country',
                hover_data=['supplier_name'],
                title='Supplier Performance Matrix'
            )
            st.plotly_chart(fig)
            
            # Detailed data table
            st.dataframe(df)
            
    except Exception as e:
        st.error(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    main()
