from setrepcli import SetRepClient
from utilities import wait_key, add_item_to_menus, remove_item_from_menus, is_integer, is_time_format, prompt_for_bilateral_choice
from abconsolemenu import *
from abconsolemenu.items import *
from abconsolemenu import prompt_utils as pu
from constants import *
from telethon.sync import TelegramClient
from telethon.sessions import StringSession
import sys
import os
import json
import validators
import feedparser
import time
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
import re
from xpilot import DrvTypes
from abconsolemenu.validators.positiveint import PositiveIntValidator

prompt: pu.PromptUtils = pu.PromptUtils(Screen())
menus: list[ConsoleMenu] = []

SETTING_DFT =   [
                    {'code': 'browser_driver', 'value': 'Undetected Chrome'}, 
                    {'code': 'headless', 'value': '1'}, 
                    {'code': 'log_enabled', 'value': '0'}, 
                    {'code': 'min_start_delay', 'value': '180'}, 
                    {'code': 'max_start_delay', 'value': '1800'}, 
                    {'code': 'min_n_rss_items_to_post', 'value': '1'}, 
                    {'code': 'max_n_rss_items_to_post', 'value': '1'}, 
                    {'code': 'min_posting_interval', 'value': '60'}, 
                    {'code': 'max_posting_interval', 'value': '600'}, 
                ]

user_key: str = ''
user_token: str = ''
set_rep: SetRepClient = None
settings: list = None
accounts: list = []
feeds: list = []

config_mode: bool = True

last_read_feed_rss_error: str = None

def get_setting(code):
    global settings
    for d in settings:
        if d.get('code') == code:
            return d.get('value')
    return None

def set_browser_driver():
    print("*********************")
    print("CHANGE BROWSER DRIVER")
    print("*********************\n")
    curr_val = get_setting('browser_driver')
    print(f"Current value: {curr_val}\n")
    new_val = DrvTypes.DT_CHROME
    if curr_val == new_val:
        new_val = DrvTypes.DT_UNDETECTEDCHROME
    res = prompt_for_bilateral_choice(f"Change valure to '{new_val}'?", 's', 'n')
    if (res == 's'):
        if set_rep.set_key_value('main', 'browser_driver', new_val):
            get_settings(user_key, user_token, True)
            print(f"\nNew value setted: '{new_val}'.")
        else:    
            print("\n[ERROR] Setting save failed.")
    else:        
        print("\nNo changes have been made.")    
    wait_key()

def set_headless_browser():
    print("*******************************")
    print("ENABLE/DISABLE HEADLESS BROWSER")
    print("*******************************\n")
    curr_val = int(get_setting('headless'))
    curr_val_desc = 'DISABLED'
    new_val_desc = 'ENABLED'
    new_val = 1
    if curr_val:
        curr_val_desc = 'ENABLED'
        new_val_desc = 'DISABLED'
        new_val = 0
    print(f"Current value: {curr_val_desc}\n")
    res = prompt_for_bilateral_choice(f"Change valure to '{new_val_desc}'?", 's', 'n')
    if (res == 's'):
        if set_rep.set_key_value('main', 'headless', new_val):
            get_settings(user_key, user_token, True)
            print(f"\nNew value setted: '{new_val_desc}'.")
        else:    
            print("\n[ERROR] Setting save failed.")
    else:        
        print("\nNo changes have been made.")    
    wait_key()

def set_min_start_delay():
    print("***************")
    print("MIN START DELAY")
    print("***************\n")
    curr_val = get_setting('min_start_delay')
    print(f"Current value (seconds): {curr_val}\n")
    v = PositiveIntValidator()
    putils = pu.PromptUtils(Screen())
    go_on: bool = True
    while go_on:
        new_val = putils.input(prompt=f"\nNew value (seconds):", default=curr_val, validators=v)
        go_on = not new_val.validation_result
    if set_rep.set_key_value('main', 'min_start_delay', new_val.input_string):
        get_settings(user_key, user_token, True)
        print(f"\nNew value setted: {new_val.input_string} seconds.")
    else:    
        print("\n[ERROR] Setting save failed.")
    wait_key()

def set_max_start_delay():
    print("***************")
    print("MAX START DELAY")
    print("***************\n")
    curr_val = get_setting('max_start_delay')
    print(f"Current value (seconds): {curr_val}\n")
    v = PositiveIntValidator()
    putils = pu.PromptUtils(Screen())
    go_on: bool = True
    while go_on:
        new_val = putils.input(prompt=f"\nNew value (seconds):", default=curr_val, validators=v)
        go_on = not new_val.validation_result
    if set_rep.set_key_value('main', 'max_start_delay', new_val.input_string):
        get_settings(user_key, user_token, True)
        print(f"\nNew value setted: {new_val.input_string} seconds.")
    else:    
        print("\n[ERROR] Setting save failed.")
    wait_key()

def load_settings():
    global config_mode, user_key, user_token
    try:
        if len(sys.argv) > 1:
            config_mode = False
            for par in sys.argv[1:]:
                par = par.strip()
                if par == '-s':
                    config_mode = True
                if len(par) > 2:
                    if (not user_key) and (par[:2] == '-k'):
                        user_key = par[2:]
                    if (not user_token) and (par[:2] == '-t'):
                        user_token = par[2:]
        if not user_key:
            user_key = prompt.input(prompt = "Insert user key:", enable_quit = True)[0]
        if not user_token:
            user_token = prompt.input(prompt = "Insert user token:", enable_quit = True)[0]
        get_settings(user_key, user_token)
    except Exception as e:
        if str(e):
            print(f"[ERROR] {str(e)}")

def apply_settings_dft():
    global settings, SETTING_DFT
    for setting in settings:
        for default in SETTING_DFT:
            if (setting['code'] == default['code']) and (setting['value'] is None):
                setting['value'] = default['value']
    
def mnu_add_to_list(menu: ConsoleMenu) -> None:
    if menu:
        menus.append(menu)

def get_settings(user_key: str, user_token: str, silent: bool = False):
    global set_rep, settings, accounts, feeds
    if not silent:
        print("Loading settings...")
    try:
        set_rep = SetRepClient(SETREP_BASE_URL, user_key, user_token, APP_CODE)
        settings = set_rep.get_section_keys_values('main')
        apply_settings_dft()
        json_accounts = set_rep.get_key_value('main', 'x_accounts')
        if json_accounts:
            accounts = json.loads(json_accounts)
        json_feeds = set_rep.get_key_value('main', 'rss_feeds')
        if json_feeds:
            feeds = json.loads(json_feeds)
    except Exception as e:
        set_rep = None
        if str(e):
            if not silent:
                print(f"[ERROR] {str(e)}")
    finally:
        if not silent:
            print("Loading settings finished.")

def str_to_groups_list(grp: str):
    grp = grp.strip()
    if grp:
        res = grp.split(',')
        result: list = []
        ok: bool = False
        for item in res:
            item = item.strip()
            if item:
                ok = True
                if is_integer(item):
                    result.append(int(item))
                else:
                    result.append(item)
        if ok:
            return result
    return None

def str_to_list(text: str):
    text = text.strip()
    if text:
        res = text.split(',')
        result: list = []
        ok: bool = False
        for item in res:
            item = item.strip()
            if item:
                ok = True
                result.append(item)
        if ok:
            return result
    return None

def add_job() -> None: 
    print("Adding job...")
    wrong_data: bool = True
    while wrong_data:
        new_item_name = prompt.input(prompt = "Name:")[0].strip()
        wrong_data = (not new_item_name) or job_name_exists(new_item_name)
        if wrong_data:
            print("Duplicate name. Choose another name...")
    wrong_data = True
    while wrong_data:
        new_item_rss = prompt.input(prompt = "RSS URL:")[0].strip()
        wrong_data = not validators.url(new_item_rss)
        if wrong_data:
            print("Wrong URL. Insert a valid URL...")
    new_item_groups: list = None
    while not new_item_groups:
        new_item_groups = str_to_groups_list(prompt.input(prompt = "Target groups (name or ID comma separated):")[0])
    new_item_model_code: str = None
    if models:
        model_names: list[str] = []
        for model in models:
            model_names.append(model['name'])
        model_index = prompt.prompt_for_numbered_choice(choices = model_names, title = 'Message model:', clear_screen = False)
        new_item_model_code = models[model_index]['code']
    new_item_send_as = prompt.input(prompt = "Send as (optional):")[0].strip()
    if not new_item_send_as:
        new_item_send_as = None
    new_item_forbidden_words = str_to_list(prompt.input(prompt = "Forbidden words (comma separated, optional):")[0])
    new_item_required_words = str_to_list(prompt.input(prompt = "Required words (comma separated, optional):")[0])
    wrong_data: bool = True
    while wrong_data:
        new_item_time_from = prompt.input(prompt = "Time interval from [hh:mm] (optional):")[0].strip()
        wrong_data = new_item_time_from and (not is_time_format(new_item_time_from))
        if wrong_data:
            print("Wrong time format. Insert a valid time or press [ENTER]...")
    if not new_item_time_from:
        new_item_time_from = None
    wrong_data: bool = True
    while wrong_data:
        new_item_time_to = prompt.input(prompt = "Time interval to [hh:mm] (optional):")[0].strip()
        wrong_data = new_item_time_to and (not is_time_format(new_item_time_to))
        if wrong_data:
            print("Wrong time format. Insert a valid time or press [ENTER]...")
        else:
            if new_item_time_to:
                wrong_data = new_item_time_to < new_item_time_from
                if wrong_data:
                    print("Must be after time interval to. Insert a valid time or press [ENTER]...")
    if not new_item_time_to:
        new_item_time_to = None
    new_item = {
        "name": new_item_name,
        "rss": new_item_rss,
        "groups": new_item_groups,
        "model_code": new_item_model_code,
        "send_as": new_item_send_as,
        "forbidden_words": new_item_forbidden_words,
        "required_words": new_item_required_words,
        "time_from": new_item_time_from,
        "time_to": new_item_time_to,
        "last_rss_items": None
    }    
    jobs.append(new_item)
    try:
        save_jobs()
    except Exception as e:
        jobs.pop(len(jobs) - 1)
        print(f"[ERROR] {str(e)}. Operation aborted.")
    else:
        del_item: FunctionItem = FunctionItem(new_item_name, del_job, [len(jobs) - 1])
        view_item: FunctionItem = FunctionItem(new_item_name, view_job, [len(jobs) - 1])
        add_item_to_menus(menus, del_item, ['Delete Job'], False)
        add_item_to_menus(menus, view_item, ['View Job'], False)
        print(f"{new_item_name} created.")
    wait_key()

def del_job(index: int) -> None:
    key_data = jobs[index]
    key_name = key_data['name']
    jobs.pop(index)
    try:
        save_jobs()
    except Exception as e:
        jobs.insert(index, key_data)
        print(f"[ERROR] {str(e)}. Operation aborted.")
    else:
        remove_item_from_menus(menus, key_name)
        print(key_name + " deleted.")
    wait_key()

def get_mnu_delete_jobs() -> list[dict]:
    result = []

    return result

    for index, job in enumerate(jobs):
        result.append({"title": job['name'], "type": "func", "exec": "core.del_job", "args": [index]})
    return result

def view_job(index: int) -> None:
    print("Job data...\n")
    key_data = jobs[index]
    model_name: str = ''
    if key_data['model_code']:
        for model in models:
            if model['code'] == key_data['model_code']:
                model_name = model['name'] 
    grps: str = ", ".join(str(item) for item in key_data['groups'])
    print(f"NAME           : {key_data['name']}\nRSS            : {key_data['rss']}\nGROUPS         : {grps}\nMODEL          : {model_name}\nSEND AS        : {key_data['send_as']}\nFORBIDDEN WORDS: {key_data['forbidden_words']}\nREQUIRED WORDS : {key_data['required_words']}\nTIME FROM      : {key_data['time_from']}\nTIME TO        : {key_data['time_to']}\n")
    wait_key()

def get_mnu_view_jobs() -> list[dict]:
    result = []
    for index, job in enumerate(jobs):
        result.append({"title": job['name'], "type": "func", "exec": "core.view_job", "args": [index]})
    return result

def job_name_exists(name: str)->bool:
    found = False
    name = name.strip().upper()
    for item in jobs:
        if item.get("name").strip().upper() == name:
            found = True
            break
    return found

def save_jobs():
    value: str = json.dumps(jobs)
    set_rep.set_key_value('main', 'jobs', value)

def read_feed_rss(url: str, sanitizeLink: bool = True, asc_order_by_date: bool = True)->list[dict]:

    def sanitize_link(link: str)->str:
        parsed_url = urlparse(link)
        params = parse_qs(parsed_url.query)
        params.pop('utm_source', None)
        params.pop('utm_medium', None)
        params.pop('utm_campaign', None)
        new_query = urlencode(params, doseq=True)
        new_url = urlunparse(
            (parsed_url.scheme, parsed_url.netloc, parsed_url.path,
            parsed_url.params, new_query, parsed_url.fragment)
        )
        return new_url.rstrip('?')

    global last_read_feed_rss_error
    try:
        url = url.strip()
        if not validators.url(url):
            raise Exception("Wrong RSS feed URL")
        result: list[dict] = []
        feed = feedparser.parse(url)
        for entry in feed.entries:
            item = {}
            if entry.title:
                item["title"] = entry.title
            else:
                item["title"] = None
            if entry.link:
                if sanitizeLink:
                    item["link"] = sanitize_link(entry.link)
                else:
                    item["link"] = entry.link
            else:
                item["link"] = None
            if entry.published_parsed:
                item["published"] = time.strftime('%Y-%m-%d %H:%M:%S', entry.published_parsed)
                item["published_parsed"] = entry.published_parsed
            else:
                item["published"] = ''
                item["published_parsed"] = None
            if entry.summary:
                item["summary"] = entry.summary
            else:
                item["summary"] = None
            item["id"] = entry.id
            tags: list[str] = []
            try:
                if entry.tags:
                    for t in entry.tags:
                        tags.append(t['term'].strip())
            except Exception as e:
                ...
            item["tags"] = tags
            result.append(item)
        if asc_order_by_date and result and (len(result) > 0):
            result.sort(key=lambda x: x['published'])
        return result
    except Exception as e:
        last_read_feed_rss_error = str(e)
        return None

def apply_model(model_code: str, replacements: dict)-> str:
    model_content: str = ''
    for model in models:
        if model['code'] == model_code:
            model_content = model['value']
    if model_content:
        pattern = re.compile(r'%%(.*?)%%')
        matches = pattern.findall(model_content)
        for match in matches:
            if match in replacements:
                model_content = model_content.replace(f'%%{match}%%', replacements[match])
    return model_content

def start():
    print(settings)
    if config_mode:
        wait_key()
    return

    from xpilot import XPilot
    browser = XPilot(login='BarbagalloA', password='kim62330', headless=False)
    try:
        res = browser.Login()
        if res:
            print('Logged in as ' + str(browser.GetCurrentAccountName()))
        else:
            print('Login failed')
    finally:
#        browser.Close()
#        browser = None
        ...
    ...

    if config_mode:
        wait_key()

    return
    print(">>> Start posting RSS items... <<<")
    for job_index, job in enumerate(core.accounts):
        ...
    print(">>> Posting RSS items completed. <<<")


