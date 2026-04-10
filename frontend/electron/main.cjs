/**
 * Electron main process.
 * Manages the BrowserWindow and auto-starts the FastAPI backend as a child process.
 */

const { app, BrowserWindow, dialog } = require('electron');
const path = require('path');
const { spawn } = require('child_process');

let mainWindow = null;
let backendProcess = null;

const isDev = !app.isPackaged;
const BACKEND_PORT = 8000;
const FRONTEND_PORT = 5173;

/**
 * Start the FastAPI backend as a child process.
 */
function startBackend() {
  const backendDir = isDev
    ? path.join(__dirname, '..', '..', 'backend')
    : path.join(process.resourcesPath, 'backend');

  console.log('[Electron] Starting backend from:', backendDir);

  backendProcess = spawn('python', [
    '-m', 'uvicorn', 'app.main:app',
    '--host', '127.0.0.1',
    '--port', String(BACKEND_PORT),
  ], {
    cwd: backendDir,
    stdio: ['inherit', 'pipe', 'pipe'],
    env: { ...process.env, PYTHONIOENCODING: 'utf-8' },
  });

  backendProcess.stdout?.on('data', (data) => {
    console.log(`[Backend] ${data.toString().trim()}`);
  });

  backendProcess.stderr?.on('data', (data) => {
    console.error(`[Backend ERR] ${data.toString().trim()}`);
  });

  backendProcess.on('error', (err) => {
    console.error('[Electron] Failed to start backend:', err.message);
    dialog.showErrorBox(
      'Backend Error',
      `Cannot start FastAPI backend.\n\nMake sure Python is installed and accessible.\n\nError: ${err.message}`
    );
  });

  backendProcess.on('exit', (code) => {
    console.log(`[Electron] Backend exited with code: ${code}`);
  });
}

/**
 * Wait for the backend to be ready (health check).
 */
async function waitForBackend(maxRetries = 30) {
  for (let i = 0; i < maxRetries; i++) {
    try {
      const response = await fetch(`http://127.0.0.1:${BACKEND_PORT}/api/health`);
      if (response.ok) {
        console.log('[Electron] Backend is ready!');
        return true;
      }
    } catch {
      // Not ready yet
    }
    await new Promise(r => setTimeout(r, 1000));
  }
  console.error('[Electron] Backend failed to start within timeout');
  return false;
}

/**
 * Create the main application window.
 */
function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1400,
    height: 900,
    minWidth: 1000,
    minHeight: 700,
    title: 'AutoScheduling SME',
    icon: path.join(__dirname, 'icon.ico'),
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
    },
    backgroundColor: '#0a0e1a',
    show: false,
  });

  // Load the app
  const url = isDev
    ? `http://localhost:${FRONTEND_PORT}`
    : `file://${path.join(__dirname, '..', 'dist', 'index.html')}`;

  console.log('[Electron] Loading:', url);
  mainWindow.loadURL(url);

  // Show window when ready
  mainWindow.once('ready-to-show', () => {
    mainWindow.show();
  });

  // Open DevTools in development
  if (isDev) {
    mainWindow.webContents.openDevTools({ mode: 'detach' });
  }

  mainWindow.on('closed', () => {
    mainWindow = null;
  });
}

// ── App lifecycle ────────────────────────────────────────────────

app.whenReady().then(async () => {
  startBackend();

  // Wait for backend to be ready before showing the window
  const ready = await waitForBackend();

  if (!ready) {
    dialog.showErrorBox(
      'Startup Error',
      'FastAPI backend did not start in time.\nPlease check that Python and dependencies are installed.'
    );
  }

  createWindow();

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) createWindow();
  });
});

app.on('window-all-closed', () => {
  // Kill backend process
  if (backendProcess) {
    console.log('[Electron] Shutting down backend...');
    backendProcess.kill('SIGTERM');
    backendProcess = null;
  }

  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('before-quit', () => {
  if (backendProcess) {
    backendProcess.kill('SIGTERM');
    backendProcess = null;
  }
});
