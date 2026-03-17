import { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { api } from '../services/api';
import './Dashboard.css';

export default function AcademicPortal() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const studentId = searchParams.get('student_id');
  
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [data, setData] = useState<any>(null);
  const [walletBalance, setWalletBalance] = useState<number>(0);

  useEffect(() => {
    loadPortalData();
  }, [studentId]);

  const loadPortalData = async () => {
    setLoading(true);
    setError('');
    try {
      // Get portal data (Attendance, Fees, Notifications)
      // If studentId is provided, we are a parent viewing for a child
      const portalData = await api.request(`/institute/dashboard/${studentId ? `?student_id=${studentId}` : ''}`);
      setData(portalData);

      // Get current user's wallet balance for fee payment
      // We assume student persona or someone with a wallet is accessing this
      const walletData = await api.getBalance('student');
      setWalletBalance(parseFloat(walletData.balance as any));
      } catch (err: any) {      setError(err.message || 'Failed to load Academic Portal');
    } finally {
      setLoading(false);
    }
  };

  const [showDepositModal, setShowDepositModal] = useState(false);
  const [depositAmount, setDepositAmount] = useState('');
  const [depositOTP, setDepositOTP] = useState('');
  const [otpSent, setOtpSent] = useState(false);
  const [cacheKey, setCacheKey] = useState('');
  const [debugOTP, setDebugOTP] = useState('');

  const handlePayFee = async (paymentId: number, amount: number) => {
    console.log('handlePayFee called with:', { paymentId, amount });
    
    if (!paymentId) {
      setError('No fee payment record found. Please contact the Institute.');
      return;
    }

    if (walletBalance < amount) {
      setError(`Insufficient wallet balance (₹${walletBalance.toFixed(2)}). Please add funds first.`);
      return;
    }

    if (!window.confirm(`Confirm payment of ₹${amount.toFixed(2)} for tuition fees?`)) return;

    try {
      console.log('Initiating payment request...');
      setLoading(true);
      setError('');
      setSuccess('Processing your payment, please wait...');
      
      const res = await api.payFeeSelf(paymentId);
      console.log('Payment response:', res);
      setSuccess('Fee paid successfully! Receipt has been generated.');
      loadPortalData();
    } catch (err: any) {
      console.error('Payment error:', err);
      setError(err.message || 'Payment failed');
    } finally {
      setLoading(false);
    }
  };

  const handleRequestDepositOTP = async () => {
    if (!depositAmount || parseFloat(depositAmount) <= 0) {
      setError('Please enter a valid amount');
      return;
    }
    try {
      const res: any = await api.requestOTP('student', parseFloat(depositAmount));
      setCacheKey(res.cache_key);
      if (res.otp_code) setDebugOTP(res.otp_code);
      setOtpSent(true);
      setSuccess('OTP sent to your registered email');
    } catch (err: any) {
      setError(err.message);
    }
  };

  const handleConfirmDeposit = async () => {
    if (!depositOTP) {
      setError('Please enter the OTP');
      return;
    }
    try {
      await api.request('/student/wallet/deposit/', {
        method: 'POST',
        body: JSON.stringify({
          amount: parseFloat(depositAmount),
          otp: depositOTP,
          cache_key: cacheKey
        })
      });
      setSuccess(`₹${depositAmount} added to your wallet successfully!`);
      setShowDepositModal(false);
      setDepositAmount('');
      setDepositOTP('');
      setOtpSent(false);
      setCacheKey('');
      loadPortalData();
    } catch (err: any) {
      setError(err.message);
    }
  };

  const [showDropdown, setShowDropdown] = useState(false);

  const handleLogout = () => {
    api.clearToken();
    navigate('/login');
  };

  if (loading) return <div className="loading">Opening Academic Portal...</div>;
  
  if (!data || data.message === 'No institute profile linked.') {
    return (
      <div className="dashboard-container">
        <header className="dashboard-header">
          <button onClick={() => navigate(-1)} className="back-btn">← Back</button>
          <h1>Academic Portal 🎓</h1>
        </header>
        <main className="dashboard-main">
          <div className="info-card" style={{ textAlign: 'center', padding: '3rem' }}>
            <div style={{ fontSize: '4rem' }}>🛰️</div>
            <h2>No Academic Link Found</h2>
            <p>You (or your child) are not currently enrolled in any registered Institute.</p>
            <button onClick={() => navigate('/select-module')} className="submit-btn" style={{ marginTop: '1rem' }}>Return Home</button>
          </div>
        </main>
      </div>
    );
  }

  // If the data is for a different role, we might be in the wrong portal
  if (data.role === 'OWNER') {
    return (
      <div className="dashboard-container">
        <header className="dashboard-header">
          <button onClick={() => navigate(-1)} className="back-btn">← Back</button>
          <h1>Wrong Portal</h1>
        </header>
        <main className="dashboard-main">
          <div className="info-card" style={{ textAlign: 'center', padding: '2rem' }}>
            <h2>Institute Owner Detected</h2>
            <p>You are logged in as an Institute Owner. Please use the Institute Dashboard.</p>
            <button onClick={() => navigate('/dashboard/institute')} className="submit-btn">Go to Institute Dashboard</button>
          </div>
        </main>
      </div>
    );
  }

  return (
    <div className="dashboard-container">
      <header className="modern-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '0.75rem 2rem', background: 'white', boxShadow: '0 2px 10px rgba(0,0,0,0.1)', position: 'sticky', top: 0, zIndex: 1000 }}>
        {/* Left: Back button */}
        <div style={{ flex: '0 0 120px' }}>
          <button onClick={() => navigate(-1)} className="back-link" style={{ background: 'transparent', color: '#4a5568', border: 'none', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '5px', cursor: 'pointer', padding: 0 }}>
            <span style={{ fontSize: '1.2rem' }}>←</span>
            <span className="hide-mobile">Back</span>
          </button>
        </div>

        {/* Center: Title */}
        <h1 style={{ flex: 1, textAlign: 'center', margin: 0, fontSize: '1.25rem', fontWeight: 700, color: '#2c3e50' }}>Academic Portal 🎓</h1>

        {/* Right: Actions & Profile */}
        <div style={{ flex: '0 0 120px', display: 'flex', justifyContent: 'flex-end', alignItems: 'center', gap: '15px', position: 'relative' }}>
          <button 
            onClick={loadPortalData} 
            title="Refresh Data"
            style={{ background: 'none', border: 'none', cursor: 'pointer', fontSize: '1.2rem', padding: '5px' }}
          >
            🔄
          </button>
          
          <div 
            className="profile-trigger" 
            onClick={() => setShowDropdown(!showDropdown)}
            style={{ display: 'flex', alignItems: 'center', gap: '10px', cursor: 'pointer', padding: '5px 10px', borderRadius: '30px', transition: 'background 0.2s' }}
          >
            <span className="hide-mobile" style={{ fontSize: '0.85rem', fontWeight: 600, color: '#4a5568' }}>
              {data.profile?.student_name ? data.profile.student_name.split(' ')[0] : 'Student'}
            </span>
            <div className="avatar" style={{ width: '35px', height: '35px', background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)', color: 'white', borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 'bold', fontSize: '0.9rem' }}>
              {data.profile?.student_name?.[0] || 'S'}
            </div>
          </div>

          {showDropdown && (
            <div className="profile-dropdown" style={{ position: 'absolute', top: '100%', right: 0, marginTop: '10px', background: 'white', borderRadius: '12px', boxShadow: '0 10px 25px rgba(0,0,0,0.15)', border: '1px solid #eee', minWidth: '180px', overflow: 'hidden', animation: 'fadeIn 0.2s ease' }}>
              <div style={{ padding: '15px', borderBottom: '1px solid #f5f5f5', background: '#fafafa' }}>
                <p style={{ margin: 0, fontWeight: 'bold', fontSize: '0.9rem', color: '#2c3e50' }}>{data.profile?.student_name}</p>
                <p style={{ margin: 0, fontSize: '0.75rem', color: '#7f8c8d' }}>Student Account</p>
              </div>
              <button 
                onClick={handleLogout}
                style={{ width: '100%', padding: '12px 15px', border: 'none', background: 'transparent', textAlign: 'left', display: 'flex', alignItems: 'center', gap: '10px', cursor: 'pointer', color: '#e74c3c', fontWeight: 600, fontSize: '0.9rem' }}
              >
                <span>🚪</span> Logout
              </button>
            </div>
          )}
        </div>
      </header>

      <div style={{ background: '#f8fafc', padding: '10px 24px', color: '#64748b', fontSize: '0.85rem', borderBottom: '1px solid #e2e8f0', display: 'flex', alignItems: 'center', gap: '8px' }}>
        <span>📍</span> Enrolled at: <strong style={{ color: '#334155' }}>{data.institute_name}</strong>
      </div>

      <main className="dashboard-main">
        {error && <div className="error-message" style={{ marginBottom: '1rem' }}>{error}</div>}
        {success && <div className="success-message" style={{ marginBottom: '1rem' }}>{success}</div>}

        <div className="dashboard-grid" style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '1.5rem' }}>
          
          {/* FEE PAYMENT SECTION */}
          <div className="info-card">
            <h3 style={{ display: 'flex', justifyContent: 'space-between' }}>
              Fee Status 💸
              <span className={`tag ${data.current_fee_status?.status || 'PENDING'}`} style={{ fontSize: '0.7rem' }}>
                {data.current_fee_status?.status || 'PENDING'}
              </span>
            </h3>
            {/* Debug info */}
            <div style={{ fontSize: '0.6rem', color: '#999', marginBottom: '5px' }}>
              Payment ID: {data.current_fee_status?.id} | Status: {data.current_fee_status?.status}
            </div>
            <div style={{ marginTop: '1rem' }}>
              <div style={{ fontSize: '2rem', fontWeight: 'bold', color: data.current_fee_status?.status === 'PAID' ? '#2ecc71' : '#e74c3c' }}>
                ₹{parseFloat(data.current_fee_status?.total_amount || '0').toFixed(2)}
              </div>
              <p style={{ color: '#666', fontSize: '0.8rem' }}>
                Monthly Tuition Fee for {data.current_fee_status ? ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'][data.current_fee_status.month-1] : '---'} {data.current_fee_status?.year || ''}
              </p>
              
              {data.current_fee_status?.status !== 'PAID' ? (
                <div style={{ marginTop: '1.5rem', padding: '15px', background: '#f8f9fa', borderRadius: '10px', border: '1px solid #eee' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '10px', fontSize: '0.9rem', alignItems: 'center' }}>
                    <span>Your Wallet Balance: <strong>₹{walletBalance.toFixed(2)}</strong></span>
                    <button 
                      onClick={() => setShowDepositModal(true)}
                      style={{ padding: '4px 10px', background: '#667eea', color: 'white', border: 'none', borderRadius: '5px', fontSize: '0.75rem', cursor: 'pointer' }}
                    >
                      ➕ Add Funds
                    </button>
                  </div>
                  <button 
                    onClick={() => {
                      console.log('Pay Fees button clicked!');
                      const id = data.current_fee_status?.id;
                      const amt = parseFloat(data.current_fee_status?.total_amount || '0');
                      console.log('Detected payment info:', { id, amt });
                      if (id) {
                        handlePayFee(id, amt);
                      } else {
                        console.error('Payment ID is missing in data.current_fee_status');
                        setError('Payment record ID missing. Please refresh.');
                      }
                    }}
                    className="submit-btn" 
                    style={{ background: '#2ecc71', width: '100%' }}
                  >
                    💳 Pay Fees Now
                  </button>
                </div>
              ) : (
                <div style={{ marginTop: '1.5rem', padding: '15px', background: '#f0fdf4', borderRadius: '10px', border: '1px solid #dcfce7', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span style={{ fontSize: '0.9rem', color: '#166534' }}>Wallet Balance: <strong>₹{walletBalance.toFixed(2)}</strong></span>
                  <button 
                    onClick={() => setShowDepositModal(true)}
                    style={{ padding: '6px 12px', background: '#667eea', color: 'white', border: 'none', borderRadius: '6px', fontSize: '0.8rem', fontWeight: 600, cursor: 'pointer' }}
                  >
                    ➕ Add Funds
                  </button>
                </div>
              )}
            </div>
          </div>

          {/* Deposit Modal */}
          {showDepositModal && (
            <div className="modal-overlay" style={{ display: 'flex', background: 'rgba(0,0,0,0.5)' }}>
              <div className="modal" style={{ maxWidth: '400px' }}>
                <h2>Add Funds to Wallet 💰</h2>
                <p>Top up your wallet to pay fees and manage expenses.</p>
                
                {!otpSent ? (
                  <div className="form-group" style={{ textAlign: 'left' }}>
                    <label>Amount (₹)</label>
                    <input 
                      type="number" 
                      value={depositAmount} 
                      onChange={e => setDepositAmount(e.target.value)} 
                      placeholder="Enter amount (e.g. 1000)"
                      required 
                    />
                    <button 
                      onClick={handleRequestDepositOTP}
                      className="submit-btn" 
                      style={{ marginTop: '1rem' }}
                    >
                      Next: Verify Identity
                    </button>
                  </div>
                ) : (
                  <div className="form-group" style={{ textAlign: 'left' }}>
                    <label>Enter OTP Code</label>
                    <input 
                      type="text" 
                      value={depositOTP} 
                      onChange={e => setDepositOTP(e.target.value)} 
                      placeholder="6-digit code"
                      maxLength={6}
                      required 
                    />
                    {debugOTP && (
                      <div style={{ background: '#fff9db', padding: '10px', borderRadius: '5px', marginTop: '10px', fontSize: '0.85rem', border: '1px solid #fab005', color: '#856404' }}>
                        <strong>Test OTP:</strong> {debugOTP}
                      </div>
                    )}
                    <button 
                      onClick={handleConfirmDeposit}
                      className="submit-btn" 
                      style={{ marginTop: '1rem', background: '#2ecc71' }}
                    >
                      Confirm Deposit
                    </button>
                    <button 
                      onClick={() => setOtpSent(false)}
                      style={{ width: '100%', padding: '10px', background: 'none', border: 'none', color: '#666', cursor: 'pointer', fontSize: '0.85rem' }}
                    >
                      ← Back to amount
                    </button>
                  </div>
                )}
                
                {!otpSent && (
                  <button 
                    className="cancel-btn" 
                    onClick={() => { setShowDepositModal(false); setDepositAmount(''); }}
                  >
                    Cancel
                  </button>
                )}
              </div>
            </div>
          )}

          {/* ATTENDANCE SECTION */}
          <div className="info-card">
            <h3>Attendance Tracker 📅</h3>
            <div style={{ marginTop: '1rem', textAlign: 'center' }}>
              <div style={{ fontSize: '2.5rem', fontWeight: 'bold', color: '#3498db' }}>{data.attendance?.percentage}%</div>
              <p style={{ color: '#666', fontSize: '0.8rem' }}>Overall Attendance Rate</p>
              
              <div style={{ marginTop: '1.5rem', textAlign: 'left' }}>
                <h4 style={{ fontSize: '0.9rem', marginBottom: '10px' }}>Recent Records:</h4>
                {data.attendance?.recent?.length > 0 ? (
                  data.attendance.recent.map((a: any) => (
                    <div key={a.id} style={{ display: 'flex', justifyContent: 'space-between', padding: '8px 0', borderBottom: '1px solid #f0f0f0', fontSize: '0.85rem' }}>
                      <span>{new Date(a.date).toLocaleDateString()}</span>
                      <span style={{ fontWeight: 'bold', color: a.status === 'PRESENT' ? '#27ae60' : '#e74c3c' }}>{a.status}</span>
                    </div>
                  ))
                ) : (
                  <p style={{ fontSize: '0.8rem', color: '#999' }}>No attendance marked yet.</p>
                )}
              </div>
            </div>
          </div>

          {/* NOTIFICATIONS / REMINDERS */}
          <div className="info-card" style={{ gridColumn: 'span 1' }}>
            <h3>Institute Notices 🔔</h3>
            <div style={{ marginTop: '1rem', maxHeight: '350px', overflowY: 'auto' }}>
              {data.notifications?.length > 0 ? (
                data.notifications.map((n: any) => (
                  <div key={n.id} style={{ padding: '12px', borderBottom: '1px solid #eee', background: n.notification_type === 'FEE_REMINDER' ? '#fff5f5' : 'transparent', borderRadius: '8px', marginBottom: '8px' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '5px' }}>
                      <strong style={{ fontSize: '0.75rem', color: '#667eea' }}>{n.notification_type.replace('_', ' ')}</strong>
                      <span style={{ fontSize: '0.7rem', color: '#999' }}>{new Date(n.sent_at).toLocaleDateString()}</span>
                    </div>
                    <p style={{ fontSize: '0.85rem', margin: 0, lineHeight: '1.4' }}>{n.message}</p>
                  </div>
                ))
              ) : (
                <p style={{ textAlign: 'center', color: '#999', padding: '2rem' }}>No notices from the Institute.</p>
              )}
            </div>
          </div>

          {/* FEE HISTORY */}
          <div className="info-card" style={{ gridColumn: 'span 1' }}>
            <h3>Payment History 📜</h3>
            <div className="table-container" style={{ marginTop: '1rem' }}>
              <table className="statement-table" style={{ fontSize: '0.85rem' }}>
                <thead>
                  <tr>
                    <th>Period</th>
                    <th>Amount</th>
                    <th style={{ textAlign: 'right' }}>Status</th>
                  </tr>
                </thead>
                <tbody>
                  {data.recent_fees?.map((f: any) => (
                    <tr key={f.id}>
                      <td>{['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'][f.month-1]} {f.year}</td>
                      <td>₹{parseFloat(f.total_amount).toFixed(2)}</td>
                      <td style={{ textAlign: 'right' }}>
                        <span className={`tag ${f.status}`}>{f.status}</span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

        </div>
      </main>
    </div>
  );
}
