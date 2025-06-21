import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const MenuSelling = () => {
  const { dealId } = useParams();
  const [deal, setDeal] = useState(null);
  const [menuData, setMenuData] = useState(null);
  const [selectedVSC, setSelectedVSC] = useState('');
  const [includeGAP, setIncludeGAP] = useState(false);
  const [loading, setLoading] = useState(true);
  const [updating, setUpdating] = useState(false);

  useEffect(() => {
    fetchMenuData();
  }, [dealId]);

  const fetchMenuData = async () => {
    try {
      const [dealResponse, menuResponse] = await Promise.all([
        axios.get(`${API}/deals/${dealId}`),
        axios.get(`${API}/deals/${dealId}/menu`)
      ]);
      
      setDeal(dealResponse.data);
      setMenuData(menuResponse.data);
      setSelectedVSC(menuResponse.data.selected_vsc || '');
      setIncludeGAP(menuResponse.data.has_gap || false);
      setLoading(false);
    } catch (error) {
      console.error('Error fetching menu data:', error);
      setLoading(false);
    }
  };

  const updateMenuSelection = async () => {
    setUpdating(true);
    try {
      await axios.post(`${API}/deals/${dealId}/menu-selection`, {
        deal_id: dealId,
        selected_vsc_id: selectedVSC || null,
        include_gap: includeGAP
      });
      
      alert('F&I products updated successfully!');
      fetchMenuData(); // Refresh data
    } catch (error) {
      console.error('Error updating menu selection:', error);
      alert('Error updating F&I products');
    } finally {
      setUpdating(false);
    }
  };

  const getVSCPrice = (vscId) => {
    if (!menuData?.vsc_options) return 0;
    const vsc = menuData.vsc_options.find(v => v.id === vscId);
    return vsc ? vsc.final_price : 0;
  };

  const calculateTotal = () => {
    let total = 0;
    if (selectedVSC) {
      total += getVSCPrice(selectedVSC);
    }
    if (includeGAP && menuData?.gap_option) {
      total += menuData.gap_option.final_price;
    }
    return total;
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (!deal || !menuData) {
    return (
      <div className="text-center py-12">
        <div className="text-gray-400 text-6xl mb-4">❌</div>
        <h3 className="text-lg font-medium text-gray-900 mb-2">Unable to load F&I menu</h3>
        <Link to="/" className="text-blue-600 hover:text-blue-800">← Back to Dashboard</Link>
      </div>
    );
  }

  // Group VSC options by coverage type
  const vscByType = menuData.vsc_options.reduce((acc, vsc) => {
    if (!acc[vsc.coverage_type]) {
      acc[vsc.coverage_type] = [];
    }
    acc[vsc.coverage_type].push(vsc);
    return acc;
  }, {});

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      {/* Header */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <div className="flex justify-between items-start">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">F&I Menu - Deal {deal.deal_number}</h1>
            <p className="text-gray-600 mt-1">
              {deal.customer.first_name} {deal.customer.last_name} • 
              {deal.vehicle.year} {deal.vehicle.make} {deal.vehicle.model}
            </p>
          </div>
          <Link
            to={`/deal/${deal.id}`}
            className="text-gray-600 hover:text-gray-800 px-4 py-2 rounded-lg border border-gray-300 transition-colors"
          >
            ← Back to Deal
          </Link>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Menu Selection */}
        <div className="lg:col-span-2 space-y-6">
          
          {/* VSC Options */}
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">🛡️ Vehicle Service Contract (VSC)</h2>
            <p className="text-gray-600 text-sm mb-6">Protect your investment with comprehensive coverage options</p>
            
            <div className="space-y-4">
              <div>
                <label className="flex items-center p-4 border-2 border-gray-200 rounded-lg hover:bg-gray-50 cursor-pointer">
                  <input
                    type="radio"
                    name="vsc"
                    value=""
                    checked={selectedVSC === ''}
                    onChange={(e) => setSelectedVSC(e.target.value)}
                    className="mr-3"
                  />
                  <div className="flex-1">
                    <div className="font-medium text-gray-900">No Extended Warranty</div>
                    <div className="text-sm text-gray-600">Decline extended warranty coverage</div>
                  </div>
                  <div className="text-right">
                    <div className="font-bold text-gray-900">$0</div>
                  </div>
                </label>
              </div>

              {Object.entries(vscByType).map(([coverageType, options]) => (
                <div key={coverageType} className="border rounded-lg p-4">
                  <h3 className="font-medium text-gray-900 mb-3 capitalize">
                    {coverageType.replace('_', ' ')} Coverage
                  </h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                    {options.map((vsc) => (
                      <label
                        key={vsc.id}
                        className={`flex items-center p-3 border rounded-lg hover:bg-gray-50 cursor-pointer transition-colors ${
                          selectedVSC === vsc.id ? 'border-blue-500 bg-blue-50' : 'border-gray-200'
                        }`}
                      >
                        <input
                          type="radio"
                          name="vsc"
                          value={vsc.id}
                          checked={selectedVSC === vsc.id}
                          onChange={(e) => setSelectedVSC(e.target.value)}
                          className="mr-3"
                        />
                        <div className="flex-1">
                          <div className="font-medium text-sm">
                            {vsc.term.replace('_', ' ')} • {vsc.mileage_limit.toLocaleString()} mi
                          </div>
                          <div className="text-xs text-gray-600">{vsc.description}</div>
                        </div>
                        <div className="text-right">
                          <div className="font-bold text-blue-600">${vsc.final_price.toLocaleString()}</div>
                          <div className="text-xs text-gray-500">Cost: ${vsc.base_cost.toLocaleString()}</div>
                        </div>
                      </label>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* GAP Insurance */}
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">🛡️ GAP Insurance</h2>
            <p className="text-gray-600 text-sm mb-6">Protection against negative equity in your loan</p>
            
            <div className="space-y-4">
              <label className="flex items-center p-4 border-2 border-gray-200 rounded-lg hover:bg-gray-50 cursor-pointer">
                <input
                  type="checkbox"
                  checked={!includeGAP}
                  onChange={(e) => setIncludeGAP(!e.target.checked)}
                  className="mr-3"
                />
                <div className="flex-1">
                  <div className="font-medium text-gray-900">No GAP Insurance</div>
                  <div className="text-sm text-gray-600">Decline GAP coverage</div>
                </div>
                <div className="text-right">
                  <div className="font-bold text-gray-900">$0</div>
                </div>
              </label>

              {menuData.gap_option && (
                <label className={`flex items-center p-4 border-2 rounded-lg hover:bg-gray-50 cursor-pointer transition-colors ${
                  includeGAP ? 'border-blue-500 bg-blue-50' : 'border-gray-200'
                }`}>
                  <input
                    type="checkbox"
                    checked={includeGAP}
                    onChange={(e) => setIncludeGAP(e.target.checked)}
                    className="mr-3"
                  />
                  <div className="flex-1">
                    <div className="font-medium text-gray-900">GAP Insurance</div>
                    <div className="text-sm text-gray-600">{menuData.gap_option.description}</div>
                    <div className="text-xs text-gray-500 mt-1">
                      Base Cost: ${menuData.gap_option.base_cost.toLocaleString()} • 
                      Markup: ${menuData.gap_option.markup.toLocaleString()}
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="font-bold text-blue-600">${menuData.gap_option.final_price.toLocaleString()}</div>
                  </div>
                </label>
              )}
            </div>
          </div>
        </div>

        {/* Summary Panel */}
        <div className="space-y-6">
          {/* Deal Summary */}
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 sticky top-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Deal Summary</h3>
            
            <div className="space-y-3 text-sm">
              <div className="flex justify-between">
                <span className="text-gray-600">Vehicle Price:</span>
                <span>${deal.total_vehicle_price?.toLocaleString()}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Fees & Taxes:</span>
                <span>${deal.total_fees_taxes?.toLocaleString()}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Current F&I Products:</span>
                <span>${deal.total_fi_products?.toLocaleString()}</span>
              </div>
              <hr className="my-3" />
              <div className="flex justify-between font-medium">
                <span>Subtotal:</span>
                <span>${deal.total_deal_amount?.toLocaleString()}</span>
              </div>
            </div>

            <div className="mt-6 pt-4 border-t border-gray-200">
              <h4 className="font-medium text-gray-900 mb-3">New F&I Selection</h4>
              <div className="space-y-2 text-sm">
                {selectedVSC && (
                  <div className="flex justify-between">
                    <span className="text-gray-600">VSC:</span>
                    <span className="text-green-600">+${getVSCPrice(selectedVSC).toLocaleString()}</span>
                  </div>
                )}
                {includeGAP && menuData.gap_option && (
                  <div className="flex justify-between">
                    <span className="text-gray-600">GAP:</span>
                    <span className="text-green-600">+${menuData.gap_option.final_price.toLocaleString()}</span>
                  </div>
                )}
                <hr className="my-2" />
                <div className="flex justify-between font-bold text-lg">
                  <span>New Total:</span>
                  <span className="text-blue-600">
                    ${((deal.total_deal_amount || 0) - (deal.total_fi_products || 0) + calculateTotal()).toLocaleString()}
                  </span>
                </div>
                <div className="flex justify-between text-sm text-gray-600">
                  <span>F&I Products:</span>
                  <span>${calculateTotal().toLocaleString()}</span>
                </div>
              </div>
            </div>

            <button
              onClick={updateMenuSelection}
              disabled={updating}
              className="w-full mt-6 bg-blue-600 hover:bg-blue-700 text-white py-3 px-4 rounded-lg font-semibold disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {updating ? 'Updating...' : 'Update F&I Selection'}
            </button>
          </div>

          {/* Compliance Info */}
          <div className="bg-blue-50 rounded-xl border border-blue-200 p-4">
            <h4 className="font-medium text-blue-900 mb-2">📋 Compliance Note</h4>
            <p className="text-blue-800 text-sm">
              All F&I products are optional. Customers have the right to decline any additional products.
              Pricing includes dealer markup as disclosed.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default MenuSelling;