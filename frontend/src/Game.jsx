import { useEffect, useState, useRef } from 'react';
import { io } from 'socket.io-client';

function Game() {
  const [text, setText] = useState("");
  const [chatMessage, setChatMessage] = useState(""); 
  const [question, setQuestion] = useState(null);
  const [questionId, setQuestionId] = useState(null);
  const [questionNum, setQuestionNum] = useState(null);
  const [questionTotalNum, setQuestionTotalNum] = useState(null);
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
      setQuestionNum(data.current_question_num);
      setQuestionTotalNum(data.question_total_num);
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
        { message: data.message },
      ]);
    });

    socket.current.on('leaderboard', (data) => {
      setLeaderboard(data.leaderboard);
    });

    socket.current.on('room_messages', (data) => {
      setMessages(data.messages);
    });

    socket.current.on('game_end', (data) => {
      setQuestion(data.message);
    });

    return () => {
      if (socket.current) {
        socket.current.disconnect();
      }
    };
  }, []);

  const handleSubmitAnswer = () => {
    if (questionId !== null && text.trim() !== "") {
      socket.current.emit('check_answer', { session_id: sessionId, username: username, question_id: questionId, answer: text });
      setText(""); // Clear the input field after submitting
    }
  };

  const handleSendMessage = () => {
    if (chatMessage.trim() !== "") {
      socket.current.emit('send_message', { session_id: sessionId, username: username, message: chatMessage });
      setChatMessage(""); // Clear the chat input field
    }
  };

  const handleKeyDown = (event) => {
    if (event.key === 'Enter') {
      handleSubmitAnswer(); // Submit the answer when the Enter key is pressed
    }
  };

  const handleKeyDownChat = (event) => {
    if (event.key === 'Enter') {
      handleSendMessage(); // Send the chat message when the Enter key is pressed
    }
  };


  return (
    <>
      <div style={{ display: 'flex', flexDirection: 'column', padding: '20px', alignItems: 'center' }}>
        <div style={{ width: '100%', marginBottom: '20px' }}>
          <h1>Problem {questionNum} of {questionTotalNum}:</h1>
          <p><strong>{question || 'Loading question...'}</strong></p>

          <div>
            <input
              type="text"
              placeholder="Enter your answer here"
              onChange={(e) => setText(e.target.value)}
              onKeyDown={handleKeyDown} // Add keydown listener
              value={text}
              style={{ padding: '10px', fontSize: '16px', width: '300px', marginRight: '10px' }}
            />
            <button onClick={handleSubmitAnswer} style={{ padding: '10px 20px', fontSize: '16px' }}>
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
          <div style={{ maxHeight: '200px', overflowY: 'auto', border: '1px solid #ccc', padding: '10px', marginBottom: '10px' }}>
            {messages.length > 0 ? (
              messages.slice(-10).map((msg, index) => (
                <div key={index}>
                    {msg.username ? (
                    <>
                        <strong>{msg.username}</strong>: {msg.message}
                    </>
                    ) : (
                    <>{msg.message}</>
                    )}
                </div>
              ))
            ) : (
              <p>No messages yet.</p>
            )}
          </div>
          <input
            type="text"
            placeholder="Type a message..."
            value={chatMessage}
            onChange={(e) => setChatMessage(e.target.value)}
            onKeyDown={handleKeyDownChat} // Add keydown listener for chat
            style={{ padding: '10px', fontSize: '16px', width: '300px', marginRight: '10px' }}
          />
          <button onClick={handleSendMessage} style={{ padding: '10px 20px', fontSize: '16px' }}>
            Send
          </button>
        </div>
      </div>
    </>
  );
}

export default Game;
