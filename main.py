import streamlit as st
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from bs4 import BeautifulSoup
import time


st.title("Amazon Reviews Scraper")
url = st.text_input("Enter Amazon product URL")

def get_review_page_url(product_url):
    chrome_driver_path = "./chromedriver.exe"  
    options = webdriver.ChromeOptions()
    driver = webdriver.Chrome(service=Service(chrome_driver_path), options=options)

    try:
        driver.get(product_url)
        time.sleep(5) 
        html_data = BeautifulSoup(driver.page_source, 'html.parser')

        reviews_link = html_data.find('a', {'data-hook': 'see-all-reviews-link-foot'})
        if reviews_link:
            reviews_url = 'https://www.amazon.in' + reviews_link['href']
        else:
            reviews_url = None
    finally:
        driver.quit()

    return reviews_url

def scrape_amazon_reviews(reviews_url):
    chrome_driver_path = "./chromedriver.exe"
    options = webdriver.ChromeOptions()
    
    driver = webdriver.Chrome(service=Service(chrome_driver_path), options=options)
    
    names = []
    ratings = []
    rating_dates = []
    titles = []
    reviews_text = []
    
    try:
        driver.get(reviews_url)
        
        while True:  
            time.sleep(5)  
            html_data = BeautifulSoup(driver.page_source, 'html.parser')

            reviews = html_data.find_all('div', {'data-hook': 'review'})
            for review in reviews:
                name = review.find('span', {'class': 'a-profile-name'}).text
                names.append(name.strip())

                rating = review.find('span', {'class': 'a-icon-alt'}).text
                ratings.append(rating)

                rating_date = review.find('span', {'data-hook': 'review-date'}).text
                rating_dates.append(rating_date)

                title = review.find('a', {'data-hook': 'review-title'}).text
                titles.append(title)

                review_body = review.find('span', {'data-hook': 'review-body'})
                review_text = review_body.get_text(separator=" ").strip() if review_body else ""
                reviews_text.append(review_text)

            next_button = html_data.find('li', {'class': 'a-last'})
            if next_button is None or not next_button.find('a'):
                break  
            next_page_url = 'https://www.amazon.in' + next_button.find('a')['href']
            driver.get(next_page_url)
            time.sleep(3)  
    finally:
        driver.quit()

    return pd.DataFrame({
        'profile_name': names,
        'rating': ratings,
        'rating_date': rating_dates,
        'title': titles,
        'review_text': reviews_text
    })

if st.button("Scrape Reviews"):
    if url:
        try:
            review_page_url = get_review_page_url(url)
            if review_page_url:
                data = scrape_amazon_reviews(review_page_url)
                st.success(f"Scraped {len(data)} reviews!")
                st.write(data)
                st.download_button(label="Download CSV", data=data.to_csv(index=False), file_name='amazon_reviews.csv', mime='text/csv')
            else:
                st.error("Could not find the review page URL.")
        except Exception as e:
            st.error(f"Error: {e}")
    else:
        st.warning("Please enter a valid URL")
