import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import pandas as pd
import logging
import os

# Configure logging
logging.basicConfig(
    filename="./sandringham-Golfclub-Data/scraper.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)


class GolfClubScraper:
    def __init__(self, base_url):
        """
        Initialize the GolfClubScraper class with base_url and course_url.
        """
        self.base_url = base_url
        logging.info("GolfClubScraper initialized with base_url: %s ", base_url)

    def count_return(self, available_string):
        # Count the number of available players
        if "players" in available_string:
            available_string = available_string.replace("players", "").strip()
            if "to" in available_string:
                available_string = available_string.split("to")[1].strip()
            else:
                available_string = available_string.split("or")[1].strip()
        else:
            available_string = available_string.replace("player", "").strip()
        return int(available_string)

    def scrape_course_data(self):
        """
        Scrape course data for Sandringham GolfClub.
        """
        logging.info("Scraping course data for Sandringham Golfclub")
        # Define the number of days to scrape bookings for
        num_days = 5
        course_data = {}
        # Send a GET request to the URL
        response = requests.get(self.base_url)

        # Parse the HTML content using BeautifulSoup
        soup = BeautifulSoup(response.content, "html.parser")

        # Find all the course on the page
        slot_rows = soup.select("thead tr th[class = matrixHdrSched]")
        logging.info("Found %d slot rows", len(slot_rows))

        slot_tees = []
        for row in slot_rows:
            slot_tee_temp = row.text.strip()
            slot_tees.append(slot_tee_temp)
        logging.info("Found slot tees: %s", slot_tees)
        # Loop through each day
        for i in range(num_days):
            slot_data = []
            # Calculate the date for the current day
            date = (datetime.now() + timedelta(days=i)).strftime("%Y-%m-%d")
            date1 = (datetime.now() + timedelta(days=i)).strftime("%Y%m%d")
            # Construct the URL for the current day
            url = f"{self.base_url}?teedate={date1}"
            logging.info("Constructing URL for date: %s", url)
            response = requests.get(url)
            soup = BeautifulSoup(response.content, "html.parser")
            booking_slots = soup.select("tbody tr")
            logging.info("Found %d booking slots", len(booking_slots))
            for slot in booking_slots:

                tee_time = slot.find("td", class_="mtrxTeeTimes")
                slot_tee_time = tee_time.text.strip()
                logging.info("Found tee time: %s", slot_tee_time)
                availables_string = slot.find("td", class_="matrixPlayers").text
                available_count = self.count_return(availables_string)
                logging.info("Found available count: %d", available_count)
                slot_tees_rows = slot.find_all(
                    "td", class_=lambda x: "matrixsched" in x
                )

                for index, slot_tee_row in enumerate(slot_tees_rows):

                    if "mtrxInactive" in slot_tee_row.get("class"):
                        continue
                    slot_tee = slot_tees[index]
                    logging.info("Found slot tee: %s", slot_tee)
                    price_div = slot_tee_row.find("div", class_="mtrxPrice")
                    price = price_div.text.strip()
                    logging.info("Found price: %s", price)
                    slot_data.append([slot_tee_time, slot_tee, price, available_count])

            course_data[date] = slot_data

        self.export_to_excel(course_data)

    def export_to_excel(self, course_data):
        """
        Export course data to Excel files.
        """
        course_name = "Sandringham_Golf"
        logging.info("Exporting course data to Excel for course: %s", course_name)

        file_path = f"./sandringham-Golfclub-data/{course_name}.xlsx"
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


# Define the base URL for the Waverley Golf Club booking page
base_url = "https://sandringham.quick18.com/teetimes/searchmatrix"


# Create an instance of the GolfClubScraper class
scraper = GolfClubScraper(base_url)

# Call the scrape_course_data method to initiate the scraping process and export the data to Excel files
scraper.scrape_course_data()
