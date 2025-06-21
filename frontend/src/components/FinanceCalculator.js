import React, { useState } from 'react';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const FinanceCalculator = ({ dealId, onFinanceAdded }) => {
  const [financeData, setFinanceData] = useState({
    loan_amount: '',
    apr: '',
    term_months: 60,
    down_payment: ''
  });
  const [calculation, setCalculation] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleInputChange = (field, value) => {
    setFinanceData(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const calculatePayment = async () => {
    if (!financeData.loan_amount || !financeData.apr) {
      alert('Please enter loan amount and APR');
      return;
    }

    setLoading(true);
    try {
      const response = await axios.post(`${API}/finance/calculate`, {
        loan_amount: parseFloat(financeData.loan_amount),
        apr: parseFloat(financeData.apr),
        term_months: parseInt(financeData.term_months),
        down_payment: parseFloat(financeData.down_payment) || 0
      });
      setCalculation(response.data);
    } catch (error) {
      console.error('Error calculating finance:', error);
      alert('Error calculating finance terms');
    } finally {
      setLoading(false);
    }
  };

  const addFinanceToDeal = async () => {
    if (!calculation) {
      alert('Please calculate finance terms first');
      return;
    }

    setLoading(true);
    try {
      await axios.post(`${API}/deals/${dealId}/finance`, {
        loan_amount: parseFloat(financeData.loan_amount),
        apr: parseFloat(financeData.apr),
        term_months: parseInt(financeData.term_months),
        down_payment: parseFloat(financeData.down_payment) || 0
      });
      alert('Finance terms added to deal successfully!');
      onFinanceAdded();
    } catch (error) {
      console.error('Error adding finance to deal:', error);
      alert('Error adding finance terms to deal');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
      <h2 className="text-lg font-semibold text-gray-900 mb-6">Finance Calculator</h2>
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Input Section */}
        <div className="space-y-4">
          <h3 className="font-medium text-gray-900">Loan Details</h3>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Loan Amount *</label>
            <input
              type="number"
              step="0.01"
              value={financeData.loan_amount}
              onChange={(e) => handleInputChange('loan_amount', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="Enter loan amount"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">APR (%) *</label>
            <input
              type="number"
              step="0.01"
              value={financeData.apr}
              onChange={(e) => handleInputChange('apr', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="Enter APR"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Term (Months)</label>
            <select
              value={financeData.term_months}
              onChange={(e) => handleInputChange('term_months', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value={12}>12 months</option>
              <option value={24}>24 months</option>
              <option value={36}>36 months</option>
              <option value={48}>48 months</option>
              <option value={60}>60 months</option>
              <option value={72}>72 months</option>
              <option value={84}>84 months</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Down Payment</label>
            <input
              type="number"
              step="0.01"
              value={financeData.down_payment}
              onChange={(e) => handleInputChange('down_payment', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="Enter down payment"
            />
          </div>

          <button
            onClick={calculatePayment}
            disabled={loading}
            className="w-full bg-blue-600 hover:bg-blue-700 text-white py-2 px-4 rounded-md font-medium disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {loading ? 'Calculating...' : 'Calculate Payment'}
          </button>
        </div>

        {/* Results Section */}
        <div className="space-y-4">
          <h3 className="font-medium text-gray-900">Payment Calculation</h3>
          
          {calculation ? (
            <div className="bg-gray-50 rounded-lg p-4 space-y-3">
              <div className="flex justify-between items-center">
                <span className="text-gray-600">Monthly Payment:</span>
                <span className="text-2xl font-bold text-blue-600">
                  ${calculation.monthly_payment?.toLocaleString()}
                </span>
              </div>
              
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-600">Loan Amount:</span>
                  <span className="font-medium">${calculation.loan_amount?.toLocaleString()}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">APR:</span>
                  <span className="font-medium">{calculation.apr}%</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Term:</span>
                  <span className="font-medium">{calculation.term_months} months</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Down Payment:</span>
                  <span className="font-medium">${calculation.down_payment?.toLocaleString()}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Total Interest:</span>
                  <span className="font-medium">${calculation.total_interest?.toLocaleString()}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Total Cost:</span>
                  <span className="font-medium">${calculation.total_cost?.toLocaleString()}</span>
                </div>
              </div>

              <button
                onClick={addFinanceToDeal}
                disabled={loading}
                className="w-full bg-green-600 hover:bg-green-700 text-white py-2 px-4 rounded-md font-medium disabled:opacity-50 disabled:cursor-not-allowed transition-colors mt-4"
              >
                {loading ? 'Adding to Deal...' : 'Add to Deal'}
              </button>
            </div>
          ) : (
            <div className="bg-gray-50 rounded-lg p-8 text-center text-gray-500">
              <div className="text-4xl mb-2">🧮</div>
              <p>Enter loan details and click Calculate Payment to see results</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default FinanceCalculator;