CREATE SCHEMA IF NOT EXISTS public;

CREATE TABLE IF NOT EXISTS public.idents (
    ident_file character varying(256) NOT NULL UNIQUE,
    ident_cgname character varying(256) NOT NULL,
    ident_duration integer,
    ident_id serial PRIMARY KEY,
    ident_lastplay timestamp with time zone
);

CREATE TABLE IF NOT EXISTS public.runlog (
    run_cmd character varying(256) NOT NULL,
    run_id serial PRIMARY KEY,
    run_type character varying(8) NOT NULL,
    run_time timestamp with time zone NOT NULL
);

CREATE TABLE IF NOT EXISTS public.videos (
    video_file character varying(256) NOT NULL UNIQUE,
    video_cgname character varying(256) NOT NULL,
    video_duration integer,
    video_id serial PRIMARY KEY,
    video_lastplay timestamp with time zone
);
