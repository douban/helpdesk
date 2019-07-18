import Vue from 'vue'
import Vuex from 'vuex'

Vue.use(Vuex)

const debug = process.env.NODE_ENV !== 'production'

export default new Vuex.Store({
  strict: debug,
  state: {
    userProfile: '',
    actionDefinition: ''
  },
  mutations: {
    setUserProfile (state, profile) {
      state.userProfile = profile
    },
    setActionDefinition (state, definition) {
      state.actionDefinition = definition
    }
  },
  actions: {
    updateUserProfile ({ commit }, profile) {
      commit('setUserProfile', profile)
    },
    deleteUserProfile ({ commit }) {
      commit('setUserProfile', '')
    },
    updateActionDefinition ({ commit }, definition) {
      commit('setActionDefinition', definition)
    }
  },
  getters: {
    isAdmin: (state) => {
      return state.userProfile.is_admin
    },
    isAuthenticated: (state) => {
      if (state.userProfile) {
        if (state.userProfile.is_authenticated) {
          return true
        }
      }
      return false
    }
  }
})
