import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import pandas as pd
import logging
import os

# Configure logging
logging.basicConfig(
    filename="./morningtonGolfclub_Data/scraper.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)


class GolfClubScraper:
    def __init__(self, base_url, course_url):
        """
        Initialize the GolfClubScraper class with base_url and course_url.
        """
        self.base_url = base_url
        self.course_url = course_url
        logging.info(
            "GolfClubScraper initialized with base_url: %s and course_url: %s",
            base_url,
            course_url,
        )

    def get_course_status(self, feeid_value, course_name):
        """
        Extract course status data for a specific course.
        """
        logging.info("Getting course status for course: %s", course_name)
        # Define the number of days to scrape bookings for
        num_days = 5
        course_data = {}

        # Loop through each day
        for i in range(num_days):
            # Calculate the date for the current day
            date = (datetime.now() + timedelta(days=i)).strftime("%Y-%m-%d")

            # Construct the URL for the current day
            url = f"{self.course_url}&selectedDate={date}&feeGroupId={feeid_value}"

            # Send a GET request to the URL
            response = requests.get(url)

            # Parse the HTML content using BeautifulSoup
            soup = BeautifulSoup(response.content, "html.parser")

            # Find all the booking slots on the page
            booking_slots = soup.select("div[class*=row-time]")

            slot_data = []
            for slot in booking_slots:
                fee_items = slot.select("div.fees-wrapper ul li")
                # Extract and print the price and type information
                fee_types = []
                prices = []
                for index, item in enumerate(fee_items):
                    price = item.find("span", class_="price").get_text(strip=True)
                    fee_type = item.get_text(strip=True).replace(price, "").strip()
                    prices.append(price)
                    fee_types.append(fee_type)
                # Count available booting and Taken booking
                p_elements = slot.select("div.records-wrapper p.small")
                taken_count = 0
                available_count = 0

                for p_element in p_elements:
                    text = p_element.get_text(strip=True)
                    if text == "Taken":
                        taken_count += 1
                    elif text == "Available":
                        available_count += 1
                ###---Booking ID for every booking time---
                data_value = slot.get("data-value")
                ###---Booking Time and Tee
                slot_tee_time = slot.find("h3").text
                slot_tee = slot.find("h4").text

                slot_data.append(
                    [
                        slot_tee_time,
                        slot_tee,
                        fee_types,
                        prices,
                        taken_count,
                        available_count,
                    ]
                )

            course_data[date] = slot_data

        self.export_to_excel(course_name, course_data)

    def scrape_course_data(self):
        """
        Scrape course data for all courses.
        """
        logging.info("Scraping course data for all courses")
        response = requests.get(self.base_url)
        soup = BeautifulSoup(response.content, "html.parser")
        # Find the all course based on base_url
        fee_group_rows = soup.select("div[class*=feeGroupRow]")
        # Loop all course base on base_url
        for row in fee_group_rows:
            feeid_value = row.get("data-feeid")
            course_name = row.find("h3").text
            self.get_course_status(feeid_value, course_name)

    def export_to_excel(self, course_name, course_data):
        """
        Export course data to Excel files.
        """
        logging.info("Exporting course data to Excel for course: %s", course_name)
        file_path = f"./morningtonGolfclub_Data/{course_name}.xlsx"

        if os.path.exists(file_path):
            # Append the data to the existing file
            with pd.ExcelWriter(file_path, mode="w") as writer:
                for date, data in course_data.items():
                    df_data = []
                    fee_types_set = set()
                    prices_dict = {}
                    for slot in data:
                        slot_tee_time = slot[0]
                        slot_tee = slot[1]
                        taken_count = slot[-2]
                        available_count = slot[-1]
                        prices = slot[3]
                        fee_types = slot[2]

                        for fee_type, price in zip(fee_types, prices):
                            fee_types_set.add(fee_type)
                            if fee_type not in prices_dict:
                                prices_dict[fee_type] = [price]
                            else:
                                prices_dict[fee_type].append(price)

                        # Append the slot information and prices to df_data
                        row = [slot_tee_time, slot_tee, taken_count, available_count]
                        for fee_type in fee_types_set:
                            row.append(
                                prices_dict.get(fee_type, [""])[0]
                                if len(prices_dict.get(fee_type, [""])) > 0
                                else ""
                            )
                        df_data.append(row)
                    # Create the DataFrame with dynamic column names based on fee types
                    columns = [
                        "slot_tee_time",
                        "slot_tee",
                        "taken_count",
                        "available_count",
                    ] + list(fee_types_set)
                    df = pd.DataFrame(df_data, columns=columns)
                    df.to_excel(writer, sheet_name=date, index=False)
        else:
            with pd.ExcelWriter(file_path) as writer:
                for date, data in course_data.items():
                    df_data = []
                    fee_types_set = set()
                    prices_dict = {}
                    for slot in data:
                        slot_tee_time = slot[0]
                        slot_tee = slot[1]
                        taken_count = slot[-2]
                        available_count = slot[-1]
                        prices = slot[3]
                        fee_types = slot[2]

                        for fee_type, price in zip(fee_types, prices):
                            fee_types_set.add(fee_type)
                            if fee_type not in prices_dict:
                                prices_dict[fee_type] = [price]
                            else:
                                prices_dict[fee_type].append(price)

                        # Append the slot information and prices to df_data
                        row = [slot_tee_time, slot_tee, taken_count, available_count]
                        for fee_type in fee_types_set:
                            row.append(
                                prices_dict.get(fee_type, [""])[0]
                                if len(prices_dict.get(fee_type, [""])) > 0
                                else ""
                            )
                        df_data.append(row)
                    # Create the DataFrame with dynamic column names based on fee types
                    columns = [
                        "slot_tee_time",
                        "slot_tee",
                        "taken_count",
                        "available_count",
                    ] + list(fee_types_set)
                    df = pd.DataFrame(df_data, columns=columns)
                    df.to_excel(writer, sheet_name=date, index=False)


# Define the base URL for the Waverley Golf Club booking page
base_url = "https://www.morningtongolf.com.au/guests/bookings/ViewPublicCalendar.msp?booking_resource_id=3000000"
course_url = "https://www.morningtongolf.com.au/guests/bookings/ViewPublicTimesheet.msp?bookingResourceId=3000000"

# Create an instance of the GolfClubScraper class
scraper = GolfClubScraper(base_url, course_url)

# Call the scrape_course_data method to initiate the scraping process and export the data to Excel files
scraper.scrape_course_data()
