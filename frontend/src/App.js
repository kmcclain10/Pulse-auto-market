import React, { useState, useEffect } from "react";
import "./App.css";
import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Repair Shop Card Component
const RepairShopCard = ({ shop, onViewDetails, onBookAppointment }) => {
  const renderStars = (rating) => {
    const stars = [];
    for (let i = 1; i <= 5; i++) {
      stars.push(
        <span key={i} className={`text-lg ${i <= rating ? 'text-yellow-400' : 'text-gray-300'}`}>
          ★
        </span>
      );
    }
    return stars;
  };

  return (
    <div className="bg-white rounded-lg shadow-md overflow-hidden hover:shadow-lg transition-shadow duration-300">
      {/* Shop Header */}
      <div className="p-4 border-b border-gray-200">
        <div className="flex justify-between items-start mb-2">
          <h3 className="text-lg font-semibold text-gray-900">{shop.name}</h3>
          {shop.featured && (
            <span className="px-2 py-1 bg-blue-100 text-blue-800 text-xs font-medium rounded-full">
              Featured
            </span>
          )}
        </div>
        
        <div className="flex items-center mb-2">
          <div className="flex items-center mr-4">
            {renderStars(shop.rating)}
            <span className="ml-1 text-sm text-gray-600">({shop.review_count})</span>
          </div>
          {shop.certifications.includes("ASE Certified") && (
            <span className="px-2 py-1 bg-green-100 text-green-800 text-xs rounded-full">
              ASE Certified
            </span>
          )}
        </div>

        <p className="text-gray-600 text-sm mb-2">{shop.description}</p>
        
        <div className="text-sm text-gray-500">
          <div>{shop.address}</div>
          <div>{shop.city}, {shop.state} {shop.zip_code}</div>
          <div className="mt-1">{shop.phone}</div>
        </div>
      </div>

      {/* Services Preview */}
      <div className="p-4 border-b border-gray-200">
        <h4 className="font-medium text-gray-900 mb-2">Popular Services</h4>
        <div className="grid grid-cols-1 gap-1">
          {shop.services.filter(s => s.popular).slice(0, 3).map(service => (
            <div key={service.id} className="flex justify-between text-sm">
              <span className="text-gray-700">{service.name}</span>
              <span className="text-gray-500">
                ${service.price_range_min} - ${service.price_range_max}
              </span>
            </div>
          ))}
        </div>
      </div>

      {/* Specialties */}
      {shop.specialties.length > 0 && (
        <div className="p-4 border-b border-gray-200">
          <h4 className="font-medium text-gray-900 mb-2">Specialties</h4>
          <div className="flex flex-wrap gap-1">
            {shop.specialties.slice(0, 4).map(specialty => (
              <span key={specialty} className="px-2 py-1 bg-gray-100 text-gray-700 text-xs rounded">
                {specialty}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Action Buttons */}
      <div className="p-4">
        <div className="grid grid-cols-2 gap-2">
          <button
            onClick={() => onViewDetails(shop)}
            className="bg-gray-100 text-gray-700 py-2 px-4 rounded-md hover:bg-gray-200 transition-colors duration-200 text-sm"
          >
            View Details
          </button>
          <button
            onClick={() => onBookAppointment(shop)}
            className="bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 transition-colors duration-200 text-sm"
          >
            Book Appointment
          </button>
        </div>
      </div>
    </div>
  );
};

// Repair Shop Detail Modal
const RepairShopDetailModal = ({ shop, onClose, onBookAppointment }) => {
  const [reviews, setReviews] = useState([]);
  const [loadingReviews, setLoadingReviews] = useState(false);

  useEffect(() => {
    if (shop) {
      loadReviews();
    }
  }, [shop]);

  const loadReviews = async () => {
    setLoadingReviews(true);
    try {
      const response = await axios.get(`${API}/repair-shops/${shop.id}/reviews`);
      setReviews(response.data);
    } catch (error) {
      console.error('Error loading reviews:', error);
    } finally {
      setLoadingReviews(false);
    }
  };

  if (!shop) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg max-w-4xl w-full max-h-screen overflow-y-auto">
        {/* Header */}
        <div className="flex justify-between items-center p-6 border-b">
          <div>
            <h2 className="text-2xl font-bold text-gray-900">{shop.name}</h2>
            <p className="text-gray-600">{shop.address}, {shop.city}, {shop.state}</p>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 text-2xl"
          >
            ×
          </button>
        </div>

        {/* Content */}
        <div className="p-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Left Column */}
            <div>
              <div className="mb-6">
                <h3 className="text-lg font-semibold mb-3">About</h3>
                <p className="text-gray-700">{shop.description}</p>
                {shop.established_year && (
                  <p className="text-sm text-gray-500 mt-2">
                    Established {shop.established_year} • {shop.num_bays} Service Bays
                  </p>
                )}
              </div>

              <div className="mb-6">
                <h3 className="text-lg font-semibold mb-3">Contact</h3>
                <div className="space-y-1 text-gray-700">
                  <div>📞 {shop.phone}</div>
                  <div>📧 {shop.owner_email}</div>
                  {shop.website && (
                    <div>🌐 <a href={shop.website} target="_blank" rel="noopener noreferrer" className="text-blue-600">Website</a></div>
                  )}
                </div>
              </div>

              <div className="mb-6">
                <h3 className="text-lg font-semibold mb-3">Business Hours</h3>
                <div className="space-y-1 text-sm">
                  {Object.entries(shop.business_hours).map(([day, hours]) => (
                    <div key={day} className="flex justify-between">
                      <span className="capitalize">{day}:</span>
                      <span>
                        {hours.closed ? 'Closed' : `${hours.open} - ${hours.close}`}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* Right Column */}
            <div>
              <div className="mb-6">
                <h3 className="text-lg font-semibold mb-3">Services</h3>
                <div className="space-y-3">
                  {shop.services.map(service => (
                    <div key={service.id} className="border border-gray-200 rounded-lg p-3">
                      <div className="flex justify-between items-start mb-1">
                        <h4 className="font-medium">{service.name}</h4>
                        <span className="text-sm text-gray-500">
                          ${service.price_range_min} - ${service.price_range_max}
                        </span>
                      </div>
                      <p className="text-sm text-gray-600">{service.description}</p>
                      <p className="text-xs text-gray-500 mt-1">
                        Est. {service.estimated_duration} minutes
                      </p>
                    </div>
                  ))}
                </div>
              </div>

              <div className="mb-6">
                <h3 className="text-lg font-semibold mb-3">Reviews ({shop.review_count})</h3>
                {loadingReviews ? (
                  <div className="text-center py-4">Loading reviews...</div>
                ) : reviews.length > 0 ? (
                  <div className="space-y-3">
                    {reviews.slice(0, 3).map(review => (
                      <div key={review.id} className="border border-gray-200 rounded-lg p-3">
                        <div className="flex justify-between items-start mb-1">
                          <h4 className="font-medium">{review.customer_name}</h4>
                          <div className="flex">
                            {[...Array(5)].map((_, i) => (
                              <span key={i} className={`text-sm ${i < review.rating ? 'text-yellow-400' : 'text-gray-300'}`}>
                                ★
                              </span>
                            ))}
                          </div>
                        </div>
                        <p className="text-sm text-gray-600">{review.comment}</p>
                        <p className="text-xs text-gray-500 mt-1">
                          {new Date(review.created_at).toLocaleDateString()}
                        </p>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-gray-500">No reviews yet</p>
                )}
              </div>
            </div>
          </div>

          {/* Book Appointment Button */}
          <div className="border-t pt-4 text-center">
            <button
              onClick={() => onBookAppointment(shop)}
              className="bg-blue-600 text-white px-8 py-3 rounded-md hover:bg-blue-700 transition-colors duration-200"
            >
              Book Appointment with {shop.name}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

// Appointment Booking Modal
const AppointmentBookingModal = ({ shop, onClose, onConfirm }) => {
  const [formData, setFormData] = useState({
    customer_name: '',
    customer_email: '',
    customer_phone: '',
    service_id: '',
    appointment_date: '',
    appointment_time: '',
    service_description: '',
    special_requests: '',
    vehicle_year: '',
    vehicle_make: '',
    vehicle_model: ''
  });
  const [availableSlots, setAvailableSlots] = useState([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (formData.appointment_date) {
      loadAvailableSlots();
    }
  }, [formData.appointment_date]);

  const loadAvailableSlots = async () => {
    try {
      const response = await axios.get(`${API}/repair-shops/${shop.id}/availability?date=${formData.appointment_date}`);
      setAvailableSlots(response.data.available_slots);
    } catch (error) {
      console.error('Error loading available slots:', error);
    }
  };

  const handleInputChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    
    try {
      const appointmentDateTime = new Date(`${formData.appointment_date}T${formData.appointment_time}`);
      
      const appointmentData = {
        repair_shop_id: shop.id,
        service_id: formData.service_id,
        customer_name: formData.customer_name,
        customer_email: formData.customer_email,
        customer_phone: formData.customer_phone,
        appointment_date: appointmentDateTime.toISOString(),
        service_description: formData.service_description,
        special_requests: formData.special_requests,
        vehicle_year: formData.vehicle_year ? parseInt(formData.vehicle_year) : null,
        vehicle_make: formData.vehicle_make,
        vehicle_model: formData.vehicle_model
      };

      const response = await axios.post(`${API}/appointments`, appointmentData);
      onConfirm(response.data);
      onClose();
    } catch (error) {
      alert('Error booking appointment: ' + (error.response?.data?.detail || error.message));
    } finally {
      setLoading(false);
    }
  };

  if (!shop) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg max-w-2xl w-full max-h-screen overflow-y-auto">
        <div className="flex justify-between items-center p-6 border-b">
          <h2 className="text-xl font-bold">Book Appointment - {shop.name}</h2>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600 text-2xl">×</button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          {/* Customer Information */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Full Name *</label>
              <input
                type="text"
                name="customer_name"
                value={formData.customer_name}
                onChange={handleInputChange}
                className="w-full p-2 border border-gray-300 rounded-md"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Phone *</label>
              <input
                type="tel"
                name="customer_phone"
                value={formData.customer_phone}
                onChange={handleInputChange}
                className="w-full p-2 border border-gray-300 rounded-md"
                required
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Email *</label>
            <input
              type="email"
              name="customer_email"
              value={formData.customer_email}
              onChange={handleInputChange}
              className="w-full p-2 border border-gray-300 rounded-md"
              required
            />
          </div>

          {/* Vehicle Information */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Vehicle Year</label>
              <input
                type="number"
                name="vehicle_year"
                value={formData.vehicle_year}
                onChange={handleInputChange}
                className="w-full p-2 border border-gray-300 rounded-md"
                min="1990"
                max="2025"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Make</label>
              <input
                type="text"
                name="vehicle_make"
                value={formData.vehicle_make}
                onChange={handleInputChange}
                className="w-full p-2 border border-gray-300 rounded-md"
                placeholder="e.g., Toyota"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Model</label>
              <input
                type="text"
                name="vehicle_model"
                value={formData.vehicle_model}
                onChange={handleInputChange}
                className="w-full p-2 border border-gray-300 rounded-md"
                placeholder="e.g., Camry"
              />
            </div>
          </div>

          {/* Service Selection */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Service Needed *</label>
            <select
              name="service_id"
              value={formData.service_id}
              onChange={handleInputChange}
              className="w-full p-2 border border-gray-300 rounded-md"
              required
            >
              <option value="">Select a service</option>
              {shop.services.map(service => (
                <option key={service.id} value={service.id}>
                  {service.name} (${service.price_range_min} - ${service.price_range_max})
                </option>
              ))}
            </select>
          </div>

          {/* Date and Time */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Appointment Date *</label>
              <input
                type="date"
                name="appointment_date"
                value={formData.appointment_date}
                onChange={handleInputChange}
                className="w-full p-2 border border-gray-300 rounded-md"
                min={new Date().toISOString().split('T')[0]}
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Preferred Time *</label>
              <select
                name="appointment_time"
                value={formData.appointment_time}
                onChange={handleInputChange}
                className="w-full p-2 border border-gray-300 rounded-md"
                required
                disabled={!formData.appointment_date}
              >
                <option value="">Select time</option>
                {availableSlots.map(slot => (
                  <option key={slot} value={slot}>{slot}</option>
                ))}
              </select>
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Service Description *</label>
            <textarea
              name="service_description"
              value={formData.service_description}
              onChange={handleInputChange}
              className="w-full p-2 border border-gray-300 rounded-md"
              rows="3"
              placeholder="Describe what you need help with..."
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Special Requests</label>
            <textarea
              name="special_requests"
              value={formData.special_requests}
              onChange={handleInputChange}
              className="w-full p-2 border border-gray-300 rounded-md"
              rows="2"
              placeholder="Any special requests or notes..."
            />
          </div>

          <div className="flex justify-end space-x-4 pt-4">
            <button
              type="button"
              onClick={onClose}
              className="px-6 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading}
              className="px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
            >
              {loading ? 'Booking...' : 'Book Appointment'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

// Repair Shop Directory Component
const RepairShopDirectory = () => {
  const [repairShops, setRepairShops] = useState([]);
  const [loading, setLoading] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [zipCode, setZipCode] = useState('');
  const [selectedShop, setSelectedShop] = useState(null);
  const [showDetails, setShowDetails] = useState(false);
  const [showBooking, setShowBooking] = useState(false);
  const [bookingShop, setBookingShop] = useState(null);

  useEffect(() => {
    loadRepairShops();
  }, []);

  const loadRepairShops = async (searchParams = {}) => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      Object.entries(searchParams).forEach(([key, value]) => {
        if (value) params.append(key, value);
      });
      
      const response = await axios.get(`${API}/repair-shops/search?${params.toString()}`);
      setRepairShops(response.data);
    } catch (error) {
      console.error('Error loading repair shops:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = () => {
    const searchParams = {};
    if (zipCode) searchParams.zip_code = zipCode;
    if (searchQuery) searchParams.query = searchQuery;
    loadRepairShops(searchParams);
  };

  const handleViewDetails = (shop) => {
    setSelectedShop(shop);
    setShowDetails(true);
  };

  const handleBookAppointment = (shop) => {
    setBookingShop(shop);
    setShowBooking(true);
    setShowDetails(false);
  };

  const handleAppointmentConfirmed = (appointment) => {
    alert(`Appointment booked successfully! Confirmation ID: ${appointment.id}`);
  };

  return (
    <div>
      {/* Search Section */}
      <div className="bg-white p-6 rounded-lg shadow-md mb-6">
        <h3 className="text-lg font-semibold mb-4">Find Repair Shops</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">ZIP Code</label>
            <input
              type="text"
              placeholder="Enter ZIP code"
              value={zipCode}
              onChange={(e) => setZipCode(e.target.value)}
              className="w-full p-2 border border-gray-300 rounded-md"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Service or Shop Name</label>
            <input
              type="text"
              placeholder="e.g., oil change, brake repair"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full p-2 border border-gray-300 rounded-md"
            />
          </div>
          <div className="flex items-end">
            <button
              onClick={handleSearch}
              className="w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 transition-colors duration-200"
            >
              Search
            </button>
          </div>
        </div>
      </div>

      {/* Results */}
      {loading ? (
        <div className="flex justify-center items-center py-12">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {repairShops.length > 0 ? (
            repairShops.map(shop => (
              <RepairShopCard
                key={shop.id}
                shop={shop}
                onViewDetails={handleViewDetails}
                onBookAppointment={handleBookAppointment}
              />
            ))
          ) : (
            <div className="col-span-full text-center py-12">
              <div className="text-6xl mb-4">🔧</div>
              <p className="text-gray-500 text-lg">No repair shops found</p>
              <p className="text-gray-400 text-sm mt-2">Try adjusting your search criteria</p>
            </div>
          )}
        </div>
      )}

      {/* Modals */}
      {showDetails && (
        <RepairShopDetailModal
          shop={selectedShop}
          onClose={() => setShowDetails(false)}
          onBookAppointment={handleBookAppointment}
        />
      )}

      {showBooking && (
        <AppointmentBookingModal
          shop={bookingShop}
          onClose={() => setShowBooking(false)}
          onConfirm={handleAppointmentConfirmed}
        />
      )}
    </div>
  );
};

// Enhanced Vehicle Card Component with Image Gallery
const VehicleCard = ({ vehicle, onViewImages }) => {
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
    <div className="bg-white rounded-lg shadow-md overflow-hidden hover:shadow-lg transition-shadow duration-300 vehicle-card">
      {/* Enhanced Vehicle Image Section */}
      <div className="h-48 bg-gray-200 overflow-hidden relative">
        {vehicle.images && vehicle.images.length > 0 ? (
          <div className="relative w-full h-full">
            <img
              src={vehicle.images[0]}
              alt={`${vehicle.year} ${vehicle.make} ${vehicle.model}`}
              className="w-full h-full object-cover"
              onError={(e) => {
                e.target.src = "https://images.unsplash.com/photo-1549317661-bd32c8ce0db2?w=800&q=80";
              }}
            />
            {/* Image Count Badge */}
            {vehicle.image_count > 1 && (
              <div className="absolute top-2 left-2 bg-black bg-opacity-70 text-white px-2 py-1 rounded-full text-xs">
                +{vehicle.image_count} photos
              </div>
            )}
            {/* High Quality Badge */}
            <div className="absolute top-2 right-2 bg-blue-600 text-white px-2 py-1 rounded-full text-xs">
              HD Images
            </div>
          </div>
        ) : (
          <div className="w-full h-full flex items-center justify-center text-gray-500 vehicle-image-placeholder">
            <div className="text-center">
              <svg className="w-16 h-16 mx-auto mb-2" fill="currentColor" viewBox="0 0 20 20">
                <path d="M4 3a2 2 0 00-2 2v10a2 2 0 002 2h12a2 2 0 002-2V5a2 2 0 00-2-2H4zm12 12H4l4-8 3 6 2-4 3 6z" />
              </svg>
              <div className="text-sm">Images Loading...</div>
            </div>
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
          <div className="savings-highlight mb-3 text-xs">
            <div className="font-medium">
              Save ${vehicle.market_price_analysis.savings.toLocaleString()}
            </div>
            <div className="opacity-90">
              vs. market avg ${vehicle.market_price_analysis.market_average.toLocaleString()}
            </div>
          </div>
        )}

        {/* Action Buttons */}
        <div className="space-y-2">
          <button 
            onClick={() => onViewImages(vehicle)}
            className="w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 transition-colors duration-200"
          >
            View {vehicle.image_count || 0} Photos
          </button>
          <button className="w-full bg-gray-100 text-gray-700 py-2 px-4 rounded-md hover:bg-gray-200 transition-colors duration-200">
            Contact Dealer
          </button>
        </div>
      </div>
    </div>
  );
};

// Enhanced Image Gallery Modal
const ImageGalleryModal = ({ vehicle, onClose }) => {
  const [images, setImages] = useState([]);
  const [currentImageIndex, setCurrentImageIndex] = useState(0);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (vehicle) {
      loadVehicleImages();
    }
  }, [vehicle]);

  const loadVehicleImages = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`${API}/vehicles/${vehicle.vin}/images`);
      setImages(response.data.images || []);
    } catch (error) {
      console.error('Error loading vehicle images:', error);
      // Fallback to placeholder images
      setImages([
        {
          urls: {
            large: 'https://images.unsplash.com/photo-1549317661-bd32c8ce0db2?w=1024&q=80',
            medium: 'https://images.unsplash.com/photo-1549317661-bd32c8ce0db2?w=640&q=80',
            thumbnail: 'https://images.unsplash.com/photo-1549317661-bd32c8ce0db2?w=320&q=80'
          }
        }
      ]);
    } finally {
      setLoading(false);
    }
  };

  if (!vehicle) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-90 flex items-center justify-center z-50">
      <div className="max-w-6xl max-h-screen w-full h-full flex flex-col">
        {/* Header */}
        <div className="flex justify-between items-center p-4 text-white">
          <h2 className="text-xl font-semibold">
            {vehicle.year} {vehicle.make} {vehicle.model} - Gallery
          </h2>
          <button
            onClick={onClose}
            className="text-white hover:text-gray-300 text-2xl"
          >
            ×
          </button>
        </div>

        {/* Image Display */}
        <div className="flex-1 flex items-center justify-center p-4">
          {loading ? (
            <div className="text-white text-center">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-white mx-auto mb-4"></div>
              <div>Loading high-resolution images...</div>
            </div>
          ) : images.length > 0 ? (
            <div className="relative w-full h-full max-w-4xl">
              <img
                src={images[currentImageIndex]?.urls?.large || images[currentImageIndex]?.urls?.medium}
                alt={`${vehicle.year} ${vehicle.make} ${vehicle.model} - Image ${currentImageIndex + 1}`}
                className="w-full h-full object-contain"
                onError={(e) => {
                  e.target.src = "https://images.unsplash.com/photo-1549317661-bd32c8ce0db2?w=1024&q=80";
                }}
              />
              
              {/* Navigation Arrows */}
              {images.length > 1 && (
                <>
                  <button
                    onClick={() => setCurrentImageIndex(prev => prev > 0 ? prev - 1 : images.length - 1)}
                    className="absolute left-4 top-1/2 transform -translate-y-1/2 bg-black bg-opacity-50 text-white p-2 rounded-full hover:bg-opacity-70"
                  >
                    ‹
                  </button>
                  <button
                    onClick={() => setCurrentImageIndex(prev => prev < images.length - 1 ? prev + 1 : 0)}
                    className="absolute right-4 top-1/2 transform -translate-y-1/2 bg-black bg-opacity-50 text-white p-2 rounded-full hover:bg-opacity-70"
                  >
                    ›
                  </button>
                </>
              )}
              
              {/* Image Counter */}
              <div className="absolute bottom-4 left-1/2 transform -translate-x-1/2 bg-black bg-opacity-50 text-white px-3 py-1 rounded-full">
                {currentImageIndex + 1} / {images.length}
              </div>
            </div>
          ) : (
            <div className="text-white text-center">
              <div className="text-6xl mb-4">📷</div>
              <div>No images available</div>
              <div className="text-sm text-gray-400 mt-2">Images will be scraped automatically</div>
            </div>
          )}
        </div>

        {/* Thumbnail Strip */}
        {!loading && images.length > 1 && (
          <div className="p-4">
            <div className="flex space-x-2 justify-center overflow-x-auto">
              {images.map((image, index) => (
                <button
                  key={index}
                  onClick={() => setCurrentImageIndex(index)}
                  className={`flex-shrink-0 w-16 h-12 rounded overflow-hidden border-2 ${
                    index === currentImageIndex ? 'border-blue-500' : 'border-transparent'
                  }`}
                >
                  <img
                    src={image.urls?.thumbnail || image.urls?.medium}
                    alt={`Thumbnail ${index + 1}`}
                    className="w-full h-full object-cover"
                    onError={(e) => {
                      e.target.src = "https://images.unsplash.com/photo-1549317661-bd32c8ce0db2?w=320&q=80";
                    }}
                  />
                </button>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

// Search Filter Component (Enhanced)
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
      
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
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

        {/* Images Filter */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Images</label>
          <select
            value={filters.with_images || ''}
            onChange={(e) => handleFilterChange('with_images', e.target.value)}
            className="w-full p-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          >
            <option value="">All Vehicles</option>
            <option value="true">With Images Only</option>
            <option value="multiple">5+ Images</option>
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

// Enhanced Stats Component
const StatsSection = ({ stats }) => (
  <div className="bg-gradient-to-r from-blue-600 to-purple-600 text-white p-6 rounded-lg mb-6">
    <h2 className="text-2xl font-bold mb-4">Marketplace Stats</h2>
    <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
      <div className="text-center">
        <div className="text-3xl font-bold stats-counter">{stats.total_vehicles?.toLocaleString() || 0}</div>
        <div className="text-sm opacity-90">Total Vehicles</div>
      </div>
      <div className="text-center">
        <div className="text-3xl font-bold stats-counter">{stats.total_dealers || 0}</div>
        <div className="text-sm opacity-90">Dealers</div>
      </div>
      <div className="text-center">
        <div className="text-3xl font-bold stats-counter">{stats.vehicles_with_images || 0}</div>
        <div className="text-sm opacity-90">With Photos</div>
      </div>
      <div className="text-center">
        <div className="text-3xl font-bold stats-counter">{stats.deal_pulse_stats?.great_deals || 0}</div>
        <div className="text-sm opacity-90">Great Deals</div>
      </div>
      <div className="text-center">
        <div className="text-3xl font-bold stats-counter">{stats.image_coverage_percentage || 0}%</div>
        <div className="text-sm opacity-90">Image Coverage</div>
      </div>
    </div>
  </div>
);

// Enhanced Admin Panel Component
const AdminPanel = ({ onScrapeDealer }) => {
  const [dealers, setDealers] = useState([]);
  const [scrapeJobs, setScrapeJobs] = useState([]);
  const [imageStats, setImageStats] = useState({});
  const [showAddDealer, setShowAddDealer] = useState(false);
  const [newDealer, setNewDealer] = useState({
    name: '',
    website_url: '',
    location: '',
    scraper_adapter: 'generic',
    image_scraping_enabled: true
  });

  useEffect(() => {
    loadDealers();
    loadScrapeJobs();
    loadImageStats();
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

  const loadImageStats = async () => {
    try {
      const response = await axios.get(`${API}/images/stats`);
      setImageStats(response.data);
    } catch (error) {
      console.error('Error loading image stats:', error);
    }
  };

  const handleAddDealer = async (e) => {
    e.preventDefault();
    try {
      await axios.post(`${API}/dealers`, newDealer);
      setNewDealer({ 
        name: '', 
        website_url: '', 
        location: '', 
        scraper_adapter: 'generic',
        image_scraping_enabled: true 
      });
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
      loadImageStats();
    } catch (error) {
      console.error('Error scraping dealer:', error);
    }
  };

  const handleCleanupImages = async () => {
    try {
      const response = await axios.post(`${API}/images/cleanup`);
      alert(`Cleaned up ${response.data.cleaned_count} expired image records`);
      loadImageStats();
    } catch (error) {
      console.error('Error cleaning up images:', error);
    }
  };

  return (
    <div className="space-y-6">
      {/* Image Statistics */}
      <div className="bg-white p-6 rounded-lg shadow-md">
        <h3 className="text-lg font-semibold mb-4">Image Processing Stats</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="text-center p-4 bg-blue-50 rounded-lg">
            <div className="text-2xl font-bold text-blue-600">{imageStats.total_image_records || 0}</div>
            <div className="text-sm text-gray-600">Image Records</div>
          </div>
          <div className="text-center p-4 bg-green-50 rounded-lg">
            <div className="text-2xl font-bold text-green-600">{imageStats.vehicles_with_images || 0}</div>
            <div className="text-sm text-gray-600">Vehicles with Images</div>
          </div>
          <div className="text-center p-4 bg-purple-50 rounded-lg">
            <div className="text-2xl font-bold text-purple-600">{imageStats.average_images_per_vehicle || 0}</div>
            <div className="text-sm text-gray-600">Avg Images/Vehicle</div>
          </div>
        </div>
        <div className="mt-4">
          <button
            onClick={handleCleanupImages}
            className="bg-red-500 text-white px-4 py-2 rounded-md text-sm hover:bg-red-600"
          >
            Cleanup Expired Images
          </button>
        </div>
      </div>

      {/* Dealer Management */}
      <div className="bg-white p-6 rounded-lg shadow-md">
        <h3 className="text-lg font-semibold mb-4">Dealer Management</h3>
        
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
                <option value="cars_com">Cars.com</option>
                <option value="autotrader">AutoTrader</option>
              </select>
              <label className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  checked={newDealer.image_scraping_enabled}
                  onChange={(e) => setNewDealer({...newDealer, image_scraping_enabled: e.target.checked})}
                  className="rounded"
                />
                <span className="text-sm">Enable Image Scraping</span>
              </label>
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
          <table className="w-full text-sm admin-table">
            <thead>
              <tr>
                <th className="text-left p-2">Name</th>
                <th className="text-left p-2">Location</th>
                <th className="text-left p-2">Vehicles</th>
                <th className="text-left p-2">Images</th>
                <th className="text-left p-2">Last Scraped</th>
                <th className="text-left p-2">Actions</th>
              </tr>
            </thead>
            <tbody>
              {dealers.map(dealer => (
                <tr key={dealer.id}>
                  <td className="p-2">
                    <div>
                      {dealer.name}
                      {dealer.image_scraping_enabled && (
                        <span className="ml-2 px-2 py-1 bg-green-100 text-green-800 text-xs rounded-full">
                          Images Enabled
                        </span>
                      )}
                    </div>
                  </td>
                  <td className="p-2">{dealer.location}</td>
                  <td className="p-2">{dealer.vehicle_count}</td>
                  <td className="p-2">
                    {dealer.image_scraping_enabled ? '✅' : '❌'}
                  </td>
                  <td className="p-2">
                    {dealer.last_scraped ? new Date(dealer.last_scraped).toLocaleDateString() : 'Never'}
                  </td>
                  <td className="p-2">
                    <button
                      onClick={() => handleScrapeDealer(dealer.id)}
                      className="bg-blue-500 text-white px-3 py-1 rounded text-xs mr-2"
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
                  Job: {job.status} | Vehicles: {job.vehicles_found} found, {job.vehicles_added} added
                </span>
                <span className="text-xs text-gray-500">
                  Images: {job.images_scraped || 0} scraped
                </span>
              </div>
            ))}
          </div>
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
  const [selectedVehicle, setSelectedVehicle] = useState(null);
  const [showImageGallery, setShowImageGallery] = useState(false);

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

  const handleViewImages = (vehicle) => {
    setSelectedVehicle(vehicle);
    setShowImageGallery(true);
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
              <span className="ml-2 px-2 py-1 bg-green-100 text-green-800 text-xs font-medium rounded-full">
                AI-Powered Images
              </span>
            </div>
            
            <nav className="flex space-x-4">
              <button
                onClick={() => setCurrentPage('marketplace')}
                className={`px-4 py-2 rounded-md text-sm font-medium nav-active ${
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
            <div className="text-center mb-8 hero-gradient rounded-lg p-8 text-white">
              <h2 className="text-4xl font-bold mb-4">
                Find Your Perfect Vehicle
              </h2>
              <p className="text-xl mb-6">
                AI-powered price analysis • High-resolution images • Real-time inventory
              </p>
              <div className="flex justify-center space-x-4 text-sm">
                <div className="flex items-center">
                  <svg className="w-5 h-5 mr-2" fill="currentColor" viewBox="0 0 20 20">
                    <path d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  15+ Photos Per Vehicle
                </div>
                <div className="flex items-center">
                  <svg className="w-5 h-5 mr-2" fill="currentColor" viewBox="0 0 20 20">
                    <path d="M13 6a3 3 0 11-6 0 3 3 0 016 0zM18 8a2 2 0 11-4 0 2 2 0 014 0zM14 15a4 4 0 00-8 0v3h8v-3z" />
                  </svg>
                  Trusted Dealers
                </div>
                <div className="flex items-center">
                  <svg className="w-5 h-5 mr-2" fill="currentColor" viewBox="0 0 20 20">
                    <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                  </svg>
                  Deal Pulse Ratings
                </div>
              </div>
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
                <div className="text-center">
                  <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
                  <div className="text-gray-600">Loading high-resolution vehicle images...</div>
                </div>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
                {vehicles.length > 0 ? (
                  vehicles.map(vehicle => (
                    <VehicleCard 
                      key={vehicle.vin} 
                      vehicle={vehicle} 
                      onViewImages={handleViewImages}
                    />
                  ))
                ) : (
                  <div className="col-span-full text-center py-12">
                    <div className="text-6xl mb-4">🚗</div>
                    <p className="text-gray-500 text-lg">No vehicles found matching your criteria.</p>
                    <p className="text-gray-400 text-sm mt-2">Try adjusting your search filters or check back later for new inventory.</p>
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

      {/* Image Gallery Modal */}
      {showImageGallery && (
        <ImageGalleryModal 
          vehicle={selectedVehicle}
          onClose={() => {
            setShowImageGallery(false);
            setSelectedVehicle(null);
          }}
        />
      )}

      {/* Footer */}
      <footer className="footer-gradient text-white py-8 mt-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center">
            <h3 className="text-lg font-semibold mb-2">Pulse Auto Market</h3>
            <p className="text-gray-400 mb-4">The future of automotive marketplace technology</p>
            <div className="flex justify-center space-x-6 text-sm">
              <div>📸 AI-Powered Image Processing</div>
              <div>☁️ Cloud-Based Storage</div>
              <div>🔄 7-Day Auto Refresh</div>
              <div>⚡ CDN Global Delivery</div>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}

export default App;