import { useEffect } from "react";
import "@/App.css";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Logo URL
const LOGO_URL = "https://customer-assets.emergentagent.com/job_1f30f2ce-4c5c-40ac-bd4f-cb3289954aea/artifacts/p5rto5md_Untitled%20%281080%20x%201080%20px%29.png";

const Home = () => {
  const helloWorldApi = async () => {
    try {
      const response = await axios.get(`${API}/`);
      console.log(response.data.message);
    } catch (e) {
      console.error(e, `errored out requesting / api`);
    }
  };

  useEffect(() => {
    helloWorldApi();
  }, []);

  return (
    <div>
      <header className="App-header" data-testid="home-header">
        <a
          className="App-link"
          href="/"
          data-testid="logo-link"
        >
          <img 
            src={LOGO_URL} 
            alt="The Tile Shop - Your Tile Experts" 
            className="App-logo"
            data-testid="brand-logo"
          />
        </a>
        <p className="mt-5 brand-text" data-testid="tagline">Your Tile Experts</p>
        <div className="mt-8 flex gap-4">
          <button className="btn-primary" data-testid="explore-btn">
            Explore Tiles
          </button>
          <button className="btn-secondary" data-testid="contact-btn">
            Contact Us
          </button>
        </div>
      </header>
    </div>
  );
};

function App() {
  return (
    <div className="App">
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Home />}>
            <Route index element={<Home />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </div>
  );
}

export default App;
