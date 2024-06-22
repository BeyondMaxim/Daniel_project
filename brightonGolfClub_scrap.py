from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import time
import logging
import pandas as pd
import requests
import os

logging.basicConfig(
    filename="./brighton-Golfclub-data/brightonscraper.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)


class BrightonScraper:
    def __init__(self, base_url, price_url):
        # Initialize the Selenium webdriver
        self.driver = webdriver.Chrome()
        self.base_url = base_url
        self.price_url = price_url

    def scrape_price(self):
        """
        Extract the Green Fees
        """
        logging.info("Extracting Green Fees for course: %s", self.price_url)
        response = requests.get(self.price_url)
        soup = BeautifulSoup(response.content, "html.parser")
        fee_dict = {}
        green_fees_data = soup.find("meta", {"property": "og:description"}).get(
            "content"
        )
        green_fees_data = green_fees_data.split("GREEN FEES – CASUAL USERS")[1].strip()
        green_fees_data = green_fees_data.split("Adult")[1].strip()
        fee_dict["hole_9_adult_fee"], fee_dict["hole_18_adult_fee"] = (
            green_fees_data.split(" ")[:2]
        )
        green_fees_data = green_fees_data.split("Concession*")[1].strip()
        fee_dict["hole_9_concession_fee"], fee_dict["hole_18_concession_fee"] = (
            green_fees_data.split(" ")[:2]
        )
        green_fees_data = green_fees_data.split("Seniors*")[1].strip()
        fee_dict["hole_9_Seniors_fee"], fee_dict["hole_18_Seniors_fee"] = (
            green_fees_data.split(" ")[:2]
        )
        return fee_dict

    def export_to_excel(self, course_name, course_data):
        """
        Export course data to Excel files.
        """
        logging.info("Exporting course data to Excel for course: %s", course_name)
        file_path = f"./brighton-Golfclub-data/{course_name}.xlsx"
        if os.path.exists(file_path):
            with pd.ExcelWriter(file_path, mode="w") as writer:
                for date, data in course_data.items():
                    df = pd.DataFrame(
                        data,
                        columns=[
                            "slot_tee_time",
                            "slot_tee",
                            "fee_types",
                            "available_count",
                            "Junior 9 Hole",
                            "Junior 18 Hole",
                            "Seniors 9 Hole",
                            "Seniors 18 Hole",
                            "Adult 9 Hole",
                            "Adult 18 Hole",
                        ],
                    )
                    df.to_excel(writer, sheet_name=date, index=False)
        else:
            with pd.ExcelWriter(file_path) as writer:
                for date, data in course_data.items():
                    df = pd.DataFrame(
                        data,
                        columns=[
                            "slot_tee_time",
                            "slot_tee",
                            "fee_types",
                            "available_count",
                            "Junior 9 Hole",
                            "Junior 18 Hole",
                            "Seniors 9 Hole",
                            "Seniors 18 Hole",
                            "Adult 9 Hole",
                            "Adult 18 Hole",
                        ],
                    )
                    df.to_excel(writer, sheet_name=date, index=False)

    def scrape_data(self):
        # Navigate to the website
        self.driver.get(self.base_url)

        # Wait for the page to load
        wait = WebDriverWait(self.driver, 10)
        search_container = wait.until(
            EC.presence_of_element_located((By.CLASS_NAME, "searchContainer"))
        )

        # Wait for the elements to load
        wait = WebDriverWait(self.driver, 10)
        search_tees = wait.until(
            EC.presence_of_all_elements_located((By.CLASS_NAME, "searchTee"))
        )
        logging.info("Number of search tees found: %s", len(search_tees))

        # Choose the option value in the "startTee" select within the first "searchTee" div
        start_tee_select = search_tees[0].find_element(By.ID, "startTee")
        start_tee_select.click()
        start_tee_options = start_tee_select.find_elements(By.TAG_NAME, "option")

        date_select = search_tees[1].find_element(By.ID, "dateTeeTime")
        date_select.click()
        date_options = date_select.find_elements(By.TAG_NAME, "option")
        logging.info("Number of date options found: %s", len(date_options))
        date_index = 0
        course_data = {}
        fee_dict = self.scrape_price()
        for date_option in date_options:
            date = date_option.get_attribute("value")
            logging.info("Scraping data for date: %s", date)
            date_index = date_index + 1
            time.sleep(1)
            date_option.click()
            time.sleep(1)

            slot_data = []
            for option in start_tee_options:
                slot_tee_init = option.text
                logging.info("Scraping data for start tee: %s", slot_tee_init)
                time.sleep(1)
                option.click()
                time.sleep(1)

                hole_select = search_tees[2].find_element(By.ID, "hole")
                hole_select.click()
                hole_options = hole_select.find_elements(By.TAG_NAME, "option")
                logging.info("Number of hole options found: %s", len(hole_options))
                for hole_option in hole_options:
                    junior_9_hole = junior_18_hole = seniors_9_hole = (
                        seniors_18_hole
                    ) = adult_9_hole = adult_18_hole = ""
                    slot_tee = f"{slot_tee_init}-{hole_option.text}"
                    if "9 Hole" in slot_tee:
                        junior_9_hole, seniors_9_hole, adult_9_hole = (
                            fee_dict["hole_9_concession_fee"],
                            fee_dict["hole_9_Seniors_fee"],
                            fee_dict["hole_9_adult_fee"],
                        )
                    else:
                        junior_18_hole, seniors_18_hole, adult_18_hole = (
                            fee_dict["hole_18_concession_fee"],
                            fee_dict["hole_18_Seniors_fee"],
                            fee_dict["hole_18_adult_fee"],
                        )
                    logging.info("Scraping data for slot tee: %s", slot_tee)
                    time.sleep(1)
                    hole_option.click()
                    time.sleep(1)
                    hole_select.click()

                    # Search button click
                    search_button = search_tees[4].find_element(
                        By.CLASS_NAME, "searchTeeTime"
                    )
                    search_button.click()

                    # Wait for the search results to load
                    wait = WebDriverWait(self.driver, 10)
                    previous_tee_time_count = 0
                    current_tee_time_count = 0
                    flag = False
                    while True:
                        try:
                            # Wait for the search results to load
                            wait.until(
                                EC.presence_of_all_elements_located(
                                    (By.CLASS_NAME, "teetime")
                                )
                            )
                            wait.until(
                                EC.presence_of_all_elements_located(
                                    (By.CLASS_NAME, "teetime_col")
                                )
                            )

                            # Parse the search results using BeautifulSoup
                            soup = BeautifulSoup(self.driver.page_source, "html.parser")
                            search_results = soup.find_all("div", class_="teetime")
                            current_tee_time_count = len(search_results)
                            # Check if the number of teetime divs has stopped increasing
                            if current_tee_time_count == previous_tee_time_count:
                                break
                            previous_tee_time_count = current_tee_time_count
                            flag = True
                            logging.info(
                                "Number of search results found: %s",
                                len(search_results),
                            )
                        except Exception as e:
                            # logging.error('Error occurred while waiting for search results: %s', e)
                            break
                    if flag == False:
                        continue
                    for slot in search_results:
                        try:
                            slot_tee_time = slot.find("span", class_="teetime_clock")
                            fee_types = slot.find("span", class_="teetime_greenfee")
                            players_element = slot.find("strong")
                            if slot_tee_time:
                                slot_tee_time = slot_tee_time.text.strip()
                            else:
                                slot_tee_time = "N/A"
                            if fee_types:
                                fee_types = fee_types.text.strip()
                            else:
                                fee_types = "N/A"
                            if players_element:
                                available_count = int(
                                    players_element.get_text(strip=True)
                                    .replace("players", "")
                                    .strip()
                                )
                            else:
                                available_count = 0
                            slot_data.append(
                                [
                                    slot_tee_time,
                                    slot_tee,
                                    fee_types,
                                    available_count,
                                    junior_9_hole,
                                    junior_18_hole,
                                    seniors_9_hole,
                                    seniors_18_hole,
                                    adult_9_hole,
                                    adult_18_hole,
                                ]
                            )
                            print(slot_data)
                        except Exception as e:
                            # logging.error('Error occurred while parsing search results: %s', e)
                            print(e)
                    if "Start Tee 10" in slot_tee_init:
                        # logging.info('Reached the end of the search results for the current date')
                        break

                # Click on the "startTee" select again to open the options
                start_tee_select.click()
            course_data[date] = slot_data
            date_select.click()
            if date_index == 5:
                logging.info(
                    "Reached the maximum number of dates to scrape, stopping the process"
                )
                break
        course_name = "bightonGolfClup"

        self.export_to_excel(course_name, course_data)
        # Close the webdriver
        self.driver.quit()


base_url = "https://brightongolfcourse.com.au/book/"
price_url = "https://brightongolfcourse.com.au/fees/"
# Usage example
scraper = BrightonScraper(base_url, price_url)
scraper.scrape_data()
