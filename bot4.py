from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time
from telegram import Bot
from telegram.error import TelegramError
from PIL import Image
from io import BytesIO
import requests
import os

# Настройки
DISCORD_LOGIN_URL = "https://discord.com/login"
DISCORD_EMAIL = "samara63russian@gmail.com"  # Замените!
DISCORD_PASSWORD = "97944361kp4"  # Замените!
DISCORD_CHANNEL_URL = "https://discord.com/channels/1273689607552106517/1308809095834501150"  # Замените!
TELEGRAM_BOT_TOKEN = "7733610566:AAEqPPEjDll9zH0mmVlT8OAFpp5o4u1q7wE"  # Замените!
TELEGRAM_CHAT_ID = "-1002272823610"  # Замените!
SCREENSHOT_DELAY = 10  # Задержка перед скриншотом
TEMP_DIR = "D:\img"  # Временная папка для сохранения файлов
os.makedirs(TEMP_DIR, exist_ok=True)


def send_telegram_message(message):
    """Отправляет текстовое сообщение в Telegram."""
    try:
        bot = Bot(token=TELEGRAM_BOT_TOKEN)
        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
        print(f"Сообщение отправлено в Telegram: {message[:50]}...")
    except TelegramError as e:
        print(f"Ошибка при отправке текстового сообщения в Telegram: {e}")


def send_telegram_screenshot(image_bytes, caption=""):
    """Отправляет скриншот в Telegram."""
    try:
        bot = Bot(token=TELEGRAM_BOT_TOKEN)
        bot.send_photo(chat_id=TELEGRAM_CHAT_ID, photo=image_bytes, caption=caption)
        print("Скриншот отправлен в Telegram")
    except TelegramError as e:
        print(f"Ошибка при отправке скриншота в Telegram: {e}")


def send_telegram_file(file_path, caption=""):
    """Отправляет файл в Telegram."""
    try:
        bot = Bot(token=TELEGRAM_BOT_TOKEN)
        with open(file_path, "rb") as file:
            bot.send_document(chat_id=TELEGRAM_CHAT_ID, document=file, caption=caption)
        print(f"Файл {file_path} отправлен в Telegram")
    except TelegramError as e:
        print(f"Ошибка при отправке файла в Telegram: {e}")

def login_discord(driver):
    """Логинится в Discord."""
    driver.get(DISCORD_LOGIN_URL)
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.NAME, "email")))
    email_input = driver.find_element(By.NAME, "email")
    password_input = driver.find_element(By.NAME, "password")
    email_input.send_keys(DISCORD_EMAIL)
    password_input.send_keys(DISCORD_PASSWORD)
    driver.find_element(By.XPATH, "//button[@type='submit']").click()
    WebDriverWait(driver, 20).until(EC.url_contains("channels"))
    print("Успешно вошли в Discord")

def make_screenshot(driver, element):
    """Делает скриншот конкретного элемента на странице."""
    try:
        location = element.location
        size = element.size
        full_screenshot = driver.get_screenshot_as_png()
        full_image = Image.open(BytesIO(full_screenshot))
        cropped_image = full_image.crop((location['x'], location['y'], location['x'] + size['width'], location['y'] + size['height']))
        image_bytes = BytesIO()
        cropped_image.save(image_bytes, format="PNG")
        image_bytes.seek(0)
        return image_bytes
    except Exception as e:
        print(f"Ошибка при создании скриншота элемента: {e}")
        return None

def download_attachment(driver, attachment_element):
    """Загружает вложение и возвращает путь к сохраненному файлу."""
    try:
        attachment_link = attachment_element.get_attribute("href")
        response = requests.get(attachment_link, stream=True)
        response.raise_for_status()  # Проверка на ошибки
        filename = os.path.join(TEMP_DIR, os.path.basename(attachment_link))
        with open(filename, "wb") as file:
            for chunk in response.iter_content(chunk_size=8192):
                file.write(chunk)
        print(f"Файл {filename} загружен")
        return filename
    except Exception as e:
        print(f"Ошибка при загрузке вложения: {e}")
        return None

def get_new_messages(driver):
    """Получает новые сообщения из Discord, включая вложения."""
    driver.get(DISCORD_CHANNEL_URL)
    time.sleep(SCREENSHOT_DELAY)
    messages = []
    message_elements = driver.find_elements(By.CSS_SELECTOR, ".message-2qnXI6")
    for element in message_elements:
        try:
            user = element.find_element(By.CSS_SELECTOR, ".username-1A8OIy").text
            message_text_elements = element.find_elements(By.CSS_SELECTOR, ".markup-2BOw-j")
            message_text = ""
            if message_text_elements:
                 message_text = message_text_elements[0].text
            attachments = []
            attachment_elements = element.find_elements(By.CSS_SELECTOR, "a[class^='attachment-']")

            for attach in attachment_elements:
               downloaded_file_path = download_attachment(driver, attach)
               if downloaded_file_path:
                 attachments.append(downloaded_file_path)

            # если нет текста, берем скриншот всей области
            if not message_text and not attachments:
                 screenshot = make_screenshot(driver, element)
                 messages.append({"user": user, "text": None, "screenshot": screenshot, "attachments": []})
            else:
                messages.append({"user": user, "text": message_text, "screenshot": None, "attachments": attachments})

        except Exception as e:
             print(f"Ошибка при обработке сообщения: {e}")

    return messages

def main():
    """Основная логика программы."""
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
    try:
        login_discord(driver)
        last_messages = []
        while True:
           current_messages = get_new_messages(driver)
           new_messages = [msg for msg in current_messages if msg not in last_messages]
           for msg in new_messages:
               if msg['text']:
                    send_telegram_message(f"{msg['user']}: {msg['text']}")
               if msg['screenshot']:
                    send_telegram_screenshot(msg['screenshot'], caption = f"Сообщение от {msg['user']}")
               for attach in msg['attachments']:
                    send_telegram_file(attach, caption = f"Файл от {msg['user']}")
           last_messages = current_messages
           time.sleep(30)
    except Exception as e:
        print(f"Произошла ошибка: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    main()