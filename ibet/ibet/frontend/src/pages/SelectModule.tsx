import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../services/api';
import './SelectModule.css';

const modules = [
  { id: 'student', name: 'My Money Wallet', icon: '💰', persona: 'STUDENT' },
  { id: 'academic', name: 'My Academic Portal', icon: '🎓', persona: 'STUDENT_ACADEMIC' },
  { id: 'parent', name: 'Parent Dashboard', icon: '👨‍👩‍👧', persona: 'PARENT' },
  { id: 'individual', name: 'Individual Wallet', icon: '👤', persona: 'INDIVIDUAL' },
  { id: 'couple', name: 'Couple Wallet', icon: '💑', persona: 'COUPLE' },
  { id: 'institute', name: 'Institute Management', icon: '🏫', persona: 'INSTITUTE_OWNER' },
  { id: 'institute_teacher', name: 'Teacher Portal', icon: '👩‍🏫', persona: 'INSTITUTE_TEACHER' },
];

const personaMap: { [key: string]: string } = {
  'STUDENT': 'student',
  'STUDENT_ACADEMIC': 'academic',
  'PARENT': 'parent',
  'INDIVIDUAL': 'individual',
  'COUPLE': 'couple',
  'INSTITUTE_OWNER': 'institute',
  'INSTITUTE_TEACHER': 'institute'
};

export default function SelectModule() {
  const [selectedModule, setSelectedModule] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [initialCheck, setInitialCheck] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    const checkUserPersona = async () => {
      try {
        const profile = await api.getProfile();
        if (profile && profile.persona) {
          // Auto-redirect based on persona
          const route = personaMap[profile.persona];
          if (route) {
            navigate(`/dashboard/${route}`);
            return;
          }
        }
      } catch (err) {
        console.error('Failed to fetch profile during initial check:', err);
      } finally {
        setInitialCheck(false);
      }
    };

    checkUserPersona();
  }, [navigate]);

  if (initialCheck) {
    return <div className="loading">Checking account status...</div>;
  }

  const handleLogout = () => {
    api.clearToken();
    navigate('/login');
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedModule) {
      setError('Please select a module');
      return;
    }

    setLoading(true);
    setError('');

    try {
      // Find the selected module and its required persona
      const selectedMod = modules.find(m => m.id === selectedModule);
      
      if (selectedMod && selectedMod.persona) {
        console.log('Setting persona to:', selectedMod.persona);
        // Set the user's persona before navigating
        await api.selectPersona(selectedMod.persona);
        console.log('Persona set successfully');
      }
      
      navigate(`/dashboard/${selectedModule}`);
    } catch (err) {
      console.error('Failed to set persona:', err);
      // Still navigate even if persona setting fails - it might already be set
      navigate(`/dashboard/${selectedModule}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="select-module-container">
      <div className="select-module-card">
        <h1>IBET Wallet</h1>
        <h2>Select Your Module</h2>
        
        {error && <div className="error-message">{error}</div>}
        
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <select
              className="module-dropdown"
              value={selectedModule}
              onChange={(e) => {
                setSelectedModule(e.target.value);
                setError('');
              }}
              disabled={loading}
            >
              <option value="">-- Select Module --</option>
              {modules.map((module) => (
                <option key={module.id} value={module.id}>
                  {module.icon} {module.name}
                </option>
              ))}
            </select>
          </div>
          
          <button type="submit" className="go-btn" disabled={loading}>
            {loading ? 'Loading...' : 'Go'}
          </button>
        </form>
        
        <button onClick={handleLogout} className="logout-btn" style={{ marginTop: '1rem', background: 'transparent', color: 'var(--primary-color)', border: '1px solid var(--primary-color)' }}>
          Logout
        </button>
      </div>
    </div>
  );
}
