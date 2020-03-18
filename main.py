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

  return search_results_div.find_elements_by_xpath(".//li[contains(@class, 'list__item')]//h3")

def do_additional_questions():
  try:
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
  # Yes to 'Are you legally authorized to work in the United States?'
  try:
    driver.find_element_by_xpath("//span[text()='Are you legally authorized to work in the United States?']//following::input[contains(@value, 'Yes')]//following::label").click()
  except:
    print("No legally authorized question")
  try:
    driver.find_element_by_xpath("//span[text()='Will you now, or in the future, require sponsorship for employment visa status (e.g. H-1B visa status)?']//following::input[contains(@value, 'No')]//following::label").click()
  except:
    print("No visa question")
def submit_application():
  #uncheck the follow button
  driver.find_element_by_xpath("//label[contains(@for, 'follow')]").click()

  # submit form
  driver.find_element_by_xpath("//button[contains(@aria-label, 'Submit')]").click()
  time.sleep(1)
  driver.find_element_by_xpath("//button[contains(@aria-label, 'Dismiss')]").click()
  print("Applied!")

# This returns True if it's the last page, and False if it's not
def to_next_page():
  try:
    driver.find_element_by_xpath("//button[contains(@aria-label, 'Continue')]").click()
    return False
  except:
    driver.find_element_by_xpath("//button[contains(@aria-label, 'Review')]").click()
    return True

def main():
  alert_links = log_into_linkedin_and_get_job_alert_links()

  for job_search in alert_links:
    driver.get(job_search)
 
    sort_by_recent()
    
    search_results = get_job_postings_on_page()

    for job_posting in search_results:
      print("Attempting to apply to a job...")
      job_posting.click()
      # there are several possible reasons for not being able to click the apply button
      try:
        driver.find_element_by_xpath("//button[contains(@class, 'jobs-apply-button')]").click()
      except:
        try:
          # It's possible that the job has already been applied to
          applied = 'Applied' in driver.find_element_by_xpath("//*[contains(@class, 'applied-date')]//following::span").text
          if not applied:
            raise Exception("I don't think we've yet applied to this job")
          else:
            # go to the next job_posting
            print("Already applied to this job")
            continue
        except:
          try:
            driver.find_element_by_xpath("//header[contains(@class,'msg-overlay-bubble-header')]").click()
            driver.find_element_by_xpath("//button[contains(@class, 'jobs-apply-button')]").click()
          except:
            print("Error:", sys.exc_info()[0])
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
        # determine the type of page that I'm on
        header_text = driver.find_element_by_xpath("//div[contains(@class, 'jobs-easy-apply-modal')]//h3").text

        if header_text == "Contact info":
          on_last_page = to_next_page()
        elif header_text == "Resume":
          on_last_page = to_next_page()
        elif header_text == "Work authorization":
          do_work_auth_questions()
          on_last_page = to_next_page()
        elif header_text == "Additional Questions":
          do_additional_questions()
          on_last_page = to_next_page()
        else:
          raise Exception(f"I don't know what to do with the header_text {header_text}")

      submit_application()

if __name__ == "__main__":
  main()