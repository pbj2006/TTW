from flask import Flask, jsonify, request
from flask_socketio import SocketIO, emit, join_room
from flask_cors import CORS
import random

app = Flask(__name__)

# Set up CORS to allow connections from specific origin (your frontend)
CORS(app, origins=["http://localhost:5173"], supports_credentials=True)

# Initialize SocketIO with app and enable CORS for SocketIO as well
socketio = SocketIO(app, cors_allowed_origins=["http://localhost:5173"], async_mode='threading')

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

# Dictionary to map session ID (request.sid) to username
usernames = {}

# Track available rooms
@app.route('/rooms', methods=['GET'])
def get_available_rooms():
    # Return the list of active session IDs
    return jsonify(list(game_sessions.keys()))

# Create a new game session or add a user to an existing one
@socketio.on('join')
def handle_join(data):
    username = data['username']
    session_id = data['session_id']

    if session_id and username:
        join_room(session_id)


        # Store the username associated with this socket ID
        usernames[request.sid] = username
        
        # If the session_id does not exist, create a new session
        if session_id not in game_sessions:
            game_sessions[session_id] = {
                'users': [],
                'scores': {},  # Track player scores
                'messages': [],
                'current_question': None,
                'current_question_num': 1,
                'question_total_num': 5
            }
            room_messages[session_id] = []  # Initialize empty message history for the new session
        
        # Add the user to the session and initialize their score
        game_sessions[session_id]['users'].append(username)
        game_sessions[session_id]['scores'][username] = 0  # Starting score is 0
        join_room(session_id)  # Join the user to the session room

        # Add a "user joined" message to the room messages
        join_message = f'{username} has joined the game!'
        room_messages[session_id].append({
            'username': None,
            'message': join_message,
            'timestamp': str(random.randint(1, 100000)),  # Use a timestamp or generate a random value for demo
        })

        emit('joined', {'message': f'Welcome {username}! You are now in session {session_id}.'}, room=session_id)
        emit('room_messages', {'messages': room_messages[session_id]}, room=session_id)
        send_leaderboard(session_id)

        # Send the current question to the new user if one exists
        current_question = game_sessions[session_id]['current_question']
        if current_question:
            emit('question', current_question, to=request.sid)
        else:
            # If no question exists, generate a new one
            send_random_question(session_id)
    else:
        print("Invalid join data:", data)

# Function to send a random question from QUESTIONS_DB
def send_random_question(session_id):
    random_question_id = random.choice(list(QUESTIONS_DB.keys()))
    random_question_text = QUESTIONS_DB[random_question_id]['question']

    game_sessions[session_id]['current_question'] = {
        'question_id': random_question_id,
        'question_text': random_question_text
    }


    # Send the question to the users in the session
    emit('question', 
         {'question_id': random_question_id, 
          'question_text': random_question_text, 
          'question_total_num': game_sessions[session_id]['question_total_num'],
          'current_question_num': game_sessions[session_id]['current_question_num']
          }, 
         room=session_id)


# Handle receiving the answer
@socketio.on('check_answer')
def handle_check_answer(data):
    session_id = data['session_id']
    username = data['username']  # User who is answering
    user_answer = data['answer']
    question_id = data['question_id']

    if game_sessions[session_id]['current_question_num'] <= game_sessions[session_id]['question_total_num']:

        correct_answer = QUESTIONS_DB.get(question_id, {}).get('answer')
        
        if user_answer == correct_answer:
            game_sessions[session_id]['current_question_num'] += 1
            # Correct answer: add 100 points
            game_sessions[session_id]['scores'][username] += 100
            result_status = 'correct'
            if game_sessions[session_id]['current_question_num'] <= game_sessions[session_id]['question_total_num']:
                send_random_question(session_id)
            else:
                emit('game_end', {'message': 'Game ended!'})
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


# Function to send the updated leaderboard
def send_leaderboard(session_id):
    leaderboard = sorted(game_sessions[session_id]['scores'].items(), key=lambda x: x[1], reverse=True)
    emit('leaderboard', {'leaderboard': leaderboard}, room=session_id)

# Handle user disconnection
@socketio.on('disconnect')
def handle_disconnect():
    # Get the username for this session from the stored usernames using request.sid
    username = usernames.get(request.sid)

    empty_sessions = []
    user_sessions = []
    # Find which session the user was in
    for session_id, session_data in game_sessions.items():
        if username in session_data['users']:
            # Remove the user from the session
            session_data['users'].remove(username)
            session_data['scores'].pop(username, None)
            user_sessions.append(session_id)

            # If no users are left in the session, remove the session
            if len(session_data['users']) == 0:
                empty_sessions.append(session_id)

    # Optionally, you can emit a message that the user has left
    for session_id in user_sessions:
        emit('user_left', {'message': f'{username} has left the game.'}, room=session_id)
        room_messages[session_id].append({
            'username': username,
            'message': f'{username} has left the game.',
            'timestamp': str(random.randint(1, 100000)),  # Use timestamp or generate random for demo
        })

    for session_id in empty_sessions:
        del game_sessions[session_id]
        del room_messages[session_id]

    # Remove the username from the stored session mapping
    if request.sid in usernames:
        del usernames[request.sid]

@socketio.on('send_message')
def handle_send_message(data):
    session_id = data['session_id']
    username = data['username']
    message = data['message']

    if session_id in room_messages:
        # Save the message in the session's message history
        room_messages[session_id].append({
            'username': username,
            'message': message,
            'timestamp': str(random.randint(1, 100000)),  # Add a timestamp or use a real timestamp for production
        })

        # Emit the message to all users in the session
        emit('room_messages', {'messages': room_messages[session_id]}, room=session_id)

if __name__ == '__main__':
    socketio.run(app, port=3000)
