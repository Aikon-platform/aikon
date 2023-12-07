--
-- PostgreSQL database dump
--

-- Dumped from database version 14.10 (Ubuntu 14.10-1.pgdg22.04+1)
-- Dumped by pg_dump version 16.1 (Ubuntu 16.1-1.pgdg22.04+1)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: public; Type: SCHEMA; Schema: -; Owner: postgres
--

-- *not* creating schema, since initdb creates it


ALTER SCHEMA public OWNER TO postgres;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: auth_group; Type: TABLE; Schema: public; Owner: salbouy
--

CREATE TABLE public.auth_group (
    id integer NOT NULL,
    name character varying(150) NOT NULL
);


ALTER TABLE public.auth_group OWNER TO salbouy;

--
-- Name: auth_group_id_seq; Type: SEQUENCE; Schema: public; Owner: salbouy
--

CREATE SEQUENCE public.auth_group_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.auth_group_id_seq OWNER TO salbouy;

--
-- Name: auth_group_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: salbouy
--

ALTER SEQUENCE public.auth_group_id_seq OWNED BY public.auth_group.id;


--
-- Name: auth_group_permissions; Type: TABLE; Schema: public; Owner: salbouy
--

CREATE TABLE public.auth_group_permissions (
    id bigint NOT NULL,
    group_id integer NOT NULL,
    permission_id integer NOT NULL
);


ALTER TABLE public.auth_group_permissions OWNER TO salbouy;

--
-- Name: auth_group_permissions_id_seq; Type: SEQUENCE; Schema: public; Owner: salbouy
--

CREATE SEQUENCE public.auth_group_permissions_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.auth_group_permissions_id_seq OWNER TO salbouy;

--
-- Name: auth_group_permissions_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: salbouy
--

ALTER SEQUENCE public.auth_group_permissions_id_seq OWNED BY public.auth_group_permissions.id;


--
-- Name: auth_permission; Type: TABLE; Schema: public; Owner: salbouy
--

CREATE TABLE public.auth_permission (
    id integer NOT NULL,
    name character varying(255) NOT NULL,
    content_type_id integer NOT NULL,
    codename character varying(100) NOT NULL
);


ALTER TABLE public.auth_permission OWNER TO salbouy;

--
-- Name: auth_permission_id_seq; Type: SEQUENCE; Schema: public; Owner: salbouy
--

CREATE SEQUENCE public.auth_permission_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.auth_permission_id_seq OWNER TO salbouy;

--
-- Name: auth_permission_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: salbouy
--

ALTER SEQUENCE public.auth_permission_id_seq OWNED BY public.auth_permission.id;


--
-- Name: auth_user; Type: TABLE; Schema: public; Owner: salbouy
--

CREATE TABLE public.auth_user (
    id integer NOT NULL,
    password character varying(128) NOT NULL,
    last_login timestamp with time zone,
    is_superuser boolean NOT NULL,
    username character varying(150) NOT NULL,
    first_name character varying(150) NOT NULL,
    last_name character varying(150) NOT NULL,
    email character varying(254) NOT NULL,
    is_staff boolean NOT NULL,
    is_active boolean NOT NULL,
    date_joined timestamp with time zone NOT NULL
);


ALTER TABLE public.auth_user OWNER TO salbouy;

--
-- Name: auth_user_groups; Type: TABLE; Schema: public; Owner: salbouy
--

CREATE TABLE public.auth_user_groups (
    id bigint NOT NULL,
    user_id integer NOT NULL,
    group_id integer NOT NULL
);


ALTER TABLE public.auth_user_groups OWNER TO salbouy;

--
-- Name: auth_user_groups_id_seq; Type: SEQUENCE; Schema: public; Owner: salbouy
--

CREATE SEQUENCE public.auth_user_groups_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.auth_user_groups_id_seq OWNER TO salbouy;

--
-- Name: auth_user_groups_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: salbouy
--

ALTER SEQUENCE public.auth_user_groups_id_seq OWNED BY public.auth_user_groups.id;


--
-- Name: auth_user_id_seq; Type: SEQUENCE; Schema: public; Owner: salbouy
--

CREATE SEQUENCE public.auth_user_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.auth_user_id_seq OWNER TO salbouy;

--
-- Name: auth_user_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: salbouy
--

ALTER SEQUENCE public.auth_user_id_seq OWNED BY public.auth_user.id;


--
-- Name: auth_user_user_permissions; Type: TABLE; Schema: public; Owner: salbouy
--

CREATE TABLE public.auth_user_user_permissions (
    id bigint NOT NULL,
    user_id integer NOT NULL,
    permission_id integer NOT NULL
);


ALTER TABLE public.auth_user_user_permissions OWNER TO salbouy;

--
-- Name: auth_user_user_permissions_id_seq; Type: SEQUENCE; Schema: public; Owner: salbouy
--

CREATE SEQUENCE public.auth_user_user_permissions_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.auth_user_user_permissions_id_seq OWNER TO salbouy;

--
-- Name: auth_user_user_permissions_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: salbouy
--

ALTER SEQUENCE public.auth_user_user_permissions_id_seq OWNED BY public.auth_user_user_permissions.id;


--
-- Name: django_admin_log; Type: TABLE; Schema: public; Owner: salbouy
--

CREATE TABLE public.django_admin_log (
    id integer NOT NULL,
    action_time timestamp with time zone NOT NULL,
    object_id text,
    object_repr character varying(200) NOT NULL,
    action_flag smallint NOT NULL,
    change_message text NOT NULL,
    content_type_id integer,
    user_id integer NOT NULL,
    CONSTRAINT django_admin_log_action_flag_check CHECK ((action_flag >= 0))
);


ALTER TABLE public.django_admin_log OWNER TO salbouy;

--
-- Name: django_admin_log_id_seq; Type: SEQUENCE; Schema: public; Owner: salbouy
--

CREATE SEQUENCE public.django_admin_log_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.django_admin_log_id_seq OWNER TO salbouy;

--
-- Name: django_admin_log_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: salbouy
--

ALTER SEQUENCE public.django_admin_log_id_seq OWNED BY public.django_admin_log.id;


--
-- Name: django_content_type; Type: TABLE; Schema: public; Owner: salbouy
--

CREATE TABLE public.django_content_type (
    id integer NOT NULL,
    app_label character varying(100) NOT NULL,
    model character varying(100) NOT NULL
);


ALTER TABLE public.django_content_type OWNER TO salbouy;

--
-- Name: django_content_type_id_seq; Type: SEQUENCE; Schema: public; Owner: salbouy
--

CREATE SEQUENCE public.django_content_type_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.django_content_type_id_seq OWNER TO salbouy;

--
-- Name: django_content_type_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: salbouy
--

ALTER SEQUENCE public.django_content_type_id_seq OWNED BY public.django_content_type.id;


--
-- Name: django_migrations; Type: TABLE; Schema: public; Owner: salbouy
--

CREATE TABLE public.django_migrations (
    id bigint NOT NULL,
    app character varying(255) NOT NULL,
    name character varying(255) NOT NULL,
    applied timestamp with time zone NOT NULL
);


ALTER TABLE public.django_migrations OWNER TO salbouy;

--
-- Name: django_migrations_id_seq; Type: SEQUENCE; Schema: public; Owner: salbouy
--

CREATE SEQUENCE public.django_migrations_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.django_migrations_id_seq OWNER TO salbouy;

--
-- Name: django_migrations_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: salbouy
--

ALTER SEQUENCE public.django_migrations_id_seq OWNED BY public.django_migrations.id;


--
-- Name: django_session; Type: TABLE; Schema: public; Owner: salbouy
--

CREATE TABLE public.django_session (
    session_key character varying(40) NOT NULL,
    session_data text NOT NULL,
    expire_date timestamp with time zone NOT NULL
);


ALTER TABLE public.django_session OWNER TO salbouy;

--
-- Name: webapp_annotation; Type: TABLE; Schema: public; Owner: salbouy
--

CREATE TABLE public.webapp_annotation (
    id bigint NOT NULL,
    model character varying(150) NOT NULL,
    is_validated boolean NOT NULL,
    digitization_id bigint
);


ALTER TABLE public.webapp_annotation OWNER TO salbouy;

--
-- Name: webapp_annotation_id_seq; Type: SEQUENCE; Schema: public; Owner: salbouy
--

CREATE SEQUENCE public.webapp_annotation_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.webapp_annotation_id_seq OWNER TO salbouy;

--
-- Name: webapp_annotation_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: salbouy
--

ALTER SEQUENCE public.webapp_annotation_id_seq OWNED BY public.webapp_annotation.id;


--
-- Name: webapp_conservationplace; Type: TABLE; Schema: public; Owner: salbouy
--

CREATE TABLE public.webapp_conservationplace (
    id bigint NOT NULL,
    name character varying(200) NOT NULL,
    license character varying(200),
    city_id bigint
);


ALTER TABLE public.webapp_conservationplace OWNER TO salbouy;

--
-- Name: webapp_conservationplace_id_seq; Type: SEQUENCE; Schema: public; Owner: salbouy
--

CREATE SEQUENCE public.webapp_conservationplace_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.webapp_conservationplace_id_seq OWNER TO salbouy;

--
-- Name: webapp_conservationplace_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: salbouy
--

ALTER SEQUENCE public.webapp_conservationplace_id_seq OWNED BY public.webapp_conservationplace.id;


--
-- Name: webapp_content; Type: TABLE; Schema: public; Owner: salbouy
--

CREATE TABLE public.webapp_content (
    id bigint NOT NULL,
    date_min integer,
    date_max integer,
    page_min character varying(15),
    page_max character varying(15),
    place_id bigint,
    witness_id bigint,
    work_id bigint
);


ALTER TABLE public.webapp_content OWNER TO salbouy;

--
-- Name: webapp_content_id_seq; Type: SEQUENCE; Schema: public; Owner: salbouy
--

CREATE SEQUENCE public.webapp_content_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.webapp_content_id_seq OWNER TO salbouy;

--
-- Name: webapp_content_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: salbouy
--

ALTER SEQUENCE public.webapp_content_id_seq OWNED BY public.webapp_content.id;


--
-- Name: webapp_content_lang; Type: TABLE; Schema: public; Owner: salbouy
--

CREATE TABLE public.webapp_content_lang (
    id bigint NOT NULL,
    content_id bigint NOT NULL,
    language_id bigint NOT NULL
);


ALTER TABLE public.webapp_content_lang OWNER TO salbouy;

--
-- Name: webapp_content_lang_id_seq; Type: SEQUENCE; Schema: public; Owner: salbouy
--

CREATE SEQUENCE public.webapp_content_lang_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.webapp_content_lang_id_seq OWNER TO salbouy;

--
-- Name: webapp_content_lang_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: salbouy
--

ALTER SEQUENCE public.webapp_content_lang_id_seq OWNED BY public.webapp_content_lang.id;


--
-- Name: webapp_content_tags; Type: TABLE; Schema: public; Owner: salbouy
--

CREATE TABLE public.webapp_content_tags (
    id bigint NOT NULL,
    content_id bigint NOT NULL,
    tag_id bigint NOT NULL
);


ALTER TABLE public.webapp_content_tags OWNER TO salbouy;

--
-- Name: webapp_content_tags_id_seq; Type: SEQUENCE; Schema: public; Owner: salbouy
--

CREATE SEQUENCE public.webapp_content_tags_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.webapp_content_tags_id_seq OWNER TO salbouy;

--
-- Name: webapp_content_tags_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: salbouy
--

ALTER SEQUENCE public.webapp_content_tags_id_seq OWNED BY public.webapp_content_tags.id;


--
-- Name: webapp_digitization; Type: TABLE; Schema: public; Owner: salbouy
--

CREATE TABLE public.webapp_digitization (
    id bigint NOT NULL,
    digit_type character varying(150) NOT NULL,
    license character varying(200),
    pdf character varying(100) NOT NULL,
    manifest character varying(200) NOT NULL,
    images character varying(100) NOT NULL,
    witness_id bigint NOT NULL,
    is_open boolean NOT NULL,
    source character varying(500)
);


ALTER TABLE public.webapp_digitization OWNER TO salbouy;

--
-- Name: webapp_digitization_id_seq; Type: SEQUENCE; Schema: public; Owner: salbouy
--

CREATE SEQUENCE public.webapp_digitization_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.webapp_digitization_id_seq OWNER TO salbouy;

--
-- Name: webapp_digitization_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: salbouy
--

ALTER SEQUENCE public.webapp_digitization_id_seq OWNED BY public.webapp_digitization.id;


--
-- Name: webapp_edition; Type: TABLE; Schema: public; Owner: salbouy
--

CREATE TABLE public.webapp_edition (
    id bigint NOT NULL,
    name character varying(500) NOT NULL,
    place_id bigint,
    publisher_id bigint
);


ALTER TABLE public.webapp_edition OWNER TO salbouy;

--
-- Name: webapp_edition_id_seq; Type: SEQUENCE; Schema: public; Owner: salbouy
--

CREATE SEQUENCE public.webapp_edition_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.webapp_edition_id_seq OWNER TO salbouy;

--
-- Name: webapp_edition_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: salbouy
--

ALTER SEQUENCE public.webapp_edition_id_seq OWNED BY public.webapp_edition.id;


--
-- Name: webapp_language; Type: TABLE; Schema: public; Owner: salbouy
--

CREATE TABLE public.webapp_language (
    id bigint NOT NULL,
    lang character varying(200) NOT NULL,
    code character varying(200) NOT NULL
);


ALTER TABLE public.webapp_language OWNER TO salbouy;

--
-- Name: webapp_language_id_seq; Type: SEQUENCE; Schema: public; Owner: salbouy
--

CREATE SEQUENCE public.webapp_language_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.webapp_language_id_seq OWNER TO salbouy;

--
-- Name: webapp_language_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: salbouy
--

ALTER SEQUENCE public.webapp_language_id_seq OWNED BY public.webapp_language.id;


--
-- Name: webapp_person; Type: TABLE; Schema: public; Owner: salbouy
--

CREATE TABLE public.webapp_person (
    id bigint NOT NULL,
    name character varying(200) NOT NULL,
    date_min integer,
    date_max integer
);


ALTER TABLE public.webapp_person OWNER TO salbouy;

--
-- Name: webapp_person_id_seq; Type: SEQUENCE; Schema: public; Owner: salbouy
--

CREATE SEQUENCE public.webapp_person_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.webapp_person_id_seq OWNER TO salbouy;

--
-- Name: webapp_person_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: salbouy
--

ALTER SEQUENCE public.webapp_person_id_seq OWNED BY public.webapp_person.id;


--
-- Name: webapp_place; Type: TABLE; Schema: public; Owner: salbouy
--

CREATE TABLE public.webapp_place (
    id bigint NOT NULL,
    name character varying(200) NOT NULL,
    country character varying(150) NOT NULL,
    latitude numeric(8,4),
    longitude numeric(8,4)
);


ALTER TABLE public.webapp_place OWNER TO salbouy;

--
-- Name: webapp_place_id_seq; Type: SEQUENCE; Schema: public; Owner: salbouy
--

CREATE SEQUENCE public.webapp_place_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.webapp_place_id_seq OWNER TO salbouy;

--
-- Name: webapp_place_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: salbouy
--

ALTER SEQUENCE public.webapp_place_id_seq OWNED BY public.webapp_place.id;


--
-- Name: webapp_role; Type: TABLE; Schema: public; Owner: salbouy
--

CREATE TABLE public.webapp_role (
    id bigint NOT NULL,
    role character varying(150) NOT NULL,
    content_id bigint,
    person_id bigint,
    series_id bigint
);


ALTER TABLE public.webapp_role OWNER TO salbouy;

--
-- Name: webapp_role_id_seq; Type: SEQUENCE; Schema: public; Owner: salbouy
--

CREATE SEQUENCE public.webapp_role_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.webapp_role_id_seq OWNER TO salbouy;

--
-- Name: webapp_role_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: salbouy
--

ALTER SEQUENCE public.webapp_role_id_seq OWNED BY public.webapp_role.id;


--
-- Name: webapp_series; Type: TABLE; Schema: public; Owner: salbouy
--

CREATE TABLE public.webapp_series (
    id bigint NOT NULL,
    notes text NOT NULL,
    date_min integer,
    date_max integer,
    is_public boolean NOT NULL,
    edition_id bigint,
    user_id integer,
    work_id bigint
);


ALTER TABLE public.webapp_series OWNER TO salbouy;

--
-- Name: webapp_series_id_seq; Type: SEQUENCE; Schema: public; Owner: salbouy
--

CREATE SEQUENCE public.webapp_series_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.webapp_series_id_seq OWNER TO salbouy;

--
-- Name: webapp_series_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: salbouy
--

ALTER SEQUENCE public.webapp_series_id_seq OWNED BY public.webapp_series.id;


--
-- Name: webapp_series_tags; Type: TABLE; Schema: public; Owner: salbouy
--

CREATE TABLE public.webapp_series_tags (
    id bigint NOT NULL,
    series_id bigint NOT NULL,
    tag_id bigint NOT NULL
);


ALTER TABLE public.webapp_series_tags OWNER TO salbouy;

--
-- Name: webapp_series_tags_id_seq; Type: SEQUENCE; Schema: public; Owner: salbouy
--

CREATE SEQUENCE public.webapp_series_tags_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.webapp_series_tags_id_seq OWNER TO salbouy;

--
-- Name: webapp_series_tags_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: salbouy
--

ALTER SEQUENCE public.webapp_series_tags_id_seq OWNED BY public.webapp_series_tags.id;


--
-- Name: webapp_tag; Type: TABLE; Schema: public; Owner: salbouy
--

CREATE TABLE public.webapp_tag (
    id bigint NOT NULL,
    label character varying(50) NOT NULL
);


ALTER TABLE public.webapp_tag OWNER TO salbouy;

--
-- Name: webapp_tag_id_seq; Type: SEQUENCE; Schema: public; Owner: salbouy
--

CREATE SEQUENCE public.webapp_tag_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.webapp_tag_id_seq OWNER TO salbouy;

--
-- Name: webapp_tag_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: salbouy
--

ALTER SEQUENCE public.webapp_tag_id_seq OWNED BY public.webapp_tag.id;


--
-- Name: webapp_witness; Type: TABLE; Schema: public; Owner: salbouy
--

CREATE TABLE public.webapp_witness (
    id bigint NOT NULL,
    type character varying(150) NOT NULL,
    id_nb character varying(150) NOT NULL,
    notes text NOT NULL,
    nb_pages integer,
    page_type character varying(150) NOT NULL,
    is_public boolean NOT NULL,
    link character varying(200) NOT NULL,
    slug character varying(600) NOT NULL,
    volume_title character varying(500),
    volume_nb integer,
    created_at timestamp with time zone,
    updated_at timestamp with time zone,
    edition_id bigint,
    place_id bigint,
    series_id bigint,
    user_id integer
);


ALTER TABLE public.webapp_witness OWNER TO salbouy;

--
-- Name: webapp_witness_id_seq; Type: SEQUENCE; Schema: public; Owner: salbouy
--

CREATE SEQUENCE public.webapp_witness_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.webapp_witness_id_seq OWNER TO salbouy;

--
-- Name: webapp_witness_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: salbouy
--

ALTER SEQUENCE public.webapp_witness_id_seq OWNED BY public.webapp_witness.id;


--
-- Name: webapp_work; Type: TABLE; Schema: public; Owner: salbouy
--

CREATE TABLE public.webapp_work (
    id bigint NOT NULL,
    title character varying(600) NOT NULL,
    date_min integer,
    date_max integer,
    notes text,
    author_id bigint,
    place_id bigint
);


ALTER TABLE public.webapp_work OWNER TO salbouy;

--
-- Name: webapp_work_id_seq; Type: SEQUENCE; Schema: public; Owner: salbouy
--

CREATE SEQUENCE public.webapp_work_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.webapp_work_id_seq OWNER TO salbouy;

--
-- Name: webapp_work_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: salbouy
--

ALTER SEQUENCE public.webapp_work_id_seq OWNED BY public.webapp_work.id;


--
-- Name: webapp_work_lang; Type: TABLE; Schema: public; Owner: salbouy
--

CREATE TABLE public.webapp_work_lang (
    id bigint NOT NULL,
    work_id bigint NOT NULL,
    language_id bigint NOT NULL
);


ALTER TABLE public.webapp_work_lang OWNER TO salbouy;

--
-- Name: webapp_work_lang_id_seq; Type: SEQUENCE; Schema: public; Owner: salbouy
--

CREATE SEQUENCE public.webapp_work_lang_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.webapp_work_lang_id_seq OWNER TO salbouy;

--
-- Name: webapp_work_lang_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: salbouy
--

ALTER SEQUENCE public.webapp_work_lang_id_seq OWNED BY public.webapp_work_lang.id;


--
-- Name: webapp_work_tags; Type: TABLE; Schema: public; Owner: salbouy
--

CREATE TABLE public.webapp_work_tags (
    id bigint NOT NULL,
    work_id bigint NOT NULL,
    tag_id bigint NOT NULL
);


ALTER TABLE public.webapp_work_tags OWNER TO salbouy;

--
-- Name: webapp_work_tags_id_seq; Type: SEQUENCE; Schema: public; Owner: salbouy
--

CREATE SEQUENCE public.webapp_work_tags_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.webapp_work_tags_id_seq OWNER TO salbouy;

--
-- Name: webapp_work_tags_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: salbouy
--

ALTER SEQUENCE public.webapp_work_tags_id_seq OWNED BY public.webapp_work_tags.id;


--
-- Name: auth_group id; Type: DEFAULT; Schema: public; Owner: salbouy
--

ALTER TABLE ONLY public.auth_group ALTER COLUMN id SET DEFAULT nextval('public.auth_group_id_seq'::regclass);


--
-- Name: auth_group_permissions id; Type: DEFAULT; Schema: public; Owner: salbouy
--

ALTER TABLE ONLY public.auth_group_permissions ALTER COLUMN id SET DEFAULT nextval('public.auth_group_permissions_id_seq'::regclass);


--
-- Name: auth_permission id; Type: DEFAULT; Schema: public; Owner: salbouy
--

ALTER TABLE ONLY public.auth_permission ALTER COLUMN id SET DEFAULT nextval('public.auth_permission_id_seq'::regclass);


--
-- Name: auth_user id; Type: DEFAULT; Schema: public; Owner: salbouy
--

ALTER TABLE ONLY public.auth_user ALTER COLUMN id SET DEFAULT nextval('public.auth_user_id_seq'::regclass);


--
-- Name: auth_user_groups id; Type: DEFAULT; Schema: public; Owner: salbouy
--

ALTER TABLE ONLY public.auth_user_groups ALTER COLUMN id SET DEFAULT nextval('public.auth_user_groups_id_seq'::regclass);


--
-- Name: auth_user_user_permissions id; Type: DEFAULT; Schema: public; Owner: salbouy
--

ALTER TABLE ONLY public.auth_user_user_permissions ALTER COLUMN id SET DEFAULT nextval('public.auth_user_user_permissions_id_seq'::regclass);


--
-- Name: django_admin_log id; Type: DEFAULT; Schema: public; Owner: salbouy
--

ALTER TABLE ONLY public.django_admin_log ALTER COLUMN id SET DEFAULT nextval('public.django_admin_log_id_seq'::regclass);


--
-- Name: django_content_type id; Type: DEFAULT; Schema: public; Owner: salbouy
--

ALTER TABLE ONLY public.django_content_type ALTER COLUMN id SET DEFAULT nextval('public.django_content_type_id_seq'::regclass);


--
-- Name: django_migrations id; Type: DEFAULT; Schema: public; Owner: salbouy
--

ALTER TABLE ONLY public.django_migrations ALTER COLUMN id SET DEFAULT nextval('public.django_migrations_id_seq'::regclass);


--
-- Name: webapp_annotation id; Type: DEFAULT; Schema: public; Owner: salbouy
--

ALTER TABLE ONLY public.webapp_annotation ALTER COLUMN id SET DEFAULT nextval('public.webapp_annotation_id_seq'::regclass);


--
-- Name: webapp_conservationplace id; Type: DEFAULT; Schema: public; Owner: salbouy
--

ALTER TABLE ONLY public.webapp_conservationplace ALTER COLUMN id SET DEFAULT nextval('public.webapp_conservationplace_id_seq'::regclass);


--
-- Name: webapp_content id; Type: DEFAULT; Schema: public; Owner: salbouy
--

ALTER TABLE ONLY public.webapp_content ALTER COLUMN id SET DEFAULT nextval('public.webapp_content_id_seq'::regclass);


--
-- Name: webapp_content_lang id; Type: DEFAULT; Schema: public; Owner: salbouy
--

ALTER TABLE ONLY public.webapp_content_lang ALTER COLUMN id SET DEFAULT nextval('public.webapp_content_lang_id_seq'::regclass);


--
-- Name: webapp_content_tags id; Type: DEFAULT; Schema: public; Owner: salbouy
--

ALTER TABLE ONLY public.webapp_content_tags ALTER COLUMN id SET DEFAULT nextval('public.webapp_content_tags_id_seq'::regclass);


--
-- Name: webapp_digitization id; Type: DEFAULT; Schema: public; Owner: salbouy
--

ALTER TABLE ONLY public.webapp_digitization ALTER COLUMN id SET DEFAULT nextval('public.webapp_digitization_id_seq'::regclass);


--
-- Name: webapp_edition id; Type: DEFAULT; Schema: public; Owner: salbouy
--

ALTER TABLE ONLY public.webapp_edition ALTER COLUMN id SET DEFAULT nextval('public.webapp_edition_id_seq'::regclass);


--
-- Name: webapp_language id; Type: DEFAULT; Schema: public; Owner: salbouy
--

ALTER TABLE ONLY public.webapp_language ALTER COLUMN id SET DEFAULT nextval('public.webapp_language_id_seq'::regclass);


--
-- Name: webapp_person id; Type: DEFAULT; Schema: public; Owner: salbouy
--

ALTER TABLE ONLY public.webapp_person ALTER COLUMN id SET DEFAULT nextval('public.webapp_person_id_seq'::regclass);


--
-- Name: webapp_place id; Type: DEFAULT; Schema: public; Owner: salbouy
--

ALTER TABLE ONLY public.webapp_place ALTER COLUMN id SET DEFAULT nextval('public.webapp_place_id_seq'::regclass);


--
-- Name: webapp_role id; Type: DEFAULT; Schema: public; Owner: salbouy
--

ALTER TABLE ONLY public.webapp_role ALTER COLUMN id SET DEFAULT nextval('public.webapp_role_id_seq'::regclass);


--
-- Name: webapp_series id; Type: DEFAULT; Schema: public; Owner: salbouy
--

ALTER TABLE ONLY public.webapp_series ALTER COLUMN id SET DEFAULT nextval('public.webapp_series_id_seq'::regclass);


--
-- Name: webapp_series_tags id; Type: DEFAULT; Schema: public; Owner: salbouy
--

ALTER TABLE ONLY public.webapp_series_tags ALTER COLUMN id SET DEFAULT nextval('public.webapp_series_tags_id_seq'::regclass);


--
-- Name: webapp_tag id; Type: DEFAULT; Schema: public; Owner: salbouy
--

ALTER TABLE ONLY public.webapp_tag ALTER COLUMN id SET DEFAULT nextval('public.webapp_tag_id_seq'::regclass);


--
-- Name: webapp_witness id; Type: DEFAULT; Schema: public; Owner: salbouy
--

ALTER TABLE ONLY public.webapp_witness ALTER COLUMN id SET DEFAULT nextval('public.webapp_witness_id_seq'::regclass);


--
-- Name: webapp_work id; Type: DEFAULT; Schema: public; Owner: salbouy
--

ALTER TABLE ONLY public.webapp_work ALTER COLUMN id SET DEFAULT nextval('public.webapp_work_id_seq'::regclass);


--
-- Name: webapp_work_lang id; Type: DEFAULT; Schema: public; Owner: salbouy
--

ALTER TABLE ONLY public.webapp_work_lang ALTER COLUMN id SET DEFAULT nextval('public.webapp_work_lang_id_seq'::regclass);


--
-- Name: webapp_work_tags id; Type: DEFAULT; Schema: public; Owner: salbouy
--

ALTER TABLE ONLY public.webapp_work_tags ALTER COLUMN id SET DEFAULT nextval('public.webapp_work_tags_id_seq'::regclass);


--
-- Data for Name: auth_group; Type: TABLE DATA; Schema: public; Owner: salbouy
--

COPY public.auth_group (id, name) FROM stdin;
1	user
\.


--
-- Data for Name: auth_group_permissions; Type: TABLE DATA; Schema: public; Owner: salbouy
--

COPY public.auth_group_permissions (id, group_id, permission_id) FROM stdin;
1	1	25
2	1	26
3	1	27
4	1	28
5	1	29
6	1	30
7	1	31
8	1	32
9	1	33
10	1	34
12	1	36
13	1	37
14	1	38
15	1	39
16	1	40
17	1	41
18	1	42
19	1	43
20	1	44
21	1	45
22	1	46
23	1	47
24	1	48
25	1	49
26	1	50
27	1	51
28	1	52
29	1	53
30	1	54
31	1	55
32	1	56
33	1	57
34	1	58
35	1	59
36	1	60
37	1	61
38	1	62
39	1	63
40	1	64
41	1	65
42	1	66
43	1	67
44	1	68
45	1	69
46	1	70
47	1	71
48	1	72
\.


--
-- Data for Name: auth_permission; Type: TABLE DATA; Schema: public; Owner: salbouy
--

COPY public.auth_permission (id, name, content_type_id, codename) FROM stdin;
1	Can add log entry	1	add_logentry
2	Can change log entry	1	change_logentry
3	Can delete log entry	1	delete_logentry
4	Can view log entry	1	view_logentry
5	Can add permission	2	add_permission
6	Can change permission	2	change_permission
7	Can delete permission	2	delete_permission
8	Can view permission	2	view_permission
9	Can add group	3	add_group
10	Can change group	3	change_group
11	Can delete group	3	delete_group
12	Can view group	3	view_group
13	Can add user	4	add_user
14	Can change user	4	change_user
15	Can delete user	4	delete_user
16	Can view user	4	view_user
17	Can add content type	5	add_contenttype
18	Can change content type	5	change_contenttype
19	Can delete content type	5	delete_contenttype
20	Can view content type	5	view_contenttype
21	Can add session	6	add_session
22	Can change session	6	change_session
23	Can delete session	6	delete_session
24	Can view session	6	view_session
25	Can add Conservation place	7	add_conservationplace
26	Can change Conservation place	7	change_conservationplace
27	Can delete Conservation place	7	delete_conservationplace
28	Can view Conservation place	7	view_conservationplace
29	Can add Content	8	add_content
30	Can change Content	8	change_content
31	Can delete Content	8	delete_content
32	Can view Content	8	view_content
33	Can add Edition	9	add_edition
34	Can change Edition	9	change_edition
35	Can delete Edition	9	delete_edition
36	Can view Edition	9	view_edition
37	Can add Language	10	add_language
38	Can change Language	10	change_language
39	Can delete Language	10	delete_language
40	Can view Language	10	view_language
41	Can add Historical actor	11	add_person
42	Can change Historical actor	11	change_person
43	Can delete Historical actor	11	delete_person
44	Can view Historical actor	11	view_person
45	Can add Place	12	add_place
46	Can change Place	12	change_place
47	Can delete Place	12	delete_place
48	Can view Place	12	view_place
49	Can add Series	13	add_series
50	Can change Series	13	change_series
51	Can delete Series	13	delete_series
52	Can view Series	13	view_series
53	Can add Tag	14	add_tag
54	Can change Tag	14	change_tag
55	Can delete Tag	14	delete_tag
56	Can view Tag	14	view_tag
57	Can add Work	15	add_work
58	Can change Work	15	change_work
59	Can delete Work	15	delete_work
60	Can view Work	15	view_work
61	Can add Witness	16	add_witness
62	Can change Witness	16	change_witness
63	Can delete Witness	16	delete_witness
64	Can view Witness	16	view_witness
65	Can add Role	17	add_role
66	Can change Role	17	change_role
67	Can delete Role	17	delete_role
68	Can view Role	17	view_role
69	Can add Digitization	18	add_digitization
70	Can change Digitization	18	change_digitization
71	Can delete Digitization	18	delete_digitization
72	Can view Digitization	18	view_digitization
73	Can add Annotation	19	add_annotation
74	Can change Annotation	19	change_annotation
75	Can delete Annotation	19	delete_annotation
76	Can view Annotation	19	view_annotation
\.


--
-- Data for Name: auth_user; Type: TABLE DATA; Schema: public; Owner: salbouy
--

COPY public.auth_user (id, password, last_login, is_superuser, username, first_name, last_name, email, is_staff, is_active, date_joined) FROM stdin;
25	pbkdf2_sha256$320000$LPqFgRn03RqJwPrqfPOS1K$ZqNCYphz6naJ1wXn4n2SL0VvRi3Xhsf40g47JsR1mzs=	2023-09-14 08:34:29+00	f	skalleli	Syrine	Kalleli	syrine.kalleli@ens-paris-saclay.fr	t	t	2023-07-24 07:31:15+00
19	pbkdf2_sha256$320000$KZUXnBftknv4DHdm0vNhog$Crrobhz4oU3054NpI8rjIJCxWkNftIQ1B7yXuDLvxGM=	\N	f	cmontelle	Clemency	Montelle	clemency.montelle@canterbury.ac.nz	t	t	2023-04-07 12:41:20+00
11	pbkdf2_sha256$320000$SBbe2C668RYhL1NxSBisjm$C/bzAwnTSpOJrkze38onsvfHHzvFVk9KoiatdJ4GBNA=	2023-11-24 15:13:39+00	f	strigg	Scott	Trigg	scott.trigg@obspm.fr	t	t	2023-03-06 10:39:30+00
12	pbkdf2_sha256$320000$ZbP1SbtnV0IKxxg8OCppVi$6dpernAt7P4+eARWhI+/ktizNAEdrlZ9hXomRhzD2K4=	2023-12-02 10:08:09+00	f	szieme	Stefan	Zieme	stefan.zieme@hu-berlin.de	t	t	2023-03-20 08:51:31+00
2	pbkdf2_sha256$320000$2HOjorIFvKI7TGhCjAzGv0$jyi2slEsJJfmW+j+Ma9z3RYDNDWSuNAfEeQa1t8HoZQ=	\N	t	eida	Ségolène	Albouy	segolene.albouy@obspm.fr	t	t	2023-02-17 14:14:54+00
5	pbkdf2_sha256$320000$7eiwzJoz78uG3aUxy5GDE0$r95PWWISpEhLWQBoaAN6wN3BrmqHsyl8IeunkMew0Xc=	2023-11-29 13:34:21+00	f	dmanolova	Divna	Manolova	manolova.divna@gmail.com	t	t	2023-02-24 08:41:32+00
4	pbkdf2_sha256$320000$r3AaqZrdmw7sII1YJRVSHe$MhIVi2hnsagUR7BMzRsx/90sk/+OAzTgZrFV6kXGaYA=	2023-12-05 09:14:15.526124+00	f	faouinti	Fouad	Aouinti	aouinti.fouad@gmail.com	t	t	2023-02-23 08:20:29+00
22	pbkdf2_sha256$320000$XvgaJ299w7p2yNrKQcsVqN$QfGa2u4gCp+Um3n8Q9IrY4V3IEAwIrksXdGgEEZYxR0=	2023-07-09 04:59:19+00	f	jrodriguez	Josefina	Rodriguez Arribas	rodriguezarribas@gmail.com	t	t	2023-04-21 07:08:43+00
13	pbkdf2_sha256$320000$fubD9BJPUBhr0RzSyAWKRq$fVZqpQAonaiIlBE1EgFx7dmhiEehMnVk91XcNZmkJC8=	2023-03-21 13:23:26+00	f	gloizelet	Guillaume	Loizelet	gloizelet@gmail.com	t	t	2023-03-21 08:48:33+00
21	pbkdf2_sha256$320000$dS7bjpVm3obqGnFe58wSe2$Kovb3zBpQfGOI6UsFeqXNFl07p3ST7b6oJE8PN/CnMc=	\N	f	liliang	Liang	Li	liliang@ihns.ac.cn	t	t	2023-04-07 13:26:46+00
14	pbkdf2_sha256$320000$iIY1tBFzS4X4REowlFM5ME$qjjwSqbGfVNNVkrJha8rCOeJGHYG36O1wgbYTHalNNk=	2023-09-21 07:08:48+00	f	maubry	Mathieu	Aubry	mathieu.aubry.2006@polytechnique.org	t	t	2023-03-29 07:22:54+00
3	pbkdf2_sha256$320000$k7pE9GoKiizTYjHVqj7m7C$cOVKVyliiDW/utegHNcnmOj0egNeugvPRMhh69UwYYQ=	2023-11-23 10:53:25+00	f	mhusson	Matthieu	Husson	hussonmatthieu@gmail.com	t	t	2023-02-20 13:09:16+00
6	pbkdf2_sha256$320000$1JLnzTdFclLJs7WW8s4Imj$4jH1OSERy350rh8GmBU4bPPA9HQikz9zuw2qaktA4t8=	2023-07-10 08:25:01+00	f	ajmisra	Anuj	Misra	anuj.misra@gmail.com	t	t	2023-02-24 08:43:48+00
27	pbkdf2_sha256$320000$HY54asQvGzReOgUcufkSKw$6mgg2+9c+ACyQCAx8M0DCyiBWZYRGCoxocv5G6WP0C8=	\N	f	alfareferee	ALFA	Referee		t	t	2023-10-27 12:35:58+00
28	pbkdf2_sha256$320000$7A86mOteHxap5GV4LkNqeo$9698oazFAGSXMtTBHh/KgjeDHOtvnGKvUEFU5t0OMtk=	2023-11-03 11:37:12+00	f	mzilaf	Manelle	Zilaf	manelle.zilaf@psl.eu	t	t	2023-11-03 09:09:43+00
29	pbkdf2_sha256$320000$lxX0M5bkx51VW8Y9WVutZw$ybnw+Ve8/xrwpiPxEYWw3zaIrPFFCKC7gVZugGHK0Sc=	2023-11-10 09:56:18+00	f	awerlen	Alexandre	Werlen	alexandre.werlen@psl.eu	t	t	2023-11-03 09:11:55+00
26	pbkdf2_sha256$320000$r4cGwW83utsS5G6ubsjMC9$OA2x16Z7aHaa6NxLwFex9UAgoD1Yt2y2rUlUSjjmSg8=	2023-10-17 10:11:08+00	f	ccarman	Christián Carlos	Carman	ccarman@gmail.com	t	t	2023-10-13 13:29:18+00
8	pbkdf2_sha256$320000$mG6yLQu9SVJbx6tYp8D0Kx$h96AWbPZEFhqeV2rQFYzrYypCuTIfS0i1oT1gUGa0/Q=	2023-11-26 10:57:24+00	f	sgessner	Samuel	Gessner	samuel.gessner@gmail.com	t	t	2023-02-27 08:53:15+00
9	pbkdf2_sha256$320000$GyT62VU60DhC6yNgk5Zs3p$RcRDpTFKEslmdRKwuykUMU9nmxN9bQyGgee8CLIeTVI=	2023-05-25 10:34:50+00	f	ccullen	Christopher	Cullen	cc433@cam.ac.uk	t	t	2023-02-27 16:18:43+00
18	pbkdf2_sha256$320000$WMzdAh5bvsds2MRLSwoVYk$QzQH4Y6K3QY0wWmVM1udqjTabqcS6NEnG0pgYgj2xcc=	2023-10-17 10:13:05+00	f	hbohloul	Hamid	Bohloul	bohlulh@gmail.com	t	t	2023-04-07 10:48:51+00
20	pbkdf2_sha256$320000$lHGLaNk5s5oLTjgswOLBxJ$uWuKVBybzuJQHpWebH0Stipbgkf3ULuBwvh5JqcLzTg=	2023-04-07 13:46:34+00	f	shiyunli	Yunli	Shi	ylshi@ustc.edu.cn	t	t	2023-04-07 13:25:52+00
24	pbkdf2_sha256$320000$Zllvi0ROcctjIl8eStawZk$vZkMluGVGo6vPAPaGJdkhIcMMpq+0vRy9hZzZBgSr+s=	2023-06-26 13:27:00+00	f	iskoura	Ioanna	Skoura	iskoura3@gmail.com	t	t	2023-06-23 14:46:14+00
16	pbkdf2_sha256$320000$7nz7LTrJFvbSWkhnzyI2cr$GrKZ/gTJC1TNvxIPAbYUoou52isg0jY2dzhW8yVKe+0=	2023-11-28 20:30:58+00	f	jchen	Chen	Ji	xmchenji@ustc.edu.cn	t	t	2023-04-04 07:58:57+00
17	pbkdf2_sha256$320000$NiTJnMPtds35XsVAF5REyf$QNLTA33QFVQ8nl3ZbCrjkPk1RyhKa21bPUGOVW4PeDQ=	2023-04-05 22:29:06+00	f	sjohnson	Stephen	Johnson	stephen.johnston@hsm.ox.ac.uk	t	t	2023-04-04 14:52:35+00
23	pbkdf2_sha256$320000$f1owbRLVdOYTMDsgOCnzMO$Verx1ggY6B2u/7S5YStr9P2VOHkDe7EKgefovQ6tngY=	2023-06-20 12:07:05+00	f	jlebois	Jil	Le Bois	jil.lebois.hagmann@gmail.com	t	t	2023-06-06 08:07:33+00
10	pbkdf2_sha256$320000$qwjNt5cnL0ktJObn2aG0RJ$dkyGDk7/ROV+/9FrXQo20X9Lsc5Oo+2+psOV2dToxWg=	2023-06-19 13:29:34+00	f	cjami	Catherine	Jami	catherine.jami@ehess.fr	t	t	2023-02-27 16:22:43+00
15	pbkdf2_sha256$320000$CS2RM0KHmKghJLw3ZWjSHo$pHVupw1hYyIOYoSYYbpwOVdh4muH7ajOjbgh1LAfqZ4=	2023-11-23 08:24:14.339589+00	t	jnorindr	Jade	Norindr	jade.norindr@gmail.com	t	t	2023-03-29 07:25:01+00
1	pbkdf2_sha256$320000$tHn2ZK0wJH9iSrIi3cZEVN$XsUMhR7vvoCorxgnSVPSFjSuqLPH/1ZibP8iP3NBUr8=	2023-12-06 09:11:24.667574+00	t	admin	Admin	Syrte	netadmin.syrte@obspm.fr	t	t	2023-02-09 15:15:07+00
\.


--
-- Data for Name: auth_user_groups; Type: TABLE DATA; Schema: public; Owner: salbouy
--

COPY public.auth_user_groups (id, user_id, group_id) FROM stdin;
1	6	1
3	2	1
12	15	1
\.


--
-- Data for Name: auth_user_user_permissions; Type: TABLE DATA; Schema: public; Owner: salbouy
--

COPY public.auth_user_user_permissions (id, user_id, permission_id) FROM stdin;
121	11	25
122	11	26
123	11	27
124	11	28
125	11	29
126	11	30
127	11	31
128	11	32
129	11	33
130	11	34
131	11	35
132	11	36
133	11	37
134	11	38
135	11	39
136	11	40
137	11	41
138	11	42
139	11	43
140	11	44
141	11	45
142	11	46
143	11	47
144	11	48
145	11	49
146	11	50
147	11	51
148	11	52
149	11	53
150	11	54
151	11	55
152	11	56
153	11	57
154	11	58
155	11	59
156	11	60
157	11	61
158	11	62
159	11	63
160	11	64
161	11	65
162	11	66
163	11	67
164	11	68
165	11	69
166	11	70
167	11	71
168	11	72
169	1	1
170	1	2
171	1	3
172	1	4
173	1	5
174	1	6
175	1	7
176	1	8
177	1	9
178	1	10
179	1	11
180	1	12
181	1	13
182	1	14
183	1	15
184	1	16
185	1	17
186	1	18
187	1	19
188	1	20
189	1	21
190	1	22
191	1	23
192	1	24
193	1	25
194	1	26
195	1	27
196	1	28
197	1	29
198	1	30
199	1	31
200	1	32
201	1	33
202	1	34
203	1	35
204	1	36
205	1	37
206	1	38
207	1	39
208	1	40
209	1	41
210	1	42
211	1	43
212	1	44
213	1	45
214	1	46
215	1	47
216	1	48
217	1	49
218	1	50
219	1	51
220	1	52
221	1	53
222	1	54
223	1	55
224	1	56
225	1	57
226	1	58
227	1	59
228	1	60
229	1	61
230	1	62
231	1	63
232	1	64
233	1	65
234	1	66
235	1	67
236	1	68
237	1	69
238	1	70
239	1	71
240	1	72
241	11	16
242	11	13
243	11	14
244	11	15
\.


--
-- Data for Name: django_admin_log; Type: TABLE DATA; Schema: public; Owner: salbouy
--

COPY public.django_admin_log (id, action_time, object_id, object_repr, action_flag, change_message, content_type_id, user_id) FROM stdin;
68	2023-12-06 13:24:27.051843+00	2	Biblioteca Medicea Laurenziana | O II 10	2	[{"added": {"name": "Digitization", "object": "image #2: Biblioteca Medicea Laurenziana | O II 10"}}]	16	1
\.


--
-- Data for Name: django_content_type; Type: TABLE DATA; Schema: public; Owner: salbouy
--

COPY public.django_content_type (id, app_label, model) FROM stdin;
1	admin	logentry
2	auth	permission
3	auth	group
4	auth	user
5	contenttypes	contenttype
6	sessions	session
7	webapp	conservationplace
8	webapp	content
9	webapp	edition
10	webapp	language
11	webapp	person
12	webapp	place
13	webapp	series
14	webapp	tag
15	webapp	work
16	webapp	witness
17	webapp	role
18	webapp	digitization
19	webapp	annotation
\.


--
-- Data for Name: django_migrations; Type: TABLE DATA; Schema: public; Owner: salbouy
--

COPY public.django_migrations (id, app, name, applied) FROM stdin;
1	contenttypes	0001_initial	2023-12-04 15:22:53.469621+00
2	auth	0001_initial	2023-12-04 15:22:53.718542+00
3	admin	0001_initial	2023-12-04 15:22:53.774467+00
4	admin	0002_logentry_remove_auto_add	2023-12-04 15:22:53.788312+00
5	admin	0003_logentry_add_action_flag_choices	2023-12-04 15:22:53.804019+00
6	contenttypes	0002_remove_content_type_name	2023-12-04 15:22:53.835934+00
7	auth	0002_alter_permission_name_max_length	2023-12-04 15:22:53.848044+00
8	auth	0003_alter_user_email_max_length	2023-12-04 15:22:53.863348+00
9	auth	0004_alter_user_username_opts	2023-12-04 15:22:53.878624+00
10	auth	0005_alter_user_last_login_null	2023-12-04 15:22:53.89233+00
11	auth	0006_require_contenttypes_0002	2023-12-04 15:22:53.899768+00
12	auth	0007_alter_validators_add_error_messages	2023-12-04 15:22:53.916319+00
13	auth	0008_alter_user_username_max_length	2023-12-04 15:22:53.942657+00
14	auth	0009_alter_user_last_name_max_length	2023-12-04 15:22:53.958655+00
15	auth	0010_alter_group_name_max_length	2023-12-04 15:22:53.975413+00
16	auth	0011_update_proxy_permissions	2023-12-04 15:22:53.990116+00
17	auth	0012_alter_user_first_name_max_length	2023-12-04 15:22:54.004575+00
18	sessions	0001_initial	2023-12-04 15:22:54.076172+00
19	webapp	0001_initial	2023-12-04 15:22:55.422475+00
20	webapp	0002_alter_conservationplace_name	2023-12-06 10:11:41.115822+00
21	webapp	0003_digitization_is_open_digitization_source_and_more	2023-12-06 10:11:41.153933+00
\.


--
-- Data for Name: django_session; Type: TABLE DATA; Schema: public; Owner: salbouy
--

COPY public.django_session (session_key, session_data, expire_date) FROM stdin;
dqp7bz7mf2uljjne57jjm2ni0psegmp2	.eJxVjMsOwiAQRf-FtSFSHlNcuvcbyACDVA0kpV0Z_11IutDVTc45uW_mcN-y2xutbonswgQ7_TKP4UlliPjAcq881LKti-cj4Ydt_FYjva5H-3eQseVxa9PZkklq9hC1ClYbDzMK2ekEZtJeSGMjQRdaKqAICKavV0JhIvb5AsVONzs:1rABJe:W2w7IUe_SnzeqIdKhmBaBEoF_va9-abYyYvQMqAfTWc	2023-12-18 15:57:02.6232+00
9cihxoujov7o62hq5b0ewdpdoqwve19u	.eJxVjDsOwjAQBe_iGllOHP8o6TmDtetd4wCypTipEHeHSCmgfTPzXiLCtpa4dV7iTOIsBnH63RDSg-sO6A711mRqdV1mlLsiD9rltRE_L4f7d1Cgl2-dA0LInL0N05jsaJ0GrVIgZSbOxg0UdEAy6Axb0KgsOwDIpNl7VFq8P_Q0OHU:1rAnwC:gB7NgihabCehEHcJdEAF43V55JGHNxIP0rCt59-jlTI	2023-12-20 09:11:24.82609+00
\.


--
-- Data for Name: webapp_annotation; Type: TABLE DATA; Schema: public; Owner: salbouy
--

COPY public.webapp_annotation (id, model, is_validated, digitization_id) FROM stdin;
2	CHANGE THIS VALUE	f	2
3	CHANGE THIS VALUE	f	3
4	CHANGE THIS VALUE	f	4
5	CHANGE THIS VALUE	f	5
6	CHANGE THIS VALUE	f	6
8	CHANGE THIS VALUE	f	8
9	CHANGE THIS VALUE	f	9
10	CHANGE THIS VALUE	f	10
11	CHANGE THIS VALUE	f	11
12	CHANGE THIS VALUE	f	12
13	CHANGE THIS VALUE	f	13
14	CHANGE THIS VALUE	f	14
15	CHANGE THIS VALUE	f	15
16	CHANGE THIS VALUE	f	16
17	CHANGE THIS VALUE	f	17
18	CHANGE THIS VALUE	f	18
19	CHANGE THIS VALUE	f	19
20	CHANGE THIS VALUE	f	20
21	CHANGE THIS VALUE	f	21
22	CHANGE THIS VALUE	f	22
23	CHANGE THIS VALUE	f	23
24	CHANGE THIS VALUE	f	24
25	CHANGE THIS VALUE	f	25
26	CHANGE THIS VALUE	f	26
27	CHANGE THIS VALUE	f	27
28	CHANGE THIS VALUE	f	28
29	CHANGE THIS VALUE	f	29
30	CHANGE THIS VALUE	f	30
31	CHANGE THIS VALUE	f	31
32	CHANGE THIS VALUE	f	32
33	CHANGE THIS VALUE	f	33
34	CHANGE THIS VALUE	f	34
35	CHANGE THIS VALUE	f	35
36	CHANGE THIS VALUE	f	36
37	CHANGE THIS VALUE	f	37
38	CHANGE THIS VALUE	f	38
39	CHANGE THIS VALUE	f	39
40	CHANGE THIS VALUE	f	40
41	CHANGE THIS VALUE	f	41
42	CHANGE THIS VALUE	f	42
44	CHANGE THIS VALUE	f	44
45	CHANGE THIS VALUE	f	45
46	CHANGE THIS VALUE	f	46
47	CHANGE THIS VALUE	f	47
48	CHANGE THIS VALUE	f	48
49	CHANGE THIS VALUE	f	49
50	CHANGE THIS VALUE	f	50
51	CHANGE THIS VALUE	f	51
52	CHANGE THIS VALUE	f	52
53	CHANGE THIS VALUE	f	53
54	CHANGE THIS VALUE	f	54
55	CHANGE THIS VALUE	f	55
56	CHANGE THIS VALUE	f	56
57	CHANGE THIS VALUE	f	57
58	CHANGE THIS VALUE	f	58
59	CHANGE THIS VALUE	f	59
60	CHANGE THIS VALUE	f	60
61	CHANGE THIS VALUE	f	61
62	CHANGE THIS VALUE	f	62
63	CHANGE THIS VALUE	f	63
64	CHANGE THIS VALUE	f	64
65	CHANGE THIS VALUE	f	65
66	CHANGE THIS VALUE	f	66
67	CHANGE THIS VALUE	f	67
68	CHANGE THIS VALUE	f	68
69	CHANGE THIS VALUE	f	69
70	CHANGE THIS VALUE	f	70
71	CHANGE THIS VALUE	f	71
72	CHANGE THIS VALUE	f	72
73	CHANGE THIS VALUE	f	73
74	CHANGE THIS VALUE	f	74
75	CHANGE THIS VALUE	f	75
76	CHANGE THIS VALUE	f	76
77	CHANGE THIS VALUE	f	77
78	CHANGE THIS VALUE	f	78
79	CHANGE THIS VALUE	f	79
80	CHANGE THIS VALUE	f	80
81	CHANGE THIS VALUE	f	81
82	CHANGE THIS VALUE	f	82
83	CHANGE THIS VALUE	f	83
84	CHANGE THIS VALUE	f	84
85	CHANGE THIS VALUE	f	85
86	CHANGE THIS VALUE	f	86
87	CHANGE THIS VALUE	f	87
88	CHANGE THIS VALUE	f	88
89	CHANGE THIS VALUE	f	89
90	CHANGE THIS VALUE	f	90
91	CHANGE THIS VALUE	f	91
92	CHANGE THIS VALUE	f	92
93	CHANGE THIS VALUE	f	93
94	CHANGE THIS VALUE	f	94
95	CHANGE THIS VALUE	f	95
96	CHANGE THIS VALUE	f	96
97	CHANGE THIS VALUE	f	97
98	CHANGE THIS VALUE	f	98
99	CHANGE THIS VALUE	f	99
100	CHANGE THIS VALUE	f	100
101	CHANGE THIS VALUE	f	101
102	CHANGE THIS VALUE	f	102
103	CHANGE THIS VALUE	f	103
104	CHANGE THIS VALUE	f	104
105	CHANGE THIS VALUE	f	105
106	CHANGE THIS VALUE	f	106
107	CHANGE THIS VALUE	f	107
108	CHANGE THIS VALUE	f	108
109	CHANGE THIS VALUE	f	109
110	CHANGE THIS VALUE	f	110
111	CHANGE THIS VALUE	f	111
112	CHANGE THIS VALUE	f	112
113	CHANGE THIS VALUE	f	113
114	CHANGE THIS VALUE	f	114
115	CHANGE THIS VALUE	f	115
116	CHANGE THIS VALUE	f	116
117	CHANGE THIS VALUE	f	117
118	CHANGE THIS VALUE	f	118
119	CHANGE THIS VALUE	f	119
120	CHANGE THIS VALUE	f	120
121	CHANGE THIS VALUE	f	121
122	CHANGE THIS VALUE	f	122
123	CHANGE THIS VALUE	f	123
124	CHANGE THIS VALUE	f	124
125	CHANGE THIS VALUE	f	125
126	CHANGE THIS VALUE	f	126
127	CHANGE THIS VALUE	f	127
128	CHANGE THIS VALUE	f	128
129	CHANGE THIS VALUE	f	129
130	CHANGE THIS VALUE	f	130
131	CHANGE THIS VALUE	f	131
132	CHANGE THIS VALUE	f	132
133	CHANGE THIS VALUE	f	133
134	CHANGE THIS VALUE	f	134
135	CHANGE THIS VALUE	f	135
137	CHANGE THIS VALUE	f	137
138	CHANGE THIS VALUE	f	138
139	CHANGE THIS VALUE	f	139
140	CHANGE THIS VALUE	f	140
141	CHANGE THIS VALUE	f	141
142	CHANGE THIS VALUE	f	142
143	CHANGE THIS VALUE	f	143
144	CHANGE THIS VALUE	f	144
145	CHANGE THIS VALUE	f	145
146	CHANGE THIS VALUE	f	146
147	CHANGE THIS VALUE	f	147
148	CHANGE THIS VALUE	f	148
149	CHANGE THIS VALUE	f	149
150	CHANGE THIS VALUE	f	150
151	CHANGE THIS VALUE	f	151
152	CHANGE THIS VALUE	f	152
153	CHANGE THIS VALUE	f	153
154	CHANGE THIS VALUE	f	154
155	CHANGE THIS VALUE	f	155
156	CHANGE THIS VALUE	f	156
157	CHANGE THIS VALUE	f	157
158	CHANGE THIS VALUE	f	158
162	CHANGE THIS VALUE	f	162
163	CHANGE THIS VALUE	f	163
164	CHANGE THIS VALUE	f	164
165	CHANGE THIS VALUE	f	165
166	CHANGE THIS VALUE	f	166
167	CHANGE THIS VALUE	f	167
168	CHANGE THIS VALUE	f	168
169	CHANGE THIS VALUE	f	169
170	CHANGE THIS VALUE	f	170
171	CHANGE THIS VALUE	f	171
172	CHANGE THIS VALUE	f	172
\.


--
-- Data for Name: webapp_conservationplace; Type: TABLE DATA; Schema: public; Owner: salbouy
--

COPY public.webapp_conservationplace (id, name, license, city_id) FROM stdin;
1	Bibliothèque nationale de France	\N	1
2	National Library (Milli Kütüphane)	\N	2
3	Bibliothèque municipale	\N	3
4	Universitätsbibliothek	\N	4
5	Bhandarkar Oriental Research Institute	\N	6
6	Sächsische Landesbibliothek - Staats- und Universitätsbibliothek	\N	7
7	Biblioteca del Monasterio de El Escorial	\N	8
8	Biblioteca Medicea Laurenziana	\N	9
9	Gurukul Kangri Haridwar Collection	\N	10
10	Houghton Library	\N	11
11	Millet Library	\N	12
12	Süleymaniye Library	\N	12
13	Topkapı Palace Museum	\N	12
14	Badische Landesbibliothek	\N	13
15	Bibliotheek der Rijksuniversiteit	\N	14
16	University Library	\N	14
17	British Library	\N	15
18	Astan-i Quds Library	\N	16
19	Cushing/Whitney Medical Library	\N	17
20	State Library of Victoria	\N	18
21	Bayerische Staatsbibliothek	\N	19
22	Biblioteca nazionale	\N	20
23	Bibliothèque interuniversitaire de la Sorbonne	\N	1
24	Bibliothèque Mazarine	\N	1
25	Poona Mandlik Jyotish	\N	\N
26	Rajasthan Oriental Research Institute	\N	21
27	Casanatense	\N	22
28	Scindia Oriental Institute	\N	23
29	Shri Raghunath Sanskrit Research Institute	\N	24
30	Majlis Library	\N	25
31	Malek National Library	\N	25
32	Sipahsalar Library	\N	25
33	Unknown	\N	\N
34	Biblioteca Apostolica Vaticana	\N	26
35	Österreichische Nationalbibliothek	\N	27
\.


--
-- Data for Name: webapp_content; Type: TABLE DATA; Schema: public; Owner: salbouy
--

COPY public.webapp_content (id, date_min, date_max, page_min, page_max, place_id, witness_id, work_id) FROM stdin;
\.


--
-- Data for Name: webapp_content_lang; Type: TABLE DATA; Schema: public; Owner: salbouy
--

COPY public.webapp_content_lang (id, content_id, language_id) FROM stdin;
\.


--
-- Data for Name: webapp_content_tags; Type: TABLE DATA; Schema: public; Owner: salbouy
--

COPY public.webapp_content_tags (id, content_id, tag_id) FROM stdin;
\.


--
-- Data for Name: webapp_digitization; Type: TABLE DATA; Schema: public; Owner: salbouy
--

COPY public.webapp_digitization (id, digit_type, license, pdf, manifest, images, witness_id, is_open, source) FROM stdin;
2	img	\N			auto_upload.jpg	2	f	\N
3	img	\N			auto_upload.jpg	3	f	\N
4	img	\N			auto_upload.jpg	4	f	\N
5	img	\N			auto_upload.jpg	5	f	\N
6	img	\N			auto_upload.jpg	6	f	\N
8	img	\N			auto_upload.jpg	8	f	\N
9	img	\N			auto_upload.jpg	9	f	\N
10	img	\N			auto_upload.jpg	10	f	\N
11	img	\N			auto_upload.jpg	11	f	\N
12	img	\N			auto_upload.jpg	12	f	\N
13	img	\N			auto_upload.jpg	13	f	\N
14	img	\N			auto_upload.jpg	14	f	\N
15	img	\N			auto_upload.jpg	15	f	\N
16	img	\N			auto_upload.jpg	16	f	\N
17	img	\N			auto_upload.jpg	17	f	\N
18	img	\N			auto_upload.jpg	18	f	\N
19	img	\N			auto_upload.jpg	19	f	\N
20	img	\N			auto_upload.jpg	20	f	\N
21	img	\N			auto_upload.jpg	21	f	\N
22	img	\N			auto_upload.jpg	22	f	\N
23	img	\N			auto_upload.jpg	23	f	\N
24	img	\N			auto_upload.jpg	24	f	\N
25	img	\N			auto_upload.jpg	25	f	\N
26	img	\N			auto_upload.jpg	26	f	\N
27	img	\N			auto_upload.jpg	27	f	\N
28	img	\N			auto_upload.jpg	28	f	\N
29	img	\N			auto_upload.jpg	29	f	\N
30	img	\N			auto_upload.jpg	30	f	\N
31	img	\N			auto_upload.jpg	31	f	\N
32	img	\N			auto_upload.jpg	32	f	\N
33	img	\N			auto_upload.jpg	33	f	\N
34	img	\N			auto_upload.jpg	34	f	\N
35	img	\N			auto_upload.jpg	35	f	\N
36	img	\N			auto_upload.jpg	36	f	\N
37	img	\N			auto_upload.jpg	37	f	\N
38	img	\N			auto_upload.jpg	38	f	\N
39	img	\N			auto_upload.jpg	39	f	\N
40	img	\N			auto_upload.jpg	40	f	\N
41	img	\N			auto_upload.jpg	41	f	\N
42	img	\N			auto_upload.jpg	42	f	\N
44	img	\N			auto_upload.jpg	44	f	\N
45	img	\N			auto_upload.jpg	45	f	\N
46	img	\N			auto_upload.jpg	46	f	\N
47	img	\N			auto_upload.jpg	47	f	\N
48	img	\N			auto_upload.jpg	48	f	\N
49	img	\N			auto_upload.jpg	49	f	\N
50	img	\N			auto_upload.jpg	50	f	\N
51	img	\N			auto_upload.jpg	51	f	\N
52	img	\N			auto_upload.jpg	52	f	\N
53	img	\N			auto_upload.jpg	53	f	\N
54	img	\N			auto_upload.jpg	54	f	\N
55	img	\N			auto_upload.jpg	55	f	\N
56	img	\N			auto_upload.jpg	56	f	\N
57	img	\N			auto_upload.jpg	57	f	\N
58	img	\N			auto_upload.jpg	58	f	\N
59	img	\N			auto_upload.jpg	59	f	\N
60	img	\N			auto_upload.jpg	60	f	\N
61	img	\N			auto_upload.jpg	61	f	\N
62	img	\N			auto_upload.jpg	62	f	\N
63	img	\N			auto_upload.jpg	63	f	\N
64	img	\N			auto_upload.jpg	64	f	\N
65	img	\N			auto_upload.jpg	65	f	\N
66	img	\N			auto_upload.jpg	66	f	\N
67	img	\N			auto_upload.jpg	67	f	\N
68	img	\N			auto_upload.jpg	68	f	\N
69	img	\N			auto_upload.jpg	69	f	\N
70	img	\N			auto_upload.jpg	70	f	\N
71	img	\N			auto_upload.jpg	71	f	\N
72	img	\N			auto_upload.jpg	72	f	\N
73	img	\N			auto_upload.jpg	73	f	\N
74	img	\N			auto_upload.jpg	74	f	\N
75	img	\N			auto_upload.jpg	75	f	\N
76	img	\N			auto_upload.jpg	76	f	\N
77	img	\N			auto_upload.jpg	77	f	\N
78	img	\N			auto_upload.jpg	78	f	\N
79	img	\N			auto_upload.jpg	79	f	\N
80	img	\N			auto_upload.jpg	80	f	\N
81	img	\N			auto_upload.jpg	81	f	\N
82	img	\N			auto_upload.jpg	82	f	\N
83	img	\N			auto_upload.jpg	83	f	\N
84	img	\N			auto_upload.jpg	84	f	\N
85	img	\N			auto_upload.jpg	85	f	\N
86	img	\N			auto_upload.jpg	86	f	\N
87	img	\N			auto_upload.jpg	87	f	\N
88	img	\N			auto_upload.jpg	88	f	\N
89	img	\N			auto_upload.jpg	89	f	\N
90	img	\N			auto_upload.jpg	90	f	\N
91	img	\N			auto_upload.jpg	91	f	\N
92	img	\N			auto_upload.jpg	92	f	\N
93	img	\N			auto_upload.jpg	93	f	\N
94	img	\N			auto_upload.jpg	94	f	\N
95	img	\N			auto_upload.jpg	95	f	\N
96	img	\N			auto_upload.jpg	96	f	\N
97	img	\N			auto_upload.jpg	97	f	\N
98	img	\N			auto_upload.jpg	98	f	\N
99	img	\N			auto_upload.jpg	99	f	\N
100	img	\N			auto_upload.jpg	100	f	\N
101	img	\N			auto_upload.jpg	101	f	\N
102	img	\N			auto_upload.jpg	102	f	\N
103	img	\N			auto_upload.jpg	103	f	\N
104	img	\N			auto_upload.jpg	104	f	\N
105	img	\N			auto_upload.jpg	105	f	\N
106	img	\N			auto_upload.jpg	106	f	\N
107	img	\N			auto_upload.jpg	107	f	\N
108	img	\N			auto_upload.jpg	108	f	\N
109	img	\N			auto_upload.jpg	109	f	\N
110	img	\N			auto_upload.jpg	110	f	\N
111	img	\N			auto_upload.jpg	111	f	\N
112	img	\N			auto_upload.jpg	112	f	\N
113	img	\N			auto_upload.jpg	113	f	\N
114	img	\N			auto_upload.jpg	114	f	\N
115	img	\N			auto_upload.jpg	115	f	\N
116	img	\N			auto_upload.jpg	116	f	\N
117	img	\N			auto_upload.jpg	117	f	\N
118	img	\N			auto_upload.jpg	118	f	\N
119	img	\N			auto_upload.jpg	119	f	\N
120	img	\N			auto_upload.jpg	120	f	\N
121	img	\N			auto_upload.jpg	121	f	\N
122	img	\N			auto_upload.jpg	122	f	\N
123	img	\N			auto_upload.jpg	123	f	\N
124	img	\N			auto_upload.jpg	124	f	\N
125	img	\N			auto_upload.jpg	125	f	\N
126	img	\N			auto_upload.jpg	126	f	\N
127	img	\N			auto_upload.jpg	127	f	\N
128	img	\N			auto_upload.jpg	128	f	\N
129	img	\N			auto_upload.jpg	129	f	\N
130	img	\N			auto_upload.jpg	130	f	\N
131	img	\N			auto_upload.jpg	131	f	\N
132	img	\N			auto_upload.jpg	132	f	\N
133	img	\N			auto_upload.jpg	133	f	\N
134	img	\N			auto_upload.jpg	134	f	\N
135	img	\N			auto_upload.jpg	135	f	\N
137	img	\N			auto_upload.jpg	137	f	\N
138	img	\N			auto_upload.jpg	138	f	\N
139	img	\N			auto_upload.jpg	139	f	\N
140	img	\N			auto_upload.jpg	140	f	\N
141	img	\N			auto_upload.jpg	141	f	\N
142	img	\N			auto_upload.jpg	142	f	\N
143	img	\N			auto_upload.jpg	143	f	\N
144	img	\N			auto_upload.jpg	144	f	\N
145	img	\N			auto_upload.jpg	145	f	\N
146	img	\N			auto_upload.jpg	146	f	\N
147	img	\N			auto_upload.jpg	147	f	\N
148	img	\N			auto_upload.jpg	148	f	\N
149	img	\N			auto_upload.jpg	149	f	\N
150	img	\N			auto_upload.jpg	150	f	\N
151	img	\N			auto_upload.jpg	151	f	\N
152	img	\N			auto_upload.jpg	152	f	\N
153	img	\N			auto_upload.jpg	153	f	\N
154	img	\N			auto_upload.jpg	154	f	\N
155	img	\N			auto_upload.jpg	155	f	\N
156	img	\N			auto_upload.jpg	156	f	\N
157	img	\N			auto_upload.jpg	157	f	\N
158	img	\N			auto_upload.jpg	158	f	\N
162	img	\N			auto_upload.jpg	162	f	\N
163	img	\N			auto_upload.jpg	163	f	\N
164	img	\N			auto_upload.jpg	164	f	\N
165	img	\N			auto_upload.jpg	165	f	\N
166	img	\N			auto_upload.jpg	166	f	\N
167	img	\N			auto_upload.jpg	167	f	\N
168	img	\N			auto_upload.jpg	168	f	\N
169	img	\N			auto_upload.jpg	169	f	\N
170	img	\N			auto_upload.jpg	170	f	\N
171	img	\N			auto_upload.jpg	171	f	\N
172	img	\N			auto_upload.jpg	172	f	\N
\.


--
-- Data for Name: webapp_edition; Type: TABLE DATA; Schema: public; Owner: salbouy
--

COPY public.webapp_edition (id, name, place_id, publisher_id) FROM stdin;
\.


--
-- Data for Name: webapp_language; Type: TABLE DATA; Schema: public; Owner: salbouy
--

COPY public.webapp_language (id, lang, code) FROM stdin;
\.


--
-- Data for Name: webapp_person; Type: TABLE DATA; Schema: public; Owner: salbouy
--

COPY public.webapp_person (id, name, date_min, date_max) FROM stdin;
\.


--
-- Data for Name: webapp_place; Type: TABLE DATA; Schema: public; Owner: salbouy
--

COPY public.webapp_place (id, name, country, latitude, longitude) FROM stdin;
1	Paris	France	48.8534	2.3488
2	Ankara	Türkiye	39.9199	32.8543
3	Arras	France	50.2930	2.7819
4	Basel	Switzerland	47.5584	7.5733
5	Berlin	Germany	52.5244	13.4105
6	Maharashtra	India	19.2891	76.9537
7	Dresden	Germany	51.0509	13.7383
8	El Escorial	Spain	40.5914	-4.1474
9	Florence	Italy	43.7792	11.2463
10	Haridwar	India	29.9479	78.1603
11	Harvard University	United States	42.3770	-71.1167
12	Istanbul	Türkiye	41.0138	28.9497
13	Karlsruhe	Germany	49.0094	8.4044
14	Leiden	Netherlands	52.1583	4.4931
15	London	United Kingdom	51.5085	-0.1257
16	Mashad	Iran	36.2981	59.6057
17	New Haven	United States	41.3081	-72.9282
18	Melbourne	Australia	-37.8140	144.9633
19	Munich	Germany	48.1374	11.5755
20	Naples	Italy	40.8522	14.2681
21	Alwar	India	27.5625	76.6250
22	Rome	Italy	41.8919	12.5113
23	Ujjain	India	23.1824	75.7764
24	Jammu	India	32.7353	74.8617
25	Tehran	Iran	35.6944	51.4215
26	Vatican City	Vatican City	41.9027	12.4541
27	Vienna	Austria	48.2085	16.3721
\.


--
-- Data for Name: webapp_role; Type: TABLE DATA; Schema: public; Owner: salbouy
--

COPY public.webapp_role (id, role, content_id, person_id, series_id) FROM stdin;
\.


--
-- Data for Name: webapp_series; Type: TABLE DATA; Schema: public; Owner: salbouy
--

COPY public.webapp_series (id, notes, date_min, date_max, is_public, edition_id, user_id, work_id) FROM stdin;
\.


--
-- Data for Name: webapp_series_tags; Type: TABLE DATA; Schema: public; Owner: salbouy
--

COPY public.webapp_series_tags (id, series_id, tag_id) FROM stdin;
\.


--
-- Data for Name: webapp_tag; Type: TABLE DATA; Schema: public; Owner: salbouy
--

COPY public.webapp_tag (id, label) FROM stdin;
\.


--
-- Data for Name: webapp_witness; Type: TABLE DATA; Schema: public; Owner: salbouy
--

COPY public.webapp_witness (id, type, id_nb, notes, nb_pages, page_type, is_public, link, slug, volume_title, volume_nb, created_at, updated_at, edition_id, place_id, series_id, user_id) FROM stdin;
3	ms	Chinois 4957		42	oth	f	https://gallica.bnf.fr/ark:/12148/btv1b90060873/f49.item	bibliotheque-nationale-de-france-chinois-4957	\N	\N	2023-02-27 17:05:27.33338+00	2023-11-28 15:42:02.29319+00	\N	1	\N	10
4	ms	Lat. 7214		225	fol	f	https://gallica.bnf.fr/ark:/12148/btv1b100352862	bibliotheque-nationale-de-france-lat-7214	\N	\N	2023-03-06 10:45:43.515632+00	2023-06-16 12:49:02.367082+00	\N	1	\N	8
5	ms	Lat. 16211		111	fol	f	https://archivesetmanuscrits.bnf.fr/ark:/12148/cc76684b	bibliotheque-nationale-de-france-lat-16211	\N	\N	2023-03-06 10:50:45.60891+00	2023-03-22 16:14:04.300332+00	\N	1	\N	8
6	ms	F II 7	38r-46v: Canones de primo mobili\r\n58r-61r: Ad inveniendum sinum\r\n67r-77v: Tabula sinuum\r\n83v-84r: Ad inveniendum sinum	85	fol	f		f-ii-7	\N	\N	2023-03-06 13:36:13.434378+00	2023-10-24 15:37:37.230898+00	\N	4	\N	1
8	ms	gr. 2925	Diktyon ID: 52564.\r\n\r\nManuscript on paper. \r\n\r\nPrevious owners include Niccolò Ridolfi (1501-1550), then Piero Strozzi, and then the Queen of France Catherine de Médici (1519-1589).	283	fol	f	https://gallica.bnf.fr/ark:/12148/btv1b10722901r	bibliotheque-nationale-de-france-gr-2925	\N	\N	2023-03-07 14:49:07.492062+00	2023-10-05 14:02:55.47882+00	\N	1	\N	5
9	ms	gr. 2509	Diktyon ID: 52141\r\n\r\nManuscript on paper. \r\n\r\nPrevious owners include Antonios Eparchos (1492-1571); then the Royal Library at Fontainebleau (first half of the 16 C).	299	fol	f	https://gallica.bnf.fr/ark:/12148/btv1b55013389h/f542.planchecontact	bibliotheque-nationale-de-france-gr-2509	\N	\N	2023-03-07 14:57:40.075013+00	2023-11-24 16:33:43.182424+00	\N	1	\N	5
10	ms	gr. 2494	Diktyon ID: 52126\r\n\r\nManuscript on paper.	260	fol	f	https://gallica.bnf.fr/ark:/12148/btv1b10722213d	bibliotheque-nationale-de-france-gr-2494	\N	\N	2023-03-08 10:51:12.608415+00	2023-06-27 08:18:18.164296+00	\N	1	\N	5
11	ms	gr. 2404	Diktyon ID: 52036. \r\n\r\nManuscript on paper. \r\n\r\nPrevious owners include Jean-Baptiste Colbert (1619-1683) and then his sons and grandson. Eventually, his books enter the collections of the Royal Library on 11 and 12 September 1732.\r\n\r\nIt contains only Cleomedes, "The Heavens".	64	fol	f	https://gallica.bnf.fr/ark:/12148/btv1b10723373m	bibliotheque-nationale-de-france-gr-2404	\N	\N	2023-03-08 11:00:49.813318+00	2023-06-27 14:48:35.146233+00	\N	1	\N	5
12	ms	gr. 2376	Diktyon ID: 52008. \r\n\r\nManuscript on paper. \r\n\r\nPrevious owners include Jérôme Fondule who acquired a group of mss in Venice in 1538-9 for the King of France. In the second half of the 16th C the manuscript is attested at the Bibliothèque royale in Fontainebleau.	251	fol	f	https://gallica.bnf.fr/ark:/12148/btv1b107219397	bibliotheque-nationale-de-france-gr-2376	\N	\N	2023-03-08 11:06:10.438694+00	2023-06-27 14:05:12.115522+00	\N	1	\N	5
13	ms	Arabe 2516	title: al-Tuḥfa al-Shāhiyya	118	fol	f	https://archivesetmanuscrits.bnf.fr/ark:/12148/cc304327	bibliotheque-nationale-de-france-arabe-2516	\N	\N	2023-03-08 11:14:39.798697+00	2023-10-24 09:22:17.087262+00	\N	1	\N	11
14	ms	ar. 319	fols. 1b-64a : al-Tadhkira fī ʿilm al-hayʾa by Naṣīr al-Dīn al-Ṭūsī, copied 1284 in Baghdad at the Niẓāmiyya Madrasa	134	fol	f	https://opac.vatlib.it/mss/detail/Vat.ar.319	ar-319	\N	\N	2023-03-08 12:49:30.99102+00	2023-10-25 08:30:09.050182+00	\N	35	\N	11
15	ms	Feyzullah 1330	fols. 1b-83a : al-Tadhkira fī ʿilm al-hayʾa by Naṣīr al-Dīn al-Ṭūsī, copied 1356 from an autograph by Aḥmad b. Maḥmūd b. Muḥammad al-Qazwīnī\r\n\r\nfols. 84a-150a : Sharḥ al-Mulakhkhaṣ fī al-hayʾa [=Commentary on (Jaghmīnī's) Epitome of Astronomy] by Faḍl Allāh al-ʿUbaydī, copied 1355 by Aḥmad b. Maḥmūd b. Muḥammad al-Qazwīnī.  On fol. 84a, upper left corner, the text is referred to as Kitāb Ḥāshiyyat al-ʿUbaydī ʿalā al-Jaghmīnī	160	fol	f		feyzullah-1330	\N	\N	2023-03-08 13:08:58.133914+00	2023-10-05 10:20:12.46824+00	\N	12	\N	11
16	ms	Ahmet III 3314	title: Sharḥ al-Tadhkira (Commentary on [Ṭūsī's] Tadhkira)	368	fol	f		ahmet-iii-3314	\N	\N	2023-03-08 13:21:17.162707+00	2023-06-20 12:13:59.540925+00	\N	14	\N	11
17	ms	Ayasofya 2583	Ṭūsī's recension of the Almagest and three short appendices\r\n\r\n(1) fols. 1b-113a : Taḥrīr al-Majisṭī = Naṣīr al-Dīn al-Ṭūsī's recension of Ptolemy's Almagest\r\n\r\n(2) fols. 114b-116a : short treatise on the computation of the centers of the spheres of Mercury\r\n\r\n(3) fols. 116a-117b : short treatise on the computation of the anomaly caused by the eccentricity\r\n\r\n(4) fols. 117b-118a : on the figure for Venus in Book X.2 of the Aimagest\r\n\r\nCopied and collated by students of Quṭb al-Dīn al-Shīrāzī, collated with a manuscript that was corrected and read in the presence of the author (i.e., al-Ṭūsī)\r\n\r\nhttps://ptolemaeus.badw.de/ms/798	118	fol	f		ayasofya-2583	\N	\N	2023-03-08 13:34:09.180403+00	2023-09-19 12:56:27.362137+00	\N	13	\N	11
18	ms	Pertev Paşa 381	Nihāyat al-Idrāk fī dirāyat al-aflāk	110	fol	f		pertev-pasa-381	\N	\N	2023-03-08 14:13:51.888884+00	2023-09-14 14:55:01.667062+00	\N	13	\N	11
19	ms	Arabe 2330	a compendium of mathematics, astronomy, astrology, and natural philosophy\r\n\r\nfols 48b-82b : al-Mulakhkhaṣ fī al-hayʾa al-basīṭa by al-Jaghmīnī, copied 1385. This is one of the five principal MSS used by Sally Ragep in her 2016 critical edition of Jaghmīnī's Mulakhkhaṣ.	116	fol	f	https://archivesetmanuscrits.bnf.fr/ark:/12148/cc30249s	bibliotheque-nationale-de-france-arabe-2330	\N	\N	2023-03-08 14:26:21.989113+00	2023-07-11 14:18:29.370822+00	\N	1	\N	11
20	ms	Landberg 33	Muntahā al-idrāk fī dirāyat al-aflāk\r\n\r\nAhlwardt 5669\r\n\r\nPersistent URL for digital version - http://resolver.staatsbibliothek-berlin.de/SBB0000D50100000000\r\n\r\nIIIF manifest downloadable at - https://content.staatsbibliothek-berlin.de/dc/744029791/manifest	66	fol	f	https://www.qalamos.net/receive/DE1Book_manuscript_00006688	landberg-33	\N	\N	2023-03-08 14:49:17.317014+00	2023-10-26 09:26:51.4792+00	\N	5	\N	11
21	ms	gr. 2180	Diktyon ID: 51809.\r\n\r\nManuscript on paper. \r\n\r\nPrevious owners include Jean Hurault de Boistaillé (d.1572); Philippe Hurault de Cheverny (1579-1620). \r\nBibliothèque royale de France purchased the latter's personal library in 1622.	109	fol	f	https://gallica.bnf.fr/ark:/12148/btv1b52509195s	bibliotheque-nationale-de-france-gr-2180	\N	\N	2023-03-10 10:38:36.045973+00	2023-11-28 17:57:33.16634+00	\N	1	\N	5
22	ms	Lat. 14068		200	fol	f	https://gallica.bnf.fr/ark:/12148/btv1b10035278j	bibliotheque-nationale-de-france-lat-14068	\N	\N	2023-03-10 10:40:59.804969+00	2023-06-27 15:23:41.979549+00	\N	1	\N	8
23	ms	Lat. 7295A		193	fol	f	https://gallica.bnf.fr/ark:/12148/btv1b10027322j	bibliotheque-nationale-de-france-lat-7295a	\N	\N	2023-03-10 10:46:18.826758+00	2023-06-27 11:58:49.434607+00	\N	1	\N	8
71	ms	Clm 51	Peurbach Theorica novae, 72r-88v	294	fol	f	https://www.digitale-sammlungen.de/view/bsb00045298?page=1	clm-51	\N	\N	2023-03-24 08:37:20.367325+00	2023-12-04 15:03:51.850282+00	\N	22	\N	3
72	ms	Pal. lat. 1385	Peurbach Theorice,  80r-100v	346	fol	f		pal-lat-1385	\N	\N	2023-03-24 08:39:18.812574+00	2023-07-11 15:07:05.484919+00	\N	35	\N	3
24	ms	gr. 1815	Diktyon ID: 51441.\r\n\r\nManuscript on paper.\r\n\r\nPrevious owner include Cardinal Niccolò Ridolfi (1501-1550); after his death, his books were purchased by Piero Strozzi. Piero Strozzi (16 C); after his death, his widow transfers his book collection to the library of Catherine de Medici.	361	fol	f	https://gallica.bnf.fr/view3if/ga/ark:/12148/btv1b10722907f	bibliotheque-nationale-de-france-gr-1815	\N	\N	2023-03-10 10:55:53.319847+00	2023-06-26 14:22:26.903308+00	\N	1	\N	5
25	ms	Lat. 7333		70	fol	f	https://gallica.bnf.fr/ark:/12148/btv1b52514382c	bibliotheque-nationale-de-france-lat-7333	\N	\N	2023-03-10 10:55:56.67727+00	2023-03-22 16:43:20.736871+00	\N	1	\N	8
26	ms	Lat. 7267		58	fol	f	https://gallica.bnf.fr/ark:/12148/btv1b100352845	bibliotheque-nationale-de-france-lat-7267	\N	\N	2023-03-10 11:22:57.944245+00	2023-03-22 16:45:02.604692+00	\N	1	\N	8
27	ms	Lat. 7195		146	fol	f	https://gallica.bnf.fr/ark:/12148/btv1b10721445z	bibliotheque-nationale-de-france-lat-7195	\N	\N	2023-03-10 12:00:29.416213+00	2023-06-28 07:54:04.068315+00	\N	1	\N	8
28	ms	Lat. 7298		174	fol	f	https://gallica.bnf.fr/ark:/12148/btv1b10721165n	bibliotheque-nationale-de-france-lat-7298	\N	\N	2023-03-10 12:07:21.737875+00	2023-05-16 11:03:50.385144+00	\N	1	\N	8
29	ms	Ms. 4456	Diktyon ID: 49125.\r\n\r\nManuscript on paper.\r\n\r\nPrevious owners include Giovanni Pico de la Mirandola (1463-1494), Domenico Grimani (1461-1523), San Antonio di Castello (Monastery in Venice), André Hurault de Maisse (1539-1607), Théodore de Berziau (1586-1623), André de Berziau (1620-1696), Oratoire de France (Paris).	206	fol	f	https://bibnum.institutdefrance.fr/ark:/61562/mz22490	ms-4456	\N	\N	2023-03-10 12:31:03.731846+00	2023-10-24 16:18:31.266952+00	\N	25	\N	5
30	ms	Lat. 9335		160	fol	f		bibliotheque-nationale-de-france-lat-9335	\N	\N	2023-03-10 12:35:42.438037+00	2023-05-16 10:22:39.528306+00	\N	1	\N	8
31	ms	Héb. 1036		100	fol	f	https://gallica.bnf.fr/ark:/12148/btv1b10544619c	bibliotheque-nationale-de-france-heb-1036	\N	\N	2023-03-10 12:44:55.665102+00	2023-07-09 13:54:54.490389+00	\N	1	\N	8
32	ms	Vat. lat. 3379		116	fol	f	https://digi.vatlib.it/iiif/MSS_Vat.lat.3379/manifest.json	vat-lat-3379	\N	\N	2023-03-10 13:37:52.480897+00	2023-07-11 14:49:45.621013+00	\N	35	\N	8
33	ms	MS 595		117	fol	f	https://nubis.univ-paris1.fr/iiif/3/47206/manifest.json	ms-595	\N	\N	2023-03-10 13:40:27.776548+00	2023-05-23 15:17:34.524322+00	\N	24	\N	8
34	ms	688 (748)		71	fol	f	https://bvmm.irht.cnrs.fr/resultRecherche/resultRecherche.php?COMPOSITION_ID=22378	688-748	\N	\N	2023-03-10 14:10:20.584642+00	2023-07-04 18:39:35.116127+00	\N	3	\N	8
35	ms	Cod. 5203		180	fol	f		cod-5203	\N	\N	2023-03-10 16:05:25.709028+00	2023-10-25 08:58:25.50416+00	\N	36	\N	8
36	ms	Fatih 3175/1	al-Tuḥfa al-Shāhiyya\r\n\r\nWitness copied from an autograph\r\n\r\nwork #2 in this MS is another work by Shīrāzī, Faʿaltu fa lā talum, but I (Scott) do not have the scan of this part of the MS	153	fol	f		fatih-31751	\N	\N	2023-03-13 09:29:07.222844+00	2023-05-23 08:18:05.319429+00	\N	13	\N	11
37	ms	Vat. gr. 187	Diktyon ID: 66818.\r\n\r\nManuscript on paper. \r\n\r\nPrevious owners include Angelo Colocci (1474-1549).\r\n\r\nThe manuscript contains works by Ptolemy and Barlaam of Calabria.	228	fol	f	https://digi.vatlib.it/view/MSS_Vat.gr.187/0072	vat-gr-187	\N	\N	2023-03-13 09:53:56.4637+00	2023-10-24 16:19:08.344657+00	\N	35	\N	5
38	ms	Vat. gr. 1087	Diktyon ID: 67718.\r\n\r\nManuscript on paper. \r\n\r\nPrevious owners include Pope Nicholas V (1397-1455).	320	fol	f	https://digi.vatlib.it/view/MSS_Vat.gr.1087/0001	vat-gr-1087	\N	\N	2023-03-13 10:33:27.949918+00	2023-10-24 16:19:38.400533+00	\N	35	\N	5
39	ms	III C 19	Almagest Greek	246	fol	f		iii-c-19	\N	\N	2023-06-26 07:34:21.517338+00	2023-07-11 14:51:51.177376+00	\N	23	\N	1
40	ms	hebr. Or. fol. 1054	Almagest Hebrew	180	fol	f		hebr-or-fol-1054	\N	\N	2023-03-20 13:23:33.13815+00	2023-06-23 12:30:50.415167+00	\N	5	\N	12
41	ms	RARES 091 P95A	Almagest Latin (Gerard of Cremona Class B)	193	fol	f		rares-091-p95a	\N	\N	2023-03-20 17:17:54.883489+00	2023-07-11 15:15:50.279191+00	\N	21	\N	12
42	ms	Plut. 30.6	Almagest Latin (George of Trebizond)	194	fol	f		plut-306	\N	\N	2023-03-20 17:54:19.439364+00	2023-07-13 08:38:46.978679+00	\N	9	\N	12
44	ms	Ar. 6840		405	fol	f	https://gallica.bnf.fr/ark:/12148/btv1b84061572	bibliotheque-nationale-de-france-ar-6840	\N	\N	2023-03-21 13:55:13.294352+00	2023-12-02 05:09:33.556076+00	\N	1	\N	13
45	ms	Or. 1997		522	fol	f	https://www.qdl.qa/en/archive/81055/vdc_100022880536.0x000001	or-1997	\N	\N	2023-03-21 14:00:00.858485+00	2023-10-25 08:38:31.792678+00	\N	18	\N	13
46	ms	Or. 2541		37	fol	f	https://digitalcollections.universiteitleiden.nl/view/item/1572906	or-2541	\N	\N	2023-03-21 14:15:04.628504+00	2023-10-25 08:38:49.372539+00	\N	17	\N	13
47	ms	lat. 7416B	Titre :  1.° Profacii, Judaei, quadrans novus, correctus à Petro Dane de S. Audomaro. — 2.° Joannis de Sacrobosco tractatus de sphaera. — 3.° Tractatus de algorismo. — 4.° Joannis de Sacrobosco tractatus de computo. — 5.° Tractatus de quadrante veteri : authore Joanne de Montepessulano. — 6.° Alius tractatus de algorismo. — 7.° Alius tractatus de quadrante. — 8.° Tractatus de compositione cylindri. — 9.° Tabulae astronomicae : accedunt canones. — 10.° Nomina instrumentorum astrolabii, cum ejusdem usu et practica. — 11.° Messahallach de compositione et usu astrolabii. — 12.° Thebit, ben Corath, de imaginatione octavae sphaerae. — 13.° Theorica planetarum : authore Gerardo Carmonensi. — 14.° Fragmentum de astrologia judiciaria. — 15.° Fragmentum de chiromantia.\r\nDate d'édition :  1201-1400\r\nNotice du catalogue :  http://archivesetmanuscrits.bnf.fr/ark:/12148/cc66636p\r\nType :  manuscrit\r\nLangue  :  latin\r\nFormat :  Parchemin\r\nDescription :  Numérisation effectuée à partir d'un document de substitution.\r\nDroits  :  Consultable en ligne	143	fol	f	https://gallica.bnf.fr/ark:/12148/btv1b90767705	bibliotheque-nationale-de-france-lat-7416b	\N	\N	2023-03-23 16:00:48.354465+00	2023-03-23 16:00:48.35448+00	\N	1	\N	3
48	ms	lat. 16709	Titre :  Recueil\r\nAuteur  :  Aristoteles (0384-0322 av. J.-C.). Auteur du texte\r\nAuteur  :  Hermannus Alemannus (12..-1272). Traducteur\r\nAuteur  :  Boethius, Anicius Manlius Severinus (0480?-0524). Auteur du texte\r\nAuteur  :  Mallius Theodorus. Auteur du texte\r\nAuteur  :  Augustinus (saint ; 0354-0430). Auteur du texte\r\nAuteur  :  Petrus Comestor (1100?-1179?). Auteur du texte\r\nAuteur  :  Petrus de Sancto Audomaro (?). Auteur présumé du texte\r\nAuteur  :  Johannes de Lineriis. Auteur du texte\r\nAuteur  :  Johannes de Sacro Bosco (11..-1256?). Auteur du texte\r\nDate d'édition :  1201-1500\r\nContributeur  :  abbaye d’Hermières. Ancien possesseur\r\nContributeur  :  Gianozzo. Ancien possesseur\r\nContributeur  :  Collège de Sorbonne (Paris). Ancien possesseur\r\nNotice du catalogue :  http://archivesetmanuscrits.bnf.fr/ark:/12148/cc77130m\r\nType :  manuscrit\r\nLangue  :  latin\r\nFormat :  Ecritures livresques et cursives. Plusieurs copistes et unités codicologiques. - Parchemin et papier. - 145 feuillets précédés de trois gardes papier et de deux gardes parchemin et suivis de deux gardes parchemin foliotées (144 ; 145) et trois gardes papier. - 255x175 mm. - Reliure contemporaine de daim sur ais de bois. Contreplats cartonnés. Traces d’enchaînement. - Estampilles de la Bibliothèque nationale de France : 2r, 143v. Estampilles de la Bibliothèque Impériale : 24r, 35v, 36r, 49v, 66r, 71v, 81r, 92v, 107v, 129v. Estampilles de la Bibliothèque de Sorbonne : 2r, 143v\r\nDescription :  Numérisation effectuée à partir d'un document de substitution.\r\nDescription :  F. 2r-28v. Aristoteles, Poetria transl. Hermanno Alemanno cum glosa. -- F. 28v-29v. Questio supra poetriam. -- F. 29v. Partes Poetrie.F. 30-35. Boethius, De topicis differentisF. 37-42v. Regule de arte versificandi. -- F. 43-45. Mallius Theodorus, De metris.F. 50-66. Ps. Augustinus, Sermones ad fratres in eremo commorantes ; -- F. 67-90. Ps. Augustinus et Augustinus, Sermones. -- F. 90v-92v. Sermo ad annum 1354 in capitulo Sancti Audomari. -- F. 93-95v. Ps. Augustinus, Sermones. -- F. 95v. Collatio brevis 19 Junii 1357. -- F. 96-98. Augustinus, Sermones. -- F. 98v-101v. Sermo ad annum 1354 in capitulo Sancti Audomari.F. 103. Supra Topica Aristotelis.F. 104-106. Epistola Gerardi subdiaconi ad Petrum presbyterumF. 106-107v.Petrus Comestor, Sermo.F. 109-113v. Theorica planetarum Gerardi. -- F. 114. Petrus de Sancto Audomaro (?), Theorica motuum latitudinis planetarum.F. 115. Tractatus supra fractiones. -- F. 116-120v. Iohannes de Lineriis, Algorismus de minutiisF. 122-128. Iohannes de Sacrobosco, De spera. -- F. 128v-129v. Anon. De compoto. -- F. 130-132v. Johannes de Sacrobosco, Algorismus ; -- F. 132v-143. id., Computus\r\nDroits  :  Consultable en ligne\r\nIdentifiant :  ark:/12148/btv1b9067670v\r\nSource  :  Bibliothèque nationale de France. Département des Manuscrits. Latin 16709	149	fol	f	https://gallica.bnf.fr/ark:/12148/btv1b9067670v	bibliotheque-nationale-de-france-lat-16709	\N	\N	2023-03-23 16:05:38.494443+00	2023-07-04 21:26:07.621841+00	\N	1	\N	3
49	ms	lat. 16658	Titre :  Tabule astronomice\r\nAuteur  :  Richard de Fournival (1201-1260?). Auteur du texte\r\nDate d'édition :  1275-1300\r\nContributeur  :  Petrus Lemovicensis (12..-1306). Copiste\r\nContributeur  :  Petrus Lemovicensis (12..-1306). Ancien possesseur\r\nNotice du catalogue :  http://archivesetmanuscrits.bnf.fr/ark:/12148/cc77079f\r\nType :  manuscrit\r\nLangue  :  latin\r\nFormat :  France. - Ecriture livresque ; plein texte. Nombreuses annotations et ajouts de Pierre de Limoges qui a copié la Nativité des f. 31v-32r ainsi que les trois traités des ff. 137v-139v. - Lettres émanchées rouges et bleues. Initiales filigranées rouges et bleues. Rubriques à l’encre rouge. Tables exécutées à l’encre rouge et noire, les initiales en tête des tables du comput sont filigranées, à l’encre rouge et bleue. Les tables des ff. 64r-69v possèdent des colonnes de chiffres à l’encre verte. - 17 Cahiers : 1 + 2 cahiers de 12 feuillets (ff. 2-25) + 1 cahier de 6 feuillets (ff. 26+31) + 4 cahiers de 8 feullets (ff. 32+63) + 1 cahier de 6 feuillets (ff. 64+69)+ 8 cahiers de 8 feuillets (ff. 70+133) + 1 cahier de 7 feuillets (ff. 134-140 il manque un feuillet).Signatures de cahiers au crayon. Réclames : f. 13v « prius ». - Parchemin. - 140 feuillets précédés d’une garde parchemin (foliotée 1). - 185x130mm. - Reliure de parchemin estampée de filets. Dos à 3 nerfs. Titre au dos à l’encre : « Azarchel Tabula astronomica MS. » traces nettes d’enchaînement sur la garde et le contreplat supérieur. - Estampilles de la Bibliothèque nationale de France : ff. 2r, 139v. Estampilles de la Bibliothèque de Sorbonne : ff. 2r ; 137v\r\nDescription :  Numérisation effectuée à partir d'un document de substitution\r\nDescription :  F. 2-31v. Canones Tabule Toledane ;F. 31v-32. Ricardus de Furnivale, Nativitas ;f; 32v-38. Kalendarium ;F. 38v-39v. Tabule de computo ;F. 40-69v. Tabule Toledane ;F. 70-83. Tabule Tolose ;F. 83v-137. Tabule Toledane ;F. 137. Compositio Tabularum ;F. 137v. Compositio tabularum mediorum motuum ab annos Christi a Petro Lemovicensis ;F. 137v. Sphera Pythagore cum canonibus ;F. 138-139v. Theorica Planetarum Campani, Capitulum De sole ;\r\nDroits  :  Consultable en ligne\r\nIdentifiant :  ark:/12148/btv1b100337616\r\nSource  :  Bibliothèque nationale de France. Département des Manuscrits. Latin 16658	140	fol	f	https://gallica.bnf.fr/ark:/12148/btv1b100337616	bibliotheque-nationale-de-france-lat-16658	\N	\N	2023-03-23 16:13:40.597582+00	2023-03-23 16:13:40.597617+00	\N	1	\N	3
50	ms	lat. 7272	Titre :  Andalius de Nigro Januensis , Tractatus de sphaera .\r\nTitre :  Andalius de Nigro Januensis , Theorica planetarum .\r\nTitre :  Practica astrolabii .\r\nTitre :  Tractatus de sphaera .\r\nTitre :  Profatius Judaeus , Canones de aequationibus planetarum .\r\nTitre :  Andalius de Nigro Januensis , Expositio in supradictos canones .\r\nTitre :  Theorica distantiarum omnium sphaerarum, circulorum et planetarum à terra, et de magnitudine eorum .\r\nTitre :  Andalius de Nigro Januensis , Introductio ad judicia astrologica .\r\nTitre :  Thabit Ben Qurra , De Imaginibus .\r\nAuteur  :  Di Negro, Andalò (....-1334). Auteur du texte\r\nAuteur  :  Profatius Judaeus. Auteur du texte\r\nAuteur  :  T̲ābit ibn Qurrah al-Ṣābī, Abū al-Ḥasan (083.?-0901). Auteur du texte\r\nDate d'édition :  1325-1330\r\nContributeur  :  rois Aragonais de Naples. Ancien possesseur\r\nContributeur  :  Charles VIII. Ancien possesseur\r\nContributeur  :  Librairie royale de Blois. Ancien possesseur\r\nNotice du catalogue :  http://archivesetmanuscrits.bnf.fr/ark:/12148/cc664637\r\nType :  manuscrit\r\nLangue  :  latin\r\nFormat :  Italie du Sud (Naples ?). - Décoration italienne. 19 peintures représentant les signes du zodiaque, le soleil, la lune, et les planètes (116-129). - Parchemin. - A + 173 ff. + f. 115bis et 142bis à 2 colonnes. - 300 x 220 mm (just. 195 x 145 mm). - Composition des cahiers : 4 cahiers de 10 ff. (1-40), 1 cahier de 4 ff. (41-44), 5 cahiers de 10 ff. (45-94), 1 cahier de 6 ff. (95-100), 1 cahier de 10 ff. (101-110)), 1 cahier de 8 ff. (111-117), 4 cahiers de 10 ff. (101-156), 2 cahiers de 8 ff. (157-172), précédés et suvis des ff. de garde A et 173. - Réclames au verso du dernier f. de chaque cahier. F. 44-44v blanc. - Reliure du début du XVI e s. en velours rose sur ais de bois, traces de boulons, de deux fermoirs et d'une étiquette sur le plat inférieur\r\nDescription :  Numérisation effectuée à partir d'un document original.\r\nDescription :  Collection numérique : Europeana Regia : manuscrits des rois aragonais de Naples\r\nDescription :  F. 1-10. Andalius de Nigro Januensis, Tractatus de sphaera . F. 10-10v. "Tabula... horarum ... diei majoris... sec. Almagesti". F. 11-43v. Andalius de Nigro Januensis, Theorica planetarum : "Quia in theorica planetarum motus solis est..." F. 45-59v. Practica astrolabii , attribuée à Andalius de Nigro Januensis ou Masha Allah ? : "Nomina instrumentorum astrolabii sunt hec...". F. 60-63v. "Alius tractatus de spera, liber secundus. Mundus est universitas rerum visinilium cujus centrum est terra, superficies vero est firmamentum...", faussement attribué à Thâbit par une main postérieure. F. 64-67v. "Capitulum .4. de tractatu C [cédillé] odiaci. Consequenter intelligatur quidam circulus..." F. 68-84v. Profatius Judaeus, Canones de aequationibus planetarum : Quia secundum philosophum in principio Metaphisice omnes homines natura... Quia in arte astronomica modus equandi..." F. 85-99v. Andalius de Nigro Januensis, Expositio in supradictos canones : "Punctus centrum cuspis sunt sinonima il est idem significantia..." F. 100-100v. Theorica distantiarum omnium sphaerarum, circulorum et planetarum à terra, et de magnitudine eorum : "Anni qui ab Adam... Quando sol fuerit in emisperio..." F. 101-170. Andalius de Nigro Januensis, Introductio ad judicia astrologica : C [cédillé] odiacus circulus est circulus signorum cujus circumferentis..." F. 170v-173. Thabit Ben Qurra , De Imaginibus : "[D]ixit Tebith Benkorat .R. qui legit [?] philosophiam et geometriam et omnem... Dixit Aristotelis phylosophus [?] in secunda tractato sui libri... Dixit Tebit cum volueris operari de ymaginibus scito quod...". Addition. Nombreuses notes marginales de plusieurs mains ; aux ff. 112-113v, 114v 116v, 117v, 118v, 143, 161-164, indications mathématiques (astronomie ?).\r\nDescription :  Lieu de copie : Italie du Sud (Naples ?).\r\nDroits  :  Consultable en ligne\r\nIdentifiant :  ark:/12148/btv1b8452771j\r\nSource  :  Bibliothèque nationale de France. Département des Manuscrits. Latin 7272	150	fol	f	https://gallica.bnf.fr/ark:/12148/btv1b8452771j/f2.item	bibliotheque-nationale-de-france-lat-7272	\N	\N	2023-03-23 16:19:26.38379+00	2023-03-23 16:19:26.383834+00	\N	1	\N	3
51	ms	lat. 7406	Titre :  1.° Canones in tabulas Toletanas, quas exposuit Joannes de Sicilia. — 2.° Canones in coelestibus motibus editi ab Arzachele. — 3.° Tabulae astronomicae. — 4.° Geberi libri quatuor de rebus ad astronomiam pertinentibus. — 5.° Fragmentum tractatus cujus titulus est : theorica planetarum.\r\nDate d'édition :  1301-1400\r\nNotice du catalogue :  http://archivesetmanuscrits.bnf.fr/ark:/12148/cc66623r\r\nType :  manuscrit\r\nLangue  :  latin\r\nFormat :  Parchemin\r\nDescription :  Numérisation effectuée à partir d'un document de substitution.\r\nDroits  :  Consultable en ligne\r\nIdentifiant :  ark:/12148/btv1b90769073\r\nSource  :  Bibliothèque nationale de France. Département des Manuscrits. Latin 7406	143	fol	f	https://gallica.bnf.fr/ark:/12148/btv1b90769073/f1.planchecontact	bibliotheque-nationale-de-france-lat-7406	\N	\N	2023-03-23 16:23:31.561119+00	2023-03-23 16:23:31.561161+00	\N	1	\N	3
52	ms	lat. 7194	itre :  1.° Anonymi algorismus, sive liber de ratione numerandi. — 2.° Tractatus de sphaera : authore Joanne de Sacrobosco. — 3.° Ejusdem tractatus de computo. — 4.° Anonymi tractatus de instrumento astronomico quod quadrans appellatur. — 5.° Tabulae ad inveniendum gradum Solis anno bissextili, et anno primo, secundo et tertio post bissextum. — 6.° Tractatus de astrolabio : authore Messahala. — 7.° Gerardi Carmonensis theorica planetarum.\r\nDate d'édition :  1301-1400\r\nNotice du catalogue :  http://archivesetmanuscrits.bnf.fr/ark:/12148/cc66375r\r\nType :  manuscrit\r\nLangue  :  latin\r\nFormat :  Parchemin\r\nDescription :  Numérisation effectuée à partir d'un document de substitution.\r\nDroits  :  Consultable en ligne\r\nIdentifiant :  ark:/12148/btv1b10035380r\r\nSource  :  Bibliothèque nationale de France. Département des Manuscrits. Latin 7194	71	fol	f	https://gallica.bnf.fr/ark:/12148/btv1b10035380r/f1.planchecontact	bibliotheque-nationale-de-france-lat-7194	\N	\N	2023-03-23 16:27:36.202935+00	2023-03-23 16:27:36.202973+00	\N	1	\N	3
53	ms	lat. 7215	itre :  1.° Euclidis elementa : interprete Adelardo, Bathoniensi ; praemittuntur 1.° Archimedis libellus de aequiponderantibus ; 2.° anonymi tractatus de magnete. — 2.° Theoremata nonnulla pertinentia ad opticam et catoptricam. — 3.° Alia theoremata pertinentia ad staticam. — 4.° Anonymi tractatus de algorismo, sive de ratione numerandi. — 5.° Theorica planetarum : authore Gerardo Carmonensi. — 6.° Liber Thebit de quantitatibus stellarum. — 7.° Joannis de Sacrobosco tractatus de sphaera. — 8.° Boëtii de arithmetica libri duo. — 9.° Thebit, ben Corath, in almagestum ; sive de iis quae indigent expositione antequàm legatur almagestum Ptolemaei. — 10.° Fragmentum de virtutibus theologicis.\r\nDate d'édition :  1301-1400\r\nNotice du catalogue :  http://archivesetmanuscrits.bnf.fr/ark:/12148/cc663994\r\nType :  manuscrit\r\nLangue  :  latin\r\nFormat :  Parchemin\r\nDescription :  Numérisation effectuée à partir d'un document de substitution.\r\nDroits  :  Consultable en ligne\r\nIdentifiant :  ark:/12148/btv1b9066183f\r\nSource  :  Bibliothèque nationale de France. Département des Manuscrits. Latin 7215	185	fol	f	https://gallica.bnf.fr/ark:/12148/btv1b9066183f/f1.planchecontact	bibliotheque-nationale-de-france-lat-7215	\N	\N	2023-03-23 16:30:45.844491+00	2023-05-10 15:10:27.096739+00	\N	1	\N	3
54	ms	lat. 7298	itre :  Tractatus diversi de scientiis\r\nAuteur  :  Badouino de Mardochio. Auteur du texte\r\nAuteur  :  Johannes de Sacro Bosco (11..-1256?). Auteur du texte\r\nAuteur  :  Robertus Grosseteste (1175?-1253). Auteur du texte\r\nAuteur  :  Joannis de Sacrobosco. Auteur du texte\r\nAuteur  :  Joanne de Montepessulano. Auteur du texte\r\nAuteur  :  Messahallach. Auteur du texte\r\nAuteur  :  Gerardus Cremonensis (1114-1187). Auteur du texte\r\nAuteur  :  W. Massiliensis. Auteur du texte\r\nAuteur  :  Farġanī, Aḥmad ibn Muḥammad ibn Kaṯīr al- (07..?-0861?). Auteur du texte\r\nDate d'édition :  1301-1400\r\nContributeur  :  Thebit\r\nContributeur  :  Roberto Grosthead\r\nContributeur  :  Campani\r\nNotice du catalogue :  http://archivesetmanuscrits.bnf.fr/ark:/12148/cc66497t\r\nType :  manuscrit\r\nLangue  :  latin\r\nFormat :  Parchemin\r\nDescription :  Numérisation effectuée à partir d'un document de substitution.\r\nDescription :  Catalogus codicum manuscriptorum Bibliothecae regiae. Pars tertia. Tomus tertius (-quartus), Parisiis : ex typographia regia, 1744 : "1.° Tractatus compoti manualis : authore Magistro Badouino de Mardochio. — 2.° Anonymi tractatus de algorismo. — 3.° Joannis de Sacrobosco, tractatus de sphaera. — 4.° Algorismus de minutiis physicis : authore anonymo. — 5.° Roberti Grosthead, Episcopi Lincolnensis, tractatus de sphaera. — 6.° Joannis de Sacroboscotractatus de compoto. — 7.° Tractatus de quadrante : authore Joanne de Montepessulano. — 8.° Messahallachtractatus de compositione et usu astrolabii. — 9.° Nomina instrumentorum astrolabii cum ejusdem usu et practica. — 10.° Theorica planetarum : authore Gerardo CarmonensiGerardo Carmonensi. — 11.° Thebit, ben Corath, tractatus de motu octavae sphaerae. — 12.° Ejusdem tractatus de iis quae indigent expositione antequam legatur almagestum Ptolemaei. — 13.° Ejusdem liber de imaginatione sphaerae et circulorum ejus diversorum. — 14.° Ejusdem liber de quantitatibus stellarum et planetarum. — 15.° Anonymi tractatus de computo : authore Roberto Grosthead. — 16.° Anonymi theorica planetarum. — 17.° W. Massiliensisastrologia. — 18.° Alfraganirudimenta astronomica : sive libellus triginta differentiarum. — 19.° Campaniopusculum de modo adaequandi planetas, sive de quantitatibus motuum coelestium, orbium proportionibus, centrorum distantiis, ipsorumque corporum magnitudinibus. Decimo quarto saeculo videtur exaratus."\r\nDroits  :  Consultable en ligne\r\nIdentifiant :  ark:/12148/btv1b10721165n\r\nSource  :  Bibliothèque nationale de France. Département des Manuscrits. Latin 7298	184	fol	f	https://gallica.bnf.fr/ark:/12148/btv1b10721165n/f5.planchecontact	bibliotheque-nationale-de-france-lat-7298	\N	\N	2023-03-23 16:34:34.825793+00	2023-03-23 16:34:34.825816+00	\N	1	\N	3
73	ms	Ayasofya 2733/1	title: al-Risāla al-Fatḥiyya\r\nalternate title: al-Fatḥiyya fī ʿilm al-hayʾa\r\n\r\nautograph witness\r\ndedicated to Sultan Meḥmed II in honor of his victory over Uzun Ḥasan in 1473\r\n\r\nOften described as merely the Arabic translation of Qūshjī's earlier Persian work "Risāla dar ʿīlm-i Hayʾa" but in fact it is a separate (although related) work - see Hasan Umut's PhD dissertation (McGill 2019)\r\n\r\nMS Aysofya 2733 contains many other works, I (Scott) only have a scan of the first item	70	fol	f		ayasofya-27331	\N	\N	2023-04-03 09:13:53.14862+00	2023-05-22 15:32:34.080779+00	\N	13	\N	11
74	ms	Ayasofya 2643	title: Sharḥ al-Tuḥfa al-Shāhiyya (Commentary on [Quṭb al-Dīn al-Shīrāzī's] al-Tuḥfa al-shāhiyya)\r\n\r\nmay be an autograph witness	64	fol	f		ayasofya-2643	\N	\N	2023-04-03 09:26:52.50904+00	2023-05-24 14:33:16.421854+00	\N	13	\N	11
55	ms	lat. 7421	Titre :  1.° Gerlandi tabulae de computo, cum earumdem explicatione. — 2.° Anonymi algorisimus, sive liber de arithmetica. — 3.° Joannis de Sacrobosco tractatus de sphaera. — 4.° Ejusdem tractatus de computo. — 5.° Anonymi tractatus de eodem argumento. — 6.° Messahallach tractatus de compositione et usu astrolabii. — 7.° Nomina instrumentorum astrolabii cum ejusdem usu et practica : authore anonymo. — 8.° Azarchelis, sive, Arzachelis canones super tabulas astronomiae constitutas ad meridiem civitatis Toleti. — 9.° Scholium de eclipsibus solis et lunae. — 10.° Theorica planetarum : authore Gerardo Carmonensi. — 11.° Tabulae astronomicae.\r\nDate d'édition :  1301-1400\r\nNotice du catalogue :  http://archivesetmanuscrits.bnf.fr/ark:/12148/cc66644d\r\nType :  manuscrit\r\nLangue  :  latin\r\nFormat :  Parchemin\r\nDescription :  Numérisation effectuée à partir d'un document de substitution.\r\nDroits  :  Consultable en ligne\r\nIdentifiant :  ark:/12148/btv1b9067047j\r\nSource  :  Bibliothèque nationale de France. Département des Manuscrits. Latin 7421	229	fol	f	https://gallica.bnf.fr/ark:/12148/btv1b9067047j/f1.planchecontact	bibliotheque-nationale-de-france-lat-7421	\N	\N	2023-03-23 16:38:50.896576+00	2023-05-10 15:10:04.783162+00	\N	1	\N	3
56	ms	lat. 7366	itre :  1.° Anonymi tractatus de algorismo, sive de arte numerandi : praemittuntur tractatus de numerorum mysteriis, et narratio Fratris Benedicti Aretini de indulgentia loco de Portiuncula concessa ab Honorio Papa III. — 2.° Magistri Joannis de Sacrobosco tractatus de computo. — 3.° Ejusdem tractatus de sphaera. — 4.° Theorica planetarum : authore Gerardo Carmonensi. — 5.° Anonymi explicationes allegoricae quorumdam Scripturae sacrae locorum : initium desideratur. — 6.° Elementorum Euclidis libri quinque priores. — 7.° Anonymi tractatus de speculis.\r\nDate d'édition :  1301-1400\r\nNotice du catalogue :  http://archivesetmanuscrits.bnf.fr/ark:/12148/cc66576b\r\nType :  manuscrit\r\nLangue  :  latin\r\nFormat :  Parchemin\r\nDescription :  Numérisation effectuée à partir d'un document de substitution.\r\nDroits  :  Consultable en ligne\r\nIdentifiant :  ark:/12148/btv1b9067095m\r\nSource  :  Bibliothèque nationale de France. Département des manuscrits. Latin 7366	104	fol	f	https://gallica.bnf.fr/ark:/12148/btv1b9067095m/f1.planchecontact	bibliotheque-nationale-de-france-lat-7366	\N	\N	2023-03-23 16:42:55.299035+00	2023-05-10 15:09:34.701885+00	\N	1	\N	3
57	ms	lat. 7333	itre :  Tractatus diversi super astronomiam\r\nAuteur  :  Bernard de Verdun (O.F.M.). Auteur du texte\r\nAuteur  :  T̲ābit ibn Qurrah al-Ṣābī, Abū al-Ḥasan (083.?-0901). Auteur du texte\r\nDate d'édition :  1301-1400\r\nContributeur  :  Hardy, Claude (1604-1678). Ancien possesseur\r\nContributeur  :  Colbert, Jean-Baptiste (1619-1683). Ancien possesseur\r\nNotice du catalogue :  http://archivesetmanuscrits.bnf.fr/ark:/12148/cc665397\r\nType :  manuscrit\r\nLangue  :  latin\r\nFormat :  Parchemin (sauf gardes en papier). - [VIII] + 70 + [VI] feuillets. - 310 × 220 mm (2 col. 205/220 × 65 mm). - Réglure à la mine de plomb. - Reliure aux petits fers (veau estampé à froid) ; dos restauré ; traces de fermoirs\r\nDescription :  Numérisation effectuée à partir d'un document original : Latin 7333.\r\nDescription :  Mécénat : Numérisé dans le cadre du projet ALFA, Shaping a European scientific scene: Alfonsine astronomy (European Research Council, CoG, 723085), en coopération avec le CNRS.\r\nDescription :  1.° Fratris Bernardi de Virduno, ordinis Minorum, liber super totam astrologiam. — 2.° Liber de compositione et practica instrumenti astronomici, quod dicitur Turketus. — 3.° Tractatus de almanach : authore anonymo. — 4.° Theorica planetarum : authore Gerardo Carmonensi. — 5.° Liber Thebit de motu octavae sphaerae. — 6.° Ejusdem liber de iis quae indigent expositione antequam legatur almagestum Ptolemaei. — 7.° Ejusdem liber de imaginatione sphaerae et circulorum ejus diversorum. — 8.° Ejusdem liber de quantitatibus stellarum et planetarum.\r\nDroits  :  Consultable en ligne\r\nIdentifiant :  ark:/12148/btv1b52514382c\r\nSource  :  Bibliothèque nationale de France. Département des Manuscrits. Latin 7333	178	fol	f	https://gallica.bnf.fr/ark:/12148/btv1b52514382c/f1.planchecontact	bibliotheque-nationale-de-france-lat-7333	\N	\N	2023-03-23 16:46:23.391751+00	2023-03-23 16:46:23.391784+00	\N	1	\N	3
58	ms	lat. 7285	Bibliothèque nationale de France\r\nIIIF\r\nTitre :  1.° Tabulae Alphonsinae. — 2.° Canones tabularum astronomicarum : authore Joanne de Saxonia. — 3.° Tabulae sinuum et chordarum ascensionum signorum, necnon eclipsium et aliorum complurium ; quas composuit Magister Joannes de Lineriis, Picardus dioecesis Ambianensis. — 4.° Practica dictaminis : authore Magistro Joanne Bondi de Aquilegia. — 5.° Theorica planetarum : authore Gerardo Carmonensi. — 6.° Instrumentum per quod sciuntur horae diei per umbram super superficiem planam parallelam horizonti, pro quacumque regione volueris fabricare.\r\nDate d'édition :  1351-1450\r\nContributeur  :  Colbert, Jean-Baptiste (1619-1683). Ancien possesseur\r\nNotice du catalogue :  http://archivesetmanuscrits.bnf.fr/ark:/12148/cc66478n\r\nType :  manuscrit\r\nLangue  :  latin\r\nFormat :  Parchemin. - 112 feuillets (+ f. 74 bis). - Reliure veau estampé doré aux armes de Colbert\r\nDescription :  Numérisation effectuée à partir d'un document original : Latin 7285.\r\nDescription :  Mécénat : Numérisé dans le cadre du projet ALFA, Shaping a European scientific scene: Alfonsine astronomy (European Research Council, CoG, 723085), en coopération avec le CNRS.\r\nDroits  :  Consultable en ligne\r\nIdentifiant :  ark:/12148/btv1b525141063\r\nSource  :  Bibliothèque nationale de France. Département des Manuscrits. Latin 7285	268	fol	f	https://gallica.bnf.fr/ark:/12148/btv1b525141063/f1.planchecontact	bibliotheque-nationale-de-france-lat-7285	\N	\N	2023-03-23 16:49:53.284041+00	2023-03-23 16:49:53.284077+00	\N	1	\N	3
59	ms	lat. 16198	Titre :  Euclides, Geometria. -- De astronomia. Jordanus de Nemore, Elementarium arismetice. -- De quantitatibus. -- Practica geometrie. -- Demonstrationes astrolabii. -- Ex introductorio Ptolomei ad Almagestum. -- Theorica motuum planetarum. -- Liber Alkabici introductorius de judiciis astrorum.\r\nAuteur  :  Euclides (0323-0285 av. J.-C.). Auteur du texte\r\nAuteur  :  Jordanus Nemorarius (12..-12..). Auteur du texte\r\nAuteur  :  Simon Bredon (?). Auteur présumé du texte\r\nAuteur  :  Campanus Novariensis (12..-1296). Auteur du texte\r\nAuteur  :  Geminus Rhodius. Auteur du texte\r\nAuteur  :  Qabīṣī, Abū al-Ṣaqr ʿAbd al-ʿAzīz ibn ʿUṯmān al- (09..- 0990). Auteur du texte\r\nDate d'édition :  1301-1400\r\nContributeur  :  Collège de Sorbonne (Paris). Ancien possesseur\r\nNotice du catalogue :  http://archivesetmanuscrits.bnf.fr/ark:/12148/cc76671d\r\nType :  manuscrit\r\nLangue  :  latin\r\nFormat :  Angleterre. - Ecriture livresque et semi-livresque de différents modules. Un seul copiste. Alternance longues lignes et colonnes (f. 2r-150v : plein texte ; f. 151r-155v : deux colonnes ; f. 156r-177v : plein texte ; f. 178r-198v : deux colonnes). - Initiales rouges et bleues f. 2r et f. 7v. Pieds de mouches rouges f. 2r. Nombreux diagrammes à l’encre rouge et noire. Décoration inachevée, lettres d’attentes et réserves. - Parchemin. - 199 ff. précédés de 3 gardes volantes supérieures de papier, de deux feuillets de parchemin (comprenant un texte de philosophie naturelle (fin XIIIe- début XIVe siècle), l’un porte des traces d’enchaînement et correspond à une ancienne contre-garde) et suivis de deux gardes inférieures papier précédées de deux feuillets de parchemin de la même main que les deux feuillets supérieurs (fin XIIIe- début XIVe siècle). - 225x305 mm. - 24 Cahiers : 2 gardes volantes + 14 cahiers de 8 feuillets (f. 2r-113v); 1 cahier de 9 feuillets (f. 114r-122v + onglet f. 120r) ; 2 cahiers de 8 feuillets (f. 123r-146v+ onglet f. 147r) ; 1 cahier de 9 feuillets (f. 147r-155v + un onglet) ; 2 cahiers de 8 feuillets (f. 156r-171v) ; 1 cahier de 10 feuillets (f. 172r-181v + trace d’onglet au f. 178r) ; 1 cahier de 8 feuillets (f. 182r-189v); 1 cahier de 9 feuillets (f. 190r-198v + onglet f. 90r) + 2 gardes volantes. Réclames. - Reliure de parchemin restaurée au XIXe siècle, estampée de filés, plats sur ais de bois, dos restauré en parchemin souple, dos à 6 nerfs. - Estampilles de la Bibliothèque de la Sorbonne : ff. 2r, 105r, 198v. Estampilles Bibliothèque impériale : modèle Josserand Bruno type 18 : ff. 1r, 199r. Estampilles de la Bibliothèque nationale : modèle Josserand Bruno type 17 : ff. 2r, 198v\r\nDescription :  Numérisation effectuée à partir d'un document de substitution.\r\nDescription :  F. 2-73. Geometria Euclidis cum commento Campani. «Punctus est cujus pars non est. Linea est longitudo sine latitudine cujus extremitates sunt duo puncta...-...propositum erat inscripsisse. Explicit geometrica Euclidis cum commento Campani.»F. 74-122. De astronomia, «Scientia species habet quarum melior post scientiam fidei ...-... in duobus hiis signis sunt digniores ut et evanescant et destruitur id .n. est propositum.» F. 123-150. Jordanus de Nemore, Elementarium arismetice cum commento (Libri VI-X). « Latera minorum dicuntur quorum multiplicatione numeri proveniunt aliter producuntur ...-... Explicit .10. liber et per consequens totum elementarium arismitice Iordani de Nemore continens secundum maiorem numerum 453 conclusiones secundum vero minorem numerum 428, si recte addidi ». [Chaque proposition comprend des commentaires anonymes.]F. 150r/v. Traité anonyme d’arithmétique : « Quantum addit quadratum quincupli super quadratum subquincupli tamen addit quadratum sepcupli super quadratum quincupli ... »F. 151-155v. Simon Bredon (?), De arithmetica. « Quantitatum alia continua que magnitudo dicitur ...-... Ista igitur sufficiant pro sententia huius libri arismetice ». F. 156-162v. Practica geometrie. « Artis cuiuslibet consummatio in duobus consistit in theorice et practice ipsius integra perceptione...-... Et hec de radice quadratarum nichil dicta sufficiant. Explicit practica geometrica ». F. 162v-163. Campanus, Compositio astrolabii. « Tres circulos in astrolapsu descriptos duos ...-... insequamur scribendum moram faciamus. Expliciunt demonstrationes astrolabii ». 163v-165v. Jordanus de Nemore (?) Super demonstrationem ponderum (probablement un commentaire anonyme du De ponderibus). « Omnis ponderosi motum esse ad medium. Quod gravius est velotius descendere ...-... quod oportebat ostendere. Explicit liber de ponderibus ». Ce traité possède le même incipit que l’œuvre de Jordanus de Nemore. Or, le traité des poids de Jordanus compte sept postulats, tandi qu'ici en sont présentés treize.F. 166-177. Geminos de Rhodes, Introductorius in Almagesti ou De dispositione spere. « Dividitur orbis signorum in .12. partes et nominatur unaqueque partium eius nomine...-... Explicit quod abreviatum est de libro Introductorii Ptholomei ad librum suum nominatum Almagesti ». F. 178-186v. Campanus, Theorica planetarum , « Primus philosophie magister illud negotium...-...qui motus est parvus valde et pene in sensibilis. Explicit Theorica motuum planetarum. »F. 187-198v. Alcabitius, Introductorius. « Postulata a domino prolixitate vite...-... interpretatus a Iohanne Hyspalensi deo gratias. Explicit liber Alkabici Introductorius de iudiciis astrorum ».\r\nDescription :  Lieu de copie : Angleterre\r\nDroits  :  Consultable en ligne\r\nIdentifiant :  ark:/12148/btv1b90671704\r\nSource  :  Bibliothèque nationale de France. Département des Manuscrits. Latin 16198	206	fol	f	https://gallica.bnf.fr/ark:/12148/btv1b90671704/f1.planchecontact	bibliotheque-nationale-de-france-lat-16198	\N	\N	2023-03-23 16:54:41.400662+00	2023-03-23 16:54:41.400675+00	\N	1	\N	3
60	ms	lat. 7195	Titre :  Tractactus diversi super scientias Quadravii\r\nAuteur  :  Johannes de Sacro Bosco (11..-1256?). Auteur du texte\r\nAuteur  :  Gerardus cremonensis (1114-1187). Auteur du texte\r\nAuteur  :  Robertus Grosseteste (1175?-1253). Auteur du texte\r\nAuteur  :  Isaaci Arzachelis. Auteur du texte\r\nAuteur  :  Joanne Brixiensi. Traducteur\r\nAuteur  :  Farġanī, Aḥmad ibn Muḥammad ibn Kaṯīr al- (07..?-0861?). Auteur du texte\r\nAuteur  :  Thebit ben Corath. Auteur du texte\r\nDate d'édition :  1301-1400\r\nNotice du catalogue :  http://archivesetmanuscrits.bnf.fr/ark:/12148/cc663760\r\nType :  manuscrit\r\nLangue  :  latin\r\nFormat :  Parchemin\r\nDescription :  Numérisation effectuée à partir d'un document original : Latin 7195.\r\nDescription :  1.° Anonymi tractatus de algorismo, sive de numerandi ratione. — 2.° Magister Joannes de Sacrobosco, tractatus de sphaera. — 3.° Ejusdem tractatus de computo. — 4.° Anonymi tractatus de quadrante. — 5.° Tabulae ad inveniendum locum Solis anno bissextili, et anno I. II. et III.° post bissextum. — 6.° Messahallae astrolabium. — 7.° Gerardus Carmonensis, theorica planetarum. — 8.° Robertus Grosthead, sive Capitonis, Episcopi Lincolniensis, sphaera. — 9.° Isaaci Arzachelis, Toletani, astrolabium : Joanne Brixiensi interprete. — 10.° Robertus Grosthead, Episcopi Lincolniensis, tractatus de computo ecclesiastico : accedit commentarius. — 11.° Alfraganus, Liber de aggregationibus scientiae stellarum, et de principiis coelestium motuum. — 12.° Thebit ben Corath, tractatus de recta imaginatione sphaerae coelestis. — 13.° Anonymi tractatus de terrae mensura. — 14.° Thebit ben Corath, liber de motu octavae sphaerae. — 15.° Ejusdem tractatus de his quae indigent expositione antequàm legatur Ptolomaei almagestum. saeculo decimo quarto videtur exaratus.\r\nDroits  :  Consultable en ligne\r\nIdentifiant :  ark:/12148/btv1b10025367r\r\nSource  :  Bibliothèque nationale de France. Département des Manuscrits. Latin 7195	300	fol	f	https://gallica.bnf.fr/ark:/12148/btv1b10025367r/f1.planchecontact	bibliotheque-nationale-de-france-lat-7195	\N	\N	2023-03-23 16:58:24.840269+00	2023-03-23 16:58:24.840304+00	\N	1	\N	3
96	ms	Or. 202/1	title: Sharḥ al-Mulakhkhaṣ fī al-hayʾa (Commentary on [Jaghmīnī's] Mulakhkhaṣ)	\N	fol	f	http://hdl.handle.net/1887.1/item:3412141	or-2021	\N	\N	2023-04-05 12:29:53.597411+00	2023-04-05 12:29:53.597443+00	\N	17	\N	11
61	ms	lat. 14068	Titre :  Ars Turketi.\r\nTitre :  Calendriers, tables et traités astronomiques.\r\nTitre :  De kalendario Petri de Dacia (34v).\r\nTitre :  Interpretationes sompniorum (40v).\r\nTitre :  Rota fortune (50v).\r\nTitre :  Theorica planetarum (59).\r\nTitre :  Liber Thebith ben Chorath de motu octave spere (91v).\r\nTitre :  Ejusdem liber de hiis que indigent expositione antequam Iegatur Almagesti (97v).\r\nTitre :  Arnaldi de Villa, Nova astronomia (110).\r\nDate d'édition :  1401-1500\r\nNotice du catalogue :  http://archivesetmanuscrits.bnf.fr/ark:/12148/cc74912n\r\nType :  manuscrit\r\nLangue  :  latin\r\nFormat :  Papier\r\nDescription :  Numérisation effectuée à partir d'un document de substitution.\r\nDroits  :  Consultable en ligne\r\nIdentifiant :  ark:/12148/btv1b10035278j\r\nSource  :  Bibliothèque nationale de France. Département des Manuscrits. Latin 14068	207	fol	f	https://gallica.bnf.fr/ark:/12148/btv1b10035278j/f1.planchecontact	bibliotheque-nationale-de-france-lat-14068	\N	\N	2023-03-23 17:02:01.081477+00	2023-03-23 17:02:01.081512+00	\N	1	\N	3
62	ms	Fr. 2078-2079	Titre :  Français 2078-2079\r\nDate d'édition :  1401-1500\r\nSujet :  Comput.\r\nSujet :  Du nombre solaire.\r\nSujet :  Nombres, Des.\r\nSujet :  Nombre solaire.\r\nSujet :  Planètes.\r\nSujet :  Traités.\r\nSujet :  Solaire, Du nombre.\r\nNotice du catalogue :  http://archivesetmanuscrits.bnf.fr/ark:/12148/cc486259\r\nType :  manuscrit\r\nLangue  :  français\r\nFormat :  Papier\r\nDescription :  Contient : 1° « Theorica planetarum » ; 2° « Du Nombre sollaire »\r\nDescription :  Numérisation effectuée à partir d'un document original : Français 2078-2079.\r\nDroits  :  Consultable en ligne\r\nIdentifiant :  ark:/12148/btv1b10025040n\r\nSource  :  Bibliothèque nationale de France. Département des Manuscrits. Français 2078-2079	120	fol	f	https://gallica.bnf.fr/ark:/12148/btv1b10025040n/f1.planchecontact	bibliotheque-nationale-de-france-fr-2078-2079	\N	\N	2023-03-23 17:08:01.962637+00	2023-03-23 17:08:01.962656+00	\N	1	\N	3
63	ms	lat. 7432	1.° Claudii Ptolemaei quadripartitum, à Conrado Hemgarter latinè conversum, uberibusque commentariis illustratum : praemittuntur Ptolemaei et Hermetis vitae. — 2.° Exempla trium nativitatum : authore Haly. — 3.° Ptolemaei centiloquium, cum commentario Conradi Hemgarter. — 4.° Capitula de cometis, de meteoris, de terrae motu, de quantitatibus stellarum, earumque distantiis à terra. — 5.° Epistola Messahallach in rebus eclipsium solis et lunae, in conjunctionibus planetarum ac revolutionibus annorum, breviter elucidata à Joanne Hispalensi. — 6.° Abdilasis, viri illustrissimi, liber quinque differentiarum, qui et Alcabitius, id est, introductorius appellatur. — 7.° Theorica planetarum : authore Gerardo Carmonensi ; accedit commentarius. — 8.° Canones tabularum Alphonsi, olim Castellae Regis illustrissimi. — 9.° Anonymi liber de statione planetarum et retrogradatione. — 10.° Tabulae Alphonsinae. — 11.° Tractatus cujus titulus : liber Hippocratis, viri peritissimi, de illo coelesti, de quo in prognosticis sermonem fecit dicens : Est quoddam caeleste quod oportet ipsum Medicum considerare. — 12.° Anonymi tractatus de prognosticis, et de componendis atque ministrandis medicinis.	578	pag	f	https://gallica.bnf.fr/ark:/12148/btv1b100202503	bibliotheque-nationale-de-france-lat-7432	\N	\N	2023-03-23 17:11:09.852702+00	2023-03-23 17:11:09.852736+00	\N	1	\N	3
64	ms	lat. 7294	Titre :  1.° Anonymi tractatus de compositione astrolabii. — 2.° Theorica planetarum : authore Gerardo Carmonensi. — 3.° Joannis de Sacrobosco tractatus de sphaera : multa sub finem desiderantur. — 4.° Practica ad componendum cylindrum. — 5.° Compositio astrolabii nova. — 6.° Canones quadrantis novi. — 7.° Canones cylindri. — 8.° Canones astrolabii. — 9.° Anonymi tractatus de compositione sphaerae solidae cum armillis. — 10.° Anonymi practica de modo mensurandi in geometria. — 11.° Algorismus specialis et astronomicus. — 12.° La maniére de connoistre les heures de nuit. — 13.° Anonymi tractatus de compositione quadrantis. — 14.° Canones, sive utilitates quadrantis.\r\nDate d'édition :  1401-1500\r\nNotice du catalogue :  http://archivesetmanuscrits.bnf.fr/ark:/12148/cc66492m\r\nType :  manuscrit\r\nLangue  :  latin\r\nFormat :  Papier\r\nDescription :  Numérisation effectuée à partir d'un document de substitution.\r\nDroits  :  Consultable en ligne\r\nIdentifiant :  ark:/12148/btv1b90779045\r\nSource  :  Bibliothèque nationale de France. Département des Manuscrits. Latin 7294	58	fol	f	https://gallica.bnf.fr/ark:/12148/btv1b90779045/f1.planchecontact	bibliotheque-nationale-de-france-lat-7294	\N	\N	2023-03-23 17:13:42.141419+00	2023-03-23 17:13:42.141459+00	\N	1	\N	3
65	ms	lat. 7401	Titre :  1.° Joannis Campani theorica planctarum. — 2.° Canon tabulae tabularum : authore Magistro Joanne de Muris.\r\nDate d'édition :  1401-1500\r\nNotice du catalogue :  http://archivesetmanuscrits.bnf.fr/ark:/12148/cc66618r\r\nType :  manuscrit\r\nLangue  :  latin\r\nFormat :  Papier\r\nDescription :  Numérisation effectuée à partir d'un document original : Latin 7401.\r\nDroits  :  Consultable en ligne\r\nIdentifiant :  ark:/12148/btv1b52514038v\r\nSource  :  Bibliothèque nationale de France. Département des Manuscrits. Latin 7401	163	fol	f	https://gallica.bnf.fr/ark:/12148/btv1b52514038v/f1.planchecontact	bibliotheque-nationale-de-france-lat-7401	\N	\N	2023-03-23 17:16:14.181677+00	2023-10-18 10:21:22.765194+00	\N	1	\N	3
66	ms	lat. 7281	itre :  Scripta varia super scientias\r\nDate d'édition :  1401-1500\r\nContributeur  :  Jo. B. (14..-14.. ; astronome). Copiste\r\nContributeur  :  Louis le Puiset. Ancien possesseur\r\nContributeur  :  Jehan Avis (14..-14..)\r\nContributeur  :  Colbert, Jean-Baptiste\r\nNotice du catalogue :  http://archivesetmanuscrits.bnf.fr/ark:/12148/cc66474p\r\nType :  manuscrit\r\nLangue  :  latin\r\nFormat :  Écriture gothique cursive ; au moins deux mains : « Jo. B. » et peut-être Louis le Puiset (Boudet, Lire dans le ciel). - Papier. - II + 286 + II feuillets. - 300×210 mm (jusif 240×160 mm). - Réglure à la mine de plomb. - Reliure de maroquin rouge aux armes royales\r\nDescription :  Numérisation effectuée à partir d'un document original.\r\nDescription :  Mécénat : Numérisé dans le cadre du projet ALFA, Shaping a European scientific scene: Alfonsine astronomy (European Research Council, CoG, 723085), en coopération avec le CNRS.\r\nDescription :  Catalogus codicum manuscriptorum Bibliothecae regiae. Pars tertia. Tomus tertius (-quartus), Parisiis : ex typographia regia, 1744 : 1.° Opus cujus is est titulus : liber Alfraganide aggregationibus scientiae stellarum et principiis coelestium motuum , secundùm translationem graecam, quae diversa videtur à versione edita Noribergae anno 1537. et Parisiis anno 1546. — 2.° Lectiones tabularum Toletanarum secundùm Arzachelem , Hispanum. — 3.° Canones tabularum astronomicarum Arzachelis. — 4.° Joannis de Sicilia , expositio super canones Arzachelis . — 5.° Almanach Guillelmi de Sancto Clodoaldo ad annos 20. incipit anno 1292 . — 6.° Calendarium Reginae M. per Guillelmum de Sancto Clodoaldo . — 7.° Expositio intentionis Regis Alphonsi circa tabulas ejusdem . — 8.° CalendariumGaufredi de Meldis , editum anno 1320. — 9.° Theorica planetarum , edita à Joanne de Lineriis anno 1335. — 10.° Expositio tabularum Alphonsi, et motiva probantia earum falsitatem . — 11.° Canones tabularum Alphonsi Regis Castellae , a Joanne de Lineriis editi anno 1310. — 12.° Ejusdem alius tractatus in easdem tabulas. — 13.° Canon eclipsium, anno 1332 , editus à Joanne de Janua . — 14.° Investigatio eclipseos Solis , quae contigit anno 1337. eodem authore. — 15.° Canones tabularum Oxoniae anno Christi 1348 . ex tabulis Alphonsinis factarum. — 16.° Joannis de Saxoniacanones super tubulas Alphonsi , editi anno 1327. — 17.° Anonymi tractatus de magnitudine, distantia et motu astrorum , editus an. 1420. — 18.° Anonymi tractatus de commensurabilitate motuum coeli . — 19.° Tabula Magistri Jacobi de Partibus , sive sirupi ad omnes humores . Decimo quinto saeculo exaratus videtur.\r\nDroits  :  Consultable en ligne\r\nIdentifiant :  ark:/12148/btv1b525030045\r\nSource  :  Bibliothèque nationale de France. Département des Manuscrits. Latin 7281	591	fol	f	https://gallica.bnf.fr/ark:/12148/btv1b525030045/f1.planchecontact	bibliotheque-nationale-de-france-lat-7281	\N	\N	2023-03-23 17:21:46.324464+00	2023-03-23 17:21:46.32448+00	\N	1	\N	3
67	ms	lat. 7197	Titre :  Miscellanea astronomica et grammatica\r\nAuteur  :  Johannes de Sacro Bosco (11..-1256?). Auteur du texte\r\nAuteur  :  FRANCO DE POLONIA. Auteur du texte\r\nAuteur  :  Jean de Lignières (13..-13..). Auteur du texte\r\nAuteur  :  Danck, Johannes. Auteur du texte\r\nAuteur  :  Cicero, Marcus Tullius (0106-0043 av. J.-C.). Auteur du texte\r\nAuteur  :  Oresme, Nicole (1322?-1382). Auteur du texte\r\nAuteur  :  Johannes de Muris (1300?-1350?). Auteur prétendu du texte\r\nAuteur  :  Hugo de Sancto Victore (1096?-1141). Auteur du texte\r\nDate d'édition :  1425-1475\r\nContributeur  :  Heingarter, Conrad. Copiste\r\nContributeur  :  Hardy, Claude (1604-1678). Ancien possesseur\r\nContributeur  :  Colbert, Jean Baptiste (1619-1683). Ancien possesseur\r\nContributeur  :  Heingarter, Conrad. Ancien possesseur\r\nNotice du catalogue :  http://archivesetmanuscrits.bnf.fr/ark:/12148/cc66378g\r\nType :  manuscrit\r\nLangue  :  latin\r\nLangue  :  allemand\r\nFormat :  Paris. - Manuscrit essentiellement en écriture cursive et de la main de l’astrologue et médecin d’origine suisse. - Conrad Heingarter. - (cf. le colophon f. 50 : «. - Explicit tractatus spere materialis per manus Conradi Heingarter. - »). La plupart des textes sont autographes, à l’exception des f. 85-102 et 118-129v, qui se distinguent par des écritures différentes. Le manuscrit a été abondamment annoté par Heingarter, en latin et en allemand, parfois sur des feuillets isolés insérés aux cahiers. - Schémas tracés à l’encre brune, parfois au compas : f. 16 et 16v (géométriques), 38 (mappemonde), 39, 51, 52, 53v, 55, 55v et 57v (astronomiques), 74v, 79 et 79v (géométriques). 1 initiale historiée (Crucifixion) grossièrement dessinée à l’encre brune, introduisant un passage sur les divisions des Saintes Écritures : f. 82v. - Initiales rubriquées aux f. 35-36, dont une avec visage (f. 35).Initiales pommetées, évidées ou cadelées à l'encre brune aux f. 118-129 (dont une avec visage au f. 128 et une avec phylactère "Ave Maria gratia plena" au f. 129).Mains nota : ex. f. 53, 63v, 64. - Papier (filigranes : au moins 3 types de têtes de boeuf avec hampe étoilée, dont un proche de Piccard-Online n° 75176 [ex. f. 48, 58, 55], attesté à Fribourg en 1455, et un proche de Piccard-Online n° 74864 [ex. f. 12, 13, 14, 22, 24, 28, 29, 30], attesté en 1455 ; 2 types d’écus à 3 fleurs de lys surmontés d’une couronne, identiques à Briquet n°1681 [f. 76, 77, 78, 84] et à Briquet n°1683 [ex. f. 65, 68, 69, 71, 72, 73], attestés à Paris en 1456 et en 1457-1461; écu à 3 fleurs de lys surmonté d’une couronne avec lettre au-dessous, proche de Briquet n°1739, attesté à Paris en 1458 [f. 117, 123, 125 , 127, 128, 129] ; croissant surmonté d’une étoile à 6 branches, proche de Briquet n° 5345, attesté en Hollande, à Namur et à Neuchâtel entre 1419 et 1427 [f. 91, 94, 95, 97, 98, 99, 100] ; filigrane non identifié f. 34). - 130 f., dont 2 f. de garde (f. 1 et 130) récupérés d’un manuscrit sur parchemin (+ 2 demi-feuillets non foliotés insérés entre les f. 22-23 et 23-24). - 295 × 210 mm. (just. 200 × 125 mm.). - 9 cahiers : 1 cahier de 20 f. (f. 2-21), 1 cahier de 12 f. + 4 demi-feuillets (f. 22-35 ; demi-feuillets foliotés f. 32 et 34 + 2 demi-feuillets non foliotés insérés entre les f. 22 et 23 et entre les f. 23 et 24), 1 cahier de 12 f. (f. 36-47), 1 cahier de 14 f. (f. 48-61), 1 cahier de 12 f. (f. 62-73), 1 cahier de 11 f. (f. 74-84, lacune de feuillets entre f. 81 et 82), 1 cahier de 18 f. (f. 85-102), 1 cahier de 14 f. (f. 103-116), 1 cahier de 13 f. (f. 117-129). - Cadre de la justification tracé à l’encre (ex. f. 3-14, 17-21), à la pointe sèche (ex. f. 15-16) ou à la mine de plomb (ex. f. 118v, 119v, 121v, 126v), 42-59 longues lignes (2 colonnes aux f. 66r, 120v-126r, 128v-129r, 3 colonnes et plus aux f. 2, 119-120r). - Reliure du XVe siècle restaurée, de veau brun sur ais de bois, estampée aux petits fers (fleurs de lys, fleurons, quadrilobes) et ornée de filets à froid ; traces de fermoirs. - Estampille Bibliothèque royale (Ancien Régime), début XVIIIe siècle, avant 1735 (Josserand-Bruno n° 5 et Laffitte pl. XX) : ex. f. 2\r\nDescription :  Numérisation effectuée à partir d'un document original : Latin 7197.\r\nDescription :  Mécénat : Numérisé dans le cadre du projet ALFA, Shaping a European scientific scene: Alfonsine astronomy (European Research Council, CoG, 723085), en coopération avec le CNRS.\r\nDescription :  F. [I]-1 (garde et contregarde). Tables du mouvement de la lune.F. 2r-v. Notes en latin et en allemand : « Invidia. Gregorius : Indivi alieno profectu...» (cf. f. 103v) ; « Sequitur de omnibus artibus. Die buchstaben lerr ich schriben...-... in der stat der meister sin. »F. 3r-8r. [JOHANNES DE SACROBOSCO], Algorismus de integris, avec gloses, tables et schémas : « Omnia que a primeva rerum origine… [F. 7r :] De radicum extractione in numeris quadratis quam cubicis...- … tam in numeris quadratis quam cubicis. Explicit algorismus de integris... » (cf. G. L’Huillier, Le Quadripartitum numerorum de Jean de Murs, Genève, 1990, p. 637). F. 9r-14v. Arithmétique en allemand et en latin, avec tables : « Wer meisterlich und kunstlich…-… et id quod remanet tot fuerunt [verte duo folia]. » F. 15r-16r.FRANCO DE POLONIA, Tractatus torqueti : « Incipit tractatus turketi editus a magistro Francone de Polonia parisius… De nominibus partium instrumenti… - …per se facile inveniet ex predictis. Explicit. Explicit modus composicionis turketi. » (cf. L. Thorndike, P. Kibre, A Catalogue of Incipits of Mediaeval Scientific Writings in Latin, Cambridge, 1963, 383). F. 16v. Notes de géométrie en latin, avec figures : « Item pro inveniendo centro circuli nota quod... Item alius modus super eodem sit circulus... »F. 17-20, 22-30r. Arithmétique en allemand et en latin (suite du f. 14v) : « [Ante duo folia] so weist wol daz du mit 7 solt sprechen... - ... so kumpt es wider [f. 20v]. [F. 22 :] Item ein man wil köffen ein schmitten... [F. 29v :] Recipiatur narratorium et sint 12 homines inter quos sint milites...- ... sic 30 darentur duo semiplenia. »F. 21r-v. Fragment de table de comput en latin : « Ad inveniendum litteram festorum mobilium per ciclum solarem... »F. 30r-31r. Algorismus de minutiis phisicis : « Incipit algorismus de minucys physicis. Quoniam opus tabularum sine scientia phisicarum minuciarum… - … ita se habens ad dividenda sicut gradus ad dividentem. Explicit algorismus de minucys physiciis. » (cf. L’Huillier, op. cit., p. 637).F. 31r-36v. [JEAN DE LIGNIERES], Algorismus de minutiis vulgaribus et phisicis, avec schémas : « Modum representacionis minuciarum vulgarium… - …3a 3arum etc. Et sic finitur algorismus de mynucys physicis et vulgaribus, etc. » (cf. L’Huillier, op. cit., p. 638).F. 36v-37v. [Algorismus linealis ] : « Pro expeditione specierum algorismi… [F. 37r :] Ad extrahendum fere singulas questiones numeros...-... unum miliarium sexta regula...Explicit. » (cf. S. Lamassé, « Une utilisation précoce de l’algèbre en France au XVe siècle. Note sur le manuscrit 1339 de la Bibliothèque nationale de France », Revue d’histoire des mathématiques, 11, 2005, p. 239-255 [p. 244]).F. 37v-38r. [Compositio et utilitates quadrantis veteris ] : « Quadrantis noticiam habere affectantes in tribus...-... habebis horam sicut prius etc. Explicit. » (cf. Emmanuel Poulle, La bibliothèque scientifique d'un imprimeur humaniste au XVe siècle : catalogue des manuscrits d'Arnaud de Bruxelles à la Bibliothèque nationale de Paris, Genève : Droz, 1963, p. 61). F. 38r. [De dominio planetarum in nativitatibus puerorum ] : « Si quis nascatur dum Saturnus...- …timidus luteique coloris. » (cf. Thorndike, Kibre, op. cit., 1461). Suivi d'une mappemonde en T-O (f. 38r).F. 39r-50r. JOHANNES DE SACROBOSCO, De sphera, avec gloses et figures : « Incipit tractatus de spera a magistro Johanne de Sacrobusco editus…Tractatum de spera quatuor capitulis distingwimus… - …aut tota mundi machina dissolutur. Explicit tractatus spere materialis per manus Conradi Heingarter. » (cf. L. Thorndike, The "Sphere" of Sacrobosco and its commentators, Chicago, 1949).F. 50r-v. Notes d'astronomie et d'arithmétique en latin, avec schémas : « Nota inveniendo dyametrum terre duo sunt modi practicandi... [F. 50v :] Item nota cape primam figuram inferius... » F. 51-57v.Theorica planetarum [Gerardi ], avec figures et gloses : « Circulus ecentricus vel egresse… - …planete et non totaliter. Explicit theorica planetarum. » (cf. Thorndike, Kibre, op. cit., 223).F. 58v-68v.JOHANNES DE SAXONIA , Canones in Tabulas Alfonsi : « Canones ad stellarum motus Johannis Saxoniensis in tabulas Alphoncy ordinati. Tempus est mensura motus, ut vult Aristoteles…-... adde sicut dixi et proveniet tempus equatum pro gradu ascendente inveniendo. Et sic est finis anno 1446 [biffé]. » (cf. Thorndike, Kibre, op. cit., 1561).F. 68v-71r. [M. T. CICERO. Oratio pro Marcello ] : « Diuturni silentii… - …Hoc tuo facto tumulus accesserit. Vale. Finis. »F. 71r-73v. [M. T. CICERO. Oratio pro Ligario ] : « Novum crimen C. Cesar… - …hys omnibus te daturum, etc. Finis illius orationis. »F. 74r-79v. [NICOLE ORESME], Algorismus proportionum, avec figures : « Una medietas scribitur sic ½… - …hec omnia patent in figuris subscriptis. Et est finis. » (cf. L’Huillier, op. cit., 638).F. 80r-81r. [Algorismus de proportionibus ] : « Quasdam regulas ad inveniendum numerum ignotum per notos sibi proportionales… - … isti versus stant pro quarta regula. Et sic est finis hujus oppusculi de inventione numerorum proportionalium ignotorum per numeros notos. »F. 81r-v. [PS. JEAN DE MURS, Arbor Boetii ] : « Nota Boecius 2° arithmetice tractatu 2° capitulo primo dicit integrorum eam disciplinam… - …Dico quod 256 continent... » (cf. Ch. Gack-Scheiding, Johannes de Muris, epistola super reformatione antiqui kalendarii : ein Beitrag zur Kalenderreform im 14. Jahrhundert, Hannover, 1995, p. 56).F. 82r. Note en latin : « Supposito quod aliquis diversas habeat res in manibus... »F. 82v-84r. [Divisiones Sacrae Scripturae ] : « Thelogia sive sacra scriptura dividitur in duas partes… - … et habet 22 capitula. »F. 85r-102r. Tables de comput portant mention de la ville de Prague et de l’année 1400.F. 102v. [Prognosticatio ] : « In libro Bereni de Multiloquio scribitur quod in revolutione annorum ipsorum temporum mundi... Merlinus : Mantua passeribus...»F. 103r. Notes d'arithmétique en allemand et en latin : « Item es sind gesellen oder als vil man wil hand... Item si vis scire quota pars denominationis est numerator... »F. 103v. Sentences bibliques et patristiques sur les vices et les vertus (cf. f. 2r) : « Devocio. Ibunt de virtute in virtutem...-... Gula... Jeronimus : Nihil adeo obnubilat intelligentiam ut commessacio et ebrietas. »F. 104r-112r. Tables astronomiques portant mention de l’année 1444. F. 112v-113v. [De astronomia ] : « Astronomie nucleos aliquot cupiens pandere… [F. 113v :] Pro noticia autem verorum motuum oportet habere augium cognitionem... - …in vera oppositione etc. » (cf. H. Hilg, Lateinische mittelalterliche Handschriften in Quarto der Universitätsbibliothek Augsburg : die Signaturengruppen Cod. I.2.4° und Cod. II. 1.4°, Wiesbaden : Harrassowitz, 2007, p. 408 : Cod. II.1.4°.61, f. 8v).F. 114r-115r. [Practica geometriae ] : « Geometrie due sunt species sive partes… - …et exiibit continencia. » (cf. Thorndike, Kibre, op. cit., 585).F. 115v. Notes d'astronomie et de comput en latin : « Nota motum cujuslibet planete... »F. 116r. Fragment de tables alphonsines : « Ad capiendum partem proportionalem in tabulis in quibus augmentum fit per sex gradus... » F. 118r. Schéma de classification du savoir selon HUGO DE SANCTO VICTORE, Didascalicon de studio legendi, III,1.F. 118r-129v. [HUGO DE SANCTO VICTORE], De Grammatica : « De Gramatica Sostenes. Quid est gramatica ? Gramatica est scientia recte loquendi… - ... [F. 118v :] aut legendo a preceptore accipere. Finis. [F. 119r :] Alphabetum hebraicum XXII littere …-... ledeamque Helenam Troianas vexit ad urbes. » (cf. G. L. Bursill-Hall, A Census of medieval Latin grammatical manuscripts, Stuttgart-Bad Cannstatt, cop. 1981, p. 191).F. 130-[I] (contregarde et garde). Tables des mouvements de la lune et du soleil.Il s'agit d'un manuscrit d’étudiant de l’astrologue et médecin d’origine suisse Conrad Heingarter, dont l'activité universitaire est documentée à partir du milieu des années 1450. Né à Horgen, au Sud du lac de Zurich, il est mentionné comme bénéficiaire du droit de bourgeoisie à Zurich en 1440. Il fut reçu bâchelier ès art à l’Université de Paris en 1454, licencié puis maître l’année suivante. Il compléta plus tard sa formation à la Faculté de médecine dont il obtint la licence et la maîtrise en 1466 (E. Wickersheimer, Dictionnaire biographique des médecins en France au Moyen âge, nouv. éd. sous la dir. de Guy Beaujouan, Genève : Droz ; Paris : Champion, 1979, I, 107). L’explicit du f. 68v comporte une date, néanmoins biffée (« Et sic est finis anno 1446 »), retenue comme date de copie par les auteurs du Catalogue des Manuscrits datés (Cat. Mss. datés, IV,1, 27). L’année 1446 fait l’objet de calculs astronomiques au f. 113v, au même titre que d’autres, notées en marge au fil du volume : « anno 1420 / anno 1448 / anno 1456 / anno 1504 » (f. 21), « …anno 1473 currenti… ad annum 1498 currentem… » (f. 61), « …usque ad annum 1498 complectum ultimo die decembris… » (f. 67v), « item licet 1456 non sit completum… » (f. 102v), « item anno 1456 ward … » (f. 103), « radix 1456 completus ultima die decembris…» (f. 104). Or, la majorité des filigranes du papier, y compris celui du f. 68, sont attestés dans les années 1455-1461, autorisant une datation postérieure à 1446. Ces années correspondent à celles où Heingarter étudiait à Paris et le papier employé semble confirmer que plusieurs des textes furent effectivement copiés dans la capitale. La date de 1446 pourrait alors correspondre à celle de l'exemplaire ayant servi de modèle au copiste.L’opuscule des f. 85 à 102 se distingue quant à lui par son écriture et par un papier attesté hors de France dès les années 1420 : il semble avoir été composé antérieurement par un copiste anonyme mais a été intégré au recueil par Heingarter qui l’a annoté au f. 102v.Gardes et contre-gardes proviennent d’un recueil de textes et tables astronomiques et portent mention des années 1340 à 1380, avec un explicit : « Explicit magister Petrus de Saxonia » (f. 1 v).Le décor du volume est manifestement de la main de Conrad Heingarter, ce dernier ayant laissé les initiales en attente pour la plupart des textes. L’initiale du f. 82v est d’une exécution faible, à la différence des schémas, beaucoup plus soignés. Il convient de noter la mappemonde en T-O du f. 38, portant la nomenclature des pays et des peuples des trois continents. Elle se caractérise par l’énumération en périphérie des douze vents, par la mention centrale de Jérusalem, ainsi que par la localisation de Babylone et du Paradis, d’où procèdent le Nil et le Tigre.\r\nDescription :  Lieu de copie : Paris.\r\nDroits  :  Consultable en ligne\r\nIdentifiant :  ark:/12148/btv1b52514099s\r\nSource  :  Bibliothèque nationale de France. Département des Manuscrits. Latin 7197	272	fol	f	https://gallica.bnf.fr/ark:/12148/btv1b52514099s/f1.planchecontact	bibliotheque-nationale-de-france-lat-7197	\N	\N	2023-03-23 17:29:25.621466+00	2023-03-23 17:29:25.621495+00	\N	1	\N	3
68	ms	lat. 7295A	itre :  Miscellanea astronomica\r\nAuteur  :  Campanus de Novare (12..-1296). Auteur du texte\r\nAuteur  :  Jacob ben Machir (1238?-1304?). Auteur du texte\r\nAuteur  :  Masha Allah (0730?-0815?). Auteur prétendu du texte\r\nAuteur  :  Danck, Johannes. Auteur du texte\r\nAuteur  :  Jean de Lignères. Auteur du texte\r\nDate d'édition :  1401-1500\r\nContributeur  :  Heingarter, Conrad. Copiste\r\nContributeur  :  Hardy, Claude (1604-1678). Ancien possesseur\r\nContributeur  :  Colbert, Jean-Baptiste (1619-1683). Ancien possesseur\r\nContributeur  :  Heingarter, Conrad. Ancien possesseur\r\nNotice du catalogue :  http://archivesetmanuscrits.bnf.fr/ark:/12148/cc664943\r\nType :  manuscrit\r\nLangue  :  latin\r\nFormat :  Paris. - Recueil d'étudiant en écriture cursive. Il fut composé et partiellement copié à son propre usage par l’astrologue et médecin d’origine suisse Conrad Heingarter. Celui-ci a sans doute écrit l'essentiel des f. 1-32v, ainsi que les f. 35-45, 49-93, 145-152 et 181-193v (cf. Cat. mss. datés, IV, 312), dont quelques passages en allemand (f. 64v-92) ou en grec (cf. explicit et souscription autographes en caractères grecs au f. 45). Il a également annoté certains textes probablement rédigés par d’autres copistes (ex. f. 99, 100, 164, 179-180). - Illustrations : Nombreux dessins ou schémas intercalés dans le texte, parfois en pleine page, d’astronomie, de cadrans solaires et d'horloge à eau (f. 41-42v) ou d’astrolabe (f. 50-64) : f. 2, 3v, 4v, 6v, 8, 8v, 11v, 15, 16, 18, 25v, 26v, 28, 29, 30, 32, 35, 35v, 36, 37, 37v, 41, 41v, 42, 50, 50v, 52, 53, 53v, 54, 55, 55v, 56, 56v, 57, 58, 58v, 59, 59v, 60, 61, 61v, 62v, 63, 63v, 64, 181v, 182v, 183v, 184, 185, 185v, 186, 187, 187v, 188, 191v, 192, 193v.2 dessins marginaux de petites dimensions : f. 35v (tête de femme coiffée d’un hennin), 52v (cheval).Ces dessins ont été réalisés à l'encre brune, parfois à l'aide d'un compas. - Décor :1 grande initiale puzzle rouge et bleu (12 interlignes), au champ filigrané de rouge et de noir, prolongée par un listel rouge et bleu encadrant la justification, au commencement du premier texte : f. 1.2 initiales puzzle de moyen ou petit module avec champ et antenne filigranés introduisant des subdivisions de deux des traités astronomiques : f. 4v (3 interlignes), 38 (9 interlignes).2 initiales filigranées de petit module (2-3 interlignes), introduisant la subdivision d’un traité sur les proportions et le début d’un traité sur l’astrolabe : f. 42v (bleue filigranée de rouge), 49 (rouge filigranée de brun). Initiales alternativement rouges et bleues (f. 1- 62), uniquement rouges (f. 115-144), rouges pommetées (f. 174-180v).Initiales rehaussées de jaune (f. 1-10) ou de rouge (f. 25-26), au fil du texte.Pieds-de-mouche alternativement rouges et bleus (f. 1-64v, 88-93) ou seulement rouges (f. 101-111,174-180v). Mains nota : ex. f. 10v, 107v, 110, 178v, 179v.Initiales non réalisées aux f. 140, 141v-143, 182-190r, 191-193v. - Quelques marques préparatoires au décor sont encore visibles : lettres d’attente (f. 2-8v, 35-45, 49-62, 190, 191v), indications pour la rubrication (numéros de chapitres : f. 102v-108v), piqûres pour le tracé des tables (f. 76-86, 115-140, 145-154, 155-173), trous de compas (ex. f. 61-64). - Papier (filigranes : tête de bœuf surmontée d’une tige [ex. f. 76, 79, 95] proche de Briquet n° 15067, attesté à Pont-à-Mousson en 1459 ; écu avec une fleur de lys [ex. f. 50, 55] proche de Briquet n° 1527, attesté à Paris en 1458 ; écu avec 1 fleur de lys surmonté d’une croix [ex f. 10, 26, 34] proche de Briquet n° 1548, attesté à Châteaudun en 1463 ; écu avec trois fleurs de lys surmonté d’une couronne [ex. f. 64, 67, 181] proche de Briquet n° 1683-1684, attestés à Paris en 1456-1460 ; lettre P [ex. f. 47] proche de Briquet n°9167, attesté à Paris en 1461 ; main [ex. f. 100, 127] identique à Briquet n°11475, attesté à Paris en 1451-1458). - 193 f., précédés et suivis de 2 f. de garde de papier moderne. - 290 × 210 mm (justification 200-250 × 130-160 mm). - 17 cahiers :- 2 cahiers de 12 f. chacun (f. 1-12, 13-24) + 1 cahier de 10 f. (f. 25-34 ; les f. 33-34 sont blancs) ;- 1 cahier de 6 f. (f. 35-40) ; - 1 cahier de 8 f. (f. 41-48 ; les f. 46-48 sont blancs) ;- 1 cahier de 12 f. (f. 49-60) + 1 cahier de 14 f. (f. 61-74) + 2 cahiers de 12 f. chacun (f. 75-86, 87-98 ; les f. 94-98 sont blancs) ;- 1 cahier de 16 f. (f. 99-114) ;- 1 cahier de 13 f. (f. 115-127, f. 115 formé de 2 f. collés) + 1 cahier de 12 f. (f. 128-139 + 1 papillon inséré entre les f. 131-132 et un autre entre les f. 135-136) + 1 cahier de 5 f. (f. 140-144 + 1 feuillet collé au f. 139) ;- 1 cahier de 10 f. (f. 145-154 ; les f. 153-154 sont blancs) ;- 1 cahier de 12 f. (f. 155-166) + 1 cahier de 14 f. (f. 167-180) + 1 cahier de 13 f. (f. 181-193).Réclames (f. 12v, 24v) ; cahiers signés au recto inférieur droit des bifeuillets (f. 61-65, 68, 75-81 : une lettre par cahier suivie du numéro du bifeuillet) ; numérotation des bifeuillets dans l’angle supérieur droit aux f. 101-106 ; tables astronomiques des f. 78v à 86v numérotées à rebours de t à c au bas de chaque page. - Cadre de la justification tracé à l’encre, 36-46 longues lignes (f. 1-93), 44- 47 lignes sur deux colonnes (f. 99-111) ou 55-61 lignes sur deux colonnes (f. 174-180v, 181-193). - Demi-reliure Charles X, titre au dos « VARIA/DE/ ASTRONOMICA » (relieur : Lefebvre 15/11/1828). - Estampille : Bibliothèque royale (Ancien Régime), début du XVIIIe siècle, avant 1735 (Josserand-Bruno n° 5 et Laffitte pl. XX) : ex. f. 1\r\nDescription :  Numérisation effectuée à partir d'un document original : Latin 7295A.\r\nDescription :  F. 1r-32v. [CAMPANUS DE NOVARE, Theorica planetarum], avec figures : « Primus phylosophie magister…-… de Mercurio supra diximusque. Explicit. » (cf. F. S. Benjamin, G. J. Toomer, Campanus of Novara and medieval planetary theory, 1971, 83). F. 35r-40v.PROFATIUS JUDAEUS, De armillis : « De Sole. Solis instrumentum sic faciemus... - ... tantum filum equantis per successionem signorum. Et sic completum est opus nostrum ad preces venerabilis magistri B. de Gordonio doctoris excellentissime in arte medicine in Montepessulano. Explicit de armillis Profacy. » (cf. L. Thorndike, « Date of Peter of St Omer's revision of the New Quadrant of Profatius Judaeus », Isis, 51/2 (1960), p. 204-206, p. 206 n. 12 ; E. Poulle, Équatoires et horlogerie planétaire, 1980, 66). F. 41r-42r. [De horologiis in trunco faciendis], avec figures : « Notandum pro horalogys in trunco faciendis…-… verificatorium ad omnes practicas horalogy trunci etc. Et sic est finis trunci. » (cf. L. Thorndike, P. Kibre, A Catalogue of Incipits of Mediaeval Scientific Writings in Latin, 1963, 949). F. 42v-45r.Arithmetica de rerum ac numerorum proportionibus : « Incipit arithmetica de rerum ac numerorum proprietationibus. Secuntur regule artificiales quibus fere totum factum...-... in principio tanto prescisius invenies et magis quam etc. » (cf. Thorndike, Kibre, op. cit., 1437). F. 49r. [De quantitate cujuslibet lineae sive partibus proportionalibus ] : « Si vis scire quantitatem cuiuslibet linee sive partes proportionales...-... aliarum quantitatum mensurabilium in longum, latum et profundum. »F. 49r-64r. PS.-MESSAHALA, De astrolabio, avec figures : « Incipit astrolabium Messahale phylosophi. Scito quod astrolabium est nomen grecum...-... et nota illa est polus zodiaci ut patet in hac figura etc. Explicit compositio astrolabii. » (cf. E. Poulle, « L’astrolabe médiéval d’après les manuscrits de la Bibliothèque nationale », Bibliothèque de l’Ecole des chartes, 112 (1954), p. 81-103, 101 ; F. J. Carmody, Arabic astronomical and astrological sciences in Latin translation : a critical bibliography, Berkeley : University of California press, 1956, 25). F. 64v-92r.Sex alarum (texte en allemand accompagné de tables astronomiques) : « Hie wil ich anfachen bescheiden den sechs fettich…-…die 24 mol 47 minutis die dosint etc. Explicit sex alarum magister. » F. 92v-93r.De proportionibus : « Notandum quod habendo aliquid de modo proferendi…-…secundus termynus secundi numeri ad suum tertium ut 8, 4, 2 - 4, 2, 1. Et sic est finis de proportionibus. Finis Deo gratias. »F. 99, 114r. [Canon planetarum] : « Ad intelligendum tabulas astronomie necessario opportet scire Quid sit radix planete… [F. 114r :] Latitudo civitatis alicuius vel loci...-…super quam Ptholomeus composuit almagestam suam. » (cf. Thorndike, Kibre, op. cit., 48). F. 101r-111v. JOHANNES DE SAXONIA, Canones super Tabulas Alfonsi : « Canones super tabulas Alfoncii olim regis Castelle. Tempus est mensura motus ut vult Aristoteles...-... et non errabis Deo gracias. Expliciunt canones super tabulas Alfoncii. » (cf. Thorndike, Kibre, op. cit., 1561). F. 112r-113v. [Fragment de tables toledanes] : « Ascensiones ad 48 graduum latitudinem…-…Residua pars tabule ascensionum signorum sexti climatis. » (cf. G. J. Toomer, « A Survey of the Toledan Tables. », Osiris, 15 (1968), p. 5-174, 41). F. 115r-144r. Tabulae astronomicae Alphonsi Regis Castellae : « Incipiunt tabule Alfoncii olym regis Castelle illustris... »F. 145r-152r. Tables astronomiques sur le modèle du méridien d’Oxford : « Prima tabula continens veram latitudinem Saturni ab orbe signorum pro omni loco et tempore in Oxonia constituta. » F. 155r-171v.JEAN DE LIGNIERES, Tabulae astronomicae : « Incipiunt tabule magistri Johannis de Lineriis... » (cf. Thorndike, Kibre, op. cit., 1553, 8). F. 174r-180v.JEAN DE LIGNIERES, Canones : « Priores astrologi motus corporum celestium...-... Si autem ultra 6 signa in 12 et sic in ortu vespertino et reliqua utraque in canone si compleatur. // Matutino // Hic deficiunt canones quinque scilicet 41us, 42us, 43us, 44us et quadragesimus quintus. » (cf. Thorndike, Kibre, op. cit., 1127).F. 181r.JEAN DE LIGNIERES, Canones primi mobilis : « Cum volueris scire varios colores eclipsis aspice longitudinem...-... inter se equipollentium vel latitudinis equipollentis, etc. Expliciunt canones primi mobilis magistri Johannis de Lineriis finiti Wienensi studio. » (cf. Thorndike, Kibre, op. cit., 357). F. 181r-v. Notes d'astronomie en latin, avec figure : « Nota secundum Alfraganum centrum ecentrici solis distat a centro terre...-... denominatoris dividentis a denominatore divise. Figura eclipsis solaris. » F. 182-193v. [Canones], avec figures : « [A]rabes maxime secundum motum lune tempora distinguentes… [F. 186r :] Ad inveniendum medios motus planetarum in tabulis Tholetanis eadem est operatio quam in tabulis Anphoncii…-… transitum lune ab inicio eclipsis usque ad finem. Et hec omnia patent ni figura sequenti. Figura eclipsis solaris. » (dont quelques passages adaptés des canons « Quoniam cujusque actionis » des Tables toledanes, cf. F. S. Pedersen, The Toledan tables, 2002, Cb 07 et suiv. et p. 157 ; cf. Thorndike, Kibre, op. cit., 124).Il s'agit d'un manuscrit d’étudiant de l’astrologue et médecin d’origine suisse Conrad Heingarter, dont l'activité universitaire est documentée à partir du milieu des années 1450. Né à Horgen, au Sud du lac de Zurich, il est mentionné comme bénéficiaire du droit de bourgeoisie à Zurich en 1440. Il fut reçu bâchelier ès art à l’Université de Paris en 1454, licencié puis maître l’année suivante. Il compléta plus tard sa formation à la Faculté de médecine, dont il obtint la licence et la maîtrise en 1466 (cf. E. Wickersheimer, Dictionnaire biographique des médecins en France au Moyen Âge, nouv. éd. sous la dir. de Guy Beaujouan, Genève : Droz ; Paris : Champion, 1979, I, 107). Plusieurs mentions de dates apparaissent dans des annotations et certaines sont citées au passé : « …anno Christi 1462° currente… », « Item anno 1473 currente… », « …anno Christi 1482° currente… » (f. 88r) ; « Nota anno 1461 habuerunt Judei 15 pro aureo numero… » (f. 88v) ; « …anno 1427°… » (f. 100) ; « Anno Christi 1499 » (f. 110v), etc. Les divers filigranes du papier sont attestés à Paris dans le troisième quart du XVe s, entre 1450 et 1465, ce qui correspond aux années où Heingarter étudiait dans la capitale. Les schémas sont vraisemblablement de la main de Conrad Heingarter, en dépit des divers copistes qui sont intervenus dans ce volume : la plupart des dessins sont homogènes et ne diffèrent pas, sous le rapport de l’exécution ni de l’écriture, de ceux de l’autre manuscrit d’étude de Heingarter conservé au département des Manuscrits de la Bibliothèque nationale de France (ms. Latin 7197).\r\nDescription :  Lieu de copie : Paris\r\nDroits  :  Consultable en ligne\r\nIdentifiant :  ark:/12148/btv1b10027322j\r\nSource  :  Bibliothèque nationale de France. Département des Manuscrits. Latin 7295A	410	fol	f	https://gallica.bnf.fr/ark:/12148/btv1b10027322j/f1.planchecontact	bibliotheque-nationale-de-france-lat-7295a	\N	\N	2023-03-23 17:32:44.978897+00	2023-03-23 17:32:44.978933+00	\N	1	\N	3
69	ms	lat. 7417	itre :  1.° Compositiones instrumentorum astronomicorum, unà cum eorumdem usu et utilitate : authore Nicolao Guglero. — 2.° Compositio theoricarum planetarum : authore Philippo Imsero, astronomiae Professore Tubingae. — 3.° Structura instrumenti imaginatorii theoricae solis : authore Nicolao Guglero — 4.° Compositio instrumenti primi mobilis. — 5.° Astrolabii compositio de projectione sphaerae in planum : authore Philippo Impsero. — 6.° Anonymi tractatus de orbibus coelestibus. — 7.° Philippi Imseri annotationes in tabulas resolutas, et in tabulas directionum. — 8.° Nicolai Gugleri prognosticon. — 9.° Joannis Schoveri chirographus ; sive nativitas Joannis Schoveri, quam ipse scripsit. — 10.° Erasmi Doppler, anno 1462. nati, horoscopium : authore Joanne Wernero, Mathematico. — 11.° Nicolai Gugleri opusculum de cometis. — 12.° Laurentii Bonicontrii tractatus de revolutionibus nativitatum. — 13.° Joannis Haffurt, medicinae Doctoris, tractatus de judicio urinae.\r\nDate d'édition :  1539\r\nNotice du catalogue :  http://archivesetmanuscrits.bnf.fr/ark:/12148/cc66637x\r\nType :  manuscrit\r\nLangue  :  latin\r\nFormat :  Papier\r\nDescription :  Numérisation effectuée à partir d'un document de substitution.\r\nDroits  :  Consultable en ligne\r\nIdentifiant :  ark:/12148/btv1b9080835g\r\nSource  :  Bibliothèque nationale de France. Département des Manuscrits. Latin 7417	360	fol	f	https://gallica.bnf.fr/ark:/12148/btv1b9080835g/f1.planchecontact.r=theorica%20planetarum	bibliotheque-nationale-de-france-lat-7417	\N	\N	2023-03-23 17:37:31.502854+00	2023-06-13 08:23:39.955528+00	\N	1	\N	3
70	ms	lat. 16649	Titre :  Miscellanea mathematica et astronomica\r\nAuteur  :  Archimedes Syracusanus (0287-0212 av. J.-C.). Auteur du texte\r\nAuteur  :  Jordanus Nemorarius (12..-12..). Auteur du texte\r\nAuteur  :  Euclides (0323-0285 av. J.-C.). Auteur prétendu du texte\r\nAuteur  :  Hieronimus de Hassia ( ?). Auteur du texte\r\nAuteur  :  Petrus Peregrinus de Maricourt. Auteur du texte\r\nAuteur  :  Albertus Magnus (saint ; 1200?-1280). Auteur présumé du texte\r\nAuteur  :  Johannes Eligerus. Auteur du texte\r\nAuteur  :  Johannes de Gmunden. Auteur du texte\r\nAuteur  :  Masha Allah (0730?-0815?). Auteur prétendu du texte\r\nDate d'édition :  1501-1600\r\nDate d'édition :  1519\r\nContributeur  :  Collège de Sorbonne (Paris). Ancien possesseur\r\nNotice du catalogue :  http://archivesetmanuscrits.bnf.fr/ark:/12148/cc770708\r\nType :  manuscrit\r\nLangue  :  latin\r\nLangue  :  français\r\nFormat :  Nombreuses réserves et lettres d’attente. Aux f. 103-160 : nombreux diagrammes. F. 103 : une boussole sur parchemin a été fixée au feuillet de papier grâce à un nerf lui permettant de tourner, on peut lire au-dessous : « De artificio rote perpetui motus ». F. 105v, 107r, 107v, 109v, 115v, 116v, 119r, 123v, 126v, 128r, 129 passim: figures représentant pour la plupart des instruments astronomiques tels que le quadrant ou l’astrolabe. - Papier. - 194 feuillets. - 190x135mm. - Reliure en peau chamoisée beige. Une trace d’enchaînement est également visible en marge supérieure du contreplat\r\nDescription :  Numérisation effectuée à partir d'un document de substitution.\r\nDescription :  Archimedes, De mensura circuli (ff. 1r-4v) ; Jordanus Nemorarius, De ponderibus (ff. 6r-9r) ; Ps. Euclides, Liber de ponderoso et levi, quattuor propositiones (f. 9) ; Ps. Euclides, Liber de ponderoso et levi (ff. 9v-10v) ; Divinationes Petri secundum algorismum (ff. 11r-20v) ; Propositiones Elementis (ff. 39r-40v) ; Theorica planetarum Gerardi (ff. 41r-50r) ; De compositione Quadrantis Veteris (ff. 50v-53v) ; De usu quadrantis (ff. 54r-56r) ; Compositio et utilitates astrolabii spherici (ff. 56v-71) ; Magister Hieronimus de Hassia ( ?), De ortu et occasu signorum (ff. 73r-93v) ; Petrus Peregrinus de Maricourt, De magnete (ff. 94r-106r) ; De horologio (ff. 106v-109v) ; Albertus Magnus Commentum supra Minerabilia lib. III cap. 8-9 (ff. 110r-112r) ; Compositio horologii nocturni (f. 112v-113r) ; De compositione et usu cylindri (ff. 113r-116r) ; Traité de composition du quadrant en français (ff. 117r-127v) ; De usu quadrantum (ff. 128r-159r) ; Johannes Eligerus, De compositione quadrantis novi (ff. 165r-169r) ; Johannes de Gmunden, De compositione cylindri vel horologii viatorum (ff. 169r-170v) ; Compositio astrolabii nova (ff. 170v-175v) ; Johannes Eligerus, De usu quadrantis novi (ff. 175v-181r) ; Canones chilindri de altitudine solis (f. 181) ; Ps. Messahala, De usu astrolabii (ff. 181v-189v).\r\nDroits  :  Consultable en ligne\r\nIdentifiant :  ark:/12148/btv1b90726517\r\nSource  :  Bibliothèque nationale de France. Département des manuscrits. Latin 16649	218	fol	f	https://gallica.bnf.fr/ark:/12148/btv1b90726517/f1.planchecontact.r=theorica%20planetarum	bibliotheque-nationale-de-france-lat-16649	\N	\N	2023-03-23 17:41:21.678566+00	2023-03-23 17:41:21.678603+00	\N	1	\N	3
75	ms	Carullah 2060	various works of astronomy and mathematics, many by ʿAlī Qūshjī\r\n\r\n2060/1 (fols. 1b-35a) = Sharḥ al-Tuḥfa al-Shāhiyya (Commentary on [Quṭb al-Dīn al-Shīrāzī's] al-Tuḥfa al-shāhiyya) by ʿAlī Qūshjī\r\n\r\n2060/6 (fols. 133a-135b) = Risāla fī ḥall ishkāl al-muʿaddil li-l-masīr (Treatise Regarding the Solution of the Equant Problem) by ʿAlī Qūshjī	174	fol	f		carullah-2060	\N	\N	2023-04-03 09:42:04.554382+00	2023-05-24 14:34:46.51632+00	\N	13	\N	11
76	ms	Ayasofya 2614	title: Kitāb fī al-hayʾa (Book on Astronomy)\r\nanonymous work on astronomy\r\nwitness dates to before 1512, bears the seal of Ottoman Sultan Bayezid II	105	fol	f		ayasofya-2614	\N	\N	2023-04-03 10:03:43.52266+00	2023-05-25 13:44:16.638722+00	\N	13	\N	11
77	ms	Landberg 720	title: Ḥāshiya ʿalā Sharḥ al-Mulakhkhaṣ [Gloss on (Qāḍīzāde al-Rūmī's) Commentary on (Jaghmīnī's) Mulakhkhaṣ]\r\n\r\nold shelfmark: Ahlwardt 5677\r\n\r\nIIIF manifest download: https://content.staatsbibliothek-berlin.de/dc/646157701/manifest	152	fol	f	http://resolver.staatsbibliothek-berlin.de/SBB0000411900000000	landberg-720	\N	\N	2023-04-03 10:23:55.743075+00	2023-10-24 09:54:49.948303+00	\N	5	\N	11
78	ms	Samsun 810	title: Sharḥ al-Tadkira (Commentary on [Naṣīr al-Dīn al-Ṭūsī's] Tadhkira)	439	fol	f		samsun-810	\N	\N	2023-04-03 13:09:34.523002+00	2023-07-12 09:46:06.770955+00	\N	2	\N	11
79	ms	Arab SM4285	title: Sharḥ al-Tadhkira (Commentary on [Naṣīr al-Dīn al-Ṭūsī's] Tadhkira)	258	fol	f	https://nrs.lib.harvard.edu/urn-3:fhcl.hough:2920118	arab-sm4285	\N	\N	2023-04-03 13:17:27.310476+00	2023-06-27 08:21:49.534618+00	\N	11	\N	11
80	ms	IO Islamic 681	title: Sharḥ Taḥrīr al-Majisṭī (Commentary on [Naṣīr al-Dīn al-Ṭūsī's] Recension of the Almagest)	369	fol	f	https://www.qdl.qa/en/archive/81055/vdc_100030968238.0x000001	io-islamic-681	\N	\N	2023-04-03 13:24:56.089229+00	2023-07-03 09:22:20.419623+00	\N	18	\N	11
81	ms	Add MS 7473	Collection of twenty treatises (plus shorter notes and excerpts) relating to mathematics, philosophy, history and related subjects, including a number of Graeco-Arabic texts, including:\r\n\r\n(11) Ptolemy, Kitāb fī al-hay’ah al-musammá al-iqtiṣāṣ (Planetary Hypotheses) (ff. 81v-102v);\r\n\r\n(12) Zarqālī, Kitāb al-‘aml bil-ṣafīḥah al-zījīyah (On the Use of the Safīḥa/Saphaea) (ff. 103r-107v);	198	fol	f	https://www.qdl.qa/en/archive/81055/vdc_100023601232.0x000001	add-ms-7473	\N	\N	2023-04-03 13:41:10.690152+00	2023-12-04 14:26:51.279922+00	\N	18	\N	11
82	ms	Add MS 23397	Three astronomical commentaries:\r\n\r\n(1) al-Jurjānī, ʿAlī ibn Muḥammad, Sharḥ al-Mulakhkhaṣ fī al-hayʾah (Commentary on [Jaghmīnī's] Mulakhkhaṣ), ff. 4v-52r\r\n\r\n(2) al-Turkmānī, Kamāl al-Dīn, Sharḥ al-Mulakhkhaṣ fī al-hayʾah (Commentary on [Jaghmīnī's] Mulakhkhaṣ), ff. 53v-109r\r\n\r\n(3) al-Nīsābūrī, al-Ḥasan ibn Muḥammad, Tawḍīḥ al-Tadhkirah al-Nāṣirīyah (Commentary on Naṣīr [al-Dīn al-Ṭūsī's] Tadhkira), ff. 110v-364v	364	fol	f	https://www.qdl.qa/en/archive/81055/vdc_100023444610.0x000001	add-ms-23397	\N	\N	2023-04-03 13:49:01.657801+00	2023-07-03 12:25:19.172021+00	\N	18	\N	11
83	ms	Or 7368	Commentary on Ptolemy's Almagest said to be by al-Fārābī, but in fact by Ibn Sīnā/Avicenna	106	fol	f	https://www.qdl.qa/en/archive/81055/vdc_100022625065.0x000001	or-7368	\N	\N	2023-04-03 14:03:32.265275+00	2023-07-03 08:35:03.277205+00	\N	18	\N	11
84	ms	Arabe 2501	title: al-Mulakhkhaṣ fī al-hayʾa al-basīṭa (Epitome of Plain/Simplified Hayʾa)	58	fol	f	https://gallica.bnf.fr/ark:/12148/btv1b100374835	bibliotheque-nationale-de-france-arabe-2501	\N	\N	2023-04-03 14:15:04.903612+00	2023-06-27 11:27:26.502838+00	\N	1	\N	11
85	ms	Arabe 2504	Compendium of 5 astronomical texts\r\n\r\n1° al-Mulakhkhaṣ fī al-hayʾa al-basīṭa by al-Jaghmīnī\r\n\r\n2° (Fol. 24 v°) Sharḥ al-Mulakhkhaṣ (Commentary on [Jaghmīnī's] Mulakhkhaṣ) by Qāḍīzāde al-Rūmī\r\n\r\n3° (Fol. 116 v°) Kitāb al-Hayʾa (Book of Astronomy) by al-Farghānī\r\n\r\n4° (Fol. 145 v°) al-Risāla al-Fatḥiyya by ʿAlī al-Qūshjī\r\n\r\n5° (Fol. 174 v°) Commentary on [Qūshjī's] al-Risāla al-Fatḥiyya, by Mirim Çelebi	268	fol	f	http://archivesetmanuscrits.bnf.fr/ark:/12148/cc30421s	bibliotheque-nationale-de-france-arabe-2504	\N	\N	2023-04-03 14:28:14.74991+00	2023-06-28 09:13:10.734798+00	\N	1	\N	11
86	ms	Coisl. 174	Diktyon ID: 49313.\r\n\r\nManuscript on paper. \r\n\r\nPrevious owners include Demetrios Chalkokondyles (1423-1511), who lived in Florence (1475-1491) and moved to Milan afterwards. His son, Seleukos Chalkokondylos sold the manuscripts of his father thorugh the help of Daniele Gaetani during the 1520s.  Daniele Gaetani (1460-1528) acquiered the codex in Milan in 1527.  Cardinal Giovanni da Salviati (1490-1553), who inherited part of Gaetani's library. Pierre Séguier (1588-1672) whose library was inherited by his nephew Henri-Charles du Cambout, duc de Coislin (1665-1732). He gave his manuscripts to the Abbey of Saint-Germain-des-prés (Paris) in 1720.	411	fol	f	https://gallica.bnf.fr/ark:/12148/btv1b10038055n	bibliotheque-nationale-de-france-coisl-174	\N	\N	2023-04-04 08:21:57.959342+00	2023-12-01 14:49:01.516246+00	\N	1	\N	5
87	ms	Suppl. gr. 682	Diktyon ID: 53417.\r\n\r\nManuscript on paper and parchment. \r\n\r\nPrevious owners include Konstantinos Minas Minoides (ca. 1790-1860).	131	fol	f	https://gallica.bnf.fr/ark:/12148/btv1b110047250	bibliotheque-nationale-de-france-suppl-gr-682	\N	\N	2023-04-04 08:26:12.659111+00	2023-06-28 09:49:40.426024+00	\N	1	\N	5
88	ms	Suppl. gr. 651	Diktyon ID: 53386.\r\n\r\nManuscript on paper. \r\n\r\nPrevious owners include Konstantinos Minas Minoides (ca. 1790-1860).	43	fol	f	https://gallica.bnf.fr/ark:/12148/btv1b11004380q	bibliotheque-nationale-de-france-suppl-gr-651	\N	\N	2023-04-04 08:29:06.592872+00	2023-04-13 08:46:38.216749+00	\N	1	\N	5
89	ms	Or. 2541	Collective volume with the following texts or fragments of texts: \r\n\r\n[1], pp. 1-26: Tarkīb al-aflāk, an astronomical treatise in Arabic with many diagrams, by Aḥmad ibn Muḥammad al-Sijzī (d. c. 1084). This first text is signed and dated on page 26 by the copyist ʿAbd Allāh ibn Aḥmad al-Shushtarī on Tuesday 28 Rabīʿ I of the year 646 (= 8 November 1238)\r\n\r\n[2], pp. 27-31: a fragment of Kitāb al-talwīḥāt, an Arabic treatise on logic, physics and metaphysics by Yaḥyá ibn Ḥabash al-Suhrawardī (c. 1154-1191)\r\n\r\n[3], pp. 32-37: a fragment of al-Risāla al-Muʿīnīyah, a work in Persian on cosmology by Naṣīr al-Dīn al-Ṭūsī (1201-1274)	37	pag	f	http://hdl.handle.net/1887.1/item:1572906	or-2541	\N	\N	2023-04-05 10:00:46.58086+00	2023-04-05 10:00:46.580897+00	\N	17	\N	11
90	ms	Or. 188/4	title: al-Tadhkira fī ʿilm al-hayʾa\r\nalternate title: at-Taḏkira an-Nāṣiriyya fī ʿilm al-Haiʾa	111	fol	f	http://hdl.handle.net/1887.1/item:3416108	or-1884	\N	\N	2023-04-05 11:41:25.969068+00	2023-10-24 10:07:09.627132+00	\N	17	\N	11
91	ms	Or. 174/1	title: al-Tabṣira fī ʿilm al-hayʾa	62	fol	f	http://hdl.handle.net/1887.1/item:3419583	or-1741	\N	\N	2023-04-05 11:46:29.038827+00	2023-04-05 11:46:29.038851+00	\N	17	\N	11
92	ms	Or. 202/3	title: Sharḥ al-Mulakhkhaṣ fī al-hayʾa (Commentary on [Jaghmīnī's] Mulakhkhaṣ)	\N	fol	f	http://hdl.handle.net/1887.1/item:3411841	or-2023	\N	\N	2023-04-05 11:56:25.418509+00	2023-06-15 15:12:16.164842+00	\N	17	\N	11
93	ms	Or. 234/4	title: Sharḥ al-Mulakhkhaṣ fī al-hayʾa (Commentary on [Jaghmīnī's] Mulakhkhaṣ)	\N	fol	f	http://hdl.handle.net/1887.1/item:3401186	or-2344	\N	\N	2023-04-05 11:58:41.959417+00	2023-06-28 08:32:50.445736+00	\N	17	\N	11
94	ms	Or. 234/1	title: al-Mulakhkhaṣ fī al-hayʾa (Epitome of Astronomy)	\N	fol	f	http://hdl.handle.net/1887.1/item:3401440	or-2341	\N	\N	2023-04-05 12:23:50.148591+00	2023-04-05 12:23:50.148608+00	\N	17	\N	11
95	ms	Or. 234/3	title: Sharḥ al-Mulakhkhaṣ fī al-hayʾa (Commentary on [Jaghmīnī's] Mulakhkhaṣ)	\N	fol	f	http://hdl.handle.net/1887.1/item:3401306	or-2343	\N	\N	2023-04-05 12:26:02.694196+00	2023-04-05 12:26:02.694211+00	\N	17	\N	11
97	ms	Ayasofya 2645	title: Sharḥ al-Tadhkira (Commentary on [Ṭūsī's] Tadhkira)\r\n\r\nNote at the bottom of fol. 132a states the manuscript was collated against an autograph witness in October 1413	132	fol	f		ayasofya-2645	\N	\N	2023-04-05 14:18:08.936147+00	2023-05-23 07:29:53.067804+00	\N	13	\N	11
98	ms	H Husnu Paşa 1276	title: Sharḥ al-Tadhkira (Commentary on [Ṭūsī's] Tadhkira)	208	fol	f		h-husnu-pasa-1276	\N	\N	2023-04-05 14:21:50.641689+00	2023-05-25 12:51:55.84137+00	\N	13	\N	11
99	ms	Arabe 2499	title: Muntaha al-Idrāk fī Taqāsīm al-Aflāk (The utmost attainment in the configuration of the orbs)	156	fol	f	https://archivesetmanuscrits.bnf.fr/ark:/12148/cc30416s	bibliotheque-nationale-de-france-arabe-2499	\N	\N	2023-04-05 14:37:13.960142+00	2023-06-26 13:33:19.414163+00	\N	1	\N	11
100	ms	Ayasofya 2581	title: al-Tabṣira fī ʿilm al-hayʾa	155	fol	f		ayasofya-2581	\N	\N	2023-04-05 14:46:04.482332+00	2023-05-23 07:27:08.51736+00	\N	13	\N	11
101	ms	Add MS 7476	title: Sharḥ Taḥrīr al-Majisṭī  (Commentary on [Ṭūsī's] Recension of the Almagest)\r\nalternate title: Tafsīr al-Taḥrīr	343	fol	f	https://www.qdl.qa/en/archive/81055/vdc_100023403504.0x000001	add-ms-7476	\N	\N	2023-04-05 15:11:09.649354+00	2023-07-03 12:45:22.896418+00	\N	18	\N	11
102	ms	Landberg 493	title: Sharḥ Taḥrīr al-Majisṭī (Commentary on [Ṭūsī's] Recension of the Almagest)	224	fol	f	http://resolver.staatsbibliothek-berlin.de/SBB0000411400000000	landberg-493	\N	\N	2023-04-05 15:15:12.337617+00	2023-10-24 10:45:01.094434+00	\N	5	\N	11
103	ms	Fatih 3396	title: Tawḍīḥ al-Tadhkira (Elucidation of [Ṭūsī's] Tadhkira)	131	fol	f		fatih-3396	\N	\N	2023-04-05 15:23:46.048479+00	2023-05-30 08:00:16.778368+00	\N	13	\N	11
104	ms	Fatih 3397	title: Tawdīḥ al-Tadhkira (Elucidation of [Ṭūsī's] Tadhkira)\r\n\r\nwitness collated against an autograph witness	115	fol	f		fatih-3397	\N	\N	2023-04-05 15:28:36.480019+00	2023-06-02 12:12:03.755745+00	\N	13	\N	11
105	ms	Yeni Cami 792	title: Tawḍīh al-Tadhkira (Elucidation of [Ṭūsī's] Tadhkira)	171	fol	f		yeni-cami-792	\N	\N	2023-04-05 15:30:30.010582+00	2023-06-02 09:32:04.843751+00	\N	13	\N	11
106	ms	Suppl. gr. 1189	Diktyon ID: 53867.\r\n\r\nManuscript on paper.	7	fol	f	https://gallica.bnf.fr/ark:/12148/btv1b525013448	bibliotheque-nationale-de-france-suppl-gr-1189	\N	\N	2023-04-07 08:25:24.271814+00	2023-06-26 08:23:57.803661+00	\N	1	\N	5
107	ms	gr. 2419	Diktyon ID: 52051.\r\n\r\nThe manuscript is in two volumes, but it has one shelfmark and one Diktyon number. Each volume is digitized separately and has its own IIIF manifest. \r\n\r\nVol. 1: https://gallica.bnf.fr/iiif/ark:/12148/btv1b10723563z/manifest.json\r\nVol. 2: https://gallica.bnf.fr/iiif/ark:/12148/btv1b10723580f/manifest.json\r\n\r\nExternal link Vol. 1: https://gallica.bnf.fr/view3if/ga/ark:/12148/btv1b10723563z\r\nExternal link Vol. 2: https://gallica.bnf.fr/view3if/ga/ark:/12148/btv1b10723580f\r\n\r\nManuscript on paper. \r\n\r\nPrevious owners include Niccolò Ridolfi (1501-1550), after his death his books were purchased by Piero Strozzi.	342	fol	f	https://gallica.bnf.fr/view3if/ga/ark:/12148/btv1b10723563z	bibliotheque-nationale-de-france-gr-2419	\N	\N	2023-04-07 08:34:04.227438+00	2023-06-27 14:04:29.538565+00	\N	1	\N	5
108	ms	Chinois 4931	Figures de l'éclipse de lune du 7 avril 1735. Textes mantchou et Chinois ; figures de l'éclipse pour diverses provinces.	11	oth	f		bibliotheque-nationale-de-france-chinois-4931	\N	\N	2023-04-11 08:32:16.227117+00	2023-11-28 19:09:16.251791+00	\N	1	\N	16
109	ms	Chinois 4950	崇禎暦書·治暦緣起 Chong zhen li shu-Zhi li yuan qi. Collection relative au calendrier, années Chong zhen: L'origine du calendrier	427	oth	f		bibliotheque-nationale-de-france-chinois-4950	\N	\N	2023-04-11 09:14:34.698746+00	2023-11-28 19:11:03.908098+00	\N	1	\N	16
110	ms	464		299	fol	f		464	\N	\N	2023-04-11 10:23:58.302164+00	2023-10-25 08:34:37.680437+00	\N	31	\N	18
111	ms	1954	Ikhtiyarat-i Muzaffari (in Persian)	191	fol	f		1954	\N	\N	2023-04-11 11:58:08.502612+00	2023-05-30 08:08:24.019005+00	\N	32	\N	18
112	ms	Arabe 2483	Arabic translation of the Almagest (Isḥāq/Thābit translation)\r\n\r\nundated (15th c.)\r\n\r\nAcephalous and incomplete, containing only Books I.10 to VII.4 :\r\nBook I.10-16, 1r-12r\r\nBook II, 12v-40r\r\nBook III, 40v-63r\r\nBook IV, 63v-89v\r\nBook V, 90r-125v\r\nBook VI, 126r-153v\r\nBook VII.1-4, 154v-166r\r\n\r\nhttp://ptolemaeus.badw.de/ms/709	166	fol	f	https://archivesetmanuscrits.bnf.fr/ark:/12148/cc304004	bibliotheque-nationale-de-france-arabe-2483	\N	\N	2023-04-11 12:13:56.594047+00	2023-04-11 12:13:56.594082+00	\N	1	\N	11
113	ms	Add MS 7475	Arabic translation of the Almagest (Isḥāq/Thābit translation, although the star catalogue is taken from the Ḥajjāj translation)\r\n\r\nContents:\r\n\r\nBook Seven (defective at beginning; ff. 1r- 26r ?);\r\nBook Eight (ff. 27v-51r);\r\nBook Nine (ff. 51r-86r);\r\nBook Ten (ff. 86r-116v);\r\nBook Eleven (ff. 117r-161v);\r\nBook Twelve (ff. 162r-199r);\r\nBook Thirteen (ff. 199v-239v).\r\n\r\nhttp://ptolemaeus.badw.de/ms/666	239	fol	f	https://www.qdl.qa/en/archive/81055/vdc_100000004987.0x000001	add-ms-7475	\N	\N	2023-04-11 12:19:16.282572+00	2023-07-03 11:34:41.686243+00	\N	18	\N	11
114	ms	Add MS 7474	Arabic translation of the Almagest (Ḥajjāj translation)\r\n\r\nincomplete\r\n\r\nBook I, 1r-23r\r\nBook II, 23v-55v\r\nBook III, 56r-79v\r\nBook IV, 79v-105v\r\nBook V, 79v-105v\r\nBook VI, 154v-183v\r\n\r\nhttp://ptolemaeus.badw.de/ms/665	183	fol	f	https://www.qdl.qa/en/archive/81055/vdc_100000004884.0x000001	add-ms-7474	\N	\N	2023-04-11 12:30:19.249414+00	2023-07-03 12:17:42.305057+00	\N	18	\N	11
115	ms	3074	Ikhtiyarat-i Muzaffari (in Persian)	178	fol	f		3074	\N	\N	2023-04-11 12:43:46.418687+00	2023-05-30 08:10:31.459738+00	\N	32	\N	18
116	ms	Ayasofya 2662	title: Sharḥ al-Mulakhkhaṣ fī al-hayʾa (Commentary on [Jaghmīnī's] Mulakhkhaṣ)\r\n\r\nautograph witness	71	fol	f		ayasofya-2662	\N	\N	2023-04-11 12:53:35.057381+00	2023-05-30 08:11:39.994858+00	\N	13	\N	11
117	ms	Fatih 3403	title: Sharḥ al-Mulakhkhaṣ fī al-hayʾa (Commentary on [Jaghmīnī's] Mulakhkhaṣ)	71	fol	f		fatih-3403	\N	\N	2023-04-11 12:57:25.27003+00	2023-05-30 08:44:51.49329+00	\N	13	\N	11
118	ms	Add MS 23393	title: al-Tuḥfa al-Shāhiyya	177	fol	f	https://www.qdl.qa/en/archive/81055/vdc_100022676548.0x000001	add-ms-23393	\N	\N	2023-04-11 13:04:43.085871+00	2023-07-03 12:51:32.334481+00	\N	18	\N	11
119	ms	Damad Ibrahim 847	title: Sharḥ al-Tadhkira (Commentary on [Ṭūsī's] Tadhkira)\r\n\r\nnote on last folio states the work itself was completed 3 Ramadan 879 (11 January 1475), while this witness was copied from an autograph in the year of Shirwānī's death (19 Muharram 891 / 25 January 1486, expressed in an abjad phrase)	212	fol	f		damad-ibrahim-847	\N	\N	2023-04-11 13:36:45.110857+00	2023-05-30 08:46:15.025874+00	\N	13	\N	11
120	ms	Arabe 2485	Ṭūsī's recension of the Almagest and three short appendices\r\n\r\n(1) Taḥrīr al-Majisṭī = Naṣīr al-Dīn al-Ṭūsī's recension of Ptolemy's Almagest, fols. 1r-100r\r\nCopied from a copy dated Jumādā l-ūlā 678/Sept.-Oct. 1279 by a disciple of Quṭb al-Dīn al-Shīrāzī (d. 710/1311) from a copy in the hand of Quṭb al-Dīn al-Shīrāzī from an autograph (100r).\r\n\r\n(2) short treatise on the computation of the centers of the spheres of Mercury, fols. 100v‐101v\r\n\r\n(3) short treatise on the computation of the anomaly caused by the eccentricity, fols. 101v-102v\r\n\r\n(4) on the figure for Venus in Book X.2 of the Aimagest, fols. 102v-103r\r\n\r\nhttps://ptolemaeus.badw.de/ms/711	103	fol	f	https://archivesetmanuscrits.bnf.fr/ark:/12148/cc30402m	bibliotheque-nationale-de-france-arabe-2485	\N	\N	2023-04-11 14:12:45.623637+00	2023-06-27 11:39:50.337629+00	\N	1	\N	11
121	ms	3835	Tuhfa al-Shahiya (in Arabic)	212	fol	f		3835	\N	\N	2023-04-11 20:14:58.894367+00	2023-10-25 08:35:49.653895+00	\N	31	\N	18
122	ms	4162	Farsi Hay'a (in Persian)	67	fol	f		4162	\N	\N	2023-04-11 20:35:41.874078+00	2023-10-25 08:36:08.223083+00	\N	31	\N	18
123	ms	3408	al-Takmila fi sharh al-tadhkira	305	fol	f		3408	\N	\N	2023-04-11 20:54:20.009991+00	2023-05-30 08:47:39.762554+00	\N	32	\N	18
124	ms	Or 1997	al‐Qānūn al‐Masʿūdī	268	fol	f	http://explore.bl.uk/BLVU1:LSCOP-ALL:BLL01013233371	or-1997	\N	\N	2023-04-12 07:36:11.94405+00	2023-05-30 08:50:01.388305+00	\N	18	\N	18
125	ms	2132	Kitāb al‐tafhīm li‐awāʾil ṣināʿat al‐tanjīm	239	fol	f		2132	\N	\N	2023-04-12 07:57:07.710388+00	2023-05-30 08:51:23.626757+00	\N	31	\N	18
126	ms	unknown	Fī Hayʾat al‐ʿālam (On the configuration of the world)	26	fol	f		unknown	\N	\N	2023-04-12 08:03:06.121759+00	2023-10-25 08:36:43.353576+00	\N	34	\N	18
127	ms	Landberg 132	Iṣlāḥ al-Majisṭi (Correction of the Almagest)	137	fol	f		landberg-132	\N	\N	2023-04-12 08:18:36.394601+00	2023-05-30 08:54:44.692085+00	\N	5	\N	18
128	ms	3945	Title: Faʿalta fa‐lā talum (You've done it so don't blame [me])	235	fol	f		3945	\N	\N	2023-04-12 09:51:29.149212+00	2023-05-30 08:56:50.179532+00	\N	31	\N	18
129	ms	3506	The treatise's title: Nihāyat al‐idrāk fī dirāyat al‐aflāk (The highest attainment in comprehending the orbs)	314	fol	f		3506	\N	\N	2023-04-12 10:06:20.541892+00	2023-05-30 08:58:12.730108+00	\N	19	\N	18
130	ms	584	Title: al‐Tuḥfa al‐shāhiyya (The imperial gift)	166	fol	f		584	\N	\N	2023-04-12 10:40:12.173028+00	2023-10-25 08:37:13.729469+00	\N	31	\N	18
131	ms	1556	al‐Tuḥfa al‐shāhiyya (The imperial gift)	132	fol	f		1556	\N	\N	2023-04-12 10:51:09.533882+00	2023-10-25 08:37:29.768468+00	\N	31	\N	18
132	ms	Coisl. 384	Diktyon ID: 49525.\r\n\r\nManuscript on paper.	275	fol	f	https://gallica.bnf.fr/view3if/ga/ark:/12148/btv1b110046406	bibliotheque-nationale-de-france-coisl-384	\N	\N	2023-04-12 15:03:47.205894+00	2023-06-28 07:58:57.029467+00	\N	1	\N	5
133	ms	gr. 2381	Diktyon ID: 52013.\r\n\r\nManuscript on paper.	109	fol	f	https://gallica.bnf.fr/view3if/ga/ark:/12148/btv1b10722220g	bibliotheque-nationale-de-france-gr-2381	\N	\N	2023-04-13 09:11:16.043471+00	2023-11-24 11:34:26.582072+00	\N	1	\N	5
134	ms	Cod. Graec. 482	Diktyon ID: 44930.\r\n\r\nManuscript on paper. \r\n\r\nPrevious owners include Demetrios Angelos (15th C).	252	fol	f	https://www.digitale-sammlungen.de/en/view/bsb00076120?page=,1	cod-graec-482	\N	\N	2023-04-13 09:24:58.400307+00	2023-11-27 13:35:04.63329+00	\N	22	\N	5
135	ms	BPG 107	Diktyon ID: 37764.\r\n\r\nManuscript on paper.\r\n\r\nIt contains Cleomedes, "The Heavens".	45	fol	f	http://hdl.handle.net/1887.1/item:1596751	bpg-107	\N	\N	2023-04-13 09:36:27.680181+00	2023-04-13 09:37:36.54446+00	\N	16	\N	5
137	ms	Hébreu 1030	Présentation du contenu\r\nF. 1v-22v : מעשה בכדור הגלגל par Qostâ b. Lūqâ traduction en hébreu par Jacob ben Machir. \r\nIncipit : אמר אולם אחר אשר השם הנכבד נשא זה השר. \r\nExplicit : ומה שיהיה הם חלקי נטיית זה הככב מנכח הראש בעיר ההיא ודעתו. \r\nCf. Hüb, §342, p. 552-554, et pour l'original GAL I², 222; Suppl. I, 365. (Un exemplaire du texte arabe est conservé à Berlin, Ahlwardt, n°5836).\r\n\r\nF. 25v-34v : deux chapitres d'un commentaire sur l'astrolabe, le 33e, במעשה הכלי, et le 34e [f. 28v] במופתים המיוחדים לזה הכלי. Le premier de ces chapitres commence : קח לוח עגול באיזה גודל שתרצה.\r\n\r\nF. 35v-45v : traité de géométrie, différentes propositions géométriques sur les propriétés des triangles et du cercle.\r\nIncipit : כאשר היו שנ' קוים ממשולש על תושבת אחת\r\n\r\nF. 45v-71r : Moïse ben Abraham de Ciudad פרוש לכלי האצטרולב. \r\nIncipit : שער בדיעת הכרת לוח הארץ ממנה כל הגשרים היורדות למטה מן הקו. \r\nExplicit : ואין צורך להרבות בתמונות.\r\n\r\nF. 75r-80r : תקון לוח הצפיחה, instructions pour la confection de l'instrument astronomique appelé aṣ-ṣafīḥā par Mardoché ben Eliezer Komtino. \r\nIncipit : להיות שהכלי הנקרא צפיחה. \r\nExplicit : ולכן ראוי שיהיה מגלה. Cf. Hüb., p. 593, qui l'intitule מאמר תקון כלי צפיחה.\r\n\r\nF. 83v-100v : אגרת המעשה בלוח הנקרא צפיחה, par Ibrāhīm ibn Yaḥyā ibn Zarqali. (Cf. Hébreu 1021, 7e unité textuelle)\r\n\r\nF. 107r-113v : ספר פרוש האצטרולב, titre de l'explicit : ספר פירוש האצטרולב. Traduction de la risālat al-asṭūrlāb d'Aḥmad b. ʿAbd Allāh Ibn aṣ-Ṣaffār al-Gāfiqī Abu l-Qāsim par Jacob ben Machir. F. 107, table des 40 chapitres. \r\nLe texte commence au f. 107v : השער הראשון בזכרון כלי האצטרולב והשמות הנופלים עליו . \r\nExplicit : ובנכחותו אם היה יום. \r\nHüb., §362, p. 580-584. Hist Litt., XXVII, p. 604-605. Pour l'original en arabe, cf. GAL I², p. 256-257 et Suppl. I, 401-402. Traduction en catalan, José Maria Millas Vallicrosa. Assaig d'historia de les idees fisiques i matematiques a la Catalunya medieval. Barcelona, 1983\r\n\r\nF. 114r :Commentaire sur la fabrication de l'astrolabe, ביאור עשיית כלי האצטרולב (inachevé).\r\nIncipit : השער הראשון בידיעת הוצאת עגולת ראש סרטן וטלה וגדי. כשתרצה להוציא עגולת ראש גדי. (Chap. II, בהוצאת הגשרים. Chap. III, dans le texte est interrompu, בהוצאת קוי הנכחות)	114	fol	f	https://archivesetmanuscrits.bnf.fr/ark:/12148/cc76764	bibliotheque-nationale-de-france-hebreu-1030	\N	\N	2023-04-13 14:49:38.754034+00	2023-12-04 16:55:32.454346+00	\N	1	\N	11
138	ms	Hébreu 1092	Présentation du contenu\r\nF. 1r-18r : [אגרת על כללי התכונה] titre factice donné d'après le prologue. Précis anonyme d'astronomie.\r\nDébut du texte : מפני אורך הגלות ולחץ נאבדה חכמת חכמינו.\r\nL'exposé commence par ces mots : הסכימו כל חכמי המחקר הקדמונים והאחררונים שהארץ היא כדורית בכל רוחותיה.\r\nExplicit : ובכלל זה החכמה חברו בו חכמי הנסיון ספרים רבים וברוך השם ית' המלמד לאדם דעת וכול.\r\nSuivi de deux figures schématiques d'astrolabe.\r\n\r\nF. 18v-20v : Gallien (attribué à), ספר הנפש. Traduit par Juda al-Harizi. \r\nIncipit : אמר המעתיק ברוך ה' אלהי מעוזות אשר עשה לנו את הנפש הזאת אמר החכם גלינוס למוריא הפילוסוף תלמידו כי אין הזק לשכל בחברת הכסיל . \r\nExplicit : גם ראה אתה המעיין כמה זה המאמר הקצר הנכבד כולל מחכמתות אמיתיות ומסודות ידיעות המציאות והממציא יתב' וית' המלמד לאדם דעת. Cf. Hüb, §147, p. 273 et s.\r\n\r\nF. 21-28v : (copie inachevée) Jean de Sacrobosco , tractatus de sphera, ספר הגלגל. (cf. Hébreu 1031, 4).\r\n\r\nF. 21-28v : Abraham bar Hiyya (cf. Hébreu 1044, 1), ספר חשבון המהלכות. Le texte est suivi d'un certain nombre d'extraits : a) (f. 78v-79v) extrait un extrait de Jacob ben Machir sur les arcs de cercle (cf. Hébreu 1050, 6). b) (f. 79v-80v) observations sur la conjonction et l'opposition de la lune et le soleil (הרוצה לדעת עת חיבור שני המאורות ועת ניגודן). c) (f. 81-81v) table les lattitudes et des longitudes (cf. Isaac Loeb, revue des études juives, I, 1880, p. 78). d) (f. 82) observations d'Abraham ibn Ezra sur la symbolique du Tabernacle et de son mobilier (אמר אברהם הספרדי ן' עזרא אין ראוי למשכיל להחליף מה שראוי במה שאינו ראוי).\r\n\r\nF. 83-88v : גלילי כסף commentaire sur le livre d'Esther par Joseph ibn Kaspi. \r\nIncipit : אמר יוסף אבן כספי רוח אל עשתני ורוח ה' נשאתני. \r\nExplicit : ודי בזה כונתינו בספר הזה והאלים יכפר את שגגתי. \r\nTexte édité par Isaac Last, Zehn Schriften des R. Josef Ibn Kaspi. Zum ersten Male herausgegeben von Isaac Last. Nebst einer Einleitung von Prof. Dr Ludwig Blau. Presbourg, 1903, T. II, s. 31-39\r\n\r\nF. 89-91v : Abraham ibn Ezra, ערגת החכמה ופרדס הדיבור. (Cf. Hébreu 445, 8; Hébreu 946).\r\n\r\nF. 93-115v : Abu Hamid Al-Gazali, כוונת הפילוסופים. Traduction anonyme. Elle commence par : השבח לאל אשר שמרנו מן הטעות. \r\nHüb. §166 et 173.\r\n\r\nF. 115-119 : Abraham ibn Ezra, ספר השם, au f. 120 on trouve une explication d'un passage de la VIe partie du texte précédent, par Eliezer de Norzi (copié sur l'autographie, מכתיבת, de ce savant), נציע עגולה סביב מרכז מ.\r\n\r\nF. 122v-142 : Abraham Abulafia, פירוש הניקוד (cf. Hébreu 774, 2)\r\n\r\nF. 142-158 : commentaire anonyme sur le Sefer Yetsira (cf. Hébreu f. 774, 3)\r\n\r\nF.158v-167 : Abraham Abulafia, וזאת ליהודה (cf. Hébreu 768, 2)\r\n\r\nF. 167-171v : Benjamin ben Juda Anav, הקדמת הדקדוק, le titre se trouve en explicit (Steinschneider ne le tient pas pour authentique). \r\nIncipit : נאום בנימין ... בראותי ספרי המדקדקים אשר אתנו. \r\nExplicit : ויתקן מעוותי ויקבל שכר מהנותן בלתי מקבל.\r\n\r\nF. 172-172v : addition au chapitre XII du traité מהלכות הכוכבים (cf. Hébreu 1044)\r\n\r\nF. 172v-175v : calcul des tables d'Abraham bar Hiyya pour le 268e cycle (5073-5092 soit 1313-1332 de notre ère), (cf. Hébreu 1054, a). Suscription :\r\n\r\nלטובה ולברכה יזכר שם הרב נשיאנו אמן וחקר ותקן לוחות לחשוב בהן אורך הימים שנרצה לחשוב	175	fol	f	https://archivesetmanuscrits.bnf.fr/ark:/12148/cc96203z	bibliotheque-nationale-de-france-hebreu-1092	\N	\N	2023-04-13 14:51:03.859988+00	2023-07-09 14:13:22.573976+00	\N	1	\N	11
139	ms	Hébreu 1095	Présentation du contenu\r\nF. 1r -6 : liste des mois du calendrier de l'Hégire et le nombre de jours que chacun de ces mois, en caractères hébreux; calculs astronomiques, un court texte au f. 4r dont le titre suscrit est מספר המספר של. Griffonnages et opérations arithmétiques.\r\n\r\nF. 7-49 : Isaac ben Moïse Elie d'Orihuela de Tremedal (Aragon, Espagne) (cf. manuscrit Hébreu 1029, 4) ספר מלאכת המספר. En tête cinq vers du copiste en l'honneur de l'ouvrage :\r\n\r\nמקור מספר הלא הוא לתבונה. כמפתח במסגרת סגורה. הלא גם למהדס הוא כצנה. הנחה הוא למוסיקה ועזרה. ראות כל איש אשר הוא איש תבונה. נעימותו ותועלתו יקרה. באון שכלו הלא כל איש ידבר. וזה ירחיב וזה ידרוך קצרה. אשר יסד ר' יצחק וחבר. מאוד קצר וכלל כל חקורה. \r\n. Incipit : אמר המחבר בראותי אורך דברי החכמים הקדומים מחברי ספרי המספר.\r\nExplicit : וכן בכל חכמה שתקמה התחלותיה מלאכת המספר וכבר הארכנו בכל מה שצריך לכווהתינו.\r\nSuivent des vers en forme de métaphore portant l'acrostiche d'Abraham Kohen d'un problème arithmétique suivi résolution en prose : \r\nאנוש רכב עלי סוסו והיה. מנהל לסוסים עוד אחרים. בעת לכת פגעו איש שמלו. מאת סוסים למי המה שגורים. ראה אלה השיבו עוד כמותם . ואם הוסיף עליהם עוד חסרים. הלא הוסיף רביעיתם וחצים. ועם סוסי אזי מאה ס��ורים. מתי שכל הלא ידעו כלל סוס. אשר ירעה ול''ו המה מסורים. וכל זה נדעהו בחכמת המספר כי תחילה נוציא הסוס הרוכב עליו וישארו ס''ט והנה יש לנו חצי רביעית ושנים שלמים ולפי שהרביעית חלק קטן מכולם נשיב לרביעוה ויהיו לנו י''א רביעות ועתה נסדרם בדוך היחסים המובעה ונאמ' אם הי''א רביעות נתנו צ''ט כמה שוה הד' רביעיות שהם שלם אחד והנה נכפול הב' אמצעיים ונחלקם בראשון ויצאו מהחלוקה ל''ו וזה מספר הסוסים..\r\n  \r\nF. 50 : Abraham Kohen, שאלה מחכמת המספר\r\n\r\nF. 51-115 : Abraham bar Hiyya, ספר צורת הארץ. \r\nTitre : ספר צורת הארץ ותבנית כדורי הרקיע וסדר מהלך ככביהם בשם יי' אל עולם. פתח דברי כלם. כתוב אדונא מה אדור שמך בכל הארץ אשר תנה הודך על השמים.\r\nIncipit : אמר אברהם ב''ר חייא הספרדי ברוך יי' אלהי ישראל הגדול והנורא אדון העוז והתפארה השליט בעולמו הנאדר בכבוד שמו.\r\nExplicit : מספר הככבים אשר נתברר שהטענה ההיא אין לה ממש והתכוונתי להביא העניין הזה\r\n\r\nF. 116-121 : Shabbetai ben Ovadia : calendrier pour les cycles lunaires 277 à 282 (années 1484-1485 à 1597-1598).\r\n\r\nF. 122v-155 : Mordechai ben Eliezer Komtino : ספר תקון כלי הנחושת. \r\nPoème de six vers en tête commençant par ces mots : לצורי אתנה שבחות ואשנה.\r\nInicipit : אמר מרדכי בן אליעזר כומטינו יע''מש לפי שהחכמות הלמודיות הם אמצעיות בין הטבעיות והאלהיות והאמצעי הוא חבר לשתי קווצות. \r\nExplicit : ובסבבנו המסבה יסבב גם העמוד עמו ופה נשלם גם זה והתהלה אליו אשר עזרנו.\r\n\r\nF. 157-175v: commentaire sur le traité de l'astrolabe intitulé ספר פרוש האצטרולב (voir le manuscrit Hébreu 1030, 7)\r\n\r\nF. 178-226 : Nicomaque de Gerase, l'introduction à l'arithmétique (voir manuscrit Hébreu 1028)\r\n\r\nF. 227-235 : griffonnages et calculs astronomiques. Au f. 234, pièce מצחק בקוביה poème qui condamne les jeux et les joueurs de dés ou de cartes. (Cf. Thesaurus III, 168 et sq. n°2512). Au f. 235v : אפן לדעת פרט הנוצרים	236	fol	f	https://archivesetmanuscrits.bnf.fr/ark:/12148/cc98832n	bibliotheque-nationale-de-france-hebreu-1095	\N	\N	2023-04-13 14:52:08.773258+00	2023-12-04 16:36:31.78729+00	\N	1	\N	11
140	ms	705	Title: Istī‘āb al-wujūh al-mumkinah fī ṣan‘at al-uṣṭurlāb (Full discussion of all possible ways to construct the astrolabe)	101	fol	f		705	\N	\N	2023-04-13 15:14:31.678425+00	2023-05-30 09:00:51.970108+00	\N	33	\N	18
141	ms	15/BL, 368	Held at the Fergusson College Library (Pune, India)	54	fol	f		15bl-368	\N	\N	2023-04-14 06:27:58.714476+00	2023-07-12 14:20:26.438514+00	\N	26	\N	6
142	ms	2619	Held at Rajasthan Oriental Research Institute (Jodhpur), part of the Alwar Collection	61	fol	f		2619	\N	\N	2023-04-14 06:31:37.771374+00	2023-07-17 08:25:23.1202+00	\N	27	\N	6
143	ms	5 (Alm. 1)		2	fol	f	https://archive.org/details/OlOJ_surya-grahana-and-chandra-grahana-sanskrit-subject-jyotish-gurukul-kangri-collection/page/n1/mode/2up	5-alm-1	\N	\N	2023-04-14 06:38:40.262874+00	2023-11-23 10:55:39.370961+00	\N	10	\N	6
144	ms	514/1892-95	Miscatalogued as "Rekhāgaṇita"; the manuscript contains the anonymously authored work "Hayatagrantha"	55	fol	f		5141892-95	\N	\N	2023-04-14 06:44:31.167819+00	2023-07-12 15:01:22.907703+00	\N	6	\N	6
145	ms	2792 (Gha. Alm. 12, Shelf 4)	the manuscript contains : \r\n\r\n1. Jagannātha's translation (the Siddhānta Saṃrāṭ) of Ṭūsī's recension of Ptolemy's Almagest (pp.1─307)\r\n\r\n2. Jagannātha's translation (called Rekhāgaṇita) of Euclid's Elements (pp.308─588)	287	fol	f	https://archive.org/details/SiddhantaSaraKaustubhShriJagannatha2792GhaAlm12Shlf4DevanagariJyotish	2792-gha-alm-12-shelf-4	\N	\N	2023-04-14 06:53:33.63503+00	2023-10-23 12:36:32.167874+00	\N	30	\N	6
146	ms	8412		84	fol	f		8412	\N	\N	2023-04-14 06:58:26.392642+00	2023-10-25 09:14:01.901493+00	\N	29	\N	6
147	ms	Barb.lat.256		115	fol	f	https://digi.vatlib.it/view/MSS_Barb.lat.256/0001	barblat256	\N	\N	2023-04-14 10:54:50.527225+00	2023-04-14 10:54:50.527264+00	\N	35	\N	8
148	ms	Cod. Ettenheim-Münster 32		178	fol	f		cod-ettenheim-munster-32	\N	\N	2023-04-14 11:31:43.122653+00	2023-12-04 15:55:43.528948+00	\N	15	\N	8
149	ms	Manuscript 24 vault		\N	fol	f		manuscript-24-vault	\N	\N	2023-04-14 12:00:23.553416+00	2023-04-14 12:00:23.553466+00	\N	20	\N	8
150	ms	Mscr.Dresd.N.100		306	fol	f	https://digital.slub-dresden.de/werkansicht/dlf/16072/1	mscrdresdn100	\N	\N	2023-04-14 12:09:34.73473+00	2023-07-11 16:39:01.19885+00	\N	7	\N	8
151	ms	Pal. lat. 1385		160	fol	f		pal-lat-1385	\N	\N	2023-04-14 12:14:06.665136+00	2023-05-03 12:16:48.396941+00	\N	35	\N	8
152	ms	Héb. 1053		104	fol	f	https://gallica.bnf.fr/ark:/12148/btv1b105393525	bibliotheque-nationale-de-france-heb-1053	\N	\N	2023-04-14 12:29:42.845391+00	2023-07-09 14:23:59.039339+00	\N	1	\N	8
153	ms	Héb. 1052		57	fol	f		bibliotheque-nationale-de-france-heb-1052	\N	\N	2023-04-14 12:34:06.855157+00	2023-07-09 12:03:29.295236+00	\N	1	\N	8
154	ms	Add. 26984		228	fol	f		add-26984	\N	\N	2023-04-14 12:37:51.940589+00	2023-10-25 09:58:21.29014+00	\N	18	\N	8
155	ms	Héb. 1054		188	fol	f		bibliotheque-nationale-de-france-heb-1054	\N	\N	2023-04-14 12:46:09.232036+00	2023-07-09 10:44:10.425946+00	\N	1	\N	8
156	ms	Ms. hebr. 1031	A collection of astronomical texts in different hands.	215	fol	f		bibliotheque-nationale-de-france-ms-hebr-1031	\N	\N	2023-04-23 12:45:38.459147+00	2023-07-09 10:10:56.118919+00	\N	1	\N	22
157	ms	Ms. heb. 3082	A collection of astronomical text in different hands.	122	fol	f		ms-heb-3082	\N	\N	2023-04-23 12:55:02.454074+00	2023-10-25 09:29:57.299431+00	\N	28	\N	22
158	ms	Pal. lat. 1375		288	fol	f		pal-lat-1375	\N	\N	2023-05-03 12:18:14.058084+00	2023-05-03 12:18:14.058115+00	\N	35	\N	1
160	ms	Plut. 28. 14	Diktyon ID: 16195.\r\n\r\nManuscript on paper.\r\n\r\nPrevious owners include Angelo Poliziano (1454-94) and Giovanni Pico della Mirandola (1463-94).	320	fol	f	http://mss.bmlonline.it/Catalogo.aspx?Shelfmark=Plut.28.14	plut-28-14	\N	\N	2023-06-27 13:05:58.52438+00	2023-10-24 16:21:36.377099+00	\N	9	\N	5
161	ms	Plut. 28. 46	Diktyon ID: 16227.\r\n\r\nManuscript on paper.	271	fol	f	http://mss.bmlonline.it/Catalogo.aspx?Shelfmark=Plut.28.46	plut-28-46	\N	\N	2023-06-27 13:52:20.067059+00	2023-10-24 16:22:01.130504+00	\N	9	\N	5
162	ms	Pal. lat. 1340		425	fol	f	https://ptolemaeus.badw.de/jordanus/ms/9966	pal-lat-1340	\N	\N	2023-07-25 08:24:39.59758+00	2023-07-26 12:25:51.808606+00	\N	35	\N	1
163	ms	Vat. lat. 2056	Almagest Latin (unknown translator, Sicily)	94	fol	f		vat-lat-2056	\N	\N	2023-07-26 15:24:12.762375+00	2023-10-23 07:36:06.983592+00	\N	35	\N	12
164	ms	Urb. gr. 76	Diktyon ID: 66543.\r\n\r\nManuscript on paper. \r\n\r\nFf. 1-58v were copied by John Chionopoulos in 1421. They contain Cleomedes, The Heavens.	109	fol	f	https://digi.vatlib.it/view/MSS_Urb.gr.76/0001	urb-gr-76	\N	\N	2023-09-06 09:56:56.261862+00	2023-10-24 16:22:26.850725+00	\N	35	\N	5
165	ms	Chinois 4873	崇禎曆書 ·測量全義 Chong zheng li shu. — Ce liang quan yi. Collection relative au calendrier, années Chong zheng : traité de la mesure des lignes, surfaces et volumes	81	oth	f	https://gallica.bnf.fr/ark:/12148/btv1b9006248p.r=chinois%204873?rk=21459;2	bibliotheque-nationale-de-france-chinois-4873	\N	\N	2023-11-28 19:38:02.768427+00	2023-11-30 10:56:56.674026+00	\N	1	\N	16
166	ms	Chinois 4966	崇祯历书 I 恒星曆指 Heng xing li zhi. Théorie des étoiles fixes ; II 恒星經緯表 Heng xing jing wei biao. Tables des latitudes et longitudes des étoiles fixes	193	oth	f	https://gallica.bnf.fr/ark:/12148/btv1b9002745x.r=Chinois%204879?rk=64378;0https://gallica.bnf.fr/ark:/12148/btv1b9002745x.r=Chinois%204879?rk=64378;0	bibliotheque-nationale-de-france-chinois-4966	\N	\N	2023-11-28 19:50:31.235952+00	2023-11-29 15:09:37.238347+00	\N	1	\N	16
167	ms	Chinois 4879	測算刀圭 ·三角法摘要 Ce suan dao gui. — San jue fa zhe yao.Principes de trigonométrie	63	oth	f	https://gallica.bnf.fr/ark:/12148/bpt6k9822386g/f1.item.r=chinois%204899	bibliotheque-nationale-de-france-chinois-4879	\N	\N	2023-11-28 20:02:14.240681+00	2023-12-01 20:03:42.925062+00	\N	1	\N	16
168	ms	Chinois 4899	渾蓋通憲圖說 : 2卷Hun gai tong xian tu shuo : 2 juan / Li Zhi zao yan ; Zheng Huai kui ding	226	oth	f	https://gallica.bnf.fr/ark:/12148/btv1b90068517.r=chinois%204921?rk=21459;2	bibliotheque-nationale-de-france-chinois-4899	\N	\N	2023-11-28 20:57:54.782812+00	2023-12-01 20:27:56.271116+00	\N	1	\N	16
169	ms	Chinois 4921	測食畧 Ce shi lüe. Théorie abrégée des éclipses	43	oth	f	https://gallica.bnf.fr/ark:/12148/btv1b52504628d	bibliotheque-nationale-de-france-chinois-4921	\N	\N	2023-11-29 07:49:10.105601+00	2023-11-29 15:44:22.375405+00	\N	1	\N	16
170	ms	lat. 14738	Almagest Latin (Gerard of Cremona, Class A)	211	fol	f	https://gallica.bnf.fr/ark:/12148/btv1b525094719	bibliotheque-nationale-de-france-lat-14738	\N	\N	2023-12-04 11:42:18.91501+00	2023-12-04 14:20:01.834245+00	\N	1	\N	12
171	ms	lat. 16200	Almagest Latin (Gerard of Cremona, Class A)	192	fol	f	https://gallica.bnf.fr/ark:/12148/btv1b525168948	bibliotheque-nationale-de-france-lat-16200	\N	\N	2023-12-04 12:55:33.927364+00	2023-12-04 18:20:21.448073+00	\N	1	\N	12
172	ms	lat. 7257	Almagest Latin (Gerard of Cremona, Class B)	109	fol	f	https://gallica.bnf.fr/ark:/12148/btv1b525168948	bibliotheque-nationale-de-france-lat-7257	\N	\N	2023-12-04 14:35:00.616482+00	2023-12-04 17:11:06.017955+00	\N	1	\N	12
2	ms	O II 10	4r-10r: Kalendarium\r\n10v-12rb: Tabula Gerlandi\r\n12rb-17v: Balduinus de Mardochio (or Marrochio) Compotus manualis\r\n19r-26r: Sacrobosco Algorismus\r\n26v-39v: Sacrobosco De sphera\r\n40r-63v: Sacrobosco Computus\r\n64r-67v: Robertus Anglicus Quadrans vetus; 68r-68v: respective solar tables\r\n69r-71v: Pseudo-Messahallah De compositione astrolabii (just the beginning)\r\n72r-79v: Theorica planetarum Gerardi\r\n80v-84r: Pseudo-Thebit Bencora De motu octave spere\r\n84v-88r: Ptolemaica\r\n88v-90r: Thebit Bencora De recta imaginatione spere et circulorum eius diversorum\r\n90r-92r: Thebit Bencora (?) De quantitate stellarum et planetarum et proportione terre\r\n94r-123r: canons for the Toledan tables\r\n124r-204r: Toledan tables + a selection of John of Ligneres’s canons, added by a hand of the\r\nXIV century on ff. 186r-189v\r\n205ra-217rb: ‘Ut annos Arabum et menses et per consequens…’ (dated 1277)	217	fol	f		biblioteca-medicea-laurenziana-o-ii-10	\N	\N	2023-02-22 15:25:35.276864+00	2023-12-06 13:24:08.686288+00	\N	8	\N	1
\.


--
-- Data for Name: webapp_work; Type: TABLE DATA; Schema: public; Owner: salbouy
--

COPY public.webapp_work (id, title, date_min, date_max, notes, author_id, place_id) FROM stdin;
\.


--
-- Data for Name: webapp_work_lang; Type: TABLE DATA; Schema: public; Owner: salbouy
--

COPY public.webapp_work_lang (id, work_id, language_id) FROM stdin;
\.


--
-- Data for Name: webapp_work_tags; Type: TABLE DATA; Schema: public; Owner: salbouy
--

COPY public.webapp_work_tags (id, work_id, tag_id) FROM stdin;
\.


--
-- Name: auth_group_id_seq; Type: SEQUENCE SET; Schema: public; Owner: salbouy
--

SELECT pg_catalog.setval('public.auth_group_id_seq', 1, false);


--
-- Name: auth_group_permissions_id_seq; Type: SEQUENCE SET; Schema: public; Owner: salbouy
--

SELECT pg_catalog.setval('public.auth_group_permissions_id_seq', 1, false);


--
-- Name: auth_permission_id_seq; Type: SEQUENCE SET; Schema: public; Owner: salbouy
--

SELECT pg_catalog.setval('public.auth_permission_id_seq', 76, true);


--
-- Name: auth_user_groups_id_seq; Type: SEQUENCE SET; Schema: public; Owner: salbouy
--

SELECT pg_catalog.setval('public.auth_user_groups_id_seq', 1, false);


--
-- Name: auth_user_id_seq; Type: SEQUENCE SET; Schema: public; Owner: salbouy
--

SELECT pg_catalog.setval('public.auth_user_id_seq', 2, true);


--
-- Name: auth_user_user_permissions_id_seq; Type: SEQUENCE SET; Schema: public; Owner: salbouy
--

SELECT pg_catalog.setval('public.auth_user_user_permissions_id_seq', 1, false);


--
-- Name: django_admin_log_id_seq; Type: SEQUENCE SET; Schema: public; Owner: salbouy
--

SELECT pg_catalog.setval('public.django_admin_log_id_seq', 68, true);


--
-- Name: django_content_type_id_seq; Type: SEQUENCE SET; Schema: public; Owner: salbouy
--

SELECT pg_catalog.setval('public.django_content_type_id_seq', 19, true);


--
-- Name: django_migrations_id_seq; Type: SEQUENCE SET; Schema: public; Owner: salbouy
--

SELECT pg_catalog.setval('public.django_migrations_id_seq', 21, true);


--
-- Name: webapp_annotation_id_seq; Type: SEQUENCE SET; Schema: public; Owner: salbouy
--

SELECT pg_catalog.setval('public.webapp_annotation_id_seq', 1, false);


--
-- Name: webapp_conservationplace_id_seq; Type: SEQUENCE SET; Schema: public; Owner: salbouy
--

SELECT pg_catalog.setval('public.webapp_conservationplace_id_seq', 35, true);


--
-- Name: webapp_content_id_seq; Type: SEQUENCE SET; Schema: public; Owner: salbouy
--

SELECT pg_catalog.setval('public.webapp_content_id_seq', 1, false);


--
-- Name: webapp_content_lang_id_seq; Type: SEQUENCE SET; Schema: public; Owner: salbouy
--

SELECT pg_catalog.setval('public.webapp_content_lang_id_seq', 1, false);


--
-- Name: webapp_content_tags_id_seq; Type: SEQUENCE SET; Schema: public; Owner: salbouy
--

SELECT pg_catalog.setval('public.webapp_content_tags_id_seq', 1, false);


--
-- Name: webapp_digitization_id_seq; Type: SEQUENCE SET; Schema: public; Owner: salbouy
--

SELECT pg_catalog.setval('public.webapp_digitization_id_seq', 2, true);


--
-- Name: webapp_edition_id_seq; Type: SEQUENCE SET; Schema: public; Owner: salbouy
--

SELECT pg_catalog.setval('public.webapp_edition_id_seq', 1, false);


--
-- Name: webapp_language_id_seq; Type: SEQUENCE SET; Schema: public; Owner: salbouy
--

SELECT pg_catalog.setval('public.webapp_language_id_seq', 1, false);


--
-- Name: webapp_person_id_seq; Type: SEQUENCE SET; Schema: public; Owner: salbouy
--

SELECT pg_catalog.setval('public.webapp_person_id_seq', 1, false);


--
-- Name: webapp_place_id_seq; Type: SEQUENCE SET; Schema: public; Owner: salbouy
--

SELECT pg_catalog.setval('public.webapp_place_id_seq', 27, true);


--
-- Name: webapp_role_id_seq; Type: SEQUENCE SET; Schema: public; Owner: salbouy
--

SELECT pg_catalog.setval('public.webapp_role_id_seq', 1, false);


--
-- Name: webapp_series_id_seq; Type: SEQUENCE SET; Schema: public; Owner: salbouy
--

SELECT pg_catalog.setval('public.webapp_series_id_seq', 1, false);


--
-- Name: webapp_series_tags_id_seq; Type: SEQUENCE SET; Schema: public; Owner: salbouy
--

SELECT pg_catalog.setval('public.webapp_series_tags_id_seq', 1, false);


--
-- Name: webapp_tag_id_seq; Type: SEQUENCE SET; Schema: public; Owner: salbouy
--

SELECT pg_catalog.setval('public.webapp_tag_id_seq', 1, false);


--
-- Name: webapp_witness_id_seq; Type: SEQUENCE SET; Schema: public; Owner: salbouy
--

SELECT pg_catalog.setval('public.webapp_witness_id_seq', 3, true);


--
-- Name: webapp_work_id_seq; Type: SEQUENCE SET; Schema: public; Owner: salbouy
--

SELECT pg_catalog.setval('public.webapp_work_id_seq', 1, false);


--
-- Name: webapp_work_lang_id_seq; Type: SEQUENCE SET; Schema: public; Owner: salbouy
--

SELECT pg_catalog.setval('public.webapp_work_lang_id_seq', 1, false);


--
-- Name: webapp_work_tags_id_seq; Type: SEQUENCE SET; Schema: public; Owner: salbouy
--

SELECT pg_catalog.setval('public.webapp_work_tags_id_seq', 1, false);


--
-- Name: auth_group auth_group_name_key; Type: CONSTRAINT; Schema: public; Owner: salbouy
--

ALTER TABLE ONLY public.auth_group
    ADD CONSTRAINT auth_group_name_key UNIQUE (name);


--
-- Name: auth_group_permissions auth_group_permissions_group_id_permission_id_0cd325b0_uniq; Type: CONSTRAINT; Schema: public; Owner: salbouy
--

ALTER TABLE ONLY public.auth_group_permissions
    ADD CONSTRAINT auth_group_permissions_group_id_permission_id_0cd325b0_uniq UNIQUE (group_id, permission_id);


--
-- Name: auth_group_permissions auth_group_permissions_pkey; Type: CONSTRAINT; Schema: public; Owner: salbouy
--

ALTER TABLE ONLY public.auth_group_permissions
    ADD CONSTRAINT auth_group_permissions_pkey PRIMARY KEY (id);


--
-- Name: auth_group auth_group_pkey; Type: CONSTRAINT; Schema: public; Owner: salbouy
--

ALTER TABLE ONLY public.auth_group
    ADD CONSTRAINT auth_group_pkey PRIMARY KEY (id);


--
-- Name: auth_permission auth_permission_content_type_id_codename_01ab375a_uniq; Type: CONSTRAINT; Schema: public; Owner: salbouy
--

ALTER TABLE ONLY public.auth_permission
    ADD CONSTRAINT auth_permission_content_type_id_codename_01ab375a_uniq UNIQUE (content_type_id, codename);


--
-- Name: auth_permission auth_permission_pkey; Type: CONSTRAINT; Schema: public; Owner: salbouy
--

ALTER TABLE ONLY public.auth_permission
    ADD CONSTRAINT auth_permission_pkey PRIMARY KEY (id);


--
-- Name: auth_user_groups auth_user_groups_pkey; Type: CONSTRAINT; Schema: public; Owner: salbouy
--

ALTER TABLE ONLY public.auth_user_groups
    ADD CONSTRAINT auth_user_groups_pkey PRIMARY KEY (id);


--
-- Name: auth_user_groups auth_user_groups_user_id_group_id_94350c0c_uniq; Type: CONSTRAINT; Schema: public; Owner: salbouy
--

ALTER TABLE ONLY public.auth_user_groups
    ADD CONSTRAINT auth_user_groups_user_id_group_id_94350c0c_uniq UNIQUE (user_id, group_id);


--
-- Name: auth_user auth_user_pkey; Type: CONSTRAINT; Schema: public; Owner: salbouy
--

ALTER TABLE ONLY public.auth_user
    ADD CONSTRAINT auth_user_pkey PRIMARY KEY (id);


--
-- Name: auth_user_user_permissions auth_user_user_permissions_pkey; Type: CONSTRAINT; Schema: public; Owner: salbouy
--

ALTER TABLE ONLY public.auth_user_user_permissions
    ADD CONSTRAINT auth_user_user_permissions_pkey PRIMARY KEY (id);


--
-- Name: auth_user_user_permissions auth_user_user_permissions_user_id_permission_id_14a6b632_uniq; Type: CONSTRAINT; Schema: public; Owner: salbouy
--

ALTER TABLE ONLY public.auth_user_user_permissions
    ADD CONSTRAINT auth_user_user_permissions_user_id_permission_id_14a6b632_uniq UNIQUE (user_id, permission_id);


--
-- Name: auth_user auth_user_username_key; Type: CONSTRAINT; Schema: public; Owner: salbouy
--

ALTER TABLE ONLY public.auth_user
    ADD CONSTRAINT auth_user_username_key UNIQUE (username);


--
-- Name: django_admin_log django_admin_log_pkey; Type: CONSTRAINT; Schema: public; Owner: salbouy
--

ALTER TABLE ONLY public.django_admin_log
    ADD CONSTRAINT django_admin_log_pkey PRIMARY KEY (id);


--
-- Name: django_content_type django_content_type_app_label_model_76bd3d3b_uniq; Type: CONSTRAINT; Schema: public; Owner: salbouy
--

ALTER TABLE ONLY public.django_content_type
    ADD CONSTRAINT django_content_type_app_label_model_76bd3d3b_uniq UNIQUE (app_label, model);


--
-- Name: django_content_type django_content_type_pkey; Type: CONSTRAINT; Schema: public; Owner: salbouy
--

ALTER TABLE ONLY public.django_content_type
    ADD CONSTRAINT django_content_type_pkey PRIMARY KEY (id);


--
-- Name: django_migrations django_migrations_pkey; Type: CONSTRAINT; Schema: public; Owner: salbouy
--

ALTER TABLE ONLY public.django_migrations
    ADD CONSTRAINT django_migrations_pkey PRIMARY KEY (id);


--
-- Name: django_session django_session_pkey; Type: CONSTRAINT; Schema: public; Owner: salbouy
--

ALTER TABLE ONLY public.django_session
    ADD CONSTRAINT django_session_pkey PRIMARY KEY (session_key);


--
-- Name: webapp_annotation webapp_annotation_pkey; Type: CONSTRAINT; Schema: public; Owner: salbouy
--

ALTER TABLE ONLY public.webapp_annotation
    ADD CONSTRAINT webapp_annotation_pkey PRIMARY KEY (id);


--
-- Name: webapp_conservationplace webapp_conservationplace_pkey; Type: CONSTRAINT; Schema: public; Owner: salbouy
--

ALTER TABLE ONLY public.webapp_conservationplace
    ADD CONSTRAINT webapp_conservationplace_pkey PRIMARY KEY (id);


--
-- Name: webapp_content_lang webapp_content_lang_content_id_language_id_ba5000a7_uniq; Type: CONSTRAINT; Schema: public; Owner: salbouy
--

ALTER TABLE ONLY public.webapp_content_lang
    ADD CONSTRAINT webapp_content_lang_content_id_language_id_ba5000a7_uniq UNIQUE (content_id, language_id);


--
-- Name: webapp_content_lang webapp_content_lang_pkey; Type: CONSTRAINT; Schema: public; Owner: salbouy
--

ALTER TABLE ONLY public.webapp_content_lang
    ADD CONSTRAINT webapp_content_lang_pkey PRIMARY KEY (id);


--
-- Name: webapp_content webapp_content_pkey; Type: CONSTRAINT; Schema: public; Owner: salbouy
--

ALTER TABLE ONLY public.webapp_content
    ADD CONSTRAINT webapp_content_pkey PRIMARY KEY (id);


--
-- Name: webapp_content_tags webapp_content_tags_content_id_tag_id_eb38cfa9_uniq; Type: CONSTRAINT; Schema: public; Owner: salbouy
--

ALTER TABLE ONLY public.webapp_content_tags
    ADD CONSTRAINT webapp_content_tags_content_id_tag_id_eb38cfa9_uniq UNIQUE (content_id, tag_id);


--
-- Name: webapp_content_tags webapp_content_tags_pkey; Type: CONSTRAINT; Schema: public; Owner: salbouy
--

ALTER TABLE ONLY public.webapp_content_tags
    ADD CONSTRAINT webapp_content_tags_pkey PRIMARY KEY (id);


--
-- Name: webapp_digitization webapp_digitization_pkey; Type: CONSTRAINT; Schema: public; Owner: salbouy
--

ALTER TABLE ONLY public.webapp_digitization
    ADD CONSTRAINT webapp_digitization_pkey PRIMARY KEY (id);


--
-- Name: webapp_edition webapp_edition_name_key; Type: CONSTRAINT; Schema: public; Owner: salbouy
--

ALTER TABLE ONLY public.webapp_edition
    ADD CONSTRAINT webapp_edition_name_key UNIQUE (name);


--
-- Name: webapp_edition webapp_edition_pkey; Type: CONSTRAINT; Schema: public; Owner: salbouy
--

ALTER TABLE ONLY public.webapp_edition
    ADD CONSTRAINT webapp_edition_pkey PRIMARY KEY (id);


--
-- Name: webapp_language webapp_language_code_key; Type: CONSTRAINT; Schema: public; Owner: salbouy
--

ALTER TABLE ONLY public.webapp_language
    ADD CONSTRAINT webapp_language_code_key UNIQUE (code);


--
-- Name: webapp_language webapp_language_lang_key; Type: CONSTRAINT; Schema: public; Owner: salbouy
--

ALTER TABLE ONLY public.webapp_language
    ADD CONSTRAINT webapp_language_lang_key UNIQUE (lang);


--
-- Name: webapp_language webapp_language_pkey; Type: CONSTRAINT; Schema: public; Owner: salbouy
--

ALTER TABLE ONLY public.webapp_language
    ADD CONSTRAINT webapp_language_pkey PRIMARY KEY (id);


--
-- Name: webapp_person webapp_person_name_key; Type: CONSTRAINT; Schema: public; Owner: salbouy
--

ALTER TABLE ONLY public.webapp_person
    ADD CONSTRAINT webapp_person_name_key UNIQUE (name);


--
-- Name: webapp_person webapp_person_pkey; Type: CONSTRAINT; Schema: public; Owner: salbouy
--

ALTER TABLE ONLY public.webapp_person
    ADD CONSTRAINT webapp_person_pkey PRIMARY KEY (id);


--
-- Name: webapp_place webapp_place_name_key; Type: CONSTRAINT; Schema: public; Owner: salbouy
--

ALTER TABLE ONLY public.webapp_place
    ADD CONSTRAINT webapp_place_name_key UNIQUE (name);


--
-- Name: webapp_place webapp_place_pkey; Type: CONSTRAINT; Schema: public; Owner: salbouy
--

ALTER TABLE ONLY public.webapp_place
    ADD CONSTRAINT webapp_place_pkey PRIMARY KEY (id);


--
-- Name: webapp_role webapp_role_pkey; Type: CONSTRAINT; Schema: public; Owner: salbouy
--

ALTER TABLE ONLY public.webapp_role
    ADD CONSTRAINT webapp_role_pkey PRIMARY KEY (id);


--
-- Name: webapp_series webapp_series_pkey; Type: CONSTRAINT; Schema: public; Owner: salbouy
--

ALTER TABLE ONLY public.webapp_series
    ADD CONSTRAINT webapp_series_pkey PRIMARY KEY (id);


--
-- Name: webapp_series_tags webapp_series_tags_pkey; Type: CONSTRAINT; Schema: public; Owner: salbouy
--

ALTER TABLE ONLY public.webapp_series_tags
    ADD CONSTRAINT webapp_series_tags_pkey PRIMARY KEY (id);


--
-- Name: webapp_series_tags webapp_series_tags_series_id_tag_id_0c701ace_uniq; Type: CONSTRAINT; Schema: public; Owner: salbouy
--

ALTER TABLE ONLY public.webapp_series_tags
    ADD CONSTRAINT webapp_series_tags_series_id_tag_id_0c701ace_uniq UNIQUE (series_id, tag_id);


--
-- Name: webapp_tag webapp_tag_pkey; Type: CONSTRAINT; Schema: public; Owner: salbouy
--

ALTER TABLE ONLY public.webapp_tag
    ADD CONSTRAINT webapp_tag_pkey PRIMARY KEY (id);


--
-- Name: webapp_witness webapp_witness_pkey; Type: CONSTRAINT; Schema: public; Owner: salbouy
--

ALTER TABLE ONLY public.webapp_witness
    ADD CONSTRAINT webapp_witness_pkey PRIMARY KEY (id);


--
-- Name: webapp_work_lang webapp_work_lang_pkey; Type: CONSTRAINT; Schema: public; Owner: salbouy
--

ALTER TABLE ONLY public.webapp_work_lang
    ADD CONSTRAINT webapp_work_lang_pkey PRIMARY KEY (id);


--
-- Name: webapp_work_lang webapp_work_lang_work_id_language_id_ce11b18b_uniq; Type: CONSTRAINT; Schema: public; Owner: salbouy
--

ALTER TABLE ONLY public.webapp_work_lang
    ADD CONSTRAINT webapp_work_lang_work_id_language_id_ce11b18b_uniq UNIQUE (work_id, language_id);


--
-- Name: webapp_work webapp_work_pkey; Type: CONSTRAINT; Schema: public; Owner: salbouy
--

ALTER TABLE ONLY public.webapp_work
    ADD CONSTRAINT webapp_work_pkey PRIMARY KEY (id);


--
-- Name: webapp_work_tags webapp_work_tags_pkey; Type: CONSTRAINT; Schema: public; Owner: salbouy
--

ALTER TABLE ONLY public.webapp_work_tags
    ADD CONSTRAINT webapp_work_tags_pkey PRIMARY KEY (id);


--
-- Name: webapp_work_tags webapp_work_tags_work_id_tag_id_7e2568c9_uniq; Type: CONSTRAINT; Schema: public; Owner: salbouy
--

ALTER TABLE ONLY public.webapp_work_tags
    ADD CONSTRAINT webapp_work_tags_work_id_tag_id_7e2568c9_uniq UNIQUE (work_id, tag_id);


--
-- Name: webapp_work webapp_work_title_key; Type: CONSTRAINT; Schema: public; Owner: salbouy
--

ALTER TABLE ONLY public.webapp_work
    ADD CONSTRAINT webapp_work_title_key UNIQUE (title);


--
-- Name: auth_group_name_a6ea08ec_like; Type: INDEX; Schema: public; Owner: salbouy
--

CREATE INDEX auth_group_name_a6ea08ec_like ON public.auth_group USING btree (name varchar_pattern_ops);


--
-- Name: auth_group_permissions_group_id_b120cbf9; Type: INDEX; Schema: public; Owner: salbouy
--

CREATE INDEX auth_group_permissions_group_id_b120cbf9 ON public.auth_group_permissions USING btree (group_id);


--
-- Name: auth_group_permissions_permission_id_84c5c92e; Type: INDEX; Schema: public; Owner: salbouy
--

CREATE INDEX auth_group_permissions_permission_id_84c5c92e ON public.auth_group_permissions USING btree (permission_id);


--
-- Name: auth_permission_content_type_id_2f476e4b; Type: INDEX; Schema: public; Owner: salbouy
--

CREATE INDEX auth_permission_content_type_id_2f476e4b ON public.auth_permission USING btree (content_type_id);


--
-- Name: auth_user_groups_group_id_97559544; Type: INDEX; Schema: public; Owner: salbouy
--

CREATE INDEX auth_user_groups_group_id_97559544 ON public.auth_user_groups USING btree (group_id);


--
-- Name: auth_user_groups_user_id_6a12ed8b; Type: INDEX; Schema: public; Owner: salbouy
--

CREATE INDEX auth_user_groups_user_id_6a12ed8b ON public.auth_user_groups USING btree (user_id);


--
-- Name: auth_user_user_permissions_permission_id_1fbb5f2c; Type: INDEX; Schema: public; Owner: salbouy
--

CREATE INDEX auth_user_user_permissions_permission_id_1fbb5f2c ON public.auth_user_user_permissions USING btree (permission_id);


--
-- Name: auth_user_user_permissions_user_id_a95ead1b; Type: INDEX; Schema: public; Owner: salbouy
--

CREATE INDEX auth_user_user_permissions_user_id_a95ead1b ON public.auth_user_user_permissions USING btree (user_id);


--
-- Name: auth_user_username_6821ab7c_like; Type: INDEX; Schema: public; Owner: salbouy
--

CREATE INDEX auth_user_username_6821ab7c_like ON public.auth_user USING btree (username varchar_pattern_ops);


--
-- Name: django_admin_log_content_type_id_c4bce8eb; Type: INDEX; Schema: public; Owner: salbouy
--

CREATE INDEX django_admin_log_content_type_id_c4bce8eb ON public.django_admin_log USING btree (content_type_id);


--
-- Name: django_admin_log_user_id_c564eba6; Type: INDEX; Schema: public; Owner: salbouy
--

CREATE INDEX django_admin_log_user_id_c564eba6 ON public.django_admin_log USING btree (user_id);


--
-- Name: django_session_expire_date_a5c62663; Type: INDEX; Schema: public; Owner: salbouy
--

CREATE INDEX django_session_expire_date_a5c62663 ON public.django_session USING btree (expire_date);


--
-- Name: django_session_session_key_c0390e0f_like; Type: INDEX; Schema: public; Owner: salbouy
--

CREATE INDEX django_session_session_key_c0390e0f_like ON public.django_session USING btree (session_key varchar_pattern_ops);


--
-- Name: webapp_annotation_digitization_id_b9f29da8; Type: INDEX; Schema: public; Owner: salbouy
--

CREATE INDEX webapp_annotation_digitization_id_b9f29da8 ON public.webapp_annotation USING btree (digitization_id);


--
-- Name: webapp_conservationplace_city_id_44a0d112; Type: INDEX; Schema: public; Owner: salbouy
--

CREATE INDEX webapp_conservationplace_city_id_44a0d112 ON public.webapp_conservationplace USING btree (city_id);


--
-- Name: webapp_content_lang_content_id_20a417ad; Type: INDEX; Schema: public; Owner: salbouy
--

CREATE INDEX webapp_content_lang_content_id_20a417ad ON public.webapp_content_lang USING btree (content_id);


--
-- Name: webapp_content_lang_language_id_c93a003e; Type: INDEX; Schema: public; Owner: salbouy
--

CREATE INDEX webapp_content_lang_language_id_c93a003e ON public.webapp_content_lang USING btree (language_id);


--
-- Name: webapp_content_place_id_c260728a; Type: INDEX; Schema: public; Owner: salbouy
--

CREATE INDEX webapp_content_place_id_c260728a ON public.webapp_content USING btree (place_id);


--
-- Name: webapp_content_tags_content_id_0bf955e2; Type: INDEX; Schema: public; Owner: salbouy
--

CREATE INDEX webapp_content_tags_content_id_0bf955e2 ON public.webapp_content_tags USING btree (content_id);


--
-- Name: webapp_content_tags_tag_id_0d215efc; Type: INDEX; Schema: public; Owner: salbouy
--

CREATE INDEX webapp_content_tags_tag_id_0d215efc ON public.webapp_content_tags USING btree (tag_id);


--
-- Name: webapp_content_witness_id_f16015e5; Type: INDEX; Schema: public; Owner: salbouy
--

CREATE INDEX webapp_content_witness_id_f16015e5 ON public.webapp_content USING btree (witness_id);


--
-- Name: webapp_content_work_id_b4721af5; Type: INDEX; Schema: public; Owner: salbouy
--

CREATE INDEX webapp_content_work_id_b4721af5 ON public.webapp_content USING btree (work_id);


--
-- Name: webapp_digitization_witness_id_e5573a09; Type: INDEX; Schema: public; Owner: salbouy
--

CREATE INDEX webapp_digitization_witness_id_e5573a09 ON public.webapp_digitization USING btree (witness_id);


--
-- Name: webapp_edition_name_980df94d_like; Type: INDEX; Schema: public; Owner: salbouy
--

CREATE INDEX webapp_edition_name_980df94d_like ON public.webapp_edition USING btree (name varchar_pattern_ops);


--
-- Name: webapp_edition_place_id_41bf8219; Type: INDEX; Schema: public; Owner: salbouy
--

CREATE INDEX webapp_edition_place_id_41bf8219 ON public.webapp_edition USING btree (place_id);


--
-- Name: webapp_edition_publisher_id_c86042b6; Type: INDEX; Schema: public; Owner: salbouy
--

CREATE INDEX webapp_edition_publisher_id_c86042b6 ON public.webapp_edition USING btree (publisher_id);


--
-- Name: webapp_language_code_bee0b0d8_like; Type: INDEX; Schema: public; Owner: salbouy
--

CREATE INDEX webapp_language_code_bee0b0d8_like ON public.webapp_language USING btree (code varchar_pattern_ops);


--
-- Name: webapp_language_lang_6a4c3b3f_like; Type: INDEX; Schema: public; Owner: salbouy
--

CREATE INDEX webapp_language_lang_6a4c3b3f_like ON public.webapp_language USING btree (lang varchar_pattern_ops);


--
-- Name: webapp_person_name_53d4542c_like; Type: INDEX; Schema: public; Owner: salbouy
--

CREATE INDEX webapp_person_name_53d4542c_like ON public.webapp_person USING btree (name varchar_pattern_ops);


--
-- Name: webapp_place_name_80b4871c_like; Type: INDEX; Schema: public; Owner: salbouy
--

CREATE INDEX webapp_place_name_80b4871c_like ON public.webapp_place USING btree (name varchar_pattern_ops);


--
-- Name: webapp_role_content_id_8633f721; Type: INDEX; Schema: public; Owner: salbouy
--

CREATE INDEX webapp_role_content_id_8633f721 ON public.webapp_role USING btree (content_id);


--
-- Name: webapp_role_person_id_b577eba2; Type: INDEX; Schema: public; Owner: salbouy
--

CREATE INDEX webapp_role_person_id_b577eba2 ON public.webapp_role USING btree (person_id);


--
-- Name: webapp_role_series_id_c49179c5; Type: INDEX; Schema: public; Owner: salbouy
--

CREATE INDEX webapp_role_series_id_c49179c5 ON public.webapp_role USING btree (series_id);


--
-- Name: webapp_series_edition_id_9576b72d; Type: INDEX; Schema: public; Owner: salbouy
--

CREATE INDEX webapp_series_edition_id_9576b72d ON public.webapp_series USING btree (edition_id);


--
-- Name: webapp_series_tags_series_id_bde8ab99; Type: INDEX; Schema: public; Owner: salbouy
--

CREATE INDEX webapp_series_tags_series_id_bde8ab99 ON public.webapp_series_tags USING btree (series_id);


--
-- Name: webapp_series_tags_tag_id_89891755; Type: INDEX; Schema: public; Owner: salbouy
--

CREATE INDEX webapp_series_tags_tag_id_89891755 ON public.webapp_series_tags USING btree (tag_id);


--
-- Name: webapp_series_user_id_390a1f79; Type: INDEX; Schema: public; Owner: salbouy
--

CREATE INDEX webapp_series_user_id_390a1f79 ON public.webapp_series USING btree (user_id);


--
-- Name: webapp_series_work_id_649f6717; Type: INDEX; Schema: public; Owner: salbouy
--

CREATE INDEX webapp_series_work_id_649f6717 ON public.webapp_series USING btree (work_id);


--
-- Name: webapp_witness_edition_id_d768d5e0; Type: INDEX; Schema: public; Owner: salbouy
--

CREATE INDEX webapp_witness_edition_id_d768d5e0 ON public.webapp_witness USING btree (edition_id);


--
-- Name: webapp_witness_place_id_57a09860; Type: INDEX; Schema: public; Owner: salbouy
--

CREATE INDEX webapp_witness_place_id_57a09860 ON public.webapp_witness USING btree (place_id);


--
-- Name: webapp_witness_series_id_a22666db; Type: INDEX; Schema: public; Owner: salbouy
--

CREATE INDEX webapp_witness_series_id_a22666db ON public.webapp_witness USING btree (series_id);


--
-- Name: webapp_witness_slug_472fe1da; Type: INDEX; Schema: public; Owner: salbouy
--

CREATE INDEX webapp_witness_slug_472fe1da ON public.webapp_witness USING btree (slug);


--
-- Name: webapp_witness_slug_472fe1da_like; Type: INDEX; Schema: public; Owner: salbouy
--

CREATE INDEX webapp_witness_slug_472fe1da_like ON public.webapp_witness USING btree (slug varchar_pattern_ops);


--
-- Name: webapp_witness_user_id_4cc94995; Type: INDEX; Schema: public; Owner: salbouy
--

CREATE INDEX webapp_witness_user_id_4cc94995 ON public.webapp_witness USING btree (user_id);


--
-- Name: webapp_work_author_id_372548ed; Type: INDEX; Schema: public; Owner: salbouy
--

CREATE INDEX webapp_work_author_id_372548ed ON public.webapp_work USING btree (author_id);


--
-- Name: webapp_work_lang_language_id_f113e999; Type: INDEX; Schema: public; Owner: salbouy
--

CREATE INDEX webapp_work_lang_language_id_f113e999 ON public.webapp_work_lang USING btree (language_id);


--
-- Name: webapp_work_lang_work_id_dc4d651e; Type: INDEX; Schema: public; Owner: salbouy
--

CREATE INDEX webapp_work_lang_work_id_dc4d651e ON public.webapp_work_lang USING btree (work_id);


--
-- Name: webapp_work_place_id_b2951b97; Type: INDEX; Schema: public; Owner: salbouy
--

CREATE INDEX webapp_work_place_id_b2951b97 ON public.webapp_work USING btree (place_id);


--
-- Name: webapp_work_tags_tag_id_be390ef8; Type: INDEX; Schema: public; Owner: salbouy
--

CREATE INDEX webapp_work_tags_tag_id_be390ef8 ON public.webapp_work_tags USING btree (tag_id);


--
-- Name: webapp_work_tags_work_id_2802996b; Type: INDEX; Schema: public; Owner: salbouy
--

CREATE INDEX webapp_work_tags_work_id_2802996b ON public.webapp_work_tags USING btree (work_id);


--
-- Name: webapp_work_title_23981306_like; Type: INDEX; Schema: public; Owner: salbouy
--

CREATE INDEX webapp_work_title_23981306_like ON public.webapp_work USING btree (title varchar_pattern_ops);


--
-- Name: auth_group_permissions auth_group_permissio_permission_id_84c5c92e_fk_auth_perm; Type: FK CONSTRAINT; Schema: public; Owner: salbouy
--

ALTER TABLE ONLY public.auth_group_permissions
    ADD CONSTRAINT auth_group_permissio_permission_id_84c5c92e_fk_auth_perm FOREIGN KEY (permission_id) REFERENCES public.auth_permission(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: auth_group_permissions auth_group_permissions_group_id_b120cbf9_fk_auth_group_id; Type: FK CONSTRAINT; Schema: public; Owner: salbouy
--

ALTER TABLE ONLY public.auth_group_permissions
    ADD CONSTRAINT auth_group_permissions_group_id_b120cbf9_fk_auth_group_id FOREIGN KEY (group_id) REFERENCES public.auth_group(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: auth_permission auth_permission_content_type_id_2f476e4b_fk_django_co; Type: FK CONSTRAINT; Schema: public; Owner: salbouy
--

ALTER TABLE ONLY public.auth_permission
    ADD CONSTRAINT auth_permission_content_type_id_2f476e4b_fk_django_co FOREIGN KEY (content_type_id) REFERENCES public.django_content_type(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: auth_user_groups auth_user_groups_group_id_97559544_fk_auth_group_id; Type: FK CONSTRAINT; Schema: public; Owner: salbouy
--

ALTER TABLE ONLY public.auth_user_groups
    ADD CONSTRAINT auth_user_groups_group_id_97559544_fk_auth_group_id FOREIGN KEY (group_id) REFERENCES public.auth_group(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: auth_user_groups auth_user_groups_user_id_6a12ed8b_fk_auth_user_id; Type: FK CONSTRAINT; Schema: public; Owner: salbouy
--

ALTER TABLE ONLY public.auth_user_groups
    ADD CONSTRAINT auth_user_groups_user_id_6a12ed8b_fk_auth_user_id FOREIGN KEY (user_id) REFERENCES public.auth_user(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: auth_user_user_permissions auth_user_user_permi_permission_id_1fbb5f2c_fk_auth_perm; Type: FK CONSTRAINT; Schema: public; Owner: salbouy
--

ALTER TABLE ONLY public.auth_user_user_permissions
    ADD CONSTRAINT auth_user_user_permi_permission_id_1fbb5f2c_fk_auth_perm FOREIGN KEY (permission_id) REFERENCES public.auth_permission(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: auth_user_user_permissions auth_user_user_permissions_user_id_a95ead1b_fk_auth_user_id; Type: FK CONSTRAINT; Schema: public; Owner: salbouy
--

ALTER TABLE ONLY public.auth_user_user_permissions
    ADD CONSTRAINT auth_user_user_permissions_user_id_a95ead1b_fk_auth_user_id FOREIGN KEY (user_id) REFERENCES public.auth_user(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: django_admin_log django_admin_log_content_type_id_c4bce8eb_fk_django_co; Type: FK CONSTRAINT; Schema: public; Owner: salbouy
--

ALTER TABLE ONLY public.django_admin_log
    ADD CONSTRAINT django_admin_log_content_type_id_c4bce8eb_fk_django_co FOREIGN KEY (content_type_id) REFERENCES public.django_content_type(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: django_admin_log django_admin_log_user_id_c564eba6_fk_auth_user_id; Type: FK CONSTRAINT; Schema: public; Owner: salbouy
--

ALTER TABLE ONLY public.django_admin_log
    ADD CONSTRAINT django_admin_log_user_id_c564eba6_fk_auth_user_id FOREIGN KEY (user_id) REFERENCES public.auth_user(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: webapp_annotation webapp_annotation_digitization_id_b9f29da8_fk_webapp_di; Type: FK CONSTRAINT; Schema: public; Owner: salbouy
--

ALTER TABLE ONLY public.webapp_annotation
    ADD CONSTRAINT webapp_annotation_digitization_id_b9f29da8_fk_webapp_di FOREIGN KEY (digitization_id) REFERENCES public.webapp_digitization(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: webapp_conservationplace webapp_conservationplace_city_id_44a0d112_fk_webapp_place_id; Type: FK CONSTRAINT; Schema: public; Owner: salbouy
--

ALTER TABLE ONLY public.webapp_conservationplace
    ADD CONSTRAINT webapp_conservationplace_city_id_44a0d112_fk_webapp_place_id FOREIGN KEY (city_id) REFERENCES public.webapp_place(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: webapp_content_lang webapp_content_lang_content_id_20a417ad_fk_webapp_content_id; Type: FK CONSTRAINT; Schema: public; Owner: salbouy
--

ALTER TABLE ONLY public.webapp_content_lang
    ADD CONSTRAINT webapp_content_lang_content_id_20a417ad_fk_webapp_content_id FOREIGN KEY (content_id) REFERENCES public.webapp_content(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: webapp_content_lang webapp_content_lang_language_id_c93a003e_fk_webapp_language_id; Type: FK CONSTRAINT; Schema: public; Owner: salbouy
--

ALTER TABLE ONLY public.webapp_content_lang
    ADD CONSTRAINT webapp_content_lang_language_id_c93a003e_fk_webapp_language_id FOREIGN KEY (language_id) REFERENCES public.webapp_language(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: webapp_content webapp_content_place_id_c260728a_fk_webapp_place_id; Type: FK CONSTRAINT; Schema: public; Owner: salbouy
--

ALTER TABLE ONLY public.webapp_content
    ADD CONSTRAINT webapp_content_place_id_c260728a_fk_webapp_place_id FOREIGN KEY (place_id) REFERENCES public.webapp_place(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: webapp_content_tags webapp_content_tags_content_id_0bf955e2_fk_webapp_content_id; Type: FK CONSTRAINT; Schema: public; Owner: salbouy
--

ALTER TABLE ONLY public.webapp_content_tags
    ADD CONSTRAINT webapp_content_tags_content_id_0bf955e2_fk_webapp_content_id FOREIGN KEY (content_id) REFERENCES public.webapp_content(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: webapp_content_tags webapp_content_tags_tag_id_0d215efc_fk_webapp_tag_id; Type: FK CONSTRAINT; Schema: public; Owner: salbouy
--

ALTER TABLE ONLY public.webapp_content_tags
    ADD CONSTRAINT webapp_content_tags_tag_id_0d215efc_fk_webapp_tag_id FOREIGN KEY (tag_id) REFERENCES public.webapp_tag(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: webapp_content webapp_content_witness_id_f16015e5_fk_webapp_witness_id; Type: FK CONSTRAINT; Schema: public; Owner: salbouy
--

ALTER TABLE ONLY public.webapp_content
    ADD CONSTRAINT webapp_content_witness_id_f16015e5_fk_webapp_witness_id FOREIGN KEY (witness_id) REFERENCES public.webapp_witness(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: webapp_content webapp_content_work_id_b4721af5_fk_webapp_work_id; Type: FK CONSTRAINT; Schema: public; Owner: salbouy
--

ALTER TABLE ONLY public.webapp_content
    ADD CONSTRAINT webapp_content_work_id_b4721af5_fk_webapp_work_id FOREIGN KEY (work_id) REFERENCES public.webapp_work(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: webapp_digitization webapp_digitization_witness_id_e5573a09_fk_webapp_witness_id; Type: FK CONSTRAINT; Schema: public; Owner: salbouy
--

ALTER TABLE ONLY public.webapp_digitization
    ADD CONSTRAINT webapp_digitization_witness_id_e5573a09_fk_webapp_witness_id FOREIGN KEY (witness_id) REFERENCES public.webapp_witness(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: webapp_edition webapp_edition_place_id_41bf8219_fk_webapp_place_id; Type: FK CONSTRAINT; Schema: public; Owner: salbouy
--

ALTER TABLE ONLY public.webapp_edition
    ADD CONSTRAINT webapp_edition_place_id_41bf8219_fk_webapp_place_id FOREIGN KEY (place_id) REFERENCES public.webapp_place(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: webapp_edition webapp_edition_publisher_id_c86042b6_fk_webapp_person_id; Type: FK CONSTRAINT; Schema: public; Owner: salbouy
--

ALTER TABLE ONLY public.webapp_edition
    ADD CONSTRAINT webapp_edition_publisher_id_c86042b6_fk_webapp_person_id FOREIGN KEY (publisher_id) REFERENCES public.webapp_person(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: webapp_role webapp_role_content_id_8633f721_fk_webapp_content_id; Type: FK CONSTRAINT; Schema: public; Owner: salbouy
--

ALTER TABLE ONLY public.webapp_role
    ADD CONSTRAINT webapp_role_content_id_8633f721_fk_webapp_content_id FOREIGN KEY (content_id) REFERENCES public.webapp_content(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: webapp_role webapp_role_person_id_b577eba2_fk_webapp_person_id; Type: FK CONSTRAINT; Schema: public; Owner: salbouy
--

ALTER TABLE ONLY public.webapp_role
    ADD CONSTRAINT webapp_role_person_id_b577eba2_fk_webapp_person_id FOREIGN KEY (person_id) REFERENCES public.webapp_person(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: webapp_role webapp_role_series_id_c49179c5_fk_webapp_series_id; Type: FK CONSTRAINT; Schema: public; Owner: salbouy
--

ALTER TABLE ONLY public.webapp_role
    ADD CONSTRAINT webapp_role_series_id_c49179c5_fk_webapp_series_id FOREIGN KEY (series_id) REFERENCES public.webapp_series(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: webapp_series webapp_series_edition_id_9576b72d_fk_webapp_edition_id; Type: FK CONSTRAINT; Schema: public; Owner: salbouy
--

ALTER TABLE ONLY public.webapp_series
    ADD CONSTRAINT webapp_series_edition_id_9576b72d_fk_webapp_edition_id FOREIGN KEY (edition_id) REFERENCES public.webapp_edition(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: webapp_series_tags webapp_series_tags_series_id_bde8ab99_fk_webapp_series_id; Type: FK CONSTRAINT; Schema: public; Owner: salbouy
--

ALTER TABLE ONLY public.webapp_series_tags
    ADD CONSTRAINT webapp_series_tags_series_id_bde8ab99_fk_webapp_series_id FOREIGN KEY (series_id) REFERENCES public.webapp_series(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: webapp_series_tags webapp_series_tags_tag_id_89891755_fk_webapp_tag_id; Type: FK CONSTRAINT; Schema: public; Owner: salbouy
--

ALTER TABLE ONLY public.webapp_series_tags
    ADD CONSTRAINT webapp_series_tags_tag_id_89891755_fk_webapp_tag_id FOREIGN KEY (tag_id) REFERENCES public.webapp_tag(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: webapp_series webapp_series_user_id_390a1f79_fk_auth_user_id; Type: FK CONSTRAINT; Schema: public; Owner: salbouy
--

ALTER TABLE ONLY public.webapp_series
    ADD CONSTRAINT webapp_series_user_id_390a1f79_fk_auth_user_id FOREIGN KEY (user_id) REFERENCES public.auth_user(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: webapp_series webapp_series_work_id_649f6717_fk_webapp_work_id; Type: FK CONSTRAINT; Schema: public; Owner: salbouy
--

ALTER TABLE ONLY public.webapp_series
    ADD CONSTRAINT webapp_series_work_id_649f6717_fk_webapp_work_id FOREIGN KEY (work_id) REFERENCES public.webapp_work(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: webapp_witness webapp_witness_edition_id_d768d5e0_fk_webapp_edition_id; Type: FK CONSTRAINT; Schema: public; Owner: salbouy
--

ALTER TABLE ONLY public.webapp_witness
    ADD CONSTRAINT webapp_witness_edition_id_d768d5e0_fk_webapp_edition_id FOREIGN KEY (edition_id) REFERENCES public.webapp_edition(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: webapp_witness webapp_witness_series_id_a22666db_fk_webapp_series_id; Type: FK CONSTRAINT; Schema: public; Owner: salbouy
--

ALTER TABLE ONLY public.webapp_witness
    ADD CONSTRAINT webapp_witness_series_id_a22666db_fk_webapp_series_id FOREIGN KEY (series_id) REFERENCES public.webapp_series(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: webapp_witness webapp_witness_user_id_4cc94995_fk_auth_user_id; Type: FK CONSTRAINT; Schema: public; Owner: salbouy
--

ALTER TABLE ONLY public.webapp_witness
    ADD CONSTRAINT webapp_witness_user_id_4cc94995_fk_auth_user_id FOREIGN KEY (user_id) REFERENCES public.auth_user(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: webapp_work webapp_work_author_id_372548ed_fk_webapp_person_id; Type: FK CONSTRAINT; Schema: public; Owner: salbouy
--

ALTER TABLE ONLY public.webapp_work
    ADD CONSTRAINT webapp_work_author_id_372548ed_fk_webapp_person_id FOREIGN KEY (author_id) REFERENCES public.webapp_person(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: webapp_work_lang webapp_work_lang_language_id_f113e999_fk_webapp_language_id; Type: FK CONSTRAINT; Schema: public; Owner: salbouy
--

ALTER TABLE ONLY public.webapp_work_lang
    ADD CONSTRAINT webapp_work_lang_language_id_f113e999_fk_webapp_language_id FOREIGN KEY (language_id) REFERENCES public.webapp_language(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: webapp_work_lang webapp_work_lang_work_id_dc4d651e_fk_webapp_work_id; Type: FK CONSTRAINT; Schema: public; Owner: salbouy
--

ALTER TABLE ONLY public.webapp_work_lang
    ADD CONSTRAINT webapp_work_lang_work_id_dc4d651e_fk_webapp_work_id FOREIGN KEY (work_id) REFERENCES public.webapp_work(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: webapp_work webapp_work_place_id_b2951b97_fk_webapp_place_id; Type: FK CONSTRAINT; Schema: public; Owner: salbouy
--

ALTER TABLE ONLY public.webapp_work
    ADD CONSTRAINT webapp_work_place_id_b2951b97_fk_webapp_place_id FOREIGN KEY (place_id) REFERENCES public.webapp_place(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: webapp_work_tags webapp_work_tags_tag_id_be390ef8_fk_webapp_tag_id; Type: FK CONSTRAINT; Schema: public; Owner: salbouy
--

ALTER TABLE ONLY public.webapp_work_tags
    ADD CONSTRAINT webapp_work_tags_tag_id_be390ef8_fk_webapp_tag_id FOREIGN KEY (tag_id) REFERENCES public.webapp_tag(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: webapp_work_tags webapp_work_tags_work_id_2802996b_fk_webapp_work_id; Type: FK CONSTRAINT; Schema: public; Owner: salbouy
--

ALTER TABLE ONLY public.webapp_work_tags
    ADD CONSTRAINT webapp_work_tags_work_id_2802996b_fk_webapp_work_id FOREIGN KEY (work_id) REFERENCES public.webapp_work(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: SCHEMA public; Type: ACL; Schema: -; Owner: postgres
--

REVOKE USAGE ON SCHEMA public FROM PUBLIC;
GRANT ALL ON SCHEMA public TO PUBLIC;


--
-- PostgreSQL database dump complete
--
