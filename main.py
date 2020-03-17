from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from dotenv import load_dotenv
load_dotenv()
import os

driver = webdriver.Chrome(executable_path="./chromedriver")
driver.get("https://linkedin.com")
driver.implicitly_wait(10)

user = driver.find_element_by_xpath("//input[contains(@aria-label,'email')]")
user.send_keys(os.getenv("USERNAME"))
password = driver.find_element_by_xpath("//input[contains(@aria-label,'password')]")
password.send_keys(os.getenv("PASSWORD"))
password.send_keys(Keys.RETURN)

# # Sometimes, linkedin asks for verification of contact information
# try:
#   driver.find_element_by_xpath("//span[contains(@id,'prompt')]//following::button").click()

driver.get("https://www.linkedin.com/jobs/")
