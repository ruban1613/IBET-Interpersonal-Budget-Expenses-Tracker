import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../services/api';
import './Login.css';

type LoginMode = 'login' | 'forgot-password' | 'reset-password';

export default function Login() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [phone, setPhone] = useState('');
  const [otp, setOtp] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [showNewPassword, setShowNewPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [loading, setLoading] = useState(false);
  const [mode, setMode] = useState<LoginMode>('login');
  const navigate = useNavigate();

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      // WIPE previous session data completely
      api.clearAllData();
      
      const response = await api.login(username, password);
      api.setToken(response.token);
      
      const user = response.user;
      if (user) {
        localStorage.setItem('user', JSON.stringify(user));
      }

      if (user && user.persona) {
        // Map backend persona to frontend route
        const personaMap: { [key: string]: string } = {
          'STUDENT': 'student',
          'STUDENT_ACADEMIC': 'academic',
          'PARENT': 'parent',
          'INDIVIDUAL': 'individual',
          'COUPLE': 'couple',
          'INSTITUTE_OWNER': 'institute',
          'INSTITUTE_TEACHER': 'institute'
        };
        
        const route = personaMap[user.persona] || 'individual';
        navigate(`/dashboard/${route}`);
      } else {
        navigate('/select-module');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Login failed');
    } finally {
      setLoading(false);
    }
  };

  const handleRequestOTP = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      await api.requestPasswordResetOTP(username, phone);
      setSuccess('OTP sent to your registered phone number');
      setMode('reset-password');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to send OTP');
    } finally {
      setLoading(false);
    }
  };

  const handleResetPassword = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    if (newPassword !== confirmPassword) {
      setError('Passwords do not match');
      return;
    }

    if (newPassword.length < 8) {
      setError('Password must be at least 8 characters');
      return;
    }

    setLoading(true);

    try {
      await api.resetPassword(username, phone, otp, newPassword);
      setSuccess('Password reset successfully! Please login with your new password.');
      setMode('login');
      setUsername('');
      setPassword('');
      setNewPassword('');
      setConfirmPassword('');
      setOtp('');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Password reset failed');
    } finally {
      setLoading(false);
    }
  };

  const renderLoginForm = () => (
    <form onSubmit={handleLogin}>
      <div className="form-group">
        <label htmlFor="username">Username</label>
        <input
          type="text"
          id="username"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          required
          placeholder="Enter your username"
        />
      </div>
      
      <div className="form-group">
        <label htmlFor="password">Password</label>
        <div className="password-input-wrapper">
          <input
            type={showPassword ? 'text' : 'password'}
            id="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            placeholder="Enter your password"
            style={{ paddingRight: '40px' }}
          />
          <button
            type="button"
            className="password-toggle-btn"
            onClick={() => setShowPassword(!showPassword)}
          >
            {showPassword ? '👁️' : '👁️‍🗨️'}
          </button>
        </div>
      </div>
      
      <button type="submit" disabled={loading}>
        {loading ? 'Logging in...' : 'Login'}
      </button>
      
      <button 
        type="button" 
        className="forgot-password-btn"
        onClick={() => {
          setMode('forgot-password');
          setError('');
          setSuccess('');
        }}
      >
        Forgot Password?
      </button>
    </form>
  );

  const renderForgotPasswordForm = () => (
    <form onSubmit={handleRequestOTP}>
      <div className="form-group">
        <label htmlFor="username">Username</label>
        <input
          type="text"
          id="username"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          required
          placeholder="Enter your username"
        />
      </div>
      
      <div className="form-group">
        <label htmlFor="phone">Registered Phone Number</label>
        <input
          type="tel"
          id="phone"
          value={phone}
          onChange={(e) => setPhone(e.target.value)}
          required
          placeholder="Enter your phone number"
        />
      </div>
      
      <button type="submit" disabled={loading}>
        {loading ? 'Sending OTP...' : 'Send OTP'}
      </button>
      
      <button 
        type="button" 
        className="back-to-login-btn"
        onClick={() => {
          setMode('login');
          setError('');
          setSuccess('');
        }}
      >
        Back to Login
      </button>
    </form>
  );

  const renderResetPasswordForm = () => (
    <form onSubmit={handleResetPassword}>
      <div className="form-group">
        <label htmlFor="otp">Enter OTP</label>
        <input
          type="text"
          id="otp"
          value={otp}
          onChange={(e) => setOtp(e.target.value)}
          required
          maxLength={6}
          placeholder="Enter 6-digit OTP"
        />
      </div>
      
      <div className="form-group">
        <label htmlFor="newPassword">New Password</label>
        <div className="password-input-wrapper">
          <input
            type={showNewPassword ? 'text' : 'password'}
            id="newPassword"
            value={newPassword}
            onChange={(e) => setNewPassword(e.target.value)}
            required
            placeholder="Enter new password"
            style={{ paddingRight: '40px' }}
          />
          <button
            type="button"
            className="password-toggle-btn"
            onClick={() => setShowNewPassword(!showNewPassword)}
          >
            {showNewPassword ? '👁️' : '👁️‍🗨️'}
          </button>
        </div>
      </div>
      
      <div className="form-group">
        <label htmlFor="confirmPassword">Confirm Password</label>
        <div className="password-input-wrapper">
          <input
            type={showConfirmPassword ? 'text' : 'password'}
            id="confirmPassword"
            value={confirmPassword}
            onChange={(e) => setConfirmPassword(e.target.value)}
            required
            placeholder="Confirm new password"
            style={{ paddingRight: '40px' }}
          />
          <button
            type="button"
            className="password-toggle-btn"
            onClick={() => setShowConfirmPassword(!showConfirmPassword)}
          >
            {showConfirmPassword ? '👁️' : '👁️‍🗨️'}
          </button>
        </div>
      </div>
      
      <button type="submit" disabled={loading}>
        {loading ? 'Resetting Password...' : 'Reset Password'}
      </button>
      
      <button 
        type="button" 
        className="back-to-login-btn"
        onClick={() => {
          setMode('forgot-password');
          setError('');
          setSuccess('');
        }}
      >
        Back
      </button>
    </form>
  );

  return (
    <div className="login-container">
      <div className="login-card">
        <h1>IBET Wallet</h1>
        <h2>
          {mode === 'login' && 'Login'}
          {mode === 'forgot-password' && 'Forgot Password'}
          {mode === 'reset-password' && 'Reset Password'}
        </h2>
        
        {error && <div className="error-message">{error}</div>}
        {success && <div className="success-message">{success}</div>}
        
        {mode === 'login' && renderLoginForm()}
        {mode === 'forgot-password' && renderForgotPasswordForm()}
        {mode === 'reset-password' && renderResetPasswordForm()}
        
        {mode === 'login' && (
          <p className="register-link">
            Don't have an account? <a href="/register">Register</a>
          </p>
        )}
      </div>
    </div>
  );
}
