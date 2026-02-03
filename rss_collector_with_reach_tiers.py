"""
Streamlit Web App - Carbon Measures RSS Feed Collector
No terminal required - runs in your browser!
"""

import streamlit as st
import feedparser
import pandas as pd
from datetime import datetime, timedelta
from urllib.parse import quote_plus
import time
import json
from dateutil import parser as date_parser
import re

# Page configuration
st.set_page_config(
    page_title="RSS Feed Collector",
    page_icon="📰",
    layout="wide"
)

# Initialize session state for keywords
if 'custom_keywords' not in st.session_state:
    st.session_state['custom_keywords'] = []


def categorize_source(source_name):
    """
    Categorize news sources into different types
    Returns: category name
    """
    source_lower = source_name.lower()
    
    # Mainstream Media
    mainstream = [
        'cnn', 'bbc', 'reuters', 'associated press', 'ap news', 'bloomberg',
        'financial times', 'wall street journal', 'wsj', 'new york times', 'nyt',
        'washington post', 'guardian', 'telegraph', 'fox news', 'nbc', 'abc',
        'cbs', 'npr', 'pbs', 'usa today', 'time', 'newsweek', 'economist',
        'forbes', 'fortune', 'business insider', 'cnbc', 'marketwatch', 'axios'
    ]
    
    # Trade Press / Industry Publications
    trade_press = [
        'techcrunch', 'the verge', 'wired', 'ars technica', 'zdnet', 'cnet',
        'venturebeat', 'recode', 'engadget', 'gizmodo', 'mashable', 'greentech',
        'renewable energy world', 'energy storage news', 'utility dive', 'power',
        'pv magazine', 'solar power world', 'wind power monthly', 'cleantechnica',
        'electrek', 'green car reports', 'inside evs', 'automotive news',
        'trade', 'industry week', 'manufacturing', 'chemical', 'engineering'
    ]
    
    # Blogs and Independent Media
    blogs = [
        'medium', 'substack', 'blog', 'blogger', 'wordpress', 'tumblr',
        'ghost', 'writefreely', 'newsletter', 'independent', 'personal site'
    ]
    
    # Government and Academic
    government_academic = [
        '.gov', 'government', 'department of', 'ministry of', 'agency',
        'university', 'college', 'institute', 'research', 'academic',
        '.edu', 'journal', 'nature', 'science', 'pnas', 'arxiv'
    ]
    
    # NGOs and Think Tanks
    ngo_thinktank = [
        'greenpeace', 'wwf', 'nrdc', 'sierra club', 'friends of the earth',
        'brookings', 'cato', 'heritage', 'cfr', 'carnegie', 'rand',
        'center for', 'institute for', 'foundation', 'council on'
    ]
    
    # Local and Regional News
    local_regional = [
        'tribune', 'gazette', 'herald', 'times', 'post', 'news', 'daily',
        'chronicle', 'journal', 'observer', 'examiner', 'courier', 'press',
        'local', 'regional', 'community', 'county', 'city'
    ]
    
    # Check each category
    for term in mainstream:
        if term in source_lower:
            return "Mainstream Media"
    
    for term in trade_press:
        if term in source_lower:
            return "Trade Press"
    
    for term in government_academic:
        if term in source_lower:
            return "Government/Academic"
    
    for term in ngo_thinktank:
        if term in source_lower:
            return "NGO/Think Tank"
    
    for term in blogs:
        if term in source_lower:
            return "Blogs/Independent"
    
    for term in local_regional:
        if term in source_lower:
            return "Local/Regional"
    
    # Default category
    return "Other"


def calculate_reach_tier(source_name):
    """
    Calculate reach tier based on reputation and authority
    Returns: dict with tier, reach_estimate, reach_score, and reasoning
    
    Tier 1: Global news wires & papers of record (90-100 points)
    Tier 2: Major industry leaders & established media (60-89 points)
    Tier 3: Respected niche/trade publications (30-59 points)
    Tier 4: Smaller outlets, blogs, unknown sources (1-29 points)
    """
    source_lower = source_name.lower()
    
    # TIER 1: Global News Wires & Papers of Record
    # Criteria: Primary sources, 100+ Pulitzers, international bureaus, cited by others
    tier1_sources = {
        # Global News Wires (primary sources - others cite them)
        'reuters': {'score': 98, 'reason': 'Global news wire, 2,500+ journalists'},
        'associated press': {'score': 98, 'reason': 'Primary news wire, 1,400+ newspaper clients'},
        'ap news': {'score': 98, 'reason': 'Primary news wire, 1,400+ newspaper clients'},
        'bloomberg': {'score': 97, 'reason': 'Financial news primary source, Bloomberg Terminal standard'},
        'agence france-presse': {'score': 96, 'reason': 'International news wire'},
        'afp': {'score': 96, 'reason': 'International news wire'},
        
        # Papers of Record (historical authority, 50+ Pulitzers)
        'new york times': {'score': 97, 'reason': 'US paper of record, 137 Pulitzers'},
        'nyt': {'score': 97, 'reason': 'US paper of record, 137 Pulitzers'},
        'wall street journal': {'score': 96, 'reason': 'Business paper of record, 39 Pulitzers'},
        'wsj': {'score': 96, 'reason': 'Business paper of record, 39 Pulitzers'},
        'washington post': {'score': 96, 'reason': 'Political paper of record, 69 Pulitzers'},
        'financial times': {'score': 95, 'reason': 'International business paper of record'},
        'the guardian': {'score': 94, 'reason': 'UK paper of record, international reach'},
        'guardian': {'score': 94, 'reason': 'UK paper of record, international reach'},
        
        # Major International Broadcasters
        'bbc': {'score': 95, 'reason': 'Global public broadcaster, 6,000+ journalists'},
        'bbc news': {'score': 95, 'reason': 'Global public broadcaster, 6,000+ journalists'},
        'cnn': {'score': 93, 'reason': 'Global breaking news leader, international bureaus'},
        'the economist': {'score': 94, 'reason': 'Global influence, 175+ years, elite readership'},
        'economist': {'score': 94, 'reason': 'Global influence, 175+ years, elite readership'},
    }
    
    # TIER 2: Major Industry Leaders & Established Media
    # Criteria: Industry authority, 20+ reporters, professional audience, awards/recognition
    tier2_sources = {
        # Major Business & Financial Media
        'forbes': {'score': 85, 'reason': 'Major business publication, global reach'},
        'fortune': {'score': 84, 'reason': 'Established business magazine, Fortune 500 list'},
        'business insider': {'score': 82, 'reason': 'Major digital business news, 150M+ readers'},
        'cnbc': {'score': 85, 'reason': 'Leading financial news network'},
        'marketwatch': {'score': 80, 'reason': 'Major financial news site, Dow Jones owned'},
        'barrons': {'score': 83, 'reason': 'Premium financial weekly, WSJ sister publication'},
        
        # Major Tech Publications
        'techcrunch': {'score': 85, 'reason': 'VC/startup industry standard, 25+ reporters'},
        'the verge': {'score': 83, 'reason': 'Leading tech/culture publication, Vox Media'},
        'wired': {'score': 84, 'reason': 'Established tech magazine, Condé Nast, 30+ years'},
        'ars technica': {'score': 82, 'reason': 'Deep tech journalism, expert audience'},
        'recode': {'score': 81, 'reason': 'Tech industry authority, Vox Media'},
        
        # Established General News
        'axios': {'score': 84, 'reason': 'DC insider news, professional readership'},
        'politico': {'score': 85, 'reason': 'Political news authority, required reading in DC'},
        'the hill': {'score': 80, 'reason': 'Congressional news standard'},
        'npr': {'score': 86, 'reason': 'National public radio, 1,000+ member stations'},
        'pbs': {'score': 84, 'reason': 'Public broadcasting, trusted journalism'},
        'time': {'score': 82, 'reason': 'Historic news magazine, 100+ years'},
        'newsweek': {'score': 78, 'reason': 'Established news magazine'},
        'abc news': {'score': 83, 'reason': 'Major broadcast network'},
        'nbc news': {'score': 83, 'reason': 'Major broadcast network'},
        'cbs news': {'score': 83, 'reason': 'Major broadcast network'},
        'fox news': {'score': 81, 'reason': 'Major cable news network'},
        'usa today': {'score': 80, 'reason': 'National newspaper, wide circulation'},
        
        # Climate/Energy Leaders
        'canary media': {'score': 78, 'reason': 'Climate journalism leader, professional audience'},
        'utility dive': {'score': 79, 'reason': 'Utility industry standard'},
        'greentech media': {'score': 80, 'reason': 'Clean energy authority (now Wood Mackenzie)'},
        'renewable energy world': {'score': 77, 'reason': 'Renewable energy industry standard'},
        'energy storage news': {'score': 76, 'reason': 'Battery/storage industry publication'},
        
        # Other Major Industry Publications
        'the information': {'score': 82, 'reason': 'Premium tech journalism, insider access'},
        'protocol': {'score': 78, 'reason': 'Tech policy authority'},
        'venturebeat': {'score': 79, 'reason': 'Tech/AI journalism, 20+ years'},
        'zdnet': {'score': 77, 'reason': 'Enterprise tech authority'},
        'cnet': {'score': 78, 'reason': 'Consumer tech authority, 25+ years'},
    }
    
    # TIER 3: Respected Niche/Trade Publications
    # Criteria: Established in niche, cited by peers, 5-20 reporters
    tier3_sources = {
        # Tech/Digital Media
        'engadget': {'score': 55, 'reason': 'Consumer tech blog, 20+ years'},
        'gizmodo': {'score': 54, 'reason': 'Tech/science blog, Gizmodo Media'},
        'mashable': {'score': 55, 'reason': 'Digital culture publication'},
        'the next web': {'score': 52, 'reason': 'Tech industry blog'},
        '9to5mac': {'score': 50, 'reason': 'Apple news specialist'},
        'macrumors': {'score': 48, 'reason': 'Apple news community'},
        
        # Climate/Energy Niche
        'cleantechnica': {'score': 55, 'reason': 'Clean tech blog, respected in community'},
        'electrek': {'score': 56, 'reason': 'EV news leader, 9to5 network'},
        'green car reports': {'score': 53, 'reason': 'EV/hybrid specialist'},
        'inside evs': {'score': 54, 'reason': 'EV industry coverage'},
        'pv magazine': {'score': 52, 'reason': 'Solar industry publication'},
        'solar power world': {'score': 51, 'reason': 'Solar trade magazine'},
        'wind power monthly': {'score': 50, 'reason': 'Wind energy trade publication'},
        
        # Business/Industry Trades
        'industry week': {'score': 52, 'reason': 'Manufacturing trade publication'},
        'automotive news': {'score': 55, 'reason': 'Auto industry trade publication'},
        'chemical engineering': {'score': 50, 'reason': 'Chemical industry publication'},
        'manufacturing.net': {'score': 48, 'reason': 'Manufacturing trade media'},
        
        # Regional/Local Major
        'los angeles times': {'score': 58, 'reason': 'Major regional paper, 46 Pulitzers'},
        'chicago tribune': {'score': 56, 'reason': 'Major regional paper, 27 Pulitzers'},
        'boston globe': {'score': 56, 'reason': 'Major regional paper, 27 Pulitzers'},
        'san francisco chronicle': {'score': 54, 'reason': 'Major regional paper'},
        'miami herald': {'score': 53, 'reason': 'Major regional paper, 22 Pulitzers'},
        'dallas morning news': {'score': 52, 'reason': 'Major regional paper, 9 Pulitzers'},
    }
    
    # Check Tier 1
    for source_key, data in tier1_sources.items():
        if source_key in source_lower:
            return {
                'tier': 1,
                'reach_estimate': '10M+ monthly',
                'reach_score': data['score'],
                'reach_label': 'VERY HIGH',
                'reasoning': data['reason']
            }
    
    # Check Tier 2
    for source_key, data in tier2_sources.items():
        if source_key in source_lower:
            return {
                'tier': 2,
                'reach_estimate': '1M-10M monthly',
                'reach_score': data['score'],
                'reach_label': 'HIGH',
                'reasoning': data['reason']
            }
    
    # Check Tier 3
    for source_key, data in tier3_sources.items():
        if source_key in source_lower:
            return {
                'tier': 3,
                'reach_estimate': '100K-1M monthly',
                'reach_score': data['score'],
                'reach_label': 'MEDIUM',
                'reasoning': data['reason']
            }
    
    # Default: Tier 4 (Unknown/Small sources)
    return {
        'tier': 4,
        'reach_estimate': '<100K monthly',
        'reach_score': 20,
        'reach_label': 'LOW',
        'reasoning': 'Smaller outlet or unknown source'
    }


def parse_boolean_search(search_term):
    """
    Parse boolean search into Google News format
    Supports: AND, OR, NOT operators
    Examples:
    - "climate AND policy" → "climate policy"
    - "tesla OR spacex" → "tesla OR spacex"  
    - "AI NOT crypto" → "AI -crypto"
    """
    # Replace NOT with - (Google's exclude operator)
    search_term = search_term.replace(' NOT ', ' -')
    # AND is implicit in Google, but we keep it for clarity
    search_term = search_term.replace(' AND ', ' ')
    # OR stays as is (Google supports OR)
    return search_term


@st.cache_data(ttl=3600)  # Cache for 1 hour
def fetch_google_news_rss(keyword):
    """Fetch articles from Google News RSS for a specific keyword"""
    articles = []
    # Parse boolean operators
    parsed_keyword = parse_boolean_search(keyword)
    url = f"https://news.google.com/rss/search?q={quote_plus(parsed_keyword)}&hl=en-US&gl=US&ceid=US:en"
    
    try:
        feed = feedparser.parse(url)
        
        for entry in feed.entries:
            # Parse the published date
            published_str = entry.get('published', '')
            published_date = None
            
            try:
                if published_str:
                    published_date = date_parser.parse(published_str)
            except:
                pass
            
            source_name = entry.get('source', {}).get('title', 'Unknown')
            reach_data = calculate_reach_tier(source_name)
            
            article = {
                'Keyword': keyword,
                'Title': entry.get('title', ''),
                'URL': entry.get('link', ''),
                'Published': published_str,
                'Published_Date': published_date,
                'Source': source_name,
                'Source_Category': categorize_source(source_name),
                'Reach_Tier': reach_data['tier'],
                'Reach_Estimate': reach_data['reach_estimate'],
                'Reach_Score': reach_data['reach_score'],
                'Reach_Label': reach_data['reach_label'],
                'Reach_Reasoning': reach_data['reasoning'],
                'Description': entry.get('summary', '')
            }
            articles.append(article)
    except Exception as e:
        st.error(f"Error fetching {keyword}: {e}")
    
    return articles


def collect_all_feeds(progress_bar, status_text, keywords):
    """Collect RSS feeds for all keywords"""
    all_articles = []
    total_keywords = len(keywords)
    
    for i, keyword in enumerate(keywords):
        status_text.text(f"Fetching articles for: {keyword}")
        articles = fetch_google_news_rss(keyword)
        all_articles.extend(articles)
        progress_bar.progress((i + 1) / total_keywords)
        time.sleep(1)  # Be nice to Google's servers
    
    # Remove duplicates based on URL
    df = pd.DataFrame(all_articles)
    if not df.empty:
        df = df.drop_duplicates(subset=['URL'], keep='first')
    
    return df


def main():
    # Header
    st.title("📰 RSS Feed Collector")
    st.markdown("Collect and analyze RSS feeds from Google News with custom keywords and boolean search")
    
    # Sidebar
    st.sidebar.header("⚙️ Keyword Management")
    
    # Add new keyword
    with st.sidebar.expander("➕ Add New Keyword", expanded=False):
        st.markdown("""
        **Boolean Search Operators:**
        - `AND` - both terms must appear (e.g., `climate AND policy`)
        - `OR` - either term can appear (e.g., `solar OR wind`)
        - `NOT` - exclude term (e.g., `EV NOT Tesla`)
        
        You can combine operators: `(climate OR environment) AND policy NOT Trump`
        """)
        new_keyword = st.text_input("Enter keyword to monitor:", key="new_keyword_input", 
                                    placeholder="e.g., climate AND policy")
        if st.button("Add Keyword"):
            if new_keyword and new_keyword.strip():
                if new_keyword.strip() not in st.session_state['custom_keywords']:
                    st.session_state['custom_keywords'].append(new_keyword.strip())
                    st.success(f"Added: {new_keyword}")
                    st.rerun()
                else:
                    st.warning("Keyword already exists!")
            else:
                st.warning("Please enter a keyword")
    
    # Display and manage current keywords
    st.sidebar.subheader("📋 Current Keywords")
    st.sidebar.text(f"Total: {len(st.session_state['custom_keywords'])}")
    
    # Show keywords with delete buttons
    keywords_to_remove = []
    for i, keyword in enumerate(st.session_state['custom_keywords']):
        col1, col2 = st.sidebar.columns([4, 1])
        with col1:
            st.text(f"{i+1}. {keyword}")
        with col2:
            if st.button("🗑️", key=f"delete_{i}"):
                keywords_to_remove.append(keyword)
    
    # Remove keywords
    if keywords_to_remove:
        for keyword in keywords_to_remove:
            st.session_state['custom_keywords'].remove(keyword)
        st.rerun()
    
    # Clear all keywords
    if st.sidebar.button("🗑️ Clear All Keywords"):
        st.session_state['custom_keywords'] = []
        st.rerun()
    
    st.sidebar.divider()
    
    st.sidebar.header("ℹ️ About")
    st.sidebar.info("""
    This app collects RSS feeds from Google News for your custom keywords with boolean search support.
    
    **How to use:**
    1. Add keywords (with boolean operators) in the sidebar
    2. Collect articles using your keywords
    3. Filter by source category and download results
    
    **Boolean Examples:**
    - `Tesla AND production`
    - `solar OR wind`
    - `climate NOT politics`
    """)
    
    # Main content
    tab1, tab2, tab3 = st.tabs(["📥 Collect Feeds", "🔍 Search & Filter", "ℹ️ Instructions"])
    
    with tab1:
        st.header("📥 Collect RSS Feeds")
        
        # Show current keywords being monitored
        if len(st.session_state['custom_keywords']) > 0:
            st.subheader("Current Keywords")
            st.write(f"Monitoring **{len(st.session_state['custom_keywords'])}** keywords:")
            
            # Display keywords in a nice format
            keyword_cols = st.columns(3)
            for i, keyword in enumerate(st.session_state['custom_keywords']):
                with keyword_cols[i % 3]:
                    st.markdown(f"✓ {keyword}")
            
            st.divider()
        
        if len(st.session_state['custom_keywords']) == 0:
            st.info("👈 **Get Started:** Add your first keyword using the sidebar!")
            st.markdown("""
            ### How to Add Keywords:
            1. Look at the **sidebar** on the left
            2. Click **"➕ Add New Keyword"**
            3. Type your keyword (e.g., "climate change", "renewable energy")
            4. Click **"Add Keyword"**
            5. Come back here and click **"🚀 Collect Articles"**
            
            ### Example Keywords:
            - Simple: `Tesla`, `Microsoft`
            - Boolean AND: `Tesla AND production`
            - Boolean OR: `solar OR wind OR hydro`
            - Boolean NOT: `climate NOT politics`
            - Complex: `(EV OR electric vehicle) AND battery NOT Tesla`
            """)
        else:
            st.markdown("Click the button below to fetch the latest articles from Google News")
            
            col1, col2 = st.columns([1, 3])
            with col1:
                collect_button = st.button("🚀 Collect Articles", type="primary", use_container_width=True)
            
            if collect_button:
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                with st.spinner("Collecting RSS feeds..."):
                    df = collect_all_feeds(progress_bar, status_text, st.session_state['custom_keywords'])
                
                progress_bar.empty()
                status_text.empty()
                
                if df.empty:
                    st.warning("No articles found. Try again later.")
                else:
                    # Store in session state
                    st.session_state['articles_df'] = df
                    st.session_state['collection_time'] = datetime.now()
                    st.session_state['keywords_used'] = st.session_state['custom_keywords'].copy()
                    
                    st.success(f"✅ Collection complete! Found {len(df)} unique articles")
                    
                    # Display summary
                    st.subheader("📊 Summary")
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        st.metric("Total Articles", len(df))
                    with col2:
                        st.metric("Keywords Searched", len(st.session_state['custom_keywords']))
                    with col3:
                        st.metric("Unique Sources", df['Source'].nunique())
                    with col4:
                        st.metric("Source Categories", df['Source_Category'].nunique())
                    
                    # Reach metrics
                    st.subheader("🎯 Reach Analysis")
                    col1, col2, col3, col4 = st.columns(4)
                    
                    tier1_count = len(df[df['Reach_Tier'] == 1])
                    tier2_count = len(df[df['Reach_Tier'] == 2])
                    tier3_count = len(df[df['Reach_Tier'] == 3])
                    tier4_count = len(df[df['Reach_Tier'] == 4])
                    
                    with col1:
                        st.metric("Tier 1 (VERY HIGH)", tier1_count, help="Global wires & papers of record")
                    with col2:
                        st.metric("Tier 2 (HIGH)", tier2_count, help="Major industry leaders")
                    with col3:
                        st.metric("Tier 3 (MEDIUM)", tier3_count, help="Respected niche publications")
                    with col4:
                        st.metric("Tier 4 (LOW)", tier4_count, help="Smaller outlets")
                    
                    # Average reach score
                    avg_reach = df['Reach_Score'].mean()
                    st.metric("Average Reach Score", f"{avg_reach:.1f}/100")
                    
                    # Reach tier distribution chart
                    reach_tier_counts = df['Reach_Tier'].value_counts().sort_index()
                    # Map tier numbers to labels, handling missing tiers
                    reach_tier_labels = {1: 'Tier 1 (VERY HIGH)', 2: 'Tier 2 (HIGH)', 3: 'Tier 3 (MEDIUM)', 4: 'Tier 4 (LOW)'}
                    reach_tier_counts.index = [reach_tier_labels.get(i, f'Tier {i}') for i in reach_tier_counts.index]
                    st.bar_chart(reach_tier_counts)
                    
                    # Articles by keyword
                    st.subheader("Articles by Keyword")
                    keyword_counts = df['Keyword'].value_counts()
                    st.bar_chart(keyword_counts)
                    
                    # Articles by source category
                    st.subheader("Articles by Source Category")
                    category_counts = df['Source_Category'].value_counts()
                    st.bar_chart(category_counts)
                    
                    # Show breakdown of categories
                    st.subheader("📂 Source Category Breakdown")
                    for category in sorted(df['Source_Category'].unique()):
                        with st.expander(f"{category} ({len(df[df['Source_Category'] == category])} articles)"):
                            sources_in_category = df[df['Source_Category'] == category]['Source'].value_counts()
                            st.write(sources_in_category)
                    
                    # Display articles
                    st.subheader("📰 Recent Articles")
                    display_df = df[['Title', 'Source', 'Reach_Tier', 'Reach_Label', 'Source_Category', 'Keyword', 'Published', 'URL']].head(20)
                    
                    # Make URLs clickable
                    st.dataframe(
                        display_df,
                        column_config={
                            "URL": st.column_config.LinkColumn("URL"),
                            "Title": st.column_config.TextColumn("Title", width="large"),
                            "Reach_Tier": st.column_config.NumberColumn("Tier", help="1=Very High, 2=High, 3=Medium, 4=Low"),
                            "Reach_Label": st.column_config.TextColumn("Reach", help="Reach classification"),
                        },
                        hide_index=True,
                        use_container_width=True
                    )
                    
                    # Download buttons
                    st.subheader("💾 Download Data")
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        csv = df.to_csv(index=False).encode('utf-8')
                        st.download_button(
                            label="📄 Download CSV",
                            data=csv,
                            file_name=f"rss_feed_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                            mime="text/csv",
                            use_container_width=True
                        )
                    
                    with col2:
                        json_str = df.to_json(orient='records', indent=2)
                        st.download_button(
                            label="📋 Download JSON",
                            data=json_str,
                            file_name=f"rss_feed_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                            mime="application/json",
                            use_container_width=True
                        )
    
    with tab2:
        st.header("Search & Filter Collected Data")
        
        if 'articles_df' not in st.session_state:
            st.info("👈 Please collect articles first using the 'Collect Feeds' tab")
        else:
            df = st.session_state['articles_df']
            collection_time = st.session_state['collection_time']
            
            st.text(f"Last collected: {collection_time.strftime('%Y-%m-%d %H:%M:%S')}")
            
            # Show total articles
            st.metric("Total Articles Collected", len(df))
            
            st.divider()
            
            # Search
            st.subheader("🔍 Text Search")
            search_term = st.text_input("Search in titles and descriptions", "", placeholder="Type keywords to search...")
            
            # Date filter
            st.subheader("📅 Date Filter")
            col1, col2 = st.columns(2)
            
            with col1:
                # Calculate min and max dates from data
                valid_dates = df[df['Published_Date'].notna()]['Published_Date']
                if len(valid_dates) > 0:
                    # Convert to datetime and remove timezone for date picker
                    valid_dates_dt = pd.to_datetime(valid_dates).dt.tz_localize(None)
                    min_date = valid_dates_dt.min().date()
                    max_date = valid_dates_dt.max().date()
                else:
                    min_date = datetime.now().date() - timedelta(days=30)
                    max_date = datetime.now().date()
                
                start_date = st.date_input(
                    "From date",
                    value=min_date,
                    min_value=min_date,
                    max_value=max_date
                )
            
            with col2:
                end_date = st.date_input(
                    "To date",
                    value=max_date,
                    min_value=min_date,
                    max_value=max_date
                )
            
            # Quick date filters
            st.write("Quick filters:")
            col1, col2, col3, col4 = st.columns(4)
            
            # Note: These buttons will update the date inputs in the next rerun
            quick_filter = None
            
            with col1:
                if st.button("Today"):
                    quick_filter = "today"
            
            with col2:
                if st.button("Last 7 days"):
                    quick_filter = "7days"
            
            with col3:
                if st.button("Last 30 days"):
                    quick_filter = "30days"
            
            with col4:
                if st.button("All time"):
                    quick_filter = "all"
            
            # Apply quick filter
            if quick_filter == "today":
                start_date = datetime.now().date()
                end_date = datetime.now().date()
            elif quick_filter == "7days":
                start_date = (datetime.now() - timedelta(days=7)).date()
                end_date = datetime.now().date()
            elif quick_filter == "30days":
                start_date = (datetime.now() - timedelta(days=30)).date()
                end_date = datetime.now().date()
            elif quick_filter == "all":
                if len(valid_dates) > 0:
                    valid_dates_dt = pd.to_datetime(valid_dates).dt.tz_localize(None)
                    start_date = valid_dates_dt.min().date()
                    end_date = valid_dates_dt.max().date()
            
            st.divider()
            
            # Keyword filter
            st.subheader("🏷️ Filters")
            
            # Reach tier filter
            selected_reach_tiers = st.multiselect(
                "Filter by reach tier",
                options=[
                    ('Tier 1 - VERY HIGH (Global wires & papers of record)', 1),
                    ('Tier 2 - HIGH (Major industry leaders)', 2),
                    ('Tier 3 - MEDIUM (Respected niche publications)', 3),
                    ('Tier 4 - LOW (Smaller outlets)', 4)
                ],
                format_func=lambda x: x[0],
                default=[]
            )
            # Extract just the tier numbers
            selected_tiers_values = [tier[1] for tier in selected_reach_tiers]
            
            selected_keywords = st.multiselect(
                "Filter by keyword",
                options=df['Keyword'].unique().tolist(),
                default=df['Keyword'].unique().tolist()
            )
            
            # Source category filter
            selected_categories = st.multiselect(
                "Filter by source category",
                options=sorted(df['Source_Category'].unique().tolist()),
                default=[]
            )
            
            # Source filter
            selected_sources = st.multiselect(
                "Filter by specific source",
                options=sorted(df['Source'].unique().tolist()),
                default=[]
            )
            
            # Apply filters
            filtered_df = df.copy()
            
            # Date filter
            if 'Published_Date' in filtered_df.columns:
                # Convert start and end dates to datetime for comparison
                start_datetime = pd.Timestamp(start_date)
                end_datetime = pd.Timestamp(end_date) + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)
                
                # Filter by date, keeping articles without dates
                date_mask = filtered_df['Published_Date'].isna()
                if filtered_df['Published_Date'].notna().any():
                    # Remove timezone info for comparison if present
                    filtered_df['Published_Date_Compare'] = pd.to_datetime(filtered_df['Published_Date']).dt.tz_localize(None)
                    date_mask = date_mask | (
                        (filtered_df['Published_Date_Compare'] >= start_datetime) & 
                        (filtered_df['Published_Date_Compare'] <= end_datetime)
                    )
                filtered_df = filtered_df[date_mask]
            
            if search_term:
                mask = (filtered_df['Title'].str.contains(search_term, case=False, na=False) | 
                       filtered_df['Description'].str.contains(search_term, case=False, na=False))
                filtered_df = filtered_df[mask]
            
            if selected_tiers_values:
                filtered_df = filtered_df[filtered_df['Reach_Tier'].isin(selected_tiers_values)]
            
            if selected_keywords:
                filtered_df = filtered_df[filtered_df['Keyword'].isin(selected_keywords)]
            
            if selected_categories:
                filtered_df = filtered_df[filtered_df['Source_Category'].isin(selected_categories)]
            
            if selected_sources:
                filtered_df = filtered_df[filtered_df['Source'].isin(selected_sources)]
            
            # Display results
            st.divider()
            
            # Show search status prominently
            if search_term:
                st.success(f"🔍 **Search Active:** Showing results for '{search_term}'")
            
            st.subheader(f"📊 Results: {len(filtered_df)} articles")
            
            # Show active filters
            active_filters = []
            if search_term:
                active_filters.append(f"✓ Text search: '{search_term}'")
            if selected_tiers_values:
                tier_names = [f"Tier {t}" for t in selected_tiers_values]
                active_filters.append(f"Reach: {', '.join(tier_names)}")
            if len(selected_keywords) < len(df['Keyword'].unique()):
                active_filters.append(f"Keywords: {len(selected_keywords)} selected")
            if selected_categories:
                active_filters.append(f"Categories: {', '.join(selected_categories)}")
            if selected_sources:
                active_filters.append(f"Sources: {len(selected_sources)} selected")
            active_filters.append(f"Date range: {start_date} to {end_date}")
            
            if active_filters:
                st.caption("Active filters: " + " • ".join(active_filters))
            
            if len(filtered_df) > 0:
                # Show search statistics if search is active
                if search_term:
                    search_matches = len(filtered_df)
                    total_before_search = len(df)
                    
                    # Apply all filters except search to see search impact
                    temp_df = df.copy()
                    if 'Published_Date' in temp_df.columns:
                        start_datetime = pd.Timestamp(start_date)
                        end_datetime = pd.Timestamp(end_date) + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)
                        date_mask = temp_df['Published_Date'].isna()
                        if temp_df['Published_Date'].notna().any():
                            temp_df['Published_Date_Compare'] = pd.to_datetime(temp_df['Published_Date']).dt.tz_localize(None)
                            date_mask = date_mask | (
                                (temp_df['Published_Date_Compare'] >= start_datetime) & 
                                (temp_df['Published_Date_Compare'] <= end_datetime)
                            )
                        temp_df = temp_df[date_mask]
                    if selected_keywords:
                        temp_df = temp_df[temp_df['Keyword'].isin(selected_keywords)]
                    if selected_categories:
                        temp_df = temp_df[temp_df['Source_Category'].isin(selected_categories)]
                    if selected_sources:
                        temp_df = temp_df[temp_df['Source'].isin(selected_sources)]
                    
                    articles_before_search = len(temp_df)
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Articles Before Search", articles_before_search)
                    with col2:
                        st.metric("Matching Search Term", search_matches)
                    with col3:
                        match_rate = (search_matches / articles_before_search * 100) if articles_before_search > 0 else 0
                        st.metric("Match Rate", f"{match_rate:.1f}%")
                    
                    st.info(f"💡 **Search Results:** Found '{search_term}' in {search_matches} article(s)")
                
                # Show category breakdown of results
                st.subheader("📂 Results by Category")
                category_counts = filtered_df['Source_Category'].value_counts()
                col1, col2 = st.columns([2, 1])
                with col1:
                    st.bar_chart(category_counts)
                with col2:
                    st.dataframe(category_counts.reset_index().rename(columns={'index': 'Category', 'Source_Category': 'Count'}), 
                               hide_index=True)
                
                # Show reach tier breakdown
                st.subheader("🎯 Results by Reach Tier")
                reach_tier_counts = filtered_df['Reach_Tier'].value_counts().sort_index()
                reach_tier_labels = {1: 'Tier 1 (VERY HIGH)', 2: 'Tier 2 (HIGH)', 3: 'Tier 3 (MEDIUM)', 4: 'Tier 4 (LOW)'}
                reach_tier_counts.index = [reach_tier_labels.get(i, f'Tier {i}') for i in reach_tier_counts.index]
                
                col1, col2 = st.columns([2, 1])
                with col1:
                    st.bar_chart(reach_tier_counts)
                with col2:
                    # Show average reach score
                    avg_reach = filtered_df['Reach_Score'].mean()
                    st.metric("Avg Reach Score", f"{avg_reach:.1f}/100")
                    st.dataframe(reach_tier_counts.reset_index().rename(columns={'index': 'Tier', 'Reach_Tier': 'Count'}), 
                               hide_index=True)
                
                # Top sources by reach
                with st.expander("🏆 Top Sources by Reach Score"):
                    top_sources = filtered_df.nlargest(10, 'Reach_Score')[['Source', 'Reach_Score', 'Reach_Label', 'Reach_Reasoning']]
                    st.dataframe(top_sources, hide_index=True, use_container_width=True)
                
                display_df = filtered_df[['Title', 'Source', 'Reach_Tier', 'Reach_Label', 'Source_Category', 'Keyword', 'Published', 'URL']]
                
                st.dataframe(
                    display_df,
                    column_config={
                        "URL": st.column_config.LinkColumn("URL"),
                        "Title": st.column_config.TextColumn("Title", width="large"),
                        "Reach_Tier": st.column_config.NumberColumn("Tier", help="1=Very High, 2=High, 3=Medium, 4=Low"),
                        "Reach_Label": st.column_config.TextColumn("Reach"),
                    },
                    hide_index=True,
                    use_container_width=True
                )
                
                # Download filtered results
                csv = filtered_df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="📄 Download Filtered Results (CSV)",
                    data=csv,
                    file_name=f"filtered_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )
            else:
                if search_term:
                    st.error(f"❌ **No Results Found for '{search_term}'**")
                    st.warning("""
                    Your search term didn't match any articles. Try:
                    - Using different keywords
                    - Checking for typos
                    - Using partial words (e.g., "climat" instead of "climate change")
                    - Removing other filters to expand results
                    """)
                else:
                    st.warning("⚠️ No articles match your filters")
                    st.info("""
                    **Tips:**
                    - Try removing some filters
                    - Expand the date range
                    - Make sure keywords are selected
                    """)
    
    with tab3:
        st.header("📖 How to Use This App")
        
        st.markdown("""
        ### Step-by-Step Instructions
        
        #### 1. Manage Your Keywords (with Boolean Search!)
        - In the **sidebar**, click **"➕ Add New Keyword"**
        - Type your keyword with optional boolean operators:
          - `climate AND policy` - both terms must appear
          - `solar OR wind` - either term can appear
          - `EV NOT Tesla` - exclude Tesla from EV results
          - `(climate OR environment) AND policy` - combine operators
        - Click **"Add Keyword"**
        - Remove keywords by clicking the 🗑️ button next to them
        - Use **"🗑️ Clear All Keywords"** to delete all keywords at once
        
        #### 2. Collect Articles
        - Go to the **"📥 Collect Feeds"** tab
        - Review the keywords that will be searched
        - Click the **"🚀 Collect Articles"** button
        - Wait 10-30 seconds while articles are fetched
        - View results with **automatic reach tier classification**
        
        #### 3. Understanding Reach Tiers
        
        Every article is automatically scored for reach/reputation:
        
        **Tier 1 - VERY HIGH (Score: 90-100)**
        - Global news wires (Reuters, AP, Bloomberg)
        - Papers of record (NYT, WSJ, WashPost, FT, Guardian)
        - Major broadcasters (BBC, CNN)
        - **Why it matters**: Market-moving coverage, policy influence, elite audiences
        - **Examples**: Reuters (98), New York Times (97), Bloomberg (97)
        
        **Tier 2 - HIGH (Score: 60-89)**
        - Major industry publications (TechCrunch, Forbes, Wired)
        - Established business media (Fortune, Business Insider, CNBC)
        - Industry-standard trade press (Utility Dive, Politico)
        - **Why it matters**: Professional audiences, industry influence
        - **Examples**: TechCrunch (85), Forbes (85), Axios (84)
        
        **Tier 3 - MEDIUM (Score: 30-59)**
        - Respected niche publications (CleanTechnica, Electrek)
        - Major regional papers (LA Times, Chicago Tribune)
        - Specialized trade publications
        - **Why it matters**: Deep expertise, engaged niche audiences
        - **Examples**: CleanTechnica (55), Electrek (56), LA Times (58)
        
        **Tier 4 - LOW (Score: 1-29)**
        - Smaller outlets, blogs, unknown sources
        - **Why it matters**: Local impact, early signals, grassroots
        
        #### 4. Analyze Your Coverage
        
        After collection, you'll see:
        - **Tier distribution**: How many Tier 1 vs Tier 4 articles
        - **Average reach score**: Overall quality of coverage
        - **Top sources**: Highest-reach outlets covering your topics
        
        #### 5. Filter & Download
        - Go to **"🔍 Search & Filter"** tab
        - **Filter by reach tier**: Show only Tier 1 articles
        - Filter by keyword, source category, or date
        - Download filtered results with reach data included
        
        ### Source Categories Explained
        
        Articles are automatically categorized into:
        
        - **Mainstream Media**: CNN, BBC, Reuters, NYT, WSJ, etc.
        - **Trade Press**: TechCrunch, Wired, CleanTechnica, industry publications
        - **Blogs/Independent**: Medium, Substack, personal blogs
        - **Government/Academic**: .gov sites, universities, research journals
        - **NGO/Think Tank**: Greenpeace, Brookings, RAND, etc.
        - **Local/Regional**: Local newspapers and regional news outlets
        - **Other**: Sources that don't fit above categories
        
        ### How Reach Tiers Are Calculated
        
        The reputation-based system evaluates sources on:
        
        **For Tier 1:**
        ✓ Journalism awards (Pulitzer Prizes, Peabody Awards)
        ✓ Primary news sources (Reuters, AP - others cite them)
        ✓ Papers of record designation
        ✓ 50+ Pulitzer Prizes or 100+ years history
        ✓ International bureaus (25+ countries)
        ✓ Large investigative teams (50+ reporters)
        
        **For Tier 2:**
        ✓ Industry authority (TechCrunch in VC, Politico in DC)
        ✓ 20+ full-time reporters
        ✓ Professional/elite readership
        ✓ Major media company ownership
        ✓ Regular access to exclusive sources
        
        **For Tier 3:**
        ✓ Established in niche (10+ years)
        ✓ Respected by industry peers
        ✓ Cited by higher-tier outlets
        ✓ 5-20 reporters
        
        ### Use Cases for Reach Analysis
        
        **PR & Communications:**
        - "We got 5 Tier 1 mentions this quarter vs 2 last quarter"
        - "Total estimated reach: 200M+ via top-tier coverage"
        
        **Competitive Intelligence:**
        - "Competitor dominated Tier 1 (10 articles) while we had more Tier 3 (30 articles)"
        - "We need to improve our Tier 1/Tier 2 ratio"
        
        **Media Strategy:**
        - Filter to Tier 1 only: Which topics get elite media attention?
        - Compare: Do certain keywords attract higher-tier coverage?
        
        **Investor Relations:**
        - "Our average reach score improved from 45 to 62"
        - Download Tier 1+2 articles for board presentation
        
        **Trend Analysis:**
        - Track: Are we moving from niche (Tier 3) to mainstream (Tier 1)?
        - Identify: Which outlets consistently cover us?
        
        ### Boolean Search Examples
        
        **Simple Boolean:**
        - `Tesla AND production` - both words must appear
        - `solar OR wind` - either word can appear
        - `climate NOT politics` - exclude politics
        
        **Advanced Boolean:**
        - `(EV OR "electric vehicle") AND battery` - parentheses for grouping
        - `renewable energy NOT oil` - exclude specific topics
        - `Microsoft AND (Azure OR cloud)` - multiple OR conditions
        - `climate policy AND (EU OR Europe) NOT Brexit` - complex queries
        
        ### Example Keywords You Can Add
        
        **Simple keywords:**
        - "Apple", "Google", "Tesla", "Microsoft"
        - "climate change", "artificial intelligence"
        
        **Boolean keywords:**
        - "Tesla AND (production OR delivery)"
        - "climate AND policy NOT Trump"
        - "(solar OR wind) AND energy storage"
        - "Microsoft AND AI NOT gaming"
        - "EV OR electric vehicle OR battery electric"
        
        ### Tips for Better Results
        - **Use boolean AND** for precise results: "climate AND Africa"
        - **Use boolean OR** for comprehensive coverage: "solar OR photovoltaic OR PV"
        - **Use boolean NOT** to exclude: "Apple NOT iPhone" (just the company news)
        - **Combine operators**: "(climate OR environment) AND policy AND (Africa OR Kenya)"
        - **Filter by category** after collection to focus on specific source types
        - **Track mainstream vs trade press** separately for different perspectives
        
        ### Data Freshness
        - Articles are fetched from Google News RSS feeds
        - Data is cached for 1 hour to avoid excessive requests
        - Click "Collect Articles" again to refresh
        - Keywords are saved during your session only
        - Download your data regularly to build a historical database
        
        ### About This Tool
        This RSS collector helps you monitor media coverage with advanced search and categorization.
        Perfect for:
        - Media monitoring and PR tracking
        - Competitive intelligence
        - Market research across different source types
        - Industry trend analysis
        - Policy and regulatory tracking
        - ESG and sustainability reporting
        - Academic research
        - Investment research
        
        ### Frequently Asked Questions
        
        **Q: How do boolean operators work?**  
        A: They work like Google search. AND narrows results, OR expands them, NOT excludes terms.
        
        **Q: Can I see which sources are in each category?**  
        A: Yes! After collection, expand the "Source Category Breakdown" section.
        
        **Q: How many keywords can I add?**  
        A: As many as you want! More keywords = longer collection time (1-2 seconds per keyword).
        
        **Q: Are my keywords saved permanently?**  
        A: No, keywords reset when you refresh the page. Keep a list saved elsewhere.
        
        **Q: Can I collect historical articles?**  
        A: Google News RSS typically shows recent articles (last 24-48 hours). Collect regularly.
        
        **Q: Why are some sources categorized as "Other"?**  
        A: The categorization uses pattern matching. Uncommon sources may not match any category.
        
        **Q: Can I customize the source categories?**  
        A: Not in the UI, but you can modify the `categorize_source()` function in the code.
        """)
        
        st.divider()
        
        st.subheader("🎯 Quick Start Example")
        st.markdown("""
        **Scenario**: You want to track mainstream (Tier 1) media coverage of climate policy
        
        1. **Add boolean keyword**: 
           - Sidebar → "➕ Add New Keyword"
           - Type: `climate AND (policy OR regulation)`
           - Add Keyword
        
        2. **Collect**: Click "🚀 Collect Articles"
        
        3. **Analyze reach**: 
           - Check "Reach Analysis" metrics
           - See how many Tier 1 vs Tier 2 vs Tier 3 articles
           - View "Top Sources by Reach Score"
        
        4. **Filter to elite media**: 
           - Go to "Search & Filter"
           - Select "Tier 1 - VERY HIGH" in reach tier filter
           - Now you see only NYT, Reuters, WSJ, etc.
        
        5. **Download**: Click "📄 Download Filtered Results (CSV)"
           - CSV includes: Reach_Tier, Reach_Score, Reach_Label, Reach_Reasoning
           - Perfect for reports showing "elite media coverage"
        
        6. **Weekly tracking**: 
           - Repeat weekly to track: "Are we getting more Tier 1 coverage?"
           - Build trend: Average reach score over time
        
        **Result**: Data-driven PR metrics with reputation scoring!
        """)
        
        st.divider()
        
        st.subheader("💡 Pro Tips")
        st.markdown("""
        **For PR Professionals:**
        - Filter to Tier 1+2 only for executive briefings
        - Track "average reach score" as a KPI
        - Export with reach reasoning to show why each outlet matters
        
        **For Competitive Analysis:**
        - Compare your Tier 1 count vs competitors
        - Identify which outlets cover them but not you
        - Spot opportunities in under-served tiers
        
        **For Market Research:**
        - Tier 1 = mainstream narrative
        - Tier 3 = early trends, niche insights
        - Compare both for complete picture
        
        **Quality over Quantity:**
        - 1 Tier 1 article > 10 Tier 4 articles
        - Use reach score to weight your analysis
        - Focus efforts on moving up tiers
        """)
        
        st.divider()
        
        st.subheader("📊 Sample Analysis Output")
        st.markdown("""
        ```
        This Month's Coverage - "Electric Vehicles":
        
        Tier 1 (VERY HIGH):     8 articles  |  Avg Score: 95.2
        Top outlets: Reuters, Bloomberg, NYT, WSJ
        Estimated reach: 80M+ impressions
        
        Tier 2 (HIGH):         15 articles  |  Avg Score: 81.5
        Top outlets: TechCrunch, Forbes, Wired
        Estimated reach: 60M+ impressions
        
        Tier 3 (MEDIUM):       32 articles  |  Avg Score: 53.8
        Top outlets: Electrek, CleanTechnica, InsideEVs
        Estimated reach: 15M+ impressions
        
        Tier 4 (LOW):          45 articles  |  Avg Score: 20.0
        Various blogs and small outlets
        Estimated reach: 5M+ impressions
        
        Overall Metrics:
        - Total articles: 100
        - Average reach score: 52.4/100
        - Tier 1+2 coverage: 23% (good!)
        - Estimated total reach: 160M+ impressions
        ```
        
        **This type of analysis is now automatic with your CSV exports!**
        """)


if __name__ == "__main__":
    main()
