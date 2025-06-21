import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const DealForm = () => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [formData, setFormData] = useState({
    // Customer Info
    customer: {
      first_name: '',
      last_name: '',
      email: '',
      phone: '',
      address: '',
      city: '',
      state: 'CA',
      zip_code: '',
      ssn_last_four: '',
      credit_score: ''
    },
    // Vehicle Info
    vehicle: {
      vin: '',
      year: new Date().getFullYear(),
      make: '',
      model: '',
      trim: '',
      condition: 'used',
      mileage: '',
      msrp: '',
      invoice_price: '',
      selling_price: ''
    },
    // Trade-in Info
    trade_in: {
      enabled: false,
      vin: '',
      year: '',
      make: '',
      model: '',
      mileage: '',
      condition: 'average',
      estimated_value: '',
      payoff_amount: ''
    },
    salesperson: ''
  });

  const handleInputChange = (section, field, value) => {
    setFormData(prev => ({
      ...prev,
      [section]: {
        ...prev[section],
        [field]: value
      }
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      const dealData = {
        customer: formData.customer,
        vehicle: {
          ...formData.vehicle,
          year: parseInt(formData.vehicle.year),
          mileage: parseInt(formData.vehicle.mileage) || 0,
          msrp: parseFloat(formData.vehicle.msrp) || 0,
          invoice_price: parseFloat(formData.vehicle.invoice_price) || null,
          selling_price: parseFloat(formData.vehicle.selling_price) || 0
        },
        salesperson: formData.salesperson || null
      };

      // Add trade-in if enabled
      if (formData.trade_in.enabled && formData.trade_in.make) {
        dealData.trade_in = {
          vin: formData.trade_in.vin || null,
          year: parseInt(formData.trade_in.year),
          make: formData.trade_in.make,
          model: formData.trade_in.model,
          mileage: parseInt(formData.trade_in.mileage),
          condition: formData.trade_in.condition,
          estimated_value: parseFloat(formData.trade_in.estimated_value) || 0,
          payoff_amount: parseFloat(formData.trade_in.payoff_amount) || 0
        };
      }

      const response = await axios.post(`${API}/deals`, dealData);
      navigate(`/deal/${response.data.id}`);
    } catch (error) {
      console.error('Error creating deal:', error);
      alert('Error creating deal. Please check all fields and try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto">
      <div className="bg-white rounded-xl shadow-sm border border-gray-200">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-2xl font-bold text-gray-900">Create New Deal</h2>
          <p className="text-gray-600 mt-1">Enter customer and vehicle information to start the deal</p>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-8">
          {/* Customer Information */}
          <div>
            <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
              <span className="bg-blue-100 text-blue-800 rounded-full w-6 h-6 flex items-center justify-center text-sm font-bold mr-3">1</span>
              Customer Information
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">First Name *</label>
                <input
                  type="text"
                  required
                  value={formData.customer.first_name}
                  onChange={(e) => handleInputChange('customer', 'first_name', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Last Name *</label>
                <input
                  type="text"
                  required
                  value={formData.customer.last_name}
                  onChange={(e) => handleInputChange('customer', 'last_name', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
                <input
                  type="email"
                  value={formData.customer.email}
                  onChange={(e) => handleInputChange('customer', 'email', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Phone</label>
                <input
                  type="tel"
                  value={formData.customer.phone}
                  onChange={(e) => handleInputChange('customer', 'phone', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">State</label>
                <select
                  value={formData.customer.state}
                  onChange={(e) => handleInputChange('customer', 'state', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="CA">California</option>
                  <option value="TX">Texas</option>
                  <option value="FL">Florida</option>
                  <option value="NY">New York</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Credit Score</label>
                <input
                  type="number"
                  min="300"
                  max="850"
                  value={formData.customer.credit_score}
                  onChange={(e) => handleInputChange('customer', 'credit_score', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
            </div>
          </div>

          {/* Vehicle Information */}
          <div>
            <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
              <span className="bg-blue-100 text-blue-800 rounded-full w-6 h-6 flex items-center justify-center text-sm font-bold mr-3">2</span>
              Vehicle Information
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">VIN *</label>
                <input
                  type="text"
                  required
                  maxLength="17"
                  value={formData.vehicle.vin}
                  onChange={(e) => handleInputChange('vehicle', 'vin', e.target.value.toUpperCase())}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 font-mono"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Year *</label>
                <input
                  type="number"
                  required
                  min="1990"
                  max="2025"
                  value={formData.vehicle.year}
                  onChange={(e) => handleInputChange('vehicle', 'year', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Make *</label>
                <input
                  type="text"
                  required
                  value={formData.vehicle.make}
                  onChange={(e) => handleInputChange('vehicle', 'make', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Model *</label>
                <input
                  type="text"
                  required
                  value={formData.vehicle.model}
                  onChange={(e) => handleInputChange('vehicle', 'model', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Condition</label>
                <select
                  value={formData.vehicle.condition}
                  onChange={(e) => handleInputChange('vehicle', 'condition', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="new">New</option>
                  <option value="used">Used</option>
                  <option value="certified">Certified Pre-Owned</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Mileage</label>
                <input
                  type="number"
                  min="0"
                  value={formData.vehicle.mileage}
                  onChange={(e) => handleInputChange('vehicle', 'mileage', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">MSRP</label>
                <input
                  type="number"
                  min="0"
                  step="0.01"
                  value={formData.vehicle.msrp}
                  onChange={(e) => handleInputChange('vehicle', 'msrp', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Invoice Price</label>
                <input
                  type="number"
                  min="0"
                  step="0.01"
                  value={formData.vehicle.invoice_price}
                  onChange={(e) => handleInputChange('vehicle', 'invoice_price', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Selling Price *</label>
                <input
                  type="number"
                  required
                  min="0"
                  step="0.01"
                  value={formData.vehicle.selling_price}
                  onChange={(e) => handleInputChange('vehicle', 'selling_price', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
            </div>
          </div>

          {/* Trade-in Information */}
          <div>
            <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
              <span className="bg-blue-100 text-blue-800 rounded-full w-6 h-6 flex items-center justify-center text-sm font-bold mr-3">3</span>
              Trade-in Information
            </h3>
            
            <div className="mb-4">
              <label className="flex items-center">
                <input
                  type="checkbox"
                  checked={formData.trade_in.enabled}
                  onChange={(e) => handleInputChange('trade_in', 'enabled', e.target.checked)}
                  className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                />
                <span className="ml-2 text-sm font-medium text-gray-700">Customer has trade-in vehicle</span>
              </label>
            </div>

            {formData.trade_in.enabled && (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Year *</label>
                  <input
                    type="number"
                    required
                    min="1990"
                    max="2025"
                    value={formData.trade_in.year}
                    onChange={(e) => handleInputChange('trade_in', 'year', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Make *</label>
                  <input
                    type="text"
                    required
                    value={formData.trade_in.make}
                    onChange={(e) => handleInputChange('trade_in', 'make', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Model *</label>
                  <input
                    type="text"
                    required
                    value={formData.trade_in.model}
                    onChange={(e) => handleInputChange('trade_in', 'model', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Mileage *</label>
                  <input
                    type="number"
                    required
                    min="0"
                    value={formData.trade_in.mileage}
                    onChange={(e) => handleInputChange('trade_in', 'mileage', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Estimated Value *</label>
                  <input
                    type="number"
                    required
                    min="0"
                    step="0.01"
                    value={formData.trade_in.estimated_value}
                    onChange={(e) => handleInputChange('trade_in', 'estimated_value', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Payoff Amount</label>
                  <input
                    type="number"
                    min="0"
                    step="0.01"
                    value={formData.trade_in.payoff_amount}
                    onChange={(e) => handleInputChange('trade_in', 'payoff_amount', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
              </div>
            )}
          </div>

          {/* Additional Information */}
          <div>
            <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
              <span className="bg-blue-100 text-blue-800 rounded-full w-6 h-6 flex items-center justify-center text-sm font-bold mr-3">4</span>
              Additional Information
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Salesperson</label>
                <input
                  type="text"
                  value={formData.salesperson}
                  onChange={(e) => handleInputChange('salesperson', '', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
            </div>
          </div>

          {/* Submit Button */}
          <div className="flex justify-end space-x-4 pt-6 border-t border-gray-200">
            <button
              type="button"
              onClick={() => navigate('/')}
              className="px-6 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50 transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading}
              className="px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {loading ? 'Creating Deal...' : 'Create Deal'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default DealForm;