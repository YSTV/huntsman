import logging
import os
import subprocess
import time

logger = logging.getLogger(__name__)

LOOP_WAIT = 30

def run_casparcg(binary):

    while True:
        try:
            cwd = os.path.dirname(binary)

            logger.info("Starting CasparCG")
            subprocess.run(binary, cwd=cwd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except KeyboardInterrupt:
            break
        except:
            logger.exception("Unexpected error.")
        finally:
            logger.info("Restarting CasparCG in {} seconds".format(LOOP_WAIT))
            time.sleep(LOOP_WAIT)