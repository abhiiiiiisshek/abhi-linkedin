import os
import time
import logging
from typing import Optional
from dataclasses import dataclass
import openai
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
from webdriver_manager.chrome import ChromeDriverManager
from tenacity import retry, stop_after_attempt, wait_exponential

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class LinkedInConfig:
    """Configuration class for LinkedIn credentials and settings"""
    email: str
    password: str
    browser_path: Optional[str] = None
    post_interval: int = 6  # hours
    timeout: int = 10  # seconds

class LinkedInPoster:
    def __init__(self, config: LinkedInConfig):
        """Initialize the LinkedIn poster with configuration"""
        self.config = config
        self.driver = None
        self.setup_openai()
        
    def setup_openai(self):
        """Set up OpenAI API key"""
        openai_api_key = os.getenv("OPENAI_API_KEY")
        if not openai_api_key:
            raise ValueError("OpenAI API key not found in environment variables")
        openai.api_key = openai_api_key

    def setup_driver(self):
        """Set up and configure the web driver"""
        chrome_options = Options()
        chrome_options.add_argument("--headless=new")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        if self.config.browser_path:
            chrome_options.binary_location = self.config.browser_path

        self.driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=chrome_options
        )
        self.driver.implicitly_wait(self.config.timeout)

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def generate_trending_post(self) -> str:
        """Generate a trending LinkedIn post using OpenAI with retry logic"""
        try:
            prompt = """Generate an engaging LinkedIn post about:
            - Latest tech trends
            - Programming best practices
            - Career development
            - Professional growth
            
            Make it conversational, include relevant hashtags, and keep it under 280 characters."""

            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=150,
                temperature=0.7
            )
            post_content = response.choices[0].message.content.strip()
            logger.info(f"Generated post: {post_content[:50]}...")
            return post_content
        except Exception as e:
            logger.error(f"Error generating post: {str(e)}")
            raise

    def wait_and_find_element(self, by: By, value: str):
        """Wait for and find an element with explicit wait"""
        return WebDriverWait(self.driver, self.config.timeout).until(
            EC.presence_of_element_located((by, value))
        )

    def login(self):
        """Log into LinkedIn with error handling"""
        try:
            self.driver.get("https://www.linkedin.com/login")
            username = self.wait_and_find_element(By.ID, "username")
            password = self.wait_and_find_element(By.ID, "password")
            
            username.send_keys(self.config.email)
            password.send_keys(self.config.password)
            
            submit_button = self.wait_and_find_element(
                By.XPATH, "//button[contains(text(), 'Sign in')]"
            )
            submit_button.click()
            
            # Wait for feed to load to confirm successful login
            self.wait_and_find_element(By.CLASS_NAME, "share-box__open")
            logger.info("Successfully logged into LinkedIn")
            
        except TimeoutException as e:
            logger.error(f"Timeout during login: {str(e)}")
            raise
        except WebDriverException as e:
            logger.error(f"WebDriver error during login: {str(e)}")
            raise

    def post_content(self, content: str):
        """Post content to LinkedIn with error handling"""
        try:
            self.driver.get("https://www.linkedin.com/feed/")
            post_box = self.wait_and_find_element(By.CLASS_NAME, "share-box__open")
            post_box.click()

            input_area = self.wait_and_find_element(
                By.CLASS_NAME, "mentions-texteditor__contenteditable"
            )
            input_area.send_keys(content)

            post_button = self.wait_and_find_element(
                By.XPATH, "//button[contains(text(), 'Post')]"
            )
            post_button.click()

            # Wait for post confirmation
            time.sleep(3)
            logger.info("Successfully posted to LinkedIn")
            
        except Exception as e:
            logger.error(f"Error posting content: {str(e)}")
            raise

    def run_job(self):
        """Execute the complete posting job"""
        try:
            self.setup_driver()
            self.login()
            post_content = self.generate_trending_post()
            self.post_content(post_content)
        except Exception as e:
            logger.error(f"Job failed: {str(e)}")
            raise
        finally:
            if self.driver:
                self.driver.quit()

def main():
    """Main function to run the LinkedIn poster"""
    config = LinkedInConfig(
        email=os.getenv("LINKEDIN_EMAIL"),
        password=os.getenv("LINKEDIN_PASSWORD"),
        browser_path=os.getenv("BRAVE_PATH"),
    )

    poster = LinkedInPoster(config)
    
    if os.getenv("GITHUB_ACTIONS"):
        # Running in GitHub Actions - execute once
        poster.run_job()
    else:
        # Running locally - use scheduling
        import schedule
        schedule.every(config.post_interval).hours.do(poster.run_job)
        logger.info(f"Scheduled to run every {config.post_interval} hours")
        
        while True:
            schedule.run_pending()
            time.sleep(60)

if __name__ == "__main__":
    main()
