import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { api } from '../services/api';
import './Dashboard.css';

interface WalletData {
  balance: number;
  emergency_fund?: number;
  goals?: number;
  [key: string]: any;
}

const moduleInfo: { [key: string]: { name: string; icon: string } } = {
  couple: { name: 'Couple Wallet', icon: '💑' },
  individual: { name: 'Individual Wallet', icon: '👤' },
  parent: { name: 'Parent-Student', icon: '👨‍👩‍👧' },
  dailywage: { name: 'Daily Wage', icon: '💼' },
  retiree: { name: 'Retiree Wallet', icon: '🏖️' },
  student: { name: 'Student Wallet', icon: '🎓' },
};

export default function Dashboard() {
  const { module } = useParams<{ module: string }>();
  const navigate = useNavigate();
  const [wallet, setWallet] = useState<WalletData | null>(null);
  const [amount, setAmount] = useState('');
  const [otp, setOtp] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [action, setAction] = useState<'deposit' | 'withdraw'>('deposit');

  useEffect(() => {
    loadWallet();
  }, [module]);

  const loadWallet = async () => {
    if (!module) return;
    try {
      const data = await api.getWallet(module);
      setWallet(data);
    } catch (err) {
      // Wallet might not exist yet, set default
      setWallet({ balance: 0 });
    }
  };

  const handleRequestOTP = async () => {
    if (!module) return;
    setLoading(true);
    setError('');
    try {
      await api.requestOTP(module);
      setSuccess('OTP sent to your email');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to send OTP');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!module || !amount || !otp) return;

    setLoading(true);
    setError('');
    setSuccess('');

    try {
      if (action === 'deposit') {
        await api.deposit(module, parseFloat(amount), otp);
        setSuccess('Deposit successful!');
      } else {
        await api.withdraw(module, parseFloat(amount), otp);
        setSuccess('Withdrawal successful!');
      }
      setAmount('');
      setOtp('');
      loadWallet();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Transaction failed');
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = () => {
    api.clearToken();
    navigate('/login');
  };

  const handleBack = () => {
    navigate('/select-module');
  };

  if (!module || !moduleInfo[module]) {
    return <div>Invalid module</div>;
  }

  const info = moduleInfo[module];

  return (
    <div className="dashboard-container">
      <header className="dashboard-header">
        <button onClick={handleBack} className="back-btn">← Back</button>
        <h1>{info.name}</h1>
        <button onClick={handleLogout} className="logout-btn">Logout</button>
      </header>

      <main className="dashboard-main">
        <div className="balance-card">
          <h2>Current Balance</h2>
          <div className="balance-amount">
            ₹{wallet?.balance?.toFixed(2) || '0.00'}
          </div>
          {wallet?.emergency_fund !== undefined && (
            <div className="additional-balance">
              <span>Emergency Fund: ₹{wallet.emergency_fund?.toFixed(2) || '0.00'}</span>
              <span>Goals: ₹{wallet.goals?.toFixed(2) || '0.00'}</span>
            </div>
          )}
        </div>

        <div className="transaction-card">
          <div className="transaction-tabs">
            <button
              className={action === 'deposit' ? 'active' : ''}
              onClick={() => setAction('deposit')}
            >
              Deposit
            </button>
            <button
              className={action === 'withdraw' ? 'active' : ''}
              onClick={() => setAction('withdraw')}
            >
              Withdraw
            </button>
          </div>

          {error && <div className="error-message">{error}</div>}
          {success && <div className="success-message">{success}</div>}

          <form onSubmit={handleSubmit}>
            <div className="form-group">
              <label>Amount (₹)</label>
              <input
                type="number"
                step="0.01"
                min="0"
                value={amount}
                onChange={(e) => setAmount(e.target.value)}
                required
                placeholder="Enter amount"
              />
            </div>

            <button
              type="button"
              onClick={handleRequestOTP}
              className="otp-btn"
              disabled={loading || !amount}
            >
              Request OTP
            </button>

            <div className="form-group">
              <label>OTP</label>
              <input
                type="text"
                maxLength={6}
                value={otp}
                onChange={(e) => setOtp(e.target.value)}
                required
                placeholder="Enter OTP"
              />
            </div>

            <button type="submit" disabled={loading || !otp}>
              {loading ? 'Processing...' : action === 'deposit' ? 'Deposit' : 'Withdraw'}
            </button>
          </form>
        </div>
      </main>
    </div>
  );
}
