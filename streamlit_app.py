import asyncio

import pandas as pd
import streamlit as st
from inflection import humanize
from otf_api import Api

st.set_page_config(page_title="OTF API")
st.session_state.username = ""
st.session_state.password = ""

empty_form = st.empty()
login_form = empty_form.form("my_form")
username = login_form.text_input("Username")
password = login_form.text_input("Password", type="password")
submit = login_form.form_submit_button("Submit")

if submit:
    st.session_state.username = username
    st.session_state.password = password
    empty_form.empty()


async def main():
    # Show the page title and description.

    st.write("# Welcome to the OTF API")
    st.write("Login to the OTF API to get your member and home studio information")

    while st.session_state.password == "":
        await asyncio.sleep(1)

    empty = st.empty()
    empty.status("Logging in...")
    try:
        otf = await Api.create(st.session_state.username, st.session_state.password)

    except Exception as e:
        st.write(f"Error: {e}")
        return

    empty.status("Logged in!", state="complete")
    empty.empty()

    st.write(f"Thanks for logging in {otf.member.first_name}!")

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

    st.header("Upcoming Classes")
    df = pd.DataFrame.from_records(records)
    df = df.rename(columns=humanize)

    st.dataframe(df)


if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    asyncio.run(main())
