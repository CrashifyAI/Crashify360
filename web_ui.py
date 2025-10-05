"""
Crashify360 - Enhanced Streamlit Web Interface
Complete UI with all features and real-time validation
"""

import streamlit as st
import json
from datetime import datetime
import config
from valuation_engine import ValuationEngine
from validator import InputValidator
from autograp_api import AutoGrapAPI, APIError
from salvage_email import send_salvage_request, EmailError, generate_salvage_email_body
from salvage_parser import extract_salvage_value
from data_storage import DecisionStorage
from logger import get_logger

# Initialize components
engine = ValuationEngine()
validator = InputValidator()
api_client = AutoGrapAPI()
storage = DecisionStorage()
logger = get_logger()

# Page configuration
st.set_page_config(
    page_title=config.WEB_UI_CONFIG["page_title"],
    page_icon=config.WEB_UI_CONFIG["page_icon"],
    layout=config.WEB_UI_CONFIG["layout"]
)

# Custom CSS
st.markdown("""
    <style>
    .big-font {
        font-size:20px !important;
        font-weight: bold;
    }
    .success-box {
        padding: 20px;
        border-radius: 10px;
        background-color: #d4edda;
        border: 2px solid #28a745;
        margin: 10px 0;
    }
    .error-box {
        padding: 20px;
        border-radius: 10px;
        background-color: #f8d7da;
        border: 2px solid #dc3545;
        margin: 10px 0;
    }
    .warning-box {
        padding: 20px;
        border-radius: 10px;
        background-color: #fff3cd;
        border: 2px solid #ffc107;
        margin: 10px 0;
    }
    .info-box {
        padding: 20px;
        border-radius: 10px;
        background-color: #d1ecf1;
        border: 2px solid #17a2b8;
        margin: 10px 0;
    }
    </style>
    """, unsafe_allow_html=True)

# Initialize session state
if 'calculation_result' not in st.session_state:
    st.session_state.calculation_result = None
if 'validation_result' not in st.session_state:
    st.session_state.validation_result = None
if 'vehicle_data' not in st.session_state:
    st.session_state.vehicle_data = None

def main():
    """Main application"""
    
    # Header
    st.title("🚗 Crashify360 - Total Loss Evaluator")
    st.markdown("### Intelligent Total Loss Assessment System")
    
    # Sidebar navigation
    page = st.sidebar.selectbox(
        "Navigation",
        ["New Assessment", "View History", "Salvage Parser", "Statistics", "Settings"]
    )
    
    if page == "New Assessment":
        new_assessment_page()
    elif page == "View History":
        history_page()
    elif page == "Salvage Parser":
        salvage_parser_page()
    elif page == "Statistics":
        statistics_page()
    elif page == "Settings":
        settings_page()

def new_assessment_page():
    """New assessment form"""
    
    st.header("📝 New Total Loss Assessment")
    
    # Create tabs for different input methods
    tab1, tab2 = st.tabs(["Manual Entry", "VIN Lookup"])
    
    with tab1:
        manual_entry_form()
    
    with tab2:
        vin_lookup_form()

def manual_entry_form():
    """Manual entry form"""
    
    with st.form("assessment_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Vehicle Information")
            
            vin = st.text_input(
                "VIN (Vehicle Identification Number)*",
                max_chars=17,
                help="17-character VIN (no I, O, or Q)"
            ).upper()
            
            policy_type = st.selectbox(
                "Policy Type*",
                options=config.POLICY_TYPES,
                format_func=lambda x: x.replace('_', ' ').title()
            )
            
            loss_type = st.selectbox(
                "Loss Type*",
                options=list(config.LOSS_TYPES.keys()),
                format_func=lambda x: config.LOSS_TYPES[x]
            )
        
        with col2:
            st.subheader("Financial Values")
            
            policy_value = st.number_input(
                "Policy Value ($)*",
                min_value=0.0,
                value=25000.0,
                step=1000.0,
                format="%.2f"
            )
            
            salvage_value = st.number_input(
                "Salvage Value ($)*",
                min_value=0.0,
                value=5000.0,
                step=500.0,
                format="%.2f"
            )
            
            repair_quote = st.number_input(
                "Repair Quote ($)*",
                min_value=0.0,
                value=18000.0,
                step=500.0,
                format="%.2f"
            )
        
        st.subheader("Owner Contact (Optional)")
        col3, col4 = st.columns(2)
        
        with col3:
            owner_email = st.text_input("Owner Email")
        
        with col4:
            owner_phone = st.text_input("Owner Phone")
        
        # Submit button
        submitted = st.form_submit_button("🔍 Evaluate Total Loss", use_container_width=True)
        
        if submitted:
            process_assessment(
                vin, policy_type, policy_value, salvage_value,
                repair_quote, loss_type, owner_email, owner_phone
            )
    
    # Display results if available
    if st.session_state.calculation_result:
        display_results()

def vin_lookup_form():
    """VIN lookup with Auto Grap API"""
    
    st.info("🔍 Lookup vehicle details using VIN and Auto Grap API")
    
    vin = st.text_input("Enter VIN", max_chars=17).upper()
    
    col1, col2 = st.columns([1, 3])
    with col1:
        lookup_button = st.button("🔎 Lookup VIN", use_container_width=True)
    
    if lookup_button and vin:
        if not validator.validate_vin(vin):
            st.error("❌ Invalid VIN format")
            return
        
        with st.spinner("Looking up vehicle details..."):
            try:
                vehicle_data = api_client.get_market_value(vin)
                st.session_state.vehicle_data = vehicle_data
                
                st.success(f"✅ Found: {vehicle_data.get('year')} {vehicle_data.get('make')} {vehicle_data.get('model')}")
                
                # Display vehicle details
                st.subheader("Vehicle Details")
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Market Value", f"${vehicle_data.get('market_value', 0):,.2f}")
                with col2:
                    st.metric("Trade-In Value", f"${vehicle_data.get('trade_in_value', 0):,.2f}")
                with col3:
                    st.metric("Retail Value", f"${vehicle_data.get('retail_value', 0):,.2f}")
                
                st.json(vehicle_data)
                
                # Pre-fill form button
                if st.button("📝 Use These Values"):
                    # This would pre-fill the manual form
                    st.info("Values can be used in manual entry form")
            
            except APIError as e:
                st.error(f"❌ API Error: {e.message}")
            except Exception as e:
                st.error(f"❌ Unexpected error: {str(e)}")

def process_assessment(vin, policy_type, policy_value, salvage_value,
                      repair_quote, loss_type, owner_email=None, owner_phone=None):
    """Process the assessment"""
    
    with st.spinner("Calculating..."):
        # Calculate
        result, validation = engine.calculate_total_loss(
            vin=vin,
            policy_type=policy_type,
            policy_value=policy_value,
            salvage_value=salvage_value,
            repair_quote=repair_quote,
            loss_type=loss_type,
            skip_validation=False
        )
        
        st.session_state.validation_result = validation
        st.session_state.calculation_result = result
        
        # Save to storage if valid
        if result:
            decision_id = storage.save_decision(result.to_dict())
            st.session_state.calculation_result.decision_id = decision_id

def display_results():
    """Display calculation results"""
    
    result = st.session_state.calculation_result
    validation = st.session_state.validation_result
    
    st.markdown("---")
    st.header("📊 Assessment Results")
    
    # Validation messages
    if not validation.is_valid:
        st.markdown('<div class="error-box">', unsafe_allow_html=True)
        st.error("❌ Validation Errors:")
        for error in validation.errors:
            st.write(f"• **{error['field']}**: {error['message']}")
        st.markdown('</div>', unsafe_allow_html=True)
        return
    
    if validation.warnings:
        st.markdown('<div class="warning-box">', unsafe_allow_html=True)
        st.warning("⚠️ Warnings:")
        for warning in validation.warnings:
            st.write(f"• **{warning['field']}**: {warning['message']}")
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Main result
    if result.is_total_loss:
        st.markdown('<div class="error-box">', unsafe_allow_html=True)
        st.error("🔴 **TOTAL LOSS**")
        st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="success-box">', unsafe_allow_html=True)
        st.success("🟢 **REPAIRABLE**")
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Policy Value", f"${result.policy_value:,.2f}")
    with col2:
        st.metric("Salvage Value", f"${result.salvage_value:,.2f}")
    with col3:
        st.metric("Repair Quote", f"${result.repair_quote:,.2f}")
    with col4:
        st.metric("Threshold (70%)", f"${result.threshold:,.2f}")
    
    # Progress bar
    st.markdown("#### Repair Quote vs Threshold")
    progress = min(result.repair_quote / result.threshold, 1.5)
    st.progress(progress / 1.5)
    st.caption(f"{result.threshold_percentage:.1f}% of threshold")
    
    # Detailed explanation
    with st.expander("📄 Detailed Explanation", expanded=True):
        st.code(result.generate_explanation(), language=None)
    
    # Actions
    st.markdown("### Actions")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📧 Request Salvage Quote", use_container_width=True):
            st.session_state.show_salvage_form = True
    
    with col2:
        if st.button("📥 Download Report", use_container_width=True):
            # Generate downloadable report
            report = result.generate_explanation()
            st.download_button(
                "Download TXT",
                report,
                file_name=f"total_loss_report_{result.vin}_{datetime.now().strftime('%Y%m%d')}.txt"
            )
    
    with col3:
        if st.button("📊 Download JSON", use_container_width=True):
            st.download_button(
                "Download JSON",
                json.dumps(result.to_dict(), indent=2),
                file_name=f"total_loss_data_{result.vin}_{datetime.now().strftime('%Y%m%d')}.json"
            )
    
    # Salvage request form
    if st.session_state.get('show_salvage_form'):
        with st.form("salvage_request_form"):
            st.subheader("Send Salvage Request")
            
            salvage_email = st.text_input("Salvage Yard Email*", value="salvage@example.com")
            cc_emails = st.text_input("CC Emails (comma-separated)", value="")
            additional_info = st.text_area("Additional Information", height=100)
            
            col1, col2 = st.columns(2)
            with col1:
                send_button = st.form_submit_button("📤 Send Request", use_container_width=True)
            with col2:
                preview_button = st.form_submit_button("👁️ Preview Email", use_container_width=True)
            
            if preview_button:
                vehicle_info = {
                    "vin": result.vin,
                    "year": 2020,  # Would come from API
                    "make": "Toyota",
                    "model": "Camry"
                }
                preview = generate_salvage_email_body(
                    vehicle_info=vehicle_info,
                    policy_value=result.policy_value,
                    loss_type=result.loss_type,
                    additional_info=additional_info
                )
                st.markdown("#### Email Preview")
                st.markdown(preview, unsafe_allow_html=True)
            
            if send_button:
                if not validator.validate_email(salvage_email):
                    st.error("Invalid email address")
                else:
                    try:
                        vehicle_info = {
                            "vin": result.vin,
                            "year": 2020,
                            "make": "Toyota",
                            "model": "Camry"
                        }
                        
                        cc_list = [e.strip() for e in cc_emails.split(',')] if cc_emails else None
                        
                        with st.spinner("Sending email..."):
                            send_salvage_request(
                                to_email=salvage_email,
                                vehicle_info=vehicle_info,
                                policy_value=result.policy_value,
                                loss_type=result.loss_type,
                                additional_info=additional_info,
                                cc_emails=cc_list
                            )
                        
                        st.success("✅ Salvage request sent successfully!")
                        st.session_state.show_salvage_form = False
                    
                    except EmailError as e:
                        st.error(f"❌ Failed to send email: {str(e)}")

def history_page():
    """View assessment history"""
    
    st.header("📜 Assessment History")
    
    # Filters
    with st.expander("🔍 Filters", expanded=False):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            filter_loss_type = st.selectbox(
                "Loss Type",
                options=["All"] + list(config.LOSS_TYPES.keys()),
                format_func=lambda x: config.LOSS_TYPES.get(x, x)
            )
        
        with col2:
            filter_decision = st.selectbox(
                "Decision",
                options=["All", "TOTAL LOSS", "REPAIRABLE"]
            )
        
        with col3:
            limit = st.number_input("Results Limit", min_value=5, max_value=100, value=20)
    
    # Apply filters
    if filter_loss_type == "All" and filter_decision == "All":
        decisions = storage.get_recent_decisions(limit=limit)
    else:
        decisions = storage.search_decisions(
            loss_type=None if filter_loss_type == "All" else filter_loss_type,
            decision=None if filter_decision == "All" else filter_decision
        )
        decisions = decisions[:limit]
    
    if not decisions:
        st.info("No decisions found")
        return
    
    # Display as table
    st.subheader(f"Found {len(decisions)} decisions")
    
    for i, decision in enumerate(decisions, 1):
        with st.expander(
            f"{i}. {decision.get('vin')} - {decision.get('decision')} - {decision.get('stored_at', '')[:10]}"
        ):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Policy Value", f"${decision.get('policy_value', 0):,.2f}")
                st.write(f"**Loss Type:** {decision.get('loss_type', 'N/A')}")
            
            with col2:
                st.metric("Repair Quote", f"${decision.get('repair_quote', 0):,.2f}")
                st.write(f"**Policy Type:** {decision.get('policy_type', 'N/A')}")
            
            with col3:
                st.metric("Threshold", f"${decision.get('threshold', 0):,.2f}")
                st.write(f"**Decision:** {decision.get('decision', 'N/A')}")
            
            # JSON view
            if st.checkbox(f"View JSON {i}", key=f"json_{i}"):
                st.json(decision)
            
            # Download button
            st.download_button(
                "📥 Download",
                json.dumps(decision, indent=2),
                file_name=f"decision_{decision.get('id')}.json",
                key=f"download_{i}"
            )

def salvage_parser_page():
    """Salvage value parser"""
    
    st.header("🔍 Salvage Value Parser")
    st.markdown("Extract salvage values from email responses")
    
    # Input methods
    input_method = st.radio("Input Method", ["Paste Text", "Upload File"])
    
    email_text = ""
    
    if input_method == "Paste Text":
        email_text = st.text_area(
            "Paste email content here",
            height=300,
            placeholder="Paste the salvage quote email here..."
        )
    else:
        uploaded_file = st.file_uploader("Upload email file (.txt, .eml)", type=['txt', 'eml'])
        if uploaded_file:
            email_text = uploaded_file.read().decode('utf-8')
            st.text_area("File Content", email_text, height=200, disabled=True)
    
    # Optional context
    col1, col2 = st.columns(2)
    with col1:
        context_vin = st.text_input("VIN (optional)", max_chars=17)
    with col2:
        context_policy_value = st.number_input("Policy Value (optional)", min_value=0.0, value=0.0)
    
    # Parse button
    if st.button("🔎 Extract Salvage Value", use_container_width=True):
        if not email_text:
            st.warning("Please provide email text")
            return
        
        with st.spinner("Parsing..."):
            result = extract_salvage_value(
                email_text,
                vin=context_vin if context_vin else None,
                policy_value=context_policy_value if context_policy_value > 0 else None
            )
        
        # Display results
        st.markdown("---")
        st.subheader("Extraction Results")
        
        if result['success']:
            st.markdown('<div class="success-box">', unsafe_allow_html=True)
            st.success(f"✅ Extracted Salvage Value: **${result['best_value']:,.2f}**")
            st.markdown('</div>', unsafe_allow_html=True)
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Best Value", f"${result['best_value']:,.2f}")
            with col2:
                st.metric("Confidence", f"{result['confidence']:.1%}")
            with col3:
                st.metric("Method", result['method'])
            
            if len(result['values_found']) > 1:
                st.info(f"ℹ️ Found {len(result['values_found'])} values: {[f'${v:,.2f}' for v in result['values_found']]}")
            
            # Validation
            if 'validation' in result:
                validation = result['validation']
                if validation.get('message'):
                    if 'Warning' in validation['message']:
                        st.warning(validation['message'])
                    else:
                        st.info(validation['message'])
        else:
            st.markdown('<div class="error-box">', unsafe_allow_html=True)
            st.error("❌ No salvage value found in the text")
            st.markdown('</div>', unsafe_allow_html=True)
            st.info("💡 Tips: Ensure the email contains monetary values near keywords like 'salvage', 'offer', 'price', etc.")

def statistics_page():
    """Statistics dashboard"""
    
    st.header("📊 Statistics Dashboard")
    
    stats = storage.get_statistics()
    
    if stats['total_decisions'] == 0:
        st.info("No decisions recorded yet")
        return
    
    # Key metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Decisions", stats['total_decisions'])
    with col2:
        st.metric("Total Losses", f"{stats['total_losses']} ({stats['total_loss_percentage']:.1f}%)")
    with col3:
        st.metric("Repairable", stats['repairable'])
    with col4:
        st.metric("Avg Policy Value", f"${stats['avg_policy_value']:,.0f}")
    
    st.markdown("---")
    
    # Charts
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Decision Distribution")
        decision_data = {
            "Total Loss": stats['total_losses'],
            "Repairable": stats['repairable']
        }
        st.bar_chart(decision_data)
    
    with col2:
        st.subheader("Loss Type Distribution")
        if stats['loss_types']:
            st.bar_chart(stats['loss_types'])
    
    # Financial metrics
    st.markdown("---")
    st.subheader("Financial Overview")
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Average Policy Value", f"${stats['avg_policy_value']:,.2f}")
    with col2:
        st.metric("Average Repair Quote", f"${stats['avg_repair_quote']:,.2f}")
    
    # Date range
    st.markdown("---")
    st.subheader("Date Range")
    col1, col2 = st.columns(2)
    with col1:
        st.write(f"**First Decision:** {stats['first_decision'][:10] if stats['first_decision'] else 'N/A'}")
    with col2:
        st.write(f"**Last Decision:** {stats['last_decision'][:10] if stats['last_decision'] else 'N/A'}")
    
    # Export options
    st.markdown("---")
    st.subheader("Export Data")
    
    if st.button("📥 Export All Decisions to CSV"):
        try:
            csv_path = "output/decisions_export.csv"
            storage.export_to_csv(csv_path)
            st.success(f"✅ Exported to {csv_path}")
            
            with open(csv_path, 'r') as f:
                st.download_button(
                    "Download CSV",
                    f.read(),
                    file_name=f"crashify360_export_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv"
                )
        except Exception as e:
            st.error(f"Export failed: {str(e)}")

def settings_page():
    """Settings and configuration"""
    
    st.header("⚙️ Settings & Configuration")
    
    # Configuration validation
    st.subheader("Configuration Status")
    
    validation = config.validate_config()
    
    if validation['valid']:
        st.success("✅ All configuration valid")
    else:
        st.error("❌ Configuration errors:")
        for error in validation['errors']:
            st.write(f"• {error}")
    
    # Threshold settings
    st.markdown("---")
    st.subheader("Threshold Configuration")
    
    st.info("Current thresholds for total loss calculation")
    
    for policy_type, threshold in config.THRESHOLDS.items():
        col1, col2 = st.columns([2, 1])
        with col1:
            st.write(f"**{policy_type.replace('_', ' ').title()}**")
        with col2:
            st.write(f"{threshold * 100:.0f}%")
    
    # API settings
    st.markdown("---")
    st.subheader("API Configuration")
    
    col1, col2 = st.columns(2)
    with col1:
        st.write("**Auto Grap API**")
        if config.AUTO_GRAP_CONFIG['api_key']:
            st.success("✅ API Key configured")
            if st.button("Test API Connection"):
                with st.spinner("Testing..."):
                    if api_client.health_check():
                        st.success("✅ API is accessible")
                    else:
                        st.error("❌ API connection failed")
        else:
            st.error("❌ API Key not configured")
    
    with col2:
        st.write("**Email Configuration**")
        if config.EMAIL_CONFIG['user'] and config.EMAIL_CONFIG['password']:
            st.success("✅ Email configured")
        else:
            st.error("❌ Email not configured")
    
    # System info
    st.markdown("---")
    st.subheader("System Information")
    
    col1, col2 = st.columns(2)
    with col1:
        st.write(f"**Version:** 1.0.0")
        st.write(f"**Storage Path:** {config.PATHS['decisions']}")
    with col2:
        st.write(f"**Log Path:** {config.PATHS['logs']}")
        st.write(f"**Total Decisions:** {storage.get_statistics()['total_decisions']}")
    
    # Danger zone
    st.markdown("---")
    st.subheader("⚠️ Danger Zone")
    
    with st.expander("Clear All Data", expanded=False):
        st.warning("This will permanently delete all stored decisions!")
        confirm_text = st.text_input("Type 'DELETE ALL' to confirm")
        if st.button("🗑️ Clear All Decisions"):
            if confirm_text == "DELETE ALL":
                try:
                    storage.clear_all_decisions(confirm=True)
                    st.success("All decisions cleared")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {str(e)}")
            else:
                st.error("Confirmation text doesn't match")

# Run the app
if __name__ == "__main__":
    # Initialize directories
    config.initialize_directories()
    
    # Run main app
    main()

