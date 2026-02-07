import React, { useState, useEffect, useMemo } from 'react';
import axios from 'axios';
import { 
  Package, Users, FileText, Plus, Edit2, Trash2, Save, X, 
  Download, Share2, Search, Menu, Home, Camera, Upload, Image
} from 'lucide-react';
import './App.css';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Standard tile sizes
const STANDARD_TILE_SIZES = [
  '600x600mm',
  '800x800mm',
  '1000x1000mm',
  '600x1200mm',
  '300x600mm',
  '400x400mm',
  'Custom Size'
];

function App() {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [tiles, setTiles] = useState([]);
  const [customers, setCustomers] = useState([]);
  const [invoices, setInvoices] = useState([]);
  const [loading, setLoading] = useState(false);
  const [showMobileMenu, setShowMobileMenu] = useState(false);

  // Fetch all data
  useEffect(() => {
    fetchTiles();
    fetchCustomers();
    fetchInvoices();
  }, []);

  const fetchTiles = async () => {
    try {
      const response = await axios.get(`${API}/tiles`);
      setTiles(response.data);
    } catch (error) {
      console.error('Error fetching tiles:', error);
    }
  };

  const fetchCustomers = async () => {
    try {
      const response = await axios.get(`${API}/customers`);
      setCustomers(response.data);
    } catch (error) {
      console.error('Error fetching customers:', error);
    }
  };

  const fetchInvoices = async () => {
    try {
      const response = await axios.get(`${API}/invoices`);
      setInvoices(response.data);
    } catch (error) {
      console.error('Error fetching invoices:', error);
    }
  };

  return (
    <div className="min-h-screen" style={{backgroundColor: '#fef7f7'}}>
      {/* Header */}
      <header className="bg-white shadow-md sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-4">
            <div className="flex items-center space-x-3">
              <img 
                src="https://customer-assets.emergentagent.com/job_1f30f2ce-4c5c-40ac-bd4f-cb3289954aea/artifacts/p5rto5md_Untitled%20%281080%20x%201080%20px%29.png" 
                alt="The Tile Shop" 
                className="brand-logo"
                data-testid="brand-logo"
              />
              <div>
                <h1 className="text-2xl font-bold" style={{color: '#5a3825'}} data-testid="app-title">
                  The Tile Shop
                </h1>
                <p className="text-xs" style={{color: '#8b6b4a'}}>Your Tile Experts - Invoicing</p>
              </div>
            </div>
            <button
              onClick={() => setShowMobileMenu(!showMobileMenu)}
              className="lg:hidden p-2 rounded-lg hover:bg-gray-100"
              data-testid="mobile-menu-button"
            >
              <Menu className="h-6 w-6 text-gray-600" />
            </button>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="flex flex-col lg:flex-row gap-6">
          {/* Sidebar Navigation */}
          <aside className={`lg:w-64 ${showMobileMenu ? 'block' : 'hidden'} lg:block`}>
            <nav className="bg-white rounded-xl shadow-lg p-4 space-y-2" data-testid="sidebar-navigation">
              <NavItem
                icon={<Home />}
                label="Dashboard"
                active={activeTab === 'dashboard'}
                onClick={() => { setActiveTab('dashboard'); setShowMobileMenu(false); }}
                testId="nav-dashboard"
              />
              <NavItem
                icon={<Package />}
                label="Tiles Management"
                active={activeTab === 'tiles'}
                onClick={() => { setActiveTab('tiles'); setShowMobileMenu(false); }}
                testId="nav-tiles"
              />
              <NavItem
                icon={<Users />}
                label="Customers"
                active={activeTab === 'customers'}
                onClick={() => { setActiveTab('customers'); setShowMobileMenu(false); }}
                testId="nav-customers"
              />
              <NavItem
                icon={<FileText />}
                label="Invoices"
                active={activeTab === 'invoices'}
                onClick={() => { setActiveTab('invoices'); setShowMobileMenu(false); }}
                testId="nav-invoices"
              />
            </nav>
          </aside>

          {/* Main Content */}
          <main className="flex-1">
            {activeTab === 'dashboard' && (
              <Dashboard 
                tiles={tiles} 
                customers={customers} 
                invoices={invoices}
                onNavigate={setActiveTab}
              />
            )}
            {activeTab === 'tiles' && (
              <TilesManagement tiles={tiles} fetchTiles={fetchTiles} />
            )}
            {activeTab === 'customers' && (
              <CustomersManagement customers={customers} fetchCustomers={fetchCustomers} />
            )}
            {activeTab === 'invoices' && (
              <InvoicesManagement 
                invoices={invoices} 
                tiles={tiles}
                customers={customers}
                fetchInvoices={fetchInvoices} 
              />
            )}
          </main>
        </div>
      </div>
    </div>
  );
}

// Navigation Item Component
function NavItem({ icon, label, active, onClick, testId }) {
  return (
    <button
      onClick={onClick}
      data-testid={testId}
      className={`w-full flex items-center space-x-3 px-4 py-3 rounded-lg transition-all duration-200 ${
        active
          ? 'text-white shadow-lg scale-105'
          : 'text-gray-700 hover:bg-gray-100'
      }`}
      style={active ? {background: 'linear-gradient(to right, #5a3825, #6b4a35)'} : {}}
    >
      <div className="h-5 w-5">{icon}</div>
      <span className="font-medium">{label}</span>
    </button>
  );
}

// Dashboard Component
function Dashboard({ tiles, customers, invoices, onNavigate }) {
  const activeTiles = tiles.filter(t => t.active).length;
  const totalPending = customers.reduce((sum, c) => sum + c.total_pending, 0);
  const draftInvoices = invoices.filter(i => i.status === 'Draft').length;
  const paidInvoices = invoices.filter(i => i.status === 'Paid').length;

  return (
    <div className="space-y-6" data-testid="dashboard-view">
      <div className="bg-white rounded-xl shadow-lg p-6">
        <h2 className="text-2xl font-bold text-gray-800 mb-6">Dashboard Overview</h2>
        
        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <StatCard
            icon={<Package className="text-[#5a3825]" />}
            title="Active Tiles"
            value={activeTiles}
            total={tiles.length}
            color="blue"
            testId="stat-active-tiles"
            onClick={() => onNavigate('tiles')}
          />
          <StatCard
            icon={<Users className="text-green-600" />}
            title="Total Customers"
            value={customers.length}
            color="green"
            testId="stat-total-customers"
            onClick={() => onNavigate('customers')}
          />
          <StatCard
            icon={<FileText className="text-[#5a3825]" />}
            title="Total Invoices"
            value={invoices.length}
            subtitle={`${paidInvoices} Paid, ${draftInvoices} Draft`}
            color="purple"
            testId="stat-total-invoices"
            onClick={() => onNavigate('invoices')}
          />
          <StatCard
            icon={<FileText className="text-red-600" />}
            title="Pending Amount"
            value={`₹${totalPending.toFixed(2)}`}
            color="red"
            testId="stat-pending-amount"
            onClick={() => onNavigate('customers')}
          />
        </div>
      </div>

      {/* Recent Activity */}
      <div className="bg-white rounded-xl shadow-lg p-6">
        <h3 className="text-xl font-bold text-gray-800 mb-4">Recent Invoices</h3>
        <div className="space-y-3">
          {invoices.slice(0, 5).map(invoice => (
            <div
              key={invoice.invoice_id}
              className="flex items-center justify-between p-4 bg-gray-50 rounded-lg hover:bg-gray-100 transition"
              data-testid={`recent-invoice-${invoice.invoice_id}`}
            >
              <div>
                <p className="font-semibold text-gray-800">{invoice.invoice_id}</p>
                <p className="text-sm text-gray-600">{invoice.customer_name}</p>
              </div>
              <div className="text-right">
                <p className="font-bold text-gray-800">₹{invoice.grand_total.toFixed(2)}</p>
                <span className={`text-xs px-2 py-1 rounded-full ${
                  invoice.status === 'Paid' ? 'bg-green-100 text-green-800' :
                  invoice.status === 'Draft' ? 'bg-yellow-100 text-yellow-800' :
                  'bg-blue-100 text-blue-800'
                }`}>
                  {invoice.status}
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

function StatCard({ icon, title, value, total, subtitle, color, testId, onClick }) {
  const colorClasses = {
    blue: 'from-blue-500 to-blue-600',
    green: 'from-green-500 to-green-600',
    purple: 'from-purple-500 to-purple-600',
    red: 'from-red-500 to-red-600'
  };

  return (
    <div 
      onClick={onClick}
      className={`bg-white rounded-xl shadow-md p-6 border-l-4 border-transparent hover:shadow-xl transition-all ${onClick ? 'cursor-pointer hover:scale-105' : ''}`} 
      data-testid={testId}
    >
      <div className="flex items-center justify-between mb-4">
        <div className={`p-3 rounded-lg bg-gradient-to-r ${colorClasses[color]}`}>
          <div className="h-6 w-6 text-white">{icon}</div>
        </div>
      </div>
      <h3 className="text-gray-600 text-sm font-medium mb-1">{title}</h3>
      <p className="text-3xl font-bold text-gray-800">
        {value}
        {total && <span className="text-lg text-gray-400">/{total}</span>}
      </p>
      {subtitle && <p className="text-xs text-gray-500 mt-2">{subtitle}</p>}
    </div>
  );
}

// Tiles Management Component
function TilesManagement({ tiles, fetchTiles }) {
  const [showForm, setShowForm] = useState(false);
  const [editingTile, setEditingTile] = useState(null);
  const [formData, setFormData] = useState({
    size: '',
    customSize: '',
    coverage: '',
    box_packing: ''
  });
  const [searchTerm, setSearchTerm] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const finalSize = formData.size === 'Custom Size' ? formData.customSize : formData.size;
      
      const dataToSend = {
        size: finalSize,
        coverage: parseFloat(formData.coverage),
        box_packing: parseInt(formData.box_packing)
      };

      if (editingTile) {
        await axios.put(`${API}/tiles/${editingTile.tile_id}`, dataToSend);
      } else {
        await axios.post(`${API}/tiles`, dataToSend);
      }

      fetchTiles();
      resetForm();
    } catch (error) {
      alert('Error: ' + (error.response?.data?.detail || error.message));
    }
  };

  const handleDelete = async (tileId) => {
    if (window.confirm('Are you sure you want to delete this tile?')) {
      try {
        await axios.delete(`${API}/tiles/${tileId}`);
        fetchTiles();
      } catch (error) {
        alert('Error deleting tile: ' + error.message);
      }
    }
  };

  const resetForm = () => {
    setFormData({
      size: '',
      customSize: '',
      coverage: '',
      box_packing: ''
    });
    setEditingTile(null);
    setShowForm(false);
  };

  const startEdit = (tile) => {
    const isCustomSize = !STANDARD_TILE_SIZES.includes(tile.size);
    setFormData({
      size: isCustomSize ? 'Custom Size' : tile.size,
      customSize: isCustomSize ? tile.size : '',
      coverage: (tile.coverage || tile.box_coverage_sqft || '').toString(),
      box_packing: (tile.box_packing || '').toString()
    });
    setEditingTile(tile);
    setShowForm(true);
  };

  const filteredTiles = tiles.filter(tile =>
    tile.size.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="space-y-6" data-testid="tiles-management-view">
      {/* Header */}
      <div className="bg-white rounded-xl shadow-lg p-6">
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
          <div>
            <h2 className="text-2xl font-bold text-gray-800">Tiles Management</h2>
            <p className="text-gray-600 text-sm">Manage your tile inventory</p>
          </div>
          <button
            onClick={() => setShowForm(!showForm)}
            className="bg-gradient-to-r from-[#5a3825] to-[#6b4a35] text-white px-6 py-3 rounded-lg hover:shadow-lg transition-all duration-200 flex items-center space-x-2"
            data-testid="add-tile-button"
          >
            <Plus className="h-5 w-5" />
            <span>Add New Tile</span>
          </button>
        </div>

        {/* Search */}
        <div className="mt-4">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
            <input
              type="text"
              placeholder="Search tiles by name or size..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-[#5a3825] focus:border-transparent"
              data-testid="search-tiles-input"
            />
          </div>
        </div>
      </div>

      {/* Form */}
      {showForm && (
        <div className="bg-white rounded-xl shadow-lg p-6" data-testid="tile-form">
          <div className="flex justify-between items-center mb-6">
            <h3 className="text-xl font-bold text-gray-800">
              {editingTile ? 'Edit Tile' : 'Add New Tile'}
            </h3>
            <button onClick={resetForm} className="text-gray-500 hover:text-gray-700">
              <X className="h-6 w-6" />
            </button>
          </div>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Size *</label>
                <select
                  required
                  value={formData.size}
                  onChange={(e) => setFormData({ ...formData, size: e.target.value })}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-[#5a3825] focus:border-transparent"
                  data-testid="tile-size-select"
                >
                  <option value="">-- Select Size --</option>
                  {STANDARD_TILE_SIZES.map(size => (
                    <option key={size} value={size}>{size}</option>
                  ))}
                </select>
              </div>
              {formData.size === 'Custom Size' && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Custom Size *</label>
                  <input
                    type="text"
                    required
                    value={formData.customSize}
                    onChange={(e) => setFormData({ ...formData, customSize: e.target.value })}
                    placeholder="e.g., 900x450mm"
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-[#5a3825] focus:border-transparent"
                    data-testid="tile-custom-size-input"
                  />
                </div>
              )}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Coverage (Sqft per Box) *</label>
                <input
                  type="number"
                  step="0.01"
                  required
                  value={formData.coverage}
                  onChange={(e) => setFormData({ ...formData, coverage: e.target.value })}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-[#5a3825] focus:border-transparent"
                  data-testid="tile-coverage-input"
                  placeholder="e.g., 23.68"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Box Packing (Tiles per Box) *</label>
                <input
                  type="number"
                  min="1"
                  required
                  value={formData.box_packing}
                  onChange={(e) => setFormData({ ...formData, box_packing: e.target.value })}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-[#5a3825] focus:border-transparent"
                  data-testid="tile-box-packing-input"
                  placeholder="e.g., 4"
                />
              </div>
            </div>

            <div className="flex justify-end space-x-3 pt-4">
              <button
                type="button"
                onClick={resetForm}
                className="px-6 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50"
                data-testid="tile-cancel-button"
              >
                Cancel
              </button>
              <button
                type="submit"
                className="px-6 py-2 bg-gradient-to-r from-[#5a3825] to-[#6b4a35] text-white rounded-lg hover:shadow-lg transition-all"
                data-testid="tile-save-button"
              >
                <Save className="inline h-5 w-5 mr-2" />
                {editingTile ? 'Update' : 'Save'} Tile
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Tiles List */}
      <div className="bg-white rounded-xl shadow-lg overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full" data-testid="tiles-table">
            <thead className="bg-gradient-to-r from-[#5a3825] to-[#6b4a35] text-white">
              <tr>
                <th className="px-6 py-4 text-left text-sm font-semibold">Size</th>
                <th className="px-6 py-4 text-left text-sm font-semibold">Coverage (Sqft/Box)</th>
                <th className="px-6 py-4 text-left text-sm font-semibold">Box Packing</th>
                <th className="px-6 py-4 text-right text-sm font-semibold">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {filteredTiles.map((tile) => (
                <tr key={tile.tile_id} className="hover:bg-gray-50 transition" data-testid={`tile-row-${tile.tile_id}`}>
                  <td className="px-6 py-4 text-sm font-medium text-gray-900">{tile.size}</td>
                  <td className="px-6 py-4 text-sm text-gray-700">{tile.coverage || tile.box_coverage_sqft || 0} sqft</td>
                  <td className="px-6 py-4 text-sm text-gray-700">{tile.box_packing || 0} tiles</td>
                  <td className="px-6 py-4 text-right">
                    <div className="flex justify-end space-x-2">
                      <button
                        onClick={() => startEdit(tile)}
                        className="p-2 text-[#5a3825] hover:bg-blue-50 rounded-lg transition"
                        data-testid={`edit-tile-${tile.tile_id}`}
                      >
                        <Edit2 className="h-5 w-5" />
                      </button>
                      <button
                        onClick={() => handleDelete(tile.tile_id)}
                        className="p-2 text-red-600 hover:bg-red-50 rounded-lg transition"
                        data-testid={`delete-tile-${tile.tile_id}`}
                      >
                        <Trash2 className="h-5 w-5" />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {filteredTiles.length === 0 && (
            <div className="text-center py-12 text-gray-500">
              <Package className="h-16 w-16 mx-auto mb-4 text-gray-300" />
              <p>No tiles found. Add your first tile to get started!</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

// Customers Management Component
function CustomersManagement({ customers, fetchCustomers }) {
  const [showForm, setShowForm] = useState(false);
  const [editingCustomer, setEditingCustomer] = useState(null);
  const [formData, setFormData] = useState({
    name: '',
    phone: '',
    address: '',
    gstin: ''
  });
  const [searchTerm, setSearchTerm] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      if (editingCustomer) {
        await axios.put(`${API}/customers/${editingCustomer.customer_id}`, formData);
      } else {
        await axios.post(`${API}/customers`, formData);
      }
      fetchCustomers();
      resetForm();
    } catch (error) {
      alert('Error: ' + (error.response?.data?.detail || error.message));
    }
  };

  const handleDelete = async (customerId) => {
    if (window.confirm('Are you sure you want to delete this customer?')) {
      try {
        await axios.delete(`${API}/customers/${customerId}`);
        fetchCustomers();
      } catch (error) {
        alert('Error deleting customer: ' + error.message);
      }
    }
  };

  const resetForm = () => {
    setFormData({ name: '', phone: '', address: '', gstin: '' });
    setEditingCustomer(null);
    setShowForm(false);
  };

  const startEdit = (customer) => {
    setFormData({
      name: customer.name,
      phone: customer.phone,
      address: customer.address,
      gstin: customer.gstin || ''
    });
    setEditingCustomer(customer);
    setShowForm(true);
  };

  const filteredCustomers = customers.filter(customer =>
    customer.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    customer.phone.includes(searchTerm)
  );

  return (
    <div className="space-y-6" data-testid="customers-management-view">
      {/* Header */}
      <div className="bg-white rounded-xl shadow-lg p-6">
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
          <div>
            <h2 className="text-2xl font-bold text-gray-800">Customers Management</h2>
            <p className="text-gray-600 text-sm">Manage your customer database</p>
          </div>
          <button
            onClick={() => setShowForm(!showForm)}
            className="bg-gradient-to-r from-[#5a3825] to-[#6b4a35] text-white px-6 py-3 rounded-lg hover:shadow-lg transition-all duration-200 flex items-center space-x-2"
            data-testid="add-customer-button"
          >
            <Plus className="h-5 w-5" />
            <span>Add New Customer</span>
          </button>
        </div>

        {/* Search */}
        <div className="mt-4">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
            <input
              type="text"
              placeholder="Search customers by name or phone..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-[#5a3825] focus:border-transparent"
              data-testid="search-customers-input"
            />
          </div>
        </div>
      </div>

      {/* Form */}
      {showForm && (
        <div className="bg-white rounded-xl shadow-lg p-6" data-testid="customer-form">
          <div className="flex justify-between items-center mb-6">
            <h3 className="text-xl font-bold text-gray-800">
              {editingCustomer ? 'Edit Customer' : 'Add New Customer'}
            </h3>
            <button onClick={resetForm} className="text-gray-500 hover:text-gray-700">
              <X className="h-6 w-6" />
            </button>
          </div>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Customer Name *</label>
                <input
                  type="text"
                  required
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-[#5a3825] focus:border-transparent"
                  data-testid="customer-name-input"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Phone Number *</label>
                <input
                  type="tel"
                  required
                  value={formData.phone}
                  onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-[#5a3825] focus:border-transparent"
                  data-testid="customer-phone-input"
                />
              </div>
              <div className="md:col-span-2">
                <label className="block text-sm font-medium text-gray-700 mb-2">Address *</label>
                <textarea
                  required
                  value={formData.address}
                  onChange={(e) => setFormData({ ...formData, address: e.target.value })}
                  rows="3"
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-[#5a3825] focus:border-transparent"
                  data-testid="customer-address-input"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">GSTIN (Optional)</label>
                <input
                  type="text"
                  value={formData.gstin}
                  onChange={(e) => setFormData({ ...formData, gstin: e.target.value })}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-[#5a3825] focus:border-transparent"
                  data-testid="customer-gstin-input"
                />
              </div>
            </div>
            <div className="flex justify-end space-x-3 pt-4">
              <button
                type="button"
                onClick={resetForm}
                className="px-6 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50"
                data-testid="customer-cancel-button"
              >
                Cancel
              </button>
              <button
                type="submit"
                className="px-6 py-2 bg-gradient-to-r from-[#5a3825] to-[#6b4a35] text-white rounded-lg hover:shadow-lg transition-all"
                data-testid="customer-save-button"
              >
                <Save className="inline h-5 w-5 mr-2" />
                {editingCustomer ? 'Update' : 'Save'} Customer
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Customers List */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {filteredCustomers.map((customer) => (
          <div
            key={customer.customer_id}
            className="bg-white rounded-xl shadow-md hover:shadow-xl transition-shadow p-6"
            data-testid={`customer-card-${customer.customer_id}`}
          >
            <div className="flex justify-between items-start mb-4">
              <div className="flex items-center space-x-3">
                <div className="bg-gradient-to-r from-[#5a3825] to-[#6b4a35] p-3 rounded-full">
                  <Users className="h-6 w-6 text-white" />
                </div>
                <div>
                  <h3 className="font-bold text-gray-800">{customer.name}</h3>
                  <p className="text-sm text-gray-600">{customer.phone}</p>
                </div>
              </div>
              <div className="flex space-x-2">
                <button
                  onClick={() => startEdit(customer)}
                  className="p-2 text-[#5a3825] hover:bg-blue-50 rounded-lg transition"
                  data-testid={`edit-customer-${customer.customer_id}`}
                >
                  <Edit2 className="h-4 w-4" />
                </button>
                <button
                  onClick={() => handleDelete(customer.customer_id)}
                  className="p-2 text-red-600 hover:bg-red-50 rounded-lg transition"
                  data-testid={`delete-customer-${customer.customer_id}`}
                >
                  <Trash2 className="h-4 w-4" />
                </button>
              </div>
            </div>
            <div className="space-y-2 text-sm">
              <p className="text-gray-700">
                <span className="font-medium">Address:</span> {customer.address}
              </p>
              {customer.gstin && (
                <p className="text-gray-700">
                  <span className="font-medium">GSTIN:</span> {customer.gstin}
                </p>
              )}
              <p className="text-gray-700">
                <span className="font-medium">Pending:</span>{' '}
                <span className={`font-bold ${
                  customer.total_pending > 0 ? 'text-red-600' : 'text-green-600'
                }`}>
                  ₹{customer.total_pending.toFixed(2)}
                </span>
              </p>
            </div>
          </div>
        ))}
      </div>
      {filteredCustomers.length === 0 && (
        <div className="bg-white rounded-xl shadow-lg p-12 text-center">
          <Users className="h-16 w-16 mx-auto mb-4 text-gray-300" />
          <p className="text-gray-500">No customers found. Add your first customer to get started!</p>
        </div>
      )}
    </div>
  );
}

// Invoices Management Component
function InvoicesManagement({ invoices, tiles, customers, fetchInvoices }) {
  const [showForm, setShowForm] = useState(false);
  const [editingInvoice, setEditingInvoice] = useState(null);
  const [formData, setFormData] = useState({
    customer_id: '',
    line_items: [],
    transport_charges: 0,
    unloading_charges: 0,
    amount_paid: 0,
    status: 'Draft'
  });
  const [currentLineItem, setCurrentLineItem] = useState({
    location: '',
    tile_name: '',  // Manual text entry
    size: '',       // Select from existing sizes
    box_qty: 0,
    extra_sqft: 0,
    rate_per_sqft: 0,
    rate_per_box: 0,
    discount_percent: 0,
    tile_image: null,
    coverage: 0,    // Auto-fetched from tile
    box_packing: 0  // Auto-fetched from tile
  });
  const [searchTerm, setSearchTerm] = useState('');
  const [uploadingImage, setUploadingImage] = useState(false);
  const [showCamera, setShowCamera] = useState(false);

  // Get unique sizes from tiles for dropdown
  const availableSizes = useMemo(() => {
    const sizes = [...new Set(tiles.map(t => t.size))];
    return sizes;
  }, [tiles]);

  // Calculate current line item cost preview
  const lineItemPreview = useMemo(() => {
    if (!currentLineItem.tile_name || !currentLineItem.size) return null;
    
    const coverage = currentLineItem.coverage || 0;
    if (coverage <= 0) return null;
    
    const totalSqft = (currentLineItem.box_qty * coverage) + currentLineItem.extra_sqft;
    const beforeDiscount = totalSqft * currentLineItem.rate_per_sqft;
    const discount = beforeDiscount * (currentLineItem.discount_percent / 100);
    const finalAmount = beforeDiscount - discount;
    
    return {
      coverage: coverage,
      totalSqft: totalSqft.toFixed(2),
      beforeDiscount: beforeDiscount.toFixed(2),
      discount: discount.toFixed(2),
      finalAmount: finalAmount.toFixed(2)
    };
  }, [currentLineItem]);

  // Handle box quantity change
  const handleBoxQtyChange = (value) => {
    const boxQty = parseInt(value) || 0;
    setCurrentLineItem({
      ...currentLineItem,
      box_qty: boxQty
    });
  };

  // Handle extra sqft change
  const handleExtraSqftChange = (value) => {
    const extraSqft = parseFloat(value) || 0;
    setCurrentLineItem({
      ...currentLineItem,
      extra_sqft: extraSqft
    });
  };

  // Handle Rate per Sqft change - bidirectional calculation
  const handleRateSqftChange = (value) => {
    const rateSqft = parseFloat(value) || 0;
    const coverage = currentLineItem.coverage || 0;
    
    setCurrentLineItem({
      ...currentLineItem,
      rate_per_sqft: rateSqft,
      rate_per_box: coverage > 0 ? parseFloat((rateSqft * coverage).toFixed(2)) : 0
    });
  };

  // Handle Rate per Box change - bidirectional calculation
  const handleRateBoxChange = (value) => {
    const rateBox = parseFloat(value) || 0;
    const coverage = currentLineItem.coverage || 0;
    
    setCurrentLineItem({
      ...currentLineItem,
      rate_per_box: rateBox,
      rate_per_sqft: coverage > 0 ? parseFloat((rateBox / coverage).toFixed(2)) : 0
    });
  };

  // Handle size selection - auto-fetch coverage and box_packing
  const handleSizeSelect = async (size) => {
    if (!size) {
      setCurrentLineItem({
        ...currentLineItem,
        size: '',
        coverage: 0,
        box_packing: 0
      });
      return;
    }
    
    // Find tile with this size
    const tile = tiles.find(t => t.size === size);
    if (tile) {
      setCurrentLineItem({
        ...currentLineItem,
        size: size,
        coverage: tile.coverage || tile.box_coverage_sqft || 0,
        box_packing: tile.box_packing || 0
      });
    } else {
      setCurrentLineItem({
        ...currentLineItem,
        size: size,
        coverage: 0,
        box_packing: 0
      });
    }
  };

  // Calculate real-time totals
  const calculateTotals = useMemo(() => {
    const subtotal = formData.line_items.reduce((sum, item) => {
      // Use coverage stored in the line item
      const coverage = item.coverage || item.box_coverage_sqft || 0;
      const totalSqft = (item.box_qty * coverage) + item.extra_sqft;
      const beforeDiscount = totalSqft * item.rate_per_sqft;
      const discount = beforeDiscount * (item.discount_percent / 100);
      return sum + (beforeDiscount - discount);
    }, 0);
    
    const transport = parseFloat(formData.transport_charges) || 0;
    const unloading = parseFloat(formData.unloading_charges) || 0;
    const grandTotal = subtotal + transport + unloading;
    const paid = parseFloat(formData.amount_paid) || 0;
    const pending = grandTotal - paid;

    return { subtotal, transport, unloading, grandTotal, paid, pending };
  }, [formData.line_items, formData.transport_charges, formData.unloading_charges, formData.amount_paid]);

  const handleImageUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    if (file.size > 2 * 1024 * 1024) {
      alert('Image size should be less than 2MB');
      return;
    }

    if (!file.type.startsWith('image/')) {
      alert('Please upload an image file');
      return;
    }

    setUploadingImage(true);
    try {
      const reader = new FileReader();
      reader.onloadend = () => {
        setCurrentLineItem({
          ...currentLineItem,
          tile_image: reader.result
        });
        setUploadingImage(false);
      };
      reader.readAsDataURL(file);
    } catch (error) {
      alert('Error uploading image: ' + error.message);
      setUploadingImage(false);
    }
  };

  const handleCameraCapture = async () => {
    setShowCamera(true);
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ 
        video: { 
          facingMode: 'environment',
          width: { ideal: 1920 },
          height: { ideal: 1080 }
        } 
      });
      
      // Create camera modal
      const modal = document.createElement('div');
      modal.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0,0,0,0.95);
        z-index: 10000;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
      `;

      const video = document.createElement('video');
      video.style.cssText = `
        max-width: 90%;
        max-height: 70vh;
        border-radius: 8px;
      `;
      video.srcObject = stream;
      video.autoplay = true;
      video.playsInline = true;

      const buttonContainer = document.createElement('div');
      buttonContainer.style.cssText = `
        display: flex;
        gap: 20px;
        margin-top: 20px;
      `;

      const captureBtn = document.createElement('button');
      captureBtn.textContent = '📸 Capture';
      captureBtn.style.cssText = `
        padding: 15px 30px;
        background: #10b981;
        color: white;
        border: none;
        border-radius: 8px;
        font-size: 16px;
        font-weight: bold;
        cursor: pointer;
      `;

      const cancelBtn = document.createElement('button');
      cancelBtn.textContent = '✕ Cancel';
      cancelBtn.style.cssText = `
        padding: 15px 30px;
        background: #ef4444;
        color: white;
        border: none;
        border-radius: 8px;
        font-size: 16px;
        font-weight: bold;
        cursor: pointer;
      `;

      const closeCamera = () => {
        stream.getTracks().forEach(track => track.stop());
        document.body.removeChild(modal);
        setShowCamera(false);
      };

      captureBtn.onclick = () => {
        const canvas = document.createElement('canvas');
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;
        const context = canvas.getContext('2d');
        context.drawImage(video, 0, 0);
        
        const imageData = canvas.toDataURL('image/jpeg', 0.9);
        setCurrentLineItem({
          ...currentLineItem,
          tile_image: imageData
        });
        
        closeCamera();
      };

      cancelBtn.onclick = closeCamera;

      buttonContainer.appendChild(captureBtn);
      buttonContainer.appendChild(cancelBtn);
      modal.appendChild(video);
      modal.appendChild(buttonContainer);
      document.body.appendChild(modal);

    } catch (error) {
      setShowCamera(false);
      alert('Camera access denied or not available: ' + error.message);
    }
  };

  const handleRemoveImage = () => {
    setCurrentLineItem({
      ...currentLineItem,
      tile_image: null
    });
  };

  const handleAddLineItem = () => {
    if (!currentLineItem.location || !currentLineItem.tile_name || !currentLineItem.size) {
      alert('Please fill in all required fields (Location, Tile Name, Size)');
      return;
    }
    
    if (currentLineItem.rate_per_sqft <= 0 && currentLineItem.rate_per_box <= 0) {
      alert('Please enter Rate per Sqft or Rate per Box');
      return;
    }
    
    setFormData({
      ...formData,
      line_items: [...formData.line_items, { ...currentLineItem }]
    });
    
    setCurrentLineItem({
      location: '',
      tile_name: '',
      size: '',
      box_qty: 0,
      extra_sqft: 0,
      rate_per_sqft: 0,
      rate_per_box: 0,
      discount_percent: 0,
      tile_image: null,
      coverage: 0,
      box_packing: 0
    });
  };

  const handleRemoveLineItem = (index) => {
    const newItems = [...formData.line_items];
    newItems.splice(index, 1);
    setFormData({ ...formData, line_items: newItems });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (formData.line_items.length === 0) {
      alert('Please add at least one line item');
      return;
    }
    
    try {
      const dataToSend = {
        ...formData,
        transport_charges: parseFloat(formData.transport_charges),
        unloading_charges: parseFloat(formData.unloading_charges),
        amount_paid: parseFloat(formData.amount_paid)
      };

      if (editingInvoice) {
        await axios.put(`${API}/invoices/${editingInvoice.invoice_id}`, dataToSend);
      } else {
        await axios.post(`${API}/invoices`, dataToSend);
      }

      fetchInvoices();
      resetForm();
    } catch (error) {
      alert('Error: ' + (error.response?.data?.detail || error.message));
    }
  };

  const handleDelete = async (invoiceId) => {
    if (window.confirm('Are you sure you want to delete this invoice?')) {
      try {
        await axios.delete(`${API}/invoices/${invoiceId}`);
        fetchInvoices();
      } catch (error) {
        alert('Error deleting invoice: ' + error.message);
      }
    }
  };

  const handleDownloadPDF = async (invoiceId) => {
    try {
      const response = await axios.get(`${API}/invoices/${invoiceId}/pdf`, {
        responseType: 'blob'
      });
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `Invoice_${invoiceId}.pdf`);
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (error) {
      alert('Error downloading PDF: ' + error.message);
    }
  };

  const handleWhatsAppShare = async (invoice) => {
    try {
      const message = `📋 *Invoice ${invoice.invoice_id}*\n\n` +
        `👤 Customer: ${invoice.customer_name}\n` +
        `📞 Phone: ${invoice.customer_phone}\n` +
        `💰 Total Amount: ₹${invoice.grand_total.toFixed(2)}\n` +
        `✅ Paid: ₹${invoice.amount_paid.toFixed(2)}\n` +
        `⏳ Pending: ₹${invoice.pending_balance.toFixed(2)}\n` +
        `📊 Status: ${invoice.status}`;
      
      // Fetch PDF as blob
      const response = await axios.get(`${API}/invoices/${invoice.invoice_id}/pdf`, {
        responseType: 'blob'
      });
      const pdfBlob = new Blob([response.data], { type: 'application/pdf' });
      const pdfFile = new File([pdfBlob], `Invoice_${invoice.invoice_id}.pdf`, { type: 'application/pdf' });
      
      // Check if Web Share API with files is supported (mainly mobile)
      if (navigator.canShare && navigator.canShare({ files: [pdfFile] })) {
        await navigator.share({
          files: [pdfFile],
          title: `Invoice ${invoice.invoice_id}`,
          text: message
        });
      } else {
        // Fallback: Download PDF and open WhatsApp with message
        const url = window.URL.createObjectURL(pdfBlob);
        const link = document.createElement('a');
        link.href = url;
        link.setAttribute('download', `Invoice_${invoice.invoice_id}.pdf`);
        document.body.appendChild(link);
        link.click();
        link.remove();
        
        // Open WhatsApp with message
        const pdfUrl = `${BACKEND_URL}/api/public/invoices/${invoice.invoice_id}/pdf`;
        const fullMessage = message + `\n\n📥 Download Invoice PDF:\n${pdfUrl}`;
        const encodedMessage = encodeURIComponent(fullMessage);
        window.open(`https://wa.me/?text=${encodedMessage}`, '_blank');
      }
    } catch (error) {
      alert('Error sharing on WhatsApp: ' + error.message);
    }
  };

  const startEdit = (invoice) => {
    setFormData({
      customer_id: invoice.customer_id,
      line_items: invoice.line_items,
      transport_charges: invoice.transport_charges,
      unloading_charges: invoice.unloading_charges || 0,
      amount_paid: invoice.amount_paid,
      status: invoice.status
    });
    setEditingInvoice(invoice);
    setShowForm(true);
  };

  const resetForm = () => {
    setFormData({
      customer_id: '',
      line_items: [],
      transport_charges: 0,
      unloading_charges: 0,
      amount_paid: 0,
      status: 'Draft'
    });
    setCurrentLineItem({
      location: '',
      tile_name: '',
      size: '',
      box_qty: 0,
      extra_sqft: 0,
      rate_per_sqft: 0,
      rate_per_box: 0,
      discount_percent: 0,
      tile_image: null,
      coverage: 0,
      box_packing: 0
    });
    setEditingInvoice(null);
    setShowForm(false);
  };

  const filteredInvoices = invoices.filter(invoice =>
    invoice.invoice_id.toLowerCase().includes(searchTerm.toLowerCase()) ||
    invoice.customer_name.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="space-y-6" data-testid="invoices-management-view">
      {/* Header */}
      <div className="bg-white rounded-xl shadow-lg p-6">
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
          <div>
            <h2 className="text-2xl font-bold text-gray-800">Invoices Management</h2>
            <p className="text-gray-600 text-sm">Create and manage invoices</p>
          </div>
          <button
            onClick={() => setShowForm(!showForm)}
            className="bg-gradient-to-r from-[#5a3825] to-[#6b4a35] text-white px-6 py-3 rounded-lg hover:shadow-lg transition-all duration-200 flex items-center space-x-2"
            data-testid="add-invoice-button"
          >
            <Plus className="h-5 w-5" />
            <span>Create New Invoice</span>
          </button>
        </div>

        {/* Search */}
        <div className="mt-4">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
            <input
              type="text"
              placeholder="Search invoices by ID or customer name..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-[#5a3825] focus:border-transparent"
              data-testid="search-invoices-input"
            />
          </div>
        </div>
      </div>

      {/* Form */}
      {showForm && (
        <div className="bg-white rounded-xl shadow-lg p-6" data-testid="invoice-form">
          <div className="flex justify-between items-center mb-6">
            <h3 className="text-xl font-bold text-gray-800">
              {editingInvoice ? 'Edit Invoice' : 'Create New Invoice'}
            </h3>
            <button onClick={resetForm} className="text-gray-500 hover:text-gray-700">
              <X className="h-6 w-6" />
            </button>
          </div>
          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Customer Selection */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Select Customer *</label>
              <select
                required
                value={formData.customer_id}
                onChange={(e) => setFormData({ ...formData, customer_id: e.target.value })}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-[#5a3825] focus:border-transparent"
                data-testid="invoice-customer-select"
              >
                <option value="">-- Select Customer --</option>
                {customers.map(customer => (
                  <option key={customer.customer_id} value={customer.customer_id}>
                    {customer.name} - {customer.phone}
                  </option>
                ))}
              </select>
            </div>

            {/* Line Items Section */}
            <div className="border-t pt-6">
              <h4 className="text-lg font-bold text-gray-800 mb-4">Add Line Items</h4>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Location *</label>
                  <input
                    type="text"
                    value={currentLineItem.location}
                    onChange={(e) => setCurrentLineItem({ ...currentLineItem, location: e.target.value })}
                    placeholder="e.g., Main Floor"
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-[#5a3825] focus:border-transparent"
                    data-testid="line-item-location-input"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Tile Name *</label>
                  <input
                    type="text"
                    value={currentLineItem.tile_name}
                    onChange={(e) => setCurrentLineItem({ ...currentLineItem, tile_name: e.target.value })}
                    placeholder="e.g., Vitrified Premium"
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-[#5a3825] focus:border-transparent"
                    data-testid="line-item-tile-name-input"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Select Size *</label>
                  <select
                    value={currentLineItem.size}
                    onChange={(e) => handleSizeSelect(e.target.value)}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-[#5a3825] focus:border-transparent"
                    data-testid="line-item-size-select"
                  >
                    <option value="">-- Select Size --</option>
                    {availableSizes.map(size => (
                      <option key={size} value={size}>{size}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Box Quantity *</label>
                  <input
                    type="number"
                    min="0"
                    value={currentLineItem.box_qty}
                    onChange={(e) => handleBoxQtyChange(e.target.value)}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-[#5a3825] focus:border-transparent"
                    data-testid="line-item-box-qty-input"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Extra Sqft</label>
                  <input
                    type="number"
                    step="0.01"
                    min="0"
                    value={currentLineItem.extra_sqft}
                    onChange={(e) => handleExtraSqftChange(e.target.value)}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-[#5a3825] focus:border-transparent"
                    data-testid="line-item-extra-sqft-input"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Rate per Sqft (₹) *</label>
                  <input
                    type="number"
                    step="0.01"
                    min="0"
                    value={currentLineItem.rate_per_sqft}
                    onChange={(e) => handleRateSqftChange(e.target.value)}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-[#5a3825] focus:border-transparent"
                    data-testid="line-item-rate-sqft-input"
                    placeholder="Enter rate per sqft"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Rate per Box (₹) *</label>
                  <input
                    type="number"
                    step="0.01"
                    min="0"
                    value={currentLineItem.rate_per_box}
                    onChange={(e) => handleRateBoxChange(e.target.value)}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-[#5a3825] focus:border-transparent"
                    data-testid="line-item-rate-box-input"
                    placeholder="Auto-calculated or enter"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Discount %</label>
                  <input
                    type="number"
                    step="0.1"
                    min="0"
                    max="100"
                    value={currentLineItem.discount_percent}
                    onChange={(e) => setCurrentLineItem({ ...currentLineItem, discount_percent: parseFloat(e.target.value) || 0 })}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-[#5a3825] focus:border-transparent"
                    data-testid="line-item-discount-input"
                  />
                </div>
              </div>

              {/* Auto-populated tile info display */}
              {currentLineItem.coverage > 0 && (
                <div className="bg-blue-50 rounded-lg p-3 border border-blue-200 mt-3">
                  <div className="flex gap-6">
                    <p className="text-sm text-blue-800">
                      <span className="font-medium">Coverage:</span> {currentLineItem.coverage} sqft/box
                    </p>
                    {currentLineItem.box_packing > 0 && (
                      <p className="text-sm text-blue-800">
                        <span className="font-medium">Box Packing:</span> {currentLineItem.box_packing} tiles/box
                      </p>
                    )}
                  </div>
                </div>
              )}

              {/* Line Item Cost Preview */}
              {lineItemPreview && currentLineItem.tile_name && (currentLineItem.rate_per_sqft > 0 || currentLineItem.rate_per_box > 0) && (
                <div className="bg-purple-50 rounded-lg p-3 border-2 border-purple-200 mt-3">
                  <h5 className="text-sm font-bold text-gray-800 mb-2">Current Item Cost Preview</h5>
                  <div className="grid grid-cols-2 md:grid-cols-5 gap-2 text-xs">
                    <div>
                      <span className="text-gray-600">Coverage:</span>
                      <span className="ml-1 font-bold text-blue-700">{lineItemPreview.coverage} sqft/box</span>
                    </div>
                    <div>
                      <span className="text-gray-600">Total Sqft:</span>
                      <span className="ml-1 font-bold text-purple-700">{lineItemPreview.totalSqft}</span>
                    </div>
                    <div>
                      <span className="text-gray-600">Before Disc:</span>
                      <span className="ml-1 font-bold text-purple-700">₹{lineItemPreview.beforeDiscount}</span>
                    </div>
                    <div>
                      <span className="text-gray-600">Discount:</span>
                      <span className="ml-1 font-bold text-red-600">-₹{lineItemPreview.discount}</span>
                    </div>
                    <div>
                      <span className="text-gray-600">Final:</span>
                      <span className="ml-1 font-bold text-green-700">₹{lineItemPreview.finalAmount}</span>
                    </div>
                  </div>
                </div>
              )}

              {/* Photo Upload Section */}
              <div className="mt-4 border-t pt-4">
                <label className="block text-sm font-medium text-gray-700 mb-3">Tile Photo (Optional)</label>
                <div className="flex flex-wrap gap-3">
                  <button
                    type="button"
                    onClick={handleCameraCapture}
                    className="flex items-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition"
                    data-testid="camera-capture-button"
                  >
                    <Camera className="h-5 w-5" />
                    <span>Take Photo</span>
                  </button>

                  <label className="flex items-center space-x-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition cursor-pointer">
                    <Upload className="h-5 w-5" />
                    <span>Upload Image</span>
                    <input
                      type="file"
                      accept="image/*"
                      onChange={handleImageUpload}
                      className="hidden"
                      data-testid="image-upload-input"
                    />
                  </label>

                  {currentLineItem.tile_image && (
                    <button
                      type="button"
                      onClick={handleRemoveImage}
                      className="flex items-center space-x-2 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition"
                      data-testid="remove-image-button"
                    >
                      <X className="h-5 w-5" />
                      <span>Remove</span>
                    </button>
                  )}
                </div>

                {uploadingImage && (
                  <div className="mt-3 text-center text-gray-600">
                    <div className="spinner mx-auto"></div>
                    <p className="mt-2">Uploading image...</p>
                  </div>
                )}
                
                {currentLineItem.tile_image && !uploadingImage && (
                  <div className="mt-3">
                    <div className="relative inline-block">
                      <img
                        src={currentLineItem.tile_image}
                        alt="Tile preview"
                        className="h-32 w-32 object-cover rounded-lg border-2 border-gray-300"
                        data-testid="tile-image-preview"
                      />
                      <div className="absolute top-2 right-2 bg-green-500 text-white rounded-full p-1">
                        <Image className="h-4 w-4" />
                      </div>
                    </div>
                    <p className="text-xs text-gray-500 mt-2">Photo attached and will be included in invoice</p>
                  </div>
                )}
              </div>

              {/* Add Item Button */}
              <div className="mt-4">
                <button
                  type="button"
                  onClick={handleAddLineItem}
                  className="w-full px-4 py-2 bg-gradient-to-r from-[#5a3825] to-[#6b4a35] text-white rounded-lg hover:shadow-lg transition-all"
                  data-testid="add-line-item-button"
                >
                  <Plus className="inline h-5 w-5 mr-2" />
                  Add Item to Invoice
                </button>
              </div>

              {/* Line Items List */}
              {formData.line_items.length > 0 && (
                <div className="mt-6 overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead className="bg-gray-100">
                      <tr>
                        <th className="px-4 py-2 text-left">Image</th>
                        <th className="px-4 py-2 text-left">Location</th>
                        <th className="px-4 py-2 text-left">Tile Name</th>
                        <th className="px-4 py-2 text-left">Size</th>
                        <th className="px-4 py-2 text-left">Box Qty</th>
                        <th className="px-4 py-2 text-left">Rate/Sqft</th>
                        <th className="px-4 py-2 text-left">Disc%</th>
                        <th className="px-4 py-2 text-right">Actions</th>
                      </tr>
                    </thead>
                    <tbody>
                      {formData.line_items.map((item, index) => (
                        <tr key={index} className="border-b" data-testid={`line-item-${index}`}>
                          <td className="px-4 py-2">
                            {item.tile_image ? (
                              <img
                                src={item.tile_image}
                                alt="Tile"
                                className="h-12 w-12 object-cover rounded border"
                                data-testid={`line-item-image-${index}`}
                              />
                            ) : (
                              <div className="h-12 w-12 bg-gray-100 rounded flex items-center justify-center">
                                <Image className="h-6 w-6 text-gray-400" />
                              </div>
                            )}
                          </td>
                          <td className="px-4 py-2">{item.location}</td>
                          <td className="px-4 py-2">{item.tile_name || item.product_name}</td>
                          <td className="px-4 py-2">{item.size}</td>
                          <td className="px-4 py-2">{item.box_qty}</td>
                          <td className="px-4 py-2">₹{item.rate_per_sqft}</td>
                          <td className="px-4 py-2">{item.discount_percent}%</td>
                          <td className="px-4 py-2 text-right">
                            <button
                              type="button"
                              onClick={() => handleRemoveLineItem(index)}
                              className="text-red-600 hover:text-red-800"
                              data-testid={`remove-line-item-${index}`}
                            >
                              <Trash2 className="h-4 w-4" />
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>

            {/* Total Calculation Display */}
            {formData.line_items.length > 0 && (
              <div className="bg-blue-50 rounded-lg p-4 border-2 border-blue-200">
                <h4 className="text-md font-bold text-gray-800 mb-3">Invoice Summary</h4>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-gray-700">Subtotal:</span>
                    <span className="font-semibold">₹{calculateTotals.subtotal.toFixed(2)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-700">Transport Charges:</span>
                    <span className="font-semibold">₹{calculateTotals.transport.toFixed(2)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-700">Unloading Charges:</span>
                    <span className="font-semibold">₹{calculateTotals.unloading.toFixed(2)}</span>
                  </div>
                  <div className="flex justify-between border-t-2 border-blue-300 pt-2">
                    <span className="text-gray-800 font-bold">Grand Total:</span>
                    <span className="font-bold text-lg text-[#5a3825]">₹{calculateTotals.grandTotal.toFixed(2)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-700">Amount Paid:</span>
                    <span className="font-semibold text-green-600">₹{calculateTotals.paid.toFixed(2)}</span>
                  </div>
                  <div className="flex justify-between border-t-2 border-blue-300 pt-2">
                    <span className="text-gray-800 font-bold">Pending Balance:</span>
                    <span className="font-bold text-lg text-red-600">₹{calculateTotals.pending.toFixed(2)}</span>
                  </div>
                </div>
              </div>
            )}

            {/* Additional Details */}
            <div className="border-t pt-6">
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Transport Charges (₹)</label>
                  <input
                    type="number"
                    step="0.01"
                    min="0"
                    value={formData.transport_charges}
                    onChange={(e) => setFormData({ ...formData, transport_charges: parseFloat(e.target.value) || 0 })}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-[#5a3825] focus:border-transparent"
                    data-testid="invoice-transport-charges-input"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Unloading Charges (₹)</label>
                  <input
                    type="number"
                    step="0.01"
                    min="0"
                    value={formData.unloading_charges}
                    onChange={(e) => setFormData({ ...formData, unloading_charges: parseFloat(e.target.value) || 0 })}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-[#5a3825] focus:border-transparent"
                    data-testid="invoice-unloading-charges-input"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Amount Paid (₹)</label>
                  <input
                    type="number"
                    step="0.01"
                    min="0"
                    value={formData.amount_paid}
                    onChange={(e) => setFormData({ ...formData, amount_paid: parseFloat(e.target.value) || 0 })}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-[#5a3825] focus:border-transparent"
                    data-testid="invoice-amount-paid-input"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Status</label>
                  <select
                    value={formData.status}
                    onChange={(e) => setFormData({ ...formData, status: e.target.value })}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-[#5a3825] focus:border-transparent"
                    data-testid="invoice-status-select"
                  >
                    <option value="Draft">Draft</option>
                    <option value="Sent">Sent</option>
                    <option value="Paid">Paid</option>
                    <option value="Cancelled">Cancelled</option>
                  </select>
                </div>
              </div>
            </div>

            <div className="flex justify-end space-x-3 pt-4">
              <button
                type="button"
                onClick={resetForm}
                className="px-6 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50"
                data-testid="invoice-cancel-button"
              >
                Cancel
              </button>
              <button
                type="submit"
                className="px-6 py-2 bg-gradient-to-r from-[#5a3825] to-[#6b4a35] text-white rounded-lg hover:shadow-lg transition-all"
                data-testid="invoice-save-button"
              >
                <Save className="inline h-5 w-5 mr-2" />
                {editingInvoice ? 'Update' : 'Create'} Invoice
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Invoices List */}
      <div className="space-y-4">
        {filteredInvoices.map((invoice) => (
          <div
            key={invoice.invoice_id}
            className="bg-white rounded-xl shadow-md hover:shadow-xl transition-shadow p-6"
            data-testid={`invoice-card-${invoice.invoice_id}`}
          >
            <div className="flex flex-col lg:flex-row justify-between gap-4">
              <div className="flex-1">
                <div className="flex items-center space-x-3 mb-3">
                  <div className="bg-gradient-to-r from-purple-500 to-pink-500 p-3 rounded-lg">
                    <FileText className="h-6 w-6 text-white" />
                  </div>
                  <div>
                    <h3 className="text-lg font-bold text-gray-800">{invoice.invoice_id}</h3>
                    <p className="text-sm text-gray-600">
                      {new Date(invoice.invoice_date).toLocaleDateString()}
                    </p>
                  </div>
                  <span className={`px-3 py-1 rounded-full text-xs font-semibold ${
                    invoice.status === 'Paid' ? 'bg-green-100 text-green-800' :
                    invoice.status === 'Draft' ? 'bg-yellow-100 text-yellow-800' :
                    invoice.status === 'Sent' ? 'bg-blue-100 text-blue-800' :
                    'bg-gray-100 text-gray-800'
                  }`}>
                    {invoice.status}
                  </span>
                </div>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                  <div>
                    <p className="text-gray-600">Customer</p>
                    <p className="font-semibold text-gray-800">{invoice.customer_name}</p>
                  </div>
                  <div>
                    <p className="text-gray-600">Grand Total</p>
                    <p className="font-bold text-gray-800">₹{invoice.grand_total.toFixed(2)}</p>
                  </div>
                  <div>
                    <p className="text-gray-600">Amount Paid</p>
                    <p className="font-semibold text-green-600">₹{invoice.amount_paid.toFixed(2)}</p>
                  </div>
                  <div>
                    <p className="text-gray-600">Pending</p>
                    <p className="font-bold text-red-600">₹{invoice.pending_balance.toFixed(2)}</p>
                  </div>
                </div>
              </div>
              <div className="flex lg:flex-col justify-end gap-2">
                <button
                  onClick={() => startEdit(invoice)}
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition flex items-center space-x-2"
                  data-testid={`edit-invoice-${invoice.invoice_id}`}
                  disabled={invoice.status === 'Paid'}
                >
                  <Edit2 className="h-4 w-4" />
                  <span className="hidden sm:inline">Edit</span>
                </button>
                <button
                  onClick={() => handleDownloadPDF(invoice.invoice_id)}
                  className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition flex items-center space-x-2"
                  data-testid={`download-pdf-${invoice.invoice_id}`}
                >
                  <Download className="h-4 w-4" />
                  <span className="hidden sm:inline">PDF</span>
                </button>
                <button
                  onClick={() => handleWhatsAppShare(invoice)}
                  className="px-4 py-2 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 transition flex items-center space-x-2"
                  data-testid={`whatsapp-share-${invoice.invoice_id}`}
                >
                  <Share2 className="h-4 w-4" />
                  <span className="hidden sm:inline">Share</span>
                </button>
                <button
                  onClick={() => handleDelete(invoice.invoice_id)}
                  className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition flex items-center space-x-2"
                  data-testid={`delete-invoice-${invoice.invoice_id}`}
                  disabled={invoice.status === 'Paid'}
                >
                  <Trash2 className="h-4 w-4" />
                  <span className="hidden sm:inline">Delete</span>
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>
      {filteredInvoices.length === 0 && (
        <div className="bg-white rounded-xl shadow-lg p-12 text-center">
          <FileText className="h-16 w-16 mx-auto mb-4 text-gray-300" />
          <p className="text-gray-500">No invoices found. Create your first invoice to get started!</p>
        </div>
      )}
    </div>
  );
}

export default App;
