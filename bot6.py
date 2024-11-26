import os
import sys
import time
import json
import requests
from dotenv import load_dotenv

def send_telegram_message(chat_id, message, thread_id=None):
    telegram_url = f"https://api.telegram.org/bot{os.getenv('BOT_API_TOKEN')}/sendMessage"
    if thread_id:
        telegram_payload = {"chat_id": chat_id, "text": message, "message_thread_id": thread_id}
    else:
        telegram_payload = {"chat_id": chat_id, "text": message}
    response = requests.post(telegram_url, json=telegram_payload)
    if response.status_code != 200:
        print(f"Ошибка при отправке сообщения в Телеграм: {response.text}")

def get_players_to_notify(data, telegram_users):
    players_to_notify = []
    
    for member in data:
        playerName = member["playerName"]
        currentValue = int([x["currentValue"] for x in member["memberContribution"] if x["type"] == 2][0])
        
        if currentValue < 600 and playerName in telegram_users:
            telegramName = telegram_users[playerName]
            players_to_notify.append(f"{playerName} ({currentValue} / 600) {telegramName}")

    return players_to_notify

def check_response(response):
    if "guild" in response.json():
        return True
    return False

def main():
    load_dotenv(dotenv_path=sys.argv[1])
    
    if os.getenv("GUILD_ID"):
        thread_id = os.getenv("THREAD_ID")
    guild_id = os.getenv("GUILD_ID")
    chat_id = os.getenv("CHAT_ID")
    comlink_url = os.getenv("COMLINK_URL")
    telegram_users_str = os.getenv("TELEGRAM_USERS")
    telegram_users = json.loads(telegram_users_str)
    url = f"{comlink_url}/guild"

    payload = {
        "payload": {
            "guildId": guild_id,
            "includeRecentGuildActivityInfo": True
        },
        "enums": False
    }

    response = None
    while not response or not check_response(response):
        response = requests.post(url, json=payload)
        if not check_response(response):
            print("Guild не найден в ответе. Повторный запрос через 30 секунд...")
            time.sleep(30) 
    
    data = response.json()["guild"]["member"]

    players_to_notify = get_players_to_notify(data, telegram_users)
    if players_to_notify:
        message = "Кто тянет команду вниз?\nКто положил меньше всех денег в банк?\nКто не ответил ни на один вопрос?\nКто самое слабое звено?\n\n" + "\n".join(players_to_notify)
    else:
        message = "Нихуя себе дождались.\nВсе энку сдали...\n"

    send_telegram_message(chat_id, message, thread_id)

if __name__ == "__main__":
    main()