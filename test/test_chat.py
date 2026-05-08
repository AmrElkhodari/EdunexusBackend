import requests
import socketio

print("1. Attempting HTTP Login...")
# CHANGE THESE TO A REAL USER IN YOUR DB!
login_data = {
    "email": "amr2@amr.com",
    'password' : '1212',
    'school_id' : '1212',
    'classroom_id' : '1212',
    'subject_id' : '1212'
}

response = requests.post('http://127.0.0.1:5000/api/users/login', json=login_data)

if response.status_code != 200:
    print("🚨 Login failed! Check your email/password.")
    print(response.json())
    exit()

token = response.json().get('token')
print("✅ Login successful! Token acquired.")
print("2. Dialing the server via WebSockets...")

# Initialize the Socket Client
sio = socketio.Client()


# --- Event Listeners ---
@sio.event
def connect():
    print("📞 Socket connection established with the server!")

    # 3. Once connected, immediately ask to join the specific chat room
    print("3. Asking to join Classroom 1, Subject 2...")
    sio.emit('join_chat', {
        'token': token,
        'classroom_id': 1,
        'subject_id': 2
    })


@sio.event
def connect_error(data):
    print("🚨 The server rejected the socket connection.")


@sio.event
def disconnect():
    print("☎️ Server hung up the phone.")


# Listen for system announcements (like "Abdulkareem joined the chat")
@sio.event
def system_message(data):
    print(f"🤖 SYSTEM: {data['message']}")


# Listen for error messages from your Guard Clauses
@sio.event
def error(data):
    print(f"🚨 ACCESS DENIED: {data['message']}")


# --- Execution ---
# Connect to the server, passing the JWT in the 'auth' payload
sio.connect('http://127.0.0.1:5000', auth={'token': token})

# Keep the script running so the connection stays open
sio.wait()