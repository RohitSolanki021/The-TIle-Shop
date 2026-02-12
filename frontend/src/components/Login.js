import React, { useState } from 'react';
import { Lock, User, AlertCircle } from 'lucide-react';

const Login = ({ onLogin }) => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    // Validate credentials
    if (username === 'Thetileshop' && password === 'Vicky123') {
      // Store auth in localStorage
      localStorage.setItem('tileShopAuth', 'true');
      localStorage.setItem('tileShopUser', username);
      onLogin();
    } else {
      setError('Invalid username or password');
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center" style={{backgroundColor: '#fef7f7'}}>
      <div className="max-w-md w-full mx-4">
        {/* Logo and Header */}
        <div className="text-center mb-8">
          <div className="flex justify-center mb-4">
            <img 
              src="https://customer-assets.emergentagent.com/job_1f30f2ce-4c5c-40ac-bd4f-cb3289954aea/artifacts/p5rto5md_Untitled%20%281080%20x%201080%20px%29.png" 
              alt="The Tile Shop" 
              className="h-24 w-24 object-contain"
            />
          </div>
          <h1 className="text-3xl font-bold mb-2" style={{color: '#5a3825'}}>
            The Tile Shop
          </h1>
          <p className="text-gray-600">Admin Login Portal</p>
        </div>

        {/* Login Card */}
        <div className="bg-white rounded-2xl shadow-xl p-8">
          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Username Field */}
            <div>
              <label className="block text-sm font-medium mb-2" style={{color: '#5a3825'}}>
                Username
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <User className="h-5 w-5 text-gray-400" />
                </div>
                <input
                  type="text"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  className="pl-10 w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-opacity-50 transition"
                  style={{
                    focusRing: '#5a3825'
                  }}
                  placeholder="Enter username"
                  required
                  autoComplete="username"
                  data-testid="username-input"
                />
              </div>
            </div>

            {/* Password Field */}
            <div>
              <label className="block text-sm font-medium mb-2" style={{color: '#5a3825'}}>
                Password
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <Lock className="h-5 w-5 text-gray-400" />
                </div>
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="pl-10 w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-opacity-50 transition"
                  placeholder="Enter password"
                  required
                  autoComplete="current-password"
                  data-testid="password-input"
                />
              </div>
            </div>

            {/* Error Message */}
            {error && (
              <div className="flex items-center gap-2 p-3 bg-red-50 border border-red-200 rounded-lg" data-testid="error-message">
                <AlertCircle className="h-5 w-5 text-red-600 flex-shrink-0" />
                <p className="text-sm text-red-600">{error}</p>
              </div>
            )}

            {/* Submit Button */}
            <button
              type="submit"
              disabled={loading}
              className="w-full py-3 px-4 text-white font-semibold rounded-lg shadow-md hover:shadow-lg transform hover:scale-105 transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
              style={{
                background: 'linear-gradient(to right, #5a3825, #6b4a35)'
              }}
              data-testid="login-button"
            >
              {loading ? 'Logging in...' : 'Login'}
            </button>
          </form>

          {/* Footer Info */}
          <div className="mt-6 text-center text-sm text-gray-500">
            <p>Secure access to your invoicing system</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Login;
