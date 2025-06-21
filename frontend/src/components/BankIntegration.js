import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const BankIntegration = () => {
  const { dealId } = useParams();
  const [deal, setDeal] = useState(null);
  const [lenders, setLenders] = useState([]);
  const [creditApp, setCreditApp] = useState(null);
  const [submissions, setSubmissions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [showCreditApp, setShowCreditApp] = useState(false);
  const [creditData, setCreditData] = useState({
    ssn: '',
    date_of_birth: '',
    employment_status: 'full_time',
    employer_name: '',
    monthly_income: '',
    housing_status: 'rent',
    monthly_housing_payment: '',
    requested_amount: '',
    requested_term: 60,
    down_payment: 0
  });

  useEffect(() => {
    if (dealId) {
      fetchData();
    }
    fetchLenders();
  }, [dealId]);

  const fetchData = async () => {
    try {
      const [dealResponse, submissionsResponse] = await Promise.all([
        axios.get(`${API}/deals/${dealId}`),
        axios.get(`${API}/deals/${dealId}/lender-responses`)
      ]);
      
      setDeal(dealResponse.data);
      setSubmissions(submissionsResponse.data);
      
      // Set default loan amount
      setCreditData(prev => ({
        ...prev,
        requested_amount: dealResponse.data.total_deal_amount || 0,
        down_payment: dealResponse.data.finance_terms?.down_payment || 0
      }));
      
      setLoading(false);
    } catch (error) {
      console.error('Error fetching data:', error);
      setLoading(false);
    }
  };

  const fetchLenders = async () => {
    try {
      const response = await axios.get(`${API}/lenders`);
      setLenders(response.data);
    } catch (error) {
      console.error('Error fetching lenders:', error);
    }
  };

  const createCreditApplication = async () => {
    try {
      const response = await axios.post(`${API}/deals/${dealId}/credit-application`, creditData);
      setCreditApp(response.data);
      setShowCreditApp(false);
      alert('Credit application created successfully!');
    } catch (error) {
      console.error('Error creating credit application:', error);
      alert('Error creating credit application');
    }
  };

  const submitToLenders = async (selectedLenderIds) => {
    setSubmitting(true);
    try {
      const response = await axios.post(`${API}/deals/${dealId}/submit-to-lenders`, {
        lender_ids: selectedLenderIds,
        loan_amount: creditData.requested_amount,
        loan_term: creditData.requested_term
      });
      
      alert(`Submitted to ${response.data.submissions.length} lenders successfully!`);
      fetchData(); // Refresh to get responses
    } catch (error) {
      console.error('Error submitting to lenders:', error);
      alert('Error submitting to lenders');
    } finally {
      setSubmitting(false);
    }
  };

  const handleInputChange = (field, value) => {
    setCreditData(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const getSubmissionStatus = (submission) => {
    const statusColors = {
      submitted: 'bg-blue-100 text-blue-800',
      pending: 'bg-yellow-100 text-yellow-800',
      approved: 'bg-green-100 text-green-800',
      declined: 'bg-red-100 text-red-800',
      conditional: 'bg-orange-100 text-orange-800'
    };
    
    return (
      <span className={`px-2 py-1 rounded-full text-xs font-medium ${statusColors[submission.status] || 'bg-gray-100 text-gray-800'}`}>
        {submission.status.replace('_', ' ').toUpperCase()}
      </span>
    );
  };

  const getLenderSpecialty = (lender, submission) => {
    let creditScore = deal?.customer?.credit_score || 650;
    
    if (creditScore >= 720) return '🌟 Prime Rate';
    if (creditScore >= 650) return '✅ Standard Rate';
    if (creditScore >= 600) return '⚠️ Near Prime';
    return '🔴 Subprime';
  };

  const getRecommendedLenders = () => {
    const creditScore = deal?.customer?.credit_score || 650;
    
    return lenders.filter(lender => {
      if (creditScore >= lender.min_credit_score) return true;
      if (lender.specialties.includes('subprime') && creditScore >= 500) return true;
      return false;
    });
  };

  const getBestOffer = () => {
    const approvedSubmissions = submissions.filter(s => s.status === 'approved');
    if (approvedSubmissions.length === 0) return null;
    
    return approvedSubmissions.reduce((best, current) => {
      if (!best || current.approved_rate < best.approved_rate) {
        return current;
      }
      return best;
    }, null);
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  const recommendedLenders = getRecommendedLenders();
  const bestOffer = getBestOffer();

  return (
    <div className="max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <h1 className="text-2xl font-bold text-gray-900">Bank Integration & Rate Shopping</h1>
        {deal && (
          <div className="mt-2">
            <p className="text-gray-600">
              Deal {deal.deal_number} • {deal.customer.first_name} {deal.customer.last_name}
            </p>
            <p className="text-sm text-gray-500">
              Loan Amount: ${creditData.requested_amount?.toLocaleString()} • 
              Customer Credit Score: {deal.customer.credit_score || 'Not Available'}
            </p>
          </div>
        )}
      </div>

      {/* Best Offer Alert */}
      {bestOffer && (
        <div className="bg-green-50 border border-green-200 rounded-xl p-4">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <span className="text-green-600 text-2xl">🎉</span>
            </div>
            <div className="ml-3">
              <h3 className="text-lg font-medium text-green-800">Best Approved Offer</h3>
              <p className="text-green-700">
                <strong>{lenders.find(l => l.id === bestOffer.lender_id)?.name}</strong> - 
                <strong> {bestOffer.approved_rate}% APR</strong> for {bestOffer.approved_term} months - 
                <strong> ${((bestOffer.approved_amount * (bestOffer.approved_rate/100/12) * Math.pow(1 + bestOffer.approved_rate/100/12, bestOffer.approved_term)) / (Math.pow(1 + bestOffer.approved_rate/100/12, bestOffer.approved_term) - 1)).toFixed(2)}/month</strong>
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Credit Application Modal */}
      {showCreditApp && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl p-6 max-w-2xl w-full mx-4 max-h-screen overflow-y-auto">
            <h3 className="text-lg font-semibold mb-4">Credit Application</h3>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">SSN (Last 4 digits)</label>
                <input
                  type="text"
                  maxLength="4"
                  value={creditData.ssn}
                  onChange={(e) => handleInputChange('ssn', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Date of Birth</label>
                <input
                  type="date"
                  value={creditData.date_of_birth}
                  onChange={(e) => handleInputChange('date_of_birth', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Employment Status</label>
                <select
                  value={creditData.employment_status}
                  onChange={(e) => handleInputChange('employment_status', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="full_time">Full Time</option>
                  <option value="part_time">Part Time</option>
                  <option value="self_employed">Self Employed</option>
                  <option value="retired">Retired</option>
                  <option value="unemployed">Unemployed</option>
                </select>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Employer Name</label>
                <input
                  type="text"
                  value={creditData.employer_name}
                  onChange={(e) => handleInputChange('employer_name', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Monthly Income</label>
                <input
                  type="number"
                  value={creditData.monthly_income}
                  onChange={(e) => handleInputChange('monthly_income', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Housing Status</label>
                <select
                  value={creditData.housing_status}
                  onChange={(e) => handleInputChange('housing_status', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="rent">Rent</option>
                  <option value="own">Own</option>
                  <option value="other">Other</option>
                </select>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Monthly Housing Payment</label>
                <input
                  type="number"
                  value={creditData.monthly_housing_payment}
                  onChange={(e) => handleInputChange('monthly_housing_payment', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Loan Term (months)</label>
                <select
                  value={creditData.requested_term}
                  onChange={(e) => handleInputChange('requested_term', parseInt(e.target.value))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value={36}>36 months</option>
                  <option value={48}>48 months</option>
                  <option value={60}>60 months</option>
                  <option value={72}>72 months</option>
                  <option value={84}>84 months</option>
                </select>
              </div>
            </div>

            <div className="flex justify-end space-x-3">
              <button
                onClick={() => setShowCreditApp(false)}
                className="px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50 transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={createCreditApplication}
                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
              >
                Submit Application
              </button>
            </div>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Available Lenders */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-lg font-semibold text-gray-900">Available Lenders</h2>
            {!creditApp && (
              <button
                onClick={() => setShowCreditApp(true)}
                className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-md text-sm transition-colors"
              >
                Create Credit App
              </button>
            )}
          </div>
          
          <div className="space-y-4">
            {recommendedLenders.map((lender) => {
              const hasSubmission = submissions.find(s => s.lender_id === lender.id);
              
              return (
                <div key={lender.id} className="border rounded-lg p-4">
                  <div className="flex justify-between items-start mb-2">
                    <div>
                      <h3 className="font-medium">{lender.name}</h3>
                      <p className="text-sm text-gray-600">
                        {getLenderSpecialty(lender)} • Min Credit: {lender.min_credit_score}
                      </p>
                    </div>
                    {hasSubmission && getSubmissionStatus(hasSubmission)}
                  </div>
                  
                  <div className="text-sm text-gray-600 mb-3">
                    <p>Max LTV: {(lender.max_ltv * 100).toFixed(0)}%</p>
                    <p>Specialties: {lender.specialties.join(', ')}</p>
                    <div className="text-xs mt-1">
                      <span>Rates: </span>
                      {Object.entries(lender.interest_rates).map(([term, rate]) => (
                        <span key={term} className="mr-2">{term}mo: {rate}%</span>
                      ))}
                    </div>
                  </div>
                  
                  {!hasSubmission && creditApp && (
                    <button
                      onClick={() => submitToLenders([lender.id])}
                      disabled={submitting}
                      className="w-full bg-green-600 hover:bg-green-700 text-white py-2 px-4 rounded-md text-sm transition-colors disabled:opacity-50"
                    >
                      {submitting ? 'Submitting...' : 'Submit Application'}
                    </button>
                  )}
                  
                  {hasSubmission && hasSubmission.status === 'approved' && (
                    <div className="bg-green-50 p-3 rounded-md">
                      <div className="text-sm font-medium text-green-800">
                        Approved: ${hasSubmission.approved_amount?.toLocaleString()} 
                        at {hasSubmission.approved_rate}% for {hasSubmission.approved_term} months
                      </div>
                      <div className="text-xs text-green-600 mt-1">
                        Monthly Payment: ${((hasSubmission.approved_amount * (hasSubmission.approved_rate/100/12) * Math.pow(1 + hasSubmission.approved_rate/100/12, hasSubmission.approved_term)) / (Math.pow(1 + hasSubmission.approved_rate/100/12, hasSubmission.approved_term) - 1)).toFixed(2)}
                      </div>
                    </div>
                  )}
                  
                  {hasSubmission && hasSubmission.status === 'conditional' && (
                    <div className="bg-orange-50 p-3 rounded-md">
                      <div className="text-sm font-medium text-orange-800">
                        Conditional Approval - Stipulations Required:
                      </div>
                      <ul className="text-xs text-orange-600 mt-1">
                        {hasSubmission.stipulations?.map((stip, index) => (
                          <li key={index}>• {stip}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                  
                  {hasSubmission && hasSubmission.status === 'declined' && (
                    <div className="bg-red-50 p-3 rounded-md">
                      <div className="text-sm font-medium text-red-800">
                        Declined: {hasSubmission.decline_reason}
                      </div>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
          
          {creditApp && recommendedLenders.length > 0 && (
            <button
              onClick={() => submitToLenders(recommendedLenders.map(l => l.id))}
              disabled={submitting}
              className="w-full mt-4 bg-blue-600 hover:bg-blue-700 text-white py-3 px-4 rounded-md font-semibold transition-colors disabled:opacity-50"
            >
              {submitting ? 'Submitting to All Lenders...' : 'Submit to All Recommended Lenders'}
            </button>
          )}
        </div>

        {/* Submission Results */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Lender Responses</h2>
          
          {submissions.length === 0 ? (
            <div className="text-center py-8">
              <div className="text-gray-400 text-4xl mb-4">🏦</div>
              <h3 className="text-lg font-medium text-gray-900 mb-2">No Submissions Yet</h3>
              <p className="text-gray-600">Create a credit application and submit to lenders</p>
            </div>
          ) : (
            <div className="space-y-4">
              {submissions.map((submission) => {
                const lender = lenders.find(l => l.id === submission.lender_id);
                
                return (
                  <div key={submission.id} className="border rounded-lg p-4">
                    <div className="flex justify-between items-start mb-2">
                      <h3 className="font-medium">{lender?.name || 'Unknown Lender'}</h3>
                      {getSubmissionStatus(submission)}
                    </div>
                    
                    <div className="text-sm text-gray-600 mb-2">
                      <p>Submitted: {new Date(submission.submitted_at).toLocaleDateString()}</p>
                      {submission.responded_at && (
                        <p>Responded: {new Date(submission.responded_at).toLocaleDateString()}</p>
                      )}
                    </div>
                    
                    {submission.status === 'approved' && (
                      <div className="bg-green-50 p-3 rounded-md">
                        <div className="grid grid-cols-2 gap-2 text-sm">
                          <div>
                            <span className="font-medium">Amount:</span> ${submission.approved_amount?.toLocaleString()}
                          </div>
                          <div>
                            <span className="font-medium">Rate:</span> {submission.approved_rate}%
                          </div>
                          <div>
                            <span className="font-medium">Term:</span> {submission.approved_term} months
                          </div>
                          <div>
                            <span className="font-medium">Payment:</span> ${((submission.approved_amount * (submission.approved_rate/100/12) * Math.pow(1 + submission.approved_rate/100/12, submission.approved_term)) / (Math.pow(1 + submission.approved_rate/100/12, submission.approved_term) - 1)).toFixed(2)}
                          </div>
                        </div>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>

      {/* Quick Stats */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Submission Summary</h2>
        
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="text-center p-4 bg-gray-50 rounded-lg">
            <div className="text-2xl font-bold text-gray-900">{submissions.length}</div>
            <div className="text-sm text-gray-600">Total Submissions</div>
          </div>
          
          <div className="text-center p-4 bg-green-50 rounded-lg">
            <div className="text-2xl font-bold text-green-600">
              {submissions.filter(s => s.status === 'approved').length}
            </div>
            <div className="text-sm text-green-600">Approved</div>
          </div>
          
          <div className="text-center p-4 bg-orange-50 rounded-lg">
            <div className="text-2xl font-bold text-orange-600">
              {submissions.filter(s => s.status === 'conditional').length}
            </div>
            <div className="text-sm text-orange-600">Conditional</div>
          </div>
          
          <div className="text-center p-4 bg-red-50 rounded-lg">
            <div className="text-2xl font-bold text-red-600">
              {submissions.filter(s => s.status === 'declined').length}
            </div>
            <div className="text-sm text-red-600">Declined</div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default BankIntegration;