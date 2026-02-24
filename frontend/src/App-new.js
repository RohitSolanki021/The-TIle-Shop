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
