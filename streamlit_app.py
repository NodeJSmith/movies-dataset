import asyncio

import streamlit as st
from otf_api import Api


async def main():
    # Show the page title and description.
    st.set_page_config(page_title="Movies dataset", page_icon="🎬")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    otf = await Api.create(username, password)

    st.text(otf.member)
    st.text(otf.home_studio)


if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
    finally:
        print("Closing Loop")
        loop.close()
