# Huntsman
Very simple playout system. Launches CasparCG, scans some video folders, and plays the resulting media - all on one server.

## Media play order
- Ident from "idents" folder
- Video from "videos" folder
- Ident from "idents" folder
- Schedule web page
- ... repeat

# Usage
- Rename `config.json.sample` to `config.json`
- Change the relevant details in `config.json`
- Create the DB tables
- Run `python __main__.py`

# Prerequisites
- Working PostgreSQL database
- python (>= 3.6)
- psycopg2
- Installed and working CasparCG