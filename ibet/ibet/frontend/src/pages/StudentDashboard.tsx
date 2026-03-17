import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../services/api';
import './Dashboard.css';

interface WalletData {
  balance: number;
}

interface DailySpending {
  date: string;
  daily_limit: number;
  amount_spent: number;
  remaining_amount: number;
  is_locked: boolean;
  locked_by_parent: boolean;
  lock_reason: string;
}

interface MonthlySummary {
  month: number;
  year: number;
  total_allowance: number;
  total_spent: number;
  remaining_amount: number;
  days_elapsed: number;
}

export default function StudentDashboard() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [wallet, setWallet] = useState<WalletData>({ balance: 0 });
  const [specialWallet, setSpecialWallet] = useState<WalletData>({ balance: 0 });
  const [dailySpending, setDailySpending] = useState<DailySpending>({
    date: '', daily_limit: 0, amount_spent: 0, remaining_amount: 0, 
    is_locked: false, locked_by_parent: false, lock_reason: ''
  });
  const [monthlySummary, setMonthlySummary] = useState<MonthlySummary>({
    month: 0, year: 0, total_allowance: 0, total_spent: 0, remaining_amount: 0, days_elapsed: 0
  });
  const [transactions, setTransactions] = useState<any[]>([]);
  const [showFullHistory, setShowFullHistory] = useState(false);
  const [activeOtpRequests, setActiveOtpRequests] = useState<any[]>([]);
  const [userProfile, setUserProfile] = useState<any>(null);
  const [showStatementModal, setShowStatementModal] = useState(false);
  const [statementFilters, setStatementFilters] = useState({
    year: new Date().getFullYear(),
    month: new Date().getMonth() + 1,
    day: ''
  });
  const [instituteData, setInstituteData] = useState<any>(null);
  const [currentUser, setCurrentUser] = useState<{username: string, persona: string, serverTime?: string, serverDate?: string} | null>(null);
  const [resetsIn, setResetsIn] = useState<string>('');

  // Modal states
  const [showModal, setShowModal] = useState(false);
  const [action, setAction] = useState<'withdraw' | 'withdraw_special'>('withdraw');
  const [amount, setAmount] = useState('');
  const [description, setDescription] = useState('');
  const [processing, setProcessing] = useState(false);
  
  // OTP states
  const [showOtpInput, setShowOtpInput] = useState(false);
  const [otp, setOtp] = useState('');
  const [otpRequestId, setOtpRequestId] = useState<number | null>(null);
  
  // Account Unlock States
  const [showUnlockModal, setShowUnlockModal] = useState(false);
  const [unlockOtp, setUnlockOtp] = useState('');
  const [unlocking, setUnlocking] = useState(false);

  useEffect(() => {
    loadStudentData();
    
    // Dynamic Mode: Background Polling every 30 seconds
    const pollInterval = setInterval(() => {
      loadStudentData(true);
    }, 30000);

    return () => {
      clearInterval(pollInterval);
    };
  }, []);

  const loadStudentData = async (silent = false) => {
    if (!silent) setLoading(true);
    setError('');
    try {
      const [dashboardData, profileData, instData, otpData] = await Promise.all([
        api.getStudentDashboard(),
        api.getProfile(),
        api.getInstituteDashboard().catch(() => null),
        api.getStudentOtpRequests().catch(() => ({ results: [] }))
      ]);
      
      if (dashboardData) {
        setWallet({ balance: dashboardData.wallet_balance });
        setSpecialWallet({ balance: dashboardData.special_wallet_balance || 0 });
        setResetsIn(dashboardData.resets_in || '');
        setCurrentUser({ 
          username: dashboardData.user_name || 'Unknown', 
          persona: dashboardData.user_persona || 'STUDENT',
          serverTime: dashboardData.server_time,
          serverDate: dashboardData.server_date
        });
        setDailySpending({
          date: new Date().toISOString(),
          daily_limit: dashboardData.daily_limit,
          amount_spent: dashboardData.today_spent,
          remaining_amount: dashboardData.today_remaining,
          is_locked: dashboardData.is_locked,
          locked_by_parent: dashboardData.is_locked,
          lock_reason: dashboardData.active_locks > 0 ? 'Locked' : ''
        });
        setMonthlySummary({
          month: new Date().getMonth() + 1,
          year: new Date().getFullYear(),
          total_allowance: dashboardData.monthly_allowance,
          total_spent: dashboardData.monthly_spent,
          remaining_amount: dashboardData.monthly_remaining,
          days_elapsed: 1
        });
      }

      if (profileData) setUserProfile(profileData);
      if (instData && !instData.message) setInstituteData(instData);
      
      if (otpData) {
        const pending = (otpData.results || otpData).filter((r: any) => !r.is_used && new Date(r.expires_at) > new Date());
        setActiveOtpRequests(pending);
      }

      const txData = await api.getStudentTransactions();
      setTransactions(txData.results || txData || []);
    } catch (err) {
      setError('Failed to load dashboard data');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleWithdraw = async (e: React.FormEvent) => {
    e.preventDefault();
    setProcessing(true);
    setError('');
    setSuccess('');

    try {
      const val = parseFloat(amount);
      let response;
      if (action === 'withdraw_special') {
        response = await api.withdrawSpecial(val, description);
      } else {
        response = await api.withdrawStudent(val);
      }
      
      if (response && (response.requires_parent_otp || response.status === 'pending_approval')) {
        setOtpRequestId(response.otp_request_id);
        setShowOtpInput(true);
        setSuccess(response.message || 'Parent approval required.');
        setProcessing(false);
        loadStudentData(true); // Refresh to show the pending request
        return;
      }

      setSuccess('Withdrawal successful!');
      closeModal();
      loadStudentData(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Withdrawal failed');
    } finally {
      setProcessing(false);
    }
  };

  const handleVerifyOtp = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!otpRequestId || !userProfile?.id) return;
    
    setProcessing(true);
    setError('');
    try {
      await api.verifyParentOTP(otp, otpRequestId, userProfile.id);
      setSuccess('Parent approval verified! Withdrawal completed.');
      setTimeout(() => {
        closeModal();
        loadStudentData(true);
      }, 1500);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'OTP verification failed');
    } finally {
      setProcessing(false);
    }
  };

  const handleVerifyUnlockOtp = async (e: React.FormEvent) => {
    e.preventDefault();
    setUnlocking(true);
    setError('');
    try {
      const data = await api.getStudentDashboard();
      if (!data.active_lock_id) {
        setError('No active lock found to verify.');
        return;
      }
      await api.verifySpendingUnlock(data.active_lock_id, unlockOtp);
      setSuccess('Account unlocked successfully!');
      setTimeout(() => {
        setShowUnlockModal(false);
        setUnlockOtp('');
        loadStudentData(true);
      }, 1500);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unlock verification failed');
    } finally {
      setUnlocking(false);
    }
  };

  const closeModal = () => {
    setShowModal(false);
    setShowOtpInput(false);
    setOtp('');
    setOtpRequestId(null);
    setAmount('');
    setDescription('');
    setError('');
    setSuccess('');
  };

  const handleDownloadStatement = async () => {
    try {
      const data = await api.getStudentOwnStatement(statementFilters.year, statementFilters.month, statementFilters.day ? parseInt(statementFilters.day) : undefined);
      const transactions = data.results || data;
      const headers = ['Date', 'Description', 'Type', 'Amount'];
      const rows = transactions.map((tx: any) => [
        new Date(tx.date).toLocaleDateString(),
        tx.description,
        tx.transaction_type,
        tx.amount
      ]);
      const csvContent = [headers, ...rows].map(e => e.join(",")).join("\n");
      const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
      const link = document.createElement("a");
      const url = URL.createObjectURL(blob);
      link.setAttribute("href", url);
      link.setAttribute("download", `Statement_${statementFilters.month}_${statementFilters.year}.csv`);
      link.style.visibility = 'hidden';
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    } catch (err) {
      setError('Failed to download statement');
    }
  };

  const handlePrintStatement = async () => {
    try {
      const data = await api.getStudentOwnStatement(statementFilters.year, statementFilters.month, statementFilters.day ? parseInt(statementFilters.day) : undefined);
      const printWindow = window.open('', '_blank');
      if (!printWindow) return;

      const transactions = data.results || data;
      const html = `
        <html>
          <head>
            <title>Student Transaction Statement</title>
            <style>
              body { font-family: sans-serif; padding: 20px; }
              h1 { color: #667eea; text-align: center; }
              table { width: 100%; border-collapse: collapse; margin-top: 20px; }
              th, td { border: 1px solid #ddd; padding: 12px; text-align: left; }
              th { background-color: #f8f9fa; }
              .amount { text-align: right; font-weight: bold; }
              .INC { color: #2ecc71; }
              .EXP { color: #e74c3c; }
              .DEPOSIT { color: #2ecc71; }
            </style>
          </head>
          <body>
            <h1>Financial Statement 📄</h1>
            <div style="margin-bottom: 20px; border-bottom: 2px solid #667eea; padding-bottom: 10px;">
              <p><strong>Student Name:</strong> ${userProfile?.username}</p>
              <p><strong>Account ID:</strong> ${userProfile?.uid}</p>
              <p><strong>Statement Period:</strong> ${statementFilters.month}/${statementFilters.year}</p>
            </div>
            <table>
              <thead>
                <tr>
                  <th>Date</th>
                  <th>Description</th>
                  <th>Type</th>
                  <th style="text-align: right;">Amount</th>
                </tr>
              </thead>
              <tbody>
                ${transactions.map((tx: any) => `
                  <tr>
                    <td>${new Date(tx.date).toLocaleDateString()}</td>
                    <td>${tx.description}</td>
                    <td><strong>${tx.transaction_type}</strong></td>
                    <td class="amount ${tx.transaction_type}">${tx.transaction_type === 'EXP' ? '-' : '+'}₹${parseFloat(tx.amount).toFixed(2)}</td>
                  </tr>
                `).join('')}
              </tbody>
            </table>
            <div style="margin-top: 40px; text-align: center; color: #999; font-size: 0.8rem; border-top: 1px solid #eee; padding-top: 10px;">
              Generated by IBET Wallet Application on ${new Date().toLocaleString()}
            </div>
          </body>
        </html>
      `;
      printWindow.document.write(html);
      printWindow.document.close();
      // Use a timeout to ensure CSS loads before printing
      setTimeout(() => {
        printWindow.print();
      }, 500);
    } catch (err) {
      setError('Failed to generate print view');
    }
  };

  const handleLogout = () => { api.clearToken(); navigate('/login'); };

  const getProgressBarColor = () => {
    const percent = (dailySpending.amount_spent / (dailySpending.daily_limit || 1)) * 100;
    if (percent >= 100) return 'danger';
    if (percent >= 80) return 'warning';
    return 'safe';
  };

  if (loading) return <div className="loading">Loading Child Dashboard...</div>;

  return (
    <div className="dashboard-container">
      <header className="dashboard-header glass">
        <button onClick={() => navigate('/select-module')} className="back-btn" style={{ background: 'rgba(255,255,255,0.3)', border: '1px solid rgba(255,255,255,0.3)', color: 'var(--text-main)' }}>← Back</button>
        <h1 style={{ color: 'var(--primary)' }}>Children's Wallet 🎓 {userProfile?.uid && <span style={{ fontSize: '0.9rem', color: 'white', background: 'rgba(255,255,255,0.2)', backdropFilter: 'blur(4px)', padding: '2px 8px', borderRadius: '4px', marginLeft: '10px', verticalAlign: 'middle' }}>{userProfile.uid}</span>}</h1>
        <button onClick={handleLogout} className="logout-btn">Logout</button>
      </header>

      <main className="dashboard-main">
        {error && <div className="error-message">{error}</div>}
        {success && <div className="success-message">{success}</div>}

        <div className="status-bar glass" style={{ display: 'flex', gap: '1.5rem', marginBottom: '2rem', flexWrap: 'wrap', alignItems: 'center' }}>
          <div className="status-item"><span className="label">Account ID:</span><span className="value" style={{ fontWeight: 'bold' }}>{userProfile?.uid || '---'}</span></div>
          <div className="status-item"><span className="label">Role:</span><span className="value">Child</span></div>
          <div className="status-item"><span className="label">Server Date:</span><span className="value">{currentUser?.serverDate || new Date().toLocaleDateString()}</span></div>
          {resetsIn && (
            <div className="status-item" style={{ marginLeft: 'auto', background: 'rgba(255,255,255,0.25)', padding: '4px 12px', borderRadius: '20px' }}>
              <span className="label">⏰ Daily Reset in:</span>
              <span className="value" style={{ fontWeight: 'bold', marginLeft: '5px' }}>{resetsIn}</span>
            </div>
          )}
        </div>

        <div className="balance-grid">
          <div className="balance-card main-balance glass" style={{ background: 'linear-gradient(135deg, rgba(79, 70, 229, 0.8) 0%, rgba(99, 102, 241, 0.8) 100%)' }}>
            <div className="card-header"><h2>Total Balance</h2><span className="icon">💰</span></div>
            <div className="balance-amount">₹{wallet.balance.toFixed(2)}</div>
            <div className="balance-actions">
              <button onClick={() => { setAction('withdraw'); setShowModal(true); setAmount(''); }} className="action-btn">Withdraw</button>
            </div>
          </div>

          <div className="balance-card special-wallet-card glass" style={{ background: 'linear-gradient(135deg, rgba(16, 185, 129, 0.8) 0%, rgba(5, 150, 105, 0.8) 100%)' }}>
            <div className="card-header"><h2>Extra Allowance (Special Wallet)</h2><span className="icon">🎁</span></div>
            <div className="balance-amount">₹{specialWallet.balance.toFixed(2)}</div>
            <div className="balance-actions">
              <button onClick={() => { setAction('withdraw_special'); setShowModal(true); setAmount(''); }} className="action-btn">Withdraw</button>
            </div>
          </div>
        </div>

        <div className="balance-card daily-limit-card glass" style={{ marginTop: '2rem' }}>
          <div className="card-header">
            <h2>Today's Spending</h2>
            <span className={`status-pill ${dailySpending.is_locked ? 'locked' : 'active'}`}>{dailySpending.is_locked ? '🔒 Locked' : '✅ Active'}</span>
          </div>
          <div className="spending-progress-container">
            <div className="progress-stats"><span>Spent: ₹{dailySpending.amount_spent.toFixed(2)}</span><span>Limit: ₹{dailySpending.daily_limit.toFixed(2)}</span></div>
            <div className="progress-bar-bg"><div className={`progress-bar-fill ${getProgressBarColor()}`} style={{ width: `${Math.min(100, (dailySpending.amount_spent / (dailySpending.daily_limit || 1)) * 100)}%` }}></div></div>
            <div className="remaining" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span style={{ fontWeight: '600', color: dailySpending.is_locked ? 'var(--error)' : 'inherit' }}>{dailySpending.is_locked ? 'Limit exceeded!' : `₹${dailySpending.remaining_amount.toFixed(2)} remaining for today`}</span>
              {dailySpending.is_locked && (
                <div style={{ display: 'flex', gap: '8px' }}>
                  <button 
                    onClick={async () => {
                      try {
                        const data = await api.getStudentDashboard();
                        if (data.active_lock_id) {
                          await api.requestUnlock(data.active_lock_id);
                          setSuccess('Unlock request sent to parent!');
                        } else {
                          setError('No active lock record found to unlock.');
                        }
                      } catch (err) {
                        setError('Failed to send unlock request');
                      }
                    }}
                    className="submit-btn" 
                    style={{ width: 'auto', padding: '4px 12px', fontSize: '0.8rem', background: '#f39c12', marginTop: 0 }}
                  >
                    🔓 Request Unlock
                  </button>
                  <button 
                    onClick={() => setShowUnlockModal(true)}
                    className="submit-btn" 
                    style={{ width: 'auto', padding: '4px 12px', fontSize: '0.8rem', background: '#27ae60', marginTop: 0 }}
                  >
                    🔑 Enter Unlock OTP
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Pending Approvals Section */}
        {activeOtpRequests.length > 0 && (
          <div className="transaction-card glass" style={{ marginTop: '1.5rem', padding: '1.25rem' }}>
            <div className="card-header" style={{ marginBottom: '1rem' }}>
              <h2 style={{ fontSize: '1.1rem' }}>⏳ Pending Parent Approvals</h2>
            </div>
            <div>
              {activeOtpRequests.map(req => (
                <div key={req.id} className="glass" style={{ padding: '10px 15px', borderRadius: '10px', marginBottom: '8px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', background: 'rgba(255,255,255,0.1)' }}>
                  <div>
                    <div style={{ fontWeight: 'bold', color: 'white', fontSize: '0.95rem' }}>Amount: ₹{parseFloat(req.amount_requested).toFixed(2)}</div>
                    <div style={{ fontSize: '0.75rem', opacity: 0.8 }}>{req.reason || 'Extra spending'}</div>
                  </div>
                  <div style={{ textAlign: 'right' }}>
                    <div style={{ fontSize: '0.7rem', color: '#ff8a80', fontWeight: 'bold' }}>Exp: {Math.max(0, Math.floor((new Date(req.expires_at).getTime() - new Date().getTime()) / 60000))}m</div>
                    <button onClick={() => { setAmount(req.amount_requested); setOtpRequestId(req.id); setShowOtpInput(true); setShowModal(true); }} className="submit-btn" style={{ padding: '4px 10px', fontSize: '0.75rem', width: 'auto', marginTop: '4px' }}>Enter OTP</button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        <div className="dashboard-grid" style={{ marginTop: '2rem' }}>
          <div className="info-card glass" style={{ gridColumn: '1 / -1' }}>
            <h3>📊 Summary</h3>
            <div className="stats-list" style={{ marginTop: '1.5rem', display: 'flex', gap: '2rem', flexWrap: 'wrap' }}>
              <div className="stat-row" style={{ flex: 1 }}><span>Allowance:</span><span className="stat-value">₹{monthlySummary.total_allowance.toFixed(2)}</span></div>
              <div className="stat-row" style={{ flex: 1 }}><span>Spent:</span><span className="stat-value" style={{ color: '#ff8a80' }}>₹{monthlySummary.total_spent.toFixed(2)}</span></div>
              <div className="stat-row highlight" style={{ flex: 1 }}><span>Remaining:</span><span className="stat-value" style={{ color: '#90EE90' }}>₹{monthlySummary.remaining_amount.toFixed(2)}</span></div>
            </div>
          </div>
        </div>

        <div className="transaction-card glass" style={{ marginTop: '2rem' }}>
          <div className="card-header" style={{ marginBottom: '1.5rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <h2>Recent Activity</h2>
            <div style={{ display: 'flex', gap: '10px' }}>
              <button className="submit-btn" style={{ background: 'rgba(118, 75, 162, 0.8)', width: 'auto', padding: '0.5rem 1.2rem', marginTop: 0 }} onClick={() => setShowStatementModal(true)}>📄 Statement</button>
              <button onClick={() => loadStudentData(true)} className="refresh-btn" style={{ background: 'none', border: 'none', color: 'var(--primary)', cursor: 'pointer', fontWeight: 'bold' }}>🔄 Refresh</button>
            </div>
          </div>
          <div className="table-container">
            {transactions.length === 0 ? <p className="no-data" style={{ color: 'rgba(255,255,255,0.6)' }}>No transactions yet.</p> : (
              <>
                <table className="statement-table">
                  <thead><tr><th style={{ color: 'rgba(255,255,255,0.7)' }}>Date</th><th style={{ color: 'rgba(255,255,255,0.7)' }}>Description</th><th style={{ color: 'rgba(255,255,255,0.7)' }}>Type</th><th style={{ textAlign: 'right', color: 'rgba(255,255,255,0.7)' }}>Amount</th></tr></thead>
                  <tbody>
                    {(showFullHistory ? transactions : transactions.slice(0, 5)).map(tx => (
                      <tr key={tx.id} style={{ borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
                        <td style={{ color: 'rgba(255,255,255,0.8)' }}>{new Date(tx.transaction_date).toLocaleDateString()}</td>
                        <td><div style={{ fontWeight: 'bold' }}>{tx.description}</div></td>
                        <td><span className={`tag ${tx.transaction_type}`} style={{ 
                          background: tx.transaction_type === 'DEPOSIT' || tx.transaction_type === 'INC' ? 'rgba(34, 197, 94, 0.2)' : 'rgba(239, 68, 68, 0.2)',
                          color: tx.transaction_type === 'DEPOSIT' || tx.transaction_type === 'INC' ? '#90EE90' : '#ff8a80'
                        }}>{tx.transaction_type}</span></td>
                        <td style={{ textAlign: 'right', fontWeight: 'bold', color: tx.transaction_type === 'DEPOSIT' || tx.transaction_type === 'INC' ? '#90EE90' : '#ff8a80' }}>
                          {tx.transaction_type === 'DEPOSIT' || tx.transaction_type === 'INC' ? '+' : '-'}₹{parseFloat(tx.amount).toFixed(2)}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
                {transactions.length > 5 && (
                  <div style={{ textAlign: 'center', marginTop: '1.5rem' }}>
                    <button 
                      onClick={() => setShowFullHistory(!showFullHistory)} 
                      className="submit-btn" 
                      style={{ background: 'rgba(255, 255, 255, 0.1)', color: 'white', width: 'auto', border: '1px solid rgba(255, 255, 255, 0.2)', padding: '0.5rem 2rem', marginTop: 0 }}
                    >
                      {showFullHistory ? '↑ Show Less' : '🔍 View All Activity'}
                    </button>
                  </div>
                )}
              </>
            )}
          </div>
        </div>

        {instituteData && (
          <div className="balance-card glass" style={{ marginTop: '2rem', borderTop: '4px solid #3498db' }}>
            <div className="card-header" style={{ marginBottom: '1.5rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div>
                <h2>Academic Profile 🎓</h2>
                <span style={{ color: '#3498db', fontWeight: 'bold' }}>{instituteData.institute_name}</span>
              </div>
              <div style={{ textAlign: 'right' }}>
                <div style={{ fontSize: '0.8rem', opacity: 0.8 }}>Attendance</div>
                <div style={{ fontSize: '1.2rem', fontWeight: 'bold', color: '#27ae60' }}>{instituteData.attendance?.percentage}%</div>
              </div>
            </div>
            
            <div className="info-cards" style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem' }}>
              <div className="info-card">
                <h3>Monthly Fee</h3>
                <div className="info-value">₹{parseFloat(instituteData.profile.monthly_fee).toFixed(2)}</div>
                <div className="info-sub">Due: {instituteData.profile.due_day}th</div>
              </div>
              <div className="info-card">
                <h3>Fee Status</h3>
                <div className="info-value" style={{ color: instituteData.current_fee_status.status === 'PAID' ? '#27ae60' : '#c0392b' }}>
                  {instituteData.current_fee_status.status}
                </div>
                <div className="info-sub">Remaining: ₹{parseFloat(instituteData.current_fee_status.pending_amount).toFixed(2)}</div>
              </div>
            </div>

            {instituteData.notifications?.length > 0 && (
              <div style={{ marginTop: '1.5rem' }}>
                <h3 style={{ fontSize: '1rem', marginBottom: '1rem' }}>Recent Announcements 📣</h3>
                <div className="glass" style={{ padding: '10px', borderRadius: '12px', background: 'rgba(255,255,255,0.05)' }}>
                  {instituteData.notifications.slice(0, 2).map((n: any) => (
                    <div key={n.id} style={{ padding: '8px 0', borderBottom: '1px solid rgba(255,255,255,0.1)', fontSize: '0.85rem' }}>
                      <span style={{ opacity: 0.6, marginRight: '10px' }}>{new Date(n.sent_at).toLocaleDateString()}:</span>
                      {n.message}
                    </div>
                  ))}
                </div>
              </div>
            )}
            
            <button
              onClick={() => navigate('/dashboard/academic')}
              className="submit-btn"
              style={{ marginTop: '1.5rem', background: 'rgba(52, 152, 219, 0.2)', border: '1px solid #3498db', color: 'white' }}
            >
              View Full Academic Portal →
            </button>          </div>
        )}
      </main>

      {showModal && (
        <div className="modal-overlay" onClick={closeModal}>
          <div className="modal glass" onClick={e => e.stopPropagation()}>
            {!showOtpInput ? (
              <>
                <h2>{action === 'withdraw_special' ? 'Withdraw Extra Funds' : 'Withdrawal'} 💸</h2>
                <form onSubmit={handleWithdraw}>
                  <div className="form-group"><label>Amount (₹)</label><input type="number" value={amount} onChange={e => setAmount(e.target.value)} required min="1" step="0.01" /></div>
                  {action === 'withdraw_special' && (<div className="form-group"><label>Reason</label><input type="text" value={description} onChange={e => setDescription(e.target.value)} placeholder="e.g. Books" required /></div>)}
                  <button type="submit" disabled={processing} className="submit-btn">{processing ? 'Processing...' : 'Confirm'}</button>
                  <button type="button" onClick={closeModal} className="cancel-btn">Cancel</button>
                </form>
              </>
            ) : (
              <>
                <h2>Parent Approval Required 🔑</h2>
                <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', marginBottom: '1.5rem' }}>Daily limit exceeded. Enter the 6-digit OTP sent to your parent to complete this withdrawal of ₹{amount}.</p>
                <form onSubmit={handleVerifyOtp}>
                  <div className="form-group"><label>Enter OTP</label><input type="text" value={otp} onChange={e => setOtp(e.target.value)} placeholder="000000" required maxLength={6} style={{ letterSpacing: '8px', textAlign: 'center', fontSize: '1.5rem', background: 'rgba(255,255,255,0.2)', color: 'white' }} /></div>
                  <button type="submit" disabled={processing} className="submit-btn">{processing ? 'Verifying...' : 'Verify & Withdraw'}</button>
                  <button type="button" onClick={closeModal} className="cancel-btn">Cancel</button>
                </form>
              </>
            )}
          </div>
        </div>
      )}
      {showStatementModal && (
        <div className="modal-overlay" onClick={() => setShowStatementModal(false)}>
          <div className="modal glass" onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <h2>View Transaction Statement 📄</h2>
              <button className="close-btn" onClick={() => setShowStatementModal(false)} style={{ color: 'white' }}>×</button>
            </div>
            <div className="form-group" style={{ marginTop: '1.5rem' }}>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
                <div>
                  <label>Year</label>
                  <select value={statementFilters.year} onChange={e => setStatementFilters({...statementFilters, year: parseInt(e.target.value)})} style={{ background: 'rgba(255,255,255,0.2)', color: 'white' }}>
                    {[2024, 2025, 2026].map(y => <option key={y} value={y} style={{ color: 'black' }}>{y}</option>)}
                  </select>
                </div>
                <div>
                  <label>Month</label>
                  <select value={statementFilters.month} onChange={e => setStatementFilters({...statementFilters, month: parseInt(e.target.value)})} style={{ background: 'rgba(255,255,255,0.2)', color: 'white' }}>
                    {Array.from({length: 12}, (_, i) => <option key={i+1} value={i+1} style={{ color: 'black' }}>{new Date(0, i).toLocaleString('default', {month: 'long'})}</option>)}
                  </select>
                </div>
              </div>
            </div>
            <div style={{ display: 'flex', gap: '10px', marginTop: '2rem' }}>
              <button className="submit-btn" style={{ background: 'rgba(118, 75, 162, 0.8)', flex: 1, marginTop: 0 }} onClick={handleDownloadStatement}>📥 Download CSV</button>
              <button className="submit-btn" style={{ background: 'rgba(34, 197, 94, 0.8)', flex: 1, marginTop: 0 }} onClick={handlePrintStatement}>🖨️ Print</button>
            </div>
          </div>
        </div>
      )}
      {showUnlockModal && (
        <div className="modal-overlay" onClick={() => setShowUnlockModal(false)}>
          <div className="modal glass" style={{ textAlign: 'center' }} onClick={e => e.stopPropagation()}>
            <h2>🔓 Unlock Account</h2>
            <p style={{ color: 'var(--text-muted)', marginBottom: '1.5rem' }}>Enter the 6-digit Unlock OTP provided by your parent.</p>
            <form onSubmit={handleVerifyUnlockOtp}>
              <div className="form-group">
                <input 
                  type="text" 
                  value={unlockOtp} 
                  onChange={e => setUnlockOtp(e.target.value)} 
                  placeholder="000000" 
                  required 
                  maxLength={6} 
                  style={{ letterSpacing: '8px', textAlign: 'center', fontSize: '1.5rem', background: 'rgba(255,255,255,0.2)', color: 'white' }} 
                />
              </div>
              <button type="submit" disabled={unlocking} className="submit-btn" style={{ background: 'rgba(39, 174, 96, 0.8)', marginTop: 0 }}>
                {unlocking ? 'Unlocking...' : 'Verify & Unlock'}
              </button>
              <button type="button" onClick={() => setShowUnlockModal(false)} className="cancel-btn">Cancel</button>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
