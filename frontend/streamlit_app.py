"""
Streamlit UI: Enhanced chat + analytics + document management for Insight Agent IDP.
"""
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import streamlit as st
import pandas as pd
import requests
import plotly.express as px
import plotly.graph_objects as go
from typing import Dict, Any
from datetime import datetime, timedelta
from PIL import Image
import io

from app.config import settings
from app.db import SessionLocal
from app.models import Transaction, Document, DocumentCorrection
from app.services.insights import InsightsService
from app.services.anomaly_detection import AnomalyDetector
from app.services.insights_generator import generate_insights_report
from app.services.document_visualization import create_annotated_document, get_extraction_confidence
from app.services.document_comparison import DocumentComparator
from app.services.export_service import export_to_excel, export_summary_report
from app.services.categorization import categorize_expense, EXPENSE_CATEGORIES
from app.services.idp_pipeline import parse_document
from app.services.receipt_matching import ReceiptMatcher
from sqlalchemy import func

st.set_page_config(page_title="Insight Agent IDP", layout="wide")

API_BASE_URL = f"http://{settings.API_HOST}:{settings.API_PORT}"

def call_insight_api(query: str, use_rag: bool = True, use_sql: bool = True) -> Dict[str, Any]:
    """Call the FastAPI insight endpoint."""
    try:
        response = requests.post(
            f"{API_BASE_URL}/chat/insights",
            json={
                "query": query,
                "use_rag": use_rag,
                "use_sql": use_sql
            },
            timeout=120
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"answer": f"Error connecting to API: {str(e)}", "sources": [], "sql_query": None}

st.title("🚀 Insight Agent IDP")
st.markdown("AI-Powered Intelligent Document Processing & Analytics")

# Sidebar for navigation
page = st.sidebar.selectbox(
    "Navigation", 
    ["📊 Analytics Dashboard", "💬 Chat", "📄 Documents", "⚠️ Anomalies", "🔍 Document Comparison", "📈 Insights Report", "🔗 Receipt Matching", "📤 Export"]
)

if page == "📊 Analytics Dashboard":
    st.header("Analytics Dashboard")
    
    insights_service = InsightsService()
    
    # Key Metrics
    db = SessionLocal()
    try:
        total_txns = db.query(Transaction).count()
        total_spend = db.query(func.sum(Transaction.amount)).scalar() or 0
        avg_transaction = total_spend / total_txns if total_txns > 0 else 0
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Transactions", f"{total_txns:,}")
        with col2:
            st.metric("Total Spending", f"${total_spend:,.2f}")
        with col3:
            st.metric("Avg Transaction", f"${avg_transaction:,.2f}")
        with col4:
            doc_count = db.query(Document).count()
            st.metric("Documents", f"{doc_count:,}")
    finally:
        db.close()
    
    st.divider()
    
    # Time Series Analytics
    st.subheader("📈 Spending Trends")
    
    time_series = insights_service.get_time_series_data()
    
    tab1, tab2, tab3 = st.tabs(["Monthly Trend", "Vendor Trends", "Forecast"])
    
    with tab1:
        if time_series.get("monthly"):
            df_monthly = pd.DataFrame(time_series["monthly"])
            df_monthly["date"] = pd.to_datetime(df_monthly["date"])
            fig = px.line(df_monthly, x="date", y="amount", 
                         title="Monthly Spending Trend",
                         labels={"amount": "Amount ($)", "date": "Month"})
            fig.update_traces(line_color='#1f77b4', line_width=3)
            st.plotly_chart(fig, use_container_width=True)
            
            # Daily trend
            if time_series.get("daily"):
                df_daily = pd.DataFrame(time_series["daily"][-30:])  # Last 30 days
                if not df_daily.empty:
                    df_daily["date"] = pd.to_datetime(df_daily["date"])
                    fig2 = px.bar(df_daily, x="date", y="amount",
                                title="Daily Spending (Last 30 Days)")
                    st.plotly_chart(fig2, use_container_width=True)
    
    with tab2:
        if time_series.get("vendor_trends"):
            fig = go.Figure()
            for vendor, data in time_series["vendor_trends"].items():
                df_vendor = pd.DataFrame(data)
                df_vendor["date"] = pd.to_datetime(df_vendor["date"])
                fig.add_trace(go.Scatter(
                    x=df_vendor["date"],
                    y=df_vendor["amount"],
                    mode='lines+markers',
                    name=vendor
                ))
            fig.update_layout(title="Top 5 Vendors - Monthly Spending Trend",
                            xaxis_title="Month",
                            yaxis_title="Amount ($)")
            st.plotly_chart(fig, use_container_width=True)
    
    with tab3:
        forecast = insights_service.get_spending_forecast()
        if forecast.get("forecast"):
            df_forecast = pd.DataFrame(forecast["forecast"])
            fig = px.bar(df_forecast, x="month", y="predicted_amount",
                        title=f"Spending Forecast (Trend: {forecast.get('trend', 'unknown')})",
                        labels={"month": "Months Ahead", "predicted_amount": "Predicted Amount ($)"})
            st.plotly_chart(fig, use_container_width=True)
            st.info(f"Trend: {forecast.get('trend', 'unknown')} | Monthly Change: ${forecast.get('monthly_change', 0):,.2f}")
        else:
            st.info("Insufficient data for forecasting. Need at least 2 months of data.")
    
    st.divider()
    
    # Vendor and Category Stats
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🏢 Top Vendors")
        vendor_stats = insights_service.get_vendor_stats(limit=10)
        if vendor_stats:
            df = pd.DataFrame(vendor_stats)
            st.dataframe(df, use_container_width=True)
            fig = px.bar(df, x="vendor", y="total_spend",
                        title="Vendor Spending",
                        labels={"total_spend": "Total Spend ($)", "vendor": "Vendor"})
            fig.update_xaxes(tickangle=45)
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("📂 Category Breakdown")
        category_breakdown = insights_service.get_category_breakdown()
        if category_breakdown:
            df = pd.DataFrame(category_breakdown)
            st.dataframe(df, use_container_width=True)
            fig = px.pie(df, values="total_spend", names="category", 
                        title="Spending by Category")
            st.plotly_chart(fig, use_container_width=True)

elif page == "💬 Chat":
    st.header("Chat Interface")
    
    # Chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    # Display chat history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Chat input
    if prompt := st.chat_input("Ask a question about your documents..."):
        # Add user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Get response from API
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                response = call_insight_api(prompt)
            
            st.markdown(response.get("answer", "No answer generated"))
            
            # Show SQL query if available
            if response.get("sql_query"):
                with st.expander("SQL Query Used"):
                    st.code(response["sql_query"], language="sql")
            
            # Show sources if available
            if response.get("sources"):
                with st.expander(f"Sources ({len(response['sources'])} documents)"):
                    for i, source in enumerate(response["sources"], 1):
                        if isinstance(source, dict):
                            st.write(f"**Source {i}:**")
                            st.write(f"- Filename: {source.get('filename', 'Unknown')}")
                            st.write(f"- Type: {source.get('document_type', 'Unknown')}")
                            if source.get('text_snippet'):
                                st.text(source['text_snippet'][:300] + "...")
                        else:
                            st.write(source)
        
        st.session_state.messages.append({
            "role": "assistant", 
            "content": response.get("answer", "No answer generated")
        })

elif page == "📄 Documents":
    st.header("Documents")
    
    # Upload new documents
    st.subheader("📤 Upload New Document")
    uploaded_file = st.file_uploader("Choose a file", type=['pdf', 'png', 'jpg', 'jpeg'])
    
    if uploaded_file is not None:
        if st.button("Process Document"):
            with st.spinner("Processing document..."):
                # Save uploaded file
                upload_dir = Path("data/raw_docs")
                upload_dir.mkdir(parents=True, exist_ok=True)
                file_path = upload_dir / uploaded_file.name
                
                with open(file_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                
                # Process document
                result = parse_document(str(file_path))
                
                # Save to database
                db = SessionLocal()
                try:
                    doc = Document(
                        filename=uploaded_file.name,
                        file_path=str(file_path),
                        document_type=result.get("document_type", "unknown"),
                        raw_text=result.get("raw_text", ""),
                        extracted_data=result.get("extracted_data", {})
                    )
                    db.add(doc)
                    db.flush()
                    
                    # Create transactions
                    from scripts.ingest_docs import extract_transactions_from_document
                    transactions = extract_transactions_from_document(doc, result.get("extracted_data", {}))
                    for txn_data in transactions:
                        txn = Transaction(**txn_data)
                        db.add(txn)
                    
                    db.commit()
                    st.success(f"✅ Document processed! Extracted {len(transactions)} transactions.")
                    st.rerun()
                except Exception as e:
                    db.rollback()
                    st.error(f"Error processing document: {e}")
                finally:
                    db.close()
    
    st.divider()
    
    # Document list
    db = SessionLocal()
    try:
        documents = db.query(Document).all()
        
        if documents:
            st.write(f"**Total Documents:** {len(documents)}")
            
            # Document type filter
            doc_types = ["All"] + list(set([doc.document_type for doc in documents if doc.document_type]))
            selected_type = st.selectbox("Filter by type", doc_types)
            
            filtered_docs = documents if selected_type == "All" else [
                doc for doc in documents if doc.document_type == selected_type
            ]
            
            for doc in filtered_docs:
                with st.expander(f"📄 {doc.filename} ({doc.document_type})"):
                    col1, col2 = st.columns([2, 1])
                    
                    with col1:
                        if doc.extracted_data:
                            # Show extracted data with confidence scores
                            confidence = get_extraction_confidence(doc.extracted_data)
                            
                            st.write("**Extracted Fields:**")
                            for field, value in doc.extracted_data.items():
                                if value:
                                    conf_score = confidence.get(field, 0)
                                    conf_color = "🟢" if conf_score > 70 else "🟡" if conf_score > 40 else "🔴"
                                    st.write(f"{conf_color} **{field.replace('_', ' ').title()}**: {value} (Confidence: {conf_score:.0f}%)")
                            
                            # Visual annotation
                            if doc.file_path and Path(doc.file_path).exists():
                                if st.button(f"🔍 View Annotated Document", key=f"annotate_{doc.id}"):
                                    annotated = create_annotated_document(
                                        doc.file_path,
                                        doc.extracted_data
                                    )
                                    st.image(annotated, caption="Document with Extracted Fields Highlighted")
                            
                            # Edit fields
                            st.subheader("✏️ Edit Extracted Data")
                            with st.form(f"edit_form_{doc.id}"):
                                vendor = st.text_input("Vendor", value=doc.extracted_data.get("vendor", ""))
                                total = st.number_input("Total", value=float(doc.extracted_data.get("total", 0) or 0))
                                invoice_num = st.text_input("Invoice #", value=doc.extracted_data.get("invoice_number", ""))
                                
                                if st.form_submit_button("Save Corrections"):
                                    # Update extracted data
                                    doc.extracted_data["vendor"] = vendor
                                    doc.extracted_data["total"] = total
                                    doc.extracted_data["invoice_number"] = invoice_num
                                    
                                    # Save correction
                                    if vendor != doc.extracted_data.get("vendor"):
                                        correction = DocumentCorrection(
                                            document_id=doc.id,
                                            field_name="vendor",
                                            original_value=str(doc.extracted_data.get("vendor", "")),
                                            corrected_value=vendor
                                        )
                                        db.add(correction)
                                    
                                    db.commit()
                                    st.success("✅ Corrections saved!")
                                    st.rerun()
                    
                    with col2:
                        st.write(f"**Path:** {doc.file_path}")
                        st.write(f"**Created:** {doc.created_at}")
                        
                        # Similar documents
                        similar = DocumentComparator.find_similar_documents(doc.id, limit=3)
                        if similar:
                            st.write("**Similar Documents:**")
                            for sim in similar:
                                st.write(f"- {sim['filename']} (Score: {sim['similarity_score']})")
                    
                    if doc.raw_text:
                        with st.expander("Raw OCR Text"):
                            st.text_area("", doc.raw_text[:2000] + ("..." if len(doc.raw_text) > 2000 else ""), 
                                       height=200, key=f"text_{doc.id}")
        else:
            st.info("No documents found. Upload a document above or run `python scripts/ingest_docs.py` to add documents.")
    finally:
        db.close()

elif page == "⚠️ Anomalies":
    st.header("Anomaly Detection")
    
    if st.button("🔍 Run Anomaly Detection"):
        with st.spinner("Detecting anomalies..."):
            anomalies = AnomalyDetector.get_all_anomalies()
            
            if anomalies:
                st.write(f"**Found {len(anomalies)} anomalies**")
                
                # Group by severity
                high_priority = [a for a in anomalies if a.get("severity") == "high"]
                medium_priority = [a for a in anomalies if a.get("severity") == "medium"]
                low_priority = [a for a in anomalies if a.get("severity") == "low"]
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("High Priority", len(high_priority), delta=None)
                with col2:
                    st.metric("Medium Priority", len(medium_priority), delta=None)
                with col3:
                    st.metric("Low Priority", len(low_priority), delta=None)
                
                st.divider()
                
                # Display anomalies
                for anom in anomalies:
                    severity_color = {
                        "high": "🔴",
                        "medium": "🟡",
                        "low": "🟢"
                    }
                    icon = severity_color.get(anom.get("severity", "low"), "⚪")
                    
                    with st.expander(f"{icon} {anom.get('type', 'Unknown')} - {anom.get('message', '')}"):
                        st.write(f"**Severity:** {anom.get('severity', 'unknown')}")
                        st.write(f"**Type:** {anom.get('type', 'unknown')}")
                        if "transaction_id" in anom:
                            st.write(f"**Transaction ID:** {anom['transaction_id']}")
                        if "document_id" in anom:
                            st.write(f"**Document ID:** {anom['document_id']}")
            else:
                st.success("✅ No anomalies detected!")

elif page == "🔍 Document Comparison":
    st.header("Document Comparison")
    
    db = SessionLocal()
    try:
        documents = db.query(Document).all()
        
        if len(documents) < 2:
            st.info("Need at least 2 documents to compare.")
        else:
            doc_options = {f"{d.filename} (ID: {d.id})": d.id for d in documents}
            
            col1, col2 = st.columns(2)
            with col1:
                doc1_name = st.selectbox("Select Document 1", list(doc_options.keys()))
                doc1_id = doc_options[doc1_name]
            
            with col2:
                doc2_name = st.selectbox("Select Document 2", list(doc_options.keys()))
                doc2_id = doc_options[doc2_name]
            
            if st.button("Compare Documents"):
                comparison = DocumentComparator.compare_documents(doc1_id, doc2_id)
                
                if "error" not in comparison:
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.subheader("Document 1")
                        st.json(comparison["document1"])
                    
                    with col2:
                        st.subheader("Document 2")
                        st.json(comparison["document2"])
                    
                    if comparison.get("differences"):
                        st.subheader("Differences")
                        df_diff = pd.DataFrame(comparison["differences"])
                        st.dataframe(df_diff, use_container_width=True)
            
            # Price changes for vendor
            st.divider()
            st.subheader("Price Change Detection")
            vendors = db.query(Transaction.vendor).distinct().all()
            vendor_list = [v[0] for v in vendors if v[0]]
            
            if vendor_list:
                selected_vendor = st.selectbox("Select Vendor", vendor_list)
                if st.button("Analyze Price Changes"):
                    changes = DocumentComparator.detect_price_changes(selected_vendor)
                    if changes:
                        df_changes = pd.DataFrame(changes)
                        st.dataframe(df_changes, use_container_width=True)
                        
                        # Chart price changes
                        if "to_amount" in df_changes.columns:
                            fig = px.line(df_changes, x="to_date", y="to_amount",
                                        title=f"Price Changes for {selected_vendor}",
                                        labels={"to_date": "Date", "to_amount": "Amount ($)"})
                            st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.info("No price changes detected for this vendor.")
    finally:
        db.close()

elif page == "📈 Insights Report":
    st.header("AI-Generated Insights Report")
    
    if st.button("Generate Insights Report"):
        with st.spinner("Generating insights report..."):
            report = generate_insights_report()
            st.markdown(report)
            
            # Download button
            st.download_button(
                label="📥 Download Report",
                data=report,
                file_name=f"insights_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                mime="text/markdown"
            )

elif page == "🔗 Receipt Matching":
    st.header("Receipt-to-Invoice Matching")
    
    db = SessionLocal()
    try:
        # Get all receipts
        receipts = db.query(Document).filter(Document.document_type == "receipt").all()
        
        if not receipts:
            st.info("No receipts found. Upload receipt documents to use this feature.")
        else:
            st.subheader("Match Receipt to Invoice")
            
            receipt_options = {f"{r.filename} (ID: {r.id})": r.id for r in receipts}
            selected_receipt = st.selectbox("Select Receipt", list(receipt_options.keys()))
            receipt_id = receipt_options[selected_receipt]
            
            if st.button("Find Matching Invoice"):
                with st.spinner("Searching for matching invoices..."):
                    receipt = db.query(Document).filter(Document.id == receipt_id).first()
                    if receipt:
                        extracted = receipt.extracted_data or {}
                        
                        matches = ReceiptMatcher.find_matching_invoice(
                            receipt_vendor=extracted.get("vendor"),
                            receipt_amount=extracted.get("total"),
                            receipt_date=None  # Could parse date if needed
                        )
                        
                        if matches:
                            st.write(f"**Found {len(matches)} potential matches:**")
                            
                            for i, match in enumerate(matches[:5], 1):  # Show top 5
                                confidence_color = "🟢" if match["confidence"] > 70 else "🟡" if match["confidence"] > 50 else "🟠"
                                
                                with st.expander(f"{confidence_color} Match {i}: {match['invoice_filename']} (Confidence: {match['confidence']:.0f}%)"):
                                    st.write(f"**Invoice ID:** {match['invoice_id']}")
                                    st.write(f"**Vendor:** {match['invoice_vendor']}")
                                    st.write(f"**Total:** ${match['invoice_total']:.2f}")
                                    st.write(f"**Date:** {match['invoice_date']}")
                                    st.write("**Match Reasons:**")
                                    for reason in match['match_reasons']:
                                        st.write(f"- {reason}")
                                    
                                    if st.button(f"View Invoice", key=f"view_{match['invoice_id']}"):
                                        st.session_state['selected_doc_id'] = match['invoice_id']
                                        st.rerun()
                        else:
                            st.warning("No matching invoices found. Try adjusting tolerance settings.")
            
            st.divider()
            st.subheader("Unmatched Receipts")
            unmatched = ReceiptMatcher.get_unmatched_receipts()
            if unmatched:
                df_unmatched = pd.DataFrame(unmatched)
                st.dataframe(df_unmatched, use_container_width=True)
            else:
                st.info("All receipts have been matched!")
    finally:
        db.close()

elif page == "📤 Export":
    st.header("Export Data")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Export to Excel")
        if st.button("Generate Excel Report"):
            with st.spinner("Generating Excel file..."):
                excel_file = export_to_excel()
                st.download_button(
                    label="📥 Download Excel File",
                    data=excel_file.getvalue(),
                    file_name=f"expense_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
    
    with col2:
        st.subheader("Export Summary Report")
        if st.button("Generate Summary Report"):
            with st.spinner("Generating summary..."):
                summary = export_summary_report()
                st.markdown(summary)
                st.download_button(
                    label="📥 Download Summary",
                    data=summary,
                    file_name=f"summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                    mime="text/markdown"
                )
