import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import './ComparisonTable.css';

function ComparisonTable() {
  const { id } = useParams();
  const [rfpData, setRfpData] = useState(null);
  const [proposals, setProposals] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [lowestPriceId, setLowestPriceId] = useState(null);
  const [aiRecommendation, setAiRecommendation] = useState(null);
  const [loadingAi, setLoadingAi] = useState(false);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        setError(null);

        const response = await fetch(`http://localhost:8000/api/rfp/comparison/${id}/`);
        
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        setRfpData(data.rfp);
        setProposals(data.proposals);

        // Find the proposal with the lowest price
        if (data.proposals.length > 0) {
          const validProposals = data.proposals.filter(p => p.price && parseFloat(p.price) > 0);
          if (validProposals.length > 0) {
            const lowest = validProposals.reduce((min, proposal) => {
              const currentPrice = parseFloat(proposal.price);
              const minPrice = parseFloat(min.price);
              return currentPrice < minPrice ? proposal : min;
            });
            setLowestPriceId(lowest.id);
          }
        }
      } catch (err) {
        setError(err.message);
        console.error('Error fetching comparison data:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [id]);

  const fetchComparisonData = async () => {
    try {
      setLoading(true);
      setError(null);

      const response = await fetch(`http://localhost:8000/api/rfp/comparison/${id}/`);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      setRfpData(data.rfp);
      setProposals(data.proposals);

      // Find the proposal with the lowest price
      if (data.proposals.length > 0) {
        const validProposals = data.proposals.filter(p => p.price && parseFloat(p.price) > 0);
        if (validProposals.length > 0) {
          const lowest = validProposals.reduce((min, proposal) => {
            const currentPrice = parseFloat(proposal.price);
            const minPrice = parseFloat(min.price);
            return currentPrice < minPrice ? proposal : min;
          });
          setLowestPriceId(lowest.id);
        }
      }
    } catch (err) {
      setError(err.message);
      console.error('Error fetching comparison data:', err);
    } finally {
      setLoading(false);
    }
  };

  const formatPrice = (price) => {
    if (!price) return 'N/A';
    return `$${parseFloat(price).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
  };

  const getAiRecommendation = async () => {
    try {
      setLoadingAi(true);
      setError(null);

      const response = await fetch(`http://localhost:8000/api/rfp/ai-recommendation/${id}/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      setAiRecommendation(data.recommendation);
    } catch (err) {
      setError(err.message);
      console.error('Error getting AI recommendation:', err);
    } finally {
      setLoadingAi(false);
    }
  };

  if (loading) {
    return (
      <div className="comparison-container">
        <div className="loading-spinner">
          <div className="spinner"></div>
          <p>Loading comparison data...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="comparison-container">
        <div className="error-message">
          <h3>Error Loading Data</h3>
          <p>{error}</p>
          <button onClick={fetchComparisonData} className="retry-button">
            Retry
          </button>
        </div>
      </div>
    );
  }

  if (!rfpData) {
    return (
      <div className="comparison-container">
        <div className="error-message">
          <h3>No Data Found</h3>
          <p>RFP data could not be loaded.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="comparison-container">
      <div className="proposals-section">
        <div className="section-header">
          <h3>Vendor Proposals ({proposals.length})</h3>
          {proposals.length > 0 && (
            <button 
              onClick={getAiRecommendation} 
              className="ai-button"
              disabled={loadingAi}
            >
              {loadingAi ? (
                <>
                  <span className="button-spinner"></span>
                  Getting AI Recommendation...
                </>
              ) : (
                <>
                   Ask AI for Recommendation
                </>
              )}
            </button>
          )}
        </div>

        {aiRecommendation && (
          <div className="ai-recommendation-box">
            <div className="ai-recommendation-header">
              <span className="ai-icon"></span>
              <h4>AI Recommendation</h4>
              <button 
                className="close-button" 
                onClick={() => setAiRecommendation(null)}
                aria-label="Close"
              >
                ✕
              </button>
            </div>
            <div className="ai-recommendation-content">
              {aiRecommendation}
            </div>
          </div>
        )}
        
        {proposals.length === 0 ? (
          <div className="no-proposals">
            <p>No proposals have been submitted yet.</p>
          </div>
        ) : (
          <div className="table-container">
            <table className="comparison-table">
              <thead>
                <tr>
                  <th>Vendor Name</th>
                  <th>Total Price</th>
                  <th>Payment Terms</th>
                  <th>Warranty</th>
                  <th>Submitted At</th>
                </tr>
              </thead>
              <tbody>
                {proposals.map(proposal => (
                  <tr 
                    key={proposal.id}
                    className={proposal.id === lowestPriceId ? 'lowest-price' : ''}
                  >
                    <td className="vendor-cell">
                      <div className="vendor-name">{proposal.vendor_name}</div>
                      <div className="vendor-contact">{proposal.vendor_email}</div>
                      <div className="vendor-contact-person">{proposal.vendor_contact}</div>
                    </td>
                    <td className="price-cell">
                      {formatPrice(proposal.price)}
                      {proposal.id === lowestPriceId && (
                        <span className="best-price-badge">Lowest Price</span>
                      )}
                    </td>
                    <td className="terms-cell">
                      {proposal.payment_terms || 'Not specified'}
                    </td>
                    <td className="warranty-cell">
                      {proposal.warranty || 'Not specified'}
                    </td>
                    <td className="date-cell">
                      {new Date(proposal.submitted_at).toLocaleDateString('en-US', {
                        year: 'numeric',
                        month: 'short',
                        day: 'numeric',
                        hour: '2-digit',
                        minute: '2-digit'
                      })}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {proposals.length > 0 && lowestPriceId && (
        <div className="summary-section">
          <h3>Recommendation</h3>
          <div className="recommendation-card">
            {(() => {
              const bestProposal = proposals.find(p => p.id === lowestPriceId);
              return (
                <>
                  <p className="recommendation-text">
                    <strong>{bestProposal.vendor_name}</strong> offers the lowest price at{' '}
                    <strong>{formatPrice(bestProposal.price)}</strong>
                  </p>
                  <div className="recommendation-details">
                    <p><strong>Payment Terms:</strong> {bestProposal.payment_terms || 'Not specified'}</p>
                    <p><strong>Warranty:</strong> {bestProposal.warranty || 'Not specified'}</p>
                  </div>
                </>
              );
            })()}
          </div>
        </div>
      )}
    </div>
  );
}

export default ComparisonTable;
