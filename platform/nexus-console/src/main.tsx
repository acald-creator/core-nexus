import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './design-system/index.css'
import { applyAppearance, loadAppearance } from './design-system/appearance'
import App from './App.tsx'

// Apply the saved theme/layout before first paint so there is no flash.
applyAppearance(loadAppearance())

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
