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
  window: {
    minimize:    () => ipcRenderer.invoke('window-minimize'),
    maximize:    () => ipcRenderer.invoke('window-maximize'),
    close:       () => ipcRenderer.invoke('window-close'),
    isMaximized: () => ipcRenderer.invoke('window-is-maximized'),
  },
})
