import React, { useState } from 'react';
import axios from 'axios';
import { toast } from 'sonner';

export default function Compliance({ user, setUser, axiosConfig, API }) {
    const [confirmDelete, setConfirmDelete] = useState(false);

    const handleConsentToggle = async () => {
        const newConsent = !user.data_consent;
        try {
            await axios.post(`${API}/compliance/consent?consent=${newConsent}`, {}, axiosConfig);
            setUser(prev => ({ ...prev, data_consent: newConsent }));
            toast.success(`Data consent ${newConsent ? 'granted' : 'revoked'}.`);
        } catch (error) {
            toast.error(error.response?.data?.detail || 'Failed to update consent.');
        }
    };

    const handleDataDownload = async () => {
        try {
            const response = await axios.get(`${API}/compliance/data`, { ...axiosConfig, responseType: 'blob' });
            const url = window.URL.createObjectURL(new Blob([response.data]));
            const link = document.createElement('a');
            link.href = url;
            link.setAttribute('download', 'amarktai_user_data.json');
            document.body.appendChild(link);
            link.click();
            link.remove();
            toast.success('User data download initiated.');
        } catch (error) {
            toast.error(error.response?.data?.detail || 'Failed to download user data.');
        }
    };

    const handleDeleteAccount = async () => {
        if (!confirmDelete) {
            setConfirmDelete(true);
            toast.warning('Please confirm account deletion. This is irreversible.');
            return;
        }
        
        try {
            await axios.delete(`${API}/compliance/account`, axiosConfig);
            toast.success('Account successfully deleted. Logging out...');
            localStorage.removeItem('token');
            window.location.href = '/login'; // Force redirect to login
        } catch (error) {
            toast.error(error.response?.data?.detail || 'Failed to delete account.');
            setConfirmDelete(false);
        }
    };

    return (
        <div className="security-card compliance-card">
            <h4>GDPR / POPIA Compliance</h4>
            
            <div className="compliance-item">
                <p>Data Processing Consent:</p>
                <label className="switch">
                    <input 
                        type="checkbox" 
                        checked={user?.data_consent || false} 
                        onChange={handleConsentToggle} 
                    />
                    <span className="slider round"></span>
                </label>
            </div>

            <div className="compliance-item">
                <p>Download All User Data:</p>
                <button onClick={handleDataDownload} className="btn-secondary">Download JSON</button>
            </div>

            <div className="compliance-item">
                <p>Delete Account & Data:</p>
                <button 
                    onClick={handleDeleteAccount} 
                    className={`btn-error ${confirmDelete ? 'btn-confirm' : ''}`}
                >
                    {confirmDelete ? 'Click to Confirm Deletion' : 'Delete Account'}
                </button>
            </div>
        </div>
    );
}
