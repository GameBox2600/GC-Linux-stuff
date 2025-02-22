#!/usr/bin/env python2.7
import json
import urllib2
import urllib
import datetime
import re
import os

# Replace these with your actual credentials
OPENAI_API_KEY = "your-openai-api-key-here"
GOOGLE_API_KEY = "your-google-api-key-here"
CUSTOM_SEARCH_ENGINE_ID = "your-custom-search-engine-id"

# URLs for stunnel proxies:
OPENAI_URL = "http://192.168.1.3:8080/v1/chat/completions"
GOOGLE_SEARCH_URL = "http://192.168.1.3:8081/customsearch/v1"

# Global conversation history with an updated system prompt.
conversation = [
    {"role": "system", "content": (
        "You are ChatGPT, a helpful assistant. For up-to-date queries, please use the provided web search results. "
        "Do not mention that you cannot browse; simply answer using the context given."
    )}
]

def search_web(query):
    """Use the Google Custom Search API (proxied via stunnel) to fetch a snippet."""
    params = {
        "key": GOOGLE_API_KEY,
        "cx": CUSTOM_SEARCH_ENGINE_ID,
        "q": query
    }
    full_url = GOOGLE_SEARCH_URL + "?" + urllib.urlencode(params)
    req = urllib2.Request(full_url, headers={"Host": "www.googleapis.com"})
    try:
        response = urllib2.urlopen(req)
        raw_response = response.read()
        # Debug: print raw response
        print "Raw Google API Response:\n", raw_response
        result = json.loads(raw_response)
        if "items" in result and result["items"]:
            top_result = result["items"][0]
            snippet = top_result.get("snippet", "No snippet available.")
            print "Extracted snippet:\n", snippet
            return snippet
        else:
            print "No search results found."
            return "No results found."
    except Exception, e:
        error_message = "Web search error: " + str(e)
        print error_message
        return error_message

def local_query(query):
    """Handle some queries locally (e.g., current day)."""
    if "what day" in query.lower():
        return "Today is " + datetime.datetime.now().strftime("%A, %B %d, %Y")
    return None

def process_file_command(user_input):
    """
    Process file upload commands. If the input begins with:
      - "txtfile:" read the file as text.
      - "rawfile:" read the file as binary and convert to hex.
    The contents (with a header) are appended as a system message to the conversation.
    Returns True if a file command was processed.
    """
    if user_input.lower().startswith("txtfile:"):
        file_path = user_input[len("txtfile:"):].strip()
        try:
            with open(file_path, "r") as f:
                file_content = f.read()
            message = "Uploaded text file from {}:\n{}".format(file_path, file_content)
            conversation.append({"role": "system", "content": message})
            print "Text file uploaded and added to conversation."
        except Exception as e:
            print "Error reading text file:", e
        return True
    elif user_input.lower().startswith("rawfile:"):
        file_path = user_input[len("rawfile:"):].strip()
        try:
            with open(file_path, "rb") as f:
                file_data = f.read()
            # In Python 2, str objects support the 'hex' encoding.
            hex_string = file_data.encode("hex")
            message = "Uploaded raw file from {} (hex representation):\n{}".format(file_path, hex_string)
            conversation.append({"role": "system", "content": message})
            print "Raw file uploaded and added to conversation."
        except Exception as e:
            print "Error reading raw file:", e
        return True
    else:
        return False

def chat_with_gpt(prompt):
    """Append web search context and send query to ChatGPT via stunnel."""
    # Check if this is a local query first.
    local_response = local_query(prompt)
    if local_response:
        return local_response

    # Do a web search for context.
    search_summary = search_web(prompt)
    conversation.append({
        "role": "system",
        "content": "Web search results: " + search_summary
    })
    conversation.append({"role": "user", "content": prompt})

    payload = json.dumps({
        "model": "gpt-3.5-turbo",  # Change to "gpt-4" if available and desired.
        "messages": conversation
    })

    req = urllib2.Request(OPENAI_URL, payload, headers={
        "Host": "api.openai.com",
        "Content-Type": "application/json",
        "Authorization": "Bearer " + OPENAI_API_KEY
    })

    try:
        response = urllib2.urlopen(req)
        result = json.loads(response.read())
        reply = result["choices"][0]["message"]["content"]
        conversation.append({"role": "assistant", "content": reply})
        return reply
    except Exception as e:
        return "Error: " + str(e)

def extract_and_save_code(response_text):
    """
    Extract all code blocks (delimited by triple backticks) from the response.
    For each code block larger than 64 characters, save it to its own file.
    """
    code_blocks = re.findall(r"```(?:\w*\n)?(.*?)```", response_text, re.DOTALL)
    if code_blocks:
        base_timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        for i, code in enumerate(code_blocks, start=1):
            code = code.strip()
            if len(code) > 64:
                filename = "code_output_{}_block{}.txt".format(base_timestamp, i)
                with open(filename, "w") as f:
                    f.write(code + "\n")
                print "Code block {} ({} chars) saved to file: {}".format(i, len(code), filename)

def main():
    print "ChatGPT Terminal with Optional Search, File Upload, and Code Saving (type 'exit' to quit)\n"
    while True:
        user_input = raw_input("> ")
        if user_input.lower() in ["exit", "quit"]:
            break

        # Check for file upload commands
        if process_file_command(user_input):
            continue

        # Check if the user explicitly wants a search (without uploading to conversation)
        if user_input.lower().startswith("search:"):
            search_query = user_input[7:].strip()
            snippet = search_web(search_query)
            print "Search result:\n" + snippet.encode("utf-8") + "\n"
            continue

        # Otherwise, process as a normal ChatGPT query.
        output = chat_with_gpt(user_input)
        print output.encode("utf-8") + "\n"

        # Check if the assistant's reply contains any code blocks; if so, save them.
        extract_and_save_code(output)

if __name__ == "__main__":
    main()

