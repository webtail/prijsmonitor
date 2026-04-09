import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App'
import { Toaster } from 'react-hot-toast'
import './index.css'

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
    <Toaster position="bottom-right" toastOptions={{
      style: { background: '#1a1a2e', color: '#e2e8f0', border: '1px solid #2d3748' }
    }} />
  </React.StrictMode>
)
