# The Tile Shop - Invoice Management System

A full-stack invoice generation application for The Tile Shop, featuring tile inventory management, customer management, and PDF invoice generation with WhatsApp sharing.

## 🚀 Features

- **Tile Management**: Add, edit, and delete tile inventory with custom sizes
- **Customer Management**: Maintain customer database with contact details and GSTIN
- **Invoice Generation**: Create detailed invoices with multiple line items and sections
- **PDF Generation**: Professional PDF invoices with company branding
- **WhatsApp Integration**: Share invoices directly via WhatsApp
- **Authentication**: Secure login system (Username: Thetileshop, Password: Vicky123)

## 🏗️ Tech Stack

- **Frontend**: React 19, Tailwind CSS, Radix UI
- **Backend**: FastAPI (Python)
- **Database**: MongoDB
- **PDF Generation**: WeasyPrint (HTML to PDF)

## 📁 Project Structure

```
/app
├── frontend/          # React application
│   ├── src/
│   ├── public/
│   └── package.json
├── backend/           # FastAPI server
│   ├── server.py
│   ├── assets/        # PDF templates and logos
│   ├── fonts/
│   └── requirements.txt
└── vercel.json        # Vercel deployment config
```

## 🔧 Local Development

### Prerequisites
- Node.js 18+ and Yarn
- Python 3.11+
- MongoDB

### Backend Setup
```bash
cd backend
pip install -r requirements.txt

# Create .env file
echo "MONGO_URL=mongodb://localhost:27017" > .env
echo "DB_NAME=tileshop" >> .env
echo "PORT=8001" >> .env

# Start server
uvicorn server:app --reload --port 8001
```

### Frontend Setup
```bash
cd frontend
yarn install

# Create .env file
echo "REACT_APP_BACKEND_URL=http://localhost:8001" > .env

# Start development server
yarn start
```

Visit `http://localhost:3000` to access the application.

## 🚀 Deployment

See [DEPLOYMENT.md](./DEPLOYMENT.md) for detailed deployment instructions.

### Quick Deploy to Vercel (Frontend)

1. Fork/clone this repository
2. Deploy backend to Railway/Render (see DEPLOYMENT.md)
3. Import to Vercel
4. Set environment variable: `REACT_APP_BACKEND_URL=https://your-backend-url`
5. Deploy!

## 📝 Login Credentials

- **Username**: Thetileshop
- **Password**: Vicky123

## 🔐 Environment Variables

### Backend
- `MONGO_URL`: MongoDB connection string
- `DB_NAME`: Database name (default: tileshop)
- `PORT`: Server port (default: 8001)

### Frontend
- `REACT_APP_BACKEND_URL`: Backend API URL

## 📄 License

Private - The Tile Shop

## 🤝 Support

For issues and questions, please open an issue in the repository.
