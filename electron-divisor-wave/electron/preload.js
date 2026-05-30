const { contextBridge, ipcRenderer } = require('electron')

contextBridge.exposeInMainWorld('electronAPI', {
  generatePlot:         (params)  => ipcRenderer.invoke('generate-plot', params),
  autoCoeffs:           (params)  => ipcRenderer.invoke('auto-coeffs', params),
  getPlotData:          (fp)      => ipcRenderer.invoke('get-plot-data', fp),
  openOutputFolder:     ()        => ipcRenderer.invoke('open-output-folder'),
  listPlots:            ()        => ipcRenderer.invoke('list-plots'),
  // Formula bridge
  getAllFormulas:        ()        => ipcRenderer.invoke('get-all-formulas'),
  validateUserFunction: (latex)   => ipcRenderer.invoke('validate-user-function', latex),
  // User-defined functions
  listUserFunctions:    ()        => ipcRenderer.invoke('list-user-functions'),
  saveUserFunction:     (fn)      => ipcRenderer.invoke('save-user-function', fn),
  deleteUserFunction:   (id)      => ipcRenderer.invoke('delete-user-function', id),
  // GPU plotter (C# OpenGL window embedded in Electron)
  gpuPlotter: {
    launch:  (params)  => ipcRenderer.invoke('gpu-plotter-launch', params),
    send:    (payload) => ipcRenderer.invoke('gpu-plotter-send', payload),
    kill:    ()        => ipcRenderer.invoke('gpu-plotter-kill'),
    resize:  (params)  => ipcRenderer.invoke('gpu-plotter-resize', params),
    onMessage: (cb)    => ipcRenderer.on('gpu-plotter-message', (_e, msg) => cb(msg)),
    offMessage: (cb)   => ipcRenderer.off('gpu-plotter-message', cb),
  },
  window: {
    minimize:    () => ipcRenderer.invoke('window-minimize'),
    maximize:    () => ipcRenderer.invoke('window-maximize'),
    close:       () => ipcRenderer.invoke('window-close'),
    isMaximized: () => ipcRenderer.invoke('window-is-maximized'),
  },
})
