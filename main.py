from selenium import webdriver
from selenium.webdriver.common.keys import Keys
import time
from dotenv import load_dotenv
load_dotenv()
import os
import sys

driver = webdriver.Chrome(executable_path="./chromedriver")
driver.get("https://linkedin.com")
driver.implicitly_wait(2)

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

  search_results_div = driver.find_element_by_xpath("//div[contains(@class, 'jobs-search-results')]")

  # scroll to the bottom of the job posts - there's definitely a better way to do this
  time.sleep(1)
  search_results_div.send_keys(Keys.PAGE_DOWN)
  time.sleep(1)
  search_results_div.send_keys(Keys.PAGE_DOWN)
  time.sleep(1)
  search_results_div.send_keys(Keys.PAGE_DOWN)
  
  search_results = search_results_div.find_elements_by_xpath(".//li[contains(@class, 'list__item')]")

  for job_posting in search_results:
    print("Attempting to apply to a job...")
    job_posting.click()
    # It's possible that the job has already been applied to, in which case the 'jobs-apply-button' won't exist
    try:
      driver.find_element_by_xpath("//button[contains(@class, 'jobs-apply-button')]").click()
      # next page
      driver.find_element_by_xpath("//button[contains(@aria-label, 'Continue')]").click()
      # next page
      driver.find_element_by_xpath("//button[contains(@aria-label, 'Continue')]").click()

      # deal with postings that have additional questions
      try:
        driver.find_element_by_xpath("//h3[contains(text(), 'Additional Questions')]")
        questions = driver.find_elements_by_xpath("//h3[contains(text(), 'Additional Questions')]//parent::*//following::div[contains(@class, 'jobs-easy-apply-form-section__grouping')]")
        for question in questions:
          # If it's a radio button, select 'yes'
          try:
            question.find_element_by_xpath(".//input[contains(@value, 'Yes')]//following::label").click()
          # Otherwise, if it wants a number, put something in
          except:
            print("Error:", sys.exc_info()[0])            
            try:
              question.find_element_by_xpath(".//input[contains(@type, 'number')]").send_keys("3")
            except:
              print("Error:", sys.exc_info()[0])
              print("Cannot identify question type.")
        # next page
        driver.find_element_by_xpath("//button[contains(@aria-label, 'Continue')]").click()
      except:
        print("Error:", sys.exc_info()[0])
        print("No additional questions")

      # deal with postings that ask about work auth
      try:
        driver.find_element_by_xpath("//h3[contains(text(), 'Work authorization')]")
        driver.find_element_by_xpath(".//input[contains(@value, 'Yes')]//following::label").click()
      except:
        print("Error:", sys.exc_info()[0])
        print("No work auth question")

      # last page
      driver.find_element_by_xpath("//button[contains(@aria-label, 'Review')]").click()

      #uncheck the follow button
      driver.find_element_by_xpath("//label[contains(@for, 'follow')]").click()

      # submit form
      driver.find_element_by_xpath("//button[contains(@aria-label, 'Submit')]").click()
      time.sleep(0.5)
      driver.find_element_by_xpath("//button[contains(@aria-label, 'Dismiss')]").click()
      print("Applied!")
    except:
      print("Error:", sys.exc_info()[0])
      print("May have already applied to this job")