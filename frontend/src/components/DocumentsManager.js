import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const DocumentsManager = () => {
  const { dealId } = useParams();
  const [deal, setDeal] = useState(null);
  const [documents, setDocuments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);

  useEffect(() => {
    if (dealId) {
      fetchDealData();
      fetchDocuments();
    }
  }, [dealId]);

  const fetchDealData = async () => {
    try {
      const response = await axios.get(`${API}/deals/${dealId}`);
      setDeal(response.data);
    } catch (error) {
      console.error('Error fetching deal:', error);
    }
  };

  const fetchDocuments = async () => {
    try {
      const response = await axios.get(`${API}/deals/${dealId}/documents`);
      setDocuments(response.data);
      setLoading(false);
    } catch (error) {
      console.error('Error fetching documents:', error);
      setLoading(false);
    }
  };

  const generateDocuments = async (documentTypes) => {
    setGenerating(true);
    try {
      const response = await axios.post(`${API}/deals/${dealId}/documents/generate`, documentTypes);
      alert(`Generated ${response.data.documents.length} documents successfully!`);
      fetchDocuments();
    } catch (error) {
      console.error('Error generating documents:', error);
      alert('Error generating documents');
    } finally {
      setGenerating(false);
    }
  };

  const downloadPDF = async (documentId, title) => {
    try {
      const response = await axios.get(`${API}/documents/${documentId}/pdf`);
      
      // Convert base64 to blob
      const pdfData = atob(response.data.pdf_content);
      const bytes = new Uint8Array(pdfData.length);
      for (let i = 0; i < pdfData.length; i++) {
        bytes[i] = pdfData.charCodeAt(i);
      }
      const blob = new Blob([bytes], { type: 'application/pdf' });
      
      // Create download link
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${title}.pdf`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (error) {
      console.error('Error downloading PDF:', error);
      alert('Error downloading PDF');
    }
  };

  const getDocumentStatus = (status) => {
    const statusColors = {
      draft: 'bg-gray-100 text-gray-800',
      generated: 'bg-blue-100 text-blue-800',
      sent_for_signature: 'bg-yellow-100 text-yellow-800',
      signed: 'bg-green-100 text-green-800',
      finalized: 'bg-emerald-100 text-emerald-800'
    };
    
    return (
      <span className={`px-2 py-1 rounded-full text-xs font-medium ${statusColors[status] || 'bg-gray-100 text-gray-800'}`}>
        {status?.replace('_', ' ').toUpperCase()}
      </span>
    );
  };

  const availableDocuments = [
    {
      type: 'purchase_agreement',
      title: 'Purchase Agreement',
      description: 'Main vehicle purchase contract with all pricing details'
    },
    {
      type: 'odometer_disclosure',
      title: 'Odometer Disclosure',
      description: 'Federal requirement for vehicle mileage disclosure'
    },
    {
      type: 'truth_in_lending',
      title: 'Truth-in-Lending Disclosure',
      description: 'TILA disclosure for financing terms and costs'
    },
    {
      type: 'title_transfer',
      title: 'Title Transfer',
      description: 'Vehicle title transfer documentation'
    },
    {
      type: 'bill_of_sale',
      title: 'Bill of Sale',
      description: 'Official record of vehicle sale transaction'
    }
  ];

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      {/* Header */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <h1 className="text-2xl font-bold text-gray-900">Document Generation</h1>
        {deal && (
          <p className="text-gray-600 mt-1">
            Deal {deal.deal_number} • {deal.customer.first_name} {deal.customer.last_name}
          </p>
        )}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Document Generation */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Generate Documents</h2>
          
          <div className="space-y-4 mb-6">
            {availableDocuments.map((doc) => {
              const exists = documents.find(d => d.document_type === doc.type);
              
              return (
                <div key={doc.type} className="border rounded-lg p-4">
                  <div className="flex justify-between items-start mb-2">
                    <h3 className="font-medium">{doc.title}</h3>
                    {exists && getDocumentStatus(exists.status)}
                  </div>
                  <p className="text-sm text-gray-600 mb-3">{doc.description}</p>
                  
                  {exists ? (
                    <div className="flex space-x-2">
                      <button
                        onClick={() => downloadPDF(exists.id, doc.title)}
                        className="text-blue-600 hover:text-blue-800 text-sm font-medium"
                        disabled={!exists.pdf_content}
                      >
                        Download PDF
                      </button>
                      <button
                        onClick={() => generateDocuments([doc.type])}
                        className="text-gray-600 hover:text-gray-800 text-sm font-medium"
                        disabled={generating}
                      >
                        Regenerate
                      </button>
                    </div>
                  ) : (
                    <button
                      onClick={() => generateDocuments([doc.type])}
                      className="w-full bg-blue-600 hover:bg-blue-700 text-white py-2 px-4 rounded-md text-sm transition-colors"
                      disabled={generating}
                    >
                      {generating ? 'Generating...' : 'Generate Document'}
                    </button>
                  )}
                </div>
              );
            })}
          </div>

          <button
            onClick={() => generateDocuments(availableDocuments.map(d => d.type))}
            className="w-full bg-green-600 hover:bg-green-700 text-white py-3 px-4 rounded-md font-semibold transition-colors"
            disabled={generating}
          >
            {generating ? 'Generating All...' : 'Generate All Documents'}
          </button>
        </div>

        {/* Generated Documents */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Generated Documents</h2>
          
          {documents.length === 0 ? (
            <div className="text-center py-8">
              <div className="text-gray-400 text-4xl mb-4">📄</div>
              <h3 className="text-lg font-medium text-gray-900 mb-2">No Documents Generated</h3>
              <p className="text-gray-600">Generate documents using the options on the left</p>
            </div>
          ) : (
            <div className="space-y-4">
              {documents.map((doc) => (
                <div key={doc.id} className="border rounded-lg p-4">
                  <div className="flex justify-between items-start mb-2">
                    <h3 className="font-medium">{doc.title}</h3>
                    {getDocumentStatus(doc.status)}
                  </div>
                  
                  <div className="text-sm text-gray-600 mb-3">
                    <p>Type: {doc.document_type.replace('_', ' ').toUpperCase()}</p>
                    <p>Created: {new Date(doc.created_at).toLocaleDateString()}</p>
                    {doc.updated_at !== doc.created_at && (
                      <p>Updated: {new Date(doc.updated_at).toLocaleDateString()}</p>
                    )}
                  </div>

                  <div className="flex space-x-2">
                    {doc.pdf_content && (
                      <button
                        onClick={() => downloadPDF(doc.id, doc.title)}
                        className="bg-blue-600 hover:bg-blue-700 text-white py-1 px-3 rounded text-sm transition-colors"
                      >
                        Download PDF
                      </button>
                    )}
                    
                    {doc.signature_required && doc.status !== 'signed' && (
                      <button
                        className="bg-yellow-600 hover:bg-yellow-700 text-white py-1 px-3 rounded text-sm transition-colors"
                        onClick={() => alert('E-signature functionality coming next!')}
                      >
                        Send for Signature
                      </button>
                    )}
                    
                    <button
                      className="text-gray-600 hover:text-gray-800 py-1 px-3 border border-gray-300 rounded text-sm transition-colors"
                      onClick={() => alert('Preview functionality coming soon!')}
                    >
                      Preview
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Document Summary */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Document Summary</h2>
        
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="text-center p-4 bg-gray-50 rounded-lg">
            <div className="text-2xl font-bold text-gray-900">{documents.length}</div>
            <div className="text-sm text-gray-600">Total Documents</div>
          </div>
          
          <div className="text-center p-4 bg-blue-50 rounded-lg">
            <div className="text-2xl font-bold text-blue-600">
              {documents.filter(d => d.status === 'generated').length}
            </div>
            <div className="text-sm text-blue-600">Ready for Review</div>
          </div>
          
          <div className="text-center p-4 bg-yellow-50 rounded-lg">
            <div className="text-2xl font-bold text-yellow-600">
              {documents.filter(d => d.status === 'sent_for_signature').length}
            </div>
            <div className="text-sm text-yellow-600">Pending Signature</div>
          </div>
          
          <div className="text-center p-4 bg-green-50 rounded-lg">
            <div className="text-2xl font-bold text-green-600">
              {documents.filter(d => d.status === 'signed').length}
            </div>
            <div className="text-sm text-green-600">Completed</div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default DocumentsManager;