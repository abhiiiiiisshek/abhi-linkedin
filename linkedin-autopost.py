import openai
import time
import schedule
import os
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager

# Load environment variables from GitHub Secrets or .env file
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
LINKEDIN_EMAIL = os.getenv("LINKEDIN_EMAIL")
LINKEDIN_PASSWORD = os.getenv("LINKEDIN_PASSWORD")
BRAVE_PATH = os.getenv("BRAVE_PATH", "/usr/bin/brave-browser")  # Default path for Brave

# Set OpenAI API key
openai.api_key = OPENAI_API_KEY

# Configure Chrome Options for Brave
chrome_options = Options()
chrome_options.binary_location = BRAVE_PATH
chrome_options.add_argument("--headless")  # Run in the background
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--no-sandbox")

# Initialize WebDriver
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

def generate_trending_post():
    """Generates a trending LinkedIn post using OpenAI"""
    prompt = (
        "Generate a short and engaging LinkedIn post related to coding, tech industry, study motivation, "
        "or productivity hacks. The post should be catchy, professional, and under 280 characters."
    )

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=100,
        temperature=0.8
    )

    post_content = response["choices"][0]["message"]["content"].strip()
    print(f"📝 Generated Post: {post_content}")
    return post_content

def login_to_linkedin():
    """Logs into LinkedIn"""
    driver.get("https://www.linkedin.com/login")
    time.sleep(3)

    driver.find_element(By.ID, "username").send_keys(LINKEDIN_EMAIL)
    driver.find_element(By.ID, "password").send_keys(LINKEDIN_PASSWORD)
    driver.find_element(By.XPATH, "//button[contains(text(), 'Sign in')]").click()
    time.sleep(5)

def post_on_linkedin():
    """Posts generated content on LinkedIn"""
    post_content = generate_trending_post()

    driver.get("https://www.linkedin.com/feed/")
    time.sleep(5)

    try:
        post_box = driver.find_element(By.CLASS_NAME, "share-box__open")
        post_box.click()
        time.sleep(2)

        input_area = driver.find_element(By.CLASS_NAME, "mentions-texteditor__contenteditable")
        input_area.send_keys(post_content)
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

# Schedule the bot to post automatically every 6 hours
schedule.every(6).hours.do(job)

print("🔄 Running LinkedIn Auto-Post Bot...")
while True:
    schedule.run_pending()
    time.sleep(60)  # Check every minute
