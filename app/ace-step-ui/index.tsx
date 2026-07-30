import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import LoginGate from './LoginGate';
import { AuthProvider } from './context/AuthContext';
import { ResponsiveProvider } from './context/ResponsiveContext';
import { hydrateFromServer, startAutoSync } from './services/persistence';

const rootElement = document.getElementById('root');
if (!rootElement) {
  throw new Error("Could not find root element to mount to");
}

const root = ReactDOM.createRoot(rootElement);

// Hydrate UI state from the server-side file BEFORE rendering, so that all
// useState initializers read the persisted lyrics / settings. Then start the
// real-time mirror that keeps the on-disk copy in sync.
async function bootstrap() {
  await hydrateFromServer();
  root.render(
    <React.StrictMode>
      <AuthProvider>
        <ResponsiveProvider>
          <LoginGate>
            <App />
          </LoginGate>
        </ResponsiveProvider>
      </AuthProvider>
    </React.StrictMode>
  );
  startAutoSync();
}

bootstrap();