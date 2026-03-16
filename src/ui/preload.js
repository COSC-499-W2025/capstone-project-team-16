const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('electronAPI', {
  // Example of exposing a safe API to the renderer
  // sendMessage: (message) => ipcRenderer.send('message', message),
});

console.log('Electron preload script loaded');