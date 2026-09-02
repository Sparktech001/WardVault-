import { useState } from 'react'
import axios from 'axios'
import { jwtDecode } from 'jwt-decode'
import { 
  ShieldCheckIcon, 
  ExclamationTriangleIcon, 
  LockClosedIcon, 
  UserIcon, 
  DocumentTextIcon, 
  KeyIcon, 
  ArrowRightOnRectangleIcon, 
  CheckCircleIcon 
} from '@heroicons/react/24/outline'

export default function App() {
  const [token, setToken] = useState(null)
  const [role, setRole] = useState("")
  const [username, setUsername] = useState("")
  const [password, setPassword] = useState("password123")
  const [authError, setAuthError] = useState("")

  const [patientId, setPatientId] = useState("test-patient-001")
  const [wardId, setWardId] = useState("ICU-A")
  const [isEmergency, setIsEmergency] = useState(false)
  const [reason, setReason] = useState("")
  const [accessResult, setAccessResult] = useState(null)
  const [accessError, setAccessError] = useState("")
  const [loading, setLoading] = useState(false)

  const handleLogin = async (e) => {
    e.preventDefault()
    setAuthError("")
    setLoading(true)
    try {
      const params = new URLSearchParams()
      params.append('username', username)
      params.append('password', password)
      const res = await axios.post("http://127.0.0.1:8000/api/login", params)
      const accessToken = res.data.access_token
      setToken(accessToken)
      setRole(jwtDecode(accessToken).role)
    } catch (err) {
      setAuthError("Authentication failed. Invalid credentials.")
    } finally {
      setLoading(false)
    }
  }

  const handleAccess = async (e) => {
    e.preventDefault()
    setAccessError("")
    setAccessResult(null)
    setLoading(true)
    try {
      const res = await axios.post(
        "http://127.0.0.1:8000/api/records/access",
        {
          patient_id: patientId,
          client_ward_id: wardId,
          is_emergency: isEmergency,
          override_reason: isEmergency ? reason : ""
        },
        { headers: { Authorization: `Bearer ${token}` } }
      )
      setAccessResult(res.data)
    } catch (err) {
      if (err.response) {
        setAccessError(err.response.data.detail.message || err.response.data.detail || "Access Denied")
      } else {
        setAccessError("Network or Server Error")
      }
    } finally {
      setLoading(false)
    }
  }

  const logout = () => {
    setToken(null)
    setRole("")
    setAccessResult(null)
    setIsEmergency(false)
  }

  // --- LOGIN VIEW ---
  if (!token) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50 px-4">
        <div className="max-w-md w-full bg-white rounded-2xl shadow-xl border border-slate-100 p-8">
          <div className="flex flex-col items-center mb-8">
            <div className="bg-slate-900 p-3 rounded-xl mb-4 shadow-lg">
              <ShieldCheckIcon className="w-8 h-8 text-white" />
            </div>
            <h2 className="text-2xl font-bold text-slate-900 tracking-tight">WardVault</h2>
            <p className="text-sm text-slate-500 mt-1">Cryptographic Access Gateway</p>
          </div>

          {authError && (
            <div className="mb-6 flex items-center p-4 text-sm text-red-800 bg-red-50 rounded-lg border border-red-200">
              <ExclamationTriangleIcon className="w-5 h-5 mr-2 flex-shrink-0" />
              {authError}
            </div>
          )}

          <form onSubmit={handleLogin} className="space-y-5">
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Provider ID</label>
              <div className="relative">
                <UserIcon className="w-5 h-5 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
                <input 
                  type="text"
                  className="w-full pl-10 pr-4 py-2.5 bg-slate-50 border border-slate-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all outline-none"
                  value={username} onChange={e => setUsername(e.target.value)} required 
                />
              </div>
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Passphrase</label>
              <div className="relative">
                <KeyIcon className="w-5 h-5 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
                <input 
                  type="password"
                  className="w-full pl-10 pr-4 py-2.5 bg-slate-50 border border-slate-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all outline-none"
                  value={password} onChange={e => setPassword(e.target.value)} required 
                />
              </div>
            </div>
            <button type="submit" disabled={loading} className="w-full bg-slate-900 hover:bg-slate-800 text-white font-medium py-2.5 rounded-lg transition-colors flex justify-center items-center">
              {loading ? 'Authenticating...' : 'Secure Login'}
            </button>
          </form>
        </div>
      </div>
    )
  }

  // --- SECURE DASHBOARD VIEW ---
  return (
    <div className="min-h-screen bg-slate-50 py-12 px-4">
      <div className="max-w-2xl mx-auto space-y-6">
        
        <div className="bg-white rounded-2xl shadow-sm border border-slate-200 p-6 flex justify-between items-center">
          <div className="flex items-center space-x-4">
            <div className="bg-slate-900 p-2.5 rounded-lg">
              <ShieldCheckIcon className="w-6 h-6 text-white" />
            </div>
            <div>
              <h1 className="text-xl font-bold text-slate-900 leading-tight">WardVault Gateway</h1>
              <p className="text-sm text-slate-500 font-medium">Session Active • {role}</p>
            </div>
          </div>
          <button onClick={logout} className="text-slate-500 hover:text-slate-900 transition-colors p-2 rounded-lg hover:bg-slate-100 flex items-center space-x-2 text-sm font-medium">
            <ArrowRightOnRectangleIcon className="w-4 h-4" />
            <span>Lock Vault</span>
          </button>
        </div>

        <div className="bg-white rounded-2xl shadow-sm border border-slate-200 p-6 md:p-8">
          <div className="mb-6 flex items-center space-x-2">
            <DocumentTextIcon className="w-5 h-5 text-blue-600" />
            <h2 className="text-lg font-semibold text-slate-900">Request Record Access</h2>
          </div>

          <form onSubmit={handleAccess} className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Patient ID</label>
                <input 
                  className="w-full px-4 py-2.5 bg-slate-50 border border-slate-200 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none transition-all"
                  value={patientId} onChange={e => setPatientId(e.target.value)} required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Client Ward ID</label>
                <input 
                  className="w-full px-4 py-2.5 bg-slate-50 border border-slate-200 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none transition-all"
                  value={wardId} onChange={e => setWardId(e.target.value)} required
                />
              </div>
            </div>

            {role !== "Billing Clerk" && (
              <div className={`rounded-xl border transition-all duration-300 ${isEmergency ? 'bg-red-50 border-red-200 p-5' : 'bg-slate-50 border-slate-200 p-5'}`}>
                <label className="flex items-center cursor-pointer group">
                  <div className="relative flex items-center">
                    <input type="checkbox" className="sr-only" checked={isEmergency} onChange={e => setIsEmergency(e.target.checked)} />
                    <div className={`block w-10 h-6 rounded-full transition-colors ${isEmergency ? 'bg-red-600' : 'bg-slate-300 group-hover:bg-slate-400'}`}></div>
                    <div className={`absolute left-1 top-1 bg-white w-4 h-4 rounded-full transition-transform ${isEmergency ? 'translate-x-4' : ''}`}></div>
                  </div>
                  <span className={`ml-3 text-sm font-semibold flex items-center ${isEmergency ? 'text-red-700' : 'text-slate-600'}`}>
                    {isEmergency && <ExclamationTriangleIcon className="w-4 h-4 mr-1.5" />}
                    Break-Glass Emergency Override
                  </span>
                </label>

                {isEmergency && (
                  <div className="mt-4 animate-in slide-in-from-top-2 opacity-100 duration-200">
                    <label className="block text-sm font-medium text-red-800 mb-1">Clinical Justification (Audited)</label>
                    <input 
                      type="text"
                      placeholder="e.g., Patient coding, need immediate history..."
                      className="w-full px-4 py-2.5 bg-white border border-red-200 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-red-500 outline-none transition-all placeholder:text-red-300"
                      value={reason} onChange={e => setReason(e.target.value)} required={isEmergency}
                    />
                  </div>
                )}
              </div>
            )}

            <button type="submit" disabled={loading} className={`w-full font-medium py-3 rounded-xl transition-all shadow-sm flex justify-center items-center space-x-2 text-white ${isEmergency ? 'bg-red-600 hover:bg-red-700 shadow-red-200' : 'bg-blue-600 hover:bg-blue-700 shadow-blue-200'}`}>
              <LockClosedIcon className="w-5 h-5" />
              <span>{loading ? 'Decrypting Vault...' : isEmergency ? 'Execute Emergency Override' : 'Retrieve Patient Record'}</span>
            </button>
          </form>
        </div>

        {accessError && (
          <div className="bg-red-50 rounded-xl p-5 border border-red-200 flex items-start space-x-3">
            <ExclamationTriangleIcon className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
            <div>
              <h3 className="text-red-800 font-semibold text-sm">Access Denied</h3>
              <p className="text-red-600 text-sm mt-1">{accessError}</p>
            </div>
          </div>
        )}
        
        {accessResult && (
          <div className="bg-green-50 rounded-xl p-5 border border-green-200">
            <div className="flex items-center space-x-2 mb-3">
              <CheckCircleIcon className="w-5 h-5 text-green-600" />
              <h3 className="text-green-800 font-semibold text-sm">Access Granted ({accessResult.status})</h3>
            </div>
            <div className="bg-slate-900 rounded-lg p-4 font-mono text-xs text-slate-300 overflow-hidden shadow-inner">
              <div className="flex justify-between border-b border-slate-700 pb-2 mb-2">
                <span className="text-slate-500">AUDIT HASH:</span>
                <span className="text-green-400">{accessResult.audit?.current_hash.substring(0, 32)}...</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">TIMESTAMP:</span>
                <span>{new Date().toISOString()}</span>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}