import streamlit as st
from scrape import scrape_website,split_dom_content,clean_body_content,extract_body_content
st.title("AI Web Scarper")
url=st.text_input("Enter the website URL: ")
if st.button("Scrape Site"):
    st.write("Scraping the website")
    result=scrape_website(url)
    body_content=extract_body_content(result)
    cleaned_content=clean_body_content(body_content)
    st.session_state.dom_content=cleaned_content
    with st.expander("View DOM Content"):
        st.text_area("DOM Content",cleaned_content,height=300)
if "dom_content" in st.session_state:
    parse_description = (
        "Extract the customer reviews and their corresponding ratings from the provided DOM content. "
        "Identify any common themes or trends based on the reviews and ratings, such as recurring positive or negative comments about specific features. "
        "Provide a summary of these trends after listing the reviews and ratings. "
        "Only include the relevant text for reviews, ratings, and trends, and ignore any other content."
    )