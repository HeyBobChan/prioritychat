from flask import Flask, render_template, request, jsonify, session
from openai import OpenAI
import time
import os
import tempfile
import re

from datetime import datetime, timedelta

app = Flask(__name__)



# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
app.secret_key = 'b2e9c2e0f7ad4f91b5b84a2952d90b0c'


# Set up your assistant and thread (you'll need to create these in your OpenAI account)
assistant_id = "asst_EA5qnm3CjGozwl4PzF9oxpxY"

# File cleanup settings
FILE_TIMEOUT = timedelta(minutes=2)  # Adjust as needed

def wait_on_run(run, thread):
    while run.status in ["queued", "in_progress"]:
        run = client.beta.threads.runs.retrieve(
            thread_id=thread.id,
            run_id=run.id,
        )
        time.sleep(0.5)
    return run

def clean_response(text):
    cleaned_text = re.sub(r'【.*?†source】', '', text)
    cleaned_text = re.sub(r'[\[\]]', '', cleaned_text)
    return cleaned_text.strip()

def get_assistant_response(user_input="", image_data=None):
    if 'thread_id' not in session:
        session['thread_id'] = client.beta.threads.create().id

    message_content = []
    
    if user_input:
        message_content.append({"type": "text", "text": user_input})
    
    if image_data:
        # Create a temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as temp_file:
            temp_file.write(image_data)
            temp_file_path = temp_file.name

        # Upload the file to OpenAI
        with open(temp_file_path, "rb") as file:
            response = client.files.create(file=file, purpose="vision")
            file_id = response.id

        # Delete the temporary file
        os.unlink(temp_file_path)

        # Add the file to the message
        message_content.append({
            "type": "image_file",
            "image_file": {"file_id": file_id}
        })

        # Store file info in session
        if 'files' not in session:
            session['files'] = []
        session['files'].append({'id': file_id, 'timestamp': datetime.now().isoformat()})
        session.modified = True

    # Create the message
    message = client.beta.threads.messages.create(
        thread_id=session['thread_id'],
        role="user",
        content=message_content,
    )

    # Run the assistant
    run = client.beta.threads.runs.create(
        thread_id=session['thread_id'],
        assistant_id=assistant_id,
    )

    run = wait_on_run(run, client.beta.threads.retrieve(session['thread_id']))

    # Retrieve the assistant's response
    messages = client.beta.threads.messages.list(
        thread_id=session['thread_id'], order="asc", after=message.id
    )

    # Clean the response
    raw_response = messages.data[0].content[0].text.value
    cleaned_response = clean_response(raw_response)

    return cleaned_response

def cleanup_files():
    if 'files' in session:
        current_time = datetime.now()
        files_to_keep = []
        for file in session['files']:
            file_time = datetime.fromisoformat(file['timestamp'])
            if current_time - file_time < FILE_TIMEOUT:
                files_to_keep.append(file)
            else:
                try:
                    client.files.delete(file['id'])
                except Exception as e:
                    print(f"Error deleting file {file['id']}: {e}")
        session['files'] = files_to_keep
        session.modified = True

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    cleanup_files()  # Clean up old files before processing new message
    user_message = request.form.get('message', '')
    image = request.files.get('image')
    image_data = image.read() if image else None
    response = get_assistant_response(user_message, image_data)
    return jsonify({'response': response})

@app.route('/end_conversation', methods=['POST'])
def end_conversation():
    if 'files' in session:
        for file in session['files']:
            try:
                client.files.delete(file['id'])
            except Exception as e:
                print(f"Error deleting file {file['id']}: {e}")
    session.clear()
    return jsonify({'message': 'Conversation ended and resources cleaned up.'})

if __name__ == '__main__':
    # Use the environment variable `PORT` or default to 10000
    port = int(os.environ.get('PORT', 10000))
    # Ensure the app listens on 0.0.0.0 to make it externally accessible
    app.run(host='0.0.0.0', port=port)
