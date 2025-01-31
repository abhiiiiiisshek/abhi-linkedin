import os
import time
import logging
import traceback
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

# Enhanced logging setup
logging.basicConfig(
    level=logging.DEBUG,  # Changed to DEBUG level
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('linkedin_debug.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class LinkedInConfig:
    email: str
    password: str
    browser_path: Optional[str] = None
    post_interval: int = 6
    timeout: int = 20  # Increased timeout

class LinkedInPoster:
    def __init__(self, config: LinkedInConfig):
        self.config = config
        self.driver = None
        self.setup_openai()
        
    def take_screenshot(self, name: str):
        """Take screenshot for debugging"""
        try:
            if self.driver:
                self.driver.save_screenshot(f"debug_{name}_{int(time.time())}.png")
                logger.info(f"Screenshot saved: {name}")
        except Exception as e:
            logger.error(f"Failed to take screenshot: {str(e)}")

    def setup_driver(self):
        """Enhanced driver setup with more options"""
        chrome_options = Options()
        chrome_options.add_argument("--headless=new")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option("useAutomationExtension", False)
        
        # More realistic user agent
        chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

        if self.config.browser_path:
            chrome_options.binary_location = self.config.browser_path

        self.driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=chrome_options
        )
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        self.driver.implicitly_wait(self.config.timeout)
        logger.info("WebDriver setup completed")

    def login(self):
        """Enhanced login with more checks and logging"""
        try:
            logger.info("Attempting to login to LinkedIn...")
            self.driver.get("https://www.linkedin.com/login")
            time.sleep(5)  # Allow page to fully load
            
            self.take_screenshot("before_login")
            
            # Check if already logged in
            if "feed" in self.driver.current_url:
                logger.info("Already logged in")
                return
            
            username = self.wait_and_find_element(By.ID, "username")
            logger.debug("Found username field")
            username.clear()
            username.send_keys(self.config.email)
            
            password = self.wait_and_find_element(By.ID, "password")
            logger.debug("Found password field")
            password.clear()
            password.send_keys(self.config.password)
            
            submit_button = self.wait_and_find_element(
                By.XPATH, "//button[contains(text(), 'Sign in')]"
            )
            logger.debug("Found submit button")
            submit_button.click()
            
            time.sleep(5)  # Wait for login to complete
            self.take_screenshot("after_login")
            
            # Verify login success
            if "feed" not in self.driver.current_url:
                logger.error(f"Login might have failed. Current URL: {self.driver.current_url}")
                raise Exception("Login verification failed")
                
            logger.info("Successfully logged into LinkedIn")
            
        except Exception as e:
            logger.error(f"Login failed: {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            self.take_screenshot("login_error")
            raise

    def post_content(self, content: str):
        """Enhanced posting with more checks and logging"""
        try:
            logger.info("Attempting to post content...")
            self.driver.get("https://www.linkedin.com/feed/")
            time.sleep(5)
            
            self.take_screenshot("before_post")
            
            # Try different selectors for post box
            post_box = None
            selectors = [
                (By.CLASS_NAME, "share-box__open"),
                (By.XPATH, "//button[contains(@class, 'artdeco-button') and contains(@class, 'share-box-feed-entry__trigger')]"),
                (By.XPATH, "//button[contains(text(), 'Start a post')]")
            ]
            
            for by, selector in selectors:
                try:
                    post_box = self.wait_and_find_element(by, selector)
                    if post_box:
                        logger.info(f"Found post box using selector: {selector}")
                        break
                except:
                    continue
            
            if not post_box:
                raise Exception("Could not find post box")
                
            post_box.click()
            time.sleep(3)
            
            # Try different selectors for input area
            input_selectors = [
                (By.CLASS_NAME, "mentions-texteditor__contenteditable"),
                (By.CLASS_NAME, "editor-content"),
                (By.XPATH, "//div[@role='textbox']")
            ]
            
            input_area = None
            for by, selector in input_selectors:
                try:
                    input_area = self.wait_and_find_element(by, selector)
                    if input_area:
                        logger.info(f"Found input area using selector: {selector}")
                        break
                except:
                    continue
                    
            if not input_area:
                raise Exception("Could not find input area")
                
            input_area.send_keys(content)
            time.sleep(2)
            
            self.take_screenshot("before_submit")
            
            # Try different selectors for post button
            post_button = None
            button_selectors = [
                (By.XPATH, "//button[contains(text(), 'Post')]"),
                (By.XPATH, "//button[contains(@class, 'share-actions__primary-action')]")
            ]
            
            for by, selector in button_selectors:
                try:
                    post_button = self.wait_and_find_element(by, selector)
                    if post_button:
                        logger.info(f"Found post button using selector: {selector}")
                        break
                except:
                    continue
                    
            if not post_button:
                raise Exception("Could not find post button")
                
            post_button.click()
            time.sleep(5)
            
            self.take_screenshot("after_post")
            logger.info("Successfully posted to LinkedIn")
            
        except Exception as e:
            logger.error(f"Posting failed: {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            self.take_screenshot("post_error")
            raise

    def run_job(self):
        """Execute the complete posting job with enhanced error handling"""
        try:
            self.setup_driver()
            self.login()
            post_content = self.generate_trending_post()
            self.post_content(post_content)
            logger.info("Job completed successfully")
        except Exception as e:
            logger.error(f"Job failed: {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise
        finally:
            if self.driver:
                self.driver.quit()

# Rest of the code remains the same...
