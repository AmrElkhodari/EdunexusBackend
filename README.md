# EduNexus Backend 🎓

A REST + WebSocket backend for an educational mobile platform that connects students, teachers, and school administrators in one structured environment.

Built with **Flask**, **PostgreSQL**, **JWT authentication**, and **Socket.IO** for real-time chat.

---

## What is EduNexus?

EduNexus replaces the scattered communication that happens over WhatsApp groups, paper notices, and physical handouts with a role-aware system where every piece of information reaches exactly who it should.

Each school has classrooms and subjects. Every classroom-subject pair has three tabs:
- 📢 **Announcements** — posted by teachers and admins
- 📁 **Materials** — files uploaded by teachers and admins
- 💬 **Group Chat** — real-time messaging for everyone

---

## User Roles

| Role | How They Get It | Access |
|---|---|---|
| **Headmaster** | Creates a school | Full access to everything in their school |
| **Manager** | Assigned by Headmaster | Same as Headmaster for day-to-day management |
| **Teacher** | Assigned by Headmaster/Manager | One subject, all classrooms |
| **Student** | Assigned by Headmaster/Manager | One classroom, all subjects |

> To change role or school, a user must delete their account and sign up again.  
> Deleting a Headmaster account deletes the entire school and unassigns all members.

---

## Tech Stack

- **Framework** — Flask
- **Database** — PostgreSQL (production) / SQLite (local dev)
- **ORM** — SQLAlchemy
- **Auth** — Flask-JWT-Extended (JWT tokens)
- **Real-time** — Flask-SocketIO
- **File Storage** — Local disk (ephemeral on Render — replace with Cloudinary/S3 for production)
- **Deployment** — Render

---

## Project Structure

```
EduNexusBackend/
│
├── app.py                  # App factory, config, blueprint registration
├── extensions.py           # db and socketio singletons
├── models.py               # SQLAlchemy models
├── events.py               # Socket.IO event handlers
├── requirements.txt
│
└── routes/
    ├── users.py            # Register, login, settings, delete account
    ├── schools.py          # Create, get, update school
    ├── classrooms.py       # List, create, delete classrooms
    ├── subjects.py         # List, create, delete subjects
    ├── announcements.py    # Get, create, delete announcements
    ├── materials.py        # Upload, list, download, delete files
    ├── messages.py         # Chat history (REST)
    └── admin.py            # Invite, assign, remove, delete users
```

---

## Getting Started (Local)

### 1. Clone the repo
```bash
git clone https://github.com/your-username/edunexus-backend.git
cd edunexus-backend
```

### 2. Create a virtual environment
```bash
python -m venv venv
source venv/bin/activate      # Mac/Linux
venv\Scripts\activate         # Windows
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Create a `.env` file
```
JWT_SECRET=your-secret-key-here
# Leave DATABASE_URL empty to use local SQLite
```

### 5. Run the server
```bash
python app.py
```

Server runs at `http://localhost:5000`

---

## Environment Variables

| Variable | Description | Required |
|---|---|---|
| `DATABASE_URL` | PostgreSQL connection string (Render provides this) | Production only |
| `JWT_SECRET` | Secret key for signing JWT tokens | Yes |

---

## API Overview

All endpoints are prefixed with `/api/`. Protected endpoints require:
```
Authorization: Bearer <token>
```

### Users `/api/users`
| Method | Endpoint | Auth | Description |
|---|---|---|---|
| POST | `/create` | Public | Register a new account |
| POST | `/login` | Public | Login and get JWT token |
| PUT | `/settings` | JWT | Update own name/email/password |
| DELETE | `/me` | JWT | Delete own account |

### Schools `/api/schools`
| Method | Endpoint | Auth | Description |
|---|---|---|---|
| POST | `/create` | JWT | Create school (caller becomes Headmaster) |
| GET | `/<id>` | Public | Get school details |
| PUT | `/<id>/update` | JWT | Update school name |

### Classrooms `/api/classrooms`
| Method | Endpoint | Auth | Description |
|---|---|---|---|
| GET | `/` | JWT | List classrooms (filtered by role) |
| POST | `/create` | JWT (HM/Manager) | Create a classroom |
| DELETE | `/<id>/delete` | JWT (HM/Manager) | Delete a classroom |

### Subjects `/api/subjects`
| Method | Endpoint | Auth | Description |
|---|---|---|---|
| GET | `/` | JWT | List subjects (filtered by role) |
| POST | `/create` | JWT (HM/Manager) | Create a subject |
| DELETE | `/<id>/delete` | JWT (HM/Manager) | Delete a subject |

### Announcements `/api/announcements`
| Method | Endpoint | Auth | Description |
|---|---|---|---|
| GET | `/classroom/<c>/subject/<s>` | JWT | Get announcements |
| POST | `/create` | JWT (not Student) | Post an announcement |
| DELETE | `/<id>/delete` | JWT (not Student) | Delete an announcement |

### Materials `/api/materials`
| Method | Endpoint | Auth | Description |
|---|---|---|---|
| GET | `/classroom/<c>/subject/<s>` | JWT | List materials |
| POST | `/create` | JWT (not Student) | Upload a file (multipart/form-data) |
| GET | `/download/<filename>` | JWT | Download a file |
| DELETE | `/<id>/delete` | JWT (not Student) | Delete a material |

> Allowed file types: `pdf, png, jpg, jpeg, ppt, pptx, doc, docx` — max 16MB

### Messages `/api/messages`
| Method | Endpoint | Auth | Description |
|---|---|---|---|
| GET | `/classroom/<c>/subject/<s>` | JWT | Get last 50 messages |

### Admin `/api/admin`
| Method | Endpoint | Auth | Description |
|---|---|---|---|
| PUT | `/<id>/invite` | JWT (HM/Manager) | Invite unassigned user to school |
| PUT | `/<id>/classroom` | JWT (HM/Manager) | Change student's classroom |
| PUT | `/<id>/subject` | JWT (HM/Manager) | Change teacher's subject |
| PUT | `/<id>/remove` | JWT (HM/Manager) | Remove user from school |
| DELETE | `/<id>/delete` | JWT (HM/Manager) | Delete user permanently |

---

## Real-time Chat (Socket.IO)

Connect using the `socket_io_client` package. Chat rooms are named `chat_{classroom_id}_{subject_id}`.

### Events

**Client → Server**

| Event | Payload | Description |
|---|---|---|
| `join_room` | `{ token, classroom_id, subject_id }` | Join a chat room |
| `send_message` | `{ token, classroom_id, subject_id, content }` | Send a message |

**Server → Client**

| Event | Payload | Description |
|---|---|---|
| `receive_message` | `{ message_id, content, sender_name, sender_type, sending_time }` | New message broadcast |
| `error` | `{ message }` | Auth or permission error |

### Recommended flow
1. Load history via `GET /api/messages/classroom/<c>/subject/<s>`
2. Connect Socket.IO and emit `join_room`
3. Listen for `receive_message` to append live messages
4. Emit `send_message` when user taps Send

---

## Response Format

All REST endpoints return JSON in this shape:

```json
// Success
{ "status": "success", "message": "...", ...data }

// Error
{ "status": "error", "message": "reason" }
```

### HTTP Status Codes

| Code | Meaning |
|---|---|
| `200` | OK |
| `201` | Created |
| `400` | Bad request or server exception |
| `401` | Missing or invalid token |
| `403` | Forbidden — insufficient permissions |
| `404` | Resource not found |

---

## License

MIT