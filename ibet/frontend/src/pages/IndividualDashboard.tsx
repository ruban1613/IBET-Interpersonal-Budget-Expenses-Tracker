import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, 
  LineChart, Line, AreaChart, Area, Cell, PieChart, Pie
} from 'recharts';
import { api } from '../services/api';
import './Dashboard.css';

interface WalletData {
  balance: string;
  total_deposits: string;
  monthly_budget: string;
  savings_goal: string;
  current_savings: string;
  available_balance: string;
  is_locked: boolean;
}

interface InvestmentSuggestion {
  id: number;
  title: string;
  plan_type: string;
  description: string;
  benefits: string;
  minimum_investment: string;
  current_scenario_analysis: string;
}

interface MonthlySummary {
  month: string;
  total_spent: number;
  category_breakdown: Array<{ category: string; total: string }>;
  investment_suggestions: InvestmentSuggestion[];
}

interface TodaySpending {
  date: string;
  total_spent: number;
  expenses: Array<{ id: number; amount: string; category: string; description: string }>;
}

interface DailyData {
  day: number;
  date: string;
  amount: number;
}

interface YearlyData {
  month: string;
  full_month: string;
  year: number;
  amount: number;
}

interface Alert {
  id: number;
  type: string;
  title: string;
  message: string;
  percentage: string | null;
  is_read: boolean;
  created_at: string;
}

const EXPENSE_CATEGORIES = [
  { value: 'FOOD', label: 'Food & Dining', icon: '🍔' },
  { value: 'TRANSPORT', label: 'Transportation', icon: '🚗' },
  { value: 'UTILITIES', label: 'Utilities', icon: '💡' },
  { value: 'ENTERTAINMENT', label: 'Entertainment', icon: '🎬' },
  { value: 'SHOPPING', label: 'Shopping', icon: '🛒' },
  { value: 'HEALTH', label: 'Healthcare', icon: '🏥' },
  { value: 'EDUCATION', label: 'Education', icon: '📚' },
  { value: 'BILLS', label: 'Bills & Payments', icon: '📄' },
  { value: 'OTHER', label: 'Other', icon: '📦' }
];

export default function IndividualDashboard() {
  const navigate = useNavigate();
  const [wallet, setWallet] = useState<WalletData | null>(null);
  const [userProfile, setUserProfile] = useState<any>(null);
  const [monthlySummary, setMonthlySummary] = useState<MonthlySummary | null>(null);
  const [todaySpending, setTodaySpending] = useState<TodaySpending | null>(null);
  const [dailyChartData, setDailyChartData] = useState<DailyData[]>([]);
  const [yearlyChartData, setYearlyChartData] = useState<YearlyData[]>([]);
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  
  // Transaction form state
  const [showDepositModal, setShowDepositModal] = useState(false);
  const [showWithdrawModal, setShowWithdrawModal] = useState(false);
  const [showSavingsWithdrawModal, setShowSavingsWithdrawModal] = useState(false);
  const [showTransferModal, setShowTransferModal] = useState(false);
  const [showExpenseModal, setShowExpenseModal] = useState(false);
  const [showStatementModal, setShowStatementModal] = useState(false);
  const [statementData, setStatementData] = useState<any[]>([]);
  const [filterYear, setYear] = useState(new Date().getFullYear());
  const [filterMonth, setMonth] = useState(new Date().getMonth() + 1);
  const [filterDay, setDay] = useState('');
  const [loadingStatement, setLoadingStatement] = useState(false);

  const fetchStatement = async () => {
    setLoadingStatement(true);
    try {
      const data = await api.getIndividualStatement(
        filterYear, 
        filterMonth, 
        filterDay ? parseInt(filterDay) : undefined
      );
      setStatementData(data.transactions || []);
    } catch (err) {
      setTxError('Failed to fetch statement');
    } finally {
      setLoadingStatement(false);
    }
  };

  useEffect(() => {
    if (showStatementModal) {
      fetchStatement();
    }
  }, [showStatementModal, filterYear, filterMonth, filterDay]);
  const [showSettingsModal, setShowSettingsModal] = useState(false);
  const [action, setAction] = useState<'deposit' | 'withdraw' | 'transfer' | 'withdraw_savings'>('deposit');
  
  const [amount, setAmount] = useState('');
  const [description, setDescription] = useState('');
  const [category, setCategory] = useState('FOOD');
  const [otp, setOtp] = useState('');
  const [otpRequestId, setOtpRequestId] = useState<number | null>(null);
  const [processing, setProcessing] = useState(false);
  const [success, setSuccess] = useState('');
  const [txError, setTxError] = useState('');
  const [isExpense, setIsExpense] = useState(false);

  // Settings state
  const [budgetAmount, setBudgetAmount] = useState('');
  const [savingsGoalAmount, setSavingsGoalAmount] = useState('');
  const [savingSettings, setSavingSettings] = useState(false);

  // Notification panel state
  const [showNotifications, setShowNotifications] = useState(false);

  useEffect(() => {
    loadAllData();
  }, []);

  const loadAllData = async () => {
    setLoading(true);
    setError('');
    try {
      const [walletData, summaryData, todayData, alertsData, dailyData, yearlyData, profileData] = await Promise.all([
        api.getIndividualDashboard(),
        api.getIndividualMonthlySummary(),
        api.getIndividualTodaySpending(),
        api.getIndividualSpendingAlerts(),
        api.getIndividualDailySpendingSummary(),
        api.getIndividualYearlySpendingSummary(),
        api.getProfile()
      ]);
      setWallet(walletData);
      setMonthlySummary(summaryData);
      setTodaySpending(todayData);
      setDailyChartData(dailyData);
      setYearlyChartData(yearlyData);
      setAlerts(Array.isArray(alertsData) ? alertsData : (alertsData.results || []));
      setUserProfile(profileData);
    } catch (err) {
      setError('Failed to load dashboard data');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const loadAlerts = async () => {
    try {
      const data = await api.getIndividualSpendingAlerts();
      setAlerts(Array.isArray(data) ? data : (data.results || []));
    } catch (err) {
      console.error('Failed to load alerts:', err);
    }
  };

  const handleLogout = () => {
    api.clearToken();
    navigate('/login');
  };

  const handleBack = () => {
    navigate('/select-module');
  };

  const handleMarkAlertRead = async (alertId: number) => {
    try {
      await api.markIndividualAlertRead(alertId);
      setAlerts(prev => prev.map(a => a.id === alertId ? { ...a, is_read: true } : a));
    } catch (err) {
      console.error('Failed to mark alert as read:', err);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!amount || parseFloat(amount) <= 0) return;

    setProcessing(true);
    setTxError('');
    setSuccess('');

    try {
      if (action === 'deposit') {
        // Deposit does NOT require OTP in new backend
        await api.depositToIndividualWallet(parseFloat(amount), description || 'Deposit');
        setSuccess('Deposit successful!');
        setShowDepositModal(false);
      } 
      else if (action === 'withdraw') {
        // Main withdrawal does NOT require OTP
        if (isExpense) {
          await api.recordIndividualExpense(parseFloat(amount), category, description || 'Withdrawal Expense');
          setSuccess('Expense recorded successfully!');
        } else {
          await api.withdrawFromIndividualWallet(parseFloat(amount), description || 'Withdrawal');
          setSuccess('Withdrawal successful!');
        }
        setShowWithdrawModal(false);
      }
      else if (action === 'transfer') {
        // Transfer to savings requires OTP
        if (!otpRequestId) {
          const otpResult = await api.generateIndividualOTP('transfer', parseFloat(amount));
          setOtpRequestId(otpResult.otp_request_id);
          setSuccess(`OTP requested. Your OTP is: ${otpResult.otp_code}`);
          setProcessing(false);
          return;
        }
        await api.transferToIndividualSavings(parseFloat(amount), otp, otpRequestId);
        setSuccess('Transfer to savings successful!');
        setShowTransferModal(false);
      }
      else if (action === 'withdraw_savings') {
        // Withdrawal from savings requires OTP
        if (!otpRequestId) {
          const otpResult = await api.generateIndividualOTP('savings_withdrawal', parseFloat(amount));
          setOtpRequestId(otpResult.otp_request_id);
          setSuccess(`OTP requested. Your OTP is: ${otpResult.otp_code}`);
          setProcessing(false);
          return;
        }
        
        if (isExpense) {
          // Special logic for savings withdrawal as expense: we use savings balance to pay an expense
          // First withdraw to main, then record expense
          await api.withdrawFromIndividualSavings(parseFloat(amount), otp, otpRequestId, description);
          await api.recordIndividualExpense(parseFloat(amount), category, description || 'Savings Withdrawal Expense');
          setSuccess('Savings withdrawal recorded as expense!');
        } else {
          await api.withdrawFromIndividualSavings(parseFloat(amount), otp, otpRequestId, description);
          setSuccess('Withdrawal from savings successful!');
        }
        setShowSavingsWithdrawModal(false);
      }
      
      setAmount('');
      setDescription('');
      setOtp('');
      setOtpRequestId(null);
      loadAllData();
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Transaction failed';
      setTxError(errorMessage);
    } finally {
      setProcessing(false);
    }
  };

  const handleRecordExpense = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!amount || parseFloat(amount) <= 0) return;

    setProcessing(true);
    setTxError('');
    setSuccess('');

    try {
      const result = await api.recordIndividualExpense(parseFloat(amount), category, description);
      setSuccess(`Expense recorded!`);
      setShowExpenseModal(false);
      setAmount('');
      setDescription('');
      setCategory('FOOD');
      loadAllData();
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to record expense';
      setTxError(errorMessage);
    } finally {
      setProcessing(false);
    }
  };

  const handleSaveSettings = async () => {
    setSavingSettings(true);
    setTxError('');
    setSuccess('');
    try {
      if (budgetAmount) {
        await api.setMonthlyBudget(parseFloat(budgetAmount));
      }
      if (savingsGoalAmount) {
        await api.setSavingsGoal(parseFloat(savingsGoalAmount));
      }
      setSuccess('Settings saved successfully!');
      setShowSettingsModal(false);
      setBudgetAmount('');
      setSavingsGoalAmount('');
      loadAllData();
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to save settings';
      setTxError(errorMessage);
    } finally {
      setSavingSettings(false);
    }
  };

  const openModal = (type: 'deposit' | 'withdraw' | 'transfer' | 'withdraw_savings') => {
    setAction(type);
    setAmount('');
    setDescription('');
    setOtp('');
    setOtpRequestId(null);
    setTxError('');
    setSuccess('');
    if (type === 'deposit') setShowDepositModal(true);
    else if (type === 'withdraw') setShowWithdrawModal(true);
    else if (type === 'transfer') setShowTransferModal(true);
    else if (type === 'withdraw_savings') setShowSavingsWithdrawModal(true);
  };

  // Calculate spending percentage
  const monthlyBudget = parseFloat(wallet?.monthly_budget || '0');
  const totalSpent = monthlySummary?.total_spent || 0;
  const spendingPercentage = monthlyBudget > 0 ? Math.min((totalSpent / monthlyBudget) * 100, 100) : 0;

  if (loading) {
    return <div className="loading">Loading individual dashboard...</div>;
  }

  return (
    <div className="dashboard-container">
      <header className="dashboard-header">
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <button onClick={handleBack} className="back-btn">← Back</button>
          <button 
            onClick={() => setShowNotifications(!showNotifications)} 
            style={{
              position: 'relative',
              background: 'transparent',
              border: 'none',
              fontSize: '1.3rem',
              cursor: 'pointer',
              padding: '8px',
              margin: 0
            }}
          >
            🔔
            {alerts.filter(a => !a.is_read).length > 0 && (
              <span style={{
                position: 'absolute',
                top: '2px',
                right: '2px',
                background: '#e74c3c',
                color: 'white',
                borderRadius: '50%',
                width: '16px',
                height: '16px',
                fontSize: '0.65rem',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center'
              }}>
                {alerts.filter(a => !a.is_read).length}
              </span>
            )}
          </button>
        </div>
        <h1>Individual Dashboard 💼 {userProfile?.uid && <span style={{ fontSize: '0.9rem', color: '#667eea', background: 'white', padding: '2px 8px', borderRadius: '4px', marginLeft: '10px', verticalAlign: 'middle' }}>{userProfile.uid}</span>}</h1>
        <button onClick={handleLogout} className="logout-btn">Logout</button>
      </header>

      {/* Notification Panel */}
      {showNotifications && (
        <div style={{
          position: 'fixed',
          top: '60px',
          right: '10px',
          width: '350px',
          maxHeight: '70vh',
          background: 'white',
          borderRadius: '12px',
          boxShadow: '0 8px 32px rgba(0,0,0,0.15)',
          zIndex: 1000,
          overflow: 'hidden',
          display: 'flex',
          flexDirection: 'column'
        }}>
          <div style={{
            padding: '15px',
            borderBottom: '1px solid #eee',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
            color: 'white'
          }}>
            <h3 style={{ margin: 0 }}>Spending Alerts</h3>
            <div style={{ display: 'flex', gap: '8px' }}>
              <button 
                onClick={() => { loadDashboard(); loadAlerts(); }}
                title="Refresh"
                style={{
                  background: 'transparent',
                  border: 'none',
                  color: 'white',
                  fontSize: '1rem',
                  cursor: 'pointer',
                  padding: '4px 8px',
                  borderRadius: '4px'
                }}
              >
                🔄
              </button>
              <button 
                onClick={() => setShowNotifications(false)}
                style={{
                  background: 'transparent',
                  border: 'none',
                  color: 'white',
                  fontSize: '1.2rem',
                  cursor: 'pointer'
                }}
              >
                ✕
              </button>
            </div>
          </div>
          <div style={{
            overflowY: 'auto',
            flex: 1,
            padding: '10px'
          }}>
            {alerts.length === 0 ? (
              <div style={{ textAlign: 'center', padding: '30px', color: '#999' }}>
                No alerts
              </div>
            ) : (
              alerts.map(alert => (
                <div 
                  key={alert.id}
                  style={{
                    padding: '12px',
                    marginBottom: '8px',
                    borderRadius: '8px',
                    background: alert.is_read ? '#f5f5f5' : '#fff3e0',
                    border: '1px solid #eee',
                    cursor: 'pointer'
                  }}
                  onClick={() => handleMarkAlertRead(alert.id)}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start' }}>
                    <div style={{ fontWeight: alert.is_read ? 'normal' : 'bold', marginBottom: '4px' }}>
                      {alert.type === 'SPENT_50' && '⚠️ 50% Used'}
                      {alert.type === 'SPENT_80' && '🚨 80% Used'}
                      {alert.type === 'SPENT_100' && '💰 100% Used'}
                      {alert.type === 'ANOMALY' && '🔍 Anomaly Detected'}
                    </div>
                    <div style={{ fontSize: '0.75rem', color: '#999' }}>
                      {new Date(alert.created_at).toLocaleString()}
                    </div>
                  </div>
                  <div style={{ fontSize: '0.85rem', color: '#555', marginBottom: '4px' }}>
                    {alert.message}
                  </div>
                  {alert.percentage && (
                    <div style={{ fontSize: '0.8rem', color: '#e74c3c', fontWeight: 'bold' }}>
                      {alert.percentage}% of budget
                    </div>
                  )}
                </div>
              ))
            )}
          </div>
        </div>
      )}

      <main className="dashboard-main">
        {error && <div className="error-message">{error}</div>}
        {success && <div className="success-message">{success}</div>}
        {txError && <div className="error-message">{txError}</div>}

        {/* Main Wallet Balance Card */}
        <div className="balance-card">
          <h2>Main Wallet Balance</h2>
          <div className="balance-amount">
            ₹{parseFloat(wallet?.balance || '0').toFixed(2)}
          </div>
          <div className="additional-balance">
            <div className="balance-item">
              <span className="label">Monthly Budget</span>
              <span className="amount">₹{parseFloat(wallet?.monthly_budget || '0').toFixed(2)}</span>
            </div>
            <div className="balance-item">
              <span className="label">Total Deposits</span>
              <span className="amount income">₹{parseFloat(wallet?.total_deposits || '0').toFixed(2)}</span>
            </div>
          </div>
          <div style={{ marginTop: '0.5rem', textAlign: 'center' }}>
            <button 
              onClick={() => { setShowSettingsModal(true); setSuccess(''); setTxError(''); }}
              style={{
                padding: '0.5rem 1rem',
                background: 'transparent',
                border: '1px solid #667eea',
                color: '#667eea',
                borderRadius: '6px',
                cursor: 'pointer',
                fontSize: '0.85rem'
              }}
            >
              ⚙️ Set Budget & Goal
            </button>
          </div>
          <div style={{ marginTop: '1rem', display: 'flex', gap: '0.5rem', justifyContent: 'center' }}>
            <button onClick={() => openModal('deposit')} className="submit-btn" style={{ flex: 1, maxWidth: '150px' }}>
              Deposit
            </button>
            <button onClick={() => openModal('withdraw')} className="submit-btn" style={{ flex: 1, maxWidth: '150px', background: '#e74c3c' }}>
              Withdraw
            </button>
          </div>
        </div>

        {/* Info Cards - Stats */}
        <div className="info-cards">
          <div className="info-card">
            <h3>📊 Monthly Spent</h3>
            <div className="info-value">₹{totalSpent.toFixed(2)}</div>
            <div className="info-sub">{monthlySummary?.month || 'This month'}</div>
          </div>

          <div className="info-card">
            <h3>📈 Spending Progress</h3>
            <div className="info-value">{spendingPercentage.toFixed(1)}%</div>
            <div className="progress-bar">
              <div 
                className={`progress-fill ${spendingPercentage >= 80 ? 'warning' : ''} ${spendingPercentage >= 100 ? 'danger' : ''}`}
                style={{ width: `${spendingPercentage}%` }}
              />
            </div>
            <div className="info-sub">₹{totalSpent.toFixed(2)} of ₹{monthlyBudget.toFixed(2)}</div>
          </div>

          <div className="info-card">
            <h3>📅 Today's Spending</h3>
            <div className="info-value">₹{parseFloat(todaySpending?.total_spent?.toString() || '0').toFixed(2)}</div>
            <div className="info-sub">{todaySpending?.date}</div>
          </div>
        </div>

        {/* Dynamic Charts Section */}
        <div className="info-cards" style={{ gridTemplateColumns: 'repeat(auto-fit, minmax(400px, 1fr))' }}>
          {/* Daily Expenditure Chart */}
          <div className="info-card" style={{ minHeight: '400px' }}>
            <h3>📈 Spending Analysis (Every Withdrawal)</h3>
            <div style={{ width: '100%', height: '300px', marginTop: '1rem', minWidth: 0, minHeight: 0 }}>
              <ResponsiveContainer width="99%" height={300}>
                <AreaChart data={dailyChartData}>
                  <defs>
                    <linearGradient id="colorAmount" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#667eea" stopOpacity={0.8}/>
                      <stop offset="95%" stopColor="#667eea" stopOpacity={0}/>
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#eee" />
                  <XAxis 
                    dataKey="index" 
                    axisLine={false} 
                    tickLine={false} 
                    tick={{ fontSize: 10, fill: '#999' }}
                    label={{ value: 'Your Transactions (Order)', position: 'insideBottom', offset: -5, fontSize: 12 }}
                  />
                  <YAxis 
                    axisLine={false} 
                    tickLine={false} 
                    tick={{ fontSize: 12, fill: '#999' }}
                    tickFormatter={(value) => `₹${value}`}
                  />
                  <Tooltip 
                    content={({ active, payload }) => {
                      if (active && payload && payload.length) {
                        const data = payload[0].payload;
                        return (
                          <div style={{ background: 'white', padding: '10px', border: '1px solid #ccc', borderRadius: '8px', boxShadow: '0 4px 12px rgba(0,0,0,0.1)' }}>
                            <p style={{ margin: 0, fontWeight: 'bold', color: '#667eea' }}>{data.date}</p>
                            <p style={{ margin: '4px 0', fontSize: '1.1rem', fontWeight: 'bold' }}>₹{data.amount}</p>
                            <p style={{ margin: 0, color: '#333' }}>{data.category}: {data.description}</p>
                            <p style={{ margin: 0, color: '#999', fontSize: '0.75rem' }}>Transaction #{data.index}</p>
                          </div>
                        );
                      }
                      return null;
                    }}
                  />
                  <Area 
                    type="monotone" 
                    dataKey="amount" 
                    stroke="#667eea" 
                    fillOpacity={1} 
                    fill="url(#colorAmount)" 
                    dot={{ r: 4, fill: '#667eea' }}
                    activeDot={{ r: 6, strokeWidth: 0 }}
                  />
                </AreaChart>
              </ResponsiveContainer>
            </div>
            <div className="info-sub">Tracking every spending transaction recorded in March 2026</div>
          </div>

          {/* Monthly Expenditure Chart */}
          <div className="info-card" style={{ minHeight: '350px' }}>
            <h3>📊 Monthly Expenditure (Yearly)</h3>
            <div style={{ width: '100%', height: '250px', marginTop: '1rem', minWidth: 0, minHeight: 0 }}>
              <ResponsiveContainer width="99%" height={250}>
                <BarChart data={yearlyChartData}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#eee" />
                  <XAxis 
                    dataKey="month" 
                    axisLine={false} 
                    tickLine={false} 
                    tick={{ fontSize: 12, fill: '#999' }}
                  />
                  <YAxis 
                    axisLine={false} 
                    tickLine={false} 
                    tick={{ fontSize: 12, fill: '#999' }}
                    tickFormatter={(value) => `₹${value}`}
                  />
                  <Tooltip 
                    formatter={(value: any) => [`₹${value}`, 'Spent']}
                    contentStyle={{ borderRadius: '8px', border: 'none', boxShadow: '0 4px 12px rgba(0,0,0,0.1)' }}
                  />
                  <Bar dataKey="amount" fill="#764ba2" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
            <div className="info-sub">Total monthly spending for the last 12 months</div>
          </div>
        </div>

        {/* Granular Spending Pie Chart */}
        <div className="info-card" style={{ marginBottom: '2rem', minHeight: '400px' }}>
          <h3>🥧 Individual Transaction Breakdown ({monthlySummary?.month})</h3>
          <div style={{ width: '100%', height: '350px', display: 'flex', alignItems: 'center', minWidth: 0, minHeight: 0 }}>
            <ResponsiveContainer width="99%" height={350}>
              <PieChart>
                <Pie
                  data={(monthlySummary as any)?.individual_expenses || []}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={100}
                  paddingAngle={2}
                  dataKey="amount"
                  nameKey="description"
                  label={({ description, amount }) => `₹${amount}`}
                >
                  {((monthlySummary as any)?.individual_expenses || []).map((entry: any, index: number) => (
                    <Cell key={`cell-${index}`} fill={[
                      '#667eea', '#764ba2', '#e74c3c', '#2ecc71', '#f1c40f', '#9b59b6', '#34495e', '#1abc9c', '#e67e22',
                      '#ff9f43', '#00d2d3', '#54a0ff', '#5f27cd', '#c8d6e5', '#222f3e', '#10ac84', '#ee5253', '#0abde3'
                    ][index % 18]} />
                  ))}
                </Pie>
                <Tooltip 
                  content={({ active, payload }) => {
                    if (active && payload && payload.length) {
                      const data = payload[0].payload;
                      const cat = EXPENSE_CATEGORIES.find(c => c.value === data.category);
                      return (
                        <div style={{ background: 'white', padding: '10px', border: '1px solid #ccc', borderRadius: '8px', boxShadow: '0 4px 12px rgba(0,0,0,0.1)' }}>
                          <p style={{ margin: 0, fontWeight: 'bold', color: '#764ba2' }}>{data.date}</p>
                          <p style={{ margin: '4px 0', fontSize: '1.1rem', fontWeight: 'bold' }}>₹{data.amount}</p>
                          <p style={{ margin: 0, color: '#333' }}>{cat?.icon} {data.description}</p>
                          <p style={{ margin: 0, color: '#666', fontSize: '0.8rem' }}>Category: {cat?.label || data.category}</p>
                        </div>
                      );
                    }
                    return null;
                  }}
                />
              </PieChart>
            </ResponsiveContainer>
          </div>
          <div className="info-sub" style={{ textAlign: 'center' }}>Each slice represents a unique withdrawal or expense</div>
        </div>

        {/* Savings Wallet Card */}
        <div className="balance-card" style={{ background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)' }}>
          <h2 style={{ color: 'white' }}>Savings Wallet 💎</h2>
          <div className="balance-amount" style={{ color: 'white' }}>
            ₹{parseFloat(wallet?.current_savings || '0').toFixed(2)}
          </div>
          <div className="additional-balance" style={{ borderTopColor: 'rgba(255,255,255,0.2)' }}>
            <div className="balance-item">
              <span className="label" style={{ color: 'rgba(255,255,255,0.8)' }}>Total Saved</span>
              <span className="amount" style={{ color: '#90EE90' }}>₹{parseFloat(wallet?.current_savings || '0').toFixed(2)}</span>
            </div>
            <div className="balance-item">
              <span className="label" style={{ color: 'rgba(255,255,255,0.8)' }}>Savings Goal</span>
              <span className="amount" style={{ color: '#FFB6C1' }}>₹{parseFloat(wallet?.savings_goal || '0').toFixed(2)}</span>
            </div>
          </div>
          <div style={{ marginTop: '1rem', display: 'flex', gap: '0.5rem', justifyContent: 'center' }}>
            <button 
              onClick={() => openModal('transfer')} 
              className="submit-btn" 
              style={{ flex: 1, background: 'white', color: '#667eea' }}
            >
              Transfer to Savings
            </button>
            <button 
              onClick={() => openModal('withdraw_savings')} 
              className="submit-btn" 
              style={{ flex: 1, background: '#764ba2', color: 'white', border: '1px solid white' }}
            >
              Withdraw from Savings
            </button>
          </div>
        </div>

        {/* Quick Actions */}
        <div className="transaction-card">
          <h3 style={{ marginBottom: '1rem', color: 'var(--text-primary)' }}>Quick Actions</h3>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '1rem' }}>
            <button 
              onClick={() => { setShowExpenseModal(true); setSuccess(''); setTxError(''); }}
              className="submit-btn"
            >
              📝 Record Expense
            </button>
            <button 
              onClick={() => { setShowStatementModal(true); }}
              className="submit-btn"
              style={{ background: '#764ba2' }}
            >
              📄 View Statement
            </button>
            <button 
              onClick={() => { loadAllData(); }}
              className="submit-btn"
              style={{ background: 'var(--primary-color)' }}
            >
              🔄 Refresh Data
            </button>
          </div>
        </div>

        {/* Recent Expenses */}
        <div className="transaction-history">
          <h3>Today's Expenses</h3>
          {todaySpending?.expenses?.length === 0 ? (
            <div className="no-transactions">No expenses recorded today</div>
          ) : (
            <div className="transaction-list">
              {todaySpending?.expenses?.map(expense => (
                <div key={expense.id} className="transaction-item">
                  <div className="transaction-info">
                    <span className="transaction-type">
                      {EXPENSE_CATEGORIES.find(c => c.value === expense.category)?.icon || '📦'} {' '}
                      {EXPENSE_CATEGORIES.find(c => c.value === expense.category)?.label || expense.category}
                    </span>
                    {expense.description && (
                      <span style={{ fontSize: '0.8rem', color: '#666' }}>{expense.description}</span>
                    )}
                  </div>
                  <span className="transaction-amount debit">₹{expense.amount}</span>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Investment Suggestions */}
        {monthlySummary?.investment_suggestions && monthlySummary.investment_suggestions.length > 0 && (
          <div className="transaction-card" style={{ marginTop: '2rem' }}>
            <h3 style={{ marginBottom: '1.5rem', color: '#764ba2', display: 'flex', alignItems: 'center', gap: '8px' }}>
              💡 Smart Investment Suggestions
            </h3>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr', gap: '1.5rem' }}>
              {monthlySummary.investment_suggestions.map(plan => (
                <div 
                  key={plan.id} 
                  style={{ 
                    padding: '1.5rem', 
                    borderRadius: '12px', 
                    border: '1px solid #e0e0e0',
                    background: '#fff',
                    boxShadow: '0 2px 8px rgba(0,0,0,0.05)'
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
                    <h4 style={{ margin: 0, color: '#333', fontSize: '1.2rem' }}>{plan.title}</h4>
                    <span style={{ 
                      padding: '4px 12px', 
                      borderRadius: '20px', 
                      background: '#f0f0ff', 
                      color: '#667eea',
                      fontSize: '0.8rem',
                      fontWeight: 'bold'
                    }}>
                      {plan.plan_type}
                    </span>
                  </div>
                  <p style={{ color: '#666', fontSize: '0.95rem', marginBottom: '1rem', lineHeight: '1.4' }}>
                    {plan.description}
                  </p>
                  <div style={{ background: '#f9f9f9', padding: '1rem', borderRadius: '8px', marginBottom: '1rem' }}>
                    <div style={{ fontSize: '0.85rem', fontWeight: 'bold', color: '#555', marginBottom: '4px' }}>Benefits:</div>
                    <div style={{ fontSize: '0.9rem', color: '#666' }}>{plan.benefits}</div>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <div style={{ fontSize: '0.85rem', color: '#999' }}>
                      Min: <span style={{ color: '#333', fontWeight: 'bold' }}>₹{parseFloat(plan.minimum_investment).toFixed(2)}</span>
                    </div>
                    <button 
                      onClick={() => alert(`Analysis: ${plan.current_scenario_analysis}`)}
                      style={{
                        padding: '6px 16px',
                        background: '#667eea',
                        color: 'white',
                        border: 'none',
                        borderRadius: '6px',
                        cursor: 'pointer',
                        fontSize: '0.9rem'
                      }}
                    >
                      View Analysis
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

      </main>

      {/* Deposit Modal */}
      {showDepositModal && (
        <div className="modal-overlay" onClick={() => setShowDepositModal(false)}>
          <div className="modal" onClick={e => e.stopPropagation()}>
            <h2>Deposit to Main Wallet</h2>
            <p style={{ color: '#666', marginBottom: '1rem', fontSize: '0.9rem' }}>Direct deposit - no OTP required</p>
            {txError && <div className="error-message">{txError}</div>}
            {success && <div className="success-message">{success}</div>}
            <form onSubmit={handleSubmit}>
              <div className="form-group">
                <label>Amount</label>
                <input
                  type="number"
                  value={amount}
                  onChange={e => setAmount(e.target.value)}
                  placeholder="Enter amount"
                  min="1"
                  required
                />
              </div>
              <div className="form-group">
                <label>Description (Optional)</label>
                <input
                  type="text"
                  value={description}
                  onChange={e => setDescription(e.target.value)}
                  placeholder="Enter description"
                />
              </div>
              <button type="submit" disabled={processing} className="submit-btn">
                {processing ? 'Processing...' : 'Deposit'}
              </button>
              <button 
                type="button" 
                onClick={() => setShowDepositModal(false)} 
                className="cancel-btn"
                style={{ width: '100%', marginTop: '0.5rem' }}
              >
                Cancel
              </button>
            </form>
          </div>
        </div>
      )}

      {/* Withdraw Modal */}
      {showWithdrawModal && (
        <div className="modal-overlay" onClick={() => setShowWithdrawModal(false)}>
          <div className="modal" onClick={e => e.stopPropagation()}>
            <h2>Withdraw from Main Wallet</h2>
            <p style={{ color: '#666', marginBottom: '1rem', fontSize: '0.9rem' }}>Direct withdrawal - no OTP required</p>
            {txError && <div className="error-message">{txError}</div>}
            {success && <div className="success-message">{success}</div>}
            <form onSubmit={handleSubmit}>
              <div className="form-group">
                <label>Amount</label>
                <input
                  type="number"
                  value={amount}
                  onChange={e => setAmount(e.target.value)}
                  placeholder="Enter amount"
                  min="1"
                  max={parseFloat(wallet?.balance || '0')}
                  required
                />
              </div>
              <div className="form-group" style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '1rem' }}>
                <input
                  type="checkbox"
                  id="isExpense"
                  checked={isExpense}
                  onChange={e => setIsExpense(e.target.checked)}
                  style={{ width: '18px', height: '18px', margin: 0 }}
                />
                <label htmlFor="isExpense" style={{ margin: 0, fontWeight: 'normal', cursor: 'pointer' }}>
                  Is this an expense? (Track in charts)
                </label>
              </div>

              {isExpense && (
                <div className="form-group">
                  <label>Category</label>
                  <select value={category} onChange={e => setCategory(e.target.value)}>
                    {EXPENSE_CATEGORIES.map(cat => (
                      <option key={cat.value} value={cat.value}>
                        {cat.icon} {cat.label}
                      </option>
                    ))}
                  </select>
                </div>
              )}

              <div className="form-group">
                <label>Description (Optional)</label>
                <input
                  type="text"
                  value={description}
                  onChange={e => setDescription(e.target.value)}
                  placeholder="Enter description"
                />
              </div>
              <button type="submit" disabled={processing} className="submit-btn">
                {processing ? 'Processing...' : 'Withdraw'}
              </button>
              <button 
                type="button" 
                onClick={() => setShowWithdrawModal(false)} 
                className="cancel-btn"
                style={{ width: '100%', marginTop: '0.5rem' }}
              >
                Cancel
              </button>
            </form>
          </div>
        </div>
      )}

      {/* Transfer to Savings Modal */}
      {showTransferModal && (
        <div className="modal-overlay" onClick={() => setShowTransferModal(false)}>
          <div className="modal" onClick={e => e.stopPropagation()}>
            <h2>Transfer to Savings 💎</h2>
            <div style={{ 
              background: '#f0f7ff', 
              padding: '1rem', 
              borderRadius: '12px', 
              marginBottom: '1.5rem',
              border: '1px solid #cce5ff',
              textAlign: 'center'
            }}>
              <span style={{ color: '#004a99', fontSize: '0.9rem', display: 'block', marginBottom: '4px' }}>Available in Main Wallet</span>
              <span style={{ color: '#004a99', fontSize: '1.4rem', fontWeight: 'bold' }}>₹{parseFloat(wallet?.balance || '0').toFixed(2)}</span>
            </div>
            
            {txError && <div className="error-message">{txError}</div>}
            {success && <div className="success-message">{success}</div>}
            
            <form onSubmit={handleSubmit}>
              <div className="form-group">
                <label>Amount to Transfer</label>
                <input
                  type="number"
                  value={amount}
                  onChange={e => setAmount(e.target.value)}
                  placeholder="Enter amount"
                  min="1"
                  max={parseFloat(wallet?.balance || '0')}
                  required
                />
              </div>
              
              {otpRequestId && (
                <div className="form-group">
                  <label>Verification OTP</label>
                  <input
                    type="text"
                    value={otp}
                    onChange={e => setOtp(e.target.value)}
                    placeholder="Enter 6-digit OTP"
                    maxLength={6}
                    required
                    style={{ textAlign: 'center', fontSize: '1.2rem', letterSpacing: '4px' }}
                  />
                </div>
              )}
              
              <button type="submit" disabled={processing} className="submit-btn">
                {processing ? 'Processing...' : otpRequestId ? 'Verify & Transfer' : 'Generate OTP'}
              </button>
              
              <button 
                type="button" 
                onClick={() => setShowTransferModal(false)} 
                className="cancel-btn"
              >
                Cancel
              </button>
            </form>
          </div>
        </div>
      )}

      {/* Withdraw from Savings Modal */}
      {showSavingsWithdrawModal && (
        <div className="modal-overlay" onClick={() => setShowSavingsWithdrawModal(false)}>
          <div className="modal" onClick={e => e.stopPropagation()}>
            <h2>Withdraw from Savings 💎</h2>
            <div style={{ 
              background: '#fff0f0', 
              padding: '1rem', 
              borderRadius: '12px', 
              marginBottom: '1.5rem',
              border: '1px solid #ffcccc',
              textAlign: 'center'
            }}>
              <span style={{ color: '#e74c3c', fontSize: '0.9rem', display: 'block', marginBottom: '4px' }}>Current Savings Balance</span>
              <span style={{ color: '#e74c3c', fontSize: '1.4rem', fontWeight: 'bold' }}>₹{parseFloat(wallet?.current_savings || '0').toFixed(2)}</span>
            </div>

            {txError && <div className="error-message">{txError}</div>}
            {success && <div className="success-message">{success}</div>}
            
            <form onSubmit={handleSubmit}>
              <div className="form-group">
                <label>Amount to Withdraw</label>
                <input
                  type="number"
                  value={amount}
                  onChange={e => setAmount(e.target.value)}
                  placeholder="Enter amount"
                  min="1"
                  max={parseFloat(wallet?.current_savings || '0')}
                  required
                />
              </div>
              
              <div className="form-group" style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '1rem' }}>
                <input
                  type="checkbox"
                  id="isSavingsExpense"
                  checked={isExpense}
                  onChange={e => setIsExpense(e.target.checked)}
                  style={{ width: '18px', height: '18px', margin: 0 }}
                />
                <label htmlFor="isSavingsExpense" style={{ margin: 0, fontWeight: 'normal', cursor: 'pointer' }}>
                  Is this an expense? (Track in charts)
                </label>
              </div>

              {isExpense && (
                <div className="form-group">
                  <label>Category</label>
                  <select value={category} onChange={e => setCategory(e.target.value)}>
                    {EXPENSE_CATEGORIES.map(cat => (
                      <option key={cat.value} value={cat.value}>
                        {cat.icon} {cat.label}
                      </option>
                    ))}
                  </select>
                </div>
              )}

              <div className="form-group">
                <label>Description (Optional)</label>
                <input
                  type="text"
                  value={description}
                  onChange={e => setDescription(e.target.value)}
                  placeholder="What is this withdrawal for?"
                />
              </div>
              
              {otpRequestId && (
                <div className="form-group">
                  <label>Verification OTP</label>
                  <input
                    type="text"
                    value={otp}
                    onChange={e => setOtp(e.target.value)}
                    placeholder="Enter 6-digit OTP"
                    maxLength={6}
                    required
                    style={{ textAlign: 'center', fontSize: '1.2rem', letterSpacing: '4px' }}
                  />
                </div>
              )}
              
              <button type="submit" disabled={processing} className="submit-btn">
                {processing ? 'Processing...' : otpRequestId ? 'Verify & Withdraw' : 'Generate OTP'}
              </button>
              
              <button 
                type="button" 
                onClick={() => setShowSavingsWithdrawModal(false)} 
                className="cancel-btn"
              >
                Cancel
              </button>
            </form>
          </div>
        </div>
      )}

      {/* Settings Modal */}
      {showSettingsModal && (
        <div className="modal-overlay" onClick={() => setShowSettingsModal(false)}>
          <div className="modal" onClick={e => e.stopPropagation()}>
            <h2>Set Budget & Savings Goal</h2>
            <p style={{ color: '#666', marginBottom: '1rem', fontSize: '0.9rem' }}>
              Current: Budget ₹{parseFloat(wallet?.monthly_budget || '0').toFixed(2)} | Goal ₹{parseFloat(wallet?.savings_goal || '0').toFixed(2)}
            </p>
            {txError && <div className="error-message">{txError}</div>}
            {success && <div className="success-message">{success}</div>}
            <div className="form-group">
              <label>Monthly Budget (₹)</label>
              <input
                type="number"
                value={budgetAmount}
                onChange={e => setBudgetAmount(e.target.value)}
                placeholder="Enter monthly budget"
                min="0"
              />
            </div>
            <div className="form-group">
              <label>Savings Goal (₹)</label>
              <input
                type="number"
                value={savingsGoalAmount}
                onChange={e => setSavingsGoalAmount(e.target.value)}
                placeholder="Enter savings goal"
                min="0"
              />
            </div>
            <button 
              onClick={handleSaveSettings} 
              disabled={savingSettings || (!budgetAmount && !savingsGoalAmount)}
              className="submit-btn"
            >
              {savingSettings ? 'Saving...' : 'Save Settings'}
            </button>
            <button 
              type="button" 
              onClick={() => setShowSettingsModal(false)} 
              className="cancel-btn"
              style={{ width: '100%', marginTop: '0.5rem' }}
            >
              Cancel
            </button>
          </div>
        </div>
      )}

      {/* Expense Modal */}
      {showExpenseModal && (
        <div className="modal-overlay" onClick={() => setShowExpenseModal(false)}>
          <div className="modal" onClick={e => e.stopPropagation()}>
            <h2>Record Expense</h2>
            {txError && <div className="error-message">{txError}</div>}
            {success && <div className="success-message">{success}</div>}
            <form onSubmit={handleRecordExpense}>
              <div className="form-group">
                <label>Amount</label>
                <input
                  type="number"
                  value={amount}
                  onChange={e => setAmount(e.target.value)}
                  placeholder="Enter amount"
                  min="1"
                  required
                />
              </div>
              <div className="form-group">
                <label>Category</label>
                <select value={category} onChange={e => setCategory(e.target.value)}>
                  {EXPENSE_CATEGORIES.map(cat => (
                    <option key={cat.value} value={cat.value}>
                      {cat.icon} {cat.label}
                    </option>
                  ))}
                </select>
              </div>
              <div className="form-group">
                <label>Description (Optional)</label>
                <input
                  type="text"
                  value={description}
                  onChange={e => setDescription(e.target.value)}
                  placeholder="Enter description"
                />
              </div>
              <button type="submit" disabled={processing} className="submit-btn">
                {processing ? 'Processing...' : 'Record Expense'}
              </button>
              <button 
                type="button" 
                onClick={() => setShowExpenseModal(false)} 
                className="cancel-btn"
                style={{ width: '100%', marginTop: '0.5rem' }}
              >
                Cancel
              </button>
            </form>
          </div>
        </div>
      )}

      {/* Transaction Statement Modal */}
      {showStatementModal && (
        <div className="modal-overlay" onClick={() => setShowStatementModal(false)}>
          <div className="modal" style={{ maxWidth: '800px', width: '95%' }} onClick={e => e.stopPropagation()}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
              <h2 style={{ margin: 0 }}>Transaction Statement 📜</h2>
              <button onClick={() => setShowStatementModal(false)} style={{ background: 'none', border: 'none', fontSize: '1.5rem', cursor: 'pointer' }}>✕</button>
            </div>

            {/* Filters */}
            <div style={{ 
              display: 'grid', 
              gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', 
              gap: '1rem', 
              marginBottom: '1.5rem',
              background: '#f8f9fa',
              padding: '1rem',
              borderRadius: '8px'
            }}>
              <div className="form-group" style={{ marginBottom: 0 }}>
                <label>Year</label>
                <select value={filterYear} onChange={e => setYear(parseInt(e.target.value))}>
                  {[2024, 2025, 2026].map(y => <option key={y} value={y}>{y}</option>)}
                </select>
              </div>
              <div className="form-group" style={{ marginBottom: 0 }}>
                <label>Month</label>
                <select value={filterMonth} onChange={e => setMonth(parseInt(e.target.value))}>
                  {['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'].map((m, i) => (
                    <option key={m} value={i + 1}>{m}</option>
                  ))}
                </select>
              </div>
              <div className="form-group" style={{ marginBottom: 0 }}>
                <label>Specific Date (Optional)</label>
                <input 
                  type="number" 
                  min="1" 
                  max="31" 
                  value={filterDay} 
                  onChange={e => setDay(e.target.value)} 
                  placeholder="DD"
                />
              </div>
            </div>

            {/* Statement Table */}
            <div style={{ maxHeight: '400px', overflowY: 'auto', border: '1px solid #eee', borderRadius: '8px' }}>
              {loadingStatement ? (
                <div style={{ padding: '2rem', textAlign: 'center' }}>Loading transactions...</div>
              ) : statementData.length === 0 ? (
                <div style={{ padding: '2rem', textAlign: 'center', color: '#999' }}>No transactions found for this period</div>
              ) : (
                <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left' }}>
                  <thead style={{ position: 'sticky', top: 0, background: '#f0f0f0', zIndex: 1 }}>
                    <tr>
                      <th style={{ padding: '12px', borderBottom: '2px solid #ddd' }}>Date</th>
                      <th style={{ padding: '12px', borderBottom: '2px solid #ddd' }}>Description</th>
                      <th style={{ padding: '12px', borderBottom: '2px solid #ddd' }}>Type</th>
                      <th style={{ padding: '12px', borderBottom: '2px solid #ddd', textAlign: 'right' }}>Amount</th>
                    </tr>
                  </thead>
                  <tbody>
                    {statementData.map((tx: any) => (
                      <tr key={tx.id} style={{ borderBottom: '1px solid #eee' }}>
                        <td style={{ padding: '12px', fontSize: '0.9rem' }}>
                          {new Date(tx.created_at).toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' })}
                        </td>
                        <td style={{ padding: '12px' }}>
                          <div style={{ fontWeight: '500' }}>{tx.description}</div>
                          <div style={{ fontSize: '0.75rem', color: '#999' }}>Balance after: ₹{parseFloat(tx.balance_after).toFixed(2)}</div>
                        </td>
                        <td style={{ padding: '12px' }}>
                          <span style={{ 
                            padding: '2px 8px', 
                            borderRadius: '4px', 
                            fontSize: '0.75rem', 
                            fontWeight: 'bold',
                            background: tx.transaction_type === 'DEPOSIT' ? '#e8f5e9' : '#ffebee',
                            color: tx.transaction_type === 'DEPOSIT' ? '#2e7d32' : '#c62828'
                          }}>
                            {tx.transaction_type}
                          </span>
                        </td>
                        <td style={{ padding: '12px', textAlign: 'right', fontWeight: 'bold', color: tx.transaction_type === 'DEPOSIT' ? '#2e7d32' : '#c62828' }}>
                          {tx.transaction_type === 'DEPOSIT' ? '+' : '-'}₹{parseFloat(tx.amount).toFixed(2)}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>

            <div style={{ marginTop: '1.5rem', display: 'flex', justifyContent: 'flex-end' }}>
              <button 
                onClick={() => window.print()} 
                className="submit-btn" 
                style={{ width: 'auto', padding: '0.5rem 1.5rem', background: '#333' }}
              >
                🖨️ Print Statement
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
