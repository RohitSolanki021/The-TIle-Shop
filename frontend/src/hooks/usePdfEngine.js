/**
 * Hook for using the PRO Invoice PDF Engine
 */

import { useState, useCallback } from 'react';
import { generateInvoicePDF, convertInvoiceToSections } from '../pdf/pdfEngine';

/**
 * Custom hook for PDF generation
 * @param {string} templateUrl - URL to the template PDF
 */
export function usePdfEngine(templateUrl) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [templateBytes, setTemplateBytes] = useState(null);
  
  // Load template on first use
  const loadTemplate = useCallback(async () => {
    if (templateBytes) return templateBytes;
    
    try {
      const response = await fetch(templateUrl);
      if (!response.ok) {
        throw new Error('Failed to load PDF template');
      }
      const bytes = new Uint8Array(await response.arrayBuffer());
      setTemplateBytes(bytes);
      return bytes;
    } catch (err) {
      setError(err.message);
      throw err;
    }
  }, [templateUrl, templateBytes]);
  
  /**
   * Generate PDF from invoice data
   * @param {Object} invoice - Invoice from backend API
   * @returns {Promise<Uint8Array>} - PDF bytes
   */
  const generatePdf = useCallback(async (invoice) => {
    setLoading(true);
    setError(null);
    
    try {
      const template = await loadTemplate();
      const data = convertInvoiceToSections(invoice);
      const pdfBytes = await generateInvoicePDF(data, template);
      
      setLoading(false);
      return pdfBytes;
    } catch (err) {
      setLoading(false);
      setError(err.message);
      throw err;
    }
  }, [loadTemplate]);
  
  /**
   * Generate and download PDF
   * @param {Object} invoice - Invoice from backend API
   */
  const downloadPdf = useCallback(async (invoice) => {
    try {
      const pdfBytes = await generatePdf(invoice);
      
      // Create blob and download
      const blob = new Blob([pdfBytes], { type: 'application/pdf' });
      const url = URL.createObjectURL(blob);
      
      const link = document.createElement('a');
      link.href = url;
      link.download = `Invoice_${invoice.invoice_id.replace(/\//g, '-')}.pdf`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      
      URL.revokeObjectURL(url);
    } catch (err) {
      console.error('Failed to download PDF:', err);
    }
  }, [generatePdf]);
  
  /**
   * Generate PDF and open in new tab for preview
   * @param {Object} invoice - Invoice from backend API
   */
  const previewPdf = useCallback(async (invoice) => {
    try {
      const pdfBytes = await generatePdf(invoice);
      
      // Create blob and open
      const blob = new Blob([pdfBytes], { type: 'application/pdf' });
      const url = URL.createObjectURL(blob);
      
      window.open(url, '_blank');
    } catch (err) {
      console.error('Failed to preview PDF:', err);
    }
  }, [generatePdf]);
  
  return {
    loading,
    error,
    generatePdf,
    downloadPdf,
    previewPdf
  };
}

export default usePdfEngine;
