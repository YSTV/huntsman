import json
import logging
import os
import psycopg2
import subprocess
import threading
import time

import casparcg
import filewatch
import player

logger = logging.getLogger(__name__)

CONFIG_PATH = "config.json"

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    logger.info("Reading config file: \"{}\"".format(CONFIG_PATH))
    with open(CONFIG_PATH, "r") as config_file:
        CONFIG = json.load(config_file)

    conn = psycopg2.connect("dbname={} user={}".format(
            CONFIG["db"]["dbname"],
            CONFIG["db"]["user"]
        ))
    conn.set_session(autocommit=True)

    file_cur = conn.cursor()
    play_cur = conn.cursor()

    # Sort out CasparCG
    cgthread = threading.Thread(
        target=casparcg.run_casparcg,
        kwargs={"binary": CONFIG["casparcg"]["binary"]},
        daemon=True
    )
    cgthread.start()

    # Sort out Watchfolders
    filethread = threading.Thread(
        target=filewatch.watch_folders,
        kwargs={
            "media_path": CONFIG["casparcg"]["media_root"],
            "video_folder": CONFIG["casparcg"]["videos"],
            "ident_folder": CONFIG["casparcg"]["idents"],
            "dbcur": file_cur
        },
        daemon=True
    )
    filethread.start()

    # Kick off the control
    playthread = threading.Thread(
        target=player.run_control,
        kwargs={
            "cghost": CONFIG["casparcg"]["host"], 
            "cgport": CONFIG["casparcg"]["port"], 
            "cgweb": CONFIG["webpage"], 
            "dbcur": play_cur
        },
        daemon=True
    )
    time.sleep(10)
    playthread.start()

    while True:
        try:
            time.sleep(1)
        except KeyboardInterrupt:
            break
