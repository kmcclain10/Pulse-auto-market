import React, { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const CommunicationHub = () => {
  const [searchParams] = useSearchParams();
  const [communications, setCommunications] = useState([]);
  const [leads, setLeads] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedLead, setSelectedLead] = useState(searchParams.get('lead_id') || '');
  const [showAIComposer, setShowAIComposer] = useState(false);
  const [aiRequest, setAiRequest] = useState({
    prompt: '',
    type: 'email',
    context: {}
  });
  const [aiResponse, setAiResponse] = useState('');
  const [generating, setGenerating] = useState(false);

  useEffect(() => {
    fetchData();
  }, [selectedLead]);

  const fetchData = async () => {
    try {
      const params = new URLSearchParams();
      if (selectedLead) params.append('lead_id', selectedLead);

      const [commsRes, leadsRes] = await Promise.all([
        axios.get(`${API}/communications?${params}`),
        axios.get(`${API}/leads`)
      ]);

      setCommunications(commsRes.data);
      setLeads(leadsRes.data);
      setLoading(false);
    } catch (error) {
      console.error('Error fetching data:', error);
      setLoading(false);
    }
  };

  const generateAIResponse = async () => {
    setGenerating(true);
    try {
      const lead = leads.find(l => l.id === selectedLead);
      const context = {
        customer_name: lead ? `${lead.first_name} ${lead.last_name}` : '',
        customer_email: lead?.email || '',
        interested_vehicles: lead?.interested_vehicles || [],
        budget_range: lead?.budget_min && lead?.budget_max ? 
          `$${lead.budget_min.toLocaleString()} - $${lead.budget_max.toLocaleString()}` : '',
        lead_score: lead?.score || 0,
        dealership: 'ABC Motors',
        phone: '(555) 123-4567'
      };

      const response = await axios.post(`${API}/communications/ai-response`, {
        prompt: aiRequest.prompt,
        context: context,
        type: aiRequest.type
      });

      setAiResponse(response.data.response);
    } catch (error) {
      console.error('Error generating AI response:', error);
      alert('Error generating AI response');
    } finally {
      setGenerating(false);
    }
  };

  const sendAIResponse = async () => {
    try {
      if (!selectedLead) {
        alert('Please select a lead first');
        return;
      }

      await axios.post(`${API}/communications/auto-respond`, {
        inquiry: aiRequest.prompt,
        lead_id: selectedLead
      });

      alert('AI response sent successfully!');
      setShowAIComposer(false);
      setAiRequest({ prompt: '', type: 'email', context: {} });
      setAiResponse('');
      fetchData(); // Refresh communications
    } catch (error) {
      console.error('Error sending AI response:', error);
      alert('Error sending AI response');
    }
  };

  const getTypeIcon = (type) => {
    const icons = {
      email: '📧',
      sms: '💬',
      phone: '📞',
      chat: '💭',
      in_person: '👥'
    };
    return icons[type] || '📝';
  };

  const getDirectionColor = (direction) => {
    return direction === 'inbound' 
      ? 'bg-green-100 text-green-800 border-green-200' 
      : 'bg-blue-100 text-blue-800 border-blue-200';
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Communication Hub</h1>
          <p className="text-gray-600 mt-1">AI-powered customer communication management</p>
        </div>
        <button
          onClick={() => setShowAIComposer(true)}
          className="bg-purple-600 hover:bg-purple-700 text-white px-6 py-3 rounded-lg font-semibold transition-colors shadow-lg flex items-center"
        >
          🤖 AI Compose
        </button>
      </div>

      {/* Filters */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Filters</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Lead/Customer</label>
            <select
              value={selectedLead}
              onChange={(e) => setSelectedLead(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">All Communications</option>
              {leads.map(lead => (
                <option key={lead.id} value={lead.id}>
                  {lead.first_name} {lead.last_name} - Score: {lead.score}
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* AI Composer Modal */}
      {showAIComposer && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl p-6 max-w-4xl w-full mx-4 max-h-screen overflow-y-auto">
            <h3 className="text-lg font-semibold mb-4 flex items-center">
              🤖 AI Communication Composer
            </h3>
            
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Input Section */}
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Communication Type</label>
                  <select
                    value={aiRequest.type}
                    onChange={(e) => setAiRequest(prev => ({ ...prev, type: e.target.value }))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="email">Email</option>
                    <option value="sms">SMS</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    What would you like to communicate?
                  </label>
                  <textarea
                    value={aiRequest.prompt}
                    onChange={(e) => setAiRequest(prev => ({ ...prev, prompt: e.target.value }))}
                    rows={6}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="e.g., Follow up on their interest in the 2023 Toyota Camry, ask about scheduling a test drive"
                  />
                </div>

                <button
                  onClick={generateAIResponse}
                  disabled={generating || !aiRequest.prompt}
                  className="w-full bg-purple-600 hover:bg-purple-700 text-white py-2 px-4 rounded-md font-medium disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  {generating ? 'Generating AI Response...' : 'Generate AI Response'}
                </button>
              </div>

              {/* AI Response Section */}
              <div className="space-y-4">
                <h4 className="font-medium text-gray-900">AI Generated Response:</h4>
                
                {aiResponse ? (
                  <div className="bg-gray-50 rounded-lg p-4 border">
                    <div className="whitespace-pre-wrap text-sm text-gray-800">
                      {aiResponse}
                    </div>
                  </div>
                ) : (
                  <div className="bg-gray-50 rounded-lg p-8 text-center text-gray-500">
                    <div className="text-4xl mb-2">🤖</div>
                    <p>AI response will appear here</p>
                  </div>
                )}

                {aiResponse && (
                  <div className="flex space-x-3">
                    <button
                      onClick={() => setAiResponse('')}
                      className="flex-1 px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50 transition-colors"
                    >
                      Regenerate
                    </button>
                    <button
                      onClick={sendAIResponse}
                      className="flex-1 px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 transition-colors"
                    >
                      Send Response
                    </button>
                  </div>
                )}
              </div>
            </div>

            <div className="flex justify-end mt-6">
              <button
                onClick={() => {
                  setShowAIComposer(false);
                  setAiRequest({ prompt: '', type: 'email', context: {} });
                  setAiResponse('');
                }}
                className="px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50 transition-colors"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Communications List */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200">
        <div className="px-6 py-4 border-b border-gray-200 flex justify-between items-center">
          <h3 className="text-lg font-semibold text-gray-900">
            Communications ({communications.length})
          </h3>
          {selectedLead && (
            <div className="text-sm text-gray-600">
              Filtered by: {leads.find(l => l.id === selectedLead)?.first_name} {leads.find(l => l.id === selectedLead)?.last_name}
            </div>
          )}
        </div>
        
        {communications.length === 0 ? (
          <div className="text-center py-12">
            <div className="text-gray-400 text-6xl mb-4">💬</div>
            <h3 className="text-lg font-medium text-gray-900 mb-2">No communications found</h3>
            <p className="text-gray-500 mb-4">
              {selectedLead ? 'No communications for this lead yet' : 'Start communicating with leads'}
            </p>
            <button
              onClick={() => setShowAIComposer(true)}
              className="bg-purple-600 hover:bg-purple-700 text-white px-4 py-2 rounded-lg font-medium transition-colors"
            >
              🤖 Create AI Message
            </button>
          </div>
        ) : (
          <div className="divide-y divide-gray-200">
            {communications.map((comm) => {
              const lead = leads.find(l => l.id === comm.lead_id);
              
              return (
                <div key={comm.id} className="p-6 hover:bg-gray-50">
                  <div className="flex items-start space-x-4">
                    <div className={`flex-shrink-0 w-10 h-10 rounded-lg flex items-center justify-center border ${getDirectionColor(comm.direction)}`}>
                      <span className="text-lg">
                        {comm.direction === 'inbound' ? '📥' : '📤'}
                      </span>
                    </div>
                    
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center space-x-2">
                          <h4 className="text-sm font-medium text-gray-900">
                            {comm.subject || `${getTypeIcon(comm.type)} ${comm.type.toUpperCase()} Communication`}
                          </h4>
                          {comm.is_ai_generated && (
                            <span className="bg-purple-100 text-purple-800 text-xs px-2 py-1 rounded-full font-medium">
                              🤖 AI Generated
                            </span>
                          )}
                        </div>
                        <div className="text-xs text-gray-500">
                          {new Date(comm.created_at).toLocaleString()}
                        </div>
                      </div>
                      
                      {lead && (
                        <div className="text-xs text-gray-600 mt-1">
                          To/From: {lead.first_name} {lead.last_name} ({comm.to_email || comm.from_email || comm.to_phone || comm.from_phone})
                        </div>
                      )}
                      
                      <div className="mt-2 text-sm text-gray-800">
                        <div className="bg-gray-50 rounded-lg p-3 whitespace-pre-wrap">
                          {comm.content}
                        </div>
                      </div>
                      
                      <div className="mt-3 flex items-center space-x-4 text-xs text-gray-500">
                        <span className={`px-2 py-1 rounded-full border ${getDirectionColor(comm.direction)}`}>
                          {comm.direction.toUpperCase()}
                        </span>
                        <span>{getTypeIcon(comm.type)} {comm.type.toUpperCase()}</span>
                        <span>Status: {comm.status.toUpperCase()}</span>
                        {comm.sentiment && (
                          <span>Sentiment: {comm.sentiment}</span>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* AI Insights Panel */}
      <div className="bg-gradient-to-r from-purple-50 to-blue-50 rounded-xl border border-purple-200 p-6">
        <h3 className="text-lg font-semibold text-purple-900 mb-3 flex items-center">
          🤖 AI Communication Insights
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="bg-white rounded-lg p-4">
            <h4 className="font-medium text-gray-900 mb-2">Response Rate</h4>
            <div className="text-2xl font-bold text-green-600">92%</div>
            <p className="text-xs text-gray-600">of AI messages get responses</p>
          </div>
          <div className="bg-white rounded-lg p-4">
            <h4 className="font-medium text-gray-900 mb-2">Avg Response Time</h4>
            <div className="text-2xl font-bold text-blue-600">< 30s</div>
            <p className="text-xs text-gray-600">AI responds instantly</p>
          </div>
          <div className="bg-white rounded-lg p-4">
            <h4 className="font-medium text-gray-900 mb-2">Sentiment</h4>
            <div className="text-2xl font-bold text-purple-600">87%</div>
            <p className="text-xs text-gray-600">positive customer interactions</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default CommunicationHub;