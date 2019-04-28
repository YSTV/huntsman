import json
import logging
import os
import psycopg2
import time

logger = logging.getLogger(__name__)

# How long to wait between scans
LOOP_WAIT = 30

# Select statement to get existing idents
ident_select = "select ident_id,ident_file,ident_cgname,ident_duration from idents where ident_file = '{}'"
# Insert statement for adding an ident to the DB
ident_insert = "insert into idents (ident_file, ident_cgname)  values ('{}', '{}')"

# Select statement to get existing videos
video_select = "select video_id,video_file,video_cgname,video_duration from videos where video_file = '{}'"
# Insert statement for adding an ident to the DB
video_insert = "insert into videos (video_file, video_cgname)  values ('{}', '{}')"

def video_update(path, folder, db):
    """Search the specified folder in path for video files and add them
    into the videos DB.

    Args:
        path: Root path for media files
        folder: Path from media root path to videos folder
        db: Cursor for the database
    
    Returns:
        None.
    """

    for video in os.listdir(os.path.join(path, folder)):
        video = video.replace("'", "''")
        db.execute(video_select.format(video))
        result = db.fetchall()
        if result == []:
            logger.info("Adding new video to DB: \"{}\"".format(video))
            cmd =  video_insert.format(
                    video, 
                    folder.upper() + "/" + os.path.splitext(video)[0].upper()
                )
            db.execute(cmd)

def ident_update(path, folder, db):
    """Search the specified folder in path for ident files and add them
    into the ident DB.

    Args:
        path: Root path for media files
        folder: Path from media root path to ident folder
        db: Cursor for the database
    
    Returns:
        None.
    """

    for ident in os.listdir(os.path.join(path, folder)):
        ident = ident.replace("'", "''")
        db.execute(ident_select.format(ident))
        result = db.fetchall()
        if result == []:
            logger.info("Adding new ident to DB: \"{}\"".format(ident))
            cmd =  ident_insert.format(
                    ident, 
                    folder.upper() + "/" + os.path.splitext(ident)[0].upper()
                )
            db.execute(cmd)

def watch_folders(media_path, video_folder, ident_folder, dbcur):
    """Loop to actually run the watchfolders."""

    while True:
        try:
            logger.info("Scanning folders...")
            
            logger.debug("Scanning video folder.")
            video_update(media_path, video_folder, dbcur)

            logger.debug("Scanning ident folder.")
            ident_update(media_path, ident_folder, dbcur)
        except KeyboardInterrupt:
            break
        except:
            logger.exception("Unexpected error:")
        finally:
            logger.debug("Scanning again in {} seconds.".format(LOOP_WAIT))
            time.sleep(LOOP_WAIT)



if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    conn = psycopg2.connect("dbname=huntsman user=postgres")
    conn.set_session(autocommit=True)

    cur = conn.cursor()

    media_path = "V:\\CasparCG Server\\Server\\media"
    video_folder = "roses24"
    ident_folder = "ident"

    watch_folders(media_path, video_folder, ident_folder, cur)
