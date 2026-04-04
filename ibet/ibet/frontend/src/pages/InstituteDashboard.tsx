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
  const [showEditStudent, setShowEditStudent] = useState(false);
  const [selectedStudent, setSelectedStudent] = useState<any>(null);
  const [showAddTeacher, setShowAddTeacher] = useState(false);
  const [showEditTeacher, setShowEditTeacher] = useState(false);
  const [showMarkPaid, setShowMarkPaid] = useState(false);
  const [showNoticeModal, setShowNoticeModal] = useState(false);
  const [showCreateInstitute, setShowCreateInstitute] = useState(false);
  const [showAssignModal, setShowAssignModal] = useState(false);
  const [assignedStudentIds, setAssignedStudentIds] = useState<number[]>([]);
  const [teacherFilter, setTeacherFilter] = useState<string>('all');
  
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
  const [editStudentData, setEditStudentData] = useState({ student_name: '', parent_mobile: '', monthly_fee: '', due_day: '5' });
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

  const handleOpenAssignModal = (teacher: any) => {
    setSelectedTeacher(teacher);
    // Initialize with currently assigned students
    setAssignedStudentIds(teacher.assigned_students || []);
    setShowAssignModal(true);
  };

  const handleAssignStudents = async () => {
    if (!selectedTeacher) return;
    try {
      await api.assignStudentsToTeacher(selectedTeacher.id, assignedStudentIds);
      setSuccess(`Students assigned to ${selectedTeacher.user_details.username} successfully!`);
      setShowAssignModal(false);
      loadDashboard();
    } catch (err: any) {
      setError(err.message);
    }
  };

  const handleAddStudent = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newStudent.institute) {
      setError('Please select or create an institute first.');
      return;
    }
    try {
      const res = await api.createInstituteStudent(newStudent);
      setSuccess(`${res.message}. Username: ${res.username}`);
      setShowAddStudent(false);
      loadDashboard();
    } catch (err: any) { setError(err.message); }
  };

  const handleUpdateStudent = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedStudent) return;
    try {
      await api.updateInstituteStudent(selectedStudent.id, editStudentData);
      setSuccess('Student profile updated!');
      setShowEditStudent(false);
      loadDashboard();
    } catch (err: any) { setError(err.message); }
  };

  const handleAddTeacher = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newTeacher.institute) {
      setError('Please select or create an institute first.');
      return;
    }
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
      <header className="dashboard-header glass">
        <button onClick={() => navigate('/select-module')} className="back-btn" style={{ background: 'rgba(255,255,255,0.3)', border: '1px solid rgba(255,255,255,0.3)', color: 'var(--text-main)' }}>← Back</button>
        <h1 style={{ color: 'var(--primary)' }}>Institute Management 🏫 {userProfile?.uid && <span style={{ fontSize: '0.9rem', color: 'white', background: 'rgba(255,255,255,0.2)', backdropFilter: 'blur(4px)', padding: '2px 8px', borderRadius: '4px', marginLeft: '10px', verticalAlign: 'middle' }}>{userProfile.uid}</span>}</h1>
        <button onClick={handleLogout} className="logout-btn">Logout</button>
      </header>

      {dashboardData.institutes?.[0] && (
        <div className="glass" style={{ background: 'rgba(255,255,255,0.25)', padding: '10px 2rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid rgba(255,255,255,0.3)' }}>
          <div>
            <span style={{ fontWeight: 'bold', fontSize: '1.1rem', color: 'var(--primary)' }}>📍 {dashboardData.institutes[0].name}</span>
            <span style={{ marginLeft: '15px', color: 'var(--text-muted)', fontSize: '0.9rem' }}>{dashboardData.institutes[0].address}</span>
          </div>
          <div className="glass" style={{ fontSize: '0.85rem', color: '#3498db', padding: '4px 12px', borderRadius: '20px', background: 'rgba(52, 152, 219, 0.1)' }}>Account: <strong>{userProfile?.username}</strong> ({role})</div>
        </div>
      )}

      <main className="dashboard-main">
        {error && <div className="error-message">{error}</div>}
        {success && <div className="success-message">{success}</div>}

        {(role === 'OWNER' || role === 'TEACHER') && (
          <>
            {role === 'OWNER' ? (
              <div className="stats-grid" style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1.5rem', marginBottom: '2rem' }}>
                <div className="info-card glass"><h3>👥 Students</h3><div className="info-value">{dashboardData.stats.total_students}</div></div>
                <div className="info-card glass"><h3>👩‍🏫 Teachers</h3><div className="info-value">{dashboardData.stats.total_teachers}</div></div>
                <div className="info-card glass"><h3>💰 Revenue (MTD)</h3><div className="info-value" style={{ color: '#27ae60' }}>₹{dashboardData.stats.monthly_revenue.toFixed(2)}</div></div>
                <div className="info-card glass"><h3>📈 Attendance</h3><div className="info-value" style={{ color: '#f39c12' }}>{dashboardData.stats.today_attendance?.present || 0} Present</div></div>
              </div>
            ) : (
              <div className="stats-grid" style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1.5rem', marginBottom: '2rem' }}>
                <div className="info-card glass"><h3>👥 Students</h3><div className="info-value">{students.length}</div></div>
                <div className="info-card glass"><h3>📈 Today's Attendance</h3><div className="info-value" style={{ color: '#f39c12' }}>{dashboardData.stats.students_marked_today || 0} Marked</div></div>
                <div className="info-card glass"><h3>💰 Latest Salary</h3><div className="info-value" style={{ color: '#27ae60' }}>{dashboardData.recent_salaries?.[0] ? `₹${parseFloat(dashboardData.recent_salaries[0].amount).toFixed(2)}` : 'N/A'}</div></div>
              </div>
            )}

            <div className="tab-navigation">
              <button className={`tab-btn ${activeTab === 'overview' ? 'active' : ''}`} onClick={() => setActiveTab('overview')}>📊 Overview</button>
              <button className={`tab-btn ${activeTab === 'attendance' ? 'active' : ''}`} onClick={() => setActiveTab('attendance')}>📅 Attendance</button>
              <button className={`tab-btn ${activeTab === 'students' ? 'active' : ''}`} onClick={() => setActiveTab('students')}>🎓 Students</button>
              {role === 'OWNER' && (
                <>
                  <button className={`tab-btn ${activeTab === 'teachers' ? 'active' : ''}`} onClick={() => setActiveTab('teachers')}>👩‍🏫 Teachers</button>
                  <button className={`tab-btn ${activeTab === 'transactions' ? 'active' : ''}`} onClick={() => setActiveTab('transactions')}>💸 Transactions</button>
                </>
              )}
            </div>

            {activeTab === 'overview' && (
              <div className="info-card glass">
                {role === 'OWNER' ? (
                  <>
                    <h3>Quick Management</h3>
                    <div className="quick-management-grid">
                      <div className="quick-btn" onClick={() => setShowCreateInstitute(true)}>
                        <div className="quick-btn-icon">🏫</div>
                        <div className="quick-btn-text">New Institute</div>
                      </div>
                      <div className="quick-btn" onClick={() => setShowAddStudent(true)}>
                        <div className="quick-btn-icon">➕</div>
                        <div className="quick-btn-text">Add Student</div>
                      </div>
                      <div className="quick-btn" onClick={() => setShowAddTeacher(true)}>
                        <div className="quick-btn-icon">👩‍🏫</div>
                        <div className="quick-btn-text">Add Teacher</div>
                      </div>
                      <div className="quick-btn" onClick={() => setShowMarkPaid(true)}>
                        <div className="quick-btn-icon">📝</div>
                        <div className="quick-btn-text">Record Fee</div>
                      </div>
                    </div>
                  </>
                ) : (
                  <>
                    <h3>Teacher Overview</h3>
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '1.5rem', marginTop: '1rem' }}>
                      <div className="glass" style={{ padding: '1.5rem', borderRadius: '12px', background: 'rgba(255,255,255,0.1)' }}>
                        <h4>Recent Salary Payouts</h4>
                        <div className="table-container" style={{ marginTop: '1rem' }}>
                          <table className="statement-table">
                            <thead><tr><th>Period</th><th>Amount</th><th>Status</th></tr></thead>
                            <tbody>
                              {dashboardData.recent_salaries?.map((s: any, idx: number) => (
                                <tr key={idx}>
                                  <td>{s.month}/{s.year}</td>
                                  <td style={{ fontWeight: 'bold' }}>₹{parseFloat(s.amount).toFixed(2)}</td>
                                  <td><span className="tag PAID">{s.status}</span></td>
                                </tr>
                              ))}
                              {(!dashboardData.recent_salaries || dashboardData.recent_salaries.length === 0) && (
                                <tr><td colSpan={3} style={{ textAlign: 'center' }}>No recent payouts</td></tr>
                              )}
                            </tbody>
                          </table>
                        </div>
                      </div>
                      
                      <div className="glass" style={{ padding: '1.5rem', borderRadius: '12px', background: 'rgba(255,255,255,0.1)' }}>
                        <h4>Recent Notifications</h4>
                        <div className="table-container" style={{ marginTop: '1rem' }}>
                          <table className="statement-table">
                            <thead><tr><th>Date</th><th>Message</th></tr></thead>
                            <tbody>
                              {dashboardData.notifications?.map((n: any) => (
                                <tr key={n.id}>
                                  <td>{new Date(n.sent_at).toLocaleDateString()}</td>
                                  <td>{n.message}</td>
                                </tr>
                              ))}
                              {(!dashboardData.notifications || dashboardData.notifications.length === 0) && (
                                <tr><td colSpan={2} style={{ textAlign: 'center' }}>No recent notifications</td></tr>
                              )}
                            </tbody>
                          </table>
                        </div>
                      </div>
                    </div>
                  </>
                )}
              </div>
            )}

            {activeTab === 'attendance' && (
              <div className="info-card" style={{ overflowX: 'auto' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem', flexWrap: 'wrap', gap: '1rem' }}>
                  <div style={{ display: 'flex', gap: '10px' }}>
                    <div style={{ display: 'flex', gap: '10px', background: '#f0f2f5', padding: '4px', borderRadius: '8px' }}>
                      <button 
                        className={`tab-btn ${attendanceSubTab === 'students' ? 'active' : ''}`} 
                        style={{ padding: '6px 15px', fontSize: '0.85rem' }}
                        onClick={() => setAttendanceSubTab('students')}
                      >Students</button>
                      {role === 'OWNER' && (
                        <button 
                          className={`tab-btn ${attendanceSubTab === 'teachers' ? 'active' : ''}`} 
                          style={{ padding: '6px 15px', fontSize: '0.85rem' }}
                          onClick={() => setAttendanceSubTab('teachers')}
                        >Teachers</button>
                      )}
                    </div>

                    <div style={{ display: 'flex', gap: '10px', background: '#f0f2f5', padding: '4px', borderRadius: '8px' }}>
                      <button 
                        className={`tab-btn ${attendanceMode === 'report' ? 'active' : ''}`} 
                        style={{ padding: '6px 15px', fontSize: '0.85rem' }}
                        onClick={() => setAttendanceMode('report')}
                      >Report</button>
                      {attendanceSubTab === 'students' && (
                        <button 
                          className={`tab-btn ${attendanceMode === 'mark' ? 'active' : ''}`} 
                          style={{ padding: '6px 15px', fontSize: '0.85rem' }}
                          onClick={() => setAttendanceMode('mark')}
                        >Mark</button>
                      )}
                    </div>
                  </div>
                  
                  <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
                    {role === 'OWNER' && attendanceSubTab === 'students' && (
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                        <label style={{ fontSize: '0.85rem', color: 'white' }}>By Teacher: </label>
                        <select 
                          value={teacherFilter} 
                          onChange={e => setTeacherFilter(e.target.value)}
                          style={{ background: 'rgba(255,255,255,0.2)', color: 'white', border: '1px solid rgba(255,255,255,0.2)', borderRadius: '4px', padding: '4px 8px' }}
                        >
                          <option value="all" style={{ color: 'black' }}>All Students</option>
                          {teachers.map(t => (
                            <option key={t.id} value={t.id} style={{ color: 'black' }}>{t.user_details?.username}</option>
                          ))}
                        </select>
                      </div>
                    )}

                    {attendanceMode === 'report' ? (
                      <div style={{ display: 'flex', gap: '10px' }}>
                        <select value={reportMonth} onChange={e => setReportMonth(parseInt(e.target.value))} style={{ background: 'rgba(255,255,255,0.2)', color: 'white', border: '1px solid rgba(255,255,255,0.2)', borderRadius: '4px', padding: '4px 8px' }}>
                          {['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'].map((m, i) => <option key={m} value={i+1} style={{ color: 'black' }}>{m}</option>)}
                        </select>
                        <select value={reportYear} onChange={e => setReportYear(parseInt(e.target.value))} style={{ background: 'rgba(255,255,255,0.2)', color: 'white', border: '1px solid rgba(255,255,255,0.2)', borderRadius: '4px', padding: '4px 8px' }}>
                          {[2025, 2026, 2027].map(y => <option key={y} value={y} style={{ color: 'black' }}>{y}</option>)}
                        </select>
                      </div>
                    ) : (
                      <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
                        <label style={{ fontSize: '0.9rem', color: 'white' }}>Marking for: </label>
                        <input type="date" value={attendanceDate} onChange={e => setAttendanceDate(e.target.value)} style={{ background: 'rgba(255,255,255,0.2)', color: 'white', border: '1px solid rgba(255,255,255,0.2)', borderRadius: '4px', padding: '4px 8px' }} />
                      </div>
                    )}
                  </div>
                </div>

                {attendanceMode === 'report' ? (
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
                          (() => {
                            let filtered = students;
                            if (role === 'OWNER' && teacherFilter !== 'all') {
                              const targetTeacher = teachers.find(t => t.id === parseInt(teacherFilter));
                              if (targetTeacher) {
                                filtered = students.filter(s => targetTeacher.assigned_students?.includes(s.id));
                              }
                            }
                            return filtered.map(s => {
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
                            });
                          })()
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
                ) : (
                  <div className="table-container">
                    <table className="statement-table">
                      <thead>
                        <tr>
                          <th>Student Name</th>
                          <th style={{ textAlign: 'center' }}>Attendance Status</th>
                        </tr>
                      </thead>
                      <tbody>
                        {(() => {
                          let filtered = students;
                          if (role === 'OWNER' && teacherFilter !== 'all') {
                            const targetTeacher = teachers.find(t => t.id === parseInt(teacherFilter));
                            if (targetTeacher) {
                              filtered = students.filter(s => targetTeacher.assigned_students?.includes(s.id));
                            }
                          }
                          return filtered.map(s => (
                            <tr key={s.id}>
                              <td><strong>{s.student_name}</strong></td>
                              <td style={{ textAlign: 'center' }}>
                                <div style={{ display: 'flex', gap: '10px', justifyContent: 'center' }}>
                                  <button 
                                    className={`btn-enhanced ${attendanceRecords[s.id] === 'PRESENT' ? 'btn-green' : ''}`}
                                    style={{ padding: '4px 12px', fontSize: '0.8rem', background: attendanceRecords[s.id] === 'PRESENT' ? '#27ae60' : 'rgba(255,255,255,0.1)' }}
                                    onClick={() => setAttendanceRecords({...attendanceRecords, [s.id]: 'PRESENT'})}
                                  >Present</button>
                                  <button 
                                    className={`btn-enhanced ${attendanceRecords[s.id] === 'ABSENT' ? 'btn-red' : ''}`}
                                    style={{ padding: '4px 12px', fontSize: '0.8rem', background: attendanceRecords[s.id] === 'ABSENT' ? '#e74c3c' : 'rgba(255,255,255,0.1)' }}
                                    onClick={() => setAttendanceRecords({...attendanceRecords, [s.id]: 'ABSENT'})}
                                  >Absent</button>
                                  <button 
                                    className={`btn-enhanced ${attendanceRecords[s.id] === 'LATE' ? 'btn-orange' : ''}`}
                                    style={{ padding: '4px 12px', fontSize: '0.8rem', background: attendanceRecords[s.id] === 'LATE' ? '#f39c12' : 'rgba(255,255,255,0.1)' }}
                                    onClick={() => setAttendanceRecords({...attendanceRecords, [s.id]: 'LATE'})}
                                  >Late</button>
                                </div>
                              </td>
                            </tr>
                          ));
                        })()}
                      </tbody>
                    </table>
                    <div style={{ marginTop: '2rem', display: 'flex', justifyContent: 'flex-end' }}>
                      <button className="submit-btn" style={{ width: 'auto', padding: '0.8rem 2rem' }} onClick={handleMarkBulkAttendance}>Save Attendance Records</button>
                    </div>
                  </div>
                )}

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
                            <div className="action-btn-group">
                              <button className="btn-enhanced btn-blue" onClick={() => { 
                                setSelectedTeacher(t); 
                                setEditTeacherData({ 
                                  base_monthly_salary: parseFloat(t.base_monthly_salary), 
                                  working_days_per_month: t.working_days_per_month, 
                                  extra_session_rate: parseFloat(t.extra_session_rate) 
                                }); 
                                setShowEditTeacher(true); 
                              }}>✏️ Edit</button>
                              <button className="btn-enhanced btn-purple" onClick={() => { setSelectedTeacher(t); setShowAttendanceModal(true); }}>📝 Attendance</button>
                              <button className="btn-enhanced btn-orange" onClick={() => handleOpenAssignModal(t)}>🔗 Assign</button>
                              <button className="btn-enhanced btn-green" onClick={() => handleCalculatePayroll(t.id)}>💵 Payroll</button>
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

        {/* SHARED STUDENT DIRECTORY TAB */}
        {activeTab === 'students' && (
          <div className="info-card">
            <h3>Student Directory</h3>
            <div className="table-container" style={{ marginTop: '1rem' }}>
              <table className="statement-table">
                <thead><tr><th>Student Name</th><th>Monthly Fee</th><th>Fee Status</th><th>Due Day</th><th style={{ textAlign: 'right' }}>Actions</th></tr></thead>
                <tbody>
                  {students.map(s => {
                    const feeStatus = dashboardData?.student_fee_status?.[s.id];
                    return (
                      <tr key={s.id}>
                        <td><strong>{s.student_name}</strong></td>
                        <td>₹{parseFloat(s.monthly_fee).toFixed(2)}</td>
                        <td>
                          {feeStatus ? (
                            <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                              <span className={`tag ${feeStatus.status}`} style={{ 
                                background: feeStatus.status === 'PAID' ? '#2ecc71' : (feeStatus.status === 'PARTIAL' ? '#f1c40f' : '#e74c3c'),
                                color: 'white',
                                padding: '2px 8px',
                                borderRadius: '4px',
                                fontSize: '0.7rem',
                                width: 'fit-content'
                              }}>
                                {feeStatus.status} (₹{feeStatus.paid}/{feeStatus.total})
                              </span>
                              {feeStatus.status !== 'PAID' && (
                                <span style={{ fontSize: '0.75rem', color: '#e74c3c', fontWeight: 'bold' }}>
                                  Pending: ₹{feeStatus.pending}
                                </span>
                              )}
                            </div>
                          ) : <span className="tag" style={{ background: '#ccc', color: 'white', padding: '2px 8px', borderRadius: '4px', fontSize: '0.7rem' }}>UNKNOWN</span>}
                        </td>
                        <td>{s.due_day}th</td>
                        <td style={{ textAlign: 'right' }}>
                          <div className="action-btn-group">
                            <button className="btn-enhanced btn-blue" onClick={() => {
                              setSelectedStudent(s);
                              setEditStudentData({
                                student_name: s.student_name,
                                parent_mobile: s.parent_mobile,
                                monthly_fee: s.monthly_fee,
                                due_day: s.due_day.toString()
                              });
                              setShowEditStudent(true);
                            }}>✏️ Edit</button>
                            <button className="btn-enhanced btn-orange" onClick={() => { setSelectedStudentForNotice(s); setShowNoticeModal(true); }}>📣 Notice</button>
                            {role === 'OWNER' && <button className="btn-enhanced btn-red" onClick={() => handleUnlinkStudent(s.id)}>🗑️ Unlink</button>}
                            <button className="btn-enhanced btn-blue" onClick={() => api.sendFeeReminder(s.id)}>🔔 Remind</button>
                          </div>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {role === 'STUDENT' && (
          <div className="student-portal">
            <div className="balance-card">
              <h2>Student Academic Profile 🎓</h2>
              <div className="info-cards" style={{ marginTop: '1.5rem' }}>
                <div className="info-card"><h3>Institute</h3><div className="info-value">{dashboardData.institute_name}</div></div>
                <div className="info-card"><h3>Attendance</h3><div className="info-value" style={{ color: '#27ae60' }}>{dashboardData.attendance.percentage}%</div></div>
              </div>
            </div>

            <div className="stats-grid" style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '1.5rem', marginTop: '2rem' }}>
              <div className="info-card glass">
                <h3>Current Monthly Fee 💰</h3>
                {dashboardData.current_fee_status ? (
                  <div style={{ marginTop: '1rem' }}>
                    <div style={{ fontSize: '1.5rem', fontWeight: 'bold', color: dashboardData.current_fee_status.status === 'PAID' ? '#27ae60' : '#e74c3c' }}>
                      {dashboardData.current_fee_status.status}
                    </div>
                    <div className="glass" style={{ margin: '15px 0', padding: '15px', borderRadius: '8px', background: 'rgba(255,255,255,0.05)' }}>
                      <p style={{ display: 'flex', justifyContent: 'space-between', margin: '5px 0' }}><span>Total Fee:</span> <strong>₹{parseFloat(dashboardData.current_fee_status.total_amount).toFixed(2)}</strong></p>
                      <p style={{ display: 'flex', justifyContent: 'space-between', margin: '5px 0', color: '#27ae60' }}><span>Amount Paid:</span> <strong>₹{parseFloat(dashboardData.current_fee_status.paid_amount).toFixed(2)}</strong></p>
                      <hr style={{ opacity: 0.1, margin: '10px 0' }} />
                      <p style={{ display: 'flex', justifyContent: 'space-between', margin: '5px 0', fontWeight: 'bold', color: '#e74c3c', fontSize: '1.1rem' }}><span>Remaining:</span> <span>₹{parseFloat(dashboardData.current_fee_status.pending_amount).toFixed(2)}</span></p>
                    </div>
                    {dashboardData.current_fee_status.status !== 'PAID' && (
                      <p style={{ fontSize: '0.85rem', color: '#f39c12', textAlign: 'center' }}>⚠️ Please clear your dues by the {dashboardData.profile.due_day}th of this month.</p>
                    )}
                  </div>
                ) : <p>No fee record for this month.</p>}
              </div>

              <div className="info-card glass">
                <h3>Attendance Summary 📅</h3>
                <div style={{ textAlign: 'center', margin: '1rem 0' }}>
                  <div style={{ fontSize: '2.5rem', fontWeight: 'bold', color: 'var(--primary)' }}>{dashboardData.attendance.percentage}%</div>
                  <p style={{ color: 'var(--text-muted)' }}>Overall Attendance</p>
                </div>
                <div className="table-container" style={{ maxHeight: '150px', overflowY: 'auto' }}>
                  <table className="statement-table" style={{ fontSize: '0.85rem' }}>
                    <thead><tr><th>Date</th><th>Status</th><th>By</th></tr></thead>
                    <tbody>
                      {dashboardData.attendance.recent.map((a: any) => (
                        <tr key={a.id}>
                          <td>{new Date(a.date).toLocaleDateString()}</td>
                          <td><span className={`tag ${a.status}`} style={{ fontSize: '0.7rem', padding: '2px 6px' }}>{a.status}</span></td>
                          <td style={{ fontSize: '0.75rem', opacity: 0.8 }}>{a.marked_by_username || '-'}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>

            <div className="info-card glass" style={{ marginTop: '2rem' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
                <h3>Fee Transaction History 🧾</h3>
                <span className="tag" style={{ background: 'rgba(52, 152, 219, 0.2)', color: '#3498db' }}>Official Record</span>
              </div>
              <div className="table-container">
                <table className="statement-table">
                  <thead>
                    <tr>
                      <th>Payment Date</th>
                      <th>Period (MM/YYYY)</th>
                      <th>Transaction ID</th>
                      <th>Total Fee</th>
                      <th>Amount Paid</th>
                      <th>Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {dashboardData.recent_fees?.map((f: any) => (
                      <tr key={f.id}>
                        <td>{f.payment_date ? new Date(f.payment_date).toLocaleDateString() : 'Pending'}</td>
                        <td><strong>{String(f.month).padStart(2, '0')}/{f.year}</strong></td>
                        <td style={{ fontFamily: 'monospace', fontSize: '0.85rem' }}>{f.transaction_id || 'N/A'}</td>
                        <td>₹{parseFloat(f.total_amount).toFixed(2)}</td>
                        <td style={{ fontWeight: 'bold', color: '#27ae60' }}>₹{parseFloat(f.paid_amount).toFixed(2)}</td>
                        <td>
                          <span className={`tag ${f.status}`} style={{ 
                            background: f.status === 'PAID' ? '#2ecc71' : (f.status === 'PARTIAL' ? '#f1c40f' : '#e74c3c'),
                            color: 'white'
                          }}>
                            {f.status}
                          </span>
                        </td>
                      </tr>
                    ))}
                    {(!dashboardData.recent_fees || dashboardData.recent_fees.length === 0) && (
                      <tr><td colSpan={6} style={{ textAlign: 'center', padding: '20px' }}>No transaction records found.</td></tr>
                    )}
                  </tbody>
                </table>
              </div>
              <div style={{ marginTop: '1.5rem', padding: '15px', borderRadius: '8px', background: 'rgba(52, 152, 219, 0.05)', border: '1px solid rgba(52, 152, 219, 0.1)' }}>
                <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
                  <strong>Note:</strong> This report includes all fees recorded by the institute for your profile. If you notice any discrepancy, please contact the institute office immediately.
                </p>
              </div>
            </div>

            <div className="info-card glass" style={{ marginTop: '2rem' }}>
              <h3>Recent Announcements 📣</h3>
              <div className="table-container" style={{ marginTop: '1rem' }}>
                <table className="statement-table">
                  <thead><tr><th>Date</th><th>Type</th><th>Message</th></tr></thead>
                  <tbody>
                    {dashboardData.notifications?.map((n: any) => (
                      <tr key={n.id}>
                        <td>{new Date(n.sent_at).toLocaleDateString()}</td>
                        <td><span className="tag" style={{ background: 'rgba(243, 156, 18, 0.2)', color: '#f39c12', fontSize: '0.7rem' }}>{n.notification_type}</span></td>
                        <td>{n.message}</td>
                      </tr>
                    ))}
                    {(!dashboardData.notifications || dashboardData.notifications.length === 0) && (
                      <tr><td colSpan={3} style={{ textAlign: 'center' }}>No recent announcements</td></tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}


        {/* MODALS */}
        {showAssignModal && selectedTeacher && (
          <div className="modal-overlay" onClick={() => setShowAssignModal(false)}>
            <div className="modal glass" onClick={e => e.stopPropagation()} style={{ maxWidth: '600px', width: '90%' }}>
              <h2>Assign Students to {selectedTeacher.user_details?.username} 🔗</h2>
              <p style={{ color: 'var(--text-muted)', marginBottom: '1.5rem' }}>Select students that this teacher is responsible for (e.g. Art students, Music students).</p>
              
              <div style={{ maxHeight: '300px', overflowY: 'auto', background: 'rgba(255,255,255,0.1)', borderRadius: '8px', padding: '10px' }}>
                {students.map(s => (
                  <div key={s.id} style={{ display: 'flex', alignItems: 'center', gap: '10px', padding: '8px', borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
                    <input 
                      type="checkbox" 
                      id={`student-${s.id}`} 
                      checked={assignedStudentIds.includes(s.id)}
                      onChange={(e) => {
                        if (e.target.checked) {
                          setAssignedStudentIds([...assignedStudentIds, s.id]);
                        } else {
                          setAssignedStudentIds(assignedStudentIds.filter(id => id !== s.id));
                        }
                      }}
                      style={{ width: '18px', height: '18px', cursor: 'pointer' }}
                    />
                    <label htmlFor={`student-${s.id}`} style={{ cursor: 'pointer', flex: 1 }}>
                      <strong>{s.student_name}</strong>
                    </label>
                  </div>
                ))}
                {students.length === 0 && <p style={{ textAlign: 'center', padding: '20px' }}>No students available in this institute.</p>}
              </div>

              <div style={{ marginTop: '1.5rem', display: 'flex', gap: '10px' }}>
                <button className="submit-btn" onClick={handleAssignStudents} style={{ marginTop: 0 }}>Save Assignments</button>
                <button className="cancel-btn" onClick={() => setShowAssignModal(false)} style={{ marginTop: 0 }}>Cancel</button>
              </div>
            </div>
          </div>
        )}

        {showEditTeacher && selectedTeacher && (
          <div className="modal-overlay" onClick={() => setShowEditTeacher(false)}>
            <div className="modal glass" onClick={e => e.stopPropagation()}>
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
            <div className="modal glass" onClick={e => e.stopPropagation()}>
              <h2>Link New Teacher 👩‍🏫</h2>
              <form onSubmit={handleAddTeacher}>
                <div className="form-group">
                  <label>Select Institute</label>
                  <select 
                    value={newTeacher.institute} 
                    onChange={e => setNewTeacher({...newTeacher, institute: e.target.value})} 
                    required 
                    style={{ background: 'rgba(255,255,255,0.2)', color: 'white' }}
                  >
                    <option value="" style={{ color: 'black' }}>-- Select Institute --</option>
                    {dashboardData?.institutes?.map((inst: any) => (
                      <option key={inst.id} value={inst.id} style={{ color: 'black' }}>{inst.name}</option>
                    ))}
                  </select>
                </div>
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
            <div className="modal glass" onClick={e => e.stopPropagation()}>
              <h2>Send Notice to {selectedStudentForNotice.student_name} 📣</h2>
              <form onSubmit={handleSendNotice}>
                <div className="form-group">
                  <label>Message Type</label>
                  <select onChange={e => setNoticeMessage(e.target.value)} style={{ background: 'rgba(255,255,255,0.2)', color: 'white' }}>
                    <option value="" style={{ color: 'black' }}>-- Select Template or Type Below --</option>
                    <option value="Today is a leave for the institute." style={{ color: 'black' }}>Today is a leave</option>
                    <option value="There will be an extra class today." style={{ color: 'black' }}>Extra class today</option>
                    <option value="Today's class is cancelled." style={{ color: 'black' }}>Class cancelled</option>
                  </select>
                </div>
                <div className="form-group">
                  <label>Custom Message</label>
                  <textarea 
                    value={noticeMessage} 
                    onChange={e => setNoticeMessage(e.target.value)} 
                    placeholder="Type your announcement here..."
                    required
                    style={{ width: '100%', height: '100px', padding: '10px', borderRadius: '8px', border: '1px solid rgba(255,255,255,0.2)', background: 'rgba(255,255,255,0.1)', color: 'white' }}
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
            <div className="modal glass" onClick={e => e.stopPropagation()}>
              <h2>Add New Student 🎓</h2>
              <form onSubmit={handleAddStudent}>
                <div className="form-group">
                  <label>Select Institute</label>
                  <select 
                    value={newStudent.institute} 
                    onChange={e => setNewStudent({...newStudent, institute: e.target.value})} 
                    required 
                    style={{ background: 'rgba(255,255,255,0.2)', color: 'white' }}
                  >
                    <option value="" style={{ color: 'black' }}>-- Select Institute --</option>
                    {dashboardData?.institutes?.map((inst: any) => (
                      <option key={inst.id} value={inst.id} style={{ color: 'black' }}>{inst.name}</option>
                    ))}
                  </select>
                </div>
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

        {showEditStudent && selectedStudent && (
          <div className="modal-overlay" onClick={() => setShowEditStudent(false)}>
            <div className="modal glass" onClick={e => e.stopPropagation()}>
              <h2>Edit Student: {selectedStudent.student_name} ✏️</h2>
              <form onSubmit={handleUpdateStudent}>
                <div className="form-group"><label>Student Full Name</label><input type="text" value={editStudentData.student_name} onChange={e => setEditStudentData({...editStudentData, student_name: e.target.value})} required /></div>
                <div className="form-group"><label>Parent Mobile Number</label><input type="text" value={editStudentData.parent_mobile} onChange={e => setEditStudentData({...editStudentData, parent_mobile: e.target.value})} required /></div>
                <div className="form-group"><label>Monthly Fee (₹)</label><input type="number" value={editStudentData.monthly_fee} onChange={e => setEditStudentData({...editStudentData, monthly_fee: e.target.value})} required /></div>
                <div className="form-group"><label>Due Day (1-31)</label><input type="number" value={editStudentData.due_day} onChange={e => setEditStudentData({...editStudentData, due_day: e.target.value})} required min="1" max="31" /></div>
                <button type="submit" className="submit-btn">Update Profile</button>
                <button type="button" className="cancel-btn" onClick={() => setShowEditStudent(false)}>Cancel</button>
              </form>
            </div>
          </div>
        )}

        {showAttendanceModal && selectedTeacher && (
          <div className="modal-overlay" onClick={() => setShowAttendanceModal(false)}>
            <div className="modal glass" onClick={e => e.stopPropagation()}>
              <h2>Mark Attendance: {selectedTeacher.user_details?.username}</h2>
              <form onSubmit={handleMarkTeacherAttendance}>
                <div className="form-group"><label>Date</label><input type="date" value={teacherAttendanceData.date} onChange={e => setTeacherAttendanceData({...teacherAttendanceData, date: e.target.value})} required style={{ background: 'rgba(255,255,255,0.2)', color: 'white' }} /></div>
                <div className="form-group">
                  <label>Status</label>
                  <select value={teacherAttendanceData.status} onChange={e => setTeacherAttendanceData({...teacherAttendanceData, status: e.target.value})} style={{ background: 'rgba(255,255,255,0.2)', color: 'white' }}>
                    <option value="PRESENT" style={{ color: 'black' }}>Present</option>
                    <option value="ABSENT" style={{ color: 'black' }}>Absent (Full Deduction)</option>
                    <option value="HALF_DAY" style={{ color: 'black' }}>Half Day (50% Deduction)</option>
                    <option value="OVERTIME" style={{ color: 'black' }}>Overtime (1.5x Bonus)</option>
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
            <div className="modal glass" onClick={e => e.stopPropagation()}>
              <h2>Salary Breakdown: {payrollResult.teacher_name}</h2>
              <div className="payroll-summary glass" style={{ margin: '1.5rem 0', background: 'rgba(255,255,255,0.1)', padding: '15px', borderRadius: '8px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}><span>Base Monthly Salary:</span><strong>₹{payrollResult.base_salary.toFixed(2)}</strong></div>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px', color: '#ff8a80' }}><span>Leaves/Deductions ({payrollResult.absent_days}A, {payrollResult.half_days}H):</span><strong>- ₹{payrollResult.deductions.toFixed(2)}</strong></div>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px', color: '#90EE90' }}><span>Overtime Bonus ({payrollResult.ot_days} days):</span><strong>+ ₹{payrollResult.ot_bonus.toFixed(2)}</strong></div>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px', color: '#3498db' }}><span>Session Bonus ({payrollResult.extra_sessions} sessions):</span><strong>+ ₹{payrollResult.session_bonus.toFixed(2)}</strong></div>
                <hr style={{ opacity: 0.1, margin: '10px 0' }}/>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '1.2rem', fontWeight: 'bold' }}><span>Net Payout:</span><span style={{ color: '#27ae60' }}>₹{payrollResult.net_payout.toFixed(2)}</span></div>
              </div>
              <button className="submit-btn" style={{ background: 'rgba(39, 174, 96, 0.8)', marginTop: 0 }} onClick={handleMarkSalaryPaid}>Confirm & Record Payout</button>
              <button type="button" className="cancel-btn" onClick={() => setShowPayrollModal(false)}>Close</button>
            </div>
          </div>
        )}

        {showCreateInstitute && (
          <div className="modal-overlay" onClick={() => setShowCreateInstitute(false)}>
            <div className="modal glass" onClick={e => e.stopPropagation()}>
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
            <div className="modal glass" onClick={e => e.stopPropagation()}>
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
                <div className="form-group"><label>Select Student</label><select value={paymentData.student_profile} onChange={e => setPaymentData({...paymentData, student_profile: e.target.value})} required style={{ background: 'rgba(255,255,255,0.2)', color: 'white' }}><option value="" style={{ color: 'black' }}>-- Choose Student --</option>{students.map(s => <option key={s.id} value={s.id} style={{ color: 'black' }}>{s.student_name}</option>)}</select></div>
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
