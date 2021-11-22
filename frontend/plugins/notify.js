export default function({store}, inject) {
  function notify(level, content) {
    store.commit('alert/showMessage', {level, content})
  }
  inject('notify', notify)
}
