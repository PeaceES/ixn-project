from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
import time

LOGIN_URL = "http://localhost:8502/login"
VALID_EMAIL = "peaceselem@gmail.com"
VALID_PASSWORD = "validpassword"

# Helper function to perform login
def login(driver, email, password):
    driver.get(LOGIN_URL)
    time.sleep(1)
    driver.find_element(By.NAME, "email").send_keys(email)
    driver.find_element(By.NAME, "password").send_keys(password)
    driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
    time.sleep(1)

def logout_if_possible(driver):
    try:
        logout_link = driver.find_element(By.PARTIAL_LINK_TEXT, "Logout")
        logout_link.click()
        print("[TC3.0] Logged out previous session.")
        time.sleep(1)
    except Exception:
        pass  # No logout link found, continue

def test_schedule_event_and_invalid_date():
    print("\n[TC3.1] Schedule Event Test: Start")
    options = Options()
    options.add_argument('--headless=new')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.binary_location = "/usr/bin/chromium"
    service = Service("/usr/bin/chromedriver")
    driver = webdriver.Chrome(service=service, options=options)
    try:
        driver.get(LOGIN_URL)
        logout_if_possible(driver)
        login(driver, VALID_EMAIL, VALID_PASSWORD)
        print("[TC3.1] Logged in successfully.")
        # Wait for start agent button to be enabled
        for _ in range(20):
            start_btn = driver.find_element(By.ID, "start-agent")
            if start_btn.is_enabled():
                break
            time.sleep(0.5)
        else:
            print("[TC3.1] Start Agent button did not become enabled.")
            driver.quit()
            return
        start_btn.click()
        print("[TC3.1] Clicked Start Agent button. Waiting for agent to initialize...")
        time.sleep(60)
        # Wait for chat input to be enabled
        for _ in range(40):
            chat_input = driver.find_element(By.ID, "chat-input")
            if chat_input.is_enabled():
                break
            time.sleep(0.5)
        else:
            print("[TC3.1] Chat input did not become enabled.")
            driver.quit()
            return
        # Main flow: schedule a valid event
        chat_input.send_keys("Book a room for the robotics society on 17th September 2025 from 2pm to 4pm titled 'selenium's test event'")
        send_btn = driver.find_element(By.ID, "send-message")
        send_btn.click()
        print("[TC3.1] Sent valid event booking request. Waiting for confirmation...")
        found = False
        for _ in range(60):
            chat_output = driver.find_element(By.ID, "chat-output").text.lower()
            if any(word in chat_output for word in ["confirmed", "booked", "success", "reserved"]):
                found = True
                break
            time.sleep(1)
        if found:
            print("[TC3.1] System confirmed the booking. Test passed.")
        else:
            print("[TC3.1] System did not confirm the booking. Test failed.")
        # Alternative flow: invalid date
        chat_input.clear()
        chat_input.send_keys("Book a room for the robotics society on 87th Steptember 1900 from 2pm to 4pm titled 'invalid test event'")
        send_btn.click()
        print("[TC3.2] Sent invalid date booking request. Waiting for error/alternative...")
        found_error = False
        for _ in range(30):
            chat_output = driver.find_element(By.ID, "chat-output").text.lower()
            if any(word in chat_output for word in ["invalid", "error", "not possible", "alternative", "suggest"]):
                found_error = True
                break
            time.sleep(1)
        if found_error:
            print("[TC3.2] System displayed suggested alternatives.")
        else:
            print("[TC3.2] System did not suggest alternatives. Test failed.")
    except Exception as e:
        print("[TC3.1/TC3.2] Test failed:", e)
    finally:
        driver.quit()

if __name__ == "__main__":
    test_schedule_event_and_invalid_date()
