const path = require('path')

function resolve(dir) {
  return path.join(__dirname, dir)
}

module.exports = {
  productionSourceMap: true,
  devServer: {
    disableHostCheck: true,
    port: 4200,
    open: true,
    overlay: {
      warnings: false,
      errors: true
    },
    proxy: {
      '/api': {
        target: 'http://0.0.0.0:9001',
        ws: true,
        secure: false,
      },
      '/runtime': {
        target: 'http://0.0.0.0:9001',
        ws: true,
        secure: false,
      },
      '/ws': {
        target: 'ws://0.0.0.0:9002',
        ws: true,
        secure: false,
      }
    }
  },
  configureWebpack: {
    devtool: 'source-map',
    resolve: {
      alias: {
        '@': resolve('src')
      }
    }
  },
  publicPath: '/ui/',
};
