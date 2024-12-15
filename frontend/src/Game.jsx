import { useEffect, useState, useRef } from 'react';
import { io } from 'socket.io-client';

function Game() {
  const [text, setText] = useState("");
  const [question, setQuestion] = useState(null);
  const [questionId, setQuestionId] = useState(null);
  const [leaderboard, setLeaderboard] = useState([]);
  const [messages, setMessages] = useState([]);
  const [username, setUsername] = useState("");
  const [sessionId, setSessionId] = useState("");

  const socket = useRef(null);

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const username = params.get('username') || 'User123';
    const sessionId = params.get('session_id') || 'session1';

    setUsername(username);
    setSessionId(sessionId);

    socket.current = io('http://localhost:3000', {
      withCredentials: true,
      transports: ['websocket', 'polling'],
    });

    socket.current.emit('join', { username: username, session_id: sessionId });

    socket.current.on('joined', (data) => {
      console.log(data.message);
    });

    socket.current.on('question', (data) => {
      setQuestion(data.question_text);
      setQuestionId(data.question_id);
    });

    socket.current.on('answer_result', (data) => {
      if (data.username !== username) {
        setMessages((prevMessages) => [
          ...prevMessages,
          { username: data.username, message: `${data.username} got the answer ${data.status}.` },
        ]);
      } else if (data.username === username) {
        setMessages((prevMessages) => [
          ...prevMessages,
          { username: data.username, message: `Your answer is ${data.status}.` },
        ]);
      }
    });

    socket.current.on('user_left', (data) => {
      setMessages((prevMessages) => [
        ...prevMessages,
        { message: data.message},
      ]);
    })

    socket.current.on('leaderboard', (data) => {
      setLeaderboard(data.leaderboard);
    });

    socket.current.on('room_messages', (data) => {
      setMessages(data.messages);
    });

    return () => {
      if (socket.current) {
        socket.current.disconnect();
      }
    };
  }, []);

  const handleSubmitAnswer = (answer) => {
    if (questionId !== null) {
      socket.current.emit('check_answer', { session_id: sessionId, username: username, question_id: questionId, answer });
    }
  };

  return (
    <>
      <div style={{ display: 'flex', flexDirection: 'column', padding: '20px', alignItems: 'center' }}>
        <div style={{ width: '100%', marginBottom: '20px' }}>
          <h1>Problem:</h1>
          <p>Solve this equation: <strong>{question || 'Loading question...'}</strong></p>

          <div>
            <input
              type="text"
              placeholder="Enter your answer here"
              onChange={(e) => setText(e.target.value)}
              value={text}
              style={{ padding: '10px', fontSize: '16px', width: '300px', marginRight: '10px' }}
            />
            <button onClick={() => handleSubmitAnswer(text)} style={{ padding: '10px 20px', fontSize: '16px' }}>
              Submit Answer
            </button>
          </div>
        </div>

        <div style={{ width: '100%', marginBottom: '20px' }}>
          <h2>Leaderboard</h2>
          <ul>
            {leaderboard.map(([username, score]) => (
              <li key={username}>{username}: {score}</li>
            ))}
          </ul>
        </div>

        <div style={{ width: '100%', marginTop: '20px' }}>
          <h2>Messages</h2>
          {messages.length > 0 ? (
            messages.map((msg, index) => (
              <div key={index}>
                <strong>{msg.username}</strong>: {msg.message}
              </div>
            ))
          ) : (
            <p>No messages yet.</p>
          )}
        </div>
      </div>
    </>
  );
}

export default Game;
