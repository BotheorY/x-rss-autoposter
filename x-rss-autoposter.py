from menu import run_menu as rm, create_menu as cm
import core
from constants import *
import os
import warnings
import utilities as ut
import asyncio
import validators

warnings.simplefilter("ignore")

async def do_run():

    async def main_loop():
        rss: list[dict] = None
        rss_item_sent: bool = False
        core.start()
        
    await main_loop()

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
                                                            "exec": "core.set_browser_driver"
                                                        },                       
                                                        {
                                                            "title": "Enable/Disable Headless Browsing", 
                                                            "type": "func", 
                                                            "exec": "core.set_headless_browser"
                                                        },                       
                                                        {
                                                            "title": "Min Start Delay", 
                                                            "type": "func", 
                                                            "exec": "core.set_min_start_delay"
                                                        },
                                                        {
                                                            "title": "Max Start Delay", 
                                                            "type": "func", 
                                                            "exec": "core.set_max_start_delay"
                                                        },
                                                        {
                                                            "title": "Min Posting Interval", 
                                                            "type": "func", 
                                                            "exec": "core.get_mnu_delete_jobs"
                                                        },
                                                        {
                                                            "title": "Max Posting Interval", 
                                                            "type": "func", 
                                                            "exec": "core.get_mnu_delete_jobs"
                                                        },
                                                        {
                                                            "title": "Min N. RSS Items To Post", 
                                                            "type": "func", 
                                                            "exec": "core.get_mnu_delete_jobs"
                                                        },
                                                        {
                                                            "title": "Max N. RSS Items To Post", 
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
            print(f"[ERROR] {str(e)}")
            ...


if __name__ == '__main__':
    try:
        try:
            core.load_settings()
        except Exception as e:
            ...
        if (core.config_mode):
            main()
        else:
            if core.set_rep:
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