import { BrowserRouter as Router, Route, Routes } from 'react-router-dom';
import './App.css';
import { io } from 'socket.io-client';
import Lobby from './Lobby';
import Game from './Game';

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Lobby />} />
        <Route path="/game" element={<Game />} />
      </Routes>
    </Router>
  );
}

export default App;
