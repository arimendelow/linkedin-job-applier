from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as exp_conds
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import time
from dotenv import load_dotenv
load_dotenv()
import os
import sys
import datetime

driver = webdriver.Chrome(executable_path="./chromedriver")
driver.implicitly_wait(1)
wait = WebDriverWait(driver, 20)

# How far back do you want to go? If a job was posted on or before this date, it will not be applied to.
filter_date_str = '2020-3-18'
filter_date = datetime.datetime.strptime(filter_date_str, '%Y-%m-%d')

jobs_skipped = 0
max_jobs_skipped_per_search = 25 # number of jobs on one page

total_jobs_applied = 0

# Use with WebDriverWait to combine expected_conditions in an OR.
# Will return the element that it finds first
class Any_EC:
  def __init__(self, *args):
    self.ecs = args
  def __call__(self, driver):
    for fn in self.ecs:
      try:
        # fn(driver) will return the WebElement
        if fn(driver): return fn(driver)
      except:
        pass

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
    time.sleep(1) # wait for message
    driver.find_element_by_xpath("//button[contains(@aria-label,'job alerts')]").click()

  alert_list = driver.find_element_by_xpath("//h3[contains(text(), 'Saved job alerts')]//following::ul")

  # Sometimes takes it a bit to load the list
  time.sleep(2)
  alerts = alert_list.find_elements_by_xpath(".//li")

  alert_links = []
  for alert in alerts:
    link = alert.find_element_by_xpath(".//a")
    # First item in tuple is the link, the second is the alert title
    alert_links.append((link.get_attribute("href"), alert.text))
  
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
    questions = driver.find_elements_by_xpath("//h3[contains(text(), 'Additional Questions')]//parent::*//following::div[contains(@class, 'jobs-easy-apply-form-section__grouping')]")
    for question in questions:
      # If it's a radio button, select 'yes'
      try:
        question.find_element_by_xpath(".//input[contains(@value, 'Yes')]//following::label").click()
      # Otherwise, if it wants a number, put something in
      except:
        try:
          question.find_element_by_xpath(".//input[contains(@type, 'number')]").clear()
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
  #uncheck the follow button, if it exists
  try:
    driver.find_element_by_xpath("//label[contains(@for, 'follow')]").click()
  except:
    print("No follow button")

  # submit form - two different types of submit button
  try:
    # more common - this one also has a 'application submitted' dialog
    driver.find_element_by_xpath("//button[contains(@aria-label, 'Submit')]").click()
    # Wait until the 'applied to' page is loading before dismissing the application
    wait.until(exp_conds.visibility_of_element_located((By.XPATH, "//h2[contains(@id, 'post-apply')]")))
    driver.find_element_by_xpath("//button[contains(@aria-label, 'Dismiss')]").click()
  except:
    # less common
    driver.find_element_by_xpath("//button[contains(@data-control-name, 'submit')]").click()

  print("Applied!")
  global total_jobs_applied
  total_jobs_applied += 1

# This returns True if it's the last page, and False if it's not
def to_next_app_page():
  try:
    driver.find_element_by_xpath("//button[contains(@aria-label, 'Continue')]").click()
    return False
  except:
    driver.find_element_by_xpath("//button[contains(@aria-label, 'Review')]").click()
    return True

# applies to one page of jobs
def apply_to_jobs(search_results):
  for job_posting in search_results:
    job_header = job_posting.find_element_by_xpath(".//h3")
    print(f"Attempting to apply to {job_header.text}...")
    post_date_str = job_posting.find_element_by_xpath(".//time").get_attribute("datetime")
    post_date = datetime.datetime.strptime(post_date_str, '%Y-%m-%d')
    
    # If the date this job was posted at is less recent than the filter date...
    # less_recent < more_recent
    if post_date < filter_date:
      print(f"Finished applying to jobs in this search before {filter_date.date()}")
      return False # Stop applying to jobs in this search

    # else...
    job_header.click()
    # there are several possible reasons for not being able to click the apply button
    try:
      elem = WebDriverWait(driver, 20).until(Any_EC(
        # enabled Apply button - sometimes needs to load
        exp_conds.visibility_of_element_located((By.XPATH, "//button[contains(@aria-label, 'Apply to')][not(@disabled)]")),
        # apply-to dialog
        exp_conds.visibility_of_element_located((By.XPATH, "//*[contains(@class, 'applied-date')]//following::span"))
      ))
      if 'Easy Apply' in elem.text:
        try:
          elem.click()
        except:
          try:
            driver.find_element_by_xpath("//header[contains(@class,'msg-overlay-bubble-header')]").click()
            driver.find_element_by_xpath("//button[contains(@class, 'jobs-apply-button')]").click()
          except:
            print("Error:", sys.exc_info()[0])
            # go to the next job_posting
            continue
      elif 'Applied' in elem.text:
        # go to the next job_posting
        print("Already applied to this job")
        global jobs_skipped
        jobs_skipped += 1
        if jobs_skipped > max_jobs_skipped_per_search:
          print(f"Skipped {jobs_skipped} in this Search - onto the next one!")
          return False # Stop applying to jobs in this search
        continue
      else:
        raise Exception("I don't think we've yet applied to this job")
    except:
      print("Error:", sys.exc_info()[0])
      # go to the next job_posting
      continue

    # In application
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
        on_last_page = to_next_app_page()
      elif header_text == "Resume" or header_text == "Currículum":
        on_last_page = to_next_app_page()
      elif header_text == "Work authorization":
        do_work_auth_questions()
        on_last_page = to_next_app_page()
      elif header_text == "Additional Questions":
        do_additional_questions()
        on_last_page = to_next_app_page()
      else:
        raise Exception(f"I don't know what to do with the header_text {header_text}")

    submit_application()
  return True # Keep applying to jobs in this search

# Apply to jobs on every page of the results
def apply_to_jobs_pagination():
  # For date filtering
  continue_applying_to_search_results = True

  on_final_jobs_page = False
  while(not on_final_jobs_page):
    search_results = get_job_postings_on_page()

    # This function will let us know if we should keep running it
    continue_applying_to_search_results = apply_to_jobs(search_results)

    if not continue_applying_to_search_results:
      return

    # Go to next page
    pages = driver.find_element_by_xpath("//ul[contains(@class, 'pagination')]")
    current_page = pages.find_element_by_xpath(".//button[contains(@aria-current, 'true')]").text
    print()
    print(f"Done with page {current_page}!")
    try:
      next_page_btn = pages.find_element_by_xpath(f".//button[contains(@aria-label, '{int(current_page) + 1}')]")
      # Need to do this for the print statement - if we try to access the text after navigating to the next page, we'll get a state element exception
      next_page_btn_text = next_page_btn.text
      next_page_btn.click()
      print("----------------------")
      print(f"Going to page {next_page_btn_text}!")
      print()
    except:
      # On final jobs page
      print("No more pages.")
      print()
      on_final_jobs_page = True

def main():
  alert_links = log_into_linkedin_and_get_job_alert_links()

  for job_search in alert_links:
    driver.get(job_search[0])
    print("Applying to the following jobs:")
    print(job_search[1])
    print()
    sort_by_recent()
    global jobs_skipped
    jobs_skipped = 0 # reset this counter
    apply_to_jobs_pagination()
  
  print(f"Done! Applied to {total_jobs_applied} jobs.")
  driver.close()


if __name__ == "__main__":
  main()