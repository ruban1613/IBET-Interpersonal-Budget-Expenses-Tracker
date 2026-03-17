import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../services/api';
import './Dashboard.css';

interface LinkedStudent {
  id: number;
  username: string;
  email: string;
  wallet_balance: number;
}

interface StudentOverview {
  student_id: number;
  wallet_balance: number;
  daily_limit: {
    monthly_budget: number;
    daily_limit_amount: number;
    current_daily_spent: number;
  } | null;
  current_daily_spent: number;
  allowance_history?: any[];
  recent_transactions: Array<{
    id: number;
    amount: number;
    transaction_type: string;
    description: string;
    date: string;
  }>;
}

interface ParentAlert {
  id: number;
  alert_type: string;
  message: string;
  status: string;
  created_at: string;
}

interface ParentWallet {
  balance: number;
}

const EXPENSE_CATEGORIES = [
  { value: 'FOOD', label: 'Food & Dining', icon: '🍴' },
  { value: 'TRANSPORT', label: 'Transportation', icon: '🚗' },
  { value: 'UTILITIES', label: 'Utilities', icon: '💡' },
  { value: 'ENTERTAINMENT', label: 'Entertainment', icon: '🎬' },
  { value: 'SHOPPING', label: 'Shopping', icon: '🛍️' },
  { value: 'HEALTH', label: 'Healthcare', icon: '🏥' },
  { value: 'EDUCATION', label: 'Education', icon: '📚' },
  { value: 'BILLS', label: 'Bills & Payments', icon: '💵' },
  { value: 'OTHER', label: 'Other', icon: '📦' },
];

export default function ParentDashboard() {
  const navigate = useNavigate();
  const [linkedStudents, setLinkedStudents] = useState<LinkedStudent[]>([]);
  const [selectedStudent, setSelectedStudent] = useState<StudentOverview | null>(null);
  const [userProfile, setUserProfile] = useState<any>(null);
  const [alerts, setAlerts] = useState<ParentAlert[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  
  // Institute Data for Selected Student
  const [instituteData, setInstituteData] = useState<any>(null);
  
  // UI Panels
  const [showNotifications, setShowNotifications] = useState(false);
  const [parentWallet, setParentWallet] = useState<ParentWallet | null>(null);
  const [dashboardStats, setDashboardStats] = useState<any>(null);

  // Forms
  const [showLinkForm, setShowLinkForm] = useState(false);
  const [linkUsername, setLinkUsername] = useState('');
  
  // Allowance Form
  const [showAllowanceForm, setShowAllowanceForm] = useState(false);
  const [monthlyAmount, setMonthlyAmount] = useState('');
  const [dailyAllowance, setDailyAllowance] = useState('');
  const [daysInMonth, setDaysInMonth] = useState('30');
  const [allowanceOtp, setAllowanceOtp] = useState('');
  const [showAllowanceOtpInput, setShowAllowanceOtpInput] = useState(false);
  const [allowanceOtpRequestId, setAllowanceOtpRequestId] = useState<number | null>(null);
  const [allowanceGeneratedOtp, setAllowanceGeneratedOtp] = useState<string | null>(null);

  const [showLockForm, setShowLockForm] = useState(false);
  const [showDepositForm, setShowDepositForm] = useState(false);
  const [depositAmount, setDepositAmount] = useState('');
  const [depositDescription, setDepositDescription] = useState('Deposit');
  const [depositing, setDepositing] = useState(false);
  const [showTransferForm, setShowTransferForm] = useState(false);
  const [transferAmount, setTransferAmount] = useState('');
  const [transferOtp, setTransferOtp] = useState('');
  const [transferSubmitting, setTransferSubmitting] = useState(false);
  const [otpGenerated, setOtpGenerated] = useState(false);
  const [generatedOtp, setGeneratedOtp] = useState<string | null>(null);
  const [sendingOtp, setSendingOtp] = useState(false);
  const [otpRequestId, setOtpRequestId] = useState<number | null>(null);

  // Unlock States
  const [showUnlockModal, setShowUnlockModal] = useState(false);
  const [activeLockId, setActiveLockId] = useState<number | null>(null);
  const [unlockOtp, setUnlockOtp] = useState<string | null>(null);

  // Parent expense form
  const [showExpenseModal, setShowExpenseModal] = useState(false);
  const [expenseAmount, setExpenseAmount] = useState('');
  const [expenseCategory, setExpenseCategory] = useState('FOOD');
  const [expenseDescription, setExpenseDescription] = useState('');
  const [recordingExpense, setRecordingExpense] = useState(false);

  // Unlock OTP state
  const [showUnlockOtp, setShowUnlockOtp] = useState(false);
  const [unlockOtpCode, setUnlockOtpCode] = useState<string | null>(null);
  const [unlockStudentName, setUnlockStudentName] = useState<string>('');

  // Statement logic
  const [showStatementModal, setShowStatementModal] = useState(false);
  const [statementType, setStatementType] = useState<'parent' | 'student'>('parent');
  const [statementData, setStatementData] = useState<any[]>([]);
  const [filterYear, setYear] = useState(new Date().getFullYear());
  const [filterMonth, setMonth] = useState(new Date().getMonth() + 1);
  const [filterDay, setDay] = useState('');
  const [loadingStatement, setLoadingStatement] = useState(false);

  useEffect(() => {
    loadParentData();
  }, []);

  useEffect(() => {
    if (monthlyAmount && daysInMonth && parseInt(daysInMonth) > 0) {
      const daily = (parseFloat(monthlyAmount) / parseInt(daysInMonth)).toFixed(2);
      setDailyAllowance(daily);
    } else {
      setDailyAllowance('');
    }
  }, [monthlyAmount, daysInMonth]);

  useEffect(() => {
    if (showStatementModal) {
      fetchStatement();
    }
  }, [showStatementModal, filterYear, filterMonth, filterDay, statementType]);

  const loadParentData = async () => {
    setLoading(true);
    setError('');
    try {
      const [studentsData, alertsData, walletData, profileData] = await Promise.allSettled([
        api.getLinkedStudents(),
        api.getParentAlerts(),
        api.getParentWallet(),
        api.getProfile()
      ]);

      if (studentsData.status === 'fulfilled') {
        setLinkedStudents(studentsData.value.linked_students || []);
      }
      if (alertsData.status === 'fulfilled') {
        let alertsArray = [];
        if (Array.isArray(alertsData.value)) {
          alertsArray = alertsData.value;
        } else if (alertsData.value && alertsData.value.results) {
          alertsArray = alertsData.value.results;
        }
        setAlerts(alertsArray);
      }
      if (walletData.status === 'fulfilled') {
        setParentWallet(walletData.value);
      }
      if (profileData.status === 'fulfilled') {
        setUserProfile(profileData.value);
      }
    } catch (err) {
      setError('Failed to load parent data');
    } finally {
      setLoading(false);
    }
  };

  const fetchStatement = async () => {
    setLoadingStatement(true);
    try {
      let data;
      if (statementType === 'parent') {
        data = await api.getParentStatement(
          filterYear,
          filterMonth,
          filterDay ? parseInt(filterDay) : undefined
        );
      } else if (selectedStudent) {
        data = await api.getStudentStatement(
          selectedStudent.student_id,
          filterYear,
          filterMonth,
          filterDay ? parseInt(filterDay) : undefined
        );
      }
      setStatementData(data?.transactions || []);
    } catch (err) {
      setError('Failed to fetch statement');
    } finally {
      setLoadingStatement(false);
    }
  };

  const handleSelectStudent = async (studentId: number) => {
    setLoading(true);
    setError('');
    setInstituteData(null);
    try {
      const overview = await api.getStudentOverview(studentId);
      setSelectedStudent(overview);
      
      // Fetch Institute Data for this child
      // Since Parent is authenticated, we need to ensure the backend supports this
      // Or we can use the child's token if we have a way, but the better way is parent-level API
      try {
        const instData = await api.request(`/institute/dashboard/?student_id=${studentId}`);
        if (instData && !instData.message) {
          setInstituteData(instData);
        }
      } catch (e) {
        console.log("No institute profile linked for this child");
      }
    } catch (err) {
      setError('Failed to load child overview');
    } finally {
      setLoading(false);
    }
  };

  const handleLinkStudent = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setSuccess('');
    try {
      await api.linkStudent(linkUsername);
      setSuccess('Child linked successfully!');
      setLinkUsername('');
      setShowLinkForm(false);
      loadParentData();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to link child');
    }
  };

  const handleUnlinkStudent = async (studentId: number) => {
    if (!confirm('Are you sure you want to unlink this child?')) return;
    setError('');
    try {
      await api.unlinkStudent(studentId);
      setSuccess('Child unlinked successfully!');
      if (selectedStudent?.student_id === studentId) {
        setSelectedStudent(null);
      }
      loadParentData();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to unlink child');
    }
  };

  const handleDeposit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setSuccess('');
    setDepositing(true);
    try {
      const result = await api.depositToParentWallet(parseFloat(depositAmount), depositDescription);
      setSuccess(`Successfully deposited ₹${depositAmount}!`);
      setDepositAmount('');
      setShowDepositForm(false);
      loadParentData();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to deposit');
    } finally {
      setDepositing(false);
    }
  };

  const handleRecordExpense = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setSuccess('');
    setRecordingExpense(true);
    try {
      await api.recordParentExpense(parseFloat(expenseAmount), expenseCategory, expenseDescription);
      setSuccess('Expense recorded successfully!');
      setExpenseAmount('');
      setExpenseDescription('');
      setShowExpenseModal(false);
      loadParentData();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to record expense');
    } finally {
      setRecordingExpense(false);
    }
  };

  const handleSetAllowance = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedStudent) return;
    setError('');
    setSuccess('');
    try {
      const response = await api.setStudentAllowance(
        selectedStudent.student_id,
        parseFloat(monthlyAmount || '0'),
        parseFloat(dailyAllowance || '0'),
        parseInt(daysInMonth),
        allowanceOtp
      );
      if (response && response.requires_otp) {
        const otpRes = await api.requestOTP('parent_approval', 0, selectedStudent.student_id);
        setAllowanceOtpRequestId(otpRes.otp_request_id);
        setAllowanceGeneratedOtp(otpRes.otp_code);
        setShowAllowanceOtpInput(true);
        setSuccess('OTP required to change daily limit.');
        return;
      }
      setSuccess('Allowance set successfully!');
      setShowAllowanceForm(false);
      setShowAllowanceOtpInput(false);
      setAllowanceOtp('');
      setAllowanceGeneratedOtp(null);
      loadParentData(); // REFRESH PARENT BALANCE
      handleSelectStudent(selectedStudent.student_id);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to set allowance');
    }
  };

  const handleMarkAlertRead = async (alertId: number) => {
    try {
      const alert = alerts.find(a => a.id === alertId);
      
      // If it's an UNLOCK_REQUEST, trigger the OTP generation flow
      if (alert && alert.alert_type === 'UNLOCK_REQUEST') {
        try {
          // Find the lock ID from the message or context if possible
          // For now, let's look for any active lock for this student
          const data = await api.getSpendingLocks();
          const activeLock = data.results?.find((l: any) => l.is_active) || data[0];
          
          if (activeLock) {
            const res = await api.generateSpendingUnlockOTP(activeLock.id);
            setUnlockOtpCode(res.otp_code);
            setUnlockStudentName(activeLock.student_username || 'Student');
            setShowUnlockOtp(true);
          } else {
            setError('No active lock found to generate OTP for.');
          }
        } catch (err) {
          setError('Failed to generate unlock OTP');
        }
      }

      await api.markAlertAsRead(alertId);
      setAlerts(alerts.map(a => a.id === alertId ? { ...a, status: 'READ' } : a));
    } catch (err) { console.error(err); }
  };

  const handleGenerateTransferOtp = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedStudent || !transferAmount) return;
    setError('');
    setSendingOtp(true);
    try {
      const response = await api.generateTransferOTP(selectedStudent.student_id, parseFloat(transferAmount));
      setGeneratedOtp((response as any).otp_code);
      setOtpRequestId((response as any).otp_request_id);
      setOtpGenerated(true);
      setSuccess('OTP generated!');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to generate OTP');
    } finally {
      setSendingOtp(false);
    }
  };

  const handleTransferToStudent = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedStudent || !transferAmount || !transferOtp || !otpRequestId) return;
    setError('');
    setTransferSubmitting(true);
    try {
      await api.verifyParentWalletOTP(transferOtp, otpRequestId);
      setSuccess(`Transferred ₹${transferAmount} successfully!`);
      setOtpGenerated(false);
      setShowTransferForm(false);
      loadParentData();
      handleSelectStudent(selectedStudent.student_id);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Transfer failed');
    } finally {
      setTransferSubmitting(false);
    }
  };

  const handlePayFee = async (paymentId: number) => {
    if (!confirm('Pay tuition fee for this month?')) return;
    try {
      await api.payFeeSelf(paymentId); // Using the same action, backend ensures permissions
      setSuccess('Tuition fee paid successfully!');
      if (selectedStudent) handleSelectStudent(selectedStudent.student_id);
    } catch (err: any) { setError(err.message); }
  };

  const handleLogout = () => { api.clearToken(); navigate('/login'); };
  const handleBack = () => { navigate('/select-module'); };

  if (loading) return <div className="loading">Loading Parent Dashboard...</div>;

  return (
    <div className="dashboard-container">
      <header className="dashboard-header">
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <button onClick={handleBack} className="back-btn">← Back</button>
          <button onClick={() => setShowNotifications(!showNotifications)} style={{ position: 'relative', background: 'transparent', border: 'none', fontSize: '1.3rem', cursor: 'pointer' }}>
            🔔 {alerts.filter(a => a.status !== 'READ').length > 0 && <span className="notification-badge">{alerts.filter(a => a.status !== 'READ').length}</span>}
          </button>
        </div>
        <h1>Parent Dashboard 👨‍👩‍👧 {userProfile?.uid && <span style={{ fontSize: '0.9rem', color: '#764ba2', background: 'white', padding: '2px 8px', borderRadius: '4px', marginLeft: '10px', verticalAlign: 'middle' }}>{userProfile.uid}</span>}</h1>
        <button onClick={handleLogout} className="logout-btn">Logout</button>
      </header>

      {showNotifications && (
        <div className="notifications-panel">
          <div className="panel-header">
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <h3>Alerts & OTPs</h3>
              <button onClick={loadParentData} className="refresh-btn-small" style={{ background: 'none', border: 'none', color: '#764ba2', cursor: 'pointer', fontSize: '0.9rem' }}>🔄 Refresh</button>
            </div>
            <button onClick={() => setShowNotifications(false)}>✕</button>
          </div>
          <div className="panel-content">
            {alerts.length === 0 ? <p>No alerts</p> : alerts.map(alert => (
              <div key={alert.id} className={`alert-item ${alert.status === 'READ' ? 'read' : 'unread'}`} onClick={() => handleMarkAlertRead(alert.id)}>
                <div className="alert-type">{alert.alert_type}</div>
                <div className="alert-msg">{alert.message}</div>
              </div>
            ))}
          </div>
        </div>
      )}

      <main className="dashboard-main">
        {error && <div className="error-message">{error}</div>}
        {success && <div className="success-message">{success}</div>}

        <div className="balance-card">
          <h2>💰 My Wallet</h2>
          <div className="info-value">₹{parentWallet?.balance ? parseFloat(String(parentWallet.balance)).toFixed(2) : '0.00'}</div>
          <div className="button-group-grid">
            <button onClick={() => setShowDepositForm(true)} className="submit-btn">💳 Add Funds</button>
            <button onClick={() => setShowExpenseModal(true)} className="submit-btn" style={{ background: '#e67e22' }}>📝 Record Expense</button>
            <button onClick={() => { setStatementType('parent'); setShowStatementModal(true); }} className="submit-btn" style={{ background: '#764ba2' }}>📄 My Statement</button>
          </div>
        </div>

        <div className="balance-card">
          <h2>Linked Children</h2>
          <div className="info-cards">
            {linkedStudents.map(s => (
              <div key={s.id} className={`info-card ${selectedStudent?.student_id === s.id ? 'selected' : ''}`} onClick={() => handleSelectStudent(s.id)}>
                <h3>{s.username}</h3>
                <div className="info-value">₹{parseFloat(String(s.wallet_balance)).toFixed(2)}</div>
                <button onClick={(e) => { e.stopPropagation(); handleUnlinkStudent(s.id); }} className="cancel-btn-small">Unlink</button>
              </div>
            ))}
            <button className="info-card add-card" onClick={() => setShowLinkForm(true)}>+</button>
          </div>
        </div>

        {selectedStudent && (
          <>
            <div className="balance-card">
              <h2>Overview: {linkedStudents.find(s => s.id === selectedStudent.student_id)?.username}</h2>
              <div className="info-cards">
                <div className="info-card"><h3>Wallet</h3><div className="info-value">₹{parseFloat(String(selectedStudent.wallet_balance)).toFixed(2)}</div></div>
                <div className="info-card"><h3>Spent Today</h3><div className="info-value">₹{parseFloat(String(selectedStudent.current_daily_spent)).toFixed(2)}</div></div>
              </div>
              <div className="button-group-grid" style={{ marginTop: '1.5rem' }}>
                <button onClick={() => { setShowAllowanceForm(true); setMonthlyAmount(''); setDailyAllowance(''); setShowAllowanceOtpInput(false); }} className="submit-btn">Set Allowance</button>
                <button onClick={() => setShowTransferForm(true)} className="submit-btn" style={{ background: '#2ecc71' }}>💰 Transfer</button>
                <button onClick={() => { setStatementType('student'); setShowStatementModal(true); }} className="submit-btn" style={{ background: '#764ba2' }}>📄 Statement</button>
              </div>
            </div>

            {/* NEW: Academic Portal Section for Parents */}
            {instituteData && (
              <div className="balance-card" style={{ borderTop: '4px solid #3498db' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
                  <h2 style={{ margin: 0 }}>Academic Portal 🏫</h2>
                  <span style={{ padding: '4px 12px', borderRadius: '20px', background: 'rgba(52, 152, 219, 0.1)', color: '#3498db', fontSize: '0.9rem', fontWeight: 'bold' }}>{instituteData.institute_name}</span>
                </div>
                
                <div className="info-cards">
                  <div className="info-card">
                    <h3>Tuition Fee</h3>
                    <div className="info-value">₹{parseFloat(instituteData.profile.monthly_fee).toFixed(2)}</div>
                    <div className="info-sub">Due on {instituteData.profile.due_day}th</div>
                  </div>
                  <div className="info-card" style={{ borderLeft: `5px solid ${instituteData.current_fee_status.status === 'PAID' ? '#2ecc71' : '#e74c3c'}` }}>
                    <h3>Status: {instituteData.current_fee_status.status}</h3>
                    <div className="info-value" style={{ color: instituteData.current_fee_status.status === 'PAID' ? '#2ecc71' : '#e74c3c' }}>
                      {instituteData.current_fee_status.status === 'PAID' ? '✅ Paid' : `₹${parseFloat(instituteData.current_fee_status.pending_amount || instituteData.current_fee_status.amount).toFixed(2)} Due`}
                    </div>
                    {instituteData.current_fee_status.status !== 'PAID' && (
                      <button onClick={() => handlePayFee(instituteData.current_fee_status.id)} className="submit-btn" style={{ background: '#2ecc71', width: 'auto', padding: '0.4rem 1rem', fontSize: '0.85rem', marginTop: '5px' }}>💳 Pay Now</button>
                    )}
                  </div>
                  <div className="info-card">
                    <h3>Attendance</h3>
                    <div className="info-value" style={{ color: instituteData.attendance.percentage >= 75 ? '#2ecc71' : '#e74c3c' }}>{instituteData.attendance.percentage}%</div>
                    <div className="info-sub">Overall Progress</div>
                  </div>
                </div>

                <div className="dashboard-grid" style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: '1.5rem', marginTop: '2rem' }}>
                  <div className="info-card">
                    <h3>🔔 Recent Institute Alerts</h3>
                    <div style={{ marginTop: '1rem', maxHeight: '200px', overflowY: 'auto' }}>
                      {instituteData.notifications.length === 0 ? <p style={{ opacity: 0.5 }}>No alerts</p> : instituteData.notifications.map((n: any) => (
                        <div key={n.id} style={{ padding: '8px 0', borderBottom: '1px solid #eee', fontSize: '0.8rem' }}>
                          <strong>{n.notification_type.replace('_', ' ')}</strong>: {n.message}
                        </div>
                      ))}
                    </div>
                  </div>
                  <div className="info-card">
                    <h3>📅 Attendance History</h3>
                    <div style={{ marginTop: '1rem' }}>
                      {instituteData.attendance.recent.slice(0, 5).map((a: any) => (
                        <div key={a.id} style={{ display: 'flex', justifyContent: 'space-between', padding: '6px 0', borderBottom: '1px solid #f9f9f9', fontSize: '0.85rem' }}>
                          <span>{new Date(a.date).toLocaleDateString()}</span>
                          <span style={{ fontWeight: 'bold', color: a.status === 'PRESENT' ? '#2ecc71' : '#e74c3c' }}>{a.status}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            )}
          </>
        )}
      </main>

      {/* Statement Modal */}
      {showStatementModal && (
        <div className="modal-overlay" onClick={() => setShowStatementModal(false)}>
          <div className="modal wide-modal" onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <h2>{statementType === 'parent' ? 'My Statement 📜' : 'Child Statement 📜'}</h2>
              <button onClick={() => setShowStatementModal(false)}>✕</button>
            </div>
            <div className="filters-row">
              <select value={filterYear} onChange={e => setYear(parseInt(e.target.value))}>{[2024, 2025, 2026].map(y => <option key={y} value={y}>{y}</option>)}</select>
              <select value={filterMonth} onChange={e => setMonth(parseInt(e.target.value))}>{['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'].map((m, i) => <option key={m} value={i+1}>{m}</option>)}</select>
              <input type="number" placeholder="DD" value={filterDay} onChange={e => setDay(e.target.value)} min="1" max="31" />
            </div>
            <div className="table-container">
              {loadingStatement ? <p>Loading...</p> : (
                <table className="statement-table">
                  <thead><tr><th>Date</th><th>Description</th><th>Type</th><th style={{textAlign:'right'}}>Amount</th></tr></thead>
                  <tbody>
                    {statementData.map(tx => (
                      <tr key={tx.id}>
                        <td>{new Date(tx.created_at).toLocaleDateString()}</td>
                        <td>{tx.description}</td>
                        <td><span className={`tag ${tx.transaction_type}`}>{tx.transaction_type}</span></td>
                        <td style={{textAlign:'right', fontWeight:'bold'}}>₹{parseFloat(tx.amount).toFixed(2)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>
            <div className="modal-footer"><button onClick={() => window.print()} className="print-btn">🖨️ Print</button></div>
          </div>
        </div>
      )}

      {/* Allowance Modal */}
      {showAllowanceForm && (
        <div className="modal-overlay" onClick={() => setShowAllowanceForm(false)}>
          <div className="modal" onClick={e => e.stopPropagation()}>
            <h2>Set Child Allowance 💰</h2>
            <form onSubmit={handleSetAllowance}>
              {!showAllowanceOtpInput ? (
                <>
                  <div className="form-group">
                    <label>Monthly Amount (₹)</label>
                    <input type="number" value={monthlyAmount} onChange={e => setMonthlyAmount(e.target.value)} required min="1" />
                  </div>
                  <div className="form-group">
                    <label>Days in Month</label>
                    <input type="number" value={daysInMonth} onChange={e => setDaysInMonth(e.target.value)} required min="1" max="31" />
                  </div>
                  <div className="form-group">
                    <label>Daily Limit (Calculated: ₹{dailyAllowance})</label>
                    <input type="number" value={dailyAllowance} onChange={e => setDailyAllowance(e.target.value)} required step="0.01" />
                  </div>
                  <button type="submit" className="submit-btn">Update Allowance</button>
                </>
              ) : (
                <>
                  <div className="otp-display">{allowanceGeneratedOtp}</div>
                  <div className="form-group">
                    <label>Enter Verification OTP</label>
                    <input type="text" value={allowanceOtp} onChange={e => setAllowanceOtp(e.target.value)} required maxLength={6} />
                  </div>
                  <button type="submit" className="submit-btn">Confirm Daily Limit Change</button>
                </>
              )}
              <button type="button" onClick={() => setShowAllowanceForm(false)} className="cancel-btn">Cancel</button>
            </form>
          </div>
        </div>
      )}

      {/* Parent Expense Modal */}
      {showExpenseModal && (
        <div className="modal-overlay" onClick={() => setShowExpenseModal(false)}>
          <div className="modal" onClick={e => e.stopPropagation()}>
            <h2>Record My Expense 📝</h2>
            <form onSubmit={handleRecordExpense}>
              <div className="form-group"><label>Amount (₹)</label><input type="number" value={expenseAmount} onChange={e => setExpenseAmount(e.target.value)} required min="1" /></div>
              <div className="form-group">
                <label>Category</label>
                <select value={expenseCategory} onChange={e => setExpenseCategory(e.target.value)}>
                  {EXPENSE_CATEGORIES.map(c => <option key={c.value} value={c.value}>{c.icon} {c.label}</option>)}
                </select>
              </div>
              <div className="form-group"><label>Description</label><input type="text" value={expenseDescription} onChange={e => setExpenseDescription(e.target.value)} placeholder="e.g. Lunch, Groceries" /></div>
              <button type="submit" className="submit-btn" disabled={recordingExpense}>{recordingExpense ? 'Recording...' : 'Record Expense'}</button>
              <button type="button" onClick={() => setShowExpenseModal(false)} className="cancel-btn">Cancel</button>
            </form>
          </div>
        </div>
      )}

      {/* Deposit Modal */}
      {showDepositForm && (
        <div className="modal-overlay" onClick={() => setShowDepositForm(false)}>
          <div className="modal" onClick={e => e.stopPropagation()}>
            <h2>Add Funds 💳</h2>
            <form onSubmit={handleDeposit}>
              <div className="form-group"><label>Amount (₹)</label><input type="number" value={depositAmount} onChange={e => setDepositAmount(e.target.value)} required min="1" /></div>
              <button type="submit" className="submit-btn" disabled={depositing}>Deposit</button>
              <button type="button" onClick={() => setShowDepositForm(false)} className="cancel-btn">Cancel</button>
            </form>
          </div>
        </div>
      )}

      {/* Transfer Modal */}
      {showTransferForm && (
        <div className="modal-overlay" onClick={() => setShowTransferForm(false)}>
          <div className="modal" onClick={e => e.stopPropagation()}>
            <h2>Transfer to Child 💰</h2>
            {!otpGenerated ? (
              <form onSubmit={handleGenerateTransferOtp}>
                <div className="form-group"><label>Amount (₹)</label><input type="number" value={transferAmount} onChange={e => setTransferAmount(e.target.value)} required min="1" /></div>
                <button type="submit" className="submit-btn" disabled={sendingOtp}>Generate OTP</button>
              </form>
            ) : (
              <form onSubmit={handleTransferToStudent}>
                <div className="otp-display">{generatedOtp}</div>
                <div className="form-group"><label>Enter OTP</label><input type="text" value={transferOtp} onChange={e => setTransferOtp(e.target.value)} required maxLength={6} /></div>
                <button type="submit" className="submit-btn" disabled={transferSubmitting}>Complete Transfer</button>
              </form>
            )}
            <button onClick={() => setShowTransferForm(false)} className="cancel-btn">Cancel</button>
          </div>
        </div>
      )}

      {/* Link Modal */}
      {showLinkForm && (
        <div className="modal-overlay" onClick={() => setShowLinkForm(false)}>
          <div className="modal" onClick={e => e.stopPropagation()}>
            <h2>Link Child ➕</h2>
            <form onSubmit={handleLinkStudent}>
              <div className="form-group"><input type="text" value={linkUsername} onChange={e => setLinkUsername(e.target.value)} required placeholder="Child's Username" /></div>
              <button type="submit" className="submit-btn">Link</button>
              <button type="button" onClick={() => setShowLinkForm(false)} className="cancel-btn">Cancel</button>
            </form>
          </div>
        </div>
      )}

      {/* Unlock OTP Modal */}
      {showUnlockOtp && (
        <div className="modal-overlay" onClick={() => setShowUnlockOtp(false)}>
          <div className="modal" style={{ textAlign: 'center' }} onClick={e => e.stopPropagation()}>
            <h2>🔑 Unlock OTP</h2>
            <p>Share this with {unlockStudentName}:</p>
            <div className="otp-display-large">{unlockOtpCode}</div>
            <button onClick={() => setShowUnlockOtp(false)} className="submit-btn">Close</button>
          </div>
        </div>
      )}
    </div>
  );
}
