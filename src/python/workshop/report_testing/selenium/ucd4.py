from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
import time

LOGIN_URL = "http://localhost:8502/login"
VALID_EMAIL = "peaceselem@gmail.com"
VALID_PASSWORD = "validpassword"

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
        print("[TC4.0] Logged out previous session.")
        time.sleep(1)
    except Exception:
        pass

def test_modify_event_permissions():
    print("\n[TC4.1] Modify Event Test: Start")
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
        print("[TC4.1] Logged in successfully.")
        # Wait for start agent button to be enabled
        for _ in range(20):
            start_btn = driver.find_element(By.ID, "start-agent")
            if start_btn.is_enabled():
                break
            time.sleep(0.5)
        else:
            print("[TC4.1] Start Agent button did not become enabled.")
            driver.quit()
            return
        start_btn.click()
        print("[TC4.1] Clicked Start Agent button. Waiting for agent to initialize...")
        time.sleep(60)
        # Wait for chat input to be enabled
        for _ in range(40):
            chat_input = driver.find_element(By.ID, "chat-input")
            if chat_input.is_enabled():
                break
            time.sleep(0.5)
        else:
            print("[TC4.1] Chat input did not become enabled.")
            driver.quit()
            return
        # Main flow: modify Graham's test event
        chat_input.send_keys("Change the date of Graham's test event to 21st January 2026")
        send_btn = driver.find_element(By.ID, "send-message")
        send_btn.click()
        print("[TC4.1] Sent event modification request. Waiting for confirmation...")
        found = False
        for _ in range(60):
            chat_output = driver.find_element(By.ID, "chat-output").text.lower()
            if any(word in chat_output for word in ["updated", "modified", "changed", "success"]):
                found = True
                break
            time.sleep(1)
        if found:
            print("[TC4.1] System confirmed the event modification. Test passed.")
        else:
            print("[TC4.1] System did not confirm the event modification. Test failed.")
        # Alternative flow: try to modify event without permission
        chat_input.clear()
        chat_input.send_keys("Change the date of Maintenance: HVAC inspection to 21st January 2026")
        send_btn.click()
        print("[TC4.2] Sent unauthorized event modification request. Waiting for permission error...")
        found_error = False
        for _ in range(30):
            chat_output = driver.find_element(By.ID, "chat-output").text.lower()
            if any(word in chat_output for word in ["permission", "not allowed", "not authorized", "cannot", "denied"]):
                found_error = True
                break
            time.sleep(1)
        if found_error:
            print("[TC4.2] System denied modification due to permissions. Test passed.")
        else:
            print("[TC4.2] System did not deny modification due to permissions. Test failed.")
    except Exception as e:
        print("[TC4.1/TC4.2] Test failed:", e)
    finally:
        driver.quit()

if __name__ == "__main__":
    test_modify_event_permissions()
