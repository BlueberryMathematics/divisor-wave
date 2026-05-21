const { contextBridge, ipcRenderer } = require('electron')

contextBridge.exposeInMainWorld('electronAPI', {
  generatePlot:     (params)   => ipcRenderer.invoke('generate-plot', params),
  autoCoeffs:       (params)   => ipcRenderer.invoke('auto-coeffs', params),
  getPlotData:      (filePath) => ipcRenderer.invoke('get-plot-data', filePath),
  openOutputFolder: ()         => ipcRenderer.invoke('open-output-folder'),
  listPlots:        ()         => ipcRenderer.invoke('list-plots'),
  window: {
    minimize:     () => ipcRenderer.invoke('window-minimize'),
    maximize:     () => ipcRenderer.invoke('window-maximize'),
    close:        () => ipcRenderer.invoke('window-close'),
    isMaximized:  () => ipcRenderer.invoke('window-is-maximized'),
  },
})
