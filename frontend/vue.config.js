module.exports = {
  devServer: {
    proxy: {
      '^/api': {
        target: 'http://localhost:8123', // Api server address
        changeOrigin: true,
      },
      '^/auth': {
        target: 'http://localhost:8123', // Api server address
        changeOrigin: true
      }
    }
  }
}
