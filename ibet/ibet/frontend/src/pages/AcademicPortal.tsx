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
  const [showDropdown, setShowDropdown] = useState(false);

  useEffect(() => {
    loadPortalData();
  }, [studentId]);

  const loadPortalData = async () => {
    setLoading(true);
    setError('');
    try {
      const portalData = await api.request(`/institute/dashboard/${studentId ? `?student_id=${studentId}` : ''}`);
      setData(portalData);

      const walletData = await api.getBalance('student');
      setWalletBalance(parseFloat(walletData.balance as any));
    } catch (err: any) {
      setError(err.message || 'Failed to load Academic Portal');
    } finally {
      setLoading(false);
    }
  };

  const [showDepositModal, setShowDepositModal] = useState(false);
  const [showLinkModal, setShowLinkModal] = useState(false);
  const [linkData, setLinkData] = useState({ institute_name: '', student_name: '', parent_mobile: '' });
  const [depositAmount, setDepositAmount] = useState('');
  const [depositOTP, setDepositOTP] = useState('');
  const [cacheKey, setCacheKey] = useState('');
  const [otpSent, setOtpSent] = useState(false);

  const handleLinkInstitute = async () => {
    if (!linkData.institute_name || !linkData.student_name || !linkData.parent_mobile) {
      setError('Please fill in all fields');
      return;
    }
    try {
      setLoading(true);
      setError('');
      await api.linkToInstitute({ ...linkData, student_id: studentId ? parseInt(studentId) : undefined });
      setSuccess('Successfully linked to institute!');
      setShowLinkModal(false);
      loadPortalData();
    } catch (err: any) {
      setError(err.message || 'Linking failed');
    } finally {
      setLoading(false);
    }
  };

  const handlePayFee = async (paymentId: number, amount: number) => {
    if (!paymentId) {
      setError('No fee payment record found. Please contact the Institute.');
      return;
    }

    const pendingAmount = parseFloat(data.current_fee_status.total_amount) - parseFloat(data.current_fee_status.paid_amount);

    if (walletBalance < pendingAmount) {
      setError(`Insufficient wallet balance (₹${walletBalance.toFixed(2)}). You need ₹${pendingAmount.toFixed(2)} to clear your dues. Please add funds first.`);
      return;
    }

    if (!window.confirm(`Confirm payment of ₹${pendingAmount.toFixed(2)} to clear your remaining tuition fees?`)) return;

    try {
      setLoading(true);
      setError('');
      setSuccess('Processing your payment...');
      // We need to ensure the backend supports partial payments or full remaining balance
      await api.payFeeSelf(paymentId);
      setSuccess('Fee paid successfully!');
      loadPortalData();
    } catch (err: any) {
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
      const res = await api.requestOTP('student', parseFloat(depositAmount));
      setOtpSent(true);
      if (res.cache_key) setCacheKey(res.cache_key);
      if (res.otp_code) {
        setSuccess(`DEBUG: Your OTP is ${res.otp_code}`);
      } else {
        setSuccess('OTP sent to your registered email');
      }
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
      await api.deposit('student', parseFloat(depositAmount), depositOTP, cacheKey);
      setSuccess('Funds added successfully!');
      setShowDepositModal(false);
      setOtpSent(false);
      setDepositAmount('');
      setDepositOTP('');
      setCacheKey('');
      loadPortalData();
    } catch (err: any) {
      setError(err.message);
    }
  };

  const handleLogout = () => {
    api.clearToken();
    navigate('/login');
  };

  if (loading && !data) return <div className="loading">Opening Academic Portal...</div>;

  if (!data || data.message === 'No institute profile linked.') {
    return (
      <div className="dashboard-container">
        <header className="dashboard-header glass">
          <button onClick={() => navigate(-1)} className="back-btn">← Back</button>
          <h1>Academic Portal 🎓</h1>
        </header>
        <main className="dashboard-main">
          <div className="info-card glass" style={{ textAlign: 'center', padding: '3rem' }}>
            <div style={{ fontSize: '4rem' }}>🛰️</div>
            <h2>No Academic Link Found</h2>
            <p>You (or your child) are not currently enrolled in any registered Institute.</p>
            {error && <div className="error-message" style={{ marginTop: '1rem' }}>{error}</div>}
            {success && <div className="success-message" style={{ marginTop: '1rem' }}>{success}</div>}
            <div style={{ display: 'flex', gap: '1rem', justifyContent: 'center', marginTop: '1rem' }}>
              <button onClick={() => setShowLinkModal(true)} className="submit-btn" style={{ margin: 0 }}>Link Institute</button>
              <button onClick={() => navigate('/select-module')} className="cancel-btn" style={{ margin: 0 }}>Return Home</button>
            </div>
          </div>
        </main>

        {showLinkModal && (
          <div className="modal-overlay" onClick={() => setShowLinkModal(false)}>
            <div className="modal glass" onClick={e => e.stopPropagation()}>
              <h2>Link to Institute 🏫</h2>
              <div className="form-group">
                <label>Institute Name</label>
                <input type="text" value={linkData.institute_name} onChange={e => setLinkData({ ...linkData, institute_name: e.target.value })} placeholder="e.g. Racing Club" required />
              </div>
              <div className="form-group">
                <label>Student Name (as registered)</label>
                <input type="text" value={linkData.student_name} onChange={e => setLinkData({ ...linkData, student_name: e.target.value })} placeholder="e.g. Vaidhy" required />
              </div>
              <div className="form-group">
                <label>Parent Mobile (as registered)</label>
                <input type="text" value={linkData.parent_mobile} onChange={e => setLinkData({ ...linkData, parent_mobile: e.target.value })} placeholder="e.g. 6383514666" required />
              </div>
              <button onClick={handleLinkInstitute} className="submit-btn" disabled={loading}>Link Now</button>
              <button onClick={() => setShowLinkModal(false)} className="cancel-btn">Cancel</button>
            </div>
          </div>
        )}
      </div>
    );
  }

  return (
    <div className="dashboard-container">
      <header className="dashboard-header glass" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '0.75rem 2rem', background: 'rgba(255, 255, 255, 0.45)', backdropFilter: 'blur(15px)', borderBottom: '1px solid rgba(255, 255, 255, 0.3)', position: 'sticky', top: 0, zIndex: 1000 }}>
        <div style={{ flex: '0 0 120px' }}>
          <button onClick={() => navigate(-1)} className="back-btn" style={{ background: 'rgba(255,255,255,0.3)', color: 'var(--text-main)', border: '1px solid rgba(255,255,255,0.3)', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '5px', cursor: 'pointer', padding: '6px 12px' }}>
            <span>←</span>
            <span className="hide-mobile">Back</span>
          </button>
        </div>

        <h1 style={{ flex: 1, textAlign: 'center', margin: 0, fontSize: '1.25rem', fontWeight: 800, color: 'var(--primary)' }}>Academic Portal 🎓</h1>

        <div style={{ flex: '0 0 120px', display: 'flex', justifyContent: 'flex-end', alignItems: 'center', gap: '15px', position: 'relative' }}>
          <button onClick={loadPortalData} title="Refresh Data" style={{ background: 'none', border: 'none', cursor: 'pointer', fontSize: '1.2rem', padding: '5px' }}>🔄</button>
          <div className="profile-trigger glass" onClick={() => setShowDropdown(!showDropdown)} style={{ display: 'flex', alignItems: 'center', gap: '10px', cursor: 'pointer', padding: '5px 10px', borderRadius: '30px', background: 'rgba(255,255,255,0.2)', border: '1px solid rgba(255,255,255,0.3)' }}>
            <span className="hide-mobile" style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--text-main)' }}>{data.profile?.student_name?.split(' ')[0] || 'Student'}</span>
            <div className="avatar" style={{ width: '35px', height: '35px', background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)', color: 'white', borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 'bold', fontSize: '0.9rem' }}>{data.profile?.student_name?.[0] || 'S'}</div>
          </div>
          {showDropdown && (
            <div className="profile-dropdown glass" style={{ position: 'absolute', top: '100%', right: 0, marginTop: '10px', background: 'rgba(255,255,255,0.8)', backdropFilter: 'blur(10px)', borderRadius: '12px', boxShadow: '0 10px 25px rgba(0,0,0,0.15)', border: '1px solid rgba(255,255,255,0.3)', minWidth: '180px', overflow: 'hidden' }}>
              <div style={{ padding: '15px', borderBottom: '1px solid rgba(255,255,255,0.1)', background: 'rgba(255,255,255,0.1)' }}>
                <p style={{ margin: 0, fontWeight: 'bold', fontSize: '0.9rem', color: 'var(--text-main)' }}>{data.profile?.student_name}</p>
                <p style={{ margin: 0, fontSize: '0.75rem', color: 'var(--text-muted)' }}>Student Account</p>
              </div>
              <button onClick={handleLogout} style={{ width: '100%', padding: '12px 15px', border: 'none', background: 'transparent', textAlign: 'left', display: 'flex', alignItems: 'center', gap: '10px', cursor: 'pointer', color: '#e74c3c', fontWeight: 600, fontSize: '0.9rem' }}><span>🚪</span> Logout</button>
            </div>
          )}
        </div>
      </header>

      <div className="glass" style={{ background: 'rgba(255,255,255,0.2)', padding: '10px 24px', color: 'var(--text-muted)', fontSize: '0.85rem', borderBottom: '1px solid rgba(255,255,255,0.2)', display: 'flex', alignItems: 'center', gap: '8px' }}>
        <span>📍</span> Enrolled at: <strong style={{ color: 'var(--text-main)' }}>{data.institute_name}</strong>
      </div>

      <main className="dashboard-main">
        {error && <div className="error-message">{error}</div>}
        {success && <div className="success-message">{success}</div>}

        <div className="dashboard-grid" style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '1.5rem' }}>
          <div className="info-card glass">
            <h3 style={{ display: 'flex', justifyContent: 'space-between', color: 'var(--text-main)' }}>Fee Status 💸
              <span className={`tag ${data.current_fee_status?.status || 'PENDING'}`} style={{ fontSize: '0.7rem', background: data.current_fee_status?.status === 'PAID' ? 'rgba(34, 197, 94, 0.2)' : 'rgba(239, 68, 68, 0.2)', color: data.current_fee_status?.status === 'PAID' ? '#90EE90' : '#ff8a80' }}>{data.current_fee_status?.status || 'PENDING'}</span>
            </h3>
            <div style={{ marginTop: '1rem' }}>
              <div style={{ fontSize: '2rem', fontWeight: 800, color: data.current_fee_status?.status === 'PAID' ? '#27ae60' : '#ff8a80' }}>₹{parseFloat(data.current_fee_status?.total_amount || '0').toFixed(2)}</div>
              <p style={{ color: 'var(--text-muted)', fontSize: '0.8rem' }}>Monthly Fee for {data.current_fee_status ? ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'][data.current_fee_status.month-1] : '---'} {data.current_fee_status?.year || ''}</p>
              
              {data.current_fee_status && (
                <div className="glass" style={{ margin: '15px 0', padding: '15px', borderRadius: '12px', background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.1)' }}>
                  <p style={{ display: 'flex', justifyContent: 'space-between', margin: '5px 0', fontSize: '0.9rem' }}><span>Paid:</span> <strong style={{ color: '#27ae60' }}>₹{parseFloat(data.current_fee_status.paid_amount).toFixed(2)}</strong></p>
                  <p style={{ display: 'flex', justifyContent: 'space-between', margin: '5px 0', fontSize: '0.9rem' }}><span>Remaining:</span> <strong style={{ color: '#ff8a80' }}>₹{(parseFloat(data.current_fee_status.total_amount) - parseFloat(data.current_fee_status.paid_amount)).toFixed(2)}</strong></p>
                </div>
              )}
            </div>
            <div className="glass" style={{ background: 'rgba(255,255,255,0.1)', padding: '12px', borderRadius: '10px', margin: '1rem 0', fontSize: '0.85rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span>Wallet: <strong style={{ color: walletBalance < (parseFloat(data.current_fee_status?.total_amount || '0') - parseFloat(data.current_fee_status?.paid_amount || '0')) ? '#ff8a80' : '#90EE90' }}>₹{walletBalance.toFixed(2)}</strong></span>
              <button onClick={() => setShowDepositModal(true)} style={{ background: 'var(--primary)', color: 'white', border: 'none', padding: '4px 10px', borderRadius: '6px', fontSize: '0.75rem', cursor: 'pointer', fontWeight: 'bold' }}>+ Add Funds</button>
            </div>
            {data.current_fee_status?.status !== 'PAID' && (
              <button onClick={() => handlePayFee(data.current_fee_status.id, parseFloat(data.current_fee_status.total_amount))} className="submit-btn" style={{ marginTop: 0 }}>Pay Now</button>
            )}
          </div>

          <div className="info-card glass">
            <h3 style={{ color: 'var(--text-main)' }}>Attendance 📊</h3>
            <div style={{ display: 'flex', justifyContent: 'center', margin: '1.5rem 0' }}>
              <div className="glass" style={{ width: '110px', height: '110px', borderRadius: '50%', border: '6px solid rgba(255,255,255,0.1)', borderTopColor: 'var(--primary)', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center' }}>
                <span style={{ fontSize: '1.5rem', fontWeight: 'bold' }}>{data.attendance.percentage}%</span>
                <span style={{ fontSize: '0.6rem', opacity: 0.7 }}>Present</span>
              </div>
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '8px', textAlign: 'center', fontSize: '0.8rem' }}>
              <div className="glass" style={{ padding: '8px', borderRadius: '8px' }}><div>Pres.</div><div style={{ fontWeight: 800, color: '#90EE90' }}>{data.attendance.present}</div></div>
              <div className="glass" style={{ padding: '8px', borderRadius: '8px' }}><div>Abs.</div><div style={{ fontWeight: 800, color: '#ff8a80' }}>{data.attendance.absent}</div></div>
              <div className="glass" style={{ padding: '8px', borderRadius: '8px' }}><div>Late</div><div style={{ fontWeight: 800, color: '#f1c40f' }}>{data.attendance.late}</div></div>
            </div>
          </div>

          <div className="info-card glass">
            <h3 style={{ color: 'var(--text-main)' }}>Notices 🔔</h3>
            <div style={{ marginTop: '1rem', maxHeight: '200px', overflowY: 'auto' }}>
              {data.notifications.length === 0 ? <p style={{ textAlign: 'center', opacity: 0.5, padding: '2rem' }}>No notices</p> : data.notifications.map((n: any) => (
                <div key={n.id} className="glass" style={{ padding: '10px', borderRadius: '8px', marginBottom: '8px', background: 'rgba(255,255,255,0.1)', borderLeft: '3px solid var(--primary)' }}>
                  <div style={{ fontSize: '0.7rem', opacity: 0.6 }}>{new Date(n.sent_at).toLocaleDateString()}</div>
                  <div style={{ fontWeight: 'bold', fontSize: '0.85rem' }}>{n.notification_type.replace('_', ' ')}</div>
                  <div style={{ fontSize: '0.8rem', marginTop: '4px' }}>{n.message}</div>
                </div>
              ))}
            </div>
          </div>
        </div>

        <div className="transaction-card glass" style={{ marginTop: '2rem' }}>
          <h3>Fee Transaction History 🧾</h3>
          <div className="table-container">
            <table className="statement-table">
              <thead>
                <tr>
                  <th style={{ color: 'rgba(255,255,255,0.7)' }}>Period</th>
                  <th style={{ color: 'rgba(255,255,255,0.7)' }}>Total Fee</th>
                  <th style={{ color: 'rgba(255,255,255,0.7)' }}>Paid</th>
                  <th style={{ color: 'rgba(255,255,255,0.7)' }}>Transaction Date</th>
                  <th style={{ color: 'rgba(255,255,255,0.7)' }}>Status</th>
                </tr>
              </thead>
              <tbody>
                {data.recent_fees?.map((f: any) => (
                  <tr key={f.id} style={{ borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
                    <td style={{ color: 'rgba(255,255,255,0.8)' }}><strong>{['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'][f.month-1]} {f.year}</strong></td>
                    <td style={{ color: 'rgba(255,255,255,0.8)' }}>₹{parseFloat(f.total_amount).toFixed(2)}</td>
                    <td style={{ color: '#90EE90', fontWeight: 'bold' }}>₹{parseFloat(f.paid_amount).toFixed(2)}</td>
                    <td style={{ color: 'rgba(255,255,255,0.6)', fontSize: '0.85rem' }}>{f.payment_date ? new Date(f.payment_date).toLocaleDateString() : '---'}</td>
                    <td>
                      <span className={`tag ${f.status}`} style={{ 
                        fontSize: '0.7rem', 
                        background: f.status === 'PAID' ? 'rgba(34, 197, 94, 0.2)' : 'rgba(239, 68, 68, 0.2)', 
                        color: f.status === 'PAID' ? '#90EE90' : '#ff8a80',
                        padding: '2px 8px',
                        borderRadius: '4px'
                      }}>
                        {f.status}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        <div className="transaction-card glass" style={{ marginTop: '2rem' }}>
          <h3>Detailed Attendance Log</h3>
          <div className="table-container">
            <table className="statement-table">
              <thead>
                <tr>
                  <th style={{ color: 'rgba(255,255,255,0.7)' }}>Date</th>
                  <th style={{ color: 'rgba(255,255,255,0.7)' }}>Status</th>
                  <th style={{ color: 'rgba(255,255,255,0.7)' }}>Marked By</th>
                  <th style={{ color: 'rgba(255,255,255,0.7)' }}>Remarks</th>
                </tr>
              </thead>
              <tbody>
                {data.attendance.recent.map((record: any) => (
                  <tr key={record.id} style={{ borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
                    <td style={{ color: 'rgba(255,255,255,0.8)' }}>{new Date(record.date).toLocaleDateString('en-IN', { weekday: 'short', year: 'numeric', month: 'short', day: 'numeric' })}</td>
                    <td><span className={`tag ${record.status}`} style={{ background: record.status === 'PRESENT' ? 'rgba(34, 197, 94, 0.2)' : 'rgba(239, 68, 68, 0.2)', color: record.status === 'PRESENT' ? '#90EE90' : '#ff8a80' }}>{record.status}</span></td>
                    <td style={{ color: 'var(--primary)', fontWeight: '600', fontSize: '0.85rem' }}>{record.marked_by_username || 'System'}</td>
                    <td style={{ fontSize: '0.85rem', opacity: 0.6 }}>{record.remarks || '---'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </main>

      {showDepositModal && (
        <div className="modal-overlay" onClick={() => setShowDepositModal(false)}>
          <div className="modal glass" onClick={e => e.stopPropagation()}>
            <h2>Add Wallet Funds 💳</h2>
            {!otpSent ? (
              <div className="form-group"><label>Amount (₹)</label><input type="number" value={depositAmount} onChange={e => setDepositAmount(e.target.value)} required min="1" />
              <button onClick={handleRequestDepositOTP} className="submit-btn">Request OTP</button></div>
            ) : (
              <div className="form-group"><label>Enter OTP</label><input type="text" value={depositOTP} onChange={e => setDepositOTP(e.target.value)} required maxLength={6} style={{ textAlign: 'center', fontSize: '1.5rem', letterSpacing: '8px' }} />
              <button onClick={handleConfirmDeposit} className="submit-btn">Confirm Deposit</button>
              <button onClick={() => setOtpSent(false)} className="cancel-btn">Back</button></div>
            )}
            <button onClick={() => setShowDepositModal(false)} className="cancel-btn">Cancel</button>
          </div>
        </div>
      )}
    </div>
  );
}
