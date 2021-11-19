export default function ({ $axios, redirect, app, route }) {
  $axios.onRequest(config => {
    //
  })

  $axios.onError(error => {
    const code = parseInt(error.response && error.response.status)
    const currentPath = route.fullPath
    if (code === 401) {
      // 401, unauthorized , redirect to login page
      app.$notify("warning", 'Login required, redirecting to login page...')
      if (route.name !== 'login') {
        redirect({name: 'login', query: {next: currentPath}})
      }
    } else if (code === 403) {
      // 403, insufficient privilege, Redirect to login page
      app.$notify('warning', 'Insufficient privilege!' + error.response.status + ':' + JSON.stringify(error.response.data))
      if (route.name !== 'login') {
        redirect({name: 'login', query: {next: currentPath}})
      }
    } else if (code >= 500) {
      app.$notify('error' ,'Internal error, please contact webadmin' + error.response.status + ':' + JSON.stringify(error.response.data))
    } else {
      // > 500 internal error, notify only
      // > 404 notify only
      const rawMsg = JSON.stringify(error.response.data)
      const msg = rawMsg.length > 150 ? rawMsg.slice(0, 150) + '...' : rawMsg
      app.$notify('warning' ,'Request failed: ' + error.response.status + ':' + msg)
    }
  })
}
