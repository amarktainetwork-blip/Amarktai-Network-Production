import React, { useState } from 'react';
import axios from 'axios';
import { toast } from 'sonner';

export default function TwoFactorAuth({ user, setUser, axiosConfig, API }) {
    const [otpCode, setOtpCode] = useState('');
    const [qrCode, setQrCode] = useState(null);
    const [setupStep, setSetupStep] = useState(0); // 0: initial, 1: setup initiated, 2: verify
    const [tempSecret, setTempSecret] = useState('');

    const handleSetup = async () => {
        try {
            const response = await axios.get(`${API}/auth/2fa/setup`, axiosConfig);
            setQrCode(response.data.qr_code_base64);
            setTempSecret(response.data.secret);
            setSetupStep(1);
            toast.info(response.data.message);
        } catch (error) {
            toast.error(error.response?.data?.detail || 'Failed to initiate 2FA setup.');
        }
    };

    const handleEnable = async (e) => {
        e.preventDefault();
        try {
            await axios.post(`${API}/auth/2fa/enable`, { otp_code: otpCode }, axiosConfig);
            setUser(prev => ({ ...prev, is_2fa_enabled: true }));
            setSetupStep(0);
            setOtpCode('');
            setQrCode(null);
            toast.success('2FA successfully enabled!');
        } catch (error) {
            toast.error(error.response?.data?.detail || 'Invalid OTP code.');
        }
    };

    const handleDisable = async (e) => {
        e.preventDefault();
        try {
            await axios.post(`${API}/auth/2fa/disable`, { otp_code: otpCode }, axiosConfig);
            setUser(prev => ({ ...prev, is_2fa_enabled: false }));
            setSetupStep(0);
            setOtpCode('');
            toast.success('2FA successfully disabled!');
        } catch (error) {
            toast.error(error.response?.data?.detail || 'Invalid OTP code.');
        }
    };

    const renderSetup = () => (
        <div className="two-factor-setup">
            {qrCode && (
                <div className="qr-code-display">
                    <p>Scan this QR code with your authenticator app (e.g., Google Authenticator):</p>
                    <img src={`data:image/png;base64,${qrCode}`} alt="2FA QR Code" style={{ maxWidth: '200px', margin: '10px auto', display: 'block' }} />
                    <p>Or manually enter the secret: <strong>{tempSecret}</strong></p>
                </div>
            )}
            <form onSubmit={handleEnable}>
                <input
                    type="text"
                    value={otpCode}
                    onChange={(e) => setOtpCode(e.target.value)}
                    placeholder="Enter 6-digit code to verify"
                    required
                />
                <button type="submit" className="btn-success">Verify & Enable 2FA</button>
            </form>
            <button onClick={() => setSetupStep(0)} className="btn-secondary">Cancel</button>
        </div>
    );

    const renderDisable = () => (
        <div className="two-factor-disable">
            <form onSubmit={handleDisable}>
                <input
                    type="text"
                    value={otpCode}
                    onChange={(e) => setOtpCode(e.target.value)}
                    placeholder="Enter 6-digit code to disable"
                    required
                />
                <button type="submit" className="btn-error">Confirm Disable 2FA</button>
            </form>
            <button onClick={() => setSetupStep(0)} className="btn-secondary">Cancel</button>
        </div>
    );

    return (
        <div className="security-card">
            <h4>Two-Factor Authentication (2FA)</h4>
            {user?.is_2fa_enabled ? (
                <>
                    <p className="text-success">2FA is **ENABLED**.</p>
                    {setupStep === 2 ? renderDisable() : (
                        <button onClick={() => setSetupStep(2)} className="btn-warning">Disable 2FA</button>
                    )}
                </>
            ) : (
                <>
                    <p className="text-error">2FA is **DISABLED**.</p>
                    {setupStep === 1 ? renderSetup() : (
                        <button onClick={handleSetup} className="btn-primary">Enable 2FA</button>
                    )}
                </>
            )}
        </div>
    );
}
