import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import './CreateRFP.css';

const CreateRFP = () => {
  const [text, setText] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!text.trim()) {
      setError('Please enter some text to generate an RFP');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const response = await fetch('http://localhost:8000/api/rfp/create-from-text/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ text }),
      });

      const data = await response.json();

      if (response.ok) {
        // Redirect to the created RFP detail page
        navigate(`/rfp/${data.rfp.id}`);
      } else {
        setError(data.error || 'Failed to create RFP');
        setLoading(false);
      }
    } catch (err) {
      setError('Network error: Unable to connect to the server');
      setLoading(false);
    }
  };

  return (
    <div className="create-rfp-container">
      <div className="create-rfp-card">
        <h1>Create RFP from Text</h1>
        <p className="subtitle">
          Describe your requirements in natural language, and we'll generate a structured RFP for you.
        </p>

        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label htmlFor="rfp-text">RFP Description</label>
            <textarea
              id="rfp-text"
              className="rfp-textarea"
              value={text}
              onChange={(e) => setText(e.target.value)}
              placeholder="Example: We need 50 laptops with 16GB RAM and 512GB SSD. We also need 10 external monitors (27 inch, 4K). Our budget is $75,000 and we need delivery by March 15, 2024."
              rows={10}
              disabled={loading}
            />
          </div>

          {error && (
            <div className="error-message">
              <span className="error-icon"></span>
              {error}
            </div>
          )}

          <button
            type="submit"
            className="generate-button"
            disabled={loading || !text.trim()}
          >
            {loading ? (
              <>
                <span className="spinner"></span>
                Generating RFP...
              </>
            ) : (
              'Generate RFP'
            )}
          </button>
        </form>

        <div className="help-text">
          <h3>Tips for better results:</h3>
          <ul>
            <li>Include specific quantities and specifications</li>
            <li>Mention your budget if you have one</li>
            <li>Add any deadline or delivery requirements</li>
            <li>Describe technical requirements in detail</li>
          </ul>
        </div>
      </div>
    </div>
  );
};

export default CreateRFP;
