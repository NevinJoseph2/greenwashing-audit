import streamlit as st
import pdfplumber
import pandas as pd
import os
import re
import plotly.express as px
import plotly.graph_objects as go

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="Greenwashing Detector AI", layout="wide", page_icon="🌿")

# --- CUSTOM CSS ---
st.markdown("""
<style>
    .stApp { background-color: #0E1117; color: white; }
    .metric-card {
        background-color: #262730;
        padding: 20px;
        border-radius: 10px;
        border: 1px solid #444;
        text-align: center;
        margin-bottom: 20px;
    }
    .evidence-box {
        background-color: #1E1E1E;
        padding: 15px;
        border-radius: 5px;
        font-family: monospace;
        font-size: 0.85em;
        color: #00CC96;
        border-left: 3px solid #00CC96;
    }
</style>
""", unsafe_allow_html=True)

# --- DATA EXTRACTION ENGINE ---
@st.cache_data
def process_pdfs(folder_path):
    data = []
    
    if not os.path.exists(folder_path):
        return pd.DataFrame()

    files = [f for f in os.listdir(folder_path) if f.endswith('.pdf')]
    
    for filename in files:
        # --- COMPANY NAME MAPPING (Formal Names) ---
        name_map = {
            "acc.pdf": "ACC Limited",
            "adani green.pdf": "Adani Green Energy Ltd.",
            "Adani power.pdf": "Adani Power Ltd.",
            "ambuja.pdf": "Ambuja Cements Ltd.",
            "BPCL.pdf": "Bharat Petroleum Corporation Ltd.",
            "Hindalco.pdf": "Hindalco Industries Ltd.",
            "HPCL.pdf": "Hindustan Petroleum Corp. Ltd.",
            "IOCL.pdf": "Indian Oil Corporation Ltd.",
            "Jindal Steel.pdf": "Jindal Steel & Power Ltd.",
            "Jsw energy.pdf": "JSW Energy Ltd.",
            "Jsw Steel.pdf": "JSW Steel Ltd.",
            "Nacl.pdf": "National Aluminium Company Ltd.",
            "Nhpc.pdf": "NHPC Limited",
            "Nmdc.pdf": "NMDC Limited",
            "NTPC.pdf": "NTPC Limited",
            "oil india.pdf": "Oil India Limited",
            "Ongc.pdf": "Oil and Natural Gas Corporation",
            "Reliance.pdf": "Reliance Industries Ltd.",
            "SAIL.pdf": "Steel Authority of India Ltd.",
            "Shree cement.pdf": "Shree Cement Ltd.",
            "Sjvn.pdf": "SJVN Limited",
            "Tata power.pdf": "Tata Power Company Ltd.",
            "Tata Steel.pdf": "Tata Steel Ltd.",
            "Ultratech.pdf": "UltraTech Cement Ltd.",
            "Vedanta.pdf": "Vedanta Limited"
        }
        
        # Use formal name if available, otherwise fallback to filename
        company_name = name_map.get(filename, filename.replace(".pdf", "").replace("_", " ").title())
        path = os.path.join(folder_path, filename)
        
        full_text = ""
        # Extraction Variables
        csr_spend = 0.0
        renewable_energy = 0.0
        total_energy = 1.0 
        ghg_emissions = 0.0
        policy_count = 0
        
        # Evidence Snippets (For "Show Me" feature)
        csr_snippet = "Not Found"
        renew_snippet = "Not Found"
        
        try:
            with pdfplumber.open(path) as pdf:
                # Read first 5 pages for summary data to save time, or all if needed
                for page in pdf.pages[:10]: 
                    text = page.extract_text()
                    full_text += text
                    
                    # Regex Extraction with snippet capturing
                    if csr_spend == 0:
                        csr_match = re.search(r"(Community Spending|CSR Expenditure).*?([\d,]+\.?\d*)", text, re.IGNORECASE)
                        if csr_match: 
                            csr_spend = float(csr_match.group(2).replace(',', ''))
                            csr_snippet = csr_match.group(0) # Capture the text found

                    if renewable_energy == 0:
                        ren_match = re.search(r"(Renewable Energy Use|Renewable Energy).*?([\d,]+\.?\d*)", text, re.IGNORECASE)
                        if ren_match: 
                            renewable_energy = float(ren_match.group(2).replace(',', ''))
                            renew_snippet = ren_match.group(0)

                    if total_energy == 1.0:
                        en_match = re.search(r"(Total Energy Consumption|Energy Consumption).*?([\d,]+\.?\d*)", text, re.IGNORECASE)
                        if en_match: total_energy = float(en_match.group(2).replace(',', ''))

                    if ghg_emissions == 0:
                        ghg_match = re.search(r"(GHG Scope 1|Scope 1 Emissions).*?([\d,]+\.?\d*)", text, re.IGNORECASE)
                        if ghg_match: ghg_emissions = float(ghg_match.group(2).replace(',', ''))

            # Policy Counting
            policies = ['Climate Change Policy', 'Biodiversity Policy', 'Water Policy', 'Human Rights Policy', 'Whistle Blower Policy']
            for p in policies:
                if re.search(rf"{p}.*?Yes", full_text, re.IGNORECASE | re.DOTALL):
                    policy_count += 1
            
            # Scoring Logic
            talk_score = (policy_count / len(policies)) * 100
            
            # Walk Score Logic (Simplified for Demo)
            renew_mix = (renewable_energy / total_energy) * 100 if total_energy > 10 else 0
            csr_score = min((csr_spend / 500) * 50, 50) # Cap at 50 points
            walk_score = renew_mix + csr_score
            if walk_score > 100: walk_score = 100
            
            risk_score = talk_score - walk_score
            if risk_score < 0: risk_score = 0
            
            data.append({
                "Company": company_name,
                "Risk Score": round(risk_score, 1),
                "Talk Score": round(talk_score, 1),
                "Walk Score": round(walk_score, 1),
                "CSR Spend (Cr)": csr_spend,
                "Renewable Energy": renewable_energy,
                "Total Energy": total_energy,
                "GHG Scope 1": ghg_emissions,
                "Policies": policy_count,
                "CSR Evidence": csr_snippet,
                "Renewable Evidence": renew_snippet
            })
            
        except Exception:
            continue

    return pd.DataFrame(data)

# --- LOAD DATA ---
df = process_pdfs('.')

# --- MAIN LAYOUT ---
st.title("🌿 AI-Based Greenwashing Detection System")
st.markdown("### Financial Statement Analysis & Forensic Auditing Project")
st.write("This tool utilizes NLP to audit ESG reports, detecting discrepancies between qualitative claims ('Talk') and quantitative spending ('Walk').")

if not df.empty:
    # TABS FOR ORGANIZED VIEW
    tab1, tab2, tab3 = st.tabs(["📊 Audit Dashboard", "📂 Raw Data & Downloads", "📘 Methodology"])

    with tab1:
        st.divider()
        col_search, col_space = st.columns([1, 2])
        with col_search:
            selected_company = st.selectbox("🔎 Select Company to Audit:", df['Company'].unique())
        
        comp_data = df[df['Company'] == selected_company].iloc[0]

        # --- SCORECARDS ---
        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown(f"<div class='metric-card'><h3>Greenwashing Risk</h3><h1 style='color:#FF4B4B'>{comp_data['Risk Score']}</h1><p>0 = Low Risk | 100 = High Risk</p></div>", unsafe_allow_html=True)
        with c2:
            st.markdown(f"<div class='metric-card'><h3>The 'Talk' Score</h3><h1 style='color:#4B90FF'>{comp_data['Talk Score']}</h1><p>Based on Policy Declarations</p></div>", unsafe_allow_html=True)
        with c3:
            st.markdown(f"<div class='metric-card'><h3>The 'Walk' Score</h3><h1 style='color:#00CC96'>{comp_data['Walk Score']}</h1><p>Based on Financial Spending</p></div>", unsafe_allow_html=True)

        # --- DEEP DIVE ---
        st.subheader(f"📝 Forensic Evidence for {selected_company}")
        
        col_ev1, col_ev2 = st.columns(2)
        with col_ev1:
            st.info("🗣 **Qualitative Analysis (Policies)**")
            st.write(f"Policies Enacted: **{int(comp_data['Policies'])} / 5**")
            st.progress(int(comp_data['Talk Score']))
            st.caption("AI scan of: Climate, Biodiversity, Water, Human Rights, Whistleblower policies.")

        with col_ev2:
            st.warning("🏃 **Quantitative Analysis (Financials)**")
            
            st.write(f"💰 **CSR Spending:** ₹{comp_data['CSR Spend (Cr)']} Cr")
            with st.expander("View Source Text"):
                st.markdown(f"<div class='evidence-box'>{comp_data['CSR Evidence']}</div>", unsafe_allow_html=True)
            
            st.write(f"⚡ **Renewable Energy:** {comp_data['Renewable Energy']} units")
            with st.expander("View Source Text"):
                st.markdown(f"<div class='evidence-box'>{comp_data['Renewable Evidence']}</div>", unsafe_allow_html=True)

        # --- SCATTER PLOT ---
        st.divider()
        st.subheader("📍 Comparative Analysis: Industry Landscape")
        fig = px.scatter(df, x="Talk Score", y="Walk Score", color="Risk Score", 
                         size="CSR Spend (Cr)", hover_name="Company",
                         color_continuous_scale="RdYlGn_r", title="Talk vs. Walk Matrix (Top Right is Ideal)")
        fig.add_annotation(x=comp_data['Talk Score'], y=comp_data['Walk Score'], text=selected_company, showarrow=True, arrowhead=1)
        fig.update_layout(paper_bgcolor="#0E1117", plot_bgcolor="#1E1E1E", font={'color': "white"}, height=500)
        st.plotly_chart(fig, use_container_width=True)

    with tab2:
        st.subheader("📂 Full Dataset")
        st.dataframe(df)
        
        # Download Button
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Download Audit Report (CSV)",
            data=csv,
            file_name='greenwashing_audit_report.csv',
            mime='text/csv',
        )

    with tab3:
        st.markdown("""
        ### Project Methodology
        **1. Variable of Interest:**
        - We extracted **Community Spending (CSR)** and **Renewable Energy Use** from Annual Reports.
        
        **2. The 'Talk' Score (NLP):**
        - Calculated by scanning policy disclosure tables for affirmations ('Yes') on Climate, Biodiversity, and Human Rights policies.
        
        **3. The 'Walk' Score (Financials):**
        - Calculated using a weighted average of CSR intensity and Renewable Energy mix.
        
        **4. Greenwashing Detection:**
        - Defined as the divergence between the Talk Score and the Walk Score. High divergence = High Risk.
        """)

else:

    st.warning("⚠️ No data found. Please ensure the 'esg_reports' folder exists and contains PDFs.")
