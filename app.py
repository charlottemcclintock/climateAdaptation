import streamlit as st
import json
from pathlib import Path
import pandas as pd
import html
import re
import html
import re

def clean_nap_text(text, default="No information provided.", auto_link=True):
    """Escape HTML, replace newlines, and optionally auto-link URLs."""
    if not text or text.strip() == "Not stated.":
        return default
    # Escape HTML
    safe = html.escape(text)
    # Replace newlines with <br>
    safe = safe.replace("\n", "<br>")
    # Optionally auto-link URLs
    if auto_link:
        url_pattern = re.compile(r'(https?://[^\s<]+)')
        safe = url_pattern.sub(r'<a href="\\1" target="_blank">\\1</a>', safe)
    return safe

def parse_nap_outputs(text):
    """
    Converts custom NAP output link format to markdown hyperlinks in a bulleted list.
    Example: 
    {{{Title$$$https://example.com}}} 
    becomes 
    - [Title](https://example.com)
    """
    if not text or text.strip() == "Not stated.":
        return "No outputs provided."
    # Replace all triple-brace blocks with markdown links
    def replacer(match):
        content = match.group(1)
        if "$$$" in content:
            title, url = content.split("$$$", 1)
            return f"[{title.strip()}]({url.strip()})"
        return content
    # Replace all occurrences
    processed = re.sub(r"\{\{\{(.*?)\}\}\}", replacer, text)
    # Split into lines, add bullet to each non-empty line
    lines = [f"- {line.strip()}" for line in processed.splitlines() if line.strip()]
    return "\n".join(lines)

# Set page config with light theme and custom font
st.set_page_config(
    page_title="Adaptation Priorities",
    layout="wide"
)
# set up custom css styling
with open("style.css") as css:
    custom_css = css.read()
st.markdown(f"<style>{custom_css}</style>", unsafe_allow_html=True)

# Add this new CSS for table styling
st.markdown("""
    <style>
        .stDataFrame {
            font-size: 0.8em;
        }
        .stDataFrame td {
            padding: 0.5em;
        }
        .stDataFrame th {
            padding: 0.5em;
        }
        /* Set column widths */
        .stDataFrame td:nth-child(1) {  /* Sector column */
            width: 20%;
        }
        .stDataFrame td:nth-child(2) {  /* Subsector column */
            width: 30%;
        }
        .stDataFrame td:nth-child(3) {  /* Priority column */
            width: 50%;
        }
    </style>
""", unsafe_allow_html=True)

# markdown -> html to apply custom css
def apply_custom_css(css):
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)


# Load data
@st.cache_data
def load_nap_docs():
    with open("data/intermediate/nap_docs.json", "r") as f:
        return json.load(f)

@st.cache_data
def load_climatewatch_adaptation():
    return pd.read_csv("data/intermediate/climatewatch_adaptation.csv")

# Load the data
nap_docs = load_nap_docs()
adaptation_data = load_climatewatch_adaptation()

with st.sidebar:
    with st.container(border=True):
        
        st.markdown(f"### [dev] Adaptation Priorities")
        st.markdown('<p style="color: #666666;"><i>Note:</i> This application is for demonstration purposes only.</p>', unsafe_allow_html=True)

        # Create country list for selection
        countries = adaptation_data["Country"].unique()

        st.markdown('<div class="country-selector">', unsafe_allow_html=True)
        selected_country = st.selectbox(
            "Select a country",
            countries,
            key="country_selector",
            index=17
        )
        st.markdown('<div class="section-title">Data Sources</div>', unsafe_allow_html=True)

        st.markdown("Summaries of National Adaptation Plan summaries come from [NAP Trends](https://trends.napglobalnetwork.org/naps-by-country) by the NAP Global Network.")
        st.markdown("Summaries of adaptation priorities in NDCs come from [Climate Watch](https://www.climatewatchdata.org/) from the World Resources Institute.")
        st.markdown('</div>', unsafe_allow_html=True)





# Get NAP data for selected country
nap_data = next((doc for doc in nap_docs if doc["countryName"] == selected_country), None)

st.markdown('<div class="section-title">National Adaptation Plan</div>', unsafe_allow_html=True)
if nap_data:
    with st.container(border=True):
        st.markdown(f'<div class="country-name"><strong>{nap_data["countryName"]}</strong></div>', unsafe_allow_html=True)
        if nap_data.get("linkToDocUNFCCC"):
            st.markdown(
                f"*{nap_data['releaseBy']}, {nap_data['yearPublication']}* ([link]({nap_data['linkToDocUNFCCC']}))"
            )
        else:        
            st.markdown(
                f"*{nap_data['releaseBy']}, {nap_data['yearPublication']}*"
            )

        subcols = st.columns([1,5])
        with subcols[0]:
            st.markdown("**Purpose**")
        with subcols[1]:
            st.write(nap_data['purpose'] if nap_data['purpose'] != "Not stated." else "No purpose provided.")

        subcols = st.columns([1,5])
        with subcols[0]:
            st.markdown("**Vision**")
        with subcols[1]:
            st.write(nap_data['vision'] if nap_data['vision'] != "Not stated." else "No vision statement provided.")
        subcols = st.columns([1,5])
        with subcols[0]:
            st.markdown("**Goals**")
        with subcols[1]:
            st.write(nap_data['goals'] if nap_data['goals'] != "Not stated." else "No goals provided.")

        subcols = st.columns([1,5])
        with subcols[0]:
            st.markdown("**NAP Process Outputs**")
        with subcols[1]:
            st.markdown(parse_nap_outputs(nap_data['napProcessOutputs']))
else:
    st.info("No NAP data found for the selected country.")
# Adaptation Priorities Section
st.markdown('<div class="section-title">Adaptation Priorities</div>', unsafe_allow_html=True)

with st.container(border=True):
    # Filter adaptation_data for the selected country
    country_adaptation = adaptation_data[adaptation_data["Country"] == selected_country]

    if not country_adaptation.empty:
        # Get unique values for each filter
        adaptation_docs = country_adaptation['adaptation_doc'].dropna().unique()
        all_sectors = country_adaptation['name'].dropna().unique()
        all_subsectors = country_adaptation['subsector_name'].dropna().unique()

        # 3 columns for selectboxes
        col1, col2 = st.columns([2,5])
        with col1:
            selected_doc = st.pills("Document", adaptation_docs, selection_mode="multi", default=adaptation_docs)
        with col2:
            selected_sector = st.pills("Sector", all_sectors, selection_mode="multi", default=all_sectors)

        # Filter the dataframe
        filtered_df = country_adaptation[
            (country_adaptation['adaptation_doc'].isin(selected_doc)) &
            (country_adaptation['name'].isin(selected_sector)) 
        ]

        if not filtered_df.empty:
            # Prepare DataFrame for MultiIndex
            display_df = (
                filtered_df.rename(
                    columns={
                        "name": "Sector",
                        "subsector_name": "Subsector",
                        "title": "Priority"
                    }
                )[["Sector", "Subsector", "Priority"]]
                .set_index(["Sector"])
                .sort_index()
            )

            st.table(display_df)


        else:
            st.info("No priorities available for the selected filters.")
    else:
        st.info("No adaptation priorities data available for this country.")



def clean_nap_text(text, default="No information provided.", auto_link=True):
    """Escape HTML, replace newlines, and optionally auto-link URLs."""
    if not text or text.strip() == "Not stated.":
        return default
    # Escape HTML
    safe = html.escape(text)
    # Replace newlines with <br>
    safe = safe.replace("\n", "<br>")
    # Optionally auto-link URLs
    if auto_link:
        url_pattern = re.compile(r'(https?://[^\s<]+)')
        safe = url_pattern.sub(r'<a href="\\1" target="_blank">\\1</a>', safe)
    return safe 