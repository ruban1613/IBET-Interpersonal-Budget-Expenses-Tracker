// API service for connecting to Django backend
const API_BASE_URL = '/api';

interface LoginResponse {
  token: string;
  user: {
    id: number;
    username: string;
    email: string;
    persona?: string;
  };
}

interface RegisterResponse {
  message: string;
  user_id: number;
}

interface ProfileResponse {
  id: number;
  username: string;
  email: string;
  persona?: string;
  first_name?: string;
  last_name?: string;
}

interface ApiError {
  error: string;
  details?: string;
}

class ApiService {
  private token: string | null = null;

  constructor() {
    this.token = localStorage.getItem('auth_token');
  }

  setToken(token: string) {
    this.token = token;
    localStorage.setItem('auth_token', token);
  }

  clearToken() {
    this.token = null;
    localStorage.removeItem('auth_token');
    localStorage.removeItem('user');
  }

  clearAllData() {
    this.token = null;
    localStorage.clear();
  }

  getToken(): string | null {
    return this.token;
  }

  async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const headers: HeadersInit = {
      'Content-Type': 'application/json',
      ...options.headers,
    };

    if (this.token) {
      (headers as Record<string, string>)['Authorization'] = `Token ${this.token}`;
    }

    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      ...options,
      headers,
    });

    if (response.status === 204) {
      return {} as T;
    }

    if (response.status === 402) {
      return response.json();
    }

    if (!response.ok) {
      let errorMessage = 'An unexpected error occurred';
      try {
        const errorData = await response.json();
        errorMessage = errorData.error || errorData.message || JSON.stringify(errorData) || errorMessage;
      } catch (e) {
        // Fallback if not JSON
      }
      throw new Error(errorMessage);
    }

    const text = await response.text();
    return text ? JSON.parse(text) : {} as T;
  }

  // Auth endpoints
  async login(username: string, password: string): Promise<LoginResponse> {
    return this.request<LoginResponse>('/auth/login/', {
      method: 'POST',
      body: JSON.stringify({ username, password }),
    });
  }

  async register(
    username: string,
    email: string,
    phone: string,
    password: string,
    persona: string = 'INDIVIDUAL'
  ): Promise<RegisterResponse> {
    return this.request<RegisterResponse>('/auth/register/', {
      method: 'POST',
      body: JSON.stringify({ username, email, phone, password, persona }),
    });
  }

  async logout(): Promise<void> {
    await this.request('/auth/logout/', { method: 'POST' });
    this.clearToken();
  }

  async getProfile(): Promise<ProfileResponse> {
    return this.request<ProfileResponse>('/auth/profile/');
  }

  async requestPasswordResetOTP(username: string, phone: string): Promise<{ message: string }> {
    return this.request('/auth/request-password-reset/', {
      method: 'POST',
      body: JSON.stringify({ username, phone }),
    });
  }

  async resetPassword(
    username: string,
    phone: string,
    otp: string,
    newPassword: string
  ): Promise<{ message: string }> {
    return this.request('/auth/reset-password/', {
      method: 'POST',
      body: JSON.stringify({ username, phone, otp, new_password: newPassword }),
    });
  }

  async setLanguage(language: string): Promise<{ message: string }> {
    return this.request('/set-language/', {
      method: 'POST',
      body: JSON.stringify({ language }),
    });
  }

  async getLanguages(): Promise<{ languages: Array<{ code: string; name: string }> }> {
    return this.request('/languages/');
  }

  // Wallet endpoints
  async getWallet(module: string): Promise<any> {
    return this.request(`/${module}/wallet/`);
  }

  async getBalance(module: string): Promise<{ balance: number }> {
    return this.request(`/${module}/wallet/balance/`);
  }

  async getWalletBalance(): Promise<{ balance: number }> {
    return this.getBalance('student');
  }

  async deposit(module: string, amount: number, otp: string): Promise<any> {
    return this.request(`/${module}/wallet/deposit/`, {
      method: 'POST',
      body: JSON.stringify({ amount, otp }),
    });
  }

  async withdraw(module: string, amount: number, otp: string): Promise<any> {
    const headers: HeadersInit = { 'Content-Type': 'application/json' };
    if (this.token) headers['Authorization'] = `Token ${this.token}`;
    const response = await fetch(`${API_BASE_URL}/${module}/wallet/withdraw/`, {
      method: 'POST', headers,
      body: JSON.stringify({ amount, otp }),
    });
    if (response.status === 402) return response.json();
    if (!response.ok) {
      const error: ApiError = await response.json().catch(() => ({ error: 'Request failed' }));
      throw new Error(error.error || 'Request failed');
    }
    return response.json();
  }

  async requestOTP(module: string = 'student', amount?: number, studentId?: number): Promise<any> {
    if (module === 'parent' || module === 'parent_approval') {
      return this.request('/parent/wallet/generate-otp/', {
        method: 'POST',
        body: JSON.stringify({ 
          operation_type: module === 'parent_approval' ? 'allowance_change' : 'wallet_operation',
          amount: amount,
          student_id: studentId
        }),
      });
    }
    return this.request(`/${module}/wallet/generate-otp/`, {
      method: 'POST',
      body: JSON.stringify({ operation_type: 'wallet_operation', amount: amount }),
    });
  }

  async generateTransferOTP(studentId: number, amount: number): Promise<any> {
    return this.request('/parent/wallet/generate-otp/', {
      method: 'POST',
      body: JSON.stringify({
        operation_type: 'transfer_to_student',
        amount: amount,
        student_id: studentId,
        description: 'Transfer to student wallet'
      }),
    });
  }

  // Student endpoints
  async getStudentDashboard(): Promise<any> { return this.request('/student/dashboard/'); }
  async getStudentTransactions(): Promise<any> { return this.request('/student/transactions/'); }
  async getStudentWallet(): Promise<any> { return this.request('/student/wallet/'); }
  async withdrawSpecial(amount: number, description: string = ''): Promise<any> {
    const headers: HeadersInit = { 'Content-Type': 'application/json' };
    if (this.token) headers['Authorization'] = `Token ${this.token}`;
    const response = await fetch(`${API_BASE_URL}/student/wallet/withdraw_special/`, {
      method: 'POST',
      headers,
      body: JSON.stringify({ amount, description }),
    });
    if (response.status === 402) return response.json();
    if (!response.ok) {
      const error: any = await response.json().catch(() => ({ error: 'Request failed' }));
      throw new Error(error.error || error.message || 'Request failed');
    }
    return response.json();
  }
  async getStudentAllowance(): Promise<any> {
    const allowances = await this.request<any[]>('/student/monthly-allowances/');
    const active = allowances.find((a: any) => a.is_active);
    return active || allowances[0] || null;
  }
  async getDailySpending(): Promise<any> { return this.request('/student/daily-spending/'); }
  async getMonthlySpendingSummary(): Promise<any> { return this.request('/student/monthly-summaries/'); }
  async getSpendingLocks(): Promise<any> { return this.request('/student/spending-locks/'); }
  async getStudentNotifications(): Promise<any> { return this.request('/student/notifications/'); }
  async deleteStudentNotification(notificationId: number): Promise<{ message: string }> {
    return this.request(`/student/notifications/${notificationId}/`, { method: 'DELETE' });
  }
  async markNotificationAsRead(notificationId: number): Promise<any> {
    return this.request(`/student/notifications/${notificationId}/mark_read/`, { method: 'POST' });
  }
  async requestSpendingUnlock(lockId: number): Promise<{ message: string }> {
    return this.request(`/student/spending-locks/${lockId}/request_unlock/`, { method: 'POST' });
  }
  async verifySpendingUnlock(lockId: number, otp: string): Promise<{ message: string }> {
    return this.request(`/student/spending-locks/${lockId}/verify_unlock_otp/`, {
      method: 'POST', body: JSON.stringify({ otp_code: otp }),
    });
  }

  // Parent endpoints
  async getLinkedStudents(): Promise<any> { return this.request('/parent/students/'); }
  async getStudentOverview(studentId: number): Promise<any> { return this.request(`/parent/students/${studentId}/overview/`); }
  async generateParentOTP(studentId: number, amount: number, reason: string): Promise<any> {
    return this.request('/parent/generate-otp/', {
      method: 'POST', body: JSON.stringify({ student_id: studentId, amount_requested: amount, reason }),
    });
  }
  async getParentAlerts(): Promise<any> { return this.request('/parent/alerts/'); }
  async markAlertAsRead(alertId: number): Promise<any> {
    return this.request(`/parent/alerts/${alertId}/mark_as_read/`, { method: 'PATCH' });
  }
  async generateSpendingUnlockOTP(lockId: number): Promise<{ message: string; expires_in_minutes: number }> {
    return this.request(`/student/spending-locks/${lockId}/generate_unlock_otp/`, { method: 'POST' });
  }
  async getParentWallet(): Promise<any> { return this.request('/parent/wallet/'); }
  async getParentBalance(): Promise<{ balance: number }> { return this.request('/parent/wallet/balance/'); }

  async getParentStatement(year?: number, month?: number, day?: number): Promise<any> {
    let url = '/parent/wallet/statement/';
    const params = new URLSearchParams();
    if (year) params.append('year', year.toString());
    if (month) params.append('month', month.toString());
    if (day) params.append('day', day.toString());
    const qs = params.toString();
    return this.request(qs ? `${url}?${qs}` : url);
  }

  async getStudentStatement(studentId: number, year?: number, month?: number, day?: number): Promise<any> {
    let url = '/parent/wallet/student_statement/';
    const params = new URLSearchParams();
    params.append('student_id', studentId.toString());
    if (year) params.append('year', year.toString());
    if (month) params.append('month', month.toString());
    if (day) params.append('day', day.toString());
    const qs = params.toString();
    return this.request(`${url}?${qs}`);
  }
  async recordParentExpense(amount: number, category: string, description: string = ''): Promise<any> {
    return this.request('/parent/wallet/record_expense/', {
      method: 'POST',
      body: JSON.stringify({ amount, category, description })
    });
  }

// Institute Module Endpoints
async getInstituteDashboard(): Promise<any> {
  return this.request('/institute/dashboard/');
}

async getInstitutes(): Promise<any> {
  return this.request('/institute/institutes/');
}

async createInstitute(data: { name: string; address?: string; contact_number?: string }): Promise<any> {
  return this.request('/institute/institutes/', {
    method: 'POST',
    body: JSON.stringify(data)
  });
}

async deleteInstitute(id: number): Promise<any> {
  return this.request(`/institute/institutes/${id}/`, {
    method: 'DELETE'
  });
}

async getInstituteStudents(): Promise<any> {  return this.request('/institute/student-profiles/');
}

async createInstituteStudent(data: any): Promise<any> {
  return this.request('/institute/student-profiles/', {
    method: 'POST',
    body: JSON.stringify(data)
  });
}

async linkInstituteStudent(data: { username: string; institute: number; monthly_fee: number; due_day?: number }): Promise<any> {
  return this.request('/institute/student-profiles/link_by_username/', {
    method: 'POST',
    body: JSON.stringify(data)
  });
}

async deleteInstituteStudent(id: number): Promise<any> {
  return this.request(`/institute/student-profiles/${id}/`, {
    method: 'DELETE'
  });
}

async getInstituteTeachers(): Promise<any> {
  return this.request('/institute/teachers/');
}

async updateTeacherProfile(id: number, data: any): Promise<any> {
  return this.request(`/institute/teachers/${id}/`, {
    method: 'PATCH',
    body: JSON.stringify(data)
  });
}

// Teacher Attendance & Payroll
async getTeacherAttendance(teacherId?: number, month?: number, year?: number): Promise<any> {
  const params = new URLSearchParams();
  if (teacherId) params.append('teacher', teacherId.toString());
  if (month) params.append('month', month.toString());
  if (year) params.append('year', year.toString());
  return this.request(`/institute/teacher-attendance/?${params.toString()}`);
}

async markTeacherAttendance(data: { teacher: number; date: string; status: string; extra_sessions?: number; remarks?: string }): Promise<any> {
  return this.request('/institute/teacher-attendance/', {
    method: 'POST',
    body: JSON.stringify(data)
  });
}

async calculateTeacherPayout(teacherId: number, month: number, year: number): Promise<any> {
  return this.request(`/institute/teacher-attendance/calculate_payout/?teacher_id=${teacherId}&month=${month}&year=${year}`);
}

async createInstituteStudent(data: any): Promise<any> {
  return this.request('/institute/teachers/', {
    method: 'POST',
    body: JSON.stringify(data)
  });
}

async markFeeAsPaid(data: { student_profile: number; month: number; year: number; amount: number }): Promise<any> {
  return this.request('/institute/fees/mark_paid/', {
    method: 'POST',
    body: JSON.stringify(data)
  });
}

async markSalaryAsPaid(data: { teacher_profile: number; month: number; year: number; amount: number }): Promise<any> {
  return this.request('/institute/salaries/mark_paid/', {
    method: 'POST',
    body: JSON.stringify(data)
  });
}

async payFeeSelf(paymentId: number): Promise<any> {
  return this.request(`/institute/fees/${paymentId}/pay_now/`, {
    method: 'POST'
  });
}

async sendFeeReminder(studentProfileId: number): Promise<any> {
  return this.request(`/institute/student-profiles/${studentProfileId}/send_fee_reminder/`, { method: 'POST' });
}
async sendInstituteNotice(studentProfileId: number, message: string): Promise<any> {
  return this.request(`/institute/student-profiles/${studentProfileId}/send_notice/`, { 
    method: 'POST',
    body: JSON.stringify({ message })
  });
}

async markAttendanceBulk(date: string, records: Array<{ student_profile: number; status: string }>): Promise<any> {
  return this.request('/institute/attendance/mark_bulk/', {
    method: 'POST',
    body: JSON.stringify({ date, records })
  });
}
async getFeeHistory(): Promise<any> {
  return this.request('/institute/fees/');
}

async getSalaryHistory(): Promise<any> {
  return this.request('/institute/salaries/');
}

async setTransactionPIN(pin: string): Promise<any> {    return this.request('/parent/wallet/set_transaction_pin/', {
      method: 'POST', body: JSON.stringify({ pin }),
    });
  }
  async transferToStudentSpecial(studentId: number, amount: number, pin: string): Promise<any> {
    return this.request('/parent/wallet/transfer_to_student_special/', {
      method: 'POST', body: JSON.stringify({ student_id: studentId, amount, pin }),
    });
  }

  async setStudentAllowance(studentId: number, monthlyAmount: number, dailyAllowance: number, daysInMonth: number, otpCode?: string): Promise<any> {
    return this.request('/student/monthly-allowances/', {
      method: 'POST',
      body: JSON.stringify({ 
        student: studentId, 
        monthly_amount: monthlyAmount, 
        daily_allowance: dailyAllowance, 
        days_in_month: daysInMonth,
        otp_code: otpCode
      }),
    });
  }
  async createSpendingLock(studentId: number, lockType: string, amountLocked: number, reason: string): Promise<any> {
    return this.request('/student/spending-locks/', {
      method: 'POST', body: JSON.stringify({ student: studentId, lock_type: lockType, amount_locked: amountLocked }),
    });
  }
  async removeSpendingLock(lockId: number): Promise<any> {
    return this.request(`/student/spending-locks/${lockId}/`, { method: 'DELETE' });
  }
  async linkStudent(studentUsername: string): Promise<any> {
    return this.request('/parent/link-student/', { method: 'POST', body: JSON.stringify({ student_username: studentUsername }) });
  }
  async unlinkStudent(studentId: number): Promise<any> {
    return this.request(`/student/parent-requests/${studentId}/unlink/`, { method: 'POST' });
  }
  async transferToStudent(studentId: number, amount: number, otpCode: string, otpRequestId?: number): Promise<any> {
    if (otpRequestId) {
      return this.request('/parent/wallet/verify-otp/', {
        method: 'POST', body: JSON.stringify({ otp_code: otpCode, otp_request_id: otpRequestId }),
      });
    }
    const otpResponse = await this.request<{ otp_request_id: number }>('/parent/wallet/generate-otp/', {
      method: 'POST', body: JSON.stringify({ operation_type: 'transfer_to_student', amount, student_id: studentId, description: 'Transfer to student wallet' }),
    });
    return this.request('/parent/wallet/verify-otp/', {
      method: 'POST', body: JSON.stringify({ otp_code: otpCode, otp_request_id: otpResponse.otp_request_id }),
    });
  }
  async verifyParentWalletOTP(otpCode: string, otpRequestId: number): Promise<any> {
    return this.request('/parent/wallet/verify-otp/', { method: 'POST', body: JSON.stringify({ otp_code: otpCode, otp_request_id: otpRequestId }) });
  }
  async depositToParentWallet(amount: number, description: string = 'Deposit'): Promise<any> {
    return this.request('/parent/wallet/deposit/', { method: 'POST', body: JSON.stringify({ amount, description }) });
  }
  async withdrawFromParentWallet(amount: number, description: string = 'Withdrawal'): Promise<any> {
    return this.request('/parent/wallet/withdraw/', { method: 'POST', body: JSON.stringify({ amount, description }) });
  }
  async getStudentOtpRequests(): Promise<any> {
    return this.request('/student/otp-requests/');
  }
  async getStudentOwnStatement(year?: number, month?: number, day?: number): Promise<any> {
    let url = '/student/wallet/statement/';
    const params = new URLSearchParams();
    if (year) params.append('year', year.toString());
    if (month) params.append('month', month.toString());
    if (day) params.append('day', day.toString());
    const qs = params.toString();
    return this.request(qs ? `${url}?${qs}` : url);
  }
  async requestUnlock(lockId: number): Promise<any> {
    return this.request(`/student/spending-locks/${lockId}/request_unlock/`, {
      method: 'POST'
    });
  }
  async selectPersona(persona: string): Promise<any> {
    return this.request('/student/users/select-persona/', { method: 'PATCH', body: JSON.stringify({ persona }) });
  }
  async verifyParentOTP(otpCode: string, otpRequestId: number, studentId: number): Promise<any> {
    return this.request('/student/wallet/verify-parent-otp/', { 
      method: 'POST', 
      body: JSON.stringify({ otp_code: otpCode, otp_request_id: otpRequestId, student_id: studentId }) 
    });
  }
  async withdrawStudent(amount: number): Promise<any> {
    const headers: HeadersInit = { 'Content-Type': 'application/json' };
    if (this.token) headers['Authorization'] = `Token ${this.token}`;
    const response = await fetch(`${API_BASE_URL}/student/wallet/withdraw/`, { method: 'POST', headers, body: JSON.stringify({ amount }) });
    if (response.status === 402) return response.json();
    if (!response.ok) {
      const error: ApiError = await response.json().catch(() => ({ error: 'Request failed' }));
      throw new Error(error.error || 'Request failed');
    }
    return response.json();
  }

  // Individual Module Endpoints
  async getIndividualDashboard(): Promise<any> { return this.request('/individual/wallet/balance/'); }

  async getIndividualStatement(year?: number, month?: number, day?: number): Promise<any> {
    let url = '/individual/wallet/statement/';
    const params = new URLSearchParams();
    if (year) params.append('year', year.toString());
    if (month) params.append('month', month.toString());
    if (day) params.append('day', day.toString());
    
    const queryString = params.toString();
    if (queryString) url += `?${queryString}`;
    
    return this.request(url);
  }
  async depositToIndividualWallet(amount: number, description: string = 'Deposit'): Promise<any> {
    return this.request('/individual/wallet/deposit/', { method: 'POST', body: JSON.stringify({ amount, description }) });
  }
  async withdrawFromIndividualWallet(amount: number, description: string = 'Withdrawal'): Promise<any> {
    return this.request('/individual/wallet/withdraw/', { method: 'POST', body: JSON.stringify({ amount, description }) });
  }
  async transferToIndividualSavings(amount: number, otp: string, otpRequestId: number, goalName: string = 'Savings Goal'): Promise<any> {
    return this.request('/individual/wallet/transfer_to_goal/', { method: 'POST', body: JSON.stringify({ amount, otp_code: otp, otp_request_id: otpRequestId, goal_name: goalName }) });
  }
  async recordIndividualExpense(amount: number, category: string, description: string = ''): Promise<any> {
    return this.request('/individual/expenses/', { method: 'POST', body: JSON.stringify({ amount, category, description }) });
  }
  async getIndividualSpendingAlerts(): Promise<any> { return this.request('/individual/expense-alerts/'); }
  async markIndividualAlertRead(alertId: number): Promise<any> {
    return this.request(`/individual/expense-alerts/${alertId}/mark_as_read/`, { method: 'PATCH' });
  }
  async getIndividualExpenseCategories(): Promise<any> { 
    return {
      categories: [
        { value: 'FOOD', label: 'Food & Dining', icon: '🍔' },
        { value: 'TRANSPORT', label: 'Transportation', icon: '🚗' },
        { value: 'UTILITIES', label: 'Utilities', icon: '💡' },
        { value: 'ENTERTAINMENT', label: 'Entertainment', icon: '🎬' },
        { value: 'SHOPPING', label: 'Shopping', icon: '🛒' },
        { value: 'HEALTH', label: 'Healthcare', icon: '🏥' },
        { value: 'EDUCATION', label: 'Education', icon: '📚' },
        { value: 'BILLS', label: 'Bills & Payments', icon: '📄' },
        { value: 'OTHER', label: 'Other', icon: '📦' }
      ]
    };
  }
  async getIndividualSpendingStats(): Promise<any> { return this.request('/individual/wallet/monthly_summary/'); }
  async generateIndividualDepositOTP(amount: number): Promise<any> {
    return this.request('/individual/generate-otp/', { method: 'POST', body: JSON.stringify({ operation_type: 'deposit', amount }) });
  }
  async generateIndividualSavingsOTP(amount: number): Promise<any> {
    return this.request('/individual/generate-otp/', { method: 'POST', body: JSON.stringify({ operation_type: 'transfer', amount }) });
  }
  async setMonthlyBudget(monthlyBudget: number): Promise<any> {
    return this.request('/individual/wallet/set_budget/', { method: 'POST', body: JSON.stringify({ monthly_budget: monthlyBudget }) });
  }
  async setSavingsGoal(savingsGoal: number): Promise<any> {
    return this.request('/individual/wallet/set_savings_goal/', { method: 'POST', body: JSON.stringify({ savings_goal: savingsGoal }) });
  }

  async getInvestmentSuggestions(): Promise<any> {
    return this.request('/individual/investment-suggestions/');
  }

  async getIndividualTodaySpending(): Promise<any> {
    return this.request('/individual/wallet/today_spending/');
  }

  async getIndividualMonthlySummary(): Promise<any> {
    return this.request('/individual/wallet/monthly_summary/');
  }

  async getIndividualDailySpendingSummary(): Promise<any> {
    return this.request('/individual/wallet/daily_spending_summary/');
  }

  async getIndividualYearlySpendingSummary(): Promise<any> {
    return this.request('/individual/wallet/yearly_spending_summary/');
  }

  async generateIndividualOTP(operationType: string, amount?: number, description?: string): Promise<any> {
    return this.request('/individual/generate-otp/', {
      method: 'POST',
      body: JSON.stringify({ operation_type: operationType, amount, description })
    });
  }

  async withdrawFromIndividualSavings(amount: number, otpCode: string, otpRequestId: number, description: string = 'Savings Withdrawal'): Promise<any> {
    return this.request('/individual/wallet/withdraw_from_savings/', {
      method: 'POST',
      body: JSON.stringify({ amount, otp_code: otpCode, otp_request_id: otpRequestId, description })
    });
  }

  // --- Couple Module Endpoints ---
  async getCoupleWallet(): Promise<any> { return this.request('/couple/wallet/balance/'); }
  async depositToCoupleWallet(amount: number, description: string = 'Deposit'): Promise<any> {
    return this.request('/couple/wallet/deposit/', { method: 'POST', body: JSON.stringify({ amount, description }) });
  }
  async withdrawFromCoupleWallet(amount: number, description: string = 'Withdrawal', category: string = 'OTHER'): Promise<any> {
    return this.request('/couple/wallet/withdraw/', { method: 'POST', body: JSON.stringify({ amount, description, category }) });
  }
  async getCoupleSpendingStats(): Promise<any> {
    return this.request('/couple/wallet/monthly_summary/');
  }
  async getCoupleTransactions(): Promise<any[]> {
    return this.request('/couple/wallet/transactions/');
  }
  async getCouplePersonalWallet(): Promise<any> {
    return this.request('/couple/wallet/personal/');
  }
  async createPersonalWallet(): Promise<any> {
    return this.request('/couple/wallet/personal/create/', { method: 'POST' });
  }
  async togglePersonalWalletVisibility(isVisible: boolean): Promise<any> {
    return this.request('/couple/wallet/personal/visibility/', { method: 'PATCH', body: JSON.stringify({ is_visible: isVisible }) });
  }
  async depositToPersonalWallet(amount: number): Promise<any> {
    return this.request('/couple/wallet/personal/deposit/', { method: 'POST', body: JSON.stringify({ amount }) });
  }
  async withdrawFromPersonalWallet(amount: number): Promise<any> {
    return this.request('/couple/wallet/personal/withdraw/', { method: 'POST', body: JSON.stringify({ amount }) });
  }
  async getCouplePersonalTransactions(): Promise<any[]> {
    return this.request('/couple/wallet/personal/transactions/');
  }
  async getJointGoals(): Promise<any> {
    return this.request('/couple/wallet/goals/');
  }
  async createJointGoal(name: string, target_amount: number, deadline: string): Promise<any> {
    return this.request('/couple/wallet/goals_create/', { method: 'POST', body: JSON.stringify({ name, target_amount, deadline }) });
  }
  async contributeToJointGoal(id: number, amount: number): Promise<any> {
    return this.request('/couple/wallet/goals_contribute/', { method: 'POST', body: JSON.stringify({ goal_id: id, amount }) });
  }
  async updateJointGoal(id: number, data: { name?: string, target_amount?: number, deadline?: string }): Promise<any> {
    return this.request('/couple/wallet/goals/update/', { 
      method: 'PATCH', 
      body: JSON.stringify({ goal_id: id, ...data }) 
    });
  }
  async getSpendingRequests(): Promise<any> {
    return this.request('/couple/spending-requests/');
  }
  async createSpendingRequest(amount: number, description: string, category: string): Promise<any> {
    return this.request('/couple/spending-requests/', { method: 'POST', body: JSON.stringify({ amount, description, category }) });
  }
  async respondToSpendingRequest(id: number, action: 'approve' | 'reject'): Promise<any> {
    return this.request(`/couple/spending-requests/${id}/respond/`, { method: 'POST', body: JSON.stringify({ action }) });
  }
  async getCoupleSettlement(): Promise<any> {
    return this.request('/couple/wallet/settlement/');
  }
  async setCoupleBudget(amount: number): Promise<any> {
    return this.request('/couple/wallet/set_budget/', { method: 'POST', body: JSON.stringify({ monthly_budget: amount }) });
  }
}

export const api = new ApiService();
