import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';

function Lobby() {
  const [username, setUsername] = useState('');
  const [sessionId, setSessionId] = useState('');
  const [availableRooms, setAvailableRooms] = useState([]);
  const navigate = useNavigate();

  // Fetch the available rooms when the component mounts
  useEffect(() => {
    fetch('http://localhost:3000/rooms')  // Adjust the URL based on your backend configuration
      .then((response) => response.json())
      .then((data) => {
        setAvailableRooms(data);  // Set the available rooms from the backend
      })
      .catch((error) => {
        console.error('Error fetching available rooms:', error);
      });
  }, []);

  // Handle joining a room
  const handleJoin = (roomId) => {
    if (username) {
      // Navigate to the game page, passing the username and room ID
      navigate(`/game?username=${username}&session_id=${roomId}`);
    }
  };

  return (
    <div className="lobby-container">
      <h1>Math Game Lobby</h1>
      <div>
        <label>Username:</label>
        <input
          type="text"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
        />
      </div>
      
      {/* Display the list of available rooms */}
      <div>
        <h2>Available Rooms</h2>
        {availableRooms.length > 0 ? (
          <ul>
            {availableRooms.map((roomId) => (
              <li key={roomId}>
                <button onClick={() => handleJoin(roomId)}>
                  Join Room {roomId}
                </button>
              </li>
            ))}
          </ul>
        ) : (
          <p>No available rooms</p>
        )}
      </div>

      {/* Option to create a new session */}
      <div>
        <label>Or, create a new room:</label>
        <input
          type="text"
          placeholder="Enter a session ID"
          value={sessionId}
          onChange={(e) => setSessionId(e.target.value)}
        />
        <button onClick={() => handleJoin(sessionId)}>Create and Join Room</button>
      </div>
    </div>
  );
}

export default Lobby;
