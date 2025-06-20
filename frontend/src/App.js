import React, { useState, useEffect } from "react";
import "./App.css";
import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Vehicle Card Component
const VehicleCard = ({ vehicle }) => {
  const getDealPulseColor = (rating) => {
    switch (rating) {
      case "Great Deal":
        return "bg-green-100 text-green-800 border-green-300";
      case "Fair Price":
        return "bg-yellow-100 text-yellow-800 border-yellow-300";
      case "High Price":
        return "bg-red-100 text-red-800 border-red-300";
      default:
        return "bg-gray-100 text-gray-800 border-gray-300";
    }
  };

  return (
    <div className="bg-white rounded-lg shadow-md overflow-hidden hover:shadow-lg transition-shadow duration-300">
      {/* Vehicle Image */}
      <div className="h-48 bg-gray-200 overflow-hidden">
        {vehicle.images && vehicle.images.length > 0 ? (
          <img
            src={vehicle.images[0]}
            alt={`${vehicle.year} ${vehicle.make} ${vehicle.model}`}
            className="w-full h-full object-cover"
            onError={(e) => {
              e.target.src = "https://via.placeholder.com/300x200?text=No+Image";
            }}
          />
        ) : (
          <div className="w-full h-full flex items-center justify-center text-gray-500">
            <svg className="w-16 h-16" fill="currentColor" viewBox="0 0 20 20">
              <path d="M4 3a2 2 0 00-2 2v10a2 2 0 002 2h12a2 2 0 002-2V5a2 2 0 00-2-2H4zm12 12H4l4-8 3 6 2-4 3 6z" />
            </svg>
          </div>
        )}
      </div>

      {/* Vehicle Info */}
      <div className="p-4">
        <div className="flex justify-between items-start mb-2">
          <h3 className="text-lg font-semibold text-gray-900">
            {vehicle.year} {vehicle.make} {vehicle.model}
          </h3>
          {vehicle.deal_pulse_rating && (
            <span className={`px-2 py-1 text-xs font-medium rounded-full border ${getDealPulseColor(vehicle.deal_pulse_rating)}`}>
              {vehicle.deal_pulse_rating}
            </span>
          )}
        </div>

        <div className="space-y-1 text-sm text-gray-600 mb-3">
          <div className="flex justify-between">
            <span>Price:</span>
            <span className="font-semibold text-gray-900">${vehicle.price.toLocaleString()}</span>
          </div>
          <div className="flex justify-between">
            <span>Mileage:</span>
            <span>{vehicle.mileage.toLocaleString()} mi</span>
          </div>
          {vehicle.fuel_type && (
            <div className="flex justify-between">
              <span>Fuel:</span>
              <span>{vehicle.fuel_type}</span>
            </div>
          )}
          {vehicle.transmission && (
            <div className="flex justify-between">
              <span>Trans:</span>
              <span>{vehicle.transmission}</span>
            </div>
          )}
        </div>

        <div className="text-xs text-gray-500 mb-3">
          <div className="flex justify-between">
            <span>{vehicle.dealer_name}</span>
            <span>{vehicle.dealer_location}</span>
          </div>
        </div>

        {/* Market Analysis */}
        {vehicle.market_price_analysis && vehicle.market_price_analysis.savings > 0 && (
          <div className="bg-green-50 border border-green-200 rounded p-2 text-xs">
            <div className="text-green-800 font-medium">
              Save ${vehicle.market_price_analysis.savings.toLocaleString()}
            </div>
            <div className="text-green-600">
              vs. market avg ${vehicle.market_price_analysis.market_average.toLocaleString()}
            </div>
          </div>
        )}

        <button className="w-full mt-3 bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 transition-colors duration-200">
          View Details
        </button>
      </div>
    </div>
  );
};

// Search Filter Component
const SearchFilters = ({ filters, setFilters, onSearch }) => {
  const [makes, setMakes] = useState([]);
  const [models, setModels] = useState([]);

  useEffect(() => {
    // Load available makes
    axios.get(`${API}/vehicles/search/makes`)
      .then(res => setMakes(res.data.makes))
      .catch(err => console.error('Error loading makes:', err));
  }, []);

  useEffect(() => {
    // Load models when make changes
    if (filters.make) {
      axios.get(`${API}/vehicles/search/models?make=${filters.make}`)
        .then(res => setModels(res.data.models))
        .catch(err => console.error('Error loading models:', err));
    } else {
      setModels([]);
    }
  }, [filters.make]);

  const handleFilterChange = (key, value) => {
    setFilters(prev => ({
      ...prev,
      [key]: value
    }));
  };

  return (
    <div className="bg-white p-6 rounded-lg shadow-md mb-6">
      <h3 className="text-lg font-semibold mb-4">Search Filters</h3>
      
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Make */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Make</label>
          <select
            value={filters.make || ''}
            onChange={(e) => handleFilterChange('make', e.target.value)}
            className="w-full p-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          >
            <option value="">All Makes</option>
            {makes.map(make => (
              <option key={make} value={make}>{make}</option>
            ))}
          </select>
        </div>

        {/* Model */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Model</label>
          <select
            value={filters.model || ''}
            onChange={(e) => handleFilterChange('model', e.target.value)}
            className="w-full p-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            disabled={!filters.make}
          >
            <option value="">All Models</option>
            {models.map(model => (
              <option key={model} value={model}>{model}</option>
            ))}
          </select>
        </div>

        {/* Price Range */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Max Price</label>
          <select
            value={filters.price_max || ''}
            onChange={(e) => handleFilterChange('price_max', e.target.value ? parseFloat(e.target.value) : null)}
            className="w-full p-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          >
            <option value="">No Max</option>
            <option value="10000">$10,000</option>
            <option value="20000">$20,000</option>
            <option value="30000">$30,000</option>
            <option value="50000">$50,000</option>
            <option value="75000">$75,000</option>
            <option value="100000">$100,000</option>
          </select>
        </div>

        {/* Max Mileage */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Max Mileage</label>
          <select
            value={filters.mileage_max || ''}
            onChange={(e) => handleFilterChange('mileage_max', e.target.value ? parseInt(e.target.value) : null)}
            className="w-full p-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          >
            <option value="">No Max</option>
            <option value="25000">25,000 mi</option>
            <option value="50000">50,000 mi</option>
            <option value="75000">75,000 mi</option>
            <option value="100000">100,000 mi</option>
            <option value="150000">150,000 mi</option>
          </select>
        </div>
      </div>

      <div className="mt-4 flex space-x-2">
        <button
          onClick={onSearch}
          className="bg-blue-600 text-white px-6 py-2 rounded-md hover:bg-blue-700 transition-colors duration-200"
        >
          Search Vehicles
        </button>
        <button
          onClick={() => {
            setFilters({});
            onSearch();
          }}
          className="bg-gray-200 text-gray-700 px-6 py-2 rounded-md hover:bg-gray-300 transition-colors duration-200"
        >
          Clear Filters
        </button>
      </div>
    </div>
  );
};

// Stats Component
const StatsSection = ({ stats }) => (
  <div className="bg-gradient-to-r from-blue-600 to-purple-600 text-white p-6 rounded-lg mb-6">
    <h2 className="text-2xl font-bold mb-4">Marketplace Stats</h2>
    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
      <div className="text-center">
        <div className="text-3xl font-bold">{stats.total_vehicles?.toLocaleString() || 0}</div>
        <div className="text-sm opacity-90">Total Vehicles</div>
      </div>
      <div className="text-center">
        <div className="text-3xl font-bold">{stats.total_dealers || 0}</div>
        <div className="text-sm opacity-90">Dealers</div>
      </div>
      <div className="text-center">
        <div className="text-3xl font-bold">{stats.deal_pulse_stats?.great_deals || 0}</div>
        <div className="text-sm opacity-90">Great Deals</div>
      </div>
      <div className="text-center">
        <div className="text-3xl font-bold">{stats.top_makes?.length || 0}</div>
        <div className="text-sm opacity-90">Brands</div>
      </div>
    </div>
  </div>
);

// Admin Panel Component
const AdminPanel = ({ onScrapeDealer }) => {
  const [dealers, setDealers] = useState([]);
  const [scrapeJobs, setScrapeJobs] = useState([]);
  const [showAddDealer, setShowAddDealer] = useState(false);
  const [newDealer, setNewDealer] = useState({
    name: '',
    website_url: '',
    location: '',
    scraper_adapter: 'generic'
  });

  useEffect(() => {
    loadDealers();
    loadScrapeJobs();
  }, []);

  const loadDealers = async () => {
    try {
      const response = await axios.get(`${API}/dealers`);
      setDealers(response.data);
    } catch (error) {
      console.error('Error loading dealers:', error);
    }
  };

  const loadScrapeJobs = async () => {
    try {
      const response = await axios.get(`${API}/scrape/jobs`);
      setScrapeJobs(response.data);
    } catch (error) {
      console.error('Error loading scrape jobs:', error);
    }
  };

  const handleAddDealer = async (e) => {
    e.preventDefault();
    try {
      await axios.post(`${API}/dealers`, newDealer);
      setNewDealer({ name: '', website_url: '', location: '', scraper_adapter: 'generic' });
      setShowAddDealer(false);
      loadDealers();
    } catch (error) {
      console.error('Error adding dealer:', error);
    }
  };

  const handleScrapeDealer = async (dealerId) => {
    try {
      await onScrapeDealer(dealerId);
      loadScrapeJobs();
    } catch (error) {
      console.error('Error scraping dealer:', error);
    }
  };

  return (
    <div className="bg-white p-6 rounded-lg shadow-md mb-6">
      <h3 className="text-lg font-semibold mb-4">Admin Panel</h3>
      
      {/* Add Dealer Form */}
      {showAddDealer && (
        <form onSubmit={handleAddDealer} className="mb-6 p-4 border rounded-lg">
          <h4 className="font-medium mb-3">Add New Dealer</h4>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <input
              type="text"
              placeholder="Dealer Name"
              value={newDealer.name}
              onChange={(e) => setNewDealer({...newDealer, name: e.target.value})}
              className="p-2 border border-gray-300 rounded-md"
              required
            />
            <input
              type="url"
              placeholder="Website URL"
              value={newDealer.website_url}
              onChange={(e) => setNewDealer({...newDealer, website_url: e.target.value})}
              className="p-2 border border-gray-300 rounded-md"
              required
            />
            <input
              type="text"
              placeholder="Location"
              value={newDealer.location}
              onChange={(e) => setNewDealer({...newDealer, location: e.target.value})}
              className="p-2 border border-gray-300 rounded-md"
              required
            />
            <select
              value={newDealer.scraper_adapter}
              onChange={(e) => setNewDealer({...newDealer, scraper_adapter: e.target.value})}
              className="p-2 border border-gray-300 rounded-md"
            >
              <option value="generic">Generic</option>
              <option value="carmax">CarMax</option>
              <option value="cargurus">CarGurus</option>
            </select>
          </div>
          <div className="mt-4 space-x-2">
            <button type="submit" className="bg-blue-600 text-white px-4 py-2 rounded-md">
              Add Dealer
            </button>
            <button
              type="button"
              onClick={() => setShowAddDealer(false)}
              className="bg-gray-300 text-gray-700 px-4 py-2 rounded-md"
            >
              Cancel
            </button>
          </div>
        </form>
      )}

      <div className="flex justify-between items-center mb-4">
        <h4 className="font-medium">Dealers ({dealers.length})</h4>
        <button
          onClick={() => setShowAddDealer(!showAddDealer)}
          className="bg-green-600 text-white px-4 py-2 rounded-md text-sm"
        >
          Add Dealer
        </button>
      </div>

      {/* Dealers Table */}
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b">
              <th className="text-left p-2">Name</th>
              <th className="text-left p-2">Location</th>
              <th className="text-left p-2">Vehicles</th>
              <th className="text-left p-2">Last Scraped</th>
              <th className="text-left p-2">Actions</th>
            </tr>
          </thead>
          <tbody>
            {dealers.map(dealer => (
              <tr key={dealer.id} className="border-b">
                <td className="p-2">{dealer.name}</td>
                <td className="p-2">{dealer.location}</td>
                <td className="p-2">{dealer.vehicle_count}</td>
                <td className="p-2">
                  {dealer.last_scraped ? new Date(dealer.last_scraped).toLocaleDateString() : 'Never'}
                </td>
                <td className="p-2">
                  <button
                    onClick={() => handleScrapeDealer(dealer.id)}
                    className="bg-blue-500 text-white px-3 py-1 rounded text-xs"
                  >
                    Scrape Now
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Recent Scrape Jobs */}
      <div className="mt-6">
        <h4 className="font-medium mb-2">Recent Scrape Jobs</h4>
        <div className="space-y-2">
          {scrapeJobs.slice(0, 5).map(job => (
            <div key={job.id} className="flex justify-between items-center p-2 bg-gray-50 rounded">
              <span className="text-sm">
                Dealer ID: {job.dealer_id} | Status: {job.status}
              </span>
              <span className="text-xs text-gray-500">
                {job.vehicles_found} found, {job.vehicles_added} added
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

// Main App Component
function App() {
  const [vehicles, setVehicles] = useState([]);
  const [loading, setLoading] = useState(false);
  const [stats, setStats] = useState({});
  const [filters, setFilters] = useState({});
  const [currentPage, setCurrentPage] = useState('marketplace');

  useEffect(() => {
    loadVehicles();
    loadStats();
  }, []);

  const loadVehicles = async (searchFilters = {}) => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      Object.entries(searchFilters).forEach(([key, value]) => {
        if (value !== null && value !== undefined && value !== '') {
          params.append(key, value);
        }
      });
      
      const response = await axios.get(`${API}/vehicles?${params.toString()}`);
      setVehicles(response.data);
    } catch (error) {
      console.error('Error loading vehicles:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadStats = async () => {
    try {
      const response = await axios.get(`${API}/stats`);
      setStats(response.data);
    } catch (error) {
      console.error('Error loading stats:', error);
    }
  };

  const handleSearch = () => {
    loadVehicles(filters);
  };

  const handleScrapeDealer = async (dealerId) => {
    try {
      const response = await axios.post(`${API}/scrape/dealer/${dealerId}`);
      alert(`Scraping completed: ${response.data.message}`);
      loadVehicles();
      loadStats();
    } catch (error) {
      alert(`Scraping failed: ${error.response?.data?.detail || error.message}`);
    }
  };

  return (
    <div className="min-h-screen bg-gray-100">
      {/* Header */}
      <header className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-4">
            <div className="flex items-center">
              <h1 className="text-2xl font-bold text-gray-900">
                <span className="text-blue-600">Pulse</span> Auto Market
              </h1>
              <span className="ml-2 px-2 py-1 bg-blue-100 text-blue-800 text-xs font-medium rounded-full">
                BETA
              </span>
            </div>
            
            <nav className="flex space-x-4">
              <button
                onClick={() => setCurrentPage('marketplace')}
                className={`px-4 py-2 rounded-md text-sm font-medium ${
                  currentPage === 'marketplace'
                    ? 'bg-blue-600 text-white'
                    : 'text-gray-700 hover:text-blue-600'
                }`}
              >
                Marketplace
              </button>
              <button
                onClick={() => setCurrentPage('admin')}
                className={`px-4 py-2 rounded-md text-sm font-medium ${
                  currentPage === 'admin'
                    ? 'bg-blue-600 text-white'
                    : 'text-gray-700 hover:text-blue-600'
                }`}
              >
                Admin
              </button>
            </nav>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {currentPage === 'marketplace' ? (
          <>
            {/* Hero Section */}
            <div className="text-center mb-8">
              <h2 className="text-4xl font-bold text-gray-900 mb-4">
                Find Your Perfect Vehicle
              </h2>
              <p className="text-xl text-gray-600 mb-6">
                AI-powered price analysis • Real-time inventory • Trusted dealers
              </p>
            </div>

            {/* Stats */}
            <StatsSection stats={stats} />

            {/* Search Filters */}
            <SearchFilters 
              filters={filters} 
              setFilters={setFilters} 
              onSearch={handleSearch}
            />

            {/* Vehicle Grid */}
            {loading ? (
              <div className="flex justify-center items-center py-12">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
                {vehicles.length > 0 ? (
                  vehicles.map(vehicle => (
                    <VehicleCard key={vehicle.vin} vehicle={vehicle} />
                  ))
                ) : (
                  <div className="col-span-full text-center py-12">
                    <p className="text-gray-500 text-lg">No vehicles found matching your criteria.</p>
                    <p className="text-gray-400 text-sm mt-2">Try adjusting your search filters or check back later.</p>
                  </div>
                )}
              </div>
            )}
          </>
        ) : (
          /* Admin Panel */
          <AdminPanel onScrapeDealer={handleScrapeDealer} />
        )}
      </main>

      {/* Footer */}
      <footer className="bg-gray-800 text-white py-8 mt-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center">
            <h3 className="text-lg font-semibold mb-2">Pulse Auto Market</h3>
            <p className="text-gray-400">The future of automotive marketplace technology</p>
          </div>
        </div>
      </footer>
    </div>
  );
}

export default App;