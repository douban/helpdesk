import Vue from 'vue'
import Vuex from 'vuex'
import {getFirstActionFromTree} from '../utils/HFinder'

Vue.use(Vuex)

const debug = process.env.NODE_ENV !== 'production'

export default new Vuex.Store({
  strict: debug,
  state: {
    userProfile: '',
    actionDefinition: '',
    actionTree: ''
  },
  mutations: {
    setUserProfile (state, profile) {
      state.userProfile = profile
    },
    setActionDefinition (state, definition) {
      state.actionDefinition = definition
    },
    setActionTree (state, tree) {
      state.actionTree = tree
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
    },
    updateActionTree ({ commit }, tree) {
      commit('setActionTree', tree)
    }
  },
  getters: {
    isAdmin: (state) => {
      try {
        return state.userProfile.roles.includes("admin")
      } catch {
        return false
      }

    },
    isAuthenticated: (state) => {
      if (state.userProfile) {
        if (state.userProfile.is_authenticated) {
          return true
        }
      }
      return false
    },
    firstAction: (state) => {
      return getFirstActionFromTree(state.actionTree)
    }
  }
})
