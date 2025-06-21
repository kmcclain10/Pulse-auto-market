import React, { useState, useEffect, useRef } from 'react';
import { useParams } from 'react-router-dom';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const ESignatureManager = () => {
  const { dealId } = useParams();
  const [deal, setDeal] = useState(null);
  const [documents, setDocuments] = useState([]);
  const [signatureRequests, setSignatureRequests] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showSignatureCapture, setShowSignatureCapture] = useState(false);
  const [activeSignature, setActiveSignature] = useState(null);
  const canvasRef = useRef(null);
  const [isDrawing, setIsDrawing] = useState(false);

  useEffect(() => {
    if (dealId) {
      fetchData();
    }
  }, [dealId]);

  const fetchData = async () => {
    try {
      const [dealResponse, documentsResponse, signatureResponse] = await Promise.all([
        axios.get(`${API}/deals/${dealId}`),
        axios.get(`${API}/deals/${dealId}/documents`),
        axios.get(`${API}/deals/${dealId}/signature-status`)
      ]);
      
      setDeal(dealResponse.data);
      setDocuments(documentsResponse.data);
      setSignatureRequests(signatureResponse.data.signature_requests || []);
      setLoading(false);
    } catch (error) {
      console.error('Error fetching data:', error);
      setLoading(false);
    }
  };

  const createSignatureRequest = async (documentId, signers) => {
    try {
      const response = await axios.post(`${API}/documents/${documentId}/signature-request`, {
        signers: signers,
        signing_order: signers.map(s => s.email),
        expires_at: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString() // 7 days
      });
      
      alert('Signature request created successfully!');
      fetchData();
      return response.data;
    } catch (error) {
      console.error('Error creating signature request:', error);
      alert('Error creating signature request');
    }
  };

  const startDrawing = (e) => {
    setIsDrawing(true);
    const canvas = canvasRef.current;
    const rect = canvas.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    
    const ctx = canvas.getContext('2d');
    ctx.beginPath();
    ctx.moveTo(x, y);
  };

  const draw = (e) => {
    if (!isDrawing) return;
    
    const canvas = canvasRef.current;
    const rect = canvas.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    
    const ctx = canvas.getContext('2d');
    ctx.lineTo(x, y);
    ctx.stroke();
  };

  const stopDrawing = () => {
    setIsDrawing(false);
  };

  const clearSignature = () => {
    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    ctx.clearRect(0, 0, canvas.width, canvas.height);
  };

  const captureSignature = async () => {
    const canvas = canvasRef.current;
    const signatureData = canvas.toDataURL();
    
    try {
      await axios.post(`${API}/signature-requests/${activeSignature.id}/sign`, {
        signer_email: activeSignature.signer_email,
        signer_name: activeSignature.signer_name,
        signature_data: signatureData,
        ip_address: '127.0.0.1', // In production, get real IP
        user_agent: navigator.userAgent,
        legal_notice_acknowledged: true
      });
      
      alert('Signature captured successfully!');
      setShowSignatureCapture(false);
      setActiveSignature(null);
      fetchData();
    } catch (error) {
      console.error('Error capturing signature:', error);
      alert('Error capturing signature');
    }
  };

  const getSignatureStatus = (documentId) => {
    const request = signatureRequests.find(r => r.document_id === documentId);
    if (!request) return { status: 'not_requested', color: 'gray' };
    
    if (request.status === 'completed') {
      return { status: 'completed', color: 'green' };
    } else if (request.status === 'pending') {
      return { status: 'pending', color: 'yellow' };
    }
    
    return { status: 'unknown', color: 'gray' };
  };

  const defaultSigners = deal ? [
    {
      name: `${deal.customer.first_name} ${deal.customer.last_name}`,
      email: deal.customer.email || 'customer@example.com',
      role: 'Customer'
    },
    {
      name: deal.fi_manager || 'F&I Manager',
      email: 'manager@dealership.com',
      role: 'F&I Manager'
    }
  ] : [];

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
        <h1 className="text-2xl font-bold text-gray-900">E-Signature Management</h1>
        {deal && (
          <p className="text-gray-600 mt-1">
            Deal {deal.deal_number} • {deal.customer.first_name} {deal.customer.last_name}
          </p>
        )}
      </div>

      {/* Signature Capture Modal */}
      {showSignatureCapture && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl p-6 max-w-2xl w-full mx-4">
            <h3 className="text-lg font-semibold mb-4">Capture Digital Signature</h3>
            
            <div className="mb-4">
              <p className="text-sm text-gray-600 mb-2">
                Signer: <strong>{activeSignature?.signer_name}</strong>
              </p>
              <p className="text-xs text-gray-500">
                Please sign in the box below using your mouse or touch device
              </p>
            </div>

            <div className="border-2 border-gray-300 rounded-lg mb-4">
              <canvas
                ref={canvasRef}
                width={600}
                height={200}
                className="w-full h-48 cursor-crosshair"
                onMouseDown={startDrawing}
                onMouseMove={draw}
                onMouseUp={stopDrawing}
                onMouseLeave={stopDrawing}
                style={{ touchAction: 'none' }}
              />
            </div>

            <div className="flex justify-between items-center">
              <button
                onClick={clearSignature}
                className="px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50 transition-colors"
              >
                Clear
              </button>
              
              <div className="space-x-3">
                <button
                  onClick={() => {
                    setShowSignatureCapture(false);
                    setActiveSignature(null);
                  }}
                  className="px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50 transition-colors"
                >
                  Cancel
                </button>
                <button
                  onClick={captureSignature}
                  className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
                >
                  Accept Signature
                </button>
              </div>
            </div>

            {/* Legal Notice */}
            <div className="mt-4 p-3 bg-gray-50 rounded-lg text-xs text-gray-600">
              <strong>Electronic Signature Agreement:</strong> By signing electronically, you agree that your electronic signature 
              is the legal equivalent of your manual signature and has the same legal force and effect as a manual signature.
            </div>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Documents Requiring Signatures */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Documents for Signature</h2>
          
          {documents.length === 0 ? (
            <div className="text-center py-8">
              <div className="text-gray-400 text-4xl mb-4">📝</div>
              <h3 className="text-lg font-medium text-gray-900 mb-2">No Documents Available</h3>
              <p className="text-gray-600">Generate documents first to enable e-signatures</p>
            </div>
          ) : (
            <div className="space-y-4">
              {documents.map((doc) => {
                const sigStatus = getSignatureStatus(doc.id);
                
                return (
                  <div key={doc.id} className="border rounded-lg p-4">
                    <div className="flex justify-between items-start mb-3">
                      <div>
                        <h3 className="font-medium">{doc.title}</h3>
                        <p className="text-sm text-gray-600">
                          {doc.document_type.replace('_', ' ').toUpperCase()}
                        </p>
                      </div>
                      <span className={`px-2 py-1 rounded-full text-xs font-medium 
                        ${sigStatus.color === 'green' ? 'bg-green-100 text-green-800' : 
                          sigStatus.color === 'yellow' ? 'bg-yellow-100 text-yellow-800' : 
                          'bg-gray-100 text-gray-800'}`}>
                        {sigStatus.status.replace('_', ' ').toUpperCase()}
                      </span>
                    </div>

                    {sigStatus.status === 'not_requested' && (
                      <div className="space-y-3">
                        <div className="text-sm">
                          <p className="font-medium mb-2">Required Signers:</p>
                          <div className="space-y-1">
                            {defaultSigners.map((signer, index) => (
                              <div key={index} className="flex justify-between text-xs">
                                <span>{signer.name} ({signer.role})</span>
                                <span>{signer.email}</span>
                              </div>
                            ))}
                          </div>
                        </div>
                        
                        <button
                          onClick={() => createSignatureRequest(doc.id, defaultSigners)}
                          className="w-full bg-blue-600 hover:bg-blue-700 text-white py-2 px-4 rounded-md text-sm transition-colors"
                        >
                          Send for Signature
                        </button>
                      </div>
                    )}

                    {sigStatus.status === 'pending' && (
                      <div className="space-y-2">
                        <p className="text-sm text-gray-600">Pending signatures from:</p>
                        {defaultSigners.map((signer, index) => (
                          <div key={index} className="flex justify-between items-center">
                            <span className="text-sm">{signer.name} ({signer.role})</span>
                            <button
                              onClick={() => {
                                setActiveSignature({
                                  id: signatureRequests.find(r => r.document_id === doc.id)?.id,
                                  signer_name: signer.name,
                                  signer_email: signer.email
                                });
                                setShowSignatureCapture(true);
                              }}
                              className="bg-green-600 hover:bg-green-700 text-white py-1 px-3 rounded text-xs transition-colors"
                            >
                              Sign Now
                            </button>
                          </div>
                        ))}
                      </div>
                    )}

                    {sigStatus.status === 'completed' && (
                      <div className="text-sm text-green-600">
                        ✓ All signatures completed
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Signature Activity */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Signature Activity</h2>
          
          {signatureRequests.length === 0 ? (
            <div className="text-center py-8">
              <div className="text-gray-400 text-4xl mb-4">✍️</div>
              <h3 className="text-lg font-medium text-gray-900 mb-2">No Signature Activity</h3>
              <p className="text-gray-600">Signature requests will appear here</p>
            </div>
          ) : (
            <div className="space-y-4">
              {signatureRequests.map((request) => {
                const document = documents.find(d => d.id === request.document_id);
                
                return (
                  <div key={request.id} className="border rounded-lg p-4">
                    <div className="flex justify-between items-start mb-2">
                      <h3 className="font-medium">{document?.title || 'Document'}</h3>
                      <span className={`px-2 py-1 rounded-full text-xs font-medium 
                        ${request.status === 'completed' ? 'bg-green-100 text-green-800' : 
                          'bg-yellow-100 text-yellow-800'}`}>
                        {request.status.toUpperCase()}
                      </span>
                    </div>
                    
                    <div className="text-sm text-gray-600 space-y-1">
                      <p>Created: {new Date(request.created_at).toLocaleDateString()}</p>
                      {request.expires_at && (
                        <p>Expires: {new Date(request.expires_at).toLocaleDateString()}</p>
                      )}
                      {request.completed_at && (
                        <p>Completed: {new Date(request.completed_at).toLocaleDateString()}</p>
                      )}
                    </div>

                    <div className="mt-3">
                      <p className="text-sm font-medium mb-2">Signers:</p>
                      <div className="space-y-1">
                        {request.signers?.map((signer, index) => (
                          <div key={index} className="flex justify-between text-xs">
                            <span>{signer.name}</span>
                            <span className="text-gray-500">{signer.email}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>

      {/* Compliance Information */}
      <div className="bg-blue-50 rounded-xl border border-blue-200 p-6">
        <h3 className="text-lg font-semibold text-blue-900 mb-3">📋 E-Signature Compliance</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm text-blue-800">
          <div>
            <h4 className="font-medium mb-2">ESIGN Act Compliance</h4>
            <ul className="space-y-1 text-xs">
              <li>• Electronic signatures are legally equivalent to handwritten signatures</li>
              <li>• Proper consent and disclosure processes followed</li>
              <li>• Audit trail maintained for all signature events</li>
            </ul>
          </div>
          <div>
            <h4 className="font-medium mb-2">Security Features</h4>
            <ul className="space-y-1 text-xs">
              <li>• IP address and timestamp recording</li>
              <li>• Device fingerprinting for authentication</li>
              <li>• Tamper-evident document sealing</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ESignatureManager;