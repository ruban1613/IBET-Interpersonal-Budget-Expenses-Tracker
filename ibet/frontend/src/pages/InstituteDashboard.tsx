import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../services/api';
import './Dashboard.css';

export default function InstituteDashboard() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [userProfile, setUserProfile] = useState<any>(null);
  const [role, setRole] = useState<'OWNER' | 'TEACHER' | 'STUDENT' | null>(null);
  const [dashboardData, setDashboardData] = useState<any>(null);
  const [activeTab, setActiveTab] = useState('overview');

  // Owner specific states
  const [students, setStudents] = useState<any[]>([]);
  const [teachers, setTeachers] = useState<any[]>([]);
  const [showAddStudent, setShowAddStudent] = useState(false);
  const [showAddTeacher, setShowAddTeacher] = useState(false);
  const [showEditTeacher, setShowEditTeacher] = useState(false);
  const [showMarkPaid, setShowMarkPaid] = useState(false);
  const [showNoticeModal, setShowNoticeModal] = useState(false);
  const [showCreateInstitute, setShowCreateInstitute] = useState(false);
  
  // Attendance States
  const [attendanceDate, setAttendanceDate] = useState(new Date().toISOString().split('T')[0]);
  const [attendanceRecords, setAttendanceRecords] = useState<{[key: number]: string}>({});
  const [attendanceReport, setAttendanceReport] = useState<any[]>([]);
  const [teacherAttendanceReport, setTeacherAttendanceReport] = useState<any[]>([]);
  const [attendanceSubTab, setAttendanceSubTab] = useState<'students' | 'teachers'>('students');
  const [attendanceMode, setAttendanceMode] = useState<'mark' | 'report'>('report');
  const [reportMonth, setReportMonth] = useState(new Date().getMonth() + 1);
  const [reportYear, setReportYear] = useState(new Date().getFullYear());

  // Dynamic Payroll States
  const [showAttendanceModal, setShowAttendanceModal] = useState(false);
  const [showPayrollModal, setShowPayrollModal] = useState(false);
  const [selectedTeacher, setSelectedTeacher] = useState<any>(null);
  const [teacherAttendanceData, setTeacherAttendanceData] = useState({ 
    date: new Date().toISOString().split('T')[0], 
    status: 'PRESENT', 
    extra_sessions: 0, 
    remarks: '' 
  });
  const [payrollResult, setPayrollResult] = useState<any>(null);
  const [editTeacherData, setEditTeacherData] = useState({ 
    base_monthly_salary: 0, 
    working_days_per_month: 26, 
    extra_session_rate: 500 
  });

  // Notice State
  const [noticeMessage, setNoticeMessage] = useState('');
  const [selectedStudentForNotice, setSelectedStudentForNotice] = useState<any>(null);

  // Form states
  const [newInstitute, setNewInstitute] = useState({ name: '', address: '', contact_number: '' });
  const [newStudent, setNewStudent] = useState({ student_name: '', parent_mobile: '', monthly_fee: '', due_day: '5', institute: '' });
  const [newTeacher, setNewTeacher] = useState({ username: '', base_monthly_salary: 0, working_days_per_month: 26, extra_session_rate: 500, institute: '' });
  const [paymentData, setPaymentData] = useState({ student_profile: '', month: new Date().getMonth() + 1, year: new Date().getFullYear(), amount: '' });

  useEffect(() => {
    loadDashboard();
  }, []);

  useEffect(() => {
    if (activeTab === 'attendance' || activeTab === 'report') {
      fetchAttendanceReport();
    }
  }, [activeTab, reportMonth, reportYear, attendanceSubTab]);

  const loadDashboard = async () => {
    setLoading(true);
    setError('');
    try {
      const [data, profileData] = await Promise.all([
        api.getInstituteDashboard(),
        api.getProfile()
      ]);
      setRole(data.role);
      setDashboardData(data);
      setUserProfile(profileData);
      
      if (data.role === 'OWNER' || data.role === 'TEACHER') {
        const [studentList, teacherList] = await Promise.all([
          api.getInstituteStudents(),
          api.getInstituteTeachers()
        ]);
        const sList = Array.isArray(studentList) ? studentList : (studentList.results || []);
        setStudents(sList);
        setTeachers(Array.isArray(teacherList) ? teacherList : (teacherList.results || []));

        const initial: any = {};
        sList.forEach((s: any) => { initial[s.id] = 'PRESENT'; });
        setAttendanceRecords(initial);

        if (data.institutes && data.institutes.length > 0) {
          const instId = data.institutes[0].id;
          setNewStudent(prev => ({ ...prev, institute: instId }));
          setNewTeacher(prev => ({ ...prev, institute: instId }));
        }
      }
    } catch (err: any) {
      setError(err.message || 'Failed to load dashboard');
    } finally {
      setLoading(false);
    }
  };

  const fetchAttendanceReport = async () => {
    try {
      if (role === 'TEACHER' || (role === 'OWNER' && attendanceSubTab === 'students')) {
        const data: any = await api.request(`/institute/attendance/?month=${reportMonth}&year=${reportYear}`);
        setAttendanceReport(Array.isArray(data) ? data : (data.results || []));
      } else if (role === 'OWNER' && attendanceSubTab === 'teachers') {
        const data: any = await api.getTeacherAttendance(undefined, reportMonth, reportYear);
        setTeacherAttendanceReport(Array.isArray(data) ? data : (data.results || []));
      }
    } catch (err) { console.error(err); }
  };

  const handleMarkBulkAttendance = async () => {
    try {
      const records = Object.entries(attendanceRecords).map(([id, status]) => ({
        student_profile: parseInt(id),
        status: status
      }));
      await api.markAttendanceBulk(attendanceDate, records);
      setSuccess('Attendance marked successfully!');
      setAttendanceMode('report');
      fetchAttendanceReport();
    } catch (err: any) { setError(err.message); }
  };

  const handleCreateInstitute = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await api.createInstitute(newInstitute);
      setSuccess('Institute created successfully!');
      setShowCreateInstitute(false);
      loadDashboard();
    } catch (err: any) { setError(err.message); }
  };

  const handleUnlinkStudent = async (id: number) => {
    if (!confirm('Are you sure you want to remove this student?')) return;
    try {
      await api.deleteInstituteStudent(id);
      setSuccess('Student removed successfully!');
      loadDashboard();
    } catch (err: any) { setError(err.message); }
  };

  const handleSendNotice = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedStudentForNotice) return;
    try {
      await api.sendInstituteNotice(selectedStudentForNotice.id, noticeMessage);
      setSuccess(`Notice sent to ${selectedStudentForNotice.student_name}`);
      setShowNoticeModal(false);
      setNoticeMessage('');
    } catch (err: any) { setError(err.message); }
  };

  const handleMarkTeacherAttendance = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedTeacher) return;
    try {
      await api.markTeacherAttendance({
        teacher: selectedTeacher.id,
        ...teacherAttendanceData
      });
      setSuccess('Teacher attendance marked!');
      setShowAttendanceModal(false);
      loadDashboard();
    } catch (err: any) { setError(err.message); }
  };

  const handleCalculatePayroll = async (teacherId: number) => {
    try {
      const now = new Date();
      const res = await api.calculateTeacherPayout(teacherId, now.getMonth() + 1, now.getFullYear());
      setPayrollResult(res);
      setShowPayrollModal(true);
    } catch (err: any) { setError(err.message); }
  };

  const handleUpdateTeacher = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedTeacher) return;
    try {
      await api.updateTeacherProfile(selectedTeacher.id, editTeacherData);
      setSuccess('Teacher profile updated!');
      setShowEditTeacher(false);
      loadDashboard();
    } catch (err: any) { setError(err.message); }
  };

  const handleAddStudent = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const res = await api.createInstituteStudent(newStudent);
      setSuccess(`${res.message}. Username: ${res.username}`);
      setShowAddStudent(false);
      loadDashboard();
    } catch (err: any) { setError(err.message); }
  };

  const handleAddTeacher = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await api.createInstituteTeacher(newTeacher);
      setSuccess('Teacher linked successfully!');
      setShowAddTeacher(false);
      loadDashboard();
    } catch (err: any) { setError(err.message); }
  };

  const handleMarkSalaryPaid = async () => {
    try {
      await api.markSalaryAsPaid({
        teacher_profile: teachers.find(t => t.user_details.username === payrollResult.teacher_name).id,
        month: new Date().getMonth() + 1,
        year: new Date().getFullYear(),
        amount: payrollResult.net_payout
      });
      setSuccess('Salary payout recorded!');
      setShowPayrollModal(false);
      loadDashboard();
    } catch (err: any) { setError(err.message); }
  };

  const handleLogout = () => { api.clearToken(); navigate('/login'); };

  if (loading) return <div className="loading">Loading Institute Dashboard...</div>;

  const getDaysInMonth = (m: number, y: number) => new Date(y, m, 0).getDate();

  return (
    <div className="dashboard-container">
      <header className="dashboard-header">
        <button onClick={() => navigate('/select-module')} className="back-btn">← Back</button>
        <h1>Institute Management 🏫 {userProfile?.uid && <span style={{ fontSize: '0.9rem', color: '#3498db', background: 'white', padding: '2px 8px', borderRadius: '4px', marginLeft: '10px', verticalAlign: 'middle' }}>{userProfile.uid}</span>}</h1>
        <button onClick={handleLogout} className="logout-btn">Logout</button>
      </header>

      {dashboardData.institutes?.[0] && (
        <div style={{ background: 'rgba(0,0,0,0.05)', padding: '10px 20px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid #eee' }}>
          <div>
            <span style={{ fontWeight: 'bold', fontSize: '1.1rem' }}>📍 {dashboardData.institutes[0].name}</span>
            <span style={{ marginLeft: '15px', color: '#666', fontSize: '0.9rem' }}>{dashboardData.institutes[0].address}</span>
          </div>
          <div style={{ fontSize: '0.85rem', color: '#3498db' }}>Account: <strong>{userProfile?.username}</strong> ({role})</div>
        </div>
      )}

      <main className="dashboard-main">
        {error && <div className="error-message">{error}</div>}
        {success && <div className="success-message">{success}</div>}

        {role === 'OWNER' && (
          <>
            <div className="stats-grid">
              <div className="info-card"><h3>👥 Students</h3><div className="info-value">{dashboardData.stats.total_students}</div></div>
              <div className="info-card"><h3>👩‍🏫 Teachers</h3><div className="info-value">{dashboardData.stats.total_teachers}</div></div>
              <div className="info-card"><h3>💰 Revenue (MTD)</h3><div className="info-value" style={{ color: '#2ecc71' }}>₹{dashboardData.stats.monthly_revenue.toFixed(2)}</div></div>
              <div className="info-card"><h3>📈 Attendance</h3><div className="info-value" style={{ color: '#f39c12' }}>{dashboardData.stats.today_attendance?.present || 0} Present</div></div>
            </div>

            <div className="tab-navigation">
              <button className={`tab-btn ${activeTab === 'overview' ? 'active' : ''}`} onClick={() => setActiveTab('overview')}>Overview</button>
              <button className={`tab-btn ${activeTab === 'attendance' ? 'active' : ''}`} onClick={() => setActiveTab('attendance')}>Attendance</button>
              <button className={`tab-btn ${activeTab === 'students' ? 'active' : ''}`} onClick={() => setActiveTab('students')}>Students</button>
              <button className={`tab-btn ${activeTab === 'teachers' ? 'active' : ''}`} onClick={() => setActiveTab('teachers')}>Teachers</button>
              <button className={`tab-btn ${activeTab === 'transactions' ? 'active' : ''}`} onClick={() => setActiveTab('transactions')}>Transactions</button>
            </div>

            {activeTab === 'overview' && (
              <div className="quick-actions-card info-card">
                <h3>Quick Management</h3>
                <div style={{ display: 'flex', gap: '1rem', marginTop: '1rem', flexWrap: 'wrap' }}>
                  <button className="submit-btn" style={{ flex: 1, background: '#3498db' }} onClick={() => setShowCreateInstitute(true)}>🏫 New Institute</button>
                  <button className="submit-btn" style={{ flex: 1 }} onClick={() => setShowAddStudent(true)}>➕ Add Student</button>
                  <button className="submit-btn" style={{ flex: 1 }} onClick={() => setShowAddTeacher(true)}>➕ Add Teacher</button>
                  <button className="submit-btn" style={{ flex: 1, background: '#e67e22' }} onClick={() => setShowMarkPaid(true)}>📝 Record Fee</button>
                </div>
              </div>
            )}

            {activeTab === 'attendance' && (
              <div className="info-card" style={{ overflowX: 'auto' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem', flexWrap: 'wrap', gap: '1rem' }}>
                  <div style={{ display: 'flex', gap: '10px', background: '#f0f2f5', padding: '4px', borderRadius: '8px' }}>
                    <button 
                      className={`tab-btn ${attendanceSubTab === 'students' ? 'active' : ''}`} 
                      style={{ padding: '6px 15px', fontSize: '0.85rem' }}
                      onClick={() => setAttendanceSubTab('students')}
                    >Students</button>
                    <button 
                      className={`tab-btn ${attendanceSubTab === 'teachers' ? 'active' : ''}`} 
                      style={{ padding: '6px 15px', fontSize: '0.85rem' }}
                      onClick={() => setAttendanceSubTab('teachers')}
                    >Teachers</button>
                  </div>
                  
                  <div style={{ display: 'flex', gap: '10px' }}>
                    <select value={reportMonth} onChange={e => setReportMonth(parseInt(e.target.value))}>
                      {['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'].map((m, i) => <option key={m} value={i+1}>{m}</option>)}
                    </select>
                    <select value={reportYear} onChange={e => setReportYear(parseInt(e.target.value))}>
                      {[2025, 2026, 2027].map(y => <option key={y} value={y}>{y}</option>)}
                    </select>
                  </div>
                </div>

                <div className="table-container">
                  <table className="statement-table" style={{ fontSize: '0.75rem' }}>
                    <thead>
                      <tr>
                        <th style={{ minWidth: '150px' }}>{attendanceSubTab === 'students' ? 'Student Name' : 'Teacher Name'}</th>
                        {Array.from({ length: getDaysInMonth(reportMonth, reportYear) }, (_, i) => (
                          <th key={i+1} style={{ textAlign: 'center', padding: '4px' }}>{i+1}</th>
                        ))}
                        <th style={{ background: '#f9f9f9', textAlign: 'center' }}>Total</th>
                      </tr>
                    </thead>
                    <tbody>
                      {attendanceSubTab === 'students' ? (
                        students.map(s => {
                          let presentCount = 0;
                          return (
                            <tr key={s.id}>
                              <td><strong>{s.student_name}</strong></td>
                              {Array.from({ length: getDaysInMonth(reportMonth, reportYear) }, (_, i) => {
                                const day = i + 1;
                                const dateStr = `${reportYear}-${String(reportMonth).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
                                const record = attendanceReport.find(r => r.student_profile === s.id && r.date === dateStr);
                                let mark = '-'; let color = '#ccc';
                                if (record?.status === 'PRESENT') { mark = 'P'; color = '#27ae60'; presentCount++; }
                                else if (record?.status === 'ABSENT') { mark = 'A'; color = '#e74c3c'; }
                                else if (record?.status === 'LATE') { mark = 'L'; color = '#f39c12'; presentCount++; }
                                return <td key={day} style={{ textAlign: 'center', color, fontWeight: 'bold' }}>{mark}</td>;
                              })}
                              <td style={{ background: '#f9f9f9', textAlign: 'center', fontWeight: 'bold' }}>{presentCount}</td>
                            </tr>
                          );
                        })
                      ) : (
                        teachers.map(t => {
                          let presentCount = 0;
                          return (
                            <tr key={t.id}>
                              <td><strong>{t.user_details?.username}</strong></td>
                              {Array.from({ length: getDaysInMonth(reportMonth, reportYear) }, (_, i) => {
                                const day = i + 1;
                                const dateStr = `${reportYear}-${String(reportMonth).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
                                const record = teacherAttendanceReport.find(r => r.teacher === t.id && r.date === dateStr);
                                let mark = '-'; let color = '#ccc';
                                if (record?.status === 'PRESENT' || record?.status === 'OVERTIME') { mark = record.status === 'PRESENT' ? 'P' : 'OT'; color = '#27ae60'; presentCount++; }
                                else if (record?.status === 'ABSENT') { mark = 'A'; color = '#e74c3c'; }
                                else if (record?.status === 'HALF_DAY') { mark = 'H'; color = '#f39c12'; presentCount += 0.5; }
                                return <td key={day} style={{ textAlign: 'center', color, fontWeight: 'bold' }}>{mark}</td>;
                              })}
                              <td style={{ background: '#f9f9f9', textAlign: 'center', fontWeight: 'bold' }}>{presentCount}</td>
                            </tr>
                          );
                        })
                      )}
                    </tbody>
                  </table>
                </div>
                <div style={{ marginTop: '1rem', fontSize: '0.75rem', color: '#666', display: 'flex', gap: '15px' }}>
                  <span><strong>P</strong>: Present</span>
                  <span><strong>A</strong>: Absent</span>
                  <span><strong>L</strong>: Late</span>
                  {attendanceSubTab === 'teachers' && (
                    <>
                      <span><strong>H</strong>: Half Day</span>
                      <span><strong>OT</strong>: Overtime</span>
                    </>
                  )}
                </div>
              </div>
            )}

            {activeTab === 'students' && (
              <div className="info-card">
                <h3>Student Directory</h3>
                <div className="table-container" style={{ marginTop: '1rem' }}>
                  <table className="statement-table">
                    <thead><tr><th>Student Name</th><th>Monthly Fee</th><th>Due Day</th><th style={{ textAlign: 'right' }}>Actions</th></tr></thead>
                    <tbody>
                      {students.map(s => (
                        <tr key={s.id}>
                          <td><strong>{s.student_name}</strong></td>
                          <td>₹{parseFloat(s.monthly_fee).toFixed(2)}</td>
                          <td>{s.due_day}th</td>
                          <td style={{ textAlign: 'right' }}>
                            <button className="otp-btn-small" style={{ background: '#f39c12', marginRight: '5px' }} onClick={() => { setSelectedStudentForNotice(s); setShowNoticeModal(true); }}>📣 Notice</button>
                            <button className="otp-btn-small" style={{ background: '#e74c3c', marginRight: '5px' }} onClick={() => handleUnlinkStudent(s.id)}>🗑️ Unlink</button>
                            <button className="otp-btn-small" onClick={() => api.sendFeeReminder(s.id)}>🔔 Remind</button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {activeTab === 'teachers' && (
              <div className="info-card">
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
                  <h3>Teacher Payroll & Attendance</h3>
                  <button className="submit-btn" style={{ width: 'auto', padding: '0.5rem 1rem' }} onClick={() => setShowAddTeacher(true)}>+ Add Teacher</button>
                </div>
                <div className="table-container">
                  <table className="statement-table">
                    <thead><tr><th>Teacher</th><th>Base Salary</th><th>Daily Rate</th><th>Actions</th></tr></thead>
                    <tbody>
                      {teachers.map(t => (
                        <tr key={t.id}>
                          <td><strong>{t.user_details?.username}</strong></td>
                          <td>₹{parseFloat(t.base_monthly_salary).toFixed(2)}</td>
                          <td>₹{parseFloat(t.daily_rate).toFixed(2)}</td>
                          <td>
                            <div style={{ display: 'flex', gap: '8px' }}>
                              <button className="otp-btn-small" style={{ background: '#3498db' }} onClick={() => { 
                                setSelectedTeacher(t); 
                                setEditTeacherData({ 
                                  base_monthly_salary: parseFloat(t.base_monthly_salary), 
                                  working_days_per_month: t.working_days_per_month, 
                                  extra_session_rate: parseFloat(t.extra_session_rate) 
                                }); 
                                setShowEditTeacher(true); 
                              }}>✏️ Edit</button>
                              <button className="otp-btn-small" style={{ background: '#3498db' }} onClick={() => { setSelectedTeacher(t); setShowAttendanceModal(true); }}>📝 Attendance</button>
                              <button className="otp-btn-small" style={{ background: '#27ae60' }} onClick={() => handleCalculatePayroll(t.id)}>💵 Payroll</button>
                            </div>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {activeTab === 'transactions' && (
              <div className="info-card">
                <h3>Financial History</h3>
                <div className="table-container" style={{ marginTop: '1.5rem' }}>
                  <table className="statement-table">
                    <thead><tr><th>Date</th><th>Type</th><th>Name</th><th>Period</th><th>Amount</th></tr></thead>
                    <tbody>
                      {[
                        ...(dashboardData.recent_paid_fees || []).map((f: any) => ({ ...f, txType: 'COLLECTION', color: '#2ecc71' })),
                        ...(dashboardData.recent_paid_salaries || []).map((s: any) => ({ ...s, txType: 'PAYOUT', color: '#e74c3c' }))
                      ].sort((a, b) => new Date(b.payment_date || b.created_at).getTime() - new Date(a.payment_date || a.created_at).getTime()).map((tx, idx) => (
                        <tr key={idx}>
                          <td>{new Date(tx.payment_date || tx.created_at).toLocaleDateString()}</td>
                          <td><span className="tag" style={{ background: tx.color, color: 'white' }}>{tx.txType}</span></td>
                          <td><strong>{tx.student_name || tx.teacher_name || 'N/A'}</strong></td>
                          <td>{tx.month}/{tx.year}</td>
                          <td style={{ fontWeight: 'bold', color: tx.color }}>{tx.txType === 'COLLECTION' ? '+' : '-'}₹{parseFloat(tx.amount || tx.paid_amount).toFixed(2)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </>
        )}

        {/* TEACHER VIEW */}
        {role === 'TEACHER' && (
          <div className="teacher-portal">
            <div className="tab-navigation">
              <button className={`tab-btn ${activeTab === 'overview' ? 'active' : ''}`} onClick={() => setActiveTab('overview')}>Overview</button>
              <button className={`tab-btn ${activeTab === 'attendance' ? 'active' : ''}`} onClick={() => setActiveTab('attendance')}>Mark Attendance</button>
              <button className={`tab-btn ${activeTab === 'report' ? 'active' : ''}`} onClick={() => setActiveTab('report')}>Attendance Report</button>
            </div>

            {!dashboardData.profile ? (
              <div className="info-card" style={{ textAlign: 'center', padding: '3rem' }}>
                <h2>Welcome, Teacher! 👩‍🏫</h2>
                <p>Waiting for institute linking...</p>
              </div>
            ) : (
              <>
                {activeTab === 'overview' && (
                  <>
                    <div className="balance-card">
                      <h2>Teacher Portal 👨‍🏫</h2>
                      <div className="info-cards" style={{ marginTop: '1.5rem' }}>
                        <div className="info-card"><h3>Base Monthly Salary</h3><div className="info-value">₹{parseFloat(dashboardData.profile.base_monthly_salary).toFixed(2)}</div></div>
                        <div className="info-card"><h3>My Daily Rate</h3><div className="info-value">₹{parseFloat(dashboardData.profile.daily_rate).toFixed(2)}</div></div>
                      </div>
                    </div>
                    <div className="info-card" style={{ marginTop: '2rem' }}>
                      <h3>Recent Payouts</h3>
                      <div className="table-container">
                        <table className="statement-table">
                          <thead><tr><th>Period</th><th>Amount</th><th>Status</th></tr></thead>
                          <tbody>
                            {dashboardData.recent_salaries?.map((s: any) => (
                              <tr key={s.id}><td>{s.month}/{s.year}</td><td>₹{parseFloat(s.amount).toFixed(2)}</td><td><span className={`tag ${s.status}`}>{s.status}</span></td></tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    </div>
                  </>
                )}

                {activeTab === 'attendance' && (
                  <div className="info-card">
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
                      <h3>Mark Student Attendance 📝</h3>
                      <input type="date" value={attendanceDate} onChange={e => setAttendanceDate(e.target.value)} />
                    </div>
                    <table className="statement-table">
                      <thead><tr><th>Student Name</th><th>Status</th></tr></thead>
                      <tbody>
                        {students.map(s => (
                          <tr key={s.id}>
                            <td><strong>{s.student_name}</strong></td>
                            <td>
                              <select value={attendanceRecords[s.id] || 'PRESENT'} onChange={e => setAttendanceRecords({...attendanceRecords, [s.id]: e.target.value})}>
                                <option value="PRESENT">✅ Present</option>
                                <option value="ABSENT">❌ Absent</option>
                                <option value="LATE">⏰ Late</option>
                              </select>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                    <button onClick={handleMarkBulkAttendance} className="submit-btn" style={{ marginTop: '1.5rem', background: '#2ecc71' }}>💾 Save Today's Attendance</button>
                  </div>
                )}

                {activeTab === 'report' && (
                  <div className="info-card" style={{ overflowX: 'auto' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
                      <h3>Your Students Attendance Report 📜</h3>
                      <div style={{ display: 'flex', gap: '10px' }}>
                        <select value={reportMonth} onChange={e => setReportMonth(parseInt(e.target.value))}>
                          {['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'].map((m, i) => <option key={m} value={i+1}>{m}</option>)}
                        </select>
                        <select value={reportYear} onChange={e => setReportYear(parseInt(e.target.value))}>
                          {[2025, 2026, 2027].map(y => <option key={y} value={y}>{y}</option>)}
                        </select>
                      </div>
                    </div>
                    <div className="table-container">
                      <table className="statement-table" style={{ fontSize: '0.75rem' }}>
                        <thead>
                          <tr>
                            <th style={{ minWidth: '150px' }}>Student Name</th>
                            {Array.from({ length: getDaysInMonth(reportMonth, reportYear) }, (_, i) => (
                              <th key={i+1} style={{ textAlign: 'center', padding: '4px' }}>{i+1}</th>
                            ))}
                            <th style={{ background: '#f9f9f9', textAlign: 'center' }}>Total</th>
                          </tr>
                        </thead>
                        <tbody>
                          {students.map(s => {
                            let presentCount = 0;
                            return (
                              <tr key={s.id}>
                                <td><strong>{s.student_name}</strong></td>
                                {Array.from({ length: getDaysInMonth(reportMonth, reportYear) }, (_, i) => {
                                  const day = i + 1;
                                  const dateStr = `${reportYear}-${String(reportMonth).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
                                  const record = attendanceReport.find(r => r.student_profile === s.id && r.date === dateStr);
                                  let mark = '-'; let color = '#ccc';
                                  if (record?.status === 'PRESENT') { mark = 'P'; color = '#27ae60'; presentCount++; }
                                  else if (record?.status === 'ABSENT') { mark = 'A'; color = '#e74c3c'; }
                                  else if (record?.status === 'LATE') { mark = 'L'; color = '#f39c12'; presentCount++; }
                                  return <td key={day} style={{ textAlign: 'center', color, fontWeight: 'bold' }}>{mark}</td>;
                                })}
                                <td style={{ background: '#f9f9f9', textAlign: 'center', fontWeight: 'bold' }}>{presentCount}</td>
                              </tr>
                            );
                          })}
                        </tbody>
                      </table>
                    </div>
                    <div style={{ marginTop: '1rem', fontSize: '0.75rem', color: '#666', display: 'flex', gap: '15px' }}>
                      <span><strong>P</strong>: Present</span>
                      <span><strong>A</strong>: Absent</span>
                      <span><strong>L</strong>: Late</span>
                    </div>
                  </div>
                )}
              </>
            )}
          </div>
        )}

        {/* MODALS */}
        {showEditTeacher && selectedTeacher && (
          <div className="modal-overlay" onClick={() => setShowEditTeacher(false)}>
            <div className="modal" onClick={e => e.stopPropagation()}>
              <h2>Edit Teacher: {selectedTeacher.user_details?.username} ✏️</h2>
              <form onSubmit={handleUpdateTeacher}>
                <div className="form-group"><label>Base Monthly Salary (₹)</label><input type="number" value={editTeacherData.base_monthly_salary} onChange={e => setEditTeacherData({...editTeacherData, base_monthly_salary: parseFloat(e.target.value) || 0})} required min="0" /></div>
                <div className="form-group"><label>Standard Working Days</label><input type="number" value={editTeacherData.working_days_per_month} onChange={e => setEditTeacherData({...editTeacherData, working_days_per_month: parseInt(e.target.value) || 1})} required min="1" /></div>
                <div className="form-group"><label>Extra Session Rate (₹)</label><input type="number" value={editTeacherData.extra_session_rate} onChange={e => setEditTeacherData({...editTeacherData, extra_session_rate: parseFloat(e.target.value) || 0})} required min="0" /></div>
                <div className="form-group">
                  <label>Current Daily Rate: <strong>₹{((editTeacherData.base_monthly_salary || 0) / (editTeacherData.working_days_per_month || 1)).toFixed(2)}</strong></label>
                </div>
                <button type="submit" className="submit-btn">Update Profile</button>
                <button type="button" className="cancel-btn" onClick={() => setShowEditTeacher(false)}>Cancel</button>
              </form>
            </div>
          </div>
        )}

        {showAddTeacher && (
          <div className="modal-overlay" onClick={() => setShowAddTeacher(false)}>
            <div className="modal" onClick={e => e.stopPropagation()}>
              <h2>Link New Teacher 👩‍🏫</h2>
              <form onSubmit={handleAddTeacher}>
                <div className="form-group"><label>Username</label><input type="text" value={newTeacher.username} onChange={e => setNewTeacher({...newTeacher, username: e.target.value})} required /></div>
                <div className="form-group"><label>Base Monthly Salary (₹)</label><input type="number" value={newTeacher.base_monthly_salary} onChange={e => setNewTeacher({...newTeacher, base_monthly_salary: parseFloat(e.target.value) || 0})} required min="0" /></div>
                <div className="form-group"><label>Standard Working Days</label><input type="number" value={newTeacher.working_days_per_month} onChange={e => setNewTeacher({...newTeacher, working_days_per_month: parseInt(e.target.value) || 1})} required min="1" /></div>
                <div className="form-group"><label>Extra Session Rate (₹)</label><input type="number" value={newTeacher.extra_session_rate} onChange={e => setNewTeacher({...newTeacher, extra_session_rate: parseFloat(e.target.value) || 0})} required min="0" /></div>
                <button type="submit" className="submit-btn">Add Teacher</button>
                <button type="button" className="cancel-btn" onClick={() => setShowAddTeacher(false)}>Cancel</button>
              </form>
            </div>
          </div>
        )}

        {showNoticeModal && selectedStudentForNotice && (
          <div className="modal-overlay" onClick={() => setShowNoticeModal(false)}>
            <div className="modal" onClick={e => e.stopPropagation()}>
              <h2>Send Notice to {selectedStudentForNotice.student_name} 📣</h2>
              <form onSubmit={handleSendNotice}>
                <div className="form-group">
                  <label>Message Type</label>
                  <select onChange={e => setNoticeMessage(e.target.value)}>
                    <option value="">-- Select Template or Type Below --</option>
                    <option value="Today is a leave for the institute.">Today is a leave</option>
                    <option value="There will be an extra class today.">Extra class today</option>
                    <option value="Today's class is cancelled.">Class cancelled</option>
                  </select>
                </div>
                <div className="form-group">
                  <label>Custom Message</label>
                  <textarea 
                    value={noticeMessage} 
                    onChange={e => setNoticeMessage(e.target.value)} 
                    placeholder="Type your announcement here..."
                    required
                    style={{ width: '100%', height: '100px', padding: '10px', borderRadius: '8px', border: '1px solid #ddd' }}
                  />
                </div>
                <button type="submit" className="submit-btn">Send Announcement</button>
                <button type="button" className="cancel-btn" onClick={() => setShowNoticeModal(false)}>Cancel</button>
              </form>
            </div>
          </div>
        )}

        {showAddStudent && (
          <div className="modal-overlay" onClick={() => setShowAddStudent(false)}>
            <div className="modal" onClick={e => e.stopPropagation()}>
              <h2>Add New Student 🎓</h2>
              <form onSubmit={handleAddStudent}>
                <div className="form-group"><label>Student Full Name</label><input type="text" value={newStudent.student_name} onChange={e => setNewStudent({...newStudent, student_name: e.target.value})} required placeholder="e.g. Rahul Kumar" /></div>
                <div className="form-group"><label>Parent Mobile Number</label><input type="text" value={newStudent.parent_mobile} onChange={e => setNewStudent({...newStudent, parent_mobile: e.target.value})} required placeholder="+91 XXXXX XXXXX" /></div>
                <div className="form-group"><label>Monthly Fee (₹)</label><input type="number" value={newStudent.monthly_fee} onChange={e => setNewStudent({...newStudent, monthly_fee: e.target.value})} required /></div>
                <div className="form-group"><label>Due Day (1-31)</label><input type="number" value={newStudent.due_day} onChange={e => setNewStudent({...newStudent, due_day: e.target.value})} required min="1" max="31" /></div>
                <button type="submit" className="submit-btn">Register Student</button>
                <button type="button" className="cancel-btn" onClick={() => setShowAddStudent(false)}>Cancel</button>
              </form>
            </div>
          </div>
        )}

        {showAttendanceModal && selectedTeacher && (
          <div className="modal-overlay" onClick={() => setShowAttendanceModal(false)}>
            <div className="modal" onClick={e => e.stopPropagation()}>
              <h2>Mark Attendance: {selectedTeacher.user_details?.username}</h2>
              <form onSubmit={handleMarkTeacherAttendance}>
                <div className="form-group"><label>Date</label><input type="date" value={teacherAttendanceData.date} onChange={e => setTeacherAttendanceData({...teacherAttendanceData, date: e.target.value})} required /></div>
                <div className="form-group">
                  <label>Status</label>
                  <select value={teacherAttendanceData.status} onChange={e => setTeacherAttendanceData({...teacherAttendanceData, status: e.target.value})}>
                    <option value="PRESENT">Present</option>
                    <option value="ABSENT">Absent (Full Deduction)</option>
                    <option value="HALF_DAY">Half Day (50% Deduction)</option>
                    <option value="OVERTIME">Overtime (1.5x Bonus)</option>
                  </select>
                </div>
                <div className="form-group"><label>Extra Sessions Taken</label><input type="number" value={teacherAttendanceData.extra_sessions} onChange={e => setTeacherAttendanceData({...teacherAttendanceData, extra_sessions: parseInt(e.target.value)})} /></div>
                <div className="form-group"><label>Remarks</label><input type="text" value={teacherAttendanceData.remarks} onChange={e => setTeacherAttendanceData({...teacherAttendanceData, remarks: e.target.value})} /></div>
                <button type="submit" className="submit-btn">Save Attendance</button>
                <button type="button" className="cancel-btn" onClick={() => setShowAttendanceModal(false)}>Cancel</button>
              </form>
            </div>
          </div>
        )}

        {showPayrollModal && payrollResult && (
          <div className="modal-overlay" onClick={() => setShowPayrollModal(false)}>
            <div className="modal" onClick={e => e.stopPropagation()}>
              <h2>Salary Breakdown: {payrollResult.teacher_name}</h2>
              <div className="payroll-summary" style={{ margin: '1.5rem 0', background: '#f8f9fa', padding: '15px', borderRadius: '8px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}><span>Base Monthly Salary:</span><strong>₹{payrollResult.base_salary.toFixed(2)}</strong></div>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px', color: '#e74c3c' }}><span>Leaves/Deductions ({payrollResult.absent_days}A, {payrollResult.half_days}H):</span><strong>- ₹{payrollResult.deductions.toFixed(2)}</strong></div>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px', color: '#2ecc71' }}><span>Overtime Bonus ({payrollResult.ot_days} days):</span><strong>+ ₹{payrollResult.ot_bonus.toFixed(2)}</strong></div>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px', color: '#3498db' }}><span>Session Bonus ({payrollResult.extra_sessions} sessions):</span><strong>+ ₹{payrollResult.session_bonus.toFixed(2)}</strong></div>
                <hr/>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '1.2rem', fontWeight: 'bold' }}><span>Net Payout:</span><span style={{ color: '#27ae60' }}>₹{payrollResult.net_payout.toFixed(2)}</span></div>
              </div>
              <button className="submit-btn" style={{ background: '#27ae60' }} onClick={handleMarkSalaryPaid}>Confirm & Record Payout</button>
              <button type="button" className="cancel-btn" onClick={() => setShowPayrollModal(false)}>Close</button>
            </div>
          </div>
        )}

        {showCreateInstitute && (
          <div className="modal-overlay" onClick={() => setShowCreateInstitute(false)}>
            <div className="modal" onClick={e => e.stopPropagation()}>
              <h2>Setup Institute 🏫</h2>
              <form onSubmit={handleCreateInstitute}>
                <div className="form-group"><label>Institute Name</label><input type="text" value={newInstitute.name} onChange={e => setNewInstitute({...newInstitute, name: e.target.value})} required placeholder="e.g. Bright Coaching Center" /></div>
                <div className="form-group"><label>Address</label><input type="text" value={newInstitute.address} onChange={e => setNewInstitute({...newInstitute, address: e.target.value})} placeholder="Area, City" /></div>
                <div className="form-group"><label>Contact Number</label><input type="text" value={newInstitute.contact_number} onChange={e => setNewInstitute({...newInstitute, contact_number: e.target.value})} placeholder="+91 XXXXX XXXXX" /></div>
                <button type="submit" className="submit-btn">Create Institute</button>
                <button type="button" className="cancel-btn" onClick={() => setShowCreateInstitute(false)}>Cancel</button>
              </form>
            </div>
          </div>
        )}

        {showMarkPaid && (
          <div className="modal-overlay" onClick={() => setShowMarkPaid(false)}>
            <div className="modal" onClick={e => e.stopPropagation()}>
              <h2>Record Student Fee 📝</h2>
              <form onSubmit={(e) => {
                e.preventDefault();
                api.markFeeAsPaid({
                  student_profile: parseInt(paymentData.student_profile),
                  month: paymentData.month,
                  year: paymentData.year,
                  amount: parseFloat(paymentData.amount)
                }).then(() => {
                  setSuccess('Fee recorded!');
                  setShowMarkPaid(false);
                  loadDashboard();
                }).catch(err => setError(err.message));
              }}>
                <div className="form-group"><label>Select Student</label><select value={paymentData.student_profile} onChange={e => setPaymentData({...paymentData, student_profile: e.target.value})} required><option value="">-- Choose Student --</option>{students.map(s => <option key={s.id} value={s.id}>{s.student_name}</option>)}</select></div>
                <div className="form-group"><label>Amount Paid (₹)</label><input type="number" value={paymentData.amount} onChange={e => setPaymentData({...paymentData, amount: e.target.value})} required /></div>
                <button type="submit" className="submit-btn">Confirm Payment</button>
                <button type="button" className="cancel-btn" onClick={() => setShowMarkPaid(false)}>Cancel</button>
              </form>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
