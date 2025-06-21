import React from 'react';
import { Link, useLocation } from 'react-router-dom';

const Navbar = () => {
  const location = useLocation();

  const isActive = (path) => location.pathname === path;
  const isDealsActive = () => location.pathname.includes('/deal/');

  return (
    <nav className="bg-slate-900 text-white shadow-lg">
      <div className="container mx-auto px-4">
        <div className="flex justify-between items-center h-16">
          <div className="flex items-center space-x-8">
            <Link to="/" className="text-xl font-bold text-blue-400">
              🏪 DMS Pro
            </Link>
            <div className="hidden md:flex space-x-6">
              <Link
                to="/"
                className={`px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                  isActive('/') 
                    ? 'bg-blue-600 text-white' 
                    : 'text-gray-300 hover:bg-gray-700 hover:text-white'
                }`}
              >
                Dashboard
              </Link>
              <Link
                to="/deal/new"
                className={`px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                  isActive('/deal/new') 
                    ? 'bg-blue-600 text-white' 
                    : 'text-gray-300 hover:bg-gray-700 hover:text-white'
                }`}
              >
                New Deal
              </Link>
              
              {/* Deal Management Dropdown */}
              {isDealsActive() && (
                <div className="flex space-x-2">
                  <span className="text-gray-400">•</span>
                  <div className="flex space-x-2">
                    <span className="text-blue-400 text-sm">Deal Tools:</span>
                    <Link
                      to={`${location.pathname.split('/').slice(0, 3).join('/')}/menu`}
                      className="text-gray-300 hover:text-white text-sm"
                    >
                      F&I Menu
                    </Link>
                    <Link
                      to={`${location.pathname.split('/').slice(0, 3).join('/')}/forms`}
                      className="text-gray-300 hover:text-white text-sm"
                    >
                      Forms
                    </Link>
                    <Link
                      to={`${location.pathname.split('/').slice(0, 3).join('/')}/documents`}
                      className="text-gray-300 hover:text-white text-sm"
                    >
                      Documents
                    </Link>
                    <Link
                      to={`${location.pathname.split('/').slice(0, 3).join('/')}/signatures`}
                      className="text-gray-300 hover:text-white text-sm"
                    >
                      E-Sign
                    </Link>
                    <Link
                      to={`${location.pathname.split('/').slice(0, 3).join('/')}/financing`}
                      className="text-gray-300 hover:text-white text-sm"
                    >
                      Financing
                    </Link>
                  </div>
                </div>
              )}
            </div>
          </div>
          <div className="flex items-center space-x-4">
            <div className="text-right">
              <div className="text-sm text-gray-400">Enterprise F&I Platform</div>
              <div className="text-xs text-gray-500">Complete Desking Solution</div>
            </div>
            <div className="w-8 h-8 bg-blue-600 rounded-full flex items-center justify-center">
              <span className="text-sm font-semibold">FM</span>
            </div>
          </div>
        </div>
      </div>
    </nav>
  );
};

export default Navbar;