import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import './RFPDetail.css';

const RFPDetail = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [rfp, setRfp] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [vendors, setVendors] = useState([]);
  const [selectedVendors, setSelectedVendors] = useState([]);
  const [showVendorModal, setShowVendorModal] = useState(false);
  const [sending, setSending] = useState(false);
  const [sendSuccess, setSendSuccess] = useState(null);

  useEffect(() => {
    fetchRFPDetails();
    fetchVendors();
  }, [id]);
  const fetchRFPDetails = async () => {
    try {
      const response = await fetch(`http://localhost:8000/api/rfp/${id}/`);
      
      if (response.ok) {
        const data = await response.json();
        setRfp(data);
      } else {
        setError('Failed to load RFP details');
      }
    } catch (err) {
      setError('Network error: Unable to connect to the server');
    } finally {
      setLoading(false);
    }
  };

  const fetchVendors = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/rfp/vendors/');
      if (response.ok) {
        const data = await response.json();
        setVendors(data);
      }
    } catch (err) {
      console.error('Failed to fetch vendors:', err);
    }
  };

  const handleVendorToggle = (vendorId) => {
    setSelectedVendors(prev => 
      prev.includes(vendorId)
        ? prev.filter(id => id !== vendorId)
        : [...prev, vendorId]
    );
  };

  const handleSendToVendors = async () => {
    if (selectedVendors.length === 0) {
      alert('Please select at least one vendor');
      return;
    }

    setSending(true);
    setSendSuccess(null);

    try {
      const response = await fetch(`http://localhost:8000/api/rfp/rfps/${id}/send-rfp-emails/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ vendor_ids: selectedVendors }),
      });

      const data = await response.json();

      if (response.ok) {
        setSendSuccess(`Successfully sent RFP to ${data.emails_sent} vendor(s)`);
        setShowVendorModal(false);
        setSelectedVendors([]);
        // Refresh RFP details to update status
        fetchRFPDetails();
      } else {
        alert(`Failed to send emails: ${data.error || 'Unknown error'}`);
      }
    } catch (err) {
      alert('Network error: Unable to send emails');
    } finally {
      setSending(false);
    }
  };

  if (loading) {
    return (
      <div className="rfp-detail-container">
        <div className="loading-spinner-large">
          <div className="spinner"></div>
          <p>Loading RFP details...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="rfp-detail-container">
        <div className="error-container">
          <h2> Error</h2>
          <p>{error}</p>
          <button onClick={() => navigate('/')} className="back-button">
            Back to Create RFP
          </button>
        </div>
      </div>
    );
  }

  if (!rfp) {
    return (
      <div className="rfp-detail-container">
        <div className="error-container">
          <h2>RFP Not Found</h2>
          <p>The requested RFP could not be found.</p>
          <button onClick={() => navigate('/')} className="back-button">
            Back to Create RFP
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="rfp-detail-container">
      <div className="rfp-detail-card">
        <div className="rfp-header">
          <button onClick={() => navigate('/')} className="back-link">
            ← Back
          </button>
          <div className="status-badge status-draft">
            {rfp.status}
          </div>
        </div>

        <h1 className="rfp-title">{rfp.title}</h1>
        
        <div className="rfp-meta">
          <div className="meta-item">
            <span className="meta-label">RFP ID:</span>
            <span className="meta-value">#{rfp.id}</span>
          </div>
          <div className="meta-item">
            <span className="meta-label">Deadline:</span>
            <span className="meta-value">
              {new Date(rfp.deadline).toLocaleDateString('en-US', {
                year: 'numeric',
                month: 'long',
                day: 'numeric'
              })}
            </span>
          </div>
          {rfp.budget && (
            <div className="meta-item">
              <span className="meta-label">Budget:</span>
              <span className="meta-value budget-value">
                ${parseFloat(rfp.budget).toLocaleString('en-US', { minimumFractionDigits: 2 })}
              </span>
            </div>
          )}
        </div>

        <div className="rfp-section">
          <h2>Original Request</h2>
          <div className="natural-language-box">
            {rfp.natural_language_input}
          </div>
        </div>

        <div className="rfp-section">
          <h2>Items ({rfp.items?.length || 0})</h2>
          {rfp.items && rfp.items.length > 0 ? (
            <div className="items-grid">
              {rfp.items.map((item) => (
                <div key={item.id} className="item-card">
                  <div className="item-header">
                    <h3>{item.name}</h3>
                    <span className="item-quantity">
                      Qty: {item.quantity}
                    </span>
                  </div>
                  {item.specifications && (
                    <div className="item-specifications">
                      <strong>Specifications:</strong>
                      <p>{item.specifications}</p>
                    </div>
                  )}
                </div>
              ))}
            </div>
          ) : (
            <p className="no-items">No items found for this RFP</p>
          )}
        </div>

        <div className="action-buttons">
          <button onClick={() => navigate('/')} className="btn-secondary">
            Create Another RFP
          </button>
          <button 
            onClick={() => setShowVendorModal(true)} 
            className="btn-primary"
          >
             Send to Vendors
          </button>
          <button 
            onClick={() => navigate(`/comparison/${id}`)} 
            className="btn-secondary"
          >
             View Comparison
          </button>
        </div>

        {sendSuccess && (
          <div className="success-message">
            ✓ {sendSuccess}
          </div>
        )}
      </div>

      {/* Vendor Selection Modal */}
      {showVendorModal && (
        <div className="vendor-modal-overlay" onClick={() => setShowVendorModal(false)}>
          <div className="vendor-modal" onClick={(e) => e.stopPropagation()}>
            <h2>Select Vendors to Send RFP</h2>
            
            {sendSuccess && (
              <div className="success-message">
                ✓ {sendSuccess}
              </div>
            )}
            
            <div className="vendor-list">
              {vendors.length === 0 ? (
                <p>No vendors available. Please create vendors first.</p>
              ) : (
                vendors.map(vendor => (
                  <div 
                    key={vendor.id} 
                    className={`vendor-item ${selectedVendors.includes(vendor.id) ? 'selected' : ''}`}
                    onClick={() => handleVendorToggle(vendor.id)}
                  >
                    <input
                      type="checkbox"
                      checked={selectedVendors.includes(vendor.id)}
                      onChange={() => handleVendorToggle(vendor.id)}
                    />
                    <div className="vendor-info">
                      <h3>{vendor.name}</h3>
                      <p>Email: {vendor.email}</p>
                      <p>Contact: {vendor.contact_person}</p>
                    </div>
                  </div>
                ))
              )}
            </div>
            
            <div className="modal-actions">
              <button 
                onClick={() => setShowVendorModal(false)} 
                className="btn-cancel"
              >
                Cancel
              </button>
              <button 
                onClick={handleSendToVendors} 
                className="btn-send"
                disabled={sending || selectedVendors.length === 0}
              >
                {sending ? 'Sending...' : `Send to ${selectedVendors.length} Vendor(s)`}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default RFPDetail;
