import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const CRMDashboard = () => {
  const [analytics, setAnalytics] = useState({
    total_leads: 0,
    new_leads: 0,
    qualified_leads: 0,
    converted_leads: 0,
    conversion_rate: 0,
    recent_communications: 0,
    pending_tasks: 0
  });
  const [leads, setLeads] = useState([]);
  const [tasks, setTasks] = useState([]);
  const [communications, setCommunications] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    try {
      const [analyticsRes, leadsRes, tasksRes, commsRes] = await Promise.all([
        axios.get(`${API}/analytics/dashboard`),
        axios.get(`${API}/leads?limit=5`),
        axios.get(`${API}/tasks?status=pending&limit=5`),
        axios.get(`${API}/communications?limit=5`)
      ]);

      setAnalytics(analyticsRes.data);
      setLeads(leadsRes.data);
      setTasks(tasksRes.data);
      setCommunications(commsRes.data);
      setLoading(false);
    } catch (error) {
      console.error('Error fetching dashboard data:', error);
      setLoading(false);
    }
  };

  const getLeadStatusColor = (status) => {
    const colors = {
      new: 'bg-blue-100 text-blue-800',
      contacted: 'bg-yellow-100 text-yellow-800',
      qualified: 'bg-green-100 text-green-800',
      appointment_set: 'bg-purple-100 text-purple-800',
      showed: 'bg-emerald-100 text-emerald-800',
      sold: 'bg-indigo-100 text-indigo-800',
      lost: 'bg-red-100 text-red-800'
    };
    return colors[status] || 'bg-gray-100 text-gray-800';
  };

  const getScoreColor = (score) => {
    if (score >= 80) return 'text-green-600 bg-green-50';
    if (score >= 60) return 'text-yellow-600 bg-yellow-50';
    if (score >= 40) return 'text-orange-600 bg-orange-50';
    return 'text-red-600 bg-red-50';
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">AI Communication CRM</h1>
          <p className="text-gray-600 mt-1">Intelligent lead management and communication automation</p>
        </div>
        <div className="flex space-x-4">
          <Link
            to="/crm/leads/new"
            className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-3 rounded-lg font-semibold transition-colors shadow-lg"
          >
            + New Lead
          </Link>
          <Link
            to="/crm/communications"
            className="bg-green-600 hover:bg-green-700 text-white px-6 py-3 rounded-lg font-semibold transition-colors shadow-lg"
          >
            💬 Communications
          </Link>
        </div>
      </div>

      {/* Analytics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="bg-white rounded-xl shadow-sm p-6 border border-gray-200">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <div className="w-8 h-8 bg-blue-500 rounded-lg flex items-center justify-center">
                <span className="text-white text-sm font-bold">👥</span>
              </div>
            </div>
            <div className="ml-5 w-0 flex-1">
              <dl>
                <dt className="text-sm font-medium text-gray-500 truncate">Total Leads</dt>
                <dd className="text-2xl font-semibold text-gray-900">{analytics.total_leads}</dd>
              </dl>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-xl shadow-sm p-6 border border-gray-200">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <div className="w-8 h-8 bg-yellow-500 rounded-lg flex items-center justify-center">
                <span className="text-white text-sm font-bold">🆕</span>
              </div>
            </div>
            <div className="ml-5 w-0 flex-1">
              <dl>
                <dt className="text-sm font-medium text-gray-500 truncate">New Leads</dt>
                <dd className="text-2xl font-semibold text-gray-900">{analytics.new_leads}</dd>
              </dl>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-xl shadow-sm p-6 border border-gray-200">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <div className="w-8 h-8 bg-green-500 rounded-lg flex items-center justify-center">
                <span className="text-white text-sm font-bold">✅</span>
              </div>
            </div>
            <div className="ml-5 w-0 flex-1">
              <dl>
                <dt className="text-sm font-medium text-gray-500 truncate">Qualified</dt>
                <dd className="text-2xl font-semibold text-gray-900">{analytics.qualified_leads}</dd>
              </dl>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-xl shadow-sm p-6 border border-gray-200">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <div className="w-8 h-8 bg-emerald-500 rounded-lg flex items-center justify-center">
                <span className="text-white text-sm font-bold">💰</span>
              </div>
            </div>
            <div className="ml-5 w-0 flex-1">
              <dl>
                <dt className="text-sm font-medium text-gray-500 truncate">Conversion Rate</dt>
                <dd className="text-2xl font-semibold text-gray-900">{analytics.conversion_rate}%</dd>
              </dl>
            </div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Recent Leads */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200">
          <div className="px-6 py-4 border-b border-gray-200 flex justify-between items-center">
            <h3 className="text-lg font-semibold text-gray-900">Recent Leads</h3>
            <Link to="/crm/leads" className="text-blue-600 hover:text-blue-800 text-sm font-medium">
              View All →
            </Link>
          </div>
          
          {leads.length === 0 ? (
            <div className="text-center py-12">
              <div className="text-gray-400 text-4xl mb-4">👥</div>
              <h3 className="text-lg font-medium text-gray-900 mb-2">No leads yet</h3>
              <p className="text-gray-500 mb-4">Start by adding your first lead</p>
              <Link
                to="/crm/leads/new"
                className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg font-medium transition-colors"
              >
                Add Lead
              </Link>
            </div>
          ) : (
            <div className="divide-y divide-gray-200">
              {leads.map((lead) => (
                <div key={lead.id} className="p-6 hover:bg-gray-50">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-4">
                      <div className="flex-shrink-0">
                        <div className="w-10 h-10 bg-blue-500 rounded-full flex items-center justify-center">
                          <span className="text-white font-semibold text-sm">
                            {lead.first_name?.[0]}{lead.last_name?.[0]}
                          </span>
                        </div>
                      </div>
                      <div>
                        <h4 className="text-sm font-medium text-gray-900">
                          {lead.first_name} {lead.last_name}
                        </h4>
                        <p className="text-sm text-gray-500">{lead.email || lead.phone}</p>
                      </div>
                    </div>
                    <div className="flex items-center space-x-2">
                      <div className={`px-2 py-1 rounded-full text-xs font-medium ${getScoreColor(lead.score)}`}>
                        Score: {lead.score}
                      </div>
                      <span className={`px-2 py-1 rounded-full text-xs font-medium ${getLeadStatusColor(lead.status)}`}>
                        {lead.status.replace('_', ' ').toUpperCase()}
                      </span>
                    </div>
                  </div>
                  <div className="mt-2 text-xs text-gray-500">
                    Source: {lead.source} • Created: {new Date(lead.created_at).toLocaleDateString()}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Pending Tasks */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200">
          <div className="px-6 py-4 border-b border-gray-200 flex justify-between items-center">
            <h3 className="text-lg font-semibold text-gray-900">Pending Tasks</h3>
            <Link to="/crm/tasks" className="text-blue-600 hover:text-blue-800 text-sm font-medium">
              View All →
            </Link>
          </div>
          
          {tasks.length === 0 ? (
            <div className="text-center py-12">
              <div className="text-gray-400 text-4xl mb-4">✅</div>
              <h3 className="text-lg font-medium text-gray-900 mb-2">No pending tasks</h3>
              <p className="text-gray-500">All caught up!</p>
            </div>
          ) : (
            <div className="divide-y divide-gray-200">
              {tasks.map((task) => (
                <div key={task.id} className="p-6 hover:bg-gray-50">
                  <div className="flex items-center justify-between">
                    <div>
                      <h4 className="text-sm font-medium text-gray-900">{task.title}</h4>
                      <p className="text-sm text-gray-500">{task.description}</p>
                    </div>
                    <div className="text-right">
                      <div className="text-xs text-gray-500">
                        {task.due_date ? `Due: ${new Date(task.due_date).toLocaleDateString()}` : 'No due date'}
                      </div>
                      <div className="text-xs font-medium text-blue-600 mt-1">
                        {task.type.replace('_', ' ').toUpperCase()}
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Recent Communications */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200">
        <div className="px-6 py-4 border-b border-gray-200 flex justify-between items-center">
          <h3 className="text-lg font-semibold text-gray-900">Recent Communications</h3>
          <Link to="/crm/communications" className="text-blue-600 hover:text-blue-800 text-sm font-medium">
            View All →
          </Link>
        </div>
        
        {communications.length === 0 ? (
          <div className="text-center py-12">
            <div className="text-gray-400 text-4xl mb-4">💬</div>
            <h3 className="text-lg font-medium text-gray-900 mb-2">No communications yet</h3>
            <p className="text-gray-500">Communications will appear here</p>
          </div>
        ) : (
          <div className="divide-y divide-gray-200">
            {communications.map((comm) => (
              <div key={comm.id} className="p-6 hover:bg-gray-50">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <div className={`w-8 h-8 rounded-lg flex items-center justify-center ${
                      comm.direction === 'inbound' ? 'bg-green-100' : 'bg-blue-100'
                    }`}>
                      <span className={`text-sm ${
                        comm.direction === 'inbound' ? 'text-green-600' : 'text-blue-600'
                      }`}>
                        {comm.direction === 'inbound' ? '📥' : '📤'}
                      </span>
                    </div>
                    <div>
                      <h4 className="text-sm font-medium text-gray-900">
                        {comm.subject || `${comm.type.toUpperCase()} Communication`}
                      </h4>
                      <p className="text-sm text-gray-500 truncate max-w-md">
                        {comm.content.substring(0, 100)}...
                      </p>
                    </div>
                  </div>
                  <div className="text-right text-xs text-gray-500">
                    {new Date(comm.created_at).toLocaleDateString()}
                    {comm.is_ai_generated && (
                      <div className="text-purple-600 font-medium mt-1">🤖 AI Generated</div>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* AI Insights Panel */}
      <div className="bg-gradient-to-r from-purple-50 to-blue-50 rounded-xl border border-purple-200 p-6">
        <h3 className="text-lg font-semibold text-purple-900 mb-3 flex items-center">
          🤖 AI Insights & Automation
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="bg-white rounded-lg p-4">
            <h4 className="font-medium text-gray-900 mb-2">Auto-Response Rate</h4>
            <div className="text-2xl font-bold text-green-600">85%</div>
            <p className="text-xs text-gray-600">of inquiries get instant AI responses</p>
          </div>
          <div className="bg-white rounded-lg p-4">
            <h4 className="font-medium text-gray-900 mb-2">Lead Scoring</h4>
            <div className="text-2xl font-bold text-blue-600">AI</div>
            <p className="text-xs text-gray-600">automatically scores all leads</p>
          </div>
          <div className="bg-white rounded-lg p-4">
            <h4 className="font-medium text-gray-900 mb-2">Follow-up Tasks</h4>
            <div className="text-2xl font-bold text-purple-600">{analytics.pending_tasks}</div>
            <p className="text-xs text-gray-600">AI-generated tasks pending</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default CRMDashboard;