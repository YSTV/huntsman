import logging
import telnetlib
import time
import xml.etree.ElementTree

import psycopg2

logger = logging.getLogger(__name__)

LOOP_WAIT = 2

def check_web():
    return True

class Database():

    def fetchall(self):
        return self.cur.fetchall()

    def execute(self, sql):
        return self.cur.execute(sql)

    def update_ident(self, filename):
        filename = filename.replace("'", "''")
        self.cur.execute("update idents set ident_lastplay=NOW() where ident_cgname = '{}'".format(filename))


    def update_video(self, filename):
        filename = filename.replace("'", "''")
        self.cur.execute("update videos set video_lastplay=NOW() where video_cgname = '{}'".format(filename))

    def update_runlog(self, cmd, action):
        cmd = cmd.replace("'", "''")
        self.cur.execute("insert into runlog (run_cmd, run_time, run_type) values ('{}', NOW(), '{}')".format(cmd, action))

    def __init__(self, cur=None):
        if cur:
            self.cur = cur
        else:
            self.conn = psycopg2.connect("dbname=huntsman user=postgres")
            self.conn.set_session(autocommit=True)
            self.cur = self.conn.cursor()

    def get_next_video(self):
        self.execute("select video_cgname from videos where video_lastplay is null limit 1")
        video = self.fetchall()
        if video:
            return video[0][0]

        self.execute("select video_cgname from videos order by video_lastplay asc limit 1")
        return self.fetchall()[0][0]

    def get_next_ident(self):
        self.execute("select ident_cgname from idents where ident_lastplay is null limit 1")
        video = self.fetchall()
        if video:
            return video[0][0]

        self.execute("select ident_cgname from idents order by ident_lastplay asc limit 1")
        return self.fetchall()[0][0]

    def next_action(self):
        self.execute("select run_type from runlog order by run_time desc limit 2")

        rows = self.fetchall()

        if len(rows) == 0:
            return "ident"
        if len(rows) == 1:
            return "web"

        if rows[0][0] == "ident":
            if rows[1][0] == "web":
                return "video"
            elif rows[1][0] == "video":
                return "web"
        else:
            return "ident"

    def current_action(self):
        self.execute("select run_type from runlog order by run_time desc limit 1")

        rows = self.fetchall()

        if len(rows) == 0:
            return None
        else:
            return rows[0][0]

class Casparcg():

    def frames_left(self, channel=1, layer=10):

        cmd = "INFO {}-{}\r\n".format(channel, layer).encode("ascii")
        self.tel.write(cmd)
        ret_code = self.tel.read_until(b"\r\n")
        if b"201 INFO OK" not in ret_code:
            raise Exception("Unexpected response code {}".format(ret_code))
        ret = self.tel.read_until(b"\r\n")
        tree = xml.etree.ElementTree.fromstring(ret)
        frame_tot = int(tree.find("nb_frames").text)
        frame_left = int(tree.find("frames-left").text)

        if frame_left > frame_tot:
            # Probably finished
            return 0
        else:
            return int(tree.find("frames-left").text)

    def runTemplate(self, template, channel = 1, layer = 20, flayer = 1, f0 = None):

        cmd = "CG {}-{} ADD {} \"{}\" 1 \"<templateData><componentData id=\\\"f0\\\"><data id=\\\"text\\\" value=\\\"{}\\\"/></componentData></templateData>\"\r\n".format(channel, layer, flayer, template, f0)
        self.tel.write(cmd)

    def stop(self, channel, layer, flayer):

        self.tel.write('CG {}-{} STOP {}\r\n'.format(channel, layer, flayer))

    def clear(self, channel=1, layer=10):

        self.tel.write('CG {}-{} CLEAR\r\n'.format(channel, layer).encode("ascii"))
        ret_code = self.tel.read_until(b"\r\n")
        if b"202 CG OK" not in ret_code:
            raise Exception("Unexpected response code {}".format(ret_code))
    
    def play_file(self, filename, channel=1, layer=10):
        cmd = "PLAY {}-{} \"{}\" CUT 1 Linear RIGHT\r\n".format(channel, layer, filename).encode("ascii")
        self.tel.write(cmd)
        ret_code = self.tel.read_until(b"\r\n")
        if b"202 PLAY OK" not in ret_code:
            raise Exception("Unexpected response code {}".format(ret_code))
        return cmd.decode("ascii")
    
    def play_web(self, url, channel=1, layer=10):
        cmd = "PLAY {}-{} [HTML] \"{}\" CUT 1 Linear RIGHT\r\n".format(channel, layer, url)
        self._play(cmd)
        return cmd

    def _play(self, cmd):
        self.tel.write(cmd.encode("ascii"))
        ret_code = self.tel.read_until(b"\r\n")
        if b"202 PLAY OK" not in ret_code:
            raise Exception("Unexpected response code {}".format(ret_code))

    def __init__(self, host = None, port = None):
        self.host = host
        self.port = port
        self.tel = telnetlib.Telnet(host = host, port = port)
        self.name = 'casparcg'
        #self.open()

def run_control(cghost, cgport, cgweb, dbcur):

    cg = Casparcg(cghost, cgport)
    db = Database(cur=dbcur)

    action = db.next_action()
    web_count = 0

    logger.info("Starting Huntsman player control")
    while True:
        try:
            frames = cg.frames_left()
            if frames == 0:
                #cg.play_file("ROSES24/18_UNIBRASSSHIELDBRISTOL_SPR06")
                action = db.next_action()
                if action == "video":
                    next_vid = db.get_next_video()
                    logger.info("Playing {}.".format(next_vid))
                    cmd = cg.play_file(next_vid)
                    db.update_runlog(cmd, action)
                    db.update_video(next_vid)
                elif action == "web":
                    cmd = cg.play_web("https://google.com")
                    logger.info("Playing Schedule.")
                    db.update_runlog(cmd, action)
                elif action == "ident":
                    next_ident = db.get_next_ident()
                    logger.info("Playing {}.".format(next_ident))
                    cmd = cg.play_file(next_ident)
                    db.update_runlog(cmd, action)
                    db.update_ident(next_ident)
                time.sleep(1)
            elif frames < 10:
                time.sleep(1/25)
            elif frames < 75:
                time.sleep((frames-10)/25)
            else:
                if db.current_action() == "web":
                    if web_count > 10:
                        web_count = 0
                        cg.clear()
                        continue
                    else:
                        web_count += 1
                logger.debug("Still playing, waiting for {} seconds...".format(LOOP_WAIT))
        except KeyboardInterrupt:
            break
        except:
            logger.Exception("Unexpected error.")
        finally:
            time.sleep(LOOP_WAIT)


if __name__ == "__main__":
    pass
    
#    host = 'localhost'
#    port = '5250'

#    cg = Casparcg(host, port)
#    db = Database()
