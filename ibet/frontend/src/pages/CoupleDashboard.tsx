import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../services/api';
import {
  PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, AreaChart, Area
} from 'recharts';
import './Dashboard.css';

interface CoupleWalletData {
  balance: number;
  monthly_budget: number;
  emergency_fund: number;
  joint_goals: number;
  available_balance: number;
  partner1: string;
  partner2: string;
}

interface MonthlySummary {
  month_name: string;
  total_deposits: number;
  total_withdrawals: number;
  total_transfers: number;
  monthly_budget: number;
  category_breakdown: Array<{ category: string; withdrawn_by: string; total: number }>;
  spending_trend: Array<{ day: string; total: number }>;
  metrics: {
    savings_rate: number;
    p1_ratio: number;
    p2_ratio: number;
    health_score: number;
  };
}

interface PersonalWalletData {
  balance: number;
  is_visible_to_partner: boolean;
}

interface JointGoal {
  id: number;
  name: string;
  target_amount: number;
  current_amount: number;
  deadline: string;
  progress_percentage: number;
}

interface SpendingRequest {
  id: number;
  requester: string;
  amount: number;
  description: string;
  category: string;
  status: string;
  requested_at: string;
}

interface SettlementData {
  partner1_contributed: number;
  partner2_contributed: number;
  total_shared_expenses: number;
  ideal_share: number;
  imbalance: number;
  owes_to: string | null;
  amount_owed: number;
}

const JOINT_CATEGORIES = [
  { value: 'RENT', label: 'Rent', icon: '🏠' },
  { value: 'GROCERIES', label: 'Groceries', icon: '🛒' },
  { value: 'ELECTRICITY', label: 'Electricity', icon: '⚡' },
  { value: 'INTERNET', label: 'Internet', icon: '🌐' },
  { value: 'TRAVEL', label: 'Travel', icon: '✈️' },
  { value: 'EMI', label: 'EMI', icon: '💳' },
  { value: 'HOUSEHOLD', label: 'Household', icon: '🧹' },
  { value: 'OTHER', label: 'Other', icon: '📦' },
];

const COLORS = ['#667eea', '#764ba2', '#e74c3c', '#2ecc71', '#f1c40f', '#9b59b6', '#34495e', '#1abc9c'];

export default function CoupleDashboard() {
  const navigate = useNavigate();
  const [currentUser, setCurrentUser] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [activeTab, setActiveTab] = useState<'joint' | 'personal' | 'goals' | 'approvals' | 'settlement'>('joint');

  // State for data
  const [jointWallet, setJointWallet] = useState<CoupleWalletData | null>(null);
  const [userProfile, setUserProfile] = useState<any>(null);
  const [monthlySummary, setMonthlySummary] = useState<MonthlySummary | null>(null);
  const [transactions, setTransactions] = useState<any[]>([]);
  const [personalWallet, setPersonalWallet] = useState<PersonalWalletData | null>(null);
  const [personalTransactions, setPersonalTransactions] = useState<any[]>([]);
  const [goals, setGoals] = useState<JointGoal[]>([]);
  const [requests, setRequests] = useState<SpendingRequest[]>([]);
  const [settlement, setSettlement] = useState<SettlementData | null>(null);

  // Forms
  const [showDepositForm, setShowDepositForm] = useState(false);
  const [depositAmount, setDepositAmount] = useState('');
  const [showWithdrawForm, setShowWithdrawForm] = useState(false);
  const [withdrawAmount, setWithdrawAmount] = useState('');
  const [withdrawDescription, setWithdrawDescription] = useState('');
  const [withdrawCategory, setWithdrawCategory] = useState('OTHER');
  
  const [showRequestForm, setShowRequestForm] = useState(false);
  const [requestAmount, setRequestAmount] = useState('');
  const [requestDescription, setRequestDescription] = useState('');
  const [requestCategory, setRequestCategory] = useState('OTHER');

  const [showGoalForm, setShowGoalForm] = useState(false);
  const [showEditGoalForm, setShowEditGoalForm] = useState(false);
  const [selectedGoalId, setSelectedGoalId] = useState<number | null>(null);
  const [goalName, setGoalName] = useState('');
  const [goalTarget, setGoalTarget] = useState('');
  const [goalDeadline, setGoalDeadline] = useState('');

  // Private wallet forms
  const [showPersonalDepositForm, setShowPersonalDepositForm] = useState(false);
  const [showPersonalWithdrawForm, setShowPersonalWithdrawForm] = useState(false);
  const [personalAmount, setPersonalAmount] = useState('');

  // Budget state
  const [showBudgetForm, setShowBudgetForm] = useState(false);
  const [newBudget, setNewBudget] = useState('');

  // Settlement search state
  const [settlementSearch, setSettlementSearch] = useState('');
  const [settlementCategoryFilter, setSettlementCategoryFilter] = useState('ALL');

  // Linking state
  const [partnerUsername, setPartnerUsername] = useState('');
  const [linking, setLinking] = useState(false);

  const downloadSettlementCSV = () => {
    if (!settlement || !(settlement as any).history) return;
    
    const history = (settlement as any).history;
    const headers = ['Date', 'Partner', 'Type', 'Category', 'Description', 'Amount'];
    const rows = history.map((tx: any) => [
      new Date(tx.date).toLocaleDateString(),
      tx.user,
      tx.type,
      tx.category,
      tx.description.replace(/,/g, ' '),
      tx.amount
    ]);

    const csvContent = [
      headers.join(','),
      ...rows.map((r: any) => r.join(','))
    ].join('\n');

    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.setAttribute('href', url);
    link.setAttribute('download', `joint_spending_${new Date().toISOString().split('T')[0]}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  useEffect(() => {
    // FORCE fetch profile on mount to ensure we have the correct user for THIS token
    api.getProfile().then(profile => {
      setCurrentUser(profile.username);
      localStorage.setItem('user', JSON.stringify(profile));
    }).catch(err => {
      console.error('Session invalid:', err);
      api.clearToken();
      navigate('/login');
    });
  }, [navigate]);

  useEffect(() => {
    loadDashboardData();
  }, [activeTab]);

  const loadDashboardData = async () => {
    setLoading(true);
    setError('');
    try {
      // Always fetch profile to ensure UID is available
      const profile = await api.getProfile();
      setUserProfile(profile);

      if (activeTab === 'joint') {
        const [walletData, summaryData, historyData] = await Promise.all([
          api.getCoupleWallet().catch(() => null),
          api.getCoupleSpendingStats().catch(() => null),
          api.getCoupleTransactions().catch(() => [])
        ]);
        if (walletData) setJointWallet(walletData);
        if (summaryData) setMonthlySummary(summaryData);
        const txList = Array.isArray(historyData) ? historyData : (historyData as any)?.results || [];
        setTransactions(txList);
      } else if (activeTab === 'personal') {
        const [personalData, personalHistory] = await Promise.all([
          api.getCouplePersonalWallet().catch(() => null),
          api.getCouplePersonalTransactions().catch(() => [])
        ]);
        setPersonalWallet(personalData);
        setPersonalTransactions(personalHistory || []);
      } else if (activeTab === 'goals') {
        const goalsData = await api.getJointGoals();
        setGoals(goalsData);
      } else if (activeTab === 'approvals') {
        const requestsData = await api.getSpendingRequests();
        setRequests(requestsData);
      } else if (activeTab === 'settlement') {
        const settlementData = await api.getCoupleSettlement();
        setSettlement(settlementData);
      }
    } catch (err) {
      console.error(err);
      setError('Failed to load data.');
    } finally {
      setLoading(false);
    }
  };

  const handleLinkPartner = async (e: React.FormEvent) => {
    e.preventDefault();
    setLinking(true);
    setError('');
    try {
      await api.request('/couple/create-couple/', {
        method: 'POST',
        body: JSON.stringify({ partner_username: partnerUsername })
      });
      setSuccess('Partner linked successfully!');
      setTimeout(() => window.location.reload(), 1500);
    } catch (err: any) {
      setError(err.message || 'Failed to link partner.');
    } finally {
      setLinking(false);
    }
  };

  const handleUnlinkPartner = async () => {
    if (!window.confirm('Are you sure you want to unlink?')) return;
    try {
      await api.request('/couple/unlink-couple/', { method: 'POST' });
      window.location.reload();
    } catch (err) {
      setError('Failed to unlink partner.');
    }
  };

  const handleDeposit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await api.depositToCoupleWallet(parseFloat(depositAmount));
      setSuccess('Deposited successfully!');
      setShowDepositForm(false);
      setDepositAmount('');
      loadDashboardData();
    } catch (err: any) {
      setError(err.message || 'Deposit failed');
    }
  };

  const handleWithdraw = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const amount = parseFloat(withdrawAmount);
      if (amount > 10000) {
        await api.createSpendingRequest(amount, withdrawDescription, withdrawCategory);
        setSuccess('Amount exceeds ₹10,000. Approval request sent!');
      } else {
        await api.withdrawFromCoupleWallet(amount, withdrawDescription, withdrawCategory);
        setSuccess('Withdrawn successfully!');
      }
      setShowWithdrawForm(false);
      setWithdrawAmount(''); setWithdrawDescription('');
      loadDashboardData();
    } catch (err: any) {
      setError(err.message || 'Withdrawal failed');
    }
  };

  const handleSetBudget = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await api.setCoupleBudget(parseFloat(newBudget));
      setSuccess('Monthly budget updated!');
      setShowBudgetForm(false);
      setNewBudget('');
      loadDashboardData();
    } catch (err: any) {
      setError(err.message || 'Failed to update budget');
    }
  };

  const handlePersonalAction = async (e: React.FormEvent, action: 'deposit' | 'withdraw') => {
    e.preventDefault();
    try {
      if (action === 'deposit') {
        await api.depositToPersonalWallet(parseFloat(personalAmount));
      } else {
        await api.withdrawFromPersonalWallet(parseFloat(personalAmount));
      }
      setSuccess(`Personal wallet ${action} successful!`);
      setPersonalAmount('');
      setShowPersonalDepositForm(false);
      setShowPersonalWithdrawForm(false);
      loadDashboardData();
    } catch (err: any) {
      setError(err.message || 'Action failed');
    }
  };

  const handleUpdateGoal = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedGoalId) return;
    try {
      await api.updateJointGoal(selectedGoalId, {
        name: goalName,
        target_amount: parseFloat(goalTarget),
        deadline: goalDeadline
      });
      setSuccess('Goal updated successfully!');
      setShowEditGoalForm(false);
      loadDashboardData();
    } catch (err: any) {
      setError(err.message || 'Failed to update goal');
    }
  };

  const handleCreateGoal = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await api.createJointGoal(goalName, parseFloat(goalTarget), goalDeadline);
      setSuccess('Goal created successfully!');
      setShowGoalForm(false);
      setGoalName(''); setGoalTarget(''); setGoalDeadline('');
      loadDashboardData();
    } catch (err: any) {
      setError(err.message || 'Failed to create goal');
    }
  };

  const handleContributeToGoal = async (id: number, amount: number) => {
    try {
      await api.contributeToJointGoal(id, amount);
      setSuccess('Contributed successfully!');
      loadDashboardData();
    } catch (err: any) {
      setError(err.message || 'Failed to contribute');
    }
  };

  const handleCreateRequest = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await api.createSpendingRequest(parseFloat(requestAmount), requestDescription, requestCategory);
      setSuccess('Approval request sent!');
      setShowRequestForm(false);
      setRequestAmount(''); setRequestDescription('');
      loadDashboardData();
    } catch (err: any) {
      setError(err.message || 'Request failed');
    }
  };

  const handleRespondRequest = async (id: number, action: 'approve' | 'reject') => {
    try {
      await api.respondToSpendingRequest(id, action);
      setSuccess(`Request ${action}d successfully!`);
      loadDashboardData();
    } catch (err: any) {
      setError(err.message || `Failed to ${action} request`);
    }
  };

  const handleLogout = () => { api.clearToken(); navigate('/login'); };

  if (loading && !jointWallet && !monthlySummary) return <div className="loading">Loading...</div>;

  if (!jointWallet) {
    return (
      <div className="dashboard-container">
        <header className="dashboard-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '1rem 2rem' }}>
          <button onClick={() => navigate('/select-module')} className="back-btn">← Back</button>
          <h1 style={{ margin: 0 }}>Link Your Partner 💑</h1>
          <button onClick={handleLogout} className="logout-btn">Logout</button>
        </header>
        <main className="dashboard-main">
          <div className="balance-card">
            <h2>Start Your Shared Journey</h2>
            <p style={{ color: '#666', marginBottom: '2rem' }}>Enter your partner's username below to link accounts.</p>
            {error && <div className="error-message">{error}</div>}
            {success && <div className="success-message">{success}</div>}
            <form onSubmit={handleLinkPartner} style={{ maxWidth: '400px', margin: '0 auto' }}>
              <div className="form-group"><label>Partner's Username</label><input type="text" value={partnerUsername} onChange={e => setPartnerUsername(e.target.value)} placeholder="e.g. keerthana" required /></div>
              <button type="submit" className="submit-btn" disabled={linking}>{linking ? 'Linking...' : 'Link Partner'}</button>
            </form>
          </div>
        </main>
      </div>
    );
  }

  return (
    <div className="dashboard-container">
      <header className="dashboard-header" style={{ 
        display: 'grid', 
        gridTemplateColumns: '1.2fr 1fr 1.2fr', 
        alignItems: 'center', 
        padding: '1rem 2rem',
        background: 'rgba(0,0,0,0.25)',
        backdropFilter: 'blur(15px)',
        borderBottom: '1px solid rgba(255,255,255,0.1)',
        position: 'sticky',
        top: 0,
        zIndex: 100,
        gap: '20px'
      }}>
        {/* Left Side: Navigation & User Badge */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <button onClick={() => navigate('/select-module')} className="back-btn" style={{ padding: '8px 16px', margin: 0 }}>← Back</button>
          <button onClick={handleUnlinkPartner} className="back-btn" style={{ 
            background: 'rgba(231, 76, 60, 0.2)', 
            borderColor: '#e74c3c', 
            color: '#fff',
            padding: '8px 16px',
            margin: 0
          }}>Unlink</button>
          <div className="user-profile-badge" style={{ 
            background: 'rgba(255,255,255,0.1)', 
            padding: '6px 15px', 
            borderRadius: '25px',
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            fontSize: '0.9rem',
            border: '1px solid rgba(255,255,255,0.2)',
            marginLeft: '5px'
          }}>
            <span>👤</span>
            <strong style={{ color: '#fff', textTransform: 'capitalize' }}>{currentUser || 'User'}</strong>
            {userProfile?.uid && <span style={{ fontSize: '0.75rem', background: '#fff', color: '#667eea', padding: '1px 6px', borderRadius: '4px', fontWeight: 'bold' }}>{userProfile.uid}</span>}
          </div>
        </div>
        <h1 style={{ fontSize: '1.5rem', margin: 0, textAlign: 'center', color: '#fff', fontWeight: 'bold' }}>Couple Dashboard</h1>
        <div style={{ display: 'flex', justifyContent: 'flex-end', paddingRight: '10px' }}>
          <button onClick={handleLogout} className="logout-btn" style={{ padding: '8px 20px', margin: 0, background: 'rgba(255,255,255,0.15)', border: '1px solid rgba(255,255,255,0.4)', borderRadius: '8px', color: '#fff', cursor: 'pointer', fontWeight: '600' }}>Logout</button>
        </div>
      </header>

      <div className="tab-navigation" style={{ display: 'flex', gap: '1rem', padding: '0 2rem', marginBottom: '1rem', overflowX: 'auto' }}>
        <button className={`tab-btn ${activeTab === 'joint' ? 'active' : ''}`} onClick={() => setActiveTab('joint')}>Joint Wallet</button>
        <button className={`tab-btn ${activeTab === 'personal' ? 'active' : ''}`} onClick={() => setActiveTab('personal')}>Personal Wallet</button>
        <button className={`tab-btn ${activeTab === 'goals' ? 'active' : ''}`} onClick={() => setActiveTab('goals')}>Goals</button>
        <button className={`tab-btn ${activeTab === 'approvals' ? 'active' : ''}`} onClick={() => setActiveTab('approvals')}>Approvals</button>
        <button className={`tab-btn ${activeTab === 'settlement' ? 'active' : ''}`} onClick={() => setActiveTab('settlement')}>Settlement</button>
      </div>

      <main className="dashboard-main">
        {error && <div className="error-message">{error}</div>}
        {success && <div className="success-message">{success}</div>}

        {activeTab === 'joint' && (
          <div className="joint-wallet-layout">
            <div className="dashboard-grid">
              <div className="balance-card">
                <h2>Shared Joint Wallet</h2>
                <div className="info-value" style={{ color: '#2ecc71', fontSize: '3rem' }}>₹{jointWallet.balance}</div>
                <p style={{ color: '#666', marginBottom: '1.5rem' }}>Partners: <strong>{jointWallet.partner1}</strong> & <strong>{jointWallet.partner2}</strong></p>
                <div className="button-group-grid">
                  <button onClick={() => setShowDepositForm(true)} className="submit-btn">💳 Contribute</button>
                  <button onClick={() => setShowWithdrawForm(true)} className="submit-btn" style={{ background: '#e67e22' }}>💸 Shared Expense</button>
                </div>
              </div>
              <div className="info-card">
                <h3>📅 Monthly Budget</h3>
                <div className="info-value" style={{ fontSize: '2rem', margin: '0.5rem 0' }}>₹{jointWallet.monthly_budget}</div>
                <button onClick={() => setShowBudgetForm(true)} className="submit-btn" style={{ background: '#34495e', marginTop: '1rem', width: 'auto', padding: '0.5rem 1rem' }}>⚙️ Set New Budget</button>
              </div>
              <div className="info-card metrics-card">
                <h3>Financial Health</h3>
                <div className="health-score"><div className="score-value">{monthlySummary?.metrics?.health_score || 0}</div><div className="score-label">Health Score</div></div>
                <div className="metrics-grid">
                  <div className="metric"><span className="metric-label">Savings Rate</span><span className="metric-value">{monthlySummary?.metrics?.savings_rate || 0}%</span></div>
                  <div className="metric"><span className="metric-label">Budget Used</span><span className="metric-value">{((monthlySummary?.total_withdrawals || 0) / (monthlySummary?.monthly_budget || 1) * 100).toFixed(1)}%</span></div>
                </div>
              </div>
            </div>

            <div className="charts-container" style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(350px, 1fr))', gap: '1.5rem', marginTop: '2rem' }}>
              <div className="info-card" style={{ minWidth: 0, minHeight: 0 }}>
                <h3>Spending Trend</h3>
                <div style={{ width: '100%', height: '250px', minWidth: 0, minHeight: 0 }}>
                  <ResponsiveContainer width="99%" height={250}>
                    <AreaChart data={monthlySummary?.spending_trend || []}>
                      <defs>
                        <linearGradient id="colorCoupleTrend" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%" stopColor="#667eea" stopOpacity={0.8}/>
                          <stop offset="95%" stopColor="#667eea" stopOpacity={0}/>
                        </linearGradient>
                      </defs>
                      <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#eee" />
                      <XAxis 
                        dataKey="day" 
                        axisLine={false} 
                        tickLine={false} 
                        tick={{fontSize: 10, fill: '#999'}} 
                        label={{ value: 'Day of Month', position: 'insideBottom', offset: -5, fontSize: 12 }}
                      />
                      <YAxis 
                        axisLine={false} 
                        tickLine={false} 
                        tick={{fontSize: 10, fill: '#999'}}
                        tickFormatter={(val) => `₹${val}`}
                        domain={[0, 'auto']}
                      />
                      <Tooltip 
                        content={({ active, payload }) => {
                          if (active && payload && payload.length) {
                            const data = payload[0].payload;
                            return (
                              <div style={{ background: 'white', padding: '10px', border: '1px solid #ccc', borderRadius: '8px', boxShadow: '0 4px 12px rgba(0,0,0,0.1)' }}>
                                <p style={{ margin: 0, fontWeight: 'bold', color: '#667eea' }}>Day {data.day}</p>
                                <p style={{ margin: '4px 0', fontSize: '1.1rem', fontWeight: 'bold' }}>₹{data.total}</p>
                                <p style={{ margin: 0, color: '#999', fontSize: '0.75rem' }}>{data.full_date}</p>
                              </div>
                            );
                          }
                          return null;
                        }}
                      />
                      <Area 
                        type="monotone" 
                        dataKey="total" 
                        stroke="#667eea" 
                        fill="url(#colorCoupleTrend)" 
                        fillOpacity={1} 
                        dot={{ r: 4, fill: '#667eea' }}
                        activeDot={{ r: 6 }}
                      />
                    </AreaChart>
                  </ResponsiveContainer>
                </div>
              </div>
              <div className="info-card" style={{ minWidth: 0, minHeight: 0 }}>
                <h3>Expenses by Category</h3>
                <div style={{ width: '100%', height: '250px', minWidth: 0, minHeight: 0 }}>
                  <ResponsiveContainer width="99%" height={250}>
                    <PieChart>
                      <Pie data={monthlySummary?.category_breakdown || []} innerRadius={60} outerRadius={80} paddingAngle={5} dataKey="total" nameKey="category" label={({ category, withdrawn_by, total }) => `${category} (${withdrawn_by}): ₹${total}`}>
                        {(monthlySummary?.category_breakdown || []).map((_entry, index) => (<Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />))}
                      </Pie>
                      <Tooltip content={({ active, payload }) => {
                        if (active && payload && payload.length) {
                          const data = payload[0].payload;
                          return (<div style={{ background: 'white', padding: '10px', border: '1px solid #ccc', borderRadius: '8px' }}><p style={{ margin: 0, fontWeight: 'bold' }}>{data.category}</p><p style={{ margin: '4px 0', color: '#666' }}>Spent by: {data.withdrawn_by}</p><p style={{ margin: 0, color: '#2ecc71', fontWeight: 'bold' }}>₹{data.total}</p></div>);
                        }
                        return null;
                      }} /><Legend />
                    </PieChart>
                  </ResponsiveContainer>
                </div>
              </div>
            </div>

            <div className="info-card" style={{ marginTop: '2rem' }}>
              <h3>📜 Recent Shared Transactions</h3>
              <div className="table-container" style={{ marginTop: '1rem' }}>
                {transactions.length === 0 ? <p style={{ color: '#999', textAlign: 'center', padding: '2rem' }}>No shared transactions.</p> : (
                  <table className="statement-table">
                    <thead><tr><th>Date</th><th>User</th><th>Type</th><th>Category</th><th>Description</th><th style={{ textAlign: 'right' }}>Amount</th></tr></thead>
                    <tbody>
                      {transactions.slice(0, 15).map((tx) => {
                        const actor = tx.transaction_type === 'DEPOSIT' ? tx.deposited_by_username : tx.withdrawn_by_username;
                        return (
                          <tr key={tx.id}>
                            <td>{new Date(tx.created_at).toLocaleDateString()}</td>
                            <td><strong>{actor || 'System'}</strong></td>
                            <td><span className={`tag ${tx.transaction_type}`}>{tx.transaction_type === 'GOAL_TRANSFER' ? 'GOAL' : tx.transaction_type}</span></td>
                            <td>{tx.category || '-'}</td><td>{tx.description}</td>
                            <td style={{ textAlign: 'right', fontWeight: 'bold', color: tx.transaction_type === 'DEPOSIT' ? '#2e7d32' : '#c62828' }}>{tx.transaction_type === 'DEPOSIT' ? '+' : '-'}₹{parseFloat(tx.amount).toFixed(2)}</td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                )}
              </div>
            </div>
          </div>
        )}

        {activeTab === 'personal' && (
          <div>
            <div className="balance-card">
              <h2>My Personal Wallet 🤫</h2>
              <p style={{ color: '#666', marginBottom: '1.5rem' }}>Your private space. Your partner cannot see this unless you allow it.</p>
              {personalWallet ? (
                <div className="dashboard-grid">
                  <div className="info-cards" style={{ gridColumn: 'span 2' }}>
                    <div className="info-card">
                      <h3>My Private Balance</h3>
                      <div className="info-value" style={{ color: '#27ae60' }}>₹{personalWallet.balance}</div>
                    </div>
                    
                    <div className="info-card" style={{ display: 'flex', flexDirection: 'column', justifyContent: 'center', background: personalWallet.is_visible_to_partner ? '#e8f5e9' : '#f8f9fa' }}>
                      <label className="toggle-label" style={{ cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '10px' }}>
                        <input type="checkbox" checked={personalWallet.is_visible_to_partner} onChange={async (e) => { await api.togglePersonalWalletVisibility(e.target.checked); loadDashboardData(); }} />
                        <span style={{ fontWeight: '600' }}>Share balance with partner</span>
                      </label>
                    </div>

                    <div className="info-card" style={{ border: '1px dashed #764ba2' }}>
                      <h3>Partner's Shared Balance</h3>
                      {(personalWallet as any).partner_wallet ? (
                        <div>
                          <div className="info-value" style={{ color: '#764ba2' }}>₹{(personalWallet as any).partner_wallet.balance}</div>
                          <p style={{ fontSize: '0.8rem', color: '#666' }}>Shared by <strong>{(personalWallet as any).partner_wallet.username}</strong></p>
                        </div>
                      ) : (
                        <div style={{ color: '#999', fontSize: '0.85rem', marginTop: '10px' }}>Not shared.</div>
                      )}
                    </div>
                  </div>

                  <div className="button-group-grid" style={{ gridColumn: 'span 2', marginTop: '1.5rem' }}>
                    <button onClick={() => setShowPersonalDepositForm(true)} className="submit-btn">💳 Add Funds</button>
                    <button onClick={() => setShowPersonalWithdrawForm(true)} className="submit-btn" style={{ background: '#e67e22' }}>💸 Withdraw</button>
                  </div>
                </div>
              ) : (
                <div style={{ textAlign: 'center', padding: '2rem' }}>
                  <p>No personal wallet.</p>
                  <button onClick={async () => { await api.createPersonalWallet(); loadDashboardData(); }} className="submit-btn" style={{ width: 'auto' }}>Create Personal Wallet</button>
                </div>
              )}
            </div>

            <div className="info-card" style={{ marginTop: '2rem' }}>
              <h3>📜 My Private Transactions</h3>
              <div className="table-container" style={{ marginTop: '1rem' }}>
                {personalTransactions.length === 0 ? <p style={{ color: '#999', textAlign: 'center', padding: '2rem' }}>No private transactions recorded yet.</p> : (
                  <table className="statement-table">
                    <thead><tr><th>Date</th><th>Type</th><th>Description</th><th style={{ textAlign: 'right' }}>Amount</th></tr></thead>
                    <tbody>
                      {personalTransactions.map((tx) => (
                        <tr key={tx.id}>
                          <td>{new Date(tx.date).toLocaleDateString()}</td>
                          <td><span className={`tag ${tx.type}`}>{tx.type}</span></td>
                          <td>{tx.description}</td>
                          <td style={{ textAlign: 'right', fontWeight: 'bold', color: tx.type === 'DEPOSIT' ? '#2e7d32' : '#c62828' }}>{tx.type === 'DEPOSIT' ? '+' : '-'}₹{tx.amount.toFixed(2)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                )}
              </div>
            </div>
          </div>
        )}

        {activeTab === 'goals' && (
          <div>
            <div className="balance-card">
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}><h2 style={{ margin: 0 }}>Joint Goals 🎯</h2><button onClick={() => setShowGoalForm(true)} className="submit-btn" style={{ width: 'auto', padding: '0.5rem 1rem' }}>+ New Goal</button></div>
              <div className="info-cards">
                {goals.length === 0 ? <p style={{ color: '#999' }}>No goals set yet.</p> : goals.map(goal => (
                  <div key={goal.id} className="info-card goal-card" onClick={() => { setSelectedGoalId(goal.id); setGoalName(goal.name); setGoalTarget(goal.target_amount.toString()); setGoalDeadline(goal.deadline); setShowEditGoalForm(true); }} style={{ cursor: 'pointer' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}><h3>{goal.name}</h3><span style={{ fontSize: '1.2rem' }}>✏️</span></div>
                    <div className="goal-amounts"><span className="current">₹{goal.current_amount}</span><span className="target">of ₹{goal.target_amount}</span></div>
                    <div className="progress-bar-container"><div className="progress-bar-fill" style={{ width: `${goal.progress_percentage}%` }}></div></div>
                    <div className="goal-footer"><span className="deadline">📅 {new Date(goal.deadline).toLocaleDateString()}</span><button onClick={(e) => { e.stopPropagation(); const amt = prompt('Enter contribution amount:'); if (amt) handleContributeToGoal(goal.id, parseFloat(amt)); }} className="add-funds-btn">Add Funds</button></div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {activeTab === 'approvals' && (
          <div>
            <div className="balance-card">
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}><h2 style={{ margin: 0 }}>Spending Approvals 🛡️</h2><button onClick={() => setShowRequestForm(true)} className="submit-btn" style={{ width: 'auto', padding: '0.5rem 1rem' }}>Request Expense</button></div>
              <div className="table-container">
                {requests.length === 0 ? <p style={{ color: '#999', padding: '1rem' }}>No pending requests.</p> : (
                  <table className="statement-table">
                    <thead><tr><th>Date</th><th>Requester</th><th>Description</th><th>Amount</th><th>Status</th><th>Actions</th></tr></thead>
                    <tbody>
                      {requests.map(req => {
                        const requesterName = typeof req.requester === 'object' ? (req.requester as any).username : req.requester;
                        const isOtherPartner = requesterName !== currentUser;
                        return (
                          <tr key={req.id}>
                            <td>{req.requested_at ? new Date(req.requested_at).toLocaleDateString() : 'Unknown'}</td>
                            <td>{requesterName}</td>
                            <td>{req.description}</td><td style={{ fontWeight: 'bold' }}>₹{req.amount}</td>
                            <td><span className={`tag ${req.status === 'APPROVED' ? 'INC' : req.status === 'REJECTED' ? 'EXP' : ''}`}>{req.status}</span></td>
                            <td>{req.status === 'PENDING' && isOtherPartner && (<div style={{ display: 'flex', gap: '0.5rem' }}><button onClick={() => handleRespondRequest(req.id, 'approve')} className="action-btn approve">✓</button><button onClick={() => handleRespondRequest(req.id, 'reject')} className="action-btn reject">✕</button></div>)}</td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                )}
              </div>
            </div>
          </div>
        )}

        {activeTab === 'settlement' && (
          <div className="balance-card">
            <h2>Monthly Settlement ⚖️</h2><p style={{ color: '#666', marginBottom: '1.5rem' }}>Automatically calculates the financial imbalance between partners for shared expenses.</p>
            {settlement && jointWallet ? (
              <div>
                <div className="settlement-grid">
                  <div className="settlement-stat">
                    <span className="label"><strong>{jointWallet.partner1}</strong>'s Contribution</span>
                    <span className="value">₹{settlement.partner1_contributed}</span>
                  </div>
                  <div className="settlement-stat">
                    <span className="label"><strong>{jointWallet.partner2}</strong>'s Contribution</span>
                    <span className="value">₹{settlement.partner2_contributed}</span>
                  </div>
                  <div className="settlement-stat highlight">
                    <span className="label">Total Shared Expenses</span>
                    <span className="value">₹{settlement.total_shared_expenses}</span>
                  </div>
                </div>

                <div className="settlement-result">
                  <h3 style={{ color: '#e67e22', marginBottom: '1rem' }}>Fairness Adjustment</h3>
                  {settlement.amount_owed > 0 ? (
                    <div className="imbalance-alert">
                      <p>To balance the expenses equally (50/50):</p>
                      <div className="owed-display">
                        <strong>{settlement.owes_to}</strong> should receive <span>₹{settlement.amount_owed.toFixed(2)}</span>
                      </div>
                    </div>
                  ) : (
                    <div className="balanced-alert">
                      Contributions are perfectly balanced! 🎉
                    </div>
                  )}
                </div>

                {/* NEW: DETAILED SETTLEMENT HISTORY */}
                <div className="info-card" style={{ marginTop: '2rem' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem', marginBottom: '1.5rem' }}>
                    <h3 style={{ margin: 0 }}>📜 Joint Spending History</h3>
                    <button 
                      onClick={downloadSettlementCSV} 
                      className="print-btn"
                      style={{ background: '#27ae60' }}
                    >
                      📥 Download CSV
                    </button>
                  </div>

                  {/* Search and Filters */}
                  <div className="filters-row" style={{ padding: '0.5rem', marginBottom: '1rem' }}>
                    <input 
                      type="text" 
                      placeholder="🔍 Search description..." 
                      value={settlementSearch} 
                      onChange={e => setSettlementSearch(e.target.value)}
                      style={{ flex: 2 }}
                    />
                    <select 
                      value={settlementCategoryFilter} 
                      onChange={e => setSettlementCategoryFilter(e.target.value)}
                      style={{ flex: 1 }}
                    >
                      <option value="ALL">All Categories</option>
                      {JOINT_CATEGORIES.map(c => <option key={c.value} value={c.value}>{c.label}</option>)}
                    </select>
                  </div>

                  <div className="table-container">
                    <table className="statement-table">
                      <thead>
                        <tr>
                          <th>Date</th>
                          <th>Partner</th>
                          <th>Type</th>
                          <th>Category</th>
                          <th style={{ textAlign: 'right' }}>Amount</th>
                        </tr>
                      </thead>
                      <tbody>
                        {(settlement as any).history
                          ?.filter((tx: any) => {
                            const matchesSearch = tx.description.toLowerCase().includes(settlementSearch.toLowerCase());
                            const matchesCat = settlementCategoryFilter === 'ALL' || tx.category === settlementCategoryFilter;
                            return matchesSearch && matchesCat;
                          })
                          .map((tx: any) => (
                          <tr key={tx.id}>
                            <td>{new Date(tx.date).toLocaleDateString()}</td>
                            <td><strong>{tx.user}</strong></td>
                            <td><span className={`tag ${tx.type}`}>{tx.type}</span></td>
                            <td>{tx.category}</td>
                            <td style={{ textAlign: 'right', fontWeight: 'bold', color: tx.type === 'DEPOSIT' ? '#2e7d32' : '#c62828' }}>
                              {tx.type === 'DEPOSIT' ? '+' : '-'}₹{tx.amount.toFixed(2)}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              </div>
            ) : (
              <p>Calculating...</p>
            )}
          </div>
        )}

        {/* MODALS */}
        {showPersonalDepositForm && (
          <div className="modal-overlay" onClick={() => setShowPersonalDepositForm(false)}><div className="modal" onClick={e => e.stopPropagation()}><h2>Add Private Funds 🤫</h2><form onSubmit={(e) => handlePersonalAction(e, 'deposit')}><div className="form-group"><label>Amount (₹)</label><input type="number" value={personalAmount} onChange={e => setPersonalAmount(e.target.value)} required min="1" /></div><button type="submit" className="submit-btn">Deposit</button><button type="button" onClick={() => setShowPersonalDepositForm(false)} className="cancel-btn">Cancel</button></form></div></div>
        )}
        {showPersonalWithdrawForm && (
          <div className="modal-overlay" onClick={() => setShowPersonalWithdrawForm(false)}><div className="modal" onClick={e => e.stopPropagation()}><h2>Private Withdrawal 💸</h2><form onSubmit={(e) => handlePersonalAction(e, 'withdraw')}><div className="form-group"><label>Amount (₹)</label><input type="number" value={personalAmount} onChange={e => setPersonalAmount(e.target.value)} required min="1" /></div><button type="submit" className="submit-btn">Withdraw</button><button type="button" onClick={() => setShowPersonalWithdrawForm(false)} className="cancel-btn">Cancel</button></form></div></div>
        )}
        {showDepositForm && (
          <div className="modal-overlay" onClick={() => setShowDepositForm(false)}><div className="modal" onClick={e => e.stopPropagation()}><h2>Contribute to Joint Wallet</h2><form onSubmit={handleDeposit}><div className="form-group"><label>Amount (₹)</label><input type="number" value={depositAmount} onChange={e => setDepositAmount(e.target.value)} required min="1" /></div><button type="submit" className="submit-btn">Contribute</button><button type="button" onClick={() => setShowDepositForm(false)} className="cancel-btn">Cancel</button></form></div></div>
        )}
        {showBudgetForm && (
          <div className="modal-overlay" onClick={() => setShowBudgetForm(false)}><div className="modal" onClick={e => e.stopPropagation()}><h2>Set Monthly Budget ⚙️</h2><form onSubmit={handleSetBudget}><div className="form-group"><label>Amount (₹)</label><input type="number" value={newBudget} onChange={e => setNewBudget(e.target.value)} required min="1" /></div><button type="submit" className="submit-btn">Update Budget</button><button type="button" onClick={() => setShowBudgetForm(false)} className="cancel-btn">Cancel</button></form></div></div>
        )}
        {showWithdrawForm && (
          <div className="modal-overlay" onClick={() => setShowWithdrawForm(false)}><div className="modal" onClick={e => e.stopPropagation()}><h2>Record Shared Expense</h2><form onSubmit={handleWithdraw}><div className="form-group"><label>Amount (₹)</label><input type="number" value={withdrawAmount} onChange={e => setWithdrawAmount(e.target.value)} required min="1" /></div><div className="form-group"><label>Category</label><select value={withdrawCategory} onChange={e => setWithdrawCategory(e.target.value)}>{JOINT_CATEGORIES.map(cat => <option key={cat.value} value={cat.value}>{cat.icon} {cat.label}</option>)}</select></div><div className="form-group"><label>Description</label><input type="text" value={withdrawDescription} onChange={e => setWithdrawDescription(e.target.value)} required placeholder="e.g., Rent, Groceries" /></div><button type="submit" className="submit-btn">Record Expense</button><button type="button" onClick={() => setShowWithdrawForm(false)} className="cancel-btn">Cancel</button></form></div></div>
        )}
        {showRequestForm && (
          <div className="modal-overlay" onClick={() => setShowRequestForm(false)}><div className="modal" onClick={e => e.stopPropagation()}><h2>Request High-Value Expense</h2><form onSubmit={handleCreateRequest}><div className="form-group"><label>Amount</label><input type="number" value={requestAmount} onChange={e => setRequestAmount(e.target.value)} required /></div><div className="form-group"><label>Category</label><select value={requestCategory} onChange={e => setRequestCategory(e.target.value)}>{JOINT_CATEGORIES.map(cat => <option key={cat.value} value={cat.value}>{cat.icon} {cat.label}</option>)}</select></div><div className="form-group"><label>Description</label><input type="text" value={requestDescription} onChange={e => setRequestDescription(e.target.value)} required /></div><button type="submit" className="submit-btn">Send Request</button><button type="button" onClick={() => setShowRequestForm(false)} className="cancel-btn">Cancel</button></form></div></div>
        )}
        {showGoalForm && (
          <div className="modal-overlay" onClick={() => setShowGoalForm(false)}><div className="modal" onClick={e => e.stopPropagation()}><h2>Create Joint Goal 🎯</h2><form onSubmit={handleCreateGoal}><div className="form-group"><label>Goal Name</label><input type="text" value={goalName} onChange={e => setGoalName(e.target.value)} required /></div><div className="form-group"><label>Target Amount</label><input type="number" value={goalTarget} onChange={e => setGoalTarget(e.target.value)} required /></div><div className="form-group"><label>Deadline</label><input type="date" value={goalDeadline} onChange={e => setGoalDeadline(e.target.value)} required /></div><button type="submit" className="submit-btn">Create Goal</button><button type="button" onClick={() => setShowGoalForm(false)} className="cancel-btn">Cancel</button></form></div></div>
        )}
        {showEditGoalForm && (
          <div className="modal-overlay" onClick={() => setShowEditGoalForm(false)}><div className="modal" onClick={e => e.stopPropagation()}><h2>Edit Joint Goal ✏️</h2><form onSubmit={handleUpdateGoal}><div className="form-group"><label>Goal Name</label><input type="text" value={goalName} onChange={e => setGoalName(e.target.value)} required /></div><div className="form-group"><label>Target Amount</label><input type="number" value={goalTarget} onChange={e => setGoalTarget(e.target.value)} required /></div><div className="form-group"><label>Deadline</label><input type="date" value={goalDeadline} onChange={e => setGoalDeadline(e.target.value)} required /></div><button type="submit" className="submit-btn">Save Changes</button><button type="button" onClick={() => setShowEditGoalForm(false)} className="cancel-btn">Cancel</button></form></div></div>
        )}
      </main>
    </div>
  );
}
