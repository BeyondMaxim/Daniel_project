from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import time
import logging
import pandas as pd
import requests
from datetime import datetime, timedelta
from selenium.webdriver.common.action_chains import ActionChains
import re
import os

logging.basicConfig(
    filename="./chron-Alberpark-Glfclub-data/alberpark.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)


class AlbertparkScraper:
    def __init__(self, base_url):
        # Initialize the Selenium webdriver
        self.driver = webdriver.Chrome()
        self.base_url = base_url
        self.scrap_data = []

    def export_to_excel(self, course_name, course_data):
        """
        Export course data to Excel files.
        """

        logging.info("Exporting course data to Excel for course: %s", course_name)
        file_path = f"./chron-Alberpark-Glfclub-data/{course_name}.xlsx"
        if os.path.exists(file_path):
            with pd.ExcelWriter(file_path, mode="w") as writer:
                for date, data in course_data.items():
                    df = pd.DataFrame(
                        data,
                        columns=[
                            "Slot_tee_time",
                            "Slot_tee",
                            "Price",
                            "Available Count",
                        ],
                    )
                    df.to_excel(writer, sheet_name=date, index=False)
        else:
            with pd.ExcelWriter(file_path) as writer:
                for date, data in course_data.items():
                    df = pd.DataFrame(
                        data,
                        columns=[
                            "Slot_tee_time",
                            "Slot_tee",
                            "Price",
                            "Available Count",
                        ],
                    )
                    df.to_excel(writer, sheet_name=date, index=False)

    def scrape_slot_tee(self, courses_pairent_div, wait_courses):

        wait = WebDriverWait(self.driver, 10)
        slot_tee_span = wait.until(
            EC.presence_of_element_located(
                (
                    By.XPATH,
                    "//div[contains(@class, 'widget-step-course')]//span[contains(@class, 'ng-binding')]",
                )
            )
        )
        slot_tee = slot_tee_span.text
        print(slot_tee)
        subhead_button = wait_courses.until(
            EC.presence_of_element_located(
                (By.XPATH, "//div[contains(@class, 'widget-subhead')]//button")
            )
        )
        subhead_button.click()
        time.sleep(1)
        available_counts_div = wait.until(
            EC.presence_of_element_located(
                (By.XPATH, '//div[contains(@class, "widget-step-players")]')
            )
        )
        try:
            # Available counts loop
            available_counts_div = wait.until(
                EC.presence_of_element_located(
                    (By.XPATH, '//div[contains(@class, "widget-step-players")]')
                )
            )
            available_counts_div.click()
            time.sleep(1)
            wait_counts = WebDriverWait(available_counts_div, 10)
            available_as = wait_counts.until(
                EC.presence_of_all_elements_located(
                    (By.XPATH, "//a[contains(@ng-model, 'nbPlayers')]")
                )
            )
            print(len(available_as))
            slot_tee_times = []
            available_count_dict = {}
            price_dict = {}
            for index_available, available_a in enumerate(available_as):

                available_counts = int((available_as[index_available].text))
                print(available_counts)
                available_as[index_available].click()
                time.sleep(1)
                under_button = wait_counts.until(
                    EC.presence_of_element_located(
                        (By.XPATH, "//button[contains(@class, 'fl-button-primary')]")
                    )
                )
                under_button.click()
                time.sleep(3)
                # extracting the price and slot tee times.

                available_slot_time_div = wait.until(
                    EC.presence_of_element_located(
                        (By.XPATH, "//div[contains(@class, 'widget-step-teetime')]")
                    )
                )

                # Find all li elements with ng-repeat attribute containing "bookable"
                bookable_li_elements = WebDriverWait(available_slot_time_div, 10).until(
                    EC.presence_of_all_elements_located(
                        (By.XPATH, '//li[contains(@ng-repeat,"bookable")]')
                    )
                )
                print(len(bookable_li_elements))
                for ind_li, li in enumerate(bookable_li_elements):

                    wait_li = WebDriverWait(li, 1)
                    try:
                        slot_tee_time = wait_li.until(
                            EC.presence_of_element_located(
                                (
                                    By.XPATH,
                                    './/booking-widget-teetime//div[contains(@class,"widget-teetime-tag")]',
                                )
                            )
                        )

                        slot_tee_price = wait_li.until(
                            EC.presence_of_element_located(
                                (
                                    By.XPATH,
                                    './/booking-widget-teetime//span[contains(@class,"widget-teetime-total")]',
                                )
                            )
                        )

                        slot_tee_time = slot_tee_time.text.strip()
                        slot_price = slot_tee_price.text.strip()
                        # print(f"Availablve time: {slot_tee_time}   Price: {slot_price}")

                        if slot_tee_time in slot_tee_times:
                            available_count_dict[slot_tee_time] = available_counts
                        else:
                            slot_tee_times.append(slot_tee_time)
                            price_dict[slot_tee_time] = slot_price
                            available_count_dict[slot_tee_time] = available_counts
                    except:
                        continue

                available_counts_div = wait.until(
                    EC.presence_of_element_located(
                        (By.XPATH, '//div[contains(@class, "widget-step-players")]')
                    )
                )
                available_counts_div.click()
                # Available counts loop
                time.sleep(1)
                wait_counts = WebDriverWait(available_counts_div, 10)
                available_as = wait_counts.until(
                    EC.presence_of_all_elements_located(
                        (By.XPATH, "//a[contains(@ng-model, 'nbPlayers')]")
                    )
                )
            print(
                f"slot tee:{slot_tee}, slot_te_times: {slot_tee_times}, price_dict: {price_dict}, available_count: { available_count_dict}"
            )

            for slot_tee_time in slot_tee_times:
                self.scrap_data.append(
                    [
                        slot_tee_time,
                        slot_tee,
                        price_dict[slot_tee_time],
                        available_count_dict[slot_tee_time],
                    ]
                )
            courses_pairent_div = wait.until(
                EC.presence_of_element_located(
                    (By.XPATH, '//div[contains(@class, "widget-step-course")]')
                )
            )
            courses_pairent_div.click()
        except Exception as e:
            print(f"eorr : {e}")
            # Create an ActionChains object
            actions = ActionChains(self.driver)
            # Move the mouse to the element
            actions.move_to_element(available_counts_div).perform()
            # Click the element
            available_counts_div.click()
            time.sleep(3)

    def scrape_data(self):
        # Navigate to the website
        self.driver.get(self.base_url)
        # Wait for the page to load
        wait = WebDriverWait(self.driver, 10)
        # Select the Ifram that contains the teetime widget and convert  ifram to content.
        iframe = wait.until(
            EC.presence_of_element_located(
                (By.XPATH, "//iframe[@title='Profile Page Booking Widget']")
            )
        )
        self.driver.switch_to.frame(iframe)

        course_data = {}
        # Lopp for up to date 5 days.
        for i in range(5):
            # Select the table that contain the calender from the self.driver that is a fraim currently.
            search_date_table = wait.until(
                EC.presence_of_element_located(
                    (By.XPATH, '//table[@class = "uib-daypicker"]')
                )
            )
            wait_teetimes = WebDriverWait(search_date_table, 10)
            # select the active date and get the id to click button
            start_date_td_id = wait_teetimes.until(
                EC.presence_of_element_located(
                    (
                        By.XPATH,
                        '//button[contains(@class,"active")]/parent::td[contains(@class,"text-center")]',
                    )
                )
            )
            start_date_td_id = start_date_td_id.get_attribute("id")
            logging.info("Id of start date td  : %s", start_date_td_id)
            parts = start_date_td_id.split("-")
            base_id = "-".join(parts[:-1]) + "-"
            if i == 0:
                sum_number = 0
            else:
                sum_number = 1
            last_number = int(parts[-1]) + sum_number
            new_id = f"{base_id}{last_number}"
            print(new_id)
            date_button = wait_teetimes.until(
                EC.presence_of_element_located(
                    (By.XPATH, f"//td[@id='{new_id}']//button")
                )
            )
            time.sleep(1)
            date_button.click()
            # after selecting the date, get the value from span that contain the active date then convert %Y-%m-%d
            date_span = wait_teetimes.until(
                EC.presence_of_element_located(
                    (
                        By.XPATH,
                        './/div[contains(@class,"widget-step-date")]//span[contains(@class ,"ng-binding")]',
                    )
                )
            )
            date_string = date_span.text
            date_parts = date_string.split()
            date_str = datetime.strptime(" ".join(date_parts[1:]), "%B %d, %Y")
            date = date_str.strftime("%Y-%m-%d")
            print(date)
            time.sleep(2)
            # selecting avaiable courses.
            courses_pairent_div = wait.until(
                EC.presence_of_element_located(
                    (By.XPATH, '//div[contains(@class, "widget-step-course")]')
                )
            )
            courses_pairent_div.click()
            time.sleep(1)
            wait_courses = WebDriverWait(courses_pairent_div, 10)
            course_li_as = wait_courses.until(
                EC.presence_of_all_elements_located(
                    (By.XPATH, '//ul//li[contains(@class,"toggler-choice")]//a')
                )
            )
            for index_li, course_li_a in enumerate(course_li_as):
                time.sleep(1)
                course_li_as[index_li].click()
                holes_click_div = wait_courses.until(
                    EC.presence_of_element_located(
                        (By.XPATH, '//div[contains(@ng-show, "showHoleOptions")]')
                    )
                )
                holes_click_as = WebDriverWait(holes_click_div, 10).until(
                    EC.presence_of_all_elements_located(
                        (By.XPATH, '//a[contains(@class, "toggler-heading")]')
                    )
                )
                if len(holes_click_as) == 1:
                    self.scrape_slot_tee(courses_pairent_div, wait_courses)
                else:
                    for index, holes_click_a in enumerate(holes_click_as):

                        holes_click_as[index].click()
                        time.sleep(2)
                        self.scrape_slot_tee(courses_pairent_div, wait_courses)

                        holes_click_as = WebDriverWait(courses_pairent_div, 10).until(
                            EC.presence_of_all_elements_located(
                                (By.XPATH, '//a[contains(@class, "toggler-heading")]')
                            )
                        )
                courses_pairent_div = wait.until(
                    EC.presence_of_element_located(
                        (By.XPATH, '//div[contains(@class, "widget-step-course")]')
                    )
                )
                courses_pairent_div.click()
                time.sleep(1)
                wait_courses = WebDriverWait(courses_pairent_div, 10)
                course_li_as = wait_courses.until(
                    EC.presence_of_all_elements_located(
                        (By.XPATH, '//ul//li[contains(@class,"toggler-choice")]//a')
                    )
                )

            course_data[date] = self.scrap_data
            self.scrap_data = []

            # Opening caleander to click the date.
            date_reset_button = wait.until(
                EC.presence_of_element_located(
                    (By.XPATH, '//div[contains(@class,"widget-step-date")]')
                )
            )
            time.sleep(1)
            date_reset_button.click()
            time.sleep(1)
            # break
        # Returning self deiver to default statement.
        self.driver.switch_to.default_content()
        course_name = "Chrongolf-Albertpark"
        self.export_to_excel(course_name, course_data)
        self.driver.quit()


base_url = "https://www.chronogolf.com/club/albert-park-golf-course"
# Usage example
scraper = AlbertparkScraper(base_url)
scraper.scrape_data()
