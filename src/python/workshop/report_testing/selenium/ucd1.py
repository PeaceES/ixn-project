from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
import time


LOGIN_URL = "http://localhost:8502/login" 
VALID_EMAIL = "peaceselem@gmail.com"
VALID_PASSWORD = "validpassword"
INVALID_EMAIL = "invaliduser@example.com"
INVALID_PASSWORD = "invalidpassword"

# Helper function to perform login
def login(driver, email, password):
    driver.get(LOGIN_URL)
    time.sleep(1)  # Wait for page to load
    driver.find_element(By.NAME, "email").send_keys(email)
    driver.find_element(By.NAME, "password").send_keys(password)
    driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
    time.sleep(1)  # Wait for response

# Test valid login
def test_valid_login():
    print("\n[TC1.1] Valid Login Test: Start")
    options = Options()
    options.add_argument('--headless=new')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.binary_location = "/usr/bin/chromium"
    service = Service("/usr/bin/chromedriver")
    driver = webdriver.Chrome(service=service, options=options)
    try:
        login(driver, VALID_EMAIL, VALID_PASSWORD)
        print("[TC1.1] System validated user is part of the university system.")
        driver.find_element(By.PARTIAL_LINK_TEXT, "Logout")
        print("[TC1.1] Landing page shown after login. Logout button present.")
        print("[TC1.1] Valid login test passed.")
    except Exception as e:
        print("[TC1.1] Valid login test failed:", e)
    finally:
        driver.quit()

# Test invalid login
def test_invalid_login():
    print("\n[TC1.2] Invalid Login Test: Start")
    options = Options()
    options.add_argument('--headless=new')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.binary_location = "/usr/bin/chromium"
    service = Service("/usr/bin/chromedriver")
    driver = webdriver.Chrome(service=service, options=options)
    try:
        login(driver, INVALID_EMAIL, INVALID_PASSWORD)
        error = driver.find_element(By.CLASS_NAME, "error")
        assert error.is_displayed()
        print("[TC1.2] System rejected invalid user. Error message displayed.")
        print("[TC1.2] Invalid login test passed.")
    except Exception as e:
        print("[TC1.2] Invalid login test failed:", e)
    finally:
        driver.quit()

if __name__ == "__main__":
    test_valid_login()
    test_invalid_login()