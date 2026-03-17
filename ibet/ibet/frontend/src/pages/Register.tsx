import { useState, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../services/api';
import './Register.css';

interface PasswordRequirements {
  hasUppercase: boolean;
  hasLowercase: boolean;
  hasNumber: boolean;
  hasSpecialChar: boolean;
  minLength: boolean;
}

export default function Register() {
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [phone, setPhone] = useState('');
  const [persona, setPersona] = useState('INDIVIDUAL');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const personaOptions = [
    { value: 'STUDENT', label: 'Student (Wallet)' },
    { value: 'STUDENT_ACADEMIC', label: 'Student (Academic)' },
    { value: 'PARENT', label: 'Parent' },
    { value: 'INDIVIDUAL', label: 'Individual' },
    { value: 'COUPLE', label: 'Couple' },
    { value: 'INSTITUTE_OWNER', label: 'Institute Owner' },
    { value: 'INSTITUTE_TEACHER', label: 'Institute Teacher' },
  ];

  const passwordRequirements: PasswordRequirements = useMemo(() => ({
    hasUppercase: /[A-Z]/.test(password),
    hasLowercase: /[a-z]/.test(password),
    hasNumber: /[0-9]/.test(password),
    hasSpecialChar: /[!@#$%^&*(),.?":{}|<>]/.test(password),
    minLength: password.length >= 8,
  }), [password]);

  const passwordStrength = useMemo(() => {
    const satisfiedCount = Object.values(passwordRequirements).filter(Boolean).length;
    if (satisfiedCount <= 2) return 'weak';
    if (satisfiedCount <= 4) return 'medium';
    return 'strong';
  }, [passwordRequirements]);

  const isPasswordValid = useMemo(() => {
    return Object.values(passwordRequirements).every(Boolean);
  }, [passwordRequirements]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    if (!isPasswordValid) {
      setError('Please meet all password requirements');
      return;
    }

    if (password !== confirmPassword) {
      setError('Passwords do not match');
      return;
    }

    setLoading(true);

    try {
      await api.register(username, email, phone, password, persona);
      navigate('/login');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Registration failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="register-container">
      <div className="register-card">
        <h1>IBET Wallet</h1>
        <h2>Register</h2>
        
        {error && <div className="error-message">{error}</div>}
        
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label htmlFor="username">Username</label>
            <input
              type="text"
              id="username"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              required
              placeholder="Choose a username"
            />
          </div>
          
          <div className="form-group">
            <label htmlFor="email">Email</label>
            <input
              type="email"
              id="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              placeholder="Enter your email"
            />
          </div>

          <div className="form-group">
            <label htmlFor="phone">Phone Number</label>
            <input
              type="tel"
              id="phone"
              value={phone}
              onChange={(e) => setPhone(e.target.value)}
              required
              placeholder="Enter your phone number"
            />
          </div>

          <div className="form-group">
            <label htmlFor="persona">Account Type</label>
            <select
              id="persona"
              value={persona}
              onChange={(e) => setPersona(e.target.value)}
              className="module-dropdown"
              style={{ width: '100%', padding: '0.8rem', borderRadius: '8px', border: '1px solid #ddd' }}
            >
              {personaOptions.map(option => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
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
                placeholder="Create a password"
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
            
            {password && (
              <div className="password-strength">
                <div className="password-strength-bar">
                  <div className={`password-strength-bar-fill ${passwordStrength}`} />
                </div>
                <p className={`password-strength-text ${passwordStrength}`}>
                  {passwordStrength === 'weak' && 'Weak'}
                  {passwordStrength === 'medium' && 'Medium'}
                  {passwordStrength === 'strong' && 'Strong'}
                </p>
              </div>
            )}
            
            <div className="password-requirements">
              <p className={passwordRequirements.hasUppercase ? 'satisfied' : ''}>
                At least 1 uppercase letter (A-Z)
              </p>
              <p className={passwordRequirements.hasLowercase ? 'satisfied' : ''}>
                At least 1 lowercase letter (a-z)
              </p>
              <p className={passwordRequirements.hasNumber ? 'satisfied' : ''}>
                At least 1 number (0-9)
              </p>
              <p className={passwordRequirements.hasSpecialChar ? 'satisfied' : ''}>
                At least 1 special character (!@#$%^&*...)
              </p>
              <p className={passwordRequirements.minLength ? 'satisfied' : ''}>
                At least 8 characters
              </p>
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
                placeholder="Confirm your password"
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
            {confirmPassword && password !== confirmPassword && (
              <p className="error-text">Passwords do not match</p>
            )}
          </div>
          
          <button type="submit" disabled={loading || !isPasswordValid}>
            {loading ? 'Registering...' : 'Register'}
          </button>
        </form>
        
        <p className="login-link">
          Already have an account? <a href="/login">Login</a>
        </p>
      </div>
    </div>
  );
}
