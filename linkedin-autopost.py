from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import time
import schedule
from webdriver_manager.chrome import ChromeDriverManager

# LinkedIn Credentials
LINKEDIN_EMAIL = "your_email@example.com"
LINKEDIN_PASSWORD = "your_password"

# Configure Chrome options
chrome_options = Options()
chrome_options.add_argument("--headless")  # Run in background
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--no-sandbox")

# Initialize WebDriver
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

def login_to_linkedin():
    """Logs into LinkedIn"""
    driver.get("https://www.linkedin.com/login")
    time.sleep(3)

    driver.find_element(By.ID, "username").send_keys(LINKEDIN_EMAIL)
    driver.find_element(By.ID, "password").send_keys(LINKEDIN_PASSWORD)
    driver.find_element(By.XPATH, "//button[contains(text(), 'Sign in')]").click()
    time.sleep(5)

def post_on_linkedin():
    """Posts a message on LinkedIn"""
    driver.get("https://www.linkedin.com/feed/")
    time.sleep(5)

    try:
        post_box = driver.find_element(By.CLASS_NAME, "share-box__open")
        post_box.click()
        time.sleep(2)

        input_area = driver.find_element(By.CLASS_NAME, "mentions-texteditor__contenteditable")
        input_area.send_keys("🚀 This is an automated post using Selenium! #Automation #LinkedInBot")
        time.sleep(2)

        post_button = driver.find_element(By.XPATH, "//button[contains(text(), 'Post')]")
        post_button.click()
        time.sleep(5)

        print("✅ Successfully posted on LinkedIn!")
    except Exception as e:
        print(f"❌ Error posting: {str(e)}")

def job():
    login_to_linkedin()
    post_on_linkedin()

# Schedule the bot to run every 6 hours
schedule.every(6).hours.do(job)

print("🔄 Running LinkedIn Bot...")
while True:
    schedule.run_pending()
    time.sleep(60)  # Check every minute

