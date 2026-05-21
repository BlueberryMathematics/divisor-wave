const { app, BrowserWindow, ipcMain, shell } = require('electron')
const path = require('path')
const { spawn } = require('child_process')

const DEV = !app.isPackaged
const START_URL = DEV ? 'http://localhost:3000' : `file://${path.join(__dirname, '../out/index.html')}`

// Paths relative to this file (electron/main.js)
const ROOT = path.resolve(__dirname, '..', '..')
const PYTHON_CLI = path.join(ROOT, 'python-divisor-wave', 'plot_cli.py')
const OUTPUT_DIR = path.join(ROOT, 'plot-outputs')

function createWindow() {
  const win = new BrowserWindow({
    width: 1400,
    height: 900,
    minWidth: 900,
    minHeight: 600,
    backgroundColor: '#06060e',
    frame: false,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false,
    },
  })
  win.loadURL(START_URL)
  if (DEV) win.webContents.openDevTools({ mode: 'detach' })
}

app.whenReady().then(createWindow)
app.on('window-all-closed', () => { if (process.platform !== 'darwin') app.quit() })
app.on('activate', () => { if (BrowserWindow.getAllWindows().length === 0) createWindow() })

// ── IPC: window controls ───────────────────────────────────────────────────
ipcMain.handle('window-minimize', () => BrowserWindow.getFocusedWindow()?.minimize())
ipcMain.handle('window-maximize', () => {
  const win = BrowserWindow.getFocusedWindow()
  win?.isMaximized() ? win.unmaximize() : win.maximize()
})
ipcMain.handle('window-close', () => BrowserWindow.getFocusedWindow()?.close())
ipcMain.handle('window-is-maximized', () => BrowserWindow.getFocusedWindow()?.isMaximized() ?? false)

// ── IPC: generate plot ─────────────────────────────────────────────────────
ipcMain.handle('generate-plot', async (_event, params) => {
  return new Promise((resolve) => {
    const fs = require('fs')
    const venvPy = path.join(ROOT, 'venv', 'Scripts', 'python.exe')   // Windows venv
    const venvPyUnix = path.join(ROOT, 'venv', 'bin', 'python')       // Mac/Linux venv
    const pythonCmd = fs.existsSync(venvPy) ? venvPy
                    : fs.existsSync(venvPyUnix) ? venvPyUnix
                    : 'python'

    const args = [
      PYTHON_CLI,
      '--function',   String(params.functionId),
      '--normalize',  params.normalize,
      '--colormap',   String(params.colormap),
      '--resolution', String(params.resolution),
      '--xmin',       String(params.xmin),
      '--xmax',       String(params.xmax),
      '--ymin',       String(params.ymin),
      '--ymax',       String(params.ymax),
      '--elev',       String(params.elev),
      '--azim',       String(params.azim),
      '--output',     OUTPUT_DIR,
      // Optional coefficient overrides — only pass when explicitly set
      ...(params.m    != null ? ['--m',    String(params.m)]    : []),
      ...(params.beta != null ? ['--beta', String(params.beta)] : []),
    ]

    let stdout = ''
    let stderr = ''

    const proc = spawn(pythonCmd, args)
    proc.stdout.on('data', d => { stdout += d.toString() })
    proc.stderr.on('data', d => { stderr += d.toString() })

    proc.on('close', (code) => {
      try {
        const lastLine = stdout.trim().split('\n').pop()
        const result = JSON.parse(lastLine)
        if (result.success && result.path) {
          const data = fs.readFileSync(result.path)
          result.dataUrl = 'data:image/png;base64,' + data.toString('base64')
        }
        resolve(result)
      } catch {
        resolve({ success: false, error: stderr || `Process exited with code ${code}` })
      }
    })

    proc.on('error', (err) => {
      resolve({ success: false, error: err.message })
    })
  })
})

// ── IPC: auto-compute coefficients ────────────────────────────────────────
ipcMain.handle('auto-coeffs', async (_event, params) => {
  return new Promise((resolve) => {
    const fs = require('fs')
    const venvPy    = path.join(ROOT, 'venv', 'Scripts', 'python.exe')
    const venvPyUnix = path.join(ROOT, 'venv', 'bin', 'python')
    const pythonCmd = fs.existsSync(venvPy) ? venvPy
                    : fs.existsSync(venvPyUnix) ? venvPyUnix
                    : 'python'

    const args = [
      PYTHON_CLI,
      '--function',  String(params.functionId),
      '--normalize', params.normalize,
      '--xmin',      String(params.xmin),
      '--xmax',      String(params.xmax),
      '--ymin',      String(params.ymin),
      '--ymax',      String(params.ymax),
      '--auto-coeffs',
    ]

    let stdout = '', stderr = ''
    const proc = spawn(pythonCmd, args)
    proc.stdout.on('data', d => { stdout += d.toString() })
    proc.stderr.on('data', d => { stderr += d.toString() })
    proc.on('close', () => {
      try {
        const result = JSON.parse(stdout.trim().split('\n').pop())
        resolve(result)
      } catch {
        resolve({ success: false, error: stderr || 'Failed to parse response' })
      }
    })
    proc.on('error', err => resolve({ success: false, error: err.message }))
  })
})

// ── IPC: load a plot as base64 (for history selection) ────────────────────
ipcMain.handle('get-plot-data', async (_event, filePath) => {
  const fs = require('fs')
  try {
    const data = fs.readFileSync(filePath)
    return { success: true, dataUrl: 'data:image/png;base64,' + data.toString('base64') }
  } catch (e) {
    return { success: false, error: e.message }
  }
})

// ── IPC: open output folder ────────────────────────────────────────────────
ipcMain.handle('open-output-folder', async () => {
  await shell.openPath(OUTPUT_DIR)
})

// ── IPC: list saved plots ──────────────────────────────────────────────────
ipcMain.handle('list-plots', async () => {
  const fs = require('fs')
  try {
    const files = fs.readdirSync(OUTPUT_DIR)
      .filter(f => f.endsWith('.png'))
      .sort()
      .reverse()
      .slice(0, 20)
      .map(f => ({ name: f, path: path.join(OUTPUT_DIR, f) }))
    return { success: true, files }
  } catch {
    return { success: true, files: [] }
  }
})
