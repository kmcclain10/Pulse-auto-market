import React, { useState, useEffect } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import axios from 'axios';
import FinanceCalculator from './FinanceCalculator';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const DealDetails = () => {
  const { dealId } = useParams();
  const navigate = useNavigate();
  const [deal, setDeal] = useState(null);
  const [loading, setLoading] = useState(true);
  const [showFinanceCalculator, setShowFinanceCalculator] = useState(false);

  useEffect(() => {
    fetchDeal();
  }, [dealId]);

  const fetchDeal = async () => {
    try {
      const response = await axios.get(`${API}/deals/${dealId}`);
      setDeal(response.data);
      setLoading(false);
    } catch (error) {
      console.error('Error fetching deal:', error);
      setLoading(false);
    }
  };

  const updateDealStatus = async (status) => {
    try {
      await axios.put(`${API}/deals/${dealId}/status`, status, {
        headers: { 'Content-Type': 'application/json' }
      });
      setDeal(prev => ({ ...prev, status }));
    } catch (error) {
      console.error('Error updating deal status:', error);
    }
  };

  const getStatusBadge = (status) => {
    const statusColors = {
      pending: 'bg-yellow-100 text-yellow-800',
      in_progress: 'bg-blue-100 text-blue-800',
      completed: 'bg-green-100 text-green-800',
      cancelled: 'bg-red-100 text-red-800'
    };
    
    return (
      <span className={`px-3 py-1 rounded-full text-sm font-medium ${statusColors[status] || 'bg-gray-100 text-gray-800'}`}>
        {status?.replace('_', ' ').toUpperCase() || 'UNKNOWN'}
      </span>
    );
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (!deal) {
    return (
      <div className="text-center py-12">
        <div className="text-gray-400 text-6xl mb-4">❌</div>
        <h3 className="text-lg font-medium text-gray-900 mb-2">Deal not found</h3>
        <Link to="/" className="text-blue-600 hover:text-blue-800">← Back to Dashboard</Link>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      {/* Header */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <div className="flex justify-between items-start">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Deal {deal.deal_number}</h1>
            <p className="text-gray-600 mt-1">
              {deal.customer.first_name} {deal.customer.last_name} • 
              {deal.vehicle.year} {deal.vehicle.make} {deal.vehicle.model}
            </p>
          </div>
          <div className="flex items-center space-x-4">
            {getStatusBadge(deal.status)}
            <div className="flex space-x-2">
              <Link
                to={`/deal/${deal.id}/financing`}
                className="bg-purple-600 hover:bg-purple-700 text-white px-4 py-2 rounded-lg font-medium transition-colors"
              >
                🏦 Financing
              </Link>
              <Link
                to={`/deal/${deal.id}/forms`}
                className="bg-orange-600 hover:bg-orange-700 text-white px-4 py-2 rounded-lg font-medium transition-colors"
              >
                📋 Forms
              </Link>
              <Link
                to={`/deal/${deal.id}/documents`}
                className="bg-indigo-600 hover:bg-indigo-700 text-white px-4 py-2 rounded-lg font-medium transition-colors"
              >
                📄 Docs
              </Link>
              <Link
                to={`/deal/${deal.id}/signatures`}
                className="bg-emerald-600 hover:bg-emerald-700 text-white px-4 py-2 rounded-lg font-medium transition-colors"
              >
                ✍️ E-Sign
              </Link>
              <Link
                to={`/deal/${deal.id}/menu`}
                className="bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-lg font-medium transition-colors"
              >
                💰 F&I Menu
              </Link>
              <Link
                to="/"
                className="text-gray-600 hover:text-gray-800 px-4 py-2 rounded-lg border border-gray-300 transition-colors"
              >
                ← Back
              </Link>
            </div>
          </div>
        </div>

        {/* Status Update */}
        <div className="mt-4 pt-4 border-t border-gray-200">
          <label className="block text-sm font-medium text-gray-700 mb-2">Update Status:</label>
          <select
            value={deal.status}
            onChange={(e) => updateDealStatus(e.target.value)}
            className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="pending">Pending</option>
            <option value="in_progress">In Progress</option>
            <option value="completed">Completed</option>
            <option value="cancelled">Cancelled</option>
          </select>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Customer Information */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Customer Information</h2>
          <div className="space-y-3">
            <div className="flex justify-between">
              <span className="text-gray-600">Name:</span>
              <span className="font-medium">{deal.customer.first_name} {deal.customer.last_name}</span>
            </div>
            {deal.customer.email && (
              <div className="flex justify-between">
                <span className="text-gray-600">Email:</span>
                <span className="font-medium">{deal.customer.email}</span>
              </div>
            )}
            {deal.customer.phone && (
              <div className="flex justify-between">
                <span className="text-gray-600">Phone:</span>
                <span className="font-medium">{deal.customer.phone}</span>
              </div>
            )}
            {deal.customer.state && (
              <div className="flex justify-between">
                <span className="text-gray-600">State:</span>
                <span className="font-medium">{deal.customer.state}</span>
              </div>
            )}
            {deal.customer.credit_score && (
              <div className="flex justify-between">
                <span className="text-gray-600">Credit Score:</span>
                <span className="font-medium">{deal.customer.credit_score}</span>
              </div>
            )}
          </div>
        </div>

        {/* Vehicle Information */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Vehicle Information</h2>
          <div className="space-y-3">
            <div className="flex justify-between">
              <span className="text-gray-600">VIN:</span>
              <span className="font-medium font-mono text-sm">{deal.vehicle.vin}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">Vehicle:</span>
              <span className="font-medium">{deal.vehicle.year} {deal.vehicle.make} {deal.vehicle.model}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">Condition:</span>
              <span className="font-medium capitalize">{deal.vehicle.condition}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">Mileage:</span>
              <span className="font-medium">{deal.vehicle.mileage?.toLocaleString() || 'N/A'}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">MSRP:</span>
              <span className="font-medium">${deal.vehicle.msrp?.toLocaleString() || 'N/A'}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">Selling Price:</span>
              <span className="font-medium text-green-600">${deal.vehicle.selling_price?.toLocaleString()}</span>
            </div>
          </div>
        </div>
      </div>

      {/* Trade-in Information */}
      {deal.trade_in && (
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Trade-in Information</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="space-y-3">
              <div className="flex justify-between">
                <span className="text-gray-600">Vehicle:</span>
                <span className="font-medium">{deal.trade_in.year} {deal.trade_in.make} {deal.trade_in.model}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Mileage:</span>
                <span className="font-medium">{deal.trade_in.mileage?.toLocaleString()}</span>
              </div>
            </div>
            <div className="space-y-3">
              <div className="flex justify-between">
                <span className="text-gray-600">Estimated Value:</span>
                <span className="font-medium">${deal.trade_in.estimated_value?.toLocaleString()}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Payoff Amount:</span>
                <span className="font-medium">${deal.trade_in.payoff_amount?.toLocaleString()}</span>
              </div>
            </div>
            <div className="space-y-3">
              <div className="flex justify-between">
                <span className="text-gray-600">Net Trade Value:</span>
                <span className="font-medium text-green-600">${deal.trade_in.net_trade_value?.toLocaleString()}</span>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Financial Summary */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-lg font-semibold text-gray-900">Financial Summary</h2>
          <button
            onClick={() => setShowFinanceCalculator(!showFinanceCalculator)}
            className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg font-medium transition-colors"
          >
            {showFinanceCalculator ? 'Hide Calculator' : 'Finance Calculator'}
          </button>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <div className="text-center p-4 bg-gray-50 rounded-lg">
            <div className="text-2xl font-bold text-gray-900">${deal.total_vehicle_price?.toLocaleString()}</div>
            <div className="text-sm text-gray-600">Vehicle Price</div>
          </div>
          <div className="text-center p-4 bg-gray-50 rounded-lg">
            <div className="text-2xl font-bold text-gray-900">${deal.total_fees_taxes?.toLocaleString()}</div>
            <div className="text-sm text-gray-600">Fees & Taxes</div>
          </div>
          <div className="text-center p-4 bg-gray-50 rounded-lg">
            <div className="text-2xl font-bold text-gray-900">${deal.total_fi_products?.toLocaleString()}</div>
            <div className="text-sm text-gray-600">F&I Products</div>
          </div>
          <div className="text-center p-4 bg-blue-50 rounded-lg">
            <div className="text-2xl font-bold text-blue-600">${deal.total_deal_amount?.toLocaleString()}</div>
            <div className="text-sm text-blue-600">Total Deal</div>
          </div>
        </div>

        {/* Tax Breakdown */}
        {deal.tax_calculation && (
          <div className="mt-6 pt-6 border-t border-gray-200">
            <h3 className="font-medium text-gray-900 mb-3">Tax & Fee Breakdown</h3>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
              <div className="flex justify-between">
                <span className="text-gray-600">Sales Tax ({(deal.tax_calculation.sales_tax_rate * 100).toFixed(2)}%):</span>
                <span>${deal.tax_calculation.sales_tax_amount?.toLocaleString()}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Title Fee:</span>
                <span>${deal.tax_calculation.title_fee?.toLocaleString()}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">License Fee:</span>
                <span>${deal.tax_calculation.license_fee?.toLocaleString()}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Doc Fee:</span>
                <span>${deal.tax_calculation.doc_fee?.toLocaleString()}</span>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Finance Calculator */}
      {showFinanceCalculator && (
        <FinanceCalculator dealId={dealId} onFinanceAdded={fetchDeal} />
      )}

      {/* Finance Terms */}
      {deal.finance_terms && (
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Finance Terms</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="space-y-3">
              <div className="flex justify-between">
                <span className="text-gray-600">Loan Amount:</span>
                <span className="font-medium">${deal.finance_terms.loan_amount?.toLocaleString()}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">APR:</span>
                <span className="font-medium">{deal.finance_terms.apr}%</span>
              </div>
            </div>
            <div className="space-y-3">
              <div className="flex justify-between">
                <span className="text-gray-600">Term:</span>
                <span className="font-medium">{deal.finance_terms.term_months} months</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Down Payment:</span>
                <span className="font-medium">${deal.finance_terms.down_payment?.toLocaleString()}</span>
              </div>
            </div>
            <div className="space-y-3">
              <div className="flex justify-between">
                <span className="text-gray-600">Monthly Payment:</span>
                <span className="font-medium text-blue-600">${deal.finance_terms.monthly_payment?.toLocaleString()}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Total Interest:</span>
                <span className="font-medium">${deal.finance_terms.total_interest?.toLocaleString()}</span>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default DealDetails;