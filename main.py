import streamlit as st
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from bs4 import BeautifulSoup
import time
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

st.title("Amazon Reviews Scraper")
url = st.text_input("Enter Amazon product URL")

def get_review_page_url(product_url):
    chrome_driver_path = "./chromedriver.exe"  
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--disable-gpu')
    driver = webdriver.Chrome(service=Service(chrome_driver_path), options=options)

    try:
        driver.get(product_url)
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'body')))
        html_data = BeautifulSoup(driver.page_source, 'html.parser')

        # Try to find the 'See All Reviews' link
        reviews_link = html_data.find('a', {'data-hook': 'see-all-reviews-link-foot'})
        if reviews_link:
            reviews_url = 'https://www.amazon.in' + reviews_link['href']
        else:
            # Alternative method to find the reviews link
            try:
                alt_reviews_link = driver.find_element(By.XPATH, "//a[contains(@href, 'customerReviews')]")
                reviews_url = alt_reviews_link.get_attribute('href')
            except Exception:
                reviews_url = None
    except Exception as e:
        st.error(f"Error retrieving review page URL: {e}")
        reviews_url = None
    finally:
        driver.quit()

    return reviews_url

def scrape_amazon_reviews(reviews_url):
    chrome_driver_path = "./chromedriver.exe"
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--disable-gpu')
    driver = webdriver.Chrome(service=Service(chrome_driver_path), options=options)

    names = []
    ratings = []
    rating_dates = []
    titles = []
    reviews_text = []

    rating_distribution = {'5 star': 0, '4 star': 0, '3 star': 0, '2 star': 0, '1 star': 0}
    total_reviews = None

    try:
        driver.get(reviews_url)

        while True:
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, "div[data-hook='review']")))
            html_data = BeautifulSoup(driver.page_source, 'html.parser')

            # Scrape review text
            reviews = html_data.find_all('div', {'data-hook': 'review'})
            for review in reviews:
                # Name
                name_tag = review.find('span', {'class': 'a-profile-name'})
                name = name_tag.text.strip() if name_tag else "Unknown"
                names.append(name)

                # Rating
                rating_tag = review.find('span', {'class': 'a-icon-alt'})
                rating = rating_tag.text.strip() if rating_tag else "No Rating"
                ratings.append(rating)

                # Rating Date
                rating_date_tag = review.find('span', {'data-hook': 'review-date'})
                rating_date = rating_date_tag.text.strip() if rating_date_tag else "No Date"
                rating_dates.append(rating_date)

                # Title
                title_tag = review.find('a', {'data-hook': 'review-title'})
                if not title_tag:
                    title_tag = review.find('span', {'data-hook': 'review-title'})
                title = title_tag.text.strip() if title_tag else "No Title"
                titles.append(title)

                # Review Text
                review_body = review.find('span', {'data-hook': 'review-body'})
                review_text = review_body.get_text(separator=" ").strip() if review_body else "No Review Text"
                reviews_text.append(review_text)
            
            # Scrape rating distribution
            histogram_columns = html_data.find_all('span', {'class': 'histogram-column-space'})
            for index, column in enumerate(histogram_columns):
                percentage = column.text.strip()
                if percentage:
                    star_rating = 5 - index  # 5 star is first, 1 star is last
                    if star_rating<=0:
                        rating_distribution[f'{star_rating+5} star'] = percentage
            rating_distribution=dict(list(rating_distribution.items())[:5])
            # Scrape total review count
            review_count_div = html_data.find('div', {'data-hook': 'total-review-count'})
            if review_count_div:
                total_reviews_text = review_count_div.get_text(strip=True)
                total_reviews = int(total_reviews_text.split(' ')[0].replace(',', ''))

            # Check for next page
            next_button = html_data.find('li', {'class': 'a-last'})
            if next_button is None or not next_button.find('a'):
                break  # No more pages
            next_page_url = 'https://www.amazon.in' + next_button.find('a')['href']
            driver.get(next_page_url)
    except Exception as e:
        st.error(f"Error scraping reviews: {e}")
    finally:
        driver.quit()

    # Create DataFrames
    rating_distribution_df = pd.DataFrame(list(rating_distribution.items()), columns=['Rating', 'Percentage'])
    review_count_df = pd.DataFrame({'Total Reviews': [total_reviews]})

    reviews_df = pd.DataFrame({
        'profile_name': names,
        'rating': ratings,
        'rating_date': rating_dates,
        'title': titles,
        'review_text': reviews_text
    })

    return reviews_df, rating_distribution_df, review_count_df

if st.button("Scrape Reviews"):
    if url:
        try:
            review_page_url = get_review_page_url(url)
            if review_page_url:
                data, rating_distribution_df, review_count_df = scrape_amazon_reviews(review_page_url)
                st.success(f"Scraped {len(data)} reviews!")
                st.write(data)
                st.download_button(label="Download Reviews CSV", data=data.to_csv(index=False), file_name='amazon_reviews.csv', mime='text/csv')
                
                st.write("Rating Distribution:")
                st.write(rating_distribution_df)
                st.download_button(label="Download Rating Distribution CSV", data=rating_distribution_df.to_csv(index=False), file_name='rating_distribution.csv', mime='text/csv')
                
                st.write("Total Reviews:")
                st.write(review_count_df)
                st.download_button(label="Download Total Reviews CSV", data=review_count_df.to_csv(index=False), file_name='total_reviews.csv', mime='text/csv')
            else:
                st.error("Could not find the review page URL.")
        except Exception as e:
            st.error(f"Error: {e}")
    else:
        st.warning("Please enter a valid URL")
