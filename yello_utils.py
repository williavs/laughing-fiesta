"""
Utility functions for Yellow Pages and Superpages scraping
"""
import logging
import random
import re
import time
import traceback
import urllib.parse

import pandas as pd
import requests
import streamlit as st
from bs4 import BeautifulSoup
from rapidfuzz import fuzz

logger = logging.getLogger(__name__)

def clean_location(location):
    """Clean location string for URL formatting."""
    cleaned = re.sub(r"\s*,\s*", ", ", location)
    parts = cleaned.split(",")
    return f"{parts[0].strip()}, {parts[-1].strip()}"

def normalize_phone(phone):
    """Remove non-digit characters from phone number."""
    return re.sub(r"\D", "", phone)

def normalize_address(address):
    """Normalize address for comparison."""
    return re.sub(r"\s+", " ", address.lower().strip())

def is_duplicate(existing, new, threshold=85):
    """Check if two business entries are duplicates using rapidfuzz."""
    name_similarity = fuzz.ratio(existing["Business Name"].lower(), new["Business Name"].lower())
    phone_match = normalize_phone(existing["Phone"]) == normalize_phone(new["Phone"])
    address_similarity = fuzz.ratio(normalize_address(existing["Address"]), normalize_address(new["Address"]))

    return (name_similarity >= threshold and phone_match) or (
        name_similarity >= threshold and address_similarity >= threshold
    )

def merge_entries(existing, new):
    """Merge two business entries, keeping the best information."""
    merged = existing.copy()
    if new["Website"] != "N/A" and existing["Website"] == "N/A":
        merged["Website"] = new["Website"]
    merged["Source"] = f"{existing['Source']}, {new['Source']}"
    return merged

def scrape_yellow_pages_generator(keyword, location, limit):
    """Generator function to scrape Yellow Pages data."""
    cleaned_location = clean_location(location)
    url = f"https://www.yellowpages.com/search?search_terms={keyword}&geo_location_terms={cleaned_location}"
    logger.info(f"Scraping URL: {url}")
    
    businesses_scraped = 0
    page = 1
    seen_websites = set()

    try:
        while businesses_scraped < limit:
            logger.info(f"Scraping Yellow Pages page {page}...")
            response = requests.get(f"{url}&page={page}")
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")
            results = soup.find_all("div", class_="result")

            if not results:
                break

            for result in results:
                if businesses_scraped >= limit:
                    return

                business_name = result.find("a", class_="business-name").text.strip()
                website_link = result.find("a", class_="track-visit-website")
                website = website_link["href"] if website_link else "N/A"

                if website == "N/A" or website in seen_websites:
                    continue

                seen_websites.add(website)

                phone = (
                    result.find("div", class_="phones").text.strip() 
                    if result.find("div", class_="phones") else "N/A"
                )
                street_address = (
                    result.find("div", class_="street-address").text.strip()
                    if result.find("div", class_="street-address")
                    else "N/A"
                )
                locality = (
                    result.find("div", class_="locality").text.strip()
                    if result.find("div", class_="locality")
                    else "N/A"
                )
                address = f"{street_address}, {locality}"

                yield {
                    "Business Name": business_name,
                    "Phone": phone,
                    "Address": address,
                    "Website": website,
                    "Source": "Yellow Pages",
                }

                businesses_scraped += 1

            page += 1
            time.sleep(2)

    except requests.RequestException as e:
        logger.error(f"Error fetching the Yellow Pages URL: {e}")
        logger.error(traceback.format_exc())
    except Exception as e:
        logger.error(f"An unexpected error occurred while scraping Yellow Pages: {e}")
        logger.error(traceback.format_exc())

def scrape_superpages_generator(keyword, location, limit):
    """Generator function to scrape Superpages data."""
    cleaned_location = clean_location(location)
    base_url = f"https://www.superpages.com/search?search_terms={keyword}&geo_location_terms={cleaned_location}"
    logger.info(f"Scraping Superpages URL: {base_url}")
    
    businesses_scraped = 0
    page_number = 1
    seen_websites = set()

    try:
        while businesses_scraped < limit:
            logger.info(f"Scraping Superpages page {page_number}...")
            url = f"{base_url}&page={page_number}"

            response = requests.get(url)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, "html.parser")
            business_listings = soup.find_all("div", class_="srp-listing")

            if not business_listings:
                break

            for listing in business_listings:
                if businesses_scraped >= limit:
                    return

                name_elem = listing.find("a", class_="business-name")
                name = name_elem.text.strip() if name_elem else "N/A"

                website_elem = listing.find("a", class_="weblink-button")
                website = website_elem["href"] if website_elem else "N/A"

                if website == "N/A" or website in seen_websites:
                    continue
                seen_websites.add(website)

                address_elem = listing.find("p", class_="adr")
                address = address_elem.text.strip() if address_elem else "N/A"

                phone_elem = listing.find("span", class_="call-number")
                phone = phone_elem.text.strip() if phone_elem else "N/A"

                yield {
                    "Business Name": name,
                    "Phone": phone,
                    "Address": address,
                    "Website": website,
                    "Source": "Superpages",
                }

                businesses_scraped += 1

            page_number += 1
            time.sleep(2)

    except requests.RequestException as e:
        logger.error(f"Error fetching the Superpages URL: {e}")
        logger.error(traceback.format_exc())
    except Exception as e:
        logger.error(f"An unexpected error occurred while scraping Superpages: {e}")
        logger.error(traceback.format_exc())

progress_phrases = [
    "Gathering companies",
    "Seeing what's out there",
    "Looking for small businesses",
    "Exploring local options",
    "Discovering hidden gems",
    "Uncovering business opportunities",
]

def inject_custom_css():
    """Inject custom CSS for animated progress bar."""
    st.markdown(
        """
        <style>
        .stProgress > div > div > div > div {
            background-image: linear-gradient(
                45deg,
                rgba(255, 255, 255, 0.15) 25%,
                transparent 25%,
                transparent 50%,
                rgba(255, 255, 255, 0.15) 50%,
                rgba(255, 255, 255, 0.15) 75%,
                transparent 75%,
                transparent 100%
            );
            background-size: 1rem 1rem;
            animation: progress-bar-stripes 1s linear infinite;
        }

        @keyframes progress-bar-stripes {
            0% { background-position: 1rem 0; }
            100% { background-position: 0 0; }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

def scrape_combined(keyword, location, limit):
    """Combined scraping function for both Yellow Pages and Superpages."""
    total_limit = limit
    per_source_limit = total_limit * 2  # Increase limit to account for duplicates

    unique_companies = []
    yellow_pages_generator = scrape_yellow_pages_generator(keyword, location, per_source_limit)
    superpages_generator = scrape_superpages_generator(keyword, location, per_source_limit)
    generators = [("Yellow Pages", yellow_pages_generator), ("Superpages", superpages_generator)]

    inject_custom_css()

    with st.spinner("Searching for businesses..."):
        progress_bar = st.progress(0)
        status_text = st.empty()

        while len(unique_companies) < total_limit and generators:
            for source, generator in generators[:]:
                try:
                    new_entry = next(generator)

                    duplicate = next(
                        (company for company in unique_companies if is_duplicate(company, new_entry)), 
                        None
                    )

                    if duplicate:
                        index = unique_companies.index(duplicate)
                        unique_companies[index] = merge_entries(duplicate, new_entry)
                    else:
                        unique_companies.append(new_entry)

                    progress = min(len(unique_companies) / total_limit, 1.0)
                    progress_bar.progress(progress)
                    status_text.text(
                        f"{random.choice(progress_phrases)}... ({len(unique_companies)} found)"
                    )

                    if len(unique_companies) >= total_limit:
                        break
                except StopIteration:
                    generators.remove((source, generator))
                except Exception as e:
                    logger.error(f"Error in {source}: {str(e)}")
                    generators.remove((source, generator))

                time.sleep(0.1)

    deduplicated_df = pd.DataFrame(unique_companies)
    st.success(f"Found {len(deduplicated_df)} unique businesses!")
    return deduplicated_df