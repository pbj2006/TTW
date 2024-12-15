from flask import Flask, jsonify, request
from flask_socketio import SocketIO, emit, join_room
from flask_cors import CORS
import random

app = Flask(__name__)

# Set up CORS to allow connections from specific origin (your frontend)
CORS(app, origins=["http://localhost:5173"], supports_credentials=True)

# Initialize SocketIO with app and enable CORS for SocketIO as well
socketio = SocketIO(app, cors_allowed_origins=["http://localhost:5173"], async_mode='threading')

# Dictionary to map session ID (request.sid) to username
usernames = {}

# Database of questions
QUESTIONS_DB = {
    0: {"question": "What's 5 + 7?", "answer": "12"},
    1: {"question": "What's 25 / 5?", "answer": "5"},
    2: {"question": "What's 10 * 2?", "answer": "20"},
    3: {"question": "What's 15 - 3?", "answer": "12"},
    4: {"question": "What's 20 + 10?", "answer": "30"},
}

# In-memory game sessions (keyed by session ID)
game_sessions = {}

# Dictionary to store messages for each room
room_messages = {}

# Route for getting a list of available rooms
@app.route('/rooms', methods=['GET'])
def get_rooms():
    available_rooms = list(game_sessions.keys())
    return jsonify(available_rooms)

# Create a new game session or add a user to an existing one
@socketio.on('join')
def handle_join(data):
    username = data['username']
    session_id = data['session_id']

    # Store the username associated with this socket ID
    usernames[request.sid] = username
    
    # If the session_id does not exist, create a new session
    if session_id not in game_sessions:
        game_sessions[session_id] = {
            'users': [],
            'used_questions': set(),  # Track used questions in the session
            'scores': {},  # Track player scores
            'messages': []
        }
        room_messages[session_id] = []  # Initialize empty message history for the new session
    
    # Add the user to the session and initialize their score
    game_sessions[session_id]['users'].append(username)
    game_sessions[session_id]['scores'][username] = 0  # Starting score is 0
    join_room(session_id)  # Join the user to the session room
    emit('joined', {'message': f'Welcome {username}! You are now in session {session_id}.'}, room=session_id)

    # Send all past messages to the new user
    emit('room_messages', {'messages': room_messages[session_id]}, room=session_id)

    # Send the updated leaderboard to all users in the room
    send_leaderboard(session_id)

    # Send a random question to the user
    send_random_question(session_id)

# Function to send a random question from QUESTIONS_DB
def send_random_question(session_id):
    # Get the list of available questions (questions not yet used in this session)
    available_questions = [q for q in QUESTIONS_DB.keys() if q not in game_sessions[session_id]['used_questions']]
    
    if available_questions:
        # Choose a random question
        random_question_id = random.choice(available_questions)
        random_question_text = QUESTIONS_DB[random_question_id]['question']
        
        # Mark this question as used
        game_sessions[session_id]['used_questions'].add(random_question_id)

        # Send the question to the users in the session
        emit('question', {'question_id': random_question_id, 'question_text': random_question_text}, room=session_id)
    else:
        # All questions have been used, reset the used questions list
        game_sessions[session_id]['used_questions'] = set()
        send_random_question(session_id)

# Handle receiving the answer
@socketio.on('check_answer')
def handle_check_answer(data):
    session_id = data['session_id']
    username = data['username']  # User who is answering
    user_answer = data['answer']
    question_id = data['question_id']
    
    correct_answer = QUESTIONS_DB.get(question_id, {}).get('answer')
    
    if user_answer == correct_answer:
        # Correct answer: add 100 points
        game_sessions[session_id]['scores'][username] += 100
        result_status = 'correct'
    else:
        # Incorrect answer: subtract 50 points
        game_sessions[session_id]['scores'][username] -= 50
        result_status = 'incorrect'

    # Save the result message to room messages
    message = f'{username} got the answer {result_status}!'
    room_messages[session_id].append({
        'username': username,
        'message': message,
        'timestamp': str(random.randint(1, 100000)),  # Use timestamp or generate random for demo
    })

    # Emit the result to the user who answered
    emit('answer_result', {
        'status': result_status,
        'username': username  # Send the username of the person who answered
    }, room=session_id)

    # Send updated leaderboard
    send_leaderboard(session_id)

    # Send new question to all users in the session
    send_random_question(session_id)

# Function to send the updated leaderboard
def send_leaderboard(session_id):
    leaderboard = sorted(game_sessions[session_id]['scores'].items(), key=lambda x: x[1], reverse=True)
    emit('leaderboard', {'leaderboard': leaderboard}, room=session_id)

# Handle user disconnect
@socketio.on('disconnect')
def handle_disconnect():
    # Get the username for this session from the stored usernames using request.sid
    username = usernames.get(request.sid)

    sessions_to_delete = []
    for session_id, session in game_sessions.items():
        # Check if the user is in this session
        if username in session['users']:
            session['users'].remove(username)  # Remove user from session
            session['scores'].pop(username)  # Remove score for user
            emit('user_left', {'username': username}, room=session_id)

            # If no users are left, remove the session
            if len(session['users']) == 0:
                sessions_to_delete.append(session_id)

    for session_id in sessions_to_delete:
        del game_sessions[session_id]
        del room_messages[session_id]
        print(f"Session {session_id} has been deleted due to no users left.")
    
    sessions_to_delete = []

if __name__ == '__main__':
    socketio.run(app, port=3000)
