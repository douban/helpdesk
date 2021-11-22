import {getFirstActionFromTree} from '@/utils/HFinder'

export const state = () => ({
  userProfile: '',
  actionDefinition: '',
  actionTree: ''
})

export const mutations = {
  setUserProfile (state, profile) {
    state.userProfile = profile
  },
  setActionDefinition (state, definition) {
    state.actionDefinition = definition
  },
  setActionTree (state, tree) {
    state.actionTree = tree
  }
}

export const actions = {
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
}

export const getters = {
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
