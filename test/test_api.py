import requests

# This is exactly what Flutter does behind the scenes!
url = "http://127.0.0.1:5000/api/users/create"
data_to_send = {
    'first_name' : 'Amr',
    'last_name' : 'Ragaa',
    'email' : 'amr2@amr.com',
    'password' : '1212',
    'school_id' : '1212',
    'classroom_id' : '1212',
    'subject_id' : '1212'
}

# Send the POST request
response = requests.post(url, json=data_to_send)

# Print out what the server says back
print("Status Code:", response.status_code)
print("Server Response:", response.json())