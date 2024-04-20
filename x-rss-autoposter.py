from menu import run_menu as rm, create_menu as cm
import core
from constants import *
import os
import warnings
import utilities as ut
import asyncio
import validators

warnings.simplefilter("ignore")

try:
    core.load_settings()
except Exception as e:
    ...

async def do_run():

    async def main_loop():
        rss: list[dict] = None
        rss_item_sent: bool = False
        print(">>> Start sending messages... <<<")

        ut.ab_log(f"[main_loop] [100] core.jobs = {core.jobs}") # debug

        for job_index, job in enumerate(core.jobs):
            rss = None
            rss_item_sent = False
            print(f"\nStart processing job {job['name']}...")
            try:
                curr_time = ut.curr_time()

                ut.ab_log(f"[main_loop] [150] Starting time filters...") # debug

                if job['time_from'] and (curr_time < job['time_from']):
                    continue
                if job['time_to'] and (curr_time > job['time_to']):
                    continue

                ut.ab_log(f"[main_loop] [200] Time filters passed") # debug

                rss = core.read_feed_rss(job['rss'])
                if not rss:
                    continue

                ut.ab_log(f"[main_loop] [300] rss = {rss}") # debug

                for rss_item in rss:
                    print(f"\n\tProcessing RSS item \"{rss_item['title']}\"...")
                    rss_item_sent = False

                    ut.ab_log(f"[main_loop] [400] rss_item = {rss_item}") # debug

                    try:

                        ut.ab_log(f"[main_loop] [500] RSS item ID = {rss_item['id']}") # debug

                        if job['last_rss_items'] and (rss_item['id'] in job['last_rss_items']):
                            continue

                        ut.ab_log(f"[main_loop] [600] RSS item ID filter passed") # debug

                        content = ''
                        if rss_item['tags']:
                            content = rss_item['title'] + '; '
                        if rss_item['tags']:
                            content = content + ", ".join(rss_item['tags']) + '; '
                        if rss_item['summary']:
                            content = content + rss_item['summary']

                        ut.ab_log(f"[main_loop] [700] content = {content}") # debug

                        if job['forbidden_words'] and any(substring.lower() in content.lower() for substring in job['forbidden_words']):
                            continue
                        if job['required_words'] and (not any(substring.lower() in content.lower() for substring in job['required_words'])):
                            continue

                        ut.ab_log(f"[main_loop] [800] words filters passed") # debug

                        print("\tSending RSS item...")
                        if job['model_code']:
                            message = core.apply_model(job['model_code'], rss_item)
                        else:
                            message = rss_item['link']
                        if not message:
                            continue

                        ut.ab_log(f"[main_loop] [900] message = {message}") # debug

                        for group_index, group in enumerate(job['groups']):
                            print(f"\t\tSending message to chat \"{group}\"...")
                            try:
                                group = await get_private_group_id(group)
                                #core.jobs[job_index]['groups'][group_index] = group

                                ut.ab_log(f"[main_loop] [1.000] group ID = {group}") # debug

                                try:
                                    if not job['send_as']:
                                        raise SendAsPeerInvalidError("You can't send messages as an empty peer")
                                    await client(functions.messages.SendMessageRequest(
                                        peer = group,
                                        message = message,
                                        send_as = job['send_as'],
                                        silent = False,
                                        no_webpage = False
                                    ))
                                except SendAsPeerInvalidError as e:
                                    await client.send_message(entity = group, message = message, link_preview = True, silent = False)
                            except Exception as e:
                                print(f"\t\t[MESSAGE ERROR] {str(e)}")
                                print("\t\tMessage not sent.")

                                ut.ab_log(f"[main_loop] [1.050] sending message FAILED!! ({str(e)})") # debug

                            else:
                                print("\t\tMessage sent.")
                                rss_item_sent = True
                        if rss_item_sent:

                            ut.ab_log(f"[main_loop] [1.100] RSS item sent") # debug

                            new_last_rss_items = job['last_rss_items']
                            if not new_last_rss_items:
                                new_last_rss_items = []
                            new_last_rss_items.append(rss_item['id'])
                            core.jobs[job_index]['last_rss_items'] = new_last_rss_items

                            ut.ab_log(f"[main_loop] [1.200] core.jobs[{job_index}]['last_rss_items'] = {core.jobs[job_index]['last_rss_items']}") # debug

                    except Exception as e:
                        print(f"\t\t[RSS item ERROR] {str(e)}")
                        print("\t\tRSS item not processed.")

                        ut.ab_log(f"[main_loop] [1.250] processing RSS item FAILED!! ({str(e)})") # debug

                    finally:
                        print("\tRSS item processed.\n\t__________\n")

                    ut.ab_log(f"[main_loop] [1.300] END RSS item (break)") # debug

                    if rss_item_sent:
                        break
            except Exception as e:
                print(f"\t\t[JOB ERROR] {str(e)}")
                print("\t\tJob not processed.")

                ut.ab_log(f"[main_loop] [1.305] processing job FAILED!! ({str(e)})") # debug

            finally:
                print("Processing job completed.\n\n*************************\n")
                last_rss_items_count = len(core.jobs[job_index]['last_rss_items'])
                
                ut.ab_log(f"[main_loop] [1.310] JOB FINALLY 1") # debug

                if rss:
                    rss_count = len(rss)
                    
                    ut.ab_log(f"[main_loop] [1.320] JOB FINALLY 2") # debug

                    if last_rss_items_count > rss_count:

                        ut.ab_log(f"[main_loop] [1.400] cutting last_rss_items") # debug

                        del core.jobs[job_index]['last_rss_items'][:last_rss_items_count - rss_count]

                ut.ab_log(f"[main_loop] [1.500] core.jobs[{job_index}]['last_rss_items'] = {core.jobs[job_index]['last_rss_items']}") # debug


        ut.ab_log(f"[main_loop] [1.600] core.jobs = {core.jobs}") # debug

        core.save_jobs()
        print(">>> Sending messages completed. <<<")

    try:
        await client.connect()
    except Exception as e:
        print(f"[CONNECTION ERROR] {str(e)}")
    else:
        if client.is_connected():
            await main_loop()
        else:
            print("Connection failed.")

def main() -> None:

    try:

        menu: dict =    {
                            "title": "MAIN MENU",
                            "items":    
                            [
                                {
                                    "title": "Settings...",
                                    "submenu":  
                                    {
                                        "title": "Settings Menu",
                                        "items": 
                                        [
                                            {
                                                "title": "System...",
                                                "submenu":  
                                                {
                                                    "title": "System Settings Menu",
                                                    "items": 
                                                    [
                                                        {
                                                            "title": "Browser Driver", 
                                                            "type": "func", 
                                                            "exec": "core.get_mnu_delete_jobs"
                                                        },                       
                                                        {
                                                            "title": "Headless Browser", 
                                                            "type": "func", 
                                                            "exec": "core.get_mnu_delete_jobs"
                                                        },                       
                                                        {
                                                            "title": "Min Start Delay", 
                                                            "type": "func", 
                                                            "exec": "core.get_mnu_delete_jobs"
                                                        },
                                                        {
                                                            "title": "Max Start Delay", 
                                                            "type": "func", 
                                                            "exec": "core.get_mnu_delete_jobs"
                                                        },
                                                        {
                                                            "title": "Min Browser Delay", 
                                                            "type": "func", 
                                                            "exec": "core.get_mnu_delete_jobs"
                                                        },
                                                        {
                                                            "title": "Max Browser Delay", 
                                                            "type": "func", 
                                                            "exec": "core.get_mnu_delete_jobs"
                                                        },
                                                        {
                                                            "title": "Enable/Disable Logging", 
                                                            "type": "func", 
                                                            "exec": "core.get_mnu_delete_jobs"
                                                        },
                                                    ]
                                                }
                                            },
                                            {
                                                "title": "X Accounts...",
                                                "submenu":  
                                                {
                                                    "title": "X Accounts Menu",
                                                    "items": 
                                                    [
                                                        {
                                                            "title": "X Account List", 
                                                            "type": "func", 
                                                            "exec": "core.get_mnu_delete_jobs"
                                                        },
                                                        {
                                                            "title": "Add X Account", 
                                                            "type": "func", 
                                                            "exec": "core.get_mnu_delete_jobs"
                                                        },
                                                        {
                                                            "title": "Delete X Account...",
                                                            "submenu":  
                                                            {
                                                                "title": "Delete X Account",
                                                                "subtitle": "Choose the X account to delete:",
                                                                "items": "core.get_mnu_delete_jobs"
                                                            }
                                                        },
                                                    ]
                                                }
                                            },
                                            {
                                                "title": "RSS Feeds...",
                                                "submenu":  
                                                {
                                                    "title": "RSS Feeds Menu",
                                                    "items": 
                                                    [
                                                        {
                                                            "title": "RSS Feeds List", 
                                                            "type": "func", 
                                                            "exec": "core.get_mnu_delete_jobs"
                                                        },
                                                        {
                                                            "title": "Add RSS Feed", 
                                                            "type": "func", 
                                                            "exec": "core.get_mnu_delete_jobs"
                                                        },
                                                        {
                                                            "title": "Delete RSS Feeds...",
                                                            "submenu":  
                                                            {
                                                                "title": "Delete RSS Feed",
                                                                "subtitle": "Choose the RSS feed to delete:",
                                                                "items": "core.get_mnu_delete_jobs"
                                                            }
                                                        },
                                                    ]
                                                }
                                            },
                                        ]
                                    }
                                },
                                {
                                    "title": "Start", 
                                    "type": "func", 
                                    "exec": "core.start"
                                },
                                {
                                    "title": "Logout", 
                                    "type": "func", 
                                    "exec": "core.get_mnu_delete_jobs"
                                },
                            ]
                        }
        err: list = [False, None, None]
        err_msg: str = None
        res = rm(cm(menu, err))

        if err[0]:
            err_msg = err[1]

        if res:
            if err_msg:
                err_msg = err_msg + " \n" + res
            else:
                err_msg = res

        if err_msg:
            raise Exception(err_msg)

    except Exception as e:
        if str(e):
#            print(f"[ERROR] {str(e)}")
            ...


if __name__ == '__main__':
    try:
        if (core.config_mode):
            main()
        else:
            if core.set_rep and core.telegram_session:
                print('Running...')   
                try:
                    asyncio.get_event_loop().run_until_complete(do_run())
                except Exception as e:
                    ...
                    ut.ab_log(f"[MAIN] [100] asyncio.get_event_loop FAILED!! ({str(e)})") # debug

                finally:
                    print("Quitting...")
    except Exception as e:
        ...