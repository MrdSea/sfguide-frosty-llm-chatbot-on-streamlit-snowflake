import openai
import re
import streamlit as st
from prompts import get_system_prompt

st.title("☃️ Frosty")

# Initialize the chat messages history
if "messages" not in st.session_state.keys():
    st.session_state.messages = [
        {"role": "system", "content": get_system_prompt()},
        {"role": "assistant", "content": "How can I help?"}
    ]

# This is a hack to fix the spinner shadow issue
# Hopefully removed before we ship
for _ in range(10):
    st.empty()

# display the prior chat messages
for message in st.session_state.messages:
    if message["role"] == "system":
        continue
    with st.chat_message(message["role"]):
        st.write(message["content"])
        if "results" in message:
            st.dataframe(message["results"])

# Prompt for user input
prompt = st.chat_input()

if prompt:
    st.chat_message("user").write(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})
    # Call LLM
    with st.chat_message("assistant"):
        # ----- non-streaming response -----
        # with st.spinner("Thinking..."):
        #     r = openai.ChatCompletion.create(
        #         model="gpt-3.5-turbo",
        #         #engine="gpt-4",
        #         messages=[{"role": m["role"], "content": m["content"]} for m in st.session_state.messages],
        #     )
        #     response = r.choices[0].message.content
        #     st.write(response)
        # ----- non-streaming response code ends here -----

        # ----- Streaming response -----
        response = ""
        resp_container = st.empty()
        for delta in openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            #engine="gpt-4",
            messages=[{"role": m["role"], "content": m["content"]} for m in st.session_state.messages],
            stream=True,
        ):
                response += delta.choices[0].delta.get("content", "")
                resp_container.markdown(response)
        # ----- Streaming response code ends here -----

        message = {"role": "assistant", "content": response}
        # Parse the response for a SQL query and execute if available
        sql_match = re.search(r"```sql\n(.*)\n```", response, re.DOTALL)
        if sql_match:
            sql = sql_match.group(1)
            message["sql"] = sql
            conn = st.experimental_connection("snowpark")
            message["results"] = conn.query(sql)
            st.dataframe(message["results"])    
        st.session_state.messages.append(message)
