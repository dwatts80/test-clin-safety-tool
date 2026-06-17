import streamlit as st
import pandas as pd
import json
import time
import requests
import os

# Set page configuration with a clinical medical theme
st.set_page_config(
    page_title="Clinical Safety Hub (DCB0129)",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling to mimic the high-end premium medical UI
st.markdown("""
    <style>
    .main {
        background-color: #f8fafc;
    }
    .stButton>button {
        border-radius: 8px;
    }
    .report-preview {
        background-color: #ffffff;
        padding: 24px;
        border-radius: 12px;
        border: 1px solid #e2e8f0;
        box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05);
    }
    .metric-card {
        background-color: #ffffff;
        padding: 16px;
        border-radius: 10px;
        border-left: 5px solid #0284c7;
        box-shadow: 0 2px 4px rgba(0,0,0,0.02);
    }
    </style>
""", unsafe_allow_html=True)

# Define standard DCB0129 / DCB0160 Risk Parameters
SEVERITY_LEVELS = {
    1: "Insignificant (1)",
    2: "Minor (2)",
    3: "Moderate (3)",
    4: "Major (4)",
    5: "Catastrophic (5)"
}

LIKELIHOOD_LEVELS = {
    1: "Very Unlikely (1)",
    2: "Unlikely (2)",
    3: "Possible (3)",
    4: "Likely (4)",
    5: "Highly Likely (5)"
}

def calculate_risk_rating(severity, likelihood):
    """Calculates risk rating based on a standard 5x5 Clinical Risk Matrix."""
    score = severity * likelihood
    if score >= 15:
        return "High (Red)", "#ef4444"
    elif score >= 5:
        return "Medium (Amber)", "#f59e0b"
    else:
        return "Low (Green)", "#10b981"

# Exponential Backoff implementation for Gemini API requests
def call_gemini_api(api_key, system_prompt, user_query):
    """Calls Gemini 2.5 Flash API using standard REST endpoint and exponential backoff."""
    if not api_key:
        return ("⚠️ **Gemini API Key missing!** Please enter an API key in the sidebar "
                "to use the Auto-Draft and Audit features. Alternatively, you can fill out sections manually.")
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-09-2025:generateContent?key={api_key}"
    headers = {"Content-Type": "application/json"}
    payload = {
        "contents": [{"parts": [{"text": user_query}]}],
        "systemInstruction": {"parts": [{"text": system_prompt}]}
    }
    
    delays = [1, 2, 4, 8, 16]
    for attempt, delay in enumerate(delays):
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            if response.status_code == 200:
                data = response.json()
                text = data.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")
                if text:
                    return text
            elif response.status_code == 429:
                # Rate limited, backoff
                pass
        except Exception:
            pass
        time.sleep(delay)
        
    return "❌ **Gemini Error:** Failed to compile response. The request timed out or received an invalid response."

# Initialize Session States
if "hazards" not in st.session_state:
    # Standard clinical hazard baseline for demonstration
    st.session_state.hazards = [
        {
            "id": "HZ-01",
            "title": "Mislabeled Drug Allergies in EHR",
            "desc": "System fails to parse legacy structured allergy code during transition, resulting in missing alerts.",
            "cause": "Database synchronization mismatch of drug schemas.",
            "consequence": "Patient receives medication to which they have a documented anaphylactic allergy.",
            "init_severity": 5,
            "init_likelihood": 3,
            "mitigation": "Enforced verification screen on first prescribing step; fallback manual allergy review mechanism; schema auto-validators.",
            "res_severity": 5,
            "res_likelihood": 1,
            "owner": "Dr. Sarah Lin (Clinical Safety Officer)",
            "status": "Controlled"
        },
        {
            "id": "HZ-02",
            "title": "Delayed Pathology Notification",
            "desc": "High-priority lab results fail to trigger active clinician notification during system busy states.",
            "cause": "Notification queue starvation or messaging buffer limit exceeded.",
            "consequence": "Sepsis or acute kidney injury markers missed, delaying critical urgent treatments.",
            "init_severity": 4,
            "init_likelihood": 4,
            "mitigation": "Asynchronous high-priority backup alert pathways; persistent SMS fallback alert configuration; automated receipt acknowledgement requests.",
            "res_severity": 4,
            "res_likelihood": 1,
            "owner": "Mark Davis (Systems Lead)",
            "status": "Under Review"
        }
    ]

if "cscr" not in st.session_state:
    st.session_state.cscr = {
        "doc_title": "Clinical Safety Case Report: PatientCare EHR v4.2",
        "executive_summary": "This Clinical Safety Case Report (CSCR) details the risk management activities undertaken for the PatientCare EHR v4.2 development. The assessment ensures adherence to DCB0129 criteria, concluding that with active controls, the clinical software is safe for release.",
        "introduction": "This document covers the deployment safety configurations for regional hospitals. PatientCare EHR acts as the central electronic record for admissions, prescribing, and ordering pathways.",
        "system_desc": "PatientCare EHR is a cloud-native clinical management web application consisting of a microservices backend, secure FHIR integrations, and an intuitive frontend layout designed for tablets and desktops.",
        "risk_management_process": "Our Clinical Safety Management System (CSMS) defines structured risk assessments. All hazards are documented, discussed with clinical leads, and assigned safety verification procedures.",
        "safety_arguments": "Clinical Safety is argued on three main pillars:\n1. Strict data integrity protocols minimizing information loss.\n2. Fail-safe alerts with mandatory clinical acknowledgments.\n3. Robust clinical system testing with standard patient synthetic profiles.",
        "conclusion": "With all outlined mitigations fully implemented, the residual risk of all hazards is deemed Acceptable and Clinical Safety Officer approved."
    }

# App Layout & Branding Header
st.markdown("""
<div style="background: linear-gradient(135deg, #0f172a 0%, #0284c7 100%); padding: 25px; border-radius: 12px; margin-bottom: 25px; color: white;">
    <h1 style="margin: 0; font-size: 2.2rem; font-weight: 700;">🛡️ Clinical Safety Hub</h1>
    <p style="margin: 5px 0 0 0; font-size: 1.1rem; opacity: 0.9;">Professional UK NHS DCB0129 Compliance Management Portal</p>
</div>
""", unsafe_allow_html=True)

# Sidebar Navigation and Configuration
st.sidebar.image("https://img.icons8.com/fluency/96/shield-with-heart.png", width=60)
st.sidebar.markdown("### Navigation Panel")
app_mode = st.sidebar.radio(
    "Go to:",
    ["Dashboard Overview", "Manage Hazard Log", "5x5 Risk Matrix", "CSCR Document Builder", "AI Safety Copilot & Auditor"]
)

st.sidebar.markdown("---")
st.sidebar.markdown("### ✨ Gemini Engine Configuration")
gemini_key = st.sidebar.text_input("Gemini API Key", type="password", value="", help="Provide your Gemini API Key to enable automatic drafting and audits.")
model_choice = "gemini-2.5-flash-preview-09-2025"
st.sidebar.info(f"Model Active:\n`{model_choice}`")

st.sidebar.markdown("---")
st.sidebar.markdown("**About DCB0129**")
st.sidebar.caption(
    "DCB0129 is a clinical risk management standard designed to ensure health IT system manufacturers "
    "address safety concerns throughout the product lifecycle."
)

# ==================== TAB 1: DASHBOARD OVERVIEW ====================
if app_mode == "Dashboard Overview":
    st.markdown("## 📊 Dashboard Summary")
    
    # Calculate indicators
    total_hz = len(st.session_state.hazards)
    controlled_hz = sum(1 for h in st.session_state.hazards if h["status"] == "Controlled")
    review_hz = sum(1 for h in st.session_state.hazards if h["status"] == "Under Review")
    draft_hz = sum(1 for h in st.session_state.hazards if h["status"] == "Draft")
    
    high_risks = 0
    for h in st.session_state.hazards:
        rating, _ = calculate_risk_rating(h["res_severity"], h["res_likelihood"])
        if "High" in rating:
            high_risks += 1

    # Render high-level cards
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f"""
        <div class="metric-card" style="border-left-color: #0284c7;">
            <p style="margin:0; font-size:0.9rem; color:#64748b; font-weight:600;">TOTAL HAZARDS</p>
            <h2 style="margin:0; color:#0f172a;">{total_hz}</h2>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div class="metric-card" style="border-left-color: #10b981;">
            <p style="margin:0; font-size:0.9rem; color:#64748b; font-weight:600;">CONTROLLED & CLOSED</p>
            <h2 style="margin:0; color:#10b981;">{controlled_hz}</h2>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown(f"""
        <div class="metric-card" style="border-left-color: #f59e0b;">
            <p style="margin:0; font-size:0.9rem; color:#64748b; font-weight:600;">PENDING REVIEW</p>
            <h2 style="margin:0; color:#f59e0b;">{review_hz + draft_hz}</h2>
        </div>
        """, unsafe_allow_html=True)
    with col4:
        st.markdown(f"""
        <div class="metric-card" style="border-left-color: #ef4444;">
            <p style="margin:0; font-size:0.9rem; color:#64748b; font-weight:600;">HIGH RESIDUAL RISKS</p>
            <h2 style="margin:0; color:#ef4444;">{high_risks}</h2>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("### 📋 Active Safety Case Overview")
    st.info(f"📍 **Report Name:** {st.session_state.cscr['doc_title']}")
    
    col_l, col_r = st.columns([2, 1])
    with col_l:
        st.markdown("### ⚠️ Quick Hazard Status Board")
        if not st.session_state.hazards:
            st.write("No hazards recorded in the safety file.")
        else:
            df_display = []
            for h in st.session_state.hazards:
                init_rating, _ = calculate_risk_rating(h["init_severity"], h["init_likelihood"])
                res_rating, _ = calculate_risk_rating(h["res_severity"], h["res_likelihood"])
                df_display.append({
                    "ID": h["id"],
                    "Title": h["title"],
                    "Owner": h["owner"],
                    "Initial Risk": init_rating,
                    "Residual Risk": res_rating,
                    "Status": h["status"]
                })
            st.table(pd.DataFrame(df_display))
            
    with col_r:
        st.markdown("### 🛠️ Portfolio Tools")
        st.write("Back up, restore, or export your complete clinical safety database.")
        
        # Download safety database as JSON
        full_backup = {
            "hazards": st.session_state.hazards,
            "cscr": st.session_state.cscr
        }
        json_str = json.dumps(full_backup, indent=4)
        st.download_button(
            label="💾 Export Safety Database (JSON)",
            data=json_str,
            file_name="clinical_safety_portfolio.json",
            mime="application/json",
            use_container_width=True
        )
        
        # Import JSON database
        uploaded_file = st.file_uploader("📥 Import Safety Database File", type="json")
        if uploaded_file is not None:
            try:
                imported_data = json.load(uploaded_file)
                if "hazards" in imported_data and "cscr" in imported_data:
                    st.session_state.hazards = imported_data["hazards"]
                    st.session_state.cscr = imported_data["cscr"]
                    st.success("✅ Safety database imported successfully!")
                    st.rerun()
                else:
                    st.error("Invalid database format. Must contain 'hazards' and 'cscr' keys.")
            except Exception as e:
                st.error(f"Failed to read file: {e}")

# ==================== TAB 2: MANAGE HAZARD LOG ====================
elif app_mode == "Manage Hazard Log":
    st.markdown("## ⚠️ Clinical Hazard Log Manager")
    
    # Form to add a new hazard
    with st.expander("➕ Register a New Hazard Entry", expanded=False):
        with st.form("new_hazard_form"):
            col1, col2 = st.columns(2)
            with col1:
                new_id = st.text_input("Hazard ID (e.g., HZ-03)", value=f"HZ-{len(st.session_state.hazards)+1:02d}")
                new_title = st.text_input("Hazard Title")
                new_desc = st.text_area("Hazard Description (What can go wrong?)")
                new_cause = st.text_area("Direct Cause of Hazard")
                new_consequence = st.text_area("Potential Clinical Consequence")
            
            with col2:
                new_owner = st.text_input("Safety Owner/Clinical Lead", value="Clinical Safety Officer")
                new_status = st.selectbox("Status", ["Draft", "Open", "Under Review", "Controlled", "Closed"])
                
                st.markdown("**Initial Risk Assessment**")
                init_sev = st.slider("Initial Severity", 1, 5, 3, help="1=Insignificant, 5=Catastrophic")
                init_lik = st.slider("Initial Likelihood", 1, 5, 3, help="1=Very Unlikely, 5=Highly Likely")
                
                st.markdown("**Control & Mitigation**")
                new_mitigation = st.text_area("Safety Mitigations / Risk Controls")
                
                st.markdown("**Residual Risk Assessment**")
                res_sev = st.slider("Residual Severity", 1, 5, 2)
                res_lik = st.slider("Residual Likelihood", 1, 5, 1)

            submitted = st.form_submit_button("Register Hazard")
            if submitted:
                if not new_title or not new_id:
                    st.error("Please supply a valid Hazard ID and Title.")
                else:
                    # Append hazard
                    st.session_state.hazards.append({
                        "id": new_id,
                        "title": new_title,
                        "desc": new_desc,
                        "cause": new_cause,
                        "consequence": new_consequence,
                        "init_severity": init_sev,
                        "init_likelihood": init_lik,
                        "mitigation": new_mitigation,
                        "res_severity": res_sev,
                        "res_likelihood": res_lik,
                        "owner": new_owner,
                        "status": new_status
                    })
                    st.success(f"Hazard {new_id} added successfully!")
                    st.rerun()

    # List & Edit existing hazards
    st.markdown("### Existing Safety Hazard Logs")
    if not st.session_state.hazards:
        st.info("No hazards found. Register one above.")
    else:
        for index, hz in enumerate(st.session_state.hazards):
            init_rating, init_color = calculate_risk_rating(hz["init_severity"], hz["init_likelihood"])
            res_rating, res_color = calculate_risk_rating(hz["res_severity"], hz["res_likelihood"])
            
            with st.container():
                col_header1, col_header2 = st.columns([4, 1])
                with col_header1:
                    st.markdown(f"#### `{hz['id']}`: {hz['title']}")
                with col_header2:
                    st.markdown(f"**Status:** `{hz['status']}`")
                
                # Internal layout of hazard detail
                col_a, col_b = st.columns(2)
                with col_a:
                    st.markdown(f"**Description:** {hz['desc']}")
                    st.markdown(f"**Causes:** {hz['cause']}")
                    st.markdown(f"**Consequences:** {hz['consequence']}")
                    st.markdown(f"**Initial Clinical Risk:** <span style='color:{init_color}; font-weight:bold;'>{init_rating}</span> (S:{hz['init_severity']} x L:{hz['init_likelihood']})", unsafe_allow_html=True)
                
                with col_b:
                    st.markdown(f"**Safety Mitigations:** {hz['mitigation']}")
                    st.markdown(f"**Residual Clinical Risk:** <span style='color:{res_color}; font-weight:bold;'>{res_rating}</span> (S:{hz['res_severity']} x L:{hz['res_likelihood']})", unsafe_allow_html=True)
                    st.markdown(f"**Lead Safety Owner:** {hz['owner']}")
                
                # Action Buttons inside Expander for Editing or Deletion
                with st.expander(f"Edit/Delete `{hz['id']}`", expanded=False):
                    edit_title = st.text_input(f"Edit Title ({hz['id']})", value=hz["title"])
                    edit_desc = st.text_area(f"Edit Description ({hz['id']})", value=hz["desc"])
                    edit_cause = st.text_area(f"Edit Cause ({hz['id']})", value=hz["cause"])
                    edit_conseq = st.text_area(f"Edit Consequence ({hz['id']})", value=hz["consequence"])
                    edit_mit = st.text_area(f"Edit Mitigation ({hz['id']})", value=hz["mitigation"])
                    edit_owner = st.text_input(f"Edit Owner ({hz['id']})", value=hz["owner"])
                    edit_status = st.selectbox(f"Edit Status ({hz['id']})", ["Draft", "Open", "Under Review", "Controlled", "Closed"], index=["Draft", "Open", "Under Review", "Controlled", "Closed"].index(hz["status"]))
                    
                    col_slide1, col_slide2 = st.columns(2)
                    with col_slide1:
                        edit_init_sev = st.slider(f"Edit Init Severity ({hz['id']})", 1, 5, hz["init_severity"])
                        edit_init_lik = st.slider(f"Edit Init Likelihood ({hz['id']})", 1, 5, hz["init_likelihood"])
                    with col_slide2:
                        edit_res_sev = st.slider(f"Edit Res Severity ({hz['id']})", 1, 5, hz["res_severity"])
                        edit_res_lik = st.slider(f"Edit Res Likelihood ({hz['id']})", 1, 5, hz["res_likelihood"])
                    
                    col_btn1, col_btn2 = st.columns(2)
                    with col_btn1:
                        if st.button(f"Save Changes to {hz['id']}", key=f"save_{hz['id']}_{index}"):
                            st.session_state.hazards[index].update({
                                "title": edit_title,
                                "desc": edit_desc,
                                "cause": edit_cause,
                                "consequence": edit_conseq,
                                "mitigation": edit_mit,
                                "owner": edit_owner,
                                "status": edit_status,
                                "init_severity": edit_init_sev,
                                "init_likelihood": edit_init_lik,
                                "res_severity": edit_res_sev,
                                "res_likelihood": edit_res_lik
                            })
                            st.success(f"Updated {hz['id']} successfully!")
                            st.rerun()
                    with col_btn2:
                        if st.button(f"🚨 Delete Hazard {hz['id']}", key=f"del_{hz['id']}_{index}"):
                            st.session_state.hazards.pop(index)
                            st.warning(f"Removed {hz['id']} from hazard records.")
                            st.rerun()
                st.markdown("---")

# ==================== TAB 3: 5X5 RISK MATRIX ====================
elif app_mode == "5x5 Risk Matrix":
    st.markdown("## 📊 5x5 Clinical Risk Assessment Matrix")
    st.write("Visual distribution of active system hazards based on Likelihood and Severity coordinates.")
    
    # Grid initialization
    matrix_cells = {s: {l: [] for l in range(1, 6)} for s in range(5, 0, -1)}
    
    # Sort hazards into grid blocks
    for hz in st.session_state.hazards:
        sev = hz["res_severity"]
        lik = hz["res_likelihood"]
        if sev in matrix_cells and lik in matrix_cells[sev]:
            matrix_cells[sev][lik].append(hz["id"])
            
    # Build beautiful Matrix View utilizing pure Streamlit & CSS styling
    html_grid = """
    <div style="font-family: sans-serif; display: flex; flex-direction: column; width: 100%; max-width: 800px; margin: auto; border: 1px solid #cbd5e1; border-radius: 8px; overflow: hidden; box-shadow: 0 4px 6px rgba(0,0,0,0.05);">
    """
    
    for s_val in range(5, 0, -1):
        html_grid += f"""<div style="display: flex; min-height: 80px; border-bottom: 1px solid #e2e8f0;">"""
        # Severity Header column on left
        html_grid += f"""<div style="width: 150px; background-color: #f1f5f9; display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 0.85rem; padding: 10px; border-right: 2px solid #cbd5e1; color:#475569;">{SEVERITY_LEVELS[s_val]}</div>"""
        
        for l_val in range(1, 6):
            # Calculate classification color
            _, cell_color = calculate_risk_rating(s_val, l_val)
            ids_in_cell = matrix_cells[s_val][l_val]
            ids_str = ", ".join(ids_in_cell) if ids_in_cell else "-"
            
            # Brighten backgrounds for cell visual representation
            bg_color = cell_color + "22"  # Add opacity to hex color
            
            html_grid += f"""
            <div style="flex: 1; background-color: {bg_color}; border-right: 1px solid #e2e8f0; display: flex; flex-direction: column; align-items: center; justify-content: center; padding: 8px;">
                <div style="font-size: 0.75rem; color: #64748b;">(S{s_val}, L{l_val})</div>
                <div style="font-weight: bold; font-size: 0.95rem; color: {cell_color}; margin-top: 4px;">{ids_str}</div>
            </div>
            """
        html_grid += "</div>"
        
    # Likelihood Footer Header Row
    html_grid += """<div style="display: flex; height: 45px; background-color: #f1f5f9;">"""
    html_grid += """<div style="width: 150px; border-right: 2px solid #cbd5e1;"></div>"""
    for l_val in range(1, 6):
        html_grid += f"""<div style="flex: 1; border-right: 1px solid #e2e8f0; display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 0.8rem; color: #475569; padding: 5px; text-align: center;">{LIKELIHOOD_LEVELS[l_val]}</div>"""
    html_grid += "</div>"
    
    html_grid += "</div>"
    
    st.markdown(html_grid, unsafe_allow_html=True)
    st.markdown("<br><p style='text-align: center; color: #64748b;'><em>Hover/Assess coordinates to inspect safety bounds and verify acceptable control measures.</em></p>", unsafe_allow_html=True)

# ==================== TAB 4: CSCR DOCUMENT BUILDER ====================
elif app_mode == "CSCR Document Builder":
    st.markdown("## 📄 Clinical Safety Case Report (CSCR) Builder")
    st.write("Modify the central safety narrative below. Utilize the **Gemini AI Auto-Draft Compiler** to draft sections instantly based on DCB0129 best practices.")
    
    st.markdown("### Document Sections & Editor")
    
    # Interactive input fields mapped to st.session_state
    doc_title = st.text_input("Report Title", value=st.session_state.cscr["doc_title"])
    
    col1, col2 = st.columns(2)
    with col1:
        exec_sum = st.text_area("1. Executive Summary", value=st.session_state.cscr["executive_summary"], height=150)
        intro = st.text_area("2. Introduction", value=st.session_state.cscr["introduction"], height=150)
        sys_desc = st.text_area("3. System Description", value=st.session_state.cscr["system_desc"], height=150)
    with col2:
        risk_proc = st.text_area("4. Clinical Risk Management Process", value=st.session_state.cscr["risk_management_process"], height=150)
        safety_args = st.text_area("5. Clinical Safety Arguments", value=st.session_state.cscr["safety_arguments"], height=150)
        concl = st.text_area("6. Conclusion & Recommendation", value=st.session_state.cscr["conclusion"], height=150)
        
    # Commit changes back to state
    if st.button("💾 Save Local Progress Draft"):
        st.session_state.cscr.update({
            "doc_title": doc_title,
            "executive_summary": exec_sum,
            "introduction": intro,
            "system_desc": sys_desc,
            "risk_management_process": risk_proc,
            "safety_arguments": safety_args,
            "conclusion": concl
        })
        st.success("Draft saved to memory!")

    st.markdown("---")
    st.markdown("### 📝 Live Compilation Viewport")
    
    # Beautiful structured report markdown rendering
    rendered_markdown = f"""
# {doc_title}

### 1. Executive Summary
{exec_sum}

### 2. Introduction
{intro}

### 3. System Description
{sys_desc}

### 4. Clinical Risk Management Process
{risk_proc}

### 5. Clinical Safety Arguments
{safety_args}

### 6. Conclusion & Recommendation
{concl}
    """
    
    st.markdown("---")
    st.markdown("### 📥 Document Export Actions")
    st.download_button(
        label="📄 Download Safety Case Report (.md)",
        data=rendered_markdown,
        file_name="clinical_safety_case_report.md",
        mime="text/markdown",
        use_container_width=True
    )
    
    # Render Preview Area with stylized container
    st.markdown("<div class='report-preview'>", unsafe_allow_html=True)
    st.markdown(rendered_markdown)
    st.markdown("</div>", unsafe_allow_html=True)

# ==================== TAB 5: AI SAFETY COPILOT & AUDITOR ====================
elif app_mode == "AI Safety Copilot & Auditor":
    st.markdown("## ✨ Gemini AI Safety Copilot")
    st.write("Leverage the advanced medical-risk-aware engine (`gemini-2.5-flash-preview-09-2025`) to run audits or draft content.")
    
    action_type = st.selectbox("Choose AI Tool Action:", [
        "Audit Current Hazard Log for Compliance",
        "Generate a Specific Clinical Hazard Record",
        "Auto-Draft Whole CSCR Narrative Template"
    ])
    
    if action_type == "Audit Current Hazard Log for Compliance":
        st.markdown("### Clinical Hazard Auditor")
        st.write("The engine evaluates all registered hazards, assesses logical risk reductions, and checks for unrealistic mitigations or vague safety statements.")
        
        if st.button("🚀 Execute Audit", use_container_width=True):
            if not gemini_key:
                st.error("Please insert your Gemini API Key in the sidebar to run the auditor.")
            else:
                with st.spinner("Analyzing hazard classifications and checking mitigations..."):
                    system_prompt = (
                        "You are an expert UK NHS Clinical Safety Officer (CSO) specialized in clinical risk "
                        "management standards DCB0129 and DCB0160. Analyze hazard logs and provide professional feedback."
                    )
                    user_query = f"""
                    Evaluate the following clinical hazard log. Look for issues like:
                    1. Vague safety controls/mitigations.
                    2. Unrealistic risk reductions (e.g., Catastrophic severity reducing to Insignificant without extreme mitigation).
                    3. Under-reporting common health IT safety hazards.
                    
                    Hazard Log JSON Data:
                    {json.dumps(st.session_state.hazards, indent=2)}
                    
                    Provide structural suggestions and constructive improvements in clear markdown.
                    """
                    audit_result = call_gemini_api(gemini_key, system_prompt, user_query)
                    st.markdown("### 📋 AI CSO Audit Findings")
                    st.markdown(audit_result)
                    
    elif action_type == "Generate a Specific Clinical Hazard Record":
        st.markdown("### Clinical Hazard Generator")
        hazard_type = st.text_input("Enter clinical system topic (e.g., 'E-Prescribing System', 'Patient Queue tracker', 'PACS Imaging Gateway')")
        
        if st.button("✨ Draft New Hazard Log Entry", use_container_width=True):
            if not gemini_key:
                st.error("Please insert your Gemini API Key in the sidebar.")
            elif not hazard_type:
                st.error("Please write a system topic first.")
            else:
                with st.spinner("Compiling DCB0129-compliant hazard profile..."):
                    system_prompt = (
                        "You are an expert Clinical Safety Officer. Generate a single hazard log structure strictly formatted as JSON."
                        "The JSON object must contain these keys: 'id', 'title', 'desc', 'cause', 'consequence', 'init_severity' (1-5), "
                        "'init_likelihood' (1-5), 'mitigation', 'res_severity' (1-5), 'res_likelihood' (1-5), 'owner', 'status' ('Draft')."
                    )
                    user_query = f"Draft a realistic health IT hazard for this topic: {hazard_type} following UK standards."
                    ai_raw_json = call_gemini_api(gemini_key, system_prompt, user_query)
                    
                    try:
                        # Clean JSON from markdown block markers if present
                        cleaned_json = ai_raw_json.strip()
                        if cleaned_json.startswith("```json"):
                            cleaned_json = cleaned_json[7:]
                        if cleaned_json.endswith("```"):
                            cleaned_json = cleaned_json[:-3]
                            
                        new_h_data = json.loads(cleaned_json)
                        st.session_state.hazards.append(new_h_data)
                        st.success(f"Successfully integrated {new_h_data['id']}: {new_h_data['title']} into your active Safety File!")
                        st.json(new_h_data)
                    except Exception as e:
                        st.error("AI returned text that was not strictly JSON. Here is the raw text instead:")
                        st.write(ai_raw_json)

    elif action_type == "Auto-Draft Whole CSCR Narrative Template":
        st.markdown("### CSCR Whole Case Draft Builder")
        st.write("Generates clinical justifications for the CSCR based on active hazards.")
        
        if st.button("✨ Auto-Draft Document Narrative", use_container_width=True):
            if not gemini_key:
                st.error("Please insert your Gemini API Key in the sidebar.")
            else:
                with st.spinner("Drafting full Safety Case Report..."):
                    system_prompt = (
                        "You are an NHS Clinical Safety Officer. Write detailed narrative sections for a "
                        "Clinical Safety Case Report (CSCR) compliant with DCB0129. Generate structured clinical prose."
                    )
                    user_query = f"""
                    Based on these active system hazards, write professional draft sections for:
                    - Executive Summary
                    - Introduction & System Description
                    - Clinical Risk Management Process
                    - Safety Arguments & Controls
                    - Conclusion
                    
                    Hazards Data:
                    {json.dumps(st.session_state.hazards, indent=2)}
                    
                    Return a JSON object containing the keys: 'doc_title', 'executive_summary', 'introduction', 'system_desc', 'risk_management_process', 'safety_arguments', 'conclusion'.
                    """
                    ai_raw_json = call_gemini_api(gemini_key, system_prompt, user_query)
                    
                    try:
                        cleaned_json = ai_raw_json.strip()
                        if cleaned_json.startswith("```json"):
                            cleaned_json = cleaned_json[7:]
                        if cleaned_json.endswith("```"):
                            cleaned_json = cleaned_json[:-3]
                            
                        new_cscr_data = json.loads(cleaned_json)
                        st.session_state.cscr.update(new_cscr_data)
                        st.success("Draft CSCR imported! Check the 'CSCR Document Builder' tab to review and edit the draft.")
                        st.json(new_cscr_data)
                    except Exception as e:
                        st.error("AI returned text that was not strictly JSON. Here is the raw text instead:")
                        st.write(ai_raw_json)

# Footer Layout
st.markdown("---")
st.markdown(
    "<p style='text-align: center; font-size: 0.85rem; color: #94a3b8;'>"
    "🛡️ Clinical Safety Hub (DCB0129) is designed to structure safety files for review by clinical authorities. "
    "Always rely on a qualified Clinical Safety Officer (CSO) to audit safety cases before final release."
    "</p>", 
    unsafe_allow_html=True
)