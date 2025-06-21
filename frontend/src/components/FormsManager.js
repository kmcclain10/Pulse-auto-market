import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const FormsManager = () => {
  const { dealId } = useParams();
  const [deal, setDeal] = useState(null);
  const [formTemplates, setFormTemplates] = useState([]);
  const [dealForms, setDealForms] = useState([]);
  const [selectedState, setSelectedState] = useState('CA');
  const [loading, setLoading] = useState(true);
  const [activeForm, setActiveForm] = useState(null);
  const [formData, setFormData] = useState({});

  useEffect(() => {
    if (dealId) {
      fetchDealData();
    }
    fetchFormTemplates();
  }, [dealId, selectedState]);

  const fetchDealData = async () => {
    try {
      const response = await axios.get(`${API}/deals/${dealId}`);
      setDeal(response.data);
      setSelectedState(response.data.customer.state || 'CA');
    } catch (error) {
      console.error('Error fetching deal:', error);
    }
  };

  const fetchFormTemplates = async () => {
    try {
      const response = await axios.get(`${API}/forms/templates?state=${selectedState}`);
      setFormTemplates(response.data);
      
      if (dealId) {
        const formsResponse = await axios.get(`${API}/deals/${dealId}/forms`);
        setDealForms(formsResponse.data);
      }
      
      setLoading(false);
    } catch (error) {
      console.error('Error fetching form templates:', error);
      setLoading(false);
    }
  };

  const createForm = async (template) => {
    try {
      const response = await axios.post(`${API}/deals/${dealId}/forms`, {
        template_id: template.form_type,
        form_type: template.form_type,
        field_values: {}
      });
      
      setDealForms(prev => [...prev, response.data]);
      setActiveForm(response.data);
      setFormData({});
    } catch (error) {
      console.error('Error creating form:', error);
      alert('Error creating form');
    }
  };

  const updateForm = async (formId, updatedData) => {
    try {
      await axios.put(`${API}/forms/${formId}`, {
        field_values: updatedData,
        status: 'draft'
      });
      
      // Refresh forms
      fetchDealData();
      alert('Form updated successfully');
    } catch (error) {
      console.error('Error updating form:', error);
      alert('Error updating form');
    }
  };

  const handleFieldChange = (fieldName, value) => {
    setFormData(prev => ({
      ...prev,
      [fieldName]: value
    }));
  };

  const renderFormField = (field) => {
    const value = formData[field.name] || activeForm?.field_values?.[field.name] || '';

    switch (field.type) {
      case 'text':
        return (
          <input
            type="text"
            value={value}
            onChange={(e) => handleFieldChange(field.name, e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            required={field.required}
          />
        );
      
      case 'number':
        return (
          <input
            type="number"
            value={value}
            onChange={(e) => handleFieldChange(field.name, e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            required={field.required}
          />
        );
      
      case 'currency':
        return (
          <input
            type="number"
            step="0.01"
            value={value}
            onChange={(e) => handleFieldChange(field.name, e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            required={field.required}
          />
        );
      
      case 'date':
        return (
          <input
            type="date"
            value={value}
            onChange={(e) => handleFieldChange(field.name, e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            required={field.required}
          />
        );
      
      case 'select':
        return (
          <select
            value={value}
            onChange={(e) => handleFieldChange(field.name, e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            required={field.required}
          >
            <option value="">Select {field.label}</option>
            {field.options?.map((option) => (
              <option key={option} value={option}>{option}</option>
            ))}
          </select>
        );
      
      case 'textarea':
        return (
          <textarea
            value={value}
            onChange={(e) => handleFieldChange(field.name, e.target.value)}
            rows={3}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            required={field.required}
          />
        );
      
      case 'signature':
        return (
          <div className="border-2 border-dashed border-gray-300 rounded-md p-4 text-center">
            <span className="text-gray-500">Digital signature will be captured here</span>
            <button className="mt-2 bg-blue-600 text-white px-4 py-2 rounded-md text-sm">
              Capture Signature
            </button>
          </div>
        );
      
      default:
        return (
          <input
            type="text"
            value={value}
            onChange={(e) => handleFieldChange(field.name, e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            required={field.required}
          />
        );
    }
  };

  const getFormStatus = (form) => {
    const statusColors = {
      draft: 'bg-gray-100 text-gray-800',
      pending_signature: 'bg-yellow-100 text-yellow-800',
      signed: 'bg-green-100 text-green-800',
      completed: 'bg-blue-100 text-blue-800'
    };
    
    return (
      <span className={`px-2 py-1 rounded-full text-xs font-medium ${statusColors[form.status] || 'bg-gray-100 text-gray-800'}`}>
        {form.status?.replace('_', ' ').toUpperCase()}
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

  return (
    <div className="max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <h1 className="text-2xl font-bold text-gray-900">Forms Management</h1>
        {deal && (
          <p className="text-gray-600 mt-1">
            Deal {deal.deal_number} • {deal.customer.first_name} {deal.customer.last_name}
          </p>
        )}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Forms List */}
        <div className="lg:col-span-1">
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Required Forms</h2>
            
            {/* State Selector */}
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-1">State</label>
              <select
                value={selectedState}
                onChange={(e) => setSelectedState(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="CA">California</option>
                <option value="TX">Texas</option>
                <option value="FL">Florida</option>
                <option value="NY">New York</option>
              </select>
            </div>

            <div className="space-y-3">
              {formTemplates.map((template) => {
                const existingForm = dealForms.find(f => f.form_type === template.form_type);
                
                return (
                  <div key={template.form_type} className="border rounded-lg p-3">
                    <div className="flex justify-between items-start mb-2">
                      <h3 className="font-medium text-sm">{template.title}</h3>
                      {template.required && (
                        <span className="bg-red-100 text-red-800 text-xs px-2 py-1 rounded-full">
                          Required
                        </span>
                      )}
                    </div>
                    <p className="text-xs text-gray-600 mb-2">{template.description}</p>
                    
                    {existingForm ? (
                      <div className="flex items-center justify-between">
                        {getFormStatus(existingForm)}
                        <button
                          onClick={() => setActiveForm(existingForm)}
                          className="text-blue-600 hover:text-blue-800 text-sm"
                        >
                          Edit
                        </button>
                      </div>
                    ) : (
                      <button
                        onClick={() => createForm(template)}
                        className="w-full bg-blue-600 hover:bg-blue-700 text-white py-1 px-3 rounded text-sm transition-colors"
                        disabled={!dealId}
                      >
                        Create Form
                      </button>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        </div>

        {/* Form Editor */}
        <div className="lg:col-span-2">
          {activeForm ? (
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
              <div className="flex justify-between items-center mb-6">
                <div>
                  <h2 className="text-lg font-semibold text-gray-900">
                    {formTemplates.find(t => t.form_type === activeForm.form_type)?.title || 'Form'}
                  </h2>
                  <p className="text-gray-600 text-sm">
                    Status: {getFormStatus(activeForm)}
                  </p>
                </div>
                <button
                  onClick={() => setActiveForm(null)}
                  className="text-gray-500 hover:text-gray-700"
                >
                  ✕
                </button>
              </div>

              <form
                onSubmit={(e) => {
                  e.preventDefault();
                  updateForm(activeForm.id, formData);
                }}
                className="space-y-4"
              >
                {formTemplates
                  .find(t => t.form_type === activeForm.form_type)
                  ?.fields?.map((field) => (
                    <div key={field.name}>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        {field.label}
                        {field.required && <span className="text-red-500 ml-1">*</span>}
                      </label>
                      {renderFormField(field)}
                    </div>
                  ))}

                <div className="flex justify-end space-x-4 pt-4 border-t border-gray-200">
                  <button
                    type="button"
                    onClick={() => setActiveForm(null)}
                    className="px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50 transition-colors"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
                  >
                    Save Form
                  </button>
                </div>
              </form>
            </div>
          ) : (
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-12 text-center">
              <div className="text-gray-400 text-6xl mb-4">📋</div>
              <h3 className="text-lg font-medium text-gray-900 mb-2">No Form Selected</h3>
              <p className="text-gray-600">
                Select a form from the list to start editing, or create a new form
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default FormsManager;