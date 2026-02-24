import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { 
  Package, Users, FileText, Plus, Edit2, Trash2, Save, X, 
  Download, Share2, Search, LogOut
} from 'lucide-react';
import './App.css';
import Login from './components/Login';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8000';
const API = `${BACKEND_URL}/api`;

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [activeTab, setActiveTab] = useState('dashboard');
  const [tiles, setTiles] = useState([]);
  const [customers, setCustomers] = useState([]);
  const [invoices, setInvoices] = useState([]);
  const [loading, setLoading] = useState(false);

  // Tile form state
  const [tileForm, setTileForm] = useState({
    size: '',
    coverage: '',
    box_packing: '',
    product_name: '',
    rate_per_sqft: '',
    rate_per_box: ''
  });
  const [editingTile, setEditingTile] = useState(null);
  const [showTileForm, setShowTileForm] = useState(false);

  // Customer form state
  const [customerForm, setCustomerForm] = useState({
    name: '',
    phone: '',
    address: '',
    gstin: ''
  });
  const [editingCustomer, setEditingCustomer] = useState(null);
  const [showCustomerForm, setShowCustomerForm] = useState(false);

  // Invoice form state
  const [invoiceForm, setInvoiceForm] = useState({
    customer_id: '',
    line_items: [],
    gst_percent: 18,
    transport_charges: 0,
    unloading_charges: 0,
    amount_paid: 0,
    status: 'Draft',
    date: new Date().toISOString().split('T')[0]
  });
  const [currentLineItem, setCurrentLineItem] = useState({
    tile_id: '',
    section_name: '',
    product_name: '',
    size: '',
    coverage: 0,
    rate_per_sqft: 0,
    rate_per_box: 0,
    box_qty: 0,
    extra_sqft: 0,
    discount_percent: 0
  });
  const [showInvoiceForm, setShowInvoiceForm] = useState(false);

  // Check authentication
  useEffect(() => {
    const auth = localStorage.getItem('tileShopAuth');
    if (auth === 'true') {
      setIsAuthenticated(true);
    }
  }, []);

  // Load data when authenticated
  useEffect(() => {
    if (isAuthenticated) {
      fetchTiles();
      fetchCustomers();
      fetchInvoices();
    }
  }, [isAuthenticated]);

  const handleLogin = () => {
    setIsAuthenticated(true);
  };

  const handleLogout = () => {
    localStorage.removeItem('tileShopAuth');
    localStorage.removeItem('tileShopUser');
    setIsAuthenticated(false);
    setActiveTab('dashboard');
  };

  // ==================== TILES ====================
  const fetchTiles = async () => {
    try {
      const response = await axios.get(`${API}/tiles`);
      setTiles(response.data || []);
    } catch (error) {
      console.error('Error fetching tiles:', error);
      alert('Error loading tiles');
    }
  };

  const handleSaveTile = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      const tileData = {
        ...tileForm,
        coverage: parseFloat(tileForm.coverage) || 0,
        box_packing: parseInt(tileForm.box_packing) || 0,
        rate_per_sqft: parseFloat(tileForm.rate_per_sqft) || 0,
        rate_per_box: parseFloat(tileForm.rate_per_box) || 0
      };

      if (editingTile) {
        await axios.put(`${API}/tiles/${editingTile.tile_id}`, tileData);
      } else {
        await axios.post(`${API}/tiles`, tileData);
      }

      fetchTiles();
      resetTileForm();
      alert(editingTile ? 'Tile updated!' : 'Tile created!');
    } catch (error) {
      console.error('Error saving tile:', error);
      alert('Error saving tile: ' + (error.response?.data?.error || error.message));
    } finally {
      setLoading(false);
    }
  };

  const handleEditTile = (tile) => {
    setTileForm({
      size: tile.size,
      coverage: tile.coverage,
      box_packing: tile.box_packing,
      product_name: tile.product_name || '',
      rate_per_sqft: tile.rate_per_sqft || '',
      rate_per_box: tile.rate_per_box || ''
    });
    setEditingTile(tile);
    setShowTileForm(true);
  };

  const handleDeleteTile = async (tileId) => {
    if (!window.confirm('Are you sure you want to delete this tile?')) return;
    try {
      await axios.delete(`${API}/tiles/${tileId}`);
      fetchTiles();
      alert('Tile deleted!');
    } catch (error) {
      console.error('Error deleting tile:', error);
      alert('Error deleting tile');
    }
  };

  const resetTileForm = () => {
    setTileForm({
      size: '',
      coverage: '',
      box_packing: '',
      product_name: '',
      rate_per_sqft: '',
      rate_per_box: ''
    });
    setEditingTile(null);
    setShowTileForm(false);
  };

  // ==================== CUSTOMERS ====================
  const fetchCustomers = async () => {
    try {
      const response = await axios.get(`${API}/customers`);
      setCustomers(response.data || []);
    } catch (error) {
      console.error('Error fetching customers:', error);
      alert('Error loading customers');
    }
  };

  const handleSaveCustomer = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      if (editingCustomer) {
        await axios.put(`${API}/customers/${editingCustomer.customer_id}`, customerForm);
      } else {
        await axios.post(`${API}/customers`, customerForm);
      }

      fetchCustomers();
      resetCustomerForm();
      alert(editingCustomer ? 'Customer updated!' : 'Customer created!');
    } catch (error) {
      console.error('Error saving customer:', error);
      alert('Error saving customer: ' + (error.response?.data?.error || error.message));
    } finally {
      setLoading(false);
    }
  };

  const handleEditCustomer = (customer) => {
    setCustomerForm({
      name: customer.name,
      phone: customer.phone,
      address: customer.address || '',
      gstin: customer.gstin || ''
    });
    setEditingCustomer(customer);
    setShowCustomerForm(true);
  };

  const handleDeleteCustomer = async (customerId) => {
    if (!window.confirm('Are you sure you want to delete this customer?')) return;
    try {
      await axios.delete(`${API}/customers/${customerId}`);
      fetchCustomers();
      alert('Customer deleted!');
    } catch (error) {
      console.error('Error deleting customer:', error);
      alert('Error deleting customer');
    }
  };

  const resetCustomerForm = () => {
    setCustomerForm({
      name: '',
      phone: '',
      address: '',
      gstin: ''
    });
    setEditingCustomer(null);
    setShowCustomerForm(false);
  };

  // ==================== INVOICES ====================
  const fetchInvoices = async () => {
    try {
      const response = await axios.get(`${API}/invoices`);
      setInvoices(response.data || []);
    } catch (error) {
      console.error('Error fetching invoices:', error);
      alert('Error loading invoices');
    }
  };

  const handleSaveInvoice = async (e) => {
    e.preventDefault();
    
    if (!invoiceForm.customer_id) {
      alert('Please select a customer');
      return;
    }
    if (invoiceForm.line_items.length === 0) {
      alert('Please add at least one line item');
      return;
    }

    setLoading(true);
    try {
      const invoiceData = {
        ...invoiceForm,
        gst_percent: parseFloat(invoiceForm.gst_percent) || 18,
        transport_charges: parseFloat(invoiceForm.transport_charges) || 0,
        unloading_charges: parseFloat(invoiceForm.unloading_charges) || 0,
        amount_paid: parseFloat(invoiceForm.amount_paid) || 0
      };

      await axios.post(`${API}/invoices`, invoiceData);

      fetchInvoices();
      fetchCustomers(); // Refresh to update pending balances
      resetInvoiceForm();
      alert('Invoice created successfully!');
    } catch (error) {
      console.error('Error saving invoice:', error);
      alert('Error saving invoice: ' + (error.response?.data?.error || error.message));
    } finally {
      setLoading(false);
    }
  };

  const handleAddLineItem = () => {
    if (!currentLineItem.tile_id) {
      alert('Please select a tile');
      return;
    }
    if (!currentLineItem.box_qty || currentLineItem.box_qty <= 0) {
      alert('Please enter box quantity');
      return;
    }

    // Add the line item
    setInvoiceForm(prev => ({
      ...prev,
      line_items: [...prev.line_items, { ...currentLineItem }]
    }));

    // Reset current line item
    setCurrentLineItem({
      tile_id: '',
      section_name: '',
      product_name: '',
      size: '',
      coverage: 0,
      rate_per_sqft: 0,
      rate_per_box: 0,
      box_qty: 0,
      extra_sqft: 0,
      discount_percent: 0
    });
  };

  const handleRemoveLineItem = (index) => {
    setInvoiceForm(prev => ({
      ...prev,
      line_items: prev.line_items.filter((_, i) => i !== index)
    }));
  };

  const handleTileSelect = (tileId) => {
    const tile = tiles.find(t => t.tile_id === tileId);
    if (tile) {
      setCurrentLineItem({
        ...currentLineItem,
        tile_id: tile.tile_id,
        product_name: tile.product_name || tile.size,
        size: tile.size,
        coverage: tile.coverage || tile.box_coverage_sqft || 0,
        rate_per_sqft: tile.rate_per_sqft || 0,
        rate_per_box: tile.rate_per_box || 0
      });
    }
  };

  const handleDeleteInvoice = async (invoiceId) => {
    if (!window.confirm('Are you sure you want to delete this invoice?')) return;
    try {
      const encodedId = encodeURIComponent(invoiceId);
      await axios.delete(`${API}/invoices/${encodedId}`);
      fetchInvoices();
      fetchCustomers(); // Refresh to update pending balances
      alert('Invoice deleted!');
    } catch (error) {
      console.error('Error deleting invoice:', error);
      alert('Error deleting invoice');
    }
  };

  const handleDownloadPDF = async (invoice) => {
    try {
      const encodedId = encodeURIComponent(invoice.invoice_id);
      const response = await axios.get(`${API}/invoices/${encodedId}/pdf`, {
        responseType: 'blob'
      });
      
      const blob = new Blob([response.data], { type: 'application/pdf' });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `Invoice_${invoice.invoice_id.replace(/\//g, '-')}.pdf`;
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Error downloading PDF:', error);
      alert('Error downloading PDF');
    }
  };

  const handleWhatsAppShare = async (invoice) => {
    try {
      const message = `📋 *Invoice ${invoice.invoice_id}*\n\n` +
        `👤 Customer: ${invoice.customer_name}\n` +
        `📞 Phone: ${invoice.customer_phone}\n` +
        `💰 Total: ₹${parseFloat(invoice.grand_total).toFixed(2)}\n` +
        `✅ Paid: ₹${parseFloat(invoice.amount_paid).toFixed(2)}\n` +
        `⏳ Pending: ₹${parseFloat(invoice.pending_balance).toFixed(2)}`;
      
      // Get PDF
      const encodedId = encodeURIComponent(invoice.invoice_id);
      const response = await axios.get(`${API}/invoices/${encodedId}/pdf`, {
        responseType: 'blob'
      });
      
      const pdfBlob = new Blob([response.data], { type: 'application/pdf' });
      const fileName = `Invoice_${invoice.invoice_id.replace(/\//g, '-')}.pdf`;
      const pdfFile = new File([pdfBlob], fileName, { type: 'application/pdf' });
      
      // Try Web Share API (mobile)
      if (navigator.canShare && navigator.canShare({ files: [pdfFile] })) {
        await navigator.share({
          files: [pdfFile],
          title: `Invoice ${invoice.invoice_id}`,
          text: message
        });
      } else {
        // Fallback: Download PDF and open WhatsApp
        const url = window.URL.createObjectURL(pdfBlob);
        const link = document.createElement('a');
        link.href = url;
        link.download = fileName;
        document.body.appendChild(link);
        link.click();
        link.remove();
        window.URL.revokeObjectURL(url);
        
        // Open WhatsApp
        const pdfUrl = `${BACKEND_URL}/api/invoices/${encodedId}/pdf`;
        const fullMessage = message + `\n\n📥 Download PDF:\n${pdfUrl}`;
        const encodedMessage = encodeURIComponent(fullMessage);
        window.open(`https://wa.me/?text=${encodedMessage}`, '_blank');
      }
    } catch (error) {
      console.error('WhatsApp share error:', error);
      alert('Error sharing on WhatsApp');
    }
  };

  const resetInvoiceForm = () => {
    setInvoiceForm({
      customer_id: '',
      line_items: [],
      gst_percent: 18,
      transport_charges: 0,
      unloading_charges: 0,
      amount_paid: 0,
      status: 'Draft',
      date: new Date().toISOString().split('T')[0]
    });
    setCurrentLineItem({
      tile_id: '',
      section_name: '',
      product_name: '',
      size: '',
      coverage: 0,
      rate_per_sqft: 0,
      rate_per_box: 0,
      box_qty: 0,
      extra_sqft: 0,
      discount_percent: 0
    });
    setShowInvoiceForm(false);
  };

  // Show login if not authenticated
  if (!isAuthenticated) {
    return <Login onLogin={handleLogin} />;
  }

  // ==================== RENDER ====================
  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex justify-between items-center">
            <h1 className="text-2xl font-bold text-gray-900">The Tile Shop</h1>
            <button
              onClick={handleLogout}
              className="flex items-center gap-2 px-4 py-2 text-gray-700 hover:bg-gray-100 rounded-lg transition"
            >
              <LogOut className="h-5 w-5" />
              Logout
            </button>
          </div>
        </div>
      </header>

      {/* Navigation Tabs */}
      <div className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <nav className="flex space-x-8">
            <button
              onClick={() => setActiveTab('dashboard')}
              className={`py-4 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'dashboard'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              Dashboard
            </button>
            <button
              onClick={() => setActiveTab('tiles')}
              className={`flex items-center gap-2 py-4 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'tiles'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              <Package className="h-4 w-4" />
              Tiles
            </button>
            <button
              onClick={() => setActiveTab('customers')}
              className={`flex items-center gap-2 py-4 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'customers'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              <Users className="h-4 w-4" />
              Customers
            </button>
            <button
              onClick={() => setActiveTab('invoices')}
              className={`flex items-center gap-2 py-4 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'invoices'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              <FileText className="h-4 w-4" />
              Invoices
            </button>
          </nav>
        </div>
      </div>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Dashboard */}
        {activeTab === 'dashboard' && (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="bg-white rounded-lg shadow p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600">Total Tiles</p>
                  <p className="text-3xl font-bold text-gray-900">{tiles.length}</p>
                </div>
                <Package className="h-12 w-12 text-blue-500" />
              </div>
            </div>
            <div className="bg-white rounded-lg shadow p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600">Total Customers</p>
                  <p className="text-3xl font-bold text-gray-900">{customers.length}</p>
                </div>
                <Users className="h-12 w-12 text-green-500" />
              </div>
            </div>
            <div className="bg-white rounded-lg shadow p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600">Total Invoices</p>
                  <p className="text-3xl font-bold text-gray-900">{invoices.length}</p>
                </div>
                <FileText className="h-12 w-12 text-purple-500" />
              </div>
            </div>
          </div>
        )}

        {/* TILES TAB - Continued in next part */}

        {/* TILES TAB */}
        {activeTab === 'tiles' && (
          <div>
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-2xl font-bold text-gray-900">Tiles Management</h2>
              <button
                onClick={() => setShowTileForm(!showTileForm)}
                className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
              >
                <Plus className="h-5 w-5" />
                Add Tile
              </button>
            </div>

            {/* Tile Form */}
            {showTileForm && (
              <div className="bg-white rounded-lg shadow p-6 mb-6">
                <h3 className="text-lg font-semibold mb-4">
                  {editingTile ? 'Edit Tile' : 'Add New Tile'}
                </h3>
                <form onSubmit={handleSaveTile} className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Size *
                    </label>
                    <input
                      type="text"
                      value={tileForm.size}
                      onChange={(e) => setTileForm({ ...tileForm, size: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                      placeholder="e.g., 600x600mm"
                      required
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Product Name
                    </label>
                    <input
                      type="text"
                      value={tileForm.product_name}
                      onChange={(e) => setTileForm({ ...tileForm, product_name: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                      placeholder="Product name"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Coverage (sqft)
                    </label>
                    <input
                      type="number"
                      step="0.01"
                      value={tileForm.coverage}
                      onChange={(e) => setTileForm({ ...tileForm, coverage: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                      placeholder="0.00"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Box Packing
                    </label>
                    <input
                      type="number"
                      value={tileForm.box_packing}
                      onChange={(e) => setTileForm({ ...tileForm, box_packing: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                      placeholder="0"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Rate per Sqft
                    </label>
                    <input
                      type="number"
                      step="0.01"
                      value={tileForm.rate_per_sqft}
                      onChange={(e) => setTileForm({ ...tileForm, rate_per_sqft: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                      placeholder="0.00"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Rate per Box
                    </label>
                    <input
                      type="number"
                      step="0.01"
                      value={tileForm.rate_per_box}
                      onChange={(e) => setTileForm({ ...tileForm, rate_per_box: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                      placeholder="0.00"
                    />
                  </div>
                  <div className="md:col-span-2 flex gap-3">
                    <button
                      type="submit"
                      disabled={loading}
                      className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
                    >
                      <Save className="h-4 w-4" />
                      {loading ? 'Saving...' : 'Save Tile'}
                    </button>
                    <button
                      type="button"
                      onClick={resetTileForm}
                      className="flex items-center gap-2 px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300"
                    >
                      <X className="h-4 w-4" />
                      Cancel
                    </button>
                  </div>
                </form>
              </div>
            )}

            {/* Tiles List */}
            <div className="bg-white rounded-lg shadow overflow-hidden">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Size</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Product</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Coverage</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Rate/Sqft</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Rate/Box</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Actions</th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {tiles.map((tile) => (
                    <tr key={tile.tile_id}>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{tile.size}</td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{tile.product_name || '-'}</td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{tile.coverage} sqft</td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">₹{parseFloat(tile.rate_per_sqft || 0).toFixed(2)}</td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">₹{parseFloat(tile.rate_per_box || 0).toFixed(2)}</td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                        <button
                          onClick={() => handleEditTile(tile)}
                          className="text-blue-600 hover:text-blue-900 mr-3"
                        >
                          <Edit2 className="h-4 w-4" />
                        </button>
                        <button
                          onClick={() => handleDeleteTile(tile.tile_id)}
                          className="text-red-600 hover:text-red-900"
                        >
                          <Trash2 className="h-4 w-4" />
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
              {tiles.length === 0 && (
                <div className="text-center py-12 text-gray-500">
                  No tiles found. Add your first tile!
                </div>
              )}
            </div>
          </div>
        )}

        {/* CUSTOMERS TAB */}
        {activeTab === 'customers' && (
          <div>
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-2xl font-bold text-gray-900">Customers Management</h2>
              <button
                onClick={() => setShowCustomerForm(!showCustomerForm)}
                className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
              >
                <Plus className="h-5 w-5" />
                Add Customer
              </button>
            </div>

            {/* Customer Form */}
            {showCustomerForm && (
              <div className="bg-white rounded-lg shadow p-6 mb-6">
                <h3 className="text-lg font-semibold mb-4">
                  {editingCustomer ? 'Edit Customer' : 'Add New Customer'}
                </h3>
                <form onSubmit={handleSaveCustomer} className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Name *
                    </label>
                    <input
                      type="text"
                      value={customerForm.name}
                      onChange={(e) => setCustomerForm({ ...customerForm, name: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                      required
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Phone *
                    </label>
                    <input
                      type="text"
                      value={customerForm.phone}
                      onChange={(e) => setCustomerForm({ ...customerForm, phone: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                      required
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Address
                    </label>
                    <textarea
                      value={customerForm.address}
                      onChange={(e) => setCustomerForm({ ...customerForm, address: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                      rows="2"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      GSTIN
                    </label>
                    <input
                      type="text"
                      value={customerForm.gstin}
                      onChange={(e) => setCustomerForm({ ...customerForm, gstin: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                  <div className="md:col-span-2 flex gap-3">
                    <button
                      type="submit"
                      disabled={loading}
                      className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
                    >
                      <Save className="h-4 w-4" />
                      {loading ? 'Saving...' : 'Save Customer'}
                    </button>
                    <button
                      type="button"
                      onClick={resetCustomerForm}
                      className="flex items-center gap-2 px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300"
                    >
                      <X className="h-4 w-4" />
                      Cancel
                    </button>
                  </div>
                </form>
              </div>
            )}

            {/* Customers List */}
            <div className="bg-white rounded-lg shadow overflow-hidden">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Name</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Phone</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Address</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">GSTIN</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Pending</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Actions</th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {customers.map((customer) => (
                    <tr key={customer.customer_id}>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{customer.name}</td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{customer.phone}</td>
                      <td className="px-6 py-4 text-sm text-gray-500">{customer.address || '-'}</td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{customer.gstin || '-'}</td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">₹{parseFloat(customer.total_pending || 0).toFixed(2)}</td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                        <button
                          onClick={() => handleEditCustomer(customer)}
                          className="text-blue-600 hover:text-blue-900 mr-3"
                        >
                          <Edit2 className="h-4 w-4" />
                        </button>
                        <button
                          onClick={() => handleDeleteCustomer(customer.customer_id)}
                          className="text-red-600 hover:text-red-900"
                        >
                          <Trash2 className="h-4 w-4" />
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
              {customers.length === 0 && (
                <div className="text-center py-12 text-gray-500">
                  No customers found. Add your first customer!
                </div>
              )}
            </div>
          </div>
        )}

        {/* INVOICES TAB - Part 1 */}
        {activeTab === 'invoices' && (
          <div>
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-2xl font-bold text-gray-900">Invoices Management</h2>
              <button
                onClick={() => setShowInvoiceForm(!showInvoiceForm)}
                className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
              >
                <Plus className="h-5 w-5" />
                Create Invoice
              </button>
            </div>

            {/* Invoice Form */}
            {showInvoiceForm && (
              <div className="bg-white rounded-lg shadow p-6 mb-6">
                <h3 className="text-lg font-semibold mb-4">Create New Invoice</h3>
                <form onSubmit={handleSaveInvoice} className="space-y-6">
                  {/* Customer Selection */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Select Customer *
                    </label>
                    <select
                      value={invoiceForm.customer_id}
                      onChange={(e) => setInvoiceForm({ ...invoiceForm, customer_id: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                      required
                    >
                      <option value="">-- Select Customer --</option>
                      {customers.map((customer) => (
                        <option key={customer.customer_id} value={customer.customer_id}>
                          {customer.name} - {customer.phone}
                        </option>
                      ))}
                    </select>
                  </div>

                  {/* Date */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Date
                      </label>
                      <input
                        type="date"
                        value={invoiceForm.date}
                        onChange={(e) => setInvoiceForm({ ...invoiceForm, date: e.target.value })}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Status
                      </label>
                      <select
                        value={invoiceForm.status}
                        onChange={(e) => setInvoiceForm({ ...invoiceForm, status: e.target.value })}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                      >
                        <option value="Draft">Draft</option>
                        <option value="Sent">Sent</option>
                        <option value="Paid">Paid</option>
                      </select>
                    </div>
                  </div>

                  {/* Add Line Item */}
                  <div className="border-t pt-4">
                    <h4 className="font-semibold mb-3">Add Items</h4>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          Select Tile *
                        </label>
                        <select
                          value={currentLineItem.tile_id}
                          onChange={(e) => handleTileSelect(e.target.value)}
                          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                        >
                          <option value="">-- Select Tile --</option>
                          {tiles.map((tile) => (
                            <option key={tile.tile_id} value={tile.tile_id}>
                              {tile.size} - {tile.product_name || 'No Name'}
                            </option>
                          ))}
                        </select>
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          Section Name
                        </label>
                        <input
                          type="text"
                          value={currentLineItem.section_name}
                          onChange={(e) => setCurrentLineItem({ ...currentLineItem, section_name: e.target.value })}
                          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                          placeholder="e.g., Living Room"
                        />
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          Box Quantity *
                        </label>
                        <input
                          type="number"
                          value={currentLineItem.box_qty}
                          onChange={(e) => setCurrentLineItem({ ...currentLineItem, box_qty: parseInt(e.target.value) || 0 })}
                          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                        />
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          Extra Sqft
                        </label>
                        <input
                          type="number"
                          step="0.01"
                          value={currentLineItem.extra_sqft}
                          onChange={(e) => setCurrentLineItem({ ...currentLineItem, extra_sqft: parseFloat(e.target.value) || 0 })}
                          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                        />
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          Discount %
                        </label>
                        <input
                          type="number"
                          step="0.1"
                          value={currentLineItem.discount_percent}
                          onChange={(e) => setCurrentLineItem({ ...currentLineItem, discount_percent: parseFloat(e.target.value) || 0 })}
                          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                        />
                      </div>
                      <div className="flex items-end">
                        <button
                          type="button"
                          onClick={handleAddLineItem}
                          className="w-full px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700"
                        >
                          Add Item
                        </button>
                      </div>
                    </div>
                  </div>

                  {/* Line Items List */}
                  {invoiceForm.line_items.length > 0 && (
                    <div className="border-t pt-4">
                      <h4 className="font-semibold mb-3">Added Items</h4>
                      <div className="space-y-2">
                        {invoiceForm.line_items.map((item, index) => (
                          <div key={index} className="flex items-center justify-between bg-gray-50 p-3 rounded-lg">
                            <div className="flex-1">
                              <p className="font-medium">{item.product_name} ({item.size})</p>
                              <p className="text-sm text-gray-600">
                                Qty: {item.box_qty} boxes | Rate: ₹{item.rate_per_sqft}/sqft | Discount: {item.discount_percent}%
                              </p>
                            </div>
                            <button
                              type="button"
                              onClick={() => handleRemoveLineItem(index)}
                              className="text-red-600 hover:text-red-900"
                            >
                              <Trash2 className="h-4 w-4" />
                            </button>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Charges */}
                  <div className="border-t pt-4">
                    <h4 className="font-semibold mb-3">Additional Charges</h4>
                    <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          GST %
                        </label>
                        <input
                          type="number"
                          step="0.1"
                          value={invoiceForm.gst_percent}
                          onChange={(e) => setInvoiceForm({ ...invoiceForm, gst_percent: e.target.value })}
                          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                        />
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          Transport Charges
                        </label>
                        <input
                          type="number"
                          step="0.01"
                          value={invoiceForm.transport_charges}
                          onChange={(e) => setInvoiceForm({ ...invoiceForm, transport_charges: e.target.value })}
                          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                        />
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          Unloading Charges
                        </label>
                        <input
                          type="number"
                          step="0.01"
                          value={invoiceForm.unloading_charges}
                          onChange={(e) => setInvoiceForm({ ...invoiceForm, unloading_charges: e.target.value })}
                          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                        />
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          Amount Paid
                        </label>
                        <input
                          type="number"
                          step="0.01"
                          value={invoiceForm.amount_paid}
                          onChange={(e) => setInvoiceForm({ ...invoiceForm, amount_paid: e.target.value })}
                          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                        />
                      </div>
                    </div>
                  </div>

                  {/* Submit Buttons */}
                  <div className="flex gap-3 border-t pt-4">
                    <button
                      type="submit"
                      disabled={loading}
                      className="flex items-center gap-2 px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
                    >
                      <Save className="h-5 w-5" />
                      {loading ? 'Creating...' : 'Create Invoice'}
                    </button>
                    <button
                      type="button"
                      onClick={resetInvoiceForm}
                      className="flex items-center gap-2 px-6 py-3 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300"
                    >
                      <X className="h-5 w-5" />
                      Cancel
                    </button>
                  </div>
                </form>
              </div>
            )}

            {/* Invoices List */}
            <div className="bg-white rounded-lg shadow overflow-hidden">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Invoice ID</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Customer</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Date</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Total</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Pending</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Actions</th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {invoices.map((invoice) => (
                    <tr key={invoice.invoice_id}>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{invoice.invoice_id}</td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{invoice.customer_name}</td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {new Date(invoice.date).toLocaleDateString()}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        ₹{parseFloat(invoice.grand_total).toFixed(2)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        ₹{parseFloat(invoice.pending_balance).toFixed(2)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`px-2 py-1 text-xs rounded-full ${
                          invoice.status === 'Paid' ? 'bg-green-100 text-green-800' :
                          invoice.status === 'Sent' ? 'bg-blue-100 text-blue-800' :
                          'bg-gray-100 text-gray-800'
                        }`}>
                          {invoice.status}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                        <button
                          onClick={() => handleDownloadPDF(invoice)}
                          className="text-green-600 hover:text-green-900 mr-3"
                          title="Download PDF"
                        >
                          <Download className="h-4 w-4" />
                        </button>
                        <button
                          onClick={() => handleWhatsAppShare(invoice)}
                          className="text-blue-600 hover:text-blue-900 mr-3"
                          title="Share on WhatsApp"
                        >
                          <Share2 className="h-4 w-4" />
                        </button>
                        <button
                          onClick={() => handleDeleteInvoice(invoice.invoice_id)}
                          className="text-red-600 hover:text-red-900"
                          title="Delete"
                        >
                          <Trash2 className="h-4 w-4" />
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
              {invoices.length === 0 && (
                <div className="text-center py-12 text-gray-500">
                  No invoices found. Create your first invoice!
                </div>
              )}
            </div>
          </div>
        )}
      </main>
    </div>
  );
}

export default App;
