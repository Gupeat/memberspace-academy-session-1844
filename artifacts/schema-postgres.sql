--
-- PostgreSQL database dump
--

\restrict kbfe8R0afG8EKColjpToRVHZX7AtpeblWIAJcMbeUGkaNBkA6TrQnlC45suY6kN

-- Dumped from database version 16.15
-- Dumped by pg_dump version 16.15

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

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: acad_course; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.acad_course (
    id uuid NOT NULL
);


--
-- Name: acad_course_session; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.acad_course_session (
    id uuid NOT NULL,
    org_id uuid NOT NULL,
    site_id uuid,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    created_by uuid,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    deleted_at timestamp with time zone,
    course_id uuid NOT NULL,
    session_no integer NOT NULL,
    label character varying(20) NOT NULL,
    start_at timestamp with time zone NOT NULL,
    end_at timestamp with time zone NOT NULL,
    room_name character varying(30) NOT NULL,
    capacity integer NOT NULL,
    waitlist_capacity integer DEFAULT 0 NOT NULL,
    signup_open_at timestamp with time zone NOT NULL,
    signup_close_at timestamp with time zone NOT NULL,
    require_review boolean DEFAULT false NOT NULL,
    cancel_deadline_hours integer DEFAULT 24 NOT NULL,
    event_id uuid,
    application_template_id uuid,
    status character varying(16) DEFAULT 'scheduled'::character varying NOT NULL,
    cancel_reason character varying(200),
    CONSTRAINT ck_acad_course_session_cancel_deadline_nonnegative CHECK ((cancel_deadline_hours >= 0)),
    CONSTRAINT ck_acad_course_session_cancel_reason_length CHECK (((cancel_reason IS NULL) OR (length((cancel_reason)::text) <= 200))),
    CONSTRAINT ck_acad_course_session_capacity_range CHECK (((capacity >= 1) AND (capacity <= 500))),
    CONSTRAINT ck_acad_course_session_label_length CHECK ((length((label)::text) <= 20)),
    CONSTRAINT ck_acad_course_session_label_not_blank CHECK ((length(TRIM(BOTH FROM label)) > 0)),
    CONSTRAINT ck_acad_course_session_room_name_length CHECK ((length((room_name)::text) <= 30)),
    CONSTRAINT ck_acad_course_session_room_name_not_blank CHECK ((length(TRIM(BOTH FROM room_name)) > 0)),
    CONSTRAINT ck_acad_course_session_session_no_positive CHECK ((session_no >= 1)),
    CONSTRAINT ck_acad_course_session_signup_before_start CHECK ((signup_close_at <= start_at)),
    CONSTRAINT ck_acad_course_session_signup_window CHECK ((signup_open_at < signup_close_at)),
    CONSTRAINT ck_acad_course_session_status_enum CHECK (((status)::text = ANY ((ARRAY['scheduled'::character varying, 'signup_open'::character varying, 'signup_closed'::character varying, 'in_progress'::character varying, 'finished'::character varying, 'cancelled'::character varying])::text[]))),
    CONSTRAINT ck_acad_course_session_time_order CHECK ((end_at > start_at)),
    CONSTRAINT ck_acad_course_session_waitlist_range CHECK (((waitlist_capacity >= 0) AND (waitlist_capacity <= 100)))
);


--
-- Name: alembic_version; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.alembic_version (
    version_num character varying(32) NOT NULL
);


--
-- Name: acad_course acad_course_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.acad_course
    ADD CONSTRAINT acad_course_pkey PRIMARY KEY (id);


--
-- Name: alembic_version alembic_version_pkc; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.alembic_version
    ADD CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num);


--
-- Name: acad_course_session pk_acad_course_session; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.acad_course_session
    ADD CONSTRAINT pk_acad_course_session PRIMARY KEY (id);


--
-- Name: acad_course_session uq_acad_course_session_course_session_no; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.acad_course_session
    ADD CONSTRAINT uq_acad_course_session_course_session_no UNIQUE (course_id, session_no);


--
-- Name: acad_course_session uq_acad_course_session_event_id; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.acad_course_session
    ADD CONSTRAINT uq_acad_course_session_event_id UNIQUE (event_id);


--
-- Name: ix_acad_course_session_course_start; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_acad_course_session_course_start ON public.acad_course_session USING btree (course_id, start_at);


--
-- Name: ix_acad_course_session_org_start; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_acad_course_session_org_start ON public.acad_course_session USING btree (org_id, start_at);


--
-- Name: acad_course_session fk_acad_course_session_course_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.acad_course_session
    ADD CONSTRAINT fk_acad_course_session_course_id FOREIGN KEY (course_id) REFERENCES public.acad_course(id);


--
-- PostgreSQL database dump complete
--

\unrestrict kbfe8R0afG8EKColjpToRVHZX7AtpeblWIAJcMbeUGkaNBkA6TrQnlC45suY6kN

