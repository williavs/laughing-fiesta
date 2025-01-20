"""
V3 Business Search Platform
"""
import streamlit as st
from pathlib import Path

# Constants and configurations
PAGES = ["Home", "Business Search", "About"]
ASSETS_DIR = Path(__file__).parent / "assets"

@st.cache_data
def load_static_logo():
    """Cache the static logo loading"""
    try:
        return str(ASSETS_DIR / "logo.png")
    except Exception:
        return None

def render_home_page():
    """Render the home page content"""
    # Header with logo
   
    st.title("Welcome to V3 Business Search")
    
    st.markdown("""
    ### 🎯 Free SMB Lead Generation Tool
    
    Get instant lists of small and medium-sized businesses for your sales outreach. 
    Perfect for salespeople targeting local service providers and professionals.
    
    #### 📋 How It Works:
    1. Select your target industry (e.g., dentists, plumbers, accountants)
    2. Enter the city and state
    3. Choose number of results (please keep under 100 for API courtesy)
    4. Get business names, websites, and phone numbers
    5. Export your list
    
    #### ⚠️ Important Notes:
    - Each search returns: Business Name, Website URL, Phone Number
    - Focuses on SMB data (not Fortune 500 or large enterprises)
    - Base data from public web sources
    - Recommended: Enrich data through [Clay](https://clay.com) or similar services
    - Keep searches under 100 results to be API-friendly
    
    #### ✨ Features
    """)
    
    # Render features in columns
    features_content(st.columns(3))
    
    st.markdown("---")
    
    # Call to action
    st.markdown("### Ready to build your prospect list?")
    if st.button("Launch Business Search", key="launch_search"):
        st.session_state.current_page = "Business Search"
        st.rerun()

def features_content(columns):
    """Render the features content in columns"""
    col1, col2, col3 = columns
    
    with col1:
        st.markdown("""
        ##### 🎯 Quick Lists
        - Industry-specific targeting
        - Local business focus
        - SMB-optimized results
        """)
    
    with col2:
        st.markdown("""
        ##### 📊 Data Points
        - Business names
        - Website URLs
        - Phone numbers
        """)
    
    with col3:
        st.markdown("""
        ##### 💼 Export Ready
        - CSV export
        - Clay compatible
        - Easy enrichment
        """)

@st.cache_resource
def get_scraper():
    """Cache the scraper import"""
    from yello_utils import scrape_combined
    return scrape_combined

def render_business_search():
    """Render the business search page"""
    st.title("Business Search")
    
    # Search controls
    col1, col2 = st.columns(2)
    
    with col1:
        keyword = st.text_input("Search Term", "Accountant")
        location = st.text_input("Location", "Seattle, WA")
    
    with col2:
        limit = st.number_input("Number of Businesses to Find", min_value=1, max_value=100, value=20)
    
    if st.button("Start Search", key="search_button"):
        try:
            scrape_combined = get_scraper()
            results_df = scrape_combined(keyword, location, limit)
            
            if not results_df.empty:
                st.subheader("Results")
                st.dataframe(results_df)
                
                # Export options
                render_export_options(results_df)
            else:
                st.warning("No results found.")
                
        except Exception as e:
            st.error(f"An error occurred: {str(e)}")

def render_export_options(results_df):
    """Handle export options for search results"""
    st.subheader("Export Data")
    if st.button("Export to CSV"):
        output_path = "business_search_data.csv"
        results_df.to_csv(output_path, index=False)
        st.success(f"Data exported to {output_path}")
        
        with open(output_path, "rb") as file:
            st.download_button(
                label="Download CSV",
                data=file,
                file_name=output_path,
                mime="text/csv"
            )

@st.cache_resource
def load_about_module():
    """Cache the about module import"""
    import importlib.util
    import sys
    
    spec = importlib.util.spec_from_file_location("about", "about.py")
    about = importlib.util.module_from_spec(spec)
    sys.modules["about"] = about
    spec.loader.exec_module(about)
    return about

def main():
    # Page configuration - must be first Streamlit command
    st.set_page_config(
        page_title="V3 Business Search | Powered by V3 AI",
        page_icon="assets/logo.png",
        layout="wide"
    )
    
    # Initialize session state
    if 'current_page' not in st.session_state:
        st.session_state.current_page = "Home"
    
    # Display static logo in sidebar
    logo_path = load_static_logo()
    if logo_path:
        st.sidebar.image(logo_path, width=400)
    
    # Navigation
    page = st.sidebar.selectbox(
        "Navigate",
        PAGES,
        key="navigation",
        index=PAGES.index(st.session_state.current_page)
    )
    
    # Add custom tools section in sidebar
    st.sidebar.markdown("---")
    st.sidebar.markdown("""
    ### 🛠️ Need Custom Tools?
    
    This tool was built by [WillyV3](https://www.linkedin.com/in/willyv3/), founder of [V3 AI](https://v3-ai.com).
    We specialize in building custom data tools for:
    
    - 🎯 Go-to-Market Intelligence
    - 🔍 Lead Generation & Enrichment
    - 📊 Market Research Automation
    - 🤖 AI-Powered Data Processing
    - 🔄 Workflow Automation
    
    #### Featured Projects:
    - [V3 AI Platform](https://v3-ai.com) - Enterprise AI Solutions
    - [PM Feels](https://pmfeels.com) - Product Management Tools
    - [Sagedoc](https://sagedoc.me) - AI Documentation
    
    #### Let's Connect:
    [![GitHub](https://img.shields.io/badge/GitHub-100000?style=for-the-badge&logo=github&logoColor=white)](https://github.com/williavs)
    [![LinkedIn](https://img.shields.io/badge/LinkedIn-0077B5?style=for-the-badge&logo=linkedin&logoColor=white)](https://www.linkedin.com/in/willyv3/)
    """)
    
    # Update session state
    st.session_state.current_page = page
    
    # Render appropriate page
    if page == "Home":
        render_home_page()
    elif page == "Business Search":
        render_business_search()
    else:  # About page
        about = load_about_module()

if __name__ == "__main__":
    main()