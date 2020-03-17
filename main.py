from selenium import webdriver
from selenium.webdriver.common.keys import Keys
import time
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

driver.find_element_by_xpath("//button[contains(@aria-label,'job alerts')]").click()


alert_list = driver.find_element_by_xpath("//h3[contains(text(), 'Saved job alerts')]//following::ul")

# Sometimes takes it a bit to load the list
time.sleep(2)

alerts = alert_list.find_elements_by_xpath(".//li")

alert_links = []
for alert in alerts:
  link = alert.find_element_by_xpath(".//a")
  alert_links.append(link.get_attribute("href"))

for job_search in alert_links:
  driver.get(job_search)

  # Sort by recent
  driver.find_element_by_xpath("//artdeco-dropdown-trigger[contains(@aria-label, 'Sort by')]").click()
  driver.find_element_by_xpath("//input[contains(@id, 'sort-by-date')]//parent::*").click()
  driver.find_element_by_xpath("//artdeco-dropdown-trigger[contains(@aria-label, 'Sort by')]").click()

  


