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

def test_start_agent_and_show_events():
    print("\n[TC2.1] Start Agent and Show Events Test: Start")
    options = Options()
    options.add_argument('--headless=new')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.binary_location = "/usr/bin/chromium"
    service = Service("/usr/bin/chromedriver")
    driver = webdriver.Chrome(service=service, options=options)
    try:
        login(driver, VALID_EMAIL, VALID_PASSWORD)
        print("[TC2.1] Logged in successfully.")
        # Wait for start agent button to be enabled
        for _ in range(20):
            start_btn = driver.find_element(By.ID, "start-agent")
            if start_btn.is_enabled():
                break
            time.sleep(0.5)
        else:
            print("[TC2.1] Start Agent button did not become enabled.")
            driver.quit()
            return
        start_btn.click()
        print("[TC2.1] Clicked Start Agent button. Waiting for agent to initialize...")
        time.sleep(60)
        # Wait for chat input to be enabled
        for _ in range(20):
            chat_input = driver.find_element(By.ID, "chat-input")
            if chat_input.is_enabled():
                break
            time.sleep(0.5)
        else:
            print("[TC2.1] Chat input did not become enabled.")
            driver.quit()
            return
        # Main flow: ask for scheduled events
        chat_input.send_keys("Show my scheduled events")
        send_btn = driver.find_element(By.ID, "send-message")
        send_btn.click()
        print("[TC2.2] Sent 'Show my scheduled events' to agent. Waiting for response...")
        found = False
        for _ in range(60):
            chat_output = driver.find_element(By.ID, "chat-output").text.lower()
            if any(word in chat_output for word in ["event", "schedule", "meeting"]):
                found = True
                break
            time.sleep(1)
        if found:
            print("[TC2.2] Agent displayed scheduled events. Main flow test passed.")
        else:
            print("[TC2.2] Agent did not display scheduled events. Main flow test failed.")
        # Alternative flow: invalid date and room
        chat_input.clear()
        chat_input.send_keys("Show events for 2025-13-99 in RoomXYZ")
        send_btn.click()
        print("[TC2.3] Sent invalid date and room to agent. Waiting for error response...")
        found_error = False
        for _ in range(30):
            chat_output = driver.find_element(By.ID, "chat-output").text.lower()
            if any(word in chat_output for word in ["invalid", "error", "not found", "unrecognized"]):
                found_error = True
                break
            time.sleep(1)
        if found_error:
            print("[TC2.3] Agent displayed error for invalid input. Alternative flow test passed.")
        else:
            print("[TC2.3] Agent did not display error for invalid input. Alternative flow test failed.")
    except Exception as e:
        print("[TC2.1/TC2.2/TC2.3] Test failed:", e)
    finally:
        driver.quit()

if __name__ == "__main__":
    test_start_agent_and_show_events()
