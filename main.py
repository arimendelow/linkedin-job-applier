from selenium import webdriver
from selenium.webdriver.common.keys import Keys
import time
from dotenv import load_dotenv
load_dotenv()
import os
import sys

driver = webdriver.Chrome(executable_path="./chromedriver")
driver.implicitly_wait(2)

def log_into_linkedin_and_get_job_alert_links():
  driver.get("https://linkedin.com")
  user = driver.find_element_by_xpath("//input[contains(@aria-label,'email')]")
  user.send_keys(os.getenv("USERNAME"))
  password = driver.find_element_by_xpath("//input[contains(@aria-label,'password')]")
  password.send_keys(os.getenv("PASSWORD"))
  password.send_keys(Keys.RETURN)

  # # Sometimes, linkedin asks for verification of contact information
  # try:
  #   driver.find_element_by_xpath("//span[contains(@id,'prompt')]//following::button").click()

  driver.get("https://www.linkedin.com/jobs/")

  # If the screen is short and the chat menu is open, it'll block the 'job alerts' button
  try:
    driver.find_element_by_xpath("//button[contains(@aria-label,'job alerts')]").click()
  except:
    driver.find_element_by_xpath("//header[contains(@class,'msg-overlay-bubble-header')]").click()
    driver.find_element_by_xpath("//button[contains(@aria-label,'job alerts')]").click()

  alert_list = driver.find_element_by_xpath("//h3[contains(text(), 'Saved job alerts')]//following::ul")

  # Sometimes takes it a bit to load the list
  time.sleep(2)

  alerts = alert_list.find_elements_by_xpath(".//li")

  alert_links = []
  for alert in alerts:
    link = alert.find_element_by_xpath(".//a")
    alert_links.append(link.get_attribute("href"))
  
  return alert_links

def sort_by_recent():
  driver.find_element_by_xpath("//artdeco-dropdown-trigger[contains(@aria-label, 'Sort by')]").click()
  driver.find_element_by_xpath("//input[contains(@id, 'sort-by-date')]//parent::*").click()
  driver.find_element_by_xpath("//artdeco-dropdown-trigger[contains(@aria-label, 'Sort by')]").click()

def get_job_postings_on_page():
  search_results_div = driver.find_element_by_xpath("//div[contains(@class, 'jobs-search-results')]")

  # scroll to the bottom of the job posts - there's definitely a better way to do this
  search_results_div.send_keys(Keys.PAGE_DOWN)
  time.sleep(1)
  search_results_div.send_keys(Keys.PAGE_DOWN)
  time.sleep(1)
  search_results_div.send_keys(Keys.PAGE_DOWN)
  time.sleep(1)
  search_results_div.send_keys(Keys.PAGE_DOWN)
  time.sleep(1)
  search_results_div.send_keys(Keys.PAGE_DOWN)
  time.sleep(1)
  search_results_div.send_keys(Keys.PAGE_DOWN)
  time.sleep(1)

  return search_results_div.find_elements_by_xpath(".//li[contains(@class, 'list__item')]")

def do_additional_questions():
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

def do_work_auth_questions():
  try:
    driver.find_element_by_xpath("//h3[contains(text(), 'Work authorization')]")
    driver.find_element_by_xpath(".//input[contains(@value, 'Yes')]//following::label").click()
  except:
    print("Error:", sys.exc_info()[0])
    print("No work auth question")

def submit_application():
  #uncheck the follow button
  driver.find_element_by_xpath("//label[contains(@for, 'follow')]").click()

  # submit form
  driver.find_element_by_xpath("//button[contains(@aria-label, 'Submit')]").click()
  time.sleep(0.5)
  driver.find_element_by_xpath("//button[contains(@aria-label, 'Dismiss')]").click()
  print("Applied!")

def main():
  alert_links = log_into_linkedin_and_get_job_alert_links()

  for job_search in alert_links:
    driver.get(job_search)
 
    sort_by_recent()
    
    search_results = get_job_postings_on_page()

    for job_posting in search_results:
      print("Attempting to apply to a job...")
      job_posting.click()
      # If the screen is short and the chat menu is open, it'll block the 'jobs-apply-button' button
      try:
        driver.find_element_by_xpath("//button[contains(@class, 'jobs-apply-button')]").click()
      except:
        try:
          driver.find_element_by_xpath("//header[contains(@class,'msg-overlay-bubble-header')]").click()
          driver.find_element_by_xpath("//button[contains(@class, 'jobs-apply-button')]").click()
        # It's also possible that the job has already been applied to, in which case the 'jobs-apply-button' won't exist
        except:
          print("Error:", sys.exc_info()[0])
          print("May have already applied to this job")
          # go to the next job_posting
          continue

      on_last_page = False
      try:
        # If there's a progress bar, then there will be multiple steps to this application
        driver.find_element_by_xpath("//div[contains(@class, 'jobs-easy-apply-content__progress-bar')]")
      except:
        # Else, this is a onepager that probably just wants contact info, which should already be proviced. so:
        on_last_page = True

      # while there is no submit button...
      while(not on_last_page):
        # does this page have additional questions? if so...

        do_additional_questions()
        # does this page ask about work auth? if so...
        # deal with postings that ask about work auth
        do_work_auth_questions()

      # If there is another page after this, it'll be a button with the label containing 'Continue'.
      # Else, it'll have the label containing 'Review'
      # to next page
      driver.find_element_by_xpath("//button[contains(@aria-label, 'Continue')]").click()
      # to last page
      driver.find_element_by_xpath("//button[contains(@aria-label, 'Review')]").click()

      submit_application()

if __name__ == "__main__":
  main()