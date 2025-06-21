import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './App.css';

const API_BASE = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';

function App() {
  const [activeTab, setActiveTab] = useState('scraper');
  const [scrapingJobs, setScrapingJobs] = useState([]);
  const [vehicles, setVehicles] = useState([]);
  const [dealerStats, setDealerStats] = useState([]);
  const [loading, setLoading] = useState(false);
  
  // Scraping form state
  const [dealerUrls, setDealerUrls] = useState([
    'https://memorymotorstn.com/',
    'https://tnautotrade.com/', 
    'https://usautomotors.com/'
  ]);
  const [maxVehicles, setMaxVehicles] = useState(50);
  const [currentJob, setCurrentJob] = useState(null);

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 10000); // Refresh every 10 seconds
    return () => clearInterval(interval);
  }, []);

  const loadData = async () => {
    try {
      const [jobsRes, vehiclesRes, statsRes] = await Promise.all([
        axios.get(`${API_BASE}/api/scrape/jobs`),
        axios.get(`${API_BASE}/api/vehicles?limit=20`),
        axios.get(`${API_BASE}/api/dealers/stats`)
      ]);
      
      setScrapingJobs(jobsRes.data);
      setVehicles(vehiclesRes.data.vehicles || []);
      setDealerStats(statsRes.data);
    } catch (error) {
      console.error('Error loading data:', error);
    }
  };

  const startScraping = async () => {
    if (dealerUrls.length === 0) return;
    
    setLoading(true);
    try {
      const response = await axios.post(`${API_BASE}/api/scrape/start`, {
        dealer_urls: dealerUrls.filter(url => url.trim()),
        max_vehicles_per_dealer: maxVehicles
      });
      
      setCurrentJob(response.data.job_id);
      await loadData();
    } catch (error) {
      console.error('Error starting scraping:', error);
      alert('Error starting scraping job');
    } finally {
      setLoading(false);
    }
  };

  const formatPrice = (price) => {
    if (!price) return 'N/A';
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(price);
  };

  const formatMileage = (mileage) => {
    if (!mileage) return 'N/A';
    return new Intl.NumberFormat('en-US').format(mileage) + ' mi';
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'completed': return 'text-green-600 bg-green-100';
      case 'running': return 'text-blue-600 bg-blue-100';
      case 'failed': return 'text-red-600 bg-red-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      {/* Header */}
      <div className="bg-white shadow-lg">
        <div className="max-w-7xl mx-auto px-4 py-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">
                🚗 Pulse Auto Market - Advanced Car Scraper
              </h1>
              <p className="text-gray-600 mt-1">
                Intelligent browser automation for small dealer lots
              </p>
            </div>
            <div className="text-right">
              <div className="text-sm text-gray-500">Total Vehicles</div>
              <div className="text-2xl font-bold text-indigo-600">{vehicles.length}</div>
            </div>
          </div>
        </div>
      </div>

      {/* Navigation Tabs */}
      <div className="max-w-7xl mx-auto px-4 py-4">
        <div className="flex space-x-1 bg-white p-1 rounded-lg shadow">
          {[
            { id: 'scraper', label: '🤖 Scraper Control', icon: '⚡' },
            { id: 'vehicles', label: '🚗 Vehicle Inventory', icon: '📊' },
            { id: 'jobs', label: '📋 Scraping Jobs', icon: '🔄' },
            { id: 'stats', label: '📈 Dealer Stats', icon: '📈' }
          ].map(tab => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`px-6 py-3 rounded-md font-medium transition-all ${
                activeTab === tab.id
                  ? 'bg-indigo-600 text-white shadow-md'
                  : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
              }`}
            >
              {tab.icon} {tab.label}
            </button>
          ))}
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 pb-8">
        {/* Scraper Control Tab */}
        {activeTab === 'scraper' && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            {/* Scraping Configuration */}
            <div className="bg-white rounded-xl shadow-lg p-6">
              <h2 className="text-xl font-bold text-gray-900 mb-4">
                🎯 Configure Scraping Job
              </h2>
              
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Dealer URLs (one per line)
                  </label>
                  <textarea
                    value={dealerUrls.join('\n')}
                    onChange={(e) => setDealerUrls(e.target.value.split('\n').filter(url => url.trim()))}
                    className="w-full h-32 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
                    placeholder="https://example-dealer.com/&#10;https://another-dealer.com/"
                  />
                  <p className="text-xs text-gray-500 mt-1">
                    {dealerUrls.length} dealer(s) configured
                  </p>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Max Vehicles per Dealer
                  </label>
                  <input
                    type="number"
                    value={maxVehicles}
                    onChange={(e) => setMaxVehicles(parseInt(e.target.value))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
                    min="1"
                    max="200"
                  />
                </div>

                <button
                  onClick={startScraping}
                  disabled={loading || dealerUrls.length === 0}
                  className={`w-full py-3 px-4 rounded-md font-medium transition-all ${
                    loading || dealerUrls.length === 0
                      ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                      : 'bg-gradient-to-r from-indigo-600 to-purple-600 text-white hover:from-indigo-700 hover:to-purple-700 shadow-lg hover:shadow-xl'
                  }`}
                >
                  {loading ? (
                    <div className="flex items-center justify-center">
                      <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white mr-2"></div>
                      Starting Scraper...
                    </div>
                  ) : (
                    '🚀 Start Advanced Scraping'
                  )}
                </button>
              </div>
            </div>

            {/* Current Job Status */}
            <div className="bg-white rounded-xl shadow-lg p-6">
              <h2 className="text-xl font-bold text-gray-900 mb-4">
                ⚡ Live Scraping Status
              </h2>
              
              {scrapingJobs.length > 0 ? (
                <div className="space-y-3">
                  {scrapingJobs.slice(0, 3).map(job => (
                    <JobStatusCard key={job.id} job={job} />
                  ))}
                </div>
              ) : (
                <div className="text-center py-8 text-gray-500">
                  <div className="text-4xl mb-2">🤖</div>
                  <p>No scraping jobs yet</p>
                  <p className="text-sm">Start your first scraping job above</p>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Vehicle Inventory Tab */}
        {activeTab === 'vehicles' && (
          <div className="bg-white rounded-xl shadow-lg">
            <div className="p-6 border-b border-gray-200">
              <h2 className="text-xl font-bold text-gray-900">
                🚗 Scraped Vehicle Inventory
              </h2>
              <p className="text-gray-600">Latest vehicles from dealer scraping</p>
            </div>
            
            <div className="p-6">
              {vehicles.length > 0 ? (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                  {vehicles.map(vehicle => (
                    <VehicleCard key={vehicle.id} vehicle={vehicle} />
                  ))}
                </div>
              ) : (
                <div className="text-center py-12 text-gray-500">
                  <div className="text-6xl mb-4">🚗</div>
                  <p className="text-lg">No vehicles scraped yet</p>
                  <p>Start a scraping job to see vehicle data here</p>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Scraping Jobs Tab */}
        {activeTab === 'jobs' && (
          <div className="bg-white rounded-xl shadow-lg">
            <div className="p-6 border-b border-gray-200">
              <h2 className="text-xl font-bold text-gray-900">
                📋 Scraping Job History
              </h2>
              <p className="text-gray-600">Track all scraping operations</p>
            </div>
            
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Job ID</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Progress</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Dealers</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Created</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200">
                  {scrapingJobs.map(job => (
                    <tr key={job.id} className="hover:bg-gray-50">
                      <td className="px-6 py-4 text-sm font-mono text-gray-900">
                        {job.id.substring(0, 8)}...
                      </td>
                      <td className="px-6 py-4">
                        <span className={`px-2 py-1 text-xs font-medium rounded-full ${getStatusColor(job.status)}`}>
                          {job.status}
                        </span>
                      </td>
                      <td className="px-6 py-4 text-sm text-gray-900">
                        <div className="flex items-center">
                          <div className="w-16 bg-gray-200 rounded-full h-2 mr-2">
                            <div 
                              className="bg-indigo-600 h-2 rounded-full" 
                              style={{ width: `${job.progress || 0}%` }}
                            ></div>
                          </div>
                          {job.progress || 0}%
                        </div>
                      </td>
                      <td className="px-6 py-4 text-sm text-gray-900">
                        {job.dealers_completed || 0}/{job.dealer_urls?.length || 0}
                      </td>
                      <td className="px-6 py-4 text-sm text-gray-500">
                        {new Date(job.created_at).toLocaleString()}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Dealer Stats Tab */}
        {activeTab === 'stats' && (
          <div className="bg-white rounded-xl shadow-lg">
            <div className="p-6 border-b border-gray-200">
              <h2 className="text-xl font-bold text-gray-900">
                📈 Dealer Performance Stats
              </h2>
              <p className="text-gray-600">Success rates and inventory counts by dealer</p>
            </div>
            
            <div className="p-6">
              {dealerStats.length > 0 ? (
                <div className="space-y-4">
                  {dealerStats.map((dealer, index) => (
                    <div key={dealer._id} className="border border-gray-200 rounded-lg p-4">
                      <div className="flex items-center justify-between">
                        <div>
                          <h3 className="font-medium text-gray-900">
                            {dealer.dealer_name || new URL(dealer._id).hostname}
                          </h3>
                          <p className="text-sm text-gray-500">{dealer._id}</p>
                        </div>
                        <div className="text-right">
                          <div className="text-lg font-bold text-indigo-600">
                            {dealer.vehicle_count} vehicles
                          </div>
                          <div className="text-xs text-gray-500">
                            Last: {new Date(dealer.last_scraped).toLocaleDateString()}
                          </div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-12 text-gray-500">
                  <div className="text-6xl mb-4">📊</div>
                  <p className="text-lg">No dealer stats available</p>
                  <p>Complete some scraping jobs to see stats</p>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

// Job Status Card Component
const JobStatusCard = ({ job }) => {
  const getStatusColor = (status) => {
    switch (status) {
      case 'completed': return 'text-green-600 bg-green-100';
      case 'running': return 'text-blue-600 bg-blue-100';
      case 'failed': return 'text-red-600 bg-red-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  return (
    <div className="border border-gray-200 rounded-lg p-4">
      <div className="flex items-center justify-between mb-2">
        <span className={`px-2 py-1 text-xs font-medium rounded-full ${getStatusColor(job.status)}`}>
          {job.status}
        </span>
        <span className="text-xs text-gray-500">
          {new Date(job.created_at).toLocaleString()}
        </span>
      </div>
      
      <div className="flex items-center justify-between mb-2">
        <span className="text-sm text-gray-600">Progress</span>
        <span className="text-sm font-medium">{job.progress || 0}%</span>
      </div>
      
      <div className="w-full bg-gray-200 rounded-full h-2 mb-2">
        <div 
          className="bg-indigo-600 h-2 rounded-full transition-all" 
          style={{ width: `${job.progress || 0}%` }}
        ></div>
      </div>
      
      <div className="text-xs text-gray-500">
        Dealers: {job.dealers_completed || 0}/{job.dealer_urls?.length || 0}
      </div>
    </div>
  );
};

// Vehicle Card Component
const VehicleCard = ({ vehicle }) => {
  const formatPrice = (price) => {
    if (!price) return 'N/A';
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(price);
  };

  const formatMileage = (mileage) => {
    if (!mileage) return 'N/A';
    return new Intl.NumberFormat('en-US').format(mileage) + ' mi';
  };

  return (
    <div className="border border-gray-200 rounded-lg overflow-hidden hover:shadow-lg transition-shadow">
      {/* Vehicle Image */}
      <div className="aspect-w-16 aspect-h-9 bg-gray-200">
        {vehicle.photos && vehicle.photos.length > 0 ? (
          <img 
            src={vehicle.photos[0]} 
            alt={`${vehicle.year} ${vehicle.make} ${vehicle.model}`}
            className="w-full h-48 object-cover"
          />
        ) : (
          <div className="w-full h-48 bg-gray-200 flex items-center justify-center">
            <div className="text-gray-400 text-4xl">🚗</div>
          </div>
        )}
      </div>
      
      {/* Vehicle Details */}
      <div className="p-4">
        <h3 className="font-bold text-lg text-gray-900 mb-1">
          {vehicle.year} {vehicle.make} {vehicle.model}
        </h3>
        
        <div className="flex items-center justify-between mb-2">
          <span className="text-xl font-bold text-green-600">
            {formatPrice(vehicle.price)}
          </span>
          <span className="text-sm text-gray-600">
            {formatMileage(vehicle.mileage)}
          </span>
        </div>
        
        <div className="text-xs text-gray-500 mb-2">
          {vehicle.dealer_name && (
            <div>📍 {vehicle.dealer_name}</div>
          )}
          <div>📅 Scraped {new Date(vehicle.scraped_at).toLocaleDateString()}</div>
        </div>
        
        {vehicle.photos && vehicle.photos.length > 1 && (
          <div className="text-xs text-blue-600">
            📸 {vehicle.photos.length} photos available
          </div>
        )}
        
        {vehicle.description && (
          <p className="text-xs text-gray-600 mt-2 line-clamp-2">
            {vehicle.description.substring(0, 100)}...
          </p>
        )}
      </div>
    </div>
  );
};

export default App;