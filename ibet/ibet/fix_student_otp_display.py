# Script to fix StudentDashboard.tsx to display OTP when parent approval is needed

with open('frontend/src/pages/StudentDashboard.tsx', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Add displayedOtp state after showParentOtpInput
old_state = "const [showParentOtpInput, setShowParentOtpInput] = useState(false);"
new_state = """const [showParentOtpInput, setShowParentOtpInput] = useState(false);
  const [displayedOtp, setDisplayedOtp] = useState<string | null>(null);"""
content = content.replace(old_state, new_state)

# 2. Update handleSubmit to capture OTP from response - first occurrence
old_response_check = """          // Check if it succeeded or needs parent approval (402 response)
          if (response && (response.status === 'pending_approval' || response.requires_parent_otp)) {
            setPendingOtpRequestId(response.otp_request_id || response.request_id || null);
            setShowParentOtpInput(true);
            setSuccess(response.message || 'Parent approval needed for this transaction');
            setSubmitting(false);
            return;
          }"""
new_response_check = """          // Check if it succeeded or needs parent approval (402 response)
          if (response && (response.status === 'pending_approval' || response.requires_parent_otp)) {
            setPendingOtpRequestId(response.otp_request_id || response.request_id || null);
            setShowParentOtpInput(true);
            // Store OTP for display if provided in response
            if (response.debug_otp) {
              setDisplayedOtp(response.debug_otp);
            }
            setSuccess(response.message || 'Parent approval needed for this transaction');
            setSubmitting(false);
            return;
          }"""
content = content.replace(old_response_check, new_response_check)

# 3. Update the second response check (for withdrawals exceeding limit)
old_response_check2 = """          // Check if parent approval is needed
          if (response && (response.status === 'pending_approval' || response.requires_parent_otp)) {
            setPendingOtpRequestId(response.otp_request_id || response.request_id || null);
            setShowParentOtpInput(true);
            setSuccess(response.message || 'Parent approval needed for this transaction');
            setSubmitting(false);
            return;
          }
          
          setSuccess('Withdrawal successful!');"""
new_response_check2 = """          // Check if parent approval is needed
          if (response && (response.status === 'pending_approval' || response.requires_parent_otp)) {
            setPendingOtpRequestId(response.otp_request_id || response.request_id || null);
            setShowParentOtpInput(true);
            // Store OTP for display if provided in response
            if (response.debug_otp) {
              setDisplayedOtp(response.debug_otp);
            }
            setSuccess(response.message || 'Parent approval needed for this transaction');
            setSubmitting(false);
            return;
          }
          
          setSuccess('Withdrawal successful!');"""
content = content.replace(old_response_check2, new_response_check2)

# 4. Update handleCancelParentOtp to clear displayed OTP
old_cancel = """  const handleCancelParentOtp = () => {
    setShowParentOtpInput(false);
    setPendingOtpRequestId(null);
    setPendingParentOtp('');
    setSuccess('');
  };"""
new_cancel = """  const handleCancelParentOtp = () => {
    setShowParentOtpInput(false);
    setPendingOtpRequestId(null);
    setPendingParentOtp('');
    setDisplayedOtp(null);
    setSuccess('');
  };"""
content = content.replace(old_cancel, new_cancel)

# 5. Add OTP display in the Parent OTP verification section
old_otp_section = """        {/* Parent OTP Verification Section */}
        {showParentOtpInput && (
          <div className="parent-otp-card">
            <h3>🔐 Parent Approval Required</h3>
            <p>Your daily limit has been exceeded. Please get the OTP from your parent to complete the transaction.</p>
            
            {txError && <div className="error-message">{txError}</div>}
            {success && <div className="success-message">{success}</div>}
            
            <div className="form-group">
              <label>Parent OTP</label>"""

new_otp_section = """        {/* Parent OTP Verification Section */}
        {showParentOtpInput && (
          <div className="parent-otp-card">
            <h3>🔐 Parent Approval Required</h3>
            <p>Your daily limit has been exceeded. Please get the OTP from your parent to complete the transaction.</p>
            
            {/* Display OTP for student to share with parent */}
            {displayedOtp && (
              <div style={{ 
                margin: '1rem 0', 
                padding: '1.5rem', 
                background: 'linear-gradient(135deg, #8e44ad 0%, #9b59b6 100%)', 
                borderRadius: '12px', 
                textAlign: 'center',
                boxShadow: '0 4px 12px rgba(142, 68, 173, 0.3)'
              }}>
                <div style={{ color: 'white', fontSize: '0.9rem', marginBottom: '0.5rem', textTransform: 'uppercase', letterSpacing: '1px' }}>
                  OTP for Parent Approval
                </div>
                <div style={{ color: 'white', fontSize: '2.5rem', fontWeight: 'bold', fontFamily: 'monospace', letterSpacing: '8px', textShadow: '0 2px 4px rgba(0,0,0,0.2)' }}>
                  {displayedOtp}
                </div>
                <div style={{ color: 'rgba(255,255,255,0.85)', fontSize: '0.8rem', marginTop: '0.5rem' }}>
                  Share this OTP with your parent
                </div>
              </div>
            )}
            
            {txError && <div className="error-message">{txError}</div>}
            {success && <div className="success-message">{success}</div>}
            
            <div className="form-group">
              <label>Parent OTP</label>"""
content = content.replace(old_otp_section, new_otp_section)

with open('frontend/src/pages/StudentDashboard.tsx', 'w', encoding='utf-8') as f:
    f.write(content)

print('Done! StudentDashboard OTP display fixed')
