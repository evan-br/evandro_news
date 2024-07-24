import os
import re
import time
import pandas as pd
from datetime import datetime
from dateutil.relativedelta import relativedelta
from robocorp import log
from robocorp.tasks import get_output_dir
from RPA.Browser.Selenium import Selenium
from RPA.FileSystem import FileSystem
from RPA.HTTP import HTTP
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class LaTimesScrapper:

    file = FileSystem()

    def __init__(self, search_term: str, topics_list: list, n_months: int, debug: bool = False) -> None:
        # Create output folder
        self.search_term = search_term
        self.topics_list = topics_list
        self.n_months = n_months
        self.debug = debug
        self.browser = Selenium(auto_close=self.debug)
        self.browser.set_selenium_page_load_timeout("60 seconds")
        self.browser.set_selenium_implicit_wait("60 seconds")    
     
    def setup_browser(self):
        """
        Setup the browser session with Selenium so the website can be accessed with another execution instance. 
        This allows to use the attach session from Robocorp Selenium so the browser session can be reused.
        The main function in this file is used for development porpuses and to test the code.
        """
        
        if self.debug:

            log.info('Creating a new browser session using a Chrome WebDriver with Raw Selenium')

            # Set the port for Chrome WebDriver to listen on
            options = Options()
            options.add_argument('--ignore-certificate-errors')
            options.add_argument('--ignore-ssl-errors')
            options.add_argument('--disable-infobars')
            options.add_argument("--lang=en-US")
            options.add_argument("--remote-debugging-port=9222") 
            self.driver = webdriver.Chrome(options=options)

            log.info(f"Executor URL: {self.driver.command_executor._url}")
            log.info(f"Session ID: {self.driver.session_id}")

        else:

            log.info("Using webdriver from the Selenium.Browser library")

    def open_website(self):

        # Open the website
        log.info("Opening website LA Times")
    
        if self.debug:
            self.driver.get("https://www.latimes.com/")
        else:
            self.browser.open_available_browser("https://www.latimes.com/")
    
    def search_by_search_phase(self) -> None:
        log.info(f"Searching for {self.search_term}")

        log.info("Waiting for element")
        self.browser.click_button("css:.px-2\.5")
        self.browser.input_text("name:q", self.search_term)
        self.browser.wait_and_click_button("css:.transition-bg")

        # Wait for page list to load
        news_list_locator = "xpath://ul[@class='search-results-module-results-menu']"
        self.browser.wait_until_element_is_enabled(news_list_locator)
        time.sleep(2)

    def close_website(self):
        if not self.debug:
            self.browser.close_browser()
        else:
            self.driver.quit()

    def attach_to_existing_session(self):
        log.info("Attaching to browser session")
        self.browser.attach_chrome_browser(port=9222)

    def close_ad_popup(self):
        #page.locator("[name=metering-bottompanel]").wait_for()
        #page.locator("xpath=//modality-custom-element").wait_for()
        self.browser.driver.find_element(By.CSS_SELECTOR, "a.met-flyout-close").click()
        pass

    def reset_topics(self):

        # If there are topics already set, click in the 'Reset' button
        if  self.browser.is_element_visible("xpath://a[contains(text(),'Reset')]"):

            log.info("Resetting topic search")
            self.browser.driver.find_element(By.XPATH, "//a[contains(text(),'Reset')]").click()
            time.sleep(2)
            self.browser.wait_until_element_is_not_visible("xpath://a[contains(text(),'Reset')]", timeout=45)
            #self.browser.wait_until_page_does_not_contain("Selected Filters", timeout=45)
            log.info("Removed topics filter")

    def search_by_topic(self) -> None:

        self.reset_topics()

        log.info("Searching for the topics: ", self.topics_list)

        # List of allowed topics. The Ideal would be to be saved as an asset or external file to easy modification
        list_allowed_topics = [ "World Nation",
 "Politics", "California", "Business", "Opinion", "Entertainment Arts", "Babylon Beyond", "Movies", "Books", "World Now", "Archives", "Television", "Sports", "Travel Experiences", "Soccer", "Food", "Top of the Ticket",
 "Opinion L.A.", "Olympics", "Music", "Obituaries", "Awards", "Technology and the Internet", "Science Medicine", "High School Sports", "Show Tracker", "24 Frames",
 "Recipes", "Culture Monster Blog", "Real Estate", "Nation Now", "Autos", "Technology Blog", "Lifestyle", "La Plaza", "Sports Now", "Jacket Copy", "Money Company", "Letters to the Editor",
 "Company Town", "Dodgers", "Lakers", "The Big Picture", "Company Town Blog", "Politi-Cal", "Angels", "L.A. Unleashed", "UCLA Sports", "USC Sports", "Climate Environment", "Clippers", "Pop Hiss", "Readers Representative", "Olympics Blog", "Orange County", "Daily Dish",
 "For the Record", "Hero Complex Blog", "Hockey", "Image", "All the Rage", "Awards Tracker", "L.A. at Home", "Afterword", "Booster Shots", "Housing Homelessness", "Varsity Times Insider", "About the Los Angeles Times", "L.A. Now", "Consumer Attorneys of Southern"] 

        for topic in self.topics_list:

            # If 'SEE ALL' button is visible, click on it
            if self.browser.is_element_visible("xpath://span[contains(.,'See All')]"):
                self.browser.driver.find_element(By.XPATH, "//span[contains(.,'See All')]").click()
            
            log.info("Search by topic: ", topic)
            if topic not in list_allowed_topics:
                log.info(f"Topic {topic} is not in the list of allowed topics")
                continue
            
            log.info(f"Clicking on topic {topic}")
            self.browser.driver.find_element(By.XPATH, f"//span[contains(.,'{topic}')]").click()
            
            time.sleep(2)

            # Set delay after click
            self.browser.wait_until_element_is_enabled("//ul[@class='search-results-module-results-menu']")

    def sort_by_latest(self):

        # Wait for Dropdown to be completly loaded
        self.browser.wait_until_element_is_enabled("name:s")

        dropdown = self.browser.driver.find_element(By.NAME, "s")
        dropdown.find_element(By.XPATH, "//option[. = 'Newest']").click()
       
        # Wait for page list to load
        news_list_locator = "xpath://ul[@class='search-results-module-results-menu']"
        self.browser.wait_until_element_is_enabled(news_list_locator)
        time.sleep(2)

    def navigate_to_next_page(self):
        nav_buttons = self.browser.driver.find_elements(By.CSS_SELECTOR, "a > .chevron-icon")

        if len(nav_buttons) == 2:
            nav_buttons[1].click()
        else:
            nav_buttons[0].click()

        # Wait for page list to load
        news_list_locator = "xpath://ul[@class='search-results-module-results-menu']"
        self.browser.wait_until_element_is_enabled(news_list_locator)

    def parse_date(self, date_string, formats):
        for fmt in formats:
            try:
                return datetime.strptime(date_string, fmt)
            except ValueError:
                continue
        raise ValueError(f"Date string '{date_string}' does not match any of the provided formats.")

    def extract_news_info(self, news_element: WebElement) -> dict:

        # Extract title
        title_element = news_element.find_element(By.CSS_SELECTOR, '.promo-title a')
        title = title_element.text

        # Extract date, if conversion fails, the date is set to the current date
        try:
            date_element = news_element.find_element(By.CSS_SELECTOR, '.promo-timestamp')
            date_string = date_element.text
            # Remove any dot characters from the string
            date_string = date_string.replace(".", "")
            month = re.search(r'^\S+', date_string).group(0)
            month_str = month[:3]
            date_string = date_string.replace(month, month_str)
            date = self.parse_date(date_string, ["%b %d, %Y", "%B %d, %Y"])
        except Exception as e:
            log.info(f"Failed to convert date string: {date_string}. Error: {e}")
            date = datetime.now()

        # Extract description
        description = ""
        description_elements = news_element.find_elements(By.CSS_SELECTOR, '.promo-description')
        if description_elements:
            description = description_elements[0].text

        # Extract picture filename
        # Assuming the picture is in an img tag under the outer_element
        picture_filename = ""
        picture_elements = news_element.find_elements(By.CSS_SELECTOR, 'img')
        if picture_elements:
            picture_url = picture_elements[0].get_attribute('src')
            picture_filename = picture_url.split('/')[-1]
            # Download the Picture and place it in the output folder. Only S3 bucked saved images are available
            if 's3.amazonaws.com' in picture_filename:
                picture_filename = picture_filename.split('s3.amazonaws.com')[-1]
                self.download_picture(picture_url, f"output/{picture_filename}")
            else:
                picture_filename = ""

        # Count of search phrases in the title and description
        search_phrases = [self.search_term] 
        count = sum(phr in title + description for phr in search_phrases)
        
        # Check if title or description contains any amount of money
        money_regex = r"\$\d+(\.\d{1,2})?|\d+ dollars|\d+ USD"
        contains_money = bool(re.search(money_regex, title + description))

        return {
            "title": title,
            "date": date,
            "description": description,
            "picture_filename": picture_filename,
            "count_of_search_phrases": count,
            "contains_money": contains_money
        }

    def extract_news_list(self) -> pd.DataFrame:
        
        if self.n_months > 1:
            datetime_search_limit = datetime.now() - relativedelta(months=self.n_months)
        else:
            datetime_search_limit = datetime.now() - relativedelta(months=1)

        # Create an empty DataFrame to store the news data
        df = pd.DataFrame()

        n_pages_extracted = 1
        while True:

            log.info(f"Extracting news from page {n_pages_extracted}º")

            # Extract current news list in the page
            news_list_locator = "xpath://ul[@class='search-results-module-results-menu']"
            news_page = self.browser.find_element(news_list_locator)
            news_list = news_page.find_elements(By.TAG_NAME, "li")

            for news in news_list:
                news_data = self.extract_news_info(news) 
                
                # Check if the news is older than the datetime_search_limit
                if news_data['date'] < datetime_search_limit:
                    
                    # If yes, remove the older news from the DataFrame and stop the extraction
                    
                    # If DataFrame empty, send empty dataframe
                    if df.empty:
                        return df

                    df = df[df['date'] >= datetime_search_limit]
                    return df

                # If not, add the news data to the DataFrame
                df_news = pd.DataFrame([news_data])
                df_news['date'] = pd.to_datetime(df_news['date'])
                df = pd.concat([df, df_news], ignore_index=True)

            # Navigate to the next page and wait for the news to load
            self.navigate_to_next_page()
            self.browser.wait_until_element_is_enabled(news_list_locator)
            n_pages_extracted += 1
    
    def download_picture(self, url: str, output_path: str) -> None:
        http = HTTP()
        http.download(url=url, 
                      target_file=output_path, 
                      overwrite=True)

    def run(self):
        self.setup_browser()
        self.open_website()
        self.search_by_search_phase()
        self.search_by_topic()
        self.sort_by_latest()
        df_news = self.extract_news_list()
        df_news.to_excel(f"output/news_data.xlsx", index=False)
        self.close_website()

def main():


    website = LaTimesScrapper(search_term="GPT", topics_list=["Technology and the Internet"], n_months=8, debug=False)
    website.run()

    #website.setup_browser()
    #website.open_website()
    
    """
    website.attach_to_existing_session()
    website.search_by_search_phase()
    website.search_by_topic()
    website.sort_by_latest()
    df_news = website.extract_news_list()
    df_news.to_excel(f"output/news_Barbie.xlsx", index=False)
    """

    input("Press Enter to finish execution")
    log.info("Execution completed successfully")

if __name__ == "__main__":
    """Perform unit tests when run as a script. Enables quick unit testing with each function call without the need to reopen the webite each time."""
    main()