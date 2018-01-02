import json
import requests
import time
import urllib

from reminder import Reminder

rmd = Reminder()
from fysom import Fysom

fsm = Fysom({'initial': 'awake',
             'events': [{'name': 'wakeup', 'src': 'sleeping', 'dst': 'awake'},
                        {'name': 'complete', 'src': '*', 'dst': 'awake'},
                        {'name': 'back', 'src': '*', 'dst': 'awake'},
                        {'name': 'work', 'src': 'awake', 'dst': 'work'},
                        {'name': 'load', 'src': 'work', 'dst': 'on_load'},
                        {'name': 'sleep', 'src': 'awake', 'dst': 'sleeping'}]
             })

TOKEN = "431420437:AAHkFdOuT31iy4z9lCyBT1E_w2qjFBTAipE"
URL = "https://api.telegram.org/bot{}/".format(TOKEN)


def get_url(url):
    response = requests.get(url)
    content = response.content.decode("utf8")
    return content


def get_json_from_url(url):
    content = get_url(url)
    js = json.loads(content)
    return js


def get_updates(offset=None):
    url = URL + "getUpdates?timeout=100"
    if offset:
        url += "&offset={}".format(offset)
    js = get_json_from_url(url)
    return js


def get_last_update_id(updates):
    update_ids = []
    for update in updates["result"]:
        update_ids.append(int(update["update_id"]))
    return max(update_ids)


def handle_updates(updates):
    for update in updates["result"]:
        text = update["message"]["text"]
        chat = update["message"]["chat"]["id"]
        items = rmd.get_items()
        if text == "/finish":
            fsm.complete()
            keyboard = build_keyboard(items)
            send_message("select a task you completed,if nothing enter 'Ok'", chat, keyboard)
        elif text in items:
            rmd.delete_item(text)
            items = rmd.get_items()
            keyboard = build_keyboard(items)
            send_message("select an item to delete,if nothing enter 'Ok'", chat, keyboard)
        elif text == "Hi":
            send_message("Hello! Add something to your schedule?", chat)
            fsm.complete()
            print(fsm.current)
        elif text == "Ok":
            send_message("Call me whenever you want!", chat)
            fsm.back()
            fsm.sleep()
            print(fsm.current)
        elif text == "Wake up":
            send_message("What's wrong?", chat)
            fsm.wakeup()
            print(fsm.current)
        elif text == "Bye":
            send_message("Bye!I am always here!", chat)
        else:
            rmd.add_item(text)
            items = rmd.get_items()
            fsm.work()
            print(fsm.current)
            message = "\n".join(items)
            send_message("Successfully add task!", chat)
            send_message(message, chat)
            fsm.load()
            print(fsm.current)
            fsm.complete()
            print(fsm.current)


def get_last_chat_id_and_text(updates):
    num_updates = len(updates["result"])
    last_update = num_updates - 1
    text = updates["result"][last_update]["message"]["text"]
    chat_id = updates["result"][last_update]["message"]["chat"]["id"]
    return (text, chat_id)


def send_message(text, chat_id, reply_markup=None):
    text = urllib.parse.quote_plus(text)
    url = URL + "sendMessage?text={}&chat_id={}&parse_mode=Markdown".format(text, chat_id)
    if reply_markup:
        url += "&reply_markup={}".format(reply_markup)
    get_url(url)


def build_keyboard(items):
    keyboard = [[item] for item in items]
    reply_markup = {"keyboard": keyboard, "one_time_keyboard": True}
    return json.dumps(reply_markup)


def main():
    rmd.setup()
    last_update_id = None
    while True:
        updates = get_updates(last_update_id)
        if len(updates["result"]) > 0:
            last_update_id = get_last_update_id(updates) + 1
            handle_updates(updates)
        time.sleep(0.5)


if __name__ == '__main__':
    main()
