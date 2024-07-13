import asyncio

import pandas as pd
import streamlit as st
from inflection import humanize
from otf_api import Api
from streamlit_local_storage import LocalStorage

st.set_page_config(page_title="OTF API", layout="wide")

LOCAL_STORAGE = LocalStorage()
ACCESS_TOKEN_KEY = "access_token"
ID_TOKEN_KEY = "id_token"
USERNAME_KEY = "username"
PASSWORD_KEY = "password"

header = st.header("Welcome to the OTF API")
CONTAINER = st.container()
LOGIN_PAGE_EMPTY = CONTAINER.empty()
LOGIN_FORM_EMPTY = LOGIN_PAGE_EMPTY.empty()


def get_username_password():
    username, password = st.session_state.get(USERNAME_KEY), st.session_state.get(PASSWORD_KEY)
    if username and password:
        return username, password

    return False


def get_tokens():
    access_token, id_token = LOCAL_STORAGE.getItem(ACCESS_TOKEN_KEY), LOCAL_STORAGE.getItem(ID_TOKEN_KEY)
    if access_token and id_token:
        return access_token, id_token

    return False


def store_tokens(otf: Api):
    LOCAL_STORAGE.setItem(ID_TOKEN_KEY, otf.user.cognito.id_token, key=ID_TOKEN_KEY)
    LOCAL_STORAGE.setItem(ACCESS_TOKEN_KEY, otf.user.cognito.access_token, key=ACCESS_TOKEN_KEY)
    LOCAL_STORAGE.setItem(USERNAME_KEY, otf.user.id_claims_data.email, key=USERNAME_KEY)


def get_username_from_session_or_local_storage():
    return st.session_state.get(USERNAME_KEY) or LOCAL_STORAGE.getItem(USERNAME_KEY)


def get_credential_kwargs():
    if get_username_password():
        username, password = get_username_password()
        return {"username": username, "password": password}

    if get_tokens():
        access_token, id_token = get_tokens()
        return {"access_token": access_token, "id_token": id_token}

    return {}


def show_form():
    if not get_credential_kwargs():
        login_form = LOGIN_FORM_EMPTY.form("login")
        login_form.text_input("Username", key=USERNAME_KEY)
        login_form.text_input("Password", type="password", key=PASSWORD_KEY)
        submit = login_form.form_submit_button("Submit")

        if submit:
            LOGIN_FORM_EMPTY.empty()


def get_all_cookies():
    """
    WARNING: We use unsupported features of Streamlit
            However, this is quite fast and works well with
            the latest version of Streamlit (1.27)
    RETURNS:
    Returns the cookies as a dictionary of kv pairs
    """
    # https://github.com/streamlit/streamlit/pull/5457
    from urllib.parse import unquote

    from streamlit.web.server.websocket_headers import _get_websocket_headers

    headers = _get_websocket_headers()

    if headers is None:
        return {}

    if "Cookie" not in headers:
        return {}

    cookie_string = headers["Cookie"]
    # A sample cookie string: "K1=V1; K2=V2; K3=V3"
    cookie_kv_pairs = cookie_string.split(";")

    cookie_dict = {}
    for kv in cookie_kv_pairs:
        k_and_v = kv.split("=")
        k = k_and_v[0].strip()
        v = k_and_v[1].strip()
        cookie_dict[k] = unquote(v)  # e.g. Convert name%40company.com to name@company.com
    return cookie_dict


async def handle_login() -> Api:
    if not get_credential_kwargs():
        LOGIN_PAGE_EMPTY.write("Login to the OTF API to get your member and home studio information")
        show_form()
        while not get_credential_kwargs():
            await asyncio.sleep(1)
    else:
        username = LOCAL_STORAGE.getItem(USERNAME_KEY) or st.session_state.get(USERNAME_KEY)
        LOGIN_PAGE_EMPTY.status(f"Refreshing session for {username} and getting your upcoming classes...")

    try:
        otf = await Api.create(**get_credential_kwargs())
        store_tokens(otf)

    except Exception as e:
        st.write(f"Error: {e}")
        LOGIN_PAGE_EMPTY.status(f"Error: {e}", state="error")
        raise e

    LOGIN_PAGE_EMPTY.status(f"Logged in as {otf.member.first_name}!", state="complete")
    LOGIN_PAGE_EMPTY.empty()

    return otf


async def show_upcoming_classes(otf: Api):
    bookings = await otf.get_bookings()
    records = []
    for class_ in bookings.bookings:
        otf_class = class_.otf_class
        records.append(
            {
                "start_date": otf_class.starts_at_local,
                "duration": otf_class.duration,
                "class_name": otf_class.name,
                "studio_name": otf_class.studio.studio_name,
                "coach": otf_class.coach.name,
                "status": class_.status,
            }
        )

    CONTAINER.write("### Upcoming Classes")
    df = pd.DataFrame.from_records(records)
    df = df.rename(columns=humanize).rename(columns=str.title)

    CONTAINER.table(df)


async def main():
    otf = await handle_login()

    await show_upcoming_classes(otf)

    # await otf._close_session()


if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    asyncio.run(main())
